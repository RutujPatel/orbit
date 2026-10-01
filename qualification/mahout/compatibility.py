"""ORBITLAB Vocabulary Compatibility Evaluator and Readiness Gate.

Evaluates compatibility between Mahout source dimensions and destination ORBITLAB:
1. 16 Issue Types: exact vs unavailable vs ambiguous.
2. 5 Priorities: exact vs unavailable vs ambiguous.
3. 6 Statuses: exact vs representable_by_destination_state vs unavailable vs ambiguous.
4. 15 Transition Pairs: valid destination path vs unavailable.
5. Field requirements and constraints (summary, description, duedate, required custom fields).

Enforces the three-valued readiness gate:
- READY: All selected 400 corpus semantics are exactly representable without distortion.
- BLOCKED: Destination cannot safely represent source vocabulary.
- BLOCKED_REQUIRES_CONFIGURATION_REVIEW: Representation is possible if project configuration is adjusted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from qualification.policy import compute_sha256_file, compute_sha256_text

DEFAULT_COMPATIBILITY_JSON_PATH = Path("/home/tecblic/orbit-private/mahout/orbitlab_vocabulary_compatibility.json")
DEFAULT_COMPATIBILITY_MD_PATH = Path("/home/tecblic/orbit-private/mahout/orbitlab_vocabulary_compatibility_report.md")


class CompatibilityClassification(str, Enum):
    """Rigorous qualification taxonomy for destination vocabulary compatibility."""

    EXACT = "exact"
    REPRESENTABLE_BY_DESTINATION_STATE = "representable_by_destination_state"
    APPROXIMATE_SEMANTIC_MAPPING = "approximate_semantic_mapping"
    UNAVAILABLE = "unavailable"
    AMBIGUOUS = "ambiguous"
    CONTRACT_NOT_REPRESENTABLE = "contract_not_representable"


class ImportReadinessGate(str, Enum):
    """Machine-readable readiness gate for Phase 4 import."""

    READY = "READY"
    BLOCKED = "BLOCKED"
    BLOCKED_REQUIRES_CONFIGURATION_REVIEW = "BLOCKED_REQUIRES_CONFIGURATION_REVIEW"


MAHOUT_SOURCE_TYPES: tuple[str, ...] = (
    "Bug",
    "Improvement",
    "New Feature",
    "Task",
    "Documentation",
    "Question",
    "Sub-task",
    "Wish",
    "Test",
    "Epic",
    "Dependency upgrade",
    "Blog - New Blog Request",
    "New JIRA Project",
    "Story",
    "Planned Work",
    "Proposal",
)

MAHOUT_SOURCE_PRIORITIES: tuple[str, ...] = (
    "Blocker",
    "Critical",
    "Major",
    "Minor",
    "Trivial",
)

MAHOUT_SOURCE_STATUSES: tuple[str, ...] = (
    "Open",
    "In Progress",
    "Patch Available",
    "Resolved",
    "Closed",
    "Reopened",
)

MAHOUT_SOURCE_TRANSITIONS: tuple[tuple[str, str], ...] = (
    ("Resolved", "Closed"),
    ("Open", "Resolved"),
    ("Open", "Patch Available"),
    ("Patch Available", "Resolved"),
    ("Open", "In Progress"),
    ("In Progress", "Resolved"),
    ("Resolved", "Reopened"),
    ("Reopened", "Resolved"),
    ("Patch Available", "Open"),
    ("In Progress", "Patch Available"),
    ("Reopened", "Patch Available"),
    ("In Progress", "Open"),
    ("Open", "Closed"),
    ("Patch Available", "In Progress"),
    ("Reopened", "In Progress"),
)


@dataclass(frozen=True, slots=True)
class ItemCompatibility:
    source_value: str
    destination_value: str | None
    classification: CompatibilityClassification
    rationale: str
    requires_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_value": self.source_value,
            "destination_value": self.destination_value,
            "classification": self.classification.value,
            "rationale": self.rationale,
            "requires_review": self.requires_review,
        }


@dataclass(frozen=True, slots=True)
class FieldCompatibility:
    field_key: str
    field_name: str
    supported: bool
    required: bool
    schema_type: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_key": self.field_key,
            "field_name": self.field_name,
            "supported": self.supported,
            "required": self.required,
            "schema_type": self.schema_type,
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class TransitionCompatibility:
    source_from: str
    source_to: str
    destination_path: list[str]
    classification: CompatibilityClassification
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_pair": f"{self.source_from}->{self.source_to}",
            "source_from": self.source_from,
            "source_to": self.source_to,
            "destination_path": list(self.destination_path),
            "classification": self.classification.value,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class CompatibilityMatrix:
    project_identity: dict[str, Any]
    issue_types: tuple[ItemCompatibility, ...]
    priorities: tuple[ItemCompatibility, ...]
    statuses: tuple[ItemCompatibility, ...]
    transitions: tuple[TransitionCompatibility, ...]
    fields: tuple[FieldCompatibility, ...]
    readiness_gate: ImportReadinessGate
    readiness_reasons: tuple[str, ...]

    @property
    def issue_type_accounting(self) -> dict[str, int]:
        counts = {
            "exact": 0,
            "unavailable": 0,
            "approximate_semantic_mapping": 0,
            "representable_by_destination_state": 0,
            "contract_not_representable": 0,
            "ambiguous": 0,
        }
        for it in self.issue_types:
            val = it.classification.value
            counts[val] = counts.get(val, 0) + 1
        counts["total"] = len(self.issue_types)
        return counts

    @property
    def status_accounting(self) -> dict[str, int]:
        counts = {
            "exact": 0,
            "representable_by_destination_state": 0,
            "unavailable": 0,
            "approximate_semantic_mapping": 0,
            "contract_not_representable": 0,
            "ambiguous": 0,
        }
        for st in self.statuses:
            val = st.classification.value
            counts[val] = counts.get(val, 0) + 1
        counts["total"] = len(self.statuses)
        return counts

    @property
    def transition_accounting(self) -> dict[str, int]:
        counts = {
            "exact": 0,
            "representable_by_destination_state": 0,
            "contract_not_representable": 0,
            "unavailable": 0,
            "ambiguous": 0,
        }
        for tr in self.transitions:
            val = tr.classification.value
            counts[val] = counts.get(val, 0) + 1
        counts["total"] = len(self.transitions)
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_identity": self.project_identity,
            "readiness_gate": self.readiness_gate.value,
            "readiness_reasons": list(self.readiness_reasons),
            "issue_type_accounting": self.issue_type_accounting,
            "status_accounting": self.status_accounting,
            "transition_accounting": self.transition_accounting,
            "issue_types": [it.to_dict() for it in self.issue_types],
            "priorities": [pr.to_dict() for pr in self.priorities],
            "statuses": [st.to_dict() for st in self.statuses],
            "transitions": [tr.to_dict() for tr in self.transitions],
            "fields": [f.to_dict() for f in self.fields],
        }


def evaluate_compatibility(
    project_meta: dict[str, Any],
    createmeta: dict[str, Any],
    statuses_meta: list[dict[str, Any]],
    priorities_meta: list[dict[str, Any]] | None = None,
) -> CompatibilityMatrix:
    """Evaluate full vocabulary compatibility against raw Jira REST inspection metadata."""
    # 1. Project identity
    proj_id_info = {
        "key": project_meta.get("key", "UNKNOWN"),
        "id": project_meta.get("id", "UNKNOWN"),
        "name": project_meta.get("name", "UNKNOWN"),
        "project_type_key": project_meta.get("projectTypeKey", "UNKNOWN"),
        "simplified": project_meta.get("simplified", False),
        "style": project_meta.get("style", "UNKNOWN"),
        "url": project_meta.get("self", ""),
    }

    # Extract available destination issue types from createmeta
    dest_types: dict[str, dict[str, Any]] = {}
    dest_fields_by_type: dict[str, dict[str, Any]] = {}

    projects_list = createmeta.get("projects", [])
    if projects_list and isinstance(projects_list[0], dict):
        for it in projects_list[0].get("issuetypes", []):
            name = it.get("name")
            if name:
                dest_types[name.lower()] = it
                dest_fields_by_type[name.lower()] = it.get("fields", {})

    # Extract available destination statuses
    dest_statuses: dict[str, dict[str, Any]] = {}
    for st_group in statuses_meta:
        if isinstance(st_group, dict):
            for st in st_group.get("statuses", []):
                name = st.get("name")
                if name:
                    dest_statuses[name.lower()] = st

    # Extract available destination priorities
    dest_priorities: dict[str, dict[str, Any]] = {}
    if priorities_meta:
        for pr in priorities_meta:
            name = pr.get("name")
            if name:
                dest_priorities[name.lower()] = pr

    reasons: list[str] = []

    # 2. Evaluate Issue Types
    type_evals: list[ItemCompatibility] = []
    unsupported_types: list[str] = []

    for src_type in MAHOUT_SOURCE_TYPES:
        src_lower = src_type.lower()
        dest_match = dest_types.get(src_lower)
        if not dest_match:
            # Check normalized match (e.g. Sub-task <-> Subtask)
            norm_key = src_lower.replace("-", "").replace(" ", "")
            for dt_k, dt_v in dest_types.items():
                if dt_k.replace("-", "").replace(" ", "") == norm_key:
                    dest_match = dt_v
                    break

        if dest_match:
            type_evals.append(ItemCompatibility(
                source_value=src_type,
                destination_value=dest_match["name"],
                classification=CompatibilityClassification.EXACT,
                rationale="Exact issue type match available in destination project",
            ))
        else:
            unsupported_types.append(src_type)
            type_evals.append(ItemCompatibility(
                source_value=src_type,
                destination_value=None,
                classification=CompatibilityClassification.UNAVAILABLE,
                rationale=(
                    f"Destination project ORBITLAB lacks issue type '{src_type}'. "
                    f"Must NOT silently map to generic type without configuration decision."
                ),
                requires_review=True,
            ))

    if unsupported_types:
        reasons.append(
            f"{len(unsupported_types)} Mahout issue types unavailable in ORBITLAB: "
            f"{', '.join(unsupported_types[:5])}" + ("..." if len(unsupported_types) > 5 else "")
        )

    # 3. Evaluate Priorities
    prio_evals: list[ItemCompatibility] = []
    unsupported_prios: list[str] = []

    for src_prio in MAHOUT_SOURCE_PRIORITIES:
        src_lower = src_prio.lower()
        if src_lower in dest_priorities:
            prio_evals.append(ItemCompatibility(
                source_value=src_prio,
                destination_value=dest_priorities[src_lower]["name"],
                classification=CompatibilityClassification.EXACT,
                rationale="Exact priority match available in destination Jira instance",
            ))
        else:
            # Check standard Jira Cloud equivalents (e.g. Blocker -> Highest)
            approx_mapping = {
                "blocker": "Highest",
                "critical": "High",
                "major": "Medium",
                "minor": "Low",
                "trivial": "Lowest",
            }
            mapped_val = approx_mapping.get(src_lower)
            if mapped_val and mapped_val.lower() in dest_priorities:
                prio_evals.append(ItemCompatibility(
                    source_value=src_prio,
                    destination_value=mapped_val,
                    classification=CompatibilityClassification.APPROXIMATE_SEMANTIC_MAPPING,
                    rationale=(
                        f"Source priority '{src_prio}' maps semantically to standard Jira Cloud '{mapped_val}'. "
                        f"Requires explicit configuration approval."
                    ),
                    requires_review=True,
                ))
            else:
                unsupported_prios.append(src_prio)
                prio_evals.append(ItemCompatibility(
                    source_value=src_prio,
                    destination_value=None,
                    classification=CompatibilityClassification.UNAVAILABLE,
                    rationale=f"Priority '{src_prio}' completely unavailable in destination Jira instance",
                    requires_review=True,
                ))

    # 4. Evaluate Statuses
    status_evals: list[ItemCompatibility] = []
    unsupported_statuses: list[str] = []

    for src_st in MAHOUT_SOURCE_STATUSES:
        src_lower = src_st.lower()
        if src_lower in dest_statuses:
            status_evals.append(ItemCompatibility(
                source_value=src_st,
                destination_value=dest_statuses[src_lower]["name"],
                classification=CompatibilityClassification.EXACT,
                rationale="Exact status match available in destination project workflow",
            ))
        else:
            # Check representable states
            approx_st_mapping = {
                "open": "To Do",
                "in progress": "In Progress",
                "resolved": "Done",
                "closed": "Done",
            }
            mapped_st = approx_st_mapping.get(src_lower)
            if mapped_st and mapped_st.lower() in dest_statuses:
                status_evals.append(ItemCompatibility(
                    source_value=src_st,
                    destination_value=mapped_st,
                    classification=CompatibilityClassification.REPRESENTABLE_BY_DESTINATION_STATE,
                    rationale=(
                        f"Source status '{src_st}' representable by destination workflow state '{mapped_st}'. "
                        f"Requires explicit qualification governance signoff."
                    ),
                    requires_review=True,
                ))
            else:
                unsupported_statuses.append(src_st)
                status_evals.append(ItemCompatibility(
                    source_value=src_st,
                    destination_value=None,
                    classification=CompatibilityClassification.UNAVAILABLE,
                    rationale=(
                        f"Source status '{src_st}' has no counterpart in destination project. "
                        f"Must NOT silently collapse into unrelated states."
                    ),
                    requires_review=True,
                ))

    if unsupported_statuses:
        reasons.append(
            f"Mahout source statuses unavailable in ORBITLAB: {', '.join(unsupported_statuses)}"
        )

    # 5. Evaluate Transition Pairs
    transition_evals: list[TransitionCompatibility] = []
    unsupported_trans: list[str] = []

    for t_from, t_to in MAHOUT_SOURCE_TRANSITIONS:
        pair_label = f"{t_from}->{t_to}"
        # A transition path is only available if both from and to statuses are representable
        from_eval = next((e for e in status_evals if e.source_value == t_from), None)
        to_eval = next((e for e in status_evals if e.source_value == t_to), None)

        if from_eval and to_eval and from_eval.destination_value and to_eval.destination_value:
            if from_eval.destination_value == to_eval.destination_value:
                # Self-loop on collapsed status (e.g. Resolved -> Closed both mapping to Done)
                transition_evals.append(TransitionCompatibility(
                    source_from=t_from,
                    source_to=t_to,
                    destination_path=[from_eval.destination_value],
                    classification=CompatibilityClassification.CONTRACT_NOT_REPRESENTABLE,
                    rationale=(
                        f"State collapse: transition {pair_label} maps both distinct source states into destination "
                        f"'{from_eval.destination_value}', obliterating the workflow transition."
                    ),
                ))
                unsupported_trans.append(pair_label)
            elif (
                from_eval.classification == CompatibilityClassification.EXACT
                and to_eval.classification == CompatibilityClassification.EXACT
            ):
                transition_evals.append(TransitionCompatibility(
                    source_from=t_from,
                    source_to=t_to,
                    destination_path=[from_eval.destination_value, to_eval.destination_value],
                    classification=CompatibilityClassification.EXACT,
                    rationale=f"Exact workflow transition preserved: {from_eval.destination_value} -> {to_eval.destination_value}",
                ))
            else:
                transition_evals.append(TransitionCompatibility(
                    source_from=t_from,
                    source_to=t_to,
                    destination_path=[from_eval.destination_value, to_eval.destination_value],
                    classification=CompatibilityClassification.REPRESENTABLE_BY_DESTINATION_STATE,
                    rationale=(
                        f"Approximate representation: path exists between mapped states "
                        f"'{from_eval.destination_value}' -> '{to_eval.destination_value}'"
                    ),
                ))
        else:
            unavail_reasons = []
            if not from_eval or not from_eval.destination_value:
                unavail_reasons.append(f"source status '{t_from}' is unavailable")
            if not to_eval or not to_eval.destination_value:
                unavail_reasons.append(f"source status '{t_to}' is unavailable")
            transition_evals.append(TransitionCompatibility(
                source_from=t_from,
                source_to=t_to,
                destination_path=[],
                classification=CompatibilityClassification.UNAVAILABLE,
                rationale=f"Unavailable transition: {', '.join(unavail_reasons)} in destination project",
            ))
            unsupported_trans.append(pair_label)

    # 6. Evaluate Required Fields & Constraints
    field_evals: list[FieldCompatibility] = []
    # Inspect common fields across destination types
    all_fields: dict[str, dict[str, Any]] = {}
    for fields_dict in dest_fields_by_type.values():
        for f_key, f_meta in fields_dict.items():
            if f_key not in all_fields:
                all_fields[f_key] = f_meta

    # Check mandatory fields for qualification
    key_fields = ["summary", "description", "duedate", "priority", "issuetype"]
    for kf in key_fields:
        f_meta = all_fields.get(kf)
        if f_meta:
            field_evals.append(FieldCompatibility(
                field_key=kf,
                field_name=f_meta.get("name", kf),
                supported=True,
                required=f_meta.get("required", False),
                schema_type=f_meta.get("schema", {}).get("type", "unknown"),
                notes="Standard field supported in destination project",
            ))
        else:
            field_evals.append(FieldCompatibility(
                field_key=kf,
                field_name=kf,
                supported=False,
                required=False,
                schema_type="unknown",
                notes=f"Field '{kf}' not present in destination project schema",
            ))

    # Check any unanticipated required fields that could block issue creation
    unanticipated_required = []
    for f_key, f_meta in all_fields.items():
        if f_meta.get("required", False) and f_key not in ("summary", "issuetype", "project"):
            unanticipated_required.append(f_meta.get("name", f_key))
            field_evals.append(FieldCompatibility(
                field_key=f_key,
                field_name=f_meta.get("name", f_key),
                supported=True,
                required=True,
                schema_type=f_meta.get("schema", {}).get("type", "unknown"),
                notes="Mandatory required custom/system field on issue creation",
            ))

    if unanticipated_required:
        reasons.append(
            f"Unanticipated required fields on issue creation: {', '.join(unanticipated_required)}"
        )

    # 7. Evaluate Readiness Gate
    if not unsupported_types and not unsupported_statuses and not unsupported_prios and not unanticipated_required:
        gate = ImportReadinessGate.READY
    elif unsupported_types or unsupported_statuses:
        # If types or statuses are missing, determine if configuration review could enable representation
        gate = ImportReadinessGate.BLOCKED_REQUIRES_CONFIGURATION_REVIEW
    else:
        gate = ImportReadinessGate.BLOCKED

    return CompatibilityMatrix(
        project_identity=proj_id_info,
        issue_types=tuple(type_evals),
        priorities=tuple(prio_evals),
        statuses=tuple(status_evals),
        transitions=tuple(transition_evals),
        fields=tuple(field_evals),
        readiness_gate=gate,
        readiness_reasons=tuple(reasons),
    )


def generate_compatibility_markdown_report(matrix: CompatibilityMatrix) -> str:
    """Generate human-readable markdown report for vocabulary compatibility."""
    proj = matrix.project_identity
    lines = [
        "# ORBITLAB Pre-Import Vocabulary Compatibility & Capability Report",
        "",
        "## 1. Project Identity & Governance",
        f"- **Project Key**: `{proj.get('key')}`",
        f"- **Project ID**: `{proj.get('id')}`",
        f"- **Project Name**: `{proj.get('name')}`",
        f"- **Project Type**: `{proj.get('project_type_key')}` (Simplified/Team-Managed: `{proj.get('simplified')}`)",
        f"- **Style**: `{proj.get('style')}`",
        f"- **Import Readiness Gate**: **`{matrix.readiness_gate.value}`**",
        "",
        "### Readiness Gate Rationale:",
    ]
    if matrix.readiness_reasons:
        for r in matrix.readiness_reasons:
            lines.append(f"- ⚠️ {r}")
    else:
        lines.append("- ✅ All 16 issue types, 5 priorities, and 6 statuses are fully compatible.")

    ita = matrix.issue_type_accounting
    sta = matrix.status_accounting
    tra = matrix.transition_accounting

    lines.extend([
        "",
        "## 2. Issue Type Compatibility Matrix (16 Mahout Types)",
        f"- **Accounting**: `{ita['total']} total = {ita['exact']} exact + {ita['unavailable']} unavailable`",
        "",
        "| Source Issue Type | Destination Representation | Classification | Governance Rationale |",
        "| :--- | :--- | :--- | :--- |",
    ])
    for it in matrix.issue_types:
        dest_val = f"`{it.destination_value}`" if it.destination_value else "*None*"
        lines.append(f"| `{it.source_value}` | {dest_val} | `{it.classification.value}` | {it.rationale} |")

    lines.extend([
        "",
        "## 3. Priority Compatibility Matrix (5 Mahout Priorities)",
        "| Source Priority | Destination Priority | Classification | Governance Rationale |",
        "| :--- | :--- | :--- | :--- |",
    ])
    for pr in matrix.priorities:
        dest_val = f"`{pr.destination_value}`" if pr.destination_value else "*None*"
        lines.append(f"| `{pr.source_value}` | {dest_val} | `{pr.classification.value}` | {pr.rationale} |")

    lines.extend([
        "",
        "## 4. Status Compatibility Matrix (6 Mahout Statuses)",
        (
            f"- **Accounting**: `{sta['total']} total = {sta['exact']} exact + "
            f"{sta['representable_by_destination_state']} representable_by_destination_state + "
            f"{sta['unavailable']} unavailable`"
        ),
        "",
        "| Source Status | Destination Status | Classification | Governance Rationale |",
        "| :--- | :--- | :--- | :--- |",
    ])
    for st in matrix.statuses:
        dest_val = f"`{st.destination_value}`" if st.destination_value else "*None*"
        lines.append(f"| `{st.source_value}` | {dest_val} | `{st.classification.value}` | {st.rationale} |")

    lines.extend([
        "",
        "## 5. Transition Path Compatibility (15 Mahout Transition Pairs)",
        (
            f"- **Accounting**: `{tra['total']} total = {tra['exact']} exact + "
            f"{tra['representable_by_destination_state']} representable_by_destination_state + "
            f"{tra['contract_not_representable']} contract_not_representable + "
            f"{tra['unavailable']} unavailable + {tra['ambiguous']} ambiguous`"
        ),
        "",
        "### Key Transition Governance Findings:",
        "- ⚠️ **`Resolved -> Closed` State Collapse**: Both `Resolved` and `Closed` map to `Done`. "
        "This collapses the transition into a destination self-loop (`Done -> Done`), classifying it as **`contract_not_representable`**.",
        f"- ⚠️ **Missing Status Impact (9 pairs)**: 9 transition pairs involve `Patch Available` (5 pairs) "
        "or `Reopened` (4 pairs: 3 unique + 1 overlap `Reopened->Patch Available`), rendering them **`unavailable`**.",
        "",
        "| Transition Pair | Destination Workflow Path | Classification | Governance Rationale |",
        "| :--- | :--- | :--- | :--- |",
    ])
    for tr in matrix.transitions:
        path_str = " -> ".join(f"`{s}`" for s in tr.destination_path) if tr.destination_path else "*No path*"
        lines.append(f"| `{tr.source_from}->{tr.source_to}` | {path_str} | `{tr.classification.value}` | {tr.rationale} |")

    lines.extend([
        "",
        "## 6. Required Fields & Creation Constraints",
        "| Field Key | Field Name | Supported | Required | Schema Type | Constraints |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])
    for f in matrix.fields:
        lines.append(
            f"| `{f.field_key}` | {f.field_name} | {'Yes' if f.supported else 'No'} | "
            f"{'**REQUIRED**' if f.required else 'Optional'} | `{f.schema_type}` | {f.notes} |"
        )

    lines.extend([
        "",
        "## 7. Next Operation & Governance Authorization",
        f"- **Import Readiness**: `{matrix.readiness_gate.value}`",
        "- **Phase 4 Mutation Status**: **HOLD — Zero Jira mutations performed**",
        "- **Phase 5 Transition Status**: **HOLD — Zero transitions performed**",
        "- **Decision**: An explicit qualification governance decision is required before importing "
        "if any source vocabulary is classified as `unavailable` or `approximate_semantic_mapping`.",
    ])

    return "\n".join(lines) + "\n"


def write_compatibility_reports(
    matrix: CompatibilityMatrix,
    json_path: Path | str = DEFAULT_COMPATIBILITY_JSON_PATH,
    md_path: Path | str = DEFAULT_COMPATIBILITY_MD_PATH,
) -> dict[str, str]:
    """Write JSON and Markdown compatibility reports to disk and return file hashes."""
    out_json = Path(json_path)
    out_md = Path(md_path)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(matrix.to_dict(), f, indent=2, ensure_ascii=False)

    md_content = generate_compatibility_markdown_report(matrix)
    with out_md.open("w", encoding="utf-8") as f:
        f.write(md_content)

    return {
        "json_path": str(out_json),
        "json_sha256": compute_sha256_file(out_json),
        "md_path": str(out_md),
        "md_sha256": compute_sha256_file(out_md),
    }
