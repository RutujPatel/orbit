# Shadow ORBIT Jira Fixture Input Contract

## Purpose

This contract defines the bounded input accepted by Shadow ORBIT's synthetic fixture importer in a later milestone.

It does not define a universal Jira schema.

A future Jira export or API adapter must project source data into this contract without changing deterministic core behavior.

## Contract version

`shadow-jira-fixture-v1`

## Top-level structure

A fixture contains:

- contract_version
- fixture_id
- organization
- team
- project
- timezone
- review_period
- configuration
- source_completeness
- work_items
- optional comparison
- optional commitments_at_preparation

## Organization

Required fields:

- external_key: stable non-empty string
- name: non-empty string

## Team

Required fields:

- external_key: stable non-empty string
- name: non-empty string

## Project

Required fields:

- provider: must equal `jira`
- site_key: stable non-empty string
- project_key: stable non-empty string
- name: non-empty string

Every accepted work-item key must belong to the selected project key.

## Review-period semantics

Required fields:

- label
- starts_at
- ends_at_exclusive
- review_cutoff_at
- source_cutoff_at

All timestamps must be ISO 8601 and timezone-aware.

Review periods use half-open intervals:

`starts_at <= event_time < ends_at_exclusive`

The source cutoff states when the imported Jira source state was observed.

The review cutoff is the temporal boundary used for review-relative evaluation.

These are conceptually distinct values even when a synthetic fixture intentionally makes them equal.

The source cutoff must not be later than the review cutoff.

When the values differ, the review artifact must disclose both values and must not describe source state as if it had been observed later than the source cutoff.

For the clean Milestone 0 fixtures:

- Week 1 uses `source_cutoff_at == review_cutoff_at == 2026-02-09T09:00:00Z`.
- Week 2 uses `source_cutoff_at == review_cutoff_at == 2026-02-16T09:00:00Z`.

The equality removes an unnecessary synthetic freshness confounder. It does not remove the conceptual distinction from Shadow ORBIT's time model.

## Configuration

### Planning basis

Fields:

- key
- description

For the clean fixture, `manual_fixture_flag` means that each item's `planned_at_period_start` value is explicitly supplied for the synthetic experiment.

It does not establish a universal product rule.

### Stalled threshold

`stalled_threshold_complete_days` is an integer.

Version 1 uses a strict comparison:

`elapsed_complete_days > stalled_threshold_complete_days`

Exactly seven complete days does not match a threshold of seven.

### Status mapping

Status names map to:

- todo
- in_progress
- blocked
- done

An unmapped status becomes an `UNKNOWN_STATUS` condition.

It must never be silently mapped.

### Priority mapping

Priority names map to:

- high
- ordinary

An unmapped priority becomes an `UNKNOWN_PRIORITY` condition.

High-priority rules require a known `high` mapping.

### Active configuration parameters

The active Milestone 0 synthetic configuration contains only parameters used by current deterministic behavior:

- planning_basis
- stalled_threshold_complete_days
- status_mapping
- priority_mapping

There is no active due-soon threshold and no due-soon rule.

## Source completeness

Fields:

- scope_complete
- history_complete_by_default
- notes

An individual work item may set `history_complete`.

A false history value prevents rules that depend on reliable transition age unless enough explicit evidence exists to evaluate the rule safely.

## Work-item fields

Required:

- source_id
- key
- title
- item_type
- priority
- status
- created_at
- updated_at
- planned_at_period_start
- history_complete
- changes

Optional or nullable:

- provider_status_category
- assignee
- resolved_at
- due_at
- status_at_period_start

## Work-item timestamp policy

Required timestamps must be valid and timezone-aware:

- created_at
- updated_at
- each change.changed_at

A record with an invalid required timestamp is quarantined.

Optional timestamps must also be timezone-aware when present:

- resolved_at
- due_at

An invalid optional timestamp is treated as an unknown field value. The record may remain accepted if no other structural failure exists, but a visible data-quality condition must be produced.

## Change records

Each change contains:

- field
- from
- to
- changed_at

Initial relevant fields are:

- status
- due_at
- priority

Unknown changes may be ignored by deterministic rules, but they must not alter source data silently.

## Duplicate-key policy

The stable source identity for manager-facing work is the Jira issue key.

If multiple raw records share one issue key, all records with that key are quarantined.

Shadow ORBIT must not choose a winner based on array order.

Quarantined records do not contribute to counts, findings, or deltas.

## Status-source policy

The configured status mapping is the bounded ORBIT interpretation used by the experiment.

If optional provider status-category metadata contradicts the mapped source status, Shadow ORBIT records a `STATUS_CATEGORY_CONTRADICTION`.

The contradiction must be visible.

A result may be retained only when the bounded source status, relevant history, and resolved timestamp provide sufficient consistent evidence. Otherwise completion-dependent evaluation is suppressed.

## Planning classification

`planned_at_period_start` may be:

- true
- false
- null

Null means Shadow ORBIT cannot determine planning classification.

A null value must not be silently converted to false.

An item created after the review period started cannot truthfully be represented as planned at period start under the clean fixture's manual planning basis.

PLAT-111 is therefore:

- `planned_at_period_start: false`
- `status_at_period_start: null`

No completion percentage is presented in Milestone 0.

## Completion during a review period

An item is completed during a period only if a supported completion timestamp satisfies:

`starts_at <= completion_timestamp < ends_at_exclusive`

A completion after the period but before review preparation does not count as period completion.

## State at period end

If complete history supports reconstruction, Shadow ORBIT may determine state at the period boundary from transitions.

The current source status must not rewrite historical period-end state.

If reconstruction is unsafe, period-end state is indeterminate.

## Overdue evaluation

A work item is eligible for `OVERDUE_HIGH_PRIORITY` only when:

- priority maps to high
- due_at is valid
- due_at is earlier than review_cutoff_at
- the item is known not to be complete in the source snapshot
- completion status is sufficiently reliable

The rule uses the review cutoff for due-time comparison and the selected source snapshot for observed work-item state.

When source cutoff and review cutoff differ, source freshness must be disclosed.

The clean synthetic fixtures make the values equal, so there is no synthetic freshness gap.

## Stalled evaluation

A work item is eligible for `STALLED_WORK` only when:

- status maps to in_progress
- relevant status history is sufficiently complete
- a last meaningful status transition can be identified
- elapsed complete 24-hour days at review cutoff is greater than the configured threshold

`updated_at` alone is not proof of a meaningful status transition.

## Blocked evaluation

A work item is eligible for `BLOCKED_HIGH_PRIORITY` only when:

- priority maps to high
- current status maps to blocked in the selected source snapshot

## Untrusted source text

All source strings are untrusted, including:

- title
- status
- priority
- assignee
- item type

HTML and script content must be rendered as inert text.

Instruction-like text has no operational meaning and must not affect deterministic evaluation.

## Comparison contract

A week-two fixture may identify:

- prior_fixture_id
- prior_review_label

Delta evaluation compares explicit prior and current records. It must never query an unspecified latest record.

## Commitments at preparation

Commitments are not Jira records, but may be included in a synthetic week-two fixture to test carry-forward.

Required commitment fields:

- external_key
- origin_review_label
- summary
- owner
- due_at
- status
- created_at

Optional research field:

- normally_lives

A later completion must not mutate the prepared state that showed the commitment as open.

## `commitment_created` comparison semantics

In version 1, `commitment_created` is a first-appearance comparison delta.

It means:

> The commitment was absent from the prior prepared review and is present in the current prepared review, with an origin or creation record available where applicable.

It does not mean that the commitment was created during the current review period.

For COMMITMENT-001:

- It originated during the 2026-W06 review.
- It was created at `2026-02-09T10:15:00Z`.
- It was absent from the prepared 2026-W06 artifact because it was created during that review after preparation.
- It first appears in the prepared 2026-W07 artifact.
- The 2026-W07 comparison may therefore emit `commitment_created`.
- Its Week 1 origin and original creation timestamp remain unchanged.

## Future Jira adapters

A future restricted Jira export or API adapter must:

1. Validate source data as untrusted.
2. Preserve Jira issue keys and source IDs.
3. Preserve relevant raw values.
4. Apply explicit status and priority mappings.
5. Produce data-quality conditions for omissions.
6. Produce the same bounded contract.
7. Avoid exposing credentials in output or logs.
8. Avoid making Jira's vendor schema the ORBIT domain model.
