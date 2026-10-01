# Phase 4B — Research & Architecture Report: Repository Identity & Evolution

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4B — Repository Identity & Evolution ADR  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Consolidation Commit (HEAD):** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`  
**Branch:** `remediation/pass3-controlled-hardening`  
**Status:** **PASS**  

---

## 1. Executive Summary

Phase 4B investigated the central architectural question:  
*How should Project ORBIT represent repository identity when a software project evolves across repository names, namespaces, mirrors, incubators, redirects, forks, migrations, predecessor/successor repositories, or external repositories?*

Operating strictly under research and architectural design governance without modifying ORBIT's semantic engine or production code:
1. **Empirical Grounding:** Examined 1,444 real-world pull request references across 47,431 Jira issues from Phase 1, 2, 3A, and 3B, cataloging authentic occurrences of upstream graduation redirects (`apache/incubator-flink` $\rightarrow$ `apache/flink`), predecessor codebases (`stratosphere/stratosphere` representing 57% of Flink's Jira PR links), external dependencies (`facebook/rocksdb`), downstream packaging (`docker-library/official-images`), and multi-component specifications (`apache/parquet-format`).
2. **Identity Model Invariants Upheld:** Confirmed that ORBIT's composite `EntityRef` triad (`source_instance`, `entity_kind`, `entity_id = "owner/repo/number"`) successfully prevents numeric PR collisions across distinct repositories (e.g. `stratosphere/stratosphere#126` vs `apache/flink#126`).
3. **Architectural Evaluation & Decision:** Evaluated three options (Option A: No New Abstraction; Option B: Minimal Evolution Metadata; Option C: Substantial Identity Model). Formally adopted **Option B (Minimal Evolution Metadata)** in [`ADR-REPOSITORY-IDENTITY-EVOLUTION.md`](file:///home/tecblic/orbit/qualification/wave3/phase4b_repository_identity/ADR-REPOSITORY-IDENTITY-EVOLUTION.md), preserving immutable repository-scoped entity identities while modeling verified repository evolution as directional metadata without auto-upgrading linkage.
4. **Implementation Firewall Enforced:** Confirmed that **zero bytes** of production code in `src/shadow_orbit/` were altered. Implementation is **not authorized** in Phase 4B.

---

## 2. Phase Scope

* **Boundary:** Forensic research, empirical characterization, adversarial safety analysis, and architectural design.
* **Prohibitions Honored:** No connector framework, no `RepositoryAliasService`, no `ProviderRegistry`, no fuzzy matching, no automatic linkage upgrade, no production code modification.
* **Data Sources Analyzed:**
  - Phase 3A 100-candidate frozen cohort (`phase3a_frozen_cohort.json`)
  - Phase 3A 288 raw GitHub artifacts (`qualification/wave3/phase3a_acquisition/raw/`)
  - Phase 3B reconciliation and canonical projections (`phase3b_reconciliation.json`, `phase3b_canonical_alignments.json`)
  - Full Phase 2 population inventory (47,431 Jira issues in MongoDB `JiraReposAnon.Apache`)

---

## 3. Governing Baseline

* **Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`develop`)
* **Consolidation HEAD:** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab` (`remediation/pass3-controlled-hardening`)
* **Working Tree State:** Completely clean.
* **Regression Record:** 817 passed, 0 failed, 3 warnings; Mahout (all 8 invariants preserved); TrueTenant (all invariants preserved); Track A zero diff.

---

## 4. Research Question

> *How should ORBIT represent repository identity when a software project evolves across repository names, namespaces, mirrors, incubators, redirects, forks, migrations, predecessor/successor repositories, or external repositories?*

### The Forensic Answer:
ORBIT must represent repository identity **strictly scoped by provider instance and repository namespace** (`EntityRef = (SourceInstance, "code_change", "owner/repo/number")`), and **must never collapse or alias distinct repositories into a single entity**. 

Repository evolution (e.g. predecessor projects, graduation renames, external dependencies) must be represented as **separate, typed, directional metadata relationships**, preserving the authentic source-grounded identity of every historical observation.

---

## 5. Existing Identity Model

In `src/shadow_orbit/evidence_types.py`:
* **`SourceInstance`:** Encapsulates provider deployment scope (`github.com/apache`).
* **`EntityRef`:** Uniquely identifies an entity via `(source_instance, entity_kind, entity_id)`.
* **Pull Request Scoping:** `entity_id = f"{owner}/{repo}/{number}"`.
* **Findings:** The current model is strictly collision-proof across repositories. Its limitation is not insecurity, but *evolution blindness* (treating related predecessor projects as completely disconnected third parties).

---

## 6. Phase 3 Evidence

Empirical findings from the 100-candidate cohort and full population:
1. **Predecessors Dominate Early History:** In Flink, 57% of all Jira PR links point to `stratosphere/stratosphere` (448 links), pre-dating ASF donation.
2. **Upstream Graduation Redirects Exist:** `apache/incubator-flink#254` redirected cleanly to `apache/flink#254` with GitHub API returning `base.repo.full_name = "apache/flink"`.
3. **External Dependencies are Frequently Referenced:** 5% of candidate links point to external libraries (`facebook/rocksdb`), downstream packaging (`docker-library/official-images`), or vendor forks (`salsify/avro-patches`).
4. **Purged Historical Mirrors Return 404:** 2% of references point to historical mirrors (`apache/incubator-parquet-mr`) that were purged during ASF consolidation.

---

## 7. Repository Identity Cases

Twenty-two structured cases were compiled and persisted in [`repository_identity_cases.json`](file:///home/tecblic/orbit/qualification/wave3/phase4b_repository_identity/repository_identity_cases.json) and [`repository_identity_cases.csv`](file:///home/tecblic/orbit/qualification/wave3/phase4b_repository_identity/repository_identity_cases.csv):
* **Empirical Cases (A–E):**
  - `CASE-A-01`: Graduation redirect (`FLINK-1359` $\rightarrow$ `incubator-flink#254` $\rightarrow$ `flink#254`)
  - `CASE-B-01`: Numeric PR collision (`stratosphere/stratosphere#126` vs `apache/flink#126`)
  - `CASE-C-01` to `C-05`: External dependencies, packaging, sister projects, companion specs, vendor forks
  - `CASE-D-01` & `D-02`: Many-to-one Jira $\rightarrow$ PR linkage (`KAFKA-12770/12771` to `#10656`; `FLINK-126/236` to Stratosphere `#126`)
  - `CASE-E-01`: One-to-many Jira $\rightarrow$ PR linkage (`FLINK-24409` to PRs `#17401`, `#17773`, `#17799`)
* **Adversarial Cases:** `ADV-01` through `ADV-12` (numeric collision, namespace collision, fork PR overlap, mirror parity, purged repos, key leaks).

---

## 8. Evolution Taxonomy

ORBIT defines a closed taxonomy of 10 repository relationships:
1. `RENAME` (same VCS repo ID, new name)
2. `NAMESPACE_MOVE` (repo transferred across organizations)
3. `REDIRECT` (HTTP/API routing rule)
4. `PREDECESSOR_SUCCESSOR` (historical project codebase superseded)
5. `FORK` (derivative codebase, `is_fork=True`)
6. `MIRROR` (read-only replica, identical commit graph)
7. `VENDOR_MIRROR` (downstream distribution mirror)
8. `EXTERNAL_DEPENDENCY` (consumed external library)
9. `ECOSYSTEM_PACKAGING` (downstream packaging/container repo)
10. `COMPANION_SPECIFICATION` (sister specification repo)

---

## 9. Evidence Matrix

Detailed in [`phase4b_evidence_matrix.md`](file:///home/tecblic/orbit/qualification/wave3/phase4b_repository_identity/phase4b_evidence_matrix.md):
* Evaluates definitions, evidentiary proof, symmetry, transitivity, and semantic impact.
* Confirms that no repository relationship changes the underlying `EntityRef` or automatically promotes linkage strength.

---

## 10. Semantic Impact Analysis

* **`ORBIT-XB-01` (Unlinked PR with Mentions):** Must distinguish external dependency PRs from project implementation PRs to avoid false positives.
* **`ORBIT-XB-02` (Lifecycle Tracking Lag):** Verified on `KAFKA-12770` (PR `#10656` merged while issue was in `Patch Available`). However, merging an `EXTERNAL_DEPENDENCY` PR does not imply the Jira issue is complete.
* **`ORBIT-XB-03` (Temporal Divergence):** Verified on `FLINK-13730` (+92d) and `FLINK-20650` (+36d). Downstream packaging PRs naturally merge post-resolution.

---

## 11. Fork, Mirror, and Dependency Boundaries

* **Forks:** Retain `is_fork=True` in `CodeChangeState.extra_properties`. Distinct `EntityRef`. Shared commit ancestry does not make a fork a successor.
* **Mirrors:** Distinct `SourceInstance` boundaries (`gitbox.apache.org` vs `github.com/apache`). Commits match by SHA; PRs exist only on GitHub.
* **Dependencies:** External repositories (`facebook/rocksdb`) remain isolated. PR merge in a dependency does not constitute issue resolution.

---

## 12. Adversarial Findings

Detailed in [`phase4b_adversarial_tests.md`](file:///home/tecblic/orbit/qualification/wave3/phase4b_repository_identity/phase4b_adversarial_tests.md):
* Numeric PR collision between `stratosphere/stratosphere#126` and `apache/flink#126` is 100% prevented by `owner/repo/number` scoping.
* 404 responses for purged historical mirrors (`apache/incubator-parquet-mr#107`) are safely handled as `NOT_FOUND` / `INSUFFICIENT_EVIDENCE` without fabrication.
* Fuzzy matching and heuristic clustering are proved dangerous and rejected.

---

## 13. Backward Compatibility

* Existing Track A evaluation is 100% unaffected.
* Existing Mahout qualification (412 items, 12 STALLED_WORK, 56 incomplete) is 100% preserved.
* Existing TrueTenant hold-out (112 items, 1 STALLED_WORK, 33 unknown) is 100% preserved.
* Apache Phase 1A/1B/1C benchmarks remain unchanged.

---

## 14. Alternatives Considered

* **Option A (No New Abstraction):** Safe, but leaves 57% of Flink Jira references disconnected as ad-hoc strings.
* **Option B (Minimal Evolution Metadata):** Retains immutable `EntityRef` while modeling evolution as typed metadata. **ADOPTED.**
* **Option C (Substantial Identity Model / Alias Registry):** Collapses repositories into single IDs. **REJECTED** due to collision risk and non-goals.

---

## 15. Decision

**Adopt OPTION B (Minimal Evolution Metadata).**  
Detailed in [`ADR-REPOSITORY-IDENTITY-EVOLUTION.md`](file:///home/tecblic/orbit/qualification/wave3/phase4b_repository_identity/ADR-REPOSITORY-IDENTITY-EVOLUTION.md).

---

## 16. Proven / Supported / Partial / Unsupported / Not Tested

### PROVEN:
1. ORBIT's repository-scoped `EntityRef` (`owner/repo/number`) completely prevents numeric identifier collisions across independent, predecessor, and fork repositories.
2. Real-world project history contains multi-repository evolution (57% predecessor links in Flink; graduation redirects; companion specification repos).
3. Cardinality handling cleanly represents many-to-one and one-to-many relationships without entity collapse.

### SUPPORTED BUT NOT INDEPENDENTLY PROVEN:
1. Jira-embedded PR URLs to predecessor repositories (`stratosphere/stratosphere`) reflect authentic historical developer intent to track implementation.

### PARTIALLY PROVEN:
1. HTTP redirect continuity reliably preserves PR identity across ASF incubator graduation renames when GitHub maintainers keep the underlying repository ID active.

### UNSUPPORTED:
1. Heuristic or fuzzy matching of repository names.
2. Inferring project succession from contributor overlap or naming similarity.

### NOT TESTED:
1. Bidirectional live synchronization and automated repository migration tooling.

---

## 17. Risks and Limitations

* **Historical Repository Purging:** When providers delete historical mirrors (e.g. `incubator-parquet-mr`), HTTP requests return 404, creating permanent offline evidence gaps.
* **Static Snapshot Boundary:** MSR 2022 dataset captures Jira descriptions at a fixed point in time; subsequent GitHub repo renames may require live API dereferencing.

---

## 18. Implementation Authorization

$$\mathbf{IMPLEMENTATION\ IS\ NOT\ AUTHORIZED\ IN\ PHASE\ 4B.}$$

Phase 4B is exclusively research and architectural design. No modifications to `src/shadow_orbit/` are permitted.

---

## 19. Recommended Next Phase

1. **Phase 4C (Formal Repository Evolution Schema Specification):** Formulate the precise data contract for `EvidenceRelationship` evolution types in a controlled staging branch.
2. **Phase 4D (Controlled Prototype Qualification):** Test the Option B metadata model against the Flink Stratosphere cohort to verify that evolution links can be dereferenced without modifying Track B evaluator rules.

---

## 20. Artifact Integrity

All Phase 4B artifacts were generated deterministically and hashed with SHA-256 in [`phase4b_hashes.json`](file:///home/tecblic/orbit/qualification/wave3/phase4b_repository_identity/phase4b_hashes.json).

| Artifact | SHA-256 Digest |
| :--- | :--- |
| `phase4b_reconnaissance.md` | `8c19dc2d85c9e82bd21755d5416f708ab878d7419204eecef486969d0623da75` |
| `repository_identity_cases.json` | `f1833289f25a25d5f8652a40f448b7eb406de5266676c639a392e8eb28c424b4` |
| `repository_identity_cases.csv` | `fd732ea8295876be24042ea22b5f25d313ecb38793d446b54abaaac5c369b7db` |
| `phase4b_evidence_matrix.md` | `797885ab6aac0009c96e02aa88212282f6758dbe5c0bb4591bf1e20d9d4e297d` |
| `phase4b_adversarial_tests.md` | `e88fdc6f53bce68a783f50fc615401abc4cf2fc90e3d1fb2e1bc4b9353b97b59` |
| `ADR-REPOSITORY-IDENTITY-EVOLUTION.md` | `faae72c44352369afd91ffef3408579264c1c0b22126a7ecd0a3165817762f50` |

---

*Report complete. Phase 4B research and architectural design concluded.*
