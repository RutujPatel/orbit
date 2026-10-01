# Phase 4C — Semantic Contract & Invariant Specification

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4C — Formal Repository Evolution Schema Specification  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Status:** **SEMANTIC CONTRACT COMPLETE**  

---

## 1. Purpose

This document defines the formal semantic invariants governing `RepositoryEvolutionRelationship`. Every validator, adapter, and future evaluator rule must satisfy these non-negotiable invariants.

---

## 2. Invariant Specifications

---

### 2.1 Identity Invariants

* **INV-ID-01 (EntityRef Immutability):**  
  A repository evolution relationship **MUST NEVER** mutate, rewrite, or alias the `EntityRef` of any code change, work item, review, commit, or repository.
  $$\forall e \in \text{Observations},\quad \text{EntityRef}(e) = \text{SourceGroundTruth}(e)$$
* **INV-ID-02 (Strict Repository-Kind Endpoints):**  
  The subject and object of `RepositoryEvolutionRelationship` **MUST STRICTLY** have `entity_kind == "repository"`.
  $$\text{source\_repository.entity\_kind} = \texttt{"repository"} \quad \land \quad \text{target\_repository.entity\_kind} = \texttt{"repository"}$$
  Passing a code change (`"code_change"`) or work item (`"work_item"`) as an endpoint is a fatal schema validation error.
* **INV-ID-03 (PR Number Isolation):**  
  The presence of a `PREDECESSOR_SUCCESSOR` relationship between Repository $A$ and Repository $B$ **DOES NOT** imply that $A/\#N$ and $B/\#N$ are the same entity.
  $$A \xrightarrow{\text{PREDECESSOR}} B \centernot\implies \text{EntityRef}(A/N) = \text{EntityRef}(B/N)$$
  `stratosphere/stratosphere#126` and `apache/flink#126` remain strictly disjoint entities.
* **INV-ID-04 (Deterministic Identifier):**  
  The `relationship_id` must be computed strictly via deterministic hashing over invariant components:
  $$\text{relationship\_id} = \text{SHA-256}\left(\text{instance\_id} + \texttt{"\|"} + \text{type} + \texttt{"\|"} + \text{src\_id} + \texttt{"\|"} + \text{tgt\_id}\right)$$
  Two relationship records with identical inputs produce identical IDs.

---

### 2.2 Evidence Invariants

* **INV-EV-01 (Mandatory Provenance):**  
  Every `RepositoryEvolutionRelationship` must carry at least one cryptographically verified `ProvenanceRef`. A relationship without provenance is invalid.
  $$|\text{provenance\_refs}| \ge 1$$
* **INV-EV-02 (No Plain URL Lineage):**  
  A plain URL embedded in a Jira description is evidence of a `DECLARED_MENTION` only. It **CANNOT** establish `PREDECESSOR_SUCCESSOR` or `RENAME` relationships on its own without corroborating VCS/governance evidence.
* **INV-EV-03 (Honest Gaps / No Synthetic Repair):**  
  When a historical repository URL returns HTTP 404 (e.g. purged mirror `apache/incubator-parquet-mr#107`), the system must record `NOT_FOUND` and `INSUFFICIENT_EVIDENCE`. It must never synthesize a successor relationship or guess replacement PRs.

---

### 2.3 Linkage Invariants

* **INV-LK-01 (Linkage Neutrality):**  
  A repository evolution relationship **MUST NEVER** automatically upgrade a `DECLARED_MENTION` into an `EXPLICIT_LINK`.
  $$\text{RepositoryEvolution}(A, B) \centernot\implies \text{UpgradeLinkage}(\text{Jira}, A/\#N)$$
  Linkage strength depends strictly on native integration evidence (e.g. Jira remote issue links), not repository evolution.
* **INV-LK-02 (Separation of Repository and Cross-System Linkage):**  
  Repository evolution expresses relationships between codebases. It is distinct from `CrossSystemStateAlignment`, which expresses relationships between tracked work items and code changes.

---

### 2.4 State and Temporal Invariants

* **INV-ST-01 (No State Transfer Across Repositories):**  
  Merging a PR in a target repository ($B$) **DOES NOT** automatically mark a Jira issue associated with repository $A$ as completed.
  $$\text{Merged}(B/\#N) \centernot\implies \text{Resolved}(\text{JiraIssue})$$
* **INV-ST-02 (External Dependency Isolation):**  
  Merging a PR in an `EXTERNAL_DEPENDENCY` repository (`facebook/rocksdb#2283`) is an external library release event; it does not indicate that the consuming project's issue (`KAFKA-9168`) is completed.
* **INV-TM-01 (No Causality from Proximity):**  
  Temporal proximity between a repository rename and an issue resolution does not imply causal connection.
* **INV-TM-02 (Temporal Coherence Separation):**  
  Temporal comparisons (`COHERENT`, `INVERTED`, `INDETERMINATE`) evaluate only observed timestamps. When an ecosystem packaging PR merges post-resolution (e.g. `FLINK-20650` $\rightarrow$ `docker-library/official-images#9249`), the evaluator records an observational `INVERTED` finding without assuming data corruption.

---

### 2.5 Graph and Transitivity Invariants

* **INV-GR-01 (Strict Lineage Acyclicity):**  
  The `PROJECT_LINEAGE` graph (`PREDECESSOR_SUCCESSOR`) must be a Directed Acyclic Graph (DAG). Cycles ($A \rightarrow B \rightarrow A$) are fatal validation errors.
* **INV-GR-02 (Routing Acyclicity):**  
  The `NAVIGATION_ROUTING` graph (`REDIRECT`, `RENAME`) must be strictly acyclic. Self-referential redirects ($A \rightarrow A$) or circular redirects ($A \rightarrow B \rightarrow A$) are illegal.
* **INV-GR-03 (Non-Transitivity of Dependencies and Forks):**  
  Relationships in `REPOSITORY_TOPOLOGY` (`FORK`, `MIRROR`) and `ECOSYSTEM_DEPENDENCY` are strictly non-transitive for semantic evaluation.
  $$A \xrightarrow{\text{DEPENDS}} B \quad \land \quad B \xrightarrow{\text{DEPENDS}} C \centernot\implies A \xrightarrow{\text{DEPENDS}} C$$

---

## 3. The Semantic Firewall

The semantic firewall is an explicit, immutable contract ensuring that repository evolution metadata remains an informational and qualifying layer, never a destructive one:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THE SEMANTIC FIREWALL                           │
├────────────────────────────────────────────────────────────────────────┤
│  [PROHIBITED]                                                          │
│  ✖  Mutate EntityRef for any code change or work item                  │
│  ✖  Collapse distinct PR numbers across repositories                   │
│  ✖  Upgrade DECLARED_MENTION to EXPLICIT_LINK                          │
│  ✖  Transfer Jira completion or GitHub merge status across codebases    │
│  ✖  Infer project lineage from contributor overlap or naming           │
│  ✖  Treat external dependency PR merges as project issue resolution    │
│                                                                        │
│  [PERMITTED / AUTHORIZED FOR FUTURE USE]                               │
│  ✔  Provide verified navigation routing from historical URLs           │
│  ✔  Document historical predecessor lineage in provenance logs         │
│  ✔  Distinguish external dependency PRs in evaluation findings         │
│  ✔  Explain post-resolution merges for downstream packaging PRs        │
└────────────────────────────────────────────────────────────────────────┘
```
