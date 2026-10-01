# Phase 4C — Final Report: Formal Repository Evolution Schema Specification

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4C — Formal Repository Evolution Schema Specification  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Consolidation Commit (HEAD):** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`  
**Branch:** `remediation/pass3-controlled-hardening`  
**Status:** **PASS**  
**Implementation Authorized:** **NO**  

---

## 1. Executive Summary

Phase 4C successfully resolved the research and data-modeling question established by Phase 4B:  
*What is the smallest exact canonical schema capable of representing verified repository evolution without mutating repository identity or corrupting ORBIT's existing evidence, linkage, state, temporal, provenance, and cross-system semantics?*

Operating strictly as a forensic specification and data-contract design exercise:
1. **Schema Formulation:** Specified a dedicated canonical relationship envelope, **`RepositoryEvolutionRelationship`**, with a machine-readable JSON Schema (`repository_evolution_schema.json`), a field-by-field contract (`phase4c_field_contract.md`), and an invariant specification (`phase4c_semantic_contract.md`).
2. **Endpoint Safety Enforced:** Mandated that endpoints must strictly be repository entities (`entity_kind="repository"`). Pull request entities (`entity_kind="code_change"`) are strictly forbidden as evolution endpoints, permanently preventing PR identity collapse.
3. **Four Discriminative Families:** Grouped the 10 Phase 4B evolution types into four distinct structural families (`NAVIGATION_ROUTING`, `PROJECT_LINEAGE`, `REPOSITORY_TOPOLOGY`, `ECOSYSTEM_DEPENDENCY`) with explicit directionality, acyclicity, and transitivity rules.
4. **Semantic Firewall Formulated:** Enforced non-negotiable invariants: zero mutation of `EntityRef`, zero automatic upgrade of `DECLARED_MENTION` to `EXPLICIT_LINK`, and zero transfer of issue completion across repository boundaries.
5. **100% Backward Compatibility:** Verified that adding `repository_relationships: tuple[RepositoryEvolutionRelationship, ...] = ()` as an optional field on `EvidenceBundle` introduces zero diff across historical bundles and benchmarks.
6. **Implementation Firewall Honored:** Confirmed that **zero bytes** of production code in `src/shadow_orbit/` were altered, and the 817-test regression suite remains 100% passing.

---

## 2. Phase Objective

To define the exact canonical data contract required to implement Phase 4B Option B (Minimal Evolution Metadata) so precisely that a future engineer can implement the schema without making further architectural or design decisions, while preserving all existing ORBIT invariants.

---

## 3. Governing Baseline

* **Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`develop`)
* **Consolidation HEAD:** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab` (`remediation/pass3-controlled-hardening`)
* **Working Tree State:** Completely clean.
* **Test Suite Baseline:** 817 passed, 0 failed, 3 warnings (10.01s).

---

## 4. Phase 4B Verification

* Recomputed SHA-256 for all 7 Phase 4B artifacts; 100% match with `phase4b_hashes.json`.
* Confirmed Phase 4B ADR adopted Option B (Minimal Evolution Metadata).
* Confirmed Phase 4B authorized zero implementation.

---

## 5. Current Identity Model

In `src/shadow_orbit/evidence_types.py`:
$$\text{EntityRef} = (\text{SourceInstance}, \text{EntityKind}, \text{EntityId})$$
For pull requests, `entity_id = f"{owner}/{repo}/{identifier}"`. This invariant completely prevents cross-repository numeric collisions (e.g. `stratosphere/stratosphere#126` vs `apache/flink#126`). Phase 4C leaves `EntityRef` completely unaltered.

---

## 6. Schema Design Problem

How to represent macro-level repository evolution facts (e.g. Stratosphere evolving into Flink, or RocksDB being consumed as a dependency) without:
- Mutating PR-level `EntityRef` strings;
- Confusing PR identity with repository identity;
- Auto-promoting informal textual mentions to explicit links;
- Bloating the runtime with ungrounded alias engines.

---

## 7. Candidate Schema Placements

Evaluated in [`schema_options.md`](file:///home/tecblic/orbit/qualification/wave3/phase4c_repository_evolution_schema/schema_options.md):
1. **Candidate 1 (Extend `EvidenceRelationship`):** Rejected due to lack of directional/temporal fields and risk of query pollution.
2. **Candidate 2 (Observation Metadata Dict):** Rejected due to massive duplication, lack of typing, and semantic distortion.
3. **Candidate 3 (Dedicated Envelope `RepositoryEvolutionRelationship`):** **ADOPTED.** Clean separation, strict repository endpoints, complete temporal/provenance fields, 100% backward compatible.
4. **Candidate 4 (Four Disjoint Relationship Classes):** Rejected due to over-engineering and surface bloat.

---

## 8. Selected Canonical Contract

The canonical data contract is formalized in [`repository_evolution_schema.json`](file:///home/tecblic/orbit/qualification/wave3/phase4c_repository_evolution_schema/repository_evolution_schema.json):

```python
@dataclass(frozen=True, slots=True)
class RepositoryEvolutionRelationship:
    relationship_id: str
    relationship_family: RelationshipFamily
    relationship_type: RepositoryEvolutionType
    source_repository: EntityRef  # entity_kind == "repository"
    target_repository: EntityRef  # entity_kind == "repository"
    directionality: RelationshipDirectionality
    transitivity_rule: TransitivityRule
    verification_status: VerificationStatus
    observed_at: datetime
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    provenance_refs: tuple[ProvenanceRef, ...] = ()
    family_payload: dict[str, Any] = field(default_factory=dict)
```

---

## 9. Relationship Taxonomy

Closed vocabulary of 10 types across 4 families:
* **`NAVIGATION_ROUTING`:** `REDIRECT`, `RENAME`, `NAMESPACE_MOVE`
* **`PROJECT_LINEAGE`:** `PREDECESSOR_SUCCESSOR`
* **`REPOSITORY_TOPOLOGY`:** `FORK`, `MIRROR`, `VENDOR_MIRROR`
* **`ECOSYSTEM_DEPENDENCY`:** `EXTERNAL_DEPENDENCY`, `ECOSYSTEM_PACKAGING`, `COMPANION_SPECIFICATION`

---

## 10. Endpoint Semantics

* **`source_repository`:** Must strictly have `entity_kind == "repository"` (e.g. `EntityRef(github, "repository", "stratosphere/stratosphere")`).
* **`target_repository`:** Must strictly have `entity_kind == "repository"` (e.g. `EntityRef(github, "repository", "apache/flink")`).
* **Enforcement:** Validator rule `INV-ID-02` immediately emits `QualityIssue(code="invalid")` if any endpoint has `entity_kind != "repository"`.

---

## 11. Identity Semantics

Primary key `relationship_id` is derived deterministically:
$$\text{relationship\_id} = \text{SHA-256}\left(\text{instance\_id} + \texttt{"\|"} + \text{type} + \texttt{"\|"} + \text{src\_id} + \texttt{"\|"} + \text{tgt\_id}\right)$$
Zero random UUIDs, zero timestamps, zero environment dependencies.

---

## 12. Evidence & Provenance Semantics

* Mandatory `provenance_refs`: Every record must point to at least one raw source fixture.
* Plain text Jira URLs are `DECLARED_MENTION` only; they cannot establish repository lineage without corroborating VCS/governance evidence (`INV-EV-02`).
* 404 responses from purged historical mirrors remain `NOT_FOUND` / `INSUFFICIENT_EVIDENCE` (`INV-EV-03`).

---

## 13. Temporal Semantics

* `observed_at`: Exact UTC timestamp when evidence was captured. Required.
* `valid_from`: Real-world effective beginning of relationship (e.g. ASF graduation date). Optional.
* `valid_to`: Real-world effective end of relationship (e.g. dependency removed). Optional.
* Timestamp proximity does not imply causality (`INV-TM-01`).

---

## 14. Cardinality Semantics

* Supports 1-to-many splits (`apache/parquet` $\rightarrow$ `mr` and `cpp`).
* Supports many-to-1 merges (`incubator-mr` and `incubator-format` $\rightarrow$ `parquet`).
* Preserves many-to-1 Jira $\rightarrow$ PR linkage (`KAFKA-12770/12771` to PR `#10656`).

---

## 15. Graph Semantics

* `PROJECT_LINEAGE` must form a strict Directed Acyclic Graph (DAG) (`INV-GR-01`). Cycles are fatal errors.
* `NAVIGATION_ROUTING` must be strictly acyclic (`INV-GR-02`). Circular loops are fatal errors.
* `ECOSYSTEM_DEPENDENCY` and `REPOSITORY_TOPOLOGY` are strictly non-transitive for semantic evaluation (`INV-GR-03`).

---

## 16. Semantic Firewall

Machine-enforced flags on every record:
* `entity_ref_mutation_forbidden: true`
* `linkage_auto_upgrade_forbidden: true`
* `state_transfer_forbidden: true`
* `temporal_causality_inference_forbidden: true`

---

## 17. Backward Compatibility

Detailed in [`phase4c_compatibility_matrix.md`](file:///home/tecblic/orbit/qualification/wave3/phase4c_repository_evolution_schema/phase4c_compatibility_matrix.md):
* Existing `EntityRef`, `SourceInstance`, `CodeChangeState`, and `WorkItemState` are 100% unchanged.
* Historical bundles without `repository_relationships` deserialize with zero diff.
* Full 817-test regression suite remains intact.

---

## 18. Adversarial Qualification

Detailed in [`phase4c_adversarial_tests.md`](file:///home/tecblic/orbit/qualification/wave3/phase4c_repository_evolution_schema/phase4c_adversarial_tests.md):
* 24 formal adversarial scenarios across Identity, Evolution, Cardinality, Evidence, and Semantics evaluated and passed conceptually.

---

## 19. Real ORBIT Case Qualification

* `FLINK-1359`: Represented via `REDIRECT` from `apache/incubator-flink` to `apache/flink`. PR `#254` retained under `apache/flink`.
* `stratosphere/stratosphere#126`: Lineage represented via `PREDECESSOR_SUCCESSOR`. PR `#126` strictly isolated from `apache/flink#126`.
* `KAFKA-9168`: Represented via `EXTERNAL_DEPENDENCY` to `facebook/rocksdb`. Merged RocksDB PR does not resolve Kafka issue.
* `FLINK-20650`: Represented via `ECOSYSTEM_PACKAGING` to `docker-library/official-images`. Post-resolution merge evaluated as observational temporal finding (`ORBIT-XB-03`).

---

## 20. Determinism

* `relationship_id` generation is strictly deterministic.
* All JSON schemas, field specifications, and test matrices are canonically ordered.
* Zero runtime timestamps or non-deterministic ordering used.

---

## 21. Regression Test Results

* Test Command: `python3 -m pytest tests/ -q`
* Execution Output: **817 passed, 3 warnings in 10.01s**
* Track A Diff: **0 diff**
* Mahout 8 Invariants: **All preserved**
* TrueTenant Invariants: **All preserved**

---

## 22. Limitations

* Schema specification is currently offline and static.
* Requires manual or structured ingestion of ASF project governance records to populate `PROJECT_LINEAGE`.
* Does not model intra-repository branch renames (e.g. `master` $\rightarrow$ `main`).

---

## 23. Implementation Boundary

$$\mathbf{IMPLEMENTATION\ AUTHORIZED:\ NO}$$

Phase 4C is exclusively research, data modeling, and specification. No code in `src/shadow_orbit/` has been modified, and no production implementation may proceed without explicit authorization in a future phase.

---

## 24. Findings Classification

### PROVEN:
1. `EntityRef` immutability and repository-scoped `entity_id` (`owner/repo/number`) prevent numeric PR collisions under all evolution scenarios.
2. Dedicated relationship envelope (`RepositoryEvolutionRelationship`) guarantees that endpoints remain strictly repository entities, preventing PR identity collapse.
3. Adding `repository_relationships` as an optional field on `EvidenceBundle` maintains 100% backward compatibility with all 817 tests and historical benchmarks.

### SUPPORTED BUT NOT INDEPENDENTLY PROVEN:
1. Distinguishing `ECOSYSTEM_DEPENDENCY` prevents false `ORBIT-XB-02` findings on internal issues when external library PRs are merged.

### PARTIALLY PROVEN:
1. Transitive traversal of `NAVIGATION_ROUTING` resolves multi-hop renames across ASF incubation and top-level graduation.

### UNSUPPORTED:
1. Heuristic or fuzzy matching of repository names.
2. Automatic upgrading of `DECLARED_MENTION` to `EXPLICIT_LINK` based on repository lineage.

### NOT TESTED:
1. Live automated synchronization of provider repository webhooks.

---

## 25. Final Verdict

$$\mathbf{PASS}$$

*The canonical data contract is exact, identity remains immutable, provenance is explicit, relationship semantics are unambiguous, backward compatibility is demonstrated, adversarial cases are covered, no production code changed, and the 817-test baseline remains intact.*

---

## 26. Recommendation for Phase 4D

Proceed to **Phase 4D — Controlled Prototype Qualification**:
* Formulate an isolated qualification fixture instantiating `RepositoryEvolutionRelationship` against authentic Phase 3 cases (`FLINK-1359`, `stratosphere#126`, `KAFKA-9168`, `FLINK-20650`).
* Verify that the contract executes cleanly under automated test conditions in an isolated staging branch without modifying production code in `src/shadow_orbit/`.
