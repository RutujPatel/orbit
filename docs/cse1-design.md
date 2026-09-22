# CSE-1 — Cross-System Evidence Foundation

**Status:** Design approved, implementation in progress.
**Baseline:** `develop` branch, commit `8615a07`, 110 tests passing.
**Dependencies added:** None. Zero runtime dependencies preserved.

---

## 1. Objective

Implement a deterministic, typed, file-based representation of independently
observed Jira and GitHub entities, together with provenance-bearing explicit
and structural relationships, while preserving all existing Jira behavior
and making no new management conclusions.

CSE-1 ends at: **normalized evidence bundle**.

CSE-1 does NOT produce: cross-system findings, recommendations,
manager-facing GitHub intelligence, scoring, risk, severity,
predictions, or interpretation.

---

## 2. Architecture

CSE-1 uses an additive, observation-centered architecture alongside the
existing Jira evaluation pipeline.

```
Jira fixture
    ↓
existing Jira validation
    ↓
existing Jira normalization
    ├──────────────→ existing Jira evaluation / artifact path
    ↓                (WorkItem, RuleMatch, etc. — unchanged)
additive Jira evidence adapter
    ↓
                 ┌─────────────────┐
GitHub fixture → │ GitHub validate  │
                 └───────┬─────────┘
                         ↓
                  GitHub normalize
                         ↓
                         └───────┐
                                 ↓
                       typed evidence observations
                                 ↓
                          relationships
                                 ↓
                       deterministic bundle
```

The existing Jira evaluation/artifact behavior stays on its current path.
Nothing in `types.py`, `validation.py`, `normalization.py`, `temporal.py`,
`evaluation.py`, `artifact.py`, `human_state.py`, `deltas.py`,
`continuity.py`, `messy_acceptance.py`, or `acceptance.py` is modified.

---

## 3. Source Independence

Each source system (Jira, GitHub) has its own:

- fixture contract and schema
- validator
- normalizer
- typed payload representation

No source system's abstractions leak into another.

GitHub PRs are not Jira WorkItems.
Jira issues are not GitHub entities.
`WorkItem` remains Jira-specific.

---

## 4. Identity Semantics

`EntityRef` is the canonical identity abstraction:

```
EntityRef
    source_instance: SourceInstance  (which Jira site / GitHub org)
    entity_kind: EntityKind          (what type of entity)
    entity_id: str                   (identity within that scope)
```

`EntityRef.entity_kind` is the sole authority for an entity's type.
No other field duplicates this.

Identity rules:

| Entity | Identity scope |
|--------|---------------|
| Jira issue | source instance + issue key |
| GitHub repository | source instance + repository ID |
| GitHub branch | repository identity + branch name |
| GitHub commit | repository identity + full SHA |
| GitHub pull request | repository identity + PR number |
| GitHub review | PR identity + review ID |

Repository names are locators, not canonical identity.
Branch names are repository-scoped.
PR numbers are repository-scoped.

Person identity resolution is explicitly out of scope.

---

## 5. Observation Semantics

`SourceObservation` (represented as `ObservationContext`) and
`EvidenceObservation` are distinct concepts.

**ObservationContext** represents the act of observing:

- observation identity
- source instance
- observation interval (when the observation window covers)
- source cutoff (when the snapshot was taken)
- coverage context (known incompleteness)

**Temporal distinctions preserved:**

| Concept | Meaning |
|---------|---------|
| Event time | When something happened in the source system |
| Observation interval | The time window the observation covers |
| Source cutoff | When we captured the snapshot |

These are intentionally separate fields. A single cutoff timestamp
must not carry multiple temporal meanings.

**EvidenceObservation** represents one entity's observed state
inside one observation:

- entity reference (EntityRef)
- observation context reference
- typed source-specific payload
- quality issues
- provenance references

An entity may appear in multiple observations with stable identity.

---

## 6. Relationship Semantics (CSE-1.5 & CSE-1.6)

Relationships are explicit, typed, and provenance-bearing.

- CSE-1.5 establishes structural relationships (`belongs_to_repository`, `review_of`, `has_head_branch`, `has_base_branch`, `contains_commit`, `has_head_commit`, `has_base_commit`) under `basis="structural_association"`.
- CSE-1.6 establishes explicit textual mentions (`mentions`) under `basis="lexical_match"` via a configured lexical policy.

A text match (e.g., "PLAT-101" appearing in a PR title or commit message)
proves only the literal text match — not business association,
implementation, completion, approval, or deployment.

"mentions" remains strictly literal. No scoring, severity, confidence, or
semantic inference.

---

## 7. Provenance Principles

Provenance is structured and bounded, distinguishing:

| Kind | What it answers |
|------|----------------|
| Entity provenance | Which supplied record supports this state? |
| Relationship provenance | Which source field supports this relationship? |
| Derivation provenance | Which transformation produced this derived artifact? |

Provenance uses explicit typed references:

- `ProvenanceRef` — source instance, observation ID, fixture ID,
  record locator, source field path
- `DerivationRef` — transformation ID, version, source refs

No `provenance: Any` or `metadata: dict[str, Any]`.

---

## 8. Coverage Principles

Partial data must never silently become absence claims.

```
Partial review data ≠ "there were no reviews"
Partial commit data ≠ "there was no development"
```

CSE-1 does not implement absence reasoning, but the architecture
preserves coverage information (via `ObservationContext.coverage_note`
and collection-level `QualityIssue`) so that future evaluation stages
can distinguish "not observed" from "observed as absent".

---

## 9. Quality Principles

Quality uses a closed code vocabulary:

```
missing | invalid | unsupported_value | contradictory | incomplete | unresolved
```

No confidence scores. No severity. No risk.

Quality issues can apply to:

- entities (via `subject_ref: EntityRef`)
- observations, collections, documents, relationships, fields
  (via `subject_scope: str`)

The existing honesty invariants are preserved:

```
unknown    ≠ false
missing    ≠ complete
unmapped   ≠ normal
invalid    ≠ absent
quarantined ≠ accepted
unsupported inference ≠ deterministic fact
```

---

## 10. Non-Goals

CSE-1 does NOT:

- replace or modify the existing Jira evaluation pipeline
- add AI, LLM, ML, embeddings, or predictions
- add network access, API clients, or databases
- add scoring, severity, risk, or health metrics
- add manager recommendations or new management rules
- add a generalized rule DSL or plugin framework
- introduce runtime dependencies
- optimize for GoGreen or SmartSHARK
- create a universal WorkItem / Ticket / EngineeringItem abstraction

---

## 11. Implementation Stages

| Stage | Purpose | Status |
|-------|---------|--------|
| CSE-1.1 | Contract & compatibility checkpoint | ✅ |
| CSE-1.2 | Identity, observation, provenance foundation | ✅ |
| CSE-1.3 | GitHub typed entities + validation + normalization | ✅ |
| CSE-1.4 | Additive Jira evidence wrapper | ✅ |
| CSE-1.5 | Structural relationships | ✅ |
| CSE-1.6 | Explicit Jira mentions (configured lexical policy) | ✅ |
| CSE-1.7 | Cross-system manifest/orchestration + EvidenceBundle | ✅ |
| CSE-1.8 | Full compatibility + research-safety checkpoint | ✅ |

Each stage requires review before the next is authorized.

---

## 12. Compatibility Statement

The existing Jira engine at HEAD `8615a07` is the protected baseline:

- `types.py` — unchanged
- `fixture_io.py` — unchanged
- `validation.py` — unchanged
- `normalization.py` — unchanged
- `temporal.py` — unchanged
- `evaluation.py` — unchanged
- `artifact.py` — unchanged
- `human_state.py` — unchanged
- `deltas.py` — unchanged
- `continuity.py` — unchanged
- `messy_acceptance.py` — unchanged
- `acceptance.py` — unchanged
- All 110 existing tests — unchanged
- All 3 fixtures — unchanged
- All 3 expected artifacts — unchanged
- Human state sidecar — unchanged
- `pyproject.toml` dependencies — unchanged (empty)

The new evidence foundation lives in `evidence_types.py` and is
not imported by any existing module.
