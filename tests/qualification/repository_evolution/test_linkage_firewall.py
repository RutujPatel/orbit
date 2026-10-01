"""Tests for Linkage Firewall (INV-LK-01, INV-LK-02) and Category E Linkage scenarios.

Authoritative reference:
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_semantic_contract.md
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_adversarial_tests.md
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceRelationship,
    ProvenanceRef,
    SourceInstance,
)
from qualification.repository_evolution.schema import (
    RepositoryEvolutionRelationship,
    RepositoryProvenanceRef,
    SemanticFirewall,
)
from qualification.repository_evolution.cases import (
    GH_SOURCE,
    JIRA_SOURCE,
    STRATOSPHERE_SOURCE,
    make_flink_1359_relationship,
    make_kafka_rocksdb_relationship,
    make_stratosphere_flink_relationship,
)
from qualification.repository_evolution.firewall import assert_linkage_firewall


class TestLinkageFirewall:
    """Verifies that repository evolution relationships NEVER upgrade linkage."""

    def test_inv_lk_01_evolution_does_not_upgrade_declared_mention(self):
        """INV-LK-01: Evolution metadata does not upgrade DECLARED_MENTION to EXPLICIT_LINK."""
        strat_rel = make_stratosphere_flink_relationship()

        jira_ref = EntityRef(JIRA_SOURCE, "work_item", "FLINK-126")
        pr_ref = EntityRef(STRATOSPHERE_SOURCE, "code_change", "stratosphere/stratosphere/126")

        # Mention linkage created via lexical match in Jira comment/description
        cross_rel = EvidenceRelationship(
            subject_ref=jira_ref,
            object_ref=pr_ref,
            kind="mentions",
            basis="lexical_match",
            subject_observation_id="obs-jira-126",
            object_observation_id="obs-gh-126",
            provenance_refs=(
                ProvenanceRef(
                    source_instance=JIRA_SOURCE,
                    observation_id="obs-jira-126",
                    fixture_id="fixtures/jira/clean/flink_issues.json",
                    record_locator="issues[FLINK-126].description",
                ),
            ),
        )

        # Assert linkage firewall verifies kind and basis remain unchanged
        assert_linkage_firewall(cross_rel, strat_rel)
        assert cross_rel.kind == "mentions"
        assert cross_rel.basis == "lexical_match"

    def test_inv_lk_01_illegal_linkage_upgrade_rejected(self):
        """INV-LK-01: Falsely promoting mention to EXPLICIT_LINK is detected and rejected."""
        strat_rel = make_stratosphere_flink_relationship()

        jira_ref = EntityRef(JIRA_SOURCE, "work_item", "FLINK-126")
        pr_ref = EntityRef(STRATOSPHERE_SOURCE, "code_change", "stratosphere/stratosphere/126")

        # Improperly upgraded relationship
        illegal_cross_rel = EvidenceRelationship(
            subject_ref=jira_ref,
            object_ref=pr_ref,
            kind="explicit_link",
            basis="explicit_metadata",
            subject_observation_id="obs-jira-126",
            object_observation_id="obs-gh-126",
            provenance_refs=(
                ProvenanceRef(
                    source_instance=JIRA_SOURCE,
                    observation_id="obs-jira-126",
                    fixture_id="fixtures/jira/clean/flink_issues.json",
                    record_locator="issues[FLINK-126].description",
                ),
            ),
        )

        with pytest.raises(AssertionError, match="INV-LK-01 VIOLATION"):
            assert_linkage_firewall(illegal_cross_rel, strat_rel)

    def test_inv_lk_02_redirect_preserves_mention_basis(self):
        """INV-LK-02: Redirect evolution does not alter cross-system linkage basis."""
        redirect_rel = make_flink_1359_relationship()

        jira_ref = EntityRef(JIRA_SOURCE, "work_item", "FLINK-1359")
        pr_ref = EntityRef(GH_SOURCE, "code_change", "apache/flink/254")

        cross_rel = EvidenceRelationship(
            subject_ref=jira_ref,
            object_ref=pr_ref,
            kind="mentions",
            basis="lexical_match",
            subject_observation_id="obs-jira-1359",
            object_observation_id="obs-gh-254",
            provenance_refs=(
                ProvenanceRef(
                    source_instance=JIRA_SOURCE,
                    observation_id="obs-jira-1359",
                    fixture_id="fixtures/jira/clean/flink_issues.json",
                    record_locator="issues[FLINK-1359].description",
                ),
            ),
        )

        assert_linkage_firewall(cross_rel, redirect_rel)
        assert cross_rel.kind == "mentions"
        assert cross_rel.basis == "lexical_match"

    def test_adv_fw_01_evolution_not_used_to_upgrade_linkage(self):
        """ADV-FW-01: Stratosphere predecessor relationship must never promote Jira mention."""
        strat_rel = make_stratosphere_flink_relationship()
        assert strat_rel.semantic_firewall.linkage_auto_upgrade_forbidden is True

    def test_adv_pr_01_plain_url_without_vcs_evidence_is_mention_only(self):
        """ADV-PR-01: Plain text Jira URL without corroborating VCS evidence produces only DECLARED_MENTION."""
        jira_ref = EntityRef(JIRA_SOURCE, "work_item", "FOO-1")
        pr_ref = EntityRef(GH_SOURCE, "code_change", "foo/bar/1")

        # Only a lexical mention is authorized
        mention_rel = EvidenceRelationship(
            subject_ref=jira_ref,
            object_ref=pr_ref,
            kind="mentions",
            basis="lexical_match",
            subject_observation_id="obs-jira-foo-1",
            object_observation_id="obs-gh-bar-1",
            provenance_refs=(
                ProvenanceRef(
                    source_instance=JIRA_SOURCE,
                    observation_id="obs-jira-foo-1",
                    fixture_id="fixtures/jira/clean/foo.json",
                    record_locator="issues[FOO-1].description",
                ),
            ),
        )
        assert mention_rel.kind == "mentions"
        assert mention_rel.basis == "lexical_match"
