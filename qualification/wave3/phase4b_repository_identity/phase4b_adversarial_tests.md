# Phase 4B — Adversarial Repository Identity Tests

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4B — Repository Identity & Evolution ADR  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Status:** **ADVERSARIAL SUITE & SAFETY ANALYSIS COMPLETE**  

---

## 1. Objective

This document evaluates ORBIT's repository identity architecture against 12 adversarial, edge, and deceptive repository scenarios derived from real-world open-source practices. 

Each scenario demonstrates the boundary between **deterministic facts** and **unsupported inference**, testing whether ORBIT's existing repository-scoped identity model maintains stability without false equivalence or identity collapse.

---

## 2. Adversarial Case Specifications

---

### Case 1: Same Numeric PR Number in Different Repositories
* **Observed Facts:**  
  PR `#885` exists in `apache/parquet-java` (title: *"Fix Parquet-2010: decimal logical type in Parquet-Avro"*).  
  PR `#885` also exists in `apache/kafka` (title: *"KAFKA-1981: Make LogCleaner thread safe"*).  
  Both PRs share the exact numeric ID `885`.
* **Safe Conclusion:**  
  The two pull requests are entirely unrelated entities belonging to completely different software projects.
* **Unsafe Inference:**  
  Keying pull requests by numeric ID alone or stripping repository namespace, causing cross-project data corruption and false state conflation.
* **Expected ORBIT Representation:**  
  `EntityRef(github, "code_change", "apache/parquet-java/885")`  
  `!= EntityRef(github, "code_change", "apache/kafka/885")`  
  *Integrity Invariant Preserved:* Full repository string in `entity_id` guarantees non-collision.

---

### Case 2: Same Repository Name in Different Namespaces
* **Observed Facts:**  
  Repository `kafka` exists under `apache/kafka` (canonical Apache project).  
  Repository `kafka` also exists under `linkedin/kafka` (vendor downstream fork).  
  Both repositories have a PR `#100`.
* **Safe Conclusion:**  
  `apache/kafka` and `linkedin/kafka` are distinct repositories with different governance, release cycles, and commit histories.
* **Unsafe Inference:**  
  Treating `linkedin/kafka` as synonymous with `apache/kafka` based on the repository name substring alone.
* **Expected ORBIT Representation:**  
  `entity_id = "apache/kafka/100"` vs `entity_id = "linkedin/kafka/100"`.  
  Different `EntityRef` instances; vendor fork isolated.

---

### Case 3: Fork with Identical PR Number
* **Observed Facts:**  
  `apache/avro` has PR `#16` (an official Apache Avro pull request from 2015).  
  `salsify/avro-patches` (a vendor fork) also has a PR `#16` (a private patch PR referenced in `AVRO-2199`).
* **Safe Conclusion:**  
  `salsify/avro-patches#16` is a private patch PR submitted to a vendor fork. It is NOT the canonical Avro PR `#16`.
* **Unsafe Inference:**  
  Falsely associating `AVRO-2199` with `apache/avro#16` because the Jira issue is in the `AVRO` project and references PR `#16`.
* **Expected ORBIT Representation:**  
  `EntityRef(github, "code_change", "salsify/avro-patches/16")` with `extra_properties["is_fork"] = True`.

---

### Case 4: Historical Incubator Repository with Successor Repository
* **Observed Facts:**  
  `FLINK-1359` description references `https://github.com/apache/incubator-flink/pull/254`.  
  GitHub's REST API automatically redirects `apache/incubator-flink` to `apache/flink` and returns PR `#254` with `base.repo.full_name = "apache/flink"`.
* **Safe Conclusion:**  
  `apache/incubator-flink` was officially renamed to `apache/flink` upon ASF graduation. Navigation continuity is established by GitHub's underlying immutable repository ID (`19853920`).
* **Unsafe Inference:**  
  Assuming all incubator repositories have active redirects, or rewriting raw historical provenance to erase the incubator URL.
* **Expected ORBIT Representation:**  
  Canonical entity is `apache/flink/254`. The requested URL (`apache/incubator-flink/pull/254`) is preserved in `ProvenanceRef` and reconciliation records as a verified `REDIRECT / GRADUATION_RENAME`.

---

### Case 5: Mirrors with Identical Commit SHAs
* **Observed Facts:**  
  An Apache project maintains a primary git repository on Apache GitBox (`gitbox.apache.org/repos/asf/kafka.git`) and a mirrored repository on GitHub (`github.com/apache/kafka`).  
  Commit `a1b2c3d` has identical commit metadata and SHA on both servers.
* **Safe Conclusion:**  
  The commit content is content-addressable and identical. However, pull requests, reviews, and issue links exist **only** on GitHub.
* **Unsafe Inference:**  
  Treating GitBox as having GitHub PR entities or attempting to query PR numbers against GitBox.
* **Expected ORBIT Representation:**  
  Different `SourceInstance` boundaries:  
  `SourceInstance("git", "gitbox.apache.org")` vs `SourceInstance("github", "github.com/apache")`.  
  Commit observations can reference both, but PR observations belong exclusively to GitHub.

---

### Case 6: Repository Renamed Without Accessible Redirect Evidence
* **Observed Facts:**  
  Jira issue `PARQUET-171` links to `https://github.com/apache/incubator-parquet-mr/pull/107`.  
  GitHub returns HTTP 404 (the historical `incubator-parquet-mr` repository mirror was deleted or purged without an HTTP redirect when repositories were merged).
* **Safe Conclusion:**  
  The reference exists in historical Jira text, but the target code change object is unavailable offline and on GitHub.
* **Unsafe Inference:**  
  Guessing that PR `#107` in `apache/parquet-mr` or `apache/parquet-java` is the same PR, or fabricating PR metadata.
* **Expected ORBIT Representation:**  
  Acquisition outcome: `NOT_FOUND`.  
  CrossSystemStateAlignment: `INSUFFICIENT_EVIDENCE`.  
  Evaluator honestly records missing evidence without synthetic repair.

---

### Case 7: Repository that Moved Organization / Namespace
* **Observed Facts:**  
  448 Jira issues in Flink reference `stratosphere/stratosphere#<number>`.  
  In 2014, Stratosphere was donated to the Apache Software Foundation and incubated as Apache Flink.  
  The original repository `stratosphere/stratosphere` remains accessible on GitHub in an archived state.
* **Safe Conclusion:**  
  `stratosphere/stratosphere` is an archived predecessor repository. It possesses its own PR sequence (`#1` to `#891`). These PRs are real historical artifacts of the Flink project's predecessor.
* **Unsafe Inference:**  
  Rewriting `stratosphere/stratosphere#126` to `apache/flink#126`. (In `apache/flink`, PR `#126` is an entirely different PR created months later).
* **Expected ORBIT Representation:**  
  `EntityRef(github, "code_change", "stratosphere/stratosphere/126")`.  
  Preserved as an authentic observation with `PREDECESSOR_SUCCESSOR` evolution relationship metadata.

---

### Case 8: External Dependency PR Mentioning a Project Jira Key
* **Observed Facts:**  
  A developer debugging `KAFKA-9168` files a PR in `facebook/rocksdb#2283` and writes *"Fixes issue observed in KAFKA-9168"* in the PR description.
* **Safe Conclusion:**  
  The author of the RocksDB PR noted a cross-project context. The PR is a contribution to Facebook RocksDB, an external dependency.
* **Unsafe Inference:**  
  Promoting the link to `EXPLICIT_LINK` or treating RocksDB commits as Apache Kafka codebase commits.
* **Expected ORBIT Representation:**  
  Relationship kind: `DECLARED_MENTION`.  
  CodeChangeState belongs to `facebook/rocksdb`.  
  Merging the RocksDB PR does NOT prove Kafka issue resolution.

---

### Case 9: PR Title Containing Jira Key Belonging to a Sister Project
* **Observed Facts:**  
  PR `#176` in `apache/arrow` has the title `"[PARQUET-752] C++ Parquet arrow reader update"`.  
  `PARQUET-752` is a Parquet Jira issue, but the PR is in the `apache/arrow` repository.
* **Safe Conclusion:**  
  Arrow and Parquet collaborate on C++ columnar data formats. Arrow merged a patch that addresses Parquet compatibility.
* **Unsafe Inference:**  
  Treating `apache/arrow#176` as `apache/parquet-java#176`.
* **Expected ORBIT Representation:**  
  `EntityRef("apache/arrow/176")` correctly linked to `PARQUET-752` via `DECLARED_MENTION`.  
  Identity scoping prevents Arrow PR from corrupting Parquet PR numbering.

---

### Case 10: Unauthenticated or Shortened Redirect
* **Observed Facts:**  
  A Jira description contains a URL from a redirector (e.g. `https://git.io/xyz` or an internal tracker link) that routes via HTTP 302 to a GitHub PR.
* **Safe Conclusion:**  
  The intermediate shortener provides transport routing only. The authentic entity identity resides strictly on GitHub.
* **Unsafe Inference:**  
  Treating the redirector URL as the entity identifier or failing closed because the URL domain is not `github.com`.
* **Expected ORBIT Representation:**  
  Destination canonical PR is adapted into `EntityRef(github, ...)`. The intermediate redirect URL is preserved in `ProvenanceRef` as navigational metadata.

---

### Case 11: Repository Lookalike Based on Naming Similarity
* **Observed Facts:**  
  `apache/parquet-format` (specification repo) and `apache/parquet-mr` (Java implementation repo) share the prefix `apache/parquet-`.
* **Safe Conclusion:**  
  These are two distinct components of the Apache Parquet project with separate source trees, separate git commit graphs, and separate PR counters.
* **Unsafe Inference:**  
  Using fuzzy string distance or heuristic clustering to treat `parquet-format` as a rename or alias of `parquet-mr`.
* **Expected ORBIT Representation:**  
  Strict exact repository matching. Heuristic clustering is explicitly prohibited.

---

### Case 12: Shared History in a Documented Fork
* **Observed Facts:**  
  `salsify/avro-patches` shares 10,000 commits with `apache/avro` up to the fork point.
* **Safe Conclusion:**  
  A fork inevitably shares historical commits with its upstream parent. That shared ancestry does NOT make the fork a successor or mirror.
* **Unsafe Inference:**  
  Inferring repository equivalence from commit SHA overlap.
* **Expected ORBIT Representation:**  
  `salsify/avro-patches` remains a distinct repository with `is_fork=True`. Commits authored on the fork branch are isolated from the canonical Apache Avro codebase.

---

## 3. Summary of Adversarial Invariants

| Adversarial Vector | Failure Mode If Handled Incorrectly | ORBIT Architectural Defense |
| :--- | :--- | :--- |
| **Numeric Collision** | Overwriting PRs with identical numbers across repos | Full `owner/repo/number` scoping in `EntityRef` |
| **Namespace Confusion** | Confusing vendor forks (`linkedin/kafka`) with upstream (`apache/kafka`) | Strict `owner` inclusion in `entity_id` |
| **Incubation Graduation** | Entity fragmentation or broken links | Navigation redirect preservation with underlying repo continuity |
| **Predecessor Collisions** | Falsely merging Stratosphere and Flink PRs (`#126`) | Explicit `PREDECESSOR_SUCCESSOR` relationship without identity mutation |
| **Purged Repositories** | Fabricating missing records | Closed outcome taxonomy (`NOT_FOUND`, `INSUFFICIENT_EVIDENCE`) |
| **External Dependencies** | Conflating external libraries with internal code | Clear dependency boundary; PR merge $\ne$ issue resolution |
| **Fuzzy Matching** | Collapsing distinct sister components (`parquet-format` vs `mr`) | Exact string matching; zero heuristic clustering |
