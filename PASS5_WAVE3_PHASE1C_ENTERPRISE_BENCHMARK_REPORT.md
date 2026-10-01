# Project ORBIT — Pass 5 / Wave 3 / Phase 1C
## Enterprise Multi-Project Benchmark Execution Report

**Corpus ID:** `ORBIT-QUAL-WAVE3-APACHE-REAL-001`  
**Execution Timestamp:** `2026-09-30T13:10:00Z`  
**Final Classification:** **`PHASE 1C VERIFIED`**

---

## 1. Executive Summary

Phase 1C executes the **Controlled Multi-Project Proving / Enterprise Benchmark Execution** for Project ORBIT Pass 5 / Wave 3. Operating strictly under read-only proving governance, this benchmark quantitatively evaluates the existing ORBIT canonical evidence pipeline and Track B evaluator against authentic, immutable Apache Jira and GitHub artifacts acquired in Phase 1A and canonically adapted in Phase 1B.

### Key Headline Results
1. **Zero Provider Leakage:** Evaluator executed across all five real enterprise linkage patterns and negative controls with strictly **0 instantiations** of `JiraIssueState` or `GitHubPullRequestState` and **0 provider-specific evaluator semantics**.
2. **100% Provenance Resolution:** All 21 canonical observations resolve directly to immutable raw source records (21/21 `RESOLVED`, 0 `UNAVAILABLE`, 0 `NOT_FOUND`, 0 `INVALID`).
3. **Zero Structural Quality Issues:** Evidence bundle validation via `validate_evidence_bundle` yielded **0 QualityIssues**.
4. **100% Deterministic Reproducibility:** Multi-cycle benchmark execution produced **byte-for-byte identical output digests** across independent runs and passed permutation invariance tests.
5. **100% Negative Control Isolation:** 3 unlinked negative controls remained completely isolated (0 relationships, 0 alignments, 0 findings) and 1 bot vulnerability token (`AXIOS-12613773`) was rejected with 0 Jira WorkItemRefs created.
6. **Zero Regression:** All 783 repository unit and acceptance tests passed; Track A code diff is strictly 0 bytes; historical fixtures diff is strictly 0 bytes; all 11 Mahout qualification invariants remain 100% preserved.

---

## 2. Governing Baseline & Repository State

| Baseline Dimension | Reference / Value | Status |
| :--- | :--- | :--- |
| **Governing Frozen Baseline** | `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`develop`) | Preserved |
| **Pass 5 Consolidation HEAD** | `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab` (`remediation/pass3-controlled-hardening`) | Unmodified |
| **Track A Code Diff** | `git diff 7a1e2ff..HEAD -- src/shadow_orbit/{evaluation,temporal,normalization,types}.py` | **0 bytes** |
| **Historical Fixtures Diff** | `git diff HEAD -- fixtures/` | **0 bytes** |
| **Working Tree Status** | No staging (`git add`), no commits, no resets, no rebases | **Clean** |

---

## 3. Source Counts & Cardinality Invariants

In accordance with strict qualification boundary rules, the distinction between raw acquired artifacts and canonical observations is explicitly maintained without reconciliation or collapse:

| Category | Component | Count | Invariant Status |
| :--- | :--- | :--- | :--- |
| **Raw Acquired Artifacts** | Target Jira Issues | 6 | Preserved (Immutable) |
| | Target GitHub PRs | 7 | Preserved (Immutable) |
| | Target GitHub Commit Arrays | 7 | Preserved (Immutable) |
| | Target GitHub Review Arrays | 7 | Preserved (Immutable) |
| | Negative Control Artifacts | 4 | Preserved (Immutable) |
| | **Total Raw Acquired Artifacts** | **31** | **Exact Match** |
| **Canonical Observations** | Canonical `WorkItemState` (6 targets + 2 neg) | 8 | Derived via pure adapter |
| | Canonical `CodeChangeState` PRs (7 targets + 1 neg) | 8 | Derived via pure adapter |
| | Canonical `CodeChangeState` Commits (Chain 2 review) | 5 | Derived via pure adapter |
| | **Total Canonical Observations** | **21** | **Exact Match** |
| **Canonical Linkages** | Evidence Relationships (1 mentions, 7 links, 5 commits) | 13 | Derived via pure adapter |
| | Cross-System State Alignments | 8 | Derived via pure adapter |

---

## 4. Five Real Enterprise Linkage Patterns — Proving Results

```
[Chain 1: PARQUET-2010] ──(Declared Mention)──▶ [PR #885 (Merged)] ───▶ CONSISTENT / COHERENT (+1h 18m)
[Chain 2: KAFKA-13557]  ──(Explicit Link)────▶ [PR #11617 + 5 Commits] ▶ CONSISTENT / COHERENT (+37s)
[Chain 3: AVRO-3234]    ──(Explicit Link)────▶ [PR #1370 (Deleted Fork)]▶ CONSISTENT / COHERENT (+56s)
[Chain 4: FLINK-24409]  ──(Multi-PR Lifecycle)─┬▶ [PR #17401 (Abandoned)] ▶ INSUFFICIENT_EVIDENCE / INDETERMINATE
                                              ├▶ [PR #17773 (Master)]    ▶ CONSISTENT / COHERENT
                                              └▶ [PR #17799 (Backport)]  ▶ CONSISTENT / COHERENT
[Chain 5: FLINK-14386]  ─┬(CLI Merge Commit)──▶ [PR #10123 (Closed GH)]  ▶ INSUFFICIENT_EVIDENCE / INDETERMINATE
[Chain 5: FLINK-14665]  ─┘
```

### Detailed Chain Forensic Results

#### Chain 1: Parquet Japicmp Compatibility Fix (`PARQUET-2010` ↔ `apache/parquet-java#885`)
- **Pattern:** One-to-One Declared Mention (`DECLARED_MENTION`).
- **Jira Status:** `Resolved` (`status_category="done"`, resolved at `2021-03-30T17:15:17Z`).
- **GitHub PR Status:** `merged` (`merged_at="2021-03-30T15:57:08Z"`).
- **Linkage Source:** Lexical mention in PR title (`PARQUET-2010: Exclude shaded netty from japicmp check`). Jira has 0 remote issue links.
- **State Alignment:** `CONSISTENT` (Work item done, code change merged).
- **Temporal Alignment:** `COHERENT` (PR merged 4,689 seconds / 1h 18m prior to Jira resolution).
- **Track B Findings:** 0 findings triggered.

#### Chain 2: Kafka Raft Implementation Cleanup (`KAFKA-13557` ↔ `apache/kafka#11617`)
- **Pattern:** One-to-Many Commits (`ONE_TO_MANY_COMMITS`).
- **Jira Status:** `Resolved` (`status_category="done"`, resolved at `2022-01-11T20:13:21Z`).
- **GitHub PR Status:** `merged` (`merged_at="2022-01-11T20:12:44Z"`).
- **Associated Commits:** 5 distinct review iteration commits mapped to `CodeChangeState` with `state="committed"`, `merged_at=None`, and `structural_association` relationships to PR.
- **Linkage Source:** Explicit Jira `remotelink` (13 links in raw Jira issue).
- **State Alignment:** `CONSISTENT` (Work item done, code change merged).
- **Temporal Alignment:** `COHERENT` (PR merged 37 seconds prior to Jira resolution).
- **Track B Findings:** 0 findings triggered.

#### Chain 3: Avro Schema Evolution and Serialization (`AVRO-3234` ↔ `apache/avro#1370`)
- **Pattern:** One-to-One Explicit Link with Post-Merge Deleted Contributor Fork.
- **Jira Status:** `Resolved` (`status_category="done"`, resolved at `2021-10-18T10:20:11Z`).
- **GitHub PR Status:** `merged` (`merged_at="2021-10-18T10:19:15Z"`).
- **Fork Disambiguation:** Head repository fork (`K-Phoen/avro`) was deleted following merge; canonical identity anchored to base upstream (`apache/avro`).
- **Linkage Source:** Explicit Jira `remotelink` (8 links in raw Jira issue).
- **State Alignment:** `CONSISTENT` (Work item done, code change merged).
- **Temporal Alignment:** `COHERENT` (PR merged 56 seconds prior to Jira resolution).
- **Track B Findings:** 0 findings triggered.

#### Chain 4: Flink KafkaSourceReaderMetrics Multi-PR Lifecycle (`FLINK-24409` ↔ 3 PRs)
- **Pattern:** One-to-Many PR Lifecycle (`ONE_TO_MANY_PRS`).
- **Jira Status:** `Resolved` (`status_category="done"`, resolved at `2021-11-17T16:57:13Z`).
- **Sub-Target 1 (`PR #17401`):** Abandoned / Superseded PR. `state="closed"`, `merged=False`, `merged_at=None`.
  - State Comparison: `INSUFFICIENT_EVIDENCE` (closed without merge).
  - Temporal Comparison: `INDETERMINATE`.
- **Sub-Target 2 (`PR #17773`):** Master branch merge. `state="merged"`, `merged=True`, `merged_at="2021-11-26T01:33:43Z"`.
  - State Comparison: `CONSISTENT`.
  - Temporal Comparison: `COHERENT`.
- **Sub-Target 3 (`PR #17799`):** Release-1.14 backport PR. `state="merged"`, `merged=True`, `merged_at="2021-11-17T16:45:29Z"`.
  - State Comparison: `CONSISTENT`.
  - Temporal Comparison: `COHERENT` (merged 11m 44s prior to Jira resolution).
- **Track B Findings:** 0 findings triggered.

#### Chain 5: Flink Command-Line Merge (`FLINK-14386` + `FLINK-14665` ↔ `apache/flink#10123`)
- **Pattern:** Many-to-One PR (`MANY_TO_ONE_PR`) with Command-Line Merge.
- **Jira Status:** Both `Closed` (`status_category="done"`).
- **GitHub PR Status:** `state="closed"`, `merged=False`, `merged_at=None`. CLI merge commit `21c9b1d899c3afbca09d7409e3512ea3dc29e939` preserved in `extra_properties`.
- **Alignments:**
  - `FLINK-14386` ↔ PR #10123: State: `INSUFFICIENT_EVIDENCE`, Temporal: `INDETERMINATE`.
  - `FLINK-14665` ↔ PR #10123: State: `INSUFFICIENT_EVIDENCE`, Temporal: `INDETERMINATE`.
- **Track B Findings:** 0 findings triggered.

---

## 5. Negative Controls Forensic Evaluation

Four negative controls were tested to prove the pipeline resists spurious linkage, bot noise, and hallucinated alignment:

| Negative Control ID | Nature of Control | Pipeline Behavior | Final Status |
| :--- | :--- | :--- | :--- |
| **`PARQUET-1812`** | Real Jira issue in `to_do` category with no GitHub links | Emitted as canonical `WorkItemState`; 0 relationships, 0 alignments, 0 findings | **`ISOLATED`** |
| **`ZOOKEEPER-4348`** | Real Jira issue in `to_do` category with no GitHub links | Emitted as canonical `WorkItemState`; 0 relationships, 0 alignments, 0 findings | **`ISOLATED`** |
| **`apache/parquet-java#3822`** | Real GitHub PR referencing only GitHub Issue `GH-3792` | Emitted as canonical `CodeChangeState`; 0 relationships, 0 alignments, 0 findings | **`ISOLATED`** |
| **`AXIOS-12613773`** | Snyk bot PR title mentioning CVE/vulnerability token | Key validator `is_valid_apache_jira_key` rejected token; 0 WorkItemRefs created | **`REJECTED`** |

- **Total Negative Controls:** 4
- **Isolation / Rejection Rate:** 100% (4/4)
- **Spurious Findings Emitted:** **0**

---

## 6. Provenance Dereferencing & Structural Validation Metrics

All canonical observations were verified against their raw source records using ORBIT's in-memory provenance dereferencing engine:

| Metric | Measured Value | Threshold / Target | Status |
| :--- | :--- | :--- | :--- |
| **Total Observations Checked** | 21 | 21 | Exact Match |
| **`RESOLVED`** | 21 (100.0%) | 100.0% | **PASS** |
| **`UNAVAILABLE`** | 0 (0.0%) | 0.0% | **PASS** |
| **`NOT_FOUND`** | 0 (0.0%) | 0.0% | **PASS** |
| **`INVALID`** | 0 (0.0%) | 0.0% | **PASS** |
| **Bundle Quality Issues** | 0 | 0 | **PASS** |

---

## 7. State & Temporal Distribution Metrics

Across the 8 cross-system alignments evaluated by Track B:

### State Comparison Distribution
- **`CONSISTENT`:** 5 (62.5%) — Chains 1, 2, 3, 4(master), 4(backport)
- **`INSUFFICIENT_EVIDENCE`:** 3 (37.5%) — Chain 4(abandoned), Chain 5(`FLINK-14386`), Chain 5(`FLINK-14665`)
- **`CONFLICTING`:** 0 (0.0%)

### Temporal Comparison Distribution
- **`COHERENT`:** 5 (62.5%) — Chains 1, 2, 3, 4(master), 4(backport)
- **`INDETERMINATE`:** 3 (37.5%) — Chain 4(abandoned), Chain 5(`FLINK-14386`), Chain 5(`FLINK-14665`)
- **`INVERTED`:** 0 (0.0%)

### Track B Evaluator Findings
- **Findings Triggered:** 0
- **Findings Suppressed:** 0
- **Rules Evaluated:** `ORBIT-XB-01`, `ORBIT-XB-02`, `ORBIT-XB-03`

---

## 8. Deterministic Serialization & Repeatability Audit

To verify that the canonical adaptation and evaluation pipeline is completely deterministic and free of nondeterminism (such as hash randomization, unordered iterations, or unstable dict ordering), a two-cycle independent execution and a permutation invariance test were conducted:

| Artifact | SHA-256 Digest |
| :--- | :--- |
| `bundle_canonical.json` | `db0fd630c4e02fed15298e0af880d21758592d295e2d667b4626bb03a5f82044` |
| `evaluation_result.json` | `e7d0bcc961cbd0034774ec6478a4c44d554fa9e8f8d70051a1e5938c03082e02` |
| `chain_results.json` | `ebc9d28fd05265b4a6362c6396171797371aa9ed207e5773ebd40bd4913dc7af` |
| `negative_control_results.json` | `4008db7056c9950b044dff7324e2627de492042fbb82d039ee7e0a7dee71837f` |
| `benchmark_metrics.json` | `841e968a6142fe0dd660e2548865e944669f1b0c64439c1763a80f2f9ec3cd1f` |

- **Multi-Cycle Comparison:** `Run 1 SHA == Run 2 SHA` is **`True`** (Byte-for-byte identical).
- **Permutation Invariance:** Observations reversed and shuffled in input bundle yielded identical serialized evaluation results.

---

## 9. Provider-Leakage Adversarial Proof

An adversarial test was executed wherein `JiraIssueState.__init__` and `GitHubPullRequestState.__init__` were intercepted with raising mocks during Track B evaluation of the Apache corpus:
- **`JiraIssueState` constructor calls:** 0
- **`GitHubPullRequestState` constructor calls:** 0
- **Exceptions raised:** 0
- **Conclusion:** Proves conclusively that the canonical evaluator branch is strictly isolated from legacy Jira/GitHub evaluator data models when processing canonical observations.

---

## 10. Regression Invariants Verification

| Gate / Test Suite | Scope | Expected | Actual | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Track A Zero Diff** | `evaluation.py`, `temporal.py`, `normalization.py`, `types.py` | 0 bytes | 0 bytes | **PASS** |
| **Fixtures Zero Diff** | `fixtures/` | 0 bytes | 0 bytes | **PASS** |
| **Mahout Invariants** | Pipeline test (`test_mahout_real_data_pipeline.py`) | 412 / 0 / 12 / 0 / Repeatable | 412 / 0 / 12 / 0 / Repeatable | **PASS** |
| **Full Repository Test Suite** | All unit and qualification tests (`pytest tests/`) | 783 passed, 0 failed, 3 warnings | 783 passed, 0 failed, 3 warnings | **PASS** |

---

## 11. Limitations & Findings

1. **Bounded Offline Proving Corpus:** The corpus consists of 31 raw records and 21 canonical observations across 5 real Apache multi-project patterns and 4 negative controls. It does not encompass live network synchronization or streaming webhooks.
2. **Command-Line Merge Handling in Chain 5:** In Apache Flink PR #10123, the maintainers merged the PR via command-line git push (`21c9b1d899c3afbca09d7409e3512ea3dc29e939`), causing GitHub to mark the PR as `closed` rather than `merged`. ORBIT preserves this CLI merge commit SHA in `extra_properties`. Under current Track B rules, the closed unmerged PR results in `INSUFFICIENT_EVIDENCE` and `INDETERMINATE`. This is mathematically faithful to the observed GitHub API state and avoids introducing unprincipled provider heuristics.
3. **No Dynamic Plugin Infrastructure:** All canonical adaptation is performed by pure adapter functions without dynamic runtime classloading or external service registries.

---

## 12. Final Classification

In accordance with the objective criteria defined in Phase 1C:
- All 5 target enterprise patterns executed through canonical models and Track B evaluator.
- 0 provider-specific evaluator semantics or constructor leaks occurred.
- 100% of negative controls remained isolated or rejected.
- Deterministic reproducibility and permutation invariance were proven.
- All 783 regression tests passed and Track A diff is 0 bytes.

Final Classification:
### **`PHASE 1C VERIFIED`**

---
*End of Phase 1C Enterprise Benchmark Execution Report.*
