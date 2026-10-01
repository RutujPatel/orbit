"""Pass 5 / Wave 3 — Real Apache Multi-Project Canonical Adaptation Tests.

Proves that real Apache Jira and GitHub artifacts from The Public Jira Dataset
and official GitHub mirrors adapt into ORBIT's canonical evidence models
(WorkItemState, CodeChangeState, CrossSystemStateAlignment) and execute through
the Track B evidence evaluator without provider-specific evaluator semantics.

Test Matrix Coverage (Section 16):
1. Jira → WorkItemState mapping
2. GitHub PR → CodeChangeState mapping
3. commit vs merge timestamp distinction (committed_at != merged_at)
4. declared mention classification (Chain 1: PARQUET-2010 ↔ PR 885)
5. explicit link classification (Chains 2, 3, 4, 5)
6. one Jira → many commits (Chain 2: KAFKA-13557 with 5 commits)
7. one Jira → many PRs (Chain 4: FLINK-24409 with 3 PRs)
8. many Jira → one PR (Chain 5: FLINK-14386 + FLINK-14665 ↔ PR 10123)
9. negative controls (PARQUET-1812, ZOOKEEPER-4348, PR 3822)
10. CVE/Snyk false-positive rejection (AXIOS-12613773 is NOT a Jira link)
11. repository-scoped PR identity (base repo prefix in entity_id)
12. Jira source-instance identity (issues.apache.org instance_id)
13. fork/upstream identity (head repo fork vs base repo canonical upstream)
14. provenance dereferencing (in-memory resolution against raw fixtures)
15. deterministic serialization (bit-for-bit identical SHA-256)
16. permutation invariance (input order invariant)
17. canonical evaluator execution without Jira/GitHub constructors (provider leakage proof)
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from qualification.wave3.apache_real.adapters import (
    APACHE_GITHUB_SOURCE,
    APACHE_JIRA_SOURCE,
    SUPPORTED_APACHE_PROJECTS,
    adapt_apache_github_commit,
    adapt_apache_github_commit_to_state,
    adapt_apache_github_pr,
    adapt_apache_github_pr_to_state,
    adapt_apache_jira_issue,
    adapt_apache_jira_issue_to_state,
    build_apache_evidence_bundle,
    build_cross_system_alignment,
    is_valid_apache_jira_key,
    load_apache_raw_fixtures,
    parse_iso_datetime,
)
from shadow_orbit.evidence_assembly import validate_evidence_bundle
from shadow_orbit.evidence_evaluation import (
    evaluate_evidence_bundle,
    serialize_evaluation_result,
)
from shadow_orbit.evidence_types import (
    CodeChangeState,
    CrossSystemStateAlignment,
    EntityRef,
    EvidenceBundle,
    EvidenceObservation,
    GitHubPullRequestState,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    WorkItemState,
    serialize_evidence_bundle,
)
from shadow_orbit.provenance_dereference import dereference_provenance_ref

CORPUS_DIR = Path(__file__).resolve().parents[2] / "qualification" / "wave3" / "apache_real"


@pytest.fixture(scope="module")
def raw_data():
    raw_files, fixtures_by_id = load_apache_raw_fixtures(CORPUS_DIR)
    return raw_files, fixtures_by_id


@pytest.fixture(scope="module")
def canonical_bundle(raw_data):
    bundle, fixtures_by_id = build_apache_evidence_bundle(CORPUS_DIR)
    return bundle, fixtures_by_id


# ======================================================================
# 1. JIRA → WORKITEMSTATE ADAPTER TESTS
# ======================================================================

class TestApacheJiraAdapter:
    """Verify that raw Apache Jira records project faithfully into WorkItemState."""

    def test_jira_to_work_item_state_mapping(self, raw_data) -> None:
        """Matrix Item 1: Test Jira → WorkItemState mapping for all target issues."""
        raw_files, _ = raw_data
        for key in ["PARQUET-2010", "KAFKA-13557", "AVRO-3234", "FLINK-24409", "FLINK-14386", "FLINK-14665"]:
            raw = raw_files[f"jira/{key}.json"]
            state = adapt_apache_jira_issue_to_state(raw)

            assert isinstance(state, WorkItemState)
            assert state.key == key
            assert state.identifier == key
            assert state.status_category in ("done", "to_do", "in_progress")
            assert state.created_at is not None
            assert state.created_at.tzinfo == timezone.utc
            assert state.extra_properties.get("project_key") == key.split("-")[0]
            assert state.extra_properties.get("issue_id") == str(raw["id"])

    def test_parquet_2010_specific_fields(self, raw_data) -> None:
        """Verify PARQUET-2010 blocker priority and resolved status."""
        raw_files, _ = raw_data
        raw = raw_files["jira/PARQUET-2010.json"]
        state = adapt_apache_jira_issue_to_state(raw)

        assert state.key == "PARQUET-2010"
        assert state.source_status == "Resolved"
        assert state.status_category == "done"
        assert state.source_priority == "Blocker"
        assert state.priority_band == "high"
        assert state.resolved_at == datetime(2021, 3, 30, 17, 15, 17, tzinfo=timezone.utc)
        assert state.due_at is None  # Missing remains None

    def test_jira_source_instance_identity(self, raw_data) -> None:
        """Matrix Item 12: Jira source-instance identity is issues.apache.org."""
        raw_files, _ = raw_data
        raw = raw_files["jira/KAFKA-13557.json"]
        ctx = ObservationContext(
            observation_id="test_ctx",
            source_instance=APACHE_JIRA_SOURCE,
        )
        obs = adapt_apache_jira_issue(raw, ctx)

        assert obs.entity_ref.source_instance == APACHE_JIRA_SOURCE
        assert obs.entity_ref.source_instance.source_kind == "jira"
        assert obs.entity_ref.source_instance.instance_id == "issues.apache.org"
        assert obs.entity_ref.entity_kind == "work_item"
        assert obs.entity_ref.entity_id == "KAFKA-13557"

    def test_invalid_and_non_apache_keys_rejected(self) -> None:
        """Matrix Item 10: Rejection of invalid keys and Snyk/CVE false positives."""
        assert is_valid_apache_jira_key("PARQUET-2010") is True
        assert is_valid_apache_jira_key("KAFKA-13557") is True
        assert is_valid_apache_jira_key("AVRO-3234") is True
        assert is_valid_apache_jira_key("FLINK-24409") is True
        assert is_valid_apache_jira_key("ZOOKEEPER-4348") is True

        # Non-Apache project keys / False positives must be rejected
        assert is_valid_apache_jira_key("AXIOS-12613773") is False
        assert is_valid_apache_jira_key("CVE-2021-1234") is False
        assert is_valid_apache_jira_key("SNYK-12345") is False
        assert is_valid_apache_jira_key("UNKNOWN-101") is False
        assert is_valid_apache_jira_key("") is False
        assert is_valid_apache_jira_key("PARQUET") is False
        assert is_valid_apache_jira_key("PARQUET-ABC") is False


# ======================================================================
# 2. GITHUB PR & COMMIT ADAPTER TESTS
# ======================================================================

class TestApacheGitHubAdapter:
    """Verify that raw Apache GitHub records project faithfully into CodeChangeState."""

    def test_github_pr_to_code_change_state_mapping(self, raw_data) -> None:
        """Matrix Item 2: Test GitHub PR → CodeChangeState mapping for target PRs."""
        raw_files, _ = raw_data
        specs = [
            ("parquet-java", 885, "merged"),
            ("kafka", 11617, "merged"),
            ("avro", 1370, "merged"),
            ("flink", 17401, "closed"),
            ("flink", 17773, "merged"),
            ("flink", 17799, "merged"),
            ("flink", 10123, "closed"),
        ]
        for repo_dir, num, expected_state in specs:
            raw = raw_files[f"github/{repo_dir}/pull_{num}.json"]
            state = adapt_apache_github_pr_to_state(raw)

            assert isinstance(state, CodeChangeState)
            assert state.change_type == "pull_request"
            assert state.identifier == str(num)
            assert state.state == expected_state
            assert state.created_at is not None
            assert state.created_at.tzinfo == timezone.utc
            assert state.committed_at is None  # PRs never carry committed_at

    def test_commit_vs_merge_timestamp_distinction(self, raw_data) -> None:
        """Matrix Item 3: Strict distinction between committed_at and merged_at.

        Rule 7: A commit is not automatically a merge. Commits have committed_at.
        PRs have merged_at. Never map commit timestamp -> merged_at or vice versa.
        """
        raw_files, _ = raw_data
        # PR has merged_at, committed_at is None
        pr_raw = raw_files["github/parquet-java/pull_885.json"]
        pr_state = adapt_apache_github_pr_to_state(pr_raw)
        assert pr_state.merged_at == datetime(2021, 3, 30, 15, 57, 8, tzinfo=timezone.utc)
        assert pr_state.committed_at is None

        # Commit has committed_at, merged_at is None
        c_raw = raw_files["github/parquet-java/pull_885_commits.json"][0]
        c_state = adapt_apache_github_commit_to_state(c_raw, repo="apache/parquet-java")
        assert c_state.committed_at == datetime(2021, 3, 25, 15, 5, 24, tzinfo=timezone.utc)
        assert c_state.merged_at is None
        assert c_state.change_type == "commit"

    def test_closed_unmerged_pr_invariants(self, raw_data) -> None:
        """Rule 6: Never convert closed + merged=false into merged (e.g. PR #10123)."""
        raw_files, _ = raw_data
        raw_10123 = raw_files["github/flink/pull_10123.json"]
        state_10123 = adapt_apache_github_pr_to_state(raw_10123)

        assert state_10123.state == "closed"
        assert state_10123.merged_at is None
        # Preserves observed command-line merge commit in extra_properties
        assert state_10123.extra_properties.get("merge_commit_sha") == "21c9b1d899c3afbca09d7409e3512ea3dc29e939"

        # Also test abandoned PR 17401
        raw_17401 = raw_files["github/flink/pull_17401.json"]
        state_17401 = adapt_apache_github_pr_to_state(raw_17401)
        assert state_17401.state == "closed"
        assert state_17401.merged_at is None

    def test_repository_scoped_pr_identity(self, raw_data) -> None:
        """Matrix Item 11: Repository-scoped PR identity in EntityRef."""
        raw_files, _ = raw_data
        raw_pr = raw_files["github/parquet-java/pull_885.json"]
        ctx = ObservationContext(
            observation_id="test_gh_ctx",
            source_instance=APACHE_GITHUB_SOURCE,
        )
        obs = adapt_apache_github_pr(raw_pr, ctx, repo="apache/parquet-java")

        assert obs.entity_ref.source_instance == APACHE_GITHUB_SOURCE
        assert obs.entity_ref.entity_kind == "code_change"
        assert obs.entity_ref.entity_id == "apache/parquet-java/885"

    def test_fork_and_upstream_identity(self, raw_data) -> None:
        """Matrix Item 13: Fork/upstream distinction preserved in extra_properties."""
        raw_files, _ = raw_data
        raw_pr = raw_files["github/parquet-java/pull_885.json"]
        state = adapt_apache_github_pr_to_state(raw_pr)

        assert state.extra_properties.get("repo") == "apache/parquet-java"
        assert state.extra_properties.get("head_repo") == "gszadovszky/parquet-mr"
        assert state.extra_properties.get("is_fork") is True


# ======================================================================
# 3. FIVE-CHAIN CANONICAL REPRESENTATION TESTS
# ======================================================================

class TestFiveChainsCanonicalRepresentation:
    """Verify that all 5 chains from the Phase 1A manifest are faithfully represented."""

    def test_chain1_parquet_declared_mention(self, canonical_bundle) -> None:
        """Matrix Item 4: Chain 1 (PARQUET-2010 ↔ PR 885) is DECLARED_MENTION."""
        bundle, _ = canonical_bundle
        alignments = [
            a for a in bundle.cross_system_alignments
            if a.subject_ref.entity_id == "PARQUET-2010" and "885" in a.corroborating_ref.entity_id
        ]
        assert len(alignments) == 1
        a = alignments[0]
        assert a.relationship_kind == "DECLARED_MENTION"
        assert a.state_comparison == "CONSISTENT"
        assert a.temporal_comparison == "COHERENT"

    def test_chain2_kafka_explicit_link_many_commits(self, canonical_bundle) -> None:
        """Matrix Item 5 & 6: Chain 2 (KAFKA-13557 ↔ PR 11617) has EXPLICIT_LINK and 5 commits."""
        bundle, _ = canonical_bundle
        alignments = [
            a for a in bundle.cross_system_alignments
            if a.subject_ref.entity_id == "KAFKA-13557" and "11617" in a.corroborating_ref.entity_id
        ]
        assert len(alignments) == 1
        a = alignments[0]
        assert a.relationship_kind == "EXPLICIT_LINK"
        assert a.state_comparison == "CONSISTENT"
        assert a.temporal_comparison == "COHERENT"

        # Verify 5 commits associated with PR 11617
        commit_rels = [
            r for r in bundle.relationships
            if r.subject_ref.entity_id == "apache/kafka/11617" and r.object_ref.entity_kind == "github_commit"
        ]
        assert len(commit_rels) == 5

    def test_chain3_avro_explicit_link(self, canonical_bundle) -> None:
        """Matrix Item 5: Chain 3 (AVRO-3234 ↔ PR 1370) has EXPLICIT_LINK."""
        bundle, _ = canonical_bundle
        alignments = [
            a for a in bundle.cross_system_alignments
            if a.subject_ref.entity_id == "AVRO-3234" and "1370" in a.corroborating_ref.entity_id
        ]
        assert len(alignments) == 1
        a = alignments[0]
        assert a.relationship_kind == "EXPLICIT_LINK"
        assert a.state_comparison == "CONSISTENT"
        assert a.temporal_comparison == "COHERENT"

    def test_chain4_flink_one_jira_many_prs(self, canonical_bundle) -> None:
        """Matrix Item 7: Chain 4 (FLINK-24409) links to 3 PRs (abandoned, master, backport)."""
        bundle, _ = canonical_bundle
        alignments = [
            a for a in bundle.cross_system_alignments
            if a.subject_ref.entity_id == "FLINK-24409"
        ]
        assert len(alignments) == 3
        pr_alignments = {a.corroborating_ref.entity_id: a for a in alignments}

        # PR 17401: abandoned unmerged
        a_17401 = pr_alignments["apache/flink/17401"]
        assert a_17401.relationship_kind == "EXPLICIT_LINK"
        assert a_17401.state_comparison == "INSUFFICIENT_EVIDENCE"
        assert a_17401.temporal_comparison == "INDETERMINATE"

        # PR 17773: merged to master
        a_17773 = pr_alignments["apache/flink/17773"]
        assert a_17773.relationship_kind == "EXPLICIT_LINK"
        assert a_17773.state_comparison == "CONSISTENT"
        assert a_17773.temporal_comparison == "COHERENT"

        # PR 17799: merged to release-1.14
        a_17799 = pr_alignments["apache/flink/17799"]
        assert a_17799.relationship_kind == "EXPLICIT_LINK"
        assert a_17799.state_comparison == "CONSISTENT"
        assert a_17799.temporal_comparison == "COHERENT"

    def test_chain5_flink_many_jira_one_pr(self, canonical_bundle) -> None:
        """Matrix Item 8: Chain 5 (FLINK-14386 + FLINK-14665 ↔ PR 10123)."""
        bundle, _ = canonical_bundle
        alignments = [
            a for a in bundle.cross_system_alignments
            if "10123" in a.corroborating_ref.entity_id
        ]
        assert len(alignments) == 2
        jira_keys = {a.subject_ref.entity_id for a in alignments}
        assert jira_keys == {"FLINK-14386", "FLINK-14665"}

        for a in alignments:
            assert a.relationship_kind == "EXPLICIT_LINK"
            # PR 10123 was closed unmerged on GitHub (command-line merge)
            assert a.state_comparison == "INSUFFICIENT_EVIDENCE"
            assert a.temporal_comparison == "INDETERMINATE"


# ======================================================================
# 4. NEGATIVE CONTROLS & REJECTION TESTS
# ======================================================================

class TestNegativeControls:
    """Verify negative controls are properly handled and produce NO spurious linkages."""

    def test_unlinked_negative_controls(self, canonical_bundle) -> None:
        """Matrix Item 9: Negative controls have NO relationships and NO alignments."""
        bundle, _ = canonical_bundle
        unlinked_keys = {"PARQUET-1812", "ZOOKEEPER-4348", "apache/parquet-java/3822"}

        # Check in observations
        observed_ids = {o.entity_ref.entity_id for o in bundle.observations}
        for u in unlinked_keys:
            assert u in observed_ids

        # Check NO relationships
        for rel in bundle.relationships:
            assert rel.subject_ref.entity_id not in unlinked_keys
            assert rel.object_ref.entity_id not in unlinked_keys

        # Check NO alignments
        for align in bundle.cross_system_alignments:
            assert align.subject_ref.entity_id not in unlinked_keys
            assert align.corroborating_ref.entity_id not in unlinked_keys

    def test_snyk_cve_false_positive_rejection(self, raw_data) -> None:
        """Matrix Item 10: AXIOS-12613773 is rejected and does NOT become a Jira WorkItemRef."""
        raw_files, _ = raw_data
        snyk_raw = raw_files["negative_controls/github/snyk_bot/pull_8.json"]
        body = snyk_raw.get("body", "")
        assert "AXIOS-12613773" in body

        # Validation rejects it
        assert is_valid_apache_jira_key("AXIOS-12613773") is False

        # Attempting to adapt as Jira issue raises ValueError
        with pytest.raises(ValueError, match="Invalid or unauthorized Jira issue key"):
            adapt_apache_jira_issue_to_state({"key": "AXIOS-12613773", "fields": {}})


# ======================================================================
# 5. PROVENANCE DEREFERENCING & BUNDLE VALIDATION
# ======================================================================

class TestProvenanceAndBundleValidation:
    """Verify that every canonical entity retains dereferenceable provenance."""

    def test_all_observations_retain_dereferenceable_provenance(self, canonical_bundle) -> None:
        """Matrix Item 14: All observations dereference against in-memory fixture dicts."""
        bundle, fixtures_by_id = canonical_bundle
        for obs in bundle.observations:
            for p in obs.provenance_refs:
                assert p.fixture_id in fixtures_by_id, f"Missing fixture {p.fixture_id}"
                fixture_data = fixtures_by_id[p.fixture_id]
                res = dereference_provenance_ref(p, fixture_data, expected_entity_ref=obs.entity_ref)
                assert res.status == "RESOLVED", (
                    f"Provenance dereferencing failed for {obs.entity_ref.entity_id}: "
                    f"status={res.status}, error={res.error_message}"
                )
                assert res.record is not None

    def test_validate_evidence_bundle_zero_issues(self, canonical_bundle) -> None:
        """Verify that validate_evidence_bundle returns strictly 0 quality issues."""
        bundle, fixtures_by_id = canonical_bundle
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures_by_id)
        assert len(issues) == 0, f"Unexpected validation issues: {[q.message for q in issues]}"


# ======================================================================
# 6. DETERMINISM & PERMUTATION INVARIANCE
# ======================================================================

class TestDeterminismAndPermutation:
    """Verify that canonical adaptation and evaluation are bit-for-bit deterministic."""

    def test_deterministic_bundle_serialization(self) -> None:
        """Matrix Item 15: Deterministic serialization produces bit-for-bit identical hashes."""
        b1, _ = build_apache_evidence_bundle(CORPUS_DIR)
        b2, _ = build_apache_evidence_bundle(CORPUS_DIR)

        json1 = json.dumps(serialize_evidence_bundle(b1), sort_keys=True, indent=2)
        json2 = json.dumps(serialize_evidence_bundle(b2), sort_keys=True, indent=2)

        hash1 = hashlib.sha256(json1.encode("utf-8")).hexdigest()
        hash2 = hashlib.sha256(json2.encode("utf-8")).hexdigest()

        assert hash1 == hash2
        assert json1 == json2

    def test_permutation_invariance_of_evaluation(self, canonical_bundle) -> None:
        """Matrix Item 16: Permuting observations produces identical evaluation results."""
        bundle, _ = canonical_bundle

        # Evaluate standard bundle
        res1 = evaluate_evidence_bundle(bundle)
        dict1 = serialize_evaluation_result(res1)
        json1 = json.dumps(dict1, sort_keys=True, indent=2)

        # Reverse observations order in new bundle
        reversed_bundle = EvidenceBundle(
            bundle_id=bundle.bundle_id,
            bundle_version=bundle.bundle_version,
            observation_contexts=bundle.observation_contexts,
            observations=tuple(reversed(bundle.observations)),
            relationships=tuple(reversed(bundle.relationships)),
            unresolved_references=bundle.unresolved_references,
            quality_issues=bundle.quality_issues,
            cross_system_alignments=tuple(reversed(bundle.cross_system_alignments)),
        )

        res2 = evaluate_evidence_bundle(reversed_bundle)
        dict2 = serialize_evaluation_result(res2)
        json2 = json.dumps(dict2, sort_keys=True, indent=2)

        assert json1 == json2


# ======================================================================
# 7. PROVIDER LEAKAGE ADVERSARIAL TEST
# ======================================================================

class TestProviderLeakageAdversarial:
    """Matrix Item 17: Adversarial execution proof that Track B evaluator

    consumes ONLY canonical state (WorkItemState, CodeChangeState) and DOES NOT
    instantiate or require JiraIssueState or GitHubPullRequestState.
    """

    def test_canonical_evaluator_execution_without_legacy_constructors(
        self, canonical_bundle
    ) -> None:
        """Adversarially intercept JiraIssueState and GitHubPullRequestState."""
        bundle, _ = canonical_bundle

        with patch.object(
            JiraIssueState,
            "__init__",
            side_effect=AssertionError("JiraIssueState must NOT be instantiated during canonical evaluation!"),
        ) as mock_jira, patch.object(
            GitHubPullRequestState,
            "__init__",
            side_effect=AssertionError("GitHubPullRequestState must NOT be instantiated during canonical evaluation!"),
        ) as mock_gh:

            result = evaluate_evidence_bundle(bundle)

            # Neither legacy constructor was invoked
            assert mock_jira.call_count == 0
            assert mock_gh.call_count == 0

        # Evaluator executed cleanly
        assert result.evaluation_id is not None
        assert result.bundle_id == bundle.bundle_id
        assert isinstance(result.findings, tuple)
        assert isinstance(result.suppressed_evaluations, tuple)
