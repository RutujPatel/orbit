# PASS 4 — Wave 4A Contract Reconciliation Report
# Track B Multi-System Delivery-Health Evaluation Contract Reconciliation

**Pass:** 4 / Milestone 2 — Cross-System Evidence & Track B Evaluation Boundary  
**Wave:** 4A (Contract Reconciliation — Documentation & Architecture Only — NO IMPLEMENTATION)  
**Date:** 2026-09-28  
**Branch:** `remediation/pass3-controlled-hardening`  
**Governing Implementation Baseline:** `e967ad57ea3b37cef4266134537acbb34e9ae715`  
**Protected Governing Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`develop`)  
**Final Status:** **PASS WITH QUALIFICATIONS**

---

## 1. Scope

This document executes **Pass 4 / Wave 4A: Track B Contract Reconciliation**.

In strict accordance with change-control directives, Wave 4A is **documentation and architecture only**. No evaluator code (`evaluate_evidence_bundle()`, `evidence_evaluation.py`) has been implemented, no existing rule logic has been modified, no production evidence structures have been altered, and no live connectors have been introduced.

The explicit purpose of Wave 4A is to reconcile two architectural issues identified during human review of the Wave 4 reconnaissance:
1. **Issue A (ORBIT-XB-03 Semantic Correction)**: Eliminate the risk of converting observed temporal inversion into an implied negative delivery-health judgment or workflow defect.
2. **Issue B (ORBIT-XB-04 Temporal Contract Investigation)**: Determine whether `JiraIssueState` in `EvidenceBundle` proves state as of `review_cutoff_at` or merely latest observed state, and establish whether `ORBIT-XB-04` can deterministically evaluate historical overdue status.

---

## 2. Starting Baseline

```text
develop:                   6d82d123f8bf50316d2b1ab7a025bc5862a474ed (Frozen governing baseline)
HEAD:                      e967ad57ea3b37cef4266134537acbb34e9ae715 (Pass 3.1 Audited Head)
Merge-Base (HEAD, develop): 6d82d123f8bf50316d2b1ab7a025bc5862a474ed
Working Branch:            remediation/pass3-controlled-hardening
Regression Suite:          666 passed, 0 failed, 0 skipped in 9.72s
Mahout Qualification:      412 accepted, 12 findings, 56 incomplete, 370 missing due dates, 0 mutations
Mutation Guard:            Active (ReadOnlyJiraGuard active, 0 mutations, 0 config mutations)
```

The protected boundaries remain 100% intact:
* `develop` is untouched.
* Mahout raw capture, allowlists, and qualification semantics are unmodified.
* Historical golden artifacts and digests are unchanged.
* Track A (`evaluate_week_one_rules()`, `calculate_supporting_facts()`) is completely untouched.

---

## 3. Issue A — XB-03 Semantic Audit

### 3.1 Background & Risk
In Wave 4 reconnaissance, candidate rule `ORBIT-XB-03` (`POST_RESOLUTION_WORK_ACTIVITY`) was proposed to detect commits or pull requests merged after the associated Jira issue was marked resolved (`alignment.temporal_comparison == "INVERTED"`).

Human architectural review correctly flagged that treating temporal inversion as a delivery-health defect or workflow failure risks converting an objective temporal observation into an unsupported inference.

### 3.2 Forensic Distinction: Fact vs. Inference

| Dimension | Forensic Fact (Supported by Repository) | Unjustified Inference (Prohibited by Evidence Contract) |
|---|---|---|
| **What is observed?** | A GitHub commit (`committed_at`) or PR merge (`merged_at`) associated via `DECLARED_MENTION` or `EXPLICIT_LINK` with Jira issue `KEY` has a timestamp strictly later than Jira issue `KEY`'s `resolved_at` timestamp. | The Jira resolution was "incorrect", "premature", or "erroneous". |
| **Workflow meaning** | Code modifications citing the ticket continued after the ticket transitioned to a resolved status. | A developer violated a process rule, or development work was late/defective. |
| **Delivery impact** | Chronological sequence: `activity_timestamp > resolved_at`. | The post-resolution work caused a delivery problem or defect. |
| **System state** | Both Jira and GitHub record accurate timestamps for their respective events. | The Jira state was "wrong" or contradicts GitHub reality (`CONFLICTING`). |

### 3.3 Legitimate Engineering Causes of Temporal Inversion
In real-world software engineering pipelines, post-resolution activity occurs routinely for benign, standard operational reasons:
1. **Documentation, Test, or Telemetry Follow-ups**: Polish commits or test fixture updates pushed after feature verification was marked complete in Jira.
2. **Release Branch Merges & Backports**: A feature was implemented and verified on a working branch (ticket marked "Done"), and subsequently merged into `main` or backported to a release branch days later.
3. **CI/CD Pipeline Delays**: A ticket was administratively resolved upon code review sign-off, but automated merge queues or staging deployments merged the PR subsequently.
4. **Minor Cleanup & Post-Verification Tweaks**: Non-functional refactorings citing the ticket key during cleanup sprints.

### 3.4 Audit Conclusion
`temporal_comparison == "INVERTED"` is an **observational temporal relationship**, NOT a defect, conflict, or failure. 

ORBIT must document and implement `ORBIT-XB-03` strictly as an **OBSERVATIONAL EVIDENCE FINDING**. It must never be classified as `CONFLICTING`, must never claim developer fault, and must never assert that the Jira resolution was incorrect.

---

## 4. XB-03 Final Contract

```text
Rule ID:                    ORBIT-XB-03
Rule Name:                  POST_RESOLUTION_WORK_ACTIVITY
Rule Version:               1.0.0
Evaluation Track:           Track B (EvidenceBundle)
Classification Category:    OBSERVATIONAL EVIDENCE FINDING
```

### 4.1 Purpose
Record deterministic, provenance-backed evidence that GitHub activity (commit or PR merge) associated with a Jira issue occurred after the recorded Jira resolution timestamp.

### 4.2 Evidence Requirements
1. Established relationship in `bundle.cross_system_alignments` originating from an established `DECLARED_MENTION` or `EXPLICIT_LINK`.
2. Authoritative Jira `resolved_at` timestamp (`datetime`).
3. Authoritative GitHub activity timestamp: `merged_at` (for PR) or `committed_at` (for commit).

### 4.3 Deterministic Predicate
```python
alignment.temporal_comparison == "INVERTED"
# Under cross_system_fusion.py, this deterministically requires:
# jira_state.resolved_at is not None
# AND (
#     (pr_state.merged_at is not None AND pr_state.merged_at > jira_state.resolved_at)
#     OR (commit_state.committed_at is not None AND commit_state.committed_at > jira_state.resolved_at)
# )
```

### 4.4 Semantic Invariants
* **Meaning**: Purely observational. Establishes the factual sequence of recorded timestamps across systems.
* **Prohibited Meanings**: Must NOT imply `CONFLICTING`, `overdue`, incorrect resolution, defective delivery, workflow violation, developer negligence, or causal blame.

### 4.5 Finding Output Schema
* **Disposition**: `TRIGGERED`
* **Sufficiency Classification**:
  - `SUPPORTED` when relationship basis is `DECLARED_MENTION`.
  - `PROVEN` when relationship basis is `EXPLICIT_LINK`.
  - `INSUFFICIENT_EVIDENCE` if either `resolved_at` or GitHub activity timestamp is missing/indeterminate.
* **Deterministic Explanation**:
  `"GitHub {github_entity_kind} {github_entity_id} was {activity_kind} at {activity_at} ({days} complete days after Jira issue {jira_key} was marked resolved at {resolved_at}). This is an observational temporal finding; it does not assert that the Jira resolution was erroneous or that a workflow violation occurred."`
* **Observed Facts**:
  ```python
  {
      "jira_key": jira_key,
      "jira_resolved_at": _iso(jira_resolved_at),
      "github_entity_kind": "github_pull_request" | "github_commit",
      "github_entity_id": github_entity_id,
      "github_activity_kind": "pr_merged" | "commit",
      "github_activity_at": _iso(activity_at),
      "elapsed_complete_days_post_resolution": elapsed_complete_days(jira_resolved_at, activity_at),
      "relationship_kind": alignment.relationship_kind,  # "declared_mention" | "explicit_link"
  }
  ```
* **Provenance Requirements**:
  `provenance_refs` must preserve the complete chain:
  - Provenance of the Jira issue observation (`record_locator: "work_items[idx]"`).
  - Provenance of the citing GitHub artifact (`record_locator: "repositories[idx].pull_requests[idx]"` or `"repositories[idx].commits[idx]"`).

### 4.6 Authorization Status
**`READY_FOR_IMPLEMENTATION (OBSERVATIONAL ONLY)`**

---

## 5. Issue B — XB-04 Temporal Contract Investigation

### 5.1 Investigation Question
In Wave 4 reconnaissance, candidate rule `ORBIT-XB-04` (`OVERDUE_HIGH_PRIORITY_ISSUE`) was proposed with the predicate:
```python
jira.priority_band == "high" AND jira.due_at < review_cutoff_at AND jira.status_category != "done"
```
The unresolved question is: **What point in time does `JiraIssueState.status_category` represent?** Does it represent state as of `review_cutoff_at`, or does it represent the latest observed state at source capture time?

### 5.2 Forensic Trace of the Evidence Pipeline

We traced the complete ingestion and evidence construction path:

```text
Raw Fixture JSON ("fixtures/jira/clean_jira_week_1.json")
      │
      │ 1. validation.py: validate_fixture(document)
      │    - Checks schema, required fields, date formats.
      │    - Checks review_period: source_cutoff_at <= review_cutoff_at.
      │    - CRITICAL: Does NOT filter or rollback work_items based on cutoff.
      ▼
NormalizedFixture (normalization.py)
      │
      │ 2. normalization.py: normalize_fixture(document)
      │    - item["source_status"] is mapped to status_category via configuration["status_mapping"].
      │    - WorkItem.changes are sorted and parsed.
      │    - WorkItem.status_category = status_mapping.get(item["source_status"], "unknown").
      │    - CRITICAL: status_category is derived directly from item["source_status"],
      │      representing the state when the snapshot was exported.
      ▼
jira_evidence_adapter.py: adapt_jira_evidence()
      │
      │ 3. jira_evidence_adapter.py lines 296-310:
      │    state = JiraIssueState(
      │        key=work_item.key,
      │        source_status=work_item.source_status,
      │        source_priority=work_item.source_priority,
      │        status_category=work_item.status_category,
      │        priority_band=work_item.priority_band,
      │        assignee=work_item.assignee,
      │        created_at=work_item.created_at,
      │        updated_at=work_item.updated_at,
      │        resolved_at=work_item.resolved_at,
      │        due_at=work_item.due_at,
      │    )
      │    - CRITICAL: Copies work_item.status_category directly.
      │    - Discards work_item.changes (JiraIssueState has no changes field).
      │    - Discards work_item.history_complete.
      │    - Does NOT perform any historical state rollback.
      ▼
EvidenceBundle.observations (evidence_assembly.py)
      │
      │ 4. EvidenceObservation.observed_state holds JiraIssueState.
      │    ObservationContext contains source_cutoff_at, but source_cutoff_at
      │    is informational metadata; it does NOT alter JiraIssueState.status_category.
```

### 5.3 The Crucial Scenario Analysis
Consider the scenario specified in the prompt:
* `due_at` = June 1
* `review_cutoff_at` = June 5
* Jira ticket resolved = June 8
* Raw Jira capture / export timestamp = June 8 (`source_cutoff_at` = June 8)

In the resulting `EvidenceBundle`:
* `jira.due_at` = June 1
* `jira.resolved_at` = June 8
* `jira.status_category` = `"done"` (because the issue was resolved prior to export)
* `review_period.review_cutoff_at` = June 5

Now evaluate the proposed `ORBIT-XB-04` predicate:
```python
jira.priority_band == "high"      # True
AND jira.due_at < review_cutoff_at  # June 1 < June 5 -> True
AND jira.status_category != "done"  # "done" != "done" -> FALSE!
```
**Outcome**: The predicate evaluates to `False`. The rule does NOT trigger.

**Forensic Reality**: At the June 5 review cutoff, the ticket had NOT been resolved (it was resolved on June 8). The ticket was objectively overdue on June 5. However, because `JiraIssueState.status_category` reflects the latest export state (June 8) rather than the cutoff state (June 5), the evaluation produces a false negative.

### 5.4 Comparison with Track A
How did Track A handle this?
1. In Track A, `calculate_supporting_facts()` calls [`status_at_period_end(item, period, status_mapping)`](file:///home/tecblic/orbit/src/shadow_orbit/temporal.py#L96-L128). That helper inspects `item.changes`, filters transitions occurring after `period.ends_at_exclusive`, and reverses them chronologically to reconstruct the exact status at period end.
2. But in `JiraIssueState`, the transition history `changes` does **not exist**.
3. Calling `status_at_period_end()` on `JiraIssueState` raises an `AttributeError`.
4. Furthermore, Track A's `evaluate_overdue_high_priority()` in `evaluation.py` lines 252-287 actually evaluated snapshot status:
   ```python
   if item.status_category == "done":
       return None
   ```
   with explanation:
   `"...and remained {item.source_status.lower()} in the source state used for the {review_cutoff} review."`
   This reveals that Track A itself conflated "source state in fixture snapshot" with "state at review cutoff", relying on an implicit assumption that the fixture was captured at or immediately after the cutoff.

---

## 6. Evidence Supporting XB-04 Conclusion

Based on repository code audit:

1. **`JiraIssueState` lacks transition history**:
   `evidence_types.py` lines 230-249 defines `JiraIssueState` with scalar fields only (`key`, `source_status`, `status_category`, `created_at`, `updated_at`, `resolved_at`, `due_at`). No `changes` field exists.
2. **`jira_evidence_adapter` does not reconstruct state**:
   `jira_evidence_adapter.py` lines 296-310 copies `work_item.status_category` directly from `NormalizedFixture` without inspecting dates or rolling back transitions.
3. **`validation.py` allows snapshots postdating cutoffs**:
   `validation.py` only validates that `review_period.source_cutoff_at <= review_period.review_cutoff_at` (lines 140-144). It does NOT enforce that `work_item.updated_at <= review_cutoff_at`, nor does it enforce that `work_item.resolved_at <= review_cutoff_at`.
4. **Current `EvidenceBundle` cannot prove state as of `review_cutoff_at`**:
   If an issue was resolved after `review_cutoff_at`, `status_category` in `EvidenceBundle` is `"done"`. The bundle cannot deterministically establish whether the issue was `"done"` *before* or *after* `review_cutoff_at` without either:
   - Comparing `resolved_at` against `review_cutoff_at` (which the user directives explicitly prohibit as synthetic temporal inference / redefining overdue), OR
   - Having changelog transitions to prove historical status at the cutoff timestamp.

### XB-04 Decision Tree Application:
* *Condition 1*: Repository proves `JiraIssueState` is a valid point-in-time snapshot at the review cutoff -> **NOT MET**.
* *Condition 2*: Repository only proves `JiraIssueState` is the latest observed state in the fixture capture -> **CONFIRMED**.
* *Mandated Directive*: **"XB-04 MUST NOT be considered ready for historical overdue evaluation. Classify XB-04 as: REQUIRES TEMPORAL CONTRACT."**

---

## 7. Final Candidate Rule Matrix

| Rule ID | Rule Name | Evidence Requirement | Deterministic Predicate | Semantic Meaning | Sufficiency Classification | Authorization Status | Blocker / Dependency |
|---|---|---|---|---|---|---|---|
| **`ORBIT-XB-01`** | `UNMERGED_PR_ON_RESOLVED_ISSUE` | `CrossSystemStateAlignment` + `JiraIssueState` + `GitHubPullRequestState` | `jira.status_category == "done"` AND `pr.state == "open"` | Open PR cites a ticket marked resolved/done. Delivery health discrepancy. | `SUPPORTED` (on lexical mention) / `PROVEN` (on explicit link) | **`READY_FOR_IMPLEMENTATION`** | None |
| **`ORBIT-XB-02`** | `MERGED_PR_ON_UNRESOLVED_ISSUE` | `CrossSystemStateAlignment` + `JiraIssueState` + `GitHubPullRequestState` | `pr.state == "merged"` AND `jira.status_category in {"todo", "in_progress", "blocked"}` | Code merged to base branch while Jira ticket remains open. Workflow tracking lag. | `SUPPORTED` (on lexical mention) / `PROVEN` (on explicit link) | **`READY_FOR_IMPLEMENTATION`** | None |
| **`ORBIT-XB-03`** | `POST_RESOLUTION_WORK_ACTIVITY` | `CrossSystemStateAlignment` (`temporal_comparison == "INVERTED"`) | `alignment.temporal_comparison == "INVERTED"` (PR merge or commit timestamp > Jira `resolved_at`) | **OBSERVATIONAL ONLY**. Records that GitHub activity postdated Jira resolution. NOT a conflict, fault, or defect. | `SUPPORTED` (on lexical mention) / `PROVEN` (on explicit link) | **`READY_FOR_IMPLEMENTATION (OBSERVATIONAL ONLY)`** | Clarified in Wave 4A; ready for purely observational implementation. |
| **`ORBIT-XB-04`** | `OVERDUE_HIGH_PRIORITY_ISSUE` | `EvidenceObservation[JiraIssueState]` + `ObservationContext` | `jira.priority_band == "high"` AND `jira.due_at < cutoff` AND `jira.status_category != "done"` | High-priority issue past due date without completion at cutoff. | `PROVEN` (if temporal contract met) | **`REQUIRES_TEMPORAL_CONTRACT`** | `JiraIssueState` reflects latest export state, not cutoff state. Needs temporal snapshot contract or historical changelog. |
| **`ORBIT-XB-05`** | `STALLED_WORK_ON_EVIDENCE_BUNDLE` | Issue changelog transitions (`changes`) or commit activity stream | Elapsed complete days since last meaningful status transition $\ge$ threshold | In-progress ticket has no progress transitions for $\ge N$ days. | `PROVEN` | **`REQUIRES_SCHEMA_CHANGE`** | `JiraIssueState` lacks `changes` transition history. |
| **`ORBIT-XB-06`** | `NATIVE_LINK_STATUS_MISMATCH` | `EXPLICIT_LINK` relationships from native Jira/GitHub issue links | `rel.kind == "explicit_link"` AND lifecycle states contradict | Structured native integration link has contradictory states. | `PROVEN` | **`REQUIRES_SCHEMA_CHANGE`** | Current v1 fixture schemas have no structured native link fields (`explicit_links` is empty). |
| **`ORBIT-XB-07`** | `LIVE_PR_COMPLETION_VERIFICATION` | Remote GitHub GraphQL/REST API query | Remote API response returns verified PR state | Live remote verification of pull request status. | N/A | **`REQUIRES_CONNECTOR` (BLOCKED)** | Project ORBIT operates in offline proving mode; network access is strictly prohibited. |
| **`ORBIT-XB-08`** | `DEVELOPER_PRODUCTIVITY_SCORING` | Commit author strings + Jira assignee strings | Ratio of PR merges to ticket completions per developer | Individual developer performance or efficiency metric. | N/A | **`NOT_DETERMINISTICALLY_SUPPORTED` (PROHIBITED)** | Prohibited by anti-inference rules: actor identity cannot be asserted from unauthenticated username strings. |

---

## 8. ADR-006 Changes

`ADR-006_TRACK_B_EVIDENCE_BUNDLE_EVALUATION.md` has been updated with the following explicit sections:
1. **Section 5.5 (XB-03 Observational Semantics)**:
   - Formally restricts `POST_RESOLUTION_WORK_ACTIVITY` to observational status.
   - Forbids classifying temporal inversion as `CONFLICTING` or asserting workflow/delivery failure.
2. **Section 5.6 (XB-04 Temporal Snapshot Contract & Limitations)**:
   - Documents that `JiraIssueState` represents latest observed state in fixture capture, not historical state as of `review_cutoff_at`.
   - Classifies `ORBIT-XB-04` as `REQUIRES TEMPORAL CONTRACT`.
   - Specifies the two architectural paths for enabling `XB-04`: (Path 1) Ingestion contract guaranteeing snapshot captured exactly at `review_cutoff_at`; or (Path 2) Schema addition of `changes: tuple[Change, ...]` to `JiraIssueState`.
3. **Section 5.7 (Rule Authorization Status After Reconciliation)**:
   - Explicitly records authorization status for all 8 candidate rules:
     * `READY FOR IMPLEMENTATION`: `ORBIT-XB-01`, `ORBIT-XB-02`, `ORBIT-XB-03` (observational only).
     * `REQUIRES TEMPORAL CONTRACT`: `ORBIT-XB-04`.
     * `REQUIRES SCHEMA CHANGE`: `ORBIT-XB-05`, `ORBIT-XB-06`.
     * `REQUIRES CONNECTOR (BLOCKED)`: `ORBIT-XB-07`.
     * `NOT DETERMINISTICALLY SUPPORTED (PROHIBITED)`: `ORBIT-XB-08`.

---

## 9. Regression Result

The full repository test suite was executed:

```text
======================= 666 passed, 3 warnings in 9.72s ========================
```

* **Passed**: 666
* **Failed**: 0
* **Skipped**: 0
* **Total test time**: 9.72s
* **Pre-Wave-3**: 641 tests
* **Wave 3 additions**: 25 tests (`tests/unit/test_p4_wave3_cross_system_fusion.py`)
* **Wave 4/4A additions**: 0 tests (documentation/contract-only waves)
* **Status**: 100% GREEN.

---

## 10. Protected Baseline Verification

```bash
git rev-parse HEAD
# Output: e967ad57ea3b37cef4266134537acbb34e9ae715

git rev-parse develop
# Output: 6d82d123f8bf50316d2b1ab7a025bc5862a474ed

git merge-base HEAD develop
# Output: 6d82d123f8bf50316d2b1ab7a025bc5862a474ed
```

### Production File Integrity Audit:
The following production files were verified to be **completely unmodified** during Wave 4A:
* `evaluate_week_one_rules()` in [`src/shadow_orbit/evaluation.py`](file:///home/tecblic/orbit/src/shadow_orbit/evaluation.py): UNTOUCHED
* `calculate_supporting_facts()` in [`src/shadow_orbit/evaluation.py`](file:///home/tecblic/orbit/src/shadow_orbit/evaluation.py): UNTOUCHED
* [`src/shadow_orbit/evidence_types.py`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py): UNTOUCHED
* [`src/shadow_orbit/evidence_assembly.py`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_assembly.py): UNTOUCHED
* [`src/shadow_orbit/cross_system_fusion.py`](file:///home/tecblic/orbit/src/shadow_orbit/cross_system_fusion.py): UNTOUCHED
* [`src/shadow_orbit/provenance_dereference.py`](file:///home/tecblic/orbit/src/shadow_orbit/provenance_dereference.py): UNTOUCHED

---

## 11. Remaining Blockers

Before Track B implementation can proceed:
1. **Human Architectural Review**: Human sign-off is required on the reconciled candidate rule matrix and ADR-006 updates.
2. **XB-04 Scope Boundary**: Human confirmation that initial Track B implementation will cover **`ORBIT-XB-01`**, **`ORBIT-XB-02`**, and **`ORBIT-XB-03`** (observational), deferring **`ORBIT-XB-04`** until a formal temporal contract or schema expansion is authorized.

---

## 12. Human Approval Gate

### Summary of Reconciled Recommendations:
1. **ORBIT-XB-03**: Approved for implementation strictly as an **OBSERVATIONAL EVIDENCE FINDING**. It establishes that associated GitHub activity postdated Jira resolution; it does not claim workflow error, defective delivery, or contradictory state.
2. **ORBIT-XB-04**: Classified as **`REQUIRES TEMPORAL CONTRACT`**. Because `JiraIssueState` represents latest observed state rather than state at `review_cutoff_at`, and lacks changelog transitions, historical overdue evaluation cannot be deterministically proven on the current `EvidenceBundle`. Implementation of XB-04 must be deferred until the temporal contract is resolved.
3. **Authorized Scope for Track B Wave 5 (when authorized)**:
   - Implement `evaluate_evidence_bundle(bundle: EvidenceBundle) -> EvidenceBundleEvaluationResult`
   - Evaluate rules: `ORBIT-XB-01`, `ORBIT-XB-02`, and `ORBIT-XB-03` (observational).
   - Zero modifications to Track A.

---

## 13. Final Governance Gate

**PASS WITH QUALIFICATIONS**

**STOP — Awaiting human architectural authorization for Track B implementation.**
