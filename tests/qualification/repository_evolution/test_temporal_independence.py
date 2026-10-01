"""Tests for Temporal Independence (INV-TM-01, INV-TM-02, ADV-FW-03, ADV-FW-04).

Authoritative reference:
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_semantic_contract.md
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_adversarial_tests.md
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    GitHubPullRequestState,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
)
from qualification.repository_evolution.schema import (
    RepositoryEvolutionRelationship,
    RepositoryProvenanceRef,
    SemanticFirewall,
)
from qualification.repository_evolution.cases import (
    DOCKER_SOURCE,
    GH_SOURCE,
    JIRA_SOURCE,
    make_flink_20650_observations,
    make_flink_docker_relationship,
)
from qualification.repository_evolution.firewall import assert_temporal_firewall


class TestTemporalIndependence:
    """Verifies that temporal proximity/order never implies causality or data corruption."""

    def test_inv_tm_01_proximity_does_not_imply_causality_adv_fw_03(self):
        """INV-TM-01 & ADV-FW-03: Temporal proximity between repo rename and issue resolution is non-causal."""
        rename_rel = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="RENAME",
            source_repository=EntityRef(GH_SOURCE, "repository", "apache/incubator-flink"),
            target_repository=EntityRef(GH_SOURCE, "repository", "apache/flink"),
            verification_status="PROVEN",
            observed_at=datetime(2014, 12, 15, 14, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(
                RepositoryProvenanceRef(
                    source_instance=GH_SOURCE,
                    fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
                    record_locator="base.repo.full_name",
                    sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
                ),
            ),
        )

        jira_obs = EvidenceObservation(
            entity_ref=EntityRef(JIRA_SOURCE, "work_item", "FLINK-100"),
            observation_context=ObservationContext(
                observation_id="obs-jira-100",
                source_instance=JIRA_SOURCE,
            ),
            observed_state=JiraIssueState(
                key="FLINK-100",
                source_status="Resolved",
                source_priority="Major",
                status_category="done",
                priority_band="medium",
                assignee=None,
                created_at=datetime(2014, 12, 1, 10, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2014, 12, 15, 14, 0, 5, tzinfo=timezone.utc),
                resolved_at=datetime(2014, 12, 15, 14, 0, 5, tzinfo=timezone.utc),  # 5 seconds after rename
            ),
            provenance_refs=(
                ProvenanceRef(
                    source_instance=JIRA_SOURCE,
                    observation_id="obs-jira-100",
                    fixture_id="fixtures/jira/clean/flink_issues.json",
                    record_locator="issues[FLINK-100]",
                ),
            ),
        )

        assert rename_rel.semantic_firewall.temporal_causality_inference_forbidden is True
        assert jira_obs.observed_state.resolved_at == datetime(2014, 12, 15, 14, 0, 5, tzinfo=timezone.utc)
        assert rename_rel.observed_at == datetime(2014, 12, 15, 14, 0, 0, tzinfo=timezone.utc)
        # Proximity does not cause any mutation or causal link

    def test_inv_tm_02_post_resolution_packaging_pr_inverted_alignment(self):
        """INV-TM-02: Packaging PR merging post-resolution is observational INVERTED without corruption."""
        flink_obs, docker_obs = make_flink_20650_observations()
        docker_rel = make_flink_docker_relationship()

        # Flink issue resolved on Jan 10, 2021
        assert flink_obs.observed_state.resolved_at == datetime(2021, 1, 10, 15, 0, 0, tzinfo=timezone.utc)
        # Packaging PR merged 36 days later on Feb 15, 2021
        assert docker_obs.observed_state.merged_at == datetime(2021, 2, 15, 16, 0, 0, tzinfo=timezone.utc)

        # Assert temporal evaluation returns INVERTED
        alignment = assert_temporal_firewall(flink_obs, docker_obs, docker_rel)
        assert alignment == "INVERTED"

        # Assert neither observation is corrupted or modified
        assert flink_obs.observed_state.status_category == "done"
        assert docker_obs.observed_state.state == "closed"

    def test_adv_fw_04_naming_similarity_does_not_infer_lineage(self):
        """ADV-FW-04: Naming similarity between sister repos does not establish predecessor/successor lineage."""
        parquet_format = EntityRef(GH_SOURCE, "repository", "apache/parquet-format")
        parquet_mr = EntityRef(GH_SOURCE, "repository", "apache/parquet-mr")

        prov = RepositoryProvenanceRef(
            source_instance=GH_SOURCE,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="base.repo.full_name",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )

        # Correct relationship: COMPANION_SPECIFICATION in ECOSYSTEM_DEPENDENCY
        valid_companion_rel = RepositoryEvolutionRelationship.create(
            relationship_family="ECOSYSTEM_DEPENDENCY",
            relationship_type="COMPANION_SPECIFICATION",
            source_repository=parquet_mr,
            target_repository=parquet_format,
            verification_status="SUPPORTED",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(prov,),
            family_payload={"dependency_scope": "specification"},
        )
        assert valid_companion_rel.relationship_type == "COMPANION_SPECIFICATION"
        assert valid_companion_rel.transitivity_rule == "STRICTLY_NON_TRANSITIVE"

        # Attempting to assign PREDECESSOR_SUCCESSOR under NAVIGATION_ROUTING fails validation
        with pytest.raises(ValueError, match="not a member of family"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="PREDECESSOR_SUCCESSOR",  # Invalid for NAVIGATION_ROUTING
                source_repository=parquet_mr,
                target_repository=parquet_format,
                verification_status="SUPPORTED",
                observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
                provenance_refs=(prov,),
            )

    def test_inv_tm_firewall_flag_enforced(self):
        """SemanticFirewall requires temporal_causality_inference_forbidden=True."""
        with pytest.raises(ValueError, match="temporal_causality_inference_forbidden"):
            SemanticFirewall(temporal_causality_inference_forbidden=False).validate()
