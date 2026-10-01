"""Pass 4 / Wave 5 — Track B EvidenceBundle Evaluator Unit & Adversarial Tests.

Verifies evaluate_evidence_bundle() for:
- ORBIT-XB-01: UNMERGED_PR_ON_RESOLVED_ISSUE
- ORBIT-XB-02: MERGED_PR_ON_UNRESOLVED_ISSUE
- ORBIT-XB-03: POST_RESOLUTION_WORK_ACTIVITY (Observational only)

Adversarial testing:
- Anti-Cartesian pairing (only relationship-bound pairs evaluated)
- Anti-transitive linking
- Anti-actor identity matching
- Anti-completion inference
- Temporal inversion != conflict
- Missing evidence remains explicit (Unknown != False)
- Full provenance preservation
- Output determinism & permutation invariance
- Frozen Track A preservation
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

import pytest

from shadow_orbit.evaluation import evaluate_week_one_rules
from shadow_orbit.evidence_evaluation import (
    EvidenceBundleEvaluationResult,
    TrackBFinding,
    evaluate_evidence_bundle,
    serialize_evaluation_result,
    serialize_track_b_finding,
)
from shadow_orbit.evidence_types import (
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
    QualityIssue,
    SourceInstance,
    UnresolvedReference,
    serialize_evidence_bundle,
)
from shadow_orbit.fixture_io import load_fixture
from shadow_orbit.normalization import normalize_fixture as normalize_jira_fixture
from shadow_orbit.validation import validate_fixture as validate_jira_fixture


# ── Shared Test Entities and Timestamps ──────────────────────────────────────

JIRA_SOURCE = SourceInstance(source_kind="jira", instance_id="jira.orbit.internal")
GITHUB_SOURCE = SourceInstance(source_kind="github", instance_id="github.com/org/repo")

T_JAN_01 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_05 = datetime(2026, 1, 5, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_10 = datetime(2026, 1, 10, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_15 = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_20 = datetime(2026, 1, 20, 10, 0, 0, tzinfo=timezone.utc)

JIRA_CTX = ObservationContext(
    observation_id="obs_jira_1",
    source_instance=JIRA_SOURCE,
    source_cutoff_at=T_JAN_20,
)
GITHUB_CTX = ObservationContext(
    observation_id="obs_github_1",
    source_instance=GITHUB_SOURCE,
    source_cutoff_at=T_JAN_20,
)


def make_jira_obs(
    key: str,
    status: str = "Done",
    status_cat: str = "done",
    created_at: datetime = T_JAN_01,
    resolved_at: datetime | None = T_JAN_10,
    due_at: datetime | None = T_JAN_05,
    assignee: str | None = "alice",
    quality_issues: tuple[QualityIssue, ...] = (),
) -> EvidenceObservation:
    ref = EntityRef(
        source_instance=JIRA_SOURCE, entity_kind="jira_issue", entity_id=key
    )
    state = JiraIssueState(
        key=key,
        source_status=status,
        source_priority="High",
        status_category=status_cat,
        priority_band="high",
        assignee=assignee,
        created_at=created_at,
        updated_at=resolved_at or created_at,
        resolved_at=resolved_at,
        due_at=due_at,
    )
    prov = ProvenanceRef(
        fixture_id="jira_fixture.json",
        record_locator=f"work_items[{key}]",
        source_field_path="work_items",
        observation_id=JIRA_CTX.observation_id,
        source_instance=JIRA_SOURCE,
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=JIRA_CTX,
        observed_state=state,
        quality_issues=quality_issues,
        provenance_refs=(prov,),
    )


def make_pr_obs(
    number: int,
    state: str = "open",
    title: str = "Implement feature",
    created_at: datetime = T_JAN_01,
    merged_at: datetime | None = None,
    author: str = "alice",
    quality_issues: tuple[QualityIssue, ...] = (),
) -> EvidenceObservation:
    ref = EntityRef(
        source_instance=GITHUB_SOURCE,
        entity_kind="github_pull_request",
        entity_id=f"repo/{number}",
    )
    pr_state = GitHubPullRequestState(
        number=number,
        title=title,
        state=state,
        author_login=author,
        target_branch="main",
        source_branch="feature",
        head_commit_sha="c0ffee1",
        is_fork=False,
        created_at=created_at,
        merged_at=merged_at,
    )
    prov = ProvenanceRef(
        fixture_id="github_fixture.json",
        record_locator=f"repositories[0].pull_requests[{number}]",
        source_field_path="pull_requests",
        observation_id=GITHUB_CTX.observation_id,
        source_instance=GITHUB_SOURCE,
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=GITHUB_CTX,
        observed_state=pr_state,
        quality_issues=quality_issues,
        provenance_refs=(prov,),
    )


def make_commit_obs(
    sha: str,
    message: str = "Fix PLAT-101",
    committed_at: datetime = T_JAN_15,
    author: str = "alice",
) -> EvidenceObservation:
    ref = EntityRef(
        source_instance=GITHUB_SOURCE,
        entity_kind="github_commit",
        entity_id=f"repo/{sha}",
    )
    state = GitHubCommitState(
        sha=sha,
        message=message,
        author_login=author,
        committed_at=committed_at,
    )
    prov = ProvenanceRef(
        fixture_id="github_fixture.json",
        record_locator=f"repositories[0].commits[{sha[:8]}]",
        source_field_path="commits",
        observation_id=GITHUB_CTX.observation_id,
        source_instance=GITHUB_SOURCE,
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=GITHUB_CTX,
        observed_state=state,
        provenance_refs=(prov,),
    )


def make_mention_rel(
    gh_ref: EntityRef,
    jira_ref: EntityRef,
    is_explicit: bool = False,
) -> EvidenceRelationship:
    kind = "explicit_link" if is_explicit else "mentions"
    basis = "explicit_metadata" if is_explicit else "lexical_match"
    prov = ProvenanceRef(
        fixture_id="github_fixture.json",
        record_locator=f"{gh_ref.entity_id}.title",
        source_field_path="title",
        observation_id=GITHUB_CTX.observation_id,
        source_instance=GITHUB_SOURCE,
    )
    return EvidenceRelationship(
        subject_ref=gh_ref,
        object_ref=jira_ref,
        kind=kind,
        basis=basis,
        subject_observation_id=GITHUB_CTX.observation_id,
        object_observation_id=JIRA_CTX.observation_id,
        provenance_refs=(prov,),
    )


# ── Test Suite: ORBIT-XB-01 (UNMERGED_PR_ON_RESOLVED_ISSUE) ─────────────────


class TestXB01UnmergedPrOnResolvedIssue:
    def test_resolved_jira_open_pr_triggers_finding(self):
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        pr = make_pr_obs(10, state="open", title="Fix PLAT-101")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb01_1",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-01"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "SUPPORTED"
        assert finding.subject_ref == jira.entity_ref
        assert finding.corroborating_refs == (pr.entity_ref,)
        assert "remains open" in finding.deterministic_explanation
        assert finding.observed_facts["jira_status_category"] == "done"
        assert finding.observed_facts["pr_state"] == "open"
        assert len(finding.provenance_refs) >= 2

    def test_resolved_jira_merged_pr_does_not_trigger_xb01(self):
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done", resolved_at=T_JAN_15)
        pr = make_pr_obs(10, state="merged", merged_at=T_JAN_10)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb01_2",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb01_findings = [f for f in res.findings if f.rule_id == "ORBIT-XB-01"]
        assert len(xb01_findings) == 0

    def test_unresolved_jira_open_pr_does_not_trigger_xb01(self):
        jira = make_jira_obs("PLAT-101", status="In Progress", status_cat="in_progress")
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb01_3",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb01_findings = [f for f in res.findings if f.rule_id == "ORBIT-XB-01"]
        assert len(xb01_findings) == 0

    def test_missing_jira_observation_emits_unresolved_suppression(self):
        pr = make_pr_obs(10, state="open")
        missing_jira_ref = EntityRef(
            source_instance=JIRA_SOURCE, entity_kind="jira_issue", entity_id="PLAT-999"
        )
        rel = make_mention_rel(pr.entity_ref, missing_jira_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb01_4",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(pr,),  # Jira is missing!
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 0
        assert len(res.suppressed_evaluations) == 1
        suppressed = res.suppressed_evaluations[0]
        assert suppressed.rule_id == "ORBIT-XB-01"
        assert suppressed.disposition == "INSUFFICIENT_EVIDENCE"
        assert suppressed.sufficiency == "UNRESOLVED"

    def test_missing_pr_state_emits_insufficient_evidence(self):
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        # PR with None state
        pr = make_pr_obs(10, state=None)  # type: ignore
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb01_5",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 0
        assert len(res.suppressed_evaluations) == 1
        assert res.suppressed_evaluations[0].sufficiency == "INSUFFICIENT_EVIDENCE"

    def test_declared_mention_has_supported_sufficiency(self):
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref, is_explicit=False)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb01_6",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        assert len(res.suppressed_evaluations) == 0
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-01"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "SUPPORTED"
        assert finding.subject_ref == jira.entity_ref
        assert finding.corroborating_refs == (pr.entity_ref,)
        assert finding.observed_facts["relationship_kind"] == "declared_mention"
        assert len(finding.provenance_refs) >= 2

    def test_explicit_link_has_proven_sufficiency(self):
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref, is_explicit=True)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb01_7",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        assert len(res.suppressed_evaluations) == 0
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-01"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "PROVEN"
        assert finding.subject_ref == jira.entity_ref
        assert finding.corroborating_refs == (pr.entity_ref,)
        assert finding.observed_facts["relationship_kind"] == "explicit_link"
        assert len(finding.provenance_refs) >= 2

    def test_unrelated_jira_and_pr_produces_no_finding(self):
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        pr = make_pr_obs(10, state="open")
        # No relationship in bundle!

        bundle = EvidenceBundle(
            bundle_id="bundle_xb01_8",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(),  # empty!
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 0
        assert len(res.suppressed_evaluations) == 0

    def test_permutation_invariance(self):
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle1 = EvidenceBundle(
            bundle_id="bundle_perm",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )
        bundle2 = EvidenceBundle(
            bundle_id="bundle_perm",
            bundle_version="1.0.0",
            observation_contexts=(GITHUB_CTX, JIRA_CTX),
            observations=(pr, jira),
            relationships=(rel,),
        )

        res1 = evaluate_evidence_bundle(bundle1)
        res2 = evaluate_evidence_bundle(bundle2)
        assert res1.evaluation_id == res2.evaluation_id
        assert res1.findings == res2.findings

    def test_deterministic_finding_id(self):
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_det",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res1 = evaluate_evidence_bundle(bundle)
        res2 = evaluate_evidence_bundle(bundle)
        assert res1.findings[0].finding_id == res2.findings[0].finding_id
        assert res1.findings[0].finding_id.startswith("finding_orbit_xb_01_")


# ── Test Suite: ORBIT-XB-02 (MERGED_PR_ON_UNRESOLVED_ISSUE) ─────────────────


class TestXB02MergedPrOnUnresolvedIssue:
    def test_unresolved_jira_merged_pr_triggers_finding(self):
        jira = make_jira_obs("PLAT-102", status="In Progress", status_cat="in_progress")
        pr = make_pr_obs(20, state="merged", title="Feature WIP", merged_at=T_JAN_10)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb02_1",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-02"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "SUPPORTED"
        assert finding.subject_ref == jira.entity_ref
        assert "is merged while referenced Jira issue" in finding.deterministic_explanation
        assert finding.observed_facts["jira_status_category"] == "in_progress"
        assert finding.observed_facts["pr_state"] == "merged"

    def test_resolved_jira_merged_pr_does_not_trigger_xb02(self):
        jira = make_jira_obs("PLAT-102", status="Done", status_cat="done")
        pr = make_pr_obs(20, state="merged", merged_at=T_JAN_10)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb02_2",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb02 = [f for f in res.findings if f.rule_id == "ORBIT-XB-02"]
        assert len(xb02) == 0

    def test_unresolved_jira_open_pr_does_not_trigger_xb02(self):
        jira = make_jira_obs("PLAT-102", status="In Progress", status_cat="in_progress")
        pr = make_pr_obs(20, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb02_3",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb02 = [f for f in res.findings if f.rule_id == "ORBIT-XB-02"]
        assert len(xb02) == 0

    def test_missing_state_emits_insufficient_evidence(self):
        jira = make_jira_obs("PLAT-102", status="UnknownStatus", status_cat="unknown")
        pr = make_pr_obs(20, state="merged", merged_at=T_JAN_10)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb02_4",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb02_findings = [f for f in res.findings if f.rule_id == "ORBIT-XB-02"]
        assert len(xb02_findings) == 0
        xb02_suppressed = [s for s in res.suppressed_evaluations if s.rule_id == "ORBIT-XB-02"]
        assert len(xb02_suppressed) == 1
        assert xb02_suppressed[0].sufficiency == "INSUFFICIENT_EVIDENCE"

    def test_missing_merged_timestamp_emits_insufficient_evidence(self):
        jira = make_jira_obs("PLAT-102", status="In Progress", status_cat="in_progress")
        pr = make_pr_obs(20, state="merged", merged_at=None)  # missing merged_at!
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb02_5",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len([f for f in res.findings if f.rule_id == "ORBIT-XB-02"]) == 0
        suppressed = [s for s in res.suppressed_evaluations if s.rule_id == "ORBIT-XB-02"]
        assert len(suppressed) == 1
        assert suppressed[0].disposition == "INSUFFICIENT_EVIDENCE"
        assert suppressed[0].sufficiency == "INSUFFICIENT_EVIDENCE"

    def test_declared_mention_has_supported_sufficiency(self):
        jira = make_jira_obs("PLAT-102", status="To Do", status_cat="todo")
        pr = make_pr_obs(20, state="merged", merged_at=T_JAN_10)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref, is_explicit=False)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb02_6",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        assert len(res.suppressed_evaluations) == 0
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-02"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "SUPPORTED"
        assert finding.subject_ref == jira.entity_ref
        assert finding.corroborating_refs == (pr.entity_ref,)
        assert finding.observed_facts["relationship_kind"] == "declared_mention"
        assert len(finding.provenance_refs) >= 2

    def test_explicit_link_has_proven_sufficiency(self):
        jira = make_jira_obs("PLAT-102", status="To Do", status_cat="todo")
        pr = make_pr_obs(20, state="merged", merged_at=T_JAN_10)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref, is_explicit=True)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb02_7",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        assert len(res.suppressed_evaluations) == 0
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-02"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "PROVEN"
        assert finding.subject_ref == jira.entity_ref
        assert finding.corroborating_refs == (pr.entity_ref,)
        assert finding.observed_facts["relationship_kind"] == "explicit_link"
        assert len(finding.provenance_refs) >= 2

    def test_unrelated_entities_produces_no_finding(self):
        jira = make_jira_obs("PLAT-102", status="In Progress", status_cat="in_progress")
        pr = make_pr_obs(20, state="merged", merged_at=T_JAN_10)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb02_8",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 0

    def test_permutation_invariance(self):
        jira = make_jira_obs("PLAT-102", status="In Progress", status_cat="in_progress")
        pr = make_pr_obs(20, state="merged", merged_at=T_JAN_10)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle1 = EvidenceBundle(
            bundle_id="bundle_xb02_perm",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )
        bundle2 = EvidenceBundle(
            bundle_id="bundle_xb02_perm",
            bundle_version="1.0.0",
            observation_contexts=(GITHUB_CTX, JIRA_CTX),
            observations=(pr, jira),
            relationships=(rel,),
        )

        res1 = evaluate_evidence_bundle(bundle1)
        res2 = evaluate_evidence_bundle(bundle2)
        assert res1.findings == res2.findings
        assert res1.evaluation_id == res2.evaluation_id

    def test_deterministic_finding_id(self):
        jira = make_jira_obs("PLAT-102", status="In Progress", status_cat="in_progress")
        pr = make_pr_obs(20, state="merged", merged_at=T_JAN_10)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb02_det",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res1 = evaluate_evidence_bundle(bundle)
        res2 = evaluate_evidence_bundle(bundle)
        assert len(res1.findings) == 1
        assert res1.evaluation_id == res2.evaluation_id
        assert res1.findings[0].finding_id == res2.findings[0].finding_id
        assert res1.findings[0].finding_id.startswith("finding_orbit_xb_02_")
        assert res1.findings == res2.findings


# ── Test Suite: ORBIT-XB-03 (POST_RESOLUTION_WORK_ACTIVITY) ──────────────────


class TestXB03PostResolutionWorkActivity:
    def test_pr_merged_after_jira_resolution_triggers_observational_finding(self):
        # Jira resolved on Jan 10; PR merged on Jan 15 (5 days later)
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=T_JAN_10)
        pr = make_pr_obs(30, state="merged", merged_at=T_JAN_15)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb03_1",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb03_findings = [f for f in res.findings if f.rule_id == "ORBIT-XB-03"]
        assert len(xb03_findings) == 1
        finding = xb03_findings[0]
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "SUPPORTED"
        assert finding.observed_facts["elapsed_complete_days_post_resolution"] == 5
        assert finding.observed_facts["temporal_comparison"] == "INVERTED"

    def test_commit_after_jira_resolution_triggers_observational_finding(self):
        # Jira resolved on Jan 10; Commit committed on Jan 15
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=T_JAN_10)
        commit = make_commit_obs("a1b2c3d4", committed_at=T_JAN_15)
        rel = make_mention_rel(commit.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb03_2",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, commit),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb03_findings = [f for f in res.findings if f.rule_id == "ORBIT-XB-03"]
        assert len(xb03_findings) == 1
        finding = xb03_findings[0]
        assert finding.disposition == "TRIGGERED"
        assert finding.observed_facts["github_activity_kind"] == "commit"

    def test_pr_merged_before_jira_resolution_does_not_trigger_xb03(self):
        # PR merged on Jan 5, Jira resolved on Jan 10 -> Coherent, no inversion
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=T_JAN_10)
        pr = make_pr_obs(30, state="merged", merged_at=T_JAN_05)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb03_3",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb03 = [f for f in res.findings if f.rule_id == "ORBIT-XB-03"]
        assert len(xb03) == 0

    def test_exact_timestamp_equality_does_not_trigger_inversion(self):
        # Both exactly at T_JAN_10 -> Coincident, not inverted
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=T_JAN_10)
        pr = make_pr_obs(30, state="merged", merged_at=T_JAN_10)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb03_4",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb03 = [f for f in res.findings if f.rule_id == "ORBIT-XB-03"]
        assert len(xb03) == 0

    def test_missing_resolved_timestamp_emits_insufficient_evidence(self):
        # Jira marked done but resolved_at is None
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=None)
        pr = make_pr_obs(30, state="merged", merged_at=T_JAN_15)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb03_5",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb03_findings = [f for f in res.findings if f.rule_id == "ORBIT-XB-03"]
        assert len(xb03_findings) == 0
        xb03_supp = [s for s in res.suppressed_evaluations if s.rule_id == "ORBIT-XB-03"]
        assert len(xb03_supp) == 1
        assert xb03_supp[0].sufficiency == "INSUFFICIENT_EVIDENCE"

    def test_missing_github_activity_timestamp_emits_insufficient_evidence(self):
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=T_JAN_10)
        pr = make_pr_obs(30, state="merged", merged_at=None)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb03_6",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        xb03_findings = [f for f in res.findings if f.rule_id == "ORBIT-XB-03"]
        assert len(xb03_findings) == 0
        xb03_supp = [s for s in res.suppressed_evaluations if s.rule_id == "ORBIT-XB-03"]
        assert len(xb03_supp) == 1
        assert xb03_supp[0].sufficiency == "INSUFFICIENT_EVIDENCE"

    def test_temporal_inversion_never_becomes_conflicting(self):
        # Crucial adversarial invariant: temporal inversion != CONFLICTING
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=T_JAN_10)
        pr = make_pr_obs(30, state="merged", merged_at=T_JAN_20)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb03_7",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        finding = res.findings[0]
        assert finding.sufficiency != "CONFLICTING"
        assert finding.sufficiency == "SUPPORTED"
        assert finding.disposition == "TRIGGERED"

    def test_explanation_factual_temporal_sequence_no_defect_language(self):
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=T_JAN_10)
        pr = make_pr_obs(30, state="merged", merged_at=T_JAN_15)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb03_8",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        expl = res.findings[0].deterministic_explanation
        assert "observational temporal finding" in expl
        # Negative / forbidden words must NOT appear
        assert "late" not in expl.lower()
        assert "defect" not in expl.lower()
        assert "violation" not in expl.lower()
        assert "fault" not in expl.lower()
        assert "error" not in expl.lower()
        assert "wrong" not in expl.lower()

    def test_declared_mention_has_supported_sufficiency(self):
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=T_JAN_10)
        pr = make_pr_obs(30, state="merged", merged_at=T_JAN_15)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref, is_explicit=False)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb03_9",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        assert len(res.suppressed_evaluations) == 0
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-03"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "SUPPORTED"
        assert finding.sufficiency != "CONFLICTING"
        assert finding.subject_ref == jira.entity_ref
        assert finding.corroborating_refs == (pr.entity_ref,)
        assert finding.observed_facts["temporal_comparison"] == "INVERTED"
        assert finding.observed_facts["relationship_kind"] == "declared_mention"
        assert len(finding.provenance_refs) >= 2

    def test_explicit_link_has_proven_sufficiency(self):
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=T_JAN_10)
        pr = make_pr_obs(30, state="merged", merged_at=T_JAN_15)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref, is_explicit=True)

        bundle = EvidenceBundle(
            bundle_id="bundle_xb03_10",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        assert len(res.suppressed_evaluations) == 0
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-03"
        assert finding.disposition == "TRIGGERED"
        assert finding.sufficiency == "PROVEN"
        assert finding.sufficiency != "CONFLICTING"
        assert finding.subject_ref == jira.entity_ref
        assert finding.corroborating_refs == (pr.entity_ref,)
        assert finding.observed_facts["temporal_comparison"] == "INVERTED"
        assert finding.observed_facts["relationship_kind"] == "explicit_link"
        assert len(finding.provenance_refs) >= 2

    def test_permutation_invariance(self):
        jira = make_jira_obs("PLAT-103", status="Done", status_cat="done", resolved_at=T_JAN_10)
        pr = make_pr_obs(30, state="merged", merged_at=T_JAN_15)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle1 = EvidenceBundle(
            bundle_id="bundle_xb03_perm",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )
        bundle2 = EvidenceBundle(
            bundle_id="bundle_xb03_perm",
            bundle_version="1.0.0",
            observation_contexts=(GITHUB_CTX, JIRA_CTX),
            observations=(pr, jira),
            relationships=(rel,),
        )

        res1 = evaluate_evidence_bundle(bundle1)
        res2 = evaluate_evidence_bundle(bundle2)
        assert res1.findings == res2.findings
        assert res1.evaluation_id == res2.evaluation_id


# ── Test Suite: Cross-Cutting & Adversarial Invariants ───────────────────────


class TestCrossCuttingAndAdversarial:
    def test_no_cartesian_pairing(self):
        """Adversarial check: 2 Jira issues, 2 PRs, but only 1 legitimate relationship."""
        jira_a = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        jira_b = make_jira_obs("PLAT-102", status="Done", status_cat="done")
        pr_a = make_pr_obs(10, state="open", title="Fix PLAT-101")
        pr_b = make_pr_obs(20, state="open", title="Unrelated feature")

        # Only PR A mentions Jira A
        rel_a = make_mention_rel(pr_a.entity_ref, jira_a.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_cartesian",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira_a, jira_b, pr_a, pr_b),
            relationships=(rel_a,),
        )

        res = evaluate_evidence_bundle(bundle)
        # Exactly 1 finding for PLAT-101 + PR #10.
        # PLAT-102 must NEVER pair with PR #10 or PR #20!
        assert len(res.findings) == 1
        assert res.findings[0].subject_ref == jira_a.entity_ref
        assert res.findings[0].corroborating_refs == (pr_a.entity_ref,)

    def test_no_transitive_association(self):
        """Adversarial check: Commit cites Jira, PR contains Commit, but PR doesn't cite Jira."""
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        commit = make_commit_obs("c0ffee1", message="Fix PLAT-101", committed_at=T_JAN_15)
        pr = make_pr_obs(10, state="open", title="Merge release branch")

        # Commit mentions Jira
        rel_commit_jira = make_mention_rel(commit.entity_ref, jira.entity_ref)
        # Structural PR contains Commit
        rel_pr_commit = EvidenceRelationship(
            subject_ref=pr.entity_ref,
            object_ref=commit.entity_ref,
            kind="contains_commit",
            basis="structural_containment",
            subject_observation_id=GITHUB_CTX.observation_id,
            object_observation_id=GITHUB_CTX.observation_id,
            provenance_refs=(),
        )

        bundle = EvidenceBundle(
            bundle_id="bundle_transitive",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, commit, pr),
            relationships=(rel_commit_jira, rel_pr_commit),
        )

        res = evaluate_evidence_bundle(bundle)
        # PR is NOT linked to Jira; no XB-01 finding should exist for PR!
        xb01_findings = [f for f in res.findings if f.rule_id == "ORBIT-XB-01"]
        assert len(xb01_findings) == 0

        # Commit is linked to Jira -> XB-03 triggers on Commit (post-resolution commit)
        xb03_findings = [f for f in res.findings if f.rule_id == "ORBIT-XB-03"]
        assert len(xb03_findings) == 1
        assert xb03_findings[0].corroborating_refs == (commit.entity_ref,)

    def test_no_actor_matching(self):
        """Adversarial check: Matching username strings do not forge relationships."""
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done", assignee="alice")
        pr = make_pr_obs(10, state="open", author="alice", title="Clean repo")
        # No relationships!

        bundle = EvidenceBundle(
            bundle_id="bundle_actor",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 0

    def test_no_completion_inference(self):
        """Adversarial check: Merged PR does not prove Jira ticket is complete."""
        jira = make_jira_obs("PLAT-102", status="In Progress", status_cat="in_progress")
        pr = make_pr_obs(20, state="merged", merged_at=T_JAN_10)
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_completion",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        # Triggers tracking lag (XB-02), never assumes ticket is complete
        assert len(res.findings) == 1
        assert res.findings[0].rule_id == "ORBIT-XB-02"
        assert "merging code does not prove issue completion" in res.findings[0].deterministic_explanation

    def test_provenance_preservation(self):
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_prov",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        finding = res.findings[0]
        # Must retain Jira provenance, PR provenance, and mention provenance
        locators = {p.record_locator for p in finding.provenance_refs}
        assert "work_items[PLAT-101]" in locators
        assert "repositories[0].pull_requests[10]" in locators
        assert "repo/10.title" in locators

    def test_stale_observation_handling(self):
        # Real pipeline signal: code='invalid' with subject_scope='provenance:temporal'
        stale_qi = QualityIssue(
            code="invalid",
            subject_ref=None,
            subject_scope="provenance:temporal",
            message="Resolved record timestamp postdates source cutoff.",
        )
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done", quality_issues=(stale_qi,))
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_stale",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 0
        assert len(res.suppressed_evaluations) == 1
        assert res.suppressed_evaluations[0].sufficiency == "STALE"
        assert res.suppressed_evaluations[0].disposition == "SUPPRESSED"

    def test_illegal_stale_quality_code_rejected(self):
        """Constructing QualityIssue with non-standard code='STALE' raises ValueError."""
        with pytest.raises(ValueError):
            QualityIssue(
                code="STALE",  # type: ignore[arg-type]
                subject_ref=None,
                subject_scope="temporal:staleness",
                message="Observation postdates review cutoff.",
            )

    def test_unresolved_reference_handling(self):
        pr = make_pr_obs(10, state="open")
        unresolved = UnresolvedReference(
            source_ref=pr.entity_ref,
            source_observation_id=GITHUB_CTX.observation_id,
            target_entity_kind="jira_issue",
            target_identifier="PLAT-404",
            relationship_kind="mentions",
            reason="Referenced key not present in Jira fixture.",
            provenance_refs=(),
        )

        bundle = EvidenceBundle(
            bundle_id="bundle_unres",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(pr,),
            unresolved_references=(unresolved,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 0
        assert len(res.suppressed_evaluations) == 1
        assert res.suppressed_evaluations[0].sufficiency == "UNRESOLVED"
        assert res.suppressed_evaluations[0].subject_ref.entity_id == "PLAT-404"

    def test_quality_issue_preservation(self):
        qi = QualityIssue(
            code="incomplete",
            subject_ref=None,
            subject_scope="jira:history",
            message="Changelog is partial.",
        )
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done", quality_issues=(qi,))
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_qi",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        finding = res.findings[0]
        assert len(finding.quality_issues) == 1
        assert finding.quality_issues[0].code == "incomplete"

    def test_deterministic_serialization(self):
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_ser",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
        )

        res1 = evaluate_evidence_bundle(bundle)
        d1 = serialize_evaluation_result(res1)
        json_str1 = json.dumps(d1, sort_keys=True)

        res2 = evaluate_evidence_bundle(bundle)
        d2 = serialize_evaluation_result(res2)
        json_str2 = json.dumps(d2, sort_keys=True)

        # Repeated evaluation and serialization produces bit-for-bit identical string
        assert json_str1 == json_str2

        # Permuted observation and context ordering produces identical serialized string
        bundle_permuted = EvidenceBundle(
            bundle_id="bundle_ser",
            bundle_version="1.0.0",
            observation_contexts=(GITHUB_CTX, JIRA_CTX),
            observations=(pr, jira),
            relationships=(rel,),
        )
        res_perm = evaluate_evidence_bundle(bundle_permuted)
        d_perm = serialize_evaluation_result(res_perm)
        json_str_perm = json.dumps(d_perm, sort_keys=True)
        assert json_str1 == json_str_perm

        # Detailed roundtrip parsing verification
        parsed = json.loads(json_str1)
        assert parsed["evaluation_id"] == res1.evaluation_id
        assert parsed["bundle_id"] == "bundle_ser"
        assert parsed["evaluated_at"] == res1.evaluated_at
        assert len(parsed["findings"]) == 1
        assert parsed["findings"][0]["rule_id"] == "ORBIT-XB-01"
        assert parsed["findings"][0]["finding_id"] == res1.findings[0].finding_id
        assert parsed["findings"][0]["disposition"] == "TRIGGERED"
        assert parsed["findings"][0]["sufficiency"] == "SUPPORTED"
        assert len(parsed["suppressed_evaluations"]) == 0
        assert parsed["summary"]["total_findings"] == 1
        assert parsed["summary"]["rules_evaluated"] == ["ORBIT-XB-01", "ORBIT-XB-02", "ORBIT-XB-03"]

    def test_xb04_not_implemented(self):
        """Verifies that ORBIT-XB-04 is NOT evaluated in Wave 5."""
        jira = make_jira_obs(
            "PLAT-104", status="In Progress", status_cat="in_progress", due_at=T_JAN_05
        )
        bundle = EvidenceBundle(
            bundle_id="bundle_no_xb04",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX,),
            observations=(jira,),
        )
        res = evaluate_evidence_bundle(bundle)
        xb04 = [f for f in res.findings if "XB-04" in f.rule_id]
        assert len(xb04) == 0

    def test_track_a_unchanged(self):
        """Verifies that Track A produces identical frozen output."""
        raw = load_fixture("fixtures/jira/northstar_clean_week_1.json")
        val = validate_jira_fixture(raw)
        norm = normalize_jira_fixture(val)
        matches, suppressed = evaluate_week_one_rules(norm)
        # In clean week 1, Track A produces 3 matches and 2 suppressed evaluations
        assert len(matches) == 3
        assert len(suppressed) == 2
        rule_keys = {m.rule_key for m in matches}
        assert rule_keys == {
            "BLOCKED_HIGH_PRIORITY",
            "OVERDUE_HIGH_PRIORITY",
            "STALLED_WORK",
        }

    def test_ambiguous_evidence_handling(self):
        """Ambiguous evidence (>1 observation candidate for same entity key) emits suppression."""
        jira_obs_1 = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        jira_obs_2 = make_jira_obs("PLAT-101", status="In Progress", status_cat="in_progress")
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira_obs_1.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_ambiguous",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira_obs_1, jira_obs_2, pr),
            relationships=(rel,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 0
        assert len(res.suppressed_evaluations) == 1
        supp = res.suppressed_evaluations[0]
        assert supp.rule_id == "ORBIT-XB-01"
        assert supp.disposition == "INSUFFICIENT_EVIDENCE"
        assert supp.sufficiency == "AMBIGUOUS"
        assert "Multiple candidate observations" in supp.deterministic_explanation
        assert supp.observed_facts["jira_obs_count"] == 2
        assert supp.observed_facts["github_obs_count"] == 1
        assert supp.subject_ref == jira_obs_1.entity_ref
        assert supp.corroborating_refs == (pr.entity_ref,)
        assert len(supp.provenance_refs) >= 3

    def test_mutation_safety(self):
        """evaluate_evidence_bundle does not mutate input EvidenceBundle or its nested structures."""
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        pr = make_pr_obs(10, state="open")
        rel = make_mention_rel(pr.entity_ref, jira.entity_ref)

        bundle = EvidenceBundle(
            bundle_id="bundle_mut_safety",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel,),
            unresolved_references=(
                UnresolvedReference(
                    source_ref=pr.entity_ref,
                    source_observation_id=GITHUB_CTX.observation_id,
                    target_entity_kind="jira_issue",
                    target_identifier="PLAT-999",
                    relationship_kind="mentions",
                    reason="Target not in fixture",
                    provenance_refs=pr.provenance_refs,
                ),
            ),
        )

        bundle_json_before = json.dumps(serialize_evidence_bundle(bundle), sort_keys=True)
        contexts_before = list(bundle.observation_contexts)
        observations_before = list(bundle.observations)
        relationships_before = list(bundle.relationships)
        unresolved_before = list(bundle.unresolved_references)

        res = evaluate_evidence_bundle(bundle)

        bundle_json_after = json.dumps(serialize_evidence_bundle(bundle), sort_keys=True)
        assert bundle_json_before == bundle_json_after
        assert bundle.observation_contexts == tuple(contexts_before)
        assert bundle.observations == tuple(observations_before)
        assert bundle.relationships == tuple(relationships_before)
        assert bundle.unresolved_references == tuple(unresolved_before)
        assert len(res.findings) == 1

    def test_duplicate_relationship_and_alignment_handling(self):
        """Duplicate relationships and alignments for the same entity pair do not produce duplicate findings."""
        jira = make_jira_obs("PLAT-101", status="Done", status_cat="done")
        pr = make_pr_obs(10, state="open")
        rel1 = make_mention_rel(pr.entity_ref, jira.entity_ref)
        rel2 = make_mention_rel(pr.entity_ref, jira.entity_ref)

        alignment = CrossSystemStateAlignment(
            jira_ref=jira.entity_ref,
            github_ref=pr.entity_ref,
            relationship_kind="declared_mention",
            state_comparison="INSUFFICIENT_EVIDENCE",
            temporal_comparison="INDETERMINATE",
            rationale="Precomputed test alignment",
            provenance_refs=rel1.provenance_refs,
        )

        bundle = EvidenceBundle(
            bundle_id="bundle_duplicate_rels",
            bundle_version="1.0.0",
            observation_contexts=(JIRA_CTX, GITHUB_CTX),
            observations=(jira, pr),
            relationships=(rel1, rel2),
            cross_system_alignments=(alignment,),
        )

        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 1
        assert len(res.suppressed_evaluations) == 0
        finding = res.findings[0]
        assert finding.rule_id == "ORBIT-XB-01"
        assert finding.disposition == "TRIGGERED"
        assert finding.subject_ref == jira.entity_ref
        assert finding.corroborating_refs == (pr.entity_ref,)
        assert len(finding.provenance_refs) >= 2
