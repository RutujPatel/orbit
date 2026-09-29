# ADR-006: Track B Evidence-Bundle Multi-System Delivery-Health Evaluation Architecture

**Status:** APPROVED & IMPLEMENTED (Wave 5 Track B Evaluator; Rules XB-01–XB-03 Implemented; XB-04–XB-08 Deferred/Prohibited)  
**Date:** 2026-09-28  
**Pass:** Pass 4 / Wave 4 (Milestone 2)  
**Author:** Forensic Software Engineering & Evidence Integrity Review  

---

## Context

Project ORBIT operates on a dual-track architectural model established under Pass 4 Wave 0:
* **Track A (Legacy / Specimen Evaluator):** `evaluate_week_one_rules(NormalizedFixture)` is a frozen, single-source Jira evaluator. It governs the Mahout qualification specimen (412 items, 12 stalled work findings, 0 mutations) and historical acceptance tests. It must remain 100% untouched.
* **Track B (Multi-Source Evidence Evaluator):** The future `evaluate_evidence_bundle(EvidenceBundle, ...)` engine. It evaluates delivery health across both Jira and GitHub evidence, operating on the validated `EvidenceBundle` container created by CSE-1.7 and verified in Waves 1–3.

Under Pass 4 Waves 1–3, ORBIT established:
1. Pure in-memory provenance dereferencing against offline source fixtures ([`ADR-004`](file:///home/tecblic/orbit/ADR-004_PROVENANCE_DEREFERENCING.md)).
2. Formal separation of explicit native metadata (`EXPLICIT_LINK`) from textual citations (`DECLARED_MENTION`) ([`ADR-005`](file:///home/tecblic/orbit/ADR-005_CROSS_SYSTEM_EVIDENCE_FUSION.md)).
3. Independent state (`CONSISTENT`, `CONFLICTING`, `INSUFFICIENT_EVIDENCE`) and temporal (`COHERENT`, `INVERTED`, `INDETERMINATE`) alignment classifications.
4. Containerization and provenance validation of `CrossSystemStateAlignment` records in `EvidenceBundle`.

However, the repository currently lacks an evaluation engine that consumes `EvidenceBundle` to produce multi-system delivery-health findings. 

This ADR defines the formal architectural contract for Track B evaluation before any implementation is authorized.

---

## Architectural Decisions (Proposals for Human Approval)

### 1. Decision 1 (Container Input Boundary)
**Track B evaluates `EvidenceBundle` directly; it does NOT evaluate raw fixtures or bypass the bundle boundary.**
* The input to Track B is strictly:
  ```python
  def evaluate_evidence_bundle(
      bundle: EvidenceBundle,
      review_period: ReviewPeriod | None = None,
  ) -> EvidenceBundleEvaluationResult:
  ```
* Bypassing `EvidenceBundle` to inspect `NormalizedGitHubFixture` or `NormalizedFixture` directly is prohibited.
* Track B assumes that `validate_evidence_bundle()` has already verified joint observation-context pairing, endpoint existence, and supporting provenance references.

### 2. Decision 2 (Strict Dual-Track Isolation)
**Track A (`evaluate_week_one_rules`) and Track B (`evaluate_evidence_bundle`) are completely decoupled.**
* Track A remains unmodified and continues to consume `NormalizedFixture`.
* Track B does NOT import, call, wrap, or modify `evaluate_week_one_rules()` or `calculate_supporting_facts()`.
* Pure mathematical and date helpers (such as `elapsed_complete_days` in `temporal.py`) may be shared if they depend only on Python standard types, but helpers requiring `WorkItem.changes` (such as `last_meaningful_status_change` or `blocked_since`) are NOT callable on `JiraIssueState` because `JiraIssueState` does not carry changelog transitions.

### 3. Decision 3 (Explicit Sufficiency Taxonomy)
**Findings must explicitly record evidence sufficiency; missing evidence is never converted to a negative finding.**
Every Track B finding and evaluation result must carry an explicit `sufficiency_classification`:
* `PROVEN`: Authoritative, complete evidence with explicit native linkage (`EXPLICIT_LINK`).
* `SUPPORTED`: Provenance-backed evidence based on valid lexical citation (`DECLARED_MENTION`).
* `INSUFFICIENT_EVIDENCE`: Required timestamps, states, or coverage notes are partial, unobserved, or missing (`Unknown != False`).
* `CONFLICTING`: Mutually incompatible authoritative records (strictly reserved; temporal inversion $\neq$ conflict).
* `STALE`: Observation postdates review cutoff timestamp.
* `UNRESOLVED`: Mentioned entity was not observed in the provided fixture.
* `AMBIGUOUS`: Mentioned key resolves to multiple conflicting observation candidates.

### 4. Decision 4 (Relationship-Bound Cross-System Findings)
**Cross-system findings are generated ONLY where an established `DECLARED_MENTION` or `EXPLICIT_LINK` exists.**
* The evaluator must never perform cartesian pairing between unlinked Jira issues and GitHub artifacts.
* Coexistence of `PLAT-101` and an unlinked PR in the same fixture universe produces zero cross-system findings.

### 5. Decision 5 (Anti-Inference Invariants)
The evaluator must enforce the following non-inferential boundaries:
1. **No Actor Identity**: Matching usernames (`author_login == "alice"` vs `assignee == "Alice"`) do not establish personal identity or ownership.
2. **No Transitive Association**: If Commit A cites `PLAT-101` and PR 10 contains Commit A, PR 10 does not automatically link to `PLAT-101` unless explicitly cited.
3. **No Completion Inference**: Merging a PR does not prove the Jira issue is complete.
4. **No Absence Inference**: Absence of a GitHub mention does not prove that development work did not occur.
5. **Conservative Contradiction**: A PR merged after Jira resolution is classified as `temporal_comparison="INVERTED"` and `sufficiency_classification="SUPPORTED"`, NEVER `CONFLICTING`.

### 6. Decision 6 (Provenance Preservation to Findings)
**Every finding emitted by Track B must preserve the full provenance chain from the underlying `EvidenceObservation` and `CrossSystemStateAlignment`.**
* Findings must carry `provenance_refs: tuple[ProvenanceRef, ...]`.
* End-to-end traceability must allow dereferencing from a finding's provenance reference directly back to the original source fixture record locator (`record_locator`) and field (`source_field_path`).

### 7. Decision 7 (XB-03 Observational Semantics)
**`ORBIT-XB-03` (`POST_RESOLUTION_WORK_ACTIVITY`) is strictly an OBSERVATIONAL EVIDENCE FINDING, not an assessment of defect, conflict, or fault.**
* **Factual Scope**: The finding establishes exclusively that GitHub activity (`committed_at` or `merged_at`) associated via an established relationship (`DECLARED_MENTION` or `EXPLICIT_LINK`) occurred at a timestamp after Jira recorded the issue as resolved (`resolved_at`).
* **Anti-Inference Invariant**: The finding must NEVER assert or imply that:
  - The Jira resolution was incorrect, premature, or erroneous.
  - Development work was late or defective.
  - The issue should have remained open.
  - A developer or team violated a workflow rule.
  - An evidence contradiction exists (`temporal_comparison == "INVERTED"` is NEVER classified as `CONFLICTING`).
* **Standard Engineering Context**: Legitimate post-resolution activity occurs routinely (documentation polish, release branch backports, CI merge queues, post-verification cleanups). The finding reports the observed sequence of events without judgment.
* **Sufficiency**: Carries `sufficiency="SUPPORTED"` when based on `DECLARED_MENTION`, and `sufficiency="PROVEN"` when based on `EXPLICIT_LINK`.

### 8. Decision 8 (XB-04 Temporal Snapshot Contract & Limitations)
**`JiraIssueState` in `EvidenceBundle` reflects the latest observed state at fixture export, NOT a point-in-time state as of `review_cutoff_at`.**
* **Forensic Finding**: `jira_evidence_adapter.py` constructs `JiraIssueState` by directly copying scalar fields (`status_category`, `source_status`, `due_at`, `resolved_at`) from `NormalizedFixture.work_items`. Transition changelogs (`changes: tuple[Change, ...]`) are discarded. No state rollback or historical reconstruction is performed.
* **Evaluation Impact**: An issue resolved after `review_cutoff_at` (e.g. resolved June 8 when cutoff is June 5) has `status_category == "done"` in the `EvidenceBundle`. A naive predicate `status_category != "done"` evaluates to `False`, failing to detect that the issue was incomplete and overdue as of the cutoff date.
* **Contract Classification**: Candidate rule `ORBIT-XB-04` (`OVERDUE_HIGH_PRIORITY_ISSUE`) is formally classified as **`REQUIRES TEMPORAL CONTRACT`**. It is NOT authorized for implementation until either:
  1. *Ingestion Contract*: An explicit guarantee that the source fixture snapshot was captured exactly at `review_cutoff_at`; or
  2. *Schema Evolution*: `JiraIssueState` is augmented with transition changelogs (`changes: tuple[Change, ...]`) enabling pure historical state reconstruction via `status_at_period_end()`.

### 9. Decision 9 (Rule Authorization Taxonomy)
**Track B candidate rules are categorized into four distinct authorization tiers before implementation:**
1. **`READY FOR IMPLEMENTATION`**:
   - `ORBIT-XB-01` (`UNMERGED_PR_ON_RESOLVED_ISSUE`): Cross-system state discrepancy.
   - `ORBIT-XB-02` (`MERGED_PR_ON_UNRESOLVED_ISSUE`): Cross-system tracking lag.
   - `ORBIT-XB-03` (`POST_RESOLUTION_WORK_ACTIVITY`): Observational temporal sequence finding.
2. **`REQUIRES TEMPORAL CONTRACT`**:
   - `ORBIT-XB-04` (`OVERDUE_HIGH_PRIORITY_ISSUE`): Blocked by lack of point-in-time cutoff state guarantee.
3. **`REQUIRES SCHEMA CHANGE`**:
   - `ORBIT-XB-05` (`STALLED_WORK_ON_EVIDENCE_BUNDLE`): Blocked by missing `changes` on `JiraIssueState`.
   - `ORBIT-XB-06` (`NATIVE_LINK_STATUS_MISMATCH`): Blocked by missing native link fields in v1 fixtures.
4. **`BLOCKED / PROHIBITED`**:
   - `ORBIT-XB-07` (`LIVE_PR_COMPLETION_VERIFICATION`): Blocked by offline proving boundary (network prohibited).
   - `ORBIT-XB-08` (`DEVELOPER_PRODUCTIVITY_SCORING`): Prohibited by anti-inference principles (unverified actor identity, heuristic scoring).

---

## Proposed Data Structures (Design Only)

```python
FindingSufficiency = Literal[
    "PROVEN",
    "SUPPORTED",
    "INSUFFICIENT_EVIDENCE",
    "CONFLICTING",
    "STALE",
    "UNRESOLVED",
    "AMBIGUOUS",
]

FindingDisposition = Literal["TRIGGERED", "SUPPRESSED", "INSUFFICIENT_EVIDENCE"]

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
```

---

## Consequences

### Positive
* Enables multi-system delivery health evaluation while maintaining 100% frozen stability on Track A.
* Strictly prevents heuristic or hallucinated cross-system connections.
* Guarantees full end-to-end provenance traceability from raw fixture through to findings.
* Explicitly distinguishes between workflow lags, missing data, and genuine contradictions.

### Negative / Trade-offs
* Without changelog transitions on `JiraIssueState`, Track A's exact `STALLED_WORK` and `BLOCKED_SINCE` rules cannot be evaluated directly on `EvidenceBundle` without schema expansion.
* Because `explicit_links` is currently empty under v1 fixtures, cross-system findings on existing fixtures will carry `sufficiency="SUPPORTED"` rather than `sufficiency="PROVEN"`.

---

## Human Approval Gate

This ADR was approved for controlled Wave 5 implementation by human architectural authorization following Wave 4A contract reconciliation.

---

## Implementation Status (Wave 5 Verified)

Under Pass 4 Wave 5, the approved Track B evaluator was implemented in [`src/shadow_orbit/evidence_evaluation.py`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_evaluation.py) and validated across 42 unit and adversarial tests ([`tests/unit/test_p4_wave5_evidence_evaluation.py`](file:///home/tecblic/orbit/tests/unit/test_p4_wave5_evidence_evaluation.py)).

* **Primary Function**: `evaluate_evidence_bundle(bundle: EvidenceBundle, review_period: ReviewPeriod | None = None) -> EvidenceBundleEvaluationResult`
* **Evaluated Rules**:
  - `ORBIT-XB-01` (`UNMERGED_PR_ON_RESOLVED_ISSUE`): Implemented and verified.
  - `ORBIT-XB-02` (`MERGED_PR_ON_UNRESOLVED_ISSUE`): Implemented and verified.
  - `ORBIT-XB-03` (`POST_RESOLUTION_WORK_ACTIVITY`): Implemented strictly as an observational evidence finding.
* **Deferred & Prohibited Rules**:
  - `ORBIT-XB-04` (`OVERDUE_HIGH_PRIORITY_ISSUE`): Explicitly deferred pending temporal contract resolution.
  - `ORBIT-XB-05` / `ORBIT-XB-06`: Deferred pending schema evolution.
  - `ORBIT-XB-07`: Blocked by offline proving boundary.
  - `ORBIT-XB-08`: Permanently prohibited by anti-inference principles.
* **Dual-Track Isolation**: Track A (`evaluate_week_one_rules()`, `calculate_supporting_facts()`) remains 100% untouched.
* **Regression**: 708 collected (696 passed, 12 skipped, 0 failed).
* **Mahout Invariants**: 412 accepted, 12 findings, 56 incomplete, 370 missing due dates, 0 mutations, repeatable=True.

