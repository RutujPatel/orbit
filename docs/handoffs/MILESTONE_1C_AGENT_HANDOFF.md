# Project ORBIT / Shadow ORBIT — Milestone 1C Agent Handoff

## Purpose

This document re-onboards an implementation agent after prior chat context was lost.

The task is:

> **Milestone 1C — Messy-Data Honesty Acceptance**

Repository precedence:

1. Checked-in locked Project ORBIT decisions
2. Checked-in Milestone 0 documentation, fixtures, and expected artifacts
3. Published Milestone 1A and 1B implementation and tests
4. Current Git state
5. This handoff

If this document conflicts with the repository, the repository wins. Report the discrepancy; do not silently normalize it.

---

# 1. Operating constraints

Milestone 1C is an **implementation milestone**, not a new product or architectural decision.

Do not:

- Create or amend a canonical ORBIT decision
- Reopen S-001 through S-033
- Modify Milestone 0 documentation
- Modify any fixture or expected artifact under `fixtures/jira/`
- Modify clean Week 1 or Week 2 semantics
- Modify generic deterministic rule semantics merely to satisfy the messy scenario
- Modify Milestone 1B continuity or attention-selection behavior
- Read an expected artifact at runtime
- Add a database, API, Jira client, network call, UI, AI, LLM, worker, or framework
- Add a generalized validation, reconciliation, anomaly, or data-quality subsystem
- Commit or push without separate user authorization
- Claim execution or passing tests unless commands were actually run

If a fixture or expected artifact conflicts with a locked contract, report:

```text
CONTRACT CONFLICT
```

and stop before implementation.

---

# 2. Required repository

Work only in the real Git clone.

Expected checkpoint:

```text
Branch: develop
HEAD: 500c4423e1f29e07184faf597422e4a05dc3a991
Short SHA: 500c442
origin/develop: same commit
Working tree: clean
Existing tests: 71 passing
```

Milestones:

```text
Milestone 0:
  PASS / CLOSED
  commit e104810

Milestone 1A:
  PASS / CLOSED / PUBLISHED
  commit 0476df7

Milestone 1B:
  PASS / CLOSED / PUBLISHED
  commit 500c442
```

If the working directory has no `.git` directory, do not implement there.

Do not run `git init` in an extracted archive. Ask the user to open or clone the real repository.

---

# 3. Mandatory repository verification

Run from the repository root:

~~~powershell
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/develop
git log --oneline --decorate -5
.venv\Scripts\python.exe -m pytest -q
~~~

On Linux/macOS, use the available virtual-environment interpreter, for example:

~~~bash
.venv/bin/python -m pytest -q
~~~

Required result:

```text
branch = develop
HEAD = 500c4423e1f29e07184faf597422e4a05dc3a991
origin/develop = same commit
working tree = clean
71 tests pass
```

If any condition fails:

1. Do not edit.
2. Report the actual output.
3. Stop until the discrepancy is resolved.

Do not reset, stash, pull, merge, rebase, switch branches, or alter the repository automatically.

---

# 4. Existing engineering baseline

## Milestone 1A

Milestone 1A implemented:

```text
fixture loading
→ validation
→ quarantine / accepted records
→ normalization
→ temporal interpretation
→ supporting facts
→ deterministic rules
→ suppression
→ grouping
→ provenance
→ prepared machine artifact
→ structural acceptance comparison
```

Important boundaries:

- Expected artifacts are test-only.
- Human state is not fabricated.
- Review periods and cutoffs are explicit.
- Time intervals are half-open.
- No system clock, network, randomness, or AI participates.
- Condition rules evaluate independently.

## Milestone 1B

Milestone 1B implemented:

```text
Week 1 source
+ Week 2 source
+ explicit prior-human-state sidecar
→ work-item deltas
→ current findings
→ prior context
→ commitment continuity
→ preserved prepared history
```

The human-state sidecar is the sole runtime authority for human context and commitments.

The Week 2 fixture’s embedded:

```text
commitments_at_preparation
```

is not runtime commitment authority.

## Approved bounded Week 2 attention policy

The initial rules remain independent.

PLAT-112 produces both:

```text
OVERDUE_HIGH_PRIORITY
STALLED_WORK
```

during raw evaluation.

The bounded Week 2 prepared artifact selects only `OVERDUE_HIGH_PRIORITY` for PLAT-112. The omitted stalled match:

- Is not a suppression
- Remains independently testable
- Does not redefine either rule
- Does not establish a generalized ranking system

Do not change this behavior in Milestone 1C.

---

# 5. Milestone 1C purpose

Milestone 1C proves:

> Given the existing bounded Jira-shaped source contract, Shadow ORBIT emits only conclusions supported by trustworthy evidence and explicitly surfaces uncertainty when evidence is insufficient.

Core honesty invariant:

```text
unknown != false
missing != complete
unmapped != normal
invalid != absent
quarantined != accepted
unsupported inference != deterministic fact
```

Prefer:

```text
ORBIT could not determine
```

over fabricated certainty.

This milestone tests machine honesty, not managerial usefulness.

It does not prove:

- Managers find the artifact useful
- Managers trust the output
- Review preparation is faster
- Findings influence decisions
- Real Jira data matches the synthetic fixture
- Customers will continue or pay
- Product-market fit

---

# 6. Protected Milestone 0 files

Inspect but do not modify:

```text
docs/shadow-scope.md
docs/jira-input-contract.md
docs/initial-rule-catalog.md
docs/review-runbook.md
docs/observation-log.md
docs/debrief-script.md
docs/system-change-log.md

fixtures/jira/northstar_clean_week_1.json
fixtures/jira/northstar_clean_week_2.json
fixtures/jira/northstar_messy_week_1.json

fixtures/jira/expected/clean_week_1_review.json
fixtures/jira/expected/clean_week_2_review.json
fixtures/jira/expected/messy_week_1_review.json
```

Do not assume the expected messy artifact path. Locate it from the repository and verify it.

Also do not modify:

```text
fixtures/experiments/northstar_clean_week_1_human_state_for_week_2.json
```

---

# 7. Mandatory read-only reconciliation

Before writing code, read the complete contents of:

```text
fixtures/jira/northstar_messy_week_1.json
the located expected messy artifact

docs/shadow-scope.md
docs/jira-input-contract.md
docs/initial-rule-catalog.md
docs/review-runbook.md
```

Inspect the current implementation:

```text
src/shadow_orbit/types.py
src/shadow_orbit/fixture_io.py
src/shadow_orbit/validation.py
src/shadow_orbit/normalization.py
src/shadow_orbit/temporal.py
src/shadow_orbit/evaluation.py
src/shadow_orbit/artifact.py
src/shadow_orbit/acceptance.py
src/shadow_orbit/human_state.py
src/shadow_orbit/deltas.py
src/shadow_orbit/continuity.py
```

Inspect all existing tests.

Do not edit during reconciliation.

---

# 8. Required per-record reconciliation

For every raw work-item record in the messy fixture, establish:

- Array position
- `source_id`
- Issue key, if valid
- Whether the key is unique
- Validation result
- Accepted or quarantined status
- Quarantine reason, if applicable
- Required timestamp validity
- Optional timestamp validity
- Raw and normalized status
- Raw and normalized priority
- History completeness
- Planning classification
- Due-date state
- Resolved/completion state
- Period-end determinability
- Eligible rules
- Matched rules
- Suppressed rules
- Data-quality conditions
- Evidence references
- Expected artifact representation

Mark unsupported or ambiguous values explicitly. Do not guess.

Calculate directly:

```text
raw record count
accepted record count
quarantined record count
duplicate record count
invalid-required-timestamp count
invalid-optional-timestamp count
unknown-status count
unknown-priority count
incomplete-history count
known-missing-due-date count
invalid-due-date count
unknown-planning count
raw rule-match count
suppressed-evaluation count
grouped finding count
underlying finding count
all supporting-fact counts
```

---

# 9. Recorded messy target — verify, do not assume

The following values were recorded in prior milestone discussions. They are not authoritative until confirmed from the checked-in fixture and expected artifact.

## Import result

Candidate expected values:

```text
raw records:          32
accepted records:     29
quarantined records:   3
```

Candidate quarantines:

```text
OPS-020 — DUPLICATE_EXTERNAL_KEY
OPS-020 — DUPLICATE_EXTERNAL_KEY
OPS-031 — INVALID_REQUIRED_TIMESTAMP
```

Both duplicate OPS-020 records should be quarantined.

OPS-031 reportedly has an invalid required `updated_at`.

## Supporting facts

Candidate values:

```text
accepted_work_item_count:                 29
known_missing_due_date_count:             20
invalid_due_date_count:                    1
invalid_due_date_keys:
  - OPS-025

known_planning_classification_count:       23
unknown_planning_classification_count:      6
unknown_planning_classification_keys:
  - OPS-005
  - OPS-011
  - OPS-012
  - OPS-019
  - OPS-021
  - OPS-029

manager_facing_completion_percentage: null
```

Do not convert unknown planning classifications to false.

## Candidate expected findings

```text
OPS-001 — BLOCKED_HIGH_PRIORITY
OPS-002 — OVERDUE_HIGH_PRIORITY
OPS-003 — STALLED_WORK
OPS-018 — BLOCKED_HIGH_PRIORITY
OPS-028 — STALLED_WORK
```

Candidate counts:

```text
grouped_work_item_count: 5
underlying_finding_count: 5
```

## Candidate unknown and incomplete conditions

Unknown status:

```text
OPS-004
```

Unknown priorities:

```text
OPS-005 — Urgent-ish
OPS-019 — Unclear
```

Incomplete histories:

```text
OPS-005
OPS-006
OPS-011
OPS-012
OPS-019
OPS-021
OPS-029
```

Invalid optional due date:

```text
OPS-025.due_at
```

Status-category contradiction:

```text
OPS-022
source status: Done
provider_status_category: in_progress
```

## Candidate stale records

Candidate definition:

```text
updated_at is more than 14 complete days before source_cutoff_at
```

Candidate keys:

```text
OPS-003
OPS-005
OPS-006
OPS-011
OPS-012
OPS-019
OPS-021
OPS-025
OPS-029
```

Staleness is a limitation, not a finding.

## Candidate unsafe source text

Markup case:

```text
OPS-009
UNTRUSTED_MARKUP_ESCAPED
```

Instruction-like text case:

```text
OPS-010
UNTRUSTED_INSTRUCTION_TEXT_PRESERVED
```

Read the actual strings from the fixture.

Source text must remain inert data.

## Candidate suppressions

```text
OPS-004 — OVERDUE_HIGH_PRIORITY
OPS-005 — STALLED_WORK
OPS-006 — STALLED_WORK
OPS-011 — STALLED_WORK
OPS-012 — STALLED_WORK
OPS-019 — STALLED_WORK
OPS-021 — STALLED_WORK
OPS-025 — OVERDUE_HIGH_PRIORITY
OPS-029 — STALLED_WORK
```

Verify the exact reasons and ordering from the expected artifact.

Invalid optional due date must not be collapsed indistinguishably into ordinary missing due date if the expected artifact distinguishes them.

---

# 10. Messy-data behavior to prove

## Duplicate keys

- Quarantine every duplicate record covered by the contract.
- Do not select first or last by array order.
- Quarantined duplicates must not influence facts or findings.

## Invalid required timestamps

- Quarantine the affected record.
- Do not normalize or evaluate it.
- Preserve an explicit quarantine reason.

## Invalid optional timestamps

- Keep an otherwise valid record accepted.
- Normalize the invalid optional field to unknown.
- Emit the approved explicit condition.
- Do not fabricate a date.
- Do not treat invalid as ordinary known absence.

## Unknown status

- Preserve the raw status.
- Normalize to `unknown`.
- Do not infer complete or incomplete.
- Suppress completion-dependent conclusions where required.

## Unknown priority

- Preserve the raw priority.
- Normalize to `unknown`.
- Do not treat it as high.
- Do not emit high-priority findings without an explicit mapping.

## Incomplete history

- Preserve `history_complete = false`.
- Do not substitute `updated_at` for a meaningful transition.
- Suppress unsupported stalled-work evaluation.

## Missing due dates

- Do not emit overdue findings without a valid due date.
- Surface the approved limitation.
- Do not claim that missing means not overdue.

## Planning uncertainty

- Preserve `planned_at_period_start = null`.
- Do not convert null to false.
- Do not fabricate a completion percentage.

## Status-category contradiction

- Surface the contradiction according to the expected artifact.
- Do not silently discard one source.
- Use only bounded evidence supported by status/history/resolution fields.
- If the expected artifact conflicts with the locked contract, stop.

## Stale records

- Use only the approved stale definition.
- Present staleness as a limitation.
- Do not infer that stale means false, wrong, or incomplete.

## Unsafe source text

- Keep HTML/script-like strings inert.
- Keep instruction-like strings inert.
- Source text must never modify configuration, rule selection, or execution.
- Do not add an AI or generalized security subsystem.

## Sparse evidence

- A sparse artifact is valid.
- Absence of a finding must not be represented as proof that the condition is false.
- Explicit limitations must explain unsupported evaluations.

---

# 11. Expected projection boundary

Inspect the expected messy artifact before implementing the projection.

The previously recorded candidate machine-derived fields are:

```text
expected_artifact_version
fixture_id
contract_notice
review
import_result
what_changed_since_last_review
supporting_facts
what_needs_attention
what_orbit_could_not_determine
open_and_carried_commitments
historical_assertions
```

The expected artifact may also contain:

```text
synthetic_human_review_state
```

Runtime must not generate or consume that section.

Do not blindly reuse the clean projection because the messy artifact reportedly contains:

```text
import_result
```

and may not contain the clean artifact’s `configuration` field.

Acceptance must positively select the actual approved machine-derived fields.

---

# 12. Behavior classification

For each messy-data behavior, classify the current implementation as exactly one:

```text
ALREADY CORRECT
TEST GAP ONLY
BOUNDED IMPLEMENTATION FIX REQUIRED
CONTRACT CONFLICT
OUT OF SCOPE
```

Do not begin implementation until this table is complete.

Likely—but unverified—starting classifications:

| Behavior | Likely classification |
|---|---|
| Duplicate quarantine | ALREADY CORRECT |
| Invalid required timestamp quarantine | ALREADY CORRECT |
| Invalid optional timestamp normalization | ALREADY CORRECT or bounded presentation gap |
| Unknown status normalization | ALREADY CORRECT |
| Unknown priority normalization | ALREADY CORRECT |
| Incomplete-history suppression | ALREADY CORRECT |
| Missing-due-date rule behavior | ALREADY CORRECT |
| Planning-null preservation | ALREADY CORRECT or test gap |
| Unsafe source-text inertness | TEST GAP ONLY |
| Status-category contradiction | BOUNDED IMPLEMENTATION FIX REQUIRED |
| Stale-record disclosure | BOUNDED IMPLEMENTATION FIX REQUIRED |
| Messy import-result assembly | BOUNDED IMPLEMENTATION FIX REQUIRED |
| Messy artifact assembly | BOUNDED IMPLEMENTATION FIX REQUIRED |
| Messy structural acceptance | TEST GAP ONLY |

The repository inspection determines the final classifications.

---

# 13. Rule-semantics stop rule

Do not modify:

```text
src/shadow_orbit/evaluation.py
```

merely because the messy fixture produces an inconvenient combination.

The Milestone 1B precedent remains:

```text
raw deterministic rules remain independent
artifact selection or representation belongs at the appropriate boundary
global rule semantics must not be silently changed for one fixture
```

If `evaluation.py` appears to require modification:

1. Do not edit it.
2. Classify the issue as `BOUNDED IMPLEMENTATION FIX REQUIRED` or `CONTRACT CONFLICT`.
3. Explain the exact fixture, expected-artifact, and contract paths.
4. Stop for user review.

---

# 14. Preferred implementation boundary

Use the existing architecture.

Strong preference:

```text
no architectural changes
no external dependencies
no protected fixture changes
```

Likely additions, subject to reconciliation:

```text
src/shadow_orbit/messy_acceptance.py
tests/unit/test_messy_honesty.py
tests/acceptance/test_messy_week_1.py
```

Likely bounded modifications:

```text
src/shadow_orbit/acceptance.py
tests/conftest.py
```

Small changes to validation or normalization are permitted only if:

- The locked input contract already requires the behavior
- The checked-in messy fixture exercises it
- Current code does not implement it
- Clean Week 1 and Week 2 behavior remains unchanged
- No generalized abstraction is introduced

Do not add:

- Validator registries
- Plugin systems
- Rule DSLs
- Dynamic rule loading
- Generic report frameworks
- Generic connector abstractions
- New dependencies

A messy-specific artifact assembler is acceptable if required by the approved expected artifact.

It must derive output from runtime inputs. It must not copy the expected artifact or hard-code the entire output document.

---

# 15. Files expected to remain untouched

Unless a concrete contract issue is first reported, do not modify:

```text
docs/
fixtures/jira/
fixtures/experiments/northstar_clean_week_1_human_state_for_week_2.json

src/shadow_orbit/evaluation.py
src/shadow_orbit/artifact.py
src/shadow_orbit/human_state.py
src/shadow_orbit/deltas.py
src/shadow_orbit/continuity.py
```

Do not modify project dependencies or add a framework.

---

# 16. Minimal testing rule

Do not target a predetermined test count.

Reuse existing tests for generic behavior.

Add only tests required for the approved messy scenario and uncovered acceptance boundaries.

Likely minimum structure:

```text
tests/unit/test_messy_honesty.py
tests/acceptance/test_messy_week_1.py
```

Potential consolidated tests:

1. Exact accepted and quarantined records
2. Quarantined records cannot affect facts or findings
3. Exact unknown, incomplete, invalid-optional, missing-date, and planning-null states
4. Exact raw matches and suppressions
5. Unsafe source text remains behaviorally inert
6. Sparse artifact contains only supported findings and provenance
7. Full structural acceptance against the positive messy projection

For each proposed test, explain why existing tests do not already prove it.

Use pytest’s actual collection result as the final test count.

---

# 17. Acceptance-test discipline

The Milestone 1C acceptance test must:

1. Independently load the messy fixture.
2. Run runtime generation without the expected artifact.
3. Independently load the expected messy artifact in test code.
4. Positively select the exact machine-derived messy projection.
5. Structurally compare parsed values.
6. Report the first mismatch path.
7. Verify fixture and expected-artifact digests remain unchanged.
8. Confirm no human state is fabricated.
9. Confirm the expected artifact is test-only.

Do not use raw JSON byte identity as the semantic comparison.

Stable deterministic serialization may be tested separately.

On mismatch:

- Do not modify the fixture.
- Do not modify the expected artifact.
- Determine whether implementation or contract is wrong.
- Stop if the expected artifact conflicts with a locked contract.

---

# 18. Regression requirements

Milestone 1C must preserve:

- Clean Week 1 acceptance
- Clean Week 2 continuity acceptance
- Raw rule independence
- Bounded Week 2 attention selection
- Human-state sidecar isolation
- Embedded commitment isolation
- Later-completion immutability
- Expected-artifact isolation
- Deterministic serialization
- Explicit review cutoffs
- No system-clock dependency
- No network
- No Jira API
- No database
- No AI
- No new runtime dependency

Run the full suite before and after implementation.

---

# 19. Implementation sequence

## Phase 1 — Read-only reconciliation

1. Verify Git and the 71-test baseline.
2. Read the entire messy fixture.
3. Locate and read the entire expected messy artifact.
4. Read relevant contracts.
5. Recalculate every count.
6. Build the per-record reconciliation.
7. Trace each expected result through current code.
8. Complete the behavior-classification table.
9. Define the exact file boundary.
10. Stop if any contract conflict exists.

Produce a concise reconciliation report before editing.

## Phase 2 — Controlled implementation

Proceed only if Phase 1 identifies no contract conflict.

1. Add the smallest messy-specific runtime path.
2. Apply only bounded behavior already required by the contract.
3. Add minimal tests.
4. Keep protected files untouched.
5. Do not change generic rule semantics.

## Phase 3 — Verification

Run:

~~~powershell
.venv\Scripts\python.exe -m compileall -q src tests
.venv\Scripts\python.exe -m pytest -q
~~~

Verify Milestone 0 files:

~~~powershell
git diff --exit-code e104810 -- docs fixtures/jira
~~~

Verify frozen Milestone 1A/1B modules:

~~~powershell
git diff --exit-code 500c442 -- `
  src/shadow_orbit/evaluation.py `
  src/shadow_orbit/artifact.py `
  src/shadow_orbit/human_state.py `
  src/shadow_orbit/deltas.py `
  src/shadow_orbit/continuity.py
~~~

Inspect expected-artifact isolation:

~~~powershell
Get-ChildItem src\shadow_orbit -Recurse -Filter *.py |
    Select-String -Pattern `
      "load_expected_artifact|messy_week_1_review|fixtures.jira.expected"
~~~

Inspect final changes:

~~~powershell
git status --short
git diff --name-status 500c442
git diff --stat 500c442
git diff --check
~~~

Do not stage, commit, or push.

---

# 20. PASS criteria

Milestone 1C is eligible for PASS only when local execution proves:

```text
exact raw-record count
exact accepted-record identities
exact quarantine identities and reasons
exact normalized unknown states
exact invalid/missing distinction
exact supporting facts
exact raw findings
exact suppressions
exact grouped findings
exact limitations
exact provenance
unsafe source text remains inert
no fabricated human state
expected artifact remains test-only
deterministic output
```

Candidate high-level values, pending repository confirmation:

```text
Raw records:             32
Accepted records:        29
Quarantined records:      3
Grouped findings:         5
Underlying findings:      5
Suppressed evaluations:   9
Known missing due dates:  20
Invalid due dates:         1
Planning unknown:          6
```

All prior tests and all approved new tests must pass.

No Milestone 0 file may change.

No clean-scenario behavior may regress.

---

# 21. Required agent report

After read-only reconciliation, report:

1. Actual Git checkpoint
2. Baseline test result
3. Located fixture and expected-artifact paths
4. Exact per-record reconciliation
5. Exact counts
6. Exact expected findings
7. Exact suppressions
8. Exact limitations
9. Source-text cases
10. Current implementation classification
11. Contract conflicts, if any
12. Exact proposed file boundary
13. Minimal test plan
14. Recommendation:
    - `APPROVE — READY TO IMPLEMENT`
    - `REVISE — DESIGN ISSUE`
    - `BLOCK — CONTRACT ISSUE`

If implementation then proceeds, report separately:

1. Files added and modified
2. Protected files verified unchanged
3. Exact implementation behavior
4. Tests added
5. Exact test output
6. Acceptance comparison result
7. Runtime-isolation checks
8. Git diff summary
9. Remaining bounded limitations
10. Status:
    - `PASS`
    - `FAIL`
    - `BLOCKED`

Do not commit or push.

---

# 22. Final instruction

Begin with repository verification and complete read-only reconciliation.

If:

- the repository is the real Git clone,
- HEAD is exactly `500c4423e1f29e07184faf597422e4a05dc3a991`,
- the working tree is clean,
- all 71 tests pass,
- and no contract conflict is found,

then proceed with the smallest compliant Milestone 1C implementation.

Otherwise stop and report the discrepancy.

Never modify an expected artifact to make a test pass.