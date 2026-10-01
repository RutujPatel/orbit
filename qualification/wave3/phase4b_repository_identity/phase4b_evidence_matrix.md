# Phase 4B — Repository Evolution Evidence Matrix

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4B — Repository Identity & Evolution ADR  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Status:** **RESEARCH & EVIDENCE TAXONOMY MATRIX**  

---

## 1. Overview & Semantic Principles

This matrix establishes the evidentiary criteria, symmetry, transitivity, and semantic effects for every repository relationship observed in the Project ORBIT corpus or required for evaluation.

### Core Non-Negotiable Invariants:
1. **Repository Identity Invariance:** A repository-evolution relationship **NEVER** mutates or collapses the underlying `EntityRef`. Entities remain strictly repo-scoped (e.g. `owner/repo/number`).
2. **Linkage Neutrality:** A repository-evolution relationship **NEVER** automatically promotes `DECLARED_MENTION` to `EXPLICIT_LINK`. Linkage strength depends solely on native integration evidence (e.g. Jira remote issue links), not repository evolution.
3. **No Inference from Proximity:** Shared commit ancestry, naming similarity, or shared author logins do not prove project succession.

---

## 2. Comprehensive Evidence Matrix

| Relationship Type | Semantic Definition | Minimum Required Evidence | Symm / Asymm | Transitive? | Changes Repo Identity? | Affects Provenance? | Affects Linkage? | Affects State / Temporal Alignment? | Evidence Strength in ORBIT Corpus |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`RENAME`** | The same repository entity is renamed under the same owner (e.g. `org/old-name` $\rightarrow$ `org/new-name`). | Underlying VCS repository ID remains unchanged (e.g. identical GitHub numeric repo ID). | Asymmetric | Yes | **NO** (Old and new names preserved in provenance; canonical entity keyed by target or origin). | **YES** (Records historical URL in `record_locator`). | **NO** (Linkage basis remains lexical or explicit). | **NO** (Evaluator operates on actual PR state). | **PROVEN** (`apache/incubator-flink` $\rightarrow$ `apache/flink`, repo ID `19853920`). |
| **`NAMESPACE_MOVE`** | A repository moves from one organization to another without project split (e.g. personal fork donated to organization). | VCS repository transfer metadata or verified HTTP redirect with identical repo ID. | Asymmetric | Yes | **NO** (Separate namespace strings preserved in `EntityRef`). | **YES** (Logs origin namespace in `ProvenanceRef`). | **NO** | **NO** | **PROVEN** (`stratosphere` $\rightarrow$ `apache`, though Stratosphere repo remained separate). |
| **`REDIRECT`** | An HTTP-level or VCS-level routing rule directing access from a requested URL to an actual target repository. | HTTP 301/302 response from authorized host or GitHub REST API `base.repo.full_name` redirection. | Asymmetric | Yes | **NO** (Evaluator targets returned canonical repo; requested URL logged in provenance). | **YES** (Navigational provenance only). | **NO** | **NO** | **PROVEN** (Candidate `#42`: `apache/incubator-flink#254` $\rightarrow$ `apache/flink#254`). |
| **`PREDECESSOR_SUCCESSOR`** | A historical codebase project was superseded by a successor codebase (e.g. `stratosphere/stratosphere` $\rightarrow$ `apache/flink`). | Formal project governance documentation, commit import records, or official donation records. | Asymmetric | Yes | **NO** (Both codebases remain separate `EntityRef` namespaces to prevent PR collision). | **YES** (Evolution relationship explicitly modeled). | **NO** (Does not turn Stratosphere PR into Flink PR). | **NO** (PR state evaluated against Jira issue). | **PROVEN** (448 Jira references in Flink point to `stratosphere/stratosphere`). |
| **`FORK`** | A derivative repository created by branching an existing codebase into a separate namespace. | GitHub `fork: true` metadata and explicit `parent` / `source` repository reference in API payload. | Asymmetric | No | **NO** (Fork has its own distinct `EntityRef`; marked with `is_fork=True`). | **YES** (Identifies upstream parent in provenance). | **NO** | **NO** | **PROVEN** (`salsify/avro-patches#16` in `AVRO-2199`). |
| **`MIRROR`** | A read-only replica of a primary repository hosted on a different provider/domain. | Cryptographically identical Git commit object graphs (identical commit SHAs and tree SHAs). | Symmetric | Yes | **NO** (`SourceInstance` distinguishes provider instances: `gitbox` vs `github`). | **YES** (Mirrored provenance recorded). | **NO** | **NO** | **PROVEN** (Apache GitBox $\leftrightarrow$ GitHub mirrors in `KAFKA-13557`). |
| **`VENDOR_MIRROR`** | A vendor-maintained downstream mirror or distribution branch (e.g. `linkedin/kafka`, `confluentinc/avro`). | Vendor documentation, public fork declaration, or downstream package release metadata. | Asymmetric | No | **NO** (Strictly isolated `EntityRef` to prevent vendor code conflation). | **YES** (Vendor scope recorded). | **NO** | **NO** | **SUPPORTED** (`linkedin/kafka` in population survey). |
| **`EXTERNAL_DEPENDENCY`** | An independent software library or engine consumed by the project (e.g. `facebook/rocksdb` in Kafka/Flink). | Project build descriptor (`pom.xml`, `build.gradle`), import statements, or issue text context. | Asymmetric | No | **NO** (Independent repository `EntityRef`). | **YES** (Identified as external dependency observation). | **NO** (Cannot resolve project issue on its own). | **YES** (PR merge in external dependency does NOT prove issue resolution). | **PROVEN** (`facebook/rocksdb#2283` in `KAFKA-9168`, `#5670` in `FLINK-14846`). |
| **`ECOSYSTEM_PACKAGING`** | A downstream container, package, or distribution repository (e.g. `docker-library/official-images`). | Downstream maintainer repository metadata and release coordination context. | Asymmetric | No | **NO** (Independent repository `EntityRef`). | **YES** (Identified as packaging observation). | **NO** | **YES** (Typically merged post-resolution; evaluates to `INVERTED`). | **PROVEN** (`docker-library/official-images#9249` in `FLINK-20650`). |
| **`COMPANION_SPECIFICATION`**| A sister repository defining specifications, formats, or schemas (e.g. `apache/parquet-format`). | Official project governance establishing the repository as a sub-component or format specification. | Asymmetric | No | **NO** (Separate `EntityRef` from implementation codebases). | **YES** (Specification scope recorded). | **NO** | **NO** | **PROVEN** (`apache/parquet-format#30` in `PARQUET-1032`). |
| **`INDEPENDENT_REPOSITORY`** | An unrelated repository with no project, organizational, or dependency relationship. | Absence of shared governance, build configuration, or VCS linkage. | Symmetric | N/A | **NO** (Completely disjoint `EntityRef`). | **NO** | **NO** | **NO** | **PROVEN** (`apache/parquet-java#885` vs `apache/kafka#885`). |

---

## 3. Analysis of Evidence Requirements by Category

### 3.1 Establishing `RENAME` / `REDIRECT`
* **Sufficient Evidence:** An authentic HTTP 301/302 response from the provider, or an authenticated REST API response where `base.repo.full_name` differs from the requested path while returning an identical GitHub `id` integer.
* **Insufficient Evidence:** Lexical similarity (e.g. assuming `incubator-parquet-mr` renamed to `parquet-java` without API verification). When API returns 404, rename **cannot** be inferred.

### 3.2 Establishing `PREDECESSOR_SUCCESSOR`
* **Sufficient Evidence:** Public ASF project graduation records, formal project documentation (e.g. "Stratosphere was renamed to Apache Flink in 2014"), or initial git import commits carrying full historical commit graphs.
* **Insufficient Evidence:** Merely observing that Flink Jira issues link to Stratosphere PRs. The Jira link establishes `DECLARED_MENTION`; establishing that Stratosphere is the predecessor requires external provenance facts.

### 3.3 Establishing `EXTERNAL_DEPENDENCY`
* **Sufficient Evidence:** The referenced repository belongs to an external organization (`facebook/rocksdb`) and is listed as a dependency in the project's build files.
* **Insufficient Evidence:** PR title mentioning a Jira key. External contributors often mention the upstream issue they are encountering, but that does not make the external repository part of the project.

---

## 4. Semantic Impact on Track B Evaluator Rules

| Rule | Semantic Impact of Repository Evolution | Evaluation Constraint |
| :--- | :--- | :--- |
| **`ORBIT-XB-01`** (Unlinked PR with Jira Mentions) | Zero impact. Only triggers if PR title/commit mentions Jira key while no link exists. If PR is in external repo, rule must distinguish internal implementation PRs from external dependencies. | External dependency PRs must not trigger false "unlinked internal PR" findings. |
| **`ORBIT-XB-02`** (Lifecycle Tracking Lag) | High relevance. Triggers when PR is merged while Jira issue remains unresolved. Proven in `KAFKA-12770` ↔ `apache/kafka#10656`. | If PR is in an external dependency, merging external PR does NOT imply the Jira issue is ready to close. |
| **`ORBIT-XB-03`** (Temporal Divergence) | High relevance. Triggers when PR merge occurs after Jira resolution ($\Delta > 0$). Proven in `FLINK-13730` (+92d) and `FLINK-20650` (+36d). | Ecosystem packaging PRs naturally merge post-resolution; evaluator must record observational finding without assuming data corruption. |
