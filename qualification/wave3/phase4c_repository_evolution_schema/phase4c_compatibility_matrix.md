# Phase 4C — Backward Compatibility Matrix & Architectural Impact

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4C — Formal Repository Evolution Schema Specification  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Status:** **COMPATIBILITY MATRIX COMPLETE**  

---

## 1. Executive Summary

This matrix demonstrates that the Phase 4C `RepositoryEvolutionRelationship` schema specification imposes **zero breaking changes, zero model corruption, and zero regression risk** on existing ORBIT canonical structures, serialized artifacts, historical golden files, or evaluation baselines.

---

## 2. Canonical Structure Interaction Matrix

| Canonical Structure | Current Role in ORBIT | Phase 4C Interaction | Mutation Impact | Backward Compatibility Status |
| :--- | :--- | :--- | :--- | :--- |
| **`EntityRef`** | Immutable cross-system entity coordinate (`source_instance`, `entity_kind`, `entity_id`). | Endpoints of evolution relationships use `entity_kind="repository"` with `entity_id="{owner}/{repo}"`. Code change `EntityRef` remains strictly `"{owner}/{repo}/{number}"`. | **ZERO MUTATION** (0 bytes changed in class definition). | **100% COMPATIBLE** (Existing equality and hashing preserved). |
| **`SourceInstance`** | Provider deployment boundary authority (`source_kind`, `instance_id`). | Reused directly as the deployment authority for repository entities (e.g. `SourceInstance("github", "github.com/apache")`). | **ZERO MUTATION** | **100% COMPATIBLE** |
| **`EvidenceBundle`** | Top-level container for observations, relationships, alignments, and quality issues. | Future implementation will add an optional field: `repository_relationships: tuple[RepositoryEvolutionRelationship, ...] = ()`. | **ZERO MUTATION** in Phase 4C. Future field is optional with empty tuple default. | **100% COMPATIBLE** (Historical bundles without this field deserialize cleanly). |
| **`EvidenceRelationship`**| Fine-grained entity association (`belongs_to_repository`, `mentions`, `review_of`). | Retains its fine-grained structural/lexical role. Macro repository evolution is isolated in `RepositoryEvolutionRelationship` to prevent query pollution. | **ZERO MUTATION** | **100% COMPATIBLE** |
| **`CrossSystemStateAlignment`** | Pairwise work-item to code-change alignment with state and temporal comparison. | Evaluator rules continue to operate strictly between work items and code changes. Evolution metadata serves only as informational qualifier. | **ZERO MUTATION** | **100% COMPATIBLE** (Alignment taxonomy unchanged). |
| **`WorkItemState`** | Canonical provider-neutral work item state. | Unchanged. Contains zero repository references. | **ZERO MUTATION** | **100% COMPATIBLE** |
| **`CodeChangeState`** | Canonical provider-neutral code change state. | Unchanged. Continues to record `extra_properties["repo"]` and `extra_properties["is_fork"]`. | **ZERO MUTATION** | **100% COMPATIBLE** |
| **Track B Evaluator** | Rule engine evaluating `ORBIT-XB-01`, `XB-02`, `XB-03`. | Evaluates existing bundle collections. Does not consume repository evolution unless a future explicit rule is authorized. | **ZERO MUTATION** | **100% COMPATIBLE** |
| **`ProvenanceRef`** | Cryptographic trail to raw source evidence. | Reused directly without alteration by `RepositoryEvolutionRelationship`. | **ZERO MUTATION** | **100% COMPATIBLE** (Dereferencing engine fully re-usable). |
| **`QualityIssue`** | Structured data quality diagnostic. | Validators will emit existing `QualityCode` values (`"invalid"`, `"unresolved"`) for malformed evolution records. | **ZERO MUTATION** | **100% COMPATIBLE** |

---

## 3. Historical Artifact & Benchmark Preservation

| Artifact Corpus | Current Governing Role | Impact of Phase 4C Specification |
| :--- | :--- | :--- |
| **Track A Acceptance Tests** | Enterprise clean/messy Jira evaluation suites (`test_clean_week_1.py`, etc.). | **ZERO DIFF.** Track A does not interact with GitHub or repository evolution. |
| **Mahout Qualification Fixture** | 412 selected/accepted issues; 12 `STALLED_WORK`; 56 incomplete; 370 missing due dates. | **ZERO DIFF.** All 8 invariants verified intact. |
| **TrueTenant Qualification Fixture** | 112 work items; 1 `STALLED_WORK`; 33 indeterminate; deterministic. | **ZERO DIFF.** All invariants verified intact. |
| **Phase 1A/1B/1C Apache Fixtures** | Hand-selected Apache Kafka, Parquet, Avro, Flink benchmark fixtures. | **ZERO DIFF.** Hash manifests remain completely untouched. |
| **Phase 3A Raw Fixtures (288 files)** | Population-derived raw PR, commit, and review payloads. | **ZERO DIFF.** Hashes verified 100% matching `raw_sha256.json`. |
| **Phase 3B Canonical Output Artifacts** | Reconciliation, canonical observations, alignments, metrics, determinism. | **ZERO DIFF.** All 14 artifact digests verified intact. |
| **Full Regression Suite** | 817 passing pytest tests. | **817 passed, 0 failed, 3 warnings.** |

---

## 4. Migration and Implementation Requirements

When implementation is formally authorized in a future phase (e.g. Phase 4D or Pass 6):

1. **Schema Extension Strategy:**
   - Define `RepositoryEvolutionRelationship` dataclass in `src/shadow_orbit/evidence_types.py`.
   - Add optional field with default empty tuple to `EvidenceBundle`:
     ```python
     repository_relationships: tuple[RepositoryEvolutionRelationship, ...] = ()
     ```
2. **Serialization Strategy:**
   - In `serialize_evidence_bundle()`, serialize `repository_relationships` as a list of dicts.
   - If `repository_relationships` is empty (historical bundles), omit the key or serialize as `[]`.
3. **Database & Storage Strategy:**
   - Zero database migration required for historical records.
   - New relational table `repository_evolution_relationships` if persistence is introduced.
4. **Validation Strategy:**
   - Add a dedicated validation pass in `validate_evidence_bundle` checking `INV-ID-02` (repository kind), `INV-GR-01` (DAG acyclicity), and `INV-EV-01` (provenance).
