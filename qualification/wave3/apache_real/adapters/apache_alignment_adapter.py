"""Canonical CrossSystemStateAlignment adapter for Apache Jira ↔ GitHub cross-system links.

Constructs generic CrossSystemStateAlignment objects using:
    subject_ref: Jira WorkItem EntityRef
    corroborating_ref: GitHub CodeChange / Commit EntityRef
without vendor-specific field names.

Evaluates state and temporal coherence deterministically using canonical state values.
"""

from __future__ import annotations

from typing import Any

from shadow_orbit.evidence_types import (
    CodeChangeState,
    CrossSystemStateAlignment,
    CrossSystemStateComparison,
    CrossSystemTemporalComparison,
    EntityRef,
    EvidenceObservation,
    ProvenanceRef,
    WorkItemState,
)


def compute_cross_system_alignment_coherence(
    work_state: WorkItemState,
    code_state: CodeChangeState,
) -> tuple[CrossSystemStateComparison, CrossSystemTemporalComparison, str]:
    """Compute state and temporal coherence between canonical WorkItemState and CodeChangeState.

    Follows CSE-1.8 / ADR-005 rules without inferring completion or causality:
    - If PR is merged and Jira is done:
        - If merged_at <= resolved_at: COHERENT, CONSISTENT
        - If merged_at > resolved_at: INVERTED, INSUFFICIENT_EVIDENCE (post-resolution activity)
        - If timestamps missing: INDETERMINATE, INSUFFICIENT_EVIDENCE
    - If PR is closed unmerged:
        - INDETERMINATE, INSUFFICIENT_EVIDENCE (closed without merge)
    - If PR is open:
        - If Jira is done: INDETERMINATE, INSUFFICIENT_EVIDENCE (discrepancy)
        - If Jira is in progress: COHERENT, CONSISTENT
    - If code change is a commit:
        - If committed_at <= resolved_at: COHERENT, CONSISTENT
        - If committed_at > resolved_at: INVERTED, INSUFFICIENT_EVIDENCE
    """
    state_comp: CrossSystemStateComparison = "INSUFFICIENT_EVIDENCE"
    temporal_comp: CrossSystemTemporalComparison = "INDETERMINATE"
    rationale: str = ""

    if code_state.change_type in ("pull_request", "merge_request"):
        if code_state.state == "merged":
            if code_state.merged_at is not None and work_state.resolved_at is not None:
                if code_state.merged_at <= work_state.resolved_at:
                    temporal_comp = "COHERENT"
                    state_comp = "CONSISTENT"
                    rationale = "GitHub PR merged prior to or coincident with Jira issue resolution."
                else:
                    temporal_comp = "INVERTED"
                    state_comp = "INSUFFICIENT_EVIDENCE"
                    rationale = (
                        "GitHub PR merged after Jira issue resolution "
                        "(potential post-resolution activity; non-conflicting)."
                    )
            elif code_state.merged_at is not None and work_state.resolved_at is None:
                temporal_comp = "INDETERMINATE"
                state_comp = "INSUFFICIENT_EVIDENCE"
                rationale = "GitHub PR merged but Jira issue lacks resolution timestamp."
            else:
                temporal_comp = "INDETERMINATE"
                state_comp = "INSUFFICIENT_EVIDENCE"
                rationale = "GitHub PR recorded as merged but lacks explicit merged_at timestamp."
        elif code_state.state == "closed":
            temporal_comp = "INDETERMINATE"
            state_comp = "INSUFFICIENT_EVIDENCE"
            rationale = "Referenced GitHub PR closed without merge."
        elif code_state.state == "open":
            if work_state.status_category == "done":
                temporal_comp = "INDETERMINATE"
                state_comp = "INSUFFICIENT_EVIDENCE"
                rationale = (
                    "Jira issue marked done while referenced GitHub PR remains open "
                    "(lifecycle discrepancy; non-conflicting)."
                )
            else:
                temporal_comp = "COHERENT"
                state_comp = "CONSISTENT"
                rationale = "Referenced GitHub PR and Jira issue both actively in progress."
        else:
            temporal_comp = "INDETERMINATE"
            state_comp = "INSUFFICIENT_EVIDENCE"
            rationale = f"Referenced GitHub PR in state '{code_state.state}' with indeterminate lifecycle alignment."

    elif code_state.change_type == "commit":
        commit_time = code_state.committed_at
        jira_resolved = work_state.resolved_at
        jira_created = work_state.created_at

        if commit_time is not None:
            if jira_resolved is not None:
                if commit_time <= jira_resolved:
                    temporal_comp = "COHERENT"
                    state_comp = "CONSISTENT"
                    rationale = "GitHub commit timestamp precedes or coincides with Jira issue resolution."
                else:
                    temporal_comp = "INVERTED"
                    state_comp = "INSUFFICIENT_EVIDENCE"
                    rationale = "GitHub commit postdates Jira issue resolution (potential post-resolution activity; non-conflicting)."
            elif jira_created is not None and commit_time >= jira_created:
                temporal_comp = "COHERENT"
                state_comp = "CONSISTENT"
                rationale = "GitHub commit committed during active Jira issue lifecycle."
            else:
                temporal_comp = "INVERTED"
                state_comp = "INSUFFICIENT_EVIDENCE"
                rationale = "GitHub commit predates Jira issue creation."
        else:
            temporal_comp = "INDETERMINATE"
            state_comp = "INSUFFICIENT_EVIDENCE"
            rationale = "GitHub commit timestamp missing; temporal comparison indeterminate."

    return state_comp, temporal_comp, rationale


def build_cross_system_alignment(
    subject_obs: EvidenceObservation,
    corroborating_obs: EvidenceObservation,
    linkage_type: str,
    custom_rationale: str | None = None,
    provenance_refs: tuple[ProvenanceRef, ...] | None = None,
) -> CrossSystemStateAlignment:
    """Build a provider-neutral CrossSystemStateAlignment between two observations.

    Parameters
    ----------
    subject_obs:
        The primary work item observation (e.g. Jira issue).
    corroborating_obs:
        The corroborating code change observation (e.g. GitHub PR or commit).
    linkage_type:
        Classification: 'DECLARED_MENTION' or 'EXPLICIT_LINK'.
    custom_rationale:
        Optional rationale override. If None, computed from state coherence.
    provenance_refs:
        Optional supporting provenance references. If None, aggregated from observations.
    """
    subject_state = subject_obs.observed_state
    corr_state = corroborating_obs.observed_state

    if isinstance(subject_state, WorkItemState) and isinstance(corr_state, CodeChangeState):
        state_comp, temporal_comp, auto_rationale = compute_cross_system_alignment_coherence(
            subject_state, corr_state
        )
    else:
        state_comp = "INSUFFICIENT_EVIDENCE"
        temporal_comp = "INDETERMINATE"
        auto_rationale = "Observations are not canonical WorkItemState / CodeChangeState."

    rationale = custom_rationale if custom_rationale is not None else auto_rationale

    if provenance_refs is not None:
        prov = provenance_refs
    else:
        # Default to corroborating observation's provenance refs to satisfy
        # validate_evidence_bundle (which validates a.provenance_refs against a.corroborating_ref)
        prov = corroborating_obs.provenance_refs

    return CrossSystemStateAlignment(
        subject_ref=subject_obs.entity_ref,
        corroborating_ref=corroborating_obs.entity_ref,
        relationship_kind=linkage_type,
        state_comparison=state_comp,
        temporal_comparison=temporal_comp,
        rationale=rationale,
        provenance_refs=prov,
    )
