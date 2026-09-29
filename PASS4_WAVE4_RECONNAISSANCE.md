# PASS 4 — Wave 4 Reconnaissance Report
# Track B Evidence-Bundle Multi-System Delivery-Health Evaluation Architecture

**Pass:** 4 / Milestone 2 — Cross-System Evidence & Track B Evaluation Boundary  
**Wave:** 4 (Reconnaissance & Architectural Contract Definition Only — NO IMPLEMENTATION)  
**Date:** 2026-09-28  
**Branch:** `remediation/pass3-controlled-hardening`  
**Governing Implementation Baseline:** `e967ad57ea3b37cef4266134537acbb34e9ae715`  
**Protected Governing Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`develop`)  
**Final Status:** **PASS WITH QUALIFICATIONS**

---

## 1. Executive Summary

Wave 4 conducts the architectural reconnaissance and contract definition for **Track B evaluation** (`evaluate_evidence_bundle`), establishing how Project ORBIT will eventually evaluate software delivery health across multi-source evidence (Jira issue tracking and GitHub source control) without compromising the frozen, deterministic Track A baseline (`evaluate_week_one_rules`).

This wave is strictly **reconnaissance and contract definition only**. In accordance with change-control instructions, zero production evaluator code has been implemented, no existing rule logic has been modified, no live network connectors have been introduced, and all historical invariants remain 100% green (666 tests passing, 0 mutations, Mahout repeatable).

### Key Architectural Findings:
1. **Container Completeness**: `EvidenceBundle` (as hardened in Waves 1–3) contains all necessary structural scaffolding: observation contexts, typed observations, structural and mention relationships, unresolved references, quality issues, and canonically sorted `CrossSystemStateAlignment` records.
2. **Jira Changelog Discrepancy**: A major forensic discovery is that `JiraIssueState` in `EvidenceBundle` is a **point-in-time state projection** (`source_status`, `status_category`, `created_at`, `updated_at`, `resolved_at`, `due_at`), whereas Track A's `WorkItem` carries an active tuple of transition history (`changes: tuple[Change, ...]`). Consequently, Track A rules relying on changelog transitions (e.g. `STALLED_WORK` and `BLOCKED_SINCE`) cannot be run on `JiraIssueState` without a schema change.
3. **Cross-System Rules are Feasible**: Three cross-system rules evaluating state discrepancies between Jira and GitHub are **immediately feasible** using existing `CrossSystemStateAlignment` data:
   - `UNMERGED_PR_ON_RESOLVED_ISSUE` (PR open while Jira issue done)
   - `MERGED_PR_ON_UNRESOLVED_ISSUE` (PR merged while Jira issue open/in-progress)
   - `POST_RESOLUTION_WORK_ACTIVITY` (PR merge or commit postdating Jira resolution timestamp)
4. **Sufficiency Taxonomy**: Track B must not collapse missing or partial evidence into negative assertions. Findings must explicitly carry an evidence sufficiency classification: `PROVEN`, `SUPPORTED`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING`, `STALE`, `UNRESOLVED`, or `AMBIGUOUS`.
5. **Strict Anti-Inference**: Temporal inversion $\neq$ conflict; username collision $\neq$ human actor identity; lack of mention $\neq$ absence of work.

---

## 2. Current Repository State

```text
develop:                   6d82d123f8bf50316d2b1ab7a025bc5862a474ed (Frozen governing baseline)
HEAD:                      e967ad57ea3b37cef4266134537acbb34e9ae715 (Pass 3.1 Audited Head)
Merge-Base (HEAD, develop): 6d82d123f8bf50316d2b1ab7a025bc5862a474ed
Working Branch:            remediation/pass3-controlled-hardening
Regression Suite:          666 passed, 0 failed, 0 skipped in 9.82s
Mahout Qualification:      412 accepted, 12 findings, 56 incomplete, 370 missing due dates, 0 mutations
Mutation Guard:            Active (ReadOnlyJiraGuard active, 0 mutations, 0 config mutations)
```

The working tree holds staged Milestone 2 capabilities from Waves 1–3:
- [`src/shadow_orbit/provenance_dereference.py`](file:///home/tecblic/orbit/src/shadow_orbit/provenance_dereference.py) (Wave 1: in-memory bounded dereferencer)
- [`src/shadow_orbit/evidence_assembly.py`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_assembly.py) (Wave 2: bundle validation integration with `fixtures_by_id`)
- [`src/shadow_orbit/evidence_types.py`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py) (Waves 2–3: cross-system alignments and link types)
- [`src/shadow_orbit/cross_system_fusion.py`](file:///home/tecblic/orbit/src/shadow_orbit/cross_system_fusion.py) (Wave 3: pure correlation engine)
- Associated test suites: `test_p4_provenance_dereferencing.py` (91 tests), `test_p4_wave2_provenance_validation.py` (23 tests), `test_p4_wave3_cross_system_fusion.py` (25 tests). Progression: 527 -> 618 (+91) -> 641 (+23) -> 666 (+25).

---

## 3. EvidenceBundle Inventory

An explicit audit of the fields and capabilities provided by [`EvidenceBundle`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py#L359-L380) reveals the exact boundary available to Track B:

| Evidence Class | Source | Identity Fields | Temporal Fields | State / Payload Fields | Supporting Provenance | Cross-System Relation | Track B Evaluation Usability | Limitations / Gaps |
|---|---|---|---|---|---|---|---|---|
| **`ObservationContext`** | Jira / GitHub | `observation_id` | `observed_interval_starts_at`, `observed_interval_ends_at_exclusive`, `source_cutoff_at` | `source_instance`, `coverage_note` | N/A (root context) | Multi-source context pairing | ✅ High (defines review boundaries and staleness) | Coverage note is freeform string; partial coverage requires parsing. |
| **`EvidenceObservation` (`jira_issue`)** | Jira | `entity_id` (issue key, e.g. `PLAT-101`) | `created_at`, `updated_at`, `resolved_at`, `due_at` | `source_status`, `source_priority`, `status_category`, `priority_band`, `assignee` | `work_items[idx]` | Target of `DECLARED_MENTION` or `EXPLICIT_LINK` | ✅ High for snapshot status, priority, and due dates | **No transition changelog (`changes`)**; cannot evaluate exact `STALLED_WORK` or `BLOCKED_SINCE`. |
| **`EvidenceObservation` (`github_repository`)** | GitHub | `entity_id` (`repo_id`) | None | `owner`, `name`, `default_branch` | `repositories[idx]` | Target of `belongs_to_repository` | ⚠️ Low (scoping context only) | No temporal fields. |
| **`EvidenceObservation` (`github_branch`)** | GitHub | `entity_id` (`{repo_id}/{name}`) | None | `name`, `head_commit_id` | `repositories[idx].branches[idx]` | Subject of `has_head_branch`, `DECLARED_MENTION` | ⚠️ Medium (branch existence and head commit) | No direct creation or commit timestamp on branch record. |
| **`EvidenceObservation` (`github_commit`)** | GitHub | `entity_id` (`{repo_id}/{sha}`) | `committed_at` | `sha`, `message`, `author_login` | `repositories[idx].commits[idx]` | Subject of `contains_commit`, `has_head_commit`, `DECLARED_MENTION` | ✅ High for commit-level activity and post-resolution edits | Author is raw login string; no verified developer identity. |
| **`EvidenceObservation` (`github_pull_request`)** | GitHub | `entity_id` (`{repo_id}/{number}`) | `created_at`, `merged_at` | `number`, `title`, `state` (open/closed/merged), `author_login`, `target_branch`, `source_branch`, `head_commit_sha`, `is_fork` | `repositories[idx].pull_requests[idx]` | Subject of `belongs_to_repository`, `DECLARED_MENTION`, `EXPLICIT_LINK` | ✅ High for PR lifecycle vs ticket status | No `closed_at` timestamp if closed unmerged; `state` is primary discriminator. |
| **`EvidenceObservation` (`github_review`)** | GitHub | `entity_id` (`{repo_id}/{num}/{id}`) | `submitted_at` | `review_id`, `state` (APPROVED, etc.), `reviewer_login` | `repositories[...].reviews[idx]` | Subject of `review_of` | ⚠️ Medium (peer review approval tracking) | Sparse in current fixtures; unverified reviewer identity. |
| **`EvidenceRelationship`** | GitHub / Cross | `(subject_ref, object_ref, kind)` | None directly | `kind` (belongs_to_repository, mentions, explicit_link, etc.), `basis` | Required (source record / field) | Defines the cross-system edge | ✅ High (authorizes cross-system pairing) | `explicit_link` is empty under v1 fixtures; all citations are `DECLARED_MENTION`. |
| **`UnresolvedReference`** | Jira / GitHub | `(source_ref, target_identifier)` | None | `target_entity_kind`, `relationship_kind`, `reason` | Required (source record / field) | Unresolved cross-system edge | ✅ High (identifies missing or ambiguous references) | Must not be conflated with non-existence of entity in source system. |
| **`QualityIssue`** | Jira / GitHub | `(code, subject_ref, subject_scope)` | None | `code`, `message` | Attached to observation or bundle | Flags data quality deficiencies | ✅ High (suppresses or flags invalid findings) | Must be checked before asserting rule triggers. |
| **`CrossSystemStateAlignment`** | Cross-System | `(jira_ref, github_ref)` | Evaluates `merged_at`, `committed_at` vs `resolved_at` | `state_comparison`, `temporal_comparison`, `rationale` | Inherited from relation provenance | Explicit paired state alignment | ✅ Critical (primary pre-computed cross-system predicate) | Derived offline in pure memory; requires relationship-bound origin. |

---

## 4. Track A vs Track B Boundary

The system maintains two distinct evaluation tracks with strictly separated responsibilities:

```
                    ┌────────────────────────────────────────────────────────┐
                    │                      SOURCE DATA                       │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     ▼                                                     ▼
      ┌─────────────────────────────┐                       ┌─────────────────────────────┐
      │     Jira Raw Fixture        │                       │    GitHub Raw Fixtures      │
      └──────────────┬──────────────┘                       └──────────────┬──────────────┘
                     │                                                     │
                     ▼                                                     ▼
      ┌─────────────────────────────┐                       ┌─────────────────────────────┐
      │    Jira NormalizedFixture   │                       │  NormalizedGitHubFixture    │
      └──────┬───────────────┬──────┘                       └──────────────┬──────────────┘
             │               │                                             │
             │               └──────────────────────┬──────────────────────┘
             ▼                                      ▼
┌─────────────────────────────┐      ┌────────────────────────────────────────────┐
│          TRACK A            │      │            CSE EVIDENCE PIPELINE           │
│   (Frozen / Historical)     │      │         (jira_evidence_adapter,            │
│  evaluate_week_one_rules()  │      │     cross_system_fusion, assembly)         │
│                             │      └──────────────────────┬─────────────────────┘
│ - Consumes:                 │                             ▼
│   NormalizedFixture (Jira)  │      ┌────────────────────────────────────────────┐
│ - Pure Jira rules:          │      │               EvidenceBundle               │
│   OVERDUE_HIGH_PRIORITY     │      │  (Observations, Contexts, Alignments,      │
│   BLOCKED_HIGH_PRIORITY     │      │   Relationships, Provenance, Issues)       │
│   STALLED_WORK              │      └──────────────────────┬─────────────────────┘
│ - Relies on WorkItem.changes│                             │
│ - Output: RuleMatch,        │                             ▼
│   SuppressedEvaluation      │      ┌────────────────────────────────────────────┐
│ - Governs Mahout 412/12/56  │      │                  TRACK B                   │
│ - Status: 100% UNTOUCHED    │      │            (Future Milestone 2)            │
└─────────────────────────────┘      │         evaluate_evidence_bundle()         │
                                     │                                            │
                                     │ - Consumes: EvidenceBundle directly        │
                                     │ - Multi-source delivery-health rules       │
                                     │ - Relationship-bound cross-system findings │
                                     │ - Explicit sufficiency taxonomy            │
                                     │ - Full in-memory provenance preservation   │
                                     │ - Status: PROPOSAL ONLY (NOT IMPLEMENTED)  │
                                     └────────────────────────────────────────────┘
```

### Forensic Comparison:
1. **Inputs**:
   - **Track A**: Consumes `NormalizedFixture`, a Jira-only structure containing `WorkItem` dataclasses and raw document configuration (`status_mapping`, `stalled_threshold_complete_days`).
   - **Track B**: Consumes `EvidenceBundle`, a multi-source container containing immutable tuples of `EvidenceObservation` (`JiraIssueState`, `GitHubPullRequestState`, etc.), `CrossSystemStateAlignment`, and `ObservationContext`.
2. **Assumptions**:
   - **Track A**: Assumes a closed single-source Jira world. Computes status transitions by scanning `WorkItem.changes`.
   - **Track B**: Operates in an open/closed multi-system boundary. Must adhere to `Unknown != False` and missing evidence $\neq$ negative assertion.
3. **Helper Sharing & Isolation**:
   - *Can be safely shared*: Stateless date and interval arithmetic in [`src/shadow_orbit/temporal.py`](file:///home/tecblic/orbit/src/shadow_orbit/temporal.py) (e.g. `elapsed_complete_days(d1, d2)`).
   - *Must remain isolated*: Functions that accept `WorkItem` and inspect `item.changes` (e.g. `blocked_since`, `last_meaningful_status_change`, `completed_during_period`) **cannot be used by Track B** because `JiraIssueState` does not have `changes`. Calling these helpers on `JiraIssueState` would cause runtime attribute crashes.
4. **Coupling Guard**:
   - Track B must never import `evaluate_week_one_rules()` or wrap Track A outputs.
   - Any attempt to feed `EvidenceBundle` into `evaluate_week_one_rules()` violates the governing baseline.

---

## 5. Existing Finding Contract

In Track A ([`src/shadow_orbit/types.py#L85-L102`](file:///home/tecblic/orbit/src/shadow_orbit/types.py#L85-L102) and [`src/shadow_orbit/artifact.py#L276-L353`](file:///home/tecblic/orbit/src/shadow_orbit/artifact.py#L276-L353)), rule evaluation produces two distinct records:

### 1. `RuleMatch`
```python
@dataclass(frozen=True, slots=True)
class RuleMatch:
    subject_key: str                            # Single Jira issue key (e.g. "PLAT-101")
    rule_key: str                               # Rule ID (e.g. "STALLED_WORK")
    rule_version: str                           # Rule semver (e.g. "1.0.0")
    observed: dict[str, Any]                    # Observed metrics (e.g. elapsed_complete_days: 7)
    threshold: dict[str, Any]                   # Configured threshold (e.g. stalled_threshold: 5)
    calculation: str                            # Human-readable calculation string
    deterministic_explanation: str              # Narrative explanation of finding
    evidence_references: tuple[dict[str, str], ...] # String role/ref dicts
    data_quality_state: str = "complete"        # "complete" or quality flag
```

### 2. `SuppressedEvaluation`
```python
@dataclass(frozen=True, slots=True)
class SuppressedEvaluation:
    subject_key: str                            # Single Jira issue key
    rule_key: str                               # Rule ID that could not be evaluated
    reason: str                                 # Specific reason (e.g. "Incomplete changelog history")
```

### Limitations of Track A Structures for Track B:
1. **Single-System Subject**: `subject_key` is a plain string assuming a Jira key. It cannot natively represent a GitHub entity or a multi-system entity pair `(jira_ref, github_ref)`.
2. **String-Only References**: `evidence_references` uses loose string mappings (`{"reference": "work_item:PLAT-101", "role": "source_work_item"}`), discarding structured `ProvenanceRef` locators.
3. **Binary Outcome**: An evaluation either matches (`RuleMatch`) or is suppressed (`SuppressedEvaluation`). It cannot represent nuanced evidence states such as `SUPPORTED`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING`, or `STALE`.

---

## 6. Proposed Track B Evaluation Boundary

To support multi-system delivery health without heuristic interpretation, Track B requires a dedicated finding and result container:

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

FindingDisposition = Literal[
    "TRIGGERED",
    "INSUFFICIENT_EVIDENCE",
    "CONFLICTING",
    "SUPPRESSED",
]

@dataclass(frozen=True, slots=True)
class TrackBFinding:
    """A deterministic multi-system delivery-health finding produced by Track B."""
    finding_id: str                             # Deterministic composite hash/UUID
    rule_id: str                                # Unique rule identifier (e.g. "ORBIT-XB-01")
    rule_version: str                           # Semantic version of rule
    subject_ref: EntityRef                      # Primary subject (Jira issue or GitHub PR)
    corroborating_refs: tuple[EntityRef, ...]   # Referenced counterpart entities
    disposition: FindingDisposition             # Outcome category
    sufficiency: FindingSufficiency             # Formal evidence sufficiency state
    deterministic_explanation: str              # Non-inferential explanation
    observed_facts: dict[str, Any]              # Exact states, timestamps, comparisons
    provenance_refs: tuple[ProvenanceRef, ...]   # Complete dereferenceable provenance chain
    quality_issues: tuple[QualityIssue, ...] = ()# Relevant quality issues attached to subject

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

### Conceptual Evaluation Pipeline Flow:
```
       EvidenceBundle (Observations, Alignments, Relationships, Provenance)
                                       │
                                       ▼
                     [ Stage 1: Structural Validation Check ]
                    (Verify zero bundle-level quarantine errors)
                                       │
                                       ▼
                   [ Stage 2: Evidence Sufficiency Filter ]
           (Identify missing timestamps, coverage notes, unresolved keys)
                                       │
                                       ▼
                   [ Stage 3: Deterministic Rule Predicates ]
            (Apply rule logic against alignments and observations)
                                       │
                                       ▼
                     [ Stage 4: Provenance Attachment ]
             (Attach exact ProvenanceRef chains from underlying edges)
                                       │
                                       ▼
                   EvidenceBundleEvaluationResult (Immutable)
```

---

## 7. Evidence Sufficiency Taxonomy

Track B must strictly preserve the distinction between facts, missing data, and contradictions:

| Classification | Definition | Emission Criteria in Track B | Anti-Inference Protection |
|---|---|---|---|
| **`PROVEN`** | Condition is established by complete, authoritative, unambiguous evidence with native integration metadata. | Requires `EXPLICIT_LINK` (structured native metadata) with coherent lifecycle states and dereferenceable provenance. | *Forensic Note:* Because current fixture schemas lack native link fields, `PROVEN` cross-system findings cannot be emitted on existing corpus. |
| **`SUPPORTED`** | Condition is established by valid evidence, but connection relies on textual mention or snapshot state. | Produced when cross-system finding is based on an established `DECLARED_MENTION` with coherent states and verified provenance. | Never claims implementation authorship; remains an evidence-backed correlation. |
| **`INSUFFICIENT_EVIDENCE`** | An observation, field, or interval required by the rule predicate is unobserved, missing, or partial. | Emitted when: (a) PR marked merged lacks `merged_at`, (b) Jira issue lacks `due_at`, (c) coverage note indicates incomplete ingestion. | **`Unknown != False`**: Missing data does not mean work did not happen. |
| **`CONFLICTING`** | Two authoritative evidence sources make assertions that are logically impossible to simultaneously be true. | Reserved strictly for contradictory authoritative records (e.g. manifest claims PR closed unmerged while deployment claims PR deployed). | **Temporal delay $\neq$ conflict**: A PR merged after Jira resolution is NOT a conflict. |
| **`STALE`** | Observation postdates review cutoff or is superseded by a newer observation outside the review window. | Emitted when observation timestamp $> \text{source\_cutoff\_at}$, or when changelog indicates changes after cutoff. | Does not make observation false; flags it as temporally invalid for current review. |
| **`UNRESOLVED`** | A cited reference does not resolve to an accepted observation in the evidence bundle. | Emitted when PR cites Jira key not found in Jira observations, or head commit sha is missing from fixture. | Does not mean ticket does not exist in Jira; means it was not observed in the provided fixture. |
| **`AMBIGUOUS`** | A reference maps to multiple candidate targets. | Emitted when PR cites a Jira key that maps to multiple Jira observations with different statuses. | Prevents arbitrary target selection. |

---

## 8. Cross-System Relationship Contract

Track B evaluation must strictly honor the relationship boundaries established in [`ADR-005`](file:///home/tecblic/orbit/ADR-005_CROSS_SYSTEM_EVIDENCE_FUSION.md):

1. **Relationship-Bound Pairing Only**:
   Cross-system rules evaluate **only** entity pairs that have an established edge in `EvidenceBundle.relationships` (`kind="explicit_link"` or `kind="mentions"`) and are pre-aligned in `EvidenceBundle.cross_system_alignments`.
   - **Cartesian Pairing is Prohibited**: If Jira issue `PLAT-101` and GitHub PR #10 both exist in the bundle, but PR #10 does not mention `PLAT-101`, the evaluator must NEVER compare their states.
2. **Lexical Mentions are Correlation Signals**:
   A `DECLARED_MENTION` indicates that a developer cited a ticket key in a PR title, branch, or commit message. It is never treated as authoritative proof of work, task assignment, or issue completion.
3. **No Transitive Link Promotion**:
   If Commit `c0ffee1` mentions `PLAT-101` and PR #10 contains Commit `c0ffee1`, PR #10 is not promoted to linking to `PLAT-101` unless PR #10 independently cites `PLAT-101`.
4. **No Actor Linking**:
   A PR authored by `alice` and a Jira issue assigned to `Alice` are never linked by actor identity. Cross-system findings evaluate lifecycle states, never person identity.

---

## 9. Temporal Contract

Track B rules must handle temporal ordering with mathematical precision:

1. **Dual Temporal and State Dimensions**:
   Every cross-system comparison must maintain separate `state_comparison` (`CONSISTENT`, `CONFLICTING`, `INSUFFICIENT_EVIDENCE`) and `temporal_comparison` (`COHERENT`, `INVERTED`, `INDETERMINATE`).
2. **Temporal Inversion Handling**:
   - `pr_merged > jira_resolved`: Classified as `temporal_comparison="INVERTED"`, `state_comparison="INSUFFICIENT_EVIDENCE"` (or non-conflicting post-resolution activity).
   - *Rationale*: A developer merging a follow-up commit or backport PR after a ticket is marked "Done" is standard software engineering practice. It indicates workflow latency or follow-up maintenance, NEVER an evidence contradiction.
3. **Source Cutoff Enforcement**:
   - Any GitHub activity (commit, PR merge) occurring after `ObservationContext.source_cutoff_at` is flagged with `QualityIssue(code="invalid", subject_scope="provenance:temporal")` and categorized as `STALE`.
4. **Timezone Normalization**:
   - All datetime comparisons must operate on timezone-aware UTC timestamps. Naive datetimes are rejected at the normalization layer.
5. **Missing Timestamps**:
   - If a PR has `state="merged"` but `merged_at=None`, or if a commit has `committed_at=None`, the temporal comparison must evaluate to `INDETERMINATE`, never defaulting to Unix epoch or current time.

---

## 10. Provenance Contract

Track B findings must preserve end-to-end provenance so that any finding can be audited back to source records:

```text
    Raw Fixture Document ("fixtures/github/clean_github_week_1.json")
          │
          │ record_locator: "repositories[0].pull_requests[0].title"
          ▼
    EvidenceObservation[GitHubPullRequestState]
          │
          │ provenance_refs: (ProvenanceRef(..., "repositories[0].pull_requests[0]"),)
          ▼
    EvidenceRelationship[mentions] / CrossSystemStateAlignment
          │
          │ provenance_refs: (ProvenanceRef(..., "repositories[0].pull_requests[0]"),)
          ▼
    TrackBFinding (rule_id: "ORBIT-XB-01")
          │
          │ provenance_refs: (ProvenanceRef(..., "repositories[0].pull_requests[0]"),)
          ▼
    In-Memory Dereferencing Verification (dereference_provenance_ref == RESOLVED)
```

### Invariants:
1. Every `TrackBFinding` must carry non-empty `provenance_refs`.
2. Provenance references on cross-system findings must include the provenance of the citing artifact (e.g. PR locator and field path) and the cited issue.
3. Provenance must dereference in pure memory against `fixtures_by_id` using the Wave 1/2 engine ([`src/shadow_orbit/provenance_dereference.py`](file:///home/tecblic/orbit/src/shadow_orbit/provenance_dereference.py)).

---

## 11. Candidate Rule Inventory

We evaluated potential delivery-health rules against the current repository state:

| Rule ID | Proposed Name | Intended Question | Required Evidence | Evidence Available in EvidenceBundle | Deterministic Predicate | Expected Finding Disposition | Insufficient-Evidence Condition | Feasibility Classification |
|---|---|---|---|---|---|---|---|---|
| **`ORBIT-XB-01`** | `UNMERGED_PR_ON_RESOLVED_ISSUE` | Does an unmerged PR reference an issue marked resolved/done? | `CrossSystemStateAlignment` + `JiraIssueState` + `GitHubPullRequestState` | ✅ Available in `bundle.cross_system_alignments` | `jira.status_category == "done"` AND `pr.state == "open"` | `TRIGGERED` (`sufficiency="SUPPORTED"`) | PR state unknown, or target Jira issue unobserved | **`READY_FOR_IMPLEMENTATION`** |
| **`ORBIT-XB-02`** | `MERGED_PR_ON_UNRESOLVED_ISSUE` | Has code merged to the base branch while the Jira issue remains incomplete? | `CrossSystemStateAlignment` + `JiraIssueState` + `GitHubPullRequestState` | ✅ Available in `bundle.cross_system_alignments` | `pr.state == "merged"` AND `jira.status_category in {"todo", "in_progress", "blocked"}` | `TRIGGERED` (`sufficiency="SUPPORTED"`) | PR merge timestamp missing or Jira status unknown | **`READY_FOR_IMPLEMENTATION`** |
| **`ORBIT-XB-03`** | `POST_RESOLUTION_WORK_ACTIVITY` | Did code modifications merge/commit after Jira recorded ticket resolution? | `CrossSystemStateAlignment` with `temporal_comparison == "INVERTED"` | ✅ Available in `bundle.cross_system_alignments` | `temporal_comp == "INVERTED"` AND `(pr_merged > jira_resolved OR commit_time > jira_resolved)` | `TRIGGERED` (`sufficiency="SUPPORTED"`) | Missing `resolved_at` or missing `merged_at`/`committed_at` | **`READY_FOR_IMPLEMENTATION`** |
| **`ORBIT-XB-04`** | `OVERDUE_HIGH_PRIORITY_ISSUE` | Is a high-priority work item past its due date without completion? | `EvidenceObservation[JiraIssueState]` + `ReviewPeriod` | ✅ Available in `bundle.observations` | `jira.priority_band == "high"` AND `jira.due_at < review_cutoff_at` AND `jira.status_category != "done"` | `TRIGGERED` (`sufficiency="PROVEN"`) | `jira.due_at is None` | **`READY_FOR_IMPLEMENTATION`** *(Single-system on bundle)* |
| **`ORBIT-XB-05`** | `STALLED_WORK_ON_EVIDENCE_BUNDLE` | Has an in-progress issue remained inactive beyond the configured threshold? | Issue changelog transitions (`changes`) or commit activity stream | ❌ **NOT AVAILABLE**: `JiraIssueState` lacks `changes` | Days since last meaningful status transition $\ge$ threshold | `SUPPRESSED` | `JiraIssueState` lacks status change history | **`REQUIRES_SCHEMA_CHANGE`** *(or new metric definition)* |
| **`ORBIT-XB-06`** | `NATIVE_LINK_STATUS_MISMATCH` | Does an explicit integration link contradict the associated ticket status? | `EXPLICIT_LINK` relationships from native Jira/GitHub issue links | ❌ **NOT AVAILABLE**: v1 fixture schemas have no structured link fields | `rel.kind == "explicit_link"` AND states contradict | `TRIGGERED` (`sufficiency="PROVEN"`) | `explicit_links == ()` | **`REQUIRES_SCHEMA_CHANGE`** *(Fixture v2 schema)* |
| **`ORBIT-XB-07`** | `LIVE_PR_COMPLETION_VERIFICATION` | Does real-time remote GitHub PR status verify offline ticket completion claims? | Remote GitHub GraphQL/REST API query | ❌ **NOT AVAILABLE**: Live network access is forbidden | Remote API returns merged/closed status | N/A | Offline proving mode active | **`REQUIRES_CONNECTOR`** |
| **`ORBIT-XB-08`** | `DEVELOPER_PRODUCTIVITY_SCORING` | Measure individual developer delivery efficiency by correlating PR volume to tickets | Commit author strings + Jira assignee strings | ❌ **PROHIBITED** | Heuristic ratio of PRs to completed tickets | N/A | Prohibited by non-inferential safety rules | **`NOT_DETERMINISTICALLY_SUPPORTED`** |

---

## 12. Anti-Inference Audit

Reconnaissance inspected potential failure modes where an evaluator could manufacture claims without evidence:

1. **The "No Activity" Fallacy**:
   - *Risk*: Concluding that because no GitHub commits cite `PLAT-101`, no engineering work was performed.
   - *Forensic Truth*: Commits may reside on private branches, commit messages may omit the prefix, or development may be in an unobserved repository. `Unknown != False`.
2. **The "Merge = Done" Fallacy**:
   - *Risk*: Assuming that because PR #10 merged, Jira issue `PLAT-101` was successfully implemented and resolved.
   - *Forensic Truth*: A merged PR may be an incomplete spike, a partial subtask, or a bugged change subsequently reverted. Ticket closure requires authoritative Jira resolution evidence.
3. **The "Temporal Inversion = Contradiction" Fallacy**:
   - *Risk*: Classifying a PR merged 2 days after ticket resolution as `CONFLICTING`.
   - *Forensic Truth*: Post-resolution merges occur routinely for hotfixes, release backports, and documentation polish. This is workflow lag, never a logical contradiction.
4. **The "Same Username = Same Person" Fallacy**:
   - *Risk*: Asserting that PR author `alice` and Jira assignee `Alice` are the same human being, and generating developer-level accountability findings.
   - *Forensic Truth*: Usernames in disparate source systems are unauthenticated strings. Actor identity resolution is explicitly out of scope.
5. **The "Coexistence = Association" Fallacy**:
   - *Risk*: Comparing Jira issue `PLAT-101` against every GitHub PR in the same repository fixture.
   - *Forensic Truth*: Coexistence in a fixture is not a relationship. Cross-system evaluation is strictly restricted to established `DECLARED_MENTION` or `EXPLICIT_LINK` edges.
6. **The "Heuristic Health Score" Fallacy**:
   - *Risk*: Computing an aggregate percentage "Delivery Health Score" (e.g. 78%) from cross-system findings.
   - *Forensic Truth*: Arbitrary weights and probabilistic scoring conceal deterministic facts. Track B outputs discrete, evidence-backed findings, never aggregate confidence scores.

---

## 13. Architectural Options

We identify three distinct architectural options for Track B:

### Option 1: Dedicated Pure `EvidenceBundle` Evaluator (RECOMMENDED)
* **Design**: Implement a standalone pure function `evaluate_evidence_bundle(bundle: EvidenceBundle, review_period: ReviewPeriod | None = None) -> EvidenceBundleEvaluationResult` in `src/shadow_orbit/evidence_evaluation.py`.
* **Data Flow**: Consumes pre-assembled and pre-validated `EvidenceBundle` directly. Evaluates candidate rules `ORBIT-XB-01` through `ORBIT-XB-04`.
* **Coupling**: Zero coupling to Track A (`evaluate_week_one_rules`) or `NormalizedFixture`.
* **Determinism & Provenance**: 100% deterministic, in-memory, bit-for-bit repeatable, with full `ProvenanceRef` preservation.
* **Migration Impact**: None. Track A and the Mahout qualification specimen remain 100% frozen.
* **Risk**: Low. Operates entirely within the approved Milestone 2 boundaries.

### Option 2: Hybrid Pipeline Bridge
* **Design**: Have Track B internally invoke Track A's `evaluate_week_one_rules()` on an adapted `NormalizedFixture`, and then merge cross-system findings onto the Track A results.
* **Coupling**: High coupling. Binds Track B to Jira-specific `WorkItem` structures and risks leaking Track B changes into Track A.
* **Risk**: High. Violates strict dual-track isolation and risks destabilizing the frozen Mahout baseline.

### Option 3: Two-Pass Monolithic Evaluation Engine
* **Design**: Refactor both Track A and Track B into a unified evaluation framework that accepts raw fixture documents and emits a single consolidated review artifact.
* **Coupling**: Extreme. Replaces the core architecture of ORBIT.
* **Risk**: Prohibitive. Directly violates Section 3 absolute scope boundaries.

---

## 14. Open Questions

The following technical questions require resolution prior to Track B implementation:

1. **Review Period Parameterization**:
   Should `evaluate_evidence_bundle()` receive an explicit `ReviewPeriod` dataclass, or should it infer the review boundary from the `ObservationContext` instances present in the `EvidenceBundle`?
   - *Observation*: `ObservationContext` already contains `observed_interval_starts_at`, `observed_interval_ends_at_exclusive`, and `source_cutoff_at`.
2. **Review Artifact Integration**:
   Should Track B findings be serialized into a new section of the machine-derived review artifact (e.g. `cross_system_findings`), or should they remain in a dedicated `EvidenceBundleEvaluationResult` JSON container during Milestone 2?
3. **Changelog History in Future Schemas**:
   Should Milestone 3 expand `JiraIssueState` to include status change history so that `STALLED_WORK` can eventually be evaluated on `EvidenceBundle`?

---

## 15. Human Approval Decisions

The following architectural decisions are presented for human review and sign-off:

### Decision D1: Container Input Boundary
* **Question**: Should Track B consume `EvidenceBundle` directly rather than normalized fixtures independently?
* **Supported by Evidence?**: **YES**. ADR-005 D4 and the Wave 3 implementation establish `EvidenceBundle` as the sole canonical container for fused cross-system evidence. Direct fixture consumption would bypass bundle validation.
* **Recommendation**: **APPROVE D1**. Track B consumes `EvidenceBundle` directly.

### Decision D2: Provenance-Backed Findings
* **Question**: Should Track B produce findings only from validated, provenance-backed evidence?
* **Supported by Evidence?**: **YES**. Wave 2 wired bounded provenance dereferencing into bundle validation. Findings without provenance cannot be forensically audited.
* **Recommendation**: **APPROVE D2**. Every finding must carry supporting `provenance_refs`.

### Decision D3: Explicit Sufficiency Taxonomy
* **Question**: Should insufficient evidence be represented explicitly rather than suppressing the finding?
* **Supported by Evidence?**: **YES**. `Unknown != False`. Suppressing incomplete observations conceals data quality deficiencies.
* **Recommendation**: **APPROVE D3**. Emit findings with `sufficiency="INSUFFICIENT_EVIDENCE"` when required fields are missing.

### Decision D4: Complete Separation from Week-One Evaluator
* **Question**: Should Track B remain a separate evaluator from `evaluate_week_one_rules()`?
* **Supported by Evidence?**: **YES**. Track A is the frozen governing baseline (`6d82d12`). Refactoring or coupling Track A introduces unacceptable regression risk to Mahout qualification.
* **Recommendation**: **APPROVE D4**. Maintain dual-track evaluation with zero coupling.

### Decision D5: Relationship-Bound Cross-System Findings
* **Question**: Should cross-system findings be restricted to established `EXPLICIT_LINK` / `DECLARED_MENTION` relationships?
* **Supported by Evidence?**: **YES**. Wave 3 confirmed that cartesian pairing produces spurious associations.
* **Recommendation**: **APPROVE D5**. Zero cross-system findings without an established relationship edge.

### Decision D6: Independent Temporal and State Dimensions
* **Question**: Should temporal and state comparisons remain separate dimensions?
* **Supported by Evidence?**: **YES**. ADR-005 established that temporal inversion is not a state conflict.
* **Recommendation**: **APPROVE D6**. Enforce `temporal_comparison` and `state_comparison` separation.

### Decision D7: Pure In-Memory Operation
* **Question**: Should Track B remain pure/in-memory until live connectors are separately authorized?
* **Supported by Evidence?**: **YES**. `Jira mutations = 0` and offline repeatability require pure in-memory execution.
* **Recommendation**: **APPROVE D7**. Zero network access, zero external I/O.

### Decision D8: Authorized Candidate Rules for Initial Implementation
* **Question**: Which candidate rule(s), if any, are sufficiently specified for the next implementation wave?
* **Architectural Assessment**:
  - `ORBIT-XB-01` (`UNMERGED_PR_ON_RESOLVED_ISSUE`): **READY**
  - `ORBIT-XB-02` (`MERGED_PR_ON_UNRESOLVED_ISSUE`): **READY**
  - `ORBIT-XB-03` (`POST_RESOLUTION_WORK_ACTIVITY`): **READY**
  - `ORBIT-XB-04` (`OVERDUE_HIGH_PRIORITY_ISSUE`): **READY**
  - `ORBIT-XB-05` (`STALLED_WORK_ON_EVIDENCE_BUNDLE`): **BLOCKED (Requires changelog schema expansion)**
  - `ORBIT-XB-06` (`NATIVE_LINK_STATUS_MISMATCH`): **BLOCKED (Requires fixture v2 schema)**
* **Status**: **OPEN FOR HUMAN APPROVAL**. Human reviewer to designate which ready rules to implement in Wave 4 Implementation.

---

## 16. Explicit Non-Goals

The following activities are explicitly declared out of scope for Wave 4:
1. Writing production code for `evaluate_evidence_bundle()`.
2. Modifying `evaluate_week_one_rules()` or Track A types.
3. Modifying `calculate_supporting_facts()`.
4. Creating live network connectors to Jira or GitHub.
5. Altering Mahout allowlists, raw captures, or golden artifacts.
6. Performing heuristic developer identity matching.
7. Calculating probabilistic confidence scores or risk rankings.

---

## 17. Forensic Safety Verification & Wave 4 Classification

### Forensic Verification Checks:
1. `git status`:
   - No untracked modifications.
   - All Wave 1–3 files staged cleanly.
2. `git rev-parse HEAD`: `e967ad57ea3b37cef4266134537acbb34e9ae715` (Governing baseline preserved).
3. `git rev-parse develop`: `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (Protected baseline preserved).
4. `git merge-base HEAD develop`: `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (Clean divergence).
5. Regression test suite: **666 passed, 0 failed, 0 skipped**.
6. Mahout qualification: **412 accepted, 12 findings, 0 mutations, repeatable=True**.

### Wave 4 Reconnaissance Classification:
**PASS WITH QUALIFICATIONS**

*Qualifications Rationale:*
Reconnaissance successfully establishes the full contract, boundaries, and candidate rules for Track B evaluation. However, implementation is qualified by:
1. `JiraIssueState` lacking status changelog history, preventing direct reuse of Track A's `STALLED_WORK` rule.
2. Existing fixture schemas lacking native structured link fields, restricting current cross-system findings to `sufficiency="SUPPORTED"` (declared mentions).
3. Final candidate rule authorization awaiting human sign-off on Decision D8.

---

## 18. Historical Wave 4 Human Review Gate

Wave 4 reconnaissance was reviewed by the human software architect. The review identified two critical contract issues requiring formal reconciliation before any implementation:
1. **Issue A (XB-03 Semantic Risk)**: Treating temporal inversion as an implied delivery health defect or workflow failure.
2. **Issue B (XB-04 Temporal Contract)**: Assuming `JiraIssueState` represents state as of `review_cutoff_at` without proving whether it reflects cutoff state or latest capture state.

These issues are resolved in Section 19 below (Wave 4A).

---

## 19. Wave 4A Contract Reconciliation

**Pass:** 4 / Milestone 2 — Cross-System Evidence & Track B Evaluation Boundary  
**Sub-Wave:** 4A (Track B Contract Reconciliation — Documentation & Architecture Only)  
**Date:** 2026-09-28  

Wave 4A reconciles the candidate rule contracts without modifying any production code or historical baseline invariants.

### 19.1 Issue A — Semantic Clarification of ORBIT-XB-03

#### Forensic Finding:
Candidate rule `ORBIT-XB-03` (`POST_RESOLUTION_WORK_ACTIVITY`) operates on `alignment.temporal_comparison == "INVERTED"`, indicating that a GitHub commit or PR merge occurred after Jira recorded the issue as resolved (`resolved_at`).

Human architectural review correctly determined that temporal inversion is an **observed temporal fact**, not an assessment of defect, conflict, or developer negligence. In standard software engineering, post-resolution activity occurs routinely for benign reasons:
- Documentation polish, test updates, and telemetry additions.
- Release-branch cherry-picks and maintenance backports.
- Asynchronous merge queue delays following ticket administrative closure.
- Minor cleanup refactorings citing the ticket key.

#### Reconciled Semantic Contract:
* `ORBIT-XB-03` is classified strictly as an **OBSERVATIONAL EVIDENCE FINDING**.
* The contract explicitly distinguishes:
  - **FACT**: GitHub activity associated with an established Jira issue relationship occurred at a timestamp after the recorded Jira resolution timestamp.
  - **PROHIBITED INFERENCE**: The Jira issue was incorrectly resolved, work was late/defective, the ticket should have remained open, a developer violated process, or the Jira state was "wrong" (`CONFLICTING`).
* **Disposition**: `TRIGGERED` (as an observational finding).
* **Sufficiency**: `SUPPORTED` (on `DECLARED_MENTION`) or `PROVEN` (on `EXPLICIT_LINK`).

---

### 19.2 Issue B — Temporal Contract Audit of ORBIT-XB-04

#### Forensic Finding:
Candidate rule `ORBIT-XB-04` (`OVERDUE_HIGH_PRIORITY_ISSUE`) proposed evaluating:
```python
jira.priority_band == "high" AND jira.due_at < review_cutoff_at AND jira.status_category != "done"
```
Reconnaissance investigated: **What point in time does `JiraIssueState.status_category` represent?**

The forensic audit of the evidence pipeline established:
1. `jira_evidence_adapter.py` lines 296-310 constructs `JiraIssueState` by copying `work_item.status_category` directly from `NormalizedFixture`.
2. Transition changelogs (`changes: tuple[Change, ...]`) are discarded. `JiraIssueState` carries only scalar snapshot values.
3. Neither `normalization.py` nor `jira_evidence_adapter.py` performs any historical state reconstruction or rollback to `review_cutoff_at`.
4. `JiraIssueState.status_category` represents the **latest observed state** in the source fixture document at capture/export time, NOT the state as of `review_cutoff_at`.

#### The Critical Scenario:
* `due_at` = June 1
* `review_cutoff_at` = June 5
* Jira ticket resolved = June 8
* Fixture export = June 8

In this scenario:
* In `EvidenceBundle`, `jira.status_category == "done"`.
* Evaluating `jira.status_category != "done"` produces `False`.
* The rule fails to trigger, even though the ticket was incomplete and overdue as of June 5.

Because `EvidenceBundle` does not carry `changes`, it cannot invoke `status_at_period_end()` to reconstruct historical status at cutoff.

#### Reconciled Status:
Under the governing decision tree:
* The repository does **NOT** prove that `JiraIssueState` is a valid point-in-time snapshot at the review cutoff.
* The repository only proves that `JiraIssueState` represents the latest observed state in the fixture capture.
* Therefore, `ORBIT-XB-04` **MUST NOT be considered ready for implementation**.
* It is reclassified as: **`REQUIRES TEMPORAL CONTRACT`**.

---

### 19.3 Rule Classification Reconciliation Table

The following table records the previous Wave 4 reconnaissance classifications versus the reconciled Wave 4A classifications:

| Rule ID | Rule Name | Previous Classification (Wave 4) | Reconciled Classification (Wave 4A) | Reason for Change | Evidence from Repository Audit |
|---|---|---|---|---|---|
| **`ORBIT-XB-01`** | `UNMERGED_PR_ON_RESOLVED_ISSUE` | `READY_FOR_IMPLEMENTATION` | `READY_FOR_IMPLEMENTATION` | No change. Predicate relies on snapshot states (`open` vs `done`) over established relationship. | `CrossSystemStateAlignment` + `JiraIssueState` + `GitHubPullRequestState`. |
| **`ORBIT-XB-02`** | `MERGED_PR_ON_UNRESOLVED_ISSUE` | `READY_FOR_IMPLEMENTATION` | `READY_FOR_IMPLEMENTATION` | No change. Predicate relies on snapshot states (`merged` vs incomplete) over established relationship. | `CrossSystemStateAlignment` + `JiraIssueState` + `GitHubPullRequestState`. |
| **`ORBIT-XB-03`** | `POST_RESOLUTION_WORK_ACTIVITY` | `READY_FOR_IMPLEMENTATION` | **`READY_FOR_IMPLEMENTATION (OBSERVATIONAL ONLY)`** | Semantics tightened: restricted strictly to an observational finding. Must not infer defect, conflict, or workflow violation. | `CrossSystemStateAlignment.temporal_comparison == "INVERTED"`. |
| **`ORBIT-XB-04`** | `OVERDUE_HIGH_PRIORITY_ISSUE` | `READY_FOR_IMPLEMENTATION` | **`REQUIRES_TEMPORAL_CONTRACT`** | `JiraIssueState` represents latest observed capture state, not state as of `review_cutoff_at`. Cannot deterministically evaluate historical overdue status without changelog or snapshot contract. | `jira_evidence_adapter.py` lines 296-310 (lacks `changes`); `temporal.py` line 96 (`status_at_period_end` unusable). |
| **`ORBIT-XB-05`** | `STALLED_WORK_ON_EVIDENCE_BUNDLE` | `REQUIRES_SCHEMA_CHANGE` | `REQUIRES_SCHEMA_CHANGE` | No change. `JiraIssueState` lacks transition history `changes`. | `evidence_types.py` lines 230-249. |
| **`ORBIT-XB-06`** | `NATIVE_LINK_STATUS_MISMATCH` | `REQUIRES_SCHEMA_CHANGE` | `REQUIRES_SCHEMA_CHANGE` | No change. Fixture schemas lack native structured link fields. | `cross_system_fusion.py` lines 122-132 (`explicit_links` is empty). |
| **`ORBIT-XB-07`** | `LIVE_PR_COMPLETION_VERIFICATION` | `REQUIRES_CONNECTOR` | `REQUIRES_CONNECTOR` (BLOCKED) | No change. Offline proving boundary strictly prohibits live network access. | `test_gate2_jira_qualification.py`. |
| **`ORBIT-XB-08`** | `DEVELOPER_PRODUCTIVITY_SCORING` | `NOT_DETERMINISTICALLY_SUPPORTED` | `NOT_DETERMINISTICALLY_SUPPORTED` (PROHIBITED) | No change. Prohibited by non-inferential safety rules (actor identity unverified). | Anti-inference rules (ADR-005, ADR-006). |

---

### 19.4 What Remains Unknown / Open Dependencies

1. **Jira Temporal Ingestion Contract**: Whether production Jira ingestion pipelines will capture snapshots pegged precisely to `review_cutoff_at`, or whether `EvidenceBundle` schema must be extended to carry `changes: tuple[Change, ...]` for historical reconstruction.
2. **Track B Wave 5 Authorization**: Human authorization to implement the evaluation engine for the three ready rules: `ORBIT-XB-01`, `ORBIT-XB-02`, and `ORBIT-XB-03` (observational).

---

## 20. STOP — Awaiting Human Architectural Authorization

Wave 4A contract reconciliation is complete.

**DO NOT PROCEED TO TRACK B IMPLEMENTATION.**  
**STOP — Awaiting human architectural authorization for Track B implementation.**

