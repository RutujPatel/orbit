# Shadow ORBIT Review Runbook

## Purpose

This runbook defines how founders conduct a Shadow ORBIT customer-learning review.

The runbook is part of the experiment.

It is not a proposed permanent customer workflow.

## Core rule

Do not show the Shadow ORBIT artifact before capturing the manager's unaided agenda.

Do not teach the manager what they should care about.

Do not rescue a weak finding.

Do not describe technical correctness as customer value.

## Before the experiment begins

Confirm:

- The review is a real recurring engineering review.
- The manager has described the last real review before seeing ORBIT.
- The participating team and Jira project are identified.
- The permitted source-data boundary is documented.
- Status and priority mappings are explicit.
- The planning basis is explicit or marked unknown.
- Data retention and deletion expectations are understood.
- The manager knows Shadow ORBIT is an experimental, founder-assisted prototype.
- The manager knows some steps will remain manual.
- The founder has not promised automated completeness.

## Before each review

Record:

- Organization and team
- Review date and expected duration
- Review sequence number in the experiment
- Participants and roles
- Source cutoff
- Review cutoff
- Import method
- Founder preparation time
- Mapping or threshold changes since the previous review
- Raw finding count
- Grouped work-item count
- Delta count
- Data-quality-condition count
- Carried commitment count
- Manual corrections made before the artifact is shown

Do not silently remove a deterministic finding because it seems unhelpful.

If a finding cannot be shown because of a software defect, record that separately as founder intervention.

## Step 1 — Capture the unaided agenda

Before revealing Shadow ORBIT, ask exactly:

> What did you expect to discuss today?

Allow the manager to answer without examples or ORBIT terminology.

Record the agenda as close to verbatim as practical.

Then ask:

> What preparation have you already done for this review?

Capture:

- Time spent
- Systems opened
- Documents or spreadsheets created
- People asked for updates
- Calculations or reconciliations performed
- Information the manager still does not trust

Do not reveal findings during this step.

## Step 2 — Reveal the prepared artifact

Show sections in this order:

1. What changed since the last review
2. What needs attention
3. What ORBIT could not determine
4. Open and carried commitments
5. Supporting facts and counts

In week one, state:

> No prior Shadow ORBIT review is available for comparison.

Do not lead with technical provenance.

Do not lead with supporting metrics.

## Step 3 — Observe first reactions

Before explaining the artifact, observe:

- Where the manager looks first
- Which language causes hesitation
- Which findings they recognize immediately
- Which findings they challenge
- Whether they ask to open Jira
- Whether they ask how ORBIT calculated something
- Whether they ignore the data-quality section
- Whether they immediately identify missing context

Avoid defending ORBIT.

If clarification is necessary, distinguish:

- What the source data said
- What the deterministic rule did
- What ORBIT could not know
- What interpretation remains the manager's responsibility

## Step 4 — Review changes

For each delta used in discussion, record:

- Whether the manager already knew it
- Whether it changed the expected agenda
- Whether it was useful context but not discussion-worthy
- Whether it was misleading
- Whether the source data was wrong
- Whether another system contained the missing explanation

A delta is not automatically a finding.

Do not ask the manager to assign a disposition to every delta unless they naturally use it.

## Step 5 — Review grouped findings

For each grouped work item, determine:

### Product disposition

- included
- not_for_this_week
- deferred
- resolved

### Experimental learning classification

- already_known
- new
- not_relevant
- source_wrong

The learning classification may be captured by the founder after the meeting if asking during the meeting would interrupt the review.

Record why the manager opened evidence, if they did.

Possible reasons include:

- Verify a date
- Verify current status
- Understand why the rule fired
- Check whether ORBIT used the right source field
- Resolve disagreement
- Explore the unfamiliar prototype

Do not treat an evidence click as proof that provenance is valuable.

## Step 6 — Capture missing manual context

Ask or observe:

- What does the manager need to discuss that ORBIT did not surface?
- Why was it absent?
- Does the context exist in Jira?
- Does it exist in email, chat, a document, another system, or only in someone's memory?
- Would the manager want that context automated?
- Did the missing context materially change interpretation of an ORBIT finding?

Add manual review items when useful.

Label their origin:

- manager_added
- founder_added_from_manager_input
- carried_commitment
- jira_derived

Do not disguise manual context as Jira-derived evidence.

## Step 7 — Run the actual discussion

Observe:

- Who operates Shadow ORBIT
- Who chairs the meeting
- Which other systems are opened
- Why those systems are opened
- Whether the discussion order changes
- Whether less time is spent reconstructing status
- Whether more time is spent correcting data
- Whether a finding leads to a decision
- Whether a finding leads to a commitment
- Whether decisions occur outside this meeting

Do not force the meeting to use every Shadow ORBIT item.

## Step 8 — Capture decisions

A decision initially requires only:

- Summary
- Optional related review item

Observe:

- Who says the decision
- Who records it
- When it is recorded
- Whether it is actually made in this meeting
- Where it would normally be recorded

Do not require rationale during the meeting.

If rationale is important, it may be added manually after the discussion.

## Step 9 — Capture commitments

A commitment initially requires:

- Summary
- Owner
- Due date

Also record as research data:

- Where would this normally live?
- Was it copied to another system?
- Who copied it?
- Did the manager consider ORBIT the authoritative record?
- Did capture feel natural or duplicative?

Do not automate write-back.

Do not send automated reminders during the initial experiment unless a later explicitly logged experiment change introduces them.

## Step 10 — Complete the review

Record:

- Actual duration
- Decisions captured
- Commitments captured
- Manual items added
- Deterministic findings discussed
- Deterministic findings ignored
- Other systems opened
- Founder actions required
- Customer actions required

The prepared artifact remains historically stable.

Post-preparation human actions do not rewrite what the manager saw at preparation.

## Step 11 — Conduct the debrief

Use `docs/debrief-script.md`.

Conduct the debrief immediately after the review where practical.

If the manager cannot remain, schedule it while the review is still fresh.

Do not ask only whether the manager liked the prototype.

Ask what should be removed, what was misleading, and what would make them stop using it.

## Step 12 — Prepare for the next review

Before the next review:

- Import the new bounded source state
- Preserve the prior review
- Calculate explicit deltas
- Re-evaluate current conditions
- Carry open commitments
- Display prior dispositions on repeated conditions
- Record every mapping, threshold, wording, or rule change
- Measure founder preparation time again

Do not suppress repeated findings automatically.

Observe whether repetition acts as useful memory or unwanted noise.

## Four-review operation progression

### Review 1

Founder operates Shadow ORBIT.

Primary questions:

- Is Jira credible enough?
- Are the explanations understandable?
- Are findings already known?
- What important context is missing?

### Review 2

Founder operates or manager participates.

Primary questions:

- Are changes more useful than static conditions?
- Does prior-disposition context help?
- Are carried commitments revisited?
- Does repetition create value or annoyance?

### Review 3

Manager operates where practical, with founder assistance only when requested.

Primary questions:

- Where does the manager hesitate?
- Can decisions and commitments be captured naturally?
- How much founder assistance remains?
- Which other systems remain necessary?

### Review 4

Use minimal founder assistance where practical.

Primary questions:

- Does repeated use persist after novelty declines?
- What would the manager retain if only one feature remained?
- Would the manager or sponsor continue?
- Is there a credible paid continuation and approval route?

## Experiment integrity rules

- Passing tests is not customer validation.
- Positive comments are weaker than repeated use.
- Founder corrections must be logged.
- Rule changes break direct comparability unless disclosed.
- Founder preparation time counts as product cost.
- Manual context must remain visibly manual.
- Missing data must remain visible.
- Source errors must not be reclassified as irrelevant findings.
- A manager's disagreement does not mutate the deterministic result.
- A manager's product disposition is not the same as learning classification.
