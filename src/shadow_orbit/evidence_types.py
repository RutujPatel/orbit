"""Common typed evidence foundation for cross-system observations.

This module provides the shared identity, observation, provenance,
quality, and serialization primitives required to represent evidence
from multiple source systems (Jira, GitHub) without modifying the
existing Jira evaluation pipeline.

All types are frozen, slotted dataclasses with immutable tuple
collections, consistent with the existing domain model in types.py.

This module does NOT replace or modify any existing Jira-specific
types.  The existing WorkItem, Change, RuleMatch, SuppressedEvaluation,
and related types remain the authoritative representations for the
Jira evaluation path.

Design reference: docs/cse1-design.md
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from typing import Any, Literal, Union


# ── Closed vocabularies ──────────────────────────────────────────────

SourceKind = Literal["jira", "github"]
"""Supported source system kinds.  Static typing only; runtime
validation of incoming values belongs to source-specific validators."""

EntityKind = Literal[
    "jira_issue",
    "github_repository",
    "github_branch",
    "github_commit",
    "github_pull_request",
    "github_review",
]
"""Closed set of entity types across supported sources."""

QualityCode = Literal[
    "missing",
    "invalid",
    "unsupported_value",
    "contradictory",
    "incomplete",
    "unresolved",
]
"""Structured quality codes.  No severity, confidence, or risk."""

RelationshipKind = Literal[
    "belongs_to_repository",
    "review_of",
    "has_head_branch",
    "has_base_branch",
    "contains_commit",
    "has_head_commit",
    "has_base_commit",
]
"""Closed set of structural relationship types resolved in CSE-1.5."""

RelationshipBasis = Literal["structural_association"]
"""How a relationship was established.  CSE-1.5 uses only
structural_association.  No temporal, semantic, or inference bases."""


# ── Identity ─────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SourceInstance:
    """A specific source-system deployment (e.g. a Jira site, a GitHub org).

    Two SourceInstances with the same source_kind but different
    instance_id represent distinct deployments whose entity IDs
    must not be compared directly.
    """

    source_kind: SourceKind
    instance_id: str


@dataclass(frozen=True, slots=True)
class EntityRef:
    """Canonical identity for an entity across systems.

    EntityRef.entity_kind is the sole authority for an entity's type.
    No other field duplicates this.

    Identity scoping examples:
        Jira issue    →  entity_id = "PLAT-104"
        GitHub PR 42  →  entity_id = "repo-id/42"
        GitHub branch →  entity_id = "repo-id/main"

    Two EntityRefs are equal iff all three fields are equal.
    """

    source_instance: SourceInstance
    entity_kind: EntityKind
    entity_id: str


@dataclass(frozen=True, slots=True)
class SourceFieldRef:
    """Locates a specific field within a source record.

    Used for relationship provenance: "which field in which entity
    supplied this value?"
    """

    entity_ref: EntityRef
    field_path: str


# ── Observation ──────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ObservationContext:
    """Identifies and describes a single observation of a source system.

    Temporal semantics — three intentionally distinct concepts:

        observed_interval_starts_at / observed_interval_ends_at_exclusive
            The half-open time window [start, end) that this observation
            covers in the source system.  Optional: not all sources
            provide clean intervals.

        source_cutoff_at
            The point at which source data was snapped for this
            observation.  Distinct from the interval: the cutoff is
            *when we captured the snapshot*, not the boundary of what
            events the source system considers included.

    Coverage:
        coverage_note
            Structured note describing known incompleteness, e.g.
            "pagination_complete: true, reviews: partial".  Future
            evaluation stages use this to distinguish "not observed"
            from "observed as absent".
    """

    observation_id: str
    source_instance: SourceInstance
    observed_interval_starts_at: datetime | None = None
    observed_interval_ends_at_exclusive: datetime | None = None
    source_cutoff_at: datetime | None = None
    coverage_note: str | None = None


# ── Quality ──────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class QualityIssue:
    """A structured quality observation.

    Quality issues can apply to entities, observations, collections,
    documents, relationships, or fields:

        subject_ref   — the specific entity, when applicable.
        subject_scope — a descriptive scope for non-entity subjects,
                        e.g. "observation:obs-1",
                             "collection:pull_requests",
                             "document:fixture-123".

    Both may be None (global quality issue), both may be present
    (entity-specific issue with scope context), or either alone.
    """

    code: QualityCode
    message: str
    subject_ref: EntityRef | None = None
    subject_scope: str | None = None


# ── Provenance ───────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ProvenanceRef:
    """Structured provenance linking an observation to its source record.

    Supports explicit fixture-local positioning via record_locator
    (e.g. "work_items[3]") and specific field attribution via
    source_field_path (e.g. "status").
    """

    source_instance: SourceInstance
    observation_id: str
    fixture_id: str | None = None
    record_locator: str | None = None
    source_field_path: str | None = None


@dataclass(frozen=True, slots=True)
class DerivationRef:
    """Structured provenance for artifacts produced by transformation.

    Not wired in the current stage; exists for future cross-system
    evaluation steps.
    """

    transformation_id: str
    transformation_version: str
    source_refs: tuple[ProvenanceRef, ...]


# ── Typed payloads ───────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class JiraIssueState:
    """Evidence-layer representation of a Jira issue's observed state.

    This is NOT the evaluation-path WorkItem.  The existing Jira
    evaluation pipeline continues to use WorkItem unchanged.  This
    type exists for the common evidence layer only.
    """

    key: str
    source_status: str
    source_priority: str
    status_category: str
    priority_band: str
    assignee: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    due_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class GitHubRepositoryState:
    """Evidence-layer stub for a GitHub repository's observed state.

    Fields will be populated in CSE-1.3.
    """

    owner: str
    name: str
    default_branch: str | None = None


@dataclass(frozen=True, slots=True)
class GitHubBranchState:
    """Evidence-layer stub for a GitHub branch's observed state.

    Fields will be populated in CSE-1.3.
    """

    name: str
    head_commit_id: str | None = None


@dataclass(frozen=True, slots=True)
class GitHubCommitState:
    """Evidence-layer stub for a GitHub commit's observed state.

    Fields will be populated in CSE-1.3.
    """

    sha: str
    message: str
    author_login: str | None = None
    committed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class GitHubPullRequestState:
    """Evidence-layer representation of a GitHub pull request's observed state.

    CSE-1.3 core fields + CSE-1.5 structural association fields.

    Fork-aware scoping:
        head_repository_id identifies the repository that owns the
        source/head branch.  When absent, the head branch's repository
        scope is unknown and has_head_branch produces an unresolved
        reference rather than assuming the host repository.
    """

    number: int
    title: str
    state: str
    author_login: str | None = None
    created_at: datetime | None = None
    merged_at: datetime | None = None
    target_branch: str | None = None
    source_branch: str | None = None
    head_commit_sha: str | None = None
    base_commit_sha: str | None = None
    head_repository_id: str | None = None
    is_fork: bool | None = None
    pull_request_commit_shas: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GitHubReviewState:
    """Evidence-layer stub for a GitHub review's observed state.

    Fields will be populated in CSE-1.3.
    """

    review_id: str
    state: str
    reviewer_login: str | None = None
    submitted_at: datetime | None = None


ObservedState = Union[
    JiraIssueState,
    GitHubRepositoryState,
    GitHubBranchState,
    GitHubCommitState,
    GitHubPullRequestState,
    GitHubReviewState,
]
"""Typed union of all supported payload types."""


# ── Evidence observation ─────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class EvidenceObservation:
    """One entity's observed state inside one observation.

    entity_ref.entity_kind is the sole authority for the entity's type.
    No separate observed_kind field exists.
    """

    entity_ref: EntityRef
    observation_context: ObservationContext
    observed_state: ObservedState
    quality_issues: tuple[QualityIssue, ...] = ()
    provenance_refs: tuple[ProvenanceRef, ...] = ()


# ── Evidence bundle ──────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    """Top-level container for cross-system evidence.

    Not fully wired until CSE-1.7.  The type exists as the structural
    target so that intermediate stages can build toward it.
    """

    bundle_id: str
    bundle_version: str
    observation_contexts: tuple[ObservationContext, ...]
    observations: tuple[EvidenceObservation, ...] = ()
    quality_issues: tuple[QualityIssue, ...] = ()


# ── Structural relationships ─────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class EvidenceRelationship:
    """A resolved structural relationship between two observed entities.

    Both subject and object must have accepted EvidenceObservation
    instances.  The observation IDs explicitly identify the observation
    evidence supporting each endpoint.

    Every relationship has supporting provenance identifying the source
    record/field or structural nesting that established the edge.
    """

    subject_ref: EntityRef
    object_ref: EntityRef
    kind: RelationshipKind
    basis: RelationshipBasis
    subject_observation_id: str
    object_observation_id: str
    provenance_refs: tuple[ProvenanceRef, ...]
    quality_issues: tuple[QualityIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class UnresolvedReference:
    """Evidence that a structural reference could not be resolved.

    Emitted when a source record references an entity that has no
    corresponding accepted EvidenceObservation (missing from fixture,
    quarantined, or ambiguous).

    This does NOT claim the entity does not exist in the source system.
    It records that the entity was not observed in the current fixture.
    """

    source_ref: EntityRef
    source_observation_id: str
    target_entity_kind: str
    target_identifier: str
    relationship_kind: RelationshipKind
    reason: str
    provenance_refs: tuple[ProvenanceRef, ...]


# ── Serialization ────────────────────────────────────────────────────

def _serialize_datetime(dt: datetime) -> str:
    """Serialize a timezone-aware datetime to canonical UTC ISO 8601.

    Naive datetimes are programming errors, not data quality issues.
    Timezone-equivalent inputs produce identical output.
    No system clock is accessed.
    """
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(
            "Cannot serialize a naive datetime; "
            "timezone information is required."
        )
    utc = dt.astimezone(timezone.utc)
    return utc.isoformat().replace("+00:00", "Z")


def serialize_source_instance(
    instance: SourceInstance,
) -> dict[str, str]:
    """Serialize a SourceInstance to a JSON-safe dict."""
    return {
        "source_kind": instance.source_kind,
        "instance_id": instance.instance_id,
    }


def serialize_entity_ref(ref: EntityRef) -> dict[str, Any]:
    """Serialize an EntityRef to a JSON-safe dict."""
    return {
        "source_instance": serialize_source_instance(
            ref.source_instance
        ),
        "entity_kind": ref.entity_kind,
        "entity_id": ref.entity_id,
    }


def serialize_observation_context(
    ctx: ObservationContext,
) -> dict[str, Any]:
    """Serialize an ObservationContext to a JSON-safe dict.

    Optional temporal fields are included only when present.
    """
    result: dict[str, Any] = {
        "observation_id": ctx.observation_id,
        "source_instance": serialize_source_instance(
            ctx.source_instance
        ),
    }
    if ctx.observed_interval_starts_at is not None:
        result["observed_interval_starts_at"] = _serialize_datetime(
            ctx.observed_interval_starts_at
        )
    if ctx.observed_interval_ends_at_exclusive is not None:
        result[
            "observed_interval_ends_at_exclusive"
        ] = _serialize_datetime(
            ctx.observed_interval_ends_at_exclusive
        )
    if ctx.source_cutoff_at is not None:
        result["source_cutoff_at"] = _serialize_datetime(
            ctx.source_cutoff_at
        )
    if ctx.coverage_note is not None:
        result["coverage_note"] = ctx.coverage_note
    return result


def serialize_quality_issue(
    issue: QualityIssue,
) -> dict[str, Any]:
    """Serialize a QualityIssue to a JSON-safe dict."""
    result: dict[str, Any] = {
        "code": issue.code,
        "message": issue.message,
    }
    if issue.subject_ref is not None:
        result["subject_ref"] = serialize_entity_ref(
            issue.subject_ref
        )
    if issue.subject_scope is not None:
        result["subject_scope"] = issue.subject_scope
    return result


def serialize_provenance_ref(
    ref: ProvenanceRef,
) -> dict[str, Any]:
    """Serialize a ProvenanceRef to a JSON-safe dict."""
    result: dict[str, Any] = {
        "source_instance": serialize_source_instance(
            ref.source_instance
        ),
        "observation_id": ref.observation_id,
    }
    if ref.fixture_id is not None:
        result["fixture_id"] = ref.fixture_id
    if ref.record_locator is not None:
        result["record_locator"] = ref.record_locator
    if ref.source_field_path is not None:
        result["source_field_path"] = ref.source_field_path
    return result


def _serialize_observed_state(
    state: ObservedState,
) -> dict[str, Any]:
    """Serialize a typed payload to a JSON-safe dict.

    Includes a _type discriminator for round-trip identification.
    All fields are emitted (None values become JSON null) to ensure
    deterministic output regardless of field presence.
    """
    result: dict[str, Any] = {"_type": type(state).__name__}
    for f in fields(state):
        value = getattr(state, f.name)
        if isinstance(value, datetime):
            result[f.name] = _serialize_datetime(value)
        else:
            result[f.name] = value
    return result


def serialize_evidence_observation(
    obs: EvidenceObservation,
) -> dict[str, Any]:
    """Serialize an EvidenceObservation to a JSON-safe dict."""
    result: dict[str, Any] = {
        "entity_ref": serialize_entity_ref(obs.entity_ref),
        "observation_context_id": (
            obs.observation_context.observation_id
        ),
        "observed_state": _serialize_observed_state(
            obs.observed_state
        ),
    }
    if obs.quality_issues:
        result["quality_issues"] = [
            serialize_quality_issue(q)
            for q in obs.quality_issues
        ]
    if obs.provenance_refs:
        result["provenance_refs"] = [
            serialize_provenance_ref(p)
            for p in obs.provenance_refs
        ]
    return result


def serialize_evidence_bundle(
    bundle: EvidenceBundle,
) -> dict[str, Any]:
    """Serialize an EvidenceBundle to a deterministic JSON-safe dict.

    Observations and contexts are sorted for deterministic output.
    No system-clock-generated fields are included.
    """
    sorted_contexts = sorted(
        bundle.observation_contexts,
        key=lambda c: (
            c.source_instance.instance_id,
            c.observation_id,
        ),
    )
    sorted_observations = sorted(
        bundle.observations,
        key=lambda o: (
            o.entity_ref.source_instance.instance_id,
            o.entity_ref.entity_kind,
            o.entity_ref.entity_id,
        ),
    )
    sorted_quality = sorted(
        bundle.quality_issues,
        key=lambda q: (q.code, q.message),
    )
    result: dict[str, Any] = {
        "bundle_id": bundle.bundle_id,
        "bundle_version": bundle.bundle_version,
        "observation_contexts": [
            serialize_observation_context(c)
            for c in sorted_contexts
        ],
        "observations": [
            serialize_evidence_observation(o)
            for o in sorted_observations
        ],
    }
    if sorted_quality:
        result["quality_issues"] = [
            serialize_quality_issue(q)
            for q in sorted_quality
        ]
    return result


def serialize_evidence_relationship(
    rel: EvidenceRelationship,
) -> dict[str, Any]:
    """Serialize an EvidenceRelationship to a JSON-safe dict."""
    result: dict[str, Any] = {
        "subject_ref": serialize_entity_ref(rel.subject_ref),
        "object_ref": serialize_entity_ref(rel.object_ref),
        "kind": rel.kind,
        "basis": rel.basis,
        "subject_observation_id": rel.subject_observation_id,
        "object_observation_id": rel.object_observation_id,
        "provenance_refs": [
            serialize_provenance_ref(p) for p in rel.provenance_refs
        ],
    }
    if rel.quality_issues:
        result["quality_issues"] = [
            serialize_quality_issue(q) for q in rel.quality_issues
        ]
    return result


def serialize_unresolved_reference(
    unres: UnresolvedReference,
) -> dict[str, Any]:
    """Serialize an UnresolvedReference to a JSON-safe dict."""
    return {
        "source_ref": serialize_entity_ref(unres.source_ref),
        "source_observation_id": unres.source_observation_id,
        "target_entity_kind": unres.target_entity_kind,
        "target_identifier": unres.target_identifier,
        "relationship_kind": unres.relationship_kind,
        "reason": unres.reason,
        "provenance_refs": [
            serialize_provenance_ref(p) for p in unres.provenance_refs
        ],
    }
