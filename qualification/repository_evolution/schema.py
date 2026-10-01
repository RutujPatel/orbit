"""Formal data models and validators for RepositoryEvolutionRelationship.

Authority:
    qualification/wave3/phase4c_repository_evolution_schema/repository_evolution_schema.json
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_field_contract.md
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_semantic_contract.md

Note:
    Phase 4E-B integrates the canonical types and validators into
    src/shadow_orbit/evidence_types.py. This qualification module
    re-exports production types while retaining qualification-layer
    JSON Schema verification.
"""

from __future__ import annotations

import json
import os
from typing import Any
import jsonschema

from shadow_orbit.evidence_types import (
    DEFAULT_DIRECTIONALITY,
    DEFAULT_TRANSITIVITY,
    FAMILY_TYPE_MAP,
    REPOSITORY_NAME_PATTERN,
    Directionality,
    RelationshipFamily,
    RelationshipType,
    RepositoryEvolutionRelationship,
    RepositoryProvenanceRef,
    SemanticFirewall,
    TransitivityRule,
    VerificationStatus,
    compute_relationship_id,
    validate_repository_evolution_graph,
    validate_repository_evolution_relationship as _prod_validate_relationship,
    verify_provenance_file_digest,
)

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "wave3",
    "phase4c_repository_evolution_schema",
    "repository_evolution_schema.json",
)

with open(SCHEMA_PATH, "r", encoding="utf-8") as _f:
    JSON_SCHEMA = json.load(_f)


def validate_repository_evolution_relationship(
    rel: RepositoryEvolutionRelationship,
) -> None:
    """Validate RepositoryEvolutionRelationship against formal Phase 4C invariants and JSON schema."""
    _prod_validate_relationship(rel)
    d = rel.to_dict()
    jsonschema.validate(instance=d, schema=JSON_SCHEMA)


__all__ = [
    "DEFAULT_DIRECTIONALITY",
    "DEFAULT_TRANSITIVITY",
    "Directionality",
    "FAMILY_TYPE_MAP",
    "JSON_SCHEMA",
    "RelationshipFamily",
    "RelationshipType",
    "RepositoryEvolutionRelationship",
    "RepositoryProvenanceRef",
    "REPOSITORY_NAME_PATTERN",
    "SemanticFirewall",
    "TransitivityRule",
    "VerificationStatus",
    "compute_relationship_id",
    "validate_repository_evolution_graph",
    "validate_repository_evolution_relationship",
    "verify_provenance_file_digest",
]
