# PASS 5 / WAVE 0 — UNIVERSAL CONNECTED SYSTEMS ARCHITECTURE RECONNAISSANCE
**Document Version:** 1.0.0  
**Timestamp:** 2026-09-29T15:15:00+05:30  
**Author:** Senior Forensic Software Architect, Project ORBIT  
**Governance State:** `PASS 5 WAVE 0 — RECONNAISSANCE COMPLETE`  
**Operational Posture:** Strictly Read-Only Architectural Inspection (Zero Code / Schema / Test Modifications)

---

## 1. Executive Summary

This forensic architectural reconnaissance evaluates the consolidated codebase of **Project ORBIT** at commit `7a1e2ff` (incorporating technical consolidation `5a9e32d` and documentation baselines `e867258` / `7a1e2ff`) against the frozen governing baseline `6d82d12`.

The objective of this reconnaissance is to rigorously answer the primary architectural question:

> **Can the current ORBIT architecture evolve from Jira + GitHub into a provider-agnostic organizational evidence and memory platform without rewriting the deterministic core every time a new SaaS system is added?**

### Key Findings

1. **The Architectural Pattern is Fundamentally Sound:**  
   The core pipeline topology established in Pass 4—*Adapters $\to$ Normalization $\to$ Evidence Observations $\to$ EvidenceBundle $\to$ Provenance Dereferencing $\to$ Fusion $\to$ Deterministic Evaluator*—is conceptually provider-agnostic. The container structures, deterministic serialization, immutable slotted types, and anti-inference guarantees (anti-Cartesian, anti-transitive, anti-actor matching, absence-as-unobserved) form an exceptionally robust foundation.

2. **Jira and GitHub Concrete Leaks Exist in the Core Types:**  
   While the pipeline topology is generic, the **type definitions, validation routines, fusion logic, and evaluator rules currently hardcode Jira- and GitHub-specific identifiers**:
   - `SourceKind` is typed as a closed literal: `Literal["jira", "github"]` (`evidence_types.py:28`).
   - `EntityKind` is closed with provider-prefixed names (`"jira_issue"`, `"github_pull_request"`, etc.) (`evidence_types.py:32-40`).
   - `CrossSystemStateAlignment` explicitly names its fields `jira_ref` and `github_ref` (`evidence_types.py:438-439`).
   - `evidence_assembly.py` contains explicit `if ref.source_instance.source_kind == "jira"` and `elif ... == "github"` validation checks (`evidence_assembly.py:627-652`).
   - `provenance_dereference.py` restricts locators to a closed set of 6 collections (`work_items`, `repositories`, `branches`, `commits`, `pull_requests`, `reviews`) and hardcodes identifier key resolution per collection (`provenance_dereference.py:44-51, 149-165`).
   - `cross_system_fusion.py` takes explicit `jira_observations` and `github_fixture` arguments and unpacks `JiraIssueState` and `GitHubPullRequestState` directly (`cross_system_fusion.py:76-80, 161-223`).
   - `evidence_evaluation.py` hardcodes `isinstance(jira_state, JiraIssueState)` and `isinstance(gh_state, GitHubPullRequestState)` within rules XB-01, XB-02, and XB-03 (`evidence_evaluation.py:441, 534, 600`).

3. **Feasibility Verdict:**  
   **YES, ORBIT can evolve into a provider-agnostic evidence platform without rewriting the deterministic core**, PROVIDED that a controlled, non-speculative refactoring is executed to **decouple closed type literals and introduce a canonical entity payload model** (`WorkItemState`, `CodeChangeState`) at the boundary. The deterministic evaluator, EvidenceBundle container, provenance tracking, and sorting/permutation machinery will require **zero algorithmic redesign**.

---

## 2. Repository Baseline

Forensic verification of git baselines confirms clean working tree and frozen integrity:

```text
HEAD:                   7a1e2fffa5265eb7ce0a444823af8d654a1b8c28
Branch:                 remediation/pass3-controlled-hardening
develop:                6d82d123f8bf50316d2b1ab7a025bc5862a474ed
merge-base:             6d82d123f8bf50316d2b1ab7a025bc5862a474ed
Working Tree Status:    CLEAN (git status --short is strictly empty)
```

### Commit Lineage
- `6d82d12` — Frozen governing baseline (develop)
- `fe7a99a` through `d2091d3` — Pass 3 controlled hardening fixes (P3-01 through P3-04)
- `5a9e32d` — Pass 4 Waves 1–5.2 technical consolidation (Track B cross-system engine)
- `e867258` — Pass 4 documentation and ADR consolidation
- `7a1e2ff` — Comprehensive documentation hierarchy reorganization under `docs/`

### Track A Isolation Invariant Verification
```bash
git diff 5a9e32d~1..HEAD -- \
  src/shadow_orbit/evaluation.py \
  src/shadow_orbit/temporal.py \
  src/shadow_orbit/normalization.py \
  src/shadow_orbit/types.py
```
**Diff Output:** Strictly empty (0 bytes, 0 lines modified).  
**Reverse Dependency Check:** Exactly 0 imports from Track A into Track B. Track A remains 100% frozen.

---

## 3. Current Pass 4 Architecture

Pass 4 established the following five core stages:

```
[ Jira Fixture ]                [ GitHub Fixture ]
       │                                │
       ▼                                ▼
[ jira_evidence_adapter ]       [ github_normalization ]
       │                                │
       └──────────────┬─────────────────┘
                      ▼
            [ Evidence Observations ]
                      │
                      ▼
            [ evidence_assembly ]
             ├── EvidenceBundle Assembly & Validation
             └── provenance_dereference (ADR-004)
                      │
                      ▼
            [ cross_system_fusion ] (ADR-005)
             ├── Pairwise Mentions / Explicit Links
             └── CrossSystemStateAlignment Matrix
                      │
                      ▼
            [ evidence_evaluation ] (ADR-006)
             └── Rules XB-01, XB-02, XB-03
                      │
                      ▼
      [ EvidenceBundleEvaluationResult ]
```

### Component Invariants Established in Pass 4
- **Permutation Invariance:** SHA-256 canonical hashing; zero system clock or random UUID access.
- **Fail-Closed Dereferencing:** ADR-004 closed 7-outcome taxonomy (`RESOLVED`, `UNRESOLVED_ABSENT`, `UNRESOLVED_AMBIGUOUS`, etc.).
- **Anti-Inference Safeguards:** No Cartesian product, no transitive closure, no developer identity equating, no completion inference, absence-is-not-failure.
- **Track A Freeze:** Complete architectural isolation of legacy Track A.

---

## 4. Provider Leakage Audit

A comprehensive search across `src/shadow_orbit/` for provider terms yielded:
- `jira`: 113 occurrences
- `github`: 95 occurrences
- `gitlab`, `azure`, `linear`, `service_now`, `salesforce`, `slack`, `teams`: 0 occurrences

### Classification Table of Core Occurrences

| Module | Line(s) | Code Snippet / Context | Classification | Impact on Multi-Provider Evolution |
| :--- | :--- | :--- | :--- | :--- |
| `evidence_types.py` | 28 | `SourceKind = Literal["jira", "github"]` | **PROVIDER-SPECIFIC CORE LEAK** | Blocks any 3rd provider at static type check. |
| `evidence_types.py` | 32–40 | `EntityKind = Literal["jira_issue", "github_..."]` | **PROVIDER-SPECIFIC CORE LEAK** | Couples entity taxonomy to vendor brand names. |
| `evidence_types.py` | 231–326 | `class JiraIssueState`, `class GitHubPullRequestState`, etc. | **PROVIDER-BOUNDARY (Misplaced)** | Vendor payloads defined in core type foundation. |
| `evidence_types.py` | 328–336 | `ObservedState = Union[JiraIssueState, GitHub...]` | **PROVIDER-SPECIFIC CORE LEAK** | Closed union prevents dynamic or 3rd provider payloads. |
| `evidence_types.py` | 438–439 | `CrossSystemStateAlignment.jira_ref`, `.github_ref` | **PROVIDER-SPECIFIC CORE LEAK** | Explicitly couples cross-system fusion to Jira+GitHub. |
| `evidence_assembly.py` | 52–60 | `_JIRA_ENTITY_KINDS`, `_GITHUB_ENTITY_KINDS` | **PROVIDER-SPECIFIC CORE LEAK** | Hardcoded validation sets for entity kinds. |
| `evidence_assembly.py` | 325–342 | `jira_context.source_instance.source_kind != "jira"` | **PROVIDER-BOUNDARY (In Orchestrator)** | Assembly orchestrator accepts concrete provider fixtures. |
| `evidence_assembly.py` | 627–652 | `if ref.source_instance.source_kind == "jira": ...` | **PROVIDER-SPECIFIC CORE LEAK** | Entity validation has hardcoded vendor branches. |
| `evidence_assembly.py` | 817–840 | `a.jira_ref.source_instance.source_kind != "jira"` | **PROVIDER-SPECIFIC CORE LEAK** | Bundle validation checks `jira_ref` and `github_ref`. |
| `cross_system_fusion.py`| 76–80 | `correlate_cross_system_evidence(jira_obs, gh_fix...)` | **PROVIDER-SPECIFIC CORE LEAK** | Function signature is bound to Jira and GitHub. |
| `cross_system_fusion.py`| 161–240| `isinstance(jira_state, JiraIssueState)` | **PROVIDER-SPECIFIC CORE LEAK** | Fusion matrix directly inspects vendor state fields. |
| `evidence_evaluation.py`| 441, 534| `isinstance(jira_state, JiraIssueState)` | **PROVIDER-SPECIFIC CORE LEAK** | Rule evaluators inspect vendor dataclasses directly. |
| `provenance_dereference.py`| 44–51 | `_AUTHORIZED_COLLECTIONS = {"work_items", ...}` | **PROVIDER-SPECIFIC CORE LEAK** | Restricts locators to Jira+GitHub fixture collections. |
| `provenance_dereference.py`| 151–165| `if collection == "work_items": ... elif "pull_requests"`| **PROVIDER-SPECIFIC CORE LEAK** | Hardcodes primary key discovery for 6 collections. |
| `jira_evidence_adapter.py`| 1–320 | Ingestion from normalized Jira fixture | **PROVIDER-BOUNDARY** | Correct placement (adapter boundary). |
| `github_normalization.py`| 1–400 | Ingestion from raw GitHub fixture | **PROVIDER-BOUNDARY** | Correct placement (normalizer boundary). |

---

## 5. Canonical Entity Inventory

Audit of canonical organizational concepts across the repository:

| Canonical Concept | Current Status | Current Code Representation | Evidence / Stateful / Historical | Provenance-Aware? |
| :--- | :--- | :--- | :--- | :--- |
| **Work / WorkItem** | Partially Represented | `WorkItem` (Track A) / `JiraIssueState` (Track B) | Track A: Stateful + Historical.<br>Track B: Evidence-only snapshot. | Track A: No.<br>Track B: Yes (`ProvenanceRef`). |
| **Repository** | Partially Represented | `GitHubRepositoryState` (Track B stub) | Evidence-only snapshot stub. | Yes (`ProvenanceRef`). |
| **PullRequest** | Partially Represented | `GitHubPullRequestState` (Track B) | Evidence-only lifecycle snapshot. | Yes (`ProvenanceRef`). |
| **Commit** | Partially Represented | `GitHubCommitState` (Track B stub) | Evidence-only snapshot. | Yes (`ProvenanceRef`). |
| **Review** | Partially Represented | `GitHubReviewState` (Track B stub) | Evidence-only snapshot. | Yes (`ProvenanceRef`). |
| **Person / Actor** | **Absent as Entity** | Primitive strings (`assignee`, `author_login`) | Evidence-only primitives; intentionally unlinked. | Field-level provenance only. |
| **Project** | Partially Represented | Track A `Project` dict; Track B key prefix | Track A: Stateful config.<br>Track B: Implicit in entity_id. | Track A: No.<br>Track B: No. |
| **Team** | **Absent** | None | None | None |
| **Goal** | **Absent** | None | None | None |
| **Decision** | **Absent** | None (only in ADR documentation) | None | None |
| **Commitment** | Partially Represented | Track A `CommitmentContinuity` / `SprintCommitment` | Track A: Evaluated commitment.<br>Track B: None. | Track A: No.<br>Track B: No. |
| **Risk** | **Absent** | None (explicitly prohibited in Pass 4) | None | None |
| **Incident** | **Absent** | None | None | None |
| **Deployment** | **Absent** | None | None | None |
| **Communication** | **Absent** | None (Slack/Teams absent) | None | None |
| **Document** | Partially Represented | Markdown files / JSON fixtures | Repository artifacts only. | Fixture IDs. |
| **Event** | Partially Represented | Track A `Change` / Track B timestamps | Track A: Discrete field changes.<br>Track B: Timestamps on state. | Track A: No.<br>Track B: Yes. |

---

## 6. EvidenceBundle Boundary Audit

Forensic evaluation of `EvidenceBundle` (`evidence_types.py:359-380`):

1. **Can Jira observations be represented?**  
   *YES.* Fully supported via `entity_kind="jira_issue"` and `observed_state=JiraIssueState`.
2. **Can GitHub observations be represented?**  
   *YES.* Fully supported via `entity_kind="github_pull_request"`, `"github_commit"`, etc.
3. **Can an unrelated SaaS observation be represented?**  
   *NO (without modifying core types).* `SourceKind` is a closed literal `["jira", "github"]`; `EntityKind` is closed; `ObservedState` is a closed union; `evidence_assembly.py:627` rejects any other `source_kind`.
4. **Can multiple providers contribute observations about the same organizational object?**  
   *STRUCTURALLY YES, SEMANTICALLY NO.* Multiple observations can coexist in `bundle.observations`, but they have distinct `EntityRef`s. There is no concept of a shared `CanonicalEntityId` (e.g. `WORK-101`) uniting them; they can only be linked via `EvidenceRelationship`.
5. **Can relationships cross provider boundaries?**  
   *YES.* `EvidenceRelationship` connects arbitrary `subject_ref: EntityRef` and `object_ref: EntityRef` across distinct `SourceInstance`s with explicit `RelationshipBasis`.
6. **Can provenance identify arbitrary source systems?**  
   *PARTIALLY.* `ProvenanceRef(source_instance, observation_id, fixture_id, record_locator, source_field_path)` is structurally provider-agnostic, but `SourceInstance.source_kind` and `provenance_dereference.py` are hardcoded to Jira and GitHub.
7. **Are source-specific fields hardcoded into the canonical types?**  
   *YES.* `JiraIssueState` has Jira-specific workflow categorizations; `GitHubPullRequestState` has fork-specific fields; `CrossSystemStateAlignment` has `jira_ref` and `github_ref`.
8. **Does the evaluator require Jira/GitHub-specific structures?**  
   *YES.* `evidence_evaluation.py` explicitly typechecks `isinstance(jira_state, JiraIssueState)` and `isinstance(gh_state, GitHubPullRequestState)`.
9. **Does cross-system fusion assume Jira + GitHub?**  
   *YES.* `cross_system_fusion.py` takes Jira observations and GitHub fixtures as named parameters and emits `CrossSystemStateAlignment` connecting Jira and GitHub endpoints.
10. **Could EvidenceBundle represent a third provider without changing its fundamental contract?**  
    *YES.* The top-level `EvidenceBundle` container fields (`bundle_id`, `bundle_version`, `observation_contexts`, `observations`, `relationships`, `unresolved_references`, `quality_issues`, `cross_system_alignments`) are purely structural. Opening the literals and generalizing `cross_system_alignments` allows any SaaS evidence to be accommodated without changing the container contract.

---

## 7. Connector Architecture Audit

Audit of integration and abstraction layers against the target architecture:

| Component | Target Role | Current Status in ORBIT | Code Location / Assessment |
| :--- | :--- | :--- | :--- |
| **Generic Transport Layer** | Network I/O, API client, auth headers | **MISSING (By Design)** | System is currently 100% offline fixture-based. Transport belongs outside core. |
| **Provider Connector Interface** | Standardized `fetch_raw()` / `sync()` | **MISSING** | No `BaseConnector` or protocol exists. |
| **Provider Capability Declaration** | Manifest of supported entities/features | **MISSING** | No structured capability declaration; only free-text `coverage_note`. |
| **Canonical Normalization Layer** | Raw payload $\to$ Canonical state | **PARTIAL** | `normalization.py` (Jira) and `github_normalization.py` (GitHub) exist, but normalize to vendor-specific schemas. |
| **Evidence Adapter Layer** | Normalized record $\to$ `EvidenceObservation` | **PARTIAL** | `jira_evidence_adapter.py` exists; GitHub normalization directly emits `EvidenceObservation`. |
| **Provenance Adapter** | Extraction $\to$ `ProvenanceRef` | **PARTIAL** | Each adapter constructs `ProvenanceRef` manually; dereferencer is coupled to 6 collections. |
| **Incremental Sync Abstraction** | Cursors, watermarks, change streams | **MISSING** | Not yet implemented; all current inputs are static fixtures. |
| **Historical-State Abstraction** | Uniform changelog / event representation | **PARTIAL** | Track A has `Change` tuples; Track B only stores point-in-time timestamps. |
| **Rate-Limit / Retry Abstraction** | Backoff, throttling, circuit breakers | **NOT YET NEEDED** | Belongs in external ingestion daemon, not in deterministic core. |
| **Authentication Abstraction** | OAuth, tokens, key rotation | **NOT YET NEEDED** | Belongs in external connector worker. |

---

## 8. Capability Model Audit

A cardinal architectural invariant of ORBIT is:

> **UNAVAILABLE EVIDENCE must never silently become NEGATIVE EVIDENCE.**

### Current Mechanisms for Capability & Absence Distinction
1. **`ObservationContext.coverage_note` (`evidence_types.py:157-170`):**  
   Free-text string intended to record partial capture (e.g. `"pagination_complete: true, reviews: partial"`).  
   *Limitation:* Unstructured; evaluator cannot programmatically branch on it.
2. **`UnresolvedReference` (`evidence_types.py:407-426`):**  
   Explicitly records that an entity cited in a relationship was not observed in the current fixture without asserting that it does not exist in the source system.  
   *Status:* **PROVEN READY.** Successfully used across Waves 1–5.
3. **`FindingSufficiency = "INSUFFICIENT_EVIDENCE"` (`evidence_evaluation.py:53-61`):**  
   Evaluator rules emit `disposition="INSUFFICIENT_EVIDENCE"` when evidence is missing, avoiding negative findings.  
   *Status:* **PROVEN READY.**
4. **Structured Capability Model:**  
   **MISSING.** There is currently no `ProviderCapabilities` dataclass declaring whether a provider supports:
   - PR reviews
   - Work item hierarchy
   - Commit association
   - Changelog / historical transitions
   - Deployment tracking

---

## 9. Provenance Generalization Audit

Inspection of `ProvenanceRef` (`evidence_types.py:200-214`) and `provenance_dereference.py`:

```python
@dataclass(frozen=True, slots=True)
class ProvenanceRef:
    source_instance: SourceInstance
    observation_id: str
    fixture_id: str | None = None
    record_locator: str | None = None
    source_field_path: str | None = None
```

### Generalization Assessment
- **Grammar & Semantics:** The locator grammar `collection[selector]` (e.g. `work_items[PLAT-104]`, `pull_requests[42]`) is elegant, scalable, and provider-neutral.
- **Fail-Closed Taxonomy (ADR-004):** The 7 resolution outcomes (`RESOLVED`, `NOT_FOUND`, `ACCESS_DENIED`, `UNAVAILABLE`, `MALFORMED_LOCATOR`, `UNSUPPORTED_LOCATOR`, `STALE`, `AMBIGUOUS`, `INVALID`) are completely provider-agnostic.
- **Hardcoded Core Couplings:**
  - `_AUTHORIZED_COLLECTIONS` (`provenance_dereference.py:44-51`): Restricts collection names to `{"work_items", "repositories", "branches", "commits", "pull_requests", "reviews"}`.
  - `_resolve_selector_in_list` (`provenance_dereference.py:149-165`): Uses hardcoded field lookups (`number`, `key`, `source_id`, `repo_id`, `sha`, `review_id`).
- **Required Decoupling:** `_AUTHORIZED_COLLECTIONS` and key-lookup strategies must be configurable per `SourceInstance` or dynamically registered by provider adapters.

---

## 10. Historical State Generalization

Audit of historical state representations across Track A and Track B:

### Current Implementation Fragmentation
1. **Track A (Mutation Changelog):**  
   `Change(field: str, from_value: Any, to_value: Any, changed_at: datetime, author: str | None)` in `types.py:16-23`.  
   Models a discrete historical mutation event. Used by `temporal.py` to reconstruct state at period boundaries.
2. **Track B (Point-in-Time Snapshot):**  
   `JiraIssueState` and `GitHubPullRequestState` in `evidence_types.py` capture current timestamps (`created_at`, `updated_at`, `resolved_at`, `merged_at`).  
   *Gap:* As discovered in Wave 4A, Track B currently contains **no changelog or transition events**. Rule XB-04 was deferred specifically because changelog history was omitted from `JiraIssueState`.

### Generalization to Other SaaS Systems
Different enterprise systems expose fundamentally distinct history models:
- **GitLab / Linear:** Linear issue history and MR system notes (similar to Jira/GitHub).
- **Salesforce:** Field History Tracking (sampled, opt-in, non-contiguous).
- **ServiceNow:** Audit tables (`sys_audit`) and journal fields (`sys_journal_field`).
- **Slack / Teams:** Append-only message stream with edit/delete mutation events.

*Conclusion:* The core does not currently possess a unified historical-state abstraction. A canonical `StateTransitionEvent` abstraction will be required when Pass 5 evaluates historical continuity across multi-provider platforms.

---

## 11. Cross-Provider Correlation Audit

Inspection of `cross_system_fusion.py` (`lines 1–288`):

### What is Genuinely Generic:
1. **Pairwise Evidence Matching:** The concept of evaluating cross-system relationships via explicit links (`explicit_metadata`) or textual citations (`lexical_match`).
2. **State Comparison Matrix:** 4-quadrant orthogonal comparison (`CONSISTENT`, `CONFLICTING`, `INSUFFICIENT_EVIDENCE`).
3. **Temporal Comparison Matrix:** 6-outcome relative timeline classification (`COHERENT`, `INVERTED`, `INDETERMINATE`).
4. **Anti-Inference Guarantees:** Prohibiting Cartesian product, transitive linking, and actor equating.

### What is Currently Provider-Specific:
1. **Signature & Parameter Names:** `correlate_cross_system_evidence(jira_observations, github_fixture, ...)`
2. **Mention Policy:** `MentionLexicalPolicy` assumes Jira-style `PROJECT-123` issue keys.
3. **Data Model:** `CrossSystemStateAlignment` explicitly binds `jira_ref: EntityRef` and `github_ref: EntityRef`.
4. **State Mapping Logic:** Concrete `if isinstance(gh_state, GitHubPullRequestState)` and `if isinstance(jira_state, JiraIssueState)` branches.

### Target Multi-Provider Correlation Model:
To support $N$-way connected systems (e.g. Jira $\leftrightarrow$ GitHub, Jira $\leftrightarrow$ Slack, Salesforce $\leftrightarrow$ ServiceNow), `CrossSystemStateAlignment` must become generic:
```python
@dataclass(frozen=True, slots=True)
class CrossSystemStateAlignment:
    subject_ref: EntityRef
    corroborating_ref: EntityRef
    relationship_kind: str
    state_comparison: CrossSystemStateComparison
    temporal_comparison: CrossSystemTemporalComparison
    rationale: str
    provenance_refs: tuple[ProvenanceRef, ...] = ()
```

---

## 12. Track A Protection

### Forensic Verification of Track A Isolation
1. **Codebase Zero-Diff:**
   ```bash
   git diff develop...HEAD -- src/shadow_orbit/evaluation.py src/shadow_orbit/temporal.py src/shadow_orbit/normalization.py src/shadow_orbit/types.py
   ```
   *Diff is strictly empty.*
2. **Reverse Dependency Audit:**
   No Track A module imports any Track B module (`evidence_types`, `evidence_assembly`, `cross_system_fusion`, `evidence_evaluation`, `provenance_dereference`, etc.).
3. **Architectural Separation:**
   Track A remains completely sealed as the historical Jira sprint baseline. The expansion to universal connected systems is **strictly a Track B evolution**.

---

## 13. Speculative Architecture Review

Every candidate abstraction evaluated against the **"Evidence of Need"** test:

| Candidate Abstraction | Classification | Rationale & Governance Ruling |
| :--- | :--- | :--- |
| **Decoupling `SourceKind` / `EntityKind` Literals** | **NOW** | Directly blocks any 3rd provider. Must be string-based with adapter validation. |
| **Generic `CrossSystemStateAlignment` (`subject_ref` / `corroborating_ref`)** | **NOW** | Prevents vendor name leakage in cross-system comparisons. |
| **Canonical Entity Payloads (`WorkItemState`, `CodeChangeState`)** | **NOW** | Allows evaluators to evaluate work items and code changes regardless of vendor. |
| **Decoupled Provenance Collection Registry** | **NOW** | Prevents locator failure when non-Jira/GitHub collections are referenced. |
| **Structured `ProviderCapabilities` Model** | **LATER** | Needed when rules branch on provider capabilities, but not for the initial 3rd provider adapter. |
| **Generic Mention / Citation Extractor DSL** | **LATER** | Regex-based policies work well; DSL is premature before 3+ distinct text citation formats exist. |
| **Universal Connector Interface (`BaseConnector`)** | **LATER** | Needed once live network transports are introduced; premature while testing offline fixtures. |
| **Universal Knowledge Graph Engine** | **SPECULATIVE** | Graph databases / semantic web ontologies would violate determinism and simplicity. |
| **Dynamic Plugin Marketplace / Hot-Reload** | **SPECULATIVE** | Completely unnecessary for an auditable, deterministic enterprise engine. |
| **Universal Schema Mapping DSL** | **SPECULATIVE** | Python dataclasses and standard functions provide type-safe, auditable mappings without custom DSL overhead. |
| **Universal OAuth / Identity Platform** | **SPECULATIVE** | Auth belongs strictly at the external ingestion boundary. |

---

## 14. Hypothetical Third-Provider Test: Linear

To evaluate extensibility without building speculative code, we execute a rigorous thought experiment adding **Linear** (modern issue tracker) as a third connected system alongside Jira and GitHub.

### Expected Provider-Specific Work (Legitimate Boundary Work)
1. **Ingestion & Normalizer:**
   - Define `linear_fixture` schema (or live client).
   - Implement `linear_normalization.py` to extract teams, issues, states, cycles, and timestamps.
2. **Mention Policy:**
   - Configure Linear issue key pattern (e.g. `ENG-\d+`, `LIN-\d+`).
3. **Evidence Adapter:**
   - Implement `linear_evidence_adapter.py` mapping normalized Linear issues to canonical `WorkItemState` with `SourceInstance(source_kind="linear", instance_id="org-slug")`.
   - Emit `EvidenceObservation` instances with accurate `ProvenanceRef` locators (`issues[ENG-104]`).

### Should Require ZERO Core Changes (Target State)
- `EvidenceBundle` container and validation logic.
- `provenance_dereference.py` locator parsing and resolution.
- `evidence_evaluation.py` rules (e.g. XB-01 and XB-02 should evaluate Linear issue + GitHub PR identically to Jira issue + GitHub PR).
- Deterministic canonical sorting, serialization, and SHA-256 finding identity generation.

### What WOULD Break in Today's Code (Current State Gaps)
1. `SourceKind = Literal["jira", "github"]` in `evidence_types.py:28` raises type errors on `"linear"`.
2. `EntityKind = Literal[...]` in `evidence_types.py:32` raises type errors on `"linear_issue"`.
3. `evidence_assembly.py:627` checks `if ref.source_instance.source_kind == "jira"` and fails validation for `"linear"`.
4. `provenance_dereference.py:44` rejects collection `"issues"` as unauthorized.
5. `CrossSystemStateAlignment` in `evidence_types.py:438` requires `jira_ref` (cannot represent `linear_ref`).
6. `cross_system_fusion.py:161` checks `isinstance(jira_state, JiraIssueState)` and ignores Linear states.
7. `evidence_evaluation.py:441` checks `isinstance(jira_state, JiraIssueState)` and suppresses findings for Linear.

---

## 15. Current vs Target Architecture

```text
CURRENT PASS 4 ARCHITECTURE:
┌─────────────────┐       ┌─────────────────┐
│  Jira Fixture   │       │ GitHub Fixture  │
└────────┬────────┘       └────────┬────────┘
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│  Jira Adapter   │       │ GitHub Normalizer│
└────────┬────────┘       └────────┬────────┘
         ▼                         ▼
┌───────────────────────────────────────────┐
│   EvidenceBundle (Jira/GitHub Hardcoded)  │
│   - SourceKind: Literal["jira", "github"] │
│   - EntityKind: "jira_*", "github_*"      │
│   - State: JiraIssueState, GitHubPRState  │
│   - Alignments: jira_ref, github_ref      │
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│ Evaluator (Checks Jira/GitHub Dataclasses)│
└───────────────────────────────────────────┘


TARGET UNIVERSAL CONNECTED SYSTEMS ARCHITECTURE:
┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  Jira Ingest   │  │ GitHub Ingest  │  │ Linear Ingest  │  │ GitLab Ingest  │
└───────┬────────┘  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
        ▼                   ▼                   ▼                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                  PROVIDER BOUNDARY: CONNECTORS & ADAPTERS                  │
│  - Vendor API transport, pagination, rate limits, authentication           │
│  - Vendor schema normalization & capability declaration                    │
│  - Emits canonical EntityRefs, ProvenanceRefs & Canonical State Payloads   │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    DETERMINISTIC ORBIT CORE (GENERIC)                      │
│                                                                            │
│  EvidenceBundle Container:                                                 │
│    - Open SourceKind / EntityKind (string-based with boundary validation)  │
│    - Canonical States: WorkItemState, CodeChangeState, ContainerState      │
│    - Generic Alignments: subject_ref, corroborating_ref                    │
│                                                                            │
│  Provenance Dereferencer:                                                  │
│    - Generic locator grammar collection[selector] with provider registry   │
│                                                                            │
│  Cross-System Fusion Engine:                                               │
│    - Pairwise entity matching (citations, explicit links)                  │
│    - Orthogonal 4-quadrant state & 6-outcome temporal comparison           │
│                                                                            │
│  Deterministic Evaluator:                                                  │
│    - Evaluates canonical concepts (WorkItem vs CodeChange)                 │
│    - Strict anti-inference invariants preserved                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Architectural Gaps

1. **Closed Type Literals (Gap G1):** `SourceKind` and `EntityKind` are static `Literal` types restricted to Jira and GitHub.
2. **Missing Canonical State Abstractions (Gap G2):** Core payload types (`JiraIssueState`, `GitHubPullRequestState`) are vendor-branded. The core lacks canonical `WorkItemState` and `CodeChangeState` abstractions.
3. **Vendor-Coupled Alignment Schema (Gap G3):** `CrossSystemStateAlignment` fields are named `jira_ref` and `github_ref`.
4. **Hardcoded Provenance Collections (Gap G4):** `provenance_dereference.py` only permits 6 collections and hardcodes their primary key fields.
5. **Evaluator Coupling (Gap G5):** Evaluator rules check vendor state classes rather than canonical state properties.
6. **Absence of Structured Capability Declarations (Gap G6):** No programmatic manifest distinguishing unsupported features from negative observations.
7. **Fragmented History Models (Gap G7):** Track A has mutation changelogs; Track B has point-in-time timestamps.

---

## 17. Recommended Boundaries

To preserve architectural integrity without speculative over-engineering:

1. **Keep External Complexity Outside Core:**  
   Authentication, network retry, pagination, OAuth, and raw schema transformations must remain strictly within provider-specific ingestion adapters. The ORBIT core must remain 100% offline, deterministic, and pure in-memory.
2. **Normalize at the Ingestion Boundary:**  
   A Jira issue, Linear ticket, GitHub issue, or GitLab issue must all enter the `EvidenceBundle` as canonical `WorkItemState` observations (with vendor-specific raw payloads preserved in provenance if needed).
3. **Decouple Types Gradually (Wave-Gated):**  
   Do not build a universal ontology DSL. Replace closed literals with validated string types and introduce canonical state classes as new providers demand them.

---

## 18. Pass 5 Architectural Scorecard

| Architectural Area | Rating | Justification & Current State |
| :--- | :--- | :--- |
| **1. Provider Isolation** | `READY WITH BOUNDED GAP` | Jira and GitHub adapters are isolated, but core types hardcode vendor names. |
| **2. Connector Boundary** | `ARCHITECTURAL GAP` | No formalized connector protocol; integration is performed via ad-hoc scripts. |
| **3. Canonical Entities** | `ARCHITECTURAL GAP` | Payloads are vendor-specific (`JiraIssueState`); canonical `WorkItemState` missing. |
| **4. EvidenceBundle Neutrality** | `READY WITH BOUNDED GAP` | Container structure is generic; payload union and alignment fields are vendor-specific. |
| **5. Provenance Neutrality** | `READY WITH BOUNDED GAP` | Locator grammar is generic; collection authorization is hardcoded to 6 names. |
| **6. Historical-State Neutrality**| `ARCHITECTURAL GAP` | Fragmented between Track A changelogs and Track B point-in-time timestamps. |
| **7. Cross-Provider Relationships**| `READY WITH BOUNDED GAP` | `EvidenceRelationship` is generic; `CrossSystemStateAlignment` is Jira/GitHub-specific. |
| **8. Capability Representation** | `ARCHITECTURAL GAP` | Only unstructured `coverage_note: str` exists; no structured capability declaration. |
| **9. Deterministic Evaluator Isolation**| `PROVEN READY` | Evaluator is 100% deterministic, offline, permutation-invariant, and anti-inferential. |
| **10. Track A Isolation** | `PROVEN READY` | Strictly 0 diff against commit `6d82d12`; zero reverse dependencies. |
| **11. Future SaaS Extensibility** | `READY WITH BOUNDED GAP` | High feasibility; bounded refactoring of literals and state payloads unlocks extensibility. |
| **12. Multi-Provider State** | `NOT YET TESTED` | Pairwise Jira $\leftrightarrow$ GitHub proven; 3+ provider organizational synthesis unproven. |

---

## 19. Human Decision Gate

The following decisions require explicit human review and approval before proceeding to Pass 5 Wave 1:

- **Decision D1 — Decouple Type Literals vs Retain Closed Taxonomy:**  
  *Option A (Recommended):* Relax `SourceKind` and `EntityKind` to `str` with boundary validation in provider adapters, opening the core to arbitrary SaaS sources.  
  *Option B:* Keep `Literal` closed and expand it manually for every new provider.

- **Decision D2 — Introduce Canonical State Models vs Provider-Specific States:**  
  *Option A (Recommended):* Define canonical `WorkItemState` and `CodeChangeState` in `evidence_types.py`. Adapters map Jira/GitHub/Linear into these canonical states, allowing evaluator rules (XB-01..XB-03) to run universally.  
  *Option B:* Keep `JiraIssueState`, `GitHubPullRequestState`, and add `LinearIssueState`, `GitLabMergeRequestState`, updating the evaluator with branching `isinstance` logic for each new provider.

- **Decision D3 — Generalize CrossSystemStateAlignment Endpoints:**  
  *Option A (Recommended):* Rename `jira_ref` and `github_ref` to `subject_ref` and `corroborating_ref` (or `object_ref`), making cross-system alignment universal across any two connected systems.  
  *Option B:* Retain `jira_ref` and `github_ref` and add additional vendor pair alignment structs (`jira_linear`, `salesforce_servicenow`).

- **Decision D4 — Selection of Next Proving Ground / Qualification Target:**  
  *Option A:* Add a modern 3rd provider offline fixture (e.g. Linear or GitLab) to validate multi-provider canonical normalization.  
  *Option B:* Perform enterprise qualification on real Jira+GitHub data (e.g. Apache Kafka or Camel) to harden the existing dual-system pipeline before expanding to a 3rd provider.

---

## 20. Recommended Next Step & Final Governance Status

### Recommended Next Step: Pass 5 Wave 1
If approved by governance, **Pass 5 Wave 1** should execute a **Controlled Core Decoupling (Bounded Refactoring)**:
1. Generalize `SourceKind` and `EntityKind` to validated string identifiers.
2. Abstract `CrossSystemStateAlignment` endpoints from `jira_ref`/`github_ref` to `subject_ref`/`corroborating_ref`.
3. Introduce canonical `WorkItemState` and `CodeChangeState` models with backward-compatible adapters for Jira and GitHub.
4. Verify 100% green regression test suite across all 711 existing tests.

---

```text
============================================================
FINAL GOVERNANCE STATUS:
PASS 5 WAVE 0 — RECONNAISSANCE COMPLETE
============================================================
```
