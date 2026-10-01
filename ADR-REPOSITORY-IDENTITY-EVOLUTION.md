# ADR-REPOSITORY-IDENTITY-EVOLUTION: Repository Identity and Project Evolution Architecture

* **Status:** **PROPOSED / RESEARCH COMPLETE — IMPLEMENTATION NOT AUTHORIZED IN PHASE 4B**
* **Date:** 2026-09-30
* **Author:** Project ORBIT Forensic Architecture Team
* **Deciders:** Founding Software Engineer & Lead Architect
* **Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)
* **Consolidation HEAD:** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`
* **Related ADRs:** ADR-001 (Provenance & Determinism), ADR-005 (Cross-System Alignments), ADR-006 (Track B Evidence Evaluation)

---

## 1. Context

Across Waves 1–3 of Project ORBIT, cross-system qualification evaluated Jira work items alongside GitHub code changes. While initial experiments operated on hand-selected, single-repository pairs (e.g. `apache/kafka`), population-derived surveys in Wave 3 (surveying 47,431 Jira issues across 5 Apache ecosystems) revealed that real software engineering projects do not inhabit a static, single-repository universe:

1. **Predecessor Projects:** In Apache Flink, **57.0% (448 / 786)** of PR references in Jira descriptions point to `stratosphere/stratosphere` (the pre-Apache predecessor project), while 33.2% point to `apache/flink`.
2. **Project Incubation & Renaming:** Apache projects undergo incubation graduation (`apache/incubator-flink` $\rightarrow$ `apache/flink`, `apache/incubator-parquet-mr` $\rightarrow$ `apache/parquet-mr`). In some cases, GitHub automatically routes old URLs via HTTP redirects; in other cases, historical incubation mirrors were purged (returning HTTP 404).
3. **Multi-Repository Modularization:** Apache Parquet spans distinct repositories for specifications (`parquet-format`), Java implementations (`parquet-mr`), C++ implementations (`parquet-cpp`), and sister columnar projects (`arrow`).
4. **External Dependencies:** Issues in Kafka and Flink frequently reference PRs in external dependencies (`facebook/rocksdb`), downstream packaging repositories (`docker-library/official-images`), and vendor forks (`salsify/avro-patches`).

---

## 2. Problem Statement

How should Project ORBIT represent repository identity and project evolution without:
1. Creating numeric pull request identifier collisions across repositories (e.g. confusing `stratosphere/stratosphere#126` with `apache/flink#126`);
2. Manufacturing false equivalence between independent codebases (e.g. treating an external RocksDB PR as an Apache Kafka codebase PR);
3. Silently upgrading informal textual mentions (`DECLARED_MENTION`) into native integration links (`EXPLICIT_LINK`);
4. Introducing bloated, speculative runtime abstractions (`RepositoryAliasService`, `ProviderRegistry`, fuzzy matching engines) that violate ORBIT's core non-goals?

---

## 3. Existing Model Analysis

In ORBIT's current production semantic engine (`src/shadow_orbit/evidence_types.py`):
- Entity identity is established by the composite triad:
  $$\text{EntityRef} = (\text{source\_instance}, \text{entity\_kind}, \text{entity\_id})$$
- For GitHub pull requests, `entity_id` is scoped by repository path:
  $$\text{entity\_id} = \texttt{"\{owner\}/\{repo\}/\{number\}"}$$
- Two observations are considered identical if and only if their `EntityRef` instances match exactly.

### Observed Strengths of the Existing Model:
- **Collision Resistance:** Completely prevents numeric PR collisions between different repositories. PR `#885` in `apache/parquet-java` and PR `#885` in `apache/kafka` have different `EntityRef` values and remain strictly isolated.
- **Provider Scoping:** Distinguishes different instances via `SourceInstance`.

### Observed Gaps of the Existing Model:
- **Evolution Blindness:** The model treats `stratosphere/stratosphere` as an unrelated third-party repository, offering no formal mechanism to record that it is the historical predecessor of `apache/flink`.
- **Dependency Conflation Risk:** The model provides no built-in distinction between an implementation PR in the project's own repository and a PR in an external dependency (`facebook/rocksdb`).

---

## 4. Observed Evidence Summary

Empirical data from Wave 3 Phase 1A, 2, 3A, and 3B establishes:

| Empirical Case | Real-World Observation | Verified Engine Behavior |
| :--- | :--- | :--- |
| **Case A (Redirect)** | `apache/incubator-flink#254` redirects to `apache/flink#254`. | GitHub API resolves canonical target repo; identity continuity preserved; 0 errors. |
| **Case B (Numeric Collision)** | `stratosphere/stratosphere#126` vs `apache/flink#126`. | Existing `owner/repo/number` scoping successfully isolates distinct PRs. |
| **Case C (External Dependencies)** | `KAFKA-9168` $\rightarrow$ `facebook/rocksdb#2283`. | Tracked as `DECLARED_MENTION`; does NOT resolve Jira issue. |
| **Case D (Many-to-One)** | `KAFKA-12770` & `12771` $\rightarrow$ `apache/kafka#10656`. | 1 PR observation, 2 alignments; Track B flags lag on `12770`. |
| **Case E (One-to-Many)** | `FLINK-24409` $\rightarrow$ PRs `#17401`, `#17773`, `#17799`. | 1 Jira observation, 3 PR observations, 3 distinct alignments. |

---

## 5. Architectural Principles for Repository Identity

1. **Deterministic Facts First:** Repository identity must be derived strictly from source facts, never from heuristic clustering, naming similarity, or contributor overlap.
2. **Repository-Scoped EntityRef Is Inviolable:** `EntityRef` for a code change entity **must always** retain its full repository namespace (`owner/repo/number`). An evolution relationship must NEVER mutate, alias, or collapse an `EntityRef`.
3. **Linkage Neutrality:** Establishing that Repository B is a successor or redirect of Repository A provides evidence of code evolution. It **NEVER** automatically promotes a `DECLARED_MENTION` into an `EXPLICIT_LINK`.
4. **No Synthetic Repair of Historical 404s:** When historical references point to purged mirrors (`apache/incubator-parquet-mr#107`), ORBIT must report `NOT_FOUND` and `INSUFFICIENT_EVIDENCE`.

---

## 6. Repository Evolution Taxonomy

ORBIT defines a closed taxonomy of 10 repository relationships:

1. **`RENAME`:** Same underlying VCS repository entity renamed under same owner. Asymmetric, transitive. Does not change `EntityRef`.
2. **`NAMESPACE_MOVE`:** Repository transferred across organizations with identical underlying repo ID. Asymmetric, transitive.
3. **`REDIRECT`:** Transport-level HTTP/VCS routing rule. Asymmetric, transitive. Navigational provenance only.
4. **`PREDECESSOR_SUCCESSOR`:** Historical project codebase superseded by successor codebase (`stratosphere` $\rightarrow$ `flink`). Asymmetric, transitive.
5. **`FORK`:** Branch of codebase in separate namespace. Asymmetric, non-transitive. `is_fork=True`.
6. **`MIRROR`:** Read-only replica with cryptographically identical commit graphs. Symmetric, transitive. Distinct `SourceInstance`.
7. **`VENDOR_MIRROR`:** Downstream vendor distribution (`linkedin/kafka`). Asymmetric, non-transitive. Isolated `EntityRef`.
8. **`EXTERNAL_DEPENDENCY`:** Consumed library or engine (`facebook/rocksdb`). Asymmetric, non-transitive.
9. **`ECOSYSTEM_PACKAGING`:** Downstream distribution/packaging repo (`docker-library/official-images`). Asymmetric, non-transitive.
10. **`COMPANION_SPECIFICATION`:** Sister format or specification repo (`apache/parquet-format`). Asymmetric, non-transitive.

---

## 7. Alternatives Considered

### Option A: No New Abstraction
* **Description:** Retain existing `EntityRef` scoping only. Treat all repository evolution strictly as external provenance/navigation notes.
* **Evaluation:** Option A is safe and prevents collisions. However, it leaves 57% of Flink Jira issues completely disconnected from project history in reporting and forces ad-hoc workarounds in evaluation runners.

### Option B: Minimal Evolution Metadata (RECOMMENDED)
* **Description:** Retain immutable `EntityRef` (`owner/repo/number`) as primary identity. Model verified evolution as an explicit, typed, directional metadata relationship (`EvidenceRelationship` or metadata annotation) without modifying core evaluator semantics or auto-upgrading linkage.
* **Evaluation:** Fully preserves backward compatibility, prevents collisions, accurately models predecessor projects and external dependencies, and requires zero modifications to existing canonical state models.

### Option C: Substantial Identity Model (Universal Alias / Clustering Engine)
* **Description:** Implement a global `RepositoryRegistry` or `RepositoryAliasService` that maps multiple repository strings to a single canonical project ID, collapsing historical repositories into modern names.
* **Evaluation:** **REJECTED.** Option C would cause catastrophic identifier collisions (e.g. collapsing `stratosphere/stratosphere#126` into `apache/flink#126`), violates ORBIT's core non-goals, and manufactures false identity equivalence from historical evolution.

---

## 8. Decision

We adopt **OPTION B: MINIMAL EVOLUTION METADATA** as Project ORBIT's target architecture for repository evolution.

### Key Decisions:
1. **Primary Entity Identity Remains Unaltered:**  
   `EntityRef` for code changes will strictly continue to use `"{owner}/{repo}/{identifier}"`.
2. **Evolution Is Modeled as Explicit Relationship Evidence:**  
   Evolutionary links (`PREDECESSOR_SUCCESSOR`, `REDIRECT`, `EXTERNAL_DEPENDENCY`) will be represented as secondary, directional `EvidenceRelationship` records between repository entities, or as structured annotations in observation metadata.
3. **No Automatic Semantic Linkage Upgrade:**  
   Repository evolution metadata will **never** automatically upgrade a `DECLARED_MENTION` to an `EXPLICIT_LINK`.
4. **Implementation Authorization:**  
   **IMPLEMENTATION IS NOT AUTHORIZED IN PHASE 4B.** Phase 4B is strictly a research and architectural specification phase. No code in `src/shadow_orbit/` may be altered without a subsequent, formally authorized implementation wave.

---

## 9. Consequences

### Positive Consequences:
- **Zero Collision Risk:** Numeric PR numbers in historical or sister repositories remain strictly partitioned.
- **Zero Production Disruption:** 817 tests, Track A, Mahout, and TrueTenant invariants remain 100% stable.
- **Honest Evidence Representation:** Predecessors, external dependencies, and redirects are explicitly documented without loss of source provenance.

### Negative Consequences / Trade-offs:
- Evaluator rules must explicitly account for relationship types (e.g. `ORBIT-XB-02` must recognize that merging an `EXTERNAL_DEPENDENCY` PR does not resolve an internal issue).

---

## 10. Explicit Non-Goals

The following remain **strictly prohibited**:
- No `RepositoryAliasService` or `RepositoryRegistry` class.
- No `ProviderRegistry` or `PluginManager`.
- No fuzzy string matching or lexical repository clustering.
- No automatic URL rewriting in raw evidence fixtures.
- No collapsing of forks or external dependencies into primary project codebases.

---

## 11. Future Qualification Requirements

Prior to any future implementation of Option B:
1. Formulate exact schema additions for repository-level observations in `src/shadow_orbit/evidence_types.py`.
2. Design test suites validating that `PREDECESSOR_SUCCESSOR` relationships preserve PR number isolation.
3. Ensure that all 817 baseline regression tests remain byte-identical.
