# Phase 4C — Architectural Analysis of Schema Placement Options

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4C — Formal Repository Evolution Schema Specification  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Status:** **ARCHITECTURAL COMPARISON & SELECTION COMPLETE**  

---

## 1. Problem Statement & Comparison Criteria

To implement **Option B (Minimal Evolution Metadata)** from Phase 4B, the canonical contract must define where and how repository evolution relationships reside within ORBIT's evidence architecture.

Four candidate architectural placements are evaluated against seven rigorous criteria:
1. **Semantic Fidelity:** Does the structure accurately model repository-to-repository evolution without confusing it with PR-level facts?
2. **Endpoint Safety:** Does the structure guarantee that endpoints are repository entities (`entity_kind="repository"`), preventing pull request identity collapse?
3. **Backward Compatibility:** Can existing tools, bundles, serializers, and Track A/B evaluators consume or ignore the data without modification?
4. **Provenance Grounding:** Does the placement provide direct, verifiable links to source provenance (`ProvenanceRef`)?
5. **Temporal Precision:** Can the placement represent effective validity windows (`valid_from`, `valid_to`) alongside observation timestamps?
6. **Query & Validation Ergonomics:** Can the model be validated with clean, deterministic, fail-closed rules?
7. **Implementation Overhead:** What is the engineering footprint required when future implementation is authorized?

---

## 2. Detailed Evaluation of Candidate Schema Placements

---

### Candidate 1: Extension of Existing `EvidenceRelationship`

* **Concept:** Expand `RelationshipKind` in `EvidenceRelationship` to include repository evolution kinds (e.g. `"predecessor_of"`, `"redirects_to"`, `"depends_on"`), reusing `EvidenceBundle.relationships`.
* **Advantages:**
  - High container reuse: `EvidenceBundle.relationships` already exists and is parsed by existing bundle serializers.
  - Native provenance: `EvidenceRelationship` already includes `provenance_refs: tuple[ProvenanceRef, ...]`.
* **Disadvantages & Semantic Risks:**
  - **Flat Schema Limitation:** `EvidenceRelationship` has a fixed flat schema (`subject_ref`, `object_ref`, `kind`, `basis`). It possesses no fields for directional semantics, effective temporal intervals (`valid_from`, `valid_to`), redirect HTTP codes, or family-specific payloads.
  - **Semantic Conflation:** Existing `EvidenceRelationship` represents structural and lexical associations between fine-grained entities (e.g., `PR contains commit`, `PR review_of PR`, `PR mentions Issue`). Infiltrating it with macro-level repository evolution creates polymorphic query pollution in the evaluator.
  - **Endpoint Enforcement Gaps:** Existing `EvidenceRelationship` allows any `EntityRef` pair; it lacks type-level constraints ensuring that both subject and object are strictly `entity_kind="repository"`.

---

### Candidate 2: Observation Metadata Annotation (`extra_properties`)

* **Concept:** Store repository evolution facts inside `extra_properties` of `CodeChangeState`, `WorkItemState`, or `ObservationContext.coverage_note`.
* **Advantages:**
  - Zero schema changes: Requires no new classes or fields in `evidence_types.py`.
  - Zero serialization changes: Handled by generic dict serialization.
* **Disadvantages & Semantic Risks:**
  - **Severe Architectural Distortion:** Repository evolution is a macro relationship between two repository entities. Attaching it to a pull request observation distorts reality: PR `#126` does not "evolve into" another repository.
  - **Massive Data Duplication:** Every single PR observation across Flink's 448 Stratosphere references would need to duplicate identical predecessor metadata.
  - **Untyped and Fragile:** Dictionaries provide no schema validation, fail-open on typos, and cannot enforce provenance integrity.
  - **Unqueryable:** The evaluator would have to inspect nested untyped dictionaries to discover repository lineage.

---

### Candidate 3: Dedicated Repository Evolution Relationship Envelope (`RepositoryEvolutionRelationship`)

* **Concept:** A standalone canonical dataclass placed in a dedicated collection on `EvidenceBundle` (e.g. `repository_relationships: tuple[RepositoryEvolutionRelationship, ...] = ()`). The envelope defines common identity, direction, temporal, and provenance fields, with a typed, family-discriminated payload.
* **Advantages:**
  - **Maximum Semantic Fidelity:** Strictly models relationships between repository-level entities (`entity_kind="repository"`).
  - **Absolute Endpoint Safety:** Schema strictly enforces that `source_repository.entity_kind == "repository"` and `target_repository.entity_kind == "repository"`. Zero possibility of PR-level identity collapse.
  - **Temporal & Directional Precision:** Encapsulates explicit direction, family classification, observation timestamps, and effective validity windows (`valid_from`, `valid_to`).
  - **Full Backward Compatibility:** Can be added to `EvidenceBundle` as an optional field with a default empty tuple `()`. Historical bundles without this field deserialize seamlessly with zero diff.
  - **Provenance Integrity:** Carries dedicated `provenance_refs` verified by ORBIT's existing dereferencing engine.
* **Disadvantages & Semantic Risks:**
  - Requires defining a new dataclass in `evidence_types.py` and updating bundle validators when implementation is authorized.

---

### Candidate 4: Multiple Independent Disjoint Canonical Relation Structures

* **Concept:** Create four separate independent relationship classes (`RepositoryRedirectRecord`, `RepositoryLineageRecord`, `RepositoryTopologyRecord`, `RepositoryDependencyRecord`), each placed in its own separate collection on `EvidenceBundle`.
* **Advantages:**
  - Complete isolation between different evolution categories.
  - Highly tailored fields for each specific family.
* **Disadvantages & Semantic Risks:**
  - **Over-Engineering & Surface Bloat:** Adds 4 new dataclasses and 4 new tuple fields to `EvidenceBundle`.
  - **Validation Fragmentation:** Forces validators and serializers to implement 4 parallel validation passes instead of one unified pass.
  - **Ecosystem Overhead:** Future tools would need to query 4 different collections to inspect repository context.

---

## 3. Comparison Matrix

| Evaluation Criterion | Candidate 1: `EvidenceRelationship` Extension | Candidate 2: Observation Metadata | Candidate 3: Dedicated Envelope (`RepositoryEvolutionRelationship`) | Candidate 4: Multiple Disjoint Structures |
| :--- | :--- | :--- | :--- | :--- |
| **Semantic Fidelity** | Low | Unacceptable | **Highest** | High |
| **Endpoint Safety** | Moderate (requires validator check) | Unacceptable | **Absolute** (Strict `entity_kind="repository"`) | Absolute |
| **Backward Compatibility** | High | High | **100% (Default empty tuple)** | Moderate |
| **Provenance Grounding** | Reuses existing | Fragile / Untyped | **Native & Dedicated** | Native |
| **Temporal Precision** | Poor (no interval fields) | Poor | **Complete (`valid_from`/`valid_to`)** | Complete |
| **Ergonomics & Validation** | Pollutes relationship queries | Poor | **Unified, Typed, Fail-Closed** | Fragmented across 4 lists |
| **Implementation Complexity** | Low | Low | **Moderate & Bounded** | High |

---

## 4. Architectural Selection and Rationale

### Selection: **Candidate 3 — Dedicated Repository Evolution Relationship Envelope (`RepositoryEvolutionRelationship`)**

### Forensic Rationale:
1. **Non-Negotiable Invariant Protection:** Candidate 3 provides a compile-time and runtime guarantee that endpoints are strictly `entity_kind="repository"`. Pull request entities cannot accidentally be passed as evolution endpoints.
2. **Clean Separation of Concerns:** Preserves the existing `EvidenceRelationship` for fine-grained entity links (`belongs_to_repository`, `mentions`, `review_of`), while providing a dedicated structure for macro-level repository evolution.
3. **Clean Family Discrimination:** Option B from Phase 4B requires distinguishing between navigation redirects, project lineage, topology, and dependencies. Candidate 3 achieves this via a typed envelope with a discriminated metadata payload, avoiding both Candidate 1's under-specification and Candidate 4's over-fragmentation.
4. **Zero Backward Invalidation:** By declaring `repository_relationships: tuple[RepositoryEvolutionRelationship, ...] = ()` on `EvidenceBundle`, all historical Phase 1, Phase 2, and Phase 3 bundles remain 100% valid and readable.
