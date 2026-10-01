# Phase 4B — Reconnaissance: Repository Identity & Evolution

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4B — Repository Identity & Evolution ADR  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Consolidation Commit (HEAD):** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`  
**Branch:** `remediation/pass3-controlled-hardening`  
**Status:** **RESEARCH & ARCHITECTURAL RECONNAISSANCE COMPLETE**  

---

## 1. Purpose and Scope

Phase 4B investigates how Project ORBIT must represent repository identity when software projects undergo real-world repository evolution across names, namespaces, mirrors, incubators, redirects, forks, migrations, predecessor/successor repositories, and external dependencies.

This phase is strictly **forensic research and architectural design**. No production code, canonical schemas, or evaluator rules are modified.

---

## 2. Existing ORBIT Canonical Identity Model

Reconnaissance of the production source tree (`src/shadow_orbit/evidence_types.py`) reveals how ORBIT currently defines identity across disparate systems:

### 2.1 The Identity Triad: `SourceInstance`, `EntityKind`, `EntityId`

Canonical entity identity is encapsulated by `EntityRef`:

```python
@dataclass(frozen=True, slots=True)
class EntityRef:
    source_instance: SourceInstance
    entity_kind: EntityKind
    entity_id: str
```

Where:
1. **`SourceInstance` (`source_kind`, `instance_id`):** Scopes the deployment boundary (e.g., `source_kind="github"`, `instance_id="github.com/apache"`). Two instances with different `instance_id` represent distinct deployments whose entity IDs cannot be compared directly.
2. **`EntityKind`:** Closed vocabulary (`"work_item"`, `"code_change"`, `"review"`, `"commit"`, `"branch"`, `"repository"`).
3. **`EntityId`:** String identifier whose formatting rules depend on the entity kind.

### 2.2 Current Pull Request Identity Scoping

In the GitHub adapter (`qualification/wave3/apache_real/adapters/apache_github_adapter.py` lines 163–170), pull requests are scoped as:

```python
eff_repo = repo or state.extra_properties.get("repo") or "apache/unknown"
entity_id = f"{eff_repo}/{state.identifier}"

entity_ref = EntityRef(
    source_instance=context.source_instance,
    entity_kind="code_change",
    entity_id=entity_id,
)
```

Example concrete identities:
- `EntityRef(github, "code_change", "apache/parquet-java/885")`
- `EntityRef(github, "code_change", "apache/kafka/11617")`
- `EntityRef(github, "code_change", "stratosphere/stratosphere/126")`
- `EntityRef(github, "code_change", "facebook/rocksdb/2283")`

### 2.3 Uniqueness Invariants in `EvidenceBundle`

In `EvidenceBundle`, observations are indexed by `EntityRef`:
- Two observations in the same bundle **must not share an identical `EntityRef`** (enforced by `validate_evidence_bundle`).
- Distinct pull requests with the same numeric ID in different repositories have distinct `entity_id` values (e.g., `"apache/flink/126"` vs `"stratosphere/stratosphere/126"`), preventing collision.

---

## 3. Attribute Classification: Identity vs Descriptive vs Navigational

A critical architectural distinction must be maintained between what identifies an entity and what merely describes or locates it:

| Field | Classification | Mutability / Stability | Evaluator Authority |
| :--- | :--- | :--- | :--- |
| **`SourceInstance.instance_id`** | **Identity-Bearing** | Immutable deployment scope | Primary boundary authority |
| **`EntityRef.entity_kind`** | **Identity-Bearing** | Immutable semantic type | Sole authority for entity kind |
| **`owner/repo` (in `entity_id`)** | **Identity-Bearing** | Repository namespace scope | Prevents cross-repo ID collision |
| **`pr_number` (in `entity_id`)** | **Identity-Bearing** | Repository-local numeric index | Local discriminator within repository |
| **`GitHub repository ID` (numeric)** | **Identity-Bearing** | Globally immutable on GitHub | Authoritative underlying ID, but unexposed in raw URLs |
| **`title`, `body`** | **Descriptive** | Highly mutable by author | Lexical mention source; zero identity authority |
| **`author_login`** | **Descriptive** | Semi-stable user handle | Contextual actor fact; zero linkage authority |
| **`html_url`** | **Navigational** | Mutable via redirects/renames | Human web access locator; not canonical identity |
| **HTTP 301/302 Redirect** | **Navigational** | Transport/routing layer | Evidence of routing continuity; not identity equivalence |
| **`fixture_id` / `record_locator`**| **Provenance-Only** | Local file / database coordinate | Evidence verification authority only |

---

## 4. Empirical Population Findings from Phase 1, 2, 3A, and 3B

Across 47,431 surveyed Jira issues in `JiraReposAnon.Apache`, 1,444 PR URLs were identified. Analysis of the complete population reveals 5 major real-world repository identity phenomena:

### 4.1 Case A — Upstream Repository Graduation & Redirects
* **Example:** `FLINK-1359` referenced `https://github.com/apache/incubator-flink/pull/254`.
* **API Behavior:** GitHub returned HTTP 200 with `base.repo.full_name = "apache/flink"`.
* **Observation:** GitHub maintains an internal immutable repository ID (`id: 19853920`). When Apache Flink graduated from incubation, the repository was renamed from `apache/incubator-flink` to `apache/flink`. GitHub's API automatically routes the old namespace to the new one.
* **Finding:** Navigation continuity is established by GitHub. However, the Jira text explicitly records the historical incubator name.

### 4.2 Case B — Numeric Identifier Collisions Across Historical Namespaces
* **Example:** `stratosphere/stratosphere#126` (referenced by `FLINK-126` and `FLINK-236`) vs `apache/flink#126` (a completely different commit and author).
* **Observation:** In Flink's Jira corpus, **57.0% (448 / 786)** of all PR references point to `stratosphere/stratosphere`, the pre-Apache predecessor project.
* **Finding:** `stratosphere/stratosphere#126` and `apache/flink#126` have completely different commits, titles, and dates. If an identity model naively "normalized" `stratosphere/stratosphere` to `apache/flink`, it would cause catastrophic cross-entity collision.

### 4.3 Case C — External Repositories & Ecosystem Dependencies
* **Examples:**
  * `KAFKA-9168` $\rightarrow$ `facebook/rocksdb#2283`
  * `FLINK-14846` $\rightarrow$ `facebook/rocksdb#5670`
  * `FLINK-20650` $\rightarrow$ `docker-library/official-images#9249`
  * `PARQUET-1639` $\rightarrow$ `apache/arrow#4985`
  * `PARQUET-1032` $\rightarrow$ `apache/parquet-format#30`
* **Observation:** Developers frequently link PRs in external dependencies, sister projects, container packaging repos, or specification sub-projects directly within Jira issues.
* **Finding:** These are authentic cross-system relationships, but the referenced repository is **not** the implementation codebase of the Jira issue's own project. They represent external ecosystem interactions.

### 4.4 Case D — Multiple Jira Issues Sharing a Single PR (Many-to-One)
* **Examples:**
  * `KAFKA-12770` and `KAFKA-12771` both link to `apache/kafka#10656`.
  * `FLINK-126` and `FLINK-236` both link to `stratosphere/stratosphere#126`.
* **Observation:** A developer opens a single pull request that resolves or touches multiple tracked Jira issues.
* **Finding:** The PR entity must exist as **one observation**, while two distinct `CrossSystemStateAlignment` records must be maintained. Crucially, in `KAFKA-12770`, the issue was left open in `Patch Available` while `KAFKA-12771` was `Resolved`, triggering an `ORBIT-XB-02` finding on the former but not the latter.

### 4.5 Case E — One Jira Issue Linking to Multiple PRs (One-to-Many)
* **Example:** `FLINK-24409` linked to PRs `#17401`, `#17773`, and `#17799`.
* **Observation:** An issue involves multiple attempts, multiple branches, or separate follow-up PRs.
* **Finding:** The Jira issue exists as **one observation**, with multiple distinct alignments to separate PR observations.

---

## 5. Architectural Assessment

Current ORBIT semantics correctly protect against ID collisions because `EntityRef` includes the full repository string (`owner/repo/number`). 

However, ORBIT currently lacks any formal mechanism to express:
1. That `stratosphere/stratosphere` was the historical predecessor of `apache/flink`.
2. That `facebook/rocksdb` is an external dependency rather than an Apache codebase.
3. That `apache/incubator-flink` redirected to `apache/flink` due to graduation.

The fundamental research challenge is: **Can ORBIT represent these real relationships without weakening repository-scoped identity or manufacturing false cross-system certainty?**
