"""Unit tests for GitHub structural relationship resolution (CSE-1.5).

Covers all authorized relationship predicates, endpoint resolution rules,
provenance attribution, quarantine isolation, fork scoping, deduplication,
ordering, immutability, and boundary protections.
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
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    SourceInstance,
    UnresolvedReference,
    serialize_evidence_relationship,
    serialize_unresolved_reference,
)
from shadow_orbit.fixture_io import load_fixture
from shadow_orbit.github_normalization import (
    NormalizedGitHubFixture,
    normalize_github_fixture,
)
from shadow_orbit.github_relationships import resolve_github_relationships
from shadow_orbit.github_validation import validate_github_fixture


FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "github"
CLEAN_FIXTURE_PATH = FIXTURES_DIR / "clean_github_week_1.json"
MESSY_FIXTURE_PATH = FIXTURES_DIR / "messy_github_week_1.json"


@pytest.fixture
def clean_normalized() -> NormalizedGitHubFixture:
    raw = load_fixture(CLEAN_FIXTURE_PATH)
    validated = validate_github_fixture(raw)
    return normalize_github_fixture(validated)


@pytest.fixture
def messy_normalized() -> NormalizedGitHubFixture:
    raw = load_fixture(MESSY_FIXTURE_PATH)
    validated = validate_github_fixture(raw)
    return normalize_github_fixture(validated)


# =====================================================================
# 1. Repository Membership (belongs_to_repository)
# =====================================================================


class TestBelongsToRepository:
    """Branches, commits, and pull requests belong to their containing repository."""

    def test_clean_fixture_repository_membership(self, clean_normalized):
        rels, unres = resolve_github_relationships(clean_normalized)
        repo_rels = [r for r in rels if r.kind == "belongs_to_repository"]

        # In clean fixture: 2 branches + 2 commits + 2 PRs = 6 relationships
        assert len(repo_rels) == 6

        subjects = {r.subject_ref.entity_id for r in repo_rels}
        assert subjects == {
            "repo-core/main",
            "repo-core/feature/auth",
            "repo-core/c0ffee1",
            "repo-core/c0ffee2",
            "repo-core/101",
            "repo-core/102",
        }

        for r in repo_rels:
            assert r.object_ref.entity_kind == "github_repository"
            assert r.object_ref.entity_id == "repo-core"
            assert r.basis == "structural_association"
            assert r.subject_observation_id == "obs-gh-week-1"
            assert r.object_observation_id == "obs-gh-week-1"
            assert len(r.provenance_refs) >= 1

    def test_branch_belongs_to_repository_provenance(self, clean_normalized):
        rels, _ = resolve_github_relationships(clean_normalized)
        main_rel = next(
            r for r in rels
            if r.kind == "belongs_to_repository"
            and r.subject_ref.entity_id == "repo-core/main"
        )
        assert main_rel.provenance_refs[0].record_locator == "repositories[0].branches[0]"
        assert main_rel.provenance_refs[0].source_field_path is None  # structural nesting


# =====================================================================
# 2. Review Parentage (review_of)
# =====================================================================


class TestReviewOf:
    """Reviews belong to their containing pull request."""

    def test_clean_fixture_review_of_relationships(self, clean_normalized):
        rels, _ = resolve_github_relationships(clean_normalized)
        rev_rels = [r for r in rels if r.kind == "review_of"]

        assert len(rev_rels) == 2
        rev1 = next(r for r in rev_rels if r.subject_ref.entity_id == "repo-core/101/rev-101-1")
        assert rev1.object_ref.entity_kind == "github_pull_request"
        assert rev1.object_ref.entity_id == "repo-core/101"
        assert rev1.basis == "structural_association"
        assert rev1.provenance_refs[0].record_locator == (
            "repositories[0].pull_requests[0].reviews[0]"
        )
        assert rev1.provenance_refs[0].source_field_path is None  # structural nesting

        rev2 = next(r for r in rev_rels if r.subject_ref.entity_id == "repo-core/102/rev-102-1")
        assert rev2.object_ref.entity_id == "repo-core/102"


# =====================================================================
# 3. Base Branch (has_base_branch)
# =====================================================================


class TestHasBaseBranch:
    """PR -> base branch via target_branch field."""

    def test_clean_fixture_has_base_branch(self, clean_normalized):
        rels, unres = resolve_github_relationships(clean_normalized)
        base_rels = [r for r in rels if r.kind == "has_base_branch"]

        # Both PR 101 and 102 target "main", which exists in repo
        assert len(base_rels) == 2
        for r in base_rels:
            assert r.object_ref.entity_kind == "github_branch"
            assert r.object_ref.entity_id == "repo-core/main"
            assert r.basis == "structural_association"
            assert r.provenance_refs[0].source_field_path == "target_branch"

    def test_unobserved_base_branch_emits_unresolved_reference(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "missing_base_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "r1",
                    "owner": "o",
                    "name": "n",
                    "branches": [{"name": "dev"}],
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "PR 1",
                            "state": "open",
                            "target_branch": "nonexistent_branch",
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        assert not any(r.kind == "has_base_branch" for r in rels)
        unres_base = [u for u in unres if u.relationship_kind == "has_base_branch"]
        assert len(unres_base) == 1
        assert unres_base[0].source_ref.entity_id == "r1/1"
        assert unres_base[0].target_entity_kind == "github_branch"
        assert unres_base[0].target_identifier == "r1/nonexistent_branch"
        assert "not observed" in unres_base[0].reason

    def test_none_target_branch_emits_no_relationship_or_unresolved(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "none_base_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "r1",
                    "owner": "o",
                    "name": "n",
                    "pull_requests": [
                        {"number": 1, "title": "PR 1", "state": "open", "target_branch": None}
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        assert not any(r.kind == "has_base_branch" for r in rels)
        assert not any(u.relationship_kind == "has_base_branch" for u in unres)


# =====================================================================
# 4. Head Branch (has_head_branch)
# =====================================================================


class TestHasHeadBranch:
    """PR -> head branch via source_branch field (fork-aware)."""

    def test_observed_head_branch_resolves(self, clean_normalized):
        rels, unres = resolve_github_relationships(clean_normalized)

        # PR 102 source_branch is "feature/auth", which is observed in repo-core
        pr102_head = next(
            r for r in rels
            if r.kind == "has_head_branch" and r.subject_ref.entity_id == "repo-core/102"
        )
        assert pr102_head.object_ref.entity_id == "repo-core/feature/auth"
        assert pr102_head.provenance_refs[0].source_field_path == "source_branch"

    def test_unobserved_head_branch_emits_unresolved_reference(self, clean_normalized):
        rels, unres = resolve_github_relationships(clean_normalized)

        # PR 101 source_branch is "feature/auth-base", which is NOT observed in repo-core
        assert not any(
            r.kind == "has_head_branch" and r.subject_ref.entity_id == "repo-core/101"
            for r in rels
        )
        pr101_unres = next(
            u for u in unres
            if u.relationship_kind == "has_head_branch"
            and u.source_ref.entity_id == "repo-core/101"
        )
        assert pr101_unres.target_identifier == "repo-core/feature/auth-base"
        assert "not observed" in pr101_unres.reason


# =====================================================================
# 5. Explicit PR -> Commit Containment (contains_commit)
# =====================================================================


class TestContainsCommit:
    """PR -> commit from explicit pull_request_commits associations."""

    def test_explicit_commit_associations_resolve(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "pr_commits_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "repo-1",
                    "owner": "org",
                    "name": "r1",
                    "commits": [
                        {"sha": "c111", "message": "First commit"},
                        {"sha": "c222", "message": "Second commit"},
                    ],
                    "pull_requests": [
                        {
                            "number": 50,
                            "title": "PR 50",
                            "state": "open",
                            "pull_request_commits": [
                                {"sha": "c111"},
                                {"sha": "c222"},
                            ],
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        cc_rels = [r for r in rels if r.kind == "contains_commit"]
        assert len(cc_rels) == 2

        target_shas = {r.object_ref.entity_id for r in cc_rels}
        assert target_shas == {"repo-1/c111", "repo-1/c222"}

        for r in cc_rels:
            assert r.subject_ref.entity_id == "repo-1/50"
            assert r.basis == "structural_association"
            assert r.provenance_refs[0].source_field_path == "pull_request_commits"

    def test_duplicate_pull_request_commits_collapse_deterministically(self):
        """Duplicate logical edges collapse into one, preserving all supporting provenance."""
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "dup_prc_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "repo-1",
                    "owner": "org",
                    "name": "r1",
                    "commits": [{"sha": "c111", "message": "Commit"}],
                    "pull_requests": [
                        {
                            "number": 10,
                            "title": "PR 10",
                            "state": "open",
                            "pull_request_commits": [
                                {"sha": "c111"},
                                {"sha": "c111"},  # duplicate logical edge
                            ],
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, _ = resolve_github_relationships(norm)

        cc_rels = [r for r in rels if r.kind == "contains_commit"]
        # Must collapse to exactly 1 logical relationship
        assert len(cc_rels) == 1
        assert cc_rels[0].subject_ref.entity_id == "repo-1/10"
        assert cc_rels[0].object_ref.entity_id == "repo-1/c111"

    def test_unobserved_associated_commit_emits_unresolved_reference(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "missing_commit_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "repo-1",
                    "owner": "org",
                    "name": "r1",
                    "commits": [],
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "PR",
                            "state": "open",
                            "pull_request_commits": [{"sha": "missing_sha"}],
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        assert not any(r.kind == "contains_commit" for r in rels)
        unres_cc = [u for u in unres if u.relationship_kind == "contains_commit"]
        assert len(unres_cc) == 1
        assert unres_cc[0].target_identifier == "repo-1/missing_sha"
        assert "not observed" in unres_cc[0].reason

    def test_no_contains_commit_inferred_without_explicit_association(self, clean_normalized):
        """Clean fixture has commits and PRs, but NO pull_request_commits array.

        Must NOT infer containment from commit messages, timestamps, or SHAs.
        """
        rels, unres = resolve_github_relationships(clean_normalized)
        assert not any(r.kind == "contains_commit" for r in rels)
        assert not any(u.relationship_kind == "contains_commit" for u in unres)


# =====================================================================
# 6. Explicit Head and Base Commits (has_head_commit, has_base_commit)
# =====================================================================


class TestHeadAndBaseCommits:
    """Explicit head_commit_sha and base_commit_sha."""

    def test_explicit_head_and_base_commit_resolve(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "head_base_commit_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "repo-1",
                    "owner": "org",
                    "name": "r1",
                    "commits": [
                        {"sha": "head_sha_123", "message": "Head commit"},
                        {"sha": "base_sha_456", "message": "Base commit"},
                    ],
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "PR 1",
                            "state": "open",
                            "head_commit_sha": "head_sha_123",
                            "base_commit_sha": "base_sha_456",
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        head_rel = next(r for r in rels if r.kind == "has_head_commit")
        assert head_rel.subject_ref.entity_id == "repo-1/1"
        assert head_rel.object_ref.entity_id == "repo-1/head_sha_123"
        assert head_rel.provenance_refs[0].source_field_path == "head_commit_sha"

        base_rel = next(r for r in rels if r.kind == "has_base_commit")
        assert base_rel.subject_ref.entity_id == "repo-1/1"
        assert base_rel.object_ref.entity_id == "repo-1/base_sha_456"
        assert base_rel.provenance_refs[0].source_field_path == "base_commit_sha"

    def test_no_transitive_derivation_of_head_commit(self, clean_normalized):
        """PR has source_branch -> branch has head_commit_id.

        Resolver must NOT emit has_head_commit via transitive derivation!
        """
        rels, unres = resolve_github_relationships(clean_normalized)
        assert not any(r.kind == "has_head_commit" for r in rels)
        assert not any(r.kind == "has_base_commit" for r in rels)


# =====================================================================
# 7. Fork Scoping and Cross-Repository Boundaries
# =====================================================================


class TestForkScoping:
    """Fork head branches must retain fork repository scope."""

    def test_explicit_fork_head_repository_resolves_to_fork_branch(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "fork_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "upstream-repo",
                    "owner": "org",
                    "name": "upstream",
                    "branches": [{"name": "main"}],
                    "pull_requests": [
                        {
                            "number": 42,
                            "title": "Community contribution",
                            "state": "open",
                            "target_branch": "main",
                            "source_branch": "feature/fix",
                            "head_repository_id": "contributor-fork",
                            "is_fork": True,
                        }
                    ],
                },
                {
                    "repo_id": "contributor-fork",
                    "owner": "contributor",
                    "name": "upstream-fork",
                    "branches": [{"name": "feature/fix"}],
                },
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        head_branch_rel = next(r for r in rels if r.kind == "has_head_branch")
        assert head_branch_rel.subject_ref.entity_id == "upstream-repo/42"
        # Must be scoped to the fork repository, NOT the upstream repository!
        assert head_branch_rel.object_ref.entity_id == "contributor-fork/feature/fix"

    def test_fork_pr_missing_head_repository_emits_unresolved(self):
        """Fork PR without explicit head_repository_id must produce unresolved reference."""
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "fork_missing_repo_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "upstream-repo",
                    "owner": "org",
                    "name": "upstream",
                    "branches": [{"name": "main"}],
                    "pull_requests": [
                        {
                            "number": 42,
                            "title": "Fork PR without head repo",
                            "state": "open",
                            "target_branch": "main",
                            "source_branch": "feature/fix",
                            "is_fork": True,
                            # head_repository_id intentionally absent
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        assert not any(r.kind == "has_head_branch" for r in rels)
        unres_head = next(u for u in unres if u.relationship_kind == "has_head_branch")
        assert unres_head.source_ref.entity_id == "upstream-repo/42"
        assert "originates from a fork" in unres_head.reason
        assert "no explicit head_repository_id" in unres_head.reason

    def test_same_branch_name_across_repositories_retains_scope(self):
        """main branch in repo A is not main branch in repo B."""
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "same_branch_diff_repo",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "repo-a",
                    "owner": "org",
                    "name": "a",
                    "branches": [{"name": "main"}],
                },
                {
                    "repo_id": "repo-b",
                    "owner": "org",
                    "name": "b",
                    "branches": [{"name": "main"}],
                },
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, _ = resolve_github_relationships(norm)

        a_main_rel = next(
            r for r in rels
            if r.kind == "belongs_to_repository" and r.subject_ref.entity_id == "repo-a/main"
        )
        b_main_rel = next(
            r for r in rels
            if r.kind == "belongs_to_repository" and r.subject_ref.entity_id == "repo-b/main"
        )
        assert a_main_rel.object_ref.entity_id == "repo-a"
        assert b_main_rel.object_ref.entity_id == "repo-b"
        assert a_main_rel.subject_ref != b_main_rel.subject_ref


# =====================================================================
# 8. Quarantine Isolation
# =====================================================================


class TestQuarantineIsolation:
    """Quarantined entities must never become resolved endpoints."""

    def test_messy_fixture_quarantined_entities_excluded(self, messy_normalized):
        rels, unres = resolve_github_relationships(messy_normalized)

        # In messy fixture:
        # - dup-branch is quarantined -> must not appear in any relationship
        # - dup-sha is quarantined -> must not appear in any relationship
        # - PR 202 (both duplicates) quarantined -> must not appear
        # - rev-dup (both duplicates) quarantined -> must not appear

        all_rel_entities = {r.subject_ref.entity_id for r in rels} | {
            r.object_ref.entity_id for r in rels
        }

        assert not any("dup-branch" in eid for eid in all_rel_entities)
        assert not any("dup-sha" in eid for eid in all_rel_entities)
        assert not any("202" in eid for eid in all_rel_entities)
        assert not any("rev-dup" in eid for eid in all_rel_entities)

    def test_reference_to_quarantined_branch_produces_unresolved_with_quarantine_reason(
        self,
    ):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "quarantined_ref_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "repo-1",
                    "owner": "org",
                    "name": "r1",
                    "branches": [
                        {"name": "bad-branch"},
                        {"name": "bad-branch"},  # duplicate -> quarantined
                    ],
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "PR targeting duplicate branch",
                            "state": "open",
                            "target_branch": "bad-branch",
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        assert not any(r.kind == "has_base_branch" for r in rels)
        unres_base = next(u for u in unres if u.relationship_kind == "has_base_branch")
        assert "quarantined" in unres_base.reason


# =====================================================================
# 9. Deterministic Ordering and Permutation Invariance
# =====================================================================


class TestDeterministicOrdering:
    """Relationships and unresolved references are deterministically ordered."""

    def test_clean_relationships_deterministically_ordered(self, clean_normalized):
        rels, unres = resolve_github_relationships(clean_normalized)
        rel_keys = [
            (
                r.kind,
                r.subject_ref.entity_id,
                r.object_ref.entity_id,
                r.subject_observation_id,
                r.object_observation_id,
            )
            for r in rels
        ]
        assert rel_keys == sorted(rel_keys)

        unres_keys = [
            (
                u.relationship_kind,
                u.source_ref.entity_id,
                u.target_entity_kind,
                u.target_identifier,
                u.reason,
            )
            for u in unres
        ]
        assert unres_keys == sorted(unres_keys)

    def test_permutation_invariance(self, clean_normalized):
        """Permuting the order of observations produces identical relationships."""
        reversed_obs = tuple(reversed(clean_normalized.observations))
        permuted_norm = NormalizedGitHubFixture(
            raw_document=clean_normalized.raw_document,
            source_instance=clean_normalized.source_instance,
            observation_context=clean_normalized.observation_context,
            observations=reversed_obs,
            quality_issues=clean_normalized.quality_issues,
            quarantined_records=clean_normalized.quarantined_records,
        )

        rels1, unres1 = resolve_github_relationships(clean_normalized)
        rels2, unres2 = resolve_github_relationships(permuted_norm)

        assert rels1 == rels2
        assert unres1 == unres2


# =====================================================================
# 10. Immutability and Audit Boundary
# =====================================================================


class TestImmutability:
    """Inputs and outputs must be immutable."""

    def test_normalized_fixture_unchanged(self, clean_normalized):
        obs_before = deepcopy(clean_normalized.observations)
        resolve_github_relationships(clean_normalized)
        assert clean_normalized.observations == obs_before

    def test_output_relationships_are_frozen(self, clean_normalized):
        rels, _ = resolve_github_relationships(clean_normalized)
        r = rels[0]
        with pytest.raises(FrozenInstanceError):
            r.kind = "mutated"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            r.subject_ref = None  # type: ignore[misc]

    def test_output_unresolved_references_are_frozen(self, clean_normalized):
        _, unres = resolve_github_relationships(clean_normalized)
        u = unres[0]
        with pytest.raises(FrozenInstanceError):
            u.relationship_kind = "mutated"  # type: ignore[misc]


# =====================================================================
# 11. Partial Coverage
# =====================================================================


class TestPartialCoverage:
    """Partial association collections do not mean 'no relationships'."""

    def test_partial_completeness_flags_do_not_block_relationships(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "partial_cov_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "source_completeness": {
                "repositories_complete": True,
                "branches_complete": False,
                "commits_complete": False,
                "pull_requests_complete": False,
                "reviews_complete": False,
            },
            "repositories": [
                {
                    "repo_id": "r1",
                    "owner": "o",
                    "name": "n",
                    "branches": [{"name": "main"}],
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "PR 1",
                            "state": "open",
                            "target_branch": "main",
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        # Explicitly supplied relationships are still resolved!
        assert any(r.kind == "has_base_branch" for r in rels)
        assert any(r.kind == "belongs_to_repository" for r in rels)


# =====================================================================
# 12. Serialization Round-Trip
# =====================================================================


class TestSerialization:
    """Serializers produce JSON-safe dicts."""

    def test_serialize_evidence_relationship(self, clean_normalized):
        rels, _ = resolve_github_relationships(clean_normalized)
        serialized = serialize_evidence_relationship(rels[0])
        assert "subject_ref" in serialized
        assert "object_ref" in serialized
        assert "kind" in serialized
        assert "basis" in serialized
        assert "subject_observation_id" in serialized
        assert "object_observation_id" in serialized
        assert "provenance_refs" in serialized

    def test_serialize_unresolved_reference(self, clean_normalized):
        _, unres = resolve_github_relationships(clean_normalized)
        serialized = serialize_unresolved_reference(unres[0])
        assert "source_ref" in serialized
        assert "source_observation_id" in serialized
        assert "target_entity_kind" in serialized
        assert "target_identifier" in serialized
        assert "relationship_kind" in serialized
        assert "reason" in serialized
        assert "provenance_refs" in serialized


# =====================================================================
# 13. Empty Input
# =====================================================================


class TestEmptyInput:
    """Empty fixtures produce empty results without error."""

    def test_empty_repositories_produces_empty_results(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "empty_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)
        assert rels == ()
        assert unres == ()


# =====================================================================
# 14. Non-Goals and CSE-1.6 Boundary Enforcements
# =====================================================================


class TestNonGoalsAndBoundaries:
    """Enforce non-goals: no Jira mentions, no text extraction, no scores."""

    def test_no_jira_key_extraction_in_relationships(self, clean_normalized):
        rels, unres = resolve_github_relationships(clean_normalized)
        for r in rels:
            assert not hasattr(r, "jira_keys")
            assert not hasattr(r, "mentions")
            assert not hasattr(r, "score")
            assert not hasattr(r, "confidence")
            assert not hasattr(r, "severity")
            assert not hasattr(r, "risk")
            assert r.basis == "structural_association"


# =====================================================================
# 15. Endpoint Observation IDs and Quarantine Edge Cases
# =====================================================================


class TestEndpointObservationsAndEdgeCases:
    """Explicit endpoint observation IDs and quarantine handling."""

    def test_endpoint_observation_ids_explicitly_identified(self, clean_normalized):
        rels, _ = resolve_github_relationships(clean_normalized)
        for r in rels:
            assert r.subject_observation_id == "obs-gh-week-1"
            assert r.object_observation_id == "obs-gh-week-1"
            assert isinstance(r.subject_observation_id, str)
            assert isinstance(r.object_observation_id, str)

    def test_contains_commit_to_quarantined_commit_emits_unresolved(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "q_commit_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "r1",
                    "owner": "o",
                    "name": "n",
                    "commits": [
                        {"sha": "dup_sha", "message": "1"},
                        {"sha": "dup_sha", "message": "2"},  # duplicate -> quarantined
                    ],
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "PR",
                            "state": "open",
                            "pull_request_commits": [{"sha": "dup_sha"}],
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        assert not any(r.kind == "contains_commit" for r in rels)
        unres_cc = next(u for u in unres if u.relationship_kind == "contains_commit")
        assert "quarantined" in unres_cc.reason

    def test_has_head_commit_to_quarantined_commit_emits_unresolved(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "q_head_commit_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "r1",
                    "owner": "o",
                    "name": "n",
                    "commits": [
                        {"sha": "dup_sha", "message": "1"},
                        {"sha": "dup_sha", "message": "2"},  # duplicate -> quarantined
                    ],
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "PR",
                            "state": "open",
                            "head_commit_sha": "dup_sha",
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        assert not any(r.kind == "has_head_commit" for r in rels)
        unres_hc = next(u for u in unres if u.relationship_kind == "has_head_commit")
        assert "quarantined" in unres_hc.reason

    def test_has_base_commit_to_quarantined_commit_emits_unresolved(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "q_base_commit_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "r1",
                    "owner": "o",
                    "name": "n",
                    "commits": [
                        {"sha": "dup_sha", "message": "1"},
                        {"sha": "dup_sha", "message": "2"},  # duplicate -> quarantined
                    ],
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "PR",
                            "state": "open",
                            "base_commit_sha": "dup_sha",
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        assert not any(r.kind == "has_base_commit" for r in rels)
        unres_bc = next(u for u in unres if u.relationship_kind == "has_base_commit")
        assert "quarantined" in unres_bc.reason

    def test_explicit_is_fork_false_scopes_to_host_repository(self):
        doc = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "is_fork_false_test",
            "source_instance": {"source_kind": "github", "instance_id": "gh-org"},
            "observation_context": {"observation_id": "obs-1"},
            "repositories": [
                {
                    "repo_id": "host-repo",
                    "owner": "o",
                    "name": "n",
                    "branches": [{"name": "feat"}],
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "Internal PR",
                            "state": "open",
                            "source_branch": "feat",
                            "is_fork": False,
                        }
                    ],
                }
            ],
        }
        norm = normalize_github_fixture(validate_github_fixture(doc))
        rels, unres = resolve_github_relationships(norm)

        head_rel = next(r for r in rels if r.kind == "has_head_branch")
        assert head_rel.object_ref.entity_id == "host-repo/feat"
