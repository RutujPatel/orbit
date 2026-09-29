# PASS 4 — Wave 5.1 Forensic Implementation Audit
# Track B EvidenceBundle Evaluator: evidence_evaluation.py

**Date:** 2026-09-29
**Auditor:** Antigravity AI forensic engineer
**Status:** **PASS WITH QUALIFICATIONS**

---

## 1. Executive Conclusion

**PASS WITH QUALIFICATIONS**

The Wave 5 Track B evaluator implementation (`evidence_evaluation.py`) is
faithful to the approved ADR-006 contract.  It is deterministic, provenance-
preserving, conservative in inference, isolated from Track A, and free of
unintended side effects.

Qualifications relate exclusively to documentation discrepancies, test
assertion strength gaps, and a test-count narrative error discovered during
this audit.  No material evidence defects were found.

---

## 2. Scope and Baselines

| Baseline | Value | Role |
|---|---|---|
| Protected governing baseline | `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` | Frozen `develop` HEAD |
| Pass 3 controlled-hardening HEAD | `e967ad57ea3b37cef4266134537acbb34e9ae715` | Git HEAD on `remediation/pass3-controlled-hardening` |
| Current Git HEAD | `e967ad57ea3b37cef4266134537acbb34e9ae715` | Identical to Pass 3 HEAD |
| Current working-tree state | **UNCOMMITTED** — 9 files added/modified | Wave 5 code exists only in working tree |
| Merge-base (HEAD, develop) | `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` | Clean divergence |
| Audited implementation state | Working tree after e967ad5 | `evidence_evaluation.py` (967 lines) + test file (1086 lines) |

**Critical distinction**: Wave 5 files have NOT been committed. They exist
only in the working tree.  `e967ad5` is the HEAD commit (Pass 3.1), not
the "Wave 5 commit".

---

## 3. Evidence Inventory

### Uncommitted Working-Tree Changes (git diff --stat HEAD)

| File | Status | Lines |
|---|---|---|
| `src/shadow_orbit/cross_system_fusion.py` | NEW | 287 |
| `src/shadow_orbit/evidence_assembly.py` | MODIFIED | +193/-5 |
| `src/shadow_orbit/evidence_evaluation.py` | **NEW** | 967 |
| `src/shadow_orbit/evidence_types.py` | MODIFIED | +80/-0 |
| `src/shadow_orbit/provenance_dereference.py` | NEW | 565 |
| `tests/unit/test_p4_provenance_dereferencing.py` | NEW | 891 |
| `tests/unit/test_p4_wave2_provenance_validation.py` | NEW | 674 |
| `tests/unit/test_p4_wave3_cross_system_fusion.py` | NEW | 1075 |
| `tests/unit/test_p4_wave5_evidence_evaluation.py` | **NEW** | 1086 |

Total: 9 files changed, 5813 insertions, 5 deletions.

### Test Execution Evidence

| Metric | Value | Source |
|---|---|---|
| Total tests collected | 708 | `pytest --collect-only -q` |
| Tests passed | 696 | `pytest -v --tb=short` |
| Tests skipped | 12 | MongoDB-dependent qualification tests |
| Tests failed | 0 | `pytest -v --tb=short` |
| Wave 5 tests | 42 | `pytest test_p4_wave5_evidence_evaluation.py --collect-only` |

### Mahout Qualification Evidence

| Metric | Value | Source |
|---|---|---|
| Accepted | 412 | `run_mahout_qualification(save_golden=False)` |
| Quarantined | 0 | Same |
| STALLED_WORK findings | 12 | Same |
| Incomplete | 56 | Same |
| Missing due dates | 370 | Same |
| Introduced | 0 | Same |
| Completed | 0 | Same |
| Jira mutations | 0 | Same |
| Config mutations | 0 | Same |
| Repeatable | True | Same |
| Engine commit | `6d82d12` | FROZEN_ENGINE_COMMIT from `qualification/config.py:21` |
| Mutation guard active | True | Same |
| Golden digest | `2fa3b4ce04133554ff3410bd21ce919c0083ae8863dd3090c39678bb3b280aeb` | Runtime output |

---

## 4. Source-Level Findings

### 4.1 Module Structure

`evidence_evaluation.py` is 967 lines organized as:

- **Lines 1-22**: Module docstring (Track B contract, anti-inference rules)
- **Lines 24-50**: Imports (evidence_types, temporal.elapsed_complete_days, types.ReviewPeriod)
- **Lines 53-97**: Type definitions (FindingSufficiency, FindingDisposition, TrackBFinding, EvidenceBundleEvaluationResult)
- **Lines 99-189**: Canonical sorting, merge, and ID generation helpers
- **Lines 195-923**: `evaluate_evidence_bundle()` — the primary evaluator
- **Lines 926-967**: Serialization functions

### 4.2 Import Chain

```
evidence_evaluation.py imports:
  └─ shadow_orbit.evidence_types (dataclasses, serializers)
  └─ shadow_orbit.temporal (elapsed_complete_days only)
  └─ shadow_orbit.types (ReviewPeriod only)
```

No circular dependencies.  No imports from Track A evaluation.py, normalization.py,
artifact.py, continuity.py, or acceptance modules.

### 4.3 Data Structures

`TrackBFinding` and `EvidenceBundleEvaluationResult` are `frozen=True, slots=True`
dataclasses — **immutable by design**.  Both match ADR-006 §Proposed Data Structures
exactly (field names, types, defaults).

---

## 5. XB-01 Audit: UNMERGED_PR_ON_RESOLVED_ISSUE

**Location**: Lines 439-530

**Contract verification:**

| Requirement | Verified | Evidence |
|---|---|---|
| Jira status_category == "done" | ✅ | L490: `jira_state.status_category == "done"` |
| GitHub PR state == "open" | ✅ | L490: `gh_state.state == "open"` |
| Relationship-bound evaluation | ✅ | L253-282: candidate_pairs sourced exclusively from alignments + authorized relationships |
| No Cartesian pairing | ✅ | L253: pairs collected from pre-established alignments/relationships only |
| No actor inference | ✅ | Zero actor/assignee field access in evaluator |
| No transitive inference | ✅ | L270-273: only "mentions" and "explicit_link" relationships accepted |
| No completion inference | ✅ | L511-512: explanation states "discrepancy without inferring defect or causality" |
| Provenance preserved | ✅ | L524: `provenance_refs=combined_prov` includes Jira, GitHub, and relationship provenance |
| Missing Jira obs → UNRESOLVED suppression | ✅ | L327-356 |
| Missing GitHub obs → UNRESOLVED suppression | ✅ | L359-388 |
| Ambiguous (>1 obs) → AMBIGUOUS suppression | ✅ | L391-420 |
| Unknown PR state → INSUFFICIENT_EVIDENCE | ✅ | L465-489 |
| Stale evidence → SUPPRESSED | ✅ | L437+L494-496+L527-530 |

**Disposition**: NO ISSUE

---

## 6. XB-02 Audit: MERGED_PR_ON_UNRESOLVED_ISSUE

**Location**: Lines 532-655

**Contract verification:**

| Requirement | Verified | Evidence |
|---|---|---|
| PR state == "merged" | ✅ | L537 |
| Jira status_category in {todo, in_progress, blocked} | ✅ | L538-542 |
| Jira status_category == "done" → no finding | ✅ | Implicit: L538 only enters block for todo/in_progress/blocked |
| Unknown status_category → INSUFFICIENT_EVIDENCE | ✅ | L623-655: `elif jira_state.status_category != "done"` catches all unmapped values |
| Missing merged_at → INSUFFICIENT_EVIDENCE | ✅ | L543-576 |
| Explanation says "merging code does not prove issue completion" | ✅ | L601 |
| Relationship-bound | ✅ | Same candidate_pairs mechanism as XB-01 |
| Provenance preserved | ✅ | L616 |
| Stale → SUPPRESSED | ✅ | L581-585+L619-622 |

**Disposition**: NO ISSUE

---

## 7. XB-03 Audit: POST_RESOLUTION_WORK_ACTIVITY

**Location**: Lines 657-802

**Contract verification:**

| Requirement | Verified | Evidence |
|---|---|---|
| OBSERVATIONAL ONLY | ✅ | L658 comment + L708 explanation |
| PR merge activity detected | ✅ | L665-672 |
| Commit activity detected | ✅ | L673-677 |
| Activity after resolved_at → TRIGGERED | ✅ | L682 |
| Activity before/equal resolved_at → no finding | ✅ | L682 uses strict `>` |
| Missing resolved_at + done → INSUFFICIENT_EVIDENCE | ✅ | L771-802 |
| Missing activity timestamp → INSUFFICIENT_EVIDENCE | ✅ | L735-770 |
| temporal_comparison = "INVERTED" | ✅ | L722 |
| Explanation: "observational temporal finding" | ✅ | L708 |
| Never CONFLICTING | ✅ | L658 comment; confirmed grep: CONFLICTING only in type def and counter, never assigned |
| No blame language | ✅ | No "late", "defect", "violation", "fault", "error", "wrong" in any explanation string |
| Does NOT assert: incorrect resolution / workflow violation / defective work | ✅ | Source verified |

**Disposition**: NO ISSUE

---

## 8. Determinism Audit

### System Clock Dependence

**CLAIM**: Wave 5 report claims zero system-clock dependence.

**VERDICT**: **PROVEN TRUE**

**Evidence**:

1. Grep for `datetime.now`, `datetime.utcnow`, `time.time`, `random.`, `uuid.`,
   `os.environ`, `socket.`, `subprocess.`, `open(`, `pathlib.`, `sys.`:
   **ZERO MATCHES** in `evidence_evaluation.py`.

2. `evaluated_at` derivation (L856-867):
   - Path A (L857): `review_period.review_cutoff_at` → input data
   - Path B (L864-865): `sorted(ctx_cutoffs)[-1]` → input data
   - Path C (L867): literal `"unspecified"` → constant string
   
   All three paths derive exclusively from function inputs.

3. `datetime` is imported (L27) but used only as a type annotation on `activity_dt`
   (L660) which is populated from `gh_state.merged_at` or `gh_state.committed_at` —
   both input data.

### Finding ID Determinism

`_generate_finding_id()` (L163-177):
- Input: `rule_id`, `subject_ref`, `corroborating_refs`, `disposition`
- Computation: SHA-256 of concatenated canonical string
- **Deterministic**: same inputs → same digest

### Evaluation ID Determinism

`_generate_evaluation_id()` (L180-189):
- Input: `bundle_id`, sorted findings IDs, sorted suppressed IDs
- All inputs are deterministic post-sort
- **Deterministic**: same inputs → same digest

### Set Iteration

**Zero `set()` usage** in `evidence_evaluation.py`.

Dictionary iteration occurs at:
- L148: `dedup.values()` → sorted before output
- L160: `dedup.values()` → sorted before output
- L268: `rels_by_pair.items()` → populates candidate_pairs dict
- L288: `candidate_pairs.values()` → main evaluation loop

All dictionary values that produce output are sorted at L846-848 before
being stored in the result.  Insertion-order variance in intermediate dicts
is neutralized by the canonical sort.

### Final Determinism Assessment

| Component | Deterministic? | Mechanism |
|---|---|---|
| Finding IDs | ✅ | SHA-256 of canonical string |
| Evaluation ID | ✅ | SHA-256 of bundle_id + sorted finding IDs |
| Findings ordering | ✅ | `sorted(findings, key=_sort_finding_key)` |
| Suppressed ordering | ✅ | `sorted(suppressed_evaluations, key=_sort_finding_key)` |
| Provenance ordering | ✅ | `_merge_provenance()` sorts by canonical key |
| Quality issue ordering | ✅ | `_merge_quality_issues()` sorts by canonical key |
| evaluated_at | ✅ | Derived from input data or constant |
| Summary counts | ✅ | Pre-initialized counters, deterministic iteration over sorted tuples |

**CONCLUSION**: The evaluator is fully deterministic.  Zero system clocks,
zero randomness, zero environment dependence.

---

## 9. Temporal/Staleness Audit

### Review Period Handling

When `review_period` is None (L858-867):
- Extracts `source_cutoff_at` from observation contexts
- Uses latest (sorted maximum) if available
- Falls back to `"unspecified"` — never guesses

When `review_period` is provided (L856-857):
- Uses `review_period.review_cutoff_at` directly

### Stale Evidence Handling

L437: `is_stale = any(q.code == "STALE" for q in combined_qi)`

When stale:
- Finding disposition → `SUPPRESSED` (L496, L585, L694)
- Finding sufficiency → `STALE` (L494, L582, L691)
- Finding appended to `suppressed_evaluations` (L528, L620, L730)

**Stale evidence CANNOT silently become valid evidence.**

### XB-04 Absence Check

Searched for indirect XB-04 behavior:
- No `status_at_period_end()` calls
- No `changes` field access
- No `history_complete` field access
- No `WorkItem` import
- No changelog reconstruction

`JiraIssueState` fields accessed: `status_category`, `source_status`, `key`,
`resolved_at`, `due_at` (never referenced in evaluator).

**CONFIRMED**: No indirect XB-04 behavior.

### Timezone Semantics

Timestamps are compared using Python's native datetime comparison (L682:
`activity_dt > jira_state.resolved_at`).  `_serialize_datetime()` is imported
from `evidence_types` and produces deterministic ISO strings.  The evaluator
does not reinterpret, convert, or assume timezone offsets.

**Disposition**: NO ISSUE

---

## 10. Sufficiency/Disposition Audit

### Disposition Usage

| Disposition | Where Used | Semantics |
|---|---|---|
| `TRIGGERED` | L496, L504, L584, L593, L693, L703 | Finding emitted to `findings` list |
| `SUPPRESSED` | L496, L504, L585, L593, L694, L703 | Stale finding → `suppressed_evaluations` |
| `INSUFFICIENT_EVIDENCE` | L330, L343, L361, L375, L393, L407, L444, L454, L470, L480, L544, L557, L625, L638, L737, L750, L774, L787, L816, L829 | Missing/incomplete evidence → `suppressed_evaluations` |

### Sufficiency Usage

| Sufficiency | Assigned When | Verified |
|---|---|---|
| `PROVEN` | `EXPLICIT_LINK` or `explicit_metadata` relationship | L298-306 |
| `SUPPORTED` | `DECLARED_MENTION` or `mentions` relationship | L305-306 |
| `INSUFFICIENT_EVIDENCE` | Missing state, incompatible types, unmapped categories | L455, L481, L558, L639, L751, L788 |
| `STALE` | Quality issue code="STALE" present | L494, L582, L691 |
| `UNRESOLVED` | Missing observation for referenced entity | L344, L376, L830 |
| `AMBIGUOUS` | Multiple observations match same entity | L408 |
| `CONFLICTING` | **NEVER ASSIGNED** — exists only in type def (L57), comment (L658), and counter init (L879) |

**Critical verification**: `unknown != false`, `missing != complete`,
`unresolved != absent`, `stale != current` — all preserved.  Unknown
Jira status categories produce `INSUFFICIENT_EVIDENCE`, not false negatives.

**Disposition**: NO ISSUE

---

## 11. Provenance Audit

### Provenance Chain Construction

Every finding receives provenance from three sources:
1. Jira observation provenance: `jira_obs.provenance_refs`
2. GitHub observation provenance: `gh_obs.provenance_refs`
3. Relationship provenance: `rel_prov` from matching relationships and alignments

Combined via `_merge_provenance()` (L139-148) which deduplicates by canonical
5-tuple key and sorts deterministically.

### Missing/Malformed Provenance Handling

- Missing Jira observation → provenance includes only relationship + GitHub (L332-334)
- Missing GitHub observation → provenance includes only relationship + Jira (L364-366)
- Ambiguous observations → provenance includes all sources (L395-398)
- Unresolved references → provenance from `UnresolvedReference.provenance_refs` (L841)

**No provenance fabrication detected.**  All provenance derives from input
bundle data.

### Wave 1/2 Provenance Integration

Wave 1 `provenance_dereference.py` (565 lines) and Wave 2 validation
integration remain intact — verified via `git diff --stat`.

**Disposition**: NO ISSUE

---

## 12. Anti-Inference Audit

| Anti-Inference Rule | Source Verification | Result |
|---|---|---|
| No Cartesian pairing | L253-282: pairs from alignments + authorized rels only | ✅ ENFORCED |
| No transitive association | L270-273: only `mentions`/`explicit_link` accepted; commit→jira does not promote PR→jira | ✅ ENFORCED |
| No actor identity | Zero references to `author_login`, `assignee`, `author`, `actor` | ✅ ENFORCED |
| No completion inference | L601: "merging code does not prove issue completion" | ✅ ENFORCED |
| No absence inference | Missing evidence → `INSUFFICIENT_EVIDENCE`, never negative findings | ✅ ENFORCED |
| Temporal inversion ≠ contradiction | `CONFLICTING` never assigned; L658 comment explicitly states "Never CONFLICTING" | ✅ ENFORCED |

**Disposition**: NO ISSUE

---

## 13. Track A Isolation Audit

### Git Diff

```
git diff HEAD -- src/shadow_orbit/evaluation.py
# (empty — zero changes)

git diff HEAD -- src/shadow_orbit/temporal.py
# (empty — zero changes)

git diff HEAD -- src/shadow_orbit/normalization.py
# (empty — zero changes)

git diff HEAD -- src/shadow_orbit/types.py
# (empty — zero changes)
```

### Reverse Import Scan

```
grep -rn "import.*evidence_evaluation\|from.*evidence_evaluation" \
  src/shadow_orbit/evaluation.py \
  src/shadow_orbit/temporal.py \
  src/shadow_orbit/normalization.py \
  src/shadow_orbit/types.py \
  src/shadow_orbit/validation.py \
  src/shadow_orbit/artifact.py \
  src/shadow_orbit/continuity.py
# EXIT CODE 1 — zero matches
```

Track A does NOT import, call, wrap, or depend on Track B.

### Shared Function Usage

`evidence_evaluation.py` imports `elapsed_complete_days` from `temporal.py`.
This is a pure mathematical function operating on Python `datetime` objects.
It does NOT require `WorkItem.changes` or any Track A-specific type.
This usage is explicitly authorized by ADR-006 Decision 2.

**Disposition**: NO ISSUE

---

## 14. External I/O / Mutation Audit

### Source Scan

```
grep -n "datetime\.now\|datetime\.utcnow\|time\.time\|random\.\|uuid\.\|
         os\.environ\|socket\.\|subprocess\.\|open(\|pathlib\.\|sys\.\|
         requests\.\|urllib\.\|httpx\.\|aiohttp\." \
  src/shadow_orbit/evidence_evaluation.py
# ZERO MATCHES
```

### Module Classification

`evidence_evaluation.py` is a **pure function module**:
- Input: `EvidenceBundle` + optional `ReviewPeriod`
- Output: `EvidenceBundleEvaluationResult`
- Side effects: None
- I/O: None
- Network: None
- Database: None
- Filesystem: None
- Process control: None

**Disposition**: NO ISSUE

---

## 15. Test Quality Audit

### Test Count Verification

| Source | Count |
|---|---|
| `pytest --collect-only -q` | 708 tests collected |
| `pytest -v --tb=short` | 696 passed, 12 skipped, 0 failed |
| Wave 5 file (`test_p4_wave5_evidence_evaluation.py`) | 42 tests |

> [!IMPORTANT]
> The 12 skipped tests are MongoDB-dependent qualification tests (not Wave 5
> tests).  All 42 Wave 5 tests passed.  The Wave 5 execution report claims
> "708 passed, 0 failed, 0 skipped" — this is a **documentation discrepancy**.
> The actual runtime result is **696 passed, 12 skipped, 0 failed**.  The
> skipped tests are pre-existing MongoDB tests, not Wave 5 regressions.

### Test Classification Summary (from forensic subagent audit)

| Classification | Count | Percentage |
|---|---|---|
| **STRONG** (tests real behavior) | 34 | 81.0% |
| **WEAK** (single-attribute assertion) | 8 | 19.0% |
| **STUB** (always passes) | 0 | 0% |

### Adversarial/Boundary Coverage

| Requirement | Covered? | Tests |
|---|---|---|
| XB-01 positive | ✅ | test_resolved_jira_open_pr_triggers_finding |
| XB-01 negative | ✅ | test_resolved_jira_merged_pr_does_not_trigger_xb01, test_unresolved_jira_open_pr_does_not_trigger_xb01 |
| XB-02 positive | ✅ | test_unresolved_jira_merged_pr_triggers_finding |
| XB-02 negative | ✅ | test_resolved_jira_merged_pr_does_not_trigger_xb02, test_unresolved_jira_open_pr_does_not_trigger_xb02 |
| XB-03 positive | ✅ | test_pr_merged_after_jira_resolution_triggers_observational_finding, test_commit_after_jira_resolution_triggers_observational_finding |
| XB-03 observational semantics | ✅ | test_temporal_inversion_never_becomes_conflicting, test_explanation_factual_temporal_sequence_no_defect_language |
| Stale evidence | ✅ | test_stale_observation_handling |
| Unresolved evidence | ✅ | test_missing_jira_observation_emits_unresolved_suppression, test_unresolved_reference_handling |
| Ambiguous evidence | ❌ | No test constructs multiple observations for the same entity |
| Anti-Cartesian | ✅ | test_no_cartesian_pairing, test_unrelated_jira_and_pr_produces_no_finding |
| Anti-transitive | ✅ | test_no_transitive_association |
| Anti-actor | ✅ | test_no_actor_matching |
| Anti-completion | ✅ | test_no_completion_inference |
| Provenance | ✅ | test_provenance_preservation |
| Deterministic IDs | ✅ | test_deterministic_finding_id (XB-01 class) |
| Permutation invariance | ✅ | 3 tests (one per rule class) |
| Track A isolation | ✅ | test_track_a_unchanged |
| XB-04 absence | ✅ | test_xb04_not_implemented |
| Serialization | ⚠️ | test_deterministic_serialization — tests JSON roundtrip but not byte-identity |
| Mutation safety | ❌ | Not tested |
| Duplicate handling | ❌ | Not tested |

### Weak Test Details

**P4-W5.1-03**: 6 tests (`test_declared_mention_has_supported_sufficiency` ×3,
`test_explicit_link_has_proven_sufficiency` ×3) assert only `res.findings[0].sufficiency`
without verifying `len(res.findings) == 1` or `findings[0].rule_id`.  These tests
pass but provide weaker coverage than their names suggest.

**P4-W5.1-04**: `test_deterministic_finding_id` in TestXB02 (L592-607) evaluates the
bundle only once and asserts prefix format — does NOT test determinism (unlike the
equivalent in TestXB01 which evaluates twice and compares).

**P4-W5.1-05**: `test_deterministic_serialization` (L1035-1056) includes
`assert isinstance(json_str, str)` which trivially always passes, and never
serializes twice to verify byte-identity.

---

## 16. ADR-006 Consistency Audit

### Header/Status Inconsistency

**P4-W5.1-01**: ADR-006 Line 3 states:
```
**Status:** PROPOSED (Design & Architectural Contract Only — NOT IMPLEMENTED)
```

However, Lines 177-194 document Wave 5 as implemented and verified (42 tests,
708 passed, Mahout invariants preserved).

**Classification**: **NON-MATERIAL DOCUMENTATION DISCREPANCY**

The header reflects the historical state at Wave 4 authoring.  The body
(Section "Implementation Status") documents the current Wave 5 state.
The header should be updated to `ACCEPTED (Implemented under Wave 5)`
or similar, but this does not affect the correctness of the implementation.

### Decision Consistency

| ADR-006 Decision | Implementation Consistent? |
|---|---|
| D1: Bundle input boundary | ✅ `evaluate_evidence_bundle(bundle: EvidenceBundle, ...)` |
| D2: Strict dual-track isolation | ✅ No Track A imports |
| D3: Explicit sufficiency taxonomy | ✅ All 7 sufficiency values defined and used correctly |
| D4: Relationship-bound findings | ✅ Anti-Cartesian candidate_pairs mechanism |
| D5: Anti-inference invariants | ✅ All 5 sub-invariants verified |
| D6: Provenance preservation | ✅ All findings carry provenance_refs |
| D7: XB-03 observational semantics | ✅ No blame language, no CONFLICTING |
| D8: XB-04 temporal contract | ✅ XB-04 absent from implementation |
| D9: Rule authorization taxonomy | ✅ Only XB-01/02/03 implemented |

### Proposed Data Structures Match

ADR-006 Lines 116-153 define `FindingSufficiency`, `FindingDisposition`,
`TrackBFinding`, and `EvidenceBundleEvaluationResult`.  The implementation
at Lines 53-96 of `evidence_evaluation.py` matches these exactly:
same field names, same types, same defaults.

**Disposition**: P4-W5.1-01 is a non-material documentation discrepancy.

---

## 17. Git Forensic Audit

```
git rev-parse HEAD
  e967ad57ea3b37cef4266134537acbb34e9ae715

git rev-parse develop
  6d82d123f8bf50316d2b1ab7a025bc5862a474ed

git merge-base HEAD develop
  6d82d123f8bf50316d2b1ab7a025bc5862a474ed

git rev-parse --abbrev-ref HEAD
  remediation/pass3-controlled-hardening
```

### Working Tree State

9 files in the working tree differ from HEAD (all are Pass 4 Wave 1-5 additions):

| Category | Files |
|---|---|
| Wave 1 | `provenance_dereference.py`, `test_p4_provenance_dereferencing.py` |
| Wave 2 | `evidence_assembly.py` (modified), `test_p4_wave2_provenance_validation.py` |
| Wave 3 | `cross_system_fusion.py`, `evidence_types.py` (modified), `test_p4_wave3_cross_system_fusion.py` |
| Wave 5 | `evidence_evaluation.py`, `test_p4_wave5_evidence_evaluation.py` |

### Track A Diff

```
git diff HEAD -- src/shadow_orbit/evaluation.py
# EMPTY — Track A untouched

git diff HEAD -- src/shadow_orbit/temporal.py
# EMPTY

git diff HEAD -- src/shadow_orbit/normalization.py
# EMPTY

git diff HEAD -- src/shadow_orbit/types.py
# EMPTY
```

### .gitignore Issue

The `.gitignore` contains a corrupt wildcard pattern (null bytes on line 31)
that matches all new files.  Wave 5 files required `git add -f` for staging.
This is a pre-existing issue, not introduced by Wave 5.

---

## 18. Mahout Regression Results

```
run_id:                   mahout-qual-76f973a5
engine_commit:            6d82d12
contract_version:         shadow-jira-fixture-v1
source_considered:        2121
primary_selected:         400
structural_dependencies:  12
total_selected:           412
not_selected_by_policy:   1709
accepted_count:           412
quarantined_count:        0
STALLED_WORK findings:    12
incomplete_at_period_end: 56
missing_due_date:         370
introduced:               0
completed:                0
jira_mutations:           0
config_mutations:         0
mutation_guard_active:    True
is_repeatable:            True
golden_digest:            2fa3b4ce04133554ff3410bd21ce919c0083ae8863dd3090c39678bb3b280aeb
```

All Mahout invariants match the expected values exactly.

---

## 19. Hash/Engine Provenance Reconciliation

### Engine Commit

`FROZEN_ENGINE_COMMIT` is defined at `qualification/config.py:21`:
```python
FROZEN_ENGINE_COMMIT = "6d82d12"
```

This represents the **frozen governing baseline** (`develop` commit), NOT
the runtime Git HEAD.  The runtime Git HEAD is `e967ad5`, which differs.
This is by design — the engine commit tracks the protected baseline against
which Mahout qualification semantics were frozen.

### Golden Digest Reconciliation

| Digest | Value | Role |
|---|---|---|
| Historical golden raw SHA | `fde866023c55290501c1a59f7ab4f208681bba85d963c4fba321e59f65969c` | Original fixture hash |
| Historical canonical JSON SHA | `06b6e83fbbcc73ccdf94345bbb9af0a5235c7961adf19770b0bc98f198e998bf` | Canonical JSON hash |
| Wave 5 execution report runtime SHA | `1fdec553e97b078563a8fc6f063a9b9722344749fe177d0c98d14750ba74c8e2` | Reported in Wave 5 execution report |
| Wave 5.1 audit runtime SHA | `2fa3b4ce04133554ff3410bd21ce919c0083ae8863dd3090c39678bb3b280aeb` | Produced by this audit run |

The runtime golden digest from this audit (`2fa3b4ce...`) differs from the
Wave 5 execution report's claimed digest (`1fdec553...`).  This is expected:
the `golden_digest` is computed from the full runtime output including
the `run_id` (which contains a random component: `mahout-qual-76f973a5` vs
`mahout-qual-007888b6`).  The important invariants are that the underlying
Mahout **acceptance, findings, and metrics** are identical across runs,
which they are.

The runtime digest is NOT the historical golden digest.

---

## 20. Defect/Discrepancy Table

| ID | Description | Classification | Section |
|---|---|---|---|
| **P4-W5.1-01** | ADR-006 header says "PROPOSED (NOT IMPLEMENTED)" while body documents Wave 5 as implemented | NON-MATERIAL DOCUMENTATION DISCREPANCY | §16 |
| **P4-W5.1-02** | Wave 5 execution report claims "708 passed, 0 failed, 0 skipped" but actual runtime is 696 passed, 12 skipped, 0 failed. The 12 skips are pre-existing MongoDB-dependent qualification tests. | NON-MATERIAL DOCUMENTATION DISCREPANCY | §15 |
| **P4-W5.1-03** | 6 sufficiency tests (declared_mention/explicit_link × 3 rules) assert only `res.findings[0].sufficiency` without verifying finding count or rule_id, providing weaker coverage than their names suggest | QUALIFICATION | §15 |
| **P4-W5.1-04** | `test_deterministic_finding_id` in TestXB02 evaluates bundle once and checks prefix only — does NOT verify determinism (unlike TestXB01 equivalent which evaluates twice) | QUALIFICATION | §15 |
| **P4-W5.1-05** | `test_deterministic_serialization` tests JSON roundtrip but never serializes twice to verify byte-identity determinism; includes trivial `isinstance(json_str, str)` assertion | QUALIFICATION | §15 |
| **P4-W5.1-06** | No test for ambiguous evidence (multiple observations for same entity triggering AMBIGUOUS suppression at L391-420) | QUALIFICATION | §15 |
| **P4-W5.1-07** | No test for mutation safety (verifying bundle immutability after evaluation) | QUALIFICATION | §15 |
| **P4-W5.1-08** | No test for duplicate observation/relationship handling | QUALIFICATION | §15 |
| **P4-W5.1-09** | Wave 1 test count narrative error: user directive states "22 + 23 + 25 = 70 tests for Waves 1-3" but Wave 1 (`test_p4_provenance_dereferencing.py`) contains 91 tests. Actual: 91 + 23 + 25 = 139 tests for Waves 1-3. The progression 527→618→641→666→708 is arithmetically correct (91+23+25+42=181 total Pass 4 additions) but the per-wave breakdown "22" for Wave 1 is wrong. | NON-MATERIAL DOCUMENTATION DISCREPANCY | §15 |

---

## 21. Canonical Traceability

### Historical P2.5 ID Preservation

This audit does not remap or renumber any historical finding IDs.
All P2.5-xx, P3-xx, and P4-Wn-xx IDs from prior passes remain intact.

### Wave 5.1 Finding IDs

All findings in this audit use the schema: `P4-W5.1-NN`
(NN = zero-padded sequential, 01 through 09).

---

## 22. Final Governance Recommendation

### Verdict: PASS WITH QUALIFICATIONS

The Wave 5 Track B evaluator implementation is architecturally sound,
deterministic, provenance-preserving, and faithfully implements the
approved ADR-006 contract for rules XB-01, XB-02, and XB-03.

### What must happen before consolidation:

1. **P4-W5.1-01**: Update ADR-006 header status from `PROPOSED (NOT IMPLEMENTED)`
   to `ACCEPTED (Implemented under Wave 5)` or equivalent.

2. **P4-W5.1-02**: Correct the Wave 5 execution report's test count claim
   from "708 passed, 0 failed, 0 skipped" to "696 passed, 12 skipped, 0 failed"
   (or explicitly note that 12 MongoDB-dependent tests are skipped by infrastructure).

3. **P4-W5.1-03 through P4-W5.1-08**: Consider strengthening the 8 weak tests
   and adding the 3 missing test categories (ambiguous evidence, mutation safety,
   duplicate handling) before merging to a protected branch.  These are
   qualifications, not blocking defects — the underlying code behavior is correct.

4. **P4-W5.1-09**: Correct the Wave 1 per-wave test count narrative in any
   future reference documents (91, not 22).

### What does NOT need to change:

- The evaluator source code (`evidence_evaluation.py`) — no material defects found
- Track A — completely untouched and verified
- Mahout qualification — all invariants preserved
- Provenance chain — complete and correct
- Determinism — proven from source
- Anti-inference invariants — all enforced

---

**END OF FORENSIC AUDIT**

**STOP — Do not proceed to Wave 5.2, consolidation, commit, merge, or Wave 6.**
