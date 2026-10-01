"""Tests for Identity Invariants (INV-ID-01 through INV-ID-04) and Category A adversarial scenarios.

Authoritative reference:
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_semantic_contract.md
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_adversarial_tests.md
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import pytest

from shadow_orbit.evidence_types import EntityRef, ProvenanceRef, SourceInstance
from qualification.repository_evolution.schema import (
    RepositoryEvolutionRelationship,
    RepositoryProvenanceRef,
    SemanticFirewall,
    compute_relationship_id,
)
from qualification.repository_evolution.cases import (
    GH_SOURCE,
    JIRA_SOURCE,
    STRATOSPHERE_SOURCE,
    make_numeric_collision_observations,
    make_stratosphere_flink_relationship,
)
from qualification.repository_evolution.firewall import assert_entity_ref_immutability


class TestIdentityInvariants:
    """Verifies INV-ID-01, INV-ID-02, INV-ID-03, INV-ID-04."""

    def test_inv_id_01_entity_ref_immutability(self, flink_repo_ref: EntityRef, incubator_flink_repo_ref: EntityRef, sample_provenance: ProvenanceRef, sample_observed_at: datetime):
        """INV-ID-01: Evolution relationships must never mutate or alias observation EntityRefs."""
        rel = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=incubator_flink_repo_ref,
            target_repository=flink_repo_ref,
            verification_status="PROVEN",
            observed_at=sample_observed_at,
            provenance_refs=(sample_provenance,),
        )
        # Even with relationship defined, the observation EntityRefs remain unmodified
        strat_obs, flink_obs = make_numeric_collision_observations()
        orig_refs = {
            strat_obs.observation_context.observation_id: strat_obs.entity_ref,
            flink_obs.observation_context.observation_id: flink_obs.entity_ref,
        }
        assert_entity_ref_immutability((strat_obs, flink_obs), orig_refs, (rel,))
        assert strat_obs.entity_ref.entity_id == "stratosphere/stratosphere/126"
        assert flink_obs.entity_ref.entity_id == "apache/flink/126"

    def test_inv_id_02_strict_repository_endpoints_accepted(self, flink_repo_ref: EntityRef, incubator_flink_repo_ref: EntityRef, sample_provenance: ProvenanceRef, sample_observed_at: datetime):
        """INV-ID-02: Endpoints with entity_kind='repository' are accepted."""
        rel = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=incubator_flink_repo_ref,
            target_repository=flink_repo_ref,
            verification_status="PROVEN",
            observed_at=sample_observed_at,
            provenance_refs=(sample_provenance,),
        )
        assert rel.source_repository.entity_kind == "repository"
        assert rel.target_repository.entity_kind == "repository"

    def test_inv_id_02_rejects_code_change_endpoints(self, flink_repo_ref: EntityRef, sample_provenance: ProvenanceRef, sample_observed_at: datetime):
        """INV-ID-02: Code change entities (pull requests) are strictly rejected as endpoints."""
        code_change_ref = EntityRef(GH_SOURCE, "code_change", "apache/flink/126")

        # As source_repository
        with pytest.raises(ValueError, match="INV-ID-02 violated.*source_repository.entity_kind"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=code_change_ref,
                target_repository=flink_repo_ref,
                verification_status="PROVEN",
                observed_at=sample_observed_at,
                provenance_refs=(sample_provenance,),
            )

        # As target_repository
        with pytest.raises(ValueError, match="INV-ID-02 violated.*target_repository.entity_kind"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=flink_repo_ref,
                target_repository=code_change_ref,
                verification_status="PROVEN",
                observed_at=sample_observed_at,
                provenance_refs=(sample_provenance,),
            )

    def test_inv_id_02_rejects_work_item_endpoints(self, flink_repo_ref: EntityRef, sample_provenance: ProvenanceRef, sample_observed_at: datetime):
        """INV-ID-02: Work items (Jira issues) are strictly rejected as endpoints."""
        work_item_ref = EntityRef(JIRA_SOURCE, "work_item", "FLINK-126")
        with pytest.raises(ValueError, match="INV-ID-02 violated"):
            RepositoryEvolutionRelationship.create(
                relationship_family="PROJECT_LINEAGE",
                relationship_type="PREDECESSOR_SUCCESSOR",
                source_repository=work_item_ref,
                target_repository=flink_repo_ref,
                verification_status="PROVEN",
                observed_at=sample_observed_at,
                provenance_refs=(sample_provenance,),
            )

    def test_inv_id_02_rejects_invalid_repo_name_format(self, gh_source: SourceInstance, flink_repo_ref: EntityRef, sample_provenance: ProvenanceRef, sample_observed_at: datetime):
        """INV-ID-02: Repository entity_id must strictly match {owner}/{repo} format."""
        invalid_repo_ref = EntityRef(gh_source, "repository", "flink")  # missing owner
        with pytest.raises(ValueError, match="Invalid source_repository entity_id"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=invalid_repo_ref,
                target_repository=flink_repo_ref,
                verification_status="PROVEN",
                observed_at=sample_observed_at,
                provenance_refs=(sample_provenance,),
            )

    def test_inv_id_03_pr_number_collision_isolation(self):
        """INV-ID-03: Lineage relationship does NOT collapse stratosphere#126 and flink#126."""
        rel = make_stratosphere_flink_relationship()
        strat_obs, flink_obs = make_numeric_collision_observations()

        # Both have PR number 126
        assert strat_obs.observed_state.number == 126
        assert flink_obs.observed_state.number == 126

        # But their EntityRefs are strictly distinct
        assert strat_obs.entity_ref != flink_obs.entity_ref
        assert strat_obs.entity_ref.entity_id == "stratosphere/stratosphere/126"
        assert flink_obs.entity_ref.entity_id == "apache/flink/126"
        assert strat_obs.entity_ref.source_instance != flink_obs.entity_ref.source_instance

        # The relationship connects repositories, not PRs
        assert rel.source_repository.entity_id == "stratosphere/stratosphere"
        assert rel.target_repository.entity_id == "apache/flink"

    def test_inv_id_04_deterministic_relationship_id_derivation(self, flink_repo_ref: EntityRef, incubator_flink_repo_ref: EntityRef, sample_provenance: ProvenanceRef, sample_observed_at: datetime):
        """INV-ID-04: Same inputs produce identical deterministic SHA-256 relationship_id."""
        rel1 = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=incubator_flink_repo_ref,
            target_repository=flink_repo_ref,
            verification_status="PROVEN",
            observed_at=sample_observed_at,
            provenance_refs=(sample_provenance,),
        )
        rel2 = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=incubator_flink_repo_ref,
            target_repository=flink_repo_ref,
            verification_status="PROVEN",
            observed_at=datetime(2020, 1, 1, tzinfo=timezone.utc),  # different timestamp
            provenance_refs=(sample_provenance,),
        )
        # Relationship ID is invariant to observed_at
        assert rel1.relationship_id == rel2.relationship_id
        expected_raw = f"{incubator_flink_repo_ref.source_instance.instance_id}|REDIRECT|apache/incubator-flink|apache/flink"
        assert rel1.relationship_id == hashlib.sha256(expected_raw.encode("utf-8")).hexdigest()

    def test_inv_id_04_rejects_tampered_relationship_id(self, flink_repo_ref: EntityRef, incubator_flink_repo_ref: EntityRef, sample_provenance: ProvenanceRef, sample_observed_at: datetime):
        """INV-ID-04: Non-matching relationship_id raises ValueError."""
        with pytest.raises(ValueError, match="INV-ID-04 violated"):
            RepositoryEvolutionRelationship(
                relationship_id="a" * 64,  # Arbitrary non-deterministic hash
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=incubator_flink_repo_ref,
                target_repository=flink_repo_ref,
                directionality="DIRECTED_FORWARD",
                transitivity_rule="TRANSITIVE_PERMITTED",
                verification_status="PROVEN",
                observed_at=sample_observed_at,
                provenance_refs=(sample_provenance,),
            )


class TestAdversarialCategoryA:
    """Verifies Category A adversarial scenarios (ADV-ID-01 through ADV-ID-05)."""

    def test_adv_id_01_same_pr_number_across_distinct_repos(self, gh_source: SourceInstance):
        """ADV-ID-01: PR #885 in parquet-java vs PR #885 in kafka must remain distinct entities."""
        parquet_pr = EntityRef(gh_source, "code_change", "apache/parquet-java/885")
        kafka_pr = EntityRef(gh_source, "code_change", "apache/kafka/885")

        assert parquet_pr != kafka_pr
        assert parquet_pr.entity_id != kafka_pr.entity_id

    def test_adv_id_02_same_repo_name_under_different_owners(self):
        """ADV-ID-02: apache/kafka vs linkedin/kafka must remain distinct repository entities."""
        apache_kafka = EntityRef(SourceInstance("github", "github.com/apache"), "repository", "apache/kafka")
        linkedin_kafka = EntityRef(SourceInstance("github", "github.com/linkedin"), "repository", "linkedin/kafka")

        assert apache_kafka != linkedin_kafka
        assert apache_kafka.entity_id == "apache/kafka"
        assert linkedin_kafka.entity_id == "linkedin/kafka"

    def test_adv_id_03_same_repo_across_different_provider_instances(self):
        """ADV-ID-03: gitbox vs github mirrors must remain distinct entities linked by MIRROR."""
        gitbox_kafka = EntityRef(SourceInstance("git", "gitbox.apache.org"), "repository", "asf/kafka")
        github_kafka = EntityRef(SourceInstance("github", "github.com/apache"), "repository", "apache/kafka")

        assert gitbox_kafka != github_kafka
        prov = RepositoryProvenanceRef(
            source_instance=SourceInstance("github", "github.com/apache"),
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="remotes.origin",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        mirror_rel = RepositoryEvolutionRelationship.create(
            relationship_family="REPOSITORY_TOPOLOGY",
            relationship_type="MIRROR",
            source_repository=gitbox_kafka,
            target_repository=github_kafka,
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(prov,),
            directionality="BIDIRECTIONAL_SYMMETRIC",
        )
        assert mirror_rel.directionality == "BIDIRECTIONAL_SYMMETRIC"
        assert mirror_rel.relationship_type == "MIRROR"

    def test_adv_id_04_repository_rename_under_same_owner(self, flink_repo_ref: EntityRef, incubator_flink_repo_ref: EntityRef, sample_provenance: ProvenanceRef, sample_observed_at: datetime):
        """ADV-ID-04: Rename creates RENAME relationship, preserves historical incubator EntityRef."""
        rel = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="RENAME",
            source_repository=incubator_flink_repo_ref,
            target_repository=flink_repo_ref,
            verification_status="PROVEN",
            observed_at=sample_observed_at,
            provenance_refs=(sample_provenance,),
            family_payload={"underlying_vcs_id_matched": True},
        )
        assert rel.relationship_type == "RENAME"
        assert rel.source_repository.entity_id == "apache/incubator-flink"
        assert rel.target_repository.entity_id == "apache/flink"

    def test_adv_id_05_repository_namespace_move(self):
        """ADV-ID-05: Org transfer retains distinct EntityRefs and creates PREDECESSOR_SUCCESSOR."""
        rel = make_stratosphere_flink_relationship()
        assert rel.relationship_type == "PREDECESSOR_SUCCESSOR"
        assert rel.source_repository.entity_id == "stratosphere/stratosphere"
        assert rel.target_repository.entity_id == "apache/flink"

    def test_inv_ev_01_empty_sha256_rejected(self, flink_repo_ref: EntityRef, incubator_flink_repo_ref: EntityRef, sample_observed_at: datetime):
        """INV-EV-01: Empty-string SHA-256 digest is rejected as invalid/ungrounded provenance."""
        empty_prov = RepositoryProvenanceRef(
            source_instance=SourceInstance("github", "github.com/apache"),
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="base.repo.full_name",
            sha256_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        with pytest.raises(ValueError, match="INV-EV-01 violated.*empty-string SHA-256"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=incubator_flink_repo_ref,
                target_repository=flink_repo_ref,
                verification_status="PROVEN",
                observed_at=sample_observed_at,
                provenance_refs=(empty_prov,),
            )
