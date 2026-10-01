"""Formal data models and validators for RepositoryEvolutionRelationship.

Authority:
    qualification/wave3/phase4c_repository_evolution_schema/repository_evolution_schema.json
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_field_contract.md
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_semantic_contract.md
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
import jsonschema

from shadow_orbit.evidence_types import EntityRef, ProvenanceRef, SourceInstance


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

# ── Closed Taxonomies ────────────────────────────────────────────────────────

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

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "wave3",
    "phase4c_repository_evolution_schema",
    "repository_evolution_schema.json",
)

with open(SCHEMA_PATH, "r", encoding="utf-8") as _f:
    JSON_SCHEMA = json.load(_f)


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
            "observed_at": self.observed_at.isoformat().replace("+00:00", "Z"),
            "valid_from": self.valid_from.isoformat().replace("+00:00", "Z") if self.valid_from else None,
            "valid_to": self.valid_to.isoformat().replace("+00:00", "Z") if self.valid_to else None,
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
                        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
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
    if rel.observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware (UTC).")

    # Semantic Firewall Checks
    rel.semantic_firewall.validate()

    # JSON Schema Validation
    d = rel.to_dict()
    jsonschema.validate(instance=d, schema=JSON_SCHEMA)


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
