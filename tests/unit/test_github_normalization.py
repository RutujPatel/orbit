"""Unit tests for GitHub fixture normalization (CSE-1.3)."""

from __future__ import annotations

import inspect
from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    GitHubBranchState,
    GitHubCommitState,
    GitHubPullRequestState,
    GitHubRepositoryState,
    GitHubReviewState,
)
from shadow_orbit.fixture_io import load_fixture
from shadow_orbit.github_normalization import (
    NormalizedGitHubFixture,
    normalize_github_fixture,
)
from shadow_orbit.github_validation import validate_github_fixture

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "github"
CLEAN_FIXTURE_PATH = FIXTURES_DIR / "clean_github_week_1.json"
MESSY_FIXTURE_PATH = FIXTURES_DIR / "messy_github_week_1.json"


@pytest.fixture
def clean_normalized() -> NormalizedGitHubFixture:
    raw = load_fixture(CLEAN_FIXTURE_PATH)
    validated = validate_github_fixture(raw)
    return normalize_github_fixture(validated)


class TestGitHubNormalization:
    """Normalization of validated GitHub data into EvidenceObservations."""

    def test_clean_fixture_produces_normalized_fixture(self, clean_normalized):
        assert isinstance(clean_normalized, NormalizedGitHubFixture)
        assert clean_normalized.source_instance.source_kind == "github"
        assert clean_normalized.source_instance.instance_id == "github.com/northstar"
        assert clean_normalized.observation_context.observation_id == "obs-gh-week-1"

    def test_repository_observation_structure(self, clean_normalized):
        repo_obs = [
            o for o in clean_normalized.observations
            if o.entity_ref.entity_kind == "github_repository"
        ]
        assert len(repo_obs) == 1
        obs = repo_obs[0]
        assert obs.entity_ref.entity_id == "repo-core"
        assert isinstance(obs.observed_state, GitHubRepositoryState)
        assert obs.observed_state.owner == "northstar"
        assert obs.observed_state.name == "northstar-core"
        assert obs.observed_state.default_branch == "main"
        assert len(obs.provenance_refs) == 1
        assert obs.provenance_refs[0].record_locator == "repositories[0]"

    def test_branch_observation_structure(self, clean_normalized):
        branch_obs = [
            o for o in clean_normalized.observations
            if o.entity_ref.entity_kind == "github_branch"
        ]
        assert len(branch_obs) == 2
        names = {o.observed_state.name for o in branch_obs}
        assert names == {"main", "feature/auth"}
        ids = {o.entity_ref.entity_id for o in branch_obs}
        assert ids == {"repo-core/main", "repo-core/feature/auth"}
        for obs in branch_obs:
            assert isinstance(obs.observed_state, GitHubBranchState)

    def test_commit_observation_structure(self, clean_normalized):
        commit_obs = [
            o for o in clean_normalized.observations
            if o.entity_ref.entity_kind == "github_commit"
        ]
        assert len(commit_obs) == 2
        shas = {o.observed_state.sha for o in commit_obs}
        assert shas == {"c0ffee1", "c0ffee2"}
        ids = {o.entity_ref.entity_id for o in commit_obs}
        assert ids == {"repo-core/c0ffee1", "repo-core/c0ffee2"}
        for obs in commit_obs:
            assert isinstance(obs.observed_state, GitHubCommitState)
            assert obs.observed_state.committed_at is not None

    def test_pull_request_observation_structure(self, clean_normalized):
        pr_obs = [
            o for o in clean_normalized.observations
            if o.entity_ref.entity_kind == "github_pull_request"
        ]
        assert len(pr_obs) == 2
        numbers = {o.observed_state.number for o in pr_obs}
        assert numbers == {101, 102}
        ids = {o.entity_ref.entity_id for o in pr_obs}
        assert ids == {"repo-core/101", "repo-core/102"}
        for obs in pr_obs:
            assert isinstance(obs.observed_state, GitHubPullRequestState)
            assert obs.observed_state.created_at is not None

        pr101 = next(o for o in pr_obs if o.observed_state.number == 101)
        assert pr101.observed_state.state == "merged"
        assert pr101.observed_state.merged_at is not None

    def test_review_observation_structure(self, clean_normalized):
        review_obs = [
            o for o in clean_normalized.observations
            if o.entity_ref.entity_kind == "github_review"
        ]
        assert len(review_obs) == 2
        ids = {o.entity_ref.entity_id for o in review_obs}
        assert ids == {
            "repo-core/101/rev-101-1",
            "repo-core/102/rev-102-1",
        }
        for obs in review_obs:
            assert isinstance(obs.observed_state, GitHubReviewState)
            assert obs.observed_state.submitted_at is not None

    def test_observations_are_deterministically_ordered(self, clean_normalized):
        obs = clean_normalized.observations
        keys = [
            (
                o.entity_ref.source_instance.instance_id,
                o.entity_ref.entity_kind,
                o.entity_ref.entity_id,
            )
            for o in obs
        ]
        assert keys == sorted(keys)

    def test_provenance_locators_address_original_raw_indexes(self):
        """When earlier elements are quarantined, subsequent observations use original pre-quarantine locators."""
        raw = load_fixture(MESSY_FIXTURE_PATH)
        validated = validate_github_fixture(raw)
        normalized = normalize_github_fixture(validated)

        # In messy fixture, repository 0 has:
        # branches: [0: main, 1: dup-branch (quarantined), 2: dup-branch (quarantined)]
        # commits: [0: abc1, 1: dup-sha (quarantined), 2: dup-sha (quarantined)]
        # PRs: [0: PR 201, 1: PR 202 (quarantined), 2: PR 202 (quarantined)]
        # PR 201 reviews: [0: rev-dup (quarantined), 1: rev-dup (quarantined), 2: rev-valid]
        valid_review_obs = next(
            o for o in normalized.observations
            if o.entity_ref.entity_kind == "github_review"
            and o.observed_state.review_id == "rev-valid"
        )
        assert len(valid_review_obs.provenance_refs) == 1
        # Review was at index 2 in PR 201 (which was at index 0 in repo 0)
        assert valid_review_obs.provenance_refs[0].record_locator == (
            "repositories[0].pull_requests[0].reviews[2]"
        )

    def test_messy_fixture_normalization_preserves_quarantined_and_quality(self):
        raw = load_fixture(MESSY_FIXTURE_PATH)
        validated = validate_github_fixture(raw)
        normalized = normalize_github_fixture(validated)

        assert len(normalized.quarantined_records) > 0
        reasons = {r.reason_code for r in normalized.quarantined_records}
        assert "DUPLICATE_PR_NUMBER" in reasons

        assert len(normalized.quality_issues) > 0

        pr_obs = [
            o for o in normalized.observations
            if o.entity_ref.entity_kind == "github_pull_request"
        ]
        assert len(pr_obs) == 1
        assert pr_obs[0].observed_state.number == 201
        assert pr_obs[0].observed_state.merged_at is None
        assert any(
            q.code == "invalid" and q.subject_scope == "field:merged_at"
            for q in pr_obs[0].quality_issues
        )

    def test_immutability_of_normalized_fixture(self, clean_normalized):
        with pytest.raises(AttributeError):
            clean_normalized.observations = ()  # type: ignore[misc]


class TestSourceIndependenceAndBoundaries:
    """Explicit tests enforcing source independence, no Jira leakage, and strict boundaries."""

    def test_github_normalization_does_not_import_jira_modules(self):
        import shadow_orbit.github_normalization as gn
        source = inspect.getsource(gn)
        for forbidden in (
            "shadow_orbit.types",
            "shadow_orbit.validation",
            "shadow_orbit.normalization",
            "shadow_orbit.temporal",
            "shadow_orbit.evaluation",
            "shadow_orbit.artifact",
            "shadow_orbit.human_state",
            "shadow_orbit.deltas",
            "shadow_orbit.continuity",
            "shadow_orbit.messy_acceptance",
            "shadow_orbit.acceptance",
        ):
            assert forbidden not in source, f"github_normalization must not import {forbidden}"

    def test_github_normalization_never_constructs_jira_work_items(self):
        raw = load_fixture(CLEAN_FIXTURE_PATH)
        validated = validate_github_fixture(raw)
        normalized = normalize_github_fixture(validated)

        for obs in normalized.observations:
            state = obs.observed_state
            assert type(state).__name__ != "WorkItem"
            assert not hasattr(state, "source_priority")
            assert not hasattr(state, "planned_at_period_start")
            assert not hasattr(state, "status_category")
            assert not hasattr(state, "priority_band")
            assert not hasattr(state, "changes")

    def test_no_jira_key_or_mention_extraction_occurs(self):
        """PR titles and commit messages containing Jira keys must remain untouched literal strings."""
        raw = load_fixture(CLEAN_FIXTURE_PATH)
        # Inject Jira keys into title and message
        raw["repositories"][0]["pull_requests"][0]["title"] = "[GG-123] Fix login bug (fixes PLAT-456)"
        raw["repositories"][0]["commits"][0]["message"] = "GG-123: initial commit for ticket"

        validated = validate_github_fixture(raw)
        normalized = normalize_github_fixture(validated)

        pr_obs = next(
            o for o in normalized.observations
            if o.entity_ref.entity_kind == "github_pull_request"
            and o.observed_state.number == 101
        )
        assert pr_obs.observed_state.title == "[GG-123] Fix login bug (fixes PLAT-456)"
        # Confirm no parsed mentions or links exist on the observation
        assert not hasattr(pr_obs, "jira_mentions")
        assert not hasattr(pr_obs.observed_state, "jira_keys")
        assert not hasattr(pr_obs, "relationships")

        commit_obs = next(
            o for o in normalized.observations
            if o.entity_ref.entity_kind == "github_commit"
            and o.observed_state.sha == "c0ffee1"
        )
        assert commit_obs.observed_state.message == "GG-123: initial commit for ticket"

    def test_person_logins_remain_literal_without_resolution(self):
        """GitHub author_login and reviewer_login remain exact literal source strings."""
        raw = load_fixture(CLEAN_FIXTURE_PATH)
        validated = validate_github_fixture(raw)
        normalized = normalize_github_fixture(validated)

        logins = {
            obs.observed_state.author_login
            for obs in normalized.observations
            if hasattr(obs.observed_state, "author_login")
        }
        logins |= {
            obs.observed_state.reviewer_login
            for obs in normalized.observations
            if hasattr(obs.observed_state, "reviewer_login")
        }
        assert logins == {"alice", "bob", "lead-dev"}
        for obs in normalized.observations:
            assert not hasattr(obs.observed_state, "person_id")
            assert not hasattr(obs.observed_state, "user_id")
            assert not hasattr(obs.observed_state, "jira_account_id")


class TestStateRecognition:
    """Bounded supported-state recognition for PR and review states."""

    def test_unknown_pr_state_normalized_to_unknown_with_quality_issue(self):
        raw = load_fixture(CLEAN_FIXTURE_PATH)
        raw["repositories"][0]["pull_requests"][0]["state"] = "SUPER_SPECIAL_VENDOR_STATE"
        validated = validate_github_fixture(raw)
        # Raw value preserved in validated dict
        assert validated.accepted_repositories[0]["pull_requests"][0]["state"] == "SUPER_SPECIAL_VENDOR_STATE"

        normalized = normalize_github_fixture(validated)
        pr_obs = next(
            o for o in normalized.observations
            if o.entity_ref.entity_kind == "github_pull_request"
            and o.observed_state.number == 101
        )
        assert pr_obs.observed_state.state == "unknown"
        assert any(
            q.code == "unsupported_value"
            and "SUPER_SPECIAL_VENDOR_STATE" in q.message
            and q.subject_scope == "field:state"
            for q in pr_obs.quality_issues
        )
        assert any(
            q.code == "unsupported_value"
            and "SUPER_SPECIAL_VENDOR_STATE" in q.message
            for q in normalized.quality_issues
        )

    def test_unknown_review_state_normalized_to_unknown_with_quality_issue(self):
        raw = load_fixture(CLEAN_FIXTURE_PATH)
        raw["repositories"][0]["pull_requests"][0]["reviews"][0]["state"] = "CUSTOM_REVIEW_STATUS"
        validated = validate_github_fixture(raw)
        # Raw value preserved in validated dict
        assert validated.accepted_repositories[0]["pull_requests"][0]["reviews"][0]["state"] == "CUSTOM_REVIEW_STATUS"

        normalized = normalize_github_fixture(validated)
        rev_obs = next(
            o for o in normalized.observations
            if o.entity_ref.entity_kind == "github_review"
            and o.observed_state.review_id == "rev-101-1"
        )
        assert rev_obs.observed_state.state == "unknown"
        assert any(
            q.code == "unsupported_value"
            and "CUSTOM_REVIEW_STATUS" in q.message
            and q.subject_scope == "field:state"
            for q in rev_obs.quality_issues
        )
        assert any(
            q.code == "unsupported_value"
            and "CUSTOM_REVIEW_STATUS" in q.message
            for q in normalized.quality_issues
        )


class TestPermutationInvariance:
    """Permutations of input record order produce identical normalized semantic evidence."""

    def test_input_permutation_produces_identical_semantic_evidence(self):
        doc1 = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "perm_test",
            "source_instance": {
                "source_kind": "github",
                "instance_id": "github.com/perm-org",
            },
            "observation_context": {
                "observation_id": "obs-perm",
                "observed_interval_starts_at": "2026-02-02T00:00:00Z",
                "observed_interval_ends_at_exclusive": "2026-02-09T00:00:00Z",
            },
            "repositories": [
                {
                    "repo_id": "repo-alpha",
                    "owner": "perm-org",
                    "name": "alpha",
                    "branches": [
                        {"name": "b-main"},
                        {"name": "b-feat"},
                    ],
                    "commits": [
                        {"sha": "sha-a1", "message": "msg a1"},
                        {"sha": "sha-a2", "message": "msg a2"},
                    ],
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "PR 1",
                            "state": "open",
                            "reviews": [
                                {"review_id": "r1-1", "state": "APPROVED"},
                                {"review_id": "r1-2", "state": "COMMENTED"},
                            ],
                        },
                        {
                            "number": 2,
                            "title": "PR 2",
                            "state": "closed",
                            "reviews": [
                                {"review_id": "r2-1", "state": "CHANGES_REQUESTED"},
                            ],
                        },
                    ],
                },
                {
                    "repo_id": "repo-beta",
                    "owner": "perm-org",
                    "name": "beta",
                    "branches": [
                        {"name": "dev"},
                        {"name": "release"},
                    ],
                    "commits": [
                        {"sha": "sha-b1", "message": "msg b1"},
                        {"sha": "sha-b2", "message": "msg b2"},
                    ],
                    "pull_requests": [
                        {
                            "number": 10,
                            "title": "PR 10",
                            "state": "merged",
                            "reviews": [
                                {"review_id": "rb-1", "state": "APPROVED"},
                            ],
                        },
                    ],
                },
            ],
        }

        # Permuted doc: reversed repositories, branches, commits, PRs, and reviews
        doc2 = deepcopy(doc1)
        doc2["repositories"].reverse()
        for repo in doc2["repositories"]:
            repo["branches"].reverse()
            repo["commits"].reverse()
            repo["pull_requests"].reverse()
            for pr in repo["pull_requests"]:
                pr["reviews"].reverse()

        norm1 = normalize_github_fixture(validate_github_fixture(doc1))
        norm2 = normalize_github_fixture(validate_github_fixture(doc2))

        assert len(norm1.observations) == len(norm2.observations)
        assert len(norm1.observations) == 17  # 2 repos + 4 branches + 4 commits + 3 PRs + 4 reviews

        # Verify exact 1:1 match of sorted semantic evidence
        for o1, o2 in zip(norm1.observations, norm2.observations):
            assert o1.entity_ref == o2.entity_ref
            assert o1.observed_state == o2.observed_state
            assert o1.quality_issues == o2.quality_issues


class TestImmutabilityAndAuditBoundary:
    """Verify deep immutability of evidence outputs and explicit audit storage boundary."""

    def test_containers_reject_attribute_mutation(self, clean_normalized):
        with pytest.raises(AttributeError):
            clean_normalized.observations = ()  # type: ignore[misc]

        with pytest.raises(AttributeError):
            clean_normalized.quality_issues = ()  # type: ignore[misc]

        with pytest.raises(AttributeError):
            clean_normalized.quarantined_records = ()  # type: ignore[misc]

    def test_evidence_observations_and_states_are_deeply_frozen(self, clean_normalized):
        obs = clean_normalized.observations[0]

        # EvidenceObservation is frozen
        with pytest.raises(FrozenInstanceError):
            obs.observed_state = None  # type: ignore[misc]

        # EntityRef is frozen
        with pytest.raises(FrozenInstanceError):
            obs.entity_ref.entity_id = "mutated"  # type: ignore[misc]

        # ObservationContext is frozen
        with pytest.raises(FrozenInstanceError):
            obs.observation_context.observation_id = "mutated"  # type: ignore[misc]

        # ProvenanceRef is frozen
        prov = obs.provenance_refs[0]
        with pytest.raises(FrozenInstanceError):
            prov.record_locator = "mutated"  # type: ignore[misc]

        # Payload states are frozen across all entity kinds
        repo_obs = next(o for o in clean_normalized.observations if o.entity_ref.entity_kind == "github_repository")
        with pytest.raises(FrozenInstanceError):
            repo_obs.observed_state.owner = "mutated"  # type: ignore[misc]

        branch_obs = next(o for o in clean_normalized.observations if o.entity_ref.entity_kind == "github_branch")
        with pytest.raises(FrozenInstanceError):
            branch_obs.observed_state.name = "mutated"  # type: ignore[misc]

        pr_obs = next(o for o in clean_normalized.observations if o.entity_ref.entity_kind == "github_pull_request")
        with pytest.raises(FrozenInstanceError):
            pr_obs.observed_state.title = "mutated"  # type: ignore[misc]

        rev_obs = next(o for o in clean_normalized.observations if o.entity_ref.entity_kind == "github_review")
        with pytest.raises(FrozenInstanceError):
            rev_obs.observed_state.state = "mutated"  # type: ignore[misc]

        # Collections on EvidenceObservation are immutable tuples
        assert isinstance(obs.provenance_refs, tuple)
        assert isinstance(obs.quality_issues, tuple)

    def test_audit_boundary_preserves_raw_dictionaries(self, clean_normalized):
        """raw_document and accepted_repositories intentionally remain dictionaries for auditability."""
        raw = load_fixture(CLEAN_FIXTURE_PATH)
        validated = validate_github_fixture(raw)

        # Validated container is frozen
        with pytest.raises(AttributeError):
            validated.accepted_repositories = ()  # type: ignore[misc]

        # But internal raw representations are dictionaries for source audit/traceability
        assert isinstance(validated.raw_document, dict)
        assert isinstance(validated.accepted_repositories, tuple)
        assert isinstance(validated.accepted_repositories[0], dict)
        assert isinstance(clean_normalized.raw_document, dict)


class TestNormalizationWithInvalidCollections:
    """Normalization handles fixtures where nested collections are invalid without crashing."""

    def test_invalid_branches_collection_produces_repo_issue_and_no_branches(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "bad_branches_test",
            "source_instance": {
                "source_kind": "github",
                "instance_id": "github.com/test-org",
            },
            "observation_context": {
                "observation_id": "obs-1",
            },
            "repositories": [
                {
                    "repo_id": "repo-bad",
                    "owner": "test-org",
                    "name": "bad-repo",
                    "branches": "not-an-array",
                }
            ],
        }
        validated = validate_github_fixture(doc)
        normalized = normalize_github_fixture(validated)

        # Only repository observation is emitted, 0 branch observations
        assert len(normalized.observations) == 1
        repo_obs = normalized.observations[0]
        assert repo_obs.entity_ref.entity_kind == "github_repository"
        assert any(
            q.code == "invalid" and q.subject_scope == "collection:branches"
            for q in repo_obs.quality_issues
        )

    def test_invalid_reviews_collection_produces_pr_issue_and_no_reviews(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "bad_reviews_test",
            "source_instance": {
                "source_kind": "github",
                "instance_id": "github.com/test-org",
            },
            "observation_context": {
                "observation_id": "obs-1",
            },
            "repositories": [
                {
                    "repo_id": "repo-1",
                    "owner": "test-org",
                    "name": "good-repo",
                    "pull_requests": [
                        {
                            "number": 55,
                            "title": "PR with bad reviews",
                            "state": "open",
                            "reviews": 12345,
                        }
                    ],
                }
            ],
        }
        validated = validate_github_fixture(doc)
        normalized = normalize_github_fixture(validated)

        # Repo observation + PR observation, 0 review observations
        kinds = [o.entity_ref.entity_kind for o in normalized.observations]
        assert kinds == ["github_pull_request", "github_repository"]
        pr_obs = next(o for o in normalized.observations if o.entity_ref.entity_kind == "github_pull_request")
        assert any(
            q.code == "invalid" and q.subject_scope == "collection:reviews"
            for q in pr_obs.quality_issues
        )

