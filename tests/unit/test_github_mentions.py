"""Unit tests for explicit Jira mention resolution (CSE-1.6).

Covers:
  1. Policy validation and fingerprinting (V0 contract grammar)
  2. Lexical pattern matching and boundary rules
  3. Field inspection (PR title, source_branch, target_branch, commit message, branch name)
  4. Deduplication and provenance aggregation
  5. Jira target resolution, ambiguity detection, and source instance matching
  6. SourceInstance validation
  7. Determinism and permutation invariance
  8. Immutability and input preservation
  9. Boundary and edge conditions
 10. End-to-end integration with adapted Jira evidence
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    EvidenceRelationship,
    GitHubBranchState,
    GitHubCommitState,
    GitHubPullRequestState,
    GitHubRepositoryState,
    GitHubReviewState,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    SourceInstance,
    UnresolvedReference,
    serialize_evidence_relationship,
    serialize_unresolved_reference,
)
from shadow_orbit.fixture_io import load_fixture
from shadow_orbit.github_mentions import (
    MentionLexicalPolicy,
    resolve_github_jira_mentions,
)
from shadow_orbit.github_normalization import (
    NormalizedGitHubFixture,
    normalize_github_fixture,
)
from shadow_orbit.github_validation import validate_github_fixture
from shadow_orbit.jira_evidence_adapter import adapt_jira_evidence
from shadow_orbit.normalization import normalize_fixture as normalize_jira_fixture
from shadow_orbit.validation import validate_fixture as validate_jira_fixture


# ── Shared Test Fixtures & Constants ─────────────────────────────────

GITHUB_SOURCE = SourceInstance(source_kind="github", instance_id="github.com/northstar")
JIRA_SOURCE = SourceInstance(source_kind="jira", instance_id="northstar.atlassian.net")
OTHER_JIRA_SOURCE = SourceInstance(source_kind="jira", instance_id="other.atlassian.net")

DEFAULT_POLICY = MentionLexicalPolicy(
    project_key_prefixes=frozenset({"PLAT", "GG", "INFRA"})
)


def make_github_obs(
    entity_kind: str,
    entity_id: str,
    state: any,
    obs_id: str = "obs-gh-1",
    locator: str = "items[0]",
) -> EvidenceObservation:
    ctx = ObservationContext(observation_id=obs_id, source_instance=GITHUB_SOURCE)
    ref = EntityRef(source_instance=GITHUB_SOURCE, entity_kind=entity_kind, entity_id=entity_id)
    prov = ProvenanceRef(source_instance=GITHUB_SOURCE, observation_id=obs_id, record_locator=locator)
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=ctx,
        observed_state=state,
        provenance_refs=(prov,),
    )


def make_jira_obs(
    key: str,
    obs_id: str = "obs-jira-1",
    source_instance: SourceInstance = JIRA_SOURCE,
) -> EvidenceObservation:
    ctx = ObservationContext(observation_id=obs_id, source_instance=source_instance)
    ref = EntityRef(source_instance=source_instance, entity_kind="jira_issue", entity_id=key)
    prov = ProvenanceRef(source_instance=source_instance, observation_id=obs_id, record_locator=f"work_items[{key}]")
    state = JiraIssueState(
        key=key,
        source_status="In Progress",
        source_priority="High",
        status_category="in_progress",
        priority_band="high",
        assignee="Alice",
        created_at=None,  # Not used by mentions resolver
        updated_at=None,
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=ctx,
        observed_state=state,
        provenance_refs=(prov,),
    )


def make_normalized_gh(
    observations: tuple[EvidenceObservation, ...],
    source_instance: SourceInstance = GITHUB_SOURCE,
    obs_id: str = "obs-gh-1",
    fixture_id: str = "test-fixture-1",
) -> NormalizedGitHubFixture:
    ctx = ObservationContext(observation_id=obs_id, source_instance=source_instance)
    return NormalizedGitHubFixture(
        raw_document={"fixture_id": fixture_id},
        source_instance=source_instance,
        observation_context=ctx,
        observations=observations,
        quality_issues=(),
        quarantined_records=(),
    )


# =====================================================================
# 1. Policy Validation and Fingerprinting
# =====================================================================

class TestMentionLexicalPolicy:
    def test_valid_policy_creation(self):
        policy = MentionLexicalPolicy(frozenset({"PLAT", "GG"}))
        assert policy.project_key_prefixes == frozenset({"PLAT", "GG"})

    def test_empty_prefixes_rejected(self):
        with pytest.raises(ValueError, match="non-empty"):
            MentionLexicalPolicy(frozenset())

    def test_non_string_prefix_rejected(self):
        with pytest.raises(TypeError, match="must be a string"):
            MentionLexicalPolicy(frozenset({123}))

    def test_empty_string_prefix_rejected(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            MentionLexicalPolicy(frozenset({""}))

    def test_lowercase_prefix_rejected(self):
        with pytest.raises(ValueError, match="violates V0 contract grammar"):
            MentionLexicalPolicy(frozenset({"plat"}))

    def test_mixed_case_prefix_rejected(self):
        with pytest.raises(ValueError, match="violates V0 contract grammar"):
            MentionLexicalPolicy(frozenset({"Plat"}))

    def test_digits_in_prefix_rejected(self):
        with pytest.raises(ValueError, match="violates V0 contract grammar"):
            MentionLexicalPolicy(frozenset({"PLAT2"}))

    def test_special_characters_in_prefix_rejected(self):
        with pytest.raises(ValueError, match="violates V0 contract grammar"):
            MentionLexicalPolicy(frozenset({"PLAT-AUTH"}))

    def test_policy_fingerprint_deterministic_and_sorted(self):
        p1 = MentionLexicalPolicy(frozenset({"PLAT", "GG", "INFRA"}))
        p2 = MentionLexicalPolicy(frozenset({"INFRA", "PLAT", "GG"}))
        assert p1.fingerprint == "jira-prefix-v0:GG,INFRA,PLAT"
        assert p1.fingerprint == p2.fingerprint
        assert p1.policy_id == p1.fingerprint

    def test_policy_immutability(self):
        policy = MentionLexicalPolicy(frozenset({"PLAT"}))
        with pytest.raises(FrozenInstanceError):
            policy.project_key_prefixes = frozenset({"GG"})


# =====================================================================
# 2. Lexical Pattern Matching and Boundary Rules
# =====================================================================

class TestLexicalPatternMatching:
    def test_single_match_in_pr_title(self):
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101 auth bug", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 1
        assert len(unres) == 0
        assert rels[0].object_ref.entity_id == "PLAT-101"
        assert rels[0].kind == "mentions"
        assert rels[0].basis == "lexical_match"

    def test_word_boundary_leading_alphanumeric_not_matched(self):
        # 'XPLAT-101' should NOT match 'PLAT'
        pr_state = GitHubPullRequestState(number=1, title="Fix XPLAT-101 auth bug", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 0
        assert len(unres) == 0

    def test_word_boundary_trailing_alphanumeric_not_matched(self):
        # 'PLAT-101A' should NOT match
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101A auth bug", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 0
        assert len(unres) == 0

    def test_bracketed_and_parenthesized_keys_matched(self):
        pr_state = GitHubPullRequestState(
            number=1,
            title="[PLAT-101] (GG-42): Auth update",
            state="open",
        )
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        jira_1 = make_jira_obs("PLAT-101")
        jira_2 = make_jira_obs("GG-42")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_1, jira_2), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 2
        keys = {r.object_ref.entity_id for r in rels}
        assert keys == {"PLAT-101", "GG-42"}

    def test_key_at_string_start_and_end(self):
        pr_state = GitHubPullRequestState(number=1, title="PLAT-101", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 1
        assert rels[0].object_ref.entity_id == "PLAT-101"

    def test_missing_numeric_suffix_rejected(self):
        # 'PLAT-' or 'PLAT' alone should NOT match
        pr_state = GitHubPullRequestState(number=1, title="PLAT- and PLAT discussion", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 0
        assert len(unres) == 0

    def test_prefix_subset_longest_match_precedence(self):
        # If policy has both 'PR' and 'PROJ', 'PROJ-10' should match 'PROJ-10', not 'PR-10'
        subset_policy = MentionLexicalPolicy(frozenset({"PR", "PROJ"}))
        pr_state = GitHubPullRequestState(number=1, title="PROJ-10 task and PR-20 task", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        j1 = make_jira_obs("PROJ-10")
        j2 = make_jira_obs("PR-20")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (j1, j2), JIRA_SOURCE, subset_policy)
        assert len(rels) == 2
        keys = {r.object_ref.entity_id for r in rels}
        assert keys == {"PROJ-10", "PR-20"}


# =====================================================================
# 3. Field Inspection Rules
# =====================================================================

class TestFieldInspection:
    def test_pr_source_branch_inspected(self):
        pr_state = GitHubPullRequestState(
            number=1,
            title="Ordinary title",
            state="open",
            source_branch="feature/PLAT-101-token-fix",
        )
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 1
        assert rels[0].object_ref.entity_id == "PLAT-101"
        assert len(rels[0].provenance_refs) == 1
        assert rels[0].provenance_refs[0].source_field_path == "source_branch"

    def test_pr_target_branch_inspected(self):
        pr_state = GitHubPullRequestState(
            number=1,
            title="Ordinary title",
            state="open",
            target_branch="release/PLAT-102-cut",
        )
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        jira_obs = make_jira_obs("PLAT-102")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 1
        assert rels[0].object_ref.entity_id == "PLAT-102"
        assert rels[0].provenance_refs[0].source_field_path == "target_branch"

    def test_commit_message_inspected(self):
        commit_state = GitHubCommitState(sha="c0ffee1", message="commit: solve PLAT-103 issue")
        commit_obs = make_github_obs("github_commit", "repo/c0ffee1", commit_state)
        jira_obs = make_jira_obs("PLAT-103")
        gh_norm = make_normalized_gh((commit_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 1
        assert rels[0].object_ref.entity_id == "PLAT-103"
        assert rels[0].provenance_refs[0].source_field_path == "message"

    def test_branch_name_inspected(self):
        branch_state = GitHubBranchState(name="feature/PLAT-104-cleanup")
        branch_obs = make_github_obs("github_branch", "repo/feature/PLAT-104-cleanup", branch_state)
        jira_obs = make_jira_obs("PLAT-104")
        gh_norm = make_normalized_gh((branch_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 1
        assert rels[0].object_ref.entity_id == "PLAT-104"
        assert rels[0].provenance_refs[0].source_field_path == "name"

    def test_uninspected_entities_skipped(self):
        # GitHubReviewState or GitHubRepositoryState should not be inspected
        repo_state = GitHubRepositoryState(owner="northstar", name="PLAT-101-repo")
        review_state = GitHubReviewState(review_id="rev-1", state="APPROVED")
        repo_obs = make_github_obs("github_repository", "repo-1", repo_state)
        rev_obs = make_github_obs("github_review", "repo-1/1/rev-1", review_state)
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((repo_obs, rev_obs))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 0
        assert len(unres) == 0

    def test_none_or_missing_fields_safely_skipped(self):
        pr_state = GitHubPullRequestState(
            number=1,
            title="No mentions here",
            state="open",
            source_branch=None,
            target_branch=None,
        )
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 0
        assert len(unres) == 0


# =====================================================================
# 4. Deduplication and Provenance Aggregation
# =====================================================================

class TestDeduplicationAndProvenance:
    def test_multiple_lexical_occurrences_same_field_collapses(self):
        """Multiple occurrences of the same key in one field -> 1 relationship, 1 provenance ref."""
        pr_state = GitHubPullRequestState(
            number=1,
            title="PLAT-101: implement PLAT-101 auth logic for PLAT-101",
            state="open",
        )
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state, locator="pull_requests[0]")
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 1
        assert len(unres) == 0
        rel = rels[0]
        assert rel.object_ref.entity_id == "PLAT-101"
        assert len(rel.provenance_refs) == 1
        assert rel.provenance_refs[0].source_field_path == "title"
        assert rel.provenance_refs[0].record_locator == "pull_requests[0]"

    def test_same_key_across_different_fields_aggregates_provenance(self):
        """Same key in title and source_branch of same PR -> 1 relationship, 2 provenance refs."""
        pr_state = GitHubPullRequestState(
            number=1,
            title="PLAT-101: implement auth",
            state="open",
            source_branch="feature/PLAT-101-auth",
        )
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state, locator="pull_requests[0]")
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 1
        assert len(unres) == 0
        rel = rels[0]
        assert rel.object_ref.entity_id == "PLAT-101"
        assert len(rel.provenance_refs) == 2
        field_paths = {p.source_field_path for p in rel.provenance_refs}
        assert field_paths == {"source_branch", "title"}

    def test_same_jira_key_across_different_github_entities(self):
        """Same Jira key mentioned in PR and Commit -> 2 separate relationships with own subjects."""
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state, obs_id="obs-pr")
        c_state = GitHubCommitState(sha="c0ffee1", message="Commit for PLAT-101")
        c_obs = make_github_obs("github_commit", "repo/c0ffee1", c_state, obs_id="obs-commit")
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs, c_obs))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 2
        assert len(unres) == 0
        subjects = {r.subject_ref.entity_id for r in rels}
        assert subjects == {"repo/1", "repo/c0ffee1"}
        sub_obs_ids = {r.subject_observation_id for r in rels}
        assert sub_obs_ids == {"obs-pr", "obs-commit"}

    def test_different_jira_keys_in_same_field(self):
        pr_state = GitHubPullRequestState(number=1, title="PLAT-101 and GG-202 both discussed", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        j1 = make_jira_obs("PLAT-101")
        j2 = make_jira_obs("GG-202")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (j1, j2), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 2
        keys = {r.object_ref.entity_id for r in rels}
        assert keys == {"PLAT-101", "GG-202"}


# =====================================================================
# 5. Jira Target Resolution & Ambiguity Rules
# =====================================================================

class TestTargetResolutionAndAmbiguity:
    def test_unobserved_jira_key_emits_unresolved_reference(self):
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-999 (not in jira)", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state, obs_id="obs-gh-1")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 0
        assert len(unres) == 1
        u = unres[0]
        assert u.source_ref.entity_id == "repo/1"
        assert u.source_observation_id == "obs-gh-1"
        assert u.target_entity_kind == "jira_issue"
        assert u.target_identifier == "PLAT-999"
        assert u.relationship_kind == "mentions"
        assert "not observed" in u.reason
        assert len(u.provenance_refs) == 1

    def test_same_jira_key_exists_in_multiple_supplied_jira_observations(self):
        """If multiple observations exist for the same Jira key -> never arbitrarily choose one!"""
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101 auth", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        j1 = make_jira_obs("PLAT-101", obs_id="obs-jira-A")
        j2 = make_jira_obs("PLAT-101", obs_id="obs-jira-B")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (j1, j2), JIRA_SOURCE, DEFAULT_POLICY)
        # MUST NOT arbitrarily pick j1 or j2 into an EvidenceRelationship
        assert len(rels) == 0
        assert len(unres) == 1
        u = unres[0]
        assert u.target_identifier == "PLAT-101"
        assert "Ambiguous Jira target" in u.reason
        assert "multiple observations found" in u.reason

    def test_jira_observation_with_wrong_source_instance_ignored(self):
        """Never resolve against a Jira observation with different source_instance."""
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101 auth", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        # Belongs to OTHER_JIRA_SOURCE, not JIRA_SOURCE
        other_jira_obs = make_jira_obs("PLAT-101", source_instance=OTHER_JIRA_SOURCE)
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (other_jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 0
        assert len(unres) == 1
        assert unres[0].target_identifier == "PLAT-101"
        assert "not observed" in unres[0].reason

    def test_jira_observation_with_non_jira_issue_entity_kind_ignored(self):
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101 auth", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        # Malformed observation with non-jira_issue entity kind
        weird_ref = EntityRef(source_instance=JIRA_SOURCE, entity_kind="github_commit", entity_id="PLAT-101")
        weird_obs = EvidenceObservation(
            entity_ref=weird_ref,
            observation_context=ObservationContext(observation_id="o1", source_instance=JIRA_SOURCE),
            observed_state=pr_state,
        )
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (weird_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 0
        assert len(unres) == 1
        assert unres[0].target_identifier == "PLAT-101"

    def test_mix_of_resolved_and_unresolved_keys(self):
        pr_state = GitHubPullRequestState(
            number=1,
            title="PLAT-101 is ready but PLAT-999 is missing",
            state="open",
        )
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert len(rels) == 1
        assert rels[0].object_ref.entity_id == "PLAT-101"
        assert len(unres) == 1
        assert unres[0].target_identifier == "PLAT-999"


# =====================================================================
# 6. SourceInstance Validation
# =====================================================================

class TestSourceInstanceValidation:
    def test_reject_non_jira_target_source_instance(self):
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        gh_norm = make_normalized_gh((pr_obs,))
        invalid_source = SourceInstance(source_kind="github", instance_id="github.com/northstar")

        with pytest.raises(ValueError, match="source_kind='jira'"):
            resolve_github_jira_mentions(gh_norm, (), invalid_source, DEFAULT_POLICY)

    def test_reject_non_github_source_normalized_fixture(self):
        invalid_gh_source = SourceInstance(source_kind="jira", instance_id="northstar.atlassian.net")
        gh_norm = make_normalized_gh((), source_instance=invalid_gh_source)

        with pytest.raises(ValueError, match="source_kind='github'"):
            resolve_github_jira_mentions(gh_norm, (), JIRA_SOURCE, DEFAULT_POLICY)


# =====================================================================
# 7. Determinism and Permutation Invariance
# =====================================================================

class TestDeterminismAndInvariance:
    def test_repeated_calls_produce_identical_output(self):
        pr_state = GitHubPullRequestState(
            number=101,
            title="Fix PLAT-101 and GG-202",
            state="open",
            source_branch="feature/INFRA-50-auth",
        )
        c_state = GitHubCommitState(sha="c0ffee1", message="Commit for PLAT-101")
        b_state = GitHubBranchState(name="feature/PLAT-101-legacy")

        gh_norm = make_normalized_gh((
            make_github_obs("github_pull_request", "repo/101", pr_state),
            make_github_obs("github_commit", "repo/c0ffee1", c_state),
            make_github_obs("github_branch", "repo/feature/PLAT-101-legacy", b_state),
        ))

        jira_obs = (
            make_jira_obs("PLAT-101"),
            make_jira_obs("GG-202"),
        )

        r1, u1 = resolve_github_jira_mentions(gh_norm, jira_obs, JIRA_SOURCE, DEFAULT_POLICY)
        r2, u2 = resolve_github_jira_mentions(gh_norm, jira_obs, JIRA_SOURCE, DEFAULT_POLICY)

        assert r1 == r2
        assert u1 == u2

    def test_github_observation_order_permutation_invariance(self):
        pr_state = GitHubPullRequestState(number=101, title="Fix PLAT-101", state="open")
        c_state = GitHubCommitState(sha="c0ffee1", message="Commit for GG-202")
        obs_a = make_github_obs("github_pull_request", "repo/101", pr_state)
        obs_b = make_github_obs("github_commit", "repo/c0ffee1", c_state)

        norm_1 = make_normalized_gh((obs_a, obs_b))
        norm_2 = make_normalized_gh((obs_b, obs_a))

        j1 = make_jira_obs("PLAT-101")
        j2 = make_jira_obs("GG-202")

        r1, u1 = resolve_github_jira_mentions(norm_1, (j1, j2), JIRA_SOURCE, DEFAULT_POLICY)
        r2, u2 = resolve_github_jira_mentions(norm_2, (j1, j2), JIRA_SOURCE, DEFAULT_POLICY)

        assert r1 == r2
        assert u1 == u2

    def test_jira_observation_order_permutation_invariance(self):
        pr_state = GitHubPullRequestState(number=101, title="Fix PLAT-101 and GG-202", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/101", pr_state)
        norm = make_normalized_gh((pr_obs,))

        j1 = make_jira_obs("PLAT-101")
        j2 = make_jira_obs("GG-202")

        r1, u1 = resolve_github_jira_mentions(norm, (j1, j2), JIRA_SOURCE, DEFAULT_POLICY)
        r2, u2 = resolve_github_jira_mentions(norm, (j2, j1), JIRA_SOURCE, DEFAULT_POLICY)

        assert r1 == r2
        assert u1 == u2


# =====================================================================
# 8. Immutability and Safety
# =====================================================================

class TestImmutabilityAndSafety:
    def test_output_collections_are_immutable(self):
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert isinstance(rels, tuple)
        assert isinstance(unres, tuple)
        assert isinstance(rels[0].provenance_refs, tuple)

    def test_inputs_are_not_mutated(self):
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs,))

        obs_copy = deepcopy(pr_obs)
        jira_copy = deepcopy(jira_obs)

        resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, DEFAULT_POLICY)

        assert pr_obs == obs_copy
        assert jira_obs == jira_copy

    def test_serialization_supports_mentions_and_lexical_match(self):
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101 and UNKNOWN-1", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        jira_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs,))
        policy = MentionLexicalPolicy(frozenset({"PLAT", "UNKNOWN"}))

        rels, unres = resolve_github_jira_mentions(gh_norm, (jira_obs,), JIRA_SOURCE, policy)
        assert len(rels) == 1
        assert len(unres) == 1

        rel_dict = serialize_evidence_relationship(rels[0])
        assert rel_dict["kind"] == "mentions"
        assert rel_dict["basis"] == "lexical_match"
        assert rel_dict["subject_ref"]["entity_id"] == "repo/1"
        assert rel_dict["object_ref"]["entity_id"] == "PLAT-101"

        unres_dict = serialize_unresolved_reference(unres[0])
        assert unres_dict["relationship_kind"] == "mentions"
        assert unres_dict["target_identifier"] == "UNKNOWN-1"


# =====================================================================
# 9. Boundary and Edge Cases
# =====================================================================

class TestBoundaryCases:
    def test_empty_github_observations(self):
        gh_norm = make_normalized_gh(())
        j_obs = make_jira_obs("PLAT-101")
        rels, unres = resolve_github_jira_mentions(gh_norm, (j_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert rels == ()
        assert unres == ()

    def test_empty_jira_observations(self):
        pr_state = GitHubPullRequestState(number=1, title="Fix PLAT-101", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (), JIRA_SOURCE, DEFAULT_POLICY)
        assert rels == ()
        assert len(unres) == 1
        assert unres[0].target_identifier == "PLAT-101"

    def test_no_mentions_in_text(self):
        pr_state = GitHubPullRequestState(number=1, title="Refactor user login controller", state="open")
        pr_obs = make_github_obs("github_pull_request", "repo/1", pr_state)
        j_obs = make_jira_obs("PLAT-101")
        gh_norm = make_normalized_gh((pr_obs,))

        rels, unres = resolve_github_jira_mentions(gh_norm, (j_obs,), JIRA_SOURCE, DEFAULT_POLICY)
        assert rels == ()
        assert unres == ()


# =====================================================================
# 10. End-to-End Integration with Real Adapters
# =====================================================================

class TestEndToEndMentionIntegration:
    @pytest.fixture
    def adapted_jira_fixture(self):
        jira_raw_path = Path(__file__).resolve().parents[2] / "fixtures" / "jira" / "northstar_clean_week_1.json"
        raw_doc = load_fixture(jira_raw_path)
        validated = validate_jira_fixture(raw_doc)
        normalized = normalize_jira_fixture(validated)
        source_instance = SourceInstance(source_kind="jira", instance_id="northstar-jira")
        ctx, obs, quality = adapt_jira_evidence(
            normalized=normalized,
            source_instance=source_instance,
            observation_id="obs-jira-test-1",
        )
        return source_instance, obs

    def test_integration_with_clean_jira_observations(self, adapted_jira_fixture):
        jira_source, jira_observations = adapted_jira_fixture

        # In clean Jira fixture, we know PLAT-101, PLAT-102, PLAT-103, ... exist
        # Create GitHub observations mentioning PLAT-101 and an unobserved PLAT-999
        pr_state = GitHubPullRequestState(
            number=101,
            title="Implement auth middleware for PLAT-101 and PLAT-999",
            state="merged",
            source_branch="feature/PLAT-101-auth",
        )
        commit_state = GitHubCommitState(
            sha="c0ffee1",
            message="Merge commit addressing PLAT-101",
        )
        gh_norm = make_normalized_gh((
            make_github_obs("github_pull_request", "repo-core/101", pr_state, obs_id="obs-gh-test-1"),
            make_github_obs("github_commit", "repo-core/c0ffee1", commit_state, obs_id="obs-gh-test-1"),
        ))

        policy = MentionLexicalPolicy(frozenset({"PLAT"}))
        rels, unres = resolve_github_jira_mentions(
            normalized=gh_norm,
            jira_observations=jira_observations,
            jira_source_instance=jira_source,
            policy=policy,
        )

        # PR 101 mentions PLAT-101 (resolved) and PLAT-999 (unresolved)
        # Commit c0ffee1 mentions PLAT-101 (resolved)
        assert len(rels) == 2
        assert len(unres) == 1

        # Check resolved relationships
        rel_map = {(r.subject_ref.entity_id, r.object_ref.entity_id): r for r in rels}
        assert ("repo-core/101", "PLAT-101") in rel_map
        assert ("repo-core/c0ffee1", "PLAT-101") in rel_map

        pr_rel = rel_map[("repo-core/101", "PLAT-101")]
        assert pr_rel.subject_observation_id == "obs-gh-test-1"
        assert pr_rel.object_observation_id == "obs-jira-test-1"
        assert pr_rel.kind == "mentions"
        assert pr_rel.basis == "lexical_match"
        # PR rel provenance covers both 'source_branch' and 'title'
        prov_fields = {p.source_field_path for p in pr_rel.provenance_refs}
        assert prov_fields == {"source_branch", "title"}

        # Check unresolved reference
        unres_item = unres[0]
        assert unres_item.source_ref.entity_id == "repo-core/101"
        assert unres_item.target_identifier == "PLAT-999"
        assert unres_item.relationship_kind == "mentions"
        assert "not observed" in unres_item.reason
