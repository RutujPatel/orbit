# Pass 5 Wave 3 — Local Cross-System Evidence Audit

**Audit Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 — Phase 0B: Local Cross-System Evidence Audit  
**Repository:** `/home/tecblic/orbit`  
**Governing Frozen Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`develop`)  
**Consolidation Commit (HEAD):** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`  
**Parent:** `7a1e2fffa5265eb7ce0a444823af8d654a1b8c28`  
**Status:** COMPLETE / READ-ONLY / UNSTAGED  

---

## 1. Executive Verdict

**VERDICT: B — REAL BUT INSUFFICIENT**

### Concise Factual Justification:
The local environment contains extensive REAL Jira evidence (**2,686,282 issues** across 16 public open-source ecosystems in `/home/tecblic/public-jira-lab/mongo-data`) and extensive REAL GitHub evidence (**17 repositories, 229 branches, 406 PRs, and 2,127 commits** in `orbit-private/github-deep-scan-2026-09-15`). However, outside the strictly excluded projects (Mahout, GoGreen, TrueTenant), the local environment contains **exactly ZERO authentic, paired, dereferenceable Jira ↔ GitHub cross-system evidence chains**. The local 17-repository GitHub archive contains 0 Jira ticket references (delivery was conducted out-of-band without Jira issue keys), while the 2.68M public Jira issues have 0 paired local GitHub repository clones or PR dumps in the filesystem.

---

## 2. Audit Scope

The following directories, artifacts, and databases were exhaustively audited in read-only mode:

1. **Local Private Datasets (`/home/tecblic/orbit-private/`):**
   - `github-deep-scan-2026-09-15/`: 17 target repositories in `raw/`, `repository_inventory.json`, `pull_request_analysis.json`, `commit_analysis.json`, `branch_analysis.json`, `jira_traceability.json`, `cross_repository_relationships.json`, `evidence_gaps.json`, `rework_signals.json`, `SHA256SUMS.txt`.
   - `ekfc-cross-context-research/`: `cross_context_validation_report.md`, `cross_system_relationships.json`, `cross_system_conflicts.json`, `github_snapshot.json`, `jira_only_view.json`, `candidate_signals.json`, `SHA256SUMS.txt`.
   - `github-org-discovery/`: `organization_repository_inventory.json`, `project_family_analysis.json`, `candidate_rankings.json`, `human_readable_report.txt`, `engineering_research_candidates.csv`, `scanner.py`, `SHA256SUMS.txt`.
   - Excluded directories inspected only for boundary verification: `mahout/`, `gate2/`, `truetenant/`, `2a/`, `gogreen/`, `gogreen-cross-system-research/`.
2. **Public Jira Dataset Archive (`/home/tecblic/public-jira-lab/mongo-data`):**
   - 15 GB WiredTiger database running via local container `public-jira-mongo` on port `27017`.
   - Database `JiraReposAnon` containing 16 deployment collections: `Apache`, `Spring`, `MongoDB`, `MariaDB`, `Hyperledger`, `JFrog`, `IntelDAOS`, `Qt`, `RedHat`, `Jira`, `Sonatype`, `Mojang`, `Sakai`, `JiraEcosystem`, `Mindville`, `SecondLife`.
3. **Local Standalone Git Repositories (`/home/tecblic/`):**
   - `vexa/` (2,603 commits), `Monitoring-Agent/` (37 commits), `Monitoring-CentralApp/` (23 commits), `project_timesheet/` (2 commits).

---

## 3. Excluded Corpora

In strict compliance with Section 2 of instructions, the following projects and all their derived artifacts were identified and **completely excluded** from candidate evaluation:

| Excluded Project | Scope & Location | Reason for Exclusion |
| :--- | :--- | :--- |
| **Apache Mahout** | `orbit-private/mahout/` (2,121 raw capture issues, 412 qualified subset) | Previously used as primary Pass 4 / Pass 5 qualification baseline. |
| **GoGreen (WMS)** | `orbit-private/gate2/`, `orbit-private/2a/`, `orbit-private/gogreen/`, `orbit-private/gogreen-cross-system-research/`, `/home/tecblic/WareHouseManagement-*`, `/home/tecblic/GoGreeen-React`, `/home/tecblic/Rutuj/GoGreenDjango` | Previously used in Gate 2, Milestone 2A, and Pass 4 research. |
| **TrueTenant** | `orbit-private/truetenant/` (`Jira.csv` with 112 issues, `truetenant_changelog.json` with 1,022 changelogs) | Previously used in Milestone 2 / Pass 4 changelog extraction. |
| **Derived Projections** | `gogreen_first_manual_projection_fixture.json`, `gogreen-cross-system-research/*.json`, `ekfc-cross-context-research/` GoGreen comparison views | Exclusively derived from excluded corpora. |

---

## 4. Candidate Dataset Inventory

The table below catalogs every non-excluded candidate dataset discovered in the local environment:

| Dataset | Provenance | Jira | GitHub | Cross-System | Classification |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **TecblicInternal Deep Scan (ActionEdge, EKFC, Entitle)** | `orbit-private/github-deep-scan-2026-09-15/raw/` (17 repos) | None | 406 PRs, 2,127 commits, 229 branches | 0 authentic links (Snyk CVE bots only) | **REAL BUT INSUFFICIENT** |
| **EKFC Cross-Context Research** | `orbit-private/ekfc-cross-context-research/` | Reconstructed View | Snapshot of 6 EKFC repos | 0 Jira links (`EXPLICIT_DISCONNECTION`) | **RECONSTRUCTED / UNLINKED** |
| **GitHub Org Discovery Inventory** | `orbit-private/github-org-discovery/` (71 repos) | None | High-level API metadata | 0 cross-system links | **REAL BUT INSUFFICIENT** |
| **Public Jira Dataset: Apache (excluding Mahout)** | `mongo-data:JiraReposAnon.Apache` (645 other projects) | 1,012,805 issues | 0 local repos | External URLs in text only; 0 local Git objects | **REAL BUT INSUFFICIENT** |
| **Public Jira Dataset: Spring** | `mongo-data:JiraReposAnon.Spring` (80 projects) | 69,156 issues | 0 local repos | 0 local Git objects | **REAL BUT INSUFFICIENT** |
| **Public Jira Dataset: MongoDB** | `mongo-data:JiraReposAnon.MongoDB` (27 projects) | 137,172 issues | 0 local repos | 0 local Git objects | **REAL BUT INSUFFICIENT** |
| **Public Jira Dataset: MariaDB** | `mongo-data:JiraReposAnon.MariaDB` (11 projects) | 31,229 issues | 0 local repos | 0 local Git objects | **REAL BUT INSUFFICIENT** |
| **Public Jira Dataset: Hyperledger** | `mongo-data:JiraReposAnon.Hyperledger` (32 projects) | 28,146 issues | 0 local repos | 0 local Git objects | **REAL BUT INSUFFICIENT** |
| **Public Jira Dataset: IntelDAOS** | `mongo-data:JiraReposAnon.IntelDAOS` (2 projects) | 9,474 issues | 0 local repos | 0 local Git objects | **REAL BUT INSUFFICIENT** |
| **Public Jira Dataset: Qt, RedHat, Jira, Sonatype, Mojang** | `mongo-data:JiraReposAnon.*` (5 collections) | 1,277,227 issues | 0 local repos | 0 local Git objects | **REAL BUT INSUFFICIENT** |
| **Local Standalone Git: vexa** | `/home/tecblic/vexa` (.git repository) | None | 2,603 commits | ADR mentions only; 0 Jira links | **REAL BUT INSUFFICIENT** |
| **Local Standalone Git: Monitoring-Agent/CentralApp** | `/home/tecblic/Monitoring-*` (.git repositories) | None | 60 commits | 0 Jira links | **REAL BUT INSUFFICIENT** |

---

## 5. Cross-System Relationship Census

A comprehensive regex scan (`\b[A-Z][A-Z0-9]{1,9}-\d+\b`) was executed across all commit messages, branch names, PR titles, PR bodies, and comment threads in the 17-repository GitHub archive (`github-deep-scan-2026-09-15/raw/`):

| Relationship Category | Count | Factual Audit Finding |
| :--- | :---: | :--- |
| **EXPLICIT_LINK** | **0** | No native Jira development panel integration, commit linkage metadata, or webhook payload exists in the raw GitHub captures. |
| **DECLARED_MENTION (Authentic Jira)** | **0** | Exactly **0 authentic Jira ticket keys** exist across all 17 repositories. |
| **DECLARED_MENTION (Automated Security Bots)** | **9** | 9 distinct keys were detected in `jira_traceability.json`, but all 9 are automated security upgrade identifiers generated by Snyk bot: `AXIOS-12613773`, `EXPAT-9459842`, `LIBXML2-10165474`, `LIBXML2-10165475`, `LIBXML2-9380730`, `MULTER-10185673`, `MULTER-10185675`, `OPENSSL-13174134`, `CVE-2025`. None are Jira issues. |
| **RECONSTRUCTED (Analyst/Script)** | **3** | In `ekfc-cross-context-research/cross_system_relationships.json`, 2 relationships are inter-service HTTP/WebSocket linkages (`EKFC-REL-01`, `EKFC-REL-02`), and 1 is an explicit disconnection record (`EKFC-REL-03`). |
| **NO_SUPPORTED_LINK** | **406** | All 406 PRs in the 17-repository archive are unlinked to Jira. |
| **UNKNOWN** | **0** | All discovered references were forensically disambiguated. |

### Relationship Cardinalities:
- One Jira issue → multiple commits: **0**
- One Jira issue → multiple PRs: **0**
- Multiple Jira issues → one commit: **0**
- Multiple Jira issues → one PR: **0**
- One repository → multiple Jira projects: **0**
- One Jira project → multiple repositories: **0**

---

## 6. Jira → GitHub Evidence Chains

The desired evidence pattern is:
```
Jira Work Item → GitHub Branch → Commit(s) → Pull Request → Merge / resulting Code Change
```

### Representative Discovered Chains:

#### Chain 1: TecblicInternal / Entitle Family (Security Bot Upgrade)
```
Vulnerability Identifier: AXIOS-12613773 (Snyk Vulnerability Database, NOT a Jira issue)
  ↓ [bot PR title declared mention]
Branch: snyk-upgrade-axios-1.12.2
  ↓ [git commit]
Commit SHA: (automated package-lock update)
  ↓ [github PR]
Pull Request: TecblicInternal/EntitleP2-FrontEnd #8 ("[Snyk] Upgrade axios from 1.11.0 to 1.12.2")
  ↓ [lifecycle state]
PR State: OPEN / UNMERGED (merged_at = None)
```
*Audit Assessment:* Non-Jira external vulnerability reference; unmerged; cannot support work item state qualification.

#### Chain 2: TecblicInternal / EKFC Family (Manual Engineering PR)
```
Jira Work Item: NONE (Jira keys absent in git history; out-of-band task tracking)
  ↓
Branch: 023-add-food-temperature-anomaly-detector
  ↓
Commit SHA: f39b1a... ("Add temperature threshold validator and SPML exemption handler")
  ↓
Pull Request: TecblicInternal/EKFC-P2-Model #14 ("Add food temperature anomaly detector")
  ↓
PR State: MERGED (merged_at = "2026-06-22T14:10:05Z", merge_commit_sha = "d48e2c...")
```
*Audit Assessment:* Authentic GitHub lifecycle chain, but Jira endpoint is **completely absent**. Evaluates under `ORBIT-XB-01` as unlinked code change, but cannot prove cross-system alignment.

#### Chain 3: Public Jira Dataset / Apache ZooKeeper (External Web URL Reference)
```
Jira Work Item: issues.apache.org:ZOOKEEPER-4424 ("Re-throwing IOException in Leader...")
  ↓ [plain-text description mention]
GitHub PR URL: https://github.com/apache/zookeeper/pull/1596 (text string in description)
  ↓
GitHub Branch / Commit / PR Object: NOT AVAILABLE LOCALLY (No git clone or PR dump on disk)
```
*Audit Assessment:* Authentic Jira issue with external GitHub PR URL in description, but the GitHub endpoint **does not exist locally** and cannot be dereferenced offline under read-only safety rules.

---

## 7. Temporal Evidence

For the non-excluded candidate datasets:

### GitHub Side (`github-deep-scan-2026-09-15`):
- **Commit Timestamps:** Preserved in ISO-8601 (`committer.date`, `author.date`).
- **PR Timestamps:** Preserved (`created_at`, `updated_at`, `closed_at`, `merged_at`).
- **Review Timestamps:** Preserved for the 4 formal reviews captured.
- **Branch Timestamps:** GitHub API does not provide native branch creation timestamps; inferred only from commit history.

### Jira Side (`mongo-data:JiraReposAnon`):
- **Creation Timestamps:** Preserved (`fields.created`).
- **Update Timestamps:** Preserved (`fields.updated`).
- **Resolution Timestamps:** Preserved (`fields.resolutiondate`).
- **Due Dates:** Preserved (`fields.duedate`).
- **Transition Timestamps:** Preserved with millisecond accuracy across all 16 collections in `changelog.histories.created`.

### Cross-System Temporal Correlation:
- **Status:** **INSUFFICIENT TEMPORAL EVIDENCE**. Because no authentic cross-system links exist between the local Jira datasets and the local GitHub datasets, cross-system temporal coherence cannot be evaluated.

---

## 8. Identity / Collision Analysis

The local datasets provide strong evidence for **intra-system** identity isolation, but **zero cross-system** identity links:

1. **GitHub Multi-Repository PR Disambiguation:**
   - PR `#1` exists concurrently in:
     * `TecblicInternal/ActionEdge-Backend`
     * `TecblicInternal/ActionEdge-FrontEnd`
     * `TecblicInternal/ActionEdge-PLC`
     * `TecblicInternal/EKFC`
     * `TecblicInternal/EntitleP2-FrontEnd`
   - In ORBIT, scoping `EntityRef.entity_id` as `{repo_id}/{pr_number}` guarantees complete isolation without collision.
2. **Jira Cross-Site Project Key Collisions:**
   - Project Key `KAFKA` exists in `Apache` (`issues.apache.org`, 12,312 issues) and in `MongoDB` (`jira.mongodb.org`, 258 issues). Issue `KAFKA-1` exists in both independent sites with completely different content. Disambiguated by `SourceInstance.instance_id`.
   - Project Key `ARIES` exists in `Apache` (2,056 issues) and `Hyperledger` (7 issues). Disambiguated by `SourceInstance.instance_id`.

---

## 9. Negative / Ambiguous Evidence

The audit identified significant negative and ambiguous cases in the raw data:

1. **Jira Issues with No GitHub Evidence:**
   - 100% of the 2,686,282 issues in `mongo-data` lack local GitHub evidence.
2. **GitHub PRs with No Jira References:**
   - 100% of the 406 PRs across the 17 TecblicInternal repositories lack Jira references (406 unlinked PRs).
3. **Ambiguous Lexical References (Snyk Security Bots):**
   - Strings matching `[A-Z]+-[0-9]+` in PR titles (e.g. `AXIOS-12613773`) mimic Jira issue keys, but represent external vulnerability database keys. A naive regex linker would generate false positive Jira links.
4. **Out-of-Band Engineering Governance:**
   - The EKFC, ActionEdge, and Entitle repositories reveal an engineering culture where task tracking was either managed verbally/out-of-band or in an unintegrated system, resulting in zero traceability in Git logs.

---

## 10. Provenance Traceability

Five representative records were traced to test source-level dereferencing:

| Trace ID | Target Entity / Edge | Relationship Artifact | Raw Source Document | Dereferencing Status |
| :--- | :--- | :--- | :--- | :--- |
| **TRACE-01** | `EntitleP2-FrontEnd/8` (PR) | `pull_request_analysis.json` | `raw/EntitleP2-FrontEnd/pull_8.json` | **RESOLVED** (Local raw JSON verified) |
| **TRACE-02** | `AXIOS-12613773` → PR #8 | `jira_traceability.json` | `raw/EntitleP2-FrontEnd/pull_8.json` | **RESOLVED** as Bot Mention (Not Jira) |
| **TRACE-03** | `EKFC-P2-Model/14` (PR) | `ekfc-cross-context-research` | `raw/EKFC-P2-Model/pull_14.json` | **RESOLVED** (Local raw JSON verified) |
| **TRACE-04** | `ZOOKEEPER-4424` (Jira) | `mongo-data:JiraReposAnon.Apache` | WiredTiger Document ID: `ZOOKEEPER-4424` | **RESOLVED** (Local MongoDB verified) |
| **TRACE-05** | `ZOOKEEPER-4424` → PR #1596 | Jira issue description URL | Local filesystem: `/home/tecblic/` | **NOT FOUND / UNAVAILABLE** (PR not stored locally) |

---

## 11. ORBIT Proving Suitability (Levels 1–10)

Evaluation of candidate non-excluded datasets against the 10-level ORBIT progression:

| Level | Progression Level | Current Local Evidence Support | Status |
| :--- | :--- | :--- | :--- |
| **Level 1** | Explicit Jira ↔ GitHub links | 0 native links exist in candidate datasets | **NOT SUPPORTED** |
| **Level 2** | Declared mentions in branches/commits/PRs | 0 authentic Jira ticket mentions in candidate repos | **NOT SUPPORTED** |
| **Level 3** | One-to-many relationships | None observable in candidate repos | **NOT SUPPORTED** |
| **Level 4** | Many-to-one relationships | None observable in candidate repos | **NOT SUPPORTED** |
| **Level 5** | Unlinked Jira and GitHub evidence | Abundant: 406 unlinked PRs, 2.68M unlinked Jira issues | **SUPPORTED** |
| **Level 6** | Ambiguous relationships | Snyk CVE references mimic Jira keys | **SUPPORTED** |
| **Level 7** | Temporal alignment | Timestamps exist independently, but no cross-system pairs | **NOT SUPPORTED** |
| **Level 8** | Cross-repository identity | 17 repos with dense overlapping PR numbers | **SUPPORTED** |
| **Level 9** | Identifier collisions | Project `KAFKA` and `ARIES` collide across MongoDB collections | **SUPPORTED** |
| **Level 10** | Deterministic multi-system evaluation | Cannot evaluate end-to-end without paired evidence | **NOT SUPPORTED** |

---

## 12. Data Integrity / Hashes

Available SHA-256 checksums for audited candidate datasets:

- `github-deep-scan-2026-09-15/SHA256SUMS.txt`:
  * `branch_analysis.json`: `eb350aae1a058f115fcd038e87c5576cb0f0358b965086deb780545d8e9736fe`
  * `commit_analysis.json`: `bbd53d77ca73bf8b855814f28f885934ba50033b39fec0253216589072a0aab8`
  * `jira_traceability.json`: `e8f1a02e75ea6e919ec41a63ce3a7e6afb60a0a17abf80b1f2886397ad4dd366`
  * `pull_request_analysis.json`: `c53cd4cb312f5accda83a782a56263ec93a535aeba3e66b18b166d3c46c3363b`
  * `repository_inventory.json`: `aa341ea75a8fb7ace95439a4fa67f27b84ffb658cbdfaf434901a9d6b914cf7c`
- `ekfc-cross-context-research/SHA256SUMS.txt`:
  * `cross_system_relationships.json`: `9522160d46cf20b8936d92aa79a98ae27c0dee2f991e7e57daf534b3f334cf91`
  * `jira_only_view.json`: `26ddb6a8677a98a17c66b695a6bfc23f53731d899504aaf83226eba11d460df6`
- `github-org-discovery/SHA256SUMS.txt`:
  * `organization_repository_inventory.json`: `0daaf68111f2bb1435e2f410e0b18a095ea8d9ebb2276135a5347bdb270f96cb`

---

## 13. Protected Baseline Verification

All protected ORBIT baselines and invariants were verified in read-only mode:

| Invariant | Protected Value | Observed Value | Match? |
| :--- | :--- | :--- | :--- |
| **Governing Baseline** | `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`develop`) | `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` | **YES** |
| **Consolidation HEAD** | `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab` | `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab` | **YES** |
| **Track A Diff** | 0 bytes (`evaluation`, `temporal`, `normalization`, `types`) | `0 bytes` | **YES** |
| **Fixtures Diff** | 0 bytes (`fixtures/`) | `0 bytes` | **YES** |
| **Mahout Invariants** | 2,121 source / 412 selected / 12 stalled / 0 mutations | Exact match (`run_mahout_qualification(save_golden=False)`) | **YES** |
| **GoGreen Artifacts** | Unchanged | Verified untouched | **YES** |
| **TrueTenant Artifacts** | Unchanged | Verified untouched | **YES** |

---

## 14. Missing Evidence

The following evidence is strictly absent from the local environment:

1. **Jira Issue Captures for Local GitHub Repositories:**
   No Jira exports, raw captures, or changelog files exist locally for `ActionEdge`, `EKFC`, or `Entitle`.
2. **Jira Ticket References in Local GitHub Commits/PRs:**
   No commit messages, branch names, or PR titles in the 17-repository archive reference Jira tickets.
3. **Local GitHub Captures for Public Jira Projects:**
   No Git repository clones, commit trees, or pull request dumps exist locally for any of the 646 Apache projects (e.g. ZooKeeper, Parquet, Kafka, Camel) or 80 Spring projects in `mongo-data`.
4. **Native Jira ↔ GitHub Integration Telemetry:**
   No Jira development panel metadata, GitHub app integration events, or commit link payloads exist in the non-excluded datasets.

---

## 15. Next-Gate Recommendation

**RECOMMENDATION: PUBLIC DATASET SEARCH REQUIRED**

### Rationale:
Local reconnaissance conclusively establishes that the local filesystem does **not** contain an authentic, previously-unused, paired Jira ↔ GitHub cross-system dataset. Real Jira data exists in abundance (2.68M issues), and real multi-repo GitHub data exists (17 repos), but they are disjoint. 

To acquire a genuine cross-system proving corpus without resorting to artificial synthetic generation:
1. Conduct an authorized search for publicly available paired Jira ↔ GitHub datasets (e.g. Apache software projects that maintain public Jira instances paired with public GitHub mirrors containing explicit `PROJECT-123` PR/commit conventions).
2. Once an authentic public pair is identified, provision the corresponding GitHub PR/commit dump locally.
3. If public pairing reveals gaps in specific edge cases (such as inverted temporal order or ambiguous linkage), apply **controlled synthetic augmentation** only as a secondary step.
