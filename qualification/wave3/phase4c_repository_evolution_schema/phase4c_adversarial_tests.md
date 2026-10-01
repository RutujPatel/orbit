# Phase 4C — Adversarial Schema Test Matrix

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4C — Formal Repository Evolution Schema Specification  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Status:** **ADVERSARIAL SPECIFICATION COMPLETE**  

---

## 1. Overview

This document specifies the complete formal adversarial test matrix for the `RepositoryEvolutionRelationship` schema. Every test scenario defines the concrete input, the required canonical representation, the strictly forbidden representation, and the underlying architectural rationale.

---

## 2. Category A: Identity Scenarios

---

### ADV-ID-01: Same PR Number Across Distinct Repositories
* **Input:** PR `#885` in `apache/parquet-java` and PR `#885` in `apache/kafka`.
* **Expected Canonical Representation:**  
  Two distinct observations:  
  `EntityRef(github, "code_change", "apache/parquet-java/885")`  
  `EntityRef(github, "code_change", "apache/kafka/885")`
* **Forbidden Representation:** Any representation keying PRs by `#885` alone or collapsing them into a shared entity.
* **Reason:** Repository namespace is an essential component of `entity_id`.

---

### ADV-ID-02: Same Repository Name Under Different Owners
* **Input:** Repository `kafka` under owner `apache` (`apache/kafka`) and under owner `linkedin` (`linkedin/kafka`).
* **Expected Canonical Representation:**  
  Two distinct repository entities:  
  `EntityRef(github, "repository", "apache/kafka")`  
  `EntityRef(github, "repository", "linkedin/kafka")`
* **Forbidden Representation:** Stripping owner namespace and treating `kafka` as a global repository ID.
* **Reason:** Namespaces establish governance boundaries; vendor forks must not be confused with upstream canonical repositories.

---

### ADV-ID-03: Same Repository Across Different Provider Instances
* **Input:** Git repository at `gitbox.apache.org/repos/asf/kafka.git` vs GitHub mirror at `github.com/apache/kafka`.
* **Expected Canonical Representation:**  
  Two distinct repository entities separated by `SourceInstance`:  
  `EntityRef(SourceInstance("git", "gitbox.apache.org"), "repository", "kafka")`  
  `EntityRef(SourceInstance("github", "github.com/apache"), "repository", "apache/kafka")`  
  Linked via `RepositoryEvolutionRelationship(type="MIRROR", directionality="BIDIRECTIONAL_SYMMETRIC")`.
* **Forbidden Representation:** Merging the two into a single `SourceInstance` or assuming GitHub PRs exist on GitBox.
* **Reason:** Provider instances have different feature sets and API boundaries.

---

### ADV-ID-04: Repository Rename Under Same Owner
* **Input:** GitHub repository `apache/incubator-flink` renamed to `apache/flink` with identical numeric repo ID (`19853920`).
* **Expected Canonical Representation:**  
  Two distinct repository entities linked by:  
  `RepositoryEvolutionRelationship(type="RENAME", source="apache/incubator-flink", target="apache/flink")`.  
  PRs created after rename are scoped to `apache/flink`.
* **Forbidden Representation:** Mutating historical `EntityRef` values of archived incubator observations.
* **Reason:** Historical provenance must record the exact identifier under which an event occurred.

---

### ADV-ID-05: Repository Namespace Move (Organization Transfer)
* **Input:** Repository `stratosphere/stratosphere` donated to the Apache Software Foundation.
* **Expected Canonical Representation:**  
  `RepositoryEvolutionRelationship(type="PREDECESSOR_SUCCESSOR", source="stratosphere/stratosphere", target="apache/flink")`.  
  Both repositories retain their distinct `EntityRef` instances.
* **Forbidden Representation:** Automatically rewriting `stratosphere/stratosphere#126` to `apache/flink#126`.
* **Reason:** The predecessor codebase had its own PR numbers (`#1` to `#891`). Rewriting causes catastrophic collisions with Flink's subsequent PR `#126`.

---

## 3. Category B: Evolution & Topology Scenarios

---

### ADV-EV-01: Incubation to Graduated Repository with Active Redirect
* **Input:** `FLINK-1359` requests `https://github.com/apache/incubator-flink/pull/254`. GitHub API redirects to `apache/flink#254`.
* **Expected Canonical Representation:**  
  Canonical code change entity is `EntityRef(github, "code_change", "apache/flink/254")`.  
  A `REDIRECT` relationship connects `apache/incubator-flink` to `apache/flink`.  
  Requested URL recorded in `ProvenanceRef`.
* **Forbidden Representation:** Failing closed with `UNRESOLVED_REFERENCE` or dropping the requested incubator URL from provenance.
* **Reason:** Navigation continuity was verified by provider redirect.

---

### ADV-EV-02: Deleted / Purged Predecessor Repository (404)
* **Input:** `PARQUET-171` links to `apache/incubator-parquet-mr#107`. GitHub returns HTTP 404.
* **Expected Canonical Representation:**  
  Acquisition outcome `NOT_FOUND`.  
  CrossSystemStateAlignment `INSUFFICIENT_EVIDENCE`.  
  Zero `RepositoryEvolutionRelationship` created without corroborating evidence.
* **Forbidden Representation:** Fabricating a redirect or guessing that PR `#107` in `apache/parquet-mr` is the same PR.
* **Reason:** Missing evidence must be reported honestly; synthesis is strictly forbidden.

---

### ADV-EV-03: Downstream Vendor Fork
* **Input:** PR `#16` in `salsify/avro-patches` referenced in `AVRO-2199`.
* **Expected Canonical Representation:**  
  `EntityRef(github, "code_change", "salsify/avro-patches/16")` with `is_fork=True`.  
  `RepositoryEvolutionRelationship(type="FORK", source="salsify/avro-patches", target="apache/avro")`.
* **Forbidden Representation:** Treating `salsify/avro-patches#16` as canonical `apache/avro#16`.
* **Reason:** Forks do not replace upstream canonical repositories.

---

### ADV-EV-04: External Dependency Reference
* **Input:** `KAFKA-9168` description links to `https://github.com/facebook/rocksdb/pull/2283`.
* **Expected Canonical Representation:**  
  `EntityRef(github, "code_change", "facebook/rocksdb/2283")` linked to `KAFKA-9168` via `DECLARED_MENTION`.  
  `RepositoryEvolutionRelationship(type="EXTERNAL_DEPENDENCY", source="apache/kafka", target="facebook/rocksdb")`.
* **Forbidden Representation:** Treating `facebook/rocksdb` as an internal Kafka repository or treating the RocksDB PR merge as resolving the Kafka issue.
* **Reason:** RocksDB is an external library; internal resolution requires a Kafka commit updating the dependency.

---

## 4. Category C: Cardinality Scenarios

---

### ADV-CD-01: One Predecessor Repository to Multiple Successors (Split)
* **Input:** Monolithic repository `apache/parquet` split into `apache/parquet-mr` and `apache/parquet-cpp`.
* **Expected Canonical Representation:**  
  Two independent relationships:  
  `PREDECESSOR_SUCCESSOR(source="apache/parquet", target="apache/parquet-mr")`  
  `PREDECESSOR_SUCCESSOR(source="apache/parquet", target="apache/parquet-cpp")`
* **Forbidden Representation:** Merging the two target repositories into one or assuming PR numbers transfer.
* **Reason:** Repository splitting is a valid one-to-many lineage graph.

---

### ADV-CD-02: Multiple Predecessors to One Successor (Merge)
* **Input:** Sub-projects `incubator-parquet-mr` and `incubator-parquet-format` merged under `apache/parquet`.
* **Expected Canonical Representation:**  
  Two independent relationships targeting the same repository:  
  `PREDECESSOR_SUCCESSOR(source="incubator-parquet-mr", target="apache/parquet")`  
  `PREDECESSOR_SUCCESSOR(source="incubator-parquet-format", target="apache/parquet")`
* **Forbidden Representation:** Collapsing the two predecessors into each other.
* **Reason:** Lineage graph must accurately preserve multi-predecessor origin.

---

### ADV-CD-03: Multiple Jira Issues Linked to One PR (Many-to-One)
* **Input:** `KAFKA-12770` and `KAFKA-12771` both link to `apache/kafka#10656`.
* **Expected Canonical Representation:**  
  Exactly ONE observation for `apache/kafka/10656`.  
  Two distinct `CrossSystemStateAlignment` records.  
  Independent Track B evaluation (`ORBIT-XB-02` triggered on `12770` only).
* **Forbidden Representation:** Duplicating the PR observation or collapsing the two Jira issues into duplicates.
* **Reason:** Proven in Phase 3B; many-to-one cardinality is an authentic real-world pattern.

---

## 5. Category D: Evidence & Provenance Scenarios

---

### ADV-PR-01: Plain Text Jira URL Without Corroborating VCS Evidence
* **Input:** A Jira description says: *"See https://github.com/foo/bar/pull/1"*, but no GitHub API, VCS, or governance record exists.
* **Expected Canonical Representation:**  
  `relationship_kind="DECLARED_MENTION"` on cross-system alignment.  
  NO `RepositoryEvolutionRelationship` created.
* **Forbidden Representation:** Inferring a `PREDECESSOR_SUCCESSOR` or `FORK` relationship between Jira's project and `foo/bar` based on text alone.
* **Reason:** Plain URLs establish lexical mention only; repository lineage requires verified provenance.

---

### ADV-PR-02: Circular Redirect Loop (Adversarial Routing)
* **Input:** Provider metadata reports Repository A redirects to B, and B redirects to A.
* **Expected Canonical Representation:**  
  Validation error: `QualityIssue(code="invalid", message="Circular routing loop detected in NAVIGATION_ROUTING")`.
* **Forbidden Representation:** Infinite loop in resolution or non-terminating graph traversal.
* **Reason:** Invariant `INV-GR-02` requires strict acyclicity in routing graphs.

---

### ADV-PR-03: Missing or Unresolvable Provenance Locator
* **Input:** A repository evolution relationship submitted with `provenance_refs` pointing to a non-existent fixture path.
* **Expected Canonical Representation:**  
  Provenance dereferencing returns `status="NOT_FOUND"`. Bundle validation emits `QualityIssue(code="unresolved")`.
* **Forbidden Representation:** Accepting the relationship into the qualified bundle without valid provenance.
* **Reason:** Invariant `INV-EV-01` requires mandatory cryptographic provenance.

---

## 6. Category E: Semantic Firewall Scenarios

---

### ADV-FW-01: Evolution Incorrectly Used to Upgrade Linkage
* **Input:** Jira issue has a `DECLARED_MENTION` of `stratosphere/stratosphere#126`. A verified `PREDECESSOR_SUCCESSOR` relationship exists between Stratosphere and Flink.
* **Expected Canonical Representation:**  
  Cross-system alignment relationship kind **MUST REMAIN** `DECLARED_MENTION`.
* **Forbidden Representation:** Automatically promoting the alignment to `EXPLICIT_LINK`.
* **Reason:** Invariant `INV-LK-01`. Repository succession does not convert an informal Jira comment URL into a native integration link.

---

### ADV-FW-02: External Dependency PR Merge Transferred as Issue Completion
* **Input:** `KAFKA-9168` is in `Open` status. Its linked PR `facebook/rocksdb#2283` is `merged`.
* **Expected Canonical Representation:**  
  Alignment state comparison: `INSUFFICIENT_EVIDENCE`.  
  `ORBIT-XB-02` finding: **NOT TRIGGERED** on external dependency PR.
* **Forbidden Representation:** Inferring that `KAFKA-9168` was completed or that the merged RocksDB PR completes Kafka work.
* **Reason:** Invariant `INV-ST-02`. An external library PR does not resolve the consuming project's issue.

---

### ADV-FW-03: Timestamp Proximity Falsely Inferred as Causality
* **Input:** Repository A renamed to B at 14:00:00Z. Issue X resolved at 14:00:05Z.
* **Expected Canonical Representation:**  
  Two independent timestamps recorded. Zero causal inference.
* **Forbidden Representation:** Generating an evaluation finding asserting that Issue X caused the repository rename.
* **Reason:** Invariant `INV-TM-01`. Proximity is not causality.

---

### ADV-FW-04: Naming Similarity Falsely Inferred as Successor
* **Input:** Repositories `apache/parquet-format` and `apache/parquet-mr` share name prefix.
* **Expected Canonical Representation:**  
  Treated as independent sister repositories (`COMPANION_SPECIFICATION`).
* **Forbidden Representation:** Treating `parquet-format` as a rename or predecessor of `parquet-mr`.
* **Reason:** Invariant `INV-ID-01`. Zero fuzzy matching or naming-based predecessor inference.
