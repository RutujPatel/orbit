"""Pass 4 / Wave 3 — Cross-System Evidence Fusion Adversarial Test Suite.

Verifies the deterministic cross-system evidence fusion contract (P3-07 / P2.5-19)
across all 25 mandated adversarial test scenarios (F01–F25):

F01: Unrelated Jira key in PR title (policy filtering and unobserved target)
F02: Same Jira key mentioned by multiple repositories (isolation and determinism)
F03: PR mentioning multiple Jira keys (distinct mentions and alignments)
F04: Jira key only in commit message (commit-level mention and alignment)
F05: Jira key only in branch name (branch-level mention and alignment)
F06: Lowercase Jira prefix rejected by policy regex
F07: Malformed Jira key rejected
F08: GitHub activity after Jira resolution (INVERTED temporal; non-conflicting)
F09: GitHub activity after source cutoff (STALE flagged by bundle validator)
F10: Missing GitHub timestamp (INDETERMINATE temporal comparison)
F11: Duplicate GitHub observations quarantined/handled deterministically
F12: Reversed GitHub observation ordering (permutation invariance)
F13: Unobserved Jira key emitted as UnresolvedReference
F14: Ambiguous Jira key emitted as UnresolvedReference
F15: Actor-name collision (no actor identity inference)
F16: Transitive mention attempt (no transitive link inference)
F17: Missing provenance in alignment rejected by validator
F18: Unresolved provenance in alignment flagged by validator
F19: Multiple Jira observations handled deterministically
F20: Deterministic alignment output across repeated executions
F21: Explicit link collection remains empty under current schemas (ADR-005 D2)
F22: EvidenceBundle alignment round-trip, deduplication, and serialization
F23: Provenance validation of alignments via fixtures_by_id dereferencing
F24: Structural validation and alignment validation coexist cleanly
F25: No Week-One evaluator behavior change (Mahout invariants preserved)
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

import pytest

from shadow_orbit.cross_system_fusion import (
    CrossSystemFusionResult,
    correlate_cross_system_evidence,
)
from shadow_orbit.evaluation import evaluate_week_one_rules
from shadow_orbit.evidence_assembly import (
    assemble_evidence_bundle,
    validate_evidence_bundle,
)
from shadow_orbit.evidence_types import (
    CrossSystemStateAlignment,
    EntityRef,
    EvidenceBundle,
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
    serialize_evidence_bundle,
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
from shadow_orbit.github_relationships import resolve_github_relationships
from shadow_orbit.github_validation import validate_github_fixture
from shadow_orbit.jira_evidence_adapter import adapt_jira_evidence
from shadow_orbit.normalization import normalize_fixture as normalize_jira_fixture
from shadow_orbit.validation import validate_fixture as validate_jira_fixture


# ── Shared Test Constants and Helper Builders ─────────────────────────

JIRA_SOURCE = SourceInstance(source_kind="jira", instance_id="jira.company.com")
GITHUB_SOURCE = SourceInstance(source_kind="github", instance_id="github.com/org-core")
GITHUB_SOURCE_2 = SourceInstance(source_kind="github", instance_id="github.com/org-secondary")

POLICY_PLAT = MentionLexicalPolicy(frozenset({"PLAT"}))
POLICY_MULTI = MentionLexicalPolicy(frozenset({"PLAT", "CORE"}))

T_JAN_01 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_05 = datetime(2026, 1, 5, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_10 = datetime(2026, 1, 10, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_15 = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_20 = datetime(2026, 1, 20, 10, 0, 0, tzinfo=timezone.utc)


def make_jira_obs(
    key: str = "PLAT-101",
    status: str = "In Progress",
    status_category: str = "in_progress",
    created_at: datetime | None = T_JAN_01,
    resolved_at: datetime | None = None,
    assignee: str | None = "Alice",
    obs_id: str = "obs-jira-1",
    source_instance: SourceInstance = JIRA_SOURCE,
    fixture_id: str = "jira-fix-1",
    record_locator: str | None = "work_items[0]",
) -> EvidenceObservation:
    ctx = ObservationContext(observation_id=obs_id, source_instance=source_instance)
    ref = EntityRef(source_instance=source_instance, entity_kind="jira_issue", entity_id=key)
    prov = ProvenanceRef(
        source_instance=source_instance,
        observation_id=obs_id,
        fixture_id=fixture_id,
        record_locator=record_locator,
    )
    state = JiraIssueState(
        key=key,
        source_status=status,
        source_priority="High",
        status_category=status_category,
        priority_band="high",
        assignee=assignee,
        created_at=created_at,
        updated_at=created_at,
        resolved_at=resolved_at,
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=ctx,
        observed_state=state,
        provenance_refs=(prov,),
    )


def make_gh_pr_obs(
    number: int = 10,
    title: str = "Implement feature",
    state: str = "open",
    repo_id: str = "repo-core",
    author_login: str = "alice",
    created_at: datetime | None = T_JAN_05,
    merged_at: datetime | None = None,
    source_branch: str = "feature/test",
    target_branch: str = "main",
    obs_id: str = "obs-gh-1",
    source_instance: SourceInstance = GITHUB_SOURCE,
    fixture_id: str = "gh-fix-1",
    locator_idx: int = 0,
) -> EvidenceObservation:
    ctx = ObservationContext(observation_id=obs_id, source_instance=source_instance)
    entity_id = f"{repo_id}/{number}"
    ref = EntityRef(source_instance=source_instance, entity_kind="github_pull_request", entity_id=entity_id)
    prov = ProvenanceRef(
        source_instance=source_instance,
        observation_id=obs_id,
        fixture_id=fixture_id,
        record_locator=f"repositories[0].pull_requests[{locator_idx}]",
    )
    st = GitHubPullRequestState(
        number=number,
        title=title,
        state=state,
        author_login=author_login,
        created_at=created_at,
        merged_at=merged_at,
        target_branch=target_branch,
        source_branch=source_branch,
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=ctx,
        observed_state=st,
        provenance_refs=(prov,),
    )


def make_gh_commit_obs(
    sha: str = "c0ffee1",
    message: str = "Implement logic",
    repo_id: str = "repo-core",
    author_login: str = "alice",
    committed_at: datetime | None = T_JAN_05,
    obs_id: str = "obs-gh-1",
    source_instance: SourceInstance = GITHUB_SOURCE,
    fixture_id: str = "gh-fix-1",
    locator_idx: int = 0,
) -> EvidenceObservation:
    ctx = ObservationContext(observation_id=obs_id, source_instance=source_instance)
    entity_id = f"{repo_id}/{sha}"
    ref = EntityRef(source_instance=source_instance, entity_kind="github_commit", entity_id=entity_id)
    prov = ProvenanceRef(
        source_instance=source_instance,
        observation_id=obs_id,
        fixture_id=fixture_id,
        record_locator=f"repositories[0].commits[{locator_idx}]",
    )
    st = GitHubCommitState(
        sha=sha,
        message=message,
        author_login=author_login,
        committed_at=committed_at,
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=ctx,
        observed_state=st,
        provenance_refs=(prov,),
    )


def make_gh_branch_obs(
    name: str = "feature/test",
    repo_id: str = "repo-core",
    obs_id: str = "obs-gh-1",
    source_instance: SourceInstance = GITHUB_SOURCE,
    fixture_id: str = "gh-fix-1",
    locator_idx: int = 0,
) -> EvidenceObservation:
    ctx = ObservationContext(observation_id=obs_id, source_instance=source_instance)
    entity_id = f"{repo_id}/{name}"
    ref = EntityRef(source_instance=source_instance, entity_kind="github_branch", entity_id=entity_id)
    prov = ProvenanceRef(
        source_instance=source_instance,
        observation_id=obs_id,
        fixture_id=fixture_id,
        record_locator=f"repositories[0].branches[{locator_idx}]",
    )
    st = GitHubBranchState(
        name=name,
        head_commit_id="c0ffee1",
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=ctx,
        observed_state=st,
        provenance_refs=(prov,),
    )


def make_normalized_gh(
    observations: tuple[EvidenceObservation, ...],
    source_instance: SourceInstance = GITHUB_SOURCE,
    obs_id: str = "obs-gh-1",
    fixture_id: str = "gh-fix-1",
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


# ═══════════════════════════════════════════════════════════════════════
# F01 – F25 ADVERSARIAL TEST SUITE
# ═══════════════════════════════════════════════════════════════════════

class TestWave3AdversarialFusion:
    """Covers F01 through F25 for Pass 4 Wave 3 Cross-System Evidence Fusion."""

    def test_f01_unrelated_jira_key_in_pr_title(self):
        """F01: Unrelated Jira key in PR title:
        -> DECLARED_MENTION when target is observed;
        -> UnresolvedReference when target is unobserved;
        -> never EXPLICIT_LINK.
        Also verifies no cartesian product pairing of arbitrary entities.
        """
        # Case 1: Prefix not permitted by policy (unrelated project key)
        pr_obs = make_gh_pr_obs(number=1, title="OTHER-999: Unrelated external issue")
        gh_fixture = make_normalized_gh((pr_obs,))
        jira_obs = make_jira_obs("PLAT-101")

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        # Invariant: Existence of both entities in evidence universe does NOT create an alignment
        assert result.declared_mentions == ()
        assert result.state_alignments == ()
        assert result.unresolved_references == ()
        assert result.explicit_links == ()

        # Case 2: Permitted prefix but key unobserved in Jira dataset
        pr_obs2 = make_gh_pr_obs(number=2, title="PLAT-999: Legitimate prefix but missing issue")
        gh_fixture2 = make_normalized_gh((pr_obs2,))
        result2 = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture2,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert result2.declared_mentions == ()
        assert result2.state_alignments == ()
        assert len(result2.unresolved_references) == 1
        assert result2.unresolved_references[0].target_identifier == "PLAT-999"
        assert "not observed" in result2.unresolved_references[0].reason
        assert result2.explicit_links == ()

        # Case 3: Permitted prefix and target is observed in Jira dataset
        pr_obs3 = make_gh_pr_obs(number=3, title="PLAT-101: Observed Jira issue citation")
        gh_fixture3 = make_normalized_gh((pr_obs3,))
        result3 = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture3,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert len(result3.declared_mentions) == 1
        assert result3.declared_mentions[0].kind == "mentions"
        assert result3.declared_mentions[0].basis == "lexical_match"
        assert len(result3.state_alignments) == 1
        assert result3.unresolved_references == ()
        # Invariant: Never classified as EXPLICIT_LINK
        assert result3.explicit_links == ()

    def test_f02_same_jira_key_mentioned_by_multiple_repositories(self):
        """F02: Same Jira key mentioned across multiple repositories tracked independently."""
        pr_repo1 = make_gh_pr_obs(number=10, title="PLAT-101 in core repo", repo_id="repo-core")
        pr_repo2 = make_gh_pr_obs(number=20, title="PLAT-101 in utils repo", repo_id="repo-utils")
        gh_fixture = make_normalized_gh((pr_repo1, pr_repo2))
        jira_obs = make_jira_obs("PLAT-101")

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert len(result.declared_mentions) == 2
        assert len(result.state_alignments) == 2

        subjects = {a.github_ref.entity_id for a in result.state_alignments}
        assert subjects == {"repo-core/10", "repo-utils/20"}
        assert all(a.jira_ref.entity_id == "PLAT-101" for a in result.state_alignments)

    def test_f03_pr_mentioning_multiple_jira_keys(self):
        """F03: PR mentioning multiple Jira keys produces independent mentions and alignments."""
        pr_obs = make_gh_pr_obs(number=15, title="PLAT-101 and PLAT-102 multi-ticket refactor")
        gh_fixture = make_normalized_gh((pr_obs,))
        jira_obs1 = make_jira_obs("PLAT-101")
        jira_obs2 = make_jira_obs("PLAT-102")

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs1, jira_obs2),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert len(result.declared_mentions) == 2
        assert len(result.state_alignments) == 2

        jira_targets = {a.jira_ref.entity_id for a in result.state_alignments}
        assert jira_targets == {"PLAT-101", "PLAT-102"}
        assert all(a.github_ref.entity_id == "repo-core/15" for a in result.state_alignments)

    def test_f04_jira_key_only_in_commit_message(self):
        """F04: Jira key only in commit message creates commit-level mention and alignment."""
        pr_obs = make_gh_pr_obs(number=1, title="Generic PR with no key")
        commit_obs = make_gh_commit_obs(
            sha="c0ffee1",
            message="PLAT-101: Commit with isolated mention",
            committed_at=T_JAN_05,
        )
        gh_fixture = make_normalized_gh((pr_obs, commit_obs))
        jira_obs = make_jira_obs(
            key="PLAT-101",
            status="Done",
            status_category="done",
            created_at=T_JAN_01,
            resolved_at=T_JAN_10,
        )

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert len(result.declared_mentions) == 1
        mention = result.declared_mentions[0]
        assert mention.subject_ref.entity_kind == "github_commit"
        assert mention.subject_ref.entity_id == "repo-core/c0ffee1"

        assert len(result.state_alignments) == 1
        align = result.state_alignments[0]
        assert align.github_ref.entity_kind == "github_commit"
        assert align.github_ref.entity_id == "repo-core/c0ffee1"
        assert align.state_comparison == "CONSISTENT"
        assert align.temporal_comparison == "COHERENT"

    def test_f05_jira_key_only_in_branch_name(self):
        """F05: Jira key only in branch name creates branch-level mention and alignment."""
        branch_obs = make_gh_branch_obs(name="feature/PLAT-101-auth-flow")
        gh_fixture = make_normalized_gh((branch_obs,))
        jira_obs = make_jira_obs("PLAT-101")

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert len(result.declared_mentions) == 1
        mention = result.declared_mentions[0]
        assert mention.subject_ref.entity_kind == "github_branch"
        assert mention.subject_ref.entity_id == "repo-core/feature/PLAT-101-auth-flow"

        assert len(result.state_alignments) == 1
        align = result.state_alignments[0]
        assert align.github_ref.entity_kind == "github_branch"
        assert align.state_comparison == "CONSISTENT"
        assert align.temporal_comparison == "INDETERMINATE"

    def test_f06_lowercase_jira_prefix_rejected(self):
        """F06: Lowercase Jira prefix rejected by policy regex."""
        pr_obs = make_gh_pr_obs(number=1, title="plat-101: lowercase prefix should be ignored")
        gh_fixture = make_normalized_gh((pr_obs,))
        jira_obs = make_jira_obs("PLAT-101")

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert result.declared_mentions == ()
        assert result.state_alignments == ()
        assert result.unresolved_references == ()

    def test_f07_malformed_jira_key_rejected(self):
        """F07: Malformed Jira keys rejected by tokenizer/regex."""
        malformed_titles = [
            "PLAT-: missing issue number",
            "PLAT: project token only",
            "PLAT-ABC: non-numeric suffix",
            "-101: missing project prefix",
            "PLAT--101: double hyphen",
        ]
        observations = [
            make_gh_pr_obs(number=i + 1, title=title)
            for i, title in enumerate(malformed_titles)
        ]
        gh_fixture = make_normalized_gh(tuple(observations))
        jira_obs = make_jira_obs("PLAT-101")

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert result.declared_mentions == ()
        assert result.state_alignments == ()
        assert result.unresolved_references == ()

    def test_f08_github_activity_after_jira_resolution_non_conflicting(self):
        """F08: GitHub activity after Jira resolution is INVERTED temporal, NEVER CONFLICTING."""
        # PR merged AFTER Jira resolution (workflow lag or post-resolution patch)
        pr_obs = make_gh_pr_obs(
            number=42,
            title="PLAT-101: Late merge",
            state="merged",
            created_at=T_JAN_05,
            merged_at=T_JAN_15,  # 5 days after Jira resolution
        )
        jira_obs = make_jira_obs(
            key="PLAT-101",
            status="Done",
            status_category="done",
            created_at=T_JAN_01,
            resolved_at=T_JAN_10,  # Resolved Jan 10
        )
        gh_fixture = make_normalized_gh((pr_obs,))

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert len(result.state_alignments) == 1
        align = result.state_alignments[0]

        # Invariant: Must NEVER be classified as CONFLICTING
        assert align.state_comparison != "CONFLICTING"
        assert align.state_comparison == "INSUFFICIENT_EVIDENCE"
        assert align.temporal_comparison == "INVERTED"
        assert "non-conflicting" in align.rationale

        # Commit after Jira resolution
        commit_obs = make_gh_commit_obs(
            sha="c0ffee99",
            message="PLAT-101: post-release hotfix",
            committed_at=T_JAN_20,
        )
        gh_fixture_commit = make_normalized_gh((commit_obs,))
        result_commit = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture_commit,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert len(result_commit.state_alignments) == 1
        align_commit = result_commit.state_alignments[0]
        assert align_commit.state_comparison != "CONFLICTING"
        assert align_commit.state_comparison == "INSUFFICIENT_EVIDENCE"
        assert align_commit.temporal_comparison == "INVERTED"
        assert "non-conflicting" in align_commit.rationale

    def test_f09_github_activity_after_source_cutoff_stale(self):
        """F09: Activity after source cutoff is flagged as temporal invalidity by bundle validator."""
        # Fixture with commit timestamp postdating cutoff
        cutoff = datetime(2026, 1, 4, 0, 0, 0, tzinfo=timezone.utc)
        ctx = ObservationContext(
            observation_id="obs-gh-1",
            source_instance=GITHUB_SOURCE,
            source_cutoff_at=cutoff,
        )
        commit_obs = make_gh_commit_obs(
            sha="c0ffee1",
            message="PLAT-101: commit past cutoff",
            committed_at=T_JAN_05,  # Jan 5 > Jan 4 cutoff
            obs_id="obs-gh-1",
        )
        jira_obs = make_jira_obs("PLAT-101")

        gh_raw = {
            "fixture_id": "gh-fix-1",
            "repositories": [
                {
                    "repo_id": "repo-core",
                    "owner": "org-core",
                    "name": "core-repo",
                    "commits": [
                        {
                            "sha": "c0ffee1",
                            "message": "PLAT-101: commit past cutoff",
                            "committed_at": "2026-01-05T10:00:00Z",
                        }
                    ],
                }
            ],
        }
        jira_raw = {
            "work_items": [
                {"key": "PLAT-101", "source_id": "1", "id": "1", "status": "In Progress"}
            ]
        }

        alignment = CrossSystemStateAlignment(
            jira_ref=jira_obs.entity_ref,
            github_ref=commit_obs.entity_ref,
            relationship_kind="mentions",
            state_comparison="CONSISTENT",
            temporal_comparison="COHERENT",
            rationale="Test alignment",
            provenance_refs=commit_obs.provenance_refs,
        )

        bundle = EvidenceBundle(
            bundle_id="b-stale",
            bundle_version="1.0",
            observation_contexts=(jira_obs.observation_context, ctx),
            observations=(jira_obs, commit_obs),
            relationships=(),
            unresolved_references=(),
            quality_issues=(),
            cross_system_alignments=(alignment,),
        )

        fixtures = {"jira-fix-1": jira_raw, "gh-fix-1": gh_raw}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)

        # Validator flags temporal cutoff violation in alignment provenance
        assert any(
            q.code == "invalid"
            and q.subject_scope == "provenance:temporal"
            and "postdates source cutoff" in q.message
            for q in issues
        )

    def test_f10_missing_github_timestamp_indeterminate(self):
        """F10: Missing GitHub timestamp results in INDETERMINATE temporal comparison."""
        # PR marked merged but lacking merged_at
        pr_obs = make_gh_pr_obs(
            number=1,
            title="PLAT-101: merged without timestamp",
            state="merged",
            created_at=T_JAN_01,
            merged_at=None,
        )
        gh_fixture = make_normalized_gh((pr_obs,))
        jira_obs = make_jira_obs("PLAT-101", status="Done", status_category="done", resolved_at=T_JAN_10)

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert len(result.state_alignments) == 1
        align = result.state_alignments[0]
        assert align.temporal_comparison == "INDETERMINATE"
        assert align.state_comparison == "INSUFFICIENT_EVIDENCE"
        assert "lacks explicit merged_at" in align.rationale

        # Commit lacking committed_at
        commit_obs = make_gh_commit_obs(
            sha="c0ffee0",
            message="PLAT-101: commit without timestamp",
            committed_at=None,
        )
        gh_fixture_c = make_normalized_gh((commit_obs,))
        result_c = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture_c,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert len(result_c.state_alignments) == 1
        align_c = result_c.state_alignments[0]
        assert align_c.temporal_comparison == "INDETERMINATE"
        assert align_c.state_comparison == "INSUFFICIENT_EVIDENCE"
        assert "timestamp missing" in align_c.rationale

    def test_f11_duplicate_github_observations_quarantined_or_handled(self):
        """F11: Duplicate GitHub observations handled safely and quarantined in bundle validation."""
        pr_obs_1 = make_gh_pr_obs(number=10, title="PLAT-101 duplicate test")
        pr_obs_2 = make_gh_pr_obs(number=10, title="PLAT-101 duplicate test")
        jira_obs = make_jira_obs("PLAT-101")

        # Bundle with duplicate observation identity
        bundle = EvidenceBundle(
            bundle_id="b-dup",
            bundle_version="1.0",
            observation_contexts=(jira_obs.observation_context, pr_obs_1.observation_context),
            observations=(jira_obs, pr_obs_1, pr_obs_2),
            relationships=(),
            unresolved_references=(),
            quality_issues=(),
            cross_system_alignments=(),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(
            q.code == "invalid"
            and q.subject_scope == "observation:identity"
            and "Duplicate observation" in q.message
            for q in issues
        )

    def test_f12_reversed_github_observation_ordering_permutation_invariance(self):
        """F12: Permutation of input observations produces bit-for-bit identical outputs."""
        obs1 = make_gh_pr_obs(number=1, title="PLAT-101: PR 1")
        obs2 = make_gh_pr_obs(number=2, title="PLAT-102: PR 2")
        obs3 = make_gh_commit_obs(sha="c0ffee3", message="PLAT-103: Commit 3")
        jira1 = make_jira_obs("PLAT-101")
        jira2 = make_jira_obs("PLAT-102")
        jira3 = make_jira_obs("PLAT-103")

        forward_gh = make_normalized_gh((obs1, obs2, obs3))
        reversed_gh = make_normalized_gh((obs3, obs2, obs1))

        res_forward = correlate_cross_system_evidence(
            jira_observations=(jira1, jira2, jira3),
            github_fixture=forward_gh,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        res_reversed = correlate_cross_system_evidence(
            jira_observations=(jira3, jira2, jira1),
            github_fixture=reversed_gh,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )

        assert res_forward.declared_mentions == res_reversed.declared_mentions
        assert res_forward.state_alignments == res_reversed.state_alignments
        assert res_forward.unresolved_references == res_reversed.unresolved_references
        assert res_forward.explicit_links == res_reversed.explicit_links

    def test_f13_unobserved_jira_key_unresolved_reference(self):
        """F13: Mentioned Jira key unobserved in Jira dataset emits UnresolvedReference."""
        pr_obs = make_gh_pr_obs(number=50, title="PLAT-404: Nonexistent ticket")
        gh_fixture = make_normalized_gh((pr_obs,))
        jira_obs = make_jira_obs("PLAT-101")

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert result.declared_mentions == ()
        assert result.state_alignments == ()
        assert len(result.unresolved_references) == 1
        unres = result.unresolved_references[0]
        assert unres.target_identifier == "PLAT-404"
        assert unres.relationship_kind == "mentions"
        assert "not observed" in unres.reason

    def test_f14_ambiguous_jira_key_unresolved_reference(self):
        """F14: Ambiguous Jira key (multiple observations) emits UnresolvedReference."""
        pr_obs = make_gh_pr_obs(number=10, title="PLAT-101: Duplicate issue in Jira")
        gh_fixture = make_normalized_gh((pr_obs,))

        # Two observations for the exact same Jira key
        jira_obs_a = make_jira_obs("PLAT-101", obs_id="obs-jira-1")
        jira_obs_b = make_jira_obs("PLAT-101", obs_id="obs-jira-2")

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs_a, jira_obs_b),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert result.declared_mentions == ()
        assert result.state_alignments == ()
        assert len(result.unresolved_references) == 1
        unres = result.unresolved_references[0]
        assert unres.target_identifier == "PLAT-101"
        assert "Ambiguous Jira target" in unres.reason

    def test_f15_actor_name_collision_no_actor_identity_inference(self):
        """F15: Matching usernames across Jira and GitHub never infer actor identity."""
        # PR author is "alice", Jira assignee is "alice"
        pr_obs = make_gh_pr_obs(number=1, title="PLAT-101: Auth", author_login="alice")
        jira_obs = make_jira_obs("PLAT-101", assignee="alice")
        gh_fixture = make_normalized_gh((pr_obs,))

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        # Mentions and alignments are formed on ticket key citations, NOT actor identity
        assert len(result.state_alignments) == 1
        align = result.state_alignments[0]
        # Verify alignment does not claim actor identity
        assert "actor" not in align.relationship_kind
        assert align.relationship_kind == "mentions"

    def test_f16_transitive_mention_attempt_no_transitive_inference(self):
        """F16: Transitive associations across GitHub entities are never inferred."""
        # Commit has mention of PLAT-101
        commit_obs = make_gh_commit_obs(sha="c0ffee1", message="PLAT-101: Fix bug")
        # PR mentions Commit c0ffee1 in title, but does NOT mention PLAT-101
        pr_obs = make_gh_pr_obs(number=10, title="Merge commit c0ffee1 into main")
        gh_fixture = make_normalized_gh((commit_obs, pr_obs))
        jira_obs = make_jira_obs("PLAT-101")

        result = correlate_cross_system_evidence(
            jira_observations=(jira_obs,),
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        # Only the commit has a declared mention and state alignment
        subjects = {a.github_ref.entity_id for a in result.state_alignments}
        assert subjects == {"repo-core/c0ffee1"}
        assert "repo-core/10" not in subjects

    def test_f17_missing_provenance_in_alignment_rejected_by_validator(self):
        """F17: State alignment with empty provenance_refs rejected by EvidenceBundle validator."""
        jira_obs = make_jira_obs("PLAT-101")
        pr_obs = make_gh_pr_obs(number=1)

        alignment = CrossSystemStateAlignment(
            jira_ref=jira_obs.entity_ref,
            github_ref=pr_obs.entity_ref,
            relationship_kind="mentions",
            state_comparison="CONSISTENT",
            temporal_comparison="COHERENT",
            rationale="Alignment missing provenance",
            provenance_refs=(),  # EMPTY
        )

        bundle = EvidenceBundle(
            bundle_id="b-empty-prov",
            bundle_version="1.0",
            observation_contexts=(jira_obs.observation_context, pr_obs.observation_context),
            observations=(jira_obs, pr_obs),
            relationships=(),
            unresolved_references=(),
            quality_issues=(),
            cross_system_alignments=(alignment,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(
            q.code == "missing"
            and q.subject_scope == "alignment:provenance"
            and "has no supporting provenance" in q.message
            for q in issues
        )

    def test_f18_unresolved_provenance_in_alignment_flagged_by_validator(self):
        """F18: State alignment with invalid/out-of-bounds locator flagged during dereferencing."""
        jira_obs = make_jira_obs("PLAT-101")
        pr_obs = make_gh_pr_obs(number=1)

        bad_prov = ProvenanceRef(
            source_instance=GITHUB_SOURCE,
            observation_id="obs-gh-1",
            fixture_id="gh-fix-1",
            record_locator="repositories[0].pull_requests[9999]",  # OOB
        )
        alignment = CrossSystemStateAlignment(
            jira_ref=jira_obs.entity_ref,
            github_ref=pr_obs.entity_ref,
            relationship_kind="mentions",
            state_comparison="CONSISTENT",
            temporal_comparison="COHERENT",
            rationale="Alignment with bad locator",
            provenance_refs=(bad_prov,),
        )

        bundle = EvidenceBundle(
            bundle_id="b-bad-loc",
            bundle_version="1.0",
            observation_contexts=(jira_obs.observation_context, pr_obs.observation_context),
            observations=(jira_obs, pr_obs),
            relationships=(),
            unresolved_references=(),
            quality_issues=(),
            cross_system_alignments=(alignment,),
        )

        gh_raw = {
            "fixture_id": "gh-fix-1",
            "repositories": [
                {
                    "repo_id": "repo-core",
                    "pull_requests": [{"number": 1, "title": "PR 1"}],
                }
            ],
        }
        fixtures = {"gh-fix-1": gh_raw}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert any(
            q.code == "unresolved"
            and q.subject_scope == "provenance:locator"
            and "out of bounds" in q.message
            for q in issues
        )

    def test_f19_multiple_jira_observations_handled_deterministically(self):
        """F19: Multiple distinct Jira issues referenced across multiple PRs sorted deterministically."""
        jira_keys = ["PLAT-300", "PLAT-100", "PLAT-200"]
        jira_obs = [make_jira_obs(k) for k in jira_keys]

        pr_obs = [
            make_gh_pr_obs(number=1, title="PLAT-300: Ticket 300"),
            make_gh_pr_obs(number=2, title="PLAT-100: Ticket 100"),
            make_gh_pr_obs(number=3, title="PLAT-200: Ticket 200"),
        ]
        gh_fixture = make_normalized_gh(tuple(pr_obs))

        result = correlate_cross_system_evidence(
            jira_observations=jira_obs,
            github_fixture=gh_fixture,
            mention_policy=POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )
        assert len(result.state_alignments) == 3
        # Canonical sort order: jira_id first
        assert [a.jira_ref.entity_id for a in result.state_alignments] == [
            "PLAT-100",
            "PLAT-200",
            "PLAT-300",
        ]

    def test_f20_deterministic_alignment_output(self):
        """F20: Exact same inputs yield identical CrossSystemFusionResult across repeated runs."""
        pr_obs = make_gh_pr_obs(number=10, title="PLAT-101 and PLAT-102")
        gh_fixture = make_normalized_gh((pr_obs,))
        jira_obs = [make_jira_obs("PLAT-101"), make_jira_obs("PLAT-102")]

        res1 = correlate_cross_system_evidence(jira_obs, gh_fixture, POLICY_PLAT, JIRA_SOURCE)
        for _ in range(5):
            res_subsequent = correlate_cross_system_evidence(jira_obs, gh_fixture, POLICY_PLAT, JIRA_SOURCE)
            assert res1 == res_subsequent

    def test_f21_explicit_link_collection_remains_empty_under_current_fixtures(self):
        """F21: Explicit link collection remains strictly empty under current schemas (ADR-005 D2)."""
        pr_obs = make_gh_pr_obs(number=1, title="PLAT-101")
        gh_fixture = make_normalized_gh((pr_obs,))
        jira_obs = [make_jira_obs("PLAT-101")]

        result = correlate_cross_system_evidence(jira_obs, gh_fixture, POLICY_PLAT, JIRA_SOURCE)
        assert result.explicit_links == ()
        assert isinstance(result.explicit_links, tuple)

    def test_f22_evidence_bundle_alignment_round_trip_and_assembly(self):
        """F22: EvidenceBundle assembly, alignment deduplication, and serialization round-trip."""
        jira_obs = make_jira_obs("PLAT-101")
        pr_obs = make_gh_pr_obs(number=1, title="PLAT-101")

        align = CrossSystemStateAlignment(
            jira_ref=jira_obs.entity_ref,
            github_ref=pr_obs.entity_ref,
            relationship_kind="mentions",
            state_comparison="CONSISTENT",
            temporal_comparison="COHERENT",
            rationale="Valid alignment",
            provenance_refs=pr_obs.provenance_refs,
        )

        bundle = assemble_evidence_bundle(
            bundle_id="b-align-test",
            bundle_version="1.0",
            jira_context=jira_obs.observation_context,
            jira_observations=(jira_obs,),
            jira_quality_issues=(),
            github_fixture=make_normalized_gh((pr_obs,)),
            cross_system_alignments=(align, align),  # Duplicate passes in
        )
        # Deduplication check
        assert len(bundle.cross_system_alignments) == 1
        assert bundle.cross_system_alignments[0] == align

        serialized = serialize_evidence_bundle(bundle)
        assert "cross_system_alignments" in serialized
        assert len(serialized["cross_system_alignments"]) == 1
        s_align = serialized["cross_system_alignments"][0]
        assert s_align["jira_ref"]["entity_id"] == "PLAT-101"
        assert s_align["github_ref"]["entity_id"] == "repo-core/1"
        assert s_align["state_comparison"] == "CONSISTENT"
        assert s_align["temporal_comparison"] == "COHERENT"

    def test_f23_provenance_validation_of_alignment_via_fixtures_by_id(self):
        """F23: Full in-memory dereferencing of alignment provenance via fixtures_by_id."""
        gh_raw = {
            "fixture_id": "gh-fix-1",
            "repositories": [
                {
                    "repo_id": "repo-core",
                    "owner": "org-core",
                    "name": "core-repo",
                    "pull_requests": [
                        {
                            "number": 1,
                            "title": "PLAT-101: Valid PR",
                            "state": "open",
                            "created_at": "2026-01-05T10:00:00Z",
                        }
                    ],
                }
            ],
        }
        jira_raw = {
            "work_items": [
                {"key": "PLAT-101", "source_id": "1", "id": "1", "status": "In Progress"}
            ]
        }

        jira_obs = make_jira_obs("PLAT-101", record_locator="work_items[0]")
        pr_obs = make_gh_pr_obs(number=1, locator_idx=0)
        gh_fixture = make_normalized_gh((pr_obs,))

        fusion = correlate_cross_system_evidence(
            (jira_obs,),
            gh_fixture,
            POLICY_PLAT,
            jira_source_instance=JIRA_SOURCE,
        )

        bundle = assemble_evidence_bundle(
            bundle_id="b-deref-pass",
            bundle_version="1.0",
            jira_context=jira_obs.observation_context,
            jira_observations=(jira_obs,),
            jira_quality_issues=(),
            github_fixture=gh_fixture,
            cross_system_alignments=fusion.state_alignments,
        )

        fixtures = {"jira-fix-1": jira_raw, "gh-fix-1": gh_raw}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert issues == ()

    def test_f24_structural_validation_and_alignment_validation_coexist(self):
        """F24: Structural relationships and cross-system alignments validate simultaneously."""
        repo_ref = EntityRef(GITHUB_SOURCE, "github_repository", "repo-core")
        repo_ctx = ObservationContext("obs-gh-1", GITHUB_SOURCE)
        repo_obs = EvidenceObservation(
            entity_ref=repo_ref,
            observation_context=repo_ctx,
            observed_state=GitHubRepositoryState("org-core", "core-repo"),
            provenance_refs=(
                ProvenanceRef(GITHUB_SOURCE, "obs-gh-1", "gh-fix-1", "repositories[0]"),
            ),
        )
        pr_obs = make_gh_pr_obs(number=1)
        jira_obs = make_jira_obs("PLAT-101")

        # Structural edge: PR belongs_to_repository repo
        struct_rel = EvidenceRelationship(
            subject_ref=pr_obs.entity_ref,
            object_ref=repo_ref,
            kind="belongs_to_repository",
            basis="structural_association",
            subject_observation_id="obs-gh-1",
            object_observation_id="obs-gh-1",
            provenance_refs=pr_obs.provenance_refs,
        )

        # Cross-system alignment
        align = CrossSystemStateAlignment(
            jira_ref=jira_obs.entity_ref,
            github_ref=pr_obs.entity_ref,
            relationship_kind="mentions",
            state_comparison="CONSISTENT",
            temporal_comparison="COHERENT",
            rationale="Coexisting alignment",
            provenance_refs=pr_obs.provenance_refs,
        )

        bundle = EvidenceBundle(
            bundle_id="b-coexist",
            bundle_version="1.0",
            observation_contexts=(jira_obs.observation_context, repo_ctx),
            observations=(jira_obs, repo_obs, pr_obs),
            relationships=(struct_rel,),
            unresolved_references=(),
            quality_issues=(),
            cross_system_alignments=(align,),
        )

        issues = validate_evidence_bundle(bundle)
        assert issues == ()

    def test_f25_no_week_one_evaluator_behavior_change(self):
        """F25: Week-One legacy rules evaluator produces 100% identical outputs and zero mutations."""
        # 1. Clean week 1 baseline evaluation
        raw = load_fixture("fixtures/jira/northstar_clean_week_1.json")
        val = validate_jira_fixture(raw)
        norm = normalize_jira_fixture(val)

        matches, suppressed = evaluate_week_one_rules(norm)
        assert len(matches) == 3
        assert len(suppressed) == 2
        assert {m.rule_key for m in matches} == {
            "OVERDUE_HIGH_PRIORITY",
            "STALLED_WORK",
            "BLOCKED_HIGH_PRIORITY",
        }

        # 2. Strict Mahout qualification specimen evaluation
        import sys
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[2]
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

        from qualification.mahout.runner import run_mahout_qualification
        mahout_res = run_mahout_qualification(save_golden=False)

        assert len(mahout_res.validated_fixture.accepted_raw_items) == 412
        assert len(mahout_res.normalized_fixture.work_items) == 412
        assert len(mahout_res.evidence_bridge.bundle.observations) == 412
        assert len(mahout_res.rule_matches) == 12
        assert all(m.rule_key == "STALLED_WORK" for m in mahout_res.rule_matches)
        assert mahout_res.is_repeatable is True
        assert mahout_res.jira_mutation_count == 0
        assert mahout_res.jira_configuration_mutation_count == 0
