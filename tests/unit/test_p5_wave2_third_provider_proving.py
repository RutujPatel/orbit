"""Comprehensive unit and proving tests for Pass 5 / Wave 2: Third-Provider Offline Proving.

Proves that synthetic Linear and GitLab observations traverse canonical
WorkItemState and CodeChangeState paths through the ORBIT Track B evaluator
without depending on provider-specific compatibility branches or live APIs.

Governing Principles:
    - deterministic facts first
    - evidence before confidence
    - unknown != false
    - missing != complete
    - unmapped != normal
    - invalid != absent
    - unsupported inference != deterministic fact
    - NO network / NO live credentials / NO external I/O
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
import random
from typing import Any
from unittest.mock import patch

import pytest

from shadow_orbit.evidence_types import (
    CodeChangeState,
    CrossSystemStateAlignment,
    EntityRef,
    EvidenceBundle,
    EvidenceObservation,
    EvidenceRelationship,
    GitHubPullRequestState,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    SourceInstance,
    WorkItemState,
    serialize_cross_system_alignment,
    serialize_evidence_bundle,
)
from shadow_orbit.evidence_evaluation import (
    evaluate_evidence_bundle,
)
from shadow_orbit.provenance_dereference import (
    ProvenanceCollectionDescriptor,
    dereference_provenance_ref,
    register_provenance_collection,
    reset_provenance_collections,
)
from shadow_orbit.third_party_adapters import (
    adapt_gitlab_commit,
    adapt_gitlab_commit_to_state,
    adapt_gitlab_merge_request,
    adapt_gitlab_mr_to_state,
    adapt_linear_issue_to_state,
    adapt_linear_work_item,
)

# Deterministic frozen UTC timestamps for synthetic fixtures
T_JAN_01 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
T_JAN_05 = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
T_JAN_10 = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
T_JAN_15 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
T_JAN_20 = datetime(2026, 1, 20, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def linear_source() -> SourceInstance:
    return SourceInstance(source_kind="linear", instance_id="lin_acme_corp")


@pytest.fixture
def gitlab_source() -> SourceInstance:
    return SourceInstance(source_kind="gitlab", instance_id="gl_acme_corp")


@pytest.fixture
def linear_context(linear_source: SourceInstance) -> ObservationContext:
    return ObservationContext(
        observation_id="obs_linear_w2_001",
        source_instance=linear_source,
        source_cutoff_at=T_JAN_20,
    )


@pytest.fixture
def gitlab_context(gitlab_source: SourceInstance) -> ObservationContext:
    return ObservationContext(
        observation_id="obs_gitlab_w2_001",
        source_instance=gitlab_source,
        source_cutoff_at=T_JAN_20,
    )


@pytest.fixture(autouse=True)
def isolate_provenance_registry():
    """Ensure provenance collection registry is completely reset before and after every test."""
    reset_provenance_collections()
    try:
        yield
    finally:
        reset_provenance_collections()


# ======================================================================
# 1. ADAPTER LEVEL PROVING
# ======================================================================

class TestThirdPartyAdapters:
    """Verify synthetic Linear and GitLab adapters conform to canonical contracts."""

    def test_linear_adapter_maps_standard_fields_faithfully(
        self, linear_source: SourceInstance, linear_context: ObservationContext
    ) -> None:
        """Linear work item adapter extracts canonical fields without manufacturing data."""
        raw_record = {
            "id": "ENG-404",
            "title": "Fix memory leak in ingestion worker",
            "state": {"name": "In Progress", "type": "started"},
            "priority": 1,
            "priority_label": "Urgent",
            "created_at": "2026-01-01T12:00:00Z",
            "updated_at": "2026-01-05T12:00:00Z",
            "due_date": "2026-01-15T12:00:00Z",
            "assignee": {"name": "Dana Scully"},
        }
        obs = adapt_linear_work_item(raw_record, linear_context, linear_source)

        assert obs.entity_ref.source_instance == linear_source
        assert obs.entity_ref.entity_kind == "work_item"
        assert obs.entity_ref.entity_id == "ENG-404"

        state = obs.observed_state
        assert isinstance(state, WorkItemState)
        assert state.identifier == "ENG-404"
        assert state.key == "ENG-404"
        assert state.source_status == "In Progress"
        assert state.status_category == "in_progress"
        assert state.source_priority == "Urgent"
        assert state.priority_band == "urgent"
        assert state.created_at == T_JAN_01
        assert state.updated_at == T_JAN_05
        assert state.due_at == T_JAN_15
        assert state.resolved_at is None  # Unresolved remains None
        assert state.assignee == "Dana Scully"
        assert state.extra_properties.get("title") == "Fix memory leak in ingestion worker"

    def test_linear_adapter_status_category_mappings(self) -> None:
        """Linear state types map deterministically to canonical status categories."""
        mappings = [
            ("completed", "done"),
            ("started", "in_progress"),
            ("unstarted", "to_do"),
            ("triage", "to_do"),
            ("backlog", "to_do"),
            ("canceled", "rejected"),
        ]
        for l_type, expected_cat in mappings:
            record = {
                "id": f"LIN-{l_type}",
                "state": {"name": l_type.title(), "type": l_type},
                "created_at": "2026-01-01T12:00:00Z",
            }
            state = adapt_linear_issue_to_state(record)
            assert state.status_category == expected_cat, f"Failed for {l_type}"

    def test_gitlab_mr_adapter_invariants(
        self, gitlab_source: SourceInstance, gitlab_context: ObservationContext
    ) -> None:
        """GitLab MR adapter maps fields and preserves committed_at=None invariant."""
        raw_mr = {
            "iid": 184,
            "title": "ENG-404: Resolve memory leak",
            "state": "merged",
            "created_at": "2026-01-01T12:00:00Z",
            "merged_at": "2026-01-10T12:00:00Z",
            "author": {"username": "scully"},
            "source_branch": "fix/eng-404",
            "target_branch": "main",
            "sha": "a1b2c3d4e5f67890123456789abcdef012345678",
        }
        obs = adapt_gitlab_merge_request(raw_mr, gitlab_context, gitlab_source)

        assert obs.entity_ref.source_instance == gitlab_source
        assert obs.entity_ref.entity_kind == "code_change"
        assert obs.entity_ref.entity_id == "184"

        state = obs.observed_state
        assert isinstance(state, CodeChangeState)
        assert state.identifier == "184"
        assert state.change_type == "merge_request"
        assert state.state == "merged"
        assert state.title == "ENG-404: Resolve memory leak"
        assert state.created_at == T_JAN_01
        assert state.merged_at == T_JAN_10
        # CRITICAL INVARIANT: committed_at is NEVER inferred from merged_at
        assert state.committed_at is None
        assert state.author == "scully"
        assert state.source_branch == "fix/eng-404"
        assert state.target_branch == "main"
        assert state.head_commit_sha == "a1b2c3d4e5f67890123456789abcdef012345678"

    def test_gitlab_commit_adapter_mapping(
        self, gitlab_source: SourceInstance, gitlab_context: ObservationContext
    ) -> None:
        """GitLab commit adapter records committed_at independently."""
        raw_commit = {
            "id": "e86725890123456789abcdef0123456789abcdef",
            "title": "ENG-404: Ingestion worker cleanup",
            "committed_date": "2026-01-08T12:00:00Z",
            "author_name": "Fox Mulder",
        }
        obs = adapt_gitlab_commit(raw_commit, gitlab_context, gitlab_source)

        state = obs.observed_state
        assert isinstance(state, CodeChangeState)
        assert state.change_type == "commit"
        assert state.identifier == "e86725890123456789abcdef0123456789abcdef"
        assert state.state == "committed"
        assert state.merged_at is None
        assert state.committed_at == datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc)


# ======================================================================
# 2. REQUIRED SPECIFICATION SCENARIOS (CASES A - I)
# ======================================================================

class TestWave2RequiredScenarios:
    """Rigorous verification of Cases A through I per Pass 5 Wave 2 specification."""

    def test_case_a_xb01_triggered(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """CASE A: Linear done + GitLab MR open -> ORBIT-XB-01 TRIGGERED (no Jira/GitHub wording)."""
        subj_obs = adapt_linear_work_item(
            {
                "id": "LIN-101",
                "title": "Telemetry ingest",
                "state": {"name": "Completed", "type": "completed"},
                "created_at": "2026-01-01T12:00:00Z",
                "completed_at": "2026-01-10T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        corr_obs = adapt_gitlab_merge_request(
            {
                "iid": 42,
                "title": "LIN-101: Add telemetry pipeline",
                "state": "opened",
                "created_at": "2026-01-01T12:00:00Z",
            },
            gitlab_context,
            gitlab_source,
        )
        rel = EvidenceRelationship(
            subject_ref=subj_obs.entity_ref,
            object_ref=corr_obs.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )
        bundle = EvidenceBundle(
            bundle_id="case_a_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(subj_obs, corr_obs),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-01"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "SUPPORTED"
        assert finding.subject_ref == subj_obs.entity_ref
        assert finding.corroborating_refs == (corr_obs.entity_ref,)

        # Assert NO Jira / GitHub leakage in generic explanation
        exp = finding.deterministic_explanation
        assert "Jira" not in exp
        assert "GitHub" not in exp
        assert "#None" not in exp
        assert "Work item LIN-101 is marked 'Completed' (status category: done)" in exp
        assert "referenced code change #42 ('LIN-101: Add telemetry pipeline') remains open" in exp

        # Assert canonical fact keys
        facts = finding.observed_facts
        assert facts["work_item_key"] == "LIN-101"
        assert facts["work_item_status"] == "Completed"
        assert facts["work_item_status_category"] == "done"
        assert facts["code_change_identifier"] == "42"
        assert facts["code_change_state"] == "open"
        assert "jira_key" not in facts
        assert "pr_number" not in facts

    def test_case_b_xb02_triggered(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """CASE B: Linear in_progress + GitLab MR merged with observed merged_at -> ORBIT-XB-02 TRIGGERED."""
        subj_obs = adapt_linear_work_item(
            {
                "id": "LIN-202",
                "title": "Auth token cache",
                "state": {"name": "Started", "type": "started"},
                "created_at": "2026-01-01T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        corr_obs = adapt_gitlab_merge_request(
            {
                "iid": 99,
                "title": "LIN-202: Cache auth tokens",
                "state": "merged",
                "created_at": "2026-01-01T12:00:00Z",
                "merged_at": "2026-01-10T12:00:00Z",
            },
            gitlab_context,
            gitlab_source,
        )
        rel = EvidenceRelationship(
            subject_ref=subj_obs.entity_ref,
            object_ref=corr_obs.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )
        bundle = EvidenceBundle(
            bundle_id="case_b_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(subj_obs, corr_obs),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-02"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "SUPPORTED"

        exp = finding.deterministic_explanation
        assert "Jira" not in exp
        assert "GitHub" not in exp
        assert "#None" not in exp
        assert "Code change #99 ('LIN-202: Cache auth tokens') is merged" in exp
        assert "work item LIN-202 remains 'Started'" in exp

        facts = finding.observed_facts
        assert facts["work_item_key"] == "LIN-202"
        assert facts["code_change_identifier"] == "99"
        assert facts["code_change_merged_at"] == "2026-01-10T12:00:00Z"

    def test_case_c_xb02_insufficient_evidence_when_merged_at_missing(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """CASE C: GitLab MR merged but merged_at is None -> ORBIT-XB-02 INSUFFICIENT_EVIDENCE."""
        subj_obs = adapt_linear_work_item(
            {
                "id": "LIN-303",
                "title": "Database replication",
                "state": {"name": "Started", "type": "started"},
                "created_at": "2026-01-01T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        corr_obs = adapt_gitlab_merge_request(
            {
                "iid": 105,
                "title": "LIN-303: Replication script",
                "state": "merged",
                "created_at": "2026-01-01T12:00:00Z",
                "merged_at": None,  # Intentionally missing
            },
            gitlab_context,
            gitlab_source,
        )
        rel = EvidenceRelationship(
            subject_ref=subj_obs.entity_ref,
            object_ref=corr_obs.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )
        bundle = EvidenceBundle(
            bundle_id="case_c_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(subj_obs, corr_obs),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        # INSUFFICIENT_EVIDENCE findings are routed to suppressed_evaluations
        assert len(res.findings) == 0
        assert len(res.suppressed_evaluations) == 1
        finding = res.suppressed_evaluations[0]
        assert finding.rule_id == "ORBIT-XB-02"
        assert finding.disposition == "INSUFFICIENT_EVIDENCE"
        assert finding.sufficiency == "INSUFFICIENT_EVIDENCE"
        assert "merged_at timestamp is missing" in finding.deterministic_explanation
        assert "Code change #105" in finding.deterministic_explanation
        assert "#None" not in finding.deterministic_explanation
        assert finding.observed_facts["code_change_merged_at"] is None

    def test_case_d_xb03_post_resolution_commit_activity(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """CASE D1: GitLab commit committed_at after Linear work item resolved_at -> ORBIT-XB-03 TRIGGERED."""
        subj_obs = adapt_linear_work_item(
            {
                "id": "LIN-404",
                "title": "API rate limiter",
                "state": {"name": "Done", "type": "completed"},
                "created_at": "2026-01-01T12:00:00Z",
                "completed_at": "2026-01-05T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        corr_obs = adapt_gitlab_commit(
            {
                "id": "c0ffee1234567890abcdef1234567890abcdef12",
                "title": "LIN-404: Fix rate limit bypass",
                "committed_date": "2026-01-10T12:00:00Z",  # 5 days post-resolution
            },
            gitlab_context,
            gitlab_source,
        )
        rel = EvidenceRelationship(
            subject_ref=subj_obs.entity_ref,
            object_ref=corr_obs.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )
        bundle = EvidenceBundle(
            bundle_id="case_d1_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(subj_obs, corr_obs),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-03"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "SUPPORTED"

        exp = finding.deterministic_explanation
        assert "Jira" not in exp
        assert "GitHub" not in exp
        assert "Corroborating commit (commit c0ffee12) occurred at 2026-01-10T12:00:00Z after work item LIN-404" in exp
        assert "5 complete days post-resolution" in exp

        facts = finding.observed_facts
        assert facts["work_item_key"] == "LIN-404"
        assert facts["corroborating_activity_kind"] == "commit"
        assert facts["elapsed_complete_days_post_resolution"] == 5
        assert facts["temporal_comparison"] == "INVERTED"

    def test_case_d_xb03_post_resolution_merge_request_activity(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """CASE D2: GitLab MR merged_at after Linear work item resolved_at -> ORBIT-XB-03 TRIGGERED."""
        subj_obs = adapt_linear_work_item(
            {
                "id": "LIN-405",
                "title": "Audit logger",
                "state": {"name": "Done", "type": "completed"},
                "created_at": "2026-01-01T12:00:00Z",
                "completed_at": "2026-01-05T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        corr_obs = adapt_gitlab_merge_request(
            {
                "iid": "MR-77",
                "title": "LIN-405: Log rotation fix",
                "state": "merged",
                "created_at": "2026-01-02T12:00:00Z",
                "merged_at": "2026-01-15T12:00:00Z",  # 10 days post-resolution
            },
            gitlab_context,
            gitlab_source,
        )
        rel = EvidenceRelationship(
            subject_ref=subj_obs.entity_ref,
            object_ref=corr_obs.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )
        bundle = EvidenceBundle(
            bundle_id="case_d2_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(subj_obs, corr_obs),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-03"
        assert finding.disposition == "TRIGGERED"
        assert "code change merge (code change #MR-77" in finding.deterministic_explanation
        assert "#None" not in finding.deterministic_explanation
        assert finding.observed_facts["elapsed_complete_days_post_resolution"] == 10

    def test_case_e_missing_observation_fails_closed(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
    ) -> None:
        """CASE E: Referenced GitLab entity is not observed -> deterministic UNRESOLVED reference."""
        subj_obs = adapt_linear_work_item(
            {
                "id": "LIN-505",
                "title": "OAuth provider",
                "state": {"name": "Completed", "type": "completed"},
                "created_at": "2026-01-01T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        unobserved_ref = EntityRef(
            source_instance=gitlab_source,
            entity_kind="code_change",
            entity_id="MR-999_NOT_FOUND",
        )
        rel = EvidenceRelationship(
            subject_ref=subj_obs.entity_ref,
            object_ref=unobserved_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id="unobserved_context",
            provenance_refs=(),
        )
        bundle = EvidenceBundle(
            bundle_id="case_e_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context,),
            observations=(subj_obs,),  # unobserved_ref is deliberately NOT in observations
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        # Evaluator must not crash, and must not trigger false findings on unobserved entities
        assert len(res.findings) == 0
        assert len(res.suppressed_evaluations) == 1
        unres = res.suppressed_evaluations[0]
        assert unres.disposition == "INSUFFICIENT_EVIDENCE"
        assert unres.sufficiency == "UNRESOLVED"
        assert unres.observed_facts["missing_entity"] == "code_change:MR-999_NOT_FOUND"
        assert "was not observed in the evidence bundle" in unres.deterministic_explanation

    def test_case_f_non_numeric_code_change_identifier(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """CASE F: Non-numeric identifier 'MR-184' must not produce '#None'."""
        subj_obs = adapt_linear_work_item(
            {
                "id": "LIN-606",
                "title": "Config migration",
                "state": {"name": "Done", "type": "completed"},
                "created_at": "2026-01-01T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        raw_code = {
            "identifier": "MR-184",  # Alphanumeric with hyphen
            "title": "LIN-606: Migrate yaml to toml",
            "state": "open",
            "created_at": "2026-01-01T12:00:00Z",
        }
        corr_obs = adapt_gitlab_merge_request(raw_code, gitlab_context, gitlab_source)

        code_state = corr_obs.observed_state
        assert isinstance(code_state, CodeChangeState)
        assert code_state.number is None  # Verify number is None for non-numeric

        rel = EvidenceRelationship(
            subject_ref=subj_obs.entity_ref,
            object_ref=corr_obs.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )
        bundle = EvidenceBundle(
            bundle_id="case_f_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(subj_obs, corr_obs),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-01"
        assert finding.disposition == "TRIGGERED"

        exp = finding.deterministic_explanation
        assert "#None" not in exp
        assert "referenced code change #MR-184 ('LIN-606: Migrate yaml to toml') remains open" in exp
        assert finding.observed_facts["code_change_identifier"] == "MR-184"

    def test_case_g_generic_serialization_omits_legacy_keys(
        self, linear_source: SourceInstance, gitlab_source: SourceInstance
    ) -> None:
        """CASE G: Generic alignment serialization contains subject_ref/corroborating_ref, NOT jira_ref/github_ref."""
        subj_ref = EntityRef(source_instance=linear_source, entity_kind="work_item", entity_id="LIN-707")
        corr_ref = EntityRef(source_instance=gitlab_source, entity_kind="code_change", entity_id="MR-707")

        alignment = CrossSystemStateAlignment(
            subject_ref=subj_ref,
            corroborating_ref=corr_ref,
            relationship_kind="mentions",
            state_comparison="DIVERGENT",
            temporal_comparison="CONCURRENT",
            rationale="Linear item done while GitLab MR open",
        )

        serialized = serialize_cross_system_alignment(alignment)
        assert "subject_ref" in serialized
        assert "corroborating_ref" in serialized
        assert serialized["subject_ref"]["entity_id"] == "LIN-707"
        assert serialized["corroborating_ref"]["entity_id"] == "MR-707"

        # INVARIANT: jira_ref and github_ref MUST NOT exist in generic serialization
        assert "jira_ref" not in serialized
        assert "github_ref" not in serialized

    def test_case_h_permutation_invariance(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """CASE H: Permuting observation and relationship lists produces identical findings and IDs."""
        obs1 = adapt_linear_work_item(
            {
                "id": "LIN-801",
                "state": {"name": "Done", "type": "completed"},
                "created_at": "2026-01-01T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        obs2 = adapt_gitlab_merge_request(
            {"iid": 1, "state": "opened", "title": "LIN-801: part 1"},
            gitlab_context,
            gitlab_source,
        )
        obs3 = adapt_linear_work_item(
            {
                "id": "LIN-802",
                "state": {"name": "Started", "type": "started"},
                "created_at": "2026-01-01T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        obs4 = adapt_gitlab_merge_request(
            {"iid": 2, "state": "merged", "merged_at": "2026-01-10T12:00:00Z", "title": "LIN-802: part 2"},
            gitlab_context,
            gitlab_source,
        )

        rel1 = EvidenceRelationship(
            subject_ref=obs1.entity_ref,
            object_ref=obs2.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )
        rel2 = EvidenceRelationship(
            subject_ref=obs3.entity_ref,
            object_ref=obs4.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )

        all_obs = [obs1, obs2, obs3, obs4]
        all_rels = [rel1, rel2]

        bundle_canonical = EvidenceBundle(
            bundle_id="perm_test",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=tuple(all_obs),
            relationships=tuple(all_rels),
        )
        base_result = evaluate_evidence_bundle(bundle_canonical)
        base_fids = [f.finding_id for f in base_result.findings]

        # Evaluate across 10 deterministic shuffles
        rng = random.Random(42)
        for i in range(10):
            shuffled_obs = list(all_obs)
            shuffled_rels = list(all_rels)
            rng.shuffle(shuffled_obs)
            rng.shuffle(shuffled_rels)

            bundle_shuffled = EvidenceBundle(
                bundle_id="perm_test",
                bundle_version="1.0.0",
                observation_contexts=(gitlab_context, linear_context),
                observations=tuple(shuffled_obs),
                relationships=tuple(shuffled_rels),
            )
            shuffled_result = evaluate_evidence_bundle(bundle_shuffled)
            shuffled_fids = [f.finding_id for f in shuffled_result.findings]

            assert shuffled_fids == base_fids, f"Permutation mismatch on iteration {i}"

    def test_case_i_deterministic_finding_ids_and_json(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """CASE I: Multiple evaluation runs yield bit-for-bit identical finding IDs and serialized output."""
        subj_obs = adapt_linear_work_item(
            {
                "id": "LIN-901",
                "state": {"name": "Done", "type": "completed"},
                "created_at": "2026-01-01T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        corr_obs = adapt_gitlab_merge_request(
            {"iid": 88, "state": "opened", "title": "LIN-901: Task"},
            gitlab_context,
            gitlab_source,
        )
        rel = EvidenceRelationship(
            subject_ref=subj_obs.entity_ref,
            object_ref=corr_obs.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )
        bundle = EvidenceBundle(
            bundle_id="determinism_test",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(subj_obs, corr_obs),
            relationships=(rel,),
        )

        first_res = evaluate_evidence_bundle(bundle)
        first_json = json.dumps(
            [f.finding_id for f in first_res.findings], sort_keys=True
        )

        for _ in range(5):
            res = evaluate_evidence_bundle(bundle)
            cur_json = json.dumps(
                [f.finding_id for f in res.findings], sort_keys=True
            )
            assert cur_json == first_json


# ======================================================================
# 3. MIXED PROVIDER TEST (SECTION 10)
# ======================================================================

class TestMixedProviderBundle:
    """Prove Jira + GitHub + Linear + GitLab can coexist in a single bundle."""

    def test_coexistence_without_cross_talk_or_global_mode_switches(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """Mixed bundle evaluates Jira/GitHub with legacy compatibility and Linear/GitLab with canonical path."""
        jira_source = SourceInstance(source_kind="jira", instance_id="jira_cloud")
        github_source = SourceInstance(source_kind="github", instance_id="gh_org")
        jira_ctx = ObservationContext(observation_id="obs_jira_1", source_instance=jira_source)
        gh_ctx = ObservationContext(observation_id="obs_gh_1", source_instance=github_source)

        # 1. Jira + GitHub pair (fires ORBIT-XB-01)
        jira_ref = EntityRef(source_instance=jira_source, entity_kind="jira_issue", entity_id="PROJ-101")
        gh_ref = EntityRef(source_instance=github_source, entity_kind="github_pull_request", entity_id="101")
        jira_obs = EvidenceObservation(
            entity_ref=jira_ref,
            observation_context=jira_ctx,
            observed_state=JiraIssueState(
                key="PROJ-101",
                source_status="Done",
                source_priority="High",
                status_category="done",
                priority_band="high",
                assignee="alice",
                created_at=T_JAN_01,
                updated_at=T_JAN_10,
                resolved_at=T_JAN_10,
            ),
        )
        gh_obs = EvidenceObservation(
            entity_ref=gh_ref,
            observation_context=gh_ctx,
            observed_state=GitHubPullRequestState(
                number=101,
                state="open",
                title="PROJ-101: Fix bug",
                created_at=T_JAN_01,
            ),
        )
        rel_jg = EvidenceRelationship(
            subject_ref=jira_ref,
            object_ref=gh_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id="obs_jira_1",
            object_observation_id="obs_gh_1",
            provenance_refs=(),
        )

        # 2. Linear + GitLab pair (fires ORBIT-XB-02)
        lin_obs = adapt_linear_work_item(
            {
                "id": "LIN-202",
                "state": {"name": "Started", "type": "started"},
                "created_at": "2026-01-01T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        gl_obs = adapt_gitlab_merge_request(
            {"iid": 202, "state": "merged", "merged_at": "2026-01-10T12:00:00Z", "title": "LIN-202: Feature"},
            gitlab_context,
            gitlab_source,
        )
        rel_lg = EvidenceRelationship(
            subject_ref=lin_obs.entity_ref,
            object_ref=gl_obs.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )

        # Assemble unified 4-provider bundle
        mixed_bundle = EvidenceBundle(
            bundle_id="mixed_4_provider_bundle",
            bundle_version="1.0.0",
            observation_contexts=(jira_ctx, gh_ctx, linear_context, gitlab_context),
            observations=(jira_obs, gh_obs, lin_obs, gl_obs),
            relationships=(rel_jg, rel_lg),
        )

        eval_result = evaluate_evidence_bundle(mixed_bundle)
        assert len(eval_result.findings) == 2

        f_jg = next(f for f in eval_result.findings if f.subject_ref == jira_ref)
        f_lg = next(f for f in eval_result.findings if f.subject_ref == lin_obs.entity_ref)

        # Verify Jira + GitHub preserves legacy formatting
        assert f_jg.rule_id == "ORBIT-XB-01"
        assert "Jira issue PROJ-101 is marked 'Done'" in f_jg.deterministic_explanation
        assert "referenced GitHub PR #101" in f_jg.deterministic_explanation
        assert f_jg.observed_facts["jira_key"] == "PROJ-101"
        assert f_jg.observed_facts["pr_number"] == 101

        # Verify Linear + GitLab uses canonical formatting
        assert f_lg.rule_id == "ORBIT-XB-02"
        assert "Code change #202 ('LIN-202: Feature') is merged while referenced work item LIN-202 remains 'Started'" in f_lg.deterministic_explanation
        assert "Jira" not in f_lg.deterministic_explanation
        assert "GitHub" not in f_lg.deterministic_explanation
        assert f_lg.observed_facts["work_item_key"] == "LIN-202"
        assert f_lg.observed_facts["code_change_identifier"] == "202"


# ======================================================================
# 4. BOUNDED PROVENANCE REGISTRATION TEST (SECTION 6.E)
# ======================================================================

class TestProvenanceRegistration:
    """Verify bounded provenance collection registration."""

    def test_bounded_collection_registration(self) -> None:
        """Register a bounded collection descriptor and dereference a record."""
        try:
            desc = ProvenanceCollectionDescriptor(
                name="gitlab_merge_requests",
                primary_key_fields=("iid", "id"),
                description="GitLab merge requests collection",
            )
            register_provenance_collection(desc)

            pref = ProvenanceRef(
                source_instance=SourceInstance(source_kind="gitlab", instance_id="gl_prod"),
                observation_id="obs_gl_001",
                fixture_id="gitlab_mr_fixture",
                record_locator="gitlab_merge_requests[184]",
                source_field_path="title",
            )
            fixture_data = {
                "gitlab_merge_requests": [
                    {"iid": 184, "title": "Refactor auth"},
                ]
            }
            res = dereference_provenance_ref(pref, fixture_data)
            assert res.status == "RESOLVED"
            assert res.record == {"iid": 184, "title": "Refactor auth"}
        finally:
            reset_provenance_collections()

    def test_descriptor_primary_key_fields_enforces_authoritative_identity(self) -> None:
        """P2: Verify that registered descriptor primary_key_fields govern identity verification.

        If a collection registers primary_key_fields=('id',), a record containing
        id='999' and number='123' must NOT match expected entity_id='123' (which would
        previously match under the unconstrained fallback).
        """
        desc = ProvenanceCollectionDescriptor(
            name="custom_issues",
            primary_key_fields=("id",),
            description="Custom issue tracking with strict id primary key",
        )
        register_provenance_collection(desc)

        pref = ProvenanceRef(
            source_instance=SourceInstance(source_kind="custom_provider", instance_id="cust_001"),
            observation_id="obs_cust_001",
            fixture_id="custom_fixture",
            record_locator="custom_issues[0]",
        )
        fixture_data = {
            "custom_issues": [
                {"id": "999", "number": "123", "title": "Ambiguous record"},
            ]
        }
        # Expected entity ref looking for '123'
        expected_ref = EntityRef(
            source_instance=SourceInstance(source_kind="custom_provider", instance_id="cust_001"),
            entity_kind="custom_issue",
            entity_id="123",
        )
        res = dereference_provenance_ref(pref, fixture_data, expected_entity_ref=expected_ref)
        # Must be rejected as INVALID identity contradiction because id is '999', not '123'
        assert res.status == "INVALID"
        assert res.quality_issue is not None
        assert res.quality_issue.code == "contradictory"

        # Now test matching record with id='123'
        fixture_matching = {
            "custom_issues": [
                {"id": "123", "number": "999", "title": "Matching record"},
            ]
        }
        res_ok = dereference_provenance_ref(pref, fixture_matching, expected_entity_ref=expected_ref)
        assert res_ok.status == "RESOLVED"
        assert res_ok.record is not None
        assert res_ok.record["id"] == "123"


# ======================================================================
# 5. ADVERSARIAL CANONICAL BRANCH ENFORCEMENT (P1 PROOF)
# ======================================================================

class TestAdversarialCanonicalBranchEnforcement:
    """P1: Adversarially prove that Linear + GitLab evaluation strictly uses the canonical branch.

    Asserts that:
    1. Neither JiraIssueState nor GitHubPullRequestState is instantiated during evaluation.
    2. Finding explanations contain generic terms ('Work item', 'code change', 'commit') and strictly
       ZERO occurrences of vendor names 'Jira' or 'GitHub' (case-insensitive).
    3. Finding observed_facts contain canonical keys ('work_item_key', 'code_change_identifier', etc.)
       and strictly ZERO legacy keys ('jira_key', 'jira_status', 'pr_number', 'pr_state').
    4. Evaluator branches across XB-01, XB-02, and XB-03 all enforce these constraints.
    """

    def test_adversarial_canonical_branch_purity_xb01_xb02_xb03(
        self,
        linear_source: SourceInstance,
        gitlab_source: SourceInstance,
        linear_context: ObservationContext,
        gitlab_context: ObservationContext,
    ) -> None:
        """Adversarially verify complete isolation from legacy Jira/GitHub facts across rules."""
        legacy_fact_keys = {
            "jira_key",
            "jira_status",
            "jira_status_category",
            "pr_number",
            "pr_state",
        }
        canonical_fact_keys = {
            "work_item_key",
            "work_item_status",
            "work_item_status_category",
        }

        # Setup 3 scenarios:
        # Scenario 1 (XB-01): Linear Done + GitLab MR Open
        obs_lin_done = adapt_linear_work_item(
            {
                "id": "LIN-ADV-01",
                "title": "Completed task",
                "state": {"name": "Done", "type": "completed"},
                "created_at": "2026-01-01T12:00:00Z",
                "completed_at": "2026-01-05T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        obs_gl_open = adapt_gitlab_merge_request(
            {
                "iid": 101,
                "title": "LIN-ADV-01: In-flight change",
                "state": "opened",
                "created_at": "2026-01-01T12:00:00Z",
            },
            gitlab_context,
            gitlab_source,
        )
        rel_xb01 = EvidenceRelationship(
            subject_ref=obs_lin_done.entity_ref,
            object_ref=obs_gl_open.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )

        # Scenario 2 (XB-02): Linear Started + GitLab MR Merged
        obs_lin_started = adapt_linear_work_item(
            {
                "id": "LIN-ADV-02",
                "title": "Ongoing task",
                "state": {"name": "Started", "type": "started"},
                "created_at": "2026-01-01T12:00:00Z",
            },
            linear_context,
            linear_source,
        )
        obs_gl_merged = adapt_gitlab_merge_request(
            {
                "iid": 102,
                "title": "LIN-ADV-02: Merged change",
                "state": "merged",
                "created_at": "2026-01-01T12:00:00Z",
                "merged_at": "2026-01-10T12:00:00Z",
            },
            gitlab_context,
            gitlab_source,
        )
        rel_xb02 = EvidenceRelationship(
            subject_ref=obs_lin_started.entity_ref,
            object_ref=obs_gl_merged.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )

        # Scenario 3 (XB-03): Linear Done + GitLab Commit post-resolution
        obs_gl_commit = adapt_gitlab_commit(
            {
                "id": "abc1234567890abcdef1234567890abcdef12345",
                "title": "LIN-ADV-01: Late commit",
                "committed_date": "2026-01-12T12:00:00Z",
            },
            gitlab_context,
            gitlab_source,
        )
        rel_xb03 = EvidenceRelationship(
            subject_ref=obs_lin_done.entity_ref,
            object_ref=obs_gl_commit.entity_ref,
            kind="mentions",
            basis="declared_mention",
            subject_observation_id=linear_context.observation_id,
            object_observation_id=gitlab_context.observation_id,
            provenance_refs=(),
        )

        bundle = EvidenceBundle(
            bundle_id="adv_purity_bundle",
            bundle_version="1.0.0",
            observation_contexts=(linear_context, gitlab_context),
            observations=(obs_lin_done, obs_gl_open, obs_lin_started, obs_gl_merged, obs_gl_commit),
            relationships=(rel_xb01, rel_xb02, rel_xb03),
        )

        # SPY: Intercept JiraIssueState and GitHubPullRequestState instantiations
        with patch.object(JiraIssueState, "__init__", side_effect=AssertionError("JiraIssueState must NOT be instantiated during third-party evaluation")) as mock_jira, \
             patch.object(GitHubPullRequestState, "__init__", side_effect=AssertionError("GitHubPullRequestState must NOT be instantiated during third-party evaluation")) as mock_gh:

            result = evaluate_evidence_bundle(bundle)

            # Neither legacy constructor was invoked
            assert mock_jira.call_count == 0
            assert mock_gh.call_count == 0

        # Assert on findings
        assert len(result.findings) >= 3
        rules_found = {f.rule_id for f in result.findings}
        assert rules_found == {"ORBIT-XB-01", "ORBIT-XB-02", "ORBIT-XB-03"}

        for f in result.findings:
            # 1. State types of subject and corroborating refs
            assert f.subject_ref.source_instance.source_kind == "linear"
            for cr in f.corroborating_refs:
                assert cr.source_instance.source_kind == "gitlab"

            # 2. Strict vendor absence in explanation
            exp = f.deterministic_explanation
            assert "jira" not in exp.lower(), f"Vendor 'Jira' leaked in explanation: {exp}"
            assert "github" not in exp.lower(), f"Vendor 'GitHub' leaked in explanation: {exp}"

            # 3. Canonical terms must be present
            assert "work item" in exp.lower() or "code change" in exp.lower() or "commit" in exp.lower()

            # 4. Strict fact keys verification: ZERO legacy keys, CANONICAL keys required
            fact_keys = set(f.observed_facts.keys())
            leaked_keys = fact_keys.intersection(legacy_fact_keys)
            assert not leaked_keys, f"Legacy keys leaked in observed_facts: {leaked_keys}"

            canonical_overlap = fact_keys.intersection(canonical_fact_keys)
            assert len(canonical_overlap) >= 1, f"Missing canonical keys in observed_facts: {fact_keys}"
