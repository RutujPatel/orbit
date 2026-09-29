# PROJECT ORBIT — PASS 4 WAVE 0: REPOSITORY & ARCHITECTURE RECONNAISSANCE

**Document ID:** `PASS4_REPOSITORY_RECONNAISSANCE.md`  
**Classification:** ARCHITECTURAL SPECIFICATION & FORENSIC RECONNAISSANCE  
**Phase:** Milestone 2 — Evidence Integration Architecture (Wave 0)  
**Governing Frozen Baseline:** Commit `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Audited Baseline Head:** Commit `e967ad57ea3b37cef4266134537acbb34e9ae715` (`e967ad5`) on branch `remediation/pass3-controlled-hardening`  
**Regression Status:** 527 tests passing / 0 failing / 0 skipped (100% pass rate in 9.64s)  
**Date:** 2026-09-28  

---

## 1. Executive Summary

This document establishes the authoritative Wave 0 architectural reconnaissance for **Pass 4 (Milestone 2 — Evidence Integration Architecture)**. 

The objective of Pass 4 is to establish bounded, auditable, and testable architectural contracts for the three capability gaps identified in Pass 2.5 and deferred during Pass 3:
1. **`P3-05` / `P2.5-17`:** Active Provenance Locator Dereferencing.
2. **`P3-06` / `P2.5-18`:** `EvidenceBundle` Evaluation Pipeline Consumption.
3. **`P3-07` / `P2.5-19`:** GitHub / Jira Cross-System Evidence Fusion.

In accordance with Wave 0 instructions, **zero code modifications or external connectors have been implemented**. This reconnaissance traces actual import graphs, execution pathways, data contracts, and boundary conditions across `src/shadow_orbit/`, `qualification/`, and `tests/`, producing empirical answers to all ten mandatory architectural investigation questions.

---

## 2. Complete Repository Subsystem Survey

The ORBIT codebase is partitioned into three distinct functional tiers:

### 2.1. Tier 1: Deterministic Engine Core (`src/shadow_orbit/`)
The engine core contains zero network I/O, zero database drivers, and zero system clock calls during execution. It operates on immutable, slotted dataclasses:
- **`types.py`:** Authoritative Jira domain models (`WorkItem`, `Change`, `ReviewPeriod`, `RuleMatch`, `SuppressedEvaluation`).
- **`evidence_types.py`:** Common Cross-System Evidence (CSE) types (`EntityRef`, `SourceInstance`, `ObservationContext`, `EvidenceObservation`, `EvidenceRelationship`, `UnresolvedReference`, `QualityIssue`, `EvidenceBundle`).
- **`validation.py` & `github_validation.py`:** Strict schema, primitive type, chronological ordering (`updated >= created`), and interval boundary validators. Isolates malformed inputs into `QuarantinedRecord` without raising unhandled exceptions.
- **`normalization.py` & `github_normalization.py`:** Transforms validated records into canonical, chronologically sorted, immutable representations. Emits structured data quality conditions (`UNKNOWN_STATUS`, `UNKNOWN_PRIORITY`, `PARTIAL_HISTORY`, `INVALID_OPTIONAL_TIMESTAMP`).
- **`temporal.py`:** Pure interval arithmetic, status category projection, reopen-cycle terminal state resolution, and elapsed time calculation.
- **`evaluation.py`:** Pure rule evaluation (`calculate_supporting_facts`, `evaluate_week_one_rules`). Evaluates `STALLED_WORK` and supporting metrics without mutating inputs.
- **`artifact.py` & `messy_acceptance.py`:** Assembles the human-readable Engineering Weekly Review artifact.
- **`jira_evidence_adapter.py`:** Read-only structural bridge transforming a Jira `NormalizedFixture` into CSE `EvidenceObservation` items.
- **`github_relationships.py` & `github_mentions.py`:** Pure graph relationship extraction resolving internal GitHub structural associations and literal lexical Jira mentions.
- **`evidence_assembly.py`:** Multi-system evidence bundle assembly, deduplication, and cross-system context validation.

### 2.2. Tier 2: Qualification Framework & Adapters (`qualification/`)
Houses extraction adapters, source selectors, and qualification harnesses that run outside the deterministic engine:
- **`qualification/mahout/runner.py`:** End-to-end qualification runner orchestrating the 412 Mahout corpus through ingestion, validation, normalization, evidence bridging, metric calculation, finding evaluation, and artifact generation.
- **`qualification/mahout/ingestion.py`, `selector.py`, `structural_dependencies.py`:** Ingestion pipeline projecting raw Apache Mahout MongoDB/JSON records into standard fixture documents.
- **`qualification/mahout/evidence_bridge.py`:** Adapts Mahout fixtures into canonical `EvidenceBundle` instances and records structural links.
- **`qualification/mahout/provenance.py`:** Traces end-to-end provenance chains (`match` $\to$ `work_item` $\to$ `raw_doc` $\to$ `validated` $\to$ `normalized` $\to$ `observation` $\to$ `review_artifact`).
- **`qualification/extraction/jira_extractor.py`:** Authorized Jira Cloud REST client for Gate 2 live extraction. Contains read-only HTTP GET transport, rate-limiting, two-pass fingerprint observation, and cryptographic receipt emission.
- **`qualification/config.py` & `policy.py`:** Frozen hashes, artifact paths, provenance verification rules, and baseline constants (`FROZEN_ENGINE_COMMIT = "6d82d12"`).

### 2.3. Tier 3: Test Suites (`tests/`)
Comprises 527 passing tests across three suites:
- `tests/unit/`: 360 unit tests covering validation, normalization, temporal arithmetic, human state, evidence types, evidence assembly, GitHub validation/normalization/relationships/mentions, and Pass 3 remediations (`test_p3_remediation.py`).
- `tests/acceptance/`: 49 acceptance tests verifying clean and messy week 1 and week 2 pipeline behavior.
- `tests/qualification/`: 118 qualification tests verifying Gate 2 Jira extraction, provenance verification, Mahout selector determinism, and history model projection.

---

## 3. Ten Core Architectural Investigation Questions

### Question 1: Where does evidence enter the system?
- **Jira Offline Path (Mahout / Qualification):**  
  Evidence enters via `load_raw_mahout_issues()` (`qualification/mahout/ingestion.py:90`), which reads the raw JSON file `/home/tecblic/orbit-private/mahout/mahout_raw_capture.json` (SHA-256: `391c9346...`). Records are filtered through frozen allowlists (`mahout_412_allowlist.txt`) and projected into the standard Jira fixture format via `build_mahout_fixture_document()` (`qualification/mahout/ingestion.py:168`) using `project_single_mahout_record()` (`qualification/mahout/description_projection.py`).
- **Jira Live Path (Gate 2 / GoGreen):**  
  Evidence enters via `AuthorizedJiraCloudExtractor.fetch_issue_with_changelog()` (`qualification/extraction/jira_extractor.py:266`) via HTTP GET requests against the Jira Cloud REST API (`/rest/api/3/issue/{key}`). Raw responses are scrubbed of credentials and persisted to `/home/tecblic/orbit-private/gate2/raw/gate2_jira_raw_capture.json`.
- **GitHub Offline Path:**  
  Evidence enters via JSON fixture files (`fixtures/github/clean_github_week_1.json`, `fixtures/github/messy_github_week_1.json`) loaded into memory as dictionary payloads complying with `shadow-github-fixture-v1`.
- **GitHub Live Path:**  
  **Does not exist.** Only an exploratory discovery record (`GITHUB_DISCOVERY_RECORD` in `qualification/config.py:80`) exists. No live GitHub REST/GraphQL extractor is implemented.

### Question 2: Where is evidence normalized?
- **Jira Ingestion & Validation Boundary:**  
  Raw fixture documents pass through `validate_fixture()` (`src/shadow_orbit/validation.py:177`). Malformed items are quarantined into `ValidatedFixture.quarantined_records`.
- **Jira Normalization Boundary:**  
  `normalize_fixture()` (`src/shadow_orbit/normalization.py:131`) transforms accepted raw items into immutable `WorkItem` instances, normalizes timestamps to UTC timezone-aware datetimes, maps provider-specific statuses and priorities, sorts changelog entries chronologically, and records `DataQualityCondition` items.
- **GitHub Ingestion & Validation Boundary:**  
  Raw GitHub JSON passes through `validate_github_fixture()` (`src/shadow_orbit/github_validation.py:539`), enforcing `shadow-github-fixture-v1`. Invalid entities are quarantined into `ValidatedGitHubFixture.quarantined_records`.
- **GitHub Normalization Boundary:**  
  `normalize_github_fixture()` (`src/shadow_orbit/github_normalization.py:77`) maps accepted repositories, branches, commits, PRs, and reviews into typed `EvidenceObservation` items wrapped in `NormalizedGitHubFixture`.
- **Cross-System Structural Normalization:**  
  `resolve_github_relationships()` (`src/shadow_orbit/github_relationships.py:91`) normalizes internal GitHub references into `EvidenceRelationship(basis="structural_association")`.  
  `resolve_github_jira_mentions()` (`src/shadow_orbit/github_mentions.py:108`) extracts Jira ticket keys into `EvidenceRelationship(kind="mentions", basis="lexical_match")`.

### Question 3: Where does evidence become deterministic?
- **Immediate Data Boundary:** Evidence becomes deterministic at the moment of instantiation into frozen dataclasses (`ValidatedFixture`, `NormalizedFixture`, `ValidatedGitHubFixture`, `NormalizedGitHubFixture`, `EvidenceBundle`).
- **Deterministic Ordering Guarantees:**
  - Jira changelog histories are chronologically sorted (`normalization.py:157`).
  - Evidence collections are sorted by canonical composite keys (`_provenance_sort_key`, `_sort_relationship_key`, `_quality_issue_sort_key` in `evidence_assembly.py:63-76`).
  - Permutation invariance tests (`P2.5-10`, `test_permutation_invariance`) prove that arbitrary shuffling of input records produces byte-for-byte identical canonical review artifacts and finding lists.
- **Zero Non-Deterministic Primitives:** Rule evaluation in `evaluation.py` uses no random generators, no system wall-clock calls (`datetime.now()` is forbidden in engine evaluation; all temporal comparisons use the explicit `ReviewPeriod` boundaries), and no mutable global state.

### Question 4: Where is provenance currently stored?
- **`ProvenanceRef` Primitives:** Defined in `src/shadow_orbit/evidence_types.py:180`:
  ```python
  class ProvenanceRef:
      source_instance: SourceInstance
      observation_id: str
      fixture_id: str | None = None
      record_locator: str | None = None
      source_field_path: str | None = None
  ```
- **Attached Locations:**
  - Attached to `EvidenceObservation.provenance_refs` (`evidence_types.py:333`).
  - Attached to `EvidenceRelationship.provenance_refs` (`evidence_types.py:381`).
  - Generated by `jira_evidence_adapter.py:271` (`record_locator=f"work_items[{raw_index}]"`).
  - Traced in `qualification/mahout/provenance.py:77` (`ProvenanceChain` linking finding $\to$ work item $\to$ raw document $\to$ review artifact).

### Question 5: Is provenance currently dereferenced anywhere?
- **NO.** Provenance is stored purely as static metadata.
- **Code Audit:** In `src/shadow_orbit/evidence_assembly.py:418-461` (`_validate_provenance_refs`), the validator checks only:
  1. That `p.observation_id` is registered in `ObservationContext`.
  2. That `p.source_instance` matches the registered context's `source_instance`.
- **The Gap:** The validator **never inspects** `p.fixture_id`, `p.record_locator`, or `p.source_field_path`. It does not attempt to resolve `"work_items[999999]"` or check if `"definitely.not.real"` exists in the source payload. Bogus locators pass validation without error (`P2.5-17` / `P3-05`).

### Question 6: Is EvidenceBundle actually consumed during evaluation?
- **NO.**
- **Code Audit:**
  - `evaluate_week_one_rules()` (`src/shadow_orbit/evaluation.py:270`) accepts `fixture: NormalizedFixture`.
  - `calculate_supporting_facts()` (`src/shadow_orbit/evaluation.py:52`) accepts `fixture: NormalizedFixture`.
  - `build_messy_week_one_artifact()` (`src/shadow_orbit/artifact.py:80`) accepts `validated: ValidatedFixture, normalized: NormalizedFixture`.
- **The Gap:** `EvidenceBundle` is assembled as an export and audit container by `qualification/mahout/evidence_bridge.py` (`build_mahout_evidence_bridge()`), but the live evaluation pipeline completely bypasses it (`P2.5-18` / `P3-06`). Zero evaluation functions consume or inspect `EvidenceBundle`.

### Question 7: Does GitHub data exist anywhere in the repository?
- **YES.** GitHub data exists in three locations:
  1. **Synthetic & Messy Fixtures:** `fixtures/github/clean_github_week_1.json` and `fixtures/github/messy_github_week_1.json`.
  2. **Research Snapshots in `orbit-private`:** `/home/tecblic/orbit-private/ekfc-cross-context-research/github_snapshot.json` and `/home/tecblic/orbit-private/gogreen-cross-system-research/normalized_github.json`.
  3. **Discovery Metadata:** `GITHUB_DISCOVERY_RECORD` in `qualification/config.py:80`.
- **Qualification Corpus Boundary:** The primary 412 Mahout qualification dataset contains **zero GitHub data**; it is an Apache Jira-exclusive corpus.

### Question 8: Does Jira/GitHub correlation already exist partially?
- **YES, at the lexical mention level only.**
- **Existing Implementation:** `src/shadow_orbit/github_mentions.py` implements `resolve_github_jira_mentions()`. It extracts Jira issue keys from GitHub PR titles, PR source/target branches, commit messages, and branch names using regex configured by `MentionLexicalPolicy` (e.g. `r"\b(?:PLAT)-\d+\b"`).
- **The Boundary:** It creates `EvidenceRelationship(kind="mentions", basis="lexical_match")`. If a mentioned key is not in the accepted Jira observations, it emits an `UnresolvedReference`.
- **What is Missing:**
  1. No semantic correlation (e.g., whether PR status aligns with Jira status).
  2. No temporal alignment (whether PR was merged before or after the Jira review cutoff).
  3. No person identity fusion (whether Jira assignee matches GitHub PR author).
  4. No consumption of mention relationships by any finding rule.

### Question 9: Where do external I/O boundaries currently exist?
- **Deterministic Engine (`src/shadow_orbit/`): ZERO external I/O.** Pure in-memory computation.
- **Filesystem I/O:**
  - `shadow_orbit.fixture_io`: Reads/writes local JSON fixtures.
  - `qualification/mahout/ingestion.py`: Reads raw JSON and allowlist text files.
  - `qualification/mahout/runner.py`: Writes `mahout_qualification_golden.json` when `save_golden=True`.
- **Database I/O:**
  - `qualification/mahout/selector.py`: Queries MongoDB `localhost:27017` collection `JiraReposAnon.Apache` for the 2,121 census and seed selection.
- **Network HTTP I/O:**
  - `qualification/extraction/jira_extractor.py`: Executes read-only HTTP GET requests to Jira Cloud REST API endpoints via Python's standard `urllib.request`. Zero write operations exist.

### Question 10: Which components are deterministic vs integration adapters?
- **Deterministic Core:** All modules in `src/shadow_orbit/` (`types`, `evidence_types`, `validation`, `github_validation`, `normalization`, `github_normalization`, `temporal`, `evaluation`, `artifact`, `messy_acceptance`, `github_relationships`, `github_mentions`, `evidence_assembly`).
- **Integration Adapters / Test Harness:**
  - `qualification/extraction/jira_extractor.py` (Jira REST network adapter).
  - `qualification/mahout/ingestion.py`, `selector.py`, `structural_dependencies.py` (Mahout data adapter).
  - `qualification/mahout/evidence_bridge.py` (Jira-to-EvidenceBundle bridge).
  - `qualification/mahout/runner.py` (Qualification orchestrator).
  - `src/shadow_orbit/jira_evidence_adapter.py` (Adapter transforming Jira fixture to CSE observations).

---

## 4. Analysis of Milestone 2 Capability Gaps

### 4.1. Gap P3-05 / P2.5-17: Active Provenance Locator Dereferencing (`ADR-004`)
- **Current Defect:** `validate_evidence_bundle()` treats `ProvenanceRef.record_locator` as uninspected text.
- **Proposed Boundary:** Bounded Fixture-Local Dereferencing. When a `ProvenanceRef` specifies a `record_locator` formatted as a JSON array pointer (e.g. `work_items[i]`, `repositories[0].pull_requests[j]`), the validator must verify:
  1. That the index exists within the corresponding accepted validated/normalized fixture in memory.
  2. That the entity ID at that position matches `entity_ref.entity_id`.
  3. If unresolvable or out-of-bounds, emit a structured `QualityIssue(code="unresolved", subject_scope="provenance:locator")`.
- **Prohibition:** Must NOT attempt remote network dereferencing or database querying during evaluation.

### 4.2. Gap P3-06 / P2.5-18: EvidenceBundle Evaluation Pipeline Consumption (`ADR-005`)
- **Current Defect:** Rule evaluation directly consumes `NormalizedFixture`, completely bypassing `EvidenceBundle`.
- **Proposed Boundary:** Dual-Track Harmonization.
  - Track A (V0 Legacy / Protected): `evaluate_week_one_rules(fixture: NormalizedFixture)` must remain untouched to protect the 503 baseline tests and 12-stalled Mahout qualification boundary.
  - Track B (Milestone 2 Joint Track): Introduce `evaluate_evidence_bundle(bundle: EvidenceBundle, period: ReviewPeriod) -> tuple[RuleMatch, ...]` that extracts observations from `EvidenceBundle` and evaluates findings over normalized observation graphs.

### 4.3. Gap P3-07 / P2.5-19: Cross-System Evidence Fusion (`ADR-006`)
- **Current Defect:** GitHub and Jira evidence exist in silos. Mentions are extracted as text matches, but zero findings or evaluation rules evaluate cross-system alignment.
- **Proposed Boundary:** Strict 3-Tier Link Classification:
  1. `EXPLICIT_LINK`: Explicitly configured remote issue link or GitHub development panel link.
  2. `DECLARED_MENTION`: Lexical mention matching `MentionLexicalPolicy` in PR title, branch, or commit.
  3. `UNRESOLVED / CONTRADICTED`: Conflicting timestamps, post-cutoff events, or unobserved keys.
- **Non-Inference Rule:** A PR mention of `PLAT-104` must NEVER be converted into "PLAT-104 is complete" or "developer worked on PLAT-104" without explicit state correlation and temporal verification.

---

## 5. Qualification Harness Hardening Analysis

### 5.1. Qualification Date Lock
- **Observation:** In `qualification/mahout/runner.py:369`, `golden_artifact["qualification_date"] = run_timestamp[:10]` uses the wall-clock execution date.
- **Implication:** Running the qualification harness on different calendar days alters the golden artifact JSON byte stream and changes the runtime digest (`1fdec553...`), introducing calendar-date sensitivity.
- **Hardening Action:** Lock `qualification_date` in the runner to the authoritative review cutoff date (`2021-06-05`) or source cutoff date, guaranteeing absolute calendar-date invariance for `golden_digest`.

### 5.2. Dual-Commit Telemetry
- **Observation:** In `qualification/mahout/runner.py:367`, `"engine_commit": FROZEN_ENGINE_COMMIT` prints the static constant `"6d82d12"` from `qualification/config.py:21`.
- **Implication:** When executed on `e967ad5`, the report claims `engine_commit: "6d82d12"`, conflating the governing baseline specification with the executing Git branch.
- **Hardening Action:** Separate into two distinct fields:
  ```json
  "governing_baseline_commit": "6d82d12",
  "runtime_git_head": "<dynamic git rev-parse HEAD>"
  ```

---

## 6. Wave 0 Summary & Forensic Scorecard

### 1. Facts Established
1. The 527-test regression suite is 100% green and runs in 9.64s.
2. The Mahout qualification invariants (2,121 considered, 400 primary, 12 dependencies, 412 corpus, 12 stalled findings, 56 incomplete, 370 missing due dates) are 100% deterministic and reproducible.
3. `src/shadow_orbit/` contains zero network or database I/O calls.
4. `ProvenanceRef` exists but is never actively dereferenced to underlying source payloads (`P2.5-17` is confirmed `UNSUPPORTED`).
5. `EvidenceBundle` is completely bypassed by the live rule evaluation pipeline (`P2.5-18` is confirmed `UNSUPPORTED`).
6. GitHub data models, validators, normalizers, structural relationship extractors, and lexical mention resolvers exist and pass 149 unit tests, but zero GitHub evidence is consumed during weekly review rule evaluation (`P2.5-19` is confirmed `UNSUPPORTED`).
7. `ReadOnlyJiraGuard` is an internal harness assertion context manager (Category C); zero mutations occur because the pipeline operates 100% offline.

### 2. Architectural Gaps
1. **Provenance Gap (`P3-05`):** No in-memory dereferencing of `record_locator` pointers against source fixtures.
2. **Evaluation Container Gap (`P3-06`):** Dual-track disconnect between `NormalizedFixture` (consumed by rules) and `EvidenceBundle` (assembled but ignored).
3. **Cross-System Fusion Gap (`P3-07`):** Lexical mentions in `github_mentions.py` do not participate in finding evaluation or contradiction detection.
4. **Harness Telemetry Gaps:** Qualification date depends on execution calendar day; `engine_commit` does not report active Git HEAD.

### 3. Unknowns (Requiring Architectural Decisions)
1. **Dereferencing Scope:** Should locator dereferencing operate strictly against in-memory fixture records (`ValidatedFixture`), or should it support file-system offset dereferencing for raw captures? *(Recommendation: In-memory fixture records for V0)*.
2. **Evaluation Migration:** Should week-one rule evaluation be refactored to consume `EvidenceBundle`, or should a parallel `JointEvidenceEvaluator` be introduced? *(Recommendation: Parallel joint evaluator to avoid risking the 503-test baseline)*.
3. **Contradiction Precedence:** When Jira indicates an issue is completed during the period, but GitHub shows a linked PR merged *after* the review cutoff, what is the authoritative finding? *(Recommendation: Emit `CROSS_SYSTEM_TEMPORAL_CONTRADICTION` finding, do not silently overwrite Jira state)*.

### 4. Proposed Boundaries
- **Dereferencing Boundary:** `dereference_provenance_locator(locator: str, fixture: ValidatedFixture) -> Any`. Fail-closed with structured `QualityIssue`.
- **EvidenceBundle Evaluation Boundary:** Pure function `evaluate_evidence_bundle(bundle: EvidenceBundle, period: ReviewPeriod) -> tuple[RuleMatch, ...]`.
- **Fusion Boundary:** `fuse_cross_system_evidence(jira_obs: Sequence[EvidenceObservation], github_obs: Sequence[EvidenceObservation]) -> tuple[CrossSystemLink, ...]`. Distinguish `EXPLICIT_LINK` from `DECLARED_MENTION`.

### 5. Files That Would Require Modification (in Waves 1–4)
- **Harness Hardening (Wave 4):**
  - `qualification/mahout/runner.py` (date lock and dual-commit telemetry).
- **Provenance Architecture (Wave 1):**
  - `src/shadow_orbit/evidence_assembly.py` (active locator dereferencing in validation).
- **EvidenceBundle Evaluation (Wave 2):**
  - `src/shadow_orbit/evidence_types.py` & `src/shadow_orbit/evaluation.py` (bundle-aware evaluation interface).
- **Cross-System Fusion (Wave 3):**
  - `src/shadow_orbit/github_mentions.py` & new fusion module `src/shadow_orbit/cross_system_fusion.py`.
- **New Unit & Adversarial Tests (Wave 5):**
  - `tests/unit/test_p4_provenance_dereferencing.py`
  - `tests/unit/test_p4_bundle_evaluation.py`
  - `tests/unit/test_p4_cross_system_fusion.py`

### 6. Risks
1. **Regression on Mahout Baseline:** Changing evaluation function signatures could break the frozen 12 STALLED_WORK finding keys.
2. **False Confidence via Lexical Over-Matching:** Treating PR title regex matches as definitive proof of issue completion creates false engineering conclusions.
3. **Calendar-Date Hash Invalidation:** Any change to the golden serialization format alters `1fdec553...`.

### 7. Questions Requiring Explicit Human Decision
1. **Decision Q1:** Do you approve the **Dual-Track Evaluation Strategy** (preserving `evaluate_week_one_rules(NormalizedFixture)` for the frozen Mahout baseline, while building `evaluate_evidence_bundle(EvidenceBundle)` for Milestone 2 multi-system findings)?
2. **Decision Q2:** Do you approve **In-Memory Fixture Dereferencing** (resolving `work_items[i]` against the in-memory `ValidatedFixture`) rather than requiring external database/disk block lookups?
3. **Decision Q3:** Do you approve classifying PR-to-Jira text matches strictly as **`DECLARED_MENTION`** (a correlation signal) rather than **`EXPLICIT_LINK`** (an authoritative association)?
