# Wave 3 Phase 2 — Population Inventory

**Phase:** Pass 5 / Wave 3 — Phase 1: Population Inventory  
**Date:** 2026-09-30  
**Governing Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed`  
**Consolidation HEAD:** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`  
**Branch:** `remediation/pass3-controlled-hardening`  
**Status:** COMPLETE / READ-ONLY  
**Artifact File:** `population_inventory.json`  

---

## 1. Executive Summary

This inventory characterizes the entire locally available real Jira/GitHub population across the 5 candidate Apache Software Foundation projects (`PARQUET`, `KAFKA`, `AVRO`, `FLINK`, `ZOOKEEPER`) in `JiraReposAnon.Apache` and the locally acquired offline GitHub fixtures.

| Metric | Population Total |
| :--- | :--- |
| **Total Jira Issues Surveyed** | **47,431** |
| **Jira Issues with `github.com` Mentions in Description** | **4,225** (8.91%) |
| **Jira Issues with Explicit GitHub PR URLs in Description** | **1,329** (2.80%) |
| **Total GitHub PR URLs Mentioned in Jira Descriptions** | **1,444** |
| **Local Offline GitHub PR Fixtures Available** | **9** (7 target + 2 control) |
| **Local Offline GitHub Commits Available** | **16** |
| **Local Offline GitHub Reviews Available** | **31** |
| **Jira Remote Links in Anonymous MongoDB Dump** | **0** (MongoDB dump does not capture remote link entity) |
| **Structured Remote Links in Acquired Live Jira Fixtures** | **7** across 5 issues |
| **Missing GitHub Objects (Referenced in Jira but Offline Missing)** | **1,443** / 1,444 (99.93%) |
| **Missing Jira Objects (Referenced in Local PR Metadata)** | **0** / 9 (100% resolvable) |

---

## 2. Evidence Categorization Framework

In accordance with Phase 1 instructions, all cross-system evidence is strictly separated into five distinct, non-overlapping categories:

1. **Source-Observed Link (`source-observed link`):**  
   Native, structured Jira Remote Issue Link or equivalent REST API relationship explicitly recorded in the source system linking a Jira issue key to a GitHub PR URL.
2. **Structural Link (`structural link`):**  
   Internal relationships within a system boundary that corroborate cross-system evidence without establishing cross-system linkage (e.g., GitHub PR to head/base commit SHAs, PR reviews, multi-issue associations).
3. **Lexical Reference (`lexical reference`):**  
   Textual references where a developer pasted a GitHub PR URL into a Jira issue description, or wrote a Jira issue key (e.g. `[KAFKA-13557]`) into a PR title, branch name, or commit message.
4. **No Link (`no link`):**  
   Issues or pull requests with no cross-system reference whatsoever.
5. **Unavailable Evidence (`unavailable evidence`):**  
   A declared cross-system reference exists (e.g., Jira issue description provides `https://github.com/apache/kafka/pull/10059`), but the corroborating GitHub PR/commit record is unavailable locally in the offline environment.

---

## 3. Project-by-Project Population Breakdown

### 3.1 Apache Parquet (`PARQUET` ↔ `apache/parquet-java`)

- **Total Jira Issues in Population:** 2,092
- **Descriptions with `github.com` references:** 340 (16.25%)
- **Descriptions with `/pull/` PR links:** 97 issues (102 PR mentions)
- **Local GitHub PR Fixtures:** 2 (`#885` target, `#3822` negative control)
- **Local GitHub Commits Available:** 1
- **Local GitHub Reviews Available:** 1
- **Jira Remote Links:** 0 (live fixture `PARQUET-2010` had no remote links; MongoDB has 0)
- **Detected Jira Keys in PR Metadata:** `PARQUET-2010` (valid target), `PARQUET-1234` (template example)
- **Missing Jira Objects:** 0 (both `PARQUET-2010` and `PARQUET-1234` exist in MongoDB)
- **Missing GitHub Objects:** 102 referenced PRs have no local GitHub JSON record
- **Primary Repository:** `apache/parquet-java`
- **Repository Evolution & Collisions:**
  - `apache/incubator-parquet-mr` (28 mentions)
  - `apache/parquet-cpp` (22 mentions)
  - `apache/parquet-mr` (18 mentions)
  - `apache/arrow` (9 mentions — external project collision)
  - `apache/parquet-format` (6 mentions)
  - `apache/incubator-parquet-format` (6 mentions)
  - `apache/spark` (2 mentions — external project collision)
  - `rdblue/brotli-codec` (1 mention — external fork/dependency)
- **Evidence Breakdown:**
  - `source-observed link`: 0
  - `structural link`: 2 (1 commit, 1 review)
  - `lexical reference`: 104 (102 in Jira descriptions + 2 in PR metadata)
  - `no link`: 1,752 issues without GitHub mentions
  - `unavailable evidence`: 102 PR references

---

### 3.2 Apache Kafka (`KAFKA` ↔ `apache/kafka`)

- **Total Jira Issues in Population:** 12,312
- **Descriptions with `github.com` references:** 1,081 (8.78%)
- **Descriptions with `/pull/` PR links:** 343 issues (370 PR mentions, 397 total URL occurrences)
- **Local GitHub PR Fixtures:** 1 (`#11617` target)
- **Local GitHub Commits Available:** 5
- **Local GitHub Reviews Available:** 11
- **Jira Remote Links:** 1 structured link in live fixture (`KAFKA-13557` → PR #11617)
- **Detected Jira Keys in PR Metadata:** `KAFKA-13557`
- **Missing Jira Objects:** 0 (`KAFKA-13557` exists in MongoDB)
- **Missing GitHub Objects:** 369 referenced PRs have no local GitHub JSON record
- **Primary Repository:** `apache/kafka` (373 references in Jira descriptions)
- **Repository Evolution & Collisions:**
  - `facebook/rocksdb` (4 mentions — dependency collision)
  - `junit-team/junit5` (3 mentions — dependency collision)
  - `linkedin/kafka` (2 mentions — upstream/downstream fork)
  - `eclipse/jetty.project` (2 mentions — dependency collision)
  - `scala/scala` (2 mentions — compiler/runtime collision)
  - `apache/logging-log4j2` (1 mention — dependency collision)
- **Evidence Breakdown:**
  - `source-observed link`: 1 (native remote link)
  - `structural link`: 16 (5 commits, 11 reviews)
  - `lexical reference`: 398 (397 in Jira descriptions + 1 in PR metadata)
  - `no link`: 11,231 issues without GitHub mentions
  - `unavailable evidence`: 396 PR references

---

### 3.3 Apache Avro (`AVRO` ↔ `apache/avro`)

- **Total Jira Issues in Population:** 3,272
- **Descriptions with `github.com` references:** 326 (9.96%)
- **Descriptions with `/pull/` PR links:** 73 issues (79 PR mentions, 84 total URL occurrences)
- **Local GitHub PR Fixtures:** 1 (`#1370` target)
- **Local GitHub Commits Available:** 2
- **Local GitHub Reviews Available:** 1
- **Jira Remote Links:** 1 structured link in live fixture (`AVRO-3234` → PR #1370)
- **Detected Jira Keys in PR Metadata:** `AVRO-3234` (valid target), `AVRO-1234` (template example)
- **Missing Jira Objects:** 0 (`AVRO-3234` and `AVRO-1234` exist in MongoDB)
- **Missing GitHub Objects:** 78 referenced PRs have no local GitHub JSON record
- **Primary Repository:** `apache/avro` (73 references in Jira descriptions)
- **Repository Evolution & Collisions:**
  - `apache/camel-quarkus` (2 mentions)
  - `google/snappy` (2 mentions)
  - `salsify/avro-patches` (2 mentions — external fork)
  - `ClickHouse/ClickHouse` (1 mention)
  - `apache/beam` (1 mention)
  - `confluentinc/avro` (1 mention — external fork)
- **Evidence Breakdown:**
  - `source-observed link`: 1 (native remote link)
  - `structural link`: 3 (2 commits, 1 review)
  - `lexical reference`: 86 (84 in Jira descriptions + 2 in PR metadata)
  - `no link`: 2,946 issues without GitHub mentions
  - `unavailable evidence`: 83 PR references

---

### 3.4 Apache Flink (`FLINK` ↔ `apache/flink`)

- **Total Jira Issues in Population:** 25,492
- **Descriptions with `github.com` references:** 2,252 (8.83%)
- **Descriptions with `/pull/` PR links:** 747 issues (779 PR mentions, 786 total URL occurrences)
- **Local GitHub PR Fixtures:** 4 (`#17401`, `#17773`, `#17799`, `#10123`)
- **Local GitHub Commits Available:** 8 (1 + 2 + 2 + 3)
- **Local GitHub Reviews Available:** 18 (1 + 5 + 0 + 12)
- **Jira Remote Links:** 5 structured links across 3 issues (`FLINK-24409` has 3, `FLINK-14386` has 1, `FLINK-14665` has 1)
- **Detected Jira Keys in PR Metadata:** `FLINK-24409`, `FLINK-14386`, `FLINK-14664`, `FLINK-14665`
- **Missing Jira Objects:** 0 (all 4 keys exist in MongoDB)
- **Missing GitHub Objects:** 775 referenced PRs have no local GitHub JSON record
- **Primary Repository:** `apache/flink` (261 references)
- **Repository Evolution & Collisions:**
  - `stratosphere/stratosphere` (448 mentions — **major historical predecessor repository** before Apache Flink incubation)
  - `apache/incubator-flink` (9 mentions — incubation period mirror)
  - `facebook/rocksdb` (7 mentions — state backend dependency)
  - `awslabs/amazon-kinesis-connector-flink` (6 mentions — external connector)
  - `apache/flink-statefun` (5 mentions — sub-project repository)
  - `dimalabs/ozone` (5 mentions — external fork)
  - `docker-library/official-images` (3 mentions — packaging repository)
  - `apache/flink-web` (3 mentions — documentation/website repository)
  - `awslabs/amazon-kinesis-producer` (3 mentions)
- **Evidence Breakdown:**
  - `source-observed link`: 5 (native remote links)
  - `structural link`: 26 (8 commits, 18 reviews)
  - `lexical reference`: 790 (786 in Jira descriptions + 4 in PR metadata)
  - `no link`: 23,240 issues without GitHub mentions
  - `unavailable evidence`: 782 PR references

---

### 3.5 Apache ZooKeeper (`ZOOKEEPER` ↔ `apache/zookeeper`)

- **Total Jira Issues in Population:** 4,263
- **Descriptions with `github.com` references:** 226 (5.30%)
- **Descriptions with `/pull/` PR links:** 69 issues (74 PR mentions, 75 total URL occurrences)
- **Local GitHub PR Fixtures:** 0
- **Local GitHub Commits Available:** 0
- **Local GitHub Reviews Available:** 0
- **Jira Remote Links:** 0
- **Detected Jira Keys in PR Metadata:** 0 (no PRs available)
- **Missing Jira Objects:** 0
- **Missing GitHub Objects:** 75 referenced PRs have no local GitHub JSON record (**100% missing**)
- **Primary Repository:** `apache/zookeeper` (66 references)
- **Repository Evolution & Collisions:**
  - `mark-5/p5-net-zookeeper` (3 mentions — Perl wrapper)
  - `apache/logging-log4j2` (1 mention — dependency)
  - `go-zookeeper/zk` (1 mention — Go client)
  - `apache/kafka` (1 mention — consumer dependency)
  - `python-zk/kazoo` (1 mention — Python client)
- **Evidence Breakdown:**
  - `source-observed link`: 0
  - `structural link`: 0
  - `lexical reference`: 75
  - `no link`: 4,037 issues without GitHub mentions
  - `unavailable evidence`: 75 PR references

---

## 4. Key Population Findings and Boundary Conditions

1. **Massive Description-Embedded Linkage Reservoir:**  
   Across the 47,431 surveyed issues, **1,329 issues contain 1,444 explicit GitHub PR URLs**. This confirms that developers frequently paste PR links directly into Jira issue descriptions.
2. **MongoDB Anonymous Dump Ground-Truth Gap:**  
   The `JiraReposAnon.Apache` MongoDB dump contains **0 structured remote links** (`remotelinks` field is empty). The structured remote links identified in Phase 1A originated from live Jira REST API queries before acquisition, not from the raw MongoDB collection.
3. **Severe Local Offline Data Boundary:**  
   Of the 1,444 declared PR URLs, only **7 target PRs** have corroborating local GitHub records on disk in `qualification/wave3/apache_real/github/`. 1,437 PRs are unavailable offline. Under the strict No-Mutation / No-Network rule, new records cannot be fetched.
4. **Historical Repository Identity Shifts:**  
   In Flink, 448 out of 786 PR links (57.0%) point to `stratosphere/stratosphere` (the pre-Apache project name). In Parquet, links span `incubator-parquet-mr`, `parquet-mr`, `parquet-cpp`, and `parquet-format`. A naive string match on `apache/flink` or `apache/parquet-java` fails to resolve these historical aliases.
5. **Template Pollution (Lexical False Positives):**  
   Both `parquet-java/pull_885` and `avro/pull_1370` contain Jira keys `PARQUET-1234` and `AVRO-1234` in their PR template boilerplate instructions. These are lexical mentions that do NOT represent authentic work links.

---

*Inventory complete. Frozen selection methodology follows in Phase 2.*
