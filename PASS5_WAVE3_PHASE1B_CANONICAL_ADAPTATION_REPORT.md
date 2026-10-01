# Pass 5 / Wave 3 — Phase 1B: Canonical Normalization & Evidence Adaptation Report

**Classification:** **`PHASE 1B VERIFIED`**  
**Date:** 2026-09-30  
**Repository:** `/home/tecblic/orbit`  
**Governing Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`develop`)  
**Consolidation HEAD:** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`  
**Working Branch:** `remediation/pass3-controlled-hardening`  

---

## 1. Executive Summary

Phase 1B has constructed a non-destructive, offline canonical adaptation layer for the 31 verified Apache Jira and GitHub artifacts acquired in Phase 1A. All 31 artifacts have been projected into ORBIT's canonical evidence models—[`WorkItemState`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py#L400-L457), [`CodeChangeState`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py#L459-L537), and [`CrossSystemStateAlignment`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py#L699-L745)—and executed through the existing Track B evidence evaluator [`evaluate_evidence_bundle`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_evaluation.py#L200-L300) without altering evaluator semantics or introducing provider-specific rules.

### Key Verification Metrics
| Invariant / Check | Expected | Actual | Status |
| :--- | :--- | :--- | :--- |
| **Track A Diff** | 0 bytes (`evaluation.py`, `temporal.py`, `normalization.py`, `types.py`) | 0 bytes | **PASS** |
| **Historical Fixtures Diff** | `git diff HEAD -- fixtures/` strictly empty | 0 bytes | **PASS** |
| **Mahout Qualification Invariants** | Accepted: 412, Quarantined: 0, STALLED_WORK: 12, Mutations: 0, Repeatable: True | Accepted: 412, Quarantined: 0, STALLED_WORK: 12, Mutations: 0, Repeatable: True | **PASS** |
| **Pre-Wave Semantic Baseline** | `2b23afaccbeb5cb512a08c0dbad08dec24612e3db5e690ea89dd4fddb7ff7b7c` | `2b23afaccbeb5cb512a08c0dbad08dec24612e3db5e690ea89dd4fddb7ff7b7c` | **PASS (100% Match)** |
| **Canonical Bundle Digest** | Distinct new Apache corpus digest | `db0fd630c4e02fed15298e0af880d21758592d295e2d667b4626bb03a5f82044` | **PASS** |
| **Canonical Evaluation Digest** | Distinct new Apache evaluation digest | `e7d0bcc961cbd0034774ec6478a4c44d554fa9e8f8d70051a1e5938c03082e02` | **PASS** |
| **Bundle Validation** | `validate_evidence_bundle(bundle, fixtures_by_id)` QualityIssues count | 0 issues | **PASS** |
| **Provider Leakage Proof** | Evaluator runs with `JiraIssueState` and `GitHubPullRequestState` disabled | 0 legacy constructor calls; 0 exceptions | **PASS** |
| **Unit Test Suite** | 21 new unit tests passing; 783 total repository tests passing | 21/21 new passed; 783/783 total passed | **PASS** |

---

## 2. Git State Verification

State checked prior to and during implementation:

```bash
git rev-parse HEAD:        ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab
git rev-parse develop:     6d82d123f8bf50316d2b1ab7a025bc5862a474ed
git merge-base HEAD develop: 6d82d123f8bf50316d2b1ab7a025bc5862a474ed
git status --short:        clean (no tracked modifications)
```

No git staging (`git add`), commits (`git commit`), rebases, resets, or merges were performed. The working directory remains completely uncommitted in accordance with Phase 1B hard governance.

---

## 3. Adapter Architecture

The adapter layer is isolated in [`qualification/wave3/apache_real/adapters/`](file:///home/tecblic/orbit/qualification/wave3/apache_real/adapters/):

```text
qualification/wave3/apache_real/adapters/
├── __init__.py                  # Public exports and contracts
├── apache_jira_adapter.py       # Raw Jira JSON -> WorkItemState & EvidenceObservation
├── apache_github_adapter.py     # Raw GitHub PR/commit JSON -> CodeChangeState & EvidenceObservation
├── apache_alignment_adapter.py  # Generic CrossSystemStateAlignment builder
└── apache_bundle_builder.py     # Deterministic EvidenceBundle orchestrator
```

### Separation of Concerns
- **Adapter Knows:** Apache project keys (`PARQUET`, `KAFKA`, `AVRO`, `FLINK`, `ZOOKEEPER`), `issues.apache.org`, GitHub mirror repository paths (`apache/parquet-java`, `apache/kafka`, etc.), raw PR attributes, and commit arrays.
- **Evaluator Knows:** Strictly provider-neutral [`WorkItemState`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py#L400-L457), [`CodeChangeState`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py#L459-L537), and generic [`CrossSystemStateAlignment`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py#L699-L745). Zero references to Apache project names or vendor-specific REST keys.

---

## 4. Canonical Mapping Table

### A. Jira Issue → `WorkItemState`
| Raw Jira Field | Canonical `WorkItemState` Attribute | Semantics / Transformation |
| :--- | :--- | :--- |
| `key` | `key`, `.identifier` | Preserved (e.g. `"PARQUET-2010"`). Validated against Apache allowlist. |
| `fields.status.statusCategory.key` | `status_category` | `"done"` -> `"done"`, `"new"` -> `"to_do"`, `"indeterminate"` -> `"in_progress"`. |
| `fields.status.name` | `source_status` | Preserved verbatim (e.g. `"Resolved"`, `"Closed"`, `"Open"`). |
| `fields.created` | `created_at` | Timezone-aware UTC `datetime`. Missing raises `ValueError`. |
| `fields.updated` | `updated_at` | Timezone-aware UTC `datetime`. |
| `fields.resolutiondate` | `resolved_at` | Timezone-aware UTC `datetime` or `None` if unresolved. |
| `fields.duedate` | `due_at` | Preserved if present; `None` if unassigned. Never manufactured. |
| `fields.priority.name` | `source_priority`, `priority_band` | `"Blocker"` -> `"high"`, `"Major"` -> `"medium"`, Minor/Trivial -> `"low"`. |
| `fields.assignee` | `assignee` | `displayName` or `name` string; `None` if unassigned. Never manufactured. |
| `project.key`, `id`, `summary`, `changelog` | `extra_properties` | Preserved losslessly in `extra_properties` mapping. |

### B. GitHub Pull Request → `CodeChangeState`
| Raw GitHub Field | Canonical `CodeChangeState` Attribute | Semantics / Transformation |
| :--- | :--- | :--- |
| `number` | `identifier` | Converted to string (e.g. `"885"`). |
| Hardcoded | `change_type` | `"pull_request"`. |
| `merged` & `merged_at` & `state` | `state` | **Rule 6:** `"merged"` iff `merged == True` AND `merged_at != None`. If `state == "closed"` and `merged == False`, state is strictly `"closed"`. |
| `merged_at` | `merged_at` | Exact UTC timestamp if merged; strictly `None` if unmerged. |
| **Inferred from commit** | `committed_at` | **Rule 7:** Strictly `None` on PR entities. Commits have committed_at. PRs do not. |
| `created_at`, `closed_at` | `created_at`, `extra_properties['closed_at']` | Timezone-aware UTC `datetime`. |
| `user.login` | `author` | String user login. |
| `head.ref` / `base.ref` | `source_branch` / `target_branch` | Preserved branch ref names. |
| `head.sha` / `base.sha` | `head_commit_sha` / `base_commit_sha` | Preserved git commit hashes. |
| `base.repo.full_name` | `extra_properties['repo']` | Canonical upstream repo (e.g. `"apache/parquet-java"`). |
| `head.repo.full_name` | `extra_properties['head_repo']` | Fork repo (e.g. `"gszadovszky/parquet-mr"`). |
| `merge_commit_sha` | `extra_properties['merge_commit_sha']` | Preserved observed merge commit hash (e.g. CLI merge for PR 10123). |

### C. GitHub Commit → `CodeChangeState`
| Raw GitHub Commit Field | Canonical `CodeChangeState` Attribute | Semantics / Transformation |
| :--- | :--- | :--- |
| `sha` | `identifier` | Commit SHA string. |
| Hardcoded | `change_type`, `state` | `change_type="commit"`, `state="committed"`. |
| `commit.committer.date` | `committed_at` | UTC `datetime` when code was committed. |
| **Merge timestamp** | `merged_at` | Strictly `None`. A commit is not a merge. |
| `commit.message` | `title` | First line of commit message. |
| `author.login` | `author` | Author login or git author name. |

---

## 5. Five-Chain Canonical Representation

All 5 multi-project cross-system linkage patterns established in Phase 1A are canonically represented and verified:

```text
CHAIN 1: PARQUET-2010 ↔ apache/parquet-java#885
├── Linkage: DECLARED_MENTION (lexical_match; 0 RemoteIssueLinks in Jira)
├── Lifecycle State: Jira Resolved / PR Merged
├── Temporal Order: PR Merged (15:57:08Z) <= Jira Resolved (17:15:17Z)
└── Alignments: state_comparison=CONSISTENT, temporal_comparison=COHERENT

CHAIN 2: KAFKA-13557 ↔ apache/kafka#11617
├── Linkage: EXPLICIT_LINK (explicit_metadata; 13 native RemoteIssueLinks)
├── Commits: 5 review commits (Cardinality: ONE_TO_MANY_COMMITS)
├── Lifecycle State: Jira Resolved / PR Merged
├── Temporal Order: PR Merged (20:12:44Z) <= Jira Resolved (20:13:21Z)
└── Alignments: state_comparison=CONSISTENT, temporal_comparison=COHERENT

CHAIN 3: AVRO-3234 ↔ apache/avro#1370
├── Linkage: EXPLICIT_LINK (explicit_metadata; 8 native RemoteIssueLinks)
├── Fork Handling: Head fork deleted post-merge; base repo (apache/avro) is canonical
├── Lifecycle State: Jira Resolved / PR Merged
├── Temporal Order: PR Merged (10:19:15Z) <= Jira Resolved (10:20:11Z)
└── Alignments: state_comparison=CONSISTENT, temporal_comparison=COHERENT

CHAIN 4: FLINK-24409 ↔ apache/flink PRs #17401, #17773, #17799
├── Linkage: EXPLICIT_LINK (Cardinality: ONE_TO_MANY_PRS)
├── PR #17401: Abandoned unmerged (state=closed, merged=False)
│   └── Alignment: state_comparison=INSUFFICIENT_EVIDENCE, temporal_comparison=INDETERMINATE
├── PR #17773: Merged to master (state=merged, merged_at=2021-11-26 01:33:43Z)
│   └── Alignment: state_comparison=CONSISTENT, temporal_comparison=COHERENT
└── PR #17799: Merged to release-1.14 (state=merged, merged_at=2021-11-17 16:45:29Z)
    └── Alignment: state_comparison=CONSISTENT, temporal_comparison=COHERENT

CHAIN 5: FLINK-14386 + FLINK-14665 ↔ apache/flink#10123
├── Linkage: EXPLICIT_LINK (Cardinality: MANY_TO_ONE_PR)
├── PR #10123: Closed unmerged on GitHub (state=closed, merged=False)
│   └── CLI Merge Commit: 21c9b1d899c3afbca09d7409e3512ea3dc29e939 preserved
└── Alignments:
    ├── FLINK-14386 ↔ PR 10123: state_comparison=INSUFFICIENT_EVIDENCE, temporal_comparison=INDETERMINATE
    └── FLINK-14665 ↔ PR 10123: state_comparison=INSUFFICIENT_EVIDENCE, temporal_comparison=INDETERMINATE
```

---

## 6. Negative Controls & Rejection Verification

### Negative Controls (Unlinked Entities)
1. **`PARQUET-1812`** (Unlinked Jira Issue): Present in observations; 0 relationships; 0 alignments.
2. **`ZOOKEEPER-4348`** (Unlinked Jira Issue): Present in observations; 0 relationships; 0 alignments.
3. **`apache/parquet-java#3822`** (Unlinked GitHub PR referencing GH-3792): Present in observations; 0 relationships; 0 alignments.
- **Anti-Cartesian Enforcement:** When evaluated by [`evaluate_evidence_bundle`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_evaluation.py#L200-L300), these unlinked entities produce **0 candidate pairs** and **0 spurious findings**.

### Snyk Bot / Vulnerability Identifier Rejection
- **Artifact:** `negative_controls/github/snyk_bot/pull_8.json`
- **Identifier:** `AXIOS-12613773` (from `SNYK-JS-AXIOS-12613773`)
- **Verification:** [`is_valid_apache_jira_key("AXIOS-12613773")`](file:///home/tecblic/orbit/qualification/wave3/apache_real/adapters/apache_jira_adapter.py#L65-L85) evaluates strictly to `False`. Attempting to adapt it raises `ValueError("Invalid or unauthorized Jira issue key 'AXIOS-12613773'")`. It is completely rejected and **does NOT become a Jira WorkItemRef**.

---

## 7. Provenance & Identity Verification

### Provenance Dereferencing
- Every canonical observation carries a [`ProvenanceRef`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py#L268-L281) specifying:
  - `source_instance`: `APACHE_JIRA_SOURCE` (`issues.apache.org`) or `APACHE_GITHUB_SOURCE` (`github.com/apache`)
  - `observation_id`: `obs_apache_jira_real_001` or `obs_apache_github_real_001`
  - `fixture_id`: relative path to immutable raw capture (e.g. `qualification/wave3/apache_real/jira/KAFKA-13557.json`)
  - `record_locator`: locator grammar addressing raw record (e.g. `work_items[KAFKA-13557]`, `pull_requests[11617]`, `commits[<sha>]`)
- All 21 observations dereferenced against `fixtures_by_id` using [`dereference_provenance_ref`](file:///home/tecblic/orbit/src/shadow_orbit/provenance_dereference.py) resolve with `status="RESOLVED"` and `error_message=None`.
- Bundle validation via [`validate_evidence_bundle(bundle, fixtures_by_id=fixtures_by_id)`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_assembly.py#L425-L500) returns strictly **0 QualityIssues**.

### Identity Scoping
- **Jira:** Scoped by instance ID `issues.apache.org` and entity kind `work_item`.
- **GitHub PR:** Scoped by base repository (e.g. `apache/parquet-java/885`) and entity kind `code_change`.
- **GitHub Commit:** Scoped by repository and SHA (e.g. `apache/kafka/<sha>`) and entity kind `github_commit`.

---

## 8. Provider-Leakage Adversarial Execution Proof

To prove that the Track B evaluator operates purely on canonical models without hidden dependencies on Jira/GitHub constructors, an adversarial test was executed:

1. Constructed the canonical Apache evidence bundle.
2. Patched [`JiraIssueState.__init__`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py#L300) with a raising mock (`AssertionError("JiraIssueState must NOT be instantiated")`).
3. Patched [`GitHubPullRequestState.__init__`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py#L356) with a raising mock (`AssertionError("GitHubPullRequestState must NOT be instantiated")`).
4. Executed [`evaluate_evidence_bundle(bundle)`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_evaluation.py#L200-L300).

### Result
- `mock_jira.call_count`: **0**
- `mock_gh.call_count`: **0**
- Exceptions raised: **0**
- Evaluation completed cleanly, returning deterministic [`EvidenceBundleEvaluationResult`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_evaluation.py#L91-L101).

---

## 9. Determinism & Permutation Invariance

1. **Deterministic Serialization:**
   - Assembled two independent bundles from the raw files.
   - Serialized both using [`serialize_evidence_bundle`](file:///home/tecblic/orbit/src/shadow_orbit/evidence_types.py).
   - Canonical JSON SHA-256 match: **100% bit-for-bit identical**.
   - Bundle SHA-256 digest: `db0fd630c4e02fed15298e0af880d21758592d295e2d667b4626bb03a5f82044`
   - Evaluation Result SHA-256 digest: `e7d0bcc961cbd0034774ec6478a4c44d554fa9e8f8d70051a1e5938c03082e02`
2. **Permutation Invariance:**
   - Inverted the ordering of observations, relationships, and alignments.
   - Evaluated the permuted bundle.
   - Serialized evaluation result JSON match: **100% bit-for-bit identical**.
   - Zero clock (`datetime.now`), random seed, or UUID generation used.

---

## 10. Test Matrix Audit

All 17 required items from Section 16 are covered in [`tests/unit/test_p5_wave3_apache_canonical_adaptation.py`](file:///home/tecblic/orbit/tests/unit/test_p5_wave3_apache_canonical_adaptation.py):

| Test Case | Description | Result |
| :--- | :--- | :--- |
| `test_jira_to_work_item_state_mapping` | Maps all 6 target Jira issues into WorkItemState | **PASS** |
| `test_parquet_2010_specific_fields` | Blocker priority and resolved status mapping | **PASS** |
| `test_jira_source_instance_identity` | Jira EntityRef identity scoped by `issues.apache.org` | **PASS** |
| `test_invalid_and_non_apache_keys_rejected` | Rejection of non-Apache keys and Snyk/CVE tokens | **PASS** |
| `test_github_pr_to_code_change_state_mapping` | Maps all 7 target PRs into CodeChangeState | **PASS** |
| `test_commit_vs_merge_timestamp_distinction` | Disentanglement of `committed_at` and `merged_at` | **PASS** |
| `test_closed_unmerged_pr_invariants` | Closed PRs (PR #10123, PR #17401) remain closed | **PASS** |
| `test_repository_scoped_pr_identity` | Base repository scoping in PR EntityRef | **PASS** |
| `test_fork_and_upstream_identity` | Head fork vs base canonical upstream preservation | **PASS** |
| `test_chain1_parquet_declared_mention` | Chain 1 canonical representation & coherence | **PASS** |
| `test_chain2_kafka_explicit_link_many_commits` | Chain 2 canonical representation & 5 commits | **PASS** |
| `test_chain3_avro_explicit_link` | Chain 3 canonical representation & fork handling | **PASS** |
| `test_chain4_flink_one_jira_many_prs` | Chain 4 representation of 3 PRs (abandoned, master, backport) | **PASS** |
| `test_chain5_flink_many_jira_one_pr` | Chain 5 representation of many-Jira to one-PR | **PASS** |
| `test_unlinked_negative_controls` | Anti-Cartesian verification for unlinked Jira and PR | **PASS** |
| `test_snyk_cve_false_positive_rejection` | Proves `AXIOS-12613773` is never a Jira work item | **PASS** |
| `test_all_observations_retain_dereferenceable_provenance` | In-memory provenance resolution against raw fixtures | **PASS** |
| `test_validate_evidence_bundle_zero_issues` | Structural validation of assembled bundle | **PASS** |
| `test_deterministic_bundle_serialization` | Bit-for-bit serialization reproducibility | **PASS** |
| `test_permutation_invariance_of_evaluation` | Permutation invariance of Track B evaluation | **PASS** |
| `test_canonical_evaluator_execution_without_legacy_constructors` | Adversarial provider leakage proof | **PASS** |

---

## 11. Known Limitations & Boundary Constraints

1. **Offline Scope:** Adapters operate purely on captured immutable JSON artifacts from Phase 1A. Zero network I/O, live webhooks, or dynamic polling.
2. **Command-Line Merges:** In GitHub REST API semantics, command-line merges (e.g. PR #10123) report `merged: false` and `merged_at: None`. This distinction is faithfully preserved; the merge commit SHA is captured in `extra_properties['merge_commit_sha']`.
3. **No Rule Mutation:** Track B rule evaluation logic was not modified or relaxed. The Apache corpus represents real engineering workflows where PRs merged prior to issue resolution evaluate as healthy (`COHERENT` / `CONSISTENT`).

---

## 12. Exact Next Gate

**Next Phase:** **Pass 5 / Wave 3 — Phase 1C: Controlled Multi-Project Proving / Enterprise Benchmark Execution**  
**Authorized Scope:** Execute benchmark qualification scripts, record formal multi-project delivery metrics across the five Apache ecosystems, and prepare consolidation documentation.

---

## 13. Final Classification

```text
================================================================================
                      FINAL CLASSIFICATION: PHASE 1B VERIFIED
================================================================================
  - 31/31 verified raw Apache records adapted to canonical models
  - 100% Track A zero diff maintained
  - 100% Mahout qualification invariants maintained (412 accepted, 0 mutations)
  - 100% Pre-Wave semantic baseline match (2b23afaccbeb...)
  - 21/21 new unit tests passing; 783/783 repository tests passing
  - Zero working tree commits; STOP condition enforced
================================================================================
```
