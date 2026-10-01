"""Cross-Stage Provenance Tracer for Mahout Qualification.

Constructs explicit, auditable, explainable trace chains linking:
    Raw Mahout Observation (MongoDB BSON / Raw JSON Capture)
        ↓
    Validated Source Record (Fixture Validator)
        ↓
    Normalized WorkItem / EvidenceObservation (Normalization Engine)
        ↓
    Temporal Fact (Temporal Reconstruction)
        ↓
    Metric Snapshot (Supporting Facts Calculation)
        ↓
    Finding Evaluation (Deterministic Finding Engine)
        ↓
    Finding (RuleMatch / SuppressedEvaluation)
        ↓
    Prepared Review Artifact (Engineering Weekly Review)

Also produces explicit explanations for WHY a finding was triggered,
and WHY a finding was suppressed when evidence was incomplete or unmapped.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from qualification.policy import canonical_record_hash
from shadow_orbit.evidence_types import EvidenceObservation, JiraIssueState
from shadow_orbit.types import (
    NormalizedFixture,
    RuleMatch,
    SuppressedEvaluation,
    ValidatedFixture,
    WorkItem,
)


@dataclass(frozen=True, slots=True)
class ProvenanceStep:
    """An individual stage in the cross-system derivation pipeline."""

    stage_name: str
    stage_identifier: str
    description: str
    attributes: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "stage_identifier": self.stage_identifier,
            "description": self.description,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class ProvenanceChain:
    """Complete traceable lineage from raw observation to review artifact."""

    trace_id: str
    target_entity_key: str
    target_concept: str  # 'triggered_finding', 'suppressed_finding', 'metric_fact'
    verdict: str  # 'TRIGGERED', 'SUPPRESSED', 'EVALUATED'
    rule_or_metric_key: str
    steps: tuple[ProvenanceStep, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "target_entity_key": self.target_entity_key,
            "target_concept": self.target_concept,
            "verdict": self.verdict,
            "rule_or_metric_key": self.rule_or_metric_key,
            "steps": [s.to_dict() for s in self.steps],
        }


def trace_triggered_finding(
    match: RuleMatch,
    work_item: WorkItem,
    raw_doc: dict[str, Any],
    validated: ValidatedFixture,
    normalized: NormalizedFixture,
    observation: EvidenceObservation[JiraIssueState] | None,
    review_artifact: dict[str, Any] | None = None,
) -> ProvenanceChain:
    """Trace a triggered finding back through every stage to the raw Mahout document."""
    key = match.subject_key
    raw_fields = raw_doc.get("fields", {}) or {}

    # Stage 1: Raw Mahout observation
    raw_hash = canonical_record_hash(raw_doc)
    step1 = ProvenanceStep(
        stage_name="raw_mahout_observation",
        stage_identifier=f"mongodb:JiraReposAnon.Apache:{key}",
        description="Raw Apache Mahout Jira issue extracted from public dataset.",
        attributes={
            "key": key,
            "source_id": str(raw_doc.get("id")),
            "content_hash": raw_hash,
            "raw_status": (raw_fields.get("status") or {}).get("name"),
            "raw_priority": (raw_fields.get("priority") or {}).get("name"),
            "raw_created": raw_fields.get("created"),
            "raw_updated": raw_fields.get("updated"),
            "raw_changelog_count": len((raw_doc.get("changelog") or {}).get("histories", [])),
        },
    )

    # Stage 2: Validated source record
    raw_items = validated.raw_document.get("work_items", [])
    raw_index = next((i for i, it in enumerate(raw_items) if it.get("key") == key), -1)
    step2 = ProvenanceStep(
        stage_name="validated_source_record",
        stage_identifier=f"fixture:work_items[{raw_index}]",
        description="Source record validated against shadow-jira-fixture-v1 schema.",
        attributes={
            "quarantine_status": "accepted",
            "record_locator": f"work_items[{raw_index}]",
            "has_validation_conditions": any(c.subject_key == key for c in validated.validation_conditions),
        },
    )

    # Stage 3: Normalized WorkItem / EvidenceObservation
    step3 = ProvenanceStep(
        stage_name="normalized_evidence",
        stage_identifier=f"evidence:jira_issue:{key}",
        description="WorkItem normalized into canonical categories and adapted to EvidenceObservation.",
        attributes={
            "status_category": work_item.status_category,
            "priority_band": work_item.priority_band,
            "history_complete": work_item.history_complete,
            "change_events_count": len(work_item.changes),
            "evidence_observation_id": (
                observation.observation_context.observation_id if observation else None
            ),
            "quality_issues": [q.code for q in observation.quality_issues] if observation else [],
        },
    )

    # Stage 4: Temporal fact
    latest_status_change = None
    if work_item.changes:
        status_changes = [c.changed_at for c in work_item.changes if c.field == "status"]
        if status_changes:
            latest_status_change = max(status_changes).isoformat()

    step4 = ProvenanceStep(
        stage_name="temporal_fact",
        stage_identifier=f"temporal:{key}",
        description="Temporal reconstruction of status lifecycle and duration.",
        attributes={
            "last_meaningful_status_change": latest_status_change,
            "review_cutoff_at": normalized.review_period.review_cutoff_at.isoformat(),
            "period_label": normalized.review_period.label,
        },
    )

    # Stage 5: Finding evaluation
    step5 = ProvenanceStep(
        stage_name="finding_evaluation",
        stage_identifier=f"rule:{match.rule_key}:v{match.rule_version}",
        description="Deterministic evaluation of rule condition against normalized facts.",
        attributes={
            "rule_key": match.rule_key,
            "rule_version": match.rule_version,
            "calculation": match.calculation,
            "observed": match.observed,
            "threshold": match.threshold,
            "deterministic_explanation": match.deterministic_explanation,
            "evidence_references": list(match.evidence_references),
        },
    )

    # Stage 6: Review artifact projection
    artifact_section = "what_needs_attention"
    step6 = ProvenanceStep(
        stage_name="review_artifact",
        stage_identifier=f"artifact:{artifact_section}:{key}",
        description="Prepared Engineering Weekly Review section presenting the finding.",
        attributes={
            "artifact_section": artifact_section,
            "presented_subject": key,
            "rule_key": match.rule_key,
        },
    )

    return ProvenanceChain(
        trace_id=f"trace:{key}:{match.rule_key}",
        target_entity_key=key,
        target_concept="triggered_finding",
        verdict="TRIGGERED",
        rule_or_metric_key=match.rule_key,
        steps=(step1, step2, step3, step4, step5, step6),
    )


def trace_suppressed_finding(
    suppressed: SuppressedEvaluation,
    work_item: WorkItem,
    raw_doc: dict[str, Any],
    validated: ValidatedFixture,
    normalized: NormalizedFixture,
    observation: EvidenceObservation[JiraIssueState] | None,
) -> ProvenanceChain:
    """Trace why a finding was suppressed when data was incomplete or unmapped."""
    key = suppressed.subject_key
    raw_fields = raw_doc.get("fields", {}) or {}

    step1 = ProvenanceStep(
        stage_name="raw_mahout_observation",
        stage_identifier=f"mongodb:JiraReposAnon.Apache:{key}",
        description="Raw Apache Mahout Jira issue extracted from public dataset.",
        attributes={
            "key": key,
            "raw_status": (raw_fields.get("status") or {}).get("name"),
            "raw_due": raw_fields.get("duedate"),
            "raw_priority": (raw_fields.get("priority") or {}).get("name"),
        },
    )

    step2 = ProvenanceStep(
        stage_name="normalized_evidence",
        stage_identifier=f"evidence:jira_issue:{key}",
        description="WorkItem normalized with explicit data quality conditions.",
        attributes={
            "status_category": work_item.status_category,
            "priority_band": work_item.priority_band,
            "due_at": work_item.due_at.isoformat() if work_item.due_at else None,
            "conditions": [
                c.code for c in normalized.data_quality_conditions if c.subject_key == key
            ],
            "quality_issues": [q.code for q in observation.quality_issues] if observation else [],
        },
    )

    step3 = ProvenanceStep(
        stage_name="finding_evaluation",
        stage_identifier=f"rule:{suppressed.rule_key}:suppression",
        description="Evaluator detected insufficient/unmapped evidence and suppressed finding.",
        attributes={
            "rule_key": suppressed.rule_key,
            "suppression_reason": suppressed.reason,
            "disposition": "suppressed_due_to_unmapped_or_incomplete_evidence",
        },
    )

    step4 = ProvenanceStep(
        stage_name="review_artifact",
        stage_identifier=f"artifact:what_orbit_could_not_determine:{key}",
        description="Suppression disclosed honestly in review artifact limitation section.",
        attributes={
            "artifact_section": "what_orbit_could_not_determine",
            "disclosed_subject": key,
            "reason": suppressed.reason,
        },
    )

    return ProvenanceChain(
        trace_id=f"trace:{key}:{suppressed.rule_key}:suppressed",
        target_entity_key=key,
        target_concept="suppressed_finding",
        verdict="SUPPRESSED",
        rule_or_metric_key=suppressed.rule_key,
        steps=(step1, step2, step3, step4),
    )
