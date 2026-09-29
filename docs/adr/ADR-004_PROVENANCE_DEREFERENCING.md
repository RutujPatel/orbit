# ADR-004: Bounded In-Memory Provenance Dereferencing & EvidenceBundle Integration

**Status:** Accepted (Updated with Wave 2 Integration)  
**Date:** 2026-09-28  
**Pass:** Pass 4 / Waves 1 & 2 (Milestone 2)  
**Author:** Forensic Engineering (Automated)

---

## Context

Pass 3.1 evidence audit (P2.5-20, PASS4 Repository Reconnaissance Q7) identified that
`validate_evidence_bundle()` treats `ProvenanceRef.record_locator` as uninspected opaque
text. Every observation and relationship carries provenance references with locator strings
like `work_items[0]`, `repositories[0].pull_requests[101]`, or
`repositories[repo-core].branches[main]`, but no code verified that these locators
actually resolve to the claimed source record, that the resolved record's identity matches
the `EntityRef`, or that the `source_field_path` exists on the resolved record.

This meant the evidence chain from "this finding came from this source record" was
**structurally claimed but never mechanically verified**.

---

## Decisions

### 1. Bounded In-Memory Provenance Resolver (Wave 1)

Implemented in `src/shadow_orbit/provenance_dereference.py`:

1. **Parses** `record_locator` strings into a validated grammar of `collection[selector]` segments.
2. **Resolves** each segment against in-memory fixture dictionaries (or fixture wrapper objects
   with a `raw_document` attribute).
3. **Verifies entity identity** by comparing the dereferenced record's natural key/id against
   the expected `EntityRef`.
4. **Validates `source_field_path`** by traversing the resolved record.
5. **Checks temporal bounds** against an optional `source_cutoff_at`.
6. **Detects access-denied** records.
7. **Emits structured `QualityIssue`** values for every failure mode.
8. **Performs zero external I/O** — no network, no filesystem, no database access.

### 2. EvidenceBundle Validation Integration (Wave 2)

Integrated into `validate_evidence_bundle(bundle, fixtures_by_id=None)` in
`src/shadow_orbit/evidence_assembly.py`:

1. **Optional parameter `fixtures_by_id`**: Defaults to `None`. When `None`, active
   dereferencing is skipped, guaranteeing 100% backward compatibility for all existing
   callers and test suites.
2. **Deterministic fixture identification (Zero Guessing)**:
   - When `fixtures_by_id` is supplied and `p.record_locator` is present:
     - If `p.fixture_id` is absent (`None`): emits structured `QualityIssue(code="unresolved", subject_scope="provenance:fixture")`. The resolver never guesses or selects a default fixture.
     - If `p.fixture_id` is not present in `fixtures_by_id`: emits structured `QualityIssue(code="unresolved", subject_scope="provenance:fixture")`.
     - If `p.fixture_id` maps to a valid fixture document: dereferencing executes via `dereference_provenance_ref`.
3. **Optional locator preservation (`record_locator=None`)**:
   - Provenance references without a locator are skipped during dereferencing. No quality
     issue is emitted solely for locator absence unless an explicit contract mandates it.
4. **Dual validation semantics**:
   - Dereferencing supplements existing structural provenance validation (e.g. registered
     observation context existence, source instance alignment); it does not replace it.
   - When both a structural defect and a dereferencing failure occur on the same provenance
     reference, both quality issues are recorded.
5. **Permutation & Duplicate Determinism**:
   - Quality issues are canonically sorted using `(code, message, subject_scope, subject_ref_key)`.
   - Repeated/duplicate identical provenance references produce deterministic output.

### Resolution Status Taxonomy (Closed Set)

| Status | Meaning | Emitted QualityCode |
|---|---|---|
| `RESOLVED` | Locator resolves, identity matches, field exists | None |
| `NOT_FOUND` | Collection missing, index OOB, identifier not found, field absent | `unresolved` / `missing` |
| `ACCESS_DENIED` | Record present but access-restricted | `unsupported_value` |
| `UNAVAILABLE` | Fixture missing from mapping or absent fixture_id | `unresolved` |
| `MALFORMED_LOCATOR` | Locator string violates grammar | `invalid` |
| `UNSUPPORTED_LOCATOR` | Collection name not in authorized set | `unsupported_value` |
| `STALE` | Record timestamp postdates source cutoff | `invalid` |
| `AMBIGUOUS` | Multiple records match an identifier selector | `invalid` |
| `INVALID` | Resolved record is non-dict, or identity contradiction | `invalid` / `contradictory` |

### Locator Grammar & Resolution Rules

```
locator       := segment ("." segment)*
segment       := collection "[" selector "]"
collection    := work_items | repositories | branches | commits | pull_requests | reviews
selector      := <digits>          → is_index=True (0-based array index)
               | <non-digit-str>   → is_index=False (natural identifier)
```

1. **Index selector** (`is_index=True`):
   - Fast path: direct 0-based array indexing (`0 <= idx < len(items)`).
   - Compatibility fallback: ONLY if `idx >= len(items)` (genuine out-of-bounds), scan for
     natural numeric identifiers (`number`, `source_id`, `id`). In-bounds indices ALWAYS win.
2. **String selector** (`is_index=False`):
   - Natural-key match by collection type.
3. **Commit SHA prefix**:
   - For `commits` collection, string selectors ≥ 7 characters match via `sha.startswith(selector)`.
4. **Tuple collection support**:
   - Collections may be `list` or `tuple` (supporting frozen `ValidatedFixture.accepted_raw_items`).

---

## Consequences

- Provenance claims are now mechanically verifiable against in-memory source fixtures.
- Every observation, structural relationship, and unresolved reference in an assembled
  `EvidenceBundle` can have its provenance verified deterministically.
- `validate_evidence_bundle()` retains full backward compatibility when called without
  `fixtures_by_id`.
- The evaluation engine remains 100% deterministic with zero external I/O.
- P3-05 and P2.5-17 integration gaps are formally closed.

---

## Verification

- **Wave 1 adversarial tests**: 91 tests in `tests/unit/test_p4_provenance_dereferencing.py`.
- **Wave 2 integration tests**: 23 tests in `tests/unit/test_p4_wave2_provenance_validation.py`.
- **Full test suite**: 641 passed, 0 failed, 0 skipped.
- **Mahout qualification invariants**:
  - Repeatable = True
  - Accepted work items = 412
  - STALLED_WORK findings = 12
  - Known incomplete at period end = 56
  - Missing due dates = 370
  - Jira mutations = 0
  - Configuration mutations = 0
  - Mutation guard active = True
