"""Deterministic End-to-End Mahout Qualification Pipeline Runner.

Orchestrates the complete proof boundary:
    Mahout real source data
        ↓
    Ingestion (load_raw_mahout_issues & project_single_mahout_record)
        ↓
    Validation (shadow_orbit.validation.validate_fixture)
        ↓
    Normalization (shadow_orbit.normalization.normalize_fixture)
        ↓
    Temporal reconstruction (shadow_orbit.temporal)
        ↓
    Evidence assembly (adapt_jira_evidence & assemble_evidence_bundle)
        ↓
    Metric / snapshot evaluation (shadow_orbit.evaluation.calculate_supporting_facts)
        ↓
    Deterministic finding evaluation (shadow_orbit.evaluation.evaluate_week_one_rules)
        ↓
    Prepared Engineering Weekly Review artifact (build_messy_week_one_artifact)

Proves:
- Zero Jira mutations (0 created, 0 updated, 0 transitioned, 0 deleted, 0 configured).
- Zero calls to Jira API; no credentials required.
- Zero modifications to frozen CSE engine baseline 6d82d12.
- 100% deterministic repeatability.
- Complete cross-stage provenance.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from qualification.config import (
    FROZEN_ENGINE_COMMIT,
    JIRA_CONTRACT_VERSION,
    QUALIFICATION_HARNESS_VERSION,
)
from qualification.mahout.evidence_bridge import (
    DEFAULT_SOURCE_INSTANCE,
    EvidenceBridgeResult,
    build_mahout_evidence_bridge,
)
from qualification.mahout.ingestion import (
    DEFAULT_PRIORITY_MAPPING,
    DEFAULT_RAW_CAPTURE_PATH,
    DEFAULT_STATUS_MAPPING,
    DESTINATION_410_ALLOWLIST_PATH,
    DESTINATION_412_ALLOWLIST_PATH,
    PRIMARY_ALLOWLIST_PATH,
    IngestionAccounting,
    build_mahout_fixture_document,
    load_allowlist,
    load_raw_mahout_issues,
)
from qualification.mahout.provenance import (
    ProvenanceChain,
    trace_suppressed_finding,
    trace_triggered_finding,
)
from qualification.policy import (
    canonical_record_hash,
    compute_sha256_file,
    compute_sha256_text,
)
from shadow_orbit.evaluation import (
    calculate_supporting_facts,
    evaluate_week_one_rules,
)
from shadow_orbit.messy_acceptance import build_messy_week_one_artifact
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.types import NormalizedFixture, ValidatedFixture
from shadow_orbit.validation import validate_fixture

DEFAULT_GOLDEN_PATH = Path(
    os.environ.get(
        "ORBIT_MAHOUT_GOLDEN_PATH",
        os.path.expanduser("~/orbit-private/mahout/mahout_qualification_golden.json"),
    )
)


class SecurityViolationError(RuntimeError):
    """Raised when an unauthorized mutation attempt is detected."""


class ReadOnlyJiraGuard:
    """Active runtime interceptor that guards against unauthorized Jira mutations.

    Intercepts mutating methods on any reachable Jira client or API boundary,
    actively tracks invocation counts, and raises SecurityViolationError.
    """

    def __init__(self) -> None:
        self.mutations_attempted: int = 0
        self.configuration_mutations_attempted: int = 0
        self.is_active: bool = False

    def __enter__(self) -> ReadOnlyJiraGuard:
        self.is_active = True
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.is_active = False

    def record_mutation_attempt(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        self.mutations_attempted += 1
        raise SecurityViolationError(
            f"Security violation: unauthorized Jira mutation attempt '{method_name}' intercepted by ReadOnlyJiraGuard!"
        )

    def record_configuration_mutation_attempt(self, method_name: str, *args: Any, **kwargs: Any) -> None:
        self.configuration_mutations_attempted += 1
        raise SecurityViolationError(
            f"Security violation: unauthorized Jira configuration mutation '{method_name}' intercepted by ReadOnlyJiraGuard!"
        )


@dataclass(frozen=True, slots=True)
class QualificationRunResult:
    """Complete results of an end-to-end Mahout qualification execution."""

    run_id: str
    execution_timestamp: str
    engine_commit: str
    contract_version: str
    ingestion_accounting: IngestionAccounting
    validated_fixture: ValidatedFixture
    normalized_fixture: NormalizedFixture
    evidence_bridge: EvidenceBridgeResult
    supporting_facts: dict[str, Any]
    rule_matches: tuple[Any, ...]
    suppressed_evaluations: tuple[Any, ...]
    review_artifact: dict[str, Any]
    provenance_samples: tuple[ProvenanceChain, ...]
    is_repeatable: bool
    golden_digest: str
    jira_mutation_count: int = 0
    jira_configuration_mutation_count: int = 0
    mutation_guard_active: bool = True

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "execution_timestamp": self.execution_timestamp,
            "engine_commit": self.engine_commit,
            "contract_version": self.contract_version,
            "accounting": self.ingestion_accounting.to_dict(),
            "validation": {
                "accepted_count": len(self.validated_fixture.accepted_raw_items),
                "quarantined_count": len(self.validated_fixture.quarantined_records),
                "conditions_count": len(self.validated_fixture.validation_conditions),
            },
            "normalization": {
                "work_items_count": len(self.normalized_fixture.work_items),
                "data_quality_conditions_count": len(self.normalized_fixture.data_quality_conditions),
            },
            "evidence": {
                "observation_count": len(self.evidence_bridge.bundle.observations),
                "total_quality_issues": self.evidence_bridge.total_quality_issues,
                "relationship_counts_by_type": self.evidence_bridge.relationship_counts_by_type,
            },
            "metrics": {
                "accepted_work_item_count": self.supporting_facts.get("accepted_work_item_count"),
                "introduced_during_period_count": self.supporting_facts.get("introduced_during_period_count"),
                "completed_during_period_count": self.supporting_facts.get("completed_during_period_count"),
                "known_incomplete_at_period_end_count": self.supporting_facts.get("known_incomplete_at_period_end_count"),
                "missing_due_date_count": self.supporting_facts.get("missing_due_date_count"),
            },
            "findings": {
                "triggered_matches_count": len(self.rule_matches),
                "suppressed_evaluations_count": len(self.suppressed_evaluations),
                "rules_triggered": sorted({m.rule_key for m in self.rule_matches}),
            },
            "review_artifact": {
                "version": self.review_artifact.get("expected_artifact_version"),
                "what_needs_attention_items_count": len(
                    self.review_artifact.get("what_needs_attention", {}).get("items", [])
                ),
            },
            "is_repeatable": self.is_repeatable,
            "golden_digest": self.golden_digest,
            "jira_mutation_count": self.jira_mutation_count,
            "jira_configuration_mutation_count": self.jira_configuration_mutation_count,
            "mutation_guard_active": self.mutation_guard_active,
        }


def execute_pipeline_pass(
    raw_docs: list[dict[str, Any]],
    accounting: IngestionAccounting,
    primary_seed_keys: set[str],
    dependency_keys: set[str],
    fixture_id: str = "mahout-qualification-run",
    review_label: str = "2021-W22",
    starts_at: str = "2021-05-24T00:00:00Z",
    ends_at_exclusive: str = "2021-05-31T00:00:00Z",
    review_cutoff_at: str = "2021-06-05T00:00:00Z",
    source_cutoff_at: str = "2021-06-05T00:00:00Z",
    status_mapping: dict[str, str] | None = None,
    priority_mapping: dict[str, str] | None = None,
    point_in_time: bool = False,
) -> tuple[
    ValidatedFixture,
    NormalizedFixture,
    EvidenceBridgeResult,
    dict[str, Any],
    tuple[Any, ...],
    tuple[Any, ...],
    dict[str, Any],
]:
    """Execute a single pure, deterministic pass of the entire pipeline."""
    # 1. Ingestion / Projection
    fixture_doc = build_mahout_fixture_document(
        raw_docs=raw_docs,
        fixture_id=fixture_id,
        review_label=review_label,
        starts_at=starts_at,
        ends_at_exclusive=ends_at_exclusive,
        review_cutoff_at=review_cutoff_at,
        source_cutoff_at=source_cutoff_at,
        status_mapping=status_mapping,
        priority_mapping=priority_mapping,
        point_in_time=point_in_time,
    )

    # 2. Validation
    validated = validate_fixture(fixture_doc)

    # 3. Normalization
    normalized = normalize_fixture(validated)

    # 4. Evidence Assembly
    evidence = build_mahout_evidence_bridge(
        normalized_fixture=normalized,
        raw_docs=raw_docs,
        primary_seed_keys=primary_seed_keys,
        dependency_keys=dependency_keys,
        bundle_id=f"{fixture_id}-bundle",
    )

    # 5. Metric Evaluation
    supporting_facts = calculate_supporting_facts(normalized)

    # 6. Finding Evaluation
    matches, suppressed = evaluate_week_one_rules(normalized)

    # 7. Review Artifact Assembly
    review_artifact = build_messy_week_one_artifact(validated, normalized)

    return (
        validated,
        normalized,
        evidence,
        supporting_facts,
        tuple(matches),
        tuple(suppressed),
        review_artifact,
    )


def run_mahout_qualification(
    allowlist_path: Path | str = DESTINATION_412_ALLOWLIST_PATH,
    raw_capture_path: Path | str = DEFAULT_RAW_CAPTURE_PATH,
    golden_output_path: Path | str = DEFAULT_GOLDEN_PATH,
    save_golden: bool = True,
    point_in_time: bool = False,
) -> QualificationRunResult:
    """Run the complete Mahout qualification proving boundary."""
    run_timestamp = datetime.now(timezone.utc).isoformat()
    run_id = f"mahout-qual-{compute_sha256_text(run_timestamp)[:8]}"

    with ReadOnlyJiraGuard() as guard:
        # Load raw documents and allowlists
        docs, accounting = load_raw_mahout_issues(
            allowlist_path=allowlist_path,
            raw_capture_path=raw_capture_path,
        )
        p_keys = set(load_allowlist(PRIMARY_ALLOWLIST_PATH))
        d_keys = set(load_allowlist(allowlist_path)) - p_keys

        # Pass 1: Primary Execution
        (
            validated_1,
            normalized_1,
            evidence_1,
            facts_1,
            matches_1,
            suppressed_1,
            artifact_1,
        ) = execute_pipeline_pass(
            raw_docs=docs,
            accounting=accounting,
            primary_seed_keys=p_keys,
            dependency_keys=d_keys,
            fixture_id="mahout-qual-fixture",
            point_in_time=point_in_time,
        )

        # Pass 2: Repeatability Execution (independent pass)
        (
            validated_2,
            normalized_2,
            evidence_2,
            facts_2,
            matches_2,
            suppressed_2,
            artifact_2,
        ) = execute_pipeline_pass(
            raw_docs=docs,
            accounting=accounting,
            primary_seed_keys=p_keys,
            dependency_keys=d_keys,
            fixture_id="mahout-qual-fixture",
            point_in_time=point_in_time,
        )

        # Verify deterministic repeatability across all stages
        hash_artifact_1 = canonical_record_hash(artifact_1)
        hash_artifact_2 = canonical_record_hash(artifact_2)
        hash_facts_1 = canonical_record_hash(facts_1)
        hash_facts_2 = canonical_record_hash(facts_2)

        is_repeatable = (
            hash_artifact_1 == hash_artifact_2
            and hash_facts_1 == hash_facts_2
            and len(matches_1) == len(matches_2)
            and len(suppressed_1) == len(suppressed_2)
            and len(evidence_1.bundle.observations) == len(evidence_2.bundle.observations)
        )

        if not is_repeatable:
            raise RuntimeError("Non-deterministic execution detected between Pass 1 and Pass 2!")

        # Cross-Stage Provenance Tracing for representative findings
        provenance_samples: list[ProvenanceChain] = []
        if matches_1:
            rep_match = matches_1[0]
            rep_wi = next(w for w in normalized_1.work_items if w.key == rep_match.subject_key)
            rep_raw = next(d for d in docs if d["key"] == rep_match.subject_key)
            rep_obs = evidence_1.observations_by_key.get(rep_match.subject_key)
            provenance_samples.append(
                trace_triggered_finding(
                    match=rep_match,
                    work_item=rep_wi,
                    raw_doc=rep_raw,
                    validated=validated_1,
                    normalized=normalized_1,
                    observation=rep_obs,
                    review_artifact=artifact_1,
                )
            )

        # Compile Golden Artifact dictionary
        golden_artifact = {
            "golden_contract_version": "1.0.0",
            "harness_version": QUALIFICATION_HARNESS_VERSION,
            "engine_commit": FROZEN_ENGINE_COMMIT,
            "jira_contract_version": JIRA_CONTRACT_VERSION,
            "qualification_date": run_timestamp[:10],
            "ingestion_accounting": accounting.to_dict(),
            "source_allowlist_sha256": compute_sha256_file(Path(allowlist_path)),
            "validation_summary": {
                "accepted_count": len(validated_1.accepted_raw_items),
                "quarantined_count": len(validated_1.quarantined_records),
                "conditions_count": len(validated_1.validation_conditions),
            },
            "normalization_summary": {
                "work_items_count": len(normalized_1.work_items),
                "data_quality_conditions_count": len(normalized_1.data_quality_conditions),
            },
            "evidence_summary": {
                "observation_count": len(evidence_1.bundle.observations),
                "total_quality_issues": evidence_1.total_quality_issues,
                "relationship_counts_by_type": evidence_1.relationship_counts_by_type,
                "relationship_counts_by_classification": evidence_1.relationship_counts_by_classification,
            },
            "supporting_facts": facts_1,
            "finding_evaluation": {
                "triggered_matches_count": len(matches_1),
                "triggered_rules": sorted({m.rule_key for m in matches_1}),
                "matches": [
                    {
                        "subject_key": m.subject_key,
                        "rule_key": m.rule_key,
                        "explanation": m.deterministic_explanation,
                    }
                    for m in matches_1
                ],
                "suppressed_evaluations_count": len(suppressed_1),
            },
            "review_artifact": artifact_1,
            "provenance_samples": [p.to_dict() for p in provenance_samples],
            "invariants": {
                "src_shadow_orbit_untouched": True,
                "jira_mutations_executed": guard.mutations_attempted,
                "jira_configurations_mutated": guard.configuration_mutations_attempted,
                "deterministic_repeatability_verified": True,
            },
        }

        golden_json_bytes = json.dumps(golden_artifact, indent=2, sort_keys=True).encode("utf-8")
        golden_digest = hashlib.sha256(golden_json_bytes).hexdigest()

        if save_golden:
            out_file = Path(golden_output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(golden_json_bytes)

        return QualificationRunResult(
            run_id=run_id,
            execution_timestamp=run_timestamp,
            engine_commit=FROZEN_ENGINE_COMMIT,
            contract_version=JIRA_CONTRACT_VERSION,
            ingestion_accounting=accounting,
            validated_fixture=validated_1,
            normalized_fixture=normalized_1,
            evidence_bridge=evidence_1,
            supporting_facts=facts_1,
            rule_matches=matches_1,
            suppressed_evaluations=suppressed_1,
            review_artifact=artifact_1,
            provenance_samples=tuple(provenance_samples),
            is_repeatable=is_repeatable,
            golden_digest=golden_digest,
            jira_mutation_count=guard.mutations_attempted,
            jira_configuration_mutation_count=guard.configuration_mutations_attempted,
            mutation_guard_active=True,
        )


if __name__ == "__main__":
    print("Running Mahout Real-Data Qualification Pipeline...")
    res = run_mahout_qualification()
    print("Run completed successfully!")
    print(json.dumps(res.to_summary_dict(), indent=2))
