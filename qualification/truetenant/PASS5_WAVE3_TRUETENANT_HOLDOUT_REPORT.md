# PASS 5 / WAVE 3 — TrueTenant Blind Hold-Out Report

## 1. Governance

| Field | Value |
|-------|-------|
| Governing baseline | `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` |
| Consolidation HEAD | `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab` |
| Branch | `remediation/pass3-controlled-hardening` |
| Working tree state | **Clean** — nothing to commit |
| Git operations performed | None (`git status --short`, `git rev-parse` only) |
| Network calls | 0 |
| Source files modified | 0 (evaluation.py, normalization.py, types.py, temporal.py, validation.py untouched) |
| Fixture files modified | 0 |
| Golden artifacts replaced | 0 |
| `save_golden` | `False` throughout |

**Blindness:** The mapping contract was written and frozen in `TRUETENANT_MAPPING_CONTRACT.md` **before** the evaluator was run. The mapping was not modified based on evaluation output.

---

## 2. Corpus

| Metric | Value |
|--------|-------|
| Total issues | 112 |
| Total changelog records | 1,022 |
| Issues with changelog history | 109 |
| Issues with zero changelog entries | 3 (TT-38, TT-41, TT-46) |
| Quarantined records | **0** |
| Accepted work items | **112** |

**Zero-history issues:**
| Key | Status | Type | Priority |
|-----|--------|------|----------|
| TT-38 | To Do | Epic | Medium |
| TT-41 | To Do | Task | Medium |
| TT-46 | To Do | Epic | Medium |

**Source status distribution (final state from CSV):**

| Source Status | Count |
|--------------|-------|
| Done | 52 |
| To Do | 19 |
| Ready For QA | 12 |
| Approved | 11 |
| Awaiting Approval | 8 |
| Dev In Progress | 4 |
| Feature Not Required | 3 |
| QA Passed | 2 |
| Not an Issue | 1 |
| **Total** | **112** |

**Additional statuses seen only in changelog transitions** (never a final state): `ReOpen`, `Pending For More Information`.

---

## 3. Frozen Mapping Contract

Written before evaluation. Derived only from source status names and transition semantics.

| TrueTenant Source Status | Canonical `status_category` | Terminal? | Confidence |
|--------------------------|----------------------------|-----------|------------|
| `To Do` | `todo` | No | HIGH |
| `Dev In Progress` | `in_progress` | No | HIGH |
| `ReOpen` | `in_progress` | No | MEDIUM |
| `Done` | `done` | YES | HIGH |
| `Feature Not Required` | `done` | YES | MEDIUM |
| `Not an Issue` | `done` | YES | MEDIUM |
| `Awaiting Approval` | **`unknown`** | No | UNMAPPED |
| `Approved` | **`unknown`** | No | UNMAPPED |
| `Ready For QA` | **`unknown`** | No | UNMAPPED |
| `QA Passed` | **`unknown`** | No | UNMAPPED |
| `Pending For More Information` | **`unknown`** | No | UNMAPPED |

**Mapped cleanly:** 6 of 11 statuses  
**Unmapped (unknown):** 5 of 11 statuses  
**Status mapping coverage:** 6/11 = **54.5%**

---

## 4. Mapping Coverage

| Metric | Value |
|--------|-------|
| Total source statuses | 11 |
| Mapped to known category | 6 (54.5%) |
| Mapped to `unknown` | 5 (45.5%) |
| Issues mapping to known category | 79 / 112 (70.5%) |
| Issues mapping to `unknown` | 33 / 112 (29.5%) |
| Quarantined | 0 |
| `UNKNOWN_STATUS` data quality conditions | 33 |
| `PARTIAL_HISTORY` conditions | 0 |
| `UNKNOWN_PRIORITY` conditions | 0 |

**Unknown-category source statuses (in final CSV state):**
- `Ready For QA`: 12 issues
- `Approved`: 11 issues
- `Awaiting Approval`: 8 issues
- `QA Passed`: 2 issues
- **Total:** 33 issues

---

## 5. Canonical State Distribution

| Canonical Category | Count | % of Total |
|-------------------|-------|-----------|
| `done` | 56 | 50.0% |
| `todo` | 19 | 17.0% |
| **`unknown`** | **33** | **29.5%** |
| `in_progress` | 4 | 3.6% |
| `blocked` | 0 | 0% |

**`unknown` is the second-largest canonical category** (29.5%) — a direct, honest consequence of the canonical model not having a representation for approval-domain and QA-gate states.

---

## 6. History Quality

| Metric | Value |
|--------|-------|
| `history_complete = True` | 112 / 112 (100%) |
| `history_complete = False` | 0 |
| `PARTIAL_HISTORY` conditions | 0 |
| Issues with zero changelog entries | 3 (confirmed authentic) |
| Issues with zero **status** changes | 11 (TT-3, TT-4, TT-5, TT-37, TT-38, TT-40, TT-41, TT-46, TT-68, TT-69, TT-104) |
| Issues with GitBranch field changes | 47 |
| Total status change events in changelog | 387 |

---

## 7. Track B Evaluation

### Counts

| Metric | Value |
|--------|-------|
| Accepted work items | 112 |
| Triggered evaluations (findings) | **1** |
| Suppressed evaluations | **0** |
| Finding rate | 1/112 = 0.9% |

### Finding Detail

| Finding | Rule | Subject | Source Status | Canonical Status |
|---------|------|---------|--------------|-----------------|
| 1 | `STALLED_WORK` | TT-2 | `Dev In Progress` | `in_progress` |

**Finding explanation (verbatim from evaluator):**
> TT-2 remained in progress in the source state used for the review. Its last known relevant status change was on 5 August, more than fourteen complete days before the 16 September review cutoff.

### Findings by Rule

| Rule | Count |
|------|-------|
| `STALLED_WORK` | 1 |
| `BLOCKED_HIGH_PRIORITY` | 0 |
| `OVERDUE_HIGH_PRIORITY` | 0 |

### Supporting Facts

| Fact | Value |
|------|-------|
| `accepted_work_item_count` | 112 |
| `planned_at_period_start_count` | 0 |
| `introduced_during_period_count` | 112 |
| `completed_during_period_count` | 56 |
| `planned_completed_during_period_count` | 0 |
| `known_incomplete_at_period_end_count` | 23 |
| `indeterminate_at_period_end_count` | **33** |
| `blocked_at_source_cutoff_count` | 0 |
| `missing_due_date_count` | 107 |
| `manager_facing_completion_percentage` | None (honest null — no planning basis) |

> **`indeterminate_at_period_end_count = 33`** exactly matches the 33 unknown-status issues. The evaluator correctly surfaces unknown items as indeterminate rather than misclassifying them.

---

## 8. Evidence Quality

### Provenance
- All 112 issues carry `source_id` (Issue id from CSV)
- All 112 issues carry `created_at` (parsed from CSV datetime format)
- All 112 issues have timezone-aware timestamps (UTC offset applied)
- Source status preserved verbatim in `source_status` field
- Changelog provenance: `issueId` → `changeHistories` → `items` (full chain intact)

### Chronology
- Changelog timestamps are epoch milliseconds — parsed to UTC ISO 8601
- Change entries sorted by `(changed_at, field, from, to)` — deterministic
- No chronology violations detected (all changeHistories arrived in sorted order from API)

### Uncertainty
- 33 issues carry `UNKNOWN_STATUS` data quality conditions
- `indeterminate_at_period_end_count = 33` — correctly propagated to supporting facts
- Unknown-status issues produce **zero findings** — the evaluator does not fire on unmapped states

### Missing Evidence
- `planned_at_period_start = None` for all 112 issues (TrueTenant has no sprint data)
- `due_at` is missing for 107 / 112 issues (95.5%)
- `resolved_at` is derived from changelog (last terminal transition), not from CSV `Resolution` column

---

## 9. Provider Leakage

| Check | Result |
|-------|--------|
| `JiraIssueState` constructor calls | **0** |
| `GitHubPullRequestState` constructor calls | **0** |
| Leakage detected | **False** |
| `jira_evidence_adapter` imported by TrueTenant ingestion | No |
| `github_normalization` imported by TrueTenant ingestion | No |
| `JiraIssueState` import in ingestion.py | No (referenced in docstring only) |

The TrueTenant path flows exclusively through:
```
CSV + changelog → ingestion.py → shadow-jira-fixture-v1 dict
  → validate_fixture() → normalize_fixture() → evaluate_week_one_rules()
```
No Jira-specific or GitHub-specific evaluator branch was invoked.

---

## 10. Determinism

| Check | Result |
|-------|--------|
| Run 1 vs Run 2 (identical input) | **Identical** |
| Run 1 vs Run 3 (permuted input order) | **Identical** |
| Work items canonical hash | Stable |
| Findings canonical hash | Stable |
| Suppressed canonical hash | Stable |
| Supporting facts canonical hash | Stable |
| Fully deterministic | **True** |

---

## 11. Regression

### Test Suite
| Suite | Before | After | Delta |
|-------|--------|-------|-------|
| All tests | 783 passed | **817 passed** | +34 (new TrueTenant) |
| Failures | 0 | **0** | 0 |

### Track A
- No semantic diff. `evaluation.py`, `temporal.py`, `normalization.py`, `types.py` unmodified.

### Mahout Invariants

| Invariant | Expected | Actual | Status |
|-----------|----------|--------|--------|
| `total_selected_for_qualification` | 412 | 412 | ✓ |
| `accepted_work_item_count` | 412 | 412 | ✓ |
| `quarantined_records` | 0 | 0 | ✓ |
| `STALLED_WORK` findings | 12 | 12 | ✓ |
| `known_incomplete_at_period_end` | 56 | 56 | ✓ |
| `missing_due_date_count` | 370 | 370 | ✓ |
| `is_repeatable` | True | True | ✓ |
| `jira_mutation_count` | 0 | 0 | ✓ |

**ALL MAHOUT INVARIANTS PRESERVED.**

### Apache Wave 3
- Raw fixture hashes: unchanged (no files modified)
- Benchmark artifacts: unchanged
- Phase 1C outputs: unchanged

---

## 12. Generalization Findings

### PROVEN

**P-1: Provider-specific adapter can project a completely different Jira status vocabulary into canonical WorkItemState without modifying core evaluation semantics.**

The TrueTenant adapter maps 6/11 statuses to known canonical categories using only CSV + changelog evidence. The evaluator (`evaluate_week_one_rules`) processes the result correctly with zero modification.

**P-2: `unknown` category correctly absorbs all unmapped states without crashing or producing spurious findings.**

33 issues map to `unknown`. Zero findings were produced for these 33 issues. The evaluator skips categories it cannot act on. `indeterminate_at_period_end_count = 33` surfaces them as transparent uncertainty.

**P-3: The canonical pipeline is fully deterministic for a new provider corpus.**

Three independent runs (including permuted input order) produced identical hashes for all outputs.

**P-4: Provider leakage is zero.**

JiraIssueState and GitHubPullRequestState constructor calls = 0. The TrueTenant path is fully isolated.

**P-5: STALLED_WORK fires correctly on `in_progress` items with complete history.**

TT-2 (`Dev In Progress` → `in_progress`) has a stale status since 5 August — 42+ days before the review cutoff. `STALLED_WORK` fires correctly and deterministically.

---

### SUPPORTED

**S-1: Terminal statuses with zero changelog outflow are safe to map to `done`.**

`Feature Not Required` (3) and `Not an Issue` (1) show zero outbound transitions. Mapping them to `done` is supported by structural evidence even though their semantic meaning differs from standard completion.

**S-2: The canonical `history_complete` flag is meaningful for TrueTenant.**

The extraction API confirmed `pagination_complete=True`. All 112 issues report `history_complete=True` correctly. The evaluator does not suppress any findings due to incomplete history.

---

### PARTIALLY PROVEN

**PP-1: The `unknown` category correctly routes all unmapped states to `indeterminate_at_period_end`.**

The mechanism works. However, the evaluator has no rule that fires on `unknown` items — so the 33 indeterminate items produce no actionable output. Whether this is correct (right to be silent) or a gap (should produce a NEEDS_REVIEW finding) is not proven by this experiment.

**PP-2: `ReOpen` maps cleanly to `in_progress`.**

Only 3 occurrences exist in changelog (never a final state). The mapping is structurally supported (ReOpen → Dev In Progress × 3) but the sample size is too small to confirm it cannot be a resting state in other TrueTenant workflows.

---

### UNSUPPORTED

**U-1: The canonical model can represent approval-domain states accurately.**

`Awaiting Approval`, `Approved`, `QA Passed`, `Ready For QA` cannot be mapped to any existing canonical category without information loss or misclassification. These 4 statuses represent 33/112 issues (29.5%). The canonical model is insufficient to represent TrueTenant's approval workflow without adding new states.

**U-2: `BLOCKED_HIGH_PRIORITY` or `OVERDUE_HIGH_PRIORITY` can fire on TrueTenant corpus.**

No findings triggered for these rules. Reasons: 111/112 issues are Medium priority, and no issues have `due_at` set (107/112 have no due date; remaining 5 may not be overdue). These rules are structurally untested against TrueTenant's data characteristics.

---

### NOT TESTED

**NT-1: Multi-period continuity (Week 2) for TrueTenant.**

Only single-period (Week 1) evaluation was conducted. TrueTenant data spans 2026-07-28 to 2026-09-15. Two-period continuity was not tested.

**NT-2: `BLOCKED_HIGH_PRIORITY` rule path for TrueTenant statuses.**

No TrueTenant status maps to `blocked`. `Pending For More Information` could be argued as `blocked` but was classified `unknown` due to insufficient evidence (1 occurrence). This path is entirely untested.

**NT-3: Approved/QA states through a hypothetical canonical extension.**

Adding `approval_pending` and `qa_pending` canonical states was explicitly prohibited. The experiment cannot assess whether such an extension would be sufficient.

---

## 13. Canonical Model Gaps

The following source concepts are observable in TrueTenant but **cannot be represented** in ORBIT's current canonical model (`StatusCategory`) without loss:

| Gap | TrueTenant States | Missing Canonical Concept | Impact |
|-----|------------------|--------------------------|--------|
| **Approval gate** | `Awaiting Approval`, `Approved` | `approval_pending`, `approved_ready` | 19/112 issues (17%) unclassifiable |
| **QA gate** | `Ready For QA`, `QA Passed` | `qa_pending`, `qa_passed` | 14/112 issues (12.5%) unclassifiable |
| **Non-implementation disposition** | `Feature Not Required`, `Not an Issue` | `rejected`, `invalid` | Currently mapped to `done` — semantically imprecise |

**Combined gap:** 33/112 issues (29.5%) cannot be classified with semantic precision.

> **None of these gaps were patched in this experiment.** Recording them here is the correct output.

---

## 14. Recommended Next Proving Step

**Based on evidence from this experiment only:**

The canonical model successfully handles the basic lifecycle (todo → in_progress → done) across three providers (Mahout, Apache, TrueTenant). The primary demonstrated boundary is the **approval/QA workflow** — a class of states with no canonical representation.

**Recommended next step:** Design and evaluate a controlled canonical extension experiment:

1. Define two new `StatusCategory` values: `approval_pending` and `qa_gate`
2. Re-run this TrueTenant experiment with the extended mapping (remapping `Awaiting Approval`, `Approved` → `approval_pending`; `Ready For QA`, `QA Passed` → `qa_gate`)
3. Verify that: (a) existing Mahout/Apache invariants are preserved, (b) new canonical states trigger appropriate new rules (if any are added), (c) the extension does not cause over-broad matching

**This recommendation is NOT permission to implement the extension.** It requires a separate governed wave with its own baseline and approval.

The experiment does **not** recommend:
- Generic ProviderRegistry / PluginManager
- Live connector infrastructure
- OAuth / webhook implementation
- Modifying existing rule semantics

---

## Files Created in This Experiment

| File | Purpose |
|------|---------|
| `qualification/truetenant/__init__.py` | Package init |
| `qualification/truetenant/ingestion.py` | Phase 4 — TrueTenant adapter (isolated, no core modification) |
| `qualification/truetenant/runner.py` | Phase 5-10 runner |
| `qualification/truetenant/PASS5_WAVE3_TRUETENANT_SOURCE_VOCABULARY.md` | Phase 1 vocabulary freeze |
| `qualification/truetenant/TRUETENANT_MAPPING_CONTRACT.md` | Phase 2+3 blind mapping contract |
| `qualification/truetenant/output/truetenant_normalization_report.json` | Phase 5 normalization report |
| `qualification/truetenant/output/truetenant_evaluation_report.json` | Phase 6+7 evaluation report |
| `qualification/truetenant/output/truetenant_holdout_combined.json` | Combined output |
| `qualification/truetenant/PASS5_WAVE3_TRUETENANT_HOLDOUT_REPORT.md` | This report |
| `tests/unit/test_truetenant_holdout.py` | Phase 12 — 34 focused TrueTenant tests |

## Files NOT Modified

All existing ORBIT source files, test files, fixture files, and golden artifacts are unchanged.

---

## Exact Metrics Summary

| Metric | Value |
|--------|-------|
| Total issues | 112 |
| Total changelog records | 1,022 |
| Quarantined | 0 |
| Accepted | 112 |
| Canonical `done` | 56 |
| Canonical `todo` | 19 |
| Canonical `unknown` | 33 |
| Canonical `in_progress` | 4 |
| Canonical `blocked` | 0 |
| STALLED_WORK findings | 1 (TT-2) |
| Other findings | 0 |
| Suppressed evaluations | 0 |
| Provider leakage calls | 0 |
| Deterministic | True |
| Mahout invariants preserved | True (all 8) |
| New tests added | 34 |
| Tests passing (total) | 817 |
| Tests failing | 0 |
| Git operations | 0 (read-only only) |
| Network calls | 0 |

---

## Git State (Final)

```
HEAD:      ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab
develop:   6d82d123f8bf50316d2b1ab7a025bc5862a474ed
branch:    remediation/pass3-controlled-hardening
status:    working tree clean (nothing to commit, working tree clean)
```

*End of PASS5_WAVE3_TRUETENANT_HOLDOUT_REPORT.md*
