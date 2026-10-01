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

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import Any, Literal, Union

import hashlib
import os
import re

# ── Validated provider and entity identifiers (Pass 5 / Wave 1) ─────────────

SourceKind = str
"""A validated provider identifier representing a source system kind.

Provider identification is validated at the provider/evidence boundary via
validate_source_kind(). Must be a non-empty, lowercase alphanumeric string
(including underscores and hyphens), e.g. 'jira', 'github', 'linear', 'gitlab'.
"""

EntityKind = str
"""A validated entity type identifier representing a domain entity kind.

Validated at the provider/evidence boundary via validate_entity_kind().
Must be a non-empty, lowercase alphanumeric string (including underscores and hyphens),
e.g. 'jira_issue', 'github_pull_request', 'work_item', 'code_change'.
"""

_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_\-]*[a-z0-9]$|^[a-z0-9]$")


def validate_source_kind(value: Any) -> str:
    """Validate a source_kind identifier at the provider/evidence boundary.

    Fails closed on non-string, empty, whitespace, uppercase, length > 64, or invalid characters.
    """
    if not isinstance(value, str):
        raise ValueError(f"source_kind must be a string, got {type(value).__name__}")
    clean = value.strip()
    if not clean:
        raise ValueError("source_kind must not be empty or whitespace")
    if clean != value:
        raise ValueError(
            f"source_kind '{value}' must not have leading or trailing whitespace"
        )
    if len(value) > 64:
        raise ValueError(
            f"source_kind '{value}' exceeds maximum length of 64 characters ({len(value)})"
        )
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"Invalid source_kind '{value}'. Must be lowercase alphanumeric with hyphens/underscores."
        )
    return value


def validate_entity_kind(value: Any) -> str:
    """Validate an entity_kind identifier at the provider/evidence boundary.

    Fails closed on non-string, empty, whitespace, uppercase, length > 64, or invalid characters.
    """
    if not isinstance(value, str):
        raise ValueError(f"entity_kind must be a string, got {type(value).__name__}")
    clean = value.strip()
    if not clean:
        raise ValueError("entity_kind must not be empty or whitespace")
    if clean != value:
        raise ValueError(
            f"entity_kind '{value}' must not have leading or trailing whitespace"
        )
    if len(value) > 64:
        raise ValueError(
            f"entity_kind '{value}' exceeds maximum length of 64 characters ({len(value)})"
        )
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"Invalid entity_kind '{value}'. Must be lowercase alphanumeric with hyphens/underscores."
        )
    return value

QualityCode = Literal[
    "missing",
    "invalid",
    "unsupported_value",
    "contradictory",
    "incomplete",
    "unresolved",
]
"""Structured quality codes.  No severity, confidence, or risk."""

VALID_QUALITY_CODES: frozenset[str] = frozenset({
    "missing",
    "invalid",
    "unsupported_value",
    "contradictory",
    "incomplete",
    "unresolved",
})


def validate_quality_code(value: Any) -> str:
    """Validate that a value is an authorized QualityCode."""
    if not isinstance(value, str):
        raise TypeError(
            f"Quality code must be a str, got {type(value).__name__}: {value!r}"
        )
    if value not in VALID_QUALITY_CODES:
        raise ValueError(
            f"Unknown quality code {value!r}. Must be one of {sorted(VALID_QUALITY_CODES)}."
        )
    return value


RelationshipKind = Literal[
    "belongs_to_repository",
    "review_of",
    "has_head_branch",
    "has_base_branch",
    "contains_commit",
    "has_head_commit",
    "has_base_commit",
    "mentions",
    "explicit_link",
]
"""Closed set of relationship types resolved across CSE-1.5, CSE-1.6, and Milestone 2."""

VALID_RELATIONSHIP_KINDS: frozenset[str] = frozenset({
    "belongs_to_repository",
    "review_of",
    "has_head_branch",
    "has_base_branch",
    "contains_commit",
    "has_head_commit",
    "has_base_commit",
    "mentions",
    "explicit_link",
})


def validate_relationship_kind(value: Any) -> str:
    """Validate that a value is an authorized RelationshipKind."""
    if not isinstance(value, str):
        raise TypeError(
            f"Relationship kind must be a str, got {type(value).__name__}: {value!r}"
        )
    if value not in VALID_RELATIONSHIP_KINDS:
        raise ValueError(
            f"Unknown relationship kind {value!r}. Must be one of {sorted(VALID_RELATIONSHIP_KINDS)}."
        )
    return value


RelationshipBasis = Literal[
    "structural_association",
    "structural_containment",
    "lexical_match",
    "explicit_metadata",
    "declared_mention",
]
"""How a relationship was established. CSE-1.5 uses structural_association.
CSE-1.6 uses lexical_match for explicit textual mentions.
Milestone 2 authorizes explicit_metadata for native integration links.
Wave 5 / Pass 5 recognize declared_mention and structural_containment."""

VALID_RELATIONSHIP_BASES: frozenset[str] = frozenset({
    "structural_association",
    "structural_containment",
    "lexical_match",
    "explicit_metadata",
    "declared_mention",
})


def validate_relationship_basis(value: Any) -> str:
    """Validate that a value is an authorized RelationshipBasis."""
    if not isinstance(value, str):
        raise TypeError(
            f"Relationship basis must be a str, got {type(value).__name__}: {value!r}"
        )
    if value not in VALID_RELATIONSHIP_BASES:
        raise ValueError(
            f"Unknown relationship basis {value!r}. Must be one of {sorted(VALID_RELATIONSHIP_BASES)}."
        )
    return value

CrossSystemStateComparison = Literal[
    "CONSISTENT",
    "CONFLICTING",
    "INSUFFICIENT_EVIDENCE",
]
"""Taxonomy of cross-system state comparisons (ADR-005 D1)."""

CrossSystemTemporalComparison = Literal[
    "COHERENT",
    "INVERTED",
    "INDETERMINATE",
]
"""Taxonomy of cross-system temporal comparisons (ADR-005 D1)."""


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

    def __post_init__(self) -> None:
        validate_source_kind(self.source_kind)
        if not isinstance(self.instance_id, str) or not self.instance_id.strip():
            raise ValueError("instance_id must be a non-empty string")


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

    def __post_init__(self) -> None:
        if not isinstance(self.source_instance, SourceInstance):
            raise TypeError("source_instance must be a SourceInstance")
        validate_entity_kind(self.entity_kind)
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise ValueError("entity_id must be a non-empty string")


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

    def __post_init__(self) -> None:
        validate_quality_code(self.code)


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


# ── Repository Evolution Provenance & Verification ───────────────────────────

@dataclass(frozen=True, slots=True)
class RepositoryProvenanceRef:
    """Provenance reference matching Phase 4C repository_evolution_schema.json."""

    source_instance: SourceInstance
    fixture_id: str
    record_locator: str
    sha256_digest: str
    observation_id: str = "obs-provenance"


def verify_provenance_file_digest(
    prov: RepositoryProvenanceRef | ProvenanceRef,
    base_dir: str = ".",
) -> bool:
    """Cryptographically verify that fixture_id file exists on disk and matches sha256_digest."""
    path = os.path.join(base_dir, prov.fixture_id)
    if not os.path.isfile(path):
        return False
    with open(path, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest()
    expected_sha = getattr(prov, "sha256_digest", None)
    return actual_sha == expected_sha


# ── Repository Evolution Taxonomies ──────────────────────────────────────────

RelationshipFamily = Literal[
    "NAVIGATION_ROUTING",
    "PROJECT_LINEAGE",
    "REPOSITORY_TOPOLOGY",
    "ECOSYSTEM_DEPENDENCY",
]

RelationshipType = Literal[
    "RENAME",
    "NAMESPACE_MOVE",
    "REDIRECT",
    "PREDECESSOR_SUCCESSOR",
    "FORK",
    "MIRROR",
    "VENDOR_MIRROR",
    "EXTERNAL_DEPENDENCY",
    "ECOSYSTEM_PACKAGING",
    "COMPANION_SPECIFICATION",
]

Directionality = Literal[
    "DIRECTED_FORWARD",
    "BIDIRECTIONAL_SYMMETRIC",
]

TransitivityRule = Literal[
    "TRANSITIVE_PERMITTED",
    "STRICTLY_NON_TRANSITIVE",
]

VerificationStatus = Literal[
    "PROVEN",
    "SUPPORTED",
    "PARTIALLY_PROVEN",
    "UNVERIFIED",
]

FAMILY_TYPE_MAP: dict[RelationshipFamily, frozenset[RelationshipType]] = {
    "NAVIGATION_ROUTING": frozenset({"RENAME", "NAMESPACE_MOVE", "REDIRECT"}),
    "PROJECT_LINEAGE": frozenset({"PREDECESSOR_SUCCESSOR"}),
    "REPOSITORY_TOPOLOGY": frozenset({"FORK", "MIRROR", "VENDOR_MIRROR"}),
    "ECOSYSTEM_DEPENDENCY": frozenset({
        "EXTERNAL_DEPENDENCY",
        "ECOSYSTEM_PACKAGING",
        "COMPANION_SPECIFICATION",
    }),
}

DEFAULT_TRANSITIVITY: dict[RelationshipType, TransitivityRule] = {
    "RENAME": "TRANSITIVE_PERMITTED",
    "NAMESPACE_MOVE": "TRANSITIVE_PERMITTED",
    "REDIRECT": "TRANSITIVE_PERMITTED",
    "PREDECESSOR_SUCCESSOR": "TRANSITIVE_PERMITTED",
    "FORK": "STRICTLY_NON_TRANSITIVE",
    "MIRROR": "STRICTLY_NON_TRANSITIVE",
    "VENDOR_MIRROR": "STRICTLY_NON_TRANSITIVE",
    "EXTERNAL_DEPENDENCY": "STRICTLY_NON_TRANSITIVE",
    "ECOSYSTEM_PACKAGING": "STRICTLY_NON_TRANSITIVE",
    "COMPANION_SPECIFICATION": "STRICTLY_NON_TRANSITIVE",
}

DEFAULT_DIRECTIONALITY: dict[RelationshipType, Directionality] = {
    "MIRROR": "BIDIRECTIONAL_SYMMETRIC",
    "RENAME": "DIRECTED_FORWARD",
    "NAMESPACE_MOVE": "DIRECTED_FORWARD",
    "REDIRECT": "DIRECTED_FORWARD",
    "PREDECESSOR_SUCCESSOR": "DIRECTED_FORWARD",
    "FORK": "DIRECTED_FORWARD",
    "VENDOR_MIRROR": "DIRECTED_FORWARD",
    "EXTERNAL_DEPENDENCY": "DIRECTED_FORWARD",
    "ECOSYSTEM_PACKAGING": "DIRECTED_FORWARD",
    "COMPANION_SPECIFICATION": "DIRECTED_FORWARD",
}

REPOSITORY_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")


# ── Deterministic Identifier Derivation ──────────────────────────────────────

def compute_relationship_id(
    instance_id: str,
    relationship_type: str,
    source_repo_id: str,
    target_repo_id: str,
) -> str:
    """Compute deterministic SHA-256 relationship ID per Field 1 derivation rule:

    relationship_id = SHA-256(instance_id | relationship_type | source_repo_id | target_repo_id)
    """
    raw = f"{instance_id}|{relationship_type}|{source_repo_id}|{target_repo_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ── Semantic Firewall Definition ─────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class SemanticFirewall:
    """Architectural assertions ensuring repository evolution remains qualifying-only."""

    entity_ref_mutation_forbidden: bool = True
    linkage_auto_upgrade_forbidden: bool = True
    state_transfer_forbidden: bool = True
    temporal_causality_inference_forbidden: bool = True

    def validate(self) -> None:
        if not (
            self.entity_ref_mutation_forbidden
            and self.linkage_auto_upgrade_forbidden
            and self.state_transfer_forbidden
            and self.temporal_causality_inference_forbidden
        ):
            raise ValueError(
                "All semantic_firewall assertions must strictly be True: "
                "entity_ref_mutation_forbidden, linkage_auto_upgrade_forbidden, "
                "state_transfer_forbidden, and temporal_causality_inference_forbidden."
            )

    def to_dict(self) -> dict[str, bool]:
        return {
            "entity_ref_mutation_forbidden": self.entity_ref_mutation_forbidden,
            "linkage_auto_upgrade_forbidden": self.linkage_auto_upgrade_forbidden,
            "state_transfer_forbidden": self.state_transfer_forbidden,
            "temporal_causality_inference_forbidden": self.temporal_causality_inference_forbidden,
        }


# ── Repository Evolution Relationship Model ──────────────────────────────────

@dataclass(frozen=True, slots=True)
class RepositoryEvolutionRelationship:
    """Formal canonical envelope for repository evolution relationships."""

    relationship_id: str
    relationship_family: RelationshipFamily
    relationship_type: RelationshipType
    source_repository: EntityRef
    target_repository: EntityRef
    directionality: Directionality
    transitivity_rule: TransitivityRule
    verification_status: VerificationStatus
    observed_at: datetime
    provenance_refs: tuple[ProvenanceRef | RepositoryProvenanceRef, ...]
    family_payload: dict[str, Any] = field(default_factory=dict)
    semantic_firewall: SemanticFirewall = field(default_factory=SemanticFirewall)
    valid_from: datetime | None = None
    valid_to: datetime | None = None

    def __post_init__(self) -> None:
        validate_repository_evolution_relationship(self)

    @classmethod
    def create(
        cls,
        relationship_family: RelationshipFamily,
        relationship_type: RelationshipType,
        source_repository: EntityRef,
        target_repository: EntityRef,
        verification_status: VerificationStatus,
        observed_at: datetime,
        provenance_refs: tuple[ProvenanceRef | RepositoryProvenanceRef, ...],
        directionality: Directionality | None = None,
        transitivity_rule: TransitivityRule | None = None,
        family_payload: dict[str, Any] | None = None,
        semantic_firewall: SemanticFirewall | None = None,
        valid_from: datetime | None = None,
        valid_to: datetime | None = None,
    ) -> RepositoryEvolutionRelationship:
        """Construct a RepositoryEvolutionRelationship with auto-computed deterministic ID."""
        rel_id = compute_relationship_id(
            instance_id=source_repository.source_instance.instance_id,
            relationship_type=relationship_type,
            source_repo_id=source_repository.entity_id,
            target_repo_id=target_repository.entity_id,
        )
        return cls(
            relationship_id=rel_id,
            relationship_family=relationship_family,
            relationship_type=relationship_type,
            source_repository=source_repository,
            target_repository=target_repository,
            directionality=directionality or DEFAULT_DIRECTIONALITY[relationship_type],
            transitivity_rule=transitivity_rule or DEFAULT_TRANSITIVITY[relationship_type],
            verification_status=verification_status,
            observed_at=observed_at,
            provenance_refs=provenance_refs,
            family_payload=family_payload or {},
            semantic_firewall=semantic_firewall or SemanticFirewall(),
            valid_from=valid_from,
            valid_to=valid_to,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to canonical JSON-serializable dictionary."""
        d: dict[str, Any] = {
            "relationship_id": self.relationship_id,
            "relationship_family": self.relationship_family,
            "relationship_type": self.relationship_type,
            "source_repository": {
                "source_instance": {
                    "source_kind": self.source_repository.source_instance.source_kind,
                    "instance_id": self.source_repository.source_instance.instance_id,
                },
                "entity_kind": self.source_repository.entity_kind,
                "entity_id": self.source_repository.entity_id,
            },
            "target_repository": {
                "source_instance": {
                    "source_kind": self.target_repository.source_instance.source_kind,
                    "instance_id": self.target_repository.source_instance.instance_id,
                },
                "entity_kind": self.target_repository.entity_kind,
                "entity_id": self.target_repository.entity_id,
            },
            "directionality": self.directionality,
            "transitivity_rule": self.transitivity_rule,
            "verification_status": self.verification_status,
            "observed_at": _serialize_datetime(self.observed_at),
            "valid_from": _serialize_datetime(self.valid_from) if self.valid_from else None,
            "valid_to": _serialize_datetime(self.valid_to) if self.valid_to else None,
            "provenance_refs": [
                {
                    "source_instance": {
                        "source_kind": p.source_instance.source_kind,
                        "instance_id": p.source_instance.instance_id,
                    },
                    "fixture_id": p.fixture_id or "fixture.json",
                    "record_locator": p.record_locator or "root",
                    "sha256_digest": getattr(
                        p,
                        "sha256_digest",
                        "",
                    ),
                }
                for p in self.provenance_refs
            ],
            "family_payload": self.family_payload,
            "semantic_firewall": self.semantic_firewall.to_dict(),
        }
        return d


# ── Canonical Validator ──────────────────────────────────────────────────────

def validate_repository_evolution_relationship(
    rel: RepositoryEvolutionRelationship,
) -> None:
    """Validate RepositoryEvolutionRelationship against all formal Phase 4C invariants."""
    # INV-ID-02: Strict Repository-Kind Endpoints
    if rel.source_repository.entity_kind != "repository":
        raise ValueError(
            f"INV-ID-02 violated: source_repository.entity_kind must be 'repository', "
            f"got {rel.source_repository.entity_kind!r}."
        )
    if rel.target_repository.entity_kind != "repository":
        raise ValueError(
            f"INV-ID-02 violated: target_repository.entity_kind must be 'repository', "
            f"got {rel.target_repository.entity_kind!r}."
        )

    # Repository name format: {owner}/{repo}
    if not REPOSITORY_NAME_PATTERN.match(rel.source_repository.entity_id):
        raise ValueError(
            f"Invalid source_repository entity_id {rel.source_repository.entity_id!r}. "
            f"Must match owner/repository format."
        )
    if not REPOSITORY_NAME_PATTERN.match(rel.target_repository.entity_id):
        raise ValueError(
            f"Invalid target_repository entity_id {rel.target_repository.entity_id!r}. "
            f"Must match owner/repository format."
        )

    # Relationship family and type coherence
    if rel.relationship_family not in FAMILY_TYPE_MAP:
        raise ValueError(f"Unknown relationship_family {rel.relationship_family!r}.")
    if rel.relationship_type not in FAMILY_TYPE_MAP[rel.relationship_family]:
        raise ValueError(
            f"relationship_type {rel.relationship_type!r} is not a member of "
            f"family {rel.relationship_family!r}. Allowed types: "
            f"{sorted(FAMILY_TYPE_MAP[rel.relationship_family])}."
        )

    # Directionality constraints
    if rel.relationship_type == "MIRROR":
        if rel.directionality != "BIDIRECTIONAL_SYMMETRIC":
            raise ValueError(
                "MIRROR relationship must have directionality='BIDIRECTIONAL_SYMMETRIC'."
            )
    else:
        if rel.directionality != "DIRECTED_FORWARD":
            raise ValueError(
                f"{rel.relationship_type} must have directionality='DIRECTED_FORWARD'."
            )

    # INV-ID-04: Deterministic Identifier Check
    expected_id = compute_relationship_id(
        instance_id=rel.source_repository.source_instance.instance_id,
        relationship_type=rel.relationship_type,
        source_repo_id=rel.source_repository.entity_id,
        target_repo_id=rel.target_repository.entity_id,
    )
    if rel.relationship_id != expected_id:
        raise ValueError(
            f"INV-ID-04 violated: relationship_id {rel.relationship_id!r} does not match "
            f"deterministic derivation {expected_id!r}."
        )

    # INV-EV-01: Mandatory Provenance & Authenticity
    if not rel.provenance_refs or len(rel.provenance_refs) == 0:
        raise ValueError("INV-EV-01 violated: provenance_refs must contain at least 1 ProvenanceRef.")

    EMPTY_STRING_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    for p in rel.provenance_refs:
        digest = getattr(p, "sha256_digest", None)
        if digest == EMPTY_STRING_SHA256:
            raise ValueError(
                f"INV-EV-01 violated: Provenance ref {p.fixture_id} has invalid empty-string SHA-256 digest. "
                "Authentic cryptographic provenance is required."
            )

    # Timezone checks
    if rel.observed_at.tzinfo is None or rel.observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware (UTC).")

    if rel.valid_from is not None:
        if rel.valid_from.tzinfo is None or rel.valid_from.utcoffset() is None:
            raise ValueError("valid_from must be timezone-aware (UTC).")
    if rel.valid_to is not None:
        if rel.valid_to.tzinfo is None or rel.valid_to.utcoffset() is None:
            raise ValueError("valid_to must be timezone-aware (UTC).")
    if rel.valid_from is not None and rel.valid_to is not None:
        if rel.valid_from > rel.valid_to:
            raise ValueError(f"valid_from ({rel.valid_from}) must not be after valid_to ({rel.valid_to}).")

    if not isinstance(rel.family_payload, dict):
        raise ValueError("family_payload must be a dictionary.")

    # Semantic Firewall Checks
    rel.semantic_firewall.validate()


# ── Graph Acyclicity Validator ───────────────────────────────────────────────

def validate_repository_evolution_graph(
    relationships: tuple[RepositoryEvolutionRelationship, ...] | list[RepositoryEvolutionRelationship],
) -> None:
    """Validate acyclicity invariants across a collection of relationships:

    - INV-GR-01: PROJECT_LINEAGE must be a DAG (no cycles).
    - INV-GR-02: NAVIGATION_ROUTING must be strictly acyclic (no self-loops or routing cycles).
    """
    # 1. Routing Graph
    routing_adj: dict[str, list[str]] = {}
    for r in relationships:
        if r.relationship_family == "NAVIGATION_ROUTING":
            src = r.source_repository.entity_id
            tgt = r.target_repository.entity_id
            if src == tgt:
                raise ValueError(
                    f"INV-GR-02 violated: Self-referential redirect detected on {src!r}."
                )
            routing_adj.setdefault(src, []).append(tgt)

    _assert_dag(routing_adj, "INV-GR-02: Cycle detected in NAVIGATION_ROUTING graph")

    # 2. Lineage Graph
    lineage_adj: dict[str, list[str]] = {}
    for r in relationships:
        if r.relationship_family == "PROJECT_LINEAGE":
            src = r.source_repository.entity_id
            tgt = r.target_repository.entity_id
            if src == tgt:
                raise ValueError(
                    f"INV-GR-01 violated: Self-referential predecessor detected on {src!r}."
                )
            lineage_adj.setdefault(src, []).append(tgt)

    _assert_dag(lineage_adj, "INV-GR-01: Cycle detected in PROJECT_LINEAGE graph")


def _assert_dag(adj: dict[str, list[str]], error_prefix: str) -> None:
    """Check for cycles using standard 3-color DFS traversal."""
    visited: dict[str, int] = {}  # 0: unvisited, 1: visiting (in stack), 2: visited

    def dfs(node: str, path: list[str]) -> None:
        visited[node] = 1
        for neighbor in adj.get(node, []):
            if visited.get(neighbor, 0) == 1:
                cycle_str = " -> ".join(path + [neighbor])
                raise ValueError(f"{error_prefix}: {cycle_str}")
            if visited.get(neighbor, 0) == 0:
                dfs(neighbor, path + [neighbor])
        visited[node] = 2

    all_nodes = set(adj.keys())
    for targets in adj.values():
        all_nodes.update(targets)

    for n in sorted(all_nodes):
        if visited.get(n, 0) == 0:
            dfs(n, [n])


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


# ── Canonical State Models (Pass 5 / Wave 1) ─────────────────────────

@dataclass(frozen=True, slots=True)
class WorkItemState:
    """Canonical, provider-neutral representation of a tracked work item's observed state.

    Represents a discrete tracked work item across any work tracking system
    (Jira, Linear, GitLab Issues, Azure Work Items, etc.).
    Contains only properties genuinely required by evaluation rules.
    """

    key: str
    source_status: str
    status_category: str
    created_at: datetime
    updated_at: datetime
    source_priority: str = ""
    priority_band: str = "medium"
    assignee: str | None = None
    resolved_at: datetime | None = None
    due_at: datetime | None = None
    extra_properties: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        key: str = "",
        source_status: str = "",
        status_category: str = "",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        source_priority: str = "",
        priority_band: str = "medium",
        assignee: str | None = None,
        resolved_at: datetime | None = None,
        due_at: datetime | None = None,
        extra_properties: dict[str, Any] | None = None,
        *,
        identifier: str | None = None,
    ) -> None:
        eff_key = identifier if identifier is not None else key
        if not eff_key:
            raise ValueError("WorkItemState requires a key or identifier")
        if created_at is None:
            raise ValueError("WorkItemState requires created_at")
        eff_updated = updated_at if updated_at is not None else (resolved_at or created_at)
        object.__setattr__(self, "key", eff_key)
        object.__setattr__(self, "source_status", source_status)
        object.__setattr__(self, "status_category", status_category)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", eff_updated)
        object.__setattr__(self, "source_priority", source_priority)
        object.__setattr__(self, "priority_band", priority_band)
        object.__setattr__(self, "assignee", assignee)
        object.__setattr__(self, "resolved_at", resolved_at)
        object.__setattr__(self, "due_at", due_at)
        object.__setattr__(self, "extra_properties", extra_properties if extra_properties is not None else {})

    @property
    def identifier(self) -> str:
        """Canonical provider-neutral alias for key."""
        return self.key


@dataclass(frozen=True, slots=True)
class CodeChangeState:
    """Canonical, provider-neutral representation of a code change artifact's observed state.

    Represents a proposed or merged code modification across any source control system
    (GitHub Pull Request, GitLab Merge Request, Azure PR, commit, revision, etc.).
    Contains only properties genuinely required by evaluation rules.
    """

    change_type: str
    identifier: str
    state: str
    title: str = ""
    created_at: datetime | None = None
    merged_at: datetime | None = None
    committed_at: datetime | None = None
    author: str | None = None
    source_branch: str | None = None
    target_branch: str | None = None
    head_commit_sha: str | None = None
    base_commit_sha: str | None = None
    extra_properties: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        change_type: str = "pull_request",
        identifier: str | None = None,
        state: str = "open",
        title: str = "",
        created_at: datetime | None = None,
        merged_at: datetime | None = None,
        committed_at: datetime | None = None,
        author: str | None = None,
        source_branch: str | None = None,
        target_branch: str | None = None,
        head_commit_sha: str | None = None,
        base_commit_sha: str | None = None,
        extra_properties: dict[str, Any] | None = None,
        *,
        number: int | str | None = None,
        change_id: str | None = None,
        sha: str | None = None,
        author_login: str | None = None,
    ) -> None:
        eff_id = str(identifier if identifier is not None else (number if number is not None else (change_id if change_id is not None else (sha or ""))))
        eff_author = author if author is not None else author_login
        object.__setattr__(self, "change_type", change_type)
        object.__setattr__(self, "identifier", eff_id)
        object.__setattr__(self, "state", state)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "merged_at", merged_at)
        object.__setattr__(self, "committed_at", committed_at)
        object.__setattr__(self, "author", eff_author)
        object.__setattr__(self, "source_branch", source_branch)
        object.__setattr__(self, "target_branch", target_branch)
        object.__setattr__(self, "head_commit_sha", head_commit_sha)
        object.__setattr__(self, "base_commit_sha", base_commit_sha)
        object.__setattr__(self, "extra_properties", extra_properties if extra_properties is not None else {})

    @property
    def number(self) -> int | None:
        """Backward-compatible integer number accessor for PR-like entities."""
        try:
            return int(self.identifier)
        except (ValueError, TypeError):
            return None

    @property
    def author_login(self) -> str | None:
        """Backward-compatible author_login alias."""
        return self.author

    @property
    def change_id(self) -> str:
        """Alias for identifier."""
        return self.identifier


def as_work_item_state(state: Any) -> WorkItemState | None:
    """Extract or adapt canonical WorkItemState from an observed state payload."""
    if isinstance(state, WorkItemState):
        return state
    if isinstance(state, JiraIssueState):
        return WorkItemState(
            key=state.key,
            source_status=state.source_status,
            source_priority=state.source_priority,
            status_category=state.status_category,
            priority_band=state.priority_band,
            assignee=state.assignee,
            created_at=state.created_at,
            updated_at=state.updated_at,
            resolved_at=state.resolved_at,
            due_at=state.due_at,
        )
    return None


def as_code_change_state(state: Any) -> CodeChangeState | None:
    """Extract or adapt canonical CodeChangeState from an observed state payload."""
    if isinstance(state, CodeChangeState):
        return state
    if isinstance(state, GitHubPullRequestState):
        return CodeChangeState(
            change_type="pull_request",
            identifier=str(state.number),
            state=state.state,
            title=state.title,
            created_at=state.created_at,
            merged_at=state.merged_at,
            committed_at=None,
            author=state.author_login,
            target_branch=state.target_branch,
            source_branch=state.source_branch,
            head_commit_sha=state.head_commit_sha,
            base_commit_sha=state.base_commit_sha,
        )
    if isinstance(state, GitHubCommitState):
        return CodeChangeState(
            change_type="commit",
            identifier=state.sha,
            state="committed",
            title=state.message,
            created_at=state.committed_at,
            committed_at=state.committed_at,
            author=state.author_login,
        )
    return None



ObservedState = Union[
    WorkItemState,
    CodeChangeState,
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

    Assembled by CSE-1.7 from independently produced Jira and GitHub
    evidence.  This is a container of evidence, not an intelligence
    object.  No scoring, severity, confidence, risk, recommendations,
    or semantic inference.

    Determinism: Equivalent input produces equivalent canonical output.
    All collections are immutable tuples.  Serialization uses canonical
    sort orders independent of input ordering.
    """

    bundle_id: str
    bundle_version: str
    observation_contexts: tuple[ObservationContext, ...]
    observations: tuple[EvidenceObservation, ...] = ()
    relationships: tuple[EvidenceRelationship, ...] = ()
    unresolved_references: tuple[UnresolvedReference, ...] = ()
    quality_issues: tuple[QualityIssue, ...] = ()
    cross_system_alignments: tuple[CrossSystemStateAlignment, ...] = ()
    repository_relationships: tuple[RepositoryEvolutionRelationship, ...] = ()


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

    def __post_init__(self) -> None:
        validate_relationship_kind(self.kind)
        validate_relationship_basis(self.basis)


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

    def __post_init__(self) -> None:
        validate_entity_kind(self.target_entity_kind)
        if not isinstance(self.target_identifier, str) or not self.target_identifier.strip():
            raise ValueError("target_identifier must be a non-empty string")


# ── Cross-system state & temporal alignments ─────────────────────────

@dataclass(frozen=True, slots=True)
class CrossSystemStateAlignment:
    """A provider-neutral cross-system state and temporal comparison between two observations.

    Captures state coherence and temporal ordering between a subject entity (e.g. work item)
    and a corroborating entity (e.g. code change, commit, branch) without inferring causality,
    completion, or developer identity.
    """

    subject_ref: EntityRef
    corroborating_ref: EntityRef
    relationship_kind: str
    state_comparison: CrossSystemStateComparison
    temporal_comparison: CrossSystemTemporalComparison
    rationale: str
    provenance_refs: tuple[ProvenanceRef, ...] = ()

    def __init__(
        self,
        subject_ref: EntityRef | None = None,
        corroborating_ref: EntityRef | None = None,
        relationship_kind: str = "",
        state_comparison: CrossSystemStateComparison = "INSUFFICIENT_EVIDENCE",
        temporal_comparison: CrossSystemTemporalComparison = "INDETERMINATE",
        rationale: str = "",
        provenance_refs: tuple[ProvenanceRef, ...] = (),
        *,
        jira_ref: EntityRef | None = None,
        github_ref: EntityRef | None = None,
    ) -> None:
        s = subject_ref if subject_ref is not None else jira_ref
        c = corroborating_ref if corroborating_ref is not None else github_ref
        if s is None or c is None:
            raise ValueError(
                "CrossSystemStateAlignment requires both subject_ref and corroborating_ref (or jira_ref/github_ref)"
            )
        object.__setattr__(self, "subject_ref", s)
        object.__setattr__(self, "corroborating_ref", c)
        object.__setattr__(self, "relationship_kind", relationship_kind)
        object.__setattr__(self, "state_comparison", state_comparison)
        object.__setattr__(self, "temporal_comparison", temporal_comparison)
        object.__setattr__(self, "rationale", rationale)
        object.__setattr__(self, "provenance_refs", provenance_refs)

    @property
    def jira_ref(self) -> EntityRef:
        """Backward-compatible alias for subject_ref."""
        return self.subject_ref

    @property
    def github_ref(self) -> EntityRef:
        """Backward-compatible alias for corroborating_ref."""
        return self.corroborating_ref


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

    Observations, contexts, relationships, unresolved references, and quality
    issues are sorted for deterministic output.
    Empty relationships, unresolved_references, and quality_issues are
    omitted for sparse, backward-compatible output.
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
    sorted_relationships = sorted(
        bundle.relationships,
        key=lambda r: (
            r.kind,
            r.basis,
            r.subject_ref.entity_id,
            r.object_ref.entity_id,
            r.subject_observation_id,
            r.object_observation_id,
        ),
    )
    sorted_unresolved = sorted(
        bundle.unresolved_references,
        key=lambda u: (
            u.relationship_kind,
            u.source_ref.entity_id,
            u.target_entity_kind,
            u.target_identifier,
            u.reason,
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
    if sorted_relationships:
        result["relationships"] = [
            serialize_evidence_relationship(r)
            for r in sorted_relationships
        ]
    if sorted_unresolved:
        result["unresolved_references"] = [
            serialize_unresolved_reference(u)
            for u in sorted_unresolved
        ]
    if sorted_quality:
        result["quality_issues"] = [
            serialize_quality_issue(q)
            for q in sorted_quality
        ]
    if bundle.cross_system_alignments:
        sorted_alignments = sorted(
            bundle.cross_system_alignments,
            key=lambda a: (
                a.subject_ref.entity_id,
                a.corroborating_ref.entity_id,
                a.relationship_kind,
                a.state_comparison,
                a.temporal_comparison,
                a.rationale,
            ),
        )
        result["cross_system_alignments"] = [
            serialize_cross_system_alignment(a)
            for a in sorted_alignments
        ]
    if bundle.repository_relationships:
        sorted_repo_rels = sorted(
            bundle.repository_relationships,
            key=lambda r: (
                r.relationship_family,
                r.relationship_type,
                r.source_repository.entity_id,
                r.target_repository.entity_id,
                r.relationship_id,
            ),
        )
        result["repository_relationships"] = [
            serialize_repository_evolution_relationship(r)
            for r in sorted_repo_rels
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


def serialize_cross_system_alignment(
    alignment: CrossSystemStateAlignment,
) -> dict[str, Any]:
    """Serialize a CrossSystemStateAlignment to a JSON-safe dict.

    Canonical endpoints are serialized as 'subject_ref' and 'corroborating_ref'.
    Legacy 'jira_ref' and 'github_ref' keys are included ONLY for legacy Jira/GitHub
    alignments to satisfy backward-compatible consumers.
    """
    result: dict[str, Any] = {
        "subject_ref": serialize_entity_ref(alignment.subject_ref),
        "corroborating_ref": serialize_entity_ref(alignment.corroborating_ref),
        "relationship_kind": alignment.relationship_kind,
        "state_comparison": alignment.state_comparison,
        "temporal_comparison": alignment.temporal_comparison,
        "rationale": alignment.rationale,
    }
    # Conditional legacy backward compatibility: emit legacy keys only for Jira/GitHub pairs
    if (
        alignment.subject_ref.source_instance.source_kind == "jira"
        and alignment.corroborating_ref.source_instance.source_kind == "github"
    ):
        result["jira_ref"] = serialize_entity_ref(alignment.subject_ref)
        result["github_ref"] = serialize_entity_ref(alignment.corroborating_ref)
    if alignment.provenance_refs:
        result["provenance_refs"] = [
            serialize_provenance_ref(p) for p in alignment.provenance_refs
        ]
    return result


def serialize_repository_evolution_relationship(
    rel: RepositoryEvolutionRelationship,
) -> dict[str, Any]:
    """Serialize a RepositoryEvolutionRelationship to a JSON-safe dict."""
    return rel.to_dict()


def deserialize_repository_evolution_relationship(
    data: dict[str, Any],
) -> RepositoryEvolutionRelationship:
    """Deserialize a dictionary into a validated RepositoryEvolutionRelationship."""
    source_repo_dict = data["source_repository"]
    source_repo = EntityRef(
        source_instance=SourceInstance(
            source_kind=source_repo_dict["source_instance"]["source_kind"],
            instance_id=source_repo_dict["source_instance"]["instance_id"],
        ),
        entity_kind=source_repo_dict["entity_kind"],
        entity_id=source_repo_dict["entity_id"],
    )
    target_repo_dict = data["target_repository"]
    target_repo = EntityRef(
        source_instance=SourceInstance(
            source_kind=target_repo_dict["source_instance"]["source_kind"],
            instance_id=target_repo_dict["source_instance"]["instance_id"],
        ),
        entity_kind=target_repo_dict["entity_kind"],
        entity_id=target_repo_dict["entity_id"],
    )
    prov_refs: list[RepositoryProvenanceRef] = []
    for p in data.get("provenance_refs", []):
        prov_refs.append(
            RepositoryProvenanceRef(
                source_instance=SourceInstance(
                    source_kind=p["source_instance"]["source_kind"],
                    instance_id=p["source_instance"]["instance_id"],
                ),
                fixture_id=p.get("fixture_id", ""),
                record_locator=p.get("record_locator", ""),
                sha256_digest=p.get("sha256_digest", ""),
                observation_id=p.get("observation_id", "obs-provenance"),
            )
        )
    firewall_data = data.get("semantic_firewall", {})
    firewall = SemanticFirewall(
        entity_ref_mutation_forbidden=firewall_data.get("entity_ref_mutation_forbidden", True),
        linkage_auto_upgrade_forbidden=firewall_data.get("linkage_auto_upgrade_forbidden", True),
        state_transfer_forbidden=firewall_data.get("state_transfer_forbidden", True),
        temporal_causality_inference_forbidden=firewall_data.get("temporal_causality_inference_forbidden", True),
    )
    obs_at_str = data["observed_at"]
    if obs_at_str.endswith("Z"):
        obs_at = datetime.fromisoformat(obs_at_str[:-1] + "+00:00")
    else:
        obs_at = datetime.fromisoformat(obs_at_str)

    valid_from: datetime | None = None
    if data.get("valid_from"):
        vf_str = data["valid_from"]
        valid_from = datetime.fromisoformat(vf_str[:-1] + "+00:00" if vf_str.endswith("Z") else vf_str)

    valid_to: datetime | None = None
    if data.get("valid_to"):
        vt_str = data["valid_to"]
        valid_to = datetime.fromisoformat(vt_str[:-1] + "+00:00" if vt_str.endswith("Z") else vt_str)

    return RepositoryEvolutionRelationship(
        relationship_id=data["relationship_id"],
        relationship_family=data["relationship_family"],
        relationship_type=data["relationship_type"],
        source_repository=source_repo,
        target_repository=target_repo,
        directionality=data["directionality"],
        transitivity_rule=data["transitivity_rule"],
        verification_status=data["verification_status"],
        observed_at=obs_at,
        provenance_refs=tuple(prov_refs),
        family_payload=data.get("family_payload", {}),
        semantic_firewall=firewall,
        valid_from=valid_from,
        valid_to=valid_to,
    )
