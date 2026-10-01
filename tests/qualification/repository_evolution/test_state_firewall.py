"""Tests for State Firewall (INV-ST-01, INV-ST-02, ADV-FW-02).

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
    SemanticFirewall,
)
from qualification.repository_evolution.cases import (
    GH_SOURCE,
    JIRA_SOURCE,
    ROCKSDB_SOURCE,
    make_flink_1359_relationship,
    make_kafka_9168_observations,
    make_kafka_rocksdb_relationship,
)
from qualification.repository_evolution.firewall import assert_state_firewall


class TestStateFirewall:
    """Verifies that repository evolution relationships NEVER transfer work state."""

    def test_inv_st_01_target_pr_merge_does_not_complete_source_jira_issue(self):
        """INV-ST-01: Merging a PR in target repo does not automatically mark source Jira issue completed."""
        redirect_rel = make_flink_1359_relationship()

        # Jira issue in progress
        jira_ref = EntityRef(JIRA_SOURCE, "work_item", "FLINK-999")
        jira_obs = EvidenceObservation(
            entity_ref=jira_ref,
            observation_context=ObservationContext(
                observation_id="obs-jira-flink-999",
                source_instance=JIRA_SOURCE,
            ),
            observed_state=JiraIssueState(
                key="FLINK-999",
                source_status="In Progress",
                source_priority="Major",
                status_category="in_progress",
                priority_band="medium",
                assignee=None,
                created_at=datetime(2014, 12, 1, 10, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2014, 12, 5, 10, 0, 0, tzinfo=timezone.utc),
                resolved_at=None,
            ),
            provenance_refs=(
                ProvenanceRef(
                    source_instance=JIRA_SOURCE,
                    observation_id="obs-jira-flink-999",
                    fixture_id="fixtures/jira/clean/flink_issues.json",
                    record_locator="issues[FLINK-999]",
                ),
            ),
        )

        # PR in target repo is merged
        gh_ref = EntityRef(GH_SOURCE, "code_change", "apache/flink/999")
        gh_obs = EvidenceObservation(
            entity_ref=gh_ref,
            observation_context=ObservationContext(
                observation_id="obs-gh-flink-pr-999",
                source_instance=GH_SOURCE,
            ),
            observed_state=GitHubPullRequestState(
                number=999,
                title="Target PR 999",
                state="closed",
                created_at=datetime(2014, 12, 2, 10, 0, 0, tzinfo=timezone.utc),
                merged_at=datetime(2014, 12, 6, 12, 0, 0, tzinfo=timezone.utc),
            ),
            provenance_refs=(
                ProvenanceRef(
                    source_instance=GH_SOURCE,
                    observation_id="obs-gh-flink-pr-999",
                    fixture_id="fixtures/github/flink/pr_999.json",
                    record_locator="pull_request[999]",
                ),
            ),
        )

        # Assert firewall passes: work item retains its authentic in_progress state
        assert_state_firewall(jira_obs, gh_obs, redirect_rel)
        assert jira_obs.observed_state.status_category == "in_progress"
        assert jira_obs.observed_state.resolved_at is None

    def test_inv_st_01_illegal_state_transfer_rejected(self):
        """INV-ST-01: Falsely transferring done status without native resolution is rejected."""
        redirect_rel = make_flink_1359_relationship()

        # Jira issue falsely marked done without resolved_at
        jira_ref = EntityRef(JIRA_SOURCE, "work_item", "FLINK-999")
        illegal_jira_obs = EvidenceObservation(
            entity_ref=jira_ref,
            observation_context=ObservationContext(
                observation_id="obs-jira-flink-999",
                source_instance=JIRA_SOURCE,
            ),
            observed_state=JiraIssueState(
                key="FLINK-999",
                source_status="Resolved",
                source_priority="Major",
                status_category="done",
                priority_band="medium",
                assignee=None,
                created_at=datetime(2014, 12, 1, 10, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2014, 12, 5, 10, 0, 0, tzinfo=timezone.utc),
                resolved_at=None,  # Missing native resolution!
            ),
            provenance_refs=(
                ProvenanceRef(
                    source_instance=JIRA_SOURCE,
                    observation_id="obs-jira-flink-999",
                    fixture_id="fixtures/jira/clean/flink_issues.json",
                    record_locator="issues[FLINK-999]",
                ),
            ),
        )

        gh_ref = EntityRef(GH_SOURCE, "code_change", "apache/flink/999")
        gh_obs = EvidenceObservation(
            entity_ref=gh_ref,
            observation_context=ObservationContext(
                observation_id="obs-gh-flink-pr-999",
                source_instance=GH_SOURCE,
            ),
            observed_state=GitHubPullRequestState(
                number=999,
                title="Target PR 999",
                state="closed",
                created_at=datetime(2014, 12, 2, 10, 0, 0, tzinfo=timezone.utc),
                merged_at=datetime(2014, 12, 6, 12, 0, 0, tzinfo=timezone.utc),
            ),
            provenance_refs=(
                ProvenanceRef(
                    source_instance=GH_SOURCE,
                    observation_id="obs-gh-flink-pr-999",
                    fixture_id="fixtures/github/flink/pr_999.json",
                    record_locator="pull_request[999]",
                ),
            ),
        )

        with pytest.raises(AssertionError, match="INV-ST-01 VIOLATION"):
            assert_state_firewall(illegal_jira_obs, gh_obs, redirect_rel)

    def test_inv_st_02_external_dependency_isolation(self):
        """INV-ST-02: Merged PR in external dependency (RocksDB) does not complete Kafka issue."""
        kafka_obs, rocks_obs = make_kafka_9168_observations()
        kafka_rocks_rel = make_kafka_rocksdb_relationship()

        assert kafka_obs.observed_state.status_category == "in_progress"
        assert kafka_obs.observed_state.resolved_at is None
        assert rocks_obs.observed_state.merged_at is not None

        # Assert firewall passes: external dependency PR does not resolve Kafka issue
        assert_state_firewall(kafka_obs, rocks_obs, kafka_rocks_rel)
        assert kafka_obs.observed_state.status_category == "in_progress"

    def test_adv_fw_02_external_dependency_pr_merge_rejected_as_resolution(self):
        """ADV-FW-02: Reject transferring external dependency PR merge as Jira issue resolution."""
        kafka_obs, rocks_obs = make_kafka_9168_observations()
        kafka_rocks_rel = make_kafka_rocksdb_relationship()

        # Adversarial attempt: mark Kafka issue done based on RocksDB PR merge without resolved_at
        illegal_kafka_obs = EvidenceObservation(
            entity_ref=kafka_obs.entity_ref,
            observation_context=kafka_obs.observation_context,
            observed_state=JiraIssueState(
                key="KAFKA-9168",
                source_status="Done",
                source_priority="Major",
                status_category="done",
                priority_band="medium",
                assignee=None,
                created_at=kafka_obs.observed_state.created_at,
                updated_at=kafka_obs.observed_state.updated_at,
                resolved_at=None,  # External PR merge cannot synthesize resolved_at
            ),
            provenance_refs=kafka_obs.provenance_refs,
        )

        with pytest.raises(AssertionError, match="INV-ST-02 VIOLATION"):
            assert_state_firewall(illegal_kafka_obs, rocks_obs, kafka_rocks_rel)

    def test_inv_st_firewall_flag_enforced(self):
        """SemanticFirewall requires state_transfer_forbidden=True."""
        with pytest.raises(ValueError, match="state_transfer_forbidden"):
            SemanticFirewall(state_transfer_forbidden=False).validate()
