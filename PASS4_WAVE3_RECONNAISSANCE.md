# PASS 4 / WAVE 3 — CROSS-SYSTEM FUSION RECONNAISSANCE & CONTRACT DESIGN
## Forensic Architecture Analysis & Integration Contract Definition (P3-07 / P2.5-19)

**Document:** PASS4_WAVE3_RECONNAISSANCE.md  
**Pass:** Pass 4 / Milestone 2 / Wave 3  
**Date:** 2026-09-28  
**Author:** Forensic Software Engineering & Evidence Integrity Review  
**Branch:** `remediation/pass3-controlled-hardening`  
**Governing Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`develop`)  
**Audited Working Head:** `e967ad57ea3b37cef4266134537acbb34e9ae715`  
**Regression State:** 641 passed, 0 failed, 0 skipped  
**Mahout Invariants:** 412 accepted, 12 STALLED_WORK, 56 incomplete, 370 missing due, 0 mutations, repeatable=True  

---

## 1. Executive Summary

This reconnaissance report executes **Pass 4 Wave 3** as an architecture-first contract definition gate. In accordance with the governing instructions, **no production code has been modified and no live connectors have been implemented.**

### Central Question
> *"What evidence is actually sufficient to establish a cross-system relationship between a Jira work item and a GitHub artifact?"*

### Primary Forensic Findings
1. **P2.5-19 / P3-07 Status**: Cross-system evidence fusion between Jira and GitHub currently exists in the repository **only** in the form of literal regex-based mention extraction (`kind="mentions"`, `basis="lexical_match"` via `github_mentions.py`). No semantic fusion, explicit cross-system metadata links, or temporal alignment assertions currently exist in code.
2. **Current Vocabulary Constraint**: The existing type contract in `evidence_types.py` permits only two values for `RelationshipBasis`: `"structural_association"` and `"lexical_match"`. All structural associations are strictly GitHub-internal (`belongs_to_repository`, `review_of`, `has_head_branch`, etc.). There is no `EXPLICIT_LINK` relationship kind or basis defined in the codebase.
3. **Data Schema Constraint**: Neither the Jira fixture schema (`shadow-jira-fixture-v1`) nor the GitHub fixture schema (`shadow-github-fixture-v1`) contains structured fields for cross-system linkage (e.g., Jira issue links, remote issue links, GitHub development panel links, or PR tracking issue IDs).
4. **Non-Inference Imperative**: Lexical matches of a Jira key (e.g., `PLAT-101`) in a PR title, branch name, or commit message are correlation signals representing **`DECLARED_MENTION`** only. They do not constitute proof of implementation responsibility, author identity, completion, merge intent, or ticket closure.
5. **Evaluation Boundary**: Week-One rule evaluation (`evaluate_week_one_rules(NormalizedFixture)`) remains strictly separated and untouched. It does not consume `EvidenceBundle` and must not be altered.

---

## 2. Current Architecture Map

The existing evidence processing pipeline follows this strict unidirectional DAG:

```
[Raw Jira Fixture]                               [Raw GitHub Fixture]
       │                                                  │
       ▼                                                  ▼
validate_fixture()                              validate_github_fixture()
       │                                                  │
       ▼                                                  ▼
normalize_fixture()                             normalize_github_fixture()
       │                                                  │
       ▼                                                  ▼
adapt_jira_evidence()                           resolve_github_relationships()
  (produces j_obs)                                (produces gh_structural_rels)
       │                                                  │
       └────────────────────────┬─────────────────────────┘
                                │
                                ▼
                  resolve_github_jira_mentions()
                    (produces mention_rels,
                     basis="lexical_match")
                                │
                                ▼
                    assemble_evidence_bundle()
                    (produces EvidenceBundle)
                                │
                                ▼
                    validate_evidence_bundle()
                    (with fixtures_by_id)
                                │
                        [EvidenceBundle]
                                │
                (Track B Evaluator - NOT YET IMPLEMENTED)
                                │
                                ▼
                    evaluate_evidence_bundle()
                    (PROPOSED Milestone 2 layer)
```

**Parallel Protected Baseline (Track A):**
```
normalize_fixture() ──► calculate_supporting_facts() ──► evaluate_week_one_rules() ──► RuleMatch tuple
```
*Track A is frozen and completely independent of EvidenceBundle.*

---

## 3. Actual Jira Evidence Model

Jira evidence is captured at three layers:

### A. Raw / Normalized Jira Model (`types.py`, `normalization.py`)
- **`WorkItem`** dataclass:
  - Identity: `source_id: str`, `key: str` (e.g. `"PLAT-101"`), `item_type: str`
  - Classification: `source_priority: str`, `priority_band: PriorityBand`, `source_status: str`, `status_category: StatusCategory`
  - Assignee: `assignee: str | None`
  - Temporal fields: `created_at: datetime`, `updated_at: datetime`, `resolved_at: datetime | None`, `due_at: datetime | None`
  - Historical state: `planned_at_period_start: bool | None`, `history_complete: bool`, `source_status_at_period_start: str | None`
  - Changes: `changes: tuple[Change, ...]` (`field`, `from_value`, `to_value`, `changed_at`)

### B. CSE Evidence Adapter (`jira_evidence_adapter.py`)
- Maps `WorkItem` $\to$ `EvidenceObservation`:
  - `entity_ref`: `EntityRef(source_instance, "jira_issue", key)`
  - `observation_context`: `ObservationContext(observation_id, source_instance, ...)`
  - `observed_state`: `JiraIssueState` (`key`, `source_status`, `source_priority`, `status_category`, `priority_band`, `assignee`, `created_at`, `updated_at`, `resolved_at`, `due_at`)
  - `provenance_refs`: `ProvenanceRef(source_instance, observation_id, fixture_id, record_locator="work_items[idx]")`

### Forensic Deficiencies in Current Jira Model
- No remote links, issue links, or development panel metadata.
- No repository associations or external commit tracking.
- `assignee` is an unverified display string (no verified cross-system identity).

---

## 4. Actual GitHub Evidence Model

GitHub evidence is captured in `github_validation.py`, `github_normalization.py`, and `evidence_types.py`:

### Entity Kinds & State Dataclasses
1. **`github_repository`** (`GitHubRepositoryState`):
   - `owner: str`, `name: str`, `default_branch: str | None`
2. **`github_branch`** (`GitHubBranchState`):
   - `name: str`, `head_commit_id: str | None`
3. **`github_commit`** (`GitHubCommitState`):
   - `sha: str`, `message: str`, `author_login: str | None`, `committed_at: datetime | None`
4. **`github_pull_request`** (`GitHubPullRequestState`):
   - `number: int`, `title: str`, `state: str` (`"open"`, `"closed"`, `"merged"`)
   - `author_login: str | None`
   - `created_at: datetime | None`, `merged_at: datetime | None`
   - `target_branch: str | None`, `source_branch: str | None`
   - `head_commit_sha: str | None`, `base_commit_sha: str | None`
   - `head_repository_id: str | None`, `is_fork: bool | None`
   - `pull_request_commit_shas: tuple[str, ...]`
5. **`github_review`** (`GitHubReviewState`):
   - `review_id: str`, `state: str` (`"APPROVED"`, `"CHANGES_REQUESTED"`, etc.)
   - `reviewer_login: str | None`, `submitted_at: datetime | None`

### Forensic Deficiencies in Current GitHub Model
- No PR `body` or `description` field in schema.
- No PR comments, commit comments, or review comments.
- No explicit `closing_issues_references` or linked issue metadata.
- Author identity is an unverified `author_login` string.

---

## 5. Existing Cross-System Relationship Behavior

Cross-system relationships currently exist **only** through `resolve_github_jira_mentions()` (`src/shadow_orbit/github_mentions.py`).

| Property | Current Value | Authority |
|---|---|---|
| Permitted `RelationshipKind` | `"mentions"` | `evidence_types.py:60` |
| Permitted `RelationshipBasis` | `"lexical_match"` | `evidence_types.py:64` |
| Subject Entity | GitHub entity (`pull_request`, `commit`, `branch`) | `github_mentions.py:310` |
| Object Entity | Jira entity (`jira_issue`) | `github_mentions.py:311` |
| Subject Scope | Source observation ID in GitHub context | `github_mentions.py:314` |
| Object Scope | Target observation ID in Jira context | `github_mentions.py:315` |
| Provenance | Points to exact GitHub field containing text match | `github_mentions.py:273-279` |

If the mentioned Jira key is unobserved or ambiguous in the provided Jira observations, an `UnresolvedReference` is emitted instead of an `EvidenceRelationship`.

---

## 6. Current Lexical Matching Behavior

- **Pattern**: Regex built from configured policy: `r"\b(?:" + "|".join(prefixes) + r")-\d+\b"`
- **Policy Enforcement**: `MentionLexicalPolicy` requires uppercase ASCII prefixes (`^[A-Z]+$`), sorted by descending length for deterministic longest-match alternation (`github_mentions.py:182-192`).
- **Scanned Fields**:
  - `github_pull_request`: `title`, `source_branch`, `target_branch`
  - `github_commit`: `message`
  - `github_branch`: `name`
- **Deduplication**:
  - Multiple occurrences of the same key in the same field collapse to one `ProvenanceRef`.
  - Same key across different fields aggregates multiple `ProvenanceRef` instances onto one logical edge.
- **Ambiguity**:
  - If multiple Jira observations share the same issue key, the mention is marked `UnresolvedReference` with reason `"Ambiguous Jira target: multiple observations found..."`.

---

## 7. Identity Evidence Matrix

| Claimed Identity | Available Data in ORBIT | Forensic Reliability | Permitted Conclusion |
|---|---|---|---|
| **Jira Issue Identity** | `key` (e.g. `PLAT-101`), `source_id` | Authoritative within `source_instance` | Authoritative issue identity |
| **GitHub PR Identity** | `repo_id/number` (e.g. `repo-core/101`) | Authoritative within `source_instance` | Authoritative PR identity |
| **GitHub Commit Identity** | `repo_id/sha` (e.g. `repo-core/c0ffee1`) | Cryptographically authoritative | Authoritative commit identity |
| **Actor Identity** (`assignee` vs `author_login`) | `assignee: "Alice"` vs `author_login: "alice"` | **UNVERIFIED / UNRELIABLE** | **NEVER infer same person**. Textual username overlap is not cryptographic identity. |
| **Work Correlation** (PR mentions key) | PR title contains `"PLAT-101"` | Correlational only | **`DECLARED_MENTION`** only. Does not prove PR implements the issue. |
| **Multi-Repo Correlation** (Multiple repos mention key) | `repo-a` and `repo-b` both mention `PLAT-101` | Ambiguous / multi-part | Preserve both mentions independently. Do not infer primary repository. |

---

## 8. Temporal Evidence Matrix

| Jira Timestamp | GitHub Timestamp | Logical Meaning of Difference | Permitted Classification | Forbidden Classification |
|---|---|---|---|---|
| `resolved_at: T_j` | `merged_at: T_g` (`T_g <= T_j`) | PR merged before issue marked Done | `CONSISTENT` (coherent timeline) | Do not infer merge caused resolution |
| `resolved_at: T_j` | `merged_at: T_g` (`T_g > T_j`) | PR merged after issue marked Done | `POTENTIAL_POST_RESOLUTION_ACTIVITY` | **DO NOT classify as CONTRADICTION** (may be hotfix, follow-up, or delayed merge) |
| `created_at: T_j` | `committed_at: T_g` (`T_g < T_j`) | Commit predates Jira issue creation | `PRE_EXISTING_WORK` | **DO NOT classify as CONTRADICTION** (reused commit, rebasing, or retrospective ticket) |
| `updated_at: T_j` | `source_cutoff: T_c` (`T_j > T_c`) | Jira updated after cutoff | `STALE` (post-cutoff) | Do not evaluate as normal period activity |
| `resolved_at: None` | `merged_at: T_g` | PR merged while issue still Open | `OPEN_WITH_MERGED_CODE` | **DO NOT classify as CONTRADICTION** (incomplete workflow) |
| `resolved_at: T_j` | `merged_at: None` (PR Open) | Issue resolved while PR still Open | `RESOLVED_WITH_OPEN_PR` | `CONFLICTING_STATE_INDICATOR` (only if contract mandates PR completion for Done) |

---

## 9. Explicit-Link Contract

For a cross-system relationship to be classified as **`EXPLICIT_LINK`**, the following deterministic conditions must all be satisfied:

1. **Source System Structure**: The link must originate from a structured API field explicitly designated for issue linkage:
   - Jira: `issuelinks`, `remotelinks`, or structured development panel entity metadata.
   - GitHub: Native issue integration metadata (`closing_issues_references` or GraphQL linked issues).
2. **Explicit Direction & Semantics**: The link must state an explicit relationship role (e.g., `fixes`, `resolves`, `relates_to`).
3. **No Regex / Text Extraction**: A link derived from regex search of unformatted text cannot be an `EXPLICIT_LINK`.
4. **Current Repository Finding**: Under the current schema (`shadow-jira-fixture-v1` and `shadow-github-fixture-v1`), **zero explicit links can be formed** because neither schema provides the required structured metadata fields.

---

## 10. Declared-Mention Contract

A relationship is classified as **`DECLARED_MENTION`** when:

1. **Extraction Source**: Extracted via deterministic lexical matching against a configured `MentionLexicalPolicy` from:
   - PR `title`, `source_branch`, `target_branch`
   - Commit `message`
   - Branch `name`
2. **Provenance**: Supported by a `ProvenanceRef` containing:
   - `record_locator` pointing to the source GitHub record
   - `source_field_path` identifying the exact field where the text matched
3. **Semantic Limits**:
   - Represents a declared textual citation only.
   - Never implies code ownership, task completion, or developer intent.
   - Preserves `basis="lexical_match"`.

---

## 11. Contradiction / Conflict Semantics

A genuine **`CONTRADICTION`** or **`CONFLICTING`** state can only be asserted when two authoritative evidence observations are mutually exclusive under governing domain rules:

### Genuine Contradictions
1. **Endpoint Identity Incompatibility**:
   - Explicit integration metadata states PR #101 belongs to Repository `northstar-core`, while repository observation states PR #101 belongs to `northstar-infra`.
2. **Mutual Exclusion Contradiction**:
   - An authoritative single-issue constraint asserts an artifact can only be bound to Jira Item X, but an equally authoritative structured record binds it to Jira Item Y.
3. **Resolved-vs-Unresolved Contradiction**:
   - An edge is recorded as both resolved and unresolved in the same bundle (existing Invariant 6 in `evidence_assembly.py`).

### Non-Contradictions (Forbidden Classifications)
- Different timestamps across systems are **NOT** contradictions.
- Open PR vs Done Jira issue is **NOT** a contradiction unless an explicit business rule defines it as forbidden; it is `CONFLICTING_STATE_INDICATOR` or `INCOMPLETE_ALIGNMENT`.
- Missing fields or absence of mention is **NOT** a contradiction; it is `INSUFFICIENT_EVIDENCE`.

---

## 12. Insufficient-Evidence Semantics

In accordance with ORBIT's core principle (*Unknown $\neq$ False, Missing $\neq$ Complete*):

1. **Unobserved Entity**: When a PR mentions `PLAT-999`, but `PLAT-999` is not in Jira observations, emit `UnresolvedReference(reason="Mentioned Jira key was not observed")`.
2. **Partial Fixture Capture**: When `source_completeness.pull_requests_complete == False`, absence of a PR cannot be evaluated as "PR does not exist". It must be classified as `INSUFFICIENT_EVIDENCE`.
3. **Missing Timestamps**: When a commit has `committed_at: null` or invalid timestamp, temporal ordering cannot be evaluated; temporal status must be `INDETERMINATE`.

---

## 13. Ambiguity Handling

Ambiguity occurs when multiple entities match an identifier without a unique resolution path:

1. **Multiple Jira Observations for Same Key**:
   - Currently handled in `github_mentions.py:321-336`: Emits `UnresolvedReference` with reason `"Ambiguous Jira target: multiple observations found"`.
2. **Multiple Mentions in Same PR**:
   - If PR #101 mentions both `PLAT-101` and `PLAT-102`, emit two distinct `EvidenceRelationship` edges. Do not arbitrarily pick one or assume primary linkage.
3. **Multiple PRs Mentioning Same Issue**:
   - Emit multiple `EvidenceRelationship` edges from each PR to the Jira issue. Aggregation belongs to future evaluation stages, not to the relationship extractor.

---

## 14. Determinism Requirements

Any cross-system fusion implementation must preserve total determinism:

1. **Permutation Invariance**:
   - Processing GitHub observations in reverse order must produce the identical tuple of relationships.
   - Processing Jira observations in different order must produce the identical tuple of relationships.
2. **Deterministic Sort Keys**:
   - Relationships sorted by: `(kind, subject_ref.entity_id, object_ref.entity_id, subject_obs_id, object_obs_id)`
   - Unresolved references sorted by: `(relationship_kind, source_ref.entity_id, target_entity_kind, target_identifier, reason)`
   - Quality issues sorted by: `(code, message, subject_scope, subject_ref_key)`
3. **Pure Functions**: Zero side effects, zero I/O, zero global mutable state, zero dependency on dictionary iteration order.

---

## 15. Proposed Minimal Correlation Boundary

The smallest viable, deterministic architecture for cross-system fusion (Wave 3 / Milestone 2):

### Pure Module: `src/shadow_orbit/cross_system_fusion.py` (Proposed)
```python
def correlate_cross_system_evidence(
    jira_observations: tuple[EvidenceObservation, ...],
    github_fixture: NormalizedGitHubFixture,
    mention_policy: MentionLexicalPolicy,
    temporal_interval: tuple[datetime, datetime] | None = None,
) -> CrossSystemFusionResult:
    """Pure, deterministic fusion of Jira and GitHub evidence."""
```

### Proposed Return Type: `CrossSystemFusionResult`
```python
@dataclass(frozen=True, slots=True)
class CrossSystemFusionResult:
    declared_mentions: tuple[EvidenceRelationship, ...]
    explicit_links: tuple[EvidenceRelationship, ...]      # empty under current fixtures
    unresolved_references: tuple[UnresolvedReference, ...]
    state_alignments: tuple[CrossSystemStateAlignment, ...]
    quality_issues: tuple[QualityIssue, ...]
```

### Proposed Alignment Type: `CrossSystemStateAlignment`
```python
@dataclass(frozen=True, slots=True)
class CrossSystemStateAlignment:
    jira_ref: EntityRef
    github_ref: EntityRef
    relationship_kind: str                               # e.g. "mentions"
    state_comparison: Literal["CONSISTENT", "CONFLICTING", "INSUFFICIENT_EVIDENCE"]
    temporal_comparison: Literal["COHERENT", "INVERTED", "INDETERMINATE"]
    rationale: str
    provenance_refs: tuple[ProvenanceRef, ...]
```

---

## 16. EvidenceBundle Interaction

- `EvidenceBundle` currently accepts `github_mention_relationships` and `github_mention_unresolved`.
- If new cross-system alignments or explicit links are introduced, they must either:
  - Be represented as `EvidenceRelationship` with explicitly authorized `RelationshipKind` and `RelationshipBasis` values; OR
  - Be added as a new immutable collection field on `EvidenceBundle` (e.g. `cross_system_alignments: tuple[...] = ()`), requiring bundle version bump (`"1.1.0"`).
- `validate_evidence_bundle()` will validate the provenance and endpoint references of these new edges against `fixtures_by_id`.

---

## 17. Evaluation Interaction

- **Week-One Evaluation (`evaluate_week_one_rules`)**:
  - MUST REMAIN UNTOUCHED. It evaluates only Jira `NormalizedFixture` rules (STALLED_WORK, etc.).
- **Milestone 2 Joint Evaluator (`evaluate_evidence_bundle`)**:
  - Future separate work. It will consume the validated `EvidenceBundle` and evaluate cross-system rules (e.g., unlinked PRs, post-resolution commits, status contradictions).
  - It will NOT alter or replace the Week-One evaluation.

---

## 18. Live Connector Boundary

- **Absolute Prohibition**: Wave 3 and all Milestone 2 offline phases strictly prohibit live connectors.
- **Rationale**:
  1. Live APIs introduce non-determinism, network latency, rate limits, and authentication state.
  2. Safety invariant: `Jira mutations = 0` must never be compromised.
  3. All contract logic must be verified deterministically against offline golden fixtures before live connectors are considered.

---

## 19. Adversarial Test Matrix (Proposed for Wave 3 Implementation)

| Test ID | Adversarial Scenario | Expected Outcome | Rationale |
|---|---|---|---|
| **ADV-F01** | Jira key appearing in unrelated PR title (accidental text match) | Emitted as `DECLARED_MENTION`, never `EXPLICIT_LINK` | Lexical mention is not proof of implementation |
| **ADV-F02** | Same Jira key mentioned across multiple distinct repositories | Multiple independent `DECLARED_MENTION` edges | No arbitrary primary repo selection |
| **ADV-F03** | PR title mentions multiple distinct Jira keys | Multiple independent `DECLARED_MENTION` edges | No multi-key suppression |
| **ADV-F04** | Jira key in commit message but absent from PR title | Edge emitted from commit observation, not PR | Provenance reflects exact source field |
| **ADV-F05** | Branch name contains Jira key (`feature/PLAT-101`) | Edge emitted from branch observation with `field:name` | Accurate provenance attribution |
| **ADV-F06** | Key with similar prefix but lowercase (`plat-101`) | No match emitted | Policy strictly enforces uppercase ASCII |
| **ADV-F07** | Number-only or prefix-only string (`PLAT-`, `101`) | No match emitted | Word boundary and full key format enforced |
| **ADV-F08** | Closed Jira issue with later GitHub commit timestamp | State alignment `CONFLICTING` or `POST_RESOLUTION_ACTIVITY` | Never classified as structural contradiction |
| **ADV-F09** | GitHub commit timestamp after observation cutoff | Provenance dereference status `STALE` | Temporal cutoff guard active |
| **ADV-F10** | GitHub commit with `committed_at: null` | Temporal comparison `INDETERMINATE` | Unknown $\neq$ False |
| **ADV-F11** | Duplicate GitHub observations for same PR number | Validation quarantine in `github_validation` | Clean evidence boundary |
| **ADV-F12** | Reversed input order of GitHub observations | Bit-for-bit identical relationship output | Permutation invariance guaranteed |
| **ADV-F13** | Mention of unobserved Jira key (`PLAT-999`) | Emits `UnresolvedReference` | Explicit incompleteness record |
| **ADV-F14** | Ambiguous Jira key (2 observations with key `PLAT-101`) | Emits `UnresolvedReference(reason="Ambiguous...")` | Ambiguity preserved |

---

## 20. Security / Mutation Implications

1. **Jira Mutation Guard**:
   - `ReadOnlyJiraGuard` remains active throughout all tests.
   - Zero `POST`, `PUT`, `PATCH`, `DELETE` operations permitted.
2. **GitHub Read-Only Constraint**:
   - Zero GitHub API calls or mutations.
   - Offline JSON fixtures only.
3. **No Credential Exposure**:
   - Fixtures contain synthetic identifiers only (`"northstar"`, `"repo-core"`, `"PLAT-101"`).

---

## 21. Risks and Unresolved Questions

1. **Schema Expressiveness Risk**: Neither Jira nor GitHub fixtures currently have fields for explicit linking. Can Milestone 2 legitimately prove `EXPLICIT_LINK` without updating the fixture schema versions (`shadow-jira-fixture-v2`, `shadow-github-fixture-v2`)?
2. **Relationship Vocabulary Extension**: Does introducing `EXPLICIT_LINK` require updating `evidence_types.py` (`RelationshipKind`, `RelationshipBasis`), and will this break existing serialization golden tests?
3. **Temporal Incoherence vs Contradiction**: Should post-resolution GitHub activity be a quality issue, a relationship attribute, or a findings rule in the future evaluator?

---

## 22. Explicit List of Decisions Requiring Human Approval

Before proceeding to any implementation in Wave 3 or beyond, human architectural approval is required on the following:

- [ ] **Decision D1: Relationship Taxonomy**: Approve the three-state taxonomy (`EXPLICIT_LINK`, `DECLARED_MENTION`, `CONTRADICTION`) and state-comparison taxonomy (`CONSISTENT`, `CONFLICTING`, `INSUFFICIENT_EVIDENCE`).
- [ ] **Decision D2: Schema Update for Explicit Links**: Decide whether to:
  - *(Option A)* Keep current fixture schemas as-is, treating all existing cross-system relationships strictly as `DECLARED_MENTION` (`EXPLICIT_LINK` remains an empty set until future fixture updates). *(Recommended)*
  - *(Option B)* Extend fixture schemas with explicit link fields (`shadow-jira-fixture-v2` / `shadow-github-fixture-v2`).
- [ ] **Decision D3: Cross-System Fusion Placement**: Approve placing the fusion logic in a dedicated pure module `src/shadow_orbit/cross_system_fusion.py` feeding into `assemble_evidence_bundle()`.
- [ ] **Decision D4: EvidenceBundle Type Expansion**: Decide whether cross-system state comparisons (`CONSISTENT` / `CONFLICTING`) are represented as `EvidenceRelationship` instances or in a new `EvidenceBundle.cross_system_alignments` field.
