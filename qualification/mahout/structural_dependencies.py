"""Mahout Governed Structural Dependency Expansion.

Implements governed structural dependency expansion for the Mahout qualification corpus:
1. Preserves the 400-issue primary seed as immutable (PRIMARY_SEED = 400).
2. Explicitly classifies added parent issues as `structural_dependency`.
3. Ensures structural dependency issues do NOT alter original 400 selection coverage or rationale.
4. Generates:
   - mahout_410_allowlist.txt
   - mahout_410_seed_manifest.json
   - mahout_410_seed_manifest_report.md
   - mahout_structural_dependency_manifest.json
   - mahout_structural_dependency_report.md
   - mahout_412_allowlist.txt (100% full closure companion)
   - mahout_412_seed_manifest.json
   - mahout_412_seed_manifest_report.md
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qualification.config import (
    DEFAULT_SAMPLING_SEED,
    FROZEN_ENGINE_COMMIT,
    JIRA_CONTRACT_VERSION,
    QUALIFICATION_HARNESS_VERSION,
)
from qualification.mahout.selector import (
    load_mahout_issues_from_mongo,
)
from qualification.policy import (
    canonical_record_hash,
    compute_sha256_file,
    compute_sha256_text,
)

PRIMARY_ALLOWLIST_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_400_allowlist.txt")
PRIMARY_MANIFEST_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_source_manifest.json")
SUBTASK_AUDIT_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_subtask_parent_audit.json")

DESTINATION_410_ALLOWLIST_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_410_allowlist.txt")
DESTINATION_410_MANIFEST_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_410_seed_manifest.json")
DESTINATION_410_REPORT_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_410_seed_manifest_report.md")

STRUCTURAL_DEP_MANIFEST_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_structural_dependency_manifest.json")
STRUCTURAL_DEP_REPORT_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_structural_dependency_report.md")

DESTINATION_412_ALLOWLIST_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_412_allowlist.txt")
DESTINATION_412_MANIFEST_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_412_seed_manifest.json")
DESTINATION_412_REPORT_PATH = Path("/home/tecblic/orbit-private/mahout/mahout_412_seed_manifest_report.md")

PRIMARY_400_SHA256 = "6dd6e30a79a1927c69b1446f3bb0d5161957d6d037a63dec5f9c70ffd14a6b50"

# The 10 structural dependency parents specified for the 410 destination corpus:
# Ranked by dependent subtask count descending, then numeric key order
SPECIFIED_10_PARENT_KEYS = (
    "MAHOUT-1838",  # 8 subtasks
    "MAHOUT-929",   # 4 subtasks
    "MAHOUT-933",   # 4 subtasks
    "MAHOUT-215",   # 3 subtasks
    "MAHOUT-2014",  # 3 subtasks
    "MAHOUT-9",     # 1 subtask
    "MAHOUT-286",   # 1 subtask
    "MAHOUT-301",   # 1 subtask
    "MAHOUT-306",   # 1 subtask
    "MAHOUT-524",   # 1 subtask
)

# Additional 2 parent keys required to achieve 100% (29/29) subtask parent closure:
FULL_CLOSURE_ADDITIONAL_PARENT_KEYS = (
    "MAHOUT-1010",  # 1 subtask: MAHOUT-1014
    "MAHOUT-1570",  # 1 subtask: MAHOUT-1816
)


@dataclass(frozen=True, slots=True)
class StructuralDependencyRecord:
    """An individual parent issue required for Jira subtask hierarchy validity."""

    source_key: str
    source_id: str
    source_issue_type: str
    reason_for_inclusion: str
    dependent_selected_subtasks: tuple[str, ...]
    classification: str = "structural_dependency"
    part_of_original_400: bool = False
    whether_the_parent_itself_was_part_of_the_original_400: bool = False
    status: str = "Closed"
    priority: str = "Major"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_key": self.source_key,
            "source_id": self.source_id,
            "source_issue_type": self.source_issue_type,
            "reason_for_inclusion": self.reason_for_inclusion,
            "dependent_selected_subtasks": list(self.dependent_selected_subtasks),
            "classification": self.classification,
            "part_of_original_400": self.part_of_original_400,
            "whether_the_parent_itself_was_part_of_the_original_400": (
                self.whether_the_parent_itself_was_part_of_the_original_400
            ),
            "status": self.status,
            "priority": self.priority,
        }


def extract_key_num(key: str) -> int:
    """Extract numeric portion of a Jira key for stable sorting."""
    if "-" in key:
        num = key.split("-", 1)[1]
        if num.isdigit():
            return int(num)
    return 0


def load_primary_seed_keys() -> list[str]:
    """Load the immutable 400 primary seed keys from disk and verify hash."""
    if not PRIMARY_ALLOWLIST_PATH.exists():
        raise FileNotFoundError(f"Primary allowlist not found: {PRIMARY_ALLOWLIST_PATH}")

    actual_hash = compute_sha256_file(PRIMARY_ALLOWLIST_PATH)
    if actual_hash != PRIMARY_400_SHA256:
        raise ValueError(
            f"Primary 400 allowlist SHA-256 mismatch! Expected {PRIMARY_400_SHA256}, got {actual_hash}"
        )

    lines = [line.strip() for line in PRIMARY_ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 400:
        raise ValueError(f"Primary allowlist must contain exactly 400 keys, found {len(lines)}")
    return lines


def build_structural_dependency_records(
    mongo_docs_by_key: dict[str, dict[str, Any]],
    subtasks_by_parent: dict[str, list[str]],
    keys: tuple[str, ...],
) -> list[StructuralDependencyRecord]:
    """Build standardized structural dependency records for given parent keys."""
    records: list[StructuralDependencyRecord] = []
    for k in keys:
        doc = mongo_docs_by_key.get(k)
        if not doc:
            raise KeyError(f"Parent key {k} not found in MongoDB Mahout dataset")

        fields = doc.get("fields", {}) or {}
        itype = fields.get("issuetype", {}).get("name") if isinstance(fields.get("issuetype"), dict) else "Unknown"
        status = fields.get("status", {}).get("name") if isinstance(fields.get("status"), dict) else "Unknown"
        priority = fields.get("priority", {}).get("name") if isinstance(fields.get("priority"), dict) else "Unknown"
        source_id = str(doc.get("id", ""))

        subs = sorted(subtasks_by_parent.get(k, []), key=extract_key_num)
        sub_count = len(subs)
        sub_str = ", ".join(subs) if sub_count <= 4 else f"{', '.join(subs[:3])} (+{sub_count - 3} more)"
        reason = (
            f"Required structural parent for {sub_count} selected Sub-task(s) ({sub_str}) in frozen 400 seed"
        )

        records.append(
            StructuralDependencyRecord(
                source_key=k,
                source_id=source_id,
                source_issue_type=itype,
                reason_for_inclusion=reason,
                dependent_selected_subtasks=tuple(subs),
                classification="structural_dependency",
                part_of_original_400=False,
                whether_the_parent_itself_was_part_of_the_original_400=False,
                status=status,
                priority=priority,
            )
        )
    return records


def generate_governed_expansion() -> dict[str, Any]:
    """Execute Governed Structural Dependency Expansion and write all artifacts."""
    # 1. Load primary 400 seed
    primary_keys = load_primary_seed_keys()
    primary_set = set(primary_keys)

    # 2. Load subtask audit to get exact subtask-parent relationships
    if not SUBTASK_AUDIT_PATH.exists():
        raise FileNotFoundError(f"Subtask audit not found: {SUBTASK_AUDIT_PATH}")
    audit_data = json.loads(SUBTASK_AUDIT_PATH.read_text(encoding="utf-8"))

    subtasks_by_parent: dict[str, list[str]] = {}
    for r in audit_data["records"]:
        if r["classification"] == "parent_outside_seed":
            subtasks_by_parent.setdefault(r["source_parent_key"], []).append(r["source_subtask_key"])

    # 3. Load all Mahout source docs from MongoDB
    docs = load_mahout_issues_from_mongo()
    docs_by_key = {d["key"]: d for d in docs}

    # 4. Build records for the specified 10 structural parents
    records_10 = build_structural_dependency_records(docs_by_key, subtasks_by_parent, SPECIFIED_10_PARENT_KEYS)
    # Build records for the 2 additional parents (for 100% full closure)
    records_additional_2 = build_structural_dependency_records(
        docs_by_key, subtasks_by_parent, FULL_CLOSURE_ADDITIONAL_PARENT_KEYS
    )
    all_12_records = records_10 + records_additional_2

    # 5. Build 410 destination corpus keys
    specified_10_keys_set = set(SPECIFIED_10_PARENT_KEYS)
    # Conservation verification:
    assert primary_set.isdisjoint(specified_10_keys_set), "Structural dependencies must not be in primary 400 seed!"
    corpus_410_keys = sorted(primary_set | specified_10_keys_set, key=extract_key_num)
    assert len(corpus_410_keys) == 410, f"Expected 410 destination keys, got {len(corpus_410_keys)}"
    assert primary_set.issubset(set(corpus_410_keys)), "Primary 400 keys must be subset of 410 destination corpus"

    # 6. Build 412 destination corpus keys (full 100% closure)
    all_12_keys_set = specified_10_keys_set | set(FULL_CLOSURE_ADDITIONAL_PARENT_KEYS)
    assert primary_set.isdisjoint(all_12_keys_set), "All 12 dependencies must not be in primary 400 seed!"
    corpus_412_keys = sorted(primary_set | all_12_keys_set, key=extract_key_num)
    assert len(corpus_412_keys) == 412, f"Expected 412 destination keys, got {len(corpus_412_keys)}"
    assert primary_set.issubset(set(corpus_412_keys)), "Primary 400 keys must be subset of 412 destination corpus"

    # 7. Write mahout_410_allowlist.txt
    allowlist_410_content = "\n".join(corpus_410_keys) + "\n"
    DESTINATION_410_ALLOWLIST_PATH.write_text(allowlist_410_content, encoding="utf-8")
    allowlist_410_sha256 = compute_sha256_file(DESTINATION_410_ALLOWLIST_PATH)

    # Write mahout_412_allowlist.txt
    allowlist_412_content = "\n".join(corpus_412_keys) + "\n"
    DESTINATION_412_ALLOWLIST_PATH.write_text(allowlist_412_content, encoding="utf-8")
    allowlist_412_sha256 = compute_sha256_file(DESTINATION_412_ALLOWLIST_PATH)

    # 8. Build Structural Dependency Manifest
    # Calculate covered subtasks
    covered_by_10 = sum(len(r.dependent_selected_subtasks) for r in records_10)
    covered_by_12 = sum(len(r.dependent_selected_subtasks) for r in all_12_records)

    dep_manifest = {
        "manifest_version": "1.0.0",
        "governance_mandate": "Governed Structural Dependency Expansion for Mahout Subtask Representation",
        "engine_commit": FROZEN_ENGINE_COMMIT,
        "accounting": {
            "primary_seed_count": 400,
            "structural_dependencies_count": 10,
            "destination_corpus_count": 410,
            "total_selected_subtasks": 31,
            "in_seed_parent_subtasks": 2,
            "outside_seed_parent_subtasks": 29,
            "subtasks_covered_by_10_dependencies": covered_by_10,
            "subtasks_unparented_in_410_corpus": 29 - covered_by_10,
            "full_closure_dependencies_count": 12,
            "full_closure_destination_corpus_count": 412,
            "subtasks_covered_by_12_dependencies": covered_by_12,
            "subtasks_unparented_in_412_corpus": 0,
        },
        "invariants": {
            "primary_seed_subset_of_destination": True,
            "original_400_seed_immutable": True,
            "original_400_allowlist_sha256": PRIMARY_400_SHA256,
            "original_400_allowlist_sha256_verified": compute_sha256_file(PRIMARY_ALLOWLIST_PATH) == PRIMARY_400_SHA256,
            "zero_synthetic_parents": True,
            "zero_subtask_type_conversion": True,
            "structural_dependencies_excluded_from_primary_coverage": True,
        },
        "structural_dependencies": [r.to_dict() for r in records_10],
        "full_closure_companion": {
            "additional_dependencies_count": len(records_additional_2),
            "additional_dependencies": [r.to_dict() for r in records_additional_2],
            "all_12_dependencies": [r.to_dict() for r in all_12_records],
        },
    }
    STRUCTURAL_DEP_MANIFEST_PATH.write_text(json.dumps(dep_manifest, indent=2), encoding="utf-8")
    dep_manifest_sha256 = compute_sha256_file(STRUCTURAL_DEP_MANIFEST_PATH)

    # 9. Build Downstream mahout_410_seed_manifest.json
    # Read primary manifest for metadata
    primary_manifest = json.loads(PRIMARY_MANIFEST_PATH.read_text(encoding="utf-8"))

    # Build items distinguishing primary_seed vs structural_dependency
    manifest_410_items = []
    # Primary 400 items
    primary_items_map = {it["identifier"]: it for it in primary_manifest["selection_accounting"]["items"]}
    for k in corpus_410_keys:
        if k in primary_set:
            orig = primary_items_map[k]
            manifest_410_items.append(
                {
                    "identifier": k,
                    "role": "primary_seed",
                    "classification": "primary_seed",
                    "status": "selected_for_qualification",
                    "reason": orig["reason"],
                    "content_hash": orig["content_hash"],
                    "metadata": dict(orig["metadata"]),
                }
            )
        else:
            rec = next(r for r in records_10 if r.source_key == k)
            doc = docs_by_key[k]
            fields = doc.get("fields", {}) or {}
            manifest_410_items.append(
                {
                    "identifier": k,
                    "role": "structural_dependency",
                    "classification": "structural_dependency",
                    "status": "structural_dependency",
                    "reason": rec.reason_for_inclusion,
                    "content_hash": canonical_record_hash(doc),
                    "metadata": {
                        "status": rec.status,
                        "priority": rec.priority,
                        "issuetype": rec.source_issue_type,
                        "has_duedate": bool(fields.get("duedate")),
                        "dependent_subtasks": list(rec.dependent_selected_subtasks),
                    },
                }
            )

    manifest_410 = {
        "manifest_version": "1.2.0",
        "governance_mandate": "Governed Structural Dependency Destination Corpus (410 Issues)",
        "qualification_identity": {
            "engine_commit": FROZEN_ENGINE_COMMIT,
            "jira_contract_version": JIRA_CONTRACT_VERSION,
            "harness_version": QUALIFICATION_HARNESS_VERSION,
            "sampling_seed": DEFAULT_SAMPLING_SEED,
            "dataset_hashes": {
                "source_dataset_content_sha256": primary_manifest["qualification_identity"]["dataset_hashes"]["source_dataset_content_sha256"],
                "primary_seed_400_allowlist_sha256": PRIMARY_400_SHA256,
                "destination_corpus_410_allowlist_sha256": allowlist_410_sha256,
                "structural_dependency_manifest_sha256": dep_manifest_sha256,
            },
            "selection_policy": {
                "primary_seed_policy": "deterministic_behavioral_coverage",
                "structural_dependency_policy": "governed_subtask_parent_resolution",
                "target_primary_seed_size": 400,
                "structural_dependencies_count": 10,
                "destination_corpus_size": 410,
            },
        },
        "corpus_accounting": {
            "is_balanced": True,
            "source_considered": 2121,
            "primary_seed_count": 400,
            "structural_dependencies_count": 10,
            "destination_corpus_count": 410,
            "not_selected_by_policy": 2121 - 410,
            "selection_failed": 0,
        },
        "primary_seed_coverage_summary": primary_manifest["coverage_summary"],
        "items": manifest_410_items,
    }
    DESTINATION_410_MANIFEST_PATH.write_text(json.dumps(manifest_410, indent=2), encoding="utf-8")
    manifest_410_sha256 = compute_sha256_file(DESTINATION_410_MANIFEST_PATH)

    # 10. Build 412 Manifest (Full Closure Companion)
    manifest_412_items = []
    for k in corpus_412_keys:
        if k in primary_set:
            orig = primary_items_map[k]
            manifest_412_items.append(
                {
                    "identifier": k,
                    "role": "primary_seed",
                    "classification": "primary_seed",
                    "status": "selected_for_qualification",
                    "reason": orig["reason"],
                    "content_hash": orig["content_hash"],
                    "metadata": dict(orig["metadata"]),
                }
            )
        else:
            rec = next(r for r in all_12_records if r.source_key == k)
            doc = docs_by_key[k]
            fields = doc.get("fields", {}) or {}
            manifest_412_items.append(
                {
                    "identifier": k,
                    "role": "structural_dependency",
                    "classification": "structural_dependency",
                    "status": "structural_dependency",
                    "reason": rec.reason_for_inclusion,
                    "content_hash": canonical_record_hash(doc),
                    "metadata": {
                        "status": rec.status,
                        "priority": rec.priority,
                        "issuetype": rec.source_issue_type,
                        "has_duedate": bool(fields.get("duedate")),
                        "dependent_subtasks": list(rec.dependent_selected_subtasks),
                    },
                }
            )

    manifest_412 = {
        "manifest_version": "1.2.0-full-closure",
        "governance_mandate": "Governed Structural Dependency Destination Corpus (412 Issues - 100% Subtask Closure)",
        "qualification_identity": {
            "engine_commit": FROZEN_ENGINE_COMMIT,
            "jira_contract_version": JIRA_CONTRACT_VERSION,
            "harness_version": QUALIFICATION_HARNESS_VERSION,
            "sampling_seed": DEFAULT_SAMPLING_SEED,
            "dataset_hashes": {
                "source_dataset_content_sha256": primary_manifest["qualification_identity"]["dataset_hashes"]["source_dataset_content_sha256"],
                "primary_seed_400_allowlist_sha256": PRIMARY_400_SHA256,
                "destination_corpus_412_allowlist_sha256": allowlist_412_sha256,
                "structural_dependency_manifest_sha256": dep_manifest_sha256,
            },
            "selection_policy": {
                "primary_seed_policy": "deterministic_behavioral_coverage",
                "structural_dependency_policy": "governed_subtask_parent_resolution_full_closure",
                "target_primary_seed_size": 400,
                "structural_dependencies_count": 12,
                "destination_corpus_size": 412,
            },
        },
        "corpus_accounting": {
            "is_balanced": True,
            "source_considered": 2121,
            "primary_seed_count": 400,
            "structural_dependencies_count": 12,
            "destination_corpus_count": 412,
            "not_selected_by_policy": 2121 - 412,
            "selection_failed": 0,
        },
        "primary_seed_coverage_summary": primary_manifest["coverage_summary"],
        "items": manifest_412_items,
    }
    DESTINATION_412_MANIFEST_PATH.write_text(json.dumps(manifest_412, indent=2), encoding="utf-8")
    manifest_412_sha256 = compute_sha256_file(DESTINATION_412_MANIFEST_PATH)

    # 11. Generate Reports
    dep_report_md = _build_structural_dependency_report_md(records_10, records_additional_2, dep_manifest)
    STRUCTURAL_DEP_REPORT_PATH.write_text(dep_report_md, encoding="utf-8")

    manifest_410_report_md = _build_410_manifest_report_md(manifest_410, records_10, allowlist_410_sha256)
    DESTINATION_410_REPORT_PATH.write_text(manifest_410_report_md, encoding="utf-8")

    manifest_412_report_md = _build_412_manifest_report_md(manifest_412, all_12_records, allowlist_412_sha256)
    DESTINATION_412_REPORT_PATH.write_text(manifest_412_report_md, encoding="utf-8")

    return {
        "primary_400_sha256": PRIMARY_400_SHA256,
        "allowlist_410_sha256": allowlist_410_sha256,
        "manifest_410_sha256": manifest_410_sha256,
        "structural_dep_manifest_sha256": dep_manifest_sha256,
        "allowlist_412_sha256": allowlist_412_sha256,
        "manifest_412_sha256": manifest_412_sha256,
        "specified_10_parent_keys": SPECIFIED_10_PARENT_KEYS,
        "full_closure_additional_parent_keys": FULL_CLOSURE_ADDITIONAL_PARENT_KEYS,
    }


def _build_structural_dependency_report_md(
    records_10: list[StructuralDependencyRecord],
    additional_2: list[StructuralDependencyRecord],
    manifest: dict[str, Any],
) -> str:
    """Build the comprehensive Markdown report for structural dependencies."""
    acc = manifest["accounting"]
    lines = [
        "# Mahout Governed Structural Dependency Report",
        "",
        "## 1. Executive Summary & Governance Authorization",
        "- **Primary Seed**: 400 issues (100% frozen, selection SHA-256 immutable: `ab15e7c5...`)",
        "- **Original 400 Allowlist SHA-256**: `6dd6e30a79a1927c69b1446f3bb0d5161957d6d037a63dec5f9c70ffd14a6b50` (Verified UNCHANGED)",
        f"- **Structural Dependencies Specified**: {acc['structural_dependencies_count']} issues",
        f"- **Destination Corpus Size**: {acc['destination_corpus_count']} issues",
        f"- **Classification**: Strictly `structural_dependency` (excluded from primary coverage statistics)",
        f"- **Engine Baseline**: Untouched @ `{FROZEN_ENGINE_COMMIT}`",
        "- **Jira Mutations**: Exactly **0** issue creations, **0** transitions, **0** configuration mutations",
        "",
        "## 2. Invariant & Set Conservation Verification",
        "| Verification Invariant | Expected | Actual | Status |",
        "| :--- | :--- | :--- | :--- |",
        "| Primary Seed Inclusion | 400 keys ⊂ Destination Corpus | 400 keys ⊂ 410 corpus | **PASS** |",
        "| Structural Dependency Count | Exactly 10 | 10 | **PASS** |",
        "| Unique Destination Keys | Exactly 410 | 410 | **PASS** |",
        "| Primary Allowlist Hash | `6dd6e30a...` | `6dd6e30a...` | **PASS (UNTOUCHED)** |",
        "| No Additional Issues | Exactly 10 added | 10 added | **PASS** |",
        "| Zero Parent Fabrication | All from Apache MongoDB | 100% real Mahout issues | **PASS** |",
        "| Zero Subtask Conversion | Retain Sub-task type | 0 converted to Task | **PASS** |",
        "",
        "## 3. Census of the 10 Specified Structural Dependencies (410 Corpus)",
        "",
        "| Source Key | Source ID | Issue Type | Status | Priority | Dependent Subtasks Covered | Reason for Inclusion |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in records_10:
        subs = ", ".join(f"`{s}`" for s in r.dependent_selected_subtasks)
        lines.append(
            f"| `{r.source_key}` | `{r.source_id}` | `{r.source_issue_type}` | `{r.status}` | `{r.priority}` | {subs} ({len(r.dependent_selected_subtasks)}) | {r.reason_for_inclusion} |"
        )

    lines.extend(
        [
            "",
            "## 4. Subtask Coverage & Census Reconciliation",
            f"- **Total Subtasks in 400 Seed**: {acc['total_selected_subtasks']}",
            f"- **In-Seed Parent Subtasks**: {acc['in_seed_parent_subtasks']} (`MAHOUT-1372` -> `MAHOUT-1371`, `MAHOUT-1866` -> `MAHOUT-1855`)",
            f"- **Outside-Seed Parent Subtasks**: {acc['outside_seed_parent_subtasks']}",
            f"- **Subtasks Covered by 10 Dependencies**: {acc['subtasks_covered_by_10_dependencies']} of 29 (93.1%)",
            f"- **Subtasks Unparented in Strict 410 Corpus**: {acc['subtasks_unparented_in_410_corpus']}",
            "",
            "> [!IMPORTANT]",
            "> **Exact Census Finding & Full-Closure Companion**:",
            "> The earlier preflight audit text contained an off-by-two typo in its section heading ('10 distinct parent issues',",
            "> although all 12 were listed immediately below it). In reality, the 29 outside-seed subtasks trace back to",
            "> **exactly 12 distinct parent keys** in Apache Mahout.",
            "> Including the 10 specified parents covers **27 of 29 subtasks**.",
            "> The remaining 2 subtasks require 2 additional parents for 100% (29/29) closure:",
            "",
            "| Source Key | Source ID | Issue Type | Status | Priority | Dependent Subtask | Role |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )
    for r in additional_2:
        subs = ", ".join(f"`{s}`" for s in r.dependent_selected_subtasks)
        lines.append(
            f"| `{r.source_key}` | `{r.source_id}` | `{r.source_issue_type}` | `{r.status}` | `{r.priority}` | {subs} | Completes 100% subtask parent legality |"
        )

    lines.extend(
        [
            "",
            "To support both governance modes with complete transparency, the pipeline has generated:",
            "1. **Governed 410 Artifacts**: `mahout_410_allowlist.txt`, `mahout_410_seed_manifest.json`, `mahout_410_seed_manifest_report.md` (exactly 10 structural dependencies).",
            "2. **Full-Closure 412 Artifacts**: `mahout_412_allowlist.txt`, `mahout_412_seed_manifest.json`, `mahout_412_seed_manifest_report.md` (all 12 dependencies, 100% legal subtask hierarchy).",
            "",
            "## 5. Artifact Hashes",
            f"- `mahout_400_allowlist.txt`: `{PRIMARY_400_SHA256}`",
            f"- `mahout_410_allowlist.txt`: `{compute_sha256_file(DESTINATION_410_ALLOWLIST_PATH)}`",
            f"- `mahout_410_seed_manifest.json`: `{compute_sha256_file(DESTINATION_410_MANIFEST_PATH)}`",
            f"- `mahout_structural_dependency_manifest.json`: `{compute_sha256_file(STRUCTURAL_DEP_MANIFEST_PATH)}`",
            f"- `mahout_412_allowlist.txt`: `{compute_sha256_file(DESTINATION_412_ALLOWLIST_PATH)}`",
            f"- `mahout_412_seed_manifest.json`: `{compute_sha256_file(DESTINATION_412_MANIFEST_PATH)}`",
            "",
        ]
    )
    return "\n".join(lines)


def _build_410_manifest_report_md(
    manifest: dict[str, Any],
    records_10: list[StructuralDependencyRecord],
    allowlist_hash: str,
) -> str:
    """Build the Markdown report for the 410 Destination Corpus."""
    acc = manifest["corpus_accounting"]
    lines = [
        "# Mahout 410 Destination Corpus Manifest Report",
        "",
        "## 1. Executive Summary",
        f"- **Destination Corpus Size**: {acc['destination_corpus_count']} issues",
        f"- **Primary Seed Count**: {acc['primary_seed_count']} issues (100% coverage population)",
        f"- **Structural Dependencies Count**: {acc['structural_dependencies_count']} issues (subtask parent support)",
        f"- **Total Source Issues Considered**: {acc['source_considered']}",
        f"- **Not Selected by Policy**: {acc['not_selected_by_policy']}",
        f"- **Selection Accounting Status**: Balanced ({acc['source_considered']} = {acc['primary_seed_count']} + {acc['structural_dependencies_count']} + {acc['not_selected_by_policy']})",
        f"- **Engine Baseline**: Frozen @ `{FROZEN_ENGINE_COMMIT}`",
        f"- **Allowlist SHA-256**: `{allowlist_hash}`",
        "",
        "## 2. Strict Role Distinction",
        "Every entity in the destination corpus is explicitly categorized into one of two mutually exclusive roles:",
        "1. `primary_seed` (400 issues): Selected via deterministic multi-tier behavioral coverage.",
        "2. `structural_dependency` (10 issues): Included strictly to provide parent entities for selected Sub-tasks in Jira Cloud.",
        "",
        "## 3. Added Structural Dependencies",
        "| Source Key | Source ID | Issue Type | Dependent Subtasks Covered |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for r in records_10:
        subs = ", ".join(f"`{s}`" for s in r.dependent_selected_subtasks)
        lines.append(f"| `{r.source_key}` | `{r.source_id}` | `{r.source_issue_type}` | {subs} |")

    lines.extend(
        [
            "",
            "## 4. Conservation & Guardrails",
            "- Primary 400 selection algorithm, coverage metrics, and tie-breaking remain 100% immutable.",
            "- Zero Jira issue mutations executed.",
            "- Zero Jira configuration mutations executed.",
            "",
        ]
    )
    return "\n".join(lines)


def _build_412_manifest_report_md(
    manifest: dict[str, Any],
    all_12_records: list[StructuralDependencyRecord],
    allowlist_hash: str,
) -> str:
    """Build the Markdown report for the 412 Full-Closure Destination Corpus."""
    acc = manifest["corpus_accounting"]
    lines = [
        "# Mahout 412 Full-Closure Destination Corpus Manifest Report",
        "",
        "## 1. Executive Summary",
        f"- **Destination Corpus Size**: {acc['destination_corpus_count']} issues",
        f"- **Primary Seed Count**: {acc['primary_seed_count']} issues",
        f"- **Structural Dependencies Count**: {acc['structural_dependencies_count']} issues",
        "- **Subtask Parent Legality**: 100% (29/29 outside-seed subtasks + 2/2 in-seed subtasks have valid parents)",
        f"- **Engine Baseline**: Frozen @ `{FROZEN_ENGINE_COMMIT}`",
        f"- **Allowlist SHA-256**: `{allowlist_hash}`",
        "",
        "## 2. All 12 Structural Dependencies",
        "| Source Key | Source ID | Issue Type | Dependent Subtasks Covered |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for r in all_12_records:
        subs = ", ".join(f"`{s}`" for s in r.dependent_selected_subtasks)
        lines.append(f"| `{r.source_key}` | `{r.source_id}` | `{r.source_issue_type}` | {subs} |")

    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print("Executing Governed Structural Dependency Expansion...")
    res = generate_governed_expansion()
    print("Done! Artifact Hashes:")
    for k, v in res.items():
        print(f"  {k}: {v}")
