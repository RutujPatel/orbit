# Shadow ORBIT Experiment System-Change Log

## Purpose

This log records changes that may affect comparability across Shadow ORBIT reviews.

It is an experimental ledger, not a general-purpose configuration-history system.

Every change to a rule, threshold, mapping, planning basis, explanation, grouping behavior, data-quality policy, or founder preparation process must be recorded before the next review is interpreted.

## Comparison rule

Two reviews are directly comparable only when material evaluation and presentation settings remain equivalent.

When a material change occurs:

- Preserve both review artifacts.
- Do not recalculate the prior prepared review in place.
- Record the change here.
- State that direct week-over-week comparison may be limited.
- Do not silently claim improvement caused by the product.

## Change categories

Allowed categories:

- review_period_semantics
- rule_definition
- rule_threshold
- delta_definition
- status_mapping
- priority_mapping
- planning_basis
- data_quality_policy
- explanation_template
- grouping_behavior
- fixture_contract
- founder_preparation_process
- review_presentation
- observation_method
- commitment_process

## Impact levels

- `non_material`: Wording or operational change that does not alter deterministic inclusion, exclusion, calculation, grouping, or interpretation.
- `presentation_material`: Changes what the manager sees or how items are grouped, without changing underlying deterministic rule results.
- `evaluation_material`: Changes which records, findings, deltas, or counts are produced.
- `experiment_material`: Changes how customer behavior is observed or measured.

## Milestone 0 baseline

| Change key | Effective point | Category | Impact | Previous value | New value | Reason |
|---|---|---|---|---|---|---|
| BASELINE-001 | Before first synthetic evaluation | review_period_semantics | evaluation_material | No Shadow ORBIT baseline | Review intervals are half-open: starts_at <= event_time < ends_at_exclusive | Avoid ambiguous period-end behavior |
| BASELINE-002 | Before first synthetic evaluation | rule_threshold | evaluation_material | No Shadow ORBIT baseline | STALLED_WORK uses more than seven complete 24-hour days | Establish explicit synthetic boundary behavior |
| BASELINE-003 | Before first synthetic evaluation | priority_mapping | evaluation_material | No Shadow ORBIT baseline | Highest and High map to high; Medium and Low map to ordinary | Support bounded clean-fixture rules |
| BASELINE-004 | Before first synthetic evaluation | status_mapping | evaluation_material | No Shadow ORBIT baseline | To Do, In Progress, Blocked, and Done use explicit mapped categories | Prevent silent status inference |
| BASELINE-005 | Before first synthetic evaluation | planning_basis | evaluation_material | No Shadow ORBIT baseline | Clean fixture uses manual_fixture_flag | Avoid treating Jira sprint membership as universally planned |
| BASELINE-006 | Before first synthetic evaluation | review_presentation | presentation_material | No Shadow ORBIT baseline | Review order is changes, attention, limitations, commitments, supporting facts | Align artifact with the experimental promise |
| BASELINE-007 | Before first synthetic evaluation | grouping_behavior | presentation_material | No Shadow ORBIT baseline | Multiple rule matches are grouped by work-item key | Avoid duplicate manager-facing work items |
| BASELINE-008 | Before first synthetic evaluation | explanation_template | presentation_material | No Shadow ORBIT baseline | Explanations are deterministic templates based on material rule inputs | Provide understandable reasons without AI narration |
| BASELINE-009 | Before first synthetic evaluation | data_quality_policy | evaluation_material | No Shadow ORBIT baseline | Unknown or insufficient evidence suppresses unsupported evaluation and remains visible | Preserve evidence-backed honesty |
| BASELINE-010 | Before first synthetic evaluation | observation_method | experiment_material | No Shadow ORBIT baseline | Unaided agenda is captured before artifact reveal | Reduce agenda-anchoring bias |
| BASELINE-011 | Before first synthetic evaluation | observation_method | experiment_material | No Shadow ORBIT baseline | Learning classification is separate from product disposition | Distinguish relevance, novelty, and source error |
| BASELINE-012 | Before first synthetic evaluation | commitment_process | experiment_material | No Shadow ORBIT baseline | Commitment requires summary, owner, and due date; normally_lives is research data | Test carry-forward without creating a general task manager |

## Entry format for later changes

Append one row using this exact column structure:

| Change key | Effective point | Category | Impact | Previous value | New value | Reason |
|---|---|---|---|---|---|---|

Use a stable sequential key such as:

- CHANGE-001
- CHANGE-002
- CHANGE-003

The effective point must identify the first review or synthetic acceptance run affected.

Examples of acceptable effective points:

- Before synthetic clean week-two acceptance
- Before Customer Alpha review 2
- After Customer Alpha review 2 and before review 3

## Required change detail

For each material change, add a detail block below its table row.

Use this structure:

### Change key

**Requested or initiated by:** founder, manager, source-data requirement, defect correction, or research-method correction

**Evidence prompting change:** observed behavior or defect description

**Expected effect:** what may change in findings, deltas, presentation, or observations

**Comparability impact:** which prior and later reviews should not be compared directly

**Historical handling:** confirmation that prior prepared reviews remain unchanged

## Changes that must be logged

Always log:

- A threshold increase or decrease
- A rule condition added or removed
- A new rule
- A removed rule
- A new delta
- A removed delta
- Status mapping changes
- Priority mapping changes
- Planning-basis changes
- A change from suppression to qualification
- Explanation wording that alters perceived meaning
- Grouping changes
- A new automatic suppression behavior
- A new reminder or notification
- Changes to unaided-agenda capture
- Changes to learning classifications
- Changes to who operates the artifact
- Changes to founder pre-editing or preparation behavior

## Changes that do not require a separate entry

Pure corrections to this log's spelling or formatting do not require a change entry when they cannot affect:

- Evaluation
- Presentation
- Manager behavior
- Research interpretation

When uncertain, record the change.

## Prohibited behavior

- Do not modify a prior prepared artifact silently.
- Do not backfill a new rule into prior reviews and present it as historical truth.
- Do not remove an inconvenient finding from the record.
- Do not merge source errors into not-relevant feedback.
- Do not compare review outcomes without disclosing material configuration changes.
- Do not treat improved customer reaction after founder coaching as product improvement.
