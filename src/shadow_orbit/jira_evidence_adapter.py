"""Additive Jira evidence adapter.

Converts an existing ``NormalizedFixture`` (containing ``WorkItem``
instances produced by the unchanged Jira pipeline) into the common
CSE evidence model without modifying any existing module.

This adapter is a **pure read-only bridge**.  It does NOT call existing
Jira validation, normalization, temporal, or evaluation functions.
It receives an already-normalized ``NormalizedFixture`` and performs
only structural copying / adaptation.

Architecture::

    existing Jira NormalizedFixture
        ↓
    jira_evidence_adapter
        ↓
    ObservationContext
    EvidenceObservation[JiraIssueState]
    bundle-level QualityIssue
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    SourceInstance,
)
from shadow_orbit.types import (
    DataQualityCondition,
    NormalizedFixture,
    WorkItem,
)

# ── Approved lossless quality-condition mappings ─────────────────────

_QUALITY_CODE_MAP: dict[str, str] = {
    "UNKNOWN_STATUS": "unsupported_value",
    "UNKNOWN_PRIORITY": "unsupported_value",
    "PARTIAL_HISTORY": "incomplete",
    "INVALID_OPTIONAL_TIMESTAMP": "invalid",
}
"""Maps existing Jira ``DataQualityCondition.code`` values to CSE
``QualityCode`` literals.  Only explicitly approved lossless mappings
appear here.  Unmapped codes are preserved via the fallback path."""


# ── Internal helpers ─────────────────────────────────────────────────

def _validate_source_instance(source_instance: SourceInstance) -> None:
    """Reject non-Jira source instances."""
    if source_instance.source_kind != "jira":
        raise ValueError(
            f"Jira evidence adapter requires source_kind='jira', "
            f"got {source_instance.source_kind!r}"
        )


def _validate_aware(dt: datetime | None, label: str) -> None:
    """Require timezone-aware datetime when not None."""
    if dt is not None and (dt.tzinfo is None or dt.utcoffset() is None):
        raise ValueError(
            f"{label} must be timezone-aware (has tzinfo with "
            f"non-None utcoffset)."
        )


def _validate_temporal_args(
    starts_at: datetime | None,
    ends_at: datetime | None,
    cutoff: datetime | None,
) -> None:
    """Validate all supplied temporal arguments."""
    _validate_aware(starts_at, "observed_interval_starts_at")
    _validate_aware(ends_at, "observed_interval_ends_at_exclusive")
    _validate_aware(cutoff, "source_cutoff_at")
    if starts_at is not None and ends_at is not None:
        if starts_at >= ends_at:
            raise ValueError(
                "observed_interval_starts_at must be strictly before "
                "observed_interval_ends_at_exclusive."
            )


def _resolve_raw_index(
    key: str,
    raw_items: list[dict[str, Any]],
) -> int:
    """Find the exact-one raw fixture index for *key*.

    Raises ``ValueError`` on zero or multiple matches.
    """
    matches = [
        idx
        for idx, item in enumerate(raw_items)
        if isinstance(item, dict) and item.get("key") == key
    ]
    if len(matches) == 0:
        raise ValueError(
            f"No raw record found for WorkItem key {key!r}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"Multiple raw records found for WorkItem key {key!r}"
        )
    return matches[0]


def _map_quality_condition(
    condition: DataQualityCondition,
    entity_refs_by_key: dict[str, EntityRef],
) -> tuple[QualityIssue, str | None]:
    """Map a single Jira DataQualityCondition to a CSE QualityIssue.

    Returns ``(quality_issue, resolved_key)`` where *resolved_key* is
    the WorkItem key if the condition was attached to an accepted entity,
    or ``None`` if the issue should be bundle-level.
    """
    subject_key = condition.subject_key

    # ── Determine code and message ───────────────────────────────
    cse_code = _QUALITY_CODE_MAP.get(condition.code)
    if cse_code is not None:
        message = condition.message
    else:
        # Unmapped Jira condition — preserve original code in message
        cse_code = "unsupported_value"
        message = (
            f"Unmapped Jira condition {condition.code}: "
            f"{condition.message}"
        )

    # ── Three-way subject resolution ─────────────────────────────
    if subject_key is None:
        # No subject — bundle-level
        return (
            QualityIssue(
                code=cse_code,
                message=message,
                subject_ref=None,
            ),
            None,
        )

    entity_ref = entity_refs_by_key.get(subject_key)
    if entity_ref is not None:
        # Subject matches an accepted WorkItem — per-entity
        return (
            QualityIssue(
                code=cse_code,
                message=message,
                subject_ref=entity_ref,
            ),
            subject_key,
        )

    # Subject key exists but no accepted WorkItem matches — orphan
    return (
        QualityIssue(
            code="unresolved",
            message=(
                f"Quality condition references unknown subject "
                f"{subject_key!r}: [{condition.code}] "
                f"{condition.message}"
            ),
            subject_ref=None,
        ),
        None,
    )


# ── Public API ───────────────────────────────────────────────────────

def adapt_jira_evidence(
    normalized: NormalizedFixture,
    source_instance: SourceInstance,
    observation_id: str,
    fixture_id: str | None = None,
    observed_interval_starts_at: datetime | None = None,
    observed_interval_ends_at_exclusive: datetime | None = None,
    source_cutoff_at: datetime | None = None,
    coverage_note: str | None = None,
) -> tuple[
    ObservationContext,
    tuple[EvidenceObservation, ...],
    tuple[QualityIssue, ...],
]:
    """Convert a Jira ``NormalizedFixture`` into CSE evidence.

    Parameters
    ----------
    normalized:
        The already-normalized Jira fixture.  NOT mutated.
    source_instance:
        Must have ``source_kind="jira"``.
    observation_id:
        Caller-supplied observation identifier.
    fixture_id:
        Optional fixture identifier for provenance.
    observed_interval_starts_at, observed_interval_ends_at_exclusive:
        Optional observation interval.  If both are supplied,
        ``starts_at`` must be strictly before ``ends_at_exclusive``.
        Must be timezone-aware if not None.
    source_cutoff_at:
        Optional source snapshot timestamp.  Must be timezone-aware
        if not None.
    coverage_note:
        Optional structured coverage note.

    Returns
    -------
    tuple of (ObservationContext, observations, bundle_quality_issues)

    Raises
    ------
    ValueError
        If ``source_instance.source_kind`` is not ``"jira"``, if any
        supplied datetime is naive, if the observation interval is
        invalid, or if provenance resolution fails (zero or multiple
        raw matches for a WorkItem key).
    """
    # ── 1. Source instance enforcement ────────────────────────────
    _validate_source_instance(source_instance)

    # ── 2. Temporal validation ───────────────────────────────────
    _validate_temporal_args(
        observed_interval_starts_at,
        observed_interval_ends_at_exclusive,
        source_cutoff_at,
    )

    # ── 3. ObservationContext construction ────────────────────────
    observation_context = ObservationContext(
        observation_id=observation_id,
        source_instance=source_instance,
        observed_interval_starts_at=observed_interval_starts_at,
        observed_interval_ends_at_exclusive=(
            observed_interval_ends_at_exclusive
        ),
        source_cutoff_at=source_cutoff_at,
        coverage_note=coverage_note,
    )

    # ── 4. Build entity refs and provenance ──────────────────────
    raw_items: list[dict[str, Any]] = normalized.raw_document[
        "work_items"
    ]

    entity_refs_by_key: dict[str, EntityRef] = {}
    provenance_by_key: dict[str, ProvenanceRef] = {}

    for work_item in normalized.work_items:
        key = work_item.key

        entity_ref = EntityRef(
            source_instance=source_instance,
            entity_kind="jira_issue",
            entity_id=key,
        )
        entity_refs_by_key[key] = entity_ref

        raw_index = _resolve_raw_index(key, raw_items)
        provenance_by_key[key] = ProvenanceRef(
            source_instance=source_instance,
            observation_id=observation_id,
            fixture_id=fixture_id,
            record_locator=f"work_items[{raw_index}]",
        )

    # ── 5. Quality condition mapping ─────────────────────────────
    per_entity_issues: dict[str, list[QualityIssue]] = {
        wi.key: [] for wi in normalized.work_items
    }
    bundle_issues: list[QualityIssue] = []

    for condition in normalized.data_quality_conditions:
        issue, resolved_key = _map_quality_condition(
            condition, entity_refs_by_key
        )
        if resolved_key is not None:
            per_entity_issues[resolved_key].append(issue)
        else:
            bundle_issues.append(issue)

    # ── 6. Assemble observations ─────────────────────────────────
    observations: list[EvidenceObservation] = []

    for work_item in normalized.work_items:
        key = work_item.key

        state = JiraIssueState(
            key=key,
            source_status=work_item.source_status,
            source_priority=work_item.source_priority,
            status_category=work_item.status_category,
            priority_band=work_item.priority_band,
            assignee=work_item.assignee,
            created_at=work_item.created_at,
            updated_at=work_item.updated_at,
            resolved_at=work_item.resolved_at,
            due_at=work_item.due_at,
        )

        entity_quality = tuple(
            sorted(
                per_entity_issues[key],
                key=lambda q: (q.code, q.message),
            )
        )

        observations.append(
            EvidenceObservation(
                entity_ref=entity_refs_by_key[key],
                observation_context=observation_context,
                observed_state=state,
                quality_issues=entity_quality,
                provenance_refs=(provenance_by_key[key],),
            )
        )

    # ── 7. Deterministic ordering ────────────────────────────────
    sorted_observations = tuple(
        sorted(
            observations,
            key=lambda o: o.entity_ref.entity_id,
        )
    )

    sorted_bundle_issues = tuple(
        sorted(
            bundle_issues,
            key=lambda q: (q.code, q.message),
        )
    )

    return observation_context, sorted_observations, sorted_bundle_issues
