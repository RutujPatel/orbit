"""Tests for the Four Authentic Empirical Cases in Phase 4D.

Authoritative references:
    qualification/wave3/phase4b_repository_identity/repository_identity_cases.json
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_semantic_contract.md
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    EvidenceRelationship,
    ProvenanceRef,
)
from qualification.repository_evolution.cases import (
    DOCKER_SOURCE,
    GH_SOURCE,
    JIRA_SOURCE,
    ROCKSDB_SOURCE,
    STRATOSPHERE_SOURCE,
    make_flink_1359_observations,
    make_flink_1359_relationship,
    make_flink_20650_observations,
    make_flink_docker_relationship,
    make_kafka_9168_observations,
    make_kafka_rocksdb_relationship,
    make_numeric_collision_observations,
    make_stratosphere_flink_relationship,
)
from qualification.repository_evolution.firewall import (
    assert_entity_ref_immutability,
    assert_linkage_firewall,
    assert_state_firewall,
    assert_temporal_firewall,
)
from qualification.repository_evolution.schema import (
    validate_repository_evolution_graph,
    validate_repository_evolution_relationship,
)


class TestAuthenticCases:
    """Verifies all four authentic empirical cases against the qualification suite."""

    def test_case_a_flink_1359_navigation_routing(self):
        """Case A: FLINK-1359 - Redirect / Navigation Routing."""
        rel = make_flink_1359_relationship()
        jira_obs, gh_obs = make_flink_1359_observations()

        # 1. Schema validation
        validate_repository_evolution_relationship(rel)
        assert rel.relationship_family == "NAVIGATION_ROUTING"
        assert rel.relationship_type == "REDIRECT"
        assert rel.directionality == "DIRECTED_FORWARD"
        assert rel.transitivity_rule == "TRANSITIVE_PERMITTED"
        assert rel.verification_status == "PROVEN"

        # 2. EntityRef Immutability
        orig_refs = {
            jira_obs.observation_context.observation_id: jira_obs.entity_ref,
            gh_obs.observation_context.observation_id: gh_obs.entity_ref,
        }
        assert_entity_ref_immutability((jira_obs, gh_obs), orig_refs, (rel,))
        assert jira_obs.entity_ref.entity_id == "FLINK-1359"
        assert gh_obs.entity_ref.entity_id == "apache/flink/254"

        # 3. Linkage Firewall
        mention_rel = EvidenceRelationship(
            subject_ref=jira_obs.entity_ref,
            object_ref=gh_obs.entity_ref,
            kind="mentions",
            basis="lexical_match",
            subject_observation_id=jira_obs.observation_context.observation_id,
            object_observation_id=gh_obs.observation_context.observation_id,
            provenance_refs=(
                ProvenanceRef(
                    source_instance=JIRA_SOURCE,
                    observation_id=jira_obs.observation_context.observation_id,
                    fixture_id="fixtures/jira/clean/flink_issues.json",
                    record_locator="issues[FLINK-1359].description",
                ),
            ),
        )
        assert_linkage_firewall(mention_rel, rel)
        assert mention_rel.kind == "mentions"

        # 4. State Firewall
        assert_state_firewall(jira_obs, gh_obs, rel)
        assert jira_obs.observed_state.status_category == "done"

        # 5. Temporal Alignment
        alignment = assert_temporal_firewall(jira_obs, gh_obs, rel)
        assert alignment == "COHERENT"

    def test_case_b_stratosphere_126_predecessor_lineage_isolation(self):
        """Case B: stratosphere#126 - Predecessor / Lineage Isolation."""
        rel = make_stratosphere_flink_relationship()
        strat_obs, flink_obs = make_numeric_collision_observations()

        # 1. Schema validation
        validate_repository_evolution_relationship(rel)
        assert rel.relationship_family == "PROJECT_LINEAGE"
        assert rel.relationship_type == "PREDECESSOR_SUCCESSOR"
        assert rel.directionality == "DIRECTED_FORWARD"
        assert rel.transitivity_rule == "TRANSITIVE_PERMITTED"
        assert rel.verification_status == "PROVEN"

        # 2. Strict Entity Isolation (INV-ID-03)
        assert strat_obs.entity_ref.entity_id == "stratosphere/stratosphere/126"
        assert flink_obs.entity_ref.entity_id == "apache/flink/126"
        assert strat_obs.entity_ref != flink_obs.entity_ref
        assert strat_obs.entity_ref.source_instance != flink_obs.entity_ref.source_instance

        # 3. Distinct Observational Facts
        assert strat_obs.observed_state.merged_at == datetime(2014, 3, 5, 12, 0, 0, tzinfo=timezone.utc)
        assert flink_obs.observed_state.merged_at == datetime(2014, 11, 22, 15, 0, 0, tzinfo=timezone.utc)
        assert "Stratosphere" in strat_obs.observed_state.title
        assert "Apache Flink" in flink_obs.observed_state.title

        # 4. Immutability
        orig_refs = {
            strat_obs.observation_context.observation_id: strat_obs.entity_ref,
            flink_obs.observation_context.observation_id: flink_obs.entity_ref,
        }
        assert_entity_ref_immutability((strat_obs, flink_obs), orig_refs, (rel,))

    def test_case_c_kafka_9168_external_dependency_isolation(self):
        """Case C: KAFKA-9168 - External Dependency Isolation."""
        rel = make_kafka_rocksdb_relationship()
        kafka_obs, rocks_obs = make_kafka_9168_observations()

        # 1. Schema validation
        validate_repository_evolution_relationship(rel)
        assert rel.relationship_family == "ECOSYSTEM_DEPENDENCY"
        assert rel.relationship_type == "EXTERNAL_DEPENDENCY"
        assert rel.directionality == "DIRECTED_FORWARD"
        assert rel.transitivity_rule == "STRICTLY_NON_TRANSITIVE"
        assert rel.verification_status == "PROVEN"

        # 2. External Dependency Isolation (INV-ST-02)
        assert kafka_obs.observed_state.status_category == "in_progress"
        assert kafka_obs.observed_state.resolved_at is None
        assert rocks_obs.observed_state.merged_at is not None

        # 3. State Firewall
        assert_state_firewall(kafka_obs, rocks_obs, rel)
        assert kafka_obs.observed_state.status_category == "in_progress"

        # 4. Immutability
        orig_refs = {
            kafka_obs.observation_context.observation_id: kafka_obs.entity_ref,
            rocks_obs.observation_context.observation_id: rocks_obs.entity_ref,
        }
        assert_entity_ref_immutability((kafka_obs, rocks_obs), orig_refs, (rel,))

    def test_case_d_flink_20650_ecosystem_packaging_temporal_independence(self):
        """Case D: FLINK-20650 - Ecosystem Packaging / Temporal Independence."""
        rel = make_flink_docker_relationship()
        flink_obs, docker_obs = make_flink_20650_observations()

        # 1. Schema validation
        validate_repository_evolution_relationship(rel)
        assert rel.relationship_family == "ECOSYSTEM_DEPENDENCY"
        assert rel.relationship_type == "ECOSYSTEM_PACKAGING"
        assert rel.directionality == "DIRECTED_FORWARD"
        assert rel.transitivity_rule == "STRICTLY_NON_TRANSITIVE"
        assert rel.verification_status == "SUPPORTED"

        # 2. Temporal Evaluation (INV-TM-02)
        alignment = assert_temporal_firewall(flink_obs, docker_obs, rel)
        assert alignment == "INVERTED"

        # 3. Preservation of Integrity
        assert flink_obs.observed_state.status_category == "done"
        assert flink_obs.observed_state.resolved_at == datetime(2021, 1, 10, 15, 0, 0, tzinfo=timezone.utc)
        assert docker_obs.observed_state.merged_at == datetime(2021, 2, 15, 16, 0, 0, tzinfo=timezone.utc)

    def test_all_cases_combined_graph_validation(self):
        """All 4 cases together form valid, acyclic lineage and routing graphs."""
        rel_a = make_flink_1359_relationship()
        rel_b = make_stratosphere_flink_relationship()
        rel_c = make_kafka_rocksdb_relationship()
        rel_d = make_flink_docker_relationship()

        # Validate graph
        validate_repository_evolution_graph([rel_a, rel_b, rel_c, rel_d])
