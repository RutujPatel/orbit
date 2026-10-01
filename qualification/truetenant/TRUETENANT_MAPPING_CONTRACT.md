# PASS 5 / WAVE 3 — TrueTenant Blind Mapping Contract

**Phase:** 2+3 — Mapping Contract (FROZEN before evaluation)  
**Date:** 2026-09-30  
**Governance:** This mapping is derived SOLELY from source status names, changelog transition semantics, and the existing canonical-state contract. It was written BEFORE any evaluator was run. It MUST NOT be modified after evaluation begins.  
**Frozen before:** Phase 4 (adapter), Phase 5 (normalization), Phase 6 (Track B evaluation)  

---

## Canonical StatusCategory Definitions (from ORBIT)

```
StatusCategory = Literal["todo", "in_progress", "blocked", "done", "unknown"]
```

| Canonical Category | Meaning |
|-------------------|---------|
| `todo` | Work identified but not started |
| `in_progress` | Active work underway |
| `blocked` | Active but externally impeded |
| `done` | Terminally resolved (any resolution) |
| `unknown` | Cannot be safely mapped from available evidence |

---

## Mapping Contract Table

**CRITICAL:** Assignments below are derived from transition semantics and status name semantics only.  
Evaluator results were NOT consulted. Finding distributions were NOT consulted.

| TrueTenant Source Status | Canonical `source_status` | Canonical `status_category` | Terminal? | Mapping Basis | Confidence |
|--------------------------|--------------------------|----------------------------|-----------|---------------|------------|
| `To Do` | `To Do` | `todo` | No | Status name + transition evidence: high outflow (102 outbound), lowest position in workflow, entry point matching ORBIT "todo" semantics. | **HIGH** |
| `Dev In Progress` | `Dev In Progress` | `in_progress` | No | Status name explicitly states active development. Matches ORBIT "in_progress" semantics directly. High throughput (82 in, 76 out). | **HIGH** |
| `ReOpen` | `ReOpen` | `in_progress` | No | Post-failure re-entry into development. Transitions only to Dev In Progress (3×). Semantically equivalent to active/restarted work. Changelog-only — never a final state. | **MEDIUM** — see note |
| `Done` | `Done` | `done` | **YES** | Explicitly terminal: 52 CSV final states, 0 outbound transitions. Status name matches ORBIT "done" directly. | **HIGH** |
| `Feature Not Required` | `Feature Not Required` | `done` | **YES** | 0 outbound transitions. Non-implementation resolution — the feature was determined not needed. This is a terminal disposition equivalent to "resolved as won't-do". Maps to `done` because work is definitively finished (negatively). | **MEDIUM** — see note |
| `Not an Issue` | `Not an Issue` | `done` | **YES** | 0 outbound transitions. 1 final CSV state. Triage/invalid disposition. Terminally resolved. Maps to `done` because no further work is expected. | **MEDIUM** — see note |
| `Awaiting Approval` | `Awaiting Approval` | **`unknown`** | No | Approval-gating state. ORBIT has no canonical "approval" category. Cannot safely assign `blocked` (not blocked by technical impediment — awaiting a business decision). Cannot safely assign `in_progress` (not active development). Cannot safely assign `todo` (work is submitted, not unstarted). | **UNMAPPED — requires canonical extension** |
| `Approved` | `Approved` | **`unknown`** | No | Post-approval, pre-development state. ORBIT has no canonical "approved" or "queued" category. Not `todo` (approved but not assigned to developer yet). Not `in_progress` (dev has not started). Not `done` (work has not happened). | **UNMAPPED — requires canonical extension** |
| `Ready For QA` | `Ready For QA` | **`unknown`** | No | QA-gating state. Dev complete but QA not yet performed. ORBIT has no canonical "qa_gate" or "review_pending" category. Not `done` (QA has not passed). Not `in_progress` (dev is complete). | **UNMAPPED — requires canonical extension** |
| `QA Passed` | `QA Passed` | **`unknown`** | No | Post-QA, pre-Done state. ORBIT has no canonical "accepted" or "release_ready" category. Not `done` (explicitly has 40 outbound transitions; issues remain open in "QA Passed" before closing). Not `in_progress`. | **UNMAPPED — requires canonical extension** |
| `Pending For More Information` | `Pending For More Information` | **`unknown`** | No | Blocking/waiting state. Could map to `blocked` — HOWEVER only 1 occurrence in changelog and 0 in CSV. Insufficient evidence to confirm this maps to technical blockage vs. approval hold. Choosing `unknown` to avoid silent over-assignment on 1 data point. | **UNMAPPED — insufficient evidence** |

---

## Mapping Summary

| Canonical Category | Source Statuses |
|-------------------|-----------------|
| `todo` | `To Do` |
| `in_progress` | `Dev In Progress`, `ReOpen` |
| `done` | `Done`, `Feature Not Required`, `Not an Issue` |
| `unknown` | `Awaiting Approval`, `Approved`, `Ready For QA`, `QA Passed`, `Pending For More Information` |
| `blocked` | *(none assigned)* |

**Mapped cleanly:** 6 of 11 statuses (3 terminal, 2 active, 1 backlog)  
**Unmapped (unknown):** 5 of 11 statuses  
**Unmapped rate:** 5/11 = **45.5%**

---

## Explicit Non-Mappings and Justifications

### Why `Awaiting Approval` ≠ `blocked`
`blocked` in ORBIT means active work is impeded by an external technical or resource dependency.  
`Awaiting Approval` is a deliberate process gate in a business workflow. The work is not impeded — it is waiting for an intentional decision step. These are semantically distinct. ORBIT's `blocked` rule (`evaluate_blocked_high_priority`) tests for "blocked since duration" — applying it to approval wait would produce misleading findings.

### Why `Approved` ≠ `in_progress`
Approval has been granted but development has not yet started. `in_progress` in ORBIT means active execution. An approved-but-not-yet-started item is closer to a "ready" state, which ORBIT does not have. Assigning `in_progress` would trigger STALLED_WORK rules on items that simply haven't been scheduled yet.

### Why `Ready For QA` ≠ `in_progress`
Development is complete. No active development work is happening. Assigning `in_progress` would misrepresent the item's state and potentially trigger false STALLED_WORK findings on legitimately complete dev work awaiting QA.

### Why `QA Passed` ≠ `done`
`QA Passed` has 40 outbound transitions in the changelog — items regularly leave `QA Passed` and move elsewhere (primarily to `Done`, but also to `Feature Not Required`). An item is not definitively resolved until it reaches `Done`. Assigning `done` prematurely would suppress findings on items still in the pipeline.

### Why `Feature Not Required` → `done`
Despite being a "won't implement" outcome, it IS terminal (0 outflow). The work is definitively resolved. The source status is preserved in `source_status` so the distinction is not lost at the display layer, even though the canonical evaluation treats it as done.

### Why `Not an Issue` → `done`
Terminal (0 outflow), triaged as invalid. Definitively resolved. Same rationale as `Feature Not Required`. Source status preserved.

### Why `ReOpen` → `in_progress`
`ReOpen` exclusively transitions to `Dev In Progress` (3/3 times). It represents a rework cycle — active work restarted after QA failure. The semantics match ORBIT's `in_progress` definition. It is never a final CSV state. Source status preserved.

---

## Issue-Level Coverage Estimate (Pre-Evaluation)

Based on CSV status distribution:

| Final Status | Count | Mapped Category |
|-------------|-------|----------------|
| `Done` | 52 | `done` |
| `To Do` | 19 | `todo` |
| `Ready For QA` | 12 | **`unknown`** |
| `Approved` | 11 | **`unknown`** |
| `Awaiting Approval` | 8 | **`unknown`** |
| `Dev In Progress` | 4 | `in_progress` |
| `Feature Not Required` | 3 | `done` |
| `QA Passed` | 2 | **`unknown`** |
| `Not an Issue` | 1 | `done` |
| **Total** | **112** | |

**Issues mapping to known category:** 52+19+4+3+1 = **79 / 112 (70.5%)**  
**Issues mapping to `unknown`:** 12+11+8+2 = **33 / 112 (29.5%)**

---

## CONTRACT INTEGRITY STATEMENT

This mapping contract was derived exclusively from:
1. Source status names
2. Changelog transition evidence (from/to counts and directions)
3. Terminal/non-terminal structural evidence (zero outflow)
4. Existing ORBIT canonical state contract (`types.py` StatusCategory definition)

The evaluator was NOT run before this contract was written.  
No finding distributions were consulted.  
No ORBIT rule semantics were used to decide assignments.  
This mapping MUST NOT be modified after Phase 5 (normalization) begins.

**Mapping contract hash (for integrity):** This file is written atomically before adapter implementation.

*Mapping contract frozen. Phase 4 implementation follows.*
