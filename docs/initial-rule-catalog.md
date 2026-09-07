# Shadow ORBIT Initial Rule and Delta Catalog

## Status

These definitions are experimental implementation contracts.

They are not validated customer requirements and do not create or amend a canonical ORBIT decision.

Passing tests against these definitions proves only that Shadow ORBIT implemented the specified deterministic behavior.

It does not prove that the rules or deltas are useful to Engineering Managers.

## Shared principles

- Every rule and delta is deterministic.
- Every rule and delta has an explicit version.
- Every evaluation uses a fixed source import and explicit review period.
- Rules must never query an implicit "latest" source state.
- Missing evidence produces suppression or qualification, not invented certainty.
- Deterministic output is separate from manager disposition.
- Experimental learning classification is separate from both.
- No rule uses an LLM.
- No severity, health, confidence, or risk taxonomy is produced.
- A delta is a fact and is not automatically a finding.
- Multiple rule results for one work item may be grouped in the manager-facing artifact while remaining separate deterministic results.
- Every manager-facing explanation is rendered from deterministic rule inputs.
- The source cutoff and review cutoff must remain distinguishable.

# Shared terminology

## Source snapshot

The bounded, validated Jira projection observed at `source_cutoff_at`.

## Review cutoff

The time at which review-relative conditions such as overdue status are evaluated.

## Known incomplete

A work item is known incomplete when its mapped source status is not `done` and the available source evidence is sufficient to trust that classification.

## Indeterminate completion state

A work item's completion state is indeterminate when its status is unmapped, contradictory, or otherwise unsupported by sufficient source evidence.

## High priority

A source priority value mapped explicitly to the `high` priority band.

For the clean fixture:

- Highest → high
- High → high
- Medium → ordinary
- Low → ordinary

## Complete day

A complete day is a full 24-hour interval.

Elapsed complete days are calculated as:

`floor((review_cutoff_at - relevant_event_at) / 24 hours)`

# Condition rules

## 1. BLOCKED_HIGH_PRIORITY v1

### Purpose

Identify work whose mapped priority is high and whose status is blocked in the selected source snapshot.

### Required inputs

- Source work-item key
- Source priority
- Mapped priority band
- Source status
- Mapped status category
- Source cutoff
- Review period
- Status-transition evidence when available

### Match conditions

The rule matches when:

1. `priority_band == high`
2. `status_category == blocked`

Both conditions must be true.

### Suppression conditions

Suppress the rule when:

- Priority cannot be mapped
- Status cannot be mapped
- Source state is structurally invalid
- The record has been quarantined

Incomplete historical changelog does not automatically suppress this rule if the current blocked status is trustworthy. It may prevent Shadow ORBIT from stating when the item became blocked.

### Observed values

Store:

- Source priority
- Mapped priority band
- Source status
- Mapped status category
- Blocked-since timestamp when supported
- Source cutoff
- Review cutoff

### Threshold values

Store:

- Required priority band: `high`
- Required status category: `blocked`

### Calculation description

`priority_band == high AND status_category == blocked at source_cutoff_at`

### Deterministic explanation templates

When blocked-since evidence exists:

`{issue_key} has been blocked since {blocked_since_date} and remained blocked in the source state used for the {review_cutoff_date} review.`

When blocked-since evidence is unavailable but current state is reliable:

`{issue_key} was blocked in the source state used for the {review_cutoff_date} review. ORBIT could not determine when the blocked condition began.`

### Minimum evidence

- Source work item
- Priority value
- Current mapped status
- Relevant status transition when the explanation includes blocked-since time
- Source cutoff
- Review cutoff

---

## 2. OVERDUE_HIGH_PRIORITY v1

### Purpose

Identify high-priority work with a valid due date before the review cutoff that is known not to be complete in the selected source snapshot.

### Required inputs

- Source work-item key
- Source priority
- Mapped priority band
- Valid timezone-aware due date
- Mapped completion state
- Source cutoff
- Review cutoff

### Match conditions

The rule matches when:

1. `priority_band == high`
2. `due_at < review_cutoff_at`
3. The work item is known incomplete in the source snapshot

All conditions must be true.

### Boundary behavior

If:

`due_at == review_cutoff_at`

the item is not overdue.

If:

`due_at > review_cutoff_at`

the item is not overdue.

### Suppression conditions

Suppress the rule when:

- Priority is unmapped
- Due date is absent
- Due date is malformed or lacks timezone information
- Completion state is indeterminate
- Status is unmapped
- Material status evidence is contradictory and cannot be resolved safely
- The record has been quarantined

### Source-cutoff qualification

The due-time comparison uses the review cutoff.

The observed completion state comes from the source snapshot.

If the source cutoff is earlier than the review cutoff, the explanation must not claim that Jira was observed exactly at the review cutoff.

### Observed values

Store:

- Source priority
- Mapped priority band
- Due date
- Source status
- Mapped status category
- Known-complete flag
- Source cutoff
- Review cutoff

### Threshold values

Store:

- Required priority band: `high`
- Due-date comparison: `due_at < review_cutoff_at`
- Requires known incomplete state: `true`

### Calculation description

`priority_band == high AND due_at < review_cutoff_at AND known_complete_at_source_cutoff == false`

### Deterministic explanation template

`{issue_key} was due on {due_date} and remained {status_plain_language} in the source state used for the {review_cutoff_date} review.`

If the due date changed during the comparison period:

`{issue_key}'s due date was changed to {current_due_date}. It remained {status_plain_language} in the source state used for the {review_cutoff_date} review.`

### Minimum evidence

- Source work item
- Priority value
- Due date
- Source completion state
- Relevant due-date change when referenced
- Source cutoff
- Review cutoff

---

## 3. STALLED_WORK v1

### Purpose

Identify work that has remained in progress without a meaningful status transition for more than the configured number of complete days.

### Required inputs

- Source work-item key
- Mapped current status category
- Complete enough relevant status history
- Last meaningful status-transition timestamp
- Review cutoff
- Configured stalled threshold

### Meaningful transition

For version 1, a meaningful transition is a change to the Jira status field.

Changes to title, description, assignee, comments, priority, or due date do not reset the stalled clock.

This is an experimental assumption. Customer observation must determine whether the definition is operationally useful.

### Match conditions

The rule matches when:

1. `status_category == in_progress`
2. Relevant status history is sufficiently complete
3. A last meaningful status transition exists
4. `elapsed_complete_days > stalled_threshold_complete_days`

### Boundary behavior

With a threshold of seven complete days:

- Seven complete days does not match
- Eight or more complete days matches

### Suppression conditions

Suppress the rule when:

- Current status is not mapped
- Current status is not `in_progress`
- Relevant history is incomplete
- Last meaningful transition cannot be established safely
- The record has been quarantined

`updated_at` alone must never be treated as the last meaningful status change.

### Observed values

Store:

- Current status
- Mapped status category
- Last meaningful status transition
- Review cutoff
- Elapsed seconds
- Elapsed complete days
- History-complete flag

### Threshold values

Store:

- Required status category: `in_progress`
- Configured complete-day threshold
- Comparison operator: `>`

### Calculation description

`status_category == in_progress AND relevant_history_complete == true AND floor((review_cutoff_at - last_meaningful_status_change_at) / 24 hours) > configured_threshold`

### Deterministic explanation template

`{issue_key} remained in progress in the source state used for the review. Its last known relevant status change was on {last_status_change_date}, more than {threshold_days} complete days before the {review_cutoff_date} review cutoff.`

### Minimum evidence

- Source work item
- Current mapped status
- Last meaningful status transition
- History-completeness state
- Review cutoff
- Configured threshold

---

## 4. OVERDUE_COMMITMENT v1

### Purpose

Identify an ORBIT commitment that remained open after its due date at review preparation.

### Required inputs

- Commitment key
- Commitment summary
- Owner
- Due date
- Status at preparation
- Origin review
- Current review cutoff

### Match conditions

The rule matches when:

1. `status == open`
2. `due_at < review_cutoff_at`

### Boundary behavior

A commitment due exactly at the review cutoff is not overdue.

### Suppression conditions

Suppress the rule when:

- Due date is absent
- Due date is invalid
- Status is unknown
- The commitment belongs to another organization
- The commitment was already completed or cancelled before preparation

### Observed values

Store:

- Commitment status at preparation
- Due date
- Owner
- Origin review
- Current review cutoff

### Threshold values

Store:

- Required status: `open`
- Due-date comparison: `due_at < review_cutoff_at`

### Calculation description

`status == open AND due_at < review_cutoff_at`

### Deterministic explanation template

`The commitment "{commitment_summary}" was due on {due_date} and remained open when the {review_label} review was prepared.`

### Minimum evidence

- Commitment record
- Prepared status
- Due date
- Origin review
- Current review cutoff

# Delta definitions

## General delta rules

A work-item delta compares:

- One explicitly selected prior prepared source state
- One explicitly selected current source state

A commitment delta compares:

- The commitment state associated with the prior prepared review
- The commitment state associated with the current prepared review

A delta must not compare against an unspecified latest record.

A delta is shown under `What changed since the last review`.

It is not automatically promoted into `What needs attention`.

## 1. newly_blocked v1

### Match

Produce when:

- Prior mapped status category was not `blocked`
- Current mapped status category is `blocked`
- The transition occurred after the prior source cutoff and no later than the current source cutoff

A newly introduced item may also produce `newly_blocked` if a supported status transition into Blocked exists during the current review period.

### Explanation

`{issue_key} became blocked on {transition_date} and remained blocked in the current source snapshot.`

---

## 2. newly_unblocked v1

### Match

Produce when:

- Prior mapped status category was `blocked`
- Current mapped status category is not `blocked`
- A supported transition out of Blocked occurred after the prior source cutoff and no later than the current source cutoff

### Explanation

`{issue_key} changed from Blocked to {current_status} on {transition_date} and was no longer blocked in the current source snapshot.`

The delta does not imply that the underlying work is complete or resolved.

---

## 3. newly_overdue v1

### Match

Produce when:

- The item was not overdue at the prior review cutoff
- The item is overdue at the current review cutoff
- The current source snapshot supports a known incomplete state

### Explanation

`{issue_key} was not overdue at the previous review cutoff. Its due date passed on {due_date}, and it remained incomplete in the current source snapshot.`

### Non-match

Do not produce when:

- The item was already overdue at the prior review cutoff
- A due date changed but overdue status was already true
- Completion state is indeterminate

---

## 4. due_date_changed v1

### Match

Produce when:

- Prior and current due dates differ
- Both values can be compared or one value changed between absent and valid
- The change is supported by explicit snapshots or change history

### Explanation templates

Both dates valid:

`{issue_key}'s due date changed from {prior_due_date} to {current_due_date}.`

Date added:

`{issue_key} received a due date of {current_due_date}.`

Date removed:

`{issue_key}'s previous due date of {prior_due_date} was removed.`

A due-date change is not automatically described as good, bad, delayed, accelerated, or risky.

---

## 5. newly_introduced v1

### Match

Produce when:

- The item did not exist in the prior source snapshot
- The item exists in the current source snapshot
- Its creation timestamp is on or after the current period start and before the current period end

### Explanation

`{issue_key} was created on {created_date} during this review period.`

---

## 6. newly_high_priority v1

### Match

Produce when:

- The item existed in the prior source snapshot
- Prior priority band was `ordinary` or `unknown`
- Current priority band is `high`
- The priority change is supported by snapshots or change history

### Explanation

`{issue_key}'s priority changed from {prior_priority} to {current_priority}.`

### Non-match

A newly introduced item already marked high does not also produce this delta in version 1.

That item is represented by `newly_introduced`, and its current priority remains visible in the delta evidence.

---

## 7. became_completed v1

### Match

Produce when:

- Prior prepared source state was known not complete
- Current source state is known complete
- Completion occurred on or after the current period start and before the current period end

### Explanation

`{issue_key} moved to Done on {completion_date} and became completed during this review period.`

### Non-match

Do not produce when:

- Completion happened before the current period started
- The item was already complete in the prior source snapshot
- Completion timing is indeterminate

---

## 8. commitment_created v1

### Match

Produce when:

- The commitment did not exist in the prior prepared review
- It exists at current review preparation
- It originated during or after the prior review

### Explanation

`The commitment "{commitment_summary}" was created during the {origin_review_label} review.`

---

## 9. commitment_completed v1

### Match

Produce when:

- Prior prepared status was `open`
- Current prepared status is `completed`
- Completion occurred after the prior preparation and no later than current preparation

### Explanation

`The commitment "{commitment_summary}" was completed on {completion_date}.`

A completion recorded during the current meeting is a post-preparation event. It must not rewrite the prepared artifact that showed the commitment as open.

---

## 10. commitment_cancelled v1

### Match

Produce when:

- Prior prepared status was `open`
- Current prepared status is `cancelled`

### Explanation

`The commitment "{commitment_summary}" was cancelled before the {current_review_label} review was prepared.`

A cancellation does not imply completion.

---

## 11. commitment_newly_overdue v1

### Match

Produce when:

- The commitment was not overdue at the prior review cutoff
- It is open at current preparation
- `due_at < current_review_cutoff_at`

### Explanation

`The commitment "{commitment_summary}" was due on {due_date} and remained open at the {current_review_label} review cutoff.`

---

## 12. commitment_still_open v1

### Match

Produce when:

- The commitment existed at the prior prepared review or originated during it
- It remains open at current preparation

### Explanation

`The commitment "{commitment_summary}" remained open when the {current_review_label} review was prepared.`

This delta may coexist with `commitment_created` or `commitment_newly_overdue`.

# Manager-facing grouping

## Grouping key

Work-item findings are grouped by Jira issue key.

Commitments remain separate commitment items.

## Grouping behavior

- One Jira issue appears once in `What needs attention`.
- Every underlying rule result remains separately inspectable.
- Grouping must not merge different Jira issue keys.
- Grouping must not invent severity or risk.
- The grouped summary must be deterministic.

## Initial grouped-summary combinations

### Blocked and overdue

`High-priority work remains blocked and is past its due date.`

### Blocked only

`High-priority work remains blocked.`

### Overdue only

`High-priority work remains incomplete after its due date.`

### Stalled only

`Work has remained in progress without a relevant status change for longer than the configured threshold.`

### Newly introduced and blocked

`New high-priority work remains blocked.`

The word `new` may be used only when the `newly_introduced` delta exists for the same current review.

## Prior disposition context

If the same issue and rule fire in a later review, show:

- Prior review label
- Prior product disposition
- Prior reason
- A neutral statement that the condition still exists

Template:

`Last review, you marked this as "{prior_disposition}": "{prior_reason}". The condition still exists.`

If no reason exists, omit the quoted reason.

Prior disposition does not suppress the current deterministic result.

# Product disposition

Allowed values:

- included
- not_for_this_week
- deferred
- resolved

Disposition is human product state.

It does not change, delete, or rewrite a deterministic finding.

# Experimental learning classification

Allowed values:

- already_known
- new
- not_relevant
- source_wrong

Learning classification is research state.

It must remain separate from product disposition.

Examples:

- included + already_known
- included + new
- not_for_this_week + not_relevant
- not_for_this_week + source_wrong

# Data-quality behavior

Shadow ORBIT must surface, at minimum:

- UNKNOWN_STATUS
- UNKNOWN_PRIORITY
- PARTIAL_HISTORY
- MISSING_DUE_DATE
- INVALID_OPTIONAL_TIMESTAMP
- INVALID_REQUIRED_TIMESTAMP
- DUPLICATE_EXTERNAL_KEY
- STATUS_CATEGORY_CONTRADICTION
- UNKNOWN_PLANNING_CLASSIFICATION
- STALE_SOURCE_RECORD
- UNTRUSTED_MARKUP_ESCAPED
- UNTRUSTED_INSTRUCTION_TEXT_PRESERVED

Data-quality conditions are not findings.

They explain what ORBIT could not determine and why an evaluation was suppressed or qualified.

# Minimum sufficient provenance

Every deterministic finding must identify:

- Fixture or source import
- Review period
- Source cutoff
- Review cutoff
- Rule key and version
- Subject key
- Material source values
- Threshold values
- Calculation description
- Evidence references
- Relevant data-quality conditions

Every deterministic delta must identify:

- Prior source import or review
- Current source import or review
- Delta key and version
- Subject key
- Prior material values
- Current material values
- Evidence references

No universal provenance graph is required for Shadow ORBIT.
```
