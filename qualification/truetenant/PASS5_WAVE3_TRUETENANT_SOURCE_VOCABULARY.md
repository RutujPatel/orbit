# PASS 5 / WAVE 3 — TrueTenant Source Vocabulary (Phase 1 Freeze)

**Phase:** 1 — Source Vocabulary Freeze  
**Date:** 2026-09-30  
**Governance:** READ ONLY — no evaluator run, no canonical assignment, no mapping decisions here  
**Source corpus:** `orbit-private/truetenant/`  
**Frozen before:** mapping contract, adapter implementation, evaluation  

---

## Corpus Inventory

| Metric | Value |
|--------|-------|
| Total issues (CSV) | 112 |
| Total changelog records | 1,022 |
| Issues with changelog history | 109 |
| Issues with zero changelog entries | 3 (TT-38, TT-41, TT-46) |
| Distinct statuses in CSV (final state) | 9 |
| Distinct statuses seen in changelog transitions | 11 |
| Total status field change events | 387 |
| Timestamp format | Epoch milliseconds (integer) |

---

## Zero-History Issues

| Issue Key | Final Status | Priority | Type |
|-----------|-------------|----------|------|
| TT-38 | To Do | Medium | Epic |
| TT-41 | To Do | Medium | Task |
| TT-46 | To Do | Medium | Epic |

These issues have no changelog history. Their current state is observable only from the CSV snapshot.

---

## Complete Source Status Vocabulary

This table lists every status string observed in either the CSV snapshot or the changelog transition history.  
**No canonical assignments are made in this document.**

| Status | CSV Count (final) | → To (transitions in) | ← From (transitions out) | Observation |
|--------|------------------|-----------------------|--------------------------|-------------|
| `To Do` | 19 | 1 | 102 | High outflow — common start state; rarely a destination |
| `Awaiting Approval` | 8 | 61 | 60 | Symmetric in/out — intermediate stage; not terminal |
| `Approved` | 11 | 59 | 43 | Intermediate; feeds into Dev In Progress |
| `Dev In Progress` | 4 | 82 | 76 | High throughput; most common active state in transitions |
| `Ready For QA` | 12 | 75 | 62 | QA gate; high traffic; feeds Done or QA Passed |
| `QA Passed` | 2 | 48 | 40 | Post-QA approval state; feeds Done |
| `Done` | 52 | 52 | 0 | No outflow — strongly terminal-looking |
| `Feature Not Required` | 3 | 3 | 0 | No outflow — terminal-looking; disposition/rejection |
| `Not an Issue` | 1 | 1 | 0 | No outflow — terminal-looking; disposition/rejection |
| `ReOpen` | 0 | 4 | 3 | Not in CSV; seen in changelog only; rework re-entry |
| `Pending For More Information` | 0 | 1 | 1 | Not in CSV; very rare; blocking/waiting state |

**Total distinct statuses:** 11

---

## Status Transition Flow (Observed)

```
To Do
  ├─→ Awaiting Approval (60×)    [approval gating path]
  ├─→ Dev In Progress (37×)      [direct dev path]
  ├─→ Done (3×)                  [direct closure — rare]
  ├─→ Approved (1×)              [unusual direct skip]
  └─→ Feature Not Required (1×)  [early triage closure]

Awaiting Approval
  ├─→ Approved (58×)             [normal approval path]
  ├─→ Feature Not Required (1×)  [rejection during approval]
  └─→ Pending For More Information (1×)  [blocked for info]

Pending For More Information
  └─→ Awaiting Approval (1×)    [return to approval]

Approved
  ├─→ Dev In Progress (42×)      [work begins post-approval]
  └─→ To Do (1×)                 [re-queued — unusual]

Dev In Progress
  ├─→ Ready For QA (75×)         [primary dev completion path]
  └─→ Not an Issue (1×)          [disposition during dev]

Ready For QA
  ├─→ QA Passed (48×)            [primary QA success]
  ├─→ Done (10×)                 [direct closure from QA — fast path]
  └─→ ReOpen (4×)                [QA failure → rework]

ReOpen
  └─→ Dev In Progress (3×)       [rework restarts dev]

QA Passed
  ├─→ Done (39×)                 [primary completion path]
  └─→ Feature Not Required (1×)  [disposition after QA]

Done           [0 outflow — terminal]
Feature Not Required  [0 outflow — terminal]
Not an Issue   [0 outflow — terminal]
```

---

## Status Character Analysis (Descriptive — Pre-Mapping)

| Status | Terminal? | Nature | Workflow position |
|--------|-----------|--------|-------------------|
| `To Do` | No | Planning/backlog | Entry point |
| `Awaiting Approval` | No | Approval-gating | Pre-dev gate |
| `Approved` | No | Approval-resolved | Post-approval, pre-dev |
| `Dev In Progress` | No | Active development | Dev execution |
| `Ready For QA` | No | QA-gating | Dev complete, QA pending |
| `QA Passed` | No | QA-resolved | Post-QA approval |
| `Done` | **YES** | Completion | Terminal — standard completion |
| `Feature Not Required` | **YES** | Disposition/rejection | Terminal — non-implementation |
| `Not an Issue` | **YES** | Disposition/rejection | Terminal — invalid/non-issue |
| `ReOpen` | No | Rework/exception | Post-QA failure re-entry |
| `Pending For More Information` | No | Blocking/waiting | Approval hold |

**Terminal statuses (zero outflow):** `Done`, `Feature Not Required`, `Not an Issue`  
**Approval-domain statuses:** `Awaiting Approval`, `Approved`, `Pending For More Information`  
**QA-domain statuses:** `Ready For QA`, `QA Passed`  
**Rework statuses:** `ReOpen`  
**CSV-only (not in changelog transitions):** None — all CSV statuses appear in transitions  
**Changelog-only (not in CSV final state):** `ReOpen`, `Pending For More Information`

---

## Issue Type and Priority Distribution

| Issue Type | Count |
|-----------|-------|
| Story | 62 |
| Bug | 40 |
| Epic | 5 |
| Task | 5 |

| Priority | Count |
|----------|-------|
| Medium | 111 |
| High | 1 |

---

## Data Quality Observations (Pre-Normalization)

- Timestamps in changelog are **epoch milliseconds** (integer) — not ISO 8601 strings  
- CSV timestamps are formatted as `DD/Mon/YY H:MM AM/PM` (e.g., `28/Jul/26 3:34 PM`)  
- `Resolution` column in CSV is empty for all non-Done statuses  
- `Due date` column is sparsely populated  
- `Assignee` field is populated for many but not all issues  
- `ReOpen` and `Pending For More Information` have no CSV representation (transitional states only)  
- 1 issue (TT-2) has the only `High` priority  
- The mapping between `Issue id` (CSV numeric) and `issueId` (changelog numeric string) is the join key

---

*Vocabulary freeze complete. No canonical assignments made. Mapping contract follows in Phase 2/3.*
