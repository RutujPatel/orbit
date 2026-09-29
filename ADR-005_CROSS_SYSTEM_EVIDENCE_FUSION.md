# ADR-005: Cross-System Evidence Fusion & Relationship Classification Contract

**Status:** Proposed (Awaiting Human Approval)  
**Date:** 2026-09-28  
**Pass:** Pass 4 / Wave 3 (Milestone 2)  
**Author:** Forensic Software Engineering & Evidence Integrity Review  

---

## Context

Project ORBIT evaluates software delivery integrity by cross-referencing activity across multiple independent source systems (Jira issue tracking and GitHub source control).

Under Pass 3.1 and Pass 4 Waves 1–2, the system established:
- Pure in-memory Jira and GitHub evidence pipelines.
- Immutable `EvidenceBundle` container with join-endpoint validation.
- Bounded in-memory provenance dereferencing against offline source fixtures.

However, cross-system relationship extraction remains bounded to literal regular expression matching (`github_mentions.py`), which labels all detected citations as `kind="mentions"`, `basis="lexical_match"`.

A critical architectural risk is the temptation to **infer semantics beyond evidence**:
- Assuming a PR author and a Jira assignee are the same individual because usernames match.
- Assuming a PR title containing `"PLAT-101"` proves implementation responsibility, merge intent, or issue completion.
- Assuming a temporal gap between Jira resolution and GitHub merge is automatically a "contradiction".

This ADR defines the formal evidence contract governing cross-system relationships before any fusion logic is implemented.

---

## Decision

### 1. Separation of Explicit Linkage and Declared Mentions

We establish a strict, non-inferential taxonomy for cross-system edges:

```
Cross-System Relationship
        │
        ├── EXPLICIT_LINK      (Structured, native integration metadata only)
        │
        └── DECLARED_MENTION   (Literal textual match in unstructured fields)
```

#### A. What Constitutes an `EXPLICIT_LINK`
An `EXPLICIT_LINK` exists **only** when established by a dedicated, structured field in the source system schema:
1. Originates from explicit metadata (e.g. Jira `remotelinks`, Jira development panel integration entities, or GitHub native `closing_issues_references`).
2. Declares a specific typed association role (e.g. `fixes`, `resolves`, `relates_to`).
3. Does **not** rely on lexical tokenization, regex matching, or unformatted text search.

*Forensic Note:* Under current offline fixture schemas (`shadow-jira-fixture-v1` and `shadow-github-fixture-v1`), structured link fields do not exist. Therefore, under existing fixture formats, the set of `EXPLICIT_LINK` relationships is legitimately **empty**.

#### B. What Constitutes a `DECLARED_MENTION`
A `DECLARED_MENTION` exists when an entity's free-form text fields contain a textual citation matching the configured policy (`MentionLexicalPolicy`):
1. Extracted from authorized fields: PR `title`, PR `source_branch`, PR `target_branch`, Commit `message`, Branch `name`.
2. Provenance explicitly traces to the source record and specific `source_field_path`.
3. Retains `basis="lexical_match"`.

#### C. What Does NOT Constitute Either Class
The following MUST NEVER be classified as either an `EXPLICIT_LINK` or a `DECLARED_MENTION`:
- Identical actor strings (e.g. `assignee: "Alice"` and `author_login: "alice"`).
- Branch names without an issue key (e.g. `feature/authentication` does not link to `"PLAT-101"` even if both discuss authentication).
- General commit messages lacking explicit project key prefixes (e.g. `"fixed the login bug"`).
- Inferred transitive links (if PR 101 mentions Commit A and Commit A mentions `PLAT-101`, PR 101 is not an explicit link to `PLAT-101`).

---

### 2. State & Temporal Alignment Semantics

Temporal and state comparisons across systems must be classified independently of the relationship taxonomy:

```
Cross-System State Comparison:
    ├── CONSISTENT
    ├── CONFLICTING
    └── INSUFFICIENT_EVIDENCE
```

1. **`CONSISTENT`**:
   - The observed timeline across systems is coherent (e.g., commit occurs before PR merge, PR merges before or at issue resolution).
2. **`CONFLICTING`**:
   - Emitted **only** when the underlying contracts establish that two observations cannot simultaneously be true.
   - Example: Authoritative repository metadata establishes PR #101 is closed without merge, while an explicit deployment manifest claims PR #101 is active in production.
   - **Do NOT manufacture contradictions from temporal differences**: A PR merged after an issue was marked "Done" is not a contradiction; it indicates post-resolution activity or workflow lag.
3. **`INSUFFICIENT_EVIDENCE`**:
   - Emitted when an entity, timestamp, or observation interval is unobserved, missing, or partial (`Unknown != False`).

---

### 3. Ambiguity & Determinism Guarantees

1. **Ambiguity Preservation**:
   - If a mentioned issue key maps to multiple Jira observations, do not select one arbitrarily. Emit an `UnresolvedReference` with reason `"Ambiguous Jira target"`.
   - If a PR mentions multiple issue keys, emit distinct edges for each key independently.
2. **Permutation Invariance**:
   - Any fusion function must yield identical output regardless of the input order of observations or fixtures.
   - All output collections are immutable tuples sorted by deterministic composite keys.

---

### 4. Intentional Architectural Deferrals

1. **Live Connectors are Intentionally Deferred**:
   - Milestone 2 requires proving the deterministic, closed-world evidence contract using offline golden fixtures.
   - Live HTTP/API connectors introduce non-determinism, authentication dependencies, network latency, and mutable remote state.
   - Safety invariant `Jira mutations = 0` is strictly maintained.
2. **Week-One Evaluator is Intentionally Untouched**:
   - `evaluate_week_one_rules(NormalizedFixture)` is a protected baseline evaluating Jira-only rules for the Mahout qualification specimen.
   - It must never be refactored or wired to consume `EvidenceBundle` directly during Milestone 2.
   - Multi-system findings belong to the future Track B evaluator (`evaluate_evidence_bundle`).

---

## Consequences

### Positive
- Prevents semantic hallucinations: textual mentions are never conflated with authoritative proof of work.
- Mathematical determinism and permutation invariance are guaranteed across cross-system evidence.
- Protected Mahout baseline and historical regression tests remain 100% green and unchanged.

### Negative / Trade-offs
- Without schema expansion to capture native issue links, `EXPLICIT_LINK` cannot be populated from existing fixtures.
- All current cross-system edges remain classified as `DECLARED_MENTION`.

---

## Human Approval Gate

Before any implementation code is written, human architectural approval is required on the classification boundaries defined herein.
