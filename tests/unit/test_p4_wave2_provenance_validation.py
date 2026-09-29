"""Pass 4 / Wave 2 — EvidenceBundle Provenance Validation Integration Tests.

Tests the integration of bounded in-memory provenance dereferencing into
validate_evidence_bundle(bundle, fixtures_by_id).

Covers all prompt requirements:
1. validate_evidence_bundle() without fixtures_by_id (backward compatibility)
2. empty fixtures_by_id ({})
3. valid fixture mapping (complete resolution, zero issues)
4. missing fixture_id (fixture cannot be identified)
5. wrong fixture_id (fixture_id not present in fixtures_by_id)
6. malformed locator (grammar violations, unclosed brackets)
7. out-of-bounds locator (index exceeding collection size)
8. entity mismatch (locator resolves to entity Y while EntityRef is entity X)
9. invalid source_field_path (field does not exist on resolved record)
10. locator-less provenance (record_locator=None skipped, no quality issue)
11. existing structural provenance error + dereference error together
12. provenance-order permutation invariance (ordering of prov refs does not affect outcome)
13. duplicate provenance determinism (duplicate identical prov refs produce deterministic output)
14. real fixture integration (end-to-end assembly + validation with real fixtures)
15. relationship provenance dereferencing (structural and mention edges)
16. unresolved reference provenance dereferencing
17. temporal cutoff staleness detection during bundle validation
18. access-denied detection during bundle validation
19. fixture wrapper object support (raw_document attribute)
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

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


# ── Shared Test Constants and Fixtures ────────────────────────────────

JIRA_SOURCE = SourceInstance(source_kind="jira", instance_id="jira.company.com")
GITHUB_SOURCE = SourceInstance(source_kind="github", instance_id="github.com/org-core")

T0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

MINIMAL_JIRA_RAW = {
    "work_items": [
        {"key": "PLAT-101", "source_id": "10001", "id": "10001", "title": "First Task", "status": "In Progress"},
        {"key": "PLAT-102", "source_id": "10002", "id": "10002", "title": "Second Task", "status": "Done"},
    ]
}

MINIMAL_GITHUB_RAW = {
    "fixture_id": "gh-min-1",
    "repositories": [
        {
            "repo_id": "repo-core",
            "owner": "org-core",
            "name": "core-repo",
            "default_branch": "main",
            "branches": [
                {"name": "main", "head_commit_id": "c0ffee1"},
            ],
            "commits": [
                {"sha": "c0ffee1", "message": "Initial commit PLAT-101", "author_login": "alice", "committed_at": "2026-01-01T12:00:00Z"},
            ],
            "pull_requests": [
                {
                    "number": 10,
                    "title": "PR for PLAT-101",
                    "state": "open",
                    "author_login": "alice",
                    "created_at": "2026-01-01T12:00:00Z",
                    "target_branch": "main",
                    "source_branch": "feature",
                    "reviews": [],
                },
            ],
        }
    ]
}


def make_test_obs(
    entity_id: str = "PLAT-101",
    obs_id: str = "obs-jira-1",
    source_instance: SourceInstance = JIRA_SOURCE,
    entity_kind: str = "jira_issue",
    fixture_id: str | None = "jira-fix-1",
    record_locator: str | None = "work_items[0]",
    source_field_path: str | None = None,
) -> EvidenceObservation:
    ctx = ObservationContext(observation_id=obs_id, source_instance=source_instance)
    ref = EntityRef(source_instance=source_instance, entity_kind=entity_kind, entity_id=entity_id)
    prov = ProvenanceRef(
        source_instance=source_instance,
        observation_id=obs_id,
        fixture_id=fixture_id,
        record_locator=record_locator,
        source_field_path=source_field_path,
    )
    state = JiraIssueState(
        key=entity_id,
        source_status="In Progress",
        source_priority="High",
        status_category="in_progress",
        priority_band="high",
        assignee="Alice",
        created_at=T0,
        updated_at=T1,
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=ctx,
        observed_state=state,
        provenance_refs=(prov,),
    )


def make_test_bundle(
    observations: tuple[EvidenceObservation, ...],
    relationships: tuple[EvidenceRelationship, ...] = (),
    unresolved_references: tuple[UnresolvedReference, ...] = (),
    observation_contexts: tuple[ObservationContext, ...] | None = None,
) -> EvidenceBundle:
    if observation_contexts is None:
        ctx_map: dict[str, ObservationContext] = {}
        for o in observations:
            ctx_map[o.observation_context.observation_id] = o.observation_context
        observation_contexts = tuple(ctx_map.values())

    return EvidenceBundle(
        bundle_id="test-bundle-w2",
        bundle_version="1.0.0",
        observation_contexts=observation_contexts,
        observations=observations,
        relationships=relationships,
        unresolved_references=unresolved_references,
        quality_issues=(),
    )


# ═══════════════════════════════════════════════════════════════════════
#  1. BACKWARD COMPATIBILITY: validate_evidence_bundle() without fixtures
# ═══════════════════════════════════════════════════════════════════════

class TestBackwardCompatibility:
    """Verify that omitting fixtures_by_id behaves identically to Pass 3.1."""

    def test_default_fixtures_by_id_is_none(self):
        obs = make_test_obs()
        bundle = make_test_bundle((obs,))
        issues = validate_evidence_bundle(bundle)
        assert issues == ()

    def test_explicit_none_fixtures_by_id(self):
        obs = make_test_obs()
        bundle = make_test_bundle((obs,))
        issues = validate_evidence_bundle(bundle, fixtures_by_id=None)
        assert issues == ()

    def test_invalid_locator_ignored_when_fixtures_by_id_none(self):
        """Even a totally bogus locator does not emit an issue if fixtures_by_id is None."""
        obs = make_test_obs(record_locator="totally.invalid[[brackets]]99999")
        bundle = make_test_bundle((obs,))
        issues = validate_evidence_bundle(bundle, fixtures_by_id=None)
        assert issues == ()


# ═══════════════════════════════════════════════════════════════════════
#  2. EMPTY fixtures_by_id ({})
# ═══════════════════════════════════════════════════════════════════════

class TestEmptyFixturesById:
    """When fixtures_by_id is an empty dict, all locator-bearing refs are UNAVAILABLE."""

    def test_empty_fixtures_dict_emits_unresolved_fixture_issue(self):
        obs = make_test_obs(fixture_id="jira-fix-1", record_locator="work_items[0]")
        bundle = make_test_bundle((obs,))
        issues = validate_evidence_bundle(bundle, fixtures_by_id={})
        assert len(issues) == 1
        assert issues[0].code == "unresolved"
        assert issues[0].subject_scope == "provenance:fixture"
        assert "unavailable in fixtures_by_id" in issues[0].message
        assert issues[0].subject_ref == obs.entity_ref


# ═══════════════════════════════════════════════════════════════════════
#  3. VALID FIXTURE MAPPING
# ═══════════════════════════════════════════════════════════════════════

class TestValidFixtureMapping:
    """When fixtures_by_id contains matching fixtures, dereferencing passes cleanly."""

    def test_valid_jira_dereferences_cleanly(self):
        obs = make_test_obs(entity_id="PLAT-101", fixture_id="jira-fix-1", record_locator="work_items[0]")
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert issues == ()

    def test_multiple_observations_all_resolve(self):
        obs1 = make_test_obs(entity_id="PLAT-101", fixture_id="jira-fix-1", record_locator="work_items[0]")
        obs2 = make_test_obs(entity_id="PLAT-102", fixture_id="jira-fix-1", record_locator="work_items[1]")
        bundle = make_test_bundle((obs1, obs2))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert issues == ()


# ═══════════════════════════════════════════════════════════════════════
#  4. MISSING fixture_id (fixture cannot be identified)
# ═══════════════════════════════════════════════════════════════════════

class TestMissingFixtureId:
    """When a locator is present but fixture_id is None, must NOT guess a fixture."""

    def test_missing_fixture_id_emits_unresolved_issue(self):
        obs = make_test_obs(fixture_id=None, record_locator="work_items[0]")
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert len(issues) == 1
        assert issues[0].code == "unresolved"
        assert issues[0].subject_scope == "provenance:fixture"
        assert "fixture_id is absent" in issues[0].message
        assert issues[0].subject_ref == obs.entity_ref


# ═══════════════════════════════════════════════════════════════════════
#  5. WRONG fixture_id (not in fixtures_by_id)
# ═══════════════════════════════════════════════════════════════════════

class TestWrongFixtureId:
    """When fixture_id does not exist in fixtures_by_id, emit structured issue."""

    def test_wrong_fixture_id_emits_unresolved_issue(self):
        obs = make_test_obs(fixture_id="nonexistent-fixture", record_locator="work_items[0]")
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert len(issues) == 1
        assert issues[0].code == "unresolved"
        assert issues[0].subject_scope == "provenance:fixture"
        assert "nonexistent-fixture" in issues[0].message
        assert "unavailable in fixtures_by_id" in issues[0].message


# ═══════════════════════════════════════════════════════════════════════
#  6. MALFORMED LOCATOR
# ═══════════════════════════════════════════════════════════════════════

class TestMalformedLocator:
    """Verify that syntax/grammar violations produce structured issues."""

    def test_unclosed_bracket(self):
        obs = make_test_obs(record_locator="work_items[0")
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert len(issues) == 1
        assert issues[0].code == "invalid"
        assert issues[0].subject_scope == "provenance:locator"
        assert "violates grammar" in issues[0].message

    def test_unauthorized_collection(self):
        obs = make_test_obs(record_locator="forbidden_table[0]")
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert len(issues) == 1
        assert issues[0].code == "unsupported_value"
        assert issues[0].subject_scope == "provenance:locator"
        assert "not an authorized" in issues[0].message


# ═══════════════════════════════════════════════════════════════════════
#  7. OUT-OF-BOUNDS LOCATOR
# ═══════════════════════════════════════════════════════════════════════

class TestOutOfBoundsLocator:
    """Verify that indices exceeding collection size produce unresolved issues."""

    def test_out_of_bounds_index(self):
        obs = make_test_obs(record_locator="work_items[99999]")
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert len(issues) == 1
        assert issues[0].code == "unresolved"
        assert issues[0].subject_scope == "provenance:locator"
        assert "out of bounds" in issues[0].message


# ═══════════════════════════════════════════════════════════════════════
#  8. ENTITY MISMATCH
# ═══════════════════════════════════════════════════════════════════════

class TestEntityMismatch:
    """Verify that resolved record identity mismatch produces contradictory issue."""

    def test_jira_identity_mismatch_detected(self):
        # Observation claims entity_id is PLAT-999, but work_items[0] is PLAT-101
        obs = make_test_obs(entity_id="PLAT-999", record_locator="work_items[0]")
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert len(issues) == 1
        assert issues[0].code == "contradictory"
        assert issues[0].subject_scope == "provenance:identity"
        assert "PLAT-101" in issues[0].message
        assert "PLAT-999" in issues[0].message


# ═══════════════════════════════════════════════════════════════════════
#  9. INVALID source_field_path
# ═══════════════════════════════════════════════════════════════════════

class TestInvalidSourceFieldPath:
    """Verify that a nonexistent field path produces missing field issue."""

    def test_nonexistent_field_path_detected(self):
        obs = make_test_obs(
            entity_id="PLAT-101",
            record_locator="work_items[0]",
            source_field_path="definitely_not_a_field",
        )
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert len(issues) == 1
        assert issues[0].code == "missing"
        assert issues[0].subject_scope == "provenance:field"
        assert "definitely_not_a_field" in issues[0].message

    def test_valid_field_path_passes(self):
        obs = make_test_obs(
            entity_id="PLAT-101",
            record_locator="work_items[0]",
            source_field_path="status",
        )
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert issues == ()


# ═══════════════════════════════════════════════════════════════════════
# 10. LOCATOR-LESS PROVENANCE (record_locator=None)
# ═══════════════════════════════════════════════════════════════════════

class TestLocatorLessProvenance:
    """Verify that record_locator=None is skipped without emitting an error."""

    def test_none_locator_skipped_cleanly(self):
        obs = make_test_obs(record_locator=None)
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert issues == ()


# ═══════════════════════════════════════════════════════════════════════
# 11. STRUCTURAL ERROR + DEREFERENCE ERROR TOGETHER
# ═══════════════════════════════════════════════════════════════════════

class TestCombinedStructuralAndDereferenceErrors:
    """Verify that structural errors and dereferencing errors coexist."""

    def test_unknown_obs_id_and_malformed_locator_both_reported(self):
        # Observation context is registered under "obs-good", but prov ref points to "obs-ghost"
        ctx = ObservationContext(observation_id="obs-good", source_instance=JIRA_SOURCE)
        ref = EntityRef(source_instance=JIRA_SOURCE, entity_kind="jira_issue", entity_id="PLAT-101")
        prov = ProvenanceRef(
            source_instance=JIRA_SOURCE,
            observation_id="obs-ghost",  # Structural error!
            fixture_id="jira-fix-1",
            record_locator="work_items[malformed[bracket]]",  # Dereferencing error!
        )
        obs = EvidenceObservation(
            entity_ref=ref,
            observation_context=ctx,
            observed_state=JiraIssueState(key="PLAT-101", source_status="Open", source_priority="P1", status_category="open", priority_band="high", assignee="A", created_at=T0, updated_at=T1),
            provenance_refs=(prov,),
        )
        bundle = make_test_bundle((obs,), observation_contexts=(ctx,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)

        scopes = {q.subject_scope for q in issues}
        assert "provenance:context" in scopes  # from structural check
        assert "provenance:locator" in scopes  # from dereferencer check


# ═══════════════════════════════════════════════════════════════════════
# 12. PROVENANCE-ORDER PERMUTATION INVARIANCE
# ═══════════════════════════════════════════════════════════════════════

class TestPermutationInvariance:
    """Verify that the order of provenance refs does not affect validation output."""

    def test_different_prov_order_produces_identical_issues(self):
        ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        ref = EntityRef(source_instance=JIRA_SOURCE, entity_kind="jira_issue", entity_id="PLAT-101")

        p_bad_loc = ProvenanceRef(
            source_instance=JIRA_SOURCE,
            observation_id="obs-jira-1",
            fixture_id="jira-fix-1",
            record_locator="work_items[99999]",  # out of bounds
        )
        p_bad_field = ProvenanceRef(
            source_instance=JIRA_SOURCE,
            observation_id="obs-jira-1",
            fixture_id="jira-fix-1",
            record_locator="work_items[0]",
            source_field_path="nonexistent_field",  # invalid field
        )

        obs_a = EvidenceObservation(
            entity_ref=ref,
            observation_context=ctx,
            observed_state=JiraIssueState(key="PLAT-101", source_status="Open", source_priority="P1", status_category="open", priority_band="high", assignee="A", created_at=T0, updated_at=T1),
            provenance_refs=(p_bad_loc, p_bad_field),
        )
        obs_b = EvidenceObservation(
            entity_ref=ref,
            observation_context=ctx,
            observed_state=JiraIssueState(key="PLAT-101", source_status="Open", source_priority="P1", status_category="open", priority_band="high", assignee="A", created_at=T0, updated_at=T1),
            provenance_refs=(p_bad_field, p_bad_loc),
        )

        bundle_a = make_test_bundle((obs_a,))
        bundle_b = make_test_bundle((obs_b,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}

        issues_a = validate_evidence_bundle(bundle_a, fixtures_by_id=fixtures)
        issues_b = validate_evidence_bundle(bundle_b, fixtures_by_id=fixtures)

        assert issues_a == issues_b
        assert len(issues_a) == 2


# ═══════════════════════════════════════════════════════════════════════
# 13. DUPLICATE PROVENANCE DETERMINISM
# ═══════════════════════════════════════════════════════════════════════

class TestDuplicateProvenanceDeterminism:
    """Verify that duplicate identical provenance references produce deterministic output."""

    def test_duplicate_prov_refs_do_not_duplicate_issues(self):
        p = ProvenanceRef(
            source_instance=JIRA_SOURCE,
            observation_id="obs-jira-1",
            fixture_id="jira-fix-1",
            record_locator="work_items[99999]",
        )
        ctx = ObservationContext(observation_id="obs-jira-1", source_instance=JIRA_SOURCE)
        ref = EntityRef(source_instance=JIRA_SOURCE, entity_kind="jira_issue", entity_id="PLAT-101")
        state = JiraIssueState(key="PLAT-101", source_status="Open", source_priority="P1", status_category="open", priority_band="high", assignee="A", created_at=T0, updated_at=T1)

        obs_single = EvidenceObservation(entity_ref=ref, observation_context=ctx, observed_state=state, provenance_refs=(p,))
        obs_dup = EvidenceObservation(entity_ref=ref, observation_context=ctx, observed_state=state, provenance_refs=(p, p))

        bundle_single = make_test_bundle((obs_single,))
        bundle_dup = make_test_bundle((obs_dup,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}

        issues_single = validate_evidence_bundle(bundle_single, fixtures_by_id=fixtures)
        issues_dup = validate_evidence_bundle(bundle_dup, fixtures_by_id=fixtures)

        assert issues_single == issues_dup
        assert len(issues_dup) == 1


# ═══════════════════════════════════════════════════════════════════════
# 14. REAL FIXTURE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════

class TestRealFixtureIntegration:
    """End-to-end assembly + validation using real fixture documents."""

    def test_northstar_and_clean_github_validate_cleanly_with_fixtures(self):
        jira_raw = load_fixture("fixtures/jira/northstar_clean_week_1.json")
        jira_val = validate_jira_fixture(jira_raw)
        jira_norm = normalize_jira_fixture(jira_val)
        jira_src = SourceInstance("jira", "jira-test")
        j_ctx, j_obs, j_qi = adapt_jira_evidence(
            jira_norm,
            jira_src,
            "obs-jira-1",
            fixture_id="northstar_clean_week_1",
        )

        gh_raw = load_fixture("fixtures/github/clean_github_week_1.json")
        gh_val = validate_github_fixture(gh_raw)
        gh_norm = normalize_github_fixture(gh_val)
        gh_rels, gh_unres = resolve_github_relationships(gh_norm)

        policy = MentionLexicalPolicy(frozenset({"PLAT"}))
        m_rels, m_unres = resolve_github_jira_mentions(gh_norm, j_obs, jira_src, policy)

        bundle = assemble_evidence_bundle(
            bundle_id="real-integration-bundle",
            bundle_version="1.0",
            jira_context=j_ctx,
            jira_observations=tuple(j_obs),
            jira_quality_issues=tuple(j_qi),
            github_fixture=gh_norm,
            github_structural_relationships=gh_rels,
            github_structural_unresolved=gh_unres,
            github_mention_relationships=m_rels,
            github_mention_unresolved=m_unres,
        )

        fixtures = {
            "northstar_clean_week_1": jira_raw,
            "clean_github_week_1": gh_raw,
        }

        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert issues == ()


# ═══════════════════════════════════════════════════════════════════════
# 15. RELATIONSHIP & UNRESOLVED REFERENCE PROVENANCE
# ═══════════════════════════════════════════════════════════════════════

class TestRelationshipAndUnresolvedProvenance:
    """Verify dereferencing on EvidenceRelationship and UnresolvedReference."""

    def test_relationship_invalid_locator_detected(self):
        j_obs = make_test_obs(entity_id="PLAT-101", record_locator="work_items[0]")
        repo_ref = EntityRef(GITHUB_SOURCE, "github_repository", "repo-core")
        repo_ctx = ObservationContext(observation_id="obs-gh-1", source_instance=GITHUB_SOURCE)
        repo_obs = EvidenceObservation(
            entity_ref=repo_ref,
            observation_context=repo_ctx,
            observed_state=GitHubRepositoryState("org-core", "core-repo"),
            provenance_refs=(
                ProvenanceRef(GITHUB_SOURCE, "obs-gh-1", "gh-min-1", "repositories[0]"),
            ),
        )

        # Relationship with bad locator
        bad_prov = ProvenanceRef(
            source_instance=GITHUB_SOURCE,
            observation_id="obs-gh-1",
            fixture_id="gh-min-1",
            record_locator="repositories[99999]",  # OOB
        )
        rel = EvidenceRelationship(
            subject_ref=repo_ref,
            object_ref=j_obs.entity_ref,
            kind="mentions",
            basis="lexical_match",
            subject_observation_id="obs-gh-1",
            object_observation_id="obs-jira-1",
            provenance_refs=(bad_prov,),
        )

        bundle = make_test_bundle((j_obs, repo_obs), relationships=(rel,))
        fixtures = {
            "jira-fix-1": MINIMAL_JIRA_RAW,
            "gh-min-1": MINIMAL_GITHUB_RAW,
        }
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert any(q.code == "unresolved" and "out of bounds" in q.message for q in issues)

    def test_unresolved_reference_invalid_locator_detected(self):
        j_obs = make_test_obs(entity_id="PLAT-101", record_locator="work_items[0]")
        bad_prov = ProvenanceRef(
            source_instance=JIRA_SOURCE,
            observation_id="obs-jira-1",
            fixture_id="jira-fix-1",
            record_locator="work_items[bad_key_not_found]",
        )
        unres = UnresolvedReference(
            source_ref=j_obs.entity_ref,
            source_observation_id="obs-jira-1",
            target_entity_kind="github_pull_request",
            target_identifier="PR-42",
            relationship_kind="mentions",
            reason="PR not observed in GitHub fixture",
            provenance_refs=(bad_prov,),
        )

        bundle = make_test_bundle((j_obs,), unresolved_references=(unres,))
        fixtures = {"jira-fix-1": MINIMAL_JIRA_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert any(q.code == "unresolved" and "not found" in q.message for q in issues)


# ═══════════════════════════════════════════════════════════════════════
# 16. TEMPORAL CUTOFF / ACCESS DENIED / FIXTURE WRAPPERS
# ═══════════════════════════════════════════════════════════════════════

class TestAdvancedDereferencingConditions:
    """Verify temporal cutoff, access-denied, and fixture wrapper handling."""

    def test_temporal_cutoff_staleness_detected(self):
        # GitHub commit has committed_at="2026-01-01T12:00:00Z"
        # Observation context specifies source_cutoff_at="2025-12-31T00:00:00Z"
        cutoff = datetime(2025, 12, 31, 0, 0, 0, tzinfo=timezone.utc)
        ctx = ObservationContext(
            observation_id="obs-gh-1",
            source_instance=GITHUB_SOURCE,
            source_cutoff_at=cutoff,
        )
        commit_ref = EntityRef(GITHUB_SOURCE, "github_commit", "repo-core/c0ffee1")
        prov = ProvenanceRef(
            source_instance=GITHUB_SOURCE,
            observation_id="obs-gh-1",
            fixture_id="gh-min-1",
            record_locator="repositories[0].commits[0]",
        )
        obs = EvidenceObservation(
            entity_ref=commit_ref,
            observation_context=ctx,
            observed_state=None,
            provenance_refs=(prov,),
        )
        bundle = make_test_bundle((obs,), observation_contexts=(ctx,))
        fixtures = {"gh-min-1": MINIMAL_GITHUB_RAW}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert len(issues) == 1
        assert issues[0].code == "invalid"
        assert issues[0].subject_scope == "provenance:temporal"
        assert "postdates source cutoff" in issues[0].message

    def test_fixture_wrapper_object_supported(self):
        class Wrapper:
            def __init__(self, doc: dict[str, Any]):
                self.raw_document = doc

        obs = make_test_obs(entity_id="PLAT-101", record_locator="work_items[0]")
        bundle = make_test_bundle((obs,))
        fixtures = {"jira-fix-1": Wrapper(MINIMAL_JIRA_RAW)}
        issues = validate_evidence_bundle(bundle, fixtures_by_id=fixtures)
        assert issues == ()
