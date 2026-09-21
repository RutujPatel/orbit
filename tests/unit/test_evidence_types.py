"""Tests for the cross-system evidence foundation (CSE-1.2).

Test categories:
    A. EntityRef identity — collision prevention, scoping
    B. Immutability — frozen records, tuple collections
    C. Observation identity — stable entity refs across observations
    D. Provenance — structured, deterministic, no Any metadata
    E. Quality — structured codes, non-entity subjects
    F. Serialization — deterministic, canonical, no clock
    G. Regression — existing Jira engine unaffected
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

import pytest

from shadow_orbit.evidence_types import (
    DerivationRef,
    EntityRef,
    EvidenceBundle,
    EvidenceObservation,
    GitHubBranchState,
    GitHubCommitState,
    GitHubPullRequestState,
    GitHubRepositoryState,
    GitHubReviewState,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    SourceFieldRef,
    SourceInstance,
    serialize_entity_ref,
    serialize_evidence_bundle,
    serialize_observation_context,
    serialize_provenance_ref,
    serialize_quality_issue,
)


# ── Helpers ──────────────────────────────────────────────────────────

_JIRA_INSTANCE = SourceInstance(
    source_kind="jira", instance_id="jira.example.com"
)
_GITHUB_INSTANCE = SourceInstance(
    source_kind="github", instance_id="github.com/TestOrg"
)

_T0 = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
_T1 = datetime(2025, 6, 8, 0, 0, 0, tzinfo=timezone.utc)
_T2 = datetime(2025, 6, 15, 0, 0, 0, tzinfo=timezone.utc)

_IST = timezone(timedelta(hours=5, minutes=30))
_T0_IST = _T0.astimezone(_IST)  # Same instant, different tz


# ═══════════════════════════════════════════════════════════════════
# A. EntityRef identity
# ═══════════════════════════════════════════════════════════════════

class TestEntityRefIdentity:
    """Verify that EntityRef prevents cross-system identity collisions."""

    def test_jira_and_github_pr_with_same_number_are_distinct(self):
        """A Jira issue '123' and a GitHub PR '123' must never equate."""
        jira_ref = EntityRef(
            source_instance=_JIRA_INSTANCE,
            entity_kind="jira_issue",
            entity_id="PLAT-123",
        )
        github_ref = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_pull_request",
            entity_id="repo-1/123",
        )
        assert jira_ref != github_ref

    def test_pr_number_requires_repository_scope(self):
        """PR 42 in repo-A and PR 42 in repo-B are distinct."""
        pr_a = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_pull_request",
            entity_id="repo-A/42",
        )
        pr_b = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_pull_request",
            entity_id="repo-B/42",
        )
        assert pr_a != pr_b

    def test_branch_name_requires_repository_scope(self):
        """Branch 'main' in repo-A and 'main' in repo-B are distinct."""
        branch_a = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_branch",
            entity_id="repo-A/main",
        )
        branch_b = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_branch",
            entity_id="repo-B/main",
        )
        assert branch_a != branch_b

    def test_review_identity_requires_pr_scope(self):
        """Review 99 on PR 42 and review 99 on PR 43 are distinct."""
        review_on_42 = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_review",
            entity_id="repo-A/42/99",
        )
        review_on_43 = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_review",
            entity_id="repo-A/43/99",
        )
        assert review_on_42 != review_on_43

    def test_same_commit_sha_in_different_repos_is_distinct(self):
        """Identical commit SHAs in different repos remain distinct."""
        sha = "abc123def456"
        commit_a = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_commit",
            entity_id=f"repo-A/{sha}",
        )
        commit_b = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_commit",
            entity_id=f"repo-B/{sha}",
        )
        assert commit_a != commit_b

    def test_source_instance_participates_in_identity(self):
        """Same entity_id and entity_kind in different instances ≠ equal."""
        ref_site_a = EntityRef(
            source_instance=SourceInstance(
                source_kind="jira", instance_id="site-a.atlassian.net"
            ),
            entity_kind="jira_issue",
            entity_id="PLAT-100",
        )
        ref_site_b = EntityRef(
            source_instance=SourceInstance(
                source_kind="jira", instance_id="site-b.atlassian.net"
            ),
            entity_kind="jira_issue",
            entity_id="PLAT-100",
        )
        assert ref_site_a != ref_site_b

    def test_identical_entity_refs_are_equal(self):
        """Two EntityRefs with same fields are equal and hash-equal."""
        ref1 = EntityRef(
            source_instance=_JIRA_INSTANCE,
            entity_kind="jira_issue",
            entity_id="PLAT-100",
        )
        ref2 = EntityRef(
            source_instance=_JIRA_INSTANCE,
            entity_kind="jira_issue",
            entity_id="PLAT-100",
        )
        assert ref1 == ref2
        assert hash(ref1) == hash(ref2)

    def test_entity_ref_usable_as_dict_key(self):
        """EntityRef can be used as a dictionary key (hashable)."""
        ref = EntityRef(
            source_instance=_JIRA_INSTANCE,
            entity_kind="jira_issue",
            entity_id="PLAT-100",
        )
        mapping = {ref: "value"}
        assert mapping[ref] == "value"


# ═══════════════════════════════════════════════════════════════════
# B. Immutability
# ═══════════════════════════════════════════════════════════════════

class TestImmutability:
    """Verify that all evidence types are frozen and immutable."""

    def test_source_instance_is_frozen(self):
        with pytest.raises(AttributeError):
            _JIRA_INSTANCE.instance_id = "other"  # type: ignore[misc]

    def test_entity_ref_is_frozen(self):
        ref = EntityRef(
            source_instance=_JIRA_INSTANCE,
            entity_kind="jira_issue",
            entity_id="PLAT-1",
        )
        with pytest.raises(AttributeError):
            ref.entity_id = "PLAT-2"  # type: ignore[misc]

    def test_observation_context_is_frozen(self):
        ctx = ObservationContext(
            observation_id="obs-1",
            source_instance=_JIRA_INSTANCE,
        )
        with pytest.raises(AttributeError):
            ctx.observation_id = "obs-2"  # type: ignore[misc]

    def test_quality_issue_is_frozen(self):
        qi = QualityIssue(code="missing", message="test")
        with pytest.raises(AttributeError):
            qi.code = "invalid"  # type: ignore[misc]

    def test_provenance_ref_is_frozen(self):
        pr = ProvenanceRef(
            source_instance=_JIRA_INSTANCE,
            observation_id="obs-1",
        )
        with pytest.raises(AttributeError):
            pr.observation_id = "obs-2"  # type: ignore[misc]

    def test_evidence_observation_is_frozen(self):
        obs = EvidenceObservation(
            entity_ref=EntityRef(
                source_instance=_JIRA_INSTANCE,
                entity_kind="jira_issue",
                entity_id="PLAT-1",
            ),
            observation_context=ObservationContext(
                observation_id="obs-1",
                source_instance=_JIRA_INSTANCE,
            ),
            observed_state=JiraIssueState(
                key="PLAT-1",
                source_status="In Progress",
                source_priority="High",
                status_category="in_progress",
                priority_band="high",
                assignee="alice",
                created_at=_T0,
                updated_at=_T1,
            ),
        )
        with pytest.raises(AttributeError):
            obs.entity_ref = None  # type: ignore[misc]

    def test_quality_issues_tuple_is_immutable(self):
        """Tuple collections inside frozen objects cannot be mutated."""
        obs = EvidenceObservation(
            entity_ref=EntityRef(
                source_instance=_JIRA_INSTANCE,
                entity_kind="jira_issue",
                entity_id="PLAT-1",
            ),
            observation_context=ObservationContext(
                observation_id="obs-1",
                source_instance=_JIRA_INSTANCE,
            ),
            observed_state=JiraIssueState(
                key="PLAT-1",
                source_status="Done",
                source_priority="High",
                status_category="done",
                priority_band="high",
                assignee=None,
                created_at=_T0,
                updated_at=_T1,
            ),
            quality_issues=(
                QualityIssue(code="missing", message="test"),
            ),
        )
        assert isinstance(obs.quality_issues, tuple)
        with pytest.raises(TypeError):
            obs.quality_issues[0] = None  # type: ignore[index]

    def test_jira_issue_state_is_frozen(self):
        state = JiraIssueState(
            key="X-1",
            source_status="Open",
            source_priority="High",
            status_category="todo",
            priority_band="high",
            assignee="bob",
            created_at=_T0,
            updated_at=_T1,
        )
        with pytest.raises(AttributeError):
            state.key = "X-2"  # type: ignore[misc]

    def test_github_pull_request_state_is_frozen(self):
        state = GitHubPullRequestState(
            number=1,
            title="Fix bug",
            state="open",
        )
        with pytest.raises(AttributeError):
            state.number = 2  # type: ignore[misc]

    def test_derivation_ref_is_frozen(self):
        dr = DerivationRef(
            transformation_id="xform-1",
            transformation_version="1",
            source_refs=(),
        )
        with pytest.raises(AttributeError):
            dr.transformation_id = "xform-2"  # type: ignore[misc]

    def test_evidence_bundle_is_frozen(self):
        bundle = EvidenceBundle(
            bundle_id="b-1",
            bundle_version="1",
            observation_contexts=(),
        )
        with pytest.raises(AttributeError):
            bundle.bundle_id = "b-2"  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════
# C. Observation identity
# ═══════════════════════════════════════════════════════════════════

class TestObservationIdentity:
    """Verify entity/observation identity semantics."""

    def test_same_entity_across_observations_keeps_same_ref(self):
        """An entity in two observations uses the same EntityRef."""
        entity_ref = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_pull_request",
            entity_id="repo-1/42",
        )
        ctx_1 = ObservationContext(
            observation_id="obs-week-1",
            source_instance=_GITHUB_INSTANCE,
            source_cutoff_at=_T1,
        )
        ctx_2 = ObservationContext(
            observation_id="obs-week-2",
            source_instance=_GITHUB_INSTANCE,
            source_cutoff_at=_T2,
        )

        obs_1 = EvidenceObservation(
            entity_ref=entity_ref,
            observation_context=ctx_1,
            observed_state=GitHubPullRequestState(
                number=42, title="WIP", state="open",
            ),
        )
        obs_2 = EvidenceObservation(
            entity_ref=entity_ref,
            observation_context=ctx_2,
            observed_state=GitHubPullRequestState(
                number=42, title="WIP", state="closed",
            ),
        )

        # Same entity identity, different observations
        assert obs_1.entity_ref == obs_2.entity_ref
        assert obs_1.observation_context != obs_2.observation_context
        assert obs_1 != obs_2

    def test_observation_contexts_with_different_ids_are_distinct(self):
        ctx_a = ObservationContext(
            observation_id="obs-A",
            source_instance=_JIRA_INSTANCE,
        )
        ctx_b = ObservationContext(
            observation_id="obs-B",
            source_instance=_JIRA_INSTANCE,
        )
        assert ctx_a != ctx_b

    def test_entity_kind_comes_only_from_entity_ref(self):
        """EvidenceObservation has no observed_kind field;
        EntityRef.entity_kind is the sole authority."""
        ref = EntityRef(
            source_instance=_JIRA_INSTANCE,
            entity_kind="jira_issue",
            entity_id="PLAT-1",
        )
        obs = EvidenceObservation(
            entity_ref=ref,
            observation_context=ObservationContext(
                observation_id="obs-1",
                source_instance=_JIRA_INSTANCE,
            ),
            observed_state=JiraIssueState(
                key="PLAT-1",
                source_status="Open",
                source_priority="High",
                status_category="todo",
                priority_band="high",
                assignee=None,
                created_at=_T0,
                updated_at=_T1,
            ),
        )
        # The entity kind is accessible only through entity_ref
        assert obs.entity_ref.entity_kind == "jira_issue"
        assert not hasattr(obs, "observed_kind")


# ═══════════════════════════════════════════════════════════════════
# D. Provenance
# ═══════════════════════════════════════════════════════════════════

class TestProvenance:
    """Verify structured provenance semantics."""

    def test_provenance_ref_serializes_deterministically(self):
        ref = ProvenanceRef(
            source_instance=_JIRA_INSTANCE,
            observation_id="obs-1",
            fixture_id="fixture-clean-week-1",
            record_locator="work_items[3]",
            source_field_path="status",
        )
        serialized = serialize_provenance_ref(ref)
        assert serialized == {
            "source_instance": {
                "source_kind": "jira",
                "instance_id": "jira.example.com",
            },
            "observation_id": "obs-1",
            "fixture_id": "fixture-clean-week-1",
            "record_locator": "work_items[3]",
            "source_field_path": "status",
        }

    def test_provenance_ref_omits_none_optional_fields(self):
        ref = ProvenanceRef(
            source_instance=_JIRA_INSTANCE,
            observation_id="obs-1",
        )
        serialized = serialize_provenance_ref(ref)
        assert "fixture_id" not in serialized
        assert "record_locator" not in serialized
        assert "source_field_path" not in serialized

    def test_field_references_are_explicit(self):
        """SourceFieldRef has explicit entity_ref and field_path."""
        ref = SourceFieldRef(
            entity_ref=EntityRef(
                source_instance=_JIRA_INSTANCE,
                entity_kind="jira_issue",
                entity_id="PLAT-1",
            ),
            field_path="status",
        )
        assert ref.entity_ref.entity_id == "PLAT-1"
        assert ref.field_path == "status"

    def test_derivation_ref_captures_transformation(self):
        source_prov = ProvenanceRef(
            source_instance=_JIRA_INSTANCE,
            observation_id="obs-1",
            fixture_id="fixture-1",
        )
        deriv = DerivationRef(
            transformation_id="jira-evidence-adapter",
            transformation_version="1",
            source_refs=(source_prov,),
        )
        assert deriv.transformation_id == "jira-evidence-adapter"
        assert len(deriv.source_refs) == 1
        assert deriv.source_refs[0].fixture_id == "fixture-1"


# ═══════════════════════════════════════════════════════════════════
# E. Quality
# ═══════════════════════════════════════════════════════════════════

class TestQuality:
    """Verify structured quality semantics."""

    def test_quality_codes_are_structured(self):
        """Each valid QualityCode can be used without error."""
        for code in (
            "missing",
            "invalid",
            "unsupported_value",
            "contradictory",
            "incomplete",
            "unresolved",
        ):
            qi = QualityIssue(code=code, message=f"test {code}")  # type: ignore[arg-type]
            assert qi.code == code

    def test_missing_is_not_invalid(self):
        qi_missing = QualityIssue(code="missing", message="field absent")
        qi_invalid = QualityIssue(code="invalid", message="field malformed")
        assert qi_missing.code != qi_invalid.code

    def test_no_absent_code_exists(self):
        """'absent' is not a valid quality code.
        missing ≠ absent by design."""
        valid_codes = {
            "missing", "invalid", "unsupported_value",
            "contradictory", "incomplete", "unresolved",
        }
        assert "absent" not in valid_codes

    def test_entity_level_quality_issue(self):
        """Quality issue referencing a specific entity."""
        ref = EntityRef(
            source_instance=_JIRA_INSTANCE,
            entity_kind="jira_issue",
            entity_id="PLAT-1",
        )
        qi = QualityIssue(
            code="incomplete",
            message="History is partial.",
            subject_ref=ref,
        )
        assert qi.subject_ref is not None
        assert qi.subject_ref.entity_id == "PLAT-1"
        assert qi.subject_scope is None

    def test_non_entity_quality_issue_via_subject_scope(self):
        """Quality issue for a collection, not a specific entity."""
        qi = QualityIssue(
            code="incomplete",
            message="PR review data is partial.",
            subject_scope="collection:pull_request_reviews",
        )
        assert qi.subject_ref is None
        assert qi.subject_scope == "collection:pull_request_reviews"

    def test_observation_level_quality_issue(self):
        """Quality issue scoped to an observation."""
        qi = QualityIssue(
            code="incomplete",
            message="Pagination stopped early.",
            subject_scope="observation:obs-week-1",
        )
        assert qi.subject_ref is None
        assert qi.subject_scope == "observation:obs-week-1"

    def test_global_quality_issue(self):
        """Quality issue with no specific subject."""
        qi = QualityIssue(
            code="unresolved",
            message="Source cutoff time not provided.",
        )
        assert qi.subject_ref is None
        assert qi.subject_scope is None

    def test_quality_issue_with_both_ref_and_scope(self):
        """Quality issue with entity ref AND scope context."""
        ref = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_pull_request",
            entity_id="repo-1/42",
        )
        qi = QualityIssue(
            code="contradictory",
            message="PR state is 'closed' but merge_commit_sha present.",
            subject_ref=ref,
            subject_scope="field:state",
        )
        assert qi.subject_ref is not None
        assert qi.subject_scope == "field:state"


# ═══════════════════════════════════════════════════════════════════
# F. Serialization
# ═══════════════════════════════════════════════════════════════════

class TestSerialization:
    """Verify deterministic, canonical serialization."""

    def test_entity_ref_serialization(self):
        ref = EntityRef(
            source_instance=_JIRA_INSTANCE,
            entity_kind="jira_issue",
            entity_id="PLAT-100",
        )
        assert serialize_entity_ref(ref) == {
            "source_instance": {
                "source_kind": "jira",
                "instance_id": "jira.example.com",
            },
            "entity_kind": "jira_issue",
            "entity_id": "PLAT-100",
        }

    def test_observation_context_with_interval_and_cutoff(self):
        """Interval and cutoff serialize as distinct fields."""
        ctx = ObservationContext(
            observation_id="obs-1",
            source_instance=_JIRA_INSTANCE,
            observed_interval_starts_at=_T0,
            observed_interval_ends_at_exclusive=_T1,
            source_cutoff_at=_T1,
            coverage_note="pagination_complete: true",
        )
        serialized = serialize_observation_context(ctx)
        assert serialized["observed_interval_starts_at"] == (
            "2025-06-01T00:00:00Z"
        )
        assert serialized["observed_interval_ends_at_exclusive"] == (
            "2025-06-08T00:00:00Z"
        )
        assert serialized["source_cutoff_at"] == (
            "2025-06-08T00:00:00Z"
        )
        assert serialized["coverage_note"] == (
            "pagination_complete: true"
        )

    def test_observation_context_minimal(self):
        """Optional fields are omitted when None."""
        ctx = ObservationContext(
            observation_id="obs-1",
            source_instance=_JIRA_INSTANCE,
        )
        serialized = serialize_observation_context(ctx)
        assert "observed_interval_starts_at" not in serialized
        assert "observed_interval_ends_at_exclusive" not in serialized
        assert "source_cutoff_at" not in serialized
        assert "coverage_note" not in serialized

    def test_timezone_equivalent_datetimes_serialize_identically(self):
        """UTC and IST representations of the same instant → same output."""
        ctx_utc = ObservationContext(
            observation_id="obs-1",
            source_instance=_JIRA_INSTANCE,
            source_cutoff_at=_T0,
        )
        ctx_ist = ObservationContext(
            observation_id="obs-1",
            source_instance=_JIRA_INSTANCE,
            source_cutoff_at=_T0_IST,
        )
        assert (
            serialize_observation_context(ctx_utc)
            == serialize_observation_context(ctx_ist)
        )

    def test_deterministic_bundle_serialization(self):
        """Same bundle serializes to identical output every time."""
        ctx = ObservationContext(
            observation_id="obs-1",
            source_instance=_JIRA_INSTANCE,
        )
        ref = EntityRef(
            source_instance=_JIRA_INSTANCE,
            entity_kind="jira_issue",
            entity_id="PLAT-1",
        )
        obs = EvidenceObservation(
            entity_ref=ref,
            observation_context=ctx,
            observed_state=JiraIssueState(
                key="PLAT-1",
                source_status="In Progress",
                source_priority="High",
                status_category="in_progress",
                priority_band="high",
                assignee="alice",
                created_at=_T0,
                updated_at=_T1,
            ),
        )
        bundle = EvidenceBundle(
            bundle_id="test-bundle",
            bundle_version="1",
            observation_contexts=(ctx,),
            observations=(obs,),
        )
        result_1 = serialize_evidence_bundle(bundle)
        result_2 = serialize_evidence_bundle(bundle)
        assert result_1 == result_2
        # Also verify JSON-safe
        json_1 = json.dumps(result_1, sort_keys=True)
        json_2 = json.dumps(result_2, sort_keys=True)
        assert json_1 == json_2

    def test_observation_order_does_not_affect_output(self):
        """Observations in different input order → same serialized output."""
        ctx = ObservationContext(
            observation_id="obs-1",
            source_instance=_GITHUB_INSTANCE,
        )
        ref_a = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_commit",
            entity_id="repo-1/aaa111",
        )
        ref_b = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_commit",
            entity_id="repo-1/bbb222",
        )
        obs_a = EvidenceObservation(
            entity_ref=ref_a,
            observation_context=ctx,
            observed_state=GitHubCommitState(
                sha="aaa111", message="first",
            ),
        )
        obs_b = EvidenceObservation(
            entity_ref=ref_b,
            observation_context=ctx,
            observed_state=GitHubCommitState(
                sha="bbb222", message="second",
            ),
        )
        bundle_ab = EvidenceBundle(
            bundle_id="b", bundle_version="1",
            observation_contexts=(ctx,),
            observations=(obs_a, obs_b),
        )
        bundle_ba = EvidenceBundle(
            bundle_id="b", bundle_version="1",
            observation_contexts=(ctx,),
            observations=(obs_b, obs_a),
        )
        assert (
            serialize_evidence_bundle(bundle_ab)
            == serialize_evidence_bundle(bundle_ba)
        )

    def test_no_now_field_in_serialized_output(self):
        """Serialized bundles must not contain generated timestamps."""
        ctx = ObservationContext(
            observation_id="obs-1",
            source_instance=_JIRA_INSTANCE,
        )
        bundle = EvidenceBundle(
            bundle_id="b-1",
            bundle_version="1",
            observation_contexts=(ctx,),
        )
        serialized = serialize_evidence_bundle(bundle)
        json_str = json.dumps(serialized)
        for forbidden in ("generated_at", "created_at_utc", "now"):
            assert forbidden not in json_str

    def test_observed_state_includes_type_discriminator(self):
        """Serialized payloads include _type for round-trip identity."""
        ctx = ObservationContext(
            observation_id="obs-1",
            source_instance=_JIRA_INSTANCE,
        )
        ref = EntityRef(
            source_instance=_JIRA_INSTANCE,
            entity_kind="jira_issue",
            entity_id="PLAT-1",
        )
        obs = EvidenceObservation(
            entity_ref=ref,
            observation_context=ctx,
            observed_state=JiraIssueState(
                key="PLAT-1",
                source_status="Done",
                source_priority="Low",
                status_category="done",
                priority_band="ordinary",
                assignee=None,
                created_at=_T0,
                updated_at=_T1,
            ),
        )
        bundle = EvidenceBundle(
            bundle_id="b",
            bundle_version="1",
            observation_contexts=(ctx,),
            observations=(obs,),
        )
        serialized = serialize_evidence_bundle(bundle)
        state = serialized["observations"][0]["observed_state"]
        assert state["_type"] == "JiraIssueState"

    def test_quality_issue_serialization_with_scope(self):
        """QualityIssue with subject_scope serializes correctly."""
        qi = QualityIssue(
            code="incomplete",
            message="Review data partial.",
            subject_scope="collection:reviews",
        )
        serialized = serialize_quality_issue(qi)
        assert serialized == {
            "code": "incomplete",
            "message": "Review data partial.",
            "subject_scope": "collection:reviews",
        }
        assert "subject_ref" not in serialized

    def test_github_pr_state_serialization(self):
        """GitHub PR payload serializes with all fields."""
        ctx = ObservationContext(
            observation_id="obs-1",
            source_instance=_GITHUB_INSTANCE,
        )
        ref = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_pull_request",
            entity_id="repo-1/42",
        )
        obs = EvidenceObservation(
            entity_ref=ref,
            observation_context=ctx,
            observed_state=GitHubPullRequestState(
                number=42,
                title="Add feature",
                state="merged",
                author_login="alice",
                created_at=_T0,
                merged_at=_T1,
                target_branch="main",
                source_branch="feature-x",
            ),
        )
        bundle = EvidenceBundle(
            bundle_id="b",
            bundle_version="1",
            observation_contexts=(ctx,),
            observations=(obs,),
        )
        serialized = serialize_evidence_bundle(bundle)
        state = serialized["observations"][0]["observed_state"]
        assert state["_type"] == "GitHubPullRequestState"
        assert state["number"] == 42
        assert state["state"] == "merged"
        assert state["created_at"] == "2025-06-01T00:00:00Z"
        assert state["merged_at"] == "2025-06-08T00:00:00Z"

    def test_observed_state_none_fields_serialize_as_none(self):
        """None values in payload serialize as None (JSON null)."""
        ctx = ObservationContext(
            observation_id="obs-1",
            source_instance=_GITHUB_INSTANCE,
        )
        ref = EntityRef(
            source_instance=_GITHUB_INSTANCE,
            entity_kind="github_commit",
            entity_id="repo-1/abc123",
        )
        obs = EvidenceObservation(
            entity_ref=ref,
            observation_context=ctx,
            observed_state=GitHubCommitState(
                sha="abc123",
                message="init",
                author_login=None,
                committed_at=None,
            ),
        )
        bundle = EvidenceBundle(
            bundle_id="b",
            bundle_version="1",
            observation_contexts=(ctx,),
            observations=(obs,),
        )
        serialized = serialize_evidence_bundle(bundle)
        state = serialized["observations"][0]["observed_state"]
        assert state["author_login"] is None
        assert state["committed_at"] is None


# ═══════════════════════════════════════════════════════════════════
# G. Regression
# ═══════════════════════════════════════════════════════════════════

class TestRegression:
    """Verify evidence_types does not interfere with the Jira engine."""

    def test_importing_evidence_types_does_not_affect_jira_types(self):
        """evidence_types is isolated; Jira types import independently."""
        from shadow_orbit.types import (
            WorkItem,
            Change,
            RuleMatch,
            SuppressedEvaluation,
            ValidatedFixture,
            NormalizedFixture,
            DataQualityCondition,
            QuarantinedRecord,
            ReviewPeriod,
        )
        # Verify the Jira types are unmodified
        assert WorkItem.__dataclass_fields__["key"].type == "str"
        assert Change.__dataclass_fields__["field"].type == "str"
        assert RuleMatch.__dataclass_fields__["rule_key"].type == "str"
        assert SuppressedEvaluation.__dataclass_fields__["reason"].type == "str"

    def test_evidence_types_has_no_dependency_on_jira_modules(self):
        """evidence_types does not import from any existing module."""
        import shadow_orbit.evidence_types as et
        import inspect

        source = inspect.getsource(et)
        for jira_module in (
            "from shadow_orbit.types",
            "from shadow_orbit.validation",
            "from shadow_orbit.normalization",
            "from shadow_orbit.temporal",
            "from shadow_orbit.evaluation",
            "from shadow_orbit.artifact",
            "from shadow_orbit.human_state",
            "from shadow_orbit.deltas",
            "from shadow_orbit.continuity",
            "from shadow_orbit.messy_acceptance",
            "from shadow_orbit.acceptance",
            "from shadow_orbit.fixture_io",
        ):
            assert jira_module not in source, (
                f"evidence_types must not import {jira_module}"
            )
