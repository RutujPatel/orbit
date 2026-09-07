# Shadow ORBIT Scope

## Status

Shadow ORBIT is an experimental, concierge-supporting implementation inside Project ORBIT's existing locked architecture.

This document does not create or amend a canonical ORBIT decision.

## Core experimental question

Would a real Engineering Manager prefer Shadow ORBIT's review workflow to the way they currently prepare for and conduct their recurring engineering review?

## Product promise under test

Walk into your weekly engineering review knowing what needs attention. Leave with decisions and commitments that will not be forgotten next week.

## Engineering spine

Stable evidence
→ deterministic changes and conditions
→ minimum sufficient provenance
→ historically stable prepared review
→ human decisions and commitments
→ explicit carry-forward

## Experimental spine

Unaided manager expectation
→ ORBIT artifact
→ observed overlap, novelty, errors, and omissions
→ real meeting behavior
→ repeated use
→ declining founder dependence
→ willingness to continue and pay

## Initial operating boundary

Shadow ORBIT supports:

- One founder/operator
- One organization at a time
- One engineering team
- One Jira project
- One recurring engineering review
- Two synthetic review periods
- Approximately four real review periods later
- Fixture-first input
- Restricted Jira export or API input later
- A small set of deterministic findings and deltas
- A thin server-rendered review artifact later
- Manual decisions, commitments, and research observations

## Manager-facing hierarchy

1. What changed since the last review
2. What needs attention
3. What ORBIT could not determine
4. Open and carried commitments
5. Supporting facts and counts

Week one states explicitly that no prior Shadow ORBIT review is available.

## Initial condition rules

Exactly four initial condition rules are in scope:

1. BLOCKED_HIGH_PRIORITY
2. OVERDUE_HIGH_PRIORITY
3. STALLED_WORK
4. OVERDUE_COMMITMENT

These rules are product hypotheses. Passing tests does not establish that managers value them.

## Initial delta types

Exactly these delta types are in scope:

- newly_blocked
- newly_unblocked
- newly_overdue
- due_date_changed
- newly_introduced
- newly_high_priority
- became_completed
- commitment_created
- commitment_completed
- commitment_cancelled
- commitment_newly_overdue
- commitment_still_open

A delta is a deterministic fact. It is not automatically a finding or an instruction to discuss something.

## Supporting facts

Shadow ORBIT may calculate bounded counts needed to explain the review.

It does not initially display a planned-completion percentage.

If planned-work counts are used, the planning basis must be explicit. Shadow ORBIT must never assume that sprint membership, fix version, or another Jira field universally means planned work.

## Required distinctions

Shadow ORBIT keeps these separate:

1. Imported source state
2. Configuration used for evaluation
3. Deterministic results
4. Prepared review state
5. Human product state
6. Experimental research observations

Manager feedback cannot mutate a deterministic finding.

## Engineering acceptance versus product validation

Engineering acceptance asks:

Does fixed input plus fixed configuration plus fixed rule versions produce the expected reproducible artifact?

Product validation asks:

Is that artifact useful enough to change manager behavior and justify continued use or payment?

Engineering acceptance is necessary but is not customer validation.

## Deliberately manual

The following remain manual during the experiment:

- Unaided agenda capture
- Definition of planned work
- Real-project status mapping
- Threshold tuning
- Learning classifications
- Post-review debrief
- Decision capture
- Commitment capture
- Observation of where commitments normally live
- Evaluation of whether repeated findings are useful or annoying
- Any customer-requested narrative

## Explicitly out of scope

Shadow ORBIT does not initially include:

- AI narration
- Chat
- Natural-language querying
- Meeting transcription
- Live facilitation
- Slack, Teams, GitHub, SAP, or ServiceNow
- Jira write-back
- Composite risk or health scores
- Finding ranking
- Alert-priority algorithms
- Forecasting
- Automated identity resolution
- A generalized rules DSL
- A generalized analytics engine
- A universal provenance graph
- A generic connector framework
- A production Next.js interface
- Production DRF API surface
- Redis, Celery, Kafka, microservices, or Kubernetes
- Enterprise authentication, billing, or compliance automation

## Synthetic acceptance boundary

The clean two-week fixtures must prove:

- Stable review periods
- Temporal correctness
- Deterministic findings
- Deterministic explanations
- Work-item grouping
- Visible data limitations
- Week-two deltas
- Prior disposition context
- Commitment carry-forward
- Historical preservation

The messy fixture must prove:

- Invalid records are rejected or quarantined
- Valid but incomplete records remain visibly qualified
- Unsupported findings are suppressed
- Untrusted text remains inert
- A sparse review is acceptable when evidence is insufficient

## Real experiment boundary

Where practical, a real experiment runs for four consecutive reviews.

At least one review should involve minimal founder assistance.

The experiment records:

- Preparation time
- Finding volume
- Finding usefulness
- Already-known rate
- Source-error rate
- Unaided-agenda overlap
- Missing context
- Decision capture
- Commitment carry-forward
- Work removed
- Work introduced
- Founder dependence
- Continued use
- Willingness to continue or pay
