"""Cross-Instance Identity Isolation Adversarial Test Suite.

Adversarial audit testing for Project ORBIT's Track B EvidenceBundle evaluator
(evaluate_evidence_bundle).

Contract Hypothesis:
    evaluate_evidence_bundle() identifies observations using (entity_kind, entity_id)
    rather than canonical identity (source_instance, entity_kind, entity_id), and
    candidate-pair indexing collapses distinct entity pairs when kinds and IDs match
    across different source instances.

Canon Contract Oracle:
    Under Project ORBIT's canonical identity contract:
    - EntityRef equality and hashing require (source_instance, entity_kind, entity_id).
    - SourceInstance distinguishes distinct system deployments (e.g., separate Jira sites).
    - Entities from separate source instances are logically independent.
    - An observation or relationship in instance A must never satisfy, collide with,
      suppress, or contaminate entities in instance B.
    - Candidate pairs are indexed by canonical identity (EntityRef, EntityRef), not
      kind/id tuples.
    - Evaluation results are strictly permutation-invariant across all semantic outputs.

These tests are derived independently from the canonical identity contract.
Per audit governance, assertions reflect the canonical contract oracle and must
NOT be weakened, skipped, or rewritten to conform to buggy implementation behavior.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import pytest

from shadow_orbit.evidence_assembly import validate_evidence_bundle
from shadow_orbit.evidence_evaluation import (
    TrackBFinding,
    _generate_finding_id,
    _sort_finding_key,
    evaluate_evidence_bundle,
)
from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceBundle,
    EvidenceObservation,
    EvidenceRelationship,
    GitHubPullRequestState,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    SourceInstance,
)

# ── Shared Canonical Fixtures ────────────────────────────────────────────────

T_JAN_01 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_10 = datetime(2026, 1, 10, 10, 0, 0, tzinfo=timezone.utc)
T_JAN_20 = datetime(2026, 1, 20, 10, 0, 0, tzinfo=timezone.utc)

JIRA_INSTANCE_A = SourceInstance(source_kind="jira", instance_id="jira-site-alpha")
JIRA_INSTANCE_B = SourceInstance(source_kind="jira", instance_id="jira-site-beta")
GITHUB_INSTANCE = SourceInstance(source_kind="github", instance_id="github.com/org/repo")

CTX_A = ObservationContext(
    observation_id="obs_ctx_jira_alpha",
    source_instance=JIRA_INSTANCE_A,
    source_cutoff_at=T_JAN_20,
)
CTX_B = ObservationContext(
    observation_id="obs_ctx_jira_beta",
    source_instance=JIRA_INSTANCE_B,
    source_cutoff_at=T_JAN_20,
)
CTX_GH = ObservationContext(
    observation_id="obs_ctx_github",
    source_instance=GITHUB_INSTANCE,
    source_cutoff_at=T_JAN_20,
)


def _make_jira_observation(
    source_instance: SourceInstance,
    context: ObservationContext,
    issue_key: str,
    status: str,
    status_category: str,
) -> EvidenceObservation:
    ref = EntityRef(
        source_instance=source_instance,
        entity_kind="jira_issue",
        entity_id=issue_key,
    )
    state = JiraIssueState(
        key=issue_key,
        source_status=status,
        source_priority="High",
        status_category=status_category,
        priority_band="high",
        assignee="developer",
        created_at=T_JAN_01,
        updated_at=T_JAN_10,
        resolved_at=T_JAN_10 if status_category == "done" else None,
    )
    prov = ProvenanceRef(
        source_instance=source_instance,
        observation_id=context.observation_id,
        fixture_id=f"{source_instance.instance_id}.json",
        record_locator=f"issues[{issue_key}]",
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=context,
        observed_state=state,
        provenance_refs=(prov,),
    )


def _make_pr_observation(
    pr_number: int,
    state: str = "open",
) -> EvidenceObservation:
    ref = EntityRef(
        source_instance=GITHUB_INSTANCE,
        entity_kind="github_pull_request",
        entity_id=f"repo/{pr_number}",
    )
    pr_state = GitHubPullRequestState(
        number=pr_number,
        title=f"PR #{pr_number}",
        state=state,
        author_login="committer",
        target_branch="main",
        source_branch="feature",
        head_commit_sha="c0ffee1",
        is_fork=False,
        created_at=T_JAN_01,
        merged_at=T_JAN_10 if state == "merged" else None,
    )
    prov = ProvenanceRef(
        source_instance=GITHUB_INSTANCE,
        observation_id=CTX_GH.observation_id,
        fixture_id="github_repo.json",
        record_locator=f"pull_requests[{pr_number}]",
    )
    return EvidenceObservation(
        entity_ref=ref,
        observation_context=CTX_GH,
        observed_state=pr_state,
        provenance_refs=(prov,),
    )


def _make_mention_relationship(
    gh_ref: EntityRef,
    jira_ref: EntityRef,
    jira_context_id: str,
) -> EvidenceRelationship:
    prov = ProvenanceRef(
        source_instance=GITHUB_INSTANCE,
        observation_id=CTX_GH.observation_id,
        fixture_id="github_repo.json",
        record_locator=f"{gh_ref.entity_id}.title",
    )
    return EvidenceRelationship(
        subject_ref=gh_ref,
        object_ref=jira_ref,
        kind="mentions",
        basis="lexical_match",
        subject_observation_id=CTX_GH.observation_id,
        object_observation_id=jira_context_id,
        provenance_refs=(prov,),
    )


def _canonicalize_finding(f: TrackBFinding) -> dict[str, Any]:
    """Extract deterministic semantic signature of a TrackBFinding."""
    return {
        "finding_id": f.finding_id,
        "rule_id": f.rule_id,
        "rule_version": f.rule_version,
        "subject_ref": (
            f.subject_ref.source_instance.source_kind,
            f.subject_ref.source_instance.instance_id,
            f.subject_ref.entity_kind,
            f.subject_ref.entity_id,
        ),
        "corroborating_refs": tuple(
            (
                c.source_instance.source_kind,
                c.source_instance.instance_id,
                c.entity_kind,
                c.entity_id,
            )
            for c in f.corroborating_refs
        ),
        "disposition": f.disposition,
        "sufficiency": f.sufficiency,
        "deterministic_explanation": f.deterministic_explanation,
        "observed_facts": f.observed_facts,
        "provenance_refs": tuple(
            (
                p.source_instance.source_kind,
                p.source_instance.instance_id,
                p.observation_id,
                p.fixture_id,
                p.record_locator,
                p.source_field_path,
            )
            for p in f.provenance_refs
        ),
        "quality_issues": tuple(
            (q.code, q.message, q.subject_scope) for q in f.quality_issues
        ),
    }


# ── Test Suite ───────────────────────────────────────────────────────────────


class TestCrossInstanceIdentityIsolation:
    """Adversarial tests verifying cross-instance isolation across distinct deployments."""

    def test_scenario_a_conflicting_duplicate_ids_across_instances(self):
        """Test A: Duplicate issue keys across instances with conflicting states.

        Setup:
            - Jira Instance Alpha has PROJ-123 with status 'Done' (category 'done').
            - Jira Instance Beta has PROJ-123 with status 'In Progress' (category 'in_progress').
            - GitHub PR #10 is 'open'.
            - EvidenceRelationship explicitly links GitHub PR #10 to Jira Alpha PROJ-123.

        Canonical Contract Oracle:
            - Jira Alpha and Jira Beta are completely distinct deployments.
            - The relationship targets Jira Alpha PROJ-123.
            - Jira Alpha is resolved ('done') while PR #10 is open, satisfying ORBIT-XB-01.
            - Jira Beta PROJ-123 must NOT cause Jira Alpha to be marked AMBIGUOUS or suppressed.
            - Evaluator must emit a TRIGGERED finding for Jira Alpha PROJ-123.
            - Jira Beta's state, observations, and provenance must not contaminate Jira Alpha.
        """
        obs_alpha = _make_jira_observation(
            JIRA_INSTANCE_A, CTX_A, "PROJ-123", "Done", "done"
        )
        obs_beta = _make_jira_observation(
            JIRA_INSTANCE_B, CTX_B, "PROJ-123", "In Progress", "in_progress"
        )
        pr_10 = _make_pr_observation(10, state="open")
        rel_alpha = _make_mention_relationship(
            pr_10.entity_ref, obs_alpha.entity_ref, CTX_A.observation_id
        )

        bundle = EvidenceBundle(
            bundle_id="bundle_scenario_a",
            bundle_version="1.0.0",
            observation_contexts=(CTX_A, CTX_B, CTX_GH),
            observations=(obs_alpha, obs_beta, pr_10),
            relationships=(rel_alpha,),
        )

        result = evaluate_evidence_bundle(bundle)

        # Oracle Assertion 1: Instance Alpha must be evaluated and TRIGGERED for ORBIT-XB-01
        assert len(result.findings) == 1, (
            f"Expected exactly 1 triggered finding for Jira Alpha, got {len(result.findings)}. "
            f"Suppressed count: {len(result.suppressed_evaluations)}"
        )
        finding = result.findings[0]
        assert finding.rule_id == "ORBIT-XB-01"
        assert finding.disposition == "TRIGGERED"
        assert finding.subject_ref == obs_alpha.entity_ref
        assert finding.subject_ref.source_instance == JIRA_INSTANCE_A

        # Oracle Assertion 2: Instance Alpha must NOT be suppressed as AMBIGUOUS due to Instance Beta
        ambiguous_suppressions = [
            s for s in result.suppressed_evaluations if s.sufficiency == "AMBIGUOUS"
        ]
        assert not ambiguous_suppressions, (
            f"Instance Alpha was erroneously marked AMBIGUOUS due to Instance Beta: "
            f"{ambiguous_suppressions}"
        )

        # Oracle Assertion 3: Jira Beta's provenance must not contaminate Jira Alpha's finding
        assert not any(
            p.source_instance == JIRA_INSTANCE_B for p in finding.provenance_refs
        ), f"Jira Beta provenance leaked into Jira Alpha finding: {finding.provenance_refs}"

    def test_scenario_b_only_wrong_instance_present(self):
        """Test B: Target instance observation is absent, but an identical key exists in another instance.

        Setup:
            - Jira Instance Alpha PROJ-123 is the target of the relationship with PR #10.
            - Jira Instance Alpha observation is ABSENT from the bundle.
            - Jira Instance Beta PROJ-123 IS observed (status 'Done', category 'done').
            - GitHub PR #10 is 'open'.

        Canonical Contract Oracle:
            - The relationship specifies subject Jira Alpha PROJ-123.
            - Jira Alpha is not in bundle.observations.
            - The evaluator must NOT adopt Jira Beta's observation to fulfill Jira Alpha's lookup.
            - The evaluation must report missing evidence / UNRESOLVED for Jira Alpha.
            - No TRIGGERED finding may be produced by substituting Jira Beta for Jira Alpha.
            - Under no circumstances may Jira Beta's provenance be attached to a Jira Alpha finding.
        """
        obs_beta = _make_jira_observation(
            JIRA_INSTANCE_B, CTX_B, "PROJ-123", "Done", "done"
        )
        pr_10 = _make_pr_observation(10, state="open")
        target_ref_alpha = EntityRef(
            source_instance=JIRA_INSTANCE_A,
            entity_kind="jira_issue",
            entity_id="PROJ-123",
        )
        rel_alpha = _make_mention_relationship(
            pr_10.entity_ref, target_ref_alpha, CTX_A.observation_id
        )

        bundle = EvidenceBundle(
            bundle_id="bundle_scenario_b",
            bundle_version="1.0.0",
            observation_contexts=(CTX_A, CTX_B, CTX_GH),
            observations=(obs_beta, pr_10),  # Jira Alpha is intentionally absent
            relationships=(rel_alpha,),
        )

        result = evaluate_evidence_bundle(bundle)

        # Oracle Assertion 1: Must NOT produce a false-positive TRIGGERED finding using Beta's state
        assert len(result.findings) == 0, (
            f"Evaluator incorrectly produced a TRIGGERED finding by adopting observation from "
            f"wrong instance Jira Beta for target Jira Alpha: {result.findings}"
        )

        # Oracle Assertion 2: Must emit an UNRESOLVED suppressed finding for missing Jira Alpha
        unresolved_suppressed = [
            s for s in result.suppressed_evaluations if s.sufficiency == "UNRESOLVED"
        ]
        assert len(unresolved_suppressed) == 1, (
            f"Expected 1 UNRESOLVED evaluation for missing Jira Alpha observation, got "
            f"{len(unresolved_suppressed)}"
        )
        supp = unresolved_suppressed[0]
        assert supp.subject_ref == target_ref_alpha
        assert supp.subject_ref.source_instance == JIRA_INSTANCE_A
        assert supp.disposition == "INSUFFICIENT_EVIDENCE"
        assert supp.rule_id == "ORBIT-XB-01"
        assert supp.corroborating_refs == (pr_10.entity_ref,)
        assert supp.observed_facts.get("missing_entity") == "jira_issue:PROJ-123"
        assert supp.observed_facts.get("referencing_entity") == "github_pull_request:repo/10"
        assert "Referenced Jira issue PROJ-123 was not observed" in supp.deterministic_explanation

        # Oracle Assertion 3: No provenance from Jira Beta may be attached to the Jira Alpha evaluation
        for s in result.suppressed_evaluations:
            assert not any(
                p.source_instance == JIRA_INSTANCE_B for p in s.provenance_refs
            ), f"Jira Beta provenance incorrectly attached to Jira Alpha evaluation: {s.provenance_refs}"

    def test_scenario_c_candidate_pair_collision_across_instances(self):
        """Test C: Candidate pairs with same entity_kind and entity_id across distinct instances.

        Setup:
            - Jira Alpha PROJ-123 is 'Done' (category 'done').
            - Jira Beta PROJ-123 is 'Done' (category 'done').
            - GitHub PR #10 is 'open'.
            - Relationship 1 links PR #10 to Jira Alpha PROJ-123.
            - Relationship 2 links PR #10 to Jira Beta PROJ-123.

        Canonical Contract Oracle:
            - Pair 1 (Jira Alpha PROJ-123, PR 10) and Pair 2 (Jira Beta PROJ-123, PR 10) are
              two distinct canonical candidate pairs.
            - The bundle must be accepted by validate_evidence_bundle() without quality issues.
            - The evaluator candidate-pair indexing must NOT collapse or overwrite either pair.
            - Both pairs must be evaluated (neither silently dropped).
            - Note: The project has not decided whether this situation should produce independent
              findings (Option A), an ambiguous multi-tenant suppression (Option B), or require
              an upstream routing policy (Option C). The test asserts structural preservation and
              isolation across all_evals without mandating finding disposition count.
        """
        obs_alpha = _make_jira_observation(
            JIRA_INSTANCE_A, CTX_A, "PROJ-123", "Done", "done"
        )
        obs_beta = _make_jira_observation(
            JIRA_INSTANCE_B, CTX_B, "PROJ-123", "Done", "done"
        )
        pr_10 = _make_pr_observation(10, state="open")
        rel_alpha = _make_mention_relationship(
            pr_10.entity_ref, obs_alpha.entity_ref, CTX_A.observation_id
        )
        rel_beta = _make_mention_relationship(
            pr_10.entity_ref, obs_beta.entity_ref, CTX_B.observation_id
        )

        bundle = EvidenceBundle(
            bundle_id="bundle_scenario_c",
            bundle_version="1.0.0",
            observation_contexts=(CTX_A, CTX_B, CTX_GH),
            observations=(obs_alpha, obs_beta, pr_10),
            relationships=(rel_alpha, rel_beta),
        )

        # Oracle Step 1: Verify bundle is valid under production assembly validation
        validation_issues = validate_evidence_bundle(bundle)
        assert validation_issues == (), (
            f"Production validate_evidence_bundle rejected multi-instance candidate bundle: "
            f"{validation_issues}"
        )

        result = evaluate_evidence_bundle(bundle)

        # Policy-Neutral Verification:
        # The project has NOT resolved whether multi-instance same-key PR associations
        # should produce N independent findings (Option A), an ambiguous multi-tenant
        # suppression (Option B), or require an upstream routing policy (Option C).
        # We do NOT assert len(result.findings) == 2 as a required product contract.
        #
        # Instead, we assert the already-established structural contracts:
        # 1. Total evaluated candidate records (findings + suppressions) must equal the
        #    number of distinct explicit relationship pairs (2 pairs; neither dropped or overwritten).
        all_evals = result.findings + result.suppressed_evaluations
        assert len(all_evals) == 2, (
            f"Expected 2 candidate pair evaluations (neither pair dropped or collapsed), "
            f"got {len(all_evals)} (findings={len(result.findings)}, "
            f"suppressed={len(result.suppressed_evaluations)})"
        )

        # 2. Both distinct canonical source instances must be represented.
        eval_instances = {
            e.subject_ref.source_instance.instance_id for e in all_evals
        }
        assert eval_instances == {"jira-site-alpha", "jira-site-beta"}, (
            f"Expected evaluations for both alpha and beta instances, got: {eval_instances}"
        )

        # 3. Full canonical EntityRef distinction and distinct finding IDs.
        subject_refs = {e.subject_ref for e in all_evals}
        assert subject_refs == {obs_alpha.entity_ref, obs_beta.entity_ref}, (
            f"Expected exact canonical subject refs for Alpha and Beta, got: {subject_refs}"
        )
        finding_ids = [e.finding_id for e in all_evals]
        assert len(set(finding_ids)) == 2, f"Evaluation finding IDs collided: {finding_ids}"

        # 4. Strict cross-instance isolation: zero state/provenance contamination.
        for e in all_evals:
            if e.subject_ref.source_instance == JIRA_INSTANCE_A:
                assert not any(
                    p.source_instance == JIRA_INSTANCE_B for p in e.provenance_refs
                ), f"Beta provenance leaked into Alpha evaluation: {e.provenance_refs}"
            elif e.subject_ref.source_instance == JIRA_INSTANCE_B:
                assert not any(
                    p.source_instance == JIRA_INSTANCE_A for p in e.provenance_refs
                ), f"Alpha provenance leaked into Beta evaluation: {e.provenance_refs}"

        # 5. Anti-Cartesian guarantee: no synthetic relationships or cross-instance pairings.
        for e in all_evals:
            assert e.corroborating_refs == (pr_10.entity_ref,), (
                f"Unexpected corroborating refs in evaluation: {e.corroborating_refs}"
            )

    def test_scenario_d_input_order_invariance(self):
        """Test D: Permutation invariance across observation and relationship orderings.

        Setup:
            - Permute the insertion order of relationships and observations from Scenario C:
                Order 1: (rel_alpha, rel_beta), observations=(obs_alpha, obs_beta, pr_10)
                Order 2: (rel_beta, rel_alpha), observations=(obs_beta, obs_alpha, pr_10)

        Canonical Contract Oracle:
            - Project ORBIT Track B mandates deterministic permutation invariance.
            - The set of evaluated pairs, findings, and dispositions must be bit-for-bit
              or logically identical regardless of input ordering.
            - Changing relationship order must NOT alter which instance pair survives or is evaluated.
            - Full canonical semantic outputs (finding IDs, rules, dispositions, subjects,
              corroborating refs, observed facts, and provenance) must match identically.
        """
        obs_alpha = _make_jira_observation(
            JIRA_INSTANCE_A, CTX_A, "PROJ-123", "Done", "done"
        )
        obs_beta = _make_jira_observation(
            JIRA_INSTANCE_B, CTX_B, "PROJ-123", "Done", "done"
        )
        pr_10 = _make_pr_observation(10, state="open")
        rel_alpha = _make_mention_relationship(
            pr_10.entity_ref, obs_alpha.entity_ref, CTX_A.observation_id
        )
        rel_beta = _make_mention_relationship(
            pr_10.entity_ref, obs_beta.entity_ref, CTX_B.observation_id
        )

        bundle_1 = EvidenceBundle(
            bundle_id="bundle_order_1",
            bundle_version="1.0.0",
            observation_contexts=(CTX_A, CTX_B, CTX_GH),
            observations=(obs_alpha, obs_beta, pr_10),
            relationships=(rel_alpha, rel_beta),
        )
        bundle_2 = EvidenceBundle(
            bundle_id="bundle_order_2",
            bundle_version="1.0.0",
            observation_contexts=(CTX_A, CTX_B, CTX_GH),
            observations=(obs_beta, obs_alpha, pr_10),
            relationships=(rel_beta, rel_alpha),
        )

        result_1 = evaluate_evidence_bundle(bundle_1)
        result_2 = evaluate_evidence_bundle(bundle_2)

        # Strengthened Oracle Assertion 1: Full canonical semantic output must match identically
        findings_1 = [_canonicalize_finding(f) for f in result_1.findings]
        findings_2 = [_canonicalize_finding(f) for f in result_2.findings]
        assert findings_1 == findings_2, (
            f"Permutation invariance violated for findings! Order 1 produced {findings_1}, "
            f"while Order 2 produced {findings_2}."
        )

        suppressed_1 = [_canonicalize_finding(s) for s in result_1.suppressed_evaluations]
        suppressed_2 = [_canonicalize_finding(s) for s in result_2.suppressed_evaluations]
        assert suppressed_1 == suppressed_2, (
            f"Permutation invariance violated for suppressed evaluations! Order 1 produced {suppressed_1}, "
            f"while Order 2 produced {suppressed_2}."
        )

    def test_scenario_e_same_state_vs_conflicting_state(self):
        """Test E: Isolation under identical state vs conflicting state across instances.

        Setup:
            - E1 (Same state): Both Alpha and Beta PROJ-123 are 'Done'. Rel targets Alpha.
            - E2 (Conflicting state): Alpha PROJ-123 is 'Done', Beta PROJ-123 is 'In Progress'. Rel targets Alpha.

        Canonical Contract Oracle:
            - In both E1 and E2, Alpha and Beta are distinct instances.
            - In both E1 and E2, Alpha PROJ-123 has an open PR #10 linked to it.
            - In both E1 and E2, Jira Alpha must evaluate to a TRIGGERED ORBIT-XB-01 finding.
            - Neither identical status nor conflicting status on Beta may suppress Alpha as AMBIGUOUS.
        """
        obs_alpha = _make_jira_observation(
            JIRA_INSTANCE_A, CTX_A, "PROJ-123", "Done", "done"
        )
        obs_beta_done = _make_jira_observation(
            JIRA_INSTANCE_B, CTX_B, "PROJ-123", "Done", "done"
        )
        obs_beta_in_progress = _make_jira_observation(
            JIRA_INSTANCE_B, CTX_B, "PROJ-123", "In Progress", "in_progress"
        )
        pr_10 = _make_pr_observation(10, state="open")
        rel_alpha = _make_mention_relationship(
            pr_10.entity_ref, obs_alpha.entity_ref, CTX_A.observation_id
        )

        bundle_e1 = EvidenceBundle(
            bundle_id="bundle_e1",
            bundle_version="1.0.0",
            observation_contexts=(CTX_A, CTX_B, CTX_GH),
            observations=(obs_alpha, obs_beta_done, pr_10),
            relationships=(rel_alpha,),
        )
        bundle_e2 = EvidenceBundle(
            bundle_id="bundle_e2",
            bundle_version="1.0.0",
            observation_contexts=(CTX_A, CTX_B, CTX_GH),
            observations=(obs_alpha, obs_beta_in_progress, pr_10),
            relationships=(rel_alpha,),
        )

        result_e1 = evaluate_evidence_bundle(bundle_e1)
        result_e2 = evaluate_evidence_bundle(bundle_e2)

        # Oracle Assertion 1: E1 must trigger finding for Alpha
        assert len(result_e1.findings) == 1, (
            f"E1 (identical status across instances) failed to trigger finding for Alpha: "
            f"findings={len(result_e1.findings)}, suppressed={len(result_e1.suppressed_evaluations)}"
        )
        assert result_e1.findings[0].subject_ref == obs_alpha.entity_ref

        # Oracle Assertion 2: E2 must trigger finding for Alpha
        assert len(result_e2.findings) == 1, (
            f"E2 (conflicting status across instances) failed to trigger finding for Alpha: "
            f"findings={len(result_e2.findings)}, suppressed={len(result_e2.suppressed_evaluations)}"
        )
        assert result_e2.findings[0].subject_ref == obs_alpha.entity_ref

    # ── Secondary Risk Investigation Tests ───────────────────────────────────

    def test_risk3_finding_id_helper_omits_source_instance(self):
        """Risk 3 Unit Investigation: _generate_finding_id omits source_instance.

        Canonical Contract Oracle:
            - Finding IDs must uniquely identify findings across all source instances.
            - Two entities in different source instances (Jira Alpha vs Jira Beta)
              must not generate identical finding IDs for the same rule and disposition.

        Actual Implementation:
            - _generate_finding_id hashes only (rule_id, entity_kind, entity_id, corroborating_refs, disposition).
            - Omits source_instance from subject_ref and corroborating_refs.
            - Directly produces colliding finding IDs.
        """
        ref_alpha = EntityRef(
            source_instance=JIRA_INSTANCE_A,
            entity_kind="jira_issue",
            entity_id="PROJ-123",
        )
        ref_beta = EntityRef(
            source_instance=JIRA_INSTANCE_B,
            entity_kind="jira_issue",
            entity_id="PROJ-123",
        )
        pr_ref = EntityRef(
            source_instance=GITHUB_INSTANCE,
            entity_kind="github_pull_request",
            entity_id="repo/10",
        )

        fid_alpha = _generate_finding_id("ORBIT-XB-01", ref_alpha, (pr_ref,), "TRIGGERED")
        fid_beta = _generate_finding_id("ORBIT-XB-01", ref_beta, (pr_ref,), "TRIGGERED")

        # Contract Oracle Assertion: Distinct source instances must yield distinct finding IDs
        assert fid_alpha != fid_beta, (
            f"Risk 3 Confirmed at helper level: _generate_finding_id generated identical finding IDs "
            f"for distinct source instances Alpha and Beta: {fid_alpha} == {fid_beta}"
        )

    def test_risk4_finding_sort_key_helper_omits_source_instance(self):
        """Risk 4 Unit Investigation: _sort_finding_key omits source_instance.

        Canonical Contract Oracle:
            - Canonical sorting of findings must break ties using source_instance.
            - Omitting source_instance causes Python's stable sort to preserve input order,
              leading to non-deterministic / permutation-dependent output ordering.

        Actual Implementation:
            - _sort_finding_key produces (rule_id, subject_ref.entity_kind, subject_ref.entity_id, corr_key, disp, suff).
            - Omits source_instance, returning identical sort keys for Alpha and Beta.
        """
        ref_alpha = EntityRef(
            source_instance=JIRA_INSTANCE_A,
            entity_kind="jira_issue",
            entity_id="PROJ-123",
        )
        ref_beta = EntityRef(
            source_instance=JIRA_INSTANCE_B,
            entity_kind="jira_issue",
            entity_id="PROJ-123",
        )
        pr_ref = EntityRef(
            source_instance=GITHUB_INSTANCE,
            entity_kind="github_pull_request",
            entity_id="repo/10",
        )

        f_alpha = TrackBFinding(
            finding_id="finding_1",
            rule_id="ORBIT-XB-01",
            rule_version="1.0.0",
            subject_ref=ref_alpha,
            corroborating_refs=(pr_ref,),
            disposition="TRIGGERED",
            sufficiency="SUPPORTED",
            deterministic_explanation="Explanation Alpha",
            observed_facts={},
            provenance_refs=(),
        )
        f_beta = TrackBFinding(
            finding_id="finding_2",
            rule_id="ORBIT-XB-01",
            rule_version="1.0.0",
            subject_ref=ref_beta,
            corroborating_refs=(pr_ref,),
            disposition="TRIGGERED",
            sufficiency="SUPPORTED",
            deterministic_explanation="Explanation Beta",
            observed_facts={},
            provenance_refs=(),
        )

        key_alpha = _sort_finding_key(f_alpha)
        key_beta = _sort_finding_key(f_beta)

        # Contract Oracle Assertion: Distinct source instances must have distinct sort keys
        assert key_alpha != key_beta, (
            f"Risk 4 Confirmed at helper level: _sort_finding_key returned identical sort keys "
            f"for distinct source instances Alpha and Beta: {key_alpha} == {key_beta}"
        )

    def test_corroborating_reference_order_invariance(self):
        """Verification A: Corroborating reference ordering must not alter finding ID or sort key.

        When multiple corroborating references are associated with a finding,
        their permutation must produce identical finding IDs and sort keys.
        """
        ref_alpha = EntityRef(
            source_instance=JIRA_INSTANCE_A,
            entity_kind="jira_issue",
            entity_id="PROJ-123",
        )
        pr_10 = EntityRef(
            source_instance=GITHUB_INSTANCE,
            entity_kind="github_pull_request",
            entity_id="repo/10",
        )
        pr_20 = EntityRef(
            source_instance=GITHUB_INSTANCE,
            entity_kind="github_pull_request",
            entity_id="repo/20",
        )

        fid_order1 = _generate_finding_id(
            "ORBIT-XB-01", ref_alpha, (pr_10, pr_20), "TRIGGERED"
        )
        fid_order2 = _generate_finding_id(
            "ORBIT-XB-01", ref_alpha, (pr_20, pr_10), "TRIGGERED"
        )
        assert fid_order1 == fid_order2, (
            f"Finding IDs differed across corroborating reference permutations: "
            f"{fid_order1} != {fid_order2}"
        )

        f_1 = TrackBFinding(
            finding_id=fid_order1,
            rule_id="ORBIT-XB-01",
            rule_version="1.0.0",
            subject_ref=ref_alpha,
            corroborating_refs=(pr_10, pr_20),
            disposition="TRIGGERED",
            sufficiency="SUPPORTED",
            deterministic_explanation="Explanation",
            observed_facts={},
            provenance_refs=(),
        )
        f_2 = TrackBFinding(
            finding_id=fid_order2,
            rule_id="ORBIT-XB-01",
            rule_version="1.0.0",
            subject_ref=ref_alpha,
            corroborating_refs=(pr_20, pr_10),
            disposition="TRIGGERED",
            sufficiency="SUPPORTED",
            deterministic_explanation="Explanation",
            observed_facts={},
            provenance_refs=(),
        )
        key_1 = _sort_finding_key(f_1)
        key_2 = _sort_finding_key(f_2)
        assert key_1 == key_2, (
            f"Sort keys differed across corroborating reference permutations: "
            f"{key_1} != {key_2}"
        )

    def test_genuine_ambiguity_vs_cross_instance_isolation(self):
        """Verification E: Genuine ambiguity within one instance vs cross-instance isolation.

        Canonical Contract Oracle:
        - When the EXACT same canonical EntityRef has multiple observations, it MUST be suppressed as AMBIGUOUS.
        - When different instances have observations with identical keys, they MUST NOT be treated as AMBIGUOUS.
        """
        # Genuine ambiguity: two observations of Jira Alpha PROJ-123
        obs_alpha_1 = _make_jira_observation(
            JIRA_INSTANCE_A, CTX_A, "PROJ-123", "Done", "done"
        )
        obs_alpha_2 = _make_jira_observation(
            JIRA_INSTANCE_A, CTX_A, "PROJ-123", "In Progress", "in_progress"
        )
        pr_10 = _make_pr_observation(10, state="open")
        rel_alpha = _make_mention_relationship(
            pr_10.entity_ref, obs_alpha_1.entity_ref, CTX_A.observation_id
        )

        bundle_ambig = EvidenceBundle(
            bundle_id="bundle_genuine_ambiguity",
            bundle_version="1.0.0",
            observation_contexts=(CTX_A, CTX_GH),
            observations=(obs_alpha_1, obs_alpha_2, pr_10),
            relationships=(rel_alpha,),
        )
        res_ambig = evaluate_evidence_bundle(bundle_ambig)

        # Genuine ambiguity must suppress
        assert len(res_ambig.findings) == 0
        assert len(res_ambig.suppressed_evaluations) == 1
        assert res_ambig.suppressed_evaluations[0].sufficiency == "AMBIGUOUS"
        assert res_ambig.suppressed_evaluations[0].observed_facts["jira_obs_count"] == 2
