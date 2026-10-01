# Phase 4C — Reconnaissance: Foundation for Repository Evolution Schema Specification

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4C — Formal Repository Evolution Schema Specification  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Consolidation Commit (HEAD):** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`  
**Branch:** `remediation/pass3-controlled-hardening`  
**Status:** **RECONNAISSANCE VERIFIED**  

---

## 1. Executive Context and Governance

Phase 4C translates the architectural decision established in Phase 4B (**Option B: Minimal Evolution Metadata**) into an exact, unambiguous, machine-readable canonical schema specification. 

This phase operates under strict read-only governance:
- **No production code changes** in `src/shadow_orbit/`.
- **No modification** of existing canonical models or evaluator semantics.
- **No modification** of historical golden fixtures or test baselines (test baseline verified at 817 passed, 0 failed).

---

## 2. Phase 4B Verification and Established Ground Truth

Prior to specification design, all Phase 4B artifacts and decisions were independently audited:
1. **Artifact Verification:** All 7 Phase 4B artifacts in `qualification/wave3/phase4b_repository_identity/` were recomputed; all 7 cryptographic hashes match `phase4b_hashes.json` exactly (0 missing, 0 mismatches).
2. **ADR Decision Confirmation:** [`ADR-REPOSITORY-IDENTITY-EVOLUTION.md`](file:///home/tecblic/orbit/qualification/wave3/phase4b_repository_identity/ADR-REPOSITORY-IDENTITY-EVOLUTION.md) explicitly adopts **Option B (Minimal Evolution Metadata)** and records:
   $$\text{Implementation Authorized: NO}$$
3. **Core Invariant Established:** Repository evolution must **never** mutate, alias, or collapse `EntityRef`. Entities remain strictly repo-scoped (e.g. `owner/repo/number`).
4. **Linkage Neutrality Invariant:** Repository evolution evidence is semantically neutral with respect to linkage strength; it **never** automatically promotes a `DECLARED_MENTION` into an `EXPLICIT_LINK`.

---

## 3. Current ORBIT Canonical Identity Model

Reconnaissance of `src/shadow_orbit/evidence_types.py` details the immutable structures that must remain untouched:

### 3.1 The Canonical Identity Triad: `EntityRef`
```python
@dataclass(frozen=True, slots=True)
class SourceInstance:
    source_kind: SourceKind  # "jira" | "github" | "git"
    instance_id: str         # "github.com/apache" | "issues.apache.org"

@dataclass(frozen=True, slots=True)
class EntityRef:
    source_instance: SourceInstance
    entity_kind: EntityKind  # "work_item" | "code_change" | "review" | "commit" | "branch" | "repository"
    entity_id: str           # string scoped by entity type
```

### 3.2 Code Change Identity Scoping
For code changes (pull requests), `entity_id` is constructed by prefixing the repository namespace:
$$\text{entity\_id} = \texttt{"\{owner\}/\{repo\}/\{identifier\}"}$$

Examples in the active corpus:
- `EntityRef(github, "code_change", "apache/parquet-java/885")`
- `EntityRef(github, "code_change", "apache/kafka/11617")`
- `EntityRef(github, "code_change", "stratosphere/stratosphere/126")`
- `EntityRef(github, "code_change", "facebook/rocksdb/2283")`

### 3.3 Pull Request vs Repository Scoping
In current ORBIT code, pull requests belong to repositories via implicit or explicit structural relationships:
- In `evidence_types.py`, `RelationshipKind` contains `"belongs_to_repository"`.
- Pull requests are `entity_kind="code_change"`.
- Repositories are `entity_kind="repository"`, with `entity_id = "{owner}/{repo}"` (e.g. `"apache/flink"`).

---

## 4. Empirical Real-World Corpus Findings

Reconnaissance of the Phase 3 population (47,431 Jira issues, 1,444 PR URLs) and the 100-candidate frozen cohort establishes four empirical realities that the schema must represent:

1. **Predecessor Project Succession (57.0% in Flink):**  
   In Apache Flink, 448 of 786 Jira PR references point to `stratosphere/stratosphere`, the pre-ASF project codebase. Stratosphere had its own PR sequence (`#1` to `#891`).
2. **Upstream Project Graduation Redirects:**  
   `FLINK-1359` referenced `apache/incubator-flink#254`. GitHub routes this to `apache/flink#254` because the underlying numeric repository ID (`19853920`) is identical.
3. **External Dependencies and Packaging Ecosystems:**  
   Issues in Kafka and Flink reference external storage engines (`facebook/rocksdb#2283`), downstream packaging repos (`docker-library/official-images#9249`), and sister projects (`apache/arrow#4985`).
4. **Historical Purged Mirrors (404s):**  
   2% of historical links (`apache/incubator-parquet-mr#107` and `#53`) point to mirrors deleted during ASF reorganization.

---

## 5. Architectural Constraints for Phase 4C Specification

To guarantee zero regression and zero architectural leakage, the Phase 4C schema specification must satisfy:

1. **Repository-Level Endpoints:** The subject and object of repository evolution must be repository entities (`entity_kind="repository"`), NOT code changes (`entity_kind="code_change"`). Evolution of repositories does not imply equivalence of pull requests.
2. **Deterministic Identity:** Every evolution relationship must possess a deterministic, content-derived `relationship_id`.
3. **Provenance Grounding:** Every evolution relationship must link directly to source provenance (`ProvenanceRef`).
4. **Family-Discriminated Envelope:** The schema must distinguish between navigation/routing evolution, project lineage, repository topology, and ecosystem dependencies.
5. **Zero Mutation of Production Code:** The specification is authored as a formal research artifact without modifying existing modules in `src/shadow_orbit/`.
