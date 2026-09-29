# PASS 4 — Wave 2 Execution Report
# EvidenceBundle Provenance Validation Integration

**Pass:** 4 / Milestone 2 — Bounded Provenance Dereferencing Integration  
**Wave:** 2 (of 3 authorized)  
**Date:** 2026-09-28  
**Branch:** `remediation/pass3-controlled-hardening`  
**Baseline Commit:** `e967ad57ea3b37cef4266134537acbb34e9ae715`  
**Protected Governing Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`develop`)  
**Final Status:** **Wave 2 PASS**

---

## 1. Wave 2 Objectives & Governance Status

| # | Wave 2 Requirement | Governing Rule / Constraint | Status |
|---|---|---|---|
| 1 | Add `fixtures_by_id: dict[str, Any] \| None = None` to `validate_evidence_bundle()` | Optional parameter, default `None` | ✅ COMPLETE |
| 2 | Preserve 100% backward compatibility when `fixtures_by_id=None` | Baseline tests run unmodified | ✅ VERIFIED (527 baseline passing) |
| 3 | Integrate Wave 1 bounded in-memory dereferencer into validation | Zero external I/O, pure in-memory | ✅ COMPLETE |
| 4 | Preserve all existing structural provenance checks | Structural + dereferencing coexist | ✅ COMPLETE (coexistence proven) |
| 5 | Required Correction: Zero-guessing fixture identification | Do NOT fallback to first fixture | ✅ ENFORCED (absent fixture_id → UNAVAILABLE) |
| 6 | Numeric PR fallback constraint | In-bounds index always wins; fallback post-OOB only | ✅ PRESERVED & TESTED |
| 7 | Optional locator contract (`record_locator=None`) | Skipped cleanly; no error emitted | ✅ PRESERVED & TESTED |
| 8 | Adversarial test suite | Minimum 14 required categories | ✅ 23 tests (all passing) |
| 9 | Full regression suite execution | Baseline 618 passing | ✅ 641 passed, 0 failed, 0 skipped |
| 10 | Mahout qualification execution (`save_golden=False`) | All historical invariants preserved | ✅ 412 / 12 / 56 / 370 / 0 mutations |
| 11 | Update ADR-004 | Document Wave 2 architecture decisions | ✅ COMPLETE |
| 12 | STOP after Wave 2 | Do not begin Wave 3 | ✅ STOPPED |

---

## 2. Implementation Summary

### Modified File: `src/shadow_orbit/evidence_assembly.py`

1. **Import added**:
   ```python
   from shadow_orbit.provenance_dereference import dereference_provenance_ref
   ```

2. **Signature updated**:
   ```python
   def validate_evidence_bundle(
       bundle: EvidenceBundle,
       fixtures_by_id: dict[str, Any] | None = None,
   ) -> tuple[QualityIssue, ...]:
   ```

3. **`_validate_provenance_refs` integration**:
   - Loops over supporting provenance references on observations, relationships, and unresolved references.
   - Retains existing structural checks (unknown observation ID, source instance mismatch).
   - When `fixtures_by_id is not None` and `p.record_locator is not None`:
     - If `p.fixture_id is None`: records `QualityIssue(code="unresolved", subject_scope="provenance:fixture")` without guessing a fixture.
     - If `p.fixture_id not in fixtures_by_id`: records `QualityIssue(code="unresolved", subject_scope="provenance:fixture")`.
     - Otherwise: resolves via `dereference_provenance_ref()` and records any returned quality issue.
   - When `p.record_locator is None`: dereferencing is skipped, preserving the optional-field contract.
   - Deduplicates identical provenance references within each subject scope to prevent redundant processing.

4. **Sort key enhanced**:
   ```python
   def _quality_issue_sort_key(q: QualityIssue) -> tuple[str, str, str, str]:
       ref_key = ""
       if q.subject_ref is not None:
           ref_key = f"{q.subject_ref.source_instance.instance_id}:{q.subject_ref.entity_kind}:{q.subject_ref.entity_id}"
       return (q.code, q.message, q.subject_scope or "", ref_key)
   ```
   Guarantees canonical, permutation-invariant ordering across `(code, message, subject_scope, subject_ref)`.

---

## 3. Test Evidence

### Wave 2 Adversarial Test Suite: `tests/unit/test_p4_wave2_provenance_validation.py`

23 tests covering all 14 required categories and advanced conditions:

| Category | Test Name | Result |
|---|---|---|
| 1. Backward compatibility (no fixtures) | `test_default_fixtures_by_id_is_none` | ✅ PASSED |
| 1. Backward compatibility (explicit None) | `test_explicit_none_fixtures_by_id` | ✅ PASSED |
| 1. Backward compatibility (bad locator ignored) | `test_invalid_locator_ignored_when_fixtures_by_id_none` | ✅ PASSED |
| 2. Empty fixtures mapping (`{}`) | `test_empty_fixtures_dict_emits_unresolved_fixture_issue` | ✅ PASSED |
| 3. Valid fixture mapping | `test_valid_jira_dereferences_cleanly` | ✅ PASSED |
| 3. Valid fixture mapping (multi-observation) | `test_multiple_observations_all_resolve` | ✅ PASSED |
| 4. Missing `fixture_id` (zero guessing) | `test_missing_fixture_id_emits_unresolved_issue` | ✅ PASSED |
| 5. Wrong `fixture_id` (not in mapping) | `test_wrong_fixture_id_emits_unresolved_issue` | ✅ PASSED |
| 6. Malformed locator (syntax error) | `test_unclosed_bracket` | ✅ PASSED |
| 6. Malformed locator (unauthorized collection) | `test_unauthorized_collection` | ✅ PASSED |
| 7. Out-of-bounds locator | `test_out_of_bounds_index` | ✅ PASSED |
| 8. Entity identity mismatch | `test_jira_identity_mismatch_detected` | ✅ PASSED |
| 9. Invalid `source_field_path` | `test_nonexistent_field_path_detected` | ✅ PASSED |
| 9. Valid `source_field_path` | `test_valid_field_path_passes` | ✅ PASSED |
| 10. Locator-less provenance (`record_locator=None`) | `test_none_locator_skipped_cleanly` | ✅ PASSED |
| 11. Structural + dereference error coexisting | `test_unknown_obs_id_and_malformed_locator_both_reported` | ✅ PASSED |
| 12. Provenance permutation invariance | `test_different_prov_order_produces_identical_issues` | ✅ PASSED |
| 13. Duplicate provenance determinism | `test_duplicate_prov_refs_do_not_duplicate_issues` | ✅ PASSED |
| 14. Real fixture integration | `test_northstar_and_clean_github_validate_cleanly_with_fixtures` | ✅ PASSED |
| 15. Relationship provenance dereferencing | `test_relationship_invalid_locator_detected` | ✅ PASSED |
| 15. Unresolved reference provenance | `test_unresolved_reference_invalid_locator_detected` | ✅ PASSED |
| 16. Temporal cutoff staleness detection | `test_temporal_cutoff_staleness_detected` | ✅ PASSED |
| 16. Fixture wrapper object support | `test_fixture_wrapper_object_supported` | ✅ PASSED |

### Full Test Suite Regression

```text
Baseline (Pass 3.1):           527 passed
Pass 4 Wave 1:                  91 passed
Pass 4 Wave 2:                  23 passed
------------------------------------------
Total:                         641 passed
Failures:                        0
Skipped:                         0
Time:                            8.98s
```

---

## 4. Mahout Qualification Invariants Verification

Executed with `save_golden=False`:

```python
from mahout.runner import run_mahout_qualification
res = run_mahout_qualification(save_golden=False)
```

| Invariant | Expected Value | Actual Value | Verdict |
|---|---|---|---|
| Repeatable | `True` | `True` | ✅ VERIFIED |
| Accepted work items | `412` | `412` | ✅ VERIFIED |
| Triggered matches | `12` | `12` | ✅ VERIFIED |
| Rules triggered | `['STALLED_WORK']` | `['STALLED_WORK']` | ✅ VERIFIED |
| Incomplete at period end | `56` | `56` | ✅ VERIFIED |
| Missing due dates | `370` | `370` | ✅ VERIFIED |
| Mutation guard active | `True` | `True` | ✅ VERIFIED |
| Jira mutations | `0` | `0` | ✅ VERIFIED |
| Configuration mutations | `0` | `0` | ✅ VERIFIED |

---

## 5. Protected Baselines Verification

| Artifact / Baseline | Constraint | Status |
|---|---|---|
| `evaluate_week_one_rules()` | Do not modify signature or logic | ✅ UNTOUCHED |
| `calculate_supporting_facts()` | Do not modify | ✅ UNTOUCHED |
| Mahout raw capture | Do not modify | ✅ UNTOUCHED |
| Mahout allowlists | Do not modify | ✅ UNTOUCHED |
| Historical golden artifacts | Do not modify | ✅ UNTOUCHED |
| `develop` baseline (`6d82d12`) | Do not touch | ✅ PROTECTED |
| Live Jira/GitHub writes | None | ✅ ZERO I/O |

---

## 6. Artifact Synchronization

The following artifacts have been updated and synchronized:
- `ADR-004_PROVENANCE_DEREFERENCING.md`
- `PASS4_WAVE2_EXECUTION_REPORT.md`
- Synced to `/home/tecblic/orbit_pass4_milestone2/`
- Synced to `<appDataDir>/brain/8a44eb06-14a2-47a0-9c3c-b117e8938d76/`

---

## 7. Final Classification

**Wave 2 PASS**

Evidence:
1. Complete backward compatibility maintained across all 527 baseline tests.
2. In-memory provenance dereferencing successfully integrated into `validate_evidence_bundle()`.
3. Zero-guessing fixture identification strictly enforced.
4. All 14 required adversarial test scenarios passing (23 tests total).
5. Full regression suite at 641 passed, 0 failed, 0 skipped.
6. Mahout qualification invariants exactly preserved (412 / 12 / 56 / 370 / 0 mutations).
7. Zero external I/O introduced.
8. No modification to `evaluate_week_one_rules()` or protected baselines.

---

## 8. Wave 2 Complete — STOPPED

Wave 2 is complete. Wave 3 (GitHub/Jira cross-source fusion evaluation) has NOT been started.

**Awaiting user review before Wave 3.**
