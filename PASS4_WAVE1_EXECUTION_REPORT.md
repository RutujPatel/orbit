# PASS 4 — Wave 1 Execution Report

**Pass:** 4 / Milestone 2 — Bounded In-Memory Provenance Dereferencing  
**Wave:** 1 (of 3 authorized)  
**Date:** 2026-09-28  
**Branch:** `remediation/pass3-controlled-hardening`  
**Baseline Commit:** `e967ad57ea3b37cef4266134537acbb34e9ae715`  
**Protected Governing Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (develop)

---

## 1. Wave 1 Scope (as authorized)

| # | Objective | Status |
|---|---|---|
| 1 | Inventory every actual `ProvenanceRef.record_locator` format emitted by the codebase | ✅ COMPLETE |
| 2 | Define the smallest resolver grammar required by real locator forms | ✅ COMPLETE |
| 3 | Implement deterministic in-memory dereferencing | ✅ COMPLETE |
| 4 | Verify locator bounds | ✅ COMPLETE |
| 5 | Verify resolved entity identity against the referenced `EvidenceObservation`/entity | ✅ COMPLETE |
| 6 | Validate `source_field_path` where applicable | ✅ COMPLETE |
| 7 | Produce structured `QualityIssue` values for invalid/unresolved provenance | ✅ COMPLETE |
| 8 | Preserve unknown/unavailable evidence semantics | ✅ COMPLETE |
| 9 | Zero external I/O from resolver | ✅ COMPLETE |
| 10 | Do not modify `evaluate_week_one_rules()` | ✅ VERIFIED |
| 11 | Do not modify Mahout fixtures, allowlists, golden artifacts, or source captures | ✅ VERIFIED |
| 12 | Add adversarial Wave 1 tests | ✅ 91 tests |
| 13 | Run relevant tests, full regression suite, verify Mahout qualification invariants | ✅ 618/618 pass |
| 14 | Produce ADR-004 | ✅ COMPLETE |
| 15 | Produce Wave 1 execution report | ✅ THIS DOCUMENT |
| 16 | STOP after Wave 1 | ✅ STOPPED |

---

## 2. Locator Grammar Inventory

Exhaustive inventory of all `record_locator` formats emitted by the production codebase:

### Jira (via `jira_evidence_adapter.py`)

| Pattern | Example | Source |
|---|---|---|
| `work_items[<index>]` | `work_items[0]`, `work_items[11]` | `jira_evidence_adapter.py:275` |

### GitHub (via `github_validation.py` → `github_normalization.py`)

| Pattern | Example | Source |
|---|---|---|
| `repositories[<index>]` | `repositories[0]` | `github_validation.py:388` |
| `repositories[<r>].branches[<index>]` | `repositories[0].branches[0]` | `github_validation.py:485` |
| `repositories[<r>].commits[<index>]` | `repositories[0].commits[0]` | `github_validation.py:599` |
| `repositories[<r>].pull_requests[<index>]` | `repositories[0].pull_requests[0]` | `github_validation.py:742` |
| `repositories[<r>].pull_requests[<p>].reviews[<index>]` | `repositories[0].pull_requests[0].reviews[0]` | `github_validation.py:955` |

### GitHub (via `github_normalization.py` fallback when `_raw_locator` absent)

| Pattern | Example | Source |
|---|---|---|
| `repositories[<repo_id>]` | `repositories[repo-core]` | `github_normalization.py:99` |
| `repositories[<repo_id>].branches[<name>]` | `repositories[repo-core].branches[main]` | `github_normalization.py:135` |
| `repositories[<repo_id>].commits[<sha>]` | `repositories[repo-core].commits[c0ffee1]` | `github_normalization.py:169` |
| `repositories[<repo_id>].pull_requests[<number>]` | `repositories[repo-core].pull_requests[101]` | `github_normalization.py:215` |
| `repositories[<repo_id>].pull_requests[<number>].reviews[<id>]` | `repositories[repo-core].pull_requests[101].reviews[rev-1]` | `github_normalization.py:323` |

### GitHub (via `github_relationships.py` and `github_mentions.py`)

These reuse `record_locator` from the base observation's `ProvenanceRef` and append `source_field_path`.

---

## 3. Implementation Summary

### New File: `src/shadow_orbit/provenance_dereference.py` (566 lines)

| Component | Description |
|---|---|
| `ProvenanceResolutionStatus` | 9-value closed Literal type |
| `LocatorSegment` | Frozen dataclass: `(collection, selector, is_index)` |
| `DereferenceResult` | Frozen dataclass: `(status, record, field_value, error_message, quality_issue)` |
| `parse_locator()` | Grammar parser → `tuple[LocatorSegment, ...]` |
| `_extract_container_dict()` | Handles raw dict, wrapper with `raw_document` |
| `_resolve_selector_in_list()` | Index + identifier + numeric-ID-fallback resolution |
| `_verify_entity_identity()` | Per-entity-kind identity matching (6 kinds) |
| `_traverse_field_path()` | Dotted field path traversal with Jira `fields` fallback |
| `dereference_locator()` | Main entry point |
| `dereference_provenance_ref()` | Convenience wrapper for `ProvenanceRef` dataclass |

### New File: `tests/unit/test_p4_provenance_dereferencing.py` (91 tests)

| Test Class | Count | Covers |
|---|---|---|
| `TestParseLocator` | 13 | Grammar parsing, malformed inputs, unauthorized collections |
| `TestIndexResolution` | 7 | Valid/OOB indices, nested indices |
| `TestIdentifierResolution` | 12 | Key, source_id, repo_id, sha, branch name, PR number |
| `TestNumericIdFallback` | 4 | OOB index → numeric ID scan, ambiguous |
| `TestEntityIdentityVerification` | 10 | All 6 entity kinds, mismatch detection |
| `TestFieldPathTraversal` | 8 | Simple, nested, Jira fallback, missing, empty, None |
| `TestFixtureUnavailability` | 5 | None fixture, non-dict, access denied, non-dict record |
| `TestTemporalCutoff` | 3 | Before/after cutoff, no timestamp |
| `TestTupleCollections` | 3 | Tuple items, key resolution, OOB fallback |
| `TestDereferenceProvenanceRef` | 4 | Convenience wrapper paths |
| `TestCollectionEdgeCases` | 5 | Missing collection, None, non-list, non-object, nested |
| `TestQualityIssueStructure` | 7 | Code/scope verification for all failure modes |
| `TestFixtureIntegration` | 3 | Clean GitHub, messy GitHub, clean Jira (real fixtures) |
| `TestPermutationInvariance` | 2 | Jira key order, GitHub PR order |
| `TestDeterminism` | 2 | Repeated calls produce identical results |
| `TestFixtureWrapperSupport` | 2 | raw_document wrapper, no-doc fixture |

### Modified File: None

No existing files were modified. The dereferencer is additive-only.

### Key Design Decision: Numeric ID Fallback

When a numeric selector (e.g. `pull_requests[101]`) is parsed as `is_index=True` (because
`"101".isdigit() == True`) but the index 101 is out of bounds for the array (which may have
only 1 item), the resolver falls back to scanning for natural numeric identifiers:

- `pull_requests` → match `item.get("number")`
- `work_items` → match `item.get("source_id")` or `item.get("id")`
- `repositories` → match `item.get("repo_id")`
- `commits` → match `item.get("sha")`

This handles the real-world locator pattern `repositories[repo-core].pull_requests[101]`
where `101` is the PR number, not a 0-based index.

---

## 4. Regression Evidence

### Test Suite Results

```
P4 adversarial tests:  91 passed, 0 failed
Full regression suite: 618 passed, 0 failed (527 pre-existing + 91 new)
```

### Mahout Qualification Invariants (Unchanged)

| Invariant | Expected | Actual |
|---|---|---|
| Accepted work items | 412 | 412 ✅ |
| Triggered findings | 12 | 12 ✅ |
| Rules triggered | `[STALLED_WORK]` | `[STALLED_WORK]` ✅ |
| Incomplete at period end | 56 | 56 ✅ |
| Missing due date | 370 | 370 ✅ |
| Repeatable | True | True ✅ |
| Jira mutations | 0 | 0 ✅ |
| Configuration mutations | 0 | 0 ✅ |
| Mutation guard active | True | True ✅ |

### Fixture Dereference Verification

| Fixture | Observations | Provenance Refs | All Resolved |
|---|---|---|---|
| `clean_github_week_1.json` | 9 | 9 | ✅ 0 failures |
| `messy_github_week_1.json` | 5 | 5 | ✅ 0 failures |
| `northstar_clean_week_1.json` | 12 | 12 | ✅ 0 failures |
| `northstar_clean_week_2.json` | 13 | 13 | ✅ 0 failures |
| Mahout (412 items, via runner) | 412 | 412 | ✅ 0 failures |

---

## 5. Protected Baselines — Verified Unchanged

| Artifact | Status |
|---|---|
| `evaluate_week_one_rules()` | ✅ NOT MODIFIED |
| Mahout fixtures | ✅ NOT MODIFIED |
| Mahout allowlists | ✅ NOT MODIFIED |
| Mahout golden artifacts | ✅ NOT MODIFIED |
| Raw source captures | ✅ NOT MODIFIED |
| `develop` branch | ✅ NOT MODIFIED |

---

## 6. Produced Artifacts

| Artifact | Path |
|---|---|
| ADR-004 | `ADR-004_PROVENANCE_DEREFERENCING.md` |
| Implementation | `src/shadow_orbit/provenance_dereference.py` |
| Adversarial tests | `tests/unit/test_p4_provenance_dereferencing.py` |
| This report | `PASS4_WAVE1_EXECUTION_REPORT.md` |

---

## 7. Wave 1 Complete — STOPPED

Wave 1 is complete. The following Waves remain authorized but not yet executed:

- **Wave 2**: EvidenceBundle evaluation — wire dereferencing into `validate_evidence_bundle()`
- **Wave 3**: GitHub–Jira cross-source fusion evaluation

Awaiting user review before proceeding.
