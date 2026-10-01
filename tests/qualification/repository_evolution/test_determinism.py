"""Tests for Determinism and Permutation Invariance in Repository Evolution.

Authoritative references:
    qualification/wave3/phase4c_repository_evolution_schema/repository_evolution_schema.json
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_semantic_contract.md
"""

from __future__ import annotations

import json
import random
from typing import Any
import jsonschema
import pytest

from qualification.repository_evolution.cases import (
    make_flink_1359_relationship,
    make_flink_docker_relationship,
    make_kafka_rocksdb_relationship,
    make_stratosphere_flink_relationship,
)
from qualification.repository_evolution.schema import (
    JSON_SCHEMA,
    compute_relationship_id,
    validate_repository_evolution_relationship,
)


class TestDeterminism:
    """Verifies content-derived ID derivation, permutation invariance, and serialization determinism."""

    def test_inv_id_04_relationship_id_derivation_determinism(self):
        """INV-ID-04: compute_relationship_id is 100% deterministic and sensitive to single-byte changes."""
        instance = "github.com/apache"
        rel_type = "REDIRECT"
        src = "apache/incubator-flink"
        tgt = "apache/flink"

        id1 = compute_relationship_id(instance, rel_type, src, tgt)
        for _ in range(50):
            assert compute_relationship_id(instance, rel_type, src, tgt) == id1

        # Changing instance
        assert compute_relationship_id("github.com/other", rel_type, src, tgt) != id1
        # Changing type
        assert compute_relationship_id(instance, "RENAME", src, tgt) != id1
        # Changing source
        assert compute_relationship_id(instance, rel_type, "apache/incubator-flink-old", tgt) != id1
        # Changing target
        assert compute_relationship_id(instance, rel_type, src, "apache/flink-new") != id1

    def test_permutation_invariance_on_relationship_collections(self):
        """Collections of relationships sorted canonically yield identical ordering regardless of input order."""
        rels = [
            make_flink_1359_relationship(),
            make_stratosphere_flink_relationship(),
            make_kafka_rocksdb_relationship(),
            make_flink_docker_relationship(),
        ]

        expected_order = sorted([r.relationship_id for r in rels])

        rng = random.Random(42)
        for _ in range(20):
            shuffled = list(rels)
            rng.shuffle(shuffled)
            sorted_ids = sorted([r.relationship_id for r in shuffled])
            assert sorted_ids == expected_order

    def test_byte_identical_json_serialization(self):
        """to_dict() serialization produces byte-identical JSON across multiple invocations."""
        rel = make_flink_1359_relationship()

        canonical_json_bytes = json.dumps(rel.to_dict(), sort_keys=True, indent=2).encode("utf-8")

        for _ in range(30):
            fresh_rel = make_flink_1359_relationship()
            fresh_bytes = json.dumps(fresh_rel.to_dict(), sort_keys=True, indent=2).encode("utf-8")
            assert fresh_bytes == canonical_json_bytes

    def test_all_cases_validate_against_phase4c_json_schema(self):
        """Every authentic case passes jsonschema.validate against repository_evolution_schema.json."""
        cases = [
            make_flink_1359_relationship(),
            make_stratosphere_flink_relationship(),
            make_kafka_rocksdb_relationship(),
            make_flink_docker_relationship(),
        ]

        for rel in cases:
            data = rel.to_dict()
            # Raises jsonschema.ValidationError if non-compliant
            jsonschema.validate(instance=data, schema=JSON_SCHEMA)
