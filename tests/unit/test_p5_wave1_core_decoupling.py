"""Pass 5 / Wave 1 — Controlled Core Decoupling Unit Test Suite.

Verifies the five decoupling deliverables (G1-G5):
- G1: Provider-neutral identifiers (SourceKind, EntityKind validated strings)
- G2: Canonical WorkItemState and CodeChangeState with adapter helpers
- G3: Generic CrossSystemStateAlignment with dual-access backward compatibility
- G4: Bounded provenance collection registration with fail-closed enforcement
- G5: Evaluator execution on canonical state models simulating non-Jira/non-GitHub providers

Invariants:
- Zero live network or external API access.
- Deterministic finding IDs and evaluation IDs via SHA-256.
- 100% backward compatibility for all existing Jira/GitHub tests and fixtures.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json

import pytest

from shadow_orbit.evidence_evaluation import (
    evaluate_evidence_bundle,
    serialize_evaluation_result,
    serialize_track_b_finding,
)
from shadow_orbit.evidence_types import (
    CodeChangeState,
    CrossSystemStateAlignment,
    EntityRef,
    EvidenceBundle,
    EvidenceObservation,
    EvidenceRelationship,
    GitHubCommitState,
    GitHubPullRequestState,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    SourceInstance,
    UnresolvedReference,
    WorkItemState,
    as_code_change_state,
    as_work_item_state,
    serialize_cross_system_alignment,
    serialize_entity_ref,
    validate_entity_kind,
    validate_source_kind,
)
from shadow_orbit.provenance_dereference import (
    DereferenceResult,
    ProvenanceCollectionDescriptor,
    dereference_locator,
    get_authorized_collections,
    parse_locator,
    register_provenance_collection,
    reset_provenance_collections,
)


# ── Shared Test Timestamps ───────────────────────────────────────────

T_JAN_01 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_05 = datetime(2026, 1, 5, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_10 = datetime(2026, 1, 10, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_15 = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_20 = datetime(2026, 1, 20, 10, 0, 0, tzinfo=timezone.utc)


# =====================================================================
# G1: Provider-Neutral Identifiers
# =====================================================================


class TestG1ProviderNeutralIdentifiers:
    """Verifies G1: SourceKind and EntityKind as validated string types."""

    def test_source_kind_validation_valid(self) -> None:
        """Known and custom provider names that satisfy identifier syntax pass validation."""
        for name in ("jira", "github", "linear", "gitlab", "azure_devops", "bitbucket", "custom-123"):
            assert validate_source_kind(name) == name

    def test_source_kind_validation_invalid(self) -> None:
        """Invalid strings (empty, whitespace, excessive length, invalid chars) are rejected."""
        invalid_cases = [
            "",
            "   ",
            "jira\nleak",
            "git hub",
            "source@name",
            "a" * 65,  # > 64 chars
        ]
        for val in invalid_cases:
            with pytest.raises(ValueError):
                validate_source_kind(val)

    def test_source_kind_validation_non_string(self) -> None:
        """Non-string values are rejected with ValueError."""
        with pytest.raises(ValueError):
            validate_source_kind(123)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            validate_source_kind(None)  # type: ignore[arg-type]

    def test_entity_kind_validation_valid(self) -> None:
        """Known, canonical, and custom entity kinds pass validation."""
        valid_kinds = (
            "jira_issue",
            "github_pull_request",
            "github_commit",
            "work_item",
            "code_change",
            "linear_issue",
            "gitlab_merge_request",
            "pull_request",
        )
        for kind in valid_kinds:
            assert validate_entity_kind(kind) == kind

    def test_entity_kind_validation_invalid(self) -> None:
        """Invalid entity kinds (empty, control chars, invalid punctuation, >64 chars) are rejected."""
        invalid_kinds = [
            "",
            "   ",
            "entity/kind",
            "work item",
            "k" * 65,
        ]
        for val in invalid_kinds:
            with pytest.raises(ValueError):
                validate_entity_kind(val)

    def test_entity_kind_validation_non_string(self) -> None:
        """Non-string entity kinds are rejected with ValueError."""
        with pytest.raises(ValueError):
            validate_entity_kind(456)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            validate_entity_kind(None)  # type: ignore[arg-type]

    def test_entity_ref_with_custom_kinds(self) -> None:
        """EntityRef works seamlessly with custom and canonical provider kinds."""
        linear_source = SourceInstance(source_kind="linear", instance_id="linear-workspace-1")
        ref = EntityRef(
            source_instance=linear_source,
            entity_kind="work_item",
            entity_id="ENG-456",
        )
        assert ref.source_instance.source_kind == "linear"
        assert ref.entity_kind == "work_item"
        assert ref.entity_id == "ENG-456"

        serialized = serialize_entity_ref(ref)
        assert serialized["source_instance"]["source_kind"] == "linear"
        assert serialized["entity_kind"] == "work_item"
        assert serialized["entity_id"] == "ENG-456"

    def test_unresolved_reference_target_entity_kind_validation(self) -> None:
        """UnresolvedReference validates target_entity_kind via validate_entity_kind()."""
        source_ref = EntityRef(
            source_instance=SourceInstance(source_kind="github", instance_id="repo"),
            entity_kind="github_pull_request",
            entity_id="1",
        )
        # Valid entity kinds succeed
        for valid_kind in ("jira_issue", "work_item", "custom_issue", "sub-task"):
            unres = UnresolvedReference(
                source_ref=source_ref,
                source_observation_id="obs_1",
                target_entity_kind=valid_kind,
                target_identifier="KEY-123",
                relationship_kind="mentions",
                reason="Target not found in bundle",
                provenance_refs=(),
            )
            assert unres.target_entity_kind == valid_kind

        # Invalid cases fail closed with ValueError
        invalid_kinds = [
            "Jira_Issue",        # Uppercase rejected
            "jira issue",        # Whitespace rejected
            " jira_issue ",      # Leading/trailing whitespace rejected
            "",                  # Empty rejected
            "   ",               # Whitespace-only rejected
            "jira/issue",        # Slashes rejected
            "jira@kind",         # Special chars rejected
            "a" * 65,            # Length > 64 rejected
            123,                 # Non-string rejected
            None,                # None rejected
        ]
        for bad_kind in invalid_kinds:
            with pytest.raises(ValueError):
                UnresolvedReference(
                    source_ref=source_ref,
                    source_observation_id="obs_1",
                    target_entity_kind=bad_kind,  # type: ignore[arg-type]
                    target_identifier="KEY-123",
                    relationship_kind="mentions",
                    reason="Testing validation",
                    provenance_refs=(),
                )


# =====================================================================
# G2: Canonical WorkItemState and CodeChangeState Models
# =====================================================================


class TestG2CanonicalStateModels:
    """Verifies G2: Canonical WorkItemState / CodeChangeState and adapters."""

    def test_work_item_state_instantiation_and_defaults(self) -> None:
        """WorkItemState can be instantiated with required and optional fields."""
        item = WorkItemState(
            identifier="TASK-1",
            source_status="In Progress",
            status_category="in_progress",
            source_priority="High",
            priority_band="high",
            created_at=T_JAN_01,
        )
        assert item.identifier == "TASK-1"
        assert item.key == "TASK-1"
        assert item.source_status == "In Progress"
        assert item.status_category == "in_progress"
        assert item.assignee is None
        assert item.resolved_at is None
        assert item.due_at is None
        assert item.extra_properties == {}

    def test_code_change_state_instantiation_and_defaults(self) -> None:
        """CodeChangeState can be instantiated for pull requests and commits."""
        pr = CodeChangeState(
            change_type="pull_request",
            identifier="42",
            state="open",
            title="Update schema",
            author="alice",
            created_at=T_JAN_01,
        )
        assert pr.change_type == "pull_request"
        assert pr.identifier == "42"
        assert pr.number == 42
        assert pr.state == "open"
        assert pr.merged_at is None

        commit = CodeChangeState(
            change_type="commit",
            identifier="abc1234",
            state="committed",
            committed_at=T_JAN_10,
            title="commit message",
        )
        assert commit.change_type == "commit"
        assert commit.identifier == "abc1234"
        assert commit.committed_at == T_JAN_10

    def test_as_work_item_state_from_jira(self) -> None:
        """as_work_item_state() cleanly adapts JiraIssueState to WorkItemState."""
        jira = JiraIssueState(
            key="PLAT-99",
            source_status="Done",
            source_priority="Critical",
            status_category="done",
            priority_band="critical",
            assignee="bob",
            created_at=T_JAN_01,
            updated_at=T_JAN_10,
            resolved_at=T_JAN_10,
            due_at=T_JAN_05,
        )
        canonical = as_work_item_state(jira)
        assert canonical is not None
        assert isinstance(canonical, WorkItemState)
        assert canonical.identifier == "PLAT-99"
        assert canonical.key == "PLAT-99"
        assert canonical.source_status == "Done"
        assert canonical.status_category == "done"
        assert canonical.source_priority == "Critical"
        assert canonical.priority_band == "critical"
        assert canonical.assignee == "bob"
        assert canonical.created_at == T_JAN_01
        assert canonical.updated_at == T_JAN_10
        assert canonical.resolved_at == T_JAN_10
        assert canonical.due_at == T_JAN_05

    def test_as_work_item_state_pass_through(self) -> None:
        """as_work_item_state() passes through an existing WorkItemState directly."""
        item = WorkItemState(
            identifier="GEN-1",
            source_status="Open",
            status_category="to_do",
            created_at=T_JAN_01,
        )
        assert as_work_item_state(item) is item

    def test_as_work_item_state_unsupported(self) -> None:
        """as_work_item_state() returns None for non-work-item objects."""
        assert as_work_item_state(None) is None
        assert as_work_item_state("string") is None
        pr = GitHubPullRequestState(number=1, title="PR", state="open", created_at=T_JAN_01)
        assert as_work_item_state(pr) is None

    def test_as_code_change_state_from_github_pr(self) -> None:
        """as_code_change_state() adapts GitHubPullRequestState to CodeChangeState."""
        pr = GitHubPullRequestState(
            number=42,
            title="Implement feature",
            state="merged",
            author_login="carol",
            created_at=T_JAN_01,
            merged_at=T_JAN_10,
        )
        code_state = as_code_change_state(pr)
        assert code_state is not None
        assert isinstance(code_state, CodeChangeState)
        assert code_state.change_type == "pull_request"
        assert code_state.identifier == "42"
        assert code_state.number == 42
        assert code_state.title == "Implement feature"
        assert code_state.state == "merged"
        assert code_state.author == "carol"
        assert code_state.author_login == "carol"
        assert code_state.created_at == T_JAN_01
        assert code_state.merged_at == T_JAN_10
        assert code_state.committed_at is None

    def test_code_change_state_distinct_nullable_timestamps(self) -> None:
        """merged_at does not populate committed_at; timestamps remain distinct and nullable."""
        # 1. committed_at remains None when omitted, even if merged_at is supplied
        pr_state = CodeChangeState(
            change_type="pull_request",
            identifier="99",
            merged_at=T_JAN_10,
        )
        assert pr_state.merged_at == T_JAN_10
        assert pr_state.committed_at is None

        # 2. actual committed_at is preserved when explicitly supplied
        commit_state = CodeChangeState(
            change_type="commit",
            identifier="sha-123",
            committed_at=T_JAN_05,
        )
        assert commit_state.committed_at == T_JAN_05
        assert commit_state.merged_at is None

        # 3. both can be independently present
        both_state = CodeChangeState(
            change_type="pull_request",
            identifier="100",
            merged_at=T_JAN_10,
            committed_at=T_JAN_05,
        )
        assert both_state.merged_at == T_JAN_10
        assert both_state.committed_at == T_JAN_05

    def test_as_code_change_state_from_github_commit(self) -> None:
        """as_code_change_state() adapts GitHubCommitState to CodeChangeState."""
        commit = GitHubCommitState(
            sha="c0ffee1",
            message="Fix typo",
            author_login="dave",
            committed_at=T_JAN_15,
        )
        code_state = as_code_change_state(commit)
        assert code_state is not None
        assert isinstance(code_state, CodeChangeState)
        assert code_state.change_type == "commit"
        assert code_state.identifier == "c0ffee1"
        assert code_state.title == "Fix typo"
        assert code_state.author == "dave"
        assert code_state.committed_at == T_JAN_15
        assert code_state.merged_at is None

    def test_as_code_change_state_pass_through(self) -> None:
        """as_code_change_state() passes through an existing CodeChangeState directly."""
        cs = CodeChangeState(change_type="pull_request", identifier="10")
        assert as_code_change_state(cs) is cs

    def test_as_code_change_state_unsupported(self) -> None:
        """as_code_change_state() returns None for non-code-change objects."""
        assert as_code_change_state(None) is None
        jira = JiraIssueState(
            key="PLAT-1", source_status="Open", source_priority="Low",
            status_category="to_do", priority_band="low", assignee=None,
            created_at=T_JAN_01, updated_at=T_JAN_01, resolved_at=None, due_at=None,
        )
        assert as_code_change_state(jira) is None


# =====================================================================
# G3: Generic CrossSystemStateAlignment
# =====================================================================


class TestG3GenericAlignment:
    """Verifies G3: Generic CrossSystemStateAlignment with dual-access semantics."""

    def test_alignment_dual_property_access(self) -> None:
        """CrossSystemStateAlignment supports both generic and legacy property access."""
        src_jira = SourceInstance(source_kind="jira", instance_id="jira.orbit.internal")
        src_gh = SourceInstance(source_kind="github", instance_id="github.com/org/repo")
        j_ref = EntityRef(source_instance=src_jira, entity_kind="jira_issue", entity_id="PLAT-1")
        g_ref = EntityRef(source_instance=src_gh, entity_kind="github_pull_request", entity_id="repo/1")

        # Constructed with subject_ref / corroborating_ref
        align = CrossSystemStateAlignment(
            subject_ref=j_ref,
            corroborating_ref=g_ref,
            relationship_kind="mentions",
            state_comparison="MISMATCH",
            temporal_comparison="COINCIDENT",
            rationale="PR 1 mentions PLAT-1",
        )
        assert align.subject_ref == j_ref
        assert align.corroborating_ref == g_ref
        # Legacy aliases
        assert align.jira_ref == j_ref
        assert align.github_ref == g_ref

    def test_alignment_legacy_keyword_instantiation(self) -> None:
        """CrossSystemStateAlignment can be instantiated using legacy jira_ref/github_ref kwargs."""
        src_jira = SourceInstance(source_kind="jira", instance_id="jira.orbit.internal")
        src_gh = SourceInstance(source_kind="github", instance_id="github.com/org/repo")
        j_ref = EntityRef(source_instance=src_jira, entity_kind="jira_issue", entity_id="PLAT-2")
        g_ref = EntityRef(source_instance=src_gh, entity_kind="github_pull_request", entity_id="repo/2")

        align = CrossSystemStateAlignment(
            jira_ref=j_ref,
            github_ref=g_ref,
            relationship_kind="mentions",
            state_comparison="MISMATCH",
            temporal_comparison="COINCIDENT",
            rationale="PR 2 mentions PLAT-2",
        )
        assert align.subject_ref == j_ref
        assert align.corroborating_ref == g_ref
        assert align.jira_ref == j_ref
        assert align.github_ref == g_ref

    def test_alignment_serialization_contains_both_keypairs_for_jira_github(self) -> None:
        """Serialized alignment dictionary contains both generic and legacy keys for Jira/GitHub pairs."""
        src_jira = SourceInstance(source_kind="jira", instance_id="jira.orbit.internal")
        src_gh = SourceInstance(source_kind="github", instance_id="github.com/org/repo")
        j_ref = EntityRef(source_instance=src_jira, entity_kind="jira_issue", entity_id="PLAT-3")
        g_ref = EntityRef(source_instance=src_gh, entity_kind="github_pull_request", entity_id="repo/3")

        align = CrossSystemStateAlignment(
            subject_ref=j_ref,
            corroborating_ref=g_ref,
            relationship_kind="explicit_link",
            state_comparison="ALIGNED",
            temporal_comparison="CORROBORATING_PRECEDES_SUBJECT",
            rationale="PR 3 linked to PLAT-3",
        )
        data = serialize_cross_system_alignment(align)
        # Generic keys
        assert "subject_ref" in data
        assert "corroborating_ref" in data
        assert data["subject_ref"]["entity_id"] == "PLAT-3"
        assert data["corroborating_ref"]["entity_id"] == "repo/3"
        # Legacy keys preserved for backward compatibility
        assert "jira_ref" in data
        assert "github_ref" in data
        assert data["jira_ref"]["entity_id"] == "PLAT-3"
        assert data["github_ref"]["entity_id"] == "repo/3"

    def test_alignment_serialization_for_third_providers_is_strictly_generic(self) -> None:
        """Serialized alignment dictionary for third-party providers contains strictly canonical keys."""
        src_linear = SourceInstance(source_kind="linear", instance_id="linear-ws")
        src_gitlab = SourceInstance(source_kind="gitlab", instance_id="gitlab.com/group/proj")
        lin_ref = EntityRef(source_instance=src_linear, entity_kind="work_item", entity_id="LIN-10")
        gl_ref = EntityRef(source_instance=src_gitlab, entity_kind="code_change", entity_id="proj/10")

        align = CrossSystemStateAlignment(
            subject_ref=lin_ref,
            corroborating_ref=gl_ref,
            relationship_kind="mentions",
            state_comparison="CONSISTENT",
            temporal_comparison="COHERENT",
            rationale="MR 10 mentions LIN-10",
        )
        data = serialize_cross_system_alignment(align)
        # Canonical keys present
        assert "subject_ref" in data
        assert "corroborating_ref" in data
        assert data["subject_ref"]["entity_id"] == "LIN-10"
        assert data["corroborating_ref"]["entity_id"] == "proj/10"
        # Legacy provider keys MUST NOT be emitted
        assert "jira_ref" not in data
        assert "github_ref" not in data

    def test_alignment_serialization_deterministic_roundtrip(self) -> None:
        """Serialization of generic alignment produces identical JSON-serializable output."""
        src_a = SourceInstance(source_kind="custom_a", instance_id="a_inst")
        src_b = SourceInstance(source_kind="custom_b", instance_id="b_inst")
        ref_a = EntityRef(source_instance=src_a, entity_kind="work_item", entity_id="ITEM-1")
        ref_b = EntityRef(source_instance=src_b, entity_kind="code_change", entity_id="CHANGE-1")

        align = CrossSystemStateAlignment(
            subject_ref=ref_a,
            corroborating_ref=ref_b,
            relationship_kind="explicit_link",
            state_comparison="CONSISTENT",
            temporal_comparison="COHERENT",
            rationale="Linked item",
        )
        data1 = serialize_cross_system_alignment(align)
        data2 = serialize_cross_system_alignment(align)
        assert data1 == data2
        json_str = json.dumps(data1, sort_keys=True)
        assert "jira_ref" not in json_str
        assert "github_ref" not in json_str


# =====================================================================
# G4: Bounded Provenance Collection Registration
# =====================================================================


class TestG4ProvenanceCollectionRegistration:
    """Verifies G4: Bounded provenance collection registration with fail-closed behavior."""

    @pytest.fixture(autouse=True)
    def isolate_registry(self) -> None:
        """Ensure provenance collection registry is isolated before and after every test."""
        reset_provenance_collections()
        yield
        reset_provenance_collections()

    def setup_method(self) -> None:
        """Reset collections to built-in baseline before each test."""
        reset_provenance_collections()

    def teardown_method(self) -> None:
        """Ensure collections are cleanly reset after each test."""
        reset_provenance_collections()

    def test_test_order_independence_and_isolation(self) -> None:
        """Builtin baseline is clean; custom registrations do not leak across tests."""
        # Built-in collections are available, no custom collections present
        assert get_authorized_collections() == frozenset({
            "work_items", "repositories", "branches", "commits", "pull_requests", "reviews"
        })
        # Register a temporary collection
        register_provenance_collection(
            ProvenanceCollectionDescriptor(
                collection_name="temp_collection",
                primary_key_fields=("id",),
            )
        )
        assert "temp_collection" in get_authorized_collections()
        # Reset restores exactly builtins
        reset_provenance_collections()
        assert "temp_collection" not in get_authorized_collections()

    def test_builtin_collections_available(self) -> None:
        """Built-in collections (work_items, pull_requests, commits, etc.) are available."""
        collections = get_authorized_collections()
        assert "work_items" in collections
        assert "pull_requests" in collections
        assert "commits" in collections
        assert "repositories" in collections
        assert "branches" in collections
        assert "reviews" in collections

    def test_register_and_dereference_custom_collection(self) -> None:
        """Registering a new provenance collection enables dereferencing into it."""
        descriptor = ProvenanceCollectionDescriptor(
            collection_name="merge_requests",
            primary_key_fields=("id", "iid"),
            description="GitLab merge requests collection",
        )
        register_provenance_collection(descriptor)
        assert "merge_requests" in get_authorized_collections()

        # Parse locator for registered custom collection
        segments, parse_err = parse_locator("merge_requests[101]")
        assert parse_err is None
        assert len(segments) == 1
        assert segments[0].collection == "merge_requests"
        assert segments[0].selector == 101

        # Dereference against a simulated GitLab fixture
        fixture = {
            "merge_requests": [
                {"id": 101, "title": "Add OAuth support", "state": "merged"},
                {"id": 102, "title": "Fix memory leak", "state": "opened"},
            ]
        }
        res = dereference_locator("merge_requests[101]", fixture=fixture, source_field_path="title")
        assert res.status == "RESOLVED"
        assert res.record is not None
        assert res.record["id"] == 101
        assert res.field_value == "Add OAuth support"

    def test_unregistered_collection_fails_closed(self) -> None:
        """Locators addressing un-registered collections fail closed."""
        segments, parse_err = parse_locator("audit_logs[0]")
        assert len(segments) == 0
        assert "not an authorized locator collection" in (parse_err or "")

        res = dereference_locator("audit_logs[0]", fixture={"audit_logs": []})
        assert res.status == "UNSUPPORTED_LOCATOR"
        assert "not an authorized locator collection" in (res.error_message or "")

    def test_reset_provenance_collections(self) -> None:
        """reset_provenance_collections() removes custom collections and restores builtins."""
        register_provenance_collection(
            ProvenanceCollectionDescriptor(
                collection_name="custom_epics",
                primary_key_fields=("epic_id",),
            )
        )
        assert "custom_epics" in get_authorized_collections()

        reset_provenance_collections()
        assert "custom_epics" not in get_authorized_collections()
        segments, err = parse_locator("custom_epics[1]")
        assert len(segments) == 0
        assert "not an authorized locator collection" in (err or "")


# =====================================================================
# G5: Evaluator Execution on Canonical State Models (Non-Jira/GitHub)
# =====================================================================


class TestG5EvaluatorOnCanonicalStates:
    """Verifies G5: Evaluator execution using canonical state models on a third provider."""

    @pytest.fixture
    def linear_source(self) -> SourceInstance:
        return SourceInstance(source_kind="linear", instance_id="linear.app/team-core")

    @pytest.fixture
    def gitlab_source(self) -> SourceInstance:
        return SourceInstance(source_kind="gitlab", instance_id="gitlab.com/group/project")

    @pytest.fixture
    def linear_context(self, linear_source: SourceInstance) -> ObservationContext:
        return ObservationContext(
            observation_id="obs_linear_1",
            source_instance=linear_source,
            source_cutoff_at=T_JAN_20,
        )

    @pytest.fixture
    def gitlab_context(self, gitlab_source: SourceInstance) -> ObservationContext:
        return ObservationContext(
            observation_id="obs_gitlab_1",
            source_instance=gitlab_source,
            source_cutoff_at=T_JAN_20,
        )

    def test_evaluator_triggers_xb01_on_canonical_states(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """ORBIT-XB-01 fires correctly on canonical WorkItemState and CodeChangeState."""
        subj_ref = EntityRef(source_instance=linear_source, entity_kind="work_item", entity_id="LIN-101")
        corr_ref = EntityRef(source_instance=gitlab_source, entity_kind="code_change", entity_id="project/1")

        work_item = WorkItemState(
            identifier="LIN-101",
            source_status="Done",
            status_category="done",
            created_at=T_JAN_01,
            resolved_at=T_JAN_10,
        )
        code_change = CodeChangeState(
            change_type="pull_request",
            identifier="project/1",
            state="open",
            title="LIN-101: Add telemetry",
            created_at=T_JAN_01,
        )

        obs_subj = EvidenceObservation(
            entity_ref=subj_ref,
            observation_context=linear_context,
            observed_state=work_item,
        )
        obs_corr = EvidenceObservation(
            entity_ref=corr_ref,
            observation_context=gitlab_context,
            observed_state=code_change,
        )
        rel = EvidenceRelationship(
            subject_ref=subj_ref,
            object_ref=corr_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id="obs_linear_1",
            object_observation_id="obs_gitlab_1",
            provenance_refs=(),
        )

        bundle = EvidenceBundle(
            bundle_id="canonical_xb01_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(obs_subj, obs_corr),
            relationships=(rel,),
        )

        result = evaluate_evidence_bundle(bundle)
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.rule_id == "ORBIT-XB-01"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "SUPPORTED"
        assert finding.subject_ref == subj_ref
        assert finding.corroborating_refs == (corr_ref,)
        assert "LIN-101 is marked 'Done'" in finding.deterministic_explanation
        assert "open" in finding.deterministic_explanation
        assert finding.finding_id.startswith("finding_orbit_xb_01_")

    def test_evaluator_triggers_xb02_on_canonical_states(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """ORBIT-XB-02 fires correctly when canonical work item is in progress but code change is merged."""
        subj_ref = EntityRef(source_instance=linear_source, entity_kind="work_item", entity_id="LIN-102")
        corr_ref = EntityRef(source_instance=gitlab_source, entity_kind="code_change", entity_id="project/2")

        work_item = WorkItemState(
            identifier="LIN-102",
            source_status="In Progress",
            status_category="in_progress",
            created_at=T_JAN_01,
            resolved_at=None,
        )
        code_change = CodeChangeState(
            change_type="pull_request",
            identifier="project/2",
            state="merged",
            title="LIN-102: Feature complete",
            created_at=T_JAN_01,
            merged_at=T_JAN_05,
        )

        obs_subj = EvidenceObservation(
            entity_ref=subj_ref,
            observation_context=linear_context,
            observed_state=work_item,
        )
        obs_corr = EvidenceObservation(
            entity_ref=corr_ref,
            observation_context=gitlab_context,
            observed_state=code_change,
        )
        rel = EvidenceRelationship(
            subject_ref=subj_ref,
            object_ref=corr_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id="obs_linear_1",
            object_observation_id="obs_gitlab_1",
            provenance_refs=(),
        )

        bundle = EvidenceBundle(
            bundle_id="canonical_xb02_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(obs_subj, obs_corr),
            relationships=(rel,),
        )

        result = evaluate_evidence_bundle(bundle)
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.rule_id == "ORBIT-XB-02"
        assert finding.disposition == "TRIGGERED"
        assert "merged" in finding.deterministic_explanation
        assert "in_progress" in finding.deterministic_explanation

    def test_evaluator_triggers_xb03_on_canonical_states(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """ORBIT-XB-03 fires correctly when canonical code activity postdates work item resolution."""
        subj_ref = EntityRef(source_instance=linear_source, entity_kind="work_item", entity_id="LIN-103")
        corr_ref = EntityRef(source_instance=gitlab_source, entity_kind="code_change", entity_id="project/sha888")

        work_item = WorkItemState(
            identifier="LIN-103",
            source_status="Closed",
            status_category="done",
            created_at=T_JAN_01,
            resolved_at=T_JAN_10,
        )
        code_change = CodeChangeState(
            change_type="commit",
            identifier="project/sha888",
            state="committed",
            title="LIN-103: Late hotfix",
            committed_at=T_JAN_15,  # 5 days post-resolution
        )

        obs_subj = EvidenceObservation(
            entity_ref=subj_ref,
            observation_context=linear_context,
            observed_state=work_item,
        )
        obs_corr = EvidenceObservation(
            entity_ref=corr_ref,
            observation_context=gitlab_context,
            observed_state=code_change,
        )
        rel = EvidenceRelationship(
            subject_ref=subj_ref,
            object_ref=corr_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id="obs_linear_1",
            object_observation_id="obs_gitlab_1",
            provenance_refs=(),
        )

        bundle = EvidenceBundle(
            bundle_id="canonical_xb03_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(obs_subj, obs_corr),
            relationships=(rel,),
        )

        result = evaluate_evidence_bundle(bundle)
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.rule_id == "ORBIT-XB-03"
        assert finding.disposition == "TRIGGERED"
        assert finding.observed_facts["temporal_comparison"] == "INVERTED"
        assert finding.observed_facts["elapsed_complete_days_post_resolution"] == 5

    def test_evaluator_triggers_xb03_on_post_resolution_pr_merge(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """ORBIT-XB-03 fires correctly when a PR is merged after resolution, using merged_at when committed_at is None."""
        subj_ref = EntityRef(source_instance=linear_source, entity_kind="work_item", entity_id="LIN-104")
        corr_ref = EntityRef(source_instance=gitlab_source, entity_kind="code_change", entity_id="project/pr104")

        work_item = WorkItemState(
            identifier="LIN-104",
            source_status="Resolved",
            status_category="done",
            created_at=T_JAN_01,
            resolved_at=T_JAN_10,
        )
        code_change = CodeChangeState(
            change_type="pull_request",
            identifier="project/pr104",
            state="merged",
            title="LIN-104: Post-resolution merge",
            created_at=T_JAN_01,
            merged_at=T_JAN_15,  # 5 days post-resolution
            committed_at=None,    # Explicitly None to prove merged_at is used
        )

        obs_subj = EvidenceObservation(
            entity_ref=subj_ref,
            observation_context=linear_context,
            observed_state=work_item,
        )
        obs_corr = EvidenceObservation(
            entity_ref=corr_ref,
            observation_context=gitlab_context,
            observed_state=code_change,
        )
        rel = EvidenceRelationship(
            subject_ref=subj_ref,
            object_ref=corr_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id="obs_linear_1",
            object_observation_id="obs_gitlab_1",
            provenance_refs=(),
        )

        bundle = EvidenceBundle(
            bundle_id="canonical_xb03_pr_merge_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(obs_subj, obs_corr),
            relationships=(rel,),
        )

        result = evaluate_evidence_bundle(bundle)
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.rule_id == "ORBIT-XB-03"
        assert finding.disposition == "TRIGGERED"
        assert finding.observed_facts["temporal_comparison"] == "INVERTED"
        assert finding.observed_facts["elapsed_complete_days_post_resolution"] == 5

    def test_canonical_permutation_invariance(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """Permuting canonical observations and relationships produces bit-for-bit identical evaluation results."""
        subj1 = EntityRef(source_instance=linear_source, entity_kind="work_item", entity_id="LIN-1")
        corr1 = EntityRef(source_instance=gitlab_source, entity_kind="code_change", entity_id="p/1")
        item1 = WorkItemState(identifier="LIN-1", source_status="Done", status_category="done", created_at=T_JAN_01, resolved_at=T_JAN_10)
        code1 = CodeChangeState(change_type="pull_request", identifier="p/1", state="open", created_at=T_JAN_01)
        obs1_a = EvidenceObservation(entity_ref=subj1, observation_context=linear_context, observed_state=item1)
        obs1_b = EvidenceObservation(entity_ref=corr1, observation_context=gitlab_context, observed_state=code1)
        rel1 = EvidenceRelationship(
            subject_ref=subj1, object_ref=corr1, kind="mentions", basis="declared_mention",
            subject_observation_id="obs_linear_1", object_observation_id="obs_gitlab_1",
            provenance_refs=(),
        )

        subj2 = EntityRef(source_instance=linear_source, entity_kind="work_item", entity_id="LIN-2")
        corr2 = EntityRef(source_instance=gitlab_source, entity_kind="code_change", entity_id="p/2")
        item2 = WorkItemState(identifier="LIN-2", source_status="In Progress", status_category="in_progress", created_at=T_JAN_01)
        code2 = CodeChangeState(change_type="pull_request", identifier="p/2", state="merged", created_at=T_JAN_01, merged_at=T_JAN_05)
        obs2_a = EvidenceObservation(entity_ref=subj2, observation_context=linear_context, observed_state=item2)
        obs2_b = EvidenceObservation(entity_ref=corr2, observation_context=gitlab_context, observed_state=code2)
        rel2 = EvidenceRelationship(
            subject_ref=subj2, object_ref=corr2, kind="mentions", basis="declared_mention",
            subject_observation_id="obs_linear_1", object_observation_id="obs_gitlab_1",
            provenance_refs=(),
        )

        bundle_forward = EvidenceBundle(
            bundle_id="permutation_test_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(obs1_a, obs1_b, obs2_a, obs2_b),
            relationships=(rel1, rel2),
        )
        bundle_reverse = EvidenceBundle(
            bundle_id="permutation_test_bundle",
            bundle_version="1.0.0",
            observation_contexts=(gitlab_context, linear_context),
            observations=(obs2_b, obs1_b, obs2_a, obs1_a),
            relationships=(rel2, rel1),
        )

        res_forward = evaluate_evidence_bundle(bundle_forward)
        res_reverse = evaluate_evidence_bundle(bundle_reverse)

        json_forward = json.dumps(serialize_evaluation_result(res_forward), sort_keys=True)
        json_reverse = json.dumps(serialize_evaluation_result(res_reverse), sort_keys=True)

        assert hashlib.sha256(json_forward.encode("utf-8")).hexdigest() == hashlib.sha256(json_reverse.encode("utf-8")).hexdigest()
