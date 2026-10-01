"""Pure, deterministic, offline Track B EvidenceBundle evaluation engine.

Evaluates multi-source software delivery health across Jira and GitHub evidence
directly from an assembled and validated EvidenceBundle.

This module belongs strictly to Track B.  It does NOT import, call, or wrap
Track A (evaluate_week_one_rules, calculate_supporting_facts).  Track A remains
completely frozen.

Permutation invariance:
    Equivalent inputs in any permutation produce bit-for-bit identical results.
    Finding IDs and evaluation IDs are canonically derived via deterministic
    SHA-256 digests; no random UUIDs or system clocks are accessed.

Anti-inference rules enforced:
    - No Cartesian cross-system pairing (relationship-bound only).
    - No transitive association promotion.
    - No developer/actor identity matching.
    - No completion inference (merging code != ticket completed).
    - Temporal inversion != contradiction (OBSERVATIONAL ONLY).
    - Missing evidence is never converted to a negative finding.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
from typing import Any, Literal

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
    QualityIssue,
    UnresolvedReference,
    WorkItemState,
    _serialize_datetime,
    as_code_change_state,
    as_work_item_state,
    serialize_entity_ref,
    serialize_provenance_ref,
    serialize_quality_issue,
)
from shadow_orbit.temporal import elapsed_complete_days
from shadow_orbit.types import ReviewPeriod


FindingSufficiency = Literal[
    "PROVEN",
    "SUPPORTED",
    "INSUFFICIENT_EVIDENCE",
    "CONFLICTING",
    "STALE",
    "UNRESOLVED",
    "AMBIGUOUS",
]

FindingDisposition = Literal[
    "TRIGGERED",
    "SUPPRESSED",
    "INSUFFICIENT_EVIDENCE",
]


@dataclass(frozen=True, slots=True)
class TrackBFinding:
    """A deterministic multi-system delivery-health finding produced by Track B."""

    finding_id: str
    rule_id: str
    rule_version: str
    subject_ref: EntityRef
    corroborating_refs: tuple[EntityRef, ...]
    disposition: FindingDisposition
    sufficiency: FindingSufficiency
    deterministic_explanation: str
    observed_facts: dict[str, Any]
    provenance_refs: tuple[ProvenanceRef, ...]
    quality_issues: tuple[QualityIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class EvidenceBundleEvaluationResult:
    """Immutable result of Track B EvidenceBundle evaluation."""

    evaluation_id: str
    bundle_id: str
    evaluated_at: str
    findings: tuple[TrackBFinding, ...]
    suppressed_evaluations: tuple[TrackBFinding, ...]
    summary: dict[str, Any]


# ── Canonical Sorting & Deterministic Identity ───────────────────────────────


def _sort_provenance_key(p: ProvenanceRef) -> tuple[str, str, str, str, str]:
    instance_id = p.source_instance.instance_id if p.source_instance else ""
    return (
        p.fixture_id or "",
        p.record_locator or "",
        p.source_field_path or "",
        p.observation_id or "",
        instance_id,
    )


def _sort_quality_issue_key(q: QualityIssue) -> tuple[str, str, str, str]:
    ref_key = ""
    if q.subject_ref is not None:
        inst = (
            q.subject_ref.source_instance.instance_id
            if q.subject_ref.source_instance
            else ""
        )
        ref_key = f"{inst}:{q.subject_ref.entity_kind}:{q.subject_ref.entity_id}"
    return (q.code, q.message, q.subject_scope or "", ref_key)


def _sort_finding_key(f: TrackBFinding) -> tuple[str, str, str, str, str, str]:
    corr_key = ":".join(
        f"{c.entity_kind}:{c.entity_id}" for c in f.corroborating_refs
    )
    return (
        f.rule_id,
        f.subject_ref.entity_kind,
        f.subject_ref.entity_id,
        corr_key,
        f.disposition,
        f.sufficiency,
    )


def _merge_provenance(
    *prov_tuples: tuple[ProvenanceRef, ...],
) -> tuple[ProvenanceRef, ...]:
    dedup: dict[tuple[str, str, str, str, str], ProvenanceRef] = {}
    for p_tup in prov_tuples:
        for p in p_tup:
            k = _sort_provenance_key(p)
            if k not in dedup:
                dedup[k] = p
    return tuple(sorted(dedup.values(), key=_sort_provenance_key))


def _merge_quality_issues(
    *qi_tuples: tuple[QualityIssue, ...],
) -> tuple[QualityIssue, ...]:
    dedup: dict[tuple[str, str, str, str], QualityIssue] = {}
    for q_tup in qi_tuples:
        for q in q_tup:
            k = _sort_quality_issue_key(q)
            if k not in dedup:
                dedup[k] = q
    return tuple(sorted(dedup.values(), key=_sort_quality_issue_key))


def _generate_finding_id(
    rule_id: str,
    subject_ref: EntityRef,
    corroborating_refs: tuple[EntityRef, ...],
    disposition: str,
) -> str:
    corr_str = ":".join(
        f"{c.entity_kind}:{c.entity_id}" for c in corroborating_refs
    )
    raw = (
        f"{rule_id}:{subject_ref.entity_kind}:{subject_ref.entity_id}:"
        f"{corr_str}:{disposition}"
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"finding_{rule_id.lower().replace('-', '_')}_{digest}"


def _generate_evaluation_id(
    bundle_id: str,
    findings: tuple[TrackBFinding, ...],
    suppressed: tuple[TrackBFinding, ...],
) -> str:
    all_f_ids = ":".join(f.finding_id for f in findings)
    all_s_ids = ":".join(s.finding_id for s in suppressed)
    raw = f"{bundle_id}:{all_f_ids}:{all_s_ids}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"eval_{bundle_id}_{digest}"


# ── Primary Evaluator ────────────────────────────────────────────────────────


def evaluate_evidence_bundle(
    bundle: EvidenceBundle,
    review_period: ReviewPeriod | None = None,
) -> EvidenceBundleEvaluationResult:
    """Evaluate an EvidenceBundle and produce deterministic Track B findings.

    Scope is strictly limited to authorized Wave 5 candidate rules:
        - ORBIT-XB-01: UNMERGED_PR_ON_RESOLVED_ISSUE
        - ORBIT-XB-02: MERGED_PR_ON_UNRESOLVED_ISSUE
        - ORBIT-XB-03: POST_RESOLUTION_WORK_ACTIVITY (Observational only)

    XB-04 through XB-08 are NOT evaluated by this function.

    Parameters
    ----------
    bundle:
        The validated EvidenceBundle container.
    review_period:
        Optional ReviewPeriod for scoping metadata.

    Returns
    -------
    EvidenceBundleEvaluationResult
        Immutable, deterministic evaluation result.
    """
    # ── 1. Index Observations by (entity_kind, entity_id) ────────────
    # Multiple observations for same entity identity indicate ambiguity.
    obs_by_key: dict[tuple[str, str], list[EvidenceObservation]] = {}
    for obs in bundle.observations:
        k = (obs.entity_ref.entity_kind, obs.entity_ref.entity_id)
        obs_by_key.setdefault(k, []).append(obs)

    # ── 2. Index Cross-System Relationships ──────────────────────────
    # Map (subject_ref, corroborating_ref) -> list of EvidenceRelationship
    rels_by_pair: dict[tuple[EntityRef, EntityRef], list[EvidenceRelationship]] = {}
    for rel in bundle.relationships:
        if (
            rel.subject_ref.entity_kind in ("jira_issue", "work_item")
            and (rel.object_ref.entity_kind.startswith("github_") or rel.object_ref.entity_kind in ("code_change", "commit", "branch"))
        ):
            pair = (rel.subject_ref, rel.object_ref)
            rels_by_pair.setdefault(pair, []).append(rel)
        elif (
            rel.object_ref.entity_kind in ("jira_issue", "work_item")
            and (rel.subject_ref.entity_kind.startswith("github_") or rel.subject_ref.entity_kind in ("code_change", "commit", "branch"))
        ):
            pair = (rel.object_ref, rel.subject_ref)
            rels_by_pair.setdefault(pair, []).append(rel)
        elif (
            rel.subject_ref.source_instance.source_kind != rel.object_ref.source_instance.source_kind
        ):
            pair = (rel.subject_ref, rel.object_ref)
            rels_by_pair.setdefault(pair, []).append(rel)

    # ── 3. Index Cross-System Alignments ─────────────────────────────
    # Map (subject_ref, corroborating_ref) -> list of CrossSystemStateAlignment
    alignments_by_pair: dict[
        tuple[EntityRef, EntityRef], list[CrossSystemStateAlignment]
    ] = {}
    for align in bundle.cross_system_alignments:
        pair = (align.subject_ref, align.corroborating_ref)
        alignments_by_pair.setdefault(pair, []).append(align)

    # ── 4. Collect Established Candidate Pairs (Strictly Anti-Cartesian)
    # A pair is evaluated IF AND ONLY IF an explicit relationship or precomputed
    # alignment exists in the bundle.  Zero cross-system pairing for unlinked entities.
    candidate_pairs: dict[
        tuple[str, str, str, str], tuple[EntityRef, EntityRef]
    ] = {}
    for pair in alignments_by_pair:
        k = (
            pair[0].entity_kind,
            pair[0].entity_id,
            pair[1].entity_kind,
            pair[1].entity_id,
        )
        candidate_pairs[k] = pair

    for pair, rel_list in rels_by_pair.items():
        # Only accept established mention or explicit link relationships
        has_authorized_rel = any(
            r.kind in {"mentions", "explicit_link"}
            or r.basis in {"declared_mention", "explicit_metadata"}
            for r in rel_list
        )
        if has_authorized_rel:
            k = (
                pair[0].entity_kind,
                pair[0].entity_id,
                pair[1].entity_kind,
                pair[1].entity_id,
            )
            candidate_pairs.setdefault(k, pair)

    findings: list[TrackBFinding] = []
    suppressed_evaluations: list[TrackBFinding] = []

    # ── 5. Evaluate Established Pairs ────────────────────────────────
    for pair in candidate_pairs.values():
        subject_ref, corr_ref = pair

        matching_rels = rels_by_pair.get(pair, [])
        matching_alignments = alignments_by_pair.get(pair, [])

        # Determine sufficiency basis:
        # EXPLICIT_LINK / explicit_metadata -> PROVEN
        # DECLARED_MENTION / mentions       -> SUPPORTED
        is_explicit = any(
            r.kind == "explicit_link" or r.basis == "explicit_metadata"
            for r in matching_rels
        ) or any(
            a.relationship_kind == "explicit_link"
            for a in matching_alignments
        )

        base_sufficiency: FindingSufficiency = (
            "PROVEN" if is_explicit else "SUPPORTED"
        )
        rel_basis = "explicit_metadata" if is_explicit else "declared_mention"
        rel_kind = "explicit_link" if is_explicit else "declared_mention"

        # Collect relationship provenance
        rel_prov: list[ProvenanceRef] = []
        for r in matching_rels:
            rel_prov.extend(r.provenance_refs)
        for a in matching_alignments:
            rel_prov.extend(a.provenance_refs)

        # Lookup observations
        subject_obs_list = obs_by_key.get(
            (subject_ref.entity_kind, subject_ref.entity_id), []
        )
        corr_obs_list = obs_by_key.get(
            (corr_ref.entity_kind, corr_ref.entity_id), []
        )

        # Handle missing subject observation
        if not subject_obs_list:
            if corr_ref.entity_kind in ("github_pull_request", "code_change"):
                fid = _generate_finding_id(
                    "ORBIT-XB-01", subject_ref, (corr_ref,), "INSUFFICIENT_EVIDENCE"
                )
                combined_p = _merge_provenance(
                    tuple(rel_prov),
                    *(o.provenance_refs for o in corr_obs_list),
                )
                is_jira = subject_ref.entity_kind == "jira_issue" or subject_ref.source_instance.source_kind == "jira"
                desc = (
                    f"Referenced Jira issue {subject_ref.entity_id} was not observed in the evidence bundle."
                    if is_jira
                    else f"Referenced work item {subject_ref.entity_id} was not observed in the evidence bundle."
                )
                suppressed_evaluations.append(
                    TrackBFinding(
                        finding_id=fid,
                        rule_id="ORBIT-XB-01",
                        rule_version="1.0.0",
                        subject_ref=subject_ref,
                        corroborating_refs=(corr_ref,),
                        disposition="INSUFFICIENT_EVIDENCE",
                        sufficiency="UNRESOLVED",
                        deterministic_explanation=desc,
                        observed_facts={
                            "missing_entity": f"{subject_ref.entity_kind}:{subject_ref.entity_id}",
                            "referencing_entity": f"{corr_ref.entity_kind}:{corr_ref.entity_id}",
                        },
                        provenance_refs=combined_p,
                    )
                )
            continue

        # Handle missing corroborating observation
        if not corr_obs_list:
            if corr_ref.entity_kind in ("github_pull_request", "code_change"):
                fid = _generate_finding_id(
                    "ORBIT-XB-01", subject_ref, (corr_ref,), "INSUFFICIENT_EVIDENCE"
                )
                combined_p = _merge_provenance(
                    tuple(rel_prov),
                    *(o.provenance_refs for o in subject_obs_list),
                )
                is_gh = corr_ref.entity_kind.startswith("github_") or corr_ref.source_instance.source_kind == "github"
                desc = (
                    f"Referenced GitHub entity {corr_ref.entity_id} was not observed in the evidence bundle."
                    if is_gh
                    else f"Referenced code change {corr_ref.entity_id} was not observed in the evidence bundle."
                )
                suppressed_evaluations.append(
                    TrackBFinding(
                        finding_id=fid,
                        rule_id="ORBIT-XB-01",
                        rule_version="1.0.0",
                        subject_ref=subject_ref,
                        corroborating_refs=(corr_ref,),
                        disposition="INSUFFICIENT_EVIDENCE",
                        sufficiency="UNRESOLVED",
                        deterministic_explanation=desc,
                        observed_facts={
                            "missing_entity": f"{corr_ref.entity_kind}:{corr_ref.entity_id}",
                            "referencing_entity": f"{subject_ref.entity_kind}:{subject_ref.entity_id}",
                        },
                        provenance_refs=combined_p,
                    )
                )
            continue

        # Handle ambiguous observations (> 1 match)
        if len(subject_obs_list) > 1 or len(corr_obs_list) > 1:
            fid = _generate_finding_id(
                "ORBIT-XB-01", subject_ref, (corr_ref,), "INSUFFICIENT_EVIDENCE"
            )
            combined_p = _merge_provenance(
                tuple(rel_prov),
                *(o.provenance_refs for o in subject_obs_list),
                *(o.provenance_refs for o in corr_obs_list),
            )
            obs_facts: dict[str, Any] = {}
            if subject_ref.source_instance.source_kind == "jira" or subject_ref.entity_kind == "jira_issue":
                obs_facts["jira_obs_count"] = len(subject_obs_list)
            else:
                obs_facts["subject_obs_count"] = len(subject_obs_list)

            if corr_ref.source_instance.source_kind == "github" or corr_ref.entity_kind.startswith("github_"):
                obs_facts["github_obs_count"] = len(corr_obs_list)
            else:
                obs_facts["corroborating_obs_count"] = len(corr_obs_list)

            suppressed_evaluations.append(
                TrackBFinding(
                    finding_id=fid,
                    rule_id="ORBIT-XB-01",
                    rule_version="1.0.0",
                    subject_ref=subject_ref,
                    corroborating_refs=(corr_ref,),
                    disposition="INSUFFICIENT_EVIDENCE",
                    sufficiency="AMBIGUOUS",
                    deterministic_explanation=(
                        f"Multiple candidate observations found for pair "
                        f"({subject_ref.entity_id}, {corr_ref.entity_id})."
                    ),
                    observed_facts=obs_facts,
                    provenance_refs=combined_p,
                )
            )
            continue

        subject_obs = subject_obs_list[0]
        corr_obs = corr_obs_list[0]

        combined_prov = _merge_provenance(
            subject_obs.provenance_refs,
            corr_obs.provenance_refs,
            tuple(rel_prov),
        )
        combined_qi = _merge_quality_issues(
            subject_obs.quality_issues,
            corr_obs.quality_issues,
        )

        is_stale = any(
            q.code in ("STALE", "stale")
            or (q.code == "invalid" and q.subject_scope in ("provenance:temporal", "temporal:staleness"))
            for q in combined_qi
        )

        work_state = as_work_item_state(subject_obs.observed_state)
        code_state = as_code_change_state(corr_obs.observed_state)
        is_raw_jira = isinstance(subject_obs.observed_state, JiraIssueState)
        is_raw_gh_pr = isinstance(corr_obs.observed_state, GitHubPullRequestState)

        # ── 5.1 Evaluate ORBIT-XB-01: UNMERGED_PR_ON_RESOLVED_ISSUE ──
        is_pr_like = corr_ref.entity_kind == "github_pull_request" or (
            corr_ref.entity_kind == "code_change"
            and (code_state is None or code_state.change_type in ("pull_request", "merge_request", "revision"))
        )
        if is_pr_like:
            if work_state is None or code_state is None:
                fid = _generate_finding_id(
                    "ORBIT-XB-01", subject_ref, (corr_ref,), "INSUFFICIENT_EVIDENCE"
                )
                suppressed_evaluations.append(
                    TrackBFinding(
                        finding_id=fid,
                        rule_id="ORBIT-XB-01",
                        rule_version="1.0.0",
                        subject_ref=subject_ref,
                        corroborating_refs=(corr_ref,),
                        disposition="INSUFFICIENT_EVIDENCE",
                        sufficiency="INSUFFICIENT_EVIDENCE",
                        deterministic_explanation=(
                            f"Observation state types for pair ({subject_ref.entity_id}, "
                            f"{corr_ref.entity_id}) are missing or incompatible."
                        ),
                        observed_facts={},
                        provenance_refs=combined_prov,
                        quality_issues=combined_qi,
                    )
                )
            elif code_state.state is None or code_state.state not in {
                "open",
                "closed",
                "merged",
            }:
                fid = _generate_finding_id(
                    "ORBIT-XB-01", subject_ref, (corr_ref,), "INSUFFICIENT_EVIDENCE"
                )
                prefix = "GitHub PR #" if is_raw_gh_pr else "Code change #"
                fact_key = "pr_state" if is_raw_gh_pr else "code_change_state"
                ident = code_state.number if is_raw_gh_pr else code_state.identifier
                suppressed_evaluations.append(
                    TrackBFinding(
                        finding_id=fid,
                        rule_id="ORBIT-XB-01",
                        rule_version="1.0.0",
                        subject_ref=subject_ref,
                        corroborating_refs=(corr_ref,),
                        disposition="INSUFFICIENT_EVIDENCE",
                        sufficiency="INSUFFICIENT_EVIDENCE",
                        deterministic_explanation=(
                            f"{prefix}{ident} state is missing or indeterminate."
                        ),
                        observed_facts={fact_key: code_state.state},
                        provenance_refs=combined_prov,
                        quality_issues=combined_qi,
                    )
                )
            elif work_state.status_category == "done" and code_state.state == "open":
                fid = _generate_finding_id(
                    "ORBIT-XB-01", subject_ref, (corr_ref,), "TRIGGERED"
                )
                finding_sufficiency = "STALE" if is_stale else base_sufficiency
                finding_disposition = (
                    "SUPPRESSED" if is_stale else "TRIGGERED"
                )
                if is_raw_jira and is_raw_gh_pr:
                    explanation = (
                        f"Jira issue {work_state.key} is marked "
                        f"'{work_state.source_status}' (status category: done) "
                        f"while referenced GitHub PR #{code_state.number} "
                        f"('{code_state.title}') remains open. This records a "
                        "cross-system lifecycle state discrepancy without inferring "
                        "defect or causality."
                    )
                    facts = {
                        "jira_key": work_state.key,
                        "jira_status": work_state.source_status,
                        "jira_status_category": work_state.status_category,
                        "pr_number": code_state.number,
                        "pr_title": code_state.title,
                        "pr_state": code_state.state,
                        "relationship_kind": rel_kind,
                        "relationship_basis": rel_basis,
                    }
                else:
                    explanation = (
                        f"Work item {work_state.key} is marked "
                        f"'{work_state.source_status}' (status category: done) "
                        f"while referenced code change #{code_state.identifier} "
                        f"('{code_state.title}') remains open. This records a "
                        "cross-system lifecycle state discrepancy without inferring "
                        "defect or causality."
                    )
                    facts = {
                        "work_item_key": work_state.key,
                        "work_item_status": work_state.source_status,
                        "work_item_status_category": work_state.status_category,
                        "code_change_identifier": code_state.identifier,
                        "code_change_number": code_state.number,
                        "code_change_title": code_state.title,
                        "code_change_state": code_state.state,
                        "relationship_kind": rel_kind,
                        "relationship_basis": rel_basis,
                    }

                finding = TrackBFinding(
                    finding_id=fid,
                    rule_id="ORBIT-XB-01",
                    rule_version="1.0.0",
                    subject_ref=subject_ref,
                    corroborating_refs=(corr_ref,),
                    disposition=finding_disposition,
                    sufficiency=finding_sufficiency,
                    deterministic_explanation=explanation,
                    observed_facts=facts,
                    provenance_refs=combined_prov,
                    quality_issues=combined_qi,
                )
                if is_stale:
                    suppressed_evaluations.append(finding)
                else:
                    findings.append(finding)

        # ── 5.2 Evaluate ORBIT-XB-02: MERGED_PR_ON_UNRESOLVED_ISSUE ──
        if is_pr_like:
            if work_state is not None and code_state is not None:
                if code_state.state == "merged":
                    if work_state.status_category in {
                        "todo",
                        "in_progress",
                        "blocked",
                    }:
                        if code_state.merged_at is None:
                            fid = _generate_finding_id(
                                "ORBIT-XB-02",
                                subject_ref,
                                (corr_ref,),
                                "INSUFFICIENT_EVIDENCE",
                            )
                            if is_raw_jira and is_raw_gh_pr:
                                explanation = (
                                    f"GitHub PR #{code_state.number} is marked merged "
                                    f"while referenced Jira issue {work_state.key} "
                                    f"remains '{work_state.source_status}', but PR "
                                    "merged_at timestamp is missing."
                                )
                                facts = {
                                    "jira_key": work_state.key,
                                    "jira_status": work_state.source_status,
                                    "jira_status_category": work_state.status_category,
                                    "pr_number": code_state.number,
                                    "pr_state": code_state.state,
                                    "pr_merged_at": None,
                                }
                            else:
                                explanation = (
                                    f"Code change #{code_state.identifier} is marked merged "
                                    f"while referenced work item {work_state.key} "
                                    f"remains '{work_state.source_status}', but "
                                    "merged_at timestamp is missing."
                                )
                                facts = {
                                    "work_item_key": work_state.key,
                                    "work_item_status": work_state.source_status,
                                    "work_item_status_category": work_state.status_category,
                                    "code_change_identifier": code_state.identifier,
                                    "code_change_number": code_state.number,
                                    "code_change_state": code_state.state,
                                    "code_change_merged_at": None,
                                }
                            suppressed_evaluations.append(
                                TrackBFinding(
                                    finding_id=fid,
                                    rule_id="ORBIT-XB-02",
                                    rule_version="1.0.0",
                                    subject_ref=subject_ref,
                                    corroborating_refs=(corr_ref,),
                                    disposition="INSUFFICIENT_EVIDENCE",
                                    sufficiency="INSUFFICIENT_EVIDENCE",
                                    deterministic_explanation=explanation,
                                    observed_facts=facts,
                                    provenance_refs=combined_prov,
                                    quality_issues=combined_qi,
                                )
                            )
                        else:
                            fid = _generate_finding_id(
                                "ORBIT-XB-02", subject_ref, (corr_ref,), "TRIGGERED"
                            )
                            finding_sufficiency = (
                                "STALE" if is_stale else base_sufficiency
                            )
                            finding_disposition = (
                                "SUPPRESSED" if is_stale else "TRIGGERED"
                            )
                            if is_raw_jira and is_raw_gh_pr:
                                explanation = (
                                    f"GitHub PR #{code_state.number} ('{code_state.title}') "
                                    f"is merged while referenced Jira issue {work_state.key} "
                                    f"remains '{work_state.source_status}' "
                                    f"(status category: {work_state.status_category}). "
                                    "This records a cross-system lifecycle tracking lag; "
                                    "merging code does not prove issue completion."
                                )
                                facts = {
                                    "jira_key": work_state.key,
                                    "jira_status": work_state.source_status,
                                    "jira_status_category": work_state.status_category,
                                    "pr_number": code_state.number,
                                    "pr_title": code_state.title,
                                    "pr_state": code_state.state,
                                    "pr_merged_at": _serialize_datetime(
                                        code_state.merged_at
                                    ),
                                    "relationship_kind": rel_kind,
                                    "relationship_basis": rel_basis,
                                }
                            else:
                                explanation = (
                                    f"Code change #{code_state.identifier} ('{code_state.title}') "
                                    f"is merged while referenced work item {work_state.key} "
                                    f"remains '{work_state.source_status}' "
                                    f"(status category: {work_state.status_category}). "
                                    "This records a cross-system lifecycle tracking lag; "
                                    "merging code does not prove issue completion."
                                )
                                facts = {
                                    "work_item_key": work_state.key,
                                    "work_item_status": work_state.source_status,
                                    "work_item_status_category": work_state.status_category,
                                    "code_change_identifier": code_state.identifier,
                                    "code_change_number": code_state.number,
                                    "code_change_title": code_state.title,
                                    "code_change_state": code_state.state,
                                    "code_change_merged_at": _serialize_datetime(
                                        code_state.merged_at
                                    ),
                                    "relationship_kind": rel_kind,
                                    "relationship_basis": rel_basis,
                                }
                            finding = TrackBFinding(
                                finding_id=fid,
                                rule_id="ORBIT-XB-02",
                                rule_version="1.0.0",
                                subject_ref=subject_ref,
                                corroborating_refs=(corr_ref,),
                                disposition=finding_disposition,
                                sufficiency=finding_sufficiency,
                                deterministic_explanation=explanation,
                                observed_facts=facts,
                                provenance_refs=combined_prov,
                                quality_issues=combined_qi,
                            )
                            if is_stale:
                                suppressed_evaluations.append(finding)
                            else:
                                findings.append(finding)
                    elif work_state.status_category != "done":
                        # Unknown or unmapped Jira status category
                        fid = _generate_finding_id(
                            "ORBIT-XB-02",
                            subject_ref,
                            (corr_ref,),
                            "INSUFFICIENT_EVIDENCE",
                        )
                        if is_raw_jira and is_raw_gh_pr:
                            explanation = (
                                f"GitHub PR #{code_state.number} is merged, but Jira issue "
                                f"{work_state.key} status category '{work_state.status_category}' "
                                "is indeterminate or unmapped."
                            )
                            facts = {
                                "jira_key": work_state.key,
                                "jira_status": work_state.source_status,
                                "jira_status_category": work_state.status_category,
                                "pr_number": code_state.number,
                                "pr_state": code_state.state,
                            }
                        else:
                            explanation = (
                                f"Code change #{code_state.identifier} is merged, but work item "
                                f"{work_state.key} status category '{work_state.status_category}' "
                                "is indeterminate or unmapped."
                            )
                            facts = {
                                "work_item_key": work_state.key,
                                "work_item_status": work_state.source_status,
                                "work_item_status_category": work_state.status_category,
                                "code_change_identifier": code_state.identifier,
                                "code_change_number": code_state.number,
                                "code_change_state": code_state.state,
                            }
                        suppressed_evaluations.append(
                            TrackBFinding(
                                finding_id=fid,
                                rule_id="ORBIT-XB-02",
                                rule_version="1.0.0",
                                subject_ref=subject_ref,
                                corroborating_refs=(corr_ref,),
                                disposition="INSUFFICIENT_EVIDENCE",
                                sufficiency="INSUFFICIENT_EVIDENCE",
                                deterministic_explanation=explanation,
                                observed_facts=facts,
                                provenance_refs=combined_prov,
                                quality_issues=combined_qi,
                            )
                        )

        # ── 5.3 Evaluate ORBIT-XB-03: POST_RESOLUTION_WORK_ACTIVITY ──
        # OBSERVATIONAL ONLY. Never CONFLICTING. Never asserts defect or fault.
        if work_state is not None:
            activity_dt: datetime | None = None
            activity_kind: str | None = None
            activity_desc: str | None = None
            activity_evaluated = False

            raw_corr_state = corr_obs.observed_state

            if code_state is not None:
                if code_state.change_type == "commit" or (code_state.committed_at is not None and code_state.merged_at is None):
                    activity_dt = code_state.committed_at
                    activity_kind = "commit"
                    activity_desc = f"commit {code_state.identifier[:8]}"
                    activity_evaluated = True
                elif code_state.state == "merged" or code_state.merged_at is not None:
                    activity_dt = code_state.merged_at
                    activity_kind = "pull request merge" if is_raw_gh_pr else "code change merge"
                    activity_desc = (
                        f"PR #{code_state.number} ('{code_state.title}')"
                        if is_raw_gh_pr
                        else f"code change #{code_state.identifier} ('{code_state.title}')"
                    )
                    activity_evaluated = True
            elif isinstance(raw_corr_state, GitHubCommitState):
                activity_dt = raw_corr_state.committed_at
                activity_kind = "commit"
                activity_desc = f"commit {raw_corr_state.sha[:8]}"
                activity_evaluated = True

            if activity_evaluated:
                if work_state.resolved_at is not None:
                    if activity_dt is not None:
                        if activity_dt > work_state.resolved_at:
                            # Observed temporal inversion -> TRIGGERED
                            days = elapsed_complete_days(
                                work_state.resolved_at, activity_dt
                            )
                            fid = _generate_finding_id(
                                "ORBIT-XB-03", subject_ref, (corr_ref,), "TRIGGERED"
                            )
                            finding_sufficiency = (
                                "STALE" if is_stale else base_sufficiency
                            )
                            finding_disposition = (
                                "SUPPRESSED" if is_stale else "TRIGGERED"
                            )
                            if is_raw_jira and (is_raw_gh_pr or isinstance(raw_corr_state, GitHubCommitState)):
                                explanation = (
                                    f"GitHub {activity_kind} ({activity_desc}) occurred at "
                                    f"{_serialize_datetime(activity_dt)} after Jira issue {work_state.key} "
                                    f"was recorded as resolved at {_serialize_datetime(work_state.resolved_at)} "
                                    f"({days} complete days post-resolution). This is an observational temporal finding."
                                )
                                facts = {
                                    "jira_key": work_state.key,
                                    "jira_resolved_at": _serialize_datetime(
                                        work_state.resolved_at
                                    ),
                                    "github_entity_kind": corr_ref.entity_kind,
                                    "github_entity_id": corr_ref.entity_id,
                                    "github_activity_kind": activity_kind,
                                    "github_activity_at": _serialize_datetime(
                                        activity_dt
                                    ),
                                    "elapsed_complete_days_post_resolution": days,
                                    "temporal_comparison": "INVERTED",
                                    "relationship_kind": rel_kind,
                                    "relationship_basis": rel_basis,
                                }
                            else:
                                explanation = (
                                    f"Corroborating {activity_kind} ({activity_desc}) occurred at "
                                    f"{_serialize_datetime(activity_dt)} after work item {work_state.key} "
                                    f"was recorded as resolved at {_serialize_datetime(work_state.resolved_at)} "
                                    f"({days} complete days post-resolution). This is an observational temporal finding."
                                )
                                facts = {
                                    "work_item_key": work_state.key,
                                    "work_item_resolved_at": _serialize_datetime(
                                        work_state.resolved_at
                                    ),
                                    "corroborating_entity_kind": corr_ref.entity_kind,
                                    "corroborating_entity_id": corr_ref.entity_id,
                                    "corroborating_activity_kind": activity_kind,
                                    "corroborating_activity_at": _serialize_datetime(
                                        activity_dt
                                    ),
                                    "elapsed_complete_days_post_resolution": days,
                                    "temporal_comparison": "INVERTED",
                                    "relationship_kind": rel_kind,
                                    "relationship_basis": rel_basis,
                                }
                            finding = TrackBFinding(
                                finding_id=fid,
                                rule_id="ORBIT-XB-03",
                                rule_version="1.0.0",
                                subject_ref=subject_ref,
                                corroborating_refs=(corr_ref,),
                                disposition=finding_disposition,
                                sufficiency=finding_sufficiency,
                                deterministic_explanation=explanation,
                                observed_facts=facts,
                                provenance_refs=combined_prov,
                                quality_issues=combined_qi,
                            )
                            if is_stale:
                                suppressed_evaluations.append(finding)
                            else:
                                findings.append(finding)
                        # else: activity_dt <= resolved_at is COHERENT (no inversion finding)

                    else:
                        # Required activity timestamp is missing
                        fid = _generate_finding_id(
                            "ORBIT-XB-03",
                            subject_ref,
                            (corr_ref,),
                            "INSUFFICIENT_EVIDENCE",
                        )
                        if is_raw_jira and (is_raw_gh_pr or isinstance(raw_corr_state, GitHubCommitState)):
                            explanation = (
                                f"Jira issue {work_state.key} was recorded as resolved at "
                                f"{_serialize_datetime(work_state.resolved_at)}, but associated "
                                f"GitHub {activity_kind} activity timestamp is missing."
                            )
                            facts = {
                                "jira_key": work_state.key,
                                "jira_resolved_at": _serialize_datetime(
                                    work_state.resolved_at
                                ),
                                "github_entity_kind": corr_ref.entity_kind,
                                "github_entity_id": corr_ref.entity_id,
                                "github_activity_kind": activity_kind,
                                "github_activity_at": None,
                            }
                        else:
                            explanation = (
                                f"Work item {work_state.key} was recorded as resolved at "
                                f"{_serialize_datetime(work_state.resolved_at)}, but associated "
                                f"corroborating {activity_kind} activity timestamp is missing."
                            )
                            facts = {
                                "work_item_key": work_state.key,
                                "work_item_resolved_at": _serialize_datetime(
                                    work_state.resolved_at
                                ),
                                "corroborating_entity_kind": corr_ref.entity_kind,
                                "corroborating_entity_id": corr_ref.entity_id,
                                "corroborating_activity_kind": activity_kind,
                                "corroborating_activity_at": None,
                            }
                        suppressed_evaluations.append(
                            TrackBFinding(
                                finding_id=fid,
                                rule_id="ORBIT-XB-03",
                                rule_version="1.0.0",
                                subject_ref=subject_ref,
                                corroborating_refs=(corr_ref,),
                                disposition="INSUFFICIENT_EVIDENCE",
                                sufficiency="INSUFFICIENT_EVIDENCE",
                                deterministic_explanation=explanation,
                                observed_facts=facts,
                                provenance_refs=combined_prov,
                                quality_issues=combined_qi,
                            )
                        )
                else:
                    # work_state resolved_at is None
                    if work_state.status_category == "done":
                        fid = _generate_finding_id(
                            "ORBIT-XB-03",
                            subject_ref,
                            (corr_ref,),
                            "INSUFFICIENT_EVIDENCE",
                        )
                        if is_raw_jira:
                            explanation = (
                                f"Jira issue {work_state.key} is marked '{work_state.source_status}' "
                                "(status category: done) but lacks an explicit resolved_at timestamp."
                            )
                            facts = {
                                "jira_key": work_state.key,
                                "jira_status": work_state.source_status,
                                "jira_status_category": work_state.status_category,
                                "jira_resolved_at": None,
                            }
                        else:
                            explanation = (
                                f"Work item {work_state.key} is marked '{work_state.source_status}' "
                                "(status category: done) but lacks an explicit resolved_at timestamp."
                            )
                            facts = {
                                "work_item_key": work_state.key,
                                "work_item_status": work_state.source_status,
                                "work_item_status_category": work_state.status_category,
                                "work_item_resolved_at": None,
                            }
                        suppressed_evaluations.append(
                            TrackBFinding(
                                finding_id=fid,
                                rule_id="ORBIT-XB-03",
                                rule_version="1.0.0",
                                subject_ref=subject_ref,
                                corroborating_refs=(corr_ref,),
                                disposition="INSUFFICIENT_EVIDENCE",
                                sufficiency="INSUFFICIENT_EVIDENCE",
                                deterministic_explanation=explanation,
                                observed_facts=facts,
                                provenance_refs=combined_prov,
                                quality_issues=combined_qi,
                            )
                        )

    # ── 6. Process Unresolved References ─────────────────────────────
    # Emits explicit INSUFFICIENT_EVIDENCE / UNRESOLVED suppressions for broken links
    for u in bundle.unresolved_references:
        if (
            u.source_ref.entity_kind in ("github_pull_request", "code_change")
            and u.target_entity_kind in ("jira_issue", "work_item")
        ):
            target_ref = EntityRef(
                source_instance=u.source_ref.source_instance,
                entity_kind=u.target_entity_kind,
                entity_id=u.target_identifier,
            )
            fid = _generate_finding_id(
                "ORBIT-XB-01",
                target_ref,
                (u.source_ref,),
                "INSUFFICIENT_EVIDENCE",
            )
            if u.target_entity_kind == "jira_issue" and u.source_ref.entity_kind == "github_pull_request":
                explanation = (
                    f"Referenced Jira issue '{u.target_identifier}' cited by GitHub PR "
                    f"#{u.source_ref.entity_id} could not be resolved in the evidence bundle "
                    f"({u.reason})."
                )
            else:
                explanation = (
                    f"Referenced work item '{u.target_identifier}' cited by code change "
                    f"#{u.source_ref.entity_id} could not be resolved in the evidence bundle "
                    f"({u.reason})."
                )
            suppressed_evaluations.append(
                TrackBFinding(
                    finding_id=fid,
                    rule_id="ORBIT-XB-01",
                    rule_version="1.0.0",
                    subject_ref=target_ref,
                    corroborating_refs=(u.source_ref,),
                    disposition="INSUFFICIENT_EVIDENCE",
                    sufficiency="UNRESOLVED",
                    deterministic_explanation=explanation,
                    observed_facts={
                        "unresolved_target_key": u.target_identifier,
                        "source_entity": f"{u.source_ref.entity_kind}:{u.source_ref.entity_id}",
                        "reason": u.reason,
                    },
                    provenance_refs=_merge_provenance(u.provenance_refs),
                )
            )

    # ── 7. Sort Findings Deterministically (Permutation Invariance) ──
    sorted_findings = tuple(sorted(findings, key=_sort_finding_key))
    sorted_suppressed = tuple(
        sorted(suppressed_evaluations, key=_sort_finding_key)
    )

    # ── 8. Compute Deterministic Evaluation ID & Timestamp ───────────
    evaluation_id = _generate_evaluation_id(
        bundle.bundle_id, sorted_findings, sorted_suppressed
    )

    if review_period is not None:
        evaluated_at = _serialize_datetime(review_period.review_cutoff_at)
    else:
        ctx_cutoffs = [
            c.source_cutoff_at
            for c in bundle.observation_contexts
            if c.source_cutoff_at is not None
        ]
        if ctx_cutoffs:
            evaluated_at = _serialize_datetime(sorted(ctx_cutoffs)[-1])
        else:
            evaluated_at = "unspecified"

    # ── 9. Compile Summary ───────────────────────────────────────────
    rule_counts: dict[str, int] = {
        "ORBIT-XB-01": 0,
        "ORBIT-XB-02": 0,
        "ORBIT-XB-03": 0,
    }
    sufficiency_counts: dict[str, int] = {
        "PROVEN": 0,
        "SUPPORTED": 0,
        "INSUFFICIENT_EVIDENCE": 0,
        "CONFLICTING": 0,
        "STALE": 0,
        "UNRESOLVED": 0,
        "AMBIGUOUS": 0,
    }
    disposition_counts: dict[str, int] = {
        "TRIGGERED": 0,
        "SUPPRESSED": 0,
        "INSUFFICIENT_EVIDENCE": 0,
    }

    for f in sorted_findings:
        rule_counts[f.rule_id] = rule_counts.get(f.rule_id, 0) + 1
        sufficiency_counts[f.sufficiency] = (
            sufficiency_counts.get(f.sufficiency, 0) + 1
        )
        disposition_counts[f.disposition] = (
            disposition_counts.get(f.disposition, 0) + 1
        )

    for s in sorted_suppressed:
        sufficiency_counts[s.sufficiency] = (
            sufficiency_counts.get(s.sufficiency, 0) + 1
        )
        disposition_counts[s.disposition] = (
            disposition_counts.get(s.disposition, 0) + 1
        )

    summary: dict[str, Any] = {
        "total_findings": len(sorted_findings),
        "total_suppressed": len(sorted_suppressed),
        "rules_evaluated": ["ORBIT-XB-01", "ORBIT-XB-02", "ORBIT-XB-03"],
        "findings_by_rule": rule_counts,
        "findings_by_sufficiency": sufficiency_counts,
        "dispositions": disposition_counts,
    }

    return EvidenceBundleEvaluationResult(
        evaluation_id=evaluation_id,
        bundle_id=bundle.bundle_id,
        evaluated_at=evaluated_at,
        findings=sorted_findings,
        suppressed_evaluations=sorted_suppressed,
        summary=summary,
    )


# ── Serialization ────────────────────────────────────────────────────────────


def serialize_track_b_finding(finding: TrackBFinding) -> dict[str, Any]:
    """Serialize a TrackBFinding to a JSON-safe dict."""
    result: dict[str, Any] = {
        "finding_id": finding.finding_id,
        "rule_id": finding.rule_id,
        "rule_version": finding.rule_version,
        "subject_ref": serialize_entity_ref(finding.subject_ref),
        "corroborating_refs": [
            serialize_entity_ref(c) for c in finding.corroborating_refs
        ],
        "disposition": finding.disposition,
        "sufficiency": finding.sufficiency,
        "deterministic_explanation": finding.deterministic_explanation,
        "observed_facts": finding.observed_facts,
        "provenance_refs": [
            serialize_provenance_ref(p) for p in finding.provenance_refs
        ],
    }
    if finding.quality_issues:
        result["quality_issues"] = [
            serialize_quality_issue(q) for q in finding.quality_issues
        ]
    return result


def serialize_evaluation_result(
    result: EvidenceBundleEvaluationResult,
) -> dict[str, Any]:
    """Serialize an EvidenceBundleEvaluationResult to a JSON-safe dict."""
    return {
        "evaluation_id": result.evaluation_id,
        "bundle_id": result.bundle_id,
        "evaluated_at": result.evaluated_at,
        "findings": [serialize_track_b_finding(f) for f in result.findings],
        "suppressed_evaluations": [
            serialize_track_b_finding(s) for s in result.suppressed_evaluations
        ],
        "summary": result.summary,
    }
