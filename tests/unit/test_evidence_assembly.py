"""Unit tests for EvidenceBundle orchestration and validation (CSE-1.7).

Covers:
  1. Input validation (bundle_id, bundle_version, source_kind, context checks)
  2. Jira-only bundle assembly
  3. GitHub-only bundle assembly
  4. Combined Jira + GitHub bundle assembly
  5. Relationship deduplication (same basis merges, cross-basis distinct)
  6. Unresolved reference deduplication (reason part of identity key)
  7. Bundle validation: joint endpoint ↔ observation pairing
  8. Bundle validation: invariants (context resolution, basis compatibility,
     provenance, cross-system identity, duplicate observations, zero-obs contexts)
  9. Determinism and permutation invariance
 10. Canonical serialization verification (sparse, sorted, deterministic)
 11. Immutability and input preservation
 12. Edge cases (empty bundle, coverage-only context)
 13. End-to-end integration with adapted Jira and normalized GitHub fixtures
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from shadow_orbit.evidence_assembly import (
    assemble_evidence_bundle,
    validate_evidence_bundle,
)
from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceBundle,
    EvidenceObservation,
    EvidenceRelationship,
    GitHubCommitState,
    GitHubPullRequestState,
    GitHubRepositoryState,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    RelationshipBasis,
    RelationshipKind,
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


# ── Shared Test Constants and Helpers ────────────────────────────────

GITHUB_SOURCE = SourceInstance(source_kind="github", instance_id="github.com/org-core")
JIRA_SOURCE = SourceInstance(source_kind="jira", instance_id="jira.company.com")
OTHER_JIRA_SOURCE = SourceInstance(source_kind="jira", instance_id="other.jira.com")

_T0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
_T1 = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)


def make_jira_obs(
    key: str,
    obs_id: str = "obs-jira-1",
    source_instance: SourceInstance = JIRA_SOURCE,
) -> EvidenceObservation:
    ctx = ObservationContext(observation_id=obs_id, source_instance=source_instance)
    ref = EntityRef(source_instance=source_instance, entity_kind="jira_issue", entity_id=key)
    prov = ProvenanceRef(
        source_instance=source_instance,
        observation_id=obs_id,
        fixture_id="jira-fix-1",
        record_locator=f"work_items[{key}]",
    )
    state = JiraIssueState(
        key=key,
        source_status="In Progress",
        source_priority="High",
        status_category="in_progress",
        priority_band="high",
        assignee="Alice",
        created_at=_T0,
        updated_at=_T1,
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=ctx,
        observed_state=state,
        provenance_refs=(prov,),
    )


def make_github_obs(
    entity_kind: str,
    entity_id: str,
    state: any,
    obs_id: str = "obs-gh-1",
    source_instance: SourceInstance = GITHUB_SOURCE,
    locator: str = "items[0]",
) -> EvidenceObservation:
    ctx = ObservationContext(observation_id=obs_id, source_instance=source_instance)
    ref = EntityRef(source_instance=source_instance, entity_kind=entity_kind, entity_id=entity_id)
    prov = ProvenanceRef(
        source_instance=source_instance,
        observation_id=obs_id,
        fixture_id="gh-fix-1",
        record_locator=locator,
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=ctx,
        observed_state=state,
        provenance_refs=(prov,),
    )


def make_normalized_gh(
    observations: tuple[EvidenceObservation, ...],
    quality_issues: tuple[QualityIssue, ...] = (),
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
        quality_issues=quality_issues,
        quarantined_records=(),
    )


def make_rel(
    subject_ref: EntityRef,
    object_ref: EntityRef,
    kind: RelationshipKind,
    basis: RelationshipBasis,
    subject_obs_id: str,
    object_obs_id: str,
    locator: str = "rel[0]",
    quality_issues: tuple[QualityIssue, ...] = (),
) -> EvidenceRelationship:
    prov = ProvenanceRef(
        source_instance=subject_ref.source_instance,
        observation_id=subject_obs_id,
        record_locator=locator,
    )
    return EvidenceRelationship(
        subject_ref=subject_ref,
        object_ref=object_ref,
        kind=kind,
        basis=basis,
        subject_observation_id=subject_obs_id,
        object_observation_id=object_obs_id,
        provenance_refs=(prov,),
        quality_issues=quality_issues,
    )


def make_unresolved(
    source_ref: EntityRef,
    source_obs_id: str,
    target_kind: str,
    target_id: str,
    kind: RelationshipKind,
    reason: str,
    locator: str = "unres[0]",
) -> UnresolvedReference:
    prov = ProvenanceRef(
        source_instance=source_ref.source_instance,
        observation_id=source_obs_id,
        record_locator=locator,
    )
    return UnresolvedReference(
        source_ref=source_ref,
        source_observation_id=source_obs_id,
        target_entity_kind=target_kind,
        target_identifier=target_id,
        relationship_kind=kind,
        reason=reason,
        provenance_refs=(prov,),
    )


# =====================================================================
# 1. Input Validation Tests
# =====================================================================

class TestAssembleInputValidation:
    def test_empty_bundle_id_raises(self):
        with pytest.raises(ValueError, match="bundle_id must be a non-empty string"):
            assemble_evidence_bundle(bundle_id="", bundle_version="1.0")

    def test_whitespace_bundle_id_raises(self):
        with pytest.raises(ValueError, match="bundle_id must be a non-empty string"):
            assemble_evidence_bundle(bundle_id="   ", bundle_version="1.0")

    def test_empty_bundle_version_raises(self):
        with pytest.raises(ValueError, match="bundle_version must be a non-empty string"):
            assemble_evidence_bundle(bundle_id="b-1", bundle_version="")

    def test_whitespace_bundle_version_raises(self):
        with pytest.raises(ValueError, match="bundle_version must be a non-empty string"):
            assemble_evidence_bundle(bundle_id="b-1", bundle_version="   ")

    def test_jira_context_wrong_source_kind_raises(self):
        bad_ctx = ObservationContext(
            observation_id="obs-1",
            source_instance=GITHUB_SOURCE,  # wrong source_kind for jira_context
        )
        with pytest.raises(ValueError, match="jira_context must have source_kind='jira'"):
            assemble_evidence_bundle(
                bundle_id="b-1",
                bundle_version="1.0",
                jira_context=bad_ctx,
            )

    def test_github_fixture_wrong_source_kind_raises(self):
        bad_gh = make_normalized_gh(
            observations=(),
            source_instance=JIRA_SOURCE,  # wrong source_kind for github_fixture
        )
        with pytest.raises(ValueError, match="github_fixture must have source_kind='github'"):
            assemble_evidence_bundle(
                bundle_id="b-1",
                bundle_version="1.0",
                github_fixture=bad_gh,
            )

    def test_jira_observations_without_jira_context_raises(self):
        obs = make_jira_obs("PLAT-1")
        with pytest.raises(ValueError, match="jira_observations supplied but jira_context is None"):
            assemble_evidence_bundle(
                bundle_id="b-1",
                bundle_version="1.0",
                jira_observations=(obs,),
            )

    def test_structural_relationships_without_github_fixture_raises(self):
        repo_ref = EntityRef(GITHUB_SOURCE, "github_repository", "repo-1")
        pr_ref = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        rel = make_rel(pr_ref, repo_ref, "belongs_to_repository", "structural_association", "obs-gh-1", "obs-gh-1")
        with pytest.raises(ValueError, match="GitHub relationships.*supplied but github_fixture is None"):
            assemble_evidence_bundle(
                bundle_id="b-1",
                bundle_version="1.0",
                github_structural_relationships=(rel,),
            )

    def test_mention_relationships_without_github_fixture_raises(self):
        pr_ref = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        jira_ref = EntityRef(JIRA_SOURCE, "jira_issue", "PLAT-100")
        rel = make_rel(pr_ref, jira_ref, "mentions", "lexical_match", "obs-gh-1", "obs-jira-1")
        with pytest.raises(ValueError, match="GitHub relationships.*supplied but github_fixture is None"):
            assemble_evidence_bundle(
                bundle_id="b-1",
                bundle_version="1.0",
                github_mention_relationships=(rel,),
            )

    def test_unresolved_references_without_github_fixture_raises(self):
        pr_ref = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        unres = make_unresolved(pr_ref, "obs-gh-1", "jira_issue", "PLAT-100", "mentions", "not observed")
        with pytest.raises(ValueError, match="GitHub relationships or unresolved references supplied"):
            assemble_evidence_bundle(
                bundle_id="b-1",
                bundle_version="1.0",
                github_mention_unresolved=(unres,),
            )

    def test_duplicate_observation_context_ids_raises(self):
        # Both Jira and GitHub using the same observation_id
        j_ctx = ObservationContext(observation_id="shared-obs-id", source_instance=JIRA_SOURCE)
        gh_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"), obs_id="shared-obs-id")
        gh_fix = make_normalized_gh(observations=(gh_obs,), obs_id="shared-obs-id")
        with pytest.raises(ValueError, match="Duplicate observation_id across supplied observation contexts"):
            assemble_evidence_bundle(
                bundle_id="b-1",
                bundle_version="1.0",
                jira_context=j_ctx,
                github_fixture=gh_fix,
            )


# =====================================================================
# 2. Jira-Only Bundle Tests
# =====================================================================

class TestJiraOnlyBundle:
    def test_assemble_jira_only_bundle(self):
        j_ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        obs1 = make_jira_obs("PLAT-101", obs_id="obs-jira-1")
        obs2 = make_jira_obs("PLAT-102", obs_id="obs-jira-1")
        bundle = assemble_evidence_bundle(
            bundle_id="jira-bundle-1",
            bundle_version="1.0.0",
            jira_context=j_ctx,
            jira_observations=(obs2, obs1),  # reverse order to test sorting
        )
        assert bundle.bundle_id == "jira-bundle-1"
        assert bundle.bundle_version == "1.0.0"
        assert len(bundle.observation_contexts) == 1
        assert bundle.observation_contexts[0].observation_id == "obs-jira-1"
        assert len(bundle.observations) == 2
        # Observations sorted canonically
        assert bundle.observations[0].entity_ref.entity_id == "PLAT-101"
        assert bundle.observations[1].entity_ref.entity_id == "PLAT-102"
        assert bundle.relationships == ()
        assert bundle.unresolved_references == ()

    def test_jira_quality_issues_preserved(self):
        j_ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        qi = QualityIssue(code="unsupported_value", message="Unknown status", subject_scope="work_items[0]")
        bundle = assemble_evidence_bundle(
            bundle_id="jira-bundle-2",
            bundle_version="1.0.0",
            jira_context=j_ctx,
            jira_quality_issues=(qi,),
        )
        assert len(bundle.quality_issues) == 1
        assert bundle.quality_issues[0].code == "unsupported_value"
        assert bundle.quality_issues[0].message == "Unknown status"


# =====================================================================
# 3. GitHub-Only Bundle Tests
# =====================================================================

class TestGitHubOnlyBundle:
    def test_assemble_github_only_bundle(self):
        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))
        pr_obs = make_github_obs("github_pull_request", "repo-1/42", GitHubPullRequestState(42, "PR", "open"))
        gh_fix = make_normalized_gh(observations=(pr_obs, repo_obs))

        rel = make_rel(
            pr_obs.entity_ref,
            repo_obs.entity_ref,
            "belongs_to_repository",
            "structural_association",
            "obs-gh-1",
            "obs-gh-1",
        )
        bundle = assemble_evidence_bundle(
            bundle_id="gh-bundle-1",
            bundle_version="1.0.0",
            github_fixture=gh_fix,
            github_structural_relationships=(rel,),
        )
        assert bundle.bundle_id == "gh-bundle-1"
        assert len(bundle.observation_contexts) == 1
        assert bundle.observation_contexts[0].source_instance == GITHUB_SOURCE
        assert len(bundle.observations) == 2
        assert len(bundle.relationships) == 1
        assert bundle.relationships[0].kind == "belongs_to_repository"

    def test_github_quality_issues_preserved(self):
        qi = QualityIssue(code="incomplete", message="Reviews partial", subject_scope="collection:reviews")
        gh_fix = make_normalized_gh(observations=(), quality_issues=(qi,))
        bundle = assemble_evidence_bundle(
            bundle_id="gh-bundle-2",
            bundle_version="1.0.0",
            github_fixture=gh_fix,
        )
        assert len(bundle.quality_issues) == 1
        assert bundle.quality_issues[0].code == "incomplete"


# =====================================================================
# 4. Combined Jira + GitHub Bundle Tests
# =====================================================================

class TestCombinedJiraGitHubBundle:
    def test_assemble_combined_bundle(self):
        j_ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        j_obs = make_jira_obs("PLAT-100", obs_id="obs-jira-1")

        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        gh_fix = make_normalized_gh(observations=(repo_obs, pr_obs))

        struct_rel = make_rel(
            pr_obs.entity_ref,
            repo_obs.entity_ref,
            "belongs_to_repository",
            "structural_association",
            "obs-gh-1",
            "obs-gh-1",
        )
        mention_rel = make_rel(
            pr_obs.entity_ref,
            j_obs.entity_ref,
            "mentions",
            "lexical_match",
            "obs-gh-1",
            "obs-jira-1",
        )

        bundle = assemble_evidence_bundle(
            bundle_id="combined-1",
            bundle_version="1.0.0",
            jira_context=j_ctx,
            jira_observations=(j_obs,),
            github_fixture=gh_fix,
            github_structural_relationships=(struct_rel,),
            github_mention_relationships=(mention_rel,),
        )

        # Contexts contain both, distinct source instances
        assert len(bundle.observation_contexts) == 2
        sources = {c.source_instance.source_kind for c in bundle.observation_contexts}
        assert sources == {"jira", "github"}

        # Total observations = 3 (1 jira + 2 github)
        assert len(bundle.observations) == 3

        # Relationships contain both structural and mention
        assert len(bundle.relationships) == 2
        kinds = {r.kind for r in bundle.relationships}
        assert kinds == {"belongs_to_repository", "mentions"}

        # Source instances preserved cleanly on endpoints
        mention = next(r for r in bundle.relationships if r.kind == "mentions")
        assert mention.subject_ref.source_instance == GITHUB_SOURCE
        assert mention.object_ref.source_instance == JIRA_SOURCE


# =====================================================================
# 5. Relationship Deduplication Tests
# =====================================================================

class TestRelationshipDeduplication:
    def test_duplicate_structural_relationship_merges_provenance(self):
        pr_ref = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        repo_ref = EntityRef(GITHUB_SOURCE, "github_repository", "repo-1")

        rel1 = make_rel(pr_ref, repo_ref, "belongs_to_repository", "structural_association", "obs-1", "obs-1", locator="loc[1]")
        rel2 = make_rel(pr_ref, repo_ref, "belongs_to_repository", "structural_association", "obs-1", "obs-1", locator="loc[2]")

        gh_fix = make_normalized_gh(observations=())
        bundle = assemble_evidence_bundle(
            bundle_id="b-dedup-1",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_structural_relationships=(rel1, rel2),
        )
        assert len(bundle.relationships) == 1
        assert len(bundle.relationships[0].provenance_refs) == 2
        # Deterministically sorted provenance
        locs = [p.record_locator for p in bundle.relationships[0].provenance_refs]
        assert locs == ["loc[1]", "loc[2]"]

    def test_duplicate_mention_relationship_merges_provenance(self):
        pr_ref = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        jira_ref = EntityRef(JIRA_SOURCE, "jira_issue", "PLAT-100")

        rel1 = make_rel(pr_ref, jira_ref, "mentions", "lexical_match", "obs-gh-1", "obs-jira-1", locator="title")
        rel2 = make_rel(pr_ref, jira_ref, "mentions", "lexical_match", "obs-gh-1", "obs-jira-1", locator="branch")

        gh_fix = make_normalized_gh(observations=())
        bundle = assemble_evidence_bundle(
            bundle_id="b-dedup-2",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_mention_relationships=(rel1, rel2),
        )
        assert len(bundle.relationships) == 1
        assert len(bundle.relationships[0].provenance_refs) == 2
        locs = [p.record_locator for p in bundle.relationships[0].provenance_refs]
        assert locs == ["branch", "title"]

    def test_structural_and_mention_between_same_endpoints_remain_distinct(self):
        # Hypothetical same endpoints with different kind/basis
        ep1 = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        ep2 = EntityRef(GITHUB_SOURCE, "github_commit", "repo-1/c0ffee")

        rel_struct = make_rel(ep1, ep2, "contains_commit", "structural_association", "obs-1", "obs-1")
        rel_mention = make_rel(ep1, ep2, "mentions", "lexical_match", "obs-1", "obs-1")

        gh_fix = make_normalized_gh(observations=())
        bundle = assemble_evidence_bundle(
            bundle_id="b-dedup-3",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_structural_relationships=(rel_struct,),
            github_mention_relationships=(rel_mention,),
        )
        assert len(bundle.relationships) == 2
        kinds = {r.kind for r in bundle.relationships}
        assert kinds == {"contains_commit", "mentions"}

    def test_merged_relationship_combines_quality_issues(self):
        pr_ref = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        repo_ref = EntityRef(GITHUB_SOURCE, "github_repository", "repo-1")

        qi1 = QualityIssue(code="incomplete", message="Issue A")
        qi2 = QualityIssue(code="invalid", message="Issue B")

        rel1 = make_rel(pr_ref, repo_ref, "belongs_to_repository", "structural_association", "obs-1", "obs-1", quality_issues=(qi1,))
        rel2 = make_rel(pr_ref, repo_ref, "belongs_to_repository", "structural_association", "obs-1", "obs-1", quality_issues=(qi2,))

        gh_fix = make_normalized_gh(observations=())
        bundle = assemble_evidence_bundle(
            bundle_id="b-dedup-4",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_structural_relationships=(rel1, rel2),
        )
        assert len(bundle.relationships) == 1
        assert len(bundle.relationships[0].quality_issues) == 2


# =====================================================================
# 6. Unresolved Reference Deduplication Tests
# =====================================================================

class TestUnresolvedReferenceDeduplication:
    def test_same_target_same_reason_merges_provenance(self):
        pr_ref = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        unres1 = make_unresolved(pr_ref, "obs-1", "jira_issue", "PLAT-100", "mentions", "not observed", locator="loc[1]")
        unres2 = make_unresolved(pr_ref, "obs-1", "jira_issue", "PLAT-100", "mentions", "not observed", locator="loc[2]")

        gh_fix = make_normalized_gh(observations=())
        bundle = assemble_evidence_bundle(
            bundle_id="b-unres-1",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_mention_unresolved=(unres1, unres2),
        )
        assert len(bundle.unresolved_references) == 1
        assert len(bundle.unresolved_references[0].provenance_refs) == 2

    def test_same_target_different_reason_preserved_as_distinct(self):
        pr_ref = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        unres1 = make_unresolved(pr_ref, "obs-1", "jira_issue", "PLAT-100", "mentions", "reason A: ambiguous")
        unres2 = make_unresolved(pr_ref, "obs-1", "jira_issue", "PLAT-100", "mentions", "reason B: quarantined")

        gh_fix = make_normalized_gh(observations=())
        bundle = assemble_evidence_bundle(
            bundle_id="b-unres-2",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_mention_unresolved=(unres1, unres2),
        )
        # Reason is part of logical identity; different reasons represent distinct evidence states!
        assert len(bundle.unresolved_references) == 2
        reasons = {u.reason for u in bundle.unresolved_references}
        assert reasons == {"reason A: ambiguous", "reason B: quarantined"}


# =====================================================================
# 7. Bundle Validation: Joint Endpoint Pairing Tests
# =====================================================================

class TestBundleValidationJointEndpointPairing:
    def test_valid_bundle_produces_no_quality_issues(self):
        j_ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        j_obs = make_jira_obs("PLAT-100", obs_id="obs-jira-1")

        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        gh_fix = make_normalized_gh(observations=(repo_obs, pr_obs))

        struct_rel = make_rel(pr_obs.entity_ref, repo_obs.entity_ref, "belongs_to_repository", "structural_association", "obs-gh-1", "obs-gh-1")
        mention_rel = make_rel(pr_obs.entity_ref, j_obs.entity_ref, "mentions", "lexical_match", "obs-gh-1", "obs-jira-1")

        bundle = assemble_evidence_bundle(
            bundle_id="b-val-1",
            bundle_version="1.0",
            jira_context=j_ctx,
            jira_observations=(j_obs,),
            github_fixture=gh_fix,
            github_structural_relationships=(struct_rel,),
            github_mention_relationships=(mention_rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert issues == ()

    def test_subject_obs_id_wrong_entity_detected(self):
        # Scenario: subject_obs_id points to an observation context, but that context contains Entity B instead of Entity A
        j_ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        j_obs_b = make_jira_obs("PLAT-200", obs_id="obs-jira-1")  # PLAT-200 is in obs-jira-1

        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        gh_fix = make_normalized_gh(observations=(repo_obs, pr_obs))

        # Malformed relationship: claims PLAT-100 is in obs-jira-1, but PLAT-100 is NOT in obs-jira-1
        bogus_jira_ref = EntityRef(JIRA_SOURCE, "jira_issue", "PLAT-100")
        bad_rel = make_rel(pr_obs.entity_ref, bogus_jira_ref, "mentions", "lexical_match", "obs-gh-1", "obs-jira-1")

        bundle = assemble_evidence_bundle(
            bundle_id="b-val-2",
            bundle_version="1.0",
            jira_context=j_ctx,
            jira_observations=(j_obs_b,),
            github_fixture=gh_fix,
            github_mention_relationships=(bad_rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 1
        assert issues[0].code == "unresolved"
        assert "Relationship object endpoint 'PLAT-100' does not resolve to an accepted observation" in issues[0].message

    def test_subject_obs_id_missing_detected(self):
        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        gh_fix = make_normalized_gh(observations=(repo_obs, pr_obs))

        # Subject observation ID does not exist anywhere in observations
        bad_rel = make_rel(pr_obs.entity_ref, repo_obs.entity_ref, "belongs_to_repository", "structural_association", "obs-ghost", "obs-gh-1")

        bundle = assemble_evidence_bundle(
            bundle_id="b-val-3",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_structural_relationships=(bad_rel,),
        )
        issues = validate_evidence_bundle(bundle)
        endpoint_issues = [q for q in issues if q.subject_scope == "relationship:endpoint"]
        assert len(endpoint_issues) >= 1
        assert any("obs-ghost" in q.message for q in endpoint_issues)

    def test_object_obs_id_missing_detected(self):
        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        gh_fix = make_normalized_gh(observations=(repo_obs, pr_obs))

        bad_rel = make_rel(pr_obs.entity_ref, repo_obs.entity_ref, "belongs_to_repository", "structural_association", "obs-gh-1", "obs-ghost")

        bundle = assemble_evidence_bundle(
            bundle_id="b-val-4",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_structural_relationships=(bad_rel,),
        )
        issues = validate_evidence_bundle(bundle)
        endpoint_issues = [q for q in issues if q.subject_scope == "relationship:endpoint"]
        assert len(endpoint_issues) >= 1
        assert any("obs-ghost" in q.message for q in endpoint_issues)


# =====================================================================
# 8. Bundle Validation: Invariants
# =====================================================================

class TestBundleValidationInvariants:
    def test_observation_context_id_not_found_detected(self):
        # Observation references an observation_context not present in bundle.observation_contexts
        orphan_ctx = ObservationContext(observation_id="unregistered-ctx", source_instance=JIRA_SOURCE)
        orphan_obs = EvidenceObservation(
            entity_ref=EntityRef(JIRA_SOURCE, "jira_issue", "PLAT-1"),
            observation_context=orphan_ctx,
            observed_state=JiraIssueState("PLAT-1", "Done", "Low", "done", "low", None, _T0, _T1),
        )
        # Construct directly without assemble_evidence_bundle to bypass assembler's context collection
        bundle = EvidenceBundle(
            bundle_id="b-inv-1",
            bundle_version="1.0",
            observation_contexts=(),
            observations=(orphan_obs,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(q.code == "unresolved" and "unregistered-ctx" in q.message for q in issues)

    def test_cross_system_jira_entity_kind_contamination_detected(self):
        # Jira source_kind with github_pull_request entity_kind
        bad_ref = EntityRef(JIRA_SOURCE, "github_pull_request", "repo/1")
        bad_obs = EvidenceObservation(
            entity_ref=bad_ref,
            observation_context=ObservationContext("obs-jira-1", JIRA_SOURCE),
            observed_state=GitHubPullRequestState(1, "title", "open"),
        )
        bundle = EvidenceBundle(
            bundle_id="b-inv-2",
            bundle_version="1.0",
            observation_contexts=(ObservationContext("obs-jira-1", JIRA_SOURCE),),
            observations=(bad_obs,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(q.code == "invalid" and "source_kind 'jira'" in q.message for q in issues)

    def test_cross_system_github_entity_kind_contamination_detected(self):
        # GitHub source_kind with jira_issue entity_kind
        bad_ref = EntityRef(GITHUB_SOURCE, "jira_issue", "PLAT-99")
        bad_obs = EvidenceObservation(
            entity_ref=bad_ref,
            observation_context=ObservationContext("obs-gh-1", GITHUB_SOURCE),
            observed_state=JiraIssueState("PLAT-99", "Done", "Low", "done", "low", None, _T0, _T1),
        )
        bundle = EvidenceBundle(
            bundle_id="b-inv-3",
            bundle_version="1.0",
            observation_contexts=(ObservationContext("obs-gh-1", GITHUB_SOURCE),),
            observations=(bad_obs,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(q.code == "invalid" and "source_kind 'github'" in q.message for q in issues)

    def test_invalid_provenance_observation_id_detected(self):
        obs = make_jira_obs("PLAT-1", obs_id="obs-jira-1")
        # Overwrite provenance to reference a nonexistent context
        bad_prov = ProvenanceRef(JIRA_SOURCE, "nonexistent-obs-id")
        bad_obs = EvidenceObservation(
            entity_ref=obs.entity_ref,
            observation_context=obs.observation_context,
            observed_state=obs.observed_state,
            provenance_refs=(bad_prov,),
        )
        bundle = EvidenceBundle(
            bundle_id="b-inv-4",
            bundle_version="1.0",
            observation_contexts=(ObservationContext("obs-jira-1", JIRA_SOURCE),),
            observations=(bad_obs,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(q.code == "invalid" and "nonexistent-obs-id" in q.message for q in issues)

    def test_duplicate_observation_identity_detected(self):
        obs1 = make_jira_obs("PLAT-1", obs_id="obs-jira-1")
        obs2 = make_jira_obs("PLAT-1", obs_id="obs-jira-1")  # accidental duplicate
        bundle = EvidenceBundle(
            bundle_id="b-inv-5",
            bundle_version="1.0",
            observation_contexts=(ObservationContext("obs-jira-1", JIRA_SOURCE),),
            observations=(obs1, obs2),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(q.code == "invalid" and "Duplicate observation identity" in q.message for q in issues)

    def test_zero_observation_context_is_valid_coverage_evidence(self):
        # A context with zero observations is legitimate coverage evidence (e.g. commits unavailable)
        cov_ctx = ObservationContext(
            observation_id="obs-gh-coverage",
            source_instance=GITHUB_SOURCE,
            coverage_note="commit collection unavailable",
        )
        bundle = EvidenceBundle(
            bundle_id="b-inv-6",
            bundle_version="1.0",
            observation_contexts=(cov_ctx,),
            observations=(),
            relationships=(),
            unresolved_references=(),
            quality_issues=(),
        )
        # Must NOT produce any issues!
        issues = validate_evidence_bundle(bundle)
        assert issues == ()

    def test_unresolved_as_resolved_conflict_detected(self):
        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        gh_fix = make_normalized_gh(observations=(repo_obs, pr_obs))

        # Both resolved and unresolved for same edge
        rel = make_rel(pr_obs.entity_ref, repo_obs.entity_ref, "belongs_to_repository", "structural_association", "obs-gh-1", "obs-gh-1")
        unres = make_unresolved(pr_obs.entity_ref, "obs-gh-1", "github_repository", "repo-1", "belongs_to_repository", "contradictory failure")

        bundle = assemble_evidence_bundle(
            bundle_id="b-inv-7",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_structural_relationships=(rel,),
            github_structural_unresolved=(unres,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(q.code == "contradictory" and "is recorded as both resolved and unresolved" in q.message for q in issues)

    def test_structural_predicate_incompatible_basis_detected(self):
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))

        # belongs_to_repository with lexical_match basis is invalid
        bad_rel = make_rel(pr_obs.entity_ref, repo_obs.entity_ref, "belongs_to_repository", "lexical_match", "obs-gh-1", "obs-gh-1")
        bundle = EvidenceBundle(
            bundle_id="b-inv-8",
            bundle_version="1.0",
            observation_contexts=(ObservationContext("obs-gh-1", GITHUB_SOURCE),),
            observations=(pr_obs, repo_obs),
            relationships=(bad_rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(q.code == "invalid" and "expected 'mentions'" in q.message for q in issues)

    def test_mention_incompatible_basis_detected(self):
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        j_obs = make_jira_obs("PLAT-100", obs_id="obs-jira-1")

        # mentions with structural_association basis is invalid
        bad_rel = make_rel(pr_obs.entity_ref, j_obs.entity_ref, "mentions", "structural_association", "obs-gh-1", "obs-jira-1")
        bundle = EvidenceBundle(
            bundle_id="b-inv-9",
            bundle_version="1.0",
            observation_contexts=(
                ObservationContext("obs-gh-1", GITHUB_SOURCE),
                ObservationContext("obs-jira-1", JIRA_SOURCE),
            ),
            observations=(pr_obs, j_obs),
            relationships=(bad_rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(q.code == "invalid" and "not a valid structural predicate" in q.message for q in issues)

    def test_observation_context_source_instance_mismatch_detected(self):
        # Observation context has ID obs-1 with GITHUB_SOURCE, but registered context has JIRA_SOURCE
        j_ctx = ObservationContext("obs-1", JIRA_SOURCE)
        mismatched_obs = EvidenceObservation(
            entity_ref=EntityRef(JIRA_SOURCE, "jira_issue", "PLAT-1"),
            observation_context=ObservationContext("obs-1", GITHUB_SOURCE),
            observed_state=JiraIssueState("PLAT-1", "Done", "Low", "done", "low", None, _T0, _T1),
        )
        bundle = EvidenceBundle(
            bundle_id="b-audit-1",
            bundle_version="1.0",
            observation_contexts=(j_ctx,),
            observations=(mismatched_obs,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(q.code == "invalid" and "context source_instance" in q.message for q in issues)

    def test_unresolved_reference_source_endpoint_pairing_detected(self):
        # Unresolved reference source_obs_id does not contain source_ref
        j_ctx = ObservationContext("obs-jira-1", JIRA_SOURCE)
        j_obs = make_jira_obs("PLAT-10", obs_id="obs-jira-1")

        # Unresolved reference claims source is PLAT-99 in obs-jira-1, but PLAT-99 is NOT in obs-jira-1
        bogus_source_ref = EntityRef(JIRA_SOURCE, "jira_issue", "PLAT-99")
        unres = make_unresolved(bogus_source_ref, "obs-jira-1", "github_commit", "c0ffee", "contains_commit", "not found")

        bundle = EvidenceBundle(
            bundle_id="b-audit-2",
            bundle_version="1.0",
            observation_contexts=(j_ctx,),
            observations=(j_obs,),
            unresolved_references=(unres,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(
            q.code == "unresolved"
            and q.subject_scope == "unresolved_reference:source"
            and "PLAT-99" in q.message
            for q in issues
        )

    def test_provenance_source_instance_mismatch_detected(self):
        # ProvenanceRef has observation_id obs-jira-1 (JIRA_SOURCE), but prov.source_instance is GITHUB_SOURCE
        j_ctx = ObservationContext("obs-jira-1", JIRA_SOURCE)
        mismatched_prov = ProvenanceRef(GITHUB_SOURCE, "obs-jira-1")
        obs = EvidenceObservation(
            entity_ref=EntityRef(JIRA_SOURCE, "jira_issue", "PLAT-1"),
            observation_context=j_ctx,
            observed_state=JiraIssueState("PLAT-1", "Done", "Low", "done", "low", None, _T0, _T1),
            provenance_refs=(mismatched_prov,),
        )
        bundle = EvidenceBundle(
            bundle_id="b-audit-3",
            bundle_version="1.0",
            observation_contexts=(j_ctx,),
            observations=(obs,),
        )
        issues = validate_evidence_bundle(bundle)
        assert any(
            q.code == "invalid"
            and "provenance source_instance" in q.message
            for q in issues
        )

    def test_relationship_and_unresolved_missing_supporting_provenance_detected(self):
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))

        # Relationship and UnresolvedReference with empty provenance_refs
        rel_no_prov = EvidenceRelationship(
            subject_ref=pr_obs.entity_ref,
            object_ref=repo_obs.entity_ref,
            kind="belongs_to_repository",
            basis="structural_association",
            subject_observation_id="obs-gh-1",
            object_observation_id="obs-gh-1",
            provenance_refs=(),
        )
        unres_no_prov = UnresolvedReference(
            source_ref=pr_obs.entity_ref,
            source_observation_id="obs-gh-1",
            target_entity_kind="github_branch",
            target_identifier="main",
            relationship_kind="has_base_branch",
            reason="not observed",
            provenance_refs=(),
        )
        bundle = EvidenceBundle(
            bundle_id="b-audit-4",
            bundle_version="1.0",
            observation_contexts=(ObservationContext("obs-gh-1", GITHUB_SOURCE),),
            observations=(pr_obs, repo_obs),
            relationships=(rel_no_prov,),
            unresolved_references=(unres_no_prov,),
        )
        issues = validate_evidence_bundle(bundle)
        missing_issues = [q for q in issues if q.code == "missing"]
        assert len(missing_issues) == 2
        scopes = {q.subject_scope for q in missing_issues}
        assert scopes == {"relationship:provenance", "unresolved_reference:provenance"}


# =====================================================================
# 9. Determinism Tests
# =====================================================================

class TestDeterminism:
    def test_repeated_assembly_identical_output(self):
        j_ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        j_obs = make_jira_obs("PLAT-100", obs_id="obs-jira-1")
        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        gh_fix = make_normalized_gh(observations=(repo_obs, pr_obs))
        rel = make_rel(pr_obs.entity_ref, repo_obs.entity_ref, "belongs_to_repository", "structural_association", "obs-gh-1", "obs-gh-1")

        b1 = assemble_evidence_bundle(
            bundle_id="b-det-1",
            bundle_version="1.0",
            jira_context=j_ctx,
            jira_observations=(j_obs,),
            github_fixture=gh_fix,
            github_structural_relationships=(rel,),
        )
        b2 = assemble_evidence_bundle(
            bundle_id="b-det-1",
            bundle_version="1.0",
            jira_context=j_ctx,
            jira_observations=(j_obs,),
            github_fixture=gh_fix,
            github_structural_relationships=(rel,),
        )
        assert b1 == b2

    def test_observation_input_permutation_invariance(self):
        j_ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        obs_a = make_jira_obs("PLAT-10", obs_id="obs-jira-1")
        obs_b = make_jira_obs("PLAT-20", obs_id="obs-jira-1")
        obs_c = make_jira_obs("PLAT-30", obs_id="obs-jira-1")

        b_forward = assemble_evidence_bundle(
            bundle_id="b-perm",
            bundle_version="1.0",
            jira_context=j_ctx,
            jira_observations=(obs_a, obs_b, obs_c),
        )
        b_reverse = assemble_evidence_bundle(
            bundle_id="b-perm",
            bundle_version="1.0",
            jira_context=j_ctx,
            jira_observations=(obs_c, obs_a, obs_b),
        )
        assert b_forward.observations == b_reverse.observations

    def test_relationship_input_permutation_invariance(self):
        pr_ref = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        repo_ref = EntityRef(GITHUB_SOURCE, "github_repository", "repo-1")
        c1_ref = EntityRef(GITHUB_SOURCE, "github_commit", "repo-1/c1")
        c2_ref = EntityRef(GITHUB_SOURCE, "github_commit", "repo-1/c2")

        rel1 = make_rel(pr_ref, repo_ref, "belongs_to_repository", "structural_association", "obs-gh-1", "obs-gh-1")
        rel2 = make_rel(pr_ref, c1_ref, "contains_commit", "structural_association", "obs-gh-1", "obs-gh-1")
        rel3 = make_rel(pr_ref, c2_ref, "contains_commit", "structural_association", "obs-gh-1", "obs-gh-1")

        gh_fix = make_normalized_gh(observations=())

        b1 = assemble_evidence_bundle(
            bundle_id="b-rel-perm",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_structural_relationships=(rel1, rel2, rel3),
        )
        b2 = assemble_evidence_bundle(
            bundle_id="b-rel-perm",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_structural_relationships=(rel3, rel1, rel2),
        )
        assert b1.relationships == b2.relationships


# =====================================================================
# 10. Canonical Serialization Verification
# =====================================================================

class TestCanonicalSerialization:
    def test_bundle_serialization_includes_relationships_and_unresolved(self):
        j_ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        j_obs = make_jira_obs("PLAT-100", obs_id="obs-jira-1")

        repo_obs = make_github_obs("github_repository", "repo-1", GitHubRepositoryState("org", "repo-1"))
        pr_obs = make_github_obs("github_pull_request", "repo-1/10", GitHubPullRequestState(10, "PR", "open"))
        gh_fix = make_normalized_gh(observations=(repo_obs, pr_obs))

        struct_rel = make_rel(pr_obs.entity_ref, repo_obs.entity_ref, "belongs_to_repository", "structural_association", "obs-gh-1", "obs-gh-1")
        unres = make_unresolved(pr_obs.entity_ref, "obs-gh-1", "jira_issue", "PLAT-999", "mentions", "not observed")

        bundle = assemble_evidence_bundle(
            bundle_id="b-ser-1",
            bundle_version="1.0",
            jira_context=j_ctx,
            jira_observations=(j_obs,),
            github_fixture=gh_fix,
            github_structural_relationships=(struct_rel,),
            github_mention_unresolved=(unres,),
        )

        serialized = serialize_evidence_bundle(bundle)
        assert "relationships" in serialized
        assert len(serialized["relationships"]) == 1
        assert serialized["relationships"][0]["kind"] == "belongs_to_repository"

        assert "unresolved_references" in serialized
        assert len(serialized["unresolved_references"]) == 1
        assert serialized["unresolved_references"][0]["target_identifier"] == "PLAT-999"

        # Verify JSON serializability
        dumped = json.dumps(serialized, sort_keys=True)
        assert "PLAT-999" in dumped
        assert "belongs_to_repository" in dumped

    def test_sparse_serialization_omits_empty_collections(self):
        # When relationships and unresolved_references are empty, they are omitted
        j_ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        bundle = assemble_evidence_bundle(
            bundle_id="b-ser-2",
            bundle_version="1.0",
            jira_context=j_ctx,
        )
        serialized = serialize_evidence_bundle(bundle)
        assert "relationships" not in serialized
        assert "unresolved_references" not in serialized
        assert "quality_issues" not in serialized


# =====================================================================
# 11. Immutability Tests
# =====================================================================

class TestImmutability:
    def test_assembled_bundle_is_frozen(self):
        bundle = assemble_evidence_bundle(
            bundle_id="b-freeze",
            bundle_version="1.0",
        )
        with pytest.raises((FrozenInstanceError, AttributeError)):
            bundle.bundle_id = "mutated"  # type: ignore[misc]

    def test_input_tuples_are_not_mutated(self):
        j_ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        obs1 = make_jira_obs("PLAT-1", obs_id="obs-jira-1")
        input_tuple = (obs1,)

        bundle = assemble_evidence_bundle(
            bundle_id="b-imm",
            bundle_version="1.0",
            jira_context=j_ctx,
            jira_observations=input_tuple,
        )
        assert input_tuple == (obs1,)
        assert bundle.observations == input_tuple


# =====================================================================
# 12. Edge Cases
# =====================================================================

class TestEdgeCases:
    def test_empty_bundle_valid(self):
        bundle = assemble_evidence_bundle(
            bundle_id="b-empty",
            bundle_version="1.0",
        )
        assert bundle.observation_contexts == ()
        assert bundle.observations == ()
        assert bundle.relationships == ()
        assert bundle.unresolved_references == ()
        assert bundle.quality_issues == ()
        issues = validate_evidence_bundle(bundle)
        assert issues == ()

    def test_bundle_with_only_unresolved_references(self):
        pr_ref = EntityRef(GITHUB_SOURCE, "github_pull_request", "repo-1/10")
        unres = make_unresolved(pr_ref, "obs-gh-1", "jira_issue", "PLAT-1", "mentions", "not observed")
        gh_fix = make_normalized_gh(observations=())

        bundle = assemble_evidence_bundle(
            bundle_id="b-unres-only",
            bundle_version="1.0",
            github_fixture=gh_fix,
            github_mention_unresolved=(unres,),
        )
        assert len(bundle.unresolved_references) == 1
        assert len(bundle.relationships) == 0

    def test_coverage_only_context_bundle(self):
        # Context with coverage_note indicating unavailable data and zero observations
        gh_ctx = ObservationContext(
            observation_id="obs-gh-cov",
            source_instance=GITHUB_SOURCE,
            coverage_note="branch collection unavailable",
        )
        gh_fix = NormalizedGitHubFixture(
            raw_document={"fixture_id": "cov-1"},
            source_instance=GITHUB_SOURCE,
            observation_context=gh_ctx,
            observations=(),
            quality_issues=(),
            quarantined_records=(),
        )
        bundle = assemble_evidence_bundle(
            bundle_id="b-cov",
            bundle_version="1.0",
            github_fixture=gh_fix,
        )
        assert len(bundle.observation_contexts) == 1
        assert bundle.observation_contexts[0].coverage_note == "branch collection unavailable"
        assert len(bundle.observations) == 0
        issues = validate_evidence_bundle(bundle)
        assert issues == ()


# =====================================================================
# 13. End-to-End Integration Tests
# =====================================================================

class TestEndToEndIntegration:
    def test_full_pipeline_jira_and_github_e2e(self):
        jira_raw_path = Path(__file__).resolve().parents[2] / "fixtures" / "jira" / "northstar_clean_week_1.json"
        raw_jira = load_fixture(jira_raw_path)
        val_jira = validate_jira_fixture(raw_jira)
        norm_jira = normalize_jira_fixture(val_jira)
        j_ctx, j_obs, j_quality = adapt_jira_evidence(
            normalized=norm_jira,
            source_instance=JIRA_SOURCE,
            observation_id="obs-jira-realistic",
            fixture_id="cross-platform-realistic-history",
        )

        # 2. GitHub pipeline: fixture with mention of real Jira keys -> validate -> normalize -> relationships -> mentions
        raw_github = {
            "contract_version": "shadow-github-fixture-v1",
            "fixture_id": "gh-e2e-fixture",
            "source_instance": {
                "source_kind": "github",
                "instance_id": "github.com/org-core",
            },
            "observation_context": {
                "observation_id": "obs-gh-e2e",
            },
            "repositories": [
                {
                    "repo_id": "repo-core",
                    "owner": "org-core",
                    "name": "core",
                    "branches": [
                        {"name": "main"},
                        {"name": "feature/PLAT-101-cache"},
                    ],
                    "commits": [
                        {
                            "sha": "a1b2c3d4e5f60000000000000000000000000001",
                            "message": "PLAT-101: fix memory cache",
                        }
                    ],
                    "pull_requests": [
                        {
                            "number": 42,
                            "title": "Implement cache layer [PLAT-101]",
                            "state": "closed",
                            "source_branch": "feature/PLAT-101-cache",
                            "target_branch": "main",
                            "pull_request_commits": ["a1b2c3d4e5f60000000000000000000000000001"],
                        }
                    ],
                }
            ],
        }

        val_github = validate_github_fixture(raw_github)
        norm_github = normalize_github_fixture(val_github)

        # Structural relationships (CSE-1.5)
        struct_rels, struct_unres = resolve_github_relationships(norm_github)

        # Mentions resolution (CSE-1.6)
        policy = MentionLexicalPolicy(frozenset({"PLAT"}))
        mention_rels, mention_unres = resolve_github_jira_mentions(
            normalized=norm_github,
            jira_observations=j_obs,
            jira_source_instance=JIRA_SOURCE,
            policy=policy,
        )

        # 3. Assemble bundle (CSE-1.7)
        bundle = assemble_evidence_bundle(
            bundle_id="e2e-bundle-1",
            bundle_version="1.0.0",
            jira_context=j_ctx,
            jira_observations=j_obs,
            jira_quality_issues=j_quality,
            github_fixture=norm_github,
            github_structural_relationships=struct_rels,
            github_structural_unresolved=struct_unres,
            github_mention_relationships=mention_rels,
            github_mention_unresolved=mention_unres,
        )

        # 4. Validate assembled bundle
        issues = validate_evidence_bundle(bundle)
        assert issues == ()

        # Assert structure
        assert len(bundle.observation_contexts) == 2
        assert len(bundle.observations) == len(j_obs) + len(norm_github.observations)
        assert len(bundle.relationships) == len(struct_rels) + len(mention_rels)
        assert len(bundle.unresolved_references) == len(struct_unres) + len(mention_unres)

        # Verify serialization
        serialized = serialize_evidence_bundle(bundle)
        assert serialized["bundle_id"] == "e2e-bundle-1"
        assert len(serialized["observation_contexts"]) == 2
        assert len(serialized["observations"]) == len(bundle.observations)
        assert len(serialized["relationships"]) == len(bundle.relationships)
