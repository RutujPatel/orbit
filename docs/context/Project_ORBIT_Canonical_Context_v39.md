# Project ORBIT — Canonical Product, Decision & Engineering Roadmap
## Persistent Context File for Future Sessions

> **Canonical status:** This file is the authoritative project context and decision tracker.
> **Canonical context version:** v37.
> **Latest locked decision:** S-034 — Jira + GitHub Cross-System Evidence Direction.
> **No later decision number is currently created.**
> The previous working name "Atlas One" is retired. The current working name is **Project ORBIT**.
> ORBIT is a working/codename only; trademark/domain clearance is not implied.

---

# 1. PROJECT IDENTITY

## Working Name

**Project ORBIT — Organizational Review & Business Intelligence Toolkit**

The name may change later. Product naming is not currently an engineering constraint.

## Project Nature

ORBIT is simultaneously:

1. A real enterprise-grade product simulation.
2. A long-form software-engineering curriculum.

The purpose is to learn how an experienced engineering organization:
- understands a problem,
- defines a product,
- models a domain,
- designs architecture,
- implements software,
- tests it,
- secures it,
- deploys it,
- operates it,
- observes it,
- scales it,
- and evolves it over years.

---

# 2. WORKING RELATIONSHIP

The project uses an **Engineering Simulation / co-founder model**.

User role:
**Founding Software Engineer**, progressively developing toward Tech Lead / Architect / Staff-level thinking.

Assistant role:
**Co-founder / senior engineering partner**, able to act as:
- Product Manager
- Staff Engineer
- Principal Architect
- Security Engineer
- QA Architect
- DevOps Engineer
- SRE
- CTO / technical co-founder

Major decisions are made jointly.

The assistant should:
- present alternatives,
- explain trade-offs,
- challenge weak assumptions,
- change its recommendation when evidence warrants it,
- avoid unilateral architectural decisions.

The user should challenge recommendations rather than simply accept them.

---

# 3. ENGINEERING DECISION FRAMEWORK

For a significant decision:

Problem
→ Goals
→ Constraints
→ Options
→ Trade-offs
→ Decision
→ Consequences
→ Validation
→ Documentation / ADR where appropriate

Principles:
- Understand before building.
- Simplicity wins.
- Prefer reversible decisions when reasonable.
- Business needs drive technology.
- Automate repeated manual work.
- Documentation is part of the product.
- Security is a feature.
- Observability is mandatory.
- Every decision has trade-offs.
- Optimize for longevity rather than demo speed.

---

# 4. DECISION GOVERNANCE — CRITICAL

This is a major project control mechanism.

## Canonical-source rule

The decision register in THIS file is authoritative.

A conversation may:
- propose,
- challenge,
- amend,
- or research a decision,

but it does not become canonical until this file is updated.

Never reconstruct a locked decision from chat memory if this file contains it.

## Decision lifecycle

DRAFT
→ DISCUSSION
→ PROPOSED
→ LOCKED
→ AMENDED (optional)
→ SUPERSEDED (only by explicit decision)

Locked decisions are never silently rewritten.

An amendment preserves:
- original decision ID,
- original locked wording/history,
- reason for amendment,
- what changed,
- current canonical wording.

## External research rule

Fresh perspectives (including Claude reviews and other research) are **advisory input**.

They do not independently create canonical ORBIT decisions.

## Pasted-decision status convention

Whenever a decision excerpt is pasted into a future conversation, its current canonical status must be stated at the top of the excerpt. Use `LOCKED`, `PROPOSED`, `DRAFT`, or `SUPERSEDED`. An excerpt without stated status requires checking the canonical register first.

## Anti-duplication rule

Before proposing a new decision number:

1. Check the entire canonical register.
2. Compare the proposed scope against the immediately preceding locked decisions.
3. If the subject already has a canonical owner, amend that decision instead.
4. Create a new decision only when the subject is genuinely new.
5. If two documents disagree, stop and reconcile before advancing.

This rule exists because duplicate decision IDs / regenerated decisions are themselves a failure mode we are explicitly trying to avoid.

---

# 5. PRODUCT PROBLEM

Organizations rely on many disconnected systems:
- Jira
- Salesforce
- SAP
- Odoo
- Microsoft Teams
- Slack
- Excel
- Word
- SharePoint
- ServiceNow
- other specialist applications

This creates:
- duplicated data,
- disconnected workflows,
- multiple accounts,
- multiple subscriptions,
- unclear ownership,
- disconnected communication,
- excessive coordination,
- difficulty finding information,
- manual movement of information,
- unnecessary meetings and "asking around".

The long-term ORBIT vision is intended to reduce this fragmentation.

---

# 6. LONG-TERM PRODUCT VISION

## ORBIT as an Organizational Operating & Execution Layer

ORBIT should eventually maintain a deterministic, permission-aware understanding of:

- people,
- teams,
- responsibilities,
- work,
- objectives,
- metrics,
- commitments,
- decisions,
- relationships,
- external systems,
- organizational events.

The eventual product should help an organization:

1. understand what is happening,
2. identify what matters,
3. support decisions,
4. obtain appropriate human approval,
5. execute actions across systems,
6. verify outcomes,
7. preserve evidence and audit history,
8. use AI as a governed reasoning/narration layer without making AI the source of facts.

## Long-term execution loop

Context Acquisition
→ Problem / Exception Detection
→ Decision Support
→ Approval / Confirmation
→ Action Execution
→ Verification
→ Audit / Organizational Memory

---

# 7. HOW THE PRODUCT STRATEGY EVOLVED

The concept deliberately evolved:

Enterprise-everything
→ Unified enterprise platform
→ Organizational Control Plane
→ Integration / Control Layer
→ Cross-system orchestration
→ Operating Rhythm
→ Weekly Operating Review
→ Deterministic, evidence-backed Engineering Weekly Review

Current position:

> **The long-term platform vision is large, but the first real product is deliberately narrow.**

---

# 8. CURRENT PRODUCT — v0

# Engineering Weekly Review

Primary user:
**Engineering Manager / Delivery Manager**

Product promise:

> **Your weekly engineering operating review prepares itself.**

The first product exists to:
- collect a bounded set of engineering operating data,
- calculate deterministic metrics,
- detect deterministic exceptions/findings,
- show evidence for every finding,
- prepare a weekly review workspace,
- record decisions and commitments,
- carry commitments into the next review,
- provide basic follow-up notifications.

## v0 core

- Scorecard
- Exceptions
- Issues
- Commitments
- Decisions
- Review agenda / discussion items
- Evidence / freshness
- Follow-up state
- Review history

---

# 9. v0 SCOPE DISCIPLINE

The first pilot is intentionally tiny:

- one organization,
- one primary persona,
- one Jira project,
- manually configured scope,
- manually mapped identities,
- email notifications,
- simple append-only history.

## Explicitly out of scope for v0

- universal enterprise search,
- generic workflow builder,
- broad cross-system action marketplace,
- autonomous AI,
- CRM/ERP/HR modules,
- project-management replacement,
- dozens of integrations,
- Kubernetes / microservice fleet without need,
- full reconciliation platform,
- self-serve enterprise connector-management UI,
- full enterprise ontology,
- full audit-product UI.

Guiding rule:

> **Design for extensibility, implement for the present.**

Another core rule:

> **Do not build the future platform before the current product requires it.**

## Foundational architecture vs v0 feature scope

ORBIT deliberately separates **foundational decisions** from **v0 feature scope**.

- v0 may be intentionally narrow in the product capabilities it implements.
- Foundational architecture and domain principles should be chosen with the eventual full-scale ORBIT product in mind.
- A v0 implementation must not assume that today's narrow feature set is the permanent shape of ORBIT.
- At the same time, the long-term vision must not be used as a reason to implement speculative features, integrations, abstractions, or infrastructure before they are earned.
- Where a future capability is likely to make an existing v0 foundation obsolete rather than merely extend it, that risk must be identified and resolved before the foundation is locked.
- Where future capability can be added, promoted, or substituted without destabilizing the foundation, v0 should leave that seam clean rather than prematurely implementing the future capability.

This creates an explicit two-level rule:

> **Build v0 narrowly; choose foundational boundaries for the ORBIT trajectory.**

Therefore, the fact that v0 is an Engineering Weekly Review sourced primarily from Jira does **not** mean ORBIT's foundational model is Jira-specific, nor does it mean manually entered metrics or other v0 conveniences must survive into the eventual product. They are temporary implementation/product choices unless later evidence makes them part of the enduring product model.

The eventual ORBIT Operating Rhythm capability may instead assemble authoritative information from multiple connected systems and automatically obtain the metrics relevant to the applicable operating rhythm. v0's narrow scope is a proof-of-concept wedge, not a constraint on that eventual product.

---

# 10. INITIAL INTEGRATION STRATEGY

## v0

Primary source:
- Jira

Notifications:
- Email

Initial scope:
- one Jira project,
- manually configured,
- manually mapped identities.

## Later candidate integrations

Only when a product requirement earns them:
- Microsoft Teams / Microsoft 365
- Google Workspace
- Slack
- Salesforce
- other systems.

We will NOT implement both Microsoft and Google ecosystems simply because both exist.

Design connector boundaries for extensibility; implement only what v0 requires.

---

# 11. DETERMINISTIC-FIRST PRODUCT PRINCIPLE

The v0 intelligence engine is deterministic.

Example:

IF overdue critical issue
AND deadline < 7 days
THEN finding = PROJECT_AT_RISK

Every important Finding should be explainable through:

Finding
→ Evidence
→ Source / Rule / Calculation

## AI is later

Future AI may:
- draft review narratives,
- summarize verified findings,
- answer natural-language questions over verified data,
- draft explanations,
- assist rule authoring.

AI must NOT become the authoritative source of facts.

Any AI-generated factual statement should trace to deterministic evidence or clearly abstain / ask.

Preferred interaction pattern:

AI statement
→ Finding
→ Evidence
→ Source / Rule / Calculation

---

# 12. TRUST, PROVENANCE & FRESHNESS

A manager must be able to ask:

> **"Why is this on my review?"**

and receive a reproducible answer.

Evidence may include:
- current value,
- target,
- previous period,
- source system,
- source records / calculation,
- time period,
- deterministic rule.

Freshness is part of trust.

Never silently show stale data as current.

If required data is stale or unavailable:
- show freshness explicitly,
- mark the affected metric/finding appropriately,
- do not fabricate continuity.

---

# 13. LONG-TERM ROADMAP

## Stage 0 — Engineering Weekly Review
**CURRENT**
- deterministic scorecard
- exceptions/findings
- issues
- commitments
- decisions
- evidence
- follow-up

## Stage 1 — Review Memory
- historical scorecards
- issue history
- commitment history
- decision history
- evidence snapshots
- state transitions
- period comparisons

## Stage 2 — Cross-System Context
- carefully selected integrations
- cross-system identity/entity mapping
- richer context

## Stage 3 — Deterministic Exception / Blocker Resolution
- blockers
- stalled work
- dependencies
- overdue commitments
- explainable findings
- `blocked_by` relationship

## Stage 4 — Cross-System Actions
- selected approved actions across external tools
- authorization
- confirmation
- execution
- verification
- audit

## Stage 5 — Multiple Operating Rhythms
- executive reviews
- product reviews
- sales reviews
- operations reviews
- program reviews
- QBRs

## Stage 6 — Organizational Context Layer
- organization
- people
- memberships
- teams
- projects
- work contexts
- external entities
- relationships
- metrics
- findings
- decisions
- commitments
- policies
- evidence

## Stage 7 — Governed AI
- explain findings
- summarize reviews
- natural-language questions over verified data
- narrative drafting
- rule-authoring assistance

## Stage 8 — AI-Assisted Execution
- propose actions
- policy/permission checks
- human confirmation where required
- execute
- verify
- audit

## Stage 9 — Governed Organizational Automation
- recurring processes
- cross-system orchestration
- policy-driven automation
- human-in-the-loop execution
- controlled autonomy

---

# 14. CANONICAL DECISION REGISTER

## S-001 — Problem & Vision
**STATUS: LOCKED**

Organizations suffer from fragmented tools, duplicated context, disconnected workflows, and coordination overhead.

Long-term answer:
Organizational operating and execution layer.

---

## S-002 — Initial Market / ICP
**STATUS: WORKING HYPOTHESIS — NOT A CURRENT PRODUCT-BUILD BLOCKER**

Current commercial hypothesis:
- roughly 20–150 employee growth-stage organizations as a targeting band,
- headcount is a targeting proxy,
- real qualification signal is relevant cross-system complexity in supported tools,
- v0 focus is an engineering/delivery manager or team using Jira.

GCC / India / larger-company team adoption remains a future market hypothesis.

Important:
**Unresolved market segmentation must not block or over-constrain the v0 engineering build.**

Market validation may inform later prioritization, packaging, and expansion decisions.

**Revisit trigger: before Stage 2 cross-system expansion or before committing meaningful GTM expenditure, whichever comes first.**

Current priority:
Build the product first.

---

## S-003 — Progressive Consolidation
**STATUS: LOCKED**

Connect existing systems
→ prove value
→ build trust
→ add native capabilities
→ progressively consolidate.

Do not attempt to replace Jira/Teams/Salesforce/etc. in v0.

---

## S-004 — Initial Product Wedge
**STATUS: LOCKED**

Operating rhythm / recurring management execution.

Not:
- search-first,
- full ontology-first,
- generic automation,
- full ERP/CRM replacement.

---

## S-005 — Initial Execution Loop
**STATUS: LOCKED**

Context Acquisition
→ Problem Detection
→ Decision Support
→ Approval / Confirmation
→ Action Execution
→ Verification
→ Audit / Organizational Memory

Human confirmation is an explicit stage where risk/policy requires it.

---

## S-006 — v0 Product
**STATUS: LOCKED**

Engineering Weekly Review for Engineering / Delivery Managers.

Promise:
> "Your weekly engineering operating review prepares itself."

This is the first real product.

Everything beyond this is deferred platform evolution unless v0 requires it.

### Foundational-trajectory clarification

S-006's narrow v0 scope does not narrow the foundational ORBIT model. The Engineering Weekly Review is the first wedge, not the eventual ceiling. Foundational concepts such as organization, people/memberships, work, metrics, findings, decisions, commitments, evidence, provenance, permissions, and external-system boundaries are designed so later ORBIT stages can compose information from multiple systems and support broader operating rhythms.

Conversely, a capability introduced for v0 convenience is not automatically part of the eventual ORBIT product. For example, a manually entered engineering-adjacent metric may be appropriate as a temporary v0 seam if real usage requires it, but the eventual cross-system Operating Rhythm should prefer authoritative connected-system data and may remove that manual mechanism entirely.

The governing distinction is:

```text
v0 feature scope       → intentionally narrow / replaceable where appropriate
foundational boundaries → durable / trajectory-aware
```

---

## S-007 — Deterministic Intelligence / Evidence
**STATUS: LOCKED AS DESIGN PRINCIPLE**

v0 intelligence is deterministic.

Finding
→ Evidence
→ Source / Rule / Calculation

AI is later and is a narration/query/assistance layer, not a source of facts.

---

## S-008 — Relationship Ownership & Provenance
**STATUS: LOCKED**

Hybrid ownership model.

External systems remain authoritative for their native records where they are designated systems of record.

ORBIT owns contextual meaning around connected systems.

Relationships are first-class and independently identifiable, with richness graduated by origin:

Direct:
- lightweight source/sync projection

Derived:
- provenance,
- evidence,
- confidence/verification,
- validity,
- supersession

Human-asserted:
- attribution,
- verification,
- permission control,
- evidence,
- supersession

Context is mutable, but history is not silently erased.

Authorized users may:
- correct,
- override,
- dispute,
- supersede,
- restore

through governed processes.

Normal organizational changes should reconcile automatically so users do not babysit ORBIT.

---

## S-009 — v0 Scope Discipline
**STATUS: LOCKED**

First pilot:
- one organization,
- one primary persona,
- one Jira project,
- manually configured scope,
- manually mapped identities,
- email notification,
- simple append-only history.

No:
- generic workflow engine,
- full connector UI,
- full audit UI,
- full reconciliation platform,
- autonomous AI,
- dozens of integrations,
- unnecessary distributed architecture,
- broad enterprise ontology.

---

## S-010 — Engineering Weekly Review Specification
**STATUS: LOCKED — AMENDED**

### Purpose

A recurring management process that:
- compares current engineering execution against expectations,
- identifies material deviations,
- reviews unresolved issues and commitments,
- records decisions,
- establishes accountable follow-up.

### Lifecycle

Collect
→ Calculate
→ Detect
→ Prepare
→ Review
→ Discuss
→ Decide
→ Commit
→ Track
→ Carry Forward

### Review phases

PREP:
- review period,
- source freshness,
- deterministic executive summary,
- scorecard,
- exceptions,
- proposed agenda,
- carried-forward items.

MEETING WORKSPACE:
For each Review Item:
Finding
→ Evidence
→ Discussion
→ Decision (optional)
→ Commitment (optional)
→ discussed / deferred / resolved

POST-REVIEW:
- decisions,
- commitments,
- outstanding issues,
- notifications,
- next-review watchlist.

### Core KPI candidates

- Completion Rate
- Critical Open Issues
- Overdue Work
- Cycle Time
- Flow Balance
- Aging Work
- Commitment Fulfillment Rate

### Flow Balance amendment

For v0:

> **Flow Balance = Work Items created during the Review Period − Work Items resolved during the Review Period.**

The default v0 population is the configured Work Item population for the tracked Jira project.

Issue-type filtering is not a separate v0 semantic feature. Unless a concrete product requirement later justifies filtering, all synchronized Work Items in scope are included.

Flow Balance is an indicator, not inherently a finding:
- positive value = net inflow / backlog growth,
- zero = inflow matched outflow,
- negative value = net backlog reduction.

Materiality is determined by the existing S-010 threshold/trend framework.

Unlike Completion Rate, Flow Balance does not require a sprint/commitment cohort.

### Completion Rate amendment

Completion Rate is conditionally enabled.

It is enabled only if pilot configuration explicitly establishes a defensible commitment cohort, e.g. sprint commitments.

For continuous-flow teams without a defensible commitment boundary:
- Completion Rate is disabled,
- ORBIT does not approximate it from arbitrary Jira due dates.

Team methodology is manually configured, not inferred.

### Materiality

Threshold materiality:
value crosses warning/critical threshold.

Trend materiality:
value moves materially against expected direction.

Metric-specific interpretation:
- count → absolute delta
- percentage/rate → percentage points
- duration → relative percentage where appropriate

Persistence increases priority/severity.

Initial thresholds are configurable v0 defaults.

### Initial deterministic Findings

- PROJECT_AT_RISK
- COMMITMENT_OVERDUE
- KPI_BREACH
- NEGATIVE_TREND
- AGING_WORK
- BACKLOG_GROWTH (optional/deferred during early v0)

Finding vs Issue:
- Finding = ORBIT detects a condition
- Issue = organization recognizes it as requiring attention

Staleness is a source/data-health signal, not a business Finding.

### Rule evaluation

TRIGGERED:
evaluated and matched.

NOT_TRIGGERED:
evaluated and did not match.

NOT_EVALUABLE:
active rule path could not be evaluated because required record-level input was missing/unusable.

Installation-disabled paths do not produce NOT_EVALUABLE.

### Commitment lifecycle

OPEN
→ COMPLETED
→ CANCELLED / SUPERSEDED as terminal alternatives

More precisely:
OPEN can transition to:
- COMPLETED
- CANCELLED
- SUPERSEDED

Overdue is computed:
OPEN + due_date < today.

Corrections of terminal states are governed corrections, not silent edits.

### Review history

Review Period is independent of Review occurrence.

Carry-forward items must be distinguishable from new items.

---

## S-011 — Minimal v0 Domain Model
**STATUS: LOCKED**

The v0 conceptual vocabulary is intentionally small:

1. Organization
2. Membership
3. Team
4. Project
5. Work Item
6. Metric
7. Metric Snapshot
8. Review Period
9. Review
10. Review Item
11. Finding
12. Evidence
13. Issue
14. Decision
15. Commitment
16. External Reference

### Work Item
A unit of executable engineering work represented locally only to the degree required by the review and backed by an external Jira reference. ORBIT does not recreate Jira's complete issue model.

### Review Item promotion
A Finding does not automatically become a Review Item.

v0 rule:
- Critical Findings are automatically eligible for promotion.
- Warning Findings remain visible in the scorecard unless explicitly promoted.
- Promotion records who/what caused it (`promoted_by`).

### Issue origin
An Issue records its origin/provenance so ORBIT can distinguish:
- derived from a Finding,
- carried forward,
- manually created by a participant.

### Review Period
A first-class temporal concept independent of a Review occurrence.

A Review evaluates a Review Period.

### Deferred Person / Identity seam

The v0 Membership abstraction intentionally does not model a standalone canonical Person/Identity layer.

A dedicated Person/Identity model must be introduced **before a second external system needs to resolve to the same human represented by an existing Jira account**.

This is a deliberate v0 simplification, not an accidental omission.

### Decision / Commitment attachment
Decisions and Commitments arise from the relevant Review Item context, rather than being treated as unscoped notes attached only to the Review.

### Deliberately NOT in v0
- Customer
- Vendor
- Contract
- generic Workflow Engine
- generic Approval Engine
- universal Search
- AI Agent
- generic Relationship Engine

---

## S-012 — Data Ownership & External Source Semantics
**STATUS: LOCKED — DO NOT REGENERATE**

This decision already exists canonically.

Do not create another S-012 under any rearranged title.

Locked principles include:
- four-layer ownership model,
- source-authoritative vs ORBIT-owned data,
- Finding state machine,
- ACTIVE / ACKNOWLEDGED / SYSTEM_RESOLVED,
- reconciliation for manually-entered data using S-008,
- non-destructive correction/history,
- explicit handling for deletion,
- archival,
- access revocation,
- temporary failures,
- source disappearance.

If S-012 needs change:
**AMEND S-012. Do not create S-012b or another S-012 title.**

---

## S-013 — Jira Projection & Synchronization Contract
**STATUS: LOCKED / CANONICALIZED**

ORBIT v0 connects to one manually configured Jira project and maintains a local synchronized Work Item projection containing fields required by active finding rules.

Jira remains authoritative for native source fields.

### Configuration ownership
Rule paths/capabilities are enabled explicitly during pilot configuration.

ORBIT does not infer installation capabilities from incidental source data.

Example:
"Uses sprint commitments: YES/NO" is explicit configuration.

### Historical backfill
Initial connection:
- one-time Jira changelog backfill,
- approximately 6–8 weeks,
- reconstruct relevant historical state/snapshots,
- seed meaningful comparison history.

After initial backfill:
ORBIT's periodic snapshots maintain ongoing history.

### Unknown statuses
Unknown Jira statuses:
- default safely to ACTIVE,
- create a visible mapping diagnostic,
- do not crash synchronization,
- do not silently assign a dangerous semantic.

### Completion
Use Jira resolution timestamp where available.
Do not infer completion solely from status names.

### Sync-run vs connection health

Sync-run state:
- RUNNING
- SUCCEEDED
- FAILED

Connection health:
- derived from freshness / last successful run,
- e.g. HEALTHY / STALE / FAILING / DISCONNECTED.

STALE is not a sync-run state.

### Missing inputs
Every deterministic rule defines behavior when supporting input is absent.

Examples:
- explicit fallback,
- NOT_EVALUABLE,
- installation-disabled path,
- data-health/configuration signal.

Never silently produce nothing.

### Reliability / data integrity
Distinguish and handle non-destructively:
- temporary failure,
- stale data,
- deletion,
- archival,
- access revocation,
- unavailable records.

Do not cascade-delete ORBIT historical context because a source record disappears.

### Evidence freshness
Every Finding's Evidence records freshness of the source data used.

### Tests
Test missing supporting fields, including:
- no due date,
- no sprint,
- missing milestone/release where an active rule path requires it,
- no previous-period snapshot,
- no resolution timestamp.

---

## S-013 Amendment A — Snapshot Cadence & Retry Semantics
**STATUS: LOCKED AMENDMENT**

### Snapshot generation

Two mechanisms:

1. Successful synchronization cycles may capture current source observations and freshness metadata.
2. Business-period Metric / Work Item snapshots are created at Review Period boundaries and during initial historical backfill.

This keeps freshness current without turning every poll into a business-period snapshot.

### Retry / backoff

At pilot scale:
- transient failures use bounded retry,
- exponential backoff with jitter,
- permanent/auth/configuration failures are not retried indefinitely,
- last-successful-sync does not advance after a failed run,
- next successful run resumes from the last known successful point using available source cursor/timestamp semantics.

Exact retry-count/backoff constants are implementation parameters to finalize during integration work.

---

# S-014 — Engineering Weekly Review Product Specification
**STATUS: LOCKED**

## Purpose

The Engineering Weekly Review is a recurring decision workspace that compares current engineering execution against expectations, identifies material deviations, reviews unresolved issues and commitments, records decisions, and establishes accountable follow-up for the next Review Period.

## Review lifecycle

```text
REVIEW CREATED
→ PREPARED
→ IN PROGRESS
→ COMPLETED
→ CARRY-FORWARD
```

This lifecycle is distinct from synchronization state, Finding state, and Commitment state.

## PREPARED / PREP view

The manager sees:
- Review Period
- source/data health and freshness
- deterministic executive summary
- scorecard
- exceptions/findings
- proposed discussion agenda
- carry-forward items

New items and carry-forward items must be visibly distinguishable.

## Review Item promotion

A Finding does not automatically become a Review Item.

- Critical Findings are automatically eligible for promotion.
- Warning Findings remain visible in the scorecard unless explicitly promoted.
- Promotion records `promoted_by`.

## MEETING WORKSPACE

A Review Item is strictly scoped to one Review / Review Period.

For a Review Item, the workflow is:

```text
Finding
→ Evidence
→ Discussion
→ Decision (optional)
→ Commitment (optional)
→ Disposition
```

Review Item disposition branches from PENDING:

```text
               ┌→ DISCUSSED
PENDING ────────┼→ DEFERRED
               └→ RESOLVED
```

All promoted Review Items and manually created Review Items require disposition before the Review can be completed.

## Manual Review Items

A participant may create a Review Item with no Finding.

Example:
- a management request,
- an external topic,
- a planned discussion item.

Such an item carries explicit provenance:

```text
origin = MANUAL
```

It follows the same meeting/disposition mechanics as a Finding-backed Review Item.

## Issue mechanics

An Issue is a durable organizational problem deliberately chosen for ongoing tracking beyond a single Review Period.

An Issue has stable identity across Reviews.

An Issue is created explicitly by a participant through an action such as:

> Track as ongoing Issue

An Issue is NOT automatically created merely because a Finding, Commitment, or Review Item persists.

A Review Item remains period-scoped and may reference an Issue.

For an open Issue in a later Review Period:
- create a new Review Item for the new Review,
- link it to the same Issue,
- link it to the prior period's corresponding Review Item where one exists.

Conceptually:

```text
Issue: Infrastructure Dependency
├── Week 32 Review Item
├── Week 33 Review Item
├── Week 34 Review Item
└── Week 35 Review Item
```

This is how cross-period organizational continuity is represented.

A Finding may also continue across periods according to its own lifecycle without requiring an Issue.

## Prepared Review Item changed before meeting

If an underlying Finding changes between preparation and the actual meeting:
- the Review Item is NOT removed,
- the change is surfaced prominently before disposition,
- the user sees the new state and timestamp,
- the Review Item still requires a disposition.

Example:

```text
Prepared:
PROJECT_AT_RISK = ACTIVE

Before meeting:
Finding becomes SYSTEM_RESOLVED

Meeting:
"Underlying finding resolved at 10:30."
```

This preserves what was prepared without presenting stale reality as current.

## Decision / Commitment attachment

Decisions and Commitments arise from the relevant Review Item context rather than being unscoped notes attached only to the Review.

A Commitment must structurally contain its required owner and due date before it can enter its normal OPEN state.

The Review completion process therefore does not need to treat missing owner/due-date as a separate post-creation completion check.

## Review completion

A Review may be completed when:
- the review is in progress,
- all promoted Review Items have a disposition,
- all manually created Review Items have a disposition,
- Decisions are captured where decisions were made,
- any created Commitments satisfy their structural requirements.

The Review does NOT require:
- every warning Finding to be discussed,
- every Issue to be resolved,
- every Commitment to be completed.

The review is a decision-making event, not a requirement that every organizational problem disappear during the meeting.

## POST-REVIEW

After completion, ORBIT produces:
- Decisions
- Commitments
- outstanding/deferred Items
- follow-up notifications
- next-review watchlist

## Carry-forward

The next Review must preserve relevant history without copying everything blindly.

Carry forward by lifecycle/eligibility:
- open Commitments,
- unresolved Issues,
- active Findings that still warrant monitoring,
- explicitly deferred Review Items.

Do not automatically carry forward:
- completed Commitments,
- cancelled Commitments,
- transient one-period Findings with no active continuation,
- purely informational content.

For Issues, a new period gets a new Review Item linked to the same Issue and prior period Review Item.

## Review history

A Review Period is independently defined from a Review occurrence.

The system should be able to show continuity such as:

```text
Week 32: Finding created
Week 33: Discussed; Issue created
Week 34: Commitment overdue
Week 35: Issue still unresolved
```

without pretending these were the same Review Item across periods.

## Freshness / degraded preparation

A Review may proceed with partially stale source data if the affected data is clearly disclosed and the manager can make an informed decision.

Stale/unavailable source data must never be presented as current.

## AI

No LLM is required for the critical v0 workflow.

The v0 critical path is:

```text
Source data
→ Deterministic metrics/rules
→ Findings
→ Evidence
→ Review
→ Human decision
```

AI may later assist with narration, summaries, natural-language queries, or rule authoring, but cannot silently replace the deterministic chain.


# S-015 — Credential & Secrets Handling
**STATUS: LOCKED**

## Scope

Define generic ORBIT principles for storing, accessing, replacing, revoking, and logging credentials/secrets used by integrations.

This decision is provider-agnostic.

First concrete application:
- v0 Jira credential.

## v0 authentication mechanism

For v0, Jira uses:
- an organization-owned Jira service account, not a personal human account,
- a manually configured Jira base URL,
- a manually configured Jira service-account identifier,
- a scoped API token restricted to the minimum Jira permissions required by ORBIT v0.

The exact provider permission/scope strings remain an implementation detail and must be finalized against the actual Jira API operations used.

OAuth application/consent flows are deferred until self-serve or multi-organization integration requirements justify them.

## Required security semantics

At minimum:
- secure secret storage,
- encryption/protection at rest,
- backend-only access,
- least-privilege internal access to secrets,
- least-privilege external provider scopes,
- credential validation before activation,
- credential replacement/rotation,
- revocation/invalid-credential handling,
- no secrets in logs/traces/errors/audit records,
- cleanup/invalidation on integration disconnect,
- credential-version auditing without exposing secret material.

## Validate-before-activate

During credential validation:
- the raw secret may exist only in transient protected runtime memory/process handling,
- it must not be persisted,
- it must not be written to ordinary application storage,
- it must not appear in logs, traces, errors, metrics, audit records, or client responses,
- it becomes an active stored credential only after validation succeeds.

## Credential ownership

Credentials are scoped to the Organization/Integration Connection rather than to the employee who configured them.

The v0 organization owner/administrator configures or replaces the integration credential.

A general ORBIT role/permission model is not required solely to implement this v0 configuration path.

## Credential lifecycle

A credential may move through:
- NOT_CONFIGURED,
- ACTIVE,
- NEEDS_REPLACEMENT / AUTH_FAILURE,
- REPLACED,
- REVOKED.

The exact provider failure modes are mapped without exposing secret material.

## Disconnect / historical data

Disconnecting an integration must:
- stop credential use,
- invalidate/remove the credential's usable access path as appropriate,
- preserve relevant connection history,
- not destructively delete unrelated historical organizational/review records.

## Technology boundary

S-015 does NOT choose:
- Vault,
- cloud secret-manager product,
- KMS,
- HSM,
- Kubernetes secret mechanism,
- encryption implementation details,
- OAuth architecture.

Those are later implementation/architecture decisions.
# 17. FUTURE ENGINEERING CURRICULUM

This project should teach the full software-engineering lifecycle.

## Product
- problem discovery
- requirements
- product scope
- UX
- product metrics
- business model

## Domain
- functional requirements
- non-functional requirements
- domain modeling
- bounded contexts
- state machines
- workflow semantics
- entity relationships

## Architecture
- architecture styles
- modularity
- backend architecture
- frontend architecture
- API strategy
- data architecture
- event architecture
- integration architecture
- security architecture

## Backend
- project structure
- database
- authentication
- authorization
- APIs
- background jobs
- caching
- storage
- search
- workflows
- notifications
- audit

## Frontend
- application shell
- routing
- design system
- forms
- state
- data fetching
- reusable components
- dashboards
- performance
- accessibility

## Quality
- unit tests
- integration tests
- contract tests
- E2E / Playwright
- performance testing
- security testing
- mutation testing
- resilience/chaos

## DevOps / Cloud
- Docker
- CI/CD
- Infrastructure as Code
- environments
- secrets
- deployment
- rollback
- cloud architecture
- Kubernetes only when justified

## Production / SRE
- logging
- metrics
- traces
- alerting
- SLOs / SLIs
- incident response
- postmortems
- backups
- disaster recovery
- scaling

## AI
- deterministic context
- retrieval
- permission-aware AI
- tool use
- human approval
- evaluations
- guardrails
- AI observability
- governed execution

## Long-term engineering
- versioning
- migrations
- feature flags
- API lifecycle
- technical debt
- refactoring
- dependency upgrades
- governance
- incremental certification
- multi-year evolution

---

# 18. PRINCIPLES TO PRESERVE

- Narrow wedge first.
- Ship before generalizing.
- Design for extensibility; implement for the present.
- Evidence before AI.
- Deterministic facts before AI narratives.
- Freshness is part of trust.
- Preserve history; do not silently overwrite reality.
- Authorized humans can correct context.
- External systems remain authoritative where appropriate.
- Users should not babysit synchronization under normal conditions.
- Do not build generic engines until multiple real use cases prove the abstraction.
- Complexity must be earned.
- Security and observability are requirements.
- Do not choose infrastructure technology before the product/domain semantics justify it.
- Do not use the long-term platform vision as an excuse to overbuild v0.
- Distinguish narrow v0 feature scope from foundational architecture: foundations should support the ORBIT trajectory, while unproven future capabilities remain deferred.
- Do not assume v0-specific mechanisms are permanent product capabilities; later product stages may replace, remove, or automate them when broader cross-system context makes them unnecessary.
- **Customer-discovery over feature-assumption:** foundational architecture should support the eventual ORBIT trajectory, but individual product surfaces, workflows, integrations, metrics, and MVP scope remain hypotheses until validated through direct customer evidence.
- **V0 is a learning wedge, not a permanent product contract:** the V0 product may be narrow and Jira-first, but its features are allowed to be added, changed, simplified, replaced, or removed as customer evidence and broader cross-system capabilities emerge.
- **No product feature becomes architecturally sacred merely because it exists in V0:** preserve durable foundations, not accidental V0 behavior.
- **Maintain a fine balance between foundation and product decisions:** continue making foundational/implementation decisions that are unlikely to be invalidated by customer discovery, while deferring or marking provisional any product decision whose answer should primarily come from real customer evidence.
- **Customer discovery is a decision gate, not a project pause:** research should run in parallel with safe foundational engineering work, but major new V0 product-scope decisions should not be locked ahead of the evidence they are meant to reflect.

---

# 19. HOW FUTURE SESSIONS MUST CONTINUE

When this file is attached:

1. Read CURRENT PROJECT STATE.
2. Read the CANONICAL DECISION REGISTER.
3. Check amendments/superseded decisions.
4. Check CURRENT ROADMAP.
5. Compare any proposed new decision with S-001 onward.
6. Amend existing decisions when the subject already has a canonical owner.
7. Only create a new decision number for a genuinely new subject.
8. Do not restart settled strategy discussions unless explicitly requested.
9. Treat external research as advisory until formally adopted.
10. Keep product strategy, semantic design, and implementation architecture distinct.
11. Do not choose technologies prematurely.
12. Maintain the joint co-founder/engineering-simulation working style.
13. Classify new decisions as **Foundational**, **Product**, or **Implementation** where useful, and explicitly note whether customer validation is required.
14. Continue foundational/implementation decisions in parallel with customer discovery when they are unlikely to constrain the validated product wedge.
15. Treat major unvalidated V0 product-scope decisions as provisional or deferred until customer discovery provides evidence.

### Current checkpoint

> **S-001–S-015 are the canonical locked decision history.**
>
> **S-034 is the latest locked decision.**
>
> The next action is to identify the next genuinely new subject only after overlap-checking it against S-001–S-034.

# 14B. S-016 — v0 Persistence & Data Architecture
**STATUS: LOCKED**

## Purpose
Define the persistence semantics required by the Engineering Weekly Review before selecting concrete database/storage technologies.

## Persistence lanes

### A. External / source-derived
- Jira Work Items
- synchronization observations
- source-derived historical snapshots

### B. ORBIT-owned governance/configuration state
- Organization
- Membership
- Team
- Project
- Metric definitions
- Review
- Review Period references/configuration
- Review Items
- Issues
- Decisions
- Commitments
- Rule definitions

### C. Human-asserted data
- manually entered Metric Snapshots
- explicit human corrections/assertions
- other user-authored contextual data

### D. Computed interpretations
Findings and Evidence are computed interpretations, neither external mirrors nor human-authored facts. Finding evaluations are persisted as immutable historical evaluations with rule/version/evidence/source context.

## Rule-version persistence
Rule definitions are versioned. A changed rule creates a new version; prior versions are preserved and never overwritten in place. Findings reference the exact rule version used.

## Review Period independence
A Review Period is independently persistable from a Review occurrence and may exist with period snapshots before any Review references it.

## Transaction boundary
The primary atomic user operation is:
- Review Item disposition
- plus resulting Decision(s)
- plus resulting Commitment(s)

These commit together or not at all. Review completion is a later validation step over accumulated state.

## Concurrency
v0 uses optimistic concurrency via an explicit version/timestamp check. Conflicts reject/reload rather than silently overwrite.

## Derived-state principle
Do not persist a state as independently authoritative when it can be deterministically derived from authoritative or recorded history.

Examples:
- Commitment overdue
- Connection health/freshness
- Finding evaluation outcome during evaluation, while the historical evaluation itself is persisted

## Historical preservation
Source deletion/disappearance must not cascade-delete unrelated historical ORBIT records.

## Pilot-scale constraint
v0 optimizes for correctness, traceability, historical integrity, and operational simplicity at one-organization/one-project scale.

## Technology boundary
S-016 does not choose PostgreSQL, ORM, Redis, Kafka, Kubernetes, cloud provider, search, or object storage.

# 14C. S-017 — Concrete Persistence / Database Technology
**STATUS: LOCKED**

## Decision
ORBIT v0 uses **PostgreSQL as the canonical transactional persistence layer**.

PostgreSQL is the single authoritative transactional store. Future search/analytics/graph/vector systems are projections, never independently canonical.

## Alternatives rejected

### Graph database
Deferred for v0. Reconsider when traversal routinely requires materially greater depth/complexity than the relational model efficiently supports (initial heuristic ~4–5+ hops) or PostgreSQL traversal latency becomes a measured product problem.

### MongoDB / document database
Rejected as the primary store because the domain benefits directly from relational integrity, normalization, explicit transactions, and constraints. The decision is not based on MongoDB lacking transaction support.

### Event sourcing
Rejected as the primary source-of-truth architecture. Historical/append-only transition records remain required.

## Logical PostgreSQL modularity
v0 uses one PostgreSQL database with explicit schemas for bounded contexts, potentially:
- `organization`
- `integration`
- `credential`
- `metric`
- `finding`
- `review`
- `execution`

## Optimistic concurrency
Use an explicit application-managed version/check, with updates guarded by the expected version.

## Open
Hosting, ORM, migration framework, connection pooling, backup/replication, Redis, search, vector infrastructure, and cloud provider remain open.

# 14D. S-018 — v0 Application Architecture
**STATUS: LOCKED**

## Decision
ORBIT v0 uses a **modular monolith** backed by the PostgreSQL database selected in S-017. Microservices are deferred until measured requirements justify independent service boundaries.

## Module ownership

### `organization`
Owns the shared domain core:
- Organization
- Membership
- Team
- Project
- Work Item

### `integration`
Owns:
- external connections
- synchronization
- source projections
- provider adapters
- synchronization/freshness behavior

Jira is the first concrete integration. Integrations populate the shared domain concepts but do not own them.

### `credential`
Owns provider-agnostic credential/secret handling from S-015. It remains a sibling of `integration`.

### `metric`
Owns Metric definitions, configuration, and metric calculations/snapshots.

### `finding`
Owns deterministic rules, Rule versions, Finding evaluation, Evidence association, and historical computed interpretations.

### `review`
Owns Review, Review Items, Issue, review lifecycle, promotion/disposition, preparation, and completion. Issue belongs here because ongoing tracking begins through the review workflow.

### `execution`
Owns Decisions, Commitments, and their persistent execution-state transitions.

## Dependency direction

```text
integration
     ↓
organization / domain context
     ↓
metric / finding
     ↓
review
     ↓
execution
```

`credential` supports `integration`; it is not a stage of the S-005 execution loop.

Modules may depend on public/domain interfaces but must not reach into private internals of other modules.

## Transactions
Cross-module use cases are coordinated at the application/use-case boundary. The S-016 atomic Review Item operation remains authoritative.

## Background execution
Jira synchronization runs outside synchronous web requests but inside the same application boundary. It is a separate execution entrypoint, not a separate service.

## Rule evaluation
`finding` owns deterministic evaluation. It runs in background/application context and may be triggered by schedule, synchronization, or Review preparation.

## Frontend/backend boundary
The frontend presents workflows and state. The backend owns authoritative rules, authorization, persistence, synchronization, evaluation, and transactions.

## Notifications
Notifications are a thin concern triggered by Review lifecycle events, not a standalone v0 domain module.

## History/audit
History remains module-owned rather than centralized.

## Modularity mechanism
Enforce boundaries using:
- explicit module/package ownership
- public interfaces
- prohibited private cross-module imports
- ownership-aware PostgreSQL schemas
- public module contract tests

## Service extraction
Extract a module only when measured requirements justify it, such as independent scaling, materially different SLOs, deployment isolation, independent operational ownership, or a proven network/API boundary.

## Team-capacity clarification
The project now has a backend developer, a data science engineer, and potentially additional contributors.

More people change execution capacity and raise the need for:
- early CI/CD
- mandatory PR/code review
- stronger automated testing
- reproducible development environments
- professional security/observability
- high UX quality within the existing v0 workflow

More people do **not** by themselves justify:
- broader v0 product scope
- microservices
- OIDC/enterprise SSO
- Redis/Celery
- graph databases
- extra integrations
- architecture created for staffing reasons

## Professional engineering standard
> **Build the smallest system that satisfies current product requirements, but build that system to professional engineering standards appropriate to the team and production risk.**

## Explicitly deferred
S-018 does not choose backend framework, frontend framework, API style, task runner, deployment/container shape, cloud provider, monorepo/polyrepo, or enterprise SSO/OIDC implementation.

# 14E. S-019 — v0 Technology Stack
**STATUS: LOCKED**

## Decision

ORBIT v0 uses the following core application technology stack:

- **Backend:** Python + Django
- **API layer:** Django REST Framework
- **API style:** REST
- **Frontend:** Next.js + React + TypeScript
- **Canonical datastore:** PostgreSQL (S-017)
- **Background execution:** Django's database-backed task system behind an ORBIT application-level task abstraction
- **Testing:** pytest + pytest-django

## Backend rationale

Django is selected because ORBIT's current domain is:
- strongly relational,
- structured,
- transactional,
- history/audit oriented,
- CRUD and workflow heavy,
- well suited to a modular monolith.

The selection is not based on developer capacity alone.

## API

Django REST Framework is the v0 API framework.

REST is the v0 API style.

GraphQL is deferred because the current product does not require its additional query/schema complexity.

## Frontend

Next.js + React + TypeScript is the v0 frontend stack.

The frontend is responsible for presentation and interaction. Authoritative business rules remain backend-owned.

## Background execution

The initial v0 background execution mechanism is Django's task system behind a thin application-level abstraction, so application code does not depend directly on provider-specific task APIs.

Conceptually:

```text
enqueue_job(...)
      ↓
ORBIT task abstraction
      ↓
Django Tasks
```

Celery/Redis are explicitly deferred until measured workload or operational requirements justify them.

Potential reconsideration triggers include:
- job throughput beyond the practical capacity of the initial worker model,
- queue latency becoming a product/SLO problem,
- materially more complex routing/prioritization,
- long-running/high-volume distributed workers,
- reliability/operational requirements beyond the initial mechanism.

Team size alone is not a trigger to add Celery/Redis.

## Testing

pytest + pytest-django are the primary automated backend testing tools.

Professional testing begins with the first meaningful implementation and should include appropriate:
- unit tests,
- integration tests,
- API tests,
- database behavior tests,
- synchronization tests,
- deterministic rule/finding tests.

Additional frontend/E2E tooling is a later implementation detail.

## Future AI note

When AI is introduced in later stages, LLM calls/narration must run asynchronously/background rather than become a synchronous dependency of the deterministic v0 request path.

This preserves S-007's deterministic critical path and prevents external LLM latency from becoming a normal request-path dependency.

## Explicitly deferred

S-019 does NOT choose:
- PostgreSQL hosting/provider,
- deployment/cloud architecture,
- Docker/Kubernetes,
- CI/CD implementation details,
- observability platform,
- enterprise SSO/OIDC,
- Redis/Celery,
- monorepo vs polyrepo.

Those are subsequent decisions.

# 14E. S-019 — v0 Technology Stack
**STATUS: LOCKED — AMENDED**

ORBIT v0 uses Python + Django; Django REST Framework; REST; Next.js + React + TypeScript; PostgreSQL; Django Tasks API behind an ORBIT job abstraction and an external worker/backend; pytest + pytest-django.

### Background execution clarification
Django Tasks provides the task API/contract, not the production worker. The execution shape is:

```text
enqueue_job(...)
      ↓
ORBIT task abstraction
      ↓
Django Tasks API
      ↓
external task backend / worker
```

The application must not depend directly on a concrete task backend. The older standalone package named `django-tasks` must not be confused with Django 6's built-in `django.tasks`. PostgreSQL-backed execution may be evaluated for v0; exact backend package/configuration remains implementation work. Celery/Redis remain deferred until workload/operational requirements justify them.

Future AI work must remain asynchronous/background rather than becoming a synchronous dependency of the deterministic v0 request path.

# 14F. S-020 — Authentication & Authorization
**STATUS: LOCKED**

## Decision
ORBIT v0 uses local application authentication with secure server-side sessions, an ORBIT-local User/Membership model, and a small role-based authorization model. The architecture preserves a future identity-provider seam; OIDC/enterprise SSO is not implemented in v0 unless the actual pilot requirement makes local authentication unacceptable.

## Authentication
- local application authentication
- secure server-side sessions
- login/logout
- session expiration
- account activation/deactivation
- password reset/recovery as required
- authentication-event logging without secrets
- appropriate brute-force/rate-limit protection

## Identity / Membership
```text
User
  ↓
Membership
  ↓
Organization
```
A standalone canonical Person/Identity layer remains deferred per S-011 and is introduced before a second external system needs to resolve to the same human represented by an existing Jira account.

## Authorization
Conceptual v0 roles:
- Organization Administrator
- Review Manager
- Member

Authorization follows:
```text
Membership
   ↓
Role
   ↓
Permission
   ↓
Scope
```
Permissions govern both what a user may do and what review/organizational data they may see.

## v0 visibility
Authenticated users may access data belonging to the configured Review scope to which their Membership grants access. Revisit richer per-person/team visibility before a second team exists within the same organization.

## Bootstrap
The first Organization and Administrator are provisioned manually, out-of-band, using a controlled management command/fixture or equivalent deployment operation. There is no public registration flow in v0.

## Disabled users
Disabling a user blocks new authentication but does not erase historical attribution, Reviews, Issues, Decisions, discussions, or Commitments. Open Commitments remain visible and should surface an inactive-owner/reassignment signal; reassignment is governed and does not rewrite original ownership history.

## Integration credentials
S-015 remains authoritative for external integration credentials and secret handling. Jira API tokens are not ORBIT login credentials.

## OIDC seam / pilot check
Before beginning local-auth implementation, the actual pilot contact should be asked whether local authentication is acceptable. If the pilot organization requires enterprise SSO, revisit implementation before committing to the local-auth path. This is a product/market requirement check, not an automatic commitment to OIDC.

## Explicitly deferred
No full enterprise IAM platform, SAML, multiple IdPs, canonical Person/Identity graph, complex org-wide row-level authorization, or public self-service registration.

# 14G. S-021 — Development Environment & Developer Workflow
**STATUS: LOCKED**

## Decision

ORBIT v0 development must be reproducible, isolated from production, easy to bootstrap, and aligned with CI.

Infrastructure dependencies should be containerized where that materially improves reproducibility; ordinary application development remains native unless a concrete requirement justifies full-container development.

## Environment model

```text
local
  ↓
CI
  ↓
development / staging
  ↓
production
```

Production configuration/data must never be required for ordinary development.

## Local development shape

```text
Developer machine
├── Django backend
├── Next.js frontend
├── Python / Node tooling
└── pytest

Containerized dependencies
├── PostgreSQL
└── task backend / worker dependency as required
```

## Configuration vs secrets

Configuration and secrets are distinct. Secrets must never be committed to Git and follow S-015's secret-handling rules.

## Git / collaboration

```text
feature branch
    ↓
pull request
    ↓
automated checks
    ↓
code review
    ↓
merge
```

CI validates the same essential quality gates developers can run locally.

## Database workflow

PostgreSQL remains canonical. Developers do not manually modify shared schema. Changes use migrations, and local databases are disposable/recreatable.

## Jira development / testing

### Default: fixtures-first

Developer laptops and automated tests use deterministic Jira fixtures, synthetic data, and recorded responses where appropriate.

No developer laptop should require live read access to an actual pilot customer's Jira project.

### Controlled connector validation

Real Jira connections are reserved for occasional connector validation against a dedicated ORBIT-team-owned Jira sandbox project.

They are never used against a pilot customer's actual project/data from ordinary developer machines.

### Structural safety

The v0 source direction remains:

```text
Jira → ORBIT
```

The synchronization path is read-only with respect to Jira. This structurally closes mutation risk but does not remove the need to protect customer data.

## Seed / fixture data

Development fixtures include accumulated historical state, not only a fresh database. Examples:
- several weeks of Reviews,
- completed and superseded/cancelled Commitments,
- a resolved Finding,
- a carried-forward Issue,
- historical Evidence/snapshots,
- state transitions across multiple periods.

## Reproducible commands

The repository provides documented commands for:
- bootstrap,
- start dependencies,
- migrations,
- seed/refresh fixtures,
- backend,
- frontend,
- background worker/tasks,
- tests.

## Deterministic development requirement

The critical v0 path must run without external AI services:

```text
Jira fixture
   ↓
sync
   ↓
metrics
   ↓
Finding
   ↓
Evidence
   ↓
Review
```

## Code ownership

Code ownership may remain lightweight and aligned with module responsibilities. A bureaucratic ownership system is not required in v0.

## Explicitly deferred

S-021 does not choose production cloud, deployment topology, Kubernetes, IaC, production observability, production secrets manager, backup/DR, autoscaling, or final deployment strategy.

# 14H. S-022 — v0 Jira Integration Implementation
**STATUS: LOCKED**

## Decision

ORBIT v0 implements Jira through a dedicated `integration` boundary inside the modular monolith.

Provider-specific API models, authentication, pagination, rate limiting, retries, and response handling remain inside the Jira adapter.

Jira payloads are normalized into ORBIT-owned domain/projection models before persistence.

Synchronization is:
- idempotent,
- checkpointed,
- retry-aware,
- non-destructive,
- observable.

No generic multi-provider integration framework is built beyond the interfaces needed to keep the Jira implementation clean.

## Jira adapter boundary

```text
ORBIT domain/application
        ↓
integration interface
        ↓
Jira adapter/client
        ↓
Jira API
```

The rest of ORBIT must not depend directly on Jira endpoint URLs, response shapes, pagination mechanics, authentication details, or Jira-specific retry behavior.

## Provider model separation

```text
Jira API Response
      ↓
Jira DTO / adapter model
      ↓
Normalization
      ↓
Validation
      ↓
ORBIT Work Item / projection
      ↓
Persistence
```

Provider-shaped Jira responses are never treated as ORBIT domain models.

## Synchronization pipeline

```text
Discover
   ↓
Fetch
   ↓
Normalize
   ↓
Validate
   ↓
Reconcile
   ↓
Persist
   ↓
Emit sync result / health signal
```

`Reconcile` means the normal per-record comparison/upsert step. It does **not** mean the comprehensive periodic drift-detection/reconciliation engine deferred by S-009.

## Checkpointing and idempotency

Initial synchronization performs the S-013 historical backfill.

Incremental synchronization begins from the last successful checkpoint.

A failed run does not advance the checkpoint.

Checkpoint advancement is **whole-run / all-or-nothing** for v0. This is safe because synchronization upserts are idempotent: a retry may reprocess records already written during a failed run without creating duplicate or incorrect projections.

v0 therefore does not implement fine-grained partial-checkpoint tracking.

Stable source identity is used for upserts, for example:

```text
provider = jira
external_id = JIRA-421
```

Repeated processing of unchanged source state converges to the same ORBIT state.

## Pagination, rate limits, and failures

The Jira adapter owns:
- pagination,
- request timeouts,
- provider rate limits,
- transient 5xx failures,
- authentication failures,
- malformed provider responses.

## Identity normalization

Because S-009 uses manual identity mapping:

```text
Jira account
      ↓
manual identity mapping
      ↓
ORBIT Membership/User
```

### Unmapped assignee behavior

An unmapped Jira assignee must **not** block or fail synchronization.

Instead:
- preserve the raw Jira account identifier,
- leave the ORBIT Membership reference unresolved,
- continue synchronizing the Work Item,
- emit a visible mapping diagnostic for an authorized administrator.

The system must not invent a Membership mapping.

## Status normalization

Unknown/unmapped Jira statuses:
- default safely to ACTIVE according to S-013,
- create a visible mapping diagnostic,
- do not crash synchronization,
- do not silently receive a dangerous semantic.

## Source disappearance

Deletion, archival, or access loss is handled non-destructively.

A source Work Item becoming unavailable must not cascade-delete historical:
- Findings,
- Evidence,
- Review Items,
- Decisions,
- Commitments,
- snapshots.

## Sync observability

Every sync run should provide:
- run ID,
- start/end time,
- duration,
- status,
- records observed,
- records created/updated,
- records affected by source disappearance where detectable,
- normalization/validation failures,
- retry count,
- successful checkpoint.

Logs/traces must not contain credentials or secret material.

Connection health remains derived from sync/freshness history.

## Testing

### Unit
Deterministic normalization and mapping behavior.

### Integration
Jira adapter against an ORBIT-owned Jira sandbox.

### Fixture/contract
Deterministic fixtures covering at minimum:
- normal Work Item,
- unknown status,
- unmapped assignee,
- missing due date,
- missing sprint,
- deleted/unavailable issue,
- malformed response,
- rate limiting,
- authentication failure,
- pagination,
- retry/reprocessing,
- historical backfill.

Default developer/CI execution remains fixture-first under S-021.

## Deferred scope

S-022 does not build:
- generic N-provider connector framework,
- self-service connector marketplace/UI,
- second provider,
- comprehensive drift-detection/reconciliation engine,
- Jira write-back/action execution,
- universal identity resolution.

# 14I. S-023 — Deterministic Metric & Snapshot Engine
**STATUS: LOCKED**

## Decision

ORBIT v0 uses a **deterministic Metric Engine** that transforms identified historical source/input snapshots within a defined Review Period into reproducible Metric Snapshots.

The Metric Engine answers:

> **What happened?**

The Finding Engine answers:

> **Does it matter enough to surface?**

Metrics are explicitly separated from materiality/threshold logic.

## Metric vs Finding boundary

```text
Work Item / source observations
           ↓
      Metric Engine
           ↓
      Metric Snapshot
           ↓
      Finding Engine
           ↓
        Finding
```

The Metric Engine does not decide whether a value is materially concerning.

## Metric Definition

A Metric Definition version describes **calculation semantics only**:
- what input fields are required,
- what calculation is performed,
- what unit/result shape is produced,
- what evaluation context is required.

Calculation-logic changes create a new Metric Definition version.

Target, warning, critical, and other materiality thresholds do **not** belong to Metric Definition calculation logic.

Threshold/materiality configuration belongs to the Finding/Rule layer and follows the Rule-version persistence model established by S-016.

Therefore:
- changing the Completion Rate calculation may create a new Metric Definition version,
- changing a warning/critical threshold does not require a new Metric Definition version,
- threshold changes are versioned as Finding/Rule changes.

## Input snapshot semantics

Metric evaluation uses historical input state defined by S-013.

For period-end/state-based metrics:
- use the applicable Review Period-end source state/snapshot.

For transition-dependent metrics:
- use the relevant source event/history information required to calculate events within the Review Period.

Example:
- Flow Balance uses Work Items created/resolved during the Review Period rather than merely the period-end state.

S-023 does not redefine S-013's source-period semantics; it consumes them.

## Metric Snapshot

A Metric Snapshot records the result of a metric evaluation in a specific context.

At minimum it preserves:
- metric identity,
- Metric Definition version,
- Review Period,
- input snapshot/version references,
- configured evaluation timezone,
- result/status,
- calculation timestamp/metadata necessary for reproducibility.

A historical Metric Snapshot is an immutable evaluation.

If source data or calculation semantics later change, a new/superseding evaluation is created rather than silently rewriting historical results.

## Timezone

All persisted source timestamps remain normalized consistently with the broader ORBIT time model.

Review Period calculations use an explicitly configured **IANA timezone identifier**, e.g.:

```text
Asia/Kolkata
America/New_York
Europe/London
```

A fixed UTC offset is not sufficient as the semantic timezone representation.

The configured IANA zone is used to determine period boundaries and local-date interpretation, including daylight-saving transitions where applicable.

## Metric evaluation status

The Metric Engine intentionally has a richer status model than the Finding Engine:

- **EVALUATED** — metric was successfully calculated.
- **NOT_EVALUABLE** — metric is configured/active, but required input for this evaluation is missing or unusable.
- **DISABLED** — metric is intentionally not enabled/applicable for this installation/configuration.
- **ERROR** — the metric engine failed unexpectedly while attempting evaluation.

This richer model is intentional.

A scorecard contains a fixed set of expected metrics, so a non-populated row must distinguish "disabled," "not evaluable," and "evaluation error."

Finding evaluation has different semantics because an exception list is variable-shaped; an unconfigured rule path does not need a placeholder Finding record.

## Missing data

Missing data must never silently become a valid numeric result unless the Metric Definition explicitly specifies that behavior.

Examples:
- missing required input → NOT_EVALUABLE,
- installation-disabled metric → DISABLED,
- engine/runtime failure → ERROR.

The engine must not silently convert unavailable data into `0`, empty success, or another misleading value.

## Determinism

Given the same:
- Metric Definition version,
- Review Period,
- input snapshot/version,
- configured timezone,
- configuration context,

the Metric Engine must produce the same Metric Snapshot result.

No LLM/probabilistic interpretation participates in the v0 metric calculation.

## Idempotency

The logical evaluation identity is based on:

```text
metric
+
Metric Definition version
+
Review Period
+
input snapshot/version
+
relevant evaluation configuration
```

If the same logical input is evaluated again without any semantic change, the operation is a no-op with respect to canonical Metric Snapshot creation.

This follows directly from the stable evaluation identity and prevents redundant authoritative snapshots.

## Re-evaluation / correction

Normal periodic evaluation creates the canonical Metric Snapshot for its context.

An explicit re-evaluation may be performed when, for example:
- a source correction is discovered,
- a Metric Definition defect is corrected,
- a configuration correction changes the evaluation context.

A correction does not overwrite the historical evaluation.

Instead:

```text
Original Metric Snapshot
        ↓
      superseded
        ↓
Corrected / re-evaluated Metric Snapshot
```

The correction history remains attributable and traceable.

## Calculation provenance

Every Metric Snapshot must be traceable to:

```text
Metric Snapshot
      ↓
Metric Definition version
      ↓
Review Period / evaluation context
      ↓
Input source snapshot/history
      ↓
Deterministic calculation
```

The implementation may use references rather than duplicating every raw source value, provided the referenced historical inputs remain reproducible.

## Time-period behavior

The Review Period is the primary business calculation boundary.

The Metric Engine does not continuously rewrite historical period results as new live source state arrives.

Historical Reviews remain stable representations of the evaluation made for their period.

## Example — Flow Balance

S-010 defines:

```text
Flow Balance =
Work Items created during the Review Period
-
Work Items resolved during the Review Period
```

Example:

```text
Review Period: Aug 17–23
Created: 34
Resolved: 28

Flow Balance = +6
```

The Metric Snapshot must reference the applicable source/input snapshot/history and the Metric Definition version used for that calculation.

## Example — Completion Rate

Completion Rate is conditionally enabled under S-010.

The pilot configuration explicitly determines whether a defensible commitment cohort exists.

For example:

```text
uses_sprints = YES
```

may enable the metric.

For a continuous-flow installation without a defensible commitment boundary:

```text
Completion Rate = DISABLED
```

ORBIT does not approximate the metric using arbitrary Jira due dates.

## Metric dependencies

Metric Definitions declare their required inputs.

Examples:

```text
FLOW_BALANCE
requires:
- WorkItem.created_at
- WorkItem.resolved_at
```

```text
CYCLE_TIME
requires:
- WorkItem.created_at
- WorkItem.resolved_at
```

```text
COMPLETION_RATE
requires:
- configured commitment-cohort data
- resolution/completion data
```

This dependency declaration supports deterministic evaluability checks.

## Calculation failures

A failed calculation must not produce a valid-looking value.

For example:

```text
ERROR
```

must not silently become:

```text
0
```

A failed Metric Snapshot must not be treated as a valid Finding input.

## Testing

The Metric Engine requires:
- unit tests with exact expected outputs,
- boundary tests,
- timezone/DST boundary tests using real IANA zones,
- missing-input tests,
- property/invariant tests,
- multi-week historical fixture tests,
- regression tests for frozen metric definitions.

Examples of boundary coverage include:
- empty Review Period,
- single Work Item,
- zero resolved items,
- all items resolved,
- timezone boundary,
- DST transition,
- missing required field,
- disabled metric,
- calculation error,
- repeated evaluation with unchanged input snapshot.

## Explicitly deferred

S-023 does not decide:
- Finding materiality thresholds,
- Finding rule semantics,
- AI interpretation,
- UI visualization,
- generic user-authored formula engines,
- analytics warehouses,
- alternative databases,
- universal metric builder/configuration UI.

Those belong to later decisions.
# 14J. S-024 — Deterministic Finding Engine
**STATUS: LOCKED**

## Decision

ORBIT v0 uses a deterministic, versioned Finding Engine that evaluates explicit Rule versions against Metric Snapshots and other declared evaluation inputs.

The Finding Engine answers:

> **Does this matter enough to surface?**

It does not redefine Metric calculation semantics.

## Engine boundary

```text
Metric Snapshot
      +
declared supporting source/context
      ↓
Finding Engine
      ↓
Rule Version
      ↓
Evaluation
      ↓
Evidence
      ↓
Finding
```

The Finding Engine does not make direct Jira API calls during normal evaluation. It consumes stable persisted inputs so historical evaluations remain reproducible.

## Rule structure

A Rule version explicitly defines identity, version, enabled/configured state, required inputs, evaluation/materiality logic, severity semantics, and output semantics. Rule definitions are versioned according to S-016. v0 does not expose arbitrary user-authored programming expressions.

## Metric / Rule separation

S-023 owns calculation semantics. S-024 owns materiality, thresholds, warning/critical boundaries, Finding classification, and Finding lifecycle evaluation.

Example: `Flow Balance = +6` is a Metric result. Whether `+6` constitutes a WARNING or CRITICAL condition is a Rule/Finding decision.

## Required inputs and evaluation outcomes

Each Rule version declares required evaluation inputs. Outcomes are:
- `TRIGGERED`
- `NOT_TRIGGERED`
- `NOT_EVALUABLE`
- `DISABLED`
- `EVALUATION_ERROR`

`NOT_EVALUABLE` means the active rule path lacks usable required input. `DISABLED` means the path is not enabled for the installation. `EVALUATION_ERROR` means the engine failed unexpectedly. These execution outcomes remain distinct from S-012's user-facing Finding lifecycle.

## Pure evaluation

The core operation is conceptually:

```text
evaluate(rule_version, evaluation_context)
    → evaluation_result + evidence
```

It does not call Jira, mutate unrelated state, create Decisions/Commitments, send notifications, or modify Reviews. Persistence and lifecycle reconciliation occur in a separate orchestration layer.

## Finding identity vs evaluation

**Finding identity** is the ongoing logical condition identified by relevant rule + subject/scope.

**Finding evaluation** is a specific determination under Rule version, Review Period, input snapshot/version, and relevant evaluation configuration/context.

One logical Finding can therefore have multiple historical evaluations across periods.

## Evaluation identity / idempotency

The logical identity of an evaluation is:

```text
rule
+
rule_version
+
Review Period
+
input_snapshot_version
+
relevant evaluation configuration
```

Same logical identity is a no-op for canonical evaluation creation. A changed input snapshot version in the same Review Period creates a new/superseding evaluation without overwriting the prior one.

## Finding orchestration

The orchestration layer maps a completed evaluation onto persistent Finding identity and lifecycle.

### TRIGGERED
- No applicable Finding → create it, persist evaluation, set `ACTIVE`.
- Existing `ACTIVE` Finding → persist evaluation, remain `ACTIVE`.
- Existing `ACKNOWLEDGED` Finding → persist evaluation and transition back to `ACTIVE`.

The final transition is mandatory: acknowledgment is not permanent suppression of a still-triggering condition.

### NOT_TRIGGERED
- Existing `ACTIVE` or `ACKNOWLEDGED` Finding → persist evaluation and transition to `SYSTEM_RESOLVED` according to S-012.
- No logical Finding → do not create an active Finding solely from `NOT_TRIGGERED`.

### NOT_EVALUABLE / DISABLED
No active Finding is fabricated. Preserve execution/evaluation information where needed for reproducibility/diagnostics. Disabled paths do not create Findings.

### EVALUATION_ERROR
Do not interpret as `NOT_TRIGGERED`. Record an operational diagnostic and surface the failure through Review preparation health indicators.

## Finding lifecycle

```text
NOT_PRESENT
    ↓
ACTIVE
    ↓
ACKNOWLEDGED
    ↓
SYSTEM_RESOLVED
```

A fresh trigger may move `ACKNOWLEDGED → ACTIVE`. Historical evaluations remain distinct from current lifecycle state.

## Evidence and severity

Every triggered Finding and relevant evaluation must be traceable to Evidence identifying the concrete inputs that caused the evaluation, such as Metric Snapshot values, comparison values, source snapshot/history, materiality comparison, and Rule/version reference.

Severity is a deterministic Rule/materiality outcome (for example INFO, WARNING, CRITICAL). Human acknowledgment does not alter the original deterministic result.

## Rule changes

A changed Rule creates a new version. Historical evaluations continue to reference the prior Rule version. Explicit re-evaluation of an old period under a new Rule creates a new evaluation; it does not mutate the old one.

## Review preparation error visibility

An enabled Rule evaluation error must be visible in the manager-facing PREP health section, e.g. `Rule engine: 1 evaluation failed`. Absence of a Finding must never imply every enabled Rule evaluated successfully.

## Rule dependencies

Rules should be independently evaluable where possible. v0 does not introduce a generic Finding-to-Finding dependency graph. Metric-backed Rules use explicit dependencies such as `Metric calculation → Finding evaluation`.

## Testing

Required coverage includes:
- exact Rule unit tests,
- threshold boundary tests,
- missing-input tests,
- Finding lifecycle tests including ACKNOWLEDGED reactivation,
- evaluation idempotency tests,
- same-period correction/supersession tests,
- multi-week historical tests,
- Review PREP error-visibility tests.

## Explicitly deferred

S-024 does not decide new KPI definitions, Metric Engine semantics, a universal user-authored rule language, generic workflow automation, AI interpretation, autonomous execution, cross-system blocker resolution, or a generic rule dependency graph.

# 14K. S-025 — Review Workspace & Frontend Architecture
**STATUS: LOCKED**

## Decision
ORBIT v0 uses a **Next.js + React + TypeScript web interface** centered on a decision-oriented Engineering Weekly Review workspace rather than a dashboard-first experience.

The frontend owns presentation, interaction, navigation, local UI state, and feedback. The backend remains authoritative for business rules, authorization, persistence, synchronization, Finding evaluation, transactions, and workflow state.

## Meeting navigation model
The Meeting Workspace uses a **hybrid agenda model**:
- persistent agenda
- active Review Item
- direct navigation/jump anywhere

The agenda must make undispositioned items impossible to miss and visibly distinguish pending, completed/dispositioned, deferred, resolved, manual, Finding-backed, and materially changed items.

## Completion safety
Before a Review can be marked COMPLETED, every required agenda/promoted Review Item, including MANUAL items, must have a valid disposition and any resulting Decision/Commitment state must satisfy its workflow rules.

If required items remain open, completion is blocked and the UI must show an explicit actionable list. The system must not silently refuse completion.

## Post-Review Summary
The completed Review's History/detail view is the v0 Post-Review Summary and presents:
- decisions made
- commitments created
- outstanding items
- relevant owners/follow-up
- people notified where applicable

A separate summary route is not required.

## Discussion capture
Governed state transitions require backend confirmation.

Live Discussion text is an intentional exception: use optimistic local echo with debounced background save, with clear unsaved/save-in-progress/failure feedback as necessary. A failed save must not be represented as persisted.

## Primary application surfaces
- Review Home / Review List
- Review PREP
- Meeting Workspace
- Review History / Post-Review Summary
- Configuration

## Evidence / freshness
Findings expose supporting Evidence directly. Freshness and source health are visible wherever stale data could affect decision quality.

## State changes
Changes after Review preparation are surfaced, with current state and timestamp. Prepared items are never silently removed or replaced; affected items still require explicit disposition.

## Manual items / Issues / Commitments
Manual Review Items retain `origin = MANUAL`. Ongoing Issues show cross-period continuity. Commitments clearly expose owner, due date, current state, derived overdue status, origin, and relevant ownership history. Inactive owners produce an explicit reassignment signal without erasing historical attribution.

## Error and degraded-state UX
The UI distinguishes valid negative/empty states from failures:
- NOT_TRIGGERED is not an error
- NOT_EVALUABLE explains missing/unusable input
- DISABLED explains configuration
- EVALUATION_ERROR appears in Review health
- sync failures appear as source/data-health issues
- authorization denial is distinct from empty data

Major surfaces define loading, populated, empty, stale/degraded, unauthorized, and error states. An empty result must not ambiguously mean "no problem" when data is unavailable or evaluation failed.

## Authorization
The frontend may hide/disable actions for usability, but backend authorization is the security boundary.

## API boundary
Frontend communicates through documented backend APIs and must not depend on Django models, database schema, Jira payloads, or private backend internals.

## Navigation / design
v0 navigation remains intentionally small:
```text
Reviews
 ├── Current Review
 └── History

Configuration
 └── Jira Connection
```
A small shared component vocabulary/design system supports consistency.

## Performance / deferred UI complexity
Optimize perceived responsiveness without premature offline mutation, complex client synchronization, or real-time collaboration.

Exact UI library, state-management, data-fetching, charting, E2E, mobile, and offline choices remain implementation decisions.

# 14L. S-026 — API Contract & Application-Service Boundary
**STATUS: LOCKED**

## Decision
ORBIT v0 separates delivery/API concerns from application/use-case orchestration, domain behavior, and persistence/infrastructure concerns.

```text
Interface / Delivery
        ↓
Application / Use Cases
        ↓
Domain
        ↓
Persistence / Infrastructure
```

Django REST Framework views remain thin delivery adapters. Application services coordinate use cases and cross-module transactions. Domain modules own authoritative business rules. Persistence and provider-specific details remain behind appropriate adapters/interfaces.

## API layer
Responsible for authentication at the delivery boundary, request parsing, serialization, HTTP status codes, API validation, pagination where appropriate, API errors, and documentation. Substantial business logic does not live in DRF views.

## Application / use-case layer
Application services represent use cases such as Prepare Review, Start Review, Disposition Review Item, Create Decision, Create Commitment, Complete Review, Run Jira Sync, Evaluate Finding, and Configure Jira Connection. The application layer coordinates authorization, cross-module orchestration, transactions, domain invocation, and side effects.

## Domain layer
Domain modules own authoritative invariants and business behavior. Domain behavior is independent of whether the caller is REST, a background task, management command, or future webhook.

## Persistence / infrastructure
Persistence and external-service details remain behind explicit adapters/interfaces where an abstraction provides real value. Generic repository ceremony is not required merely for architectural appearance.

## DTO / model separation
API representations remain distinct from domain/persistence models:

```text
HTTP Request DTO
       ↓
Application Command
       ↓
Domain
       ↓
Application Result
       ↓
HTTP Response DTO
```

## Commands and queries
Use a lightweight conceptual distinction. Commands change state; queries read state. This is not full CQRS infrastructure.

## Authorization
Commands use authenticate actor → authorize command → validate → application service → domain → transaction.

Queries are authorized by scope and filtered by permitted resources; a single allow/deny check must not substitute for row/resource filtering.

## System actors
Background work executes as a defined, auditable system/scheduler actor with explicitly scoped permissions. Absence of a human user is never treated as an authorization bypass.

## Idempotency
State-transition commands such as Complete Review or Disposition Review Item use current-state checks so safe repeats become no-ops/current-state responses where semantics permit, without re-running downstream side effects.

Retriable creation commands such as Create Decision and Create Commitment use a client-supplied idempotency key to prevent duplicate creation.

## Events and side effects
Lightweight transactional events may represent state changes such as ReviewPrepared, ReviewCompleted, and CommitmentCreated and may trigger asynchronous side effects. Events are not the canonical persistence model.

Time-derived conditions such as Commitment overdue are not transaction-triggered domain events. A scheduled check may detect the condition and trigger an optional notification without introducing a stored overdue state.

## Side-effect boundary
Domain objects do not directly send notifications, call external providers, or perform unrelated side effects as hidden consequences of state mutation. The application/use-case layer coordinates such effects.

## Error model
The application distinguishes domain/business-rule errors, request/validation errors, authorization errors, and infrastructure/external-service failures. API representations must not expose secrets or internal implementation details.

## Shared application services
REST, background tasks, management commands, and future entrypoints invoke the same application/use-case services wherever they perform the same business operation. Business logic is not duplicated per entrypoint.

## API versioning
v0 does not introduce multi-version APIs without an actual compatibility requirement.

## Explicitly deferred
S-026 does not introduce full CQRS, event sourcing, Kafka/distributed event infrastructure, API gateway, service mesh, or generic repository abstractions for every ORM query.

# 14M. S-027 — Django ORM, Domain Model & Persistence Implementation
**STATUS: LOCKED**

## Decision

ORBIT v0 uses **Django ORM as the primary persistence abstraction over PostgreSQL**.

Django applications follow the S-018 bounded-context/module ownership model. API representations and frontend view models remain distinct from Django persistence/domain models.

Raw SQL is permitted only when a measured requirement or unavoidable database-specific operation justifies it.

## Logical vs physical database boundaries

v0 uses Django application/module boundaries as the primary logical separation.

PostgreSQL remains a single database and does **not** require one physical PostgreSQL schema per bounded context in v0.

This is intentional because Django ORM, migrations, testing, and cross-module foreign keys work naturally with conventional schema usage, while the primary module-isolation requirement is already enforced at the code/application boundary.

Physical PostgreSQL schema separation becomes worth introducing when a module is actually being extracted into an independently deployed service or when a concrete database-isolation requirement justifies it.

Python module boundaries are reinforced with static analysis such as `import-linter`, and violations fail CI.

## Model ownership

Django models follow S-018 ownership:

```text
organization
integration
credential
metric
finding
review
execution
```

`organization` owns:
- Organization
- Membership
- Team
- Project
- Work Item

Integrations populate shared domain concepts but do not own the concepts themselves.

`review` owns Issue.

## API/domain/persistence separation

The following are distinct concepts:

```text
API DTO
   ≠
Application command/result
   ≠
Domain object
   ≠
Django persistence model
   ≠
Frontend view model
```

They may represent the same business concept but serve different boundaries and responsibilities.

## IDs

v0 uses **UUIDv7** for ORBIT primary identifiers.

UUIDv7 is selected for time-ordered characteristics while retaining UUID-based generation semantics.

For the trusted internal v0 pilot, the approximate creation-time information embedded in UUIDv7 identifiers is an accepted trade-off.

If ORBIT later exposes identifiers to a less-trusted/public audience, reconsider whether a separate opaque public identifier is required.

## Timestamps and timezone

Persisted timestamps use a consistent timezone-aware UTC representation.

Business-period interpretation uses the IANA timezone identifier established by S-023.

Examples:

```text
Asia/Kolkata
America/New_York
Europe/London
```

A fixed UTC offset is not the canonical organization/business timezone representation.

## Structural vs behavioral constraints

Use database/Django constraints for structural invariants where practical.

Use application/domain services for contextual business invariants.

Example:

> Review cannot be completed while required Review Items remain undispositioned.

## Relationship deletion policy

The default relationship policy is **PROTECT/RESTRICT** unless a documented relationship-specific reason requires `CASCADE` or `SET_NULL`.

Destructive cascading is therefore opt-in.

Source disappearance never authorizes destructive deletion of unrelated historical ORBIT context.

## Historical and immutable records

ORBIT distinguishes mutable operational entities from immutable historical evaluations/records.

Examples:
- Metric Snapshots
- Finding Evaluations
- Rule Versions
- state-history records

Historical records are append-oriented and must not be silently rewritten.

## Shared immutability guard

Historical/append-only models use shared `ImmutableModel`-style infrastructure rather than independently hand-rolled guards in each module.

The guard rejects ordinary updates through the normal model save path after insertion.

This is one layer of protection, not the sole immutability guarantee: bulk updates, raw SQL, and migrations can bypass `save()` and are therefore governed by migration/review policy.

## Shared optimistic-concurrency implementation

Models requiring concurrent-write protection use shared `VersionedModel`-style infrastructure with an explicit integer/version token.

Conceptually:

```text
current version = 7
      ↓
UPDATE ... WHERE id = ? AND version = 7
      ↓
1 row → success
0 rows → conflict
```

The implementation does not rely on PostgreSQL `xmin` as the application-visible version.

## Migration discipline

All schema changes use reviewed Django migrations.

Fresh-database validation must confirm:

```text
fresh database
   ↓
all migrations
   ↓
valid application state
```

Migration behavior against accumulated historical data must also be tested.

### Immutable-table migration rule

Migrations may normally add schema objects and perform safe structural transformations.

A migration that modifies existing rows in an immutable/historical table is exceptional.

Such a migration requires:
- senior review,
- explicit documentation of why historical data is being corrected,
- stated provenance/correction semantics,
- confirmation that historical records are not being silently rewritten,
- appropriate regression testing.

Bulk `.update()` or raw SQL does not bypass this governance requirement.

## History consistency

Modules own their own historical records, but should use a consistent general pattern where applicable:

```text
current state
     +
append-only historical/version records
```

Shared reusable infrastructure should be used where technically appropriate. Event sourcing is not introduced.

## Indexing

Indexes are driven by actual access patterns.

In addition to source/projection and historical indexes, v0 explicitly accounts for the Finding orchestration lookup:

```text
rule
+
subject
+
scope
+
current non-terminal state
```

This is distinct from historical evaluation lookups by rule/version.

No broad index set is introduced without an actual query requirement.

## Persistence testing

Persistence tests include:
- fresh database/migration validation,
- model constraint tests,
- foreign-key/deletion-policy tests,
- immutability guard tests,
- optimistic-concurrency conflict tests,
- historical fixture migration tests,
- UUIDv7 behavior where relevant,
- critical query/index regression tests.

## Explicitly deferred

S-027 does not decide:
- database hosting/topology,
- read replicas,
- sharding,
- partitioning,
- analytics warehouse,
- search infrastructure,
- graph/vector projections,
- disaster recovery architecture,
- production backup strategy.

# 14F. S-028 — Automated Testing Strategy
**STATUS: LOCKED**

## Purpose
S-028 defines the automated testing strategy for ORBIT v0. It protects the behavior and invariants established by S-001–S-027 without introducing new product scope.

## Testing approach
The strategy uses a layered test pyramid:
- unit/domain tests for deterministic business logic; property-based testing is part of this tier, using Hypothesis where invariants benefit from generated cases,
- integration tests for real infrastructure boundaries where required,
- API/application-service tests for contracts, authorization, state transitions, and error behavior,
- database/persistence tests for constraints, immutability, optimistic concurrency, migrations, and critical queries,
- frontend/E2E tests where cross-surface behavior warrants them.

Tests begin with meaningful implementation rather than being deferred until the end of v0.

## Core invariants and decision coverage
Testing must explicitly cover, as applicable:
- deterministic metric calculations and snapshot identity,
- Finding evaluation identity, idempotency, lifecycle transitions, and ACKNOWLEDGED-to-ACTIVE reactivation,
- governed Review state transitions and completion rules,
- application-service authorization, including query-level scope filtering,
- defined system/scheduler actors for background operations,
- optimistic-concurrency conflicts,
- immutable historical records and append-only history behavior,
- UUIDv7 persistence behavior where relevant,
- migration behavior against both fresh and accumulated historical data.

## Credential and secret non-exposure
S-015's non-exposure requirement is independently testable and must be protected by dedicated tests. Deliberately triggered credential/authentication failures must verify that credential or secret material does not appear in:
- API responses or error bodies,
- exception messages,
- application logs,
- traces or diagnostics.

## Jira integration testing
S-028 exercises the canonical Jira fixture/contract set defined by S-022 rather than maintaining a second authoritative fixture list. This includes normal Work Items, unknown status, unmapped assignee, missing due date, missing sprint, deleted/unavailable issue, malformed response, rate limiting, authentication failure, pagination, retry/reprocessing, and historical backfill.

Default developer/CI execution remains fixture-first under S-021. Real connector validation uses the ORBIT-owned Jira sandbox; customer production data is not the default development test source.

## Test ownership and determinism
Tests should be deterministic, reproducible, and safe to run repeatedly. External systems are simulated or isolated except where an integration test specifically validates the real boundary. Historical fixtures should include accumulated review and finding history rather than only fresh databases.

## Deterministic application time
Time-dependent business behavior must use an injectable/controllable application-time source in tests. Tests must be able to freeze or advance time deterministically for Review Period boundaries, overdue computation, freshness/staleness, timezone behavior, and related temporal rules. Production code must not make these behaviors depend directly on an uncontrollable system clock.

## Test execution tiers
The suite should preserve fast feedback while supporting comprehensive coverage. A practical split is:
- fast tests for local development and pull-request gates,
- slower integration/frontend/E2E or broader regression suites on an appropriate scheduled/nightly cadence.
The exact CI platform and timings remain implementation details.

## Notification failure testing
Where a workflow produces notifications, tests must cover delivery failure, retry/diagnostic behavior, and the rule that notification failure does not falsely report the underlying governed state transition as failed or uncommitted.

## Explicitly deferred
S-028 does not choose a specific frontend E2E framework, CI/CD platform, deployment platform, observability platform, or load-testing infrastructure. Those remain subsequent implementation/infrastructure decisions.

# 14G. S-029 — Frontend Architecture & Implementation Structure
**STATUS: LOCKED**

## Decision

ORBIT v0 uses a **workflow-oriented frontend architecture** built with Next.js + React + TypeScript, with the Engineering Weekly Review as the primary v0 workflow. The frontend is designed for the long-term ORBIT trajectory but implements only the structure and complexity justified by the current product.

The frontend is a client of authoritative backend state. It owns presentation, interaction, navigation, local UI state, and user feedback; it does not reimplement authoritative business rules, authorization, persistence semantics, synchronization, metric calculation, Finding evaluation, or workflow transitions.

## v0 application structure

The initial structure is intentionally lightweight and workflow-oriented:

```text
frontend/
├── app/                         # Next.js routes / application shell
├── features/
│   └── review/                  # Primary v0 workflow
│       ├── finding/
│       ├── commitment/
│       ├── decision/
│       ├── issue/
│       └── evidence/
├── shared/                      # genuinely reusable UI/utilities
└── lib/                         # API, auth, query/configuration infrastructure
```

The exact repository naming may evolve during implementation, but the architectural rule is stable: organize the v0 frontend around the Review workflow rather than creating a separate top-level frontend architecture for every backend entity.

## No premature entity layer

A top-level `entities/` layer is intentionally **not** introduced in v0.

Finding, Commitment, Decision, Issue, and Evidence are currently composed primarily through the Review workflow. Separating them into independent frontend domain layers before a second genuinely independent workflow needs them would add abstraction without demonstrated value.

A concept may be promoted into a shared/domain-oriented frontend module when multiple real workflows independently compose or depend on it. This is a promotion path, not a prohibition against future domain separation.

Conceptually:

```text
v0
features/review/
      ↓
second genuinely independent workflow appears
      ↓
promote genuinely cross-workflow concepts
      ↓
shared/domain modules where justified
```

## State architecture

Frontend state is divided by responsibility:

### Server state

Authoritative backend data is treated as server state and accessed through a dedicated data-fetching/query layer. The frontend does not maintain an independently authoritative copy of domain entities.

### Local UI state

Transient interaction state belongs locally to the relevant component/workflow, such as:
- selected Review Item,
- expanded Evidence,
- open/closed dialogs,
- active tabs,
- filters,
- temporary input state.

### Workflow progress

Workflow progress through Inspect → Discuss → Decision → Commitment → Disposition is **derived from existing authoritative and draft state where possible**, rather than represented as an independent client-side state machine.

For example, the frontend should not maintain redundant flags such as `hasReachedCommitment` when that status can be derived from the presence/state of the relevant Decision, Commitment, and Disposition data.

This follows ORBIT's broader derived-state principle: store authoritative facts; derive deterministic state.

### URL state

Navigation state that should survive refresh or be directly addressable may be represented in the URL, such as the active Review or Review Item.

## API boundary

The frontend communicates through documented backend APIs and must not depend directly on:
- Django models,
- database tables/schema,
- Jira payloads,
- private backend module internals.

Conceptually:

```text
React component
      ↓
feature query/mutation
      ↓
frontend API client
      ↓
REST API
      ↓
application service
      ↓
domain / persistence
```

The backend remains the security and business-authority boundary.

## Server-state and mutation behavior

A dedicated server-state/query library may be selected during implementation. Its cache behavior must not override ORBIT's product semantics.

Governed mutations such as completing a Review, creating a Commitment, creating a Decision, resolving an Issue, or disposing a Review Item require backend confirmation before the frontend represents the authoritative transition as completed.

Discussion text is intentionally different under S-025: it uses optimistic local echo with debounced background persistence and must clearly communicate unsaved, saving, or failed-save states where relevant. A failed save must never be represented as persisted.

## Prepared Review state-change protection

This is a first-class frontend architectural rule.

For a Review that has already been prepared, a background refetch must not blindly replace the prepared state shown to the manager.

If server state relevant to an already-rendered prepared Review Item has changed:

```text
prepared Review Item state
          ↓
background refetch
          ↓
compare with prepared state
          ↓
    ┌─────┴─────┐
 unchanged     changed
    ↓              ↓
normal refresh  StateChangedNotice
                   ↓
             manager decides
```

The frontend must surface the changed state and timestamp through the `StateChangedNotice` behavior established by S-025. It must not silently remove or replace the prepared Review Item.

## Component architecture

Components follow three practical levels:

```text
shared UI primitives
        ↓
workflow/domain components
        ↓
page/workspace composition
```

Examples include shared buttons/forms/dialogs, workflow components such as FindingCard, CommitmentPanel, EvidencePanel and StateChangedNotice, and higher-level Review Workspace composition.

Abstractions are created when genuine reuse or a clear responsibility boundary exists. The frontend does not introduce a repository/service/adapter/factory abstraction for every small concept merely for architectural symmetry with backend code.

## Design system

v0 uses a small shared component vocabulary for recurring UI primitives and consistency. It is not a standalone design-system product.

A dedicated UI/design-system platform is deferred until actual reuse, multiple products, or organizational scale justifies it.

## Testing

Frontend testing follows S-028's layered strategy.

- **React Testing Library** is the primary component/hook testing approach.
- High-value user journeys should be covered by the eventual E2E framework selected in a later implementation decision.
- The prepared-Review state-change diffing behavior must have an explicitly named test: a server-side change after preparation results in `StateChangedNotice` rather than silently replacing the prepared state.
- The underlying state-diffing logic should also be tested directly so the safety property is protected independently of a particular component rendering path.

The exact E2E framework remains deferred.

## Performance and complexity

Optimize the Review workflow for perceived responsiveness without introducing offline mutation, complex client synchronization, real-time collaboration, micro-frontends, or other infrastructure before an actual requirement justifies it.

A dedicated global entity store is not required for v0. Server-state caching and local UI state should remain separate from authoritative domain state.

## Long-term evolution

The architecture is intentionally compatible with the larger ORBIT roadmap:

```text
Engineering Weekly Review
          ↓
additional independent workflows
          ↓
shared domain concepts where reuse is proven
          ↓
broader organizational operating surfaces
```

The existence of the long-term platform vision does not justify implementing its future frontend architecture today.

## Explicitly deferred

S-029 does not choose:
- exact CSS/UI component library,
- exact server-state/data-fetching library,
- exact E2E framework,
- mobile/native architecture,
- offline-first architecture,
- real-time collaborative editing,
- micro-frontends,
- GraphQL,
- a standalone design-system platform,
- a generalized frontend entity framework.

These remain implementation or future architectural decisions unless a concrete product requirement changes their status.

---

# 14H. S-030 — CI/CD & Engineering Workflow
**STATUS: LOCKED**

## Decision

ORBIT v0 uses continuous integration with protected mainline development and controlled promotion toward production. The goal is to make the safest engineering path the easiest path for a multi-developer team without introducing unnecessary enterprise delivery machinery.

## Repository strategy

v0 uses a single repository containing the frontend and backend.

Conceptually:

```text
orbit/
├── backend/
├── frontend/
├── tests/
├── scripts/
├── docs/
└── ...
```

The frontend and backend may still be deployed independently later; the repository boundary is a product/team boundary, not a deployment constraint.

v0 does not introduce multiple repositories, Git submodules, or a monorepo management framework solely for future scale.

## Branching model

```text
main
 │
 ├── feature/...
 ├── fix/...
 └── chore/...
```

`main` is protected. Developers do not push directly to `main`. Meaningful changes enter through pull requests, required CI checks, and code review.

Long-lived GitFlow-style branches are not introduced for v0.

## Pull request requirements

A meaningful pull request should state:
- what changed,
- why it changed,
- which existing decision it implements or affects,
- what tests demonstrate the behavior,
- whether it introduces a migration,
- whether it changes an API contract,
- whether it modifies immutable/historical data.

Required CI checks must pass before merge.

## Code review

At least one other engineer reviews a normal PR before merge.

Changes involving elevated risk require appropriate additional review, including:
- authentication/authorization,
- credential handling,
- immutable/historical data,
- migrations modifying existing records,
- persistence/concurrency mechanisms,
- security-sensitive infrastructure.

## CI pipeline

The PR-blocking path covers, as applicable:

```text
Backend
├── formatting/lint
├── static/type checks
├── unit/domain tests
├── property-based tests
├── integration/API tests
└── migration checks

Frontend
├── formatting/lint
├── TypeScript checks
├── component/hook tests
├── relevant workflow tests
└── production build

Cross-system
├── OpenAPI contract check
└── generated frontend-type drift check
```

S-028 remains authoritative for the underlying testing strategy.

## Test execution tiers

### PR-blocking tier

Uses deterministic fixtures, isolated test infrastructure, and no customer production credentials.

This is the primary merge-safety gate.

### Broader integration tier

After merge and/or in an integration environment, run broader integration, workflow, frontend/E2E, migration, and regression validation as appropriate.

### Scheduled external-integration tier

Real Jira sandbox validation runs on a scheduled/nightly cadence and is **not** on the PR-blocking critical path.

It uses:
- ORBIT-owned Jira sandbox data,
- dedicated sandbox credentials,
- controlled test scope.

It never depends on a pilot customer's actual Jira project/data.

## API contract integrity

S-026's typed API boundary is mechanically enforced.

The backend OpenAPI schema is the authoritative API description.

Frontend API types are generated from that schema. CI regenerates the types and fails if the generated output differs from the committed version.

Conceptually:

```text
Backend code
     ↓
OpenAPI schema
     ↓
Generate frontend types
     ↓
Compare committed types
     ↓
DIFF?
 ┌───┴───┐
YES     NO
 │       │
FAIL    PASS
```

## Database migration safety

CI validates migrations against a clean database and realistic accumulated-history fixtures.

It also verifies that migrations are compatible with the intended deployment sequence rather than assuming schema change and application deployment are atomic.

## Immutable/historical migration gate

S-027's immutable-table rule is mechanically reinforced by testing resulting database state rather than relying on source-code pattern matching or developer self-declaration.

For protected immutable/historical tables, CI:

1. starts from the realistic accumulated-history fixture database,
2. computes a checksum of each existing row keyed by primary key,
3. runs the migration set under test,
4. computes the checksums again,
5. fails if any pre-existing protected row has changed unexpectedly.

This catches mutation regardless of whether it came through `RunPython`, bulk `.update()`, raw SQL, helper indirection, or another code path.

Any intentional historical correction must still satisfy S-027's explicit review/provenance requirements.

## Expand/contract migration discipline

ORBIT does not assume that old application code and new schema disappear atomically.

Where compatibility is required, migrations follow the expand/contract pattern:

```text
Expand
  ↓
Deploy code compatible with old + new schema
  ↓
Backfill where required
  ↓
Deploy code using new representation
  ↓
Contract old representation later
```

For example, a new required field should generally be introduced as nullable or otherwise backward-compatible before enforcement becomes mandatory.

## Old-code / new-schema compatibility check

Where required, CI must make the deployment-window compatibility test executable by:

1. checking out the previous release tag,
2. applying the current migration set to a test database,
3. running the previous release's backend test suite against that migrated schema.

This detects migrations that would break the currently deployed application during a rolling/separate deployment sequence.

## Environment separation

The delivery flow is:

```text
Developer
   ↓
Pull Request / CI
   ↓
Integration / Staging
   ↓
Controlled Production Promotion
```

Production configuration/data is not required for ordinary development or PR validation.

## Secrets and credentials

The ordinary PR path must not require real customer credentials.

Production and sandbox credentials remain isolated from repository contents and ordinary developer jobs according to S-015.

No secret may be committed to Git, embedded into frontend builds, or exposed through CI logs.

## Main branch protection

`main` enforces:
- pull-request-only changes,
- required CI checks,
- required review,
- no force pushes by ordinary developers,
- no ordinary branch deletion/bypass of protection.

## Failure semantics

CI distinguishes:

### Code/application failure
Examples: test, lint, type, build, migration validation failure.

→ blocks the PR/merge as appropriate.

### CI infrastructure failure
Examples: runner or internal CI-service failure.

→ recover/retry CI without automatically treating application code as invalid.

### External sandbox failure
Examples: ORBIT Jira sandbox outage, sandbox credential expiry, provider-side rate limiting.

→ does not block the ordinary PR path because real sandbox validation intentionally lives in the scheduled external-integration tier.

## Production promotion

v0 uses controlled production promotion rather than unconditional automatic production deployment.

The pipeline should produce a validated release artifact that is promoted rather than rebuilding arbitrary source independently in production.

Exact deployment mechanics belong to S-031.

## Rollback principle

Application rollback and database rollback are not assumed to be the same operation.

The preferred migration/deployment pattern is to preserve backward-compatible schema states so an application can be rolled back without requiring dangerous destructive database rollback.

Exact rollback mechanics belong to S-031.

## Versioning and release traceability

v0 does not require elaborate public semantic-versioning mechanics for every change.

Releases should still have:
- immutable release identifiers/tags,
- deployment-to-commit traceability,
- deployment history,
- appropriate release notes/changelog entries.

Product V0/V1 terminology is not treated as a substitute for software-release identity.

## S-020 authorization enforcement

CI explicitly protects S-020's authorization requirements, including:
- command authorization,
- query-level scope filtering,
- system/scheduler actor permissions,
- relevant authorization regression tests established by S-028.

## Explicitly deferred

S-030 does not choose:
- exact CI/CD provider,
- exact cloud/hosting platform,
- deployment/orchestration platform,
- container strategy,
- infrastructure-as-code tooling,
- exact E2E framework,
- production observability implementation,
- autoscaling,
- disaster recovery,
- multi-region deployment,
- blue/green or canary infrastructure,
- Kubernetes/GitOps architecture.

These remain subsequent engineering/infrastructure decisions.

# 14I. S-031 — Deployment & Hosting Architecture
**STATUS: LOCKED**

## Decision class
**Foundational** — customer validation is not required. The V0 deployment topology is intentionally small, but the deployment principles are intended to remain valid as ORBIT expands beyond its initial Jira-based product wedge.

## Decision
ORBIT uses a small set of independently runnable production components within the modular-monolith architecture:
- Next.js web application
- Django API / modular monolith
- background worker using the same application code and application services

PostgreSQL remains the canonical persistent datastore and also hosts the v0 database-backed task backend. Production infrastructure should be managed rather than self-hosted where practical.

## Runtime topology
```text
                         Internet
                            |
                  +---------+---------+
                  |                   |
                  v                   v
              Next.js             Django API
                                      |
                              +-------+--------+
                              |       |        |
                              v       v        v
                         PostgreSQL   Jira   other approved
                              |              integrations
                         task tables
                              |
                              v
                           Worker
```

The API may interact directly with Jira **only** for the narrow synchronous credential-validation operation defined by S-015. Normal Jira synchronization, backfill, and external-data processing are worker-only.

## Artifact model
Web, API, and Worker runtime processes are built from the same immutable application artifact. They use different runtime entrypoints/commands and environment configuration; they are not independently built application images.

This preserves S-030's build-once, validate, and promote-the-same-artifact discipline across backend runtime processes.

## Background execution
The v0 task backend is database-backed and resides within the canonical PostgreSQL instance; it is not a separate queue service such as Redis. A managed scheduler may trigger task enqueueing, while the worker executes the task through the same application-service layer used by request-driven flows.

Exact task-backend package selection and verification of safe concurrent task claiming remain implementation details.

## Credential replacement and worker state
A successful credential replacement must take effect for subsequent worker operations without an indeterminate stale-credential window. For v0, credential activation/replacement triggers a controlled restart of affected workers so they reload the newly active credential reference before subsequent Jira operations.

The raw credential remains subject to S-015's validation-window and non-exposure requirements.

## Environments
The operational environment model is:
```text
Development -> Integration / Staging -> Production
```

Development is fixture-first and does not use customer production data. Staging uses an ORBIT-owned Jira sandbox project. Scheduled/nightly CI external-integration validation uses a **separate** ORBIT-owned Jira sandbox project so staging and CI cannot contaminate one another. Neither sandbox uses customer production data.

## Managed infrastructure
Production should prefer managed services for:
- PostgreSQL
- secret/configuration storage
- scheduling where practical
- TLS/certificate management where practical

The application and worker may run as containerized production artifacts where the selected platform uses them. Containerization is a production delivery mechanism, not a requirement that local development run inside containers.

## Network and security boundaries
- PostgreSQL is not publicly reachable.
- Production secrets are not committed to source control, embedded in images, or exposed to frontend bundles.
- Ordinary development and CI do not require customer production credentials.
- Developers do not require a production database password for normal deployment workflows.
- Production access is least-privileged and auditable.
- HTTPS is required for production application traffic.

## Migration and release behavior
S-030's migration discipline remains authoritative. Database migrations are controlled deployment artifacts and must preserve compatibility across the deployment window where required. Application rollback and database rollback are treated as separate operations.

Production deployments promote the validated artifact rather than rebuilding arbitrary source independently in production.

## Worker health
A worker deployment must provide a reliable platform-level liveness/health signal. The mechanism is intentionally platform-dependent: it may use process-level health monitoring or a minimal internal health endpoint if the hosting platform requires one. The architectural requirement is the health signal, not an HTTP endpoint specifically.

A replacement worker must not displace a healthy previous worker until the platform can establish that the new worker initialized successfully.

## Scaling boundary
The deployment architecture must permit Web, API, Worker, and managed database resources to scale independently when measured workload justifies it. V0 does not prescribe autoscaling thresholds or complex scaling infrastructure.

## Backup and recovery
Production PostgreSQL must use automated backups. Point-in-time recovery is preferred where available at reasonable cost. Formal RPO/RTO targets and multi-region disaster-recovery architecture remain deferred until actual operational requirements justify them.

## Hosting-region requirement
The selected hosting architecture/provider must support a region strategy that does not unnecessarily foreclose future data-residency requirements. The initial region may be selected based on the first pilot's actual constraints and operational/cost trade-offs. Formal regional/compliance requirements remain deferred until validated.

## IaC and platform scope
Production infrastructure that becomes non-trivial or must be reproducible should be declaratively defined and version-controlled. A specific infrastructure-as-code tool is not mandated by this decision.

The following remain explicitly deferred until justified by measured requirements:
- exact cloud/hosting provider
- Kubernetes
- service mesh
- multi-region deployment
- autoscaling policy
- blue/green or canary infrastructure
- elaborate traffic-management systems
- formal enterprise SLO/SLA
- detailed observability/SRE implementation
- advanced disaster recovery

## Relationship to eventual ORBIT
This decision is designed to be **future-compatible, not future-complete**. The deployment architecture must support the eventual ORBIT platform's broader multi-system and multi-workflow capabilities without requiring the V0 deployment to carry those capabilities today.


# 14F. S-032 — Observability & Operational Health Architecture
**STATUS: LOCKED**

## Decision
ORBIT uses a provider-neutral, layered observability architecture that distinguishes infrastructure/application health from data/domain health and user impact. Operational telemetry must preserve traceability, protect secrets/customer data, and make trust failures visible rather than silently suppressed.

### Health layers
- **System health:** whether runtime components are alive and operational.
- **Application health:** whether ORBIT services, jobs, integrations, and workflows are behaving correctly.
- **Data/domain health:** whether source data, freshness, evaluations, and organizational state can be trusted.
- **User impact:** what degradation means for the user and the affected workflow.

Operational health and data health are separate concepts. A technically healthy system may still contain stale, incomplete, or otherwise untrustworthy business data.

### Correlation identifiers
Operational work must be traceable with distinct identifiers for distinct units of work:
- `request_id` — HTTP/application request
- `task_id` — background task execution
- `sync_run_id` — one connector synchronization run
- `evaluation_id` — one Finding evaluation attempt, regardless of whether triggered by schedule, synchronization completion, or Review preparation

### Error taxonomy
The operational error taxonomy includes:
- VALIDATION
- AUTHENTICATION
- AUTHORIZATION
- RATE_LIMIT
- TIMEOUT
- NETWORK
- PROVIDER
- DATA_FORMAT
- MAPPING
- DATABASE
- CONCURRENCY
- CONFIGURATION
- INTERNAL
- **IMMUTABLE_HISTORY_VIOLATION**

`IMMUTABLE_HISTORY_VIOLATION` is a reserved first-class category for attempted or detected violations of immutable historical-record guarantees. It must not inherit generic category-based suppression, sampling, or alert-deduplication rules that could make the signal invisible.

### Credential propagation
When an activated integration credential is replaced, the v0 mechanism is a controlled worker restart so running workers receive the newly active credential reference.

### Task backend relationship
The Task Backend is not an independent infrastructure service in the v0 topology. It is backed by tables within the canonical PostgreSQL instance selected by S-017/S-019; no separate Redis/task-queue service is implied by the architecture.

### Runtime artifact
Web, API, and Worker are separate runtime processes/entrypoints built from the **same application artifact**. They are not independently built application images. This preserves S-030's build-once/promote-the-same-artifact discipline while allowing different process commands.

### Local telemetry isolation
Fixture-first development remains the default. When real Jira sandbox validation is intentionally performed locally, local telemetry must use a destination genuinely separate from production observability infrastructure. Sandbox data and diagnostics must not be forwarded to production telemetry destinations by default.

### Explicitly deferred
S-032 does not choose a specific observability vendor, alerting product, metrics backend, tracing backend, logging platform, or advanced SRE implementation. Those remain implementation decisions.

---

## S-033 — Application Security, Trust Boundaries & Threat Model

STATUS: LOCKED
Classification: FOUNDATIONAL
Customer validation required: NO for the core security architecture
Decision owner: Joint founder/engineering decision
Depends on: S-015, S-020, S-026, S-027, S-030, S-031, S-032
Does not replace or amend those decisions.

1. DECISION STATEMENT

ORBIT will use a threat-model-driven, least-privilege, defense-in-depth security architecture based on explicit trust boundaries between users, browsers, ORBIT application components, tenant data, credentials, background workers, databases, and external systems.

Security will be treated as a cross-cutting architectural property, not as a collection of isolated implementation controls.

The V0 security architecture will prioritize:

1. strict organization/tenant isolation,
2. server-side authorization at every application boundary,
3. backend-only handling of integration credentials,
4. isolation of external-system failures and untrusted input,
5. safe handling of sensitive data in persistence, logs, telemetry, and errors,
6. protection of immutable/historical organizational records,
7. secure background-job execution,
8. explicit trust boundaries and data-flow ownership,
9. dependency and deployment supply-chain hygiene,
10. auditable security-relevant administrative actions.

This decision establishes security architecture and invariants, while concrete security products and enterprise controls remain implementation decisions.

2. WHY S-033 IS GENUINELY NEW

Existing decisions already cover important pieces:

S-015 — Credential & Secrets Handling
Defines organization-scoped credentials, backend-only access, least privilege, validation before activation, rotation/revocation, no secret exposure, and safe disconnect behavior. This is credential lifecycle security.

S-020 — Authentication & Authorization
Defines local authentication, roles, membership scope, command authorization, query scope filtering, and explicit system actors for background execution. This is application access control.

S-027 — Persistence
Defines protection around immutable/historical records, versioning, deletion semantics, and persistence implementation discipline. This is data-integrity protection.

S-030 — CI/CD
Defines protected main, review/CI gates, migration verification, compatibility checks, and sandbox isolation. This is engineering and delivery security/reliability discipline.

S-031 — Deployment
Defines Web/API/Worker boundaries, worker-only normal Jira operations, managed infrastructure preferences, backups, HTTPS, and least privilege. This is runtime/deployment architecture.

S-032 — Observability
Defines layered health, correlation IDs, protected telemetry, and security-relevant error categories. This is security-aware operational visibility.

What is missing is a canonical system-wide answer to:

“What does ORBIT trust, what does it not trust, where can data cross boundaries, what security invariants must always hold, what are the primary threats, and what happens when one boundary is compromised?”

That is the purpose of S-033.

3. SECURITY PHILOSOPHY

3.1 Never trust the boundary because it is “inside ORBIT”

Authentication proves identity. Authorization proves permission.

Neither means that a request, object identifier, serialized payload, integration response, or internal message should automatically be trusted.

Every boundary validates its inputs according to its responsibility.

3.2 Tenant isolation is a security invariant

An Organization is a security/data boundary in V0.

Data belonging to Organization A must never become observable or mutable through a request authorized only for Organization B.

This applies to API reads, API writes, background jobs, database queries, exports, notifications, audit/history views, integration credentials, cached data, generated artifacts, and telemetry where customer data could appear.

A technically valid query is not sufficient; it must also be scoped to the authorized Organization.

3.3 Customer data remains protected after ingestion

Once external data enters ORBIT, it becomes ORBIT-held customer data even if the external system remains authoritative for its native fields.

Source authority does not eliminate ORBIT’s responsibility to protect its local copy.

4. TRUST-BOUNDARY MODEL

Conceptual V0 trust model:

HUMAN / EXTERNAL USERS
        |
        | untrusted input
        v
BROWSER / CLIENT
        |
        | authenticated request
        v
ORBIT API
(authentication, authorization, validation)
        |
        | application boundary
        +----------------------+
        |                      |
        v                      v
ORBIT DOMAIN / APP       BACKGROUND WORKER
        |                      |
        +----------+-----------+
                   |
                   v
              POSTGRESQL
              ORBIT DATA

BACKGROUND WORKER
        |
        | credential access
        v
EXTERNAL SaaS / JIRA

Critical boundaries:

User -> Browser:
The browser is not trusted with secrets or authorization decisions.

Browser -> API:
All input is untrusted until validated and authorized.

API -> Application/Domain:
Delivery code cannot bypass application/domain invariants.

Application -> Persistence:
Database access must preserve tenant scope, ownership semantics, versioning, and immutable-history guarantees.

API -> Jira (credential-validation-only):
This is a narrow outbound trust boundary used only for S-015 credential validation. It must not be used for normal Jira data operations.

Worker -> External Provider:
External data is treated as untrusted external input and cannot directly dictate ORBIT internal semantics.

Worker -> Credential subsystem:
Workers obtain only the credential capability required for the specific organization/integration operation.

ORBIT -> External provider:
External systems are not trusted as executors of ORBIT business logic. They provide source data or, in later stages, authorized action capabilities.

5. THREAT MODEL

S-033 does not attempt to enumerate every conceivable attack. It establishes threats that materially shape ORBIT architecture.

T1 — Cross-organization data leakage

An attacker or software defect causes data from one organization to become accessible to another.

Required defenses:
- organization-scoped authorization,
- mandatory query scoping,
- explicit organization context in application services,
- background jobs carrying explicit organization scope,
- tenant-isolation tests,
- no reliance on frontend filtering for security.

T2 — Broken object-level authorization

A user changes an object ID and obtains access to an object outside their scope.

Required defense:
Authorization must be evaluated against the resource and its organization/scope, not merely against the endpoint.

T3 — Privilege escalation

A lower-privileged user attempts an administrative or workflow-sensitive operation.

Examples:
- replacing Jira credentials,
- changing integration configuration,
- changing organization membership,
- changing role assignments,
- mutating review state outside permitted workflow,
- manipulating another user’s commitments.

Required defenses:
- centralized application authorization semantics from S-020,
- explicit command permissions,
- no trust based on UI visibility,
- authorization regression tests.

T4 — Credential compromise

An attacker, compromised process, developer mistake, or malicious dependency attempts to obtain Jira credentials.

Required defenses:
S-015 remains authoritative:
- credential storage protected,
- backend-only access,
- least privilege,
- validate-before-activate,
- rotation/revocation,
- no secret exposure through logs/traces/errors/responses.

S-033 adds:
No component receives credential material unless the component genuinely needs it.

T5 — Malicious or malformed external data

External provider responses must be considered untrusted input even when obtained through valid credentials.

Possible causes:
- malformed data,
- unexpected field structures,
- malicious content inserted into issue fields,
- unexpected URLs,
- oversized responses,
- provider behavior changes.

Required defense:
External data must pass through validation/normalization before it becomes trusted ORBIT domain state.

6. TAINTED-DATA BOUNDARY

External data should conceptually flow:

External Provider
      ->
Transport Response
      ->
Schema / Format Validation
      ->
Normalization
      ->
Domain Mapping
      ->
ORBIT-Owned Projection
      ->
Metrics / Findings / Review

The raw provider response is not automatically domain truth.

“Source authoritative” means that, after validating and interpreting the source according to the integration contract, the designated provider is the authority for its native fields.

7. INPUT VALIDATION

All externally controllable input must be validated before it reaches security-sensitive logic.

Includes:
- API request payloads,
- path/query parameters,
- IDs,
- URLs,
- configuration values,
- integration responses,
- webhook payloads if introduced later,
- imported/exported data,
- notification content,
- uploaded data if introduced later.

Validation must be performed server-side.

Frontend validation is for usability, not security.

8. OUTPUT ENCODING AND CONTENT SAFETY

ORBIT will treat stored external content as data, not executable instructions.

For example, a Jira issue summary containing HTML/JavaScript-like content must never become executable browser content merely because ORBIT displays it.

The frontend must use safe rendering/encoding by default.

Future AI-generated text is also untrusted content and cannot bypass ordinary rendering/security controls.

This does not introduce AI into V0.

9. SERVER-SIDE AUTHORIZATION INVARIANT

The frontend may hide functionality; only the backend may enforce security.

Therefore:
- UI permissions are hints,
- backend permissions are authoritative,
- API requests are never trusted because they originated from ORBIT’s own frontend,
- background jobs do not inherit the permissions of whoever happened to trigger them.

This aligns with S-020 and S-026 rather than creating another authorization model.

10. BACKGROUND-WORKER SECURITY

The Worker is a high-value trust boundary because it can access customer data, access integration credentials, write organizational state, and trigger deterministic processing.

Requirements:

Explicit system actor:
Workers operate through the system/scheduler actor defined by S-020.

Explicit organization scope:
A job must identify the Organization/integration scope it is allowed to operate against.

No ambient authority:
A worker must not possess broad unrestricted access merely because it is a backend process.

No arbitrary job authority:
A task payload must not allow a user to manufacture authority by supplying a different organization ID or object reference.

The worker derives or validates its authorized scope from trusted persisted job state.

Safe retry:
Retries must not amplify authorization or create unintended duplicate security-sensitive actions.

11. INTEGRATION ISOLATION

ORBIT external integrations must be isolated from the core application.

For V0:
- Jira communication belongs in the integration boundary,
- normal Jira data operations remain Worker-driven,
- API-to-Jira direct access is limited to the S-015 credential-validation path.

The application domain must not become dependent on raw Jira HTTP behavior.

12. SSRF AND OUTBOUND-NETWORK SAFETY

V0 only supports Jira Cloud. ORBIT must not accept an administrator-supplied arbitrary Jira base URL. Instead, the integration configuration accepts a Jira site identifier, and ORBIT constructs the destination internally using the approved Atlassian Jira Cloud domain pattern.

This removes arbitrary administrator-controlled server-side URLs from the V0 Jira integration boundary and materially reduces the SSRF, unsafe-redirect, private-network-targeting, and DNS-rebinding attack surface.

The integration layer must still:
- use only the internally constructed approved Jira Cloud destination,
- avoid following redirects that escape the approved destination,
- define safe timeout and response-size behavior,
- validate provider responses before they become trusted ORBIT state,
- avoid turning generic URL fetching into a product capability.

The architecture must not evolve into a general-purpose server-side HTTP proxy.

Concrete networking implementation remains an implementation decision.

13. DATABASE SECURITY

PostgreSQL is canonical for ORBIT under S-017.

S-033 establishes:

Application-level tenant isolation is mandatory.
The database must never be treated as a substitute for application authorization.

Least-privileged database access.
Application components should use only the database capabilities they require.

Sensitive credentials are not normal application data.
Credential storage follows S-015 and must not leak into ordinary domain models.

Historical integrity is security-sensitive.
Attempts to mutate immutable records are security/integrity signals, consistent with S-027 and S-032.

Destructive operations are deliberate.
Source disappearance, disconnects, archival, and access revocation must not become accidental bulk deletion mechanisms.

14. SENSITIVE-DATA CLASSIFICATION

S-033 introduces a lightweight classification rather than a heavyweight enterprise data-governance system.

Class A — Secret material

Examples:
- API tokens,
- OAuth tokens,
- client secrets,
- private keys,
- signing secrets.

Rule:
Never expose in UI, logs, traces, metrics, errors, or ordinary audit records.

Class B — Customer organizational data

Examples:
- Jira-derived Work Items,
- findings,
- evidence,
- commitments,
- decisions,
- review content.

Rule:
Organization-scoped and protected from cross-tenant disclosure.

Class C — Operational metadata

Examples:
- request IDs,
- task IDs,
- sync IDs,
- evaluation IDs,
- timestamps,
- health signals.

Rule:
May be logged for operational purposes, but must not become an accidental channel for sensitive customer content or secrets.

15. LOGGING AND TELEMETRY SECURITY

Never log:
- API tokens,
- passwords,
- authorization headers,
- cookies containing credentials,
- private keys,
- secret configuration.

Be cautious with:
- Jira issue descriptions,
- customer-authored review content,
- email addresses,
- usernames,
- potentially sensitive organizational information.

Prefer structured identifiers such as:

organization_id
request_id
task_id
sync_run_id
evaluation_id
object_id
error_category

over logging entire objects.

S-032 remains authoritative for the operational telemetry model.

16. ERROR HANDLING

Security failures must fail closed, not fail open.

Authorization check fails:
DENY

Credential validation fails:
Do not activate credential.

Tenant scope cannot be established:
Do not access data.

External mapping is ambiguous:
Do not invent organizational state.

Historical immutability is violated:
Block mutation and emit a high-integrity security/operational signal.

17. SESSION AND BROWSER SECURITY

S-020 already chooses secure server-side sessions for V0.

S-033 adds:
- session cookies must not expose session secrets to JavaScript unnecessarily,
- production transport must use HTTPS,
- session invalidation must occur when required,
- disabled users cannot continue using an active session indefinitely,
- CSRF protections must apply to state-changing browser requests,
- authentication-related responses must not leak unnecessary information,
- authentication endpoints must enforce rate limiting / brute-force protection appropriate to V0,
- repeated failed authentication attempts must be throttled or otherwise constrained without creating unnecessary account-enumeration signals.

Concrete session middleware/configuration remains an implementation concern.

18. CSRF

Because V0 uses server-side browser sessions, state-changing browser requests must be protected against cross-site request forgery.

Any authenticated browser-originated state mutation must have an explicit CSRF defense appropriate to the chosen Django authentication/session mechanism.

This is not a new authentication model; it is a security invariant around S-020’s selected mechanism.

19. AUTHORIZATION VERSUS AUDIT

Authorization answers:
“May this action happen?”

Audit/history answers:
“What happened, who/what initiated it, and what state changed?”

S-033 does not create a new audit product.

Security-sensitive commands should leave sufficient history for investigation while respecting S-015’s prohibition on secret material.

Examples:
- credential activated/replaced/revoked,
- role changed,
- membership disabled,
- integration disconnected,
- significant administrative configuration changed,
- immutable-history violation attempted.

The actual product-level audit UI remains outside V0 unless another decision requires it.

20. DEPENDENCY AND SUPPLY-CHAIN SECURITY

S-033 establishes:
- dependencies must come from known sources,
- dependency versions should be reproducible,
- security updates must be reviewable,
- abandoned/unnecessary dependencies should not accumulate,
- CI should detect known vulnerable dependency versions where practical,
- runtime images should contain only required software,
- build artifacts should be traceable to source revisions.

S-030 provides the delivery mechanism; S-033 defines the security requirement rather than selecting a particular scanner.

21. BUILD AND RUNTIME SEPARATION

Build-time secrets must not accidentally become runtime application artifacts.

Examples:
- Jira credentials must never be bundled into frontend builds.
- Secret environment variables must not become NEXT_PUBLIC_* values.
- Build logs must not print sensitive variables.
- Frontend bundles must contain no credential material.

S-031’s one-artifact/multiple-runtime-entrypoint model does not remove this distinction.

22. PRODUCTION CONFIGURATION SECURITY

Security-sensitive configuration must be centralized, explicit, environment-specific, and fail-safe.

Examples:
- debug disabled in production,
- production secrets never committed to source,
- insecure development defaults must not accidentally become production defaults,
- security-sensitive configuration changes must be reviewable.

The specific cloud/provider mechanism remains outside S-033.

23. NETWORK SECURITY

V0 does not need an elaborate zero-trust enterprise network architecture.

It does require sensible network boundaries:

Internet
   ->
Web/API
   ->
Application
   ->
PostgreSQL

Worker
   ->
Jira

The design should avoid unnecessary public exposure of:
- PostgreSQL,
- worker interfaces,
- internal administration interfaces,
- task infrastructure,
- credential storage mechanisms.

24. SECURITY OF SOURCE-DERIVED DATA

ORBIT stores a local projection of external data because it needs deterministic historical analysis.

Therefore:

Once customer data enters ORBIT, it becomes ORBIT-held customer data even if the external system remains authoritative for its native fields.

This means:
- source authority does not eliminate ORBIT’s responsibility to protect its local copy,
- source disappearance does not justify unprotected retention,
- permissions apply to ORBIT’s copy,
- historical snapshots remain subject to organization isolation.

25. SECURITY OF DETERMINISTIC INTELLIGENCE

S-007 establishes deterministic, evidence-backed V0 intelligence.

Security controls must protect the provenance chain itself.

A user must not be able to fabricate, outside authorized workflows:

Finding
   ->
Evidence
   ->
Source / Rule / Calculation

Likewise, a malicious external payload must not be able to arbitrarily manufacture a trusted Finding.

This gives the security architecture a second goal beyond confidentiality: protecting organizational truth and provenance.

26. SECURITY OF IMMUTABLE HISTORY

ORBIT’s historical organizational memory is a product asset.

The security architecture must defend against:
- unauthorized access to history,
- unauthorized modification of history.

Historical evidence must not be silently rewritten by a compromised or incorrectly authorized application path.

This does not mean immutable history can never be corrected. S-008/S-027 already establish governed corrections and provenance.

Corrections must remain detectable and attributable.

27. SECURITY EVENT CATEGORIES

S-032’s error taxonomy remains canonical.

S-033 does not create a duplicate error taxonomy.

Security-relevant events should map into existing categories such as:
- AUTHENTICATION
- AUTHORIZATION
- CONFIGURATION
- IMMUTABLE_HISTORY_VIOLATION
- DATA_FORMAT
- MAPPING
- DATABASE
- CONCURRENCY
- INTERNAL

A future dedicated security incident/event subsystem should consume these existing signals rather than inventing a parallel operational taxonomy.

28. THREAT RESPONSE MODEL

V0 should not attempt to implement a full enterprise SIEM or security-operations platform.

Response model:

Detect
  ->
Contain
  ->
Preserve evidence
  ->
Restore safe operation
  ->
Investigate
  ->
Correct

Examples:

Invalid Jira credential:
- stop credential use,
- preserve historical context,
- surface connection health,
- allow credential replacement.

Cross-tenant authorization bug:
- deny access,
- capture operational identifiers,
- investigate affected scope,
- patch authorization path,
- add regression test.

Immutable history violation:
- reject mutation,
- preserve original history,
- emit unsuppressed signal,
- investigate caller/path.

29. SECURITY TESTING REQUIREMENTS

S-028 remains the canonical testing strategy.

S-033 adds security-specific test categories that fit into that existing pyramid.

Required categories:

Tenant isolation tests:
Prove Organization A cannot access Organization B data.

Object authorization tests:
Attempt direct access using another organization’s object identifiers.

Role escalation tests:
Verify each sensitive command rejects insufficient roles.

System actor tests:
Verify background jobs cannot exceed intended scope.

Credential non-exposure tests:
Already explicitly required by S-028/S-015.

External input tests:
Malformed and hostile provider responses must not bypass validation or crash into unsafe domain behavior.

CSRF/session security tests:
State-changing browser requests must require the expected protection.

SSRF/network-boundary tests:
Integration endpoints must not become arbitrary server-side network targets.

History-integrity tests:
Unauthorized updates to immutable/historical records must fail.

Logging tests:
Known secret values inserted into test requests must not appear in captured logs/errors/traces.

30. SECURITY PROPERTIES THAT MUST ALWAYS REMAIN TRUE

Invariant 1 — No cross-tenant access
A principal cannot read or modify another Organization’s data.

Invariant 2 — No frontend-only authorization
Security decisions are enforced server-side.

Invariant 3 — No ambient credential access
Only the execution path requiring a credential may access it.

Invariant 4 — No secret telemetry leakage
Secrets never appear in logs, traces, metrics, errors, audit records, or frontend payloads.

Invariant 5 — External input is untrusted
Provider responses are validated before becoming trusted ORBIT state.

Invariant 6 — Fail closed
Unknown/ambiguous authorization or security state denies rather than grants access.

Invariant 7 — History cannot be silently rewritten
Historical/immutable data is protected against unauthorized mutation.

Invariant 8 — Background jobs are explicitly scoped
Worker execution cannot manufacture broader authority from task parameters.

Invariant 9 — Integration boundaries are narrow
A provider adapter cannot become an unrestricted generic network/client layer.

Invariant 10 — Security signals remain observable
Security-sensitive failures cannot disappear through generic sampling/suppression.

31. V0 IMPLEMENTATION BOUNDARY

Required for V0:
- organization/tenant isolation,
- server-side authorization,
- secure session handling,
- authentication rate limiting / brute-force protection,
- CSRF protection,
- credential protection per S-015,
- safe external input handling,
- safe outbound integration boundaries,
- secret-safe logging,
- least privilege,
- immutable-history protection,
- dependency/security hygiene,
- security-focused automated tests,
- HTTPS in production,
- secure configuration practices.

Explicitly deferred:
- enterprise SSO,
- SCIM,
- fine-grained enterprise IAM,
- customer-managed encryption keys,
- HSM infrastructure,
- zero-knowledge architecture,
- customer-side encryption,
- full SIEM,
- security orchestration platform,
- enterprise DLP,
- formal SOC 2 machinery,
- ISO 27001 program,
- Kubernetes network policies,
- service mesh,
- multi-region security architecture,
- formal data residency/compliance framework,
- sophisticated secrets rotation automation,
- dedicated security operations team,
- penetration-testing program as a permanent product requirement.

These may become necessary as ORBIT moves toward broader adoption, but V0 should not pretend to be an enterprise security platform before the product has validated the market.

32. RELATIONSHIP TO MULTI-TENANCY

ORBIT V0 is a narrow pilot, but the security model should still be tenant-aware from the beginning.

This does not mean building an elaborate multi-tenant platform now.

It means avoiding architectural assumptions such as:

“there is only ever one organization”

inside domain or persistence semantics.

Instead:

Organization
    ->
authorized application scope
    ->
data access

should already be the normal model.

This is a future-compatible foundation, not a demand for premature multi-tenant infrastructure.

33. SECURITY ARCHITECTURE AND V0 SCOPE DISCIPLINE

S-033 must not become a reason to reopen the product wedge.

It should not result in building:
- a generic permission engine,
- a generic security-policy DSL,
- a full tenant administration center,
- a security dashboard,
- a generic audit product,
- a generic integration gateway.

The implementation should use the existing architecture wherever possible:

S-020 authorization
        +
S-026 application boundary
        +
S-015 credential semantics
        +
S-027 persistence rules
        +
S-031 runtime boundaries
        +
S-032 observability
        =
S-033 security architecture

34. SECURITY ARCHITECTURE OWNERSHIP BY MODULE

organization
Owns:
- organization boundary,
- memberships,
- role/scope relationships.

credential
Owns:
- credential lifecycle,
- protected credential access,
- secret-handling rules.

integration
Owns:
- external-provider trust boundary,
- request/response validation,
- provider isolation,
- outbound communication.

application/use-case layer
Owns:
- authorization orchestration,
- security-sensitive command boundaries,
- transaction/security coordination.

Domain modules
Own:
- business invariants,
- ownership semantics,
- lifecycle restrictions,
- immutable-history rules.

Persistence/infrastructure
Owns:
- safe data access,
- transaction semantics,
- connection security,
- database least privilege.

Observability
Owns:
- security-safe telemetry,
- correlation,
- security-relevant error visibility.

This follows the existing modular-monolith dependency direction instead of creating a separate security module that every module depends on.

35. FORMAL THREAT-MODEL ARTIFACT

S-033 requires a maintained threat-model document as an engineering artifact.

It should contain, at minimum:

Asset
Threat
Trust boundary
Attack path
Required invariant
Existing mitigation
Test coverage
Residual risk

Example:

Asset:
Jira API token

Threat:
Credential disclosure

Boundary:
Credential subsystem -> Worker

Invariant:
Raw credential never reaches frontend/logging

Mitigation:
S-015 credential handling

Test:
Secret non-exposure integration tests

Residual risk:
Compromised worker runtime

The threat model should evolve alongside architecture changes.

It does not need a heavyweight enterprise GRC system.

36. SECURITY REVIEW GATES

Security review is required when a change affects:
- authentication,
- authorization,
- organization scope,
- credentials/secrets,
- external integrations,
- database permissions,
- immutable/historical records,
- session handling,
- network access,
- logging/telemetry of sensitive data,
- production configuration,
- dependency/build security.

This fits the existing code-review model established by S-030 rather than adding a separate release bureaucracy.

37. ACCEPTANCE CRITERIA FOR S-033

S-033 should not be considered fully implemented until the engineering system can demonstrate:

Access control:
User -> authenticated
User -> authorized for organization
User -> authorized for operation
User -> authorized for resource

at every security-sensitive path.

Tenant isolation:
Automated tests prove that cross-organization reads/writes fail.

Credential isolation:
Automated tests prove that known test credentials cannot appear in logs, traces, errors, metrics, or API responses.

Integration isolation:
Malformed/untrusted Jira responses cannot bypass validation.

Worker isolation:
A forged or manipulated task payload cannot cause cross-organization execution.

History protection:
Unauthorized historical mutations fail and create an observable integrity signal.

Browser protection:
Session and state-changing requests use the expected Django security controls.

Authentication abuse protection:
Authentication endpoints enforce the required rate limiting / brute-force protection.

Outbound safety:
Integration endpoint configuration cannot become arbitrary server-side network access.

Supply-chain hygiene:
Dependencies and build artifacts are sufficiently controlled for V0 deployment.

Threat-model coverage:
All major V0 trust boundaries have documented threats, mitigations, and tests.

38. IMPORTANT NON-DECISIONS

To prevent S-033 from silently turning into another sprawling architecture decision, these remain intentionally open:

Secrets implementation:
S-015 remains authoritative; S-033 does not choose Vault/KMS/HSM/cloud secret manager.

Identity provider:
S-020 remains authoritative for V0 local auth. OIDC/SSO remains future work.

Database technology:
S-017 remains authoritative: PostgreSQL.

Deployment technology:
S-031 remains authoritative.

Observability technology:
S-032 remains provider-neutral.

Security/compliance certifications:
No certification program is being adopted by this decision.

AI security architecture:
Not needed for the V0 critical path; future AI architecture remains a separate decision.

39. DECISION CONSEQUENCES

Positive:
ORBIT gets a coherent security model before the system starts accumulating sensitive organizational data.

The architectural boundaries also make future expansion safer:

Jira
   ->
new SaaS source
   ->
multiple organizations
   ->
broader organizational context
   ->
actions
   ->
AI

without assuming that every new capability can bypass existing trust boundaries.

Cost:
There will be additional engineering work in:
- authorization tests,
- tenant scoping,
- secure configuration,
- integration validation,
- logging discipline,
- dependency management,
- security review,
- threat-model maintenance.

That cost is justified because ORBIT’s product value depends heavily on users trusting its organizational context.

Deliberate trade-off:
We are choosing strong foundational security invariants without enterprise-security overengineering.

40. FINAL LOCKED S-033 WORDING

S-033 — Application Security, Trust Boundaries & Threat Model — LOCKED

ORBIT uses a threat-model-driven, least-privilege, defense-in-depth security architecture based on explicit trust boundaries between users, browsers, application components, background workers, organization-scoped data, credentials, persistence, and external systems.

Organization is a fundamental security/data boundary. Cross-organization access is prohibited. Server-side authorization is authoritative; frontend visibility is never a security control. Background workers operate under explicit system-actor and organization scope and may not obtain authority from untrusted task parameters.

External provider data is treated as untrusted input and must be validated, normalized, and mapped before becoming trusted ORBIT state. External integrations remain isolated behind integration boundaries, and configured outbound endpoints must not become unrestricted generic network access.

Credential handling remains governed by S-015. Secrets are backend-only, least-privileged, validated before activation, rotatable/revocable, and never exposed through frontend responses, logs, traces, metrics, errors, or ordinary audit records.

ORBIT’s historical organizational data and immutable records are security-sensitive assets. Unauthorized mutation must fail and remain observable, consistent with S-027 and S-032.

Production sessions, state-changing browser requests, transport security, configuration handling, dependency/build hygiene, and network exposure must follow secure-by-default practices appropriate to V0.

Security controls are tested through the existing S-028 layered testing strategy, including tenant isolation, object authorization, privilege boundaries, worker scope, credential non-exposure, external-input validation, CSRF/session protections, outbound-network safety, and immutable-history protection.

S-033 defines security architecture and invariants. It does not select a specific secrets platform, identity provider, cloud security product, compliance framework, SIEM, service mesh, or enterprise IAM architecture.

The goal is strong foundational security without premature enterprise security machinery, preserving the project’s future-compatible, future-not-complete architecture principle.

LOCK FINALIZATION

S-033 is now LOCKED after the final review. The final amendments are:

1. V0 Jira integration accepts a site identifier rather than an arbitrary administrator-supplied base URL; ORBIT constructs the approved Jira Cloud destination internally.
2. V0 authentication endpoints explicitly require rate limiting / brute-force protection.
3. The Section 4 trust-boundary enumeration explicitly includes the API → Jira credential-validation-only boundary.
4. These amendments do not replace or amend S-015, S-020, S-026, S-027, S-030, S-031, or S-032; they compose those decisions into the system-wide security architecture defined by S-033.

Unlike customer-facing product decisions, the core of this decision does not require customer validation. It is a foundational engineering decision that can proceed in parallel with customer discovery.

---

# 14F. CUSTOMER DISCOVERY & V0 DECISION GATE

## Status
**ACTIVE WORKING PRINCIPLE — NOT A NEW LOCKED DECISION NUMBER**

Customer discovery is now a formal product-development gate for ORBIT V0. The purpose is to validate the underlying recurring workflow and pain before committing to additional major V0 product-scope decisions.

### What remains durable

The architectural work through S-030 is intended to provide a durable foundation for the eventual full-scale ORBIT product. It should support a future ORBIT that can connect multiple SaaS systems, gather organizational context, and eventually provide broader operating-rhythm and organizational execution capabilities.

The fact that V0 starts with a Jira-based Engineering Weekly Review does **not** mean ORBIT's foundational architecture should become Jira-specific. Existing decisions already preserve provider-agnostic concepts such as External Reference, provider-independent ownership/credential handling, application-service boundaries, and modular integration seams.

### What remains provisional

V0 is deliberately a narrow proof-of-concept wedge and a learning instrument. The following are product hypotheses rather than permanent commitments:

- Jira as the initial/only V0 source.
- Exact V0 metrics and review contents.
- Exact findings, evidence, and review presentation.
- Whether non-Jira engineering-adjacent metrics are manually entered.
- Which part of the recurring workflow provides the greatest customer value: preparation, reconciliation, meeting execution, decision capture, commitment follow-up, or another discovered pain point.
- Which additional integrations should follow Jira.

A V0 mechanism may later be **removed**, not merely extended. For example, a manually entered engineering metric may be useful before another system is integrated, then become unnecessary once ORBIT can obtain that metric automatically from an authoritative source. The architecture must therefore support replacement and removal as well as addition.

### Customer-discovery method

Before locking major new V0 product-scope decisions, research should reconstruct real recurring workflows with target users rather than primarily asking whether they would use ORBIT. Interviews should focus on:

- the last real recurring review they prepared or led;
- preparation time and people involved;
- systems opened and why each was needed;
- manual extraction, calculation, copying, and reconciliation;
- conflicting or missing information;
- meeting decisions and commitments;
- post-meeting follow-up and outcome tracking;
- existing workarounds, internal tools, and purchasing/security constraints;
- frequency, severity, and economic cost of the pain.

The initial target is approximately **5–12 high-quality interviews**, intentionally including likely users, people with the problem who solve it differently, and people who do not consider the problem significant. The exact sample is a research target, not a statistical requirement.

### Required research output

Customer discovery should produce a **Pain Map** covering:

**Systems → data gathering → reconciliation → review preparation → meeting → decisions → commitments → follow-up → outcomes**

For each meaningful pain point, capture frequency, time/cost, severity, existing workaround, willingness-to-pay signal, constraints, and the smallest plausible ORBIT intervention.

The resulting output should be a validated **V0 problem hypothesis**, not merely a feature wishlist.

### Decision discipline while research is underway

Two tracks may proceed in parallel:

**Track A — safe foundation work**
- infrastructure and engineering decisions that do not materially depend on the eventual V0 product wedge;
- security, testing, deployment, observability, API, persistence, integration, and other foundational concerns where appropriate.

**Track B — customer discovery**
- validate the recurring workflow;
- identify the highest-value pain;
- test whether the current Engineering Weekly Review wedge is correct;
- determine which existing assumptions should remain, change, or be removed.

Major V0 product decisions should wait for Track B when their correctness depends primarily on customer evidence. This is a **gate on product commitment, not a freeze on engineering progress**.

### Decision classification

Future proposals should distinguish, where useful:

- **Foundational:** durable ORBIT architecture/principles; generally safe to decide before customer discovery when independent of the product wedge.
- **Product:** user-facing workflow, scope, metrics, integrations, and value proposition; customer validation may be required.
- **Implementation:** concrete technology or delivery mechanics; decide when the relevant foundation/product semantics justify it.

No feature is considered permanent merely because it is implemented in V0.

### Customer-discovery gate: foundational vs product decisions

From this point forward, every significant proposed decision should be evaluated against the following distinction before work proceeds:

1. **Foundational decisions** — decisions about durable architecture, domain boundaries, security, persistence, integration seams, contracts, testing, deployment discipline, and other mechanisms that should remain useful across the eventual ORBIT trajectory. These may continue to be designed and locked before customer interviews when their correctness is not materially dependent on the V0 wedge.

2. **Product decisions** — decisions about what ORBIT should actually provide to users: workflows, screens, metrics, integrations, review scope, value proposition, personas, and other customer-facing product behavior. If the correctness of such a decision depends primarily on assumptions about customer pain or workflow, it should remain provisional or be deferred until direct customer evidence exists.

3. **Implementation decisions** — concrete technology and delivery choices. These may proceed when the relevant foundational and product semantics are sufficiently established, but implementation convenience must not be allowed to silently turn an unvalidated product hypothesis into a permanent product commitment.

### The balance rule

Customer research does **not** mean freezing the engineering roadmap. The operating rule is:

> **Customer research determines what ORBIT should build first; foundational architecture determines how ORBIT can evolve without being trapped by that first product.**

Therefore:

- Continue safe foundational and implementation work in parallel with customer discovery when that work is unlikely to constrain the eventual validated product wedge.
- Pause or explicitly mark provisional any major product decision whose answer should come from real customer evidence.
- Do not use the existence of a strong foundation as justification to keep expanding speculative product surface.
- Do not use the existence of an uncertain V0 wedge as justification to postpone foundational work that is genuinely wedge-independent.
- When a future capability is likely to **replace or remove** a V0 mechanism rather than merely extend it, treat removability as a first-class architectural consideration.
- Prefer clean seams and reversible boundaries over speculative implementation of future capabilities.

### V0 is allowed to evolve, simplify, replace, or disappear

V0 is a proof-of-concept and learning wedge, not a promise that every V0 capability becomes part of the eventual ORBIT product. A mechanism may be:

**added → changed → simplified → replaced → removed**

if customer evidence or broader system integration shows that the original mechanism is no longer the best solution. This includes temporary manual workarounds, V0-specific integrations, metrics, workflows, and UI surfaces.

The foundational architecture should therefore optimize for **evolution without premature generalization**: preserve durable concepts and clean boundaries, while avoiding the assumption that every current product detail deserves a permanent abstraction.


# 14G. CUSTOMER DISCOVERY & MARKET RESEARCH EVIDENCE — SEPTEMBER 2026

## Status
**WORKING RESEARCH RECORD — NOT A NEW LOCKED DECISION NUMBER**

This section records the first formal/structured discovery and deep-research signals obtained during the September 2026 customer-discovery phase. It is deliberately separated from locked product decisions. Research findings may inform future proposals, amendments, or product changes, but do not themselves change canonical decisions.

### Research integrity rule

Public research is advisory evidence. Vendor claims establish capabilities or positioning, not independently verified effectiveness. Customer anecdotes and interviews are evidence of the individual workflow described, not proof of market-wide prevalence. Hypothetical statements such as “I would use/pay for this” are weaker than observed behavior, measured time/cost, existing workaround, purchasing authority, or a paid pilot.

The September 2026 research pass used a current online-data review and explicitly identified unresolved claims requiring direct customer evidence or hands-on competitive testing.

## 14G.1 First adjacent-market informal discovery signal

A single informal conversation was conducted with a contact in an import/export trading company rather than an IT/software company. The conversation was opportunistic and not a structured Document B interview; it therefore does **not** count toward the formal 5–12 interview target or V0 falsification threshold.

Reported observations:

- The organization uses multiple SaaS systems, including Jira, SAP, Teams, and other financial/company systems.
- The organization provides Microsoft Copilot access; other teams reportedly use Claude Pro.
- The contact uses AI prompts against systems to retrieve information/metrics needed for meetings.
- Gathering, entering, validating, and preparing meeting material can still consume approximately a full workday.
- The contact estimated that AI output is often roughly 80–90% correct, but the remaining information must be manually checked; this figure is an individual estimate and is not treated as a measured statistic.
- The contact said that a system coordinating/organizing the information and preparing the meeting agenda would be valuable, and that even reducing preparation to roughly half a day would be a meaningful improvement.

### Interpretation

This is classified as a **weak adjacent-market signal** rather than formal customer evidence.

The encouraging part is the unprompted appearance of a similar pattern in a non-software organization with substantial SaaS usage and existing AI access. The signal suggests that fragmented SaaS systems and meeting-preparation work may extend beyond software companies.

The strongest useful evidence from the anecdote is the persistence of manual preparation and especially validation despite access to powerful AI. The hypothetical statement about desired automation and time savings is weaker evidence because it was given after discussing a product-like concept.

The conversation does **not** establish:

- that the person matches the V0 Engineering Manager / Delivery Manager persona;
- that the organization fits the current ICP;
- that Jira was being used for the exact workflow ORBIT targets rather than an internal technology function;
- that the reported time or accuracy figures are objectively measured;
- that the contact has purchasing authority;
- that non-software organizations systematically share this pain;
- that the market is large enough to support a business.

### Discovery implication

Continue to sample both software and selected non-software organizations, but keep the V0 wedge narrow until direct target-persona evidence justifies broadening it.

A useful non-software discovery stratum is organizations with a substantial digital-transformation, PMO, engineering/R&D, service-delivery, or operational-change function using Jira or similar workflow tooling while authoritative business state lives in ERP/CRM systems and communication/decisions live in Microsoft 365 or equivalent platforms.

## 14G.2 September 2026 deep-research conclusions

A current online-data research pass materially changed the competitive picture without overturning the locked architecture.

### Closest publicly visible long-term competitor: Rhythms.ai

Current public positioning indicates that Rhythms now markets recurring operating reviews with automatic pre-reads, risk surfacing, source-traceable numbers, connected work systems, decision logging, action carry-forward, and compounding context. It publicly lists connections including Jira, Linear, GitHub, Asana, Slack, Teams, and custom MCP integrations.

**Research conclusion:** Rhythms is no longer merely thematic competition. It is a direct product-category challenge, especially for program and executive reviews.

**Unresolved competitive questions:** whether Rhythms provides deterministic rule/calculation-level reproducibility, stable historical prepared state, typed separation of source facts vs interpretation/recommendation, equivalent organization-scoped authorization behavior, and sufficient effectiveness with real customer data.

### Microsoft Copilot / Facilitator

Current Microsoft documentation and announcements indicate credible before/during/after meeting lifecycle coverage, including agenda creation, meeting preparation, live notes, decisions, open questions, recap, tasks, and follow-up. Some task capabilities remain in public preview and some functionality has meeting/transcription/sensitivity-label constraints.

**Research conclusion:** The earlier framing of Copilot as merely a session-oriented summary assistant is obsolete.

ORBIT must not rely on generic meeting notes, agenda generation, recap, task extraction, or broad “AI memory” as durable differentiation.

### Atlassian Rovo

Current public material indicates Rovo now spans enterprise search, chat, specialized/custom agents, Jira-integrated workflows, cross-tool context, and actions within Jira. It can create/update work, draft status material, and summarize blockers/next steps.

**Research conclusion:** Rovo creates strong bundled-platform pressure for a Jira-first ORBIT product.

### Engineering-intelligence competitors

Jellyfish, LinearB, Swarmia, Bilanc, Cortex, DX, Athenian, Sleuth, Faros AI and adjacent vendors are increasingly moving beyond passive engineering dashboards toward AI analysis, executive narrative, workflow intervention, investment/capitalization analysis, developer experience, and cross-system context.

WorkBoard acquired Quantive on 28 May 2025, so they should be treated as one competitive organization rather than independent competitors.

Enji.ai emerged as a particularly relevant adjacent competitor because its public positioning combines project intelligence, cross-system context, meeting capture, executive reporting, financial information, and private/on-premise deployment.

### Real competitive unit

The most important incumbent competitor may be a **bundle**, not a single product:

> Jira/Rovo + Confluence + Teams/Copilot or Slack + Planner/Asana + an engineering-intelligence product + existing managerial process.

This bundle can be less coherent than ORBIT while still having lower procurement friction.

## 14G.3 Revised ORBIT differentiation hypothesis

The following should be treated as a **working differentiation hypothesis**, not a locked marketing claim:

> ORBIT's prospective distinction is a narrowly designed, temporally stable, deterministic operating-review workflow in which every material finding is reproducible, every decision is linked to evidence, and unresolved commitments persist explicitly across review periods.

The following are **not** considered durable differentiation by themselves because current incumbents increasingly provide them:

- AI summaries;
- automatic pre-reads;
- generic meeting notes;
- generic organizational memory;
- Jira dashboards;
- action-item extraction;
- natural-language querying;
- “connect your existing tools.”

The commercial value of the narrower distinction remains unvalidated.

## 14G.4 Reconciliation and trust as a core research hypothesis

A recurring question now deserves explicit treatment in discovery:

> Is the highest-value problem obtaining information, or determining which information is trustworthy enough to use for a decision?

The informal adjacent-market anecdote suggests that AI-assisted retrieval does not necessarily remove the human validation burden. Current research also indicates that competitive differentiation is moving away from retrieval and narrative toward durable workflow state and execution.

This does **not** establish reconciliation as the true V0 problem. Interviews must determine whether customers experience meaningful disagreement, staleness, missing context, identity mismatch, or conflicting source-of-truth behavior and whether resolving those issues is painful enough to pay to reduce.

## 14G.5 AI narration architecture — working research position

No new canonical decision is created here.

The current research supports the following implementation direction if narration later becomes justified by customer evidence:

- keep the model provider behind a replaceable adapter;
- use a curated structured fact packet rather than raw source records by default;
- give the narration layer the minimum necessary organization-scoped context;
- require stable support IDs for factual claims;
- prefer deterministic rendering or verification for material numbers, dates, entities, classifications, severity, and rule outcomes;
- treat semantic/LLM verification as a quality layer rather than proof;
- support explicit abstention when evidence is insufficient;
- preserve model/provider version, prompt-template version, fact-packet hash, claim-support links, verification outcome, timestamp, fallback route, and human approval state where narration is retained as a historical artifact;
- test prompt injection, stale data, conflicting facts, unsupported causal claims, malformed values, fake support identifiers, and other hostile inputs.

### AI cost research

Current API pricing research indicates that for small structured narration payloads, token cost is likely to be economically negligible compared with plausible B2B SaaS pricing. The principal early concerns are quality, privacy, contractual terms, data geography, reliability, verification, and model lifecycle rather than raw inference spend.

Self-hosting is therefore **not** justified for early ORBIT volume by token economics alone. More credible future triggers are customer-controlled deployment, regional/data-sovereignty requirements, prohibitions on third-party model processors, approved customer cloud capacity, fixed model artifacts, or sufficiently large predictable utilization.

### Open-weight model position

Do not train a foundation model for V0/V1. A capable API provider is the default experimental implementation path if narration is validated. Open-weight models remain a future option through managed or customer-hosted inference when evidence justifies them.

## 14G.6 Security/procurement research implications for future narration

S-033 already establishes customer organizational data as protected organization-scoped data and establishes explicit trust boundaries. If an external LLM receives customer data, that creates a concrete additional disclosure/subprocessor path that must be explicitly designed and documented before production use.

A minimum credible early-pilot trust package is expected to include, subject to actual customer requirements:

- security overview/whitepaper;
- architecture and data-flow diagram;
- Jira scopes and justification;
- data inventory/classification;
- retention/deletion policy;
- DPA template;
- subprocessor list;
- LLM data-use/retention statement;
- incident-response procedure/contact;
- encryption statement;
- tenant-isolation description;
- access-control/privileged-access process;
- backup/restore summary;
- secure-development/vulnerability-management outline;
- responsible disclosure channel;
- pilot offboarding/deletion procedure;
- certification roadmap stated conditionally rather than claimed prematurely.

Formal SOC 2/ISO certification timing remains a customer/procurement question rather than an assumed day-one universal requirement. Applicable privacy/security obligations cannot be postponed merely because certification has not been obtained.

## 14G.7 India GCC research signal

India-based GCCs are a potentially useful discovery segment because the sector is large and increasingly includes product ownership, R&D, transformation, AI/data, and enterprise-process responsibilities.

However:

> operational pain does not imply local purchasing authority.

A GCC leader may control the review process while Jira administration, OAuth approval, security, and procurement remain parent-controlled.

The most useful GCC discovery target is therefore:

> An India-based GCC that owns global product or delivery outcomes, has local innovation budget, and has previously approved departmental SaaS or read-only Jira pilots.

GCCs should remain a discovery sampling stratum rather than being declared the ICP from desk research.

## 14G.8 Pricing and business-model research signal

Current public pricing from adjacent engineering-intelligence vendors provides a market envelope but does not establish ORBIT's willingness to pay.

Observed public patterns include:

- contributor/developer pricing with annual minimums;
- modular developer pricing;
- quote-led enterprise contracts;
- platform tiers based on company size or scope.

A current ORBIT pricing hypothesis worth testing is:

> annual platform fee + included active reviewed teams + additional team bands + inexpensive/unlimited viewers, with enterprise hosting/security controls priced separately.

This remains provisional. Paid pilots and observed contracting behavior should determine the eventual model.

## 14G.9 Competitive validation experiment

Before treating the current differentiation hypothesis as commercially meaningful, run a structured hands-on benchmark using the same synthetic but realistic Jira project/data set across relevant products where feasible.

Score:

1. Can the system reproduce the exact review state as of a cutoff?
2. Can it explain a finding through rule, inputs, period, and calculation?
3. Does identical input produce identical finding output where determinism is expected?
4. Can a manager freeze prepared state?
5. Can a decision be linked to its evidence?
6. Can an unresolved commitment appear explicitly in the next review?
7. Does updating source data silently rewrite historical review meaning?
8. How are stale, missing, conflicting, or ambiguous inputs represented?
9. How much setup/configuration is required?
10. What procurement/security scope is introduced?

Initial comparison set should prioritize:

- Rhythms;
- Microsoft Copilot/Facilitator where applicable;
- Atlassian Rovo + Jira/Confluence;
- one or more engineering-intelligence vendors such as LinearB/Swarmia/Jellyfish;
- the current ORBIT design.

Preserve screenshots, outputs, dates, configuration, and observed limitations.

## 14G.10 Discovery sampling expansion

The next formal discovery cycle should not only seek more positive examples. It should deliberately test selection bias and persona assumptions.

Suggested sampling dimensions:

- 20–50, 50–150, 150–500, and 500+ employee organizations;
- Engineering Manager / Delivery Manager / Tech Lead / Scrum Master / Program or PMO leaders;
- organizations already using engineering-intelligence software;
- Microsoft-heavy and Atlassian-heavy environments;
- mature India GCCs with different procurement authority;
- non-software Jira users with substantial transformation/delivery functions;
- organizations using only dashboards/spreadsheets/manual reporting;
- at least some participants who do **not** consider recurring-review preparation a significant problem.

The interviews must remain neutral. Do not lead with “organizational memory,” “reconciliation engine,” “evidence layer,” or the current ORBIT differentiation hypothesis. Let the interviewee describe a recent workflow first.

## 14G.11 Narration proof experiment

If customer discovery later justifies narration, build an **offline evaluation before treating model quality as a product capability**.

Initial evaluation target:

- 50–100 realistic structured review packets;
- supported and deliberately unsupported claims;
- stale-data traps;
- causal traps;
- prompt injection;
- at least two lower-cost and two premium models;
- deterministic claim verification;
- measured human-edit rate;
- measured abstention/failure behavior.

The objective is not “best prose.” It is:

> **lowest total cost per narration that passes the ORBIT support/grounding contract.**

## 14G.12 Commercial validation experiment

The next commercial test should not rely on stated willingness to pay alone.

Recommended sequence:

1. Observe the workflow and baseline the real problem over 2–4 review cycles where possible.
2. Measure preparation, manual transformations, reconciliation time, meeting status-vs-decision time, follow-up administration, and correction/rework.
3. Run a fixed-scope paid pilot.
4. Test multiple price presentations, including active-team and platform-plus-team models.
5. Ask the prospect to identify the budget source, approver, procurement route, target start date, and conditions for renewal.
6. Measure adoption over consecutive reviews.

Useful success measures include:

- median preparation-time change;
- number of systems manually opened;
- number of manual transformations;
- time spent resolving discrepancies;
- decisions linked to evidence;
- commitments with owner/due date;
- carry-forward accuracy;
- correction rate;
- time spent fixing ORBIT output;
- continued usage across consecutive review cycles.

## 14G.13 What the research does NOT justify

The September 2026 research does **not** justify:

- broadening V0 to SAP, Teams, Slack, GitHub, or other systems;
- changing the primary V0 persona from Engineering Manager / Delivery Manager;
- declaring non-software companies a new ICP;
- declaring India GCCs the ICP;
- locking a price;
- making AI narration a critical V0 path;
- self-hosting an LLM;
- training a foundation model;
- creating a generic AI-agent platform;
- abandoning deterministic findings;
- replacing the modular monolith or current persistence architecture;
- creating S-034 or another decision placeholder.

## 14G.14 Current research verdict

**Architecture:** The deterministic factual core, explicit provenance, immutable review state, backend authority, modular monolith, PostgreSQL persistence, read-only Jira V0, and model-agnostic narration adapter remain coherent. No current research finding justifies overturning the locked architecture.

**Market:** The long-term category is becoming more crowded and more capable faster than earlier passes reflected. Rhythms, Microsoft, Atlassian, and engineering-intelligence vendors materially raise the competitive bar.

**Commercial:** The business case remains unvalidated. Public research establishes plausibility and competitive pressure, not sufficient demand.

**Current overall posture:**

> **CONTINUE AS A DISCIPLINED EXPERIMENT.**

Recent discovery broadens the long-term hypothesis without broadening V0: ORBIT may become a configurable organizational operating layer whose common core maintains permission-aware context, relationships, evidence, provenance, and temporal history while customer-specific workflows sit at the boundary. This remains a hypothesis, not a locked business-model decision.

The next existential question remains behavioral and commercial: whether a real manager repeatedly prefers an ORBIT workflow, whether the workflow is reusable across organizations with different operating models, and whether a buyer will pay for it.

The evidence required is direct workflow observation, manager review of real artifacts, comparative product testing where useful, repeated use, and eventually paid pilot behavior—not additional architecture speculation.


## 14G.15 GoGreen manager discovery — workflow semantics and operating-model variability

This section records direct manager evidence from the GoGreen Engineering Manager / Samyak discovery conversation. It is customer/workflow evidence, not a new locked product decision.

### Observed source evidence

The manager described the following operational meanings for the GoGreen Jira statuses:

- `Close` means work is finished/completed.
- `In Progress` means active development work.
- `Re-Open` means client review/feedback caused work to return to the developer; operationally it should be treated as active development/in progress.
- `Waiting for Additional Information` means the team is waiting for information and normally does nothing until it arrives. Although semantically blocked, the manager does not consider the waiting state itself an automatic attention trigger.
- `In Review` means initial development/fix work is complete and the client is testing on staging and providing feedback. It is an intermediate client-approval state, neither active development nor closed. It is normally brief and is not ordinarily something ORBIT should automatically flag merely because it exists.

Additional manager observations:

- Normal Jira priority order is Highest → High → Medium → Low.
- Explicit client requests can override the practical execution order without changing the Jira priority label.
- Client urgency can be communicated through comments, email, meetings, custom fields, verbal communication, or other channels.
- GoGreen is an internal WMS built specifically for clients; client direction often has the strongest practical influence on execution priority.
- The GoGreen Jira/process is relatively informal compared with other internal development projects at Tecblic.
- Other internal projects may be more structured, with the manager and CTO making final decisions on what gets done and when.
- The manager does not normally treat a long `In Review` duration as an automated finding; if it becomes problematic, the matter is discussed directly with the client.

### Critical interpretation

The evidence establishes an important distinction:

> **Source-state semantics are not the same thing as attention semantics.**

A source status can map to a conceptual state such as blocked or in-progress without implying that ORBIT should surface it as an attention item. Similarly, a Jira priority can be an authoritative source attribute without being a complete representation of real-world urgency.

This means ORBIT should avoid equating:

- `blocked` with `needs attention`; or
- source priority with organizational urgency.

The current deterministic engine must not be changed solely from this interview. Any new mapping or attention rule requires reconciliation with the existing canonical Jira contract and direct evidence.

### Project operating-model variability

The GoGreen interview also challenges the earlier assumption that projects within the same company can safely be treated as following approximately the same professional/standardized operating pattern. Current evidence supports only the narrower observation that **different projects within one organization may have materially different operating practices and source-system semantics**.

Emerging product hypothesis:

> ORBIT should be flexible enough to consume heterogeneous, imperfect organizational workflows without requiring users to manually normalize every source-system irregularity, while remaining structured enough that it does not merely institutionalize the organization's existing disorder.

Working principle for discovery purposes:

> **Flexible at the boundary, structured at the core.**

Meaning:

- tolerate source-system messiness and heterogeneous workflows;
- preserve source truth, uncertainty, provenance, and history;
- minimize manual normalization burden;
- provide structured management workflows around evidence, attention, decisions, commitments, and follow-through;
- do not assume source-system disorder should become ORBIT's canonical organizational model.

This is a **discovery hypothesis / working principle**, not a locked decision. It requires validation across multiple projects and organizations.

## 14G.16 GoGreen real-data projection learning

The first real GoGreen manual projection remains a technical/experimental milestone, not proof of manager value. The execution used a fresh Jira REST observation over a manager-approved frozen allowlist of 115 `Highest`-priority issues and achieved bounded two-pass consistency; the repository remained unchanged.

The projection surfaced substantial source/data-quality limitations, including widespread unmapped or incomplete conditions, absent due dates in the selected subset, and incomplete history for some records. These limitations are evidence about the source/project and experiment boundary, not automatically evidence of an ORBIT product defect.

A critical reconciliation lesson was recorded after observing zero prepared rule findings: the previously suggested hypothesis that `Highest → high` priority mapping was missing was **not supported** by the checked-in evidence. The canonical mapping explicitly maps `Highest` to the ORBIT `high` band. The more credible unresolved issue is status-vocabulary / mapping coverage and its interaction with attention semantics. No mapping or rule change should be made without direct forensic reconciliation against the actual run artifact and existing contract.

The manager-learning question remains separate from projection correctness:

> **A technically correct projection does not prove that a manager finds the resulting review useful.**

The next validation therefore requires actual manager review of the artifact, including unaided agenda selection, useful/missing/ignored/challenged items, corrections, decisions, commitments, and whether the artifact changes preparation or meeting behavior.

## 14G.17 Critical GoGreen manager-validated attention model — recurrence and client importance

The first direct manager review produced a high-value customer-learning result that is substantially stronger than agreement with an externally generated candidate analysis. Before relying on ORBIT's proposed agenda, Samyak independently described what he would select for the weekly review. He said he would pick tickets related to **billing, service contracts, and insurance** first because these areas are occurring repeatedly, are very important to the client, and the underlying problems **should not keep occurring**; closing these items first is therefore a practical management priority.

This is recorded as **customer-validated discovery evidence**, not a new locked product rule. The validation matters because it was expressed as the manager's unaided selection logic rather than as a reaction to a predetermined ORBIT finding.

### What this evidence supports

- **Jira priority is not sufficient to represent management priority.** A ticket can be `Highest` without being the most important discussion item, and a recurring issue in a client-critical domain can deserve attention because of its business context and recurrence.
- **Recurrence is a meaningful attention signal.** The manager cares not only that an individual item exists, but that the organization keeps encountering the same class of problem.
- **Client/business importance matters.** The reason these domains rise to the top is not merely their Jira metadata; it is their importance to the client and the expectation that the underlying problem should be resolved rather than repeatedly revisited.
- **Management attention is different from source-state semantics.** This reinforces the existing distinction between what a source system says about an item and whether that item represents something a manager should discuss now.
- **Finding ≠ issue.** A useful ORBIT attention item may ultimately need to represent a recurring problem/pattern across multiple issues rather than merely surface one Jira issue.

### Emerging product hypothesis

> **ORBIT should help managers reveal what keeps happening that should not keep happening.**

A broader hypothesis follows: **recurring activity in business-critical domains may be a stronger management-attention signal than the priority or status of an individual source item.** ORBIT should progressively help distinguish isolated execution work from recurring organizational problems that warrant discussion, intervention, and potentially a decision or commitment.

The intended causal chain remains:

> **evidence → attention → decision → commitment → verified follow-through**

For example, a recurring billing problem could eventually be represented as a pattern backed by multiple source items, brought into the review with evidence, turned into a manager decision or action, carried forward as a commitment, and checked in later reviews for whether recurrence declined. This is a future capability hypothesis, not authorization to change the current deterministic V0 rule catalog yet.

### Boundaries and validation required

This evidence is specific to the GoGreen manager and current organizational context. It does **not** justify hard-coding `billing`, `service contract`, or `insurance` as universal ORBIT categories. It also does not yet establish that recurrence alone is sufficient, that all recurring problems deserve attention, or that keyword matching is an adequate way to detect the underlying pattern.

Next validation should test: whether similar unaided attention logic appears across additional GoGreen review periods; whether another team/manager prioritizes recurrence and business-critical domains similarly; what evidence is sufficient for a manager to recognize a recurring problem; and whether ORBIT can surface these patterns without requiring users to manually tag every issue.

Most importantly, this finding should be kept separate from the earlier technical projection result: the **manager's usefulness/attention model is now producing positive customer evidence even though the first narrow deterministic Jira rules produced zero prepared findings**. Technical correctness and manager value remain separate dimensions.

## 14G.18 Additional informal adjacent-market interview — fragmented SaaS, appraisal evidence, retrieval, and organizational memory

A second informal interview was conducted with a friend working in an IT organization/division of an Australian multinational. The exact company identity was not confidently established and is intentionally not treated as a verified named customer/company reference. This was an informal conversation, not a structured formal interview, and does not by itself establish market prevalence or change the V0 falsification threshold.

Reported observations:

- The organization uses many SaaS tools and information is fragmented across multiple data sources.
- Meeting preparation can consume approximately half a day to a full day depending on meeting size.
- The contact considered meaningful reduction in this preparation burden useful.
- Employee appraisal preparation currently requires manually assembling evidence of work, including proof such as GitHub pull requests and Jira tickets, followed by manager review/approval.
- The contact saw potential value in ORBIT assembling evidence for appraisal preparation.
- The contact described a recent information-retrieval problem in which they knew an SQL query existed somewhere in organizational communication/storage but did not know where it was or who had sent it; they manually searched through Teams/chat history until finding it.
- The contact described a cross-division request for proof/overview of project work using Jira tickets and GitHub PRs after the relevant GitHub repository had already been closed by the Indian division. The inability to readily retrieve the PR links created a historical evidence/reconstruction problem.

### Interpretation

These examples suggest several potentially distinct workflows sharing a common underlying problem:

1. **Recurring meeting preparation:** assemble and reconcile evidence before a consequential review.
2. **Evidence-backed employee/appraisal preparation:** assemble a person's contribution history and supporting evidence for human review.
3. **Organizational retrieval:** find known-but-locationally-unknown information across fragmented systems.
4. **Historical reconstruction:** preserve or reconstruct evidence of work after an operational source has been closed, moved, or changed.

A possible common substrate is:

> **People + work + systems + relationships + time + evidence + provenance.**

This aligns with the long-term organizational operating/execution vision already present in S-001 and the existing relationship/provenance model. It does **not** justify expanding V0 into universal search, appraisal automation, or broad cross-system ingestion now.

### Important product boundary

The appraisal signal is currently interpreted as **evidence assembly for human appraisal**, not automated performance evaluation. ORBIT should not infer or autonomously decide employee performance from incomplete operational evidence without separate product, fairness, privacy, and governance validation.

The retrieval signal is similarly a hypothesis about a future organizational-context capability, not authorization to implement universal search in V0.

## 14G.19 Competitive discovery — Gitmore and the configurable-product hypothesis

### Gitmore

Fresh competitive research identified Gitmore as a live competitor/adjacent product whose positioning is materially relevant to ORBIT. Public positioning describes a Git-focused approach using GitHub/GitLab/Bitbucket rather than Jira, AI-generated narrative, and push delivery through channels such as Slack/email, aimed at engineering leadership reporting. This is treated as competitive positioning evidence, not independently verified customer-performance evidence.

The discovery has two implications:

1. The market does not appear to require one universal source boundary. A Git-only product can pursue substantially similar leadership-reporting pain without Jira. Therefore **Git + Jira should not be treated as a prerequisite for the broader ORBIT problem**.
2. AI-narrative-first is a recurring competitive pattern rather than a one-off. This strengthens the need to validate, rather than assume, whether ORBIT's deterministic/evidence-first sequencing creates customer value that outweighs the speed/convenience of AI-authored narrative.

A useful future validation experiment is a same-evidence comparison between an AI-written review narrative and an ORBIT-style deterministic/evidence-backed review artifact, asking managers which they would actually use in a consequential leadership review and measuring corrections, trust, comprehension, usefulness, and repeated use.

### Configurable enterprise solution hypothesis

Recent discovery also raised a strategic commercial/product hypothesis: ORBIT may ultimately be better positioned as a **configurable organizational operating layer** rather than a rigid SaaS workflow that requires every organization to conform to one predefined process.

The hypothesis is explicitly **not** “build anything a customer asks for.” That would risk turning ORBIT into bespoke software development with customer-specific code paths, no reusable product boundary, and increasing support/maintenance burden.

The stronger hypothesis is:

> **Productized core + customer-specific configuration + narrow initial workflow.**

Potential model:

- common ORBIT core: identity/permissions, sources, organizational objects, relationships, temporal history, evidence/provenance, deterministic signals, reviews, decisions, commitments, and audit/memory;
- customer-specific configuration: source mappings, terminology, review rhythms, evidence requirements, permissions, and selected workflow behavior;
- initial deployment: one narrow, high-value workflow;
- expansion: additional workflows on the same underlying organizational context once value is demonstrated.

This preserves the current V0 wedge while avoiding the assumption that the eventual ORBIT product must have one universal workflow. It is consistent with the existing working principle **“Flexible at the boundary, structured at the core.”**

### Current strategic interpretation

Do not replace the MVP/learning-wedge discipline with uncontrolled customization. Instead, treat the current V0 as a way to discover the **first repeatable ORBIT workflow** and use early customer-specific variation to identify which differences should become configuration, which should become reusable capabilities, and which should remain outside the product.

This is a **strategic hypothesis, not a locked business-model decision**. It requires validation across multiple organizations and paid pilot behavior.

## 14G.20 Updated discovery synthesis and next validation gate

The recent evidence strengthens several hypotheses without changing the locked architecture or V0 scope:

- recurring review preparation pain appears across more than one context, but prevalence and willingness to pay remain unvalidated;
- source-system semantics and operating practices can vary materially even within one organization;
- mapping semantics and attention semantics must remain distinct;
- Jira priority may not fully capture practical urgency;
- important organizational context can exist outside the primary system of record;
- meeting preparation, appraisal evidence, organizational retrieval, and historical reconstruction may be separate workflows over a shared organizational-context substrate;
- the competitive market includes both multi-source and source-specific products, and both deterministic/evidence-oriented and AI-narrative-first approaches;
- a configurable-product strategy is plausible, but uncontrolled custom development is not the intended model.

### Next validation gate

The immediate research priority is **direct behavioral validation**, not broad feature expansion:

1. complete the first real GoGreen manager review of the prepared artifact;
2. conduct additional unaided interviews, including at least one materially more structured engineering/delivery environment;
3. probe whether appraisal evidence, cross-system retrieval, and historical reconstruction recur across independent organizations;
4. observe which organizational differences are naturally configurable versus genuinely different product workflows;
5. use repeated reviews and, when warranted, a paid pilot to test whether ORBIT changes behavior and earns budget;
6. only then decide whether the first repeatable ORBIT workflow remains Engineering Weekly Review or should be narrowed/changed.

No new locked decision number is created by this section.


## 14G.21 GoGreen GitHub cross-system discovery — initial hypotheses

A read-only GitHub evidence extraction was performed against:
- `TecblicInternal/GoGreenDjango` (backend)
- `TecblicInternal/GoGreeen-React` (frontend)

The extraction covered the research window `2026-08-24` through `2026-09-15` UTC, with all 237 branches enumerated. The extraction itself completed without API errors and without modifying GitHub or the ORBIT repository. The evidence was captured outside the ORBIT repository and separately hashed.

### Confirmed source observations

- The GitHub default branch is not necessarily the authoritative operational branch. In GoGreenDjango, `main` was stale while `production`, `staging`, and `develop` represented different active environments/states.
- GoGreenDjango had a large and heterogeneous branch inventory, including stale, feature, bugfix, hotfix, workstream, scratch, backup, and ad-hoc branches.
- Current-period engineering activity was concentrated in the backend repository; no frontend PR/commit activity was observed in the selected research window.
- The backend contained recent PR/commit activity around billing, insurance, reservation logic, utilities, and related changes.
- Deterministic Jira↔GitHub references were sparse: only four Jira keys were explicitly observed in the extracted GitHub evidence (`GG-191`, `GG-239`, `GG-243`, `GG-251`).
- Jira keys were not observed in PR titles or PR bodies in the extracted sample; relationships appeared in branch names, commit messages, and timeline evidence.
- At least one merge commit explicitly referenced multiple Jira issues, demonstrating that one engineering change can correspond to multiple Jira work items.
- GitHub review metadata was sparse in the extracted sample.

### Working hypotheses — NOT LOCKED

1. **Engineering Weekly Review may require multiple operational evidence systems rather than Jira alone.**
   Jira can describe planned/workflow state while GitHub can provide implementation, integration, and execution evidence. This remains a product hypothesis requiring manager validation.

2. **Source truth should be discovered/configured rather than inferred from provider defaults.**
   A provider's default branch or nominal status cannot automatically be treated as the authoritative operational source. This appears foundational, but no amendment is locked from this observation yet.

3. **Cross-system relationships should not assume one Jira issue ↔ one GitHub PR.**
   The evidence includes a single merge commit referencing multiple Jira issues. A future ORBIT relationship model may need many-to-many links between organizational work items and engineering changes.

4. **Cross-system linkage cannot depend entirely on Jira-key naming conventions.**
   The extracted GoGreen sample had very limited explicit key traceability and no Jira keys in PR titles/bodies. ORBIT may require configurable or evidence-based relationship mechanisms, but no such mechanism is approved yet.

5. **Repository objects are not equivalent to active work.**
   Branch existence, branch age, or raw branch count should not be treated as evidence of unfinished or problematic engineering work. Activity, recency, lifecycle context, and relationships matter.

6. **Engineering execution evidence may expose a distinction between planned workflow progress and actual implementation progress.**
   GitHub can potentially show implementation, integration, merge, and review activity that is not fully represented by Jira state. This must be validated with real manager behavior before becoming a finding or rule.

7. **Repeated engineering activity around the same business/technical domain may be a management-relevant pattern.**
   GoGreen shows recurring recent engineering activity around billing/insurance/reservation areas, which aligns directionally with earlier manager discovery about recurring business-important issues. This is only a cross-source hypothesis; domain-specific rules are not authorized.

8. **Absence of evidence from one source is ambiguous.**
   Zero observed frontend activity in the research window should not be interpreted as proof that frontend work did not occur. ORBIT should distinguish “no activity observed in this source/window” from “no activity exists.”

9. **GitHub review metadata may not be sufficient on its own to define review-health findings.**
   The sample contained only one recorded review event across the extracted PR set. Whether this reflects workflow reality or source limitations remains unvalidated.

10. **The useful management unit may be larger than an individual Jira issue.**
    Cross-system evidence may reveal an engineering change, delivery thread, recurring problem, or domain pattern spanning multiple work items. This is a research hypothesis, not a domain-model decision.

### Research boundary

These observations do NOT authorize:
- a GitHub connector implementation;
- new GitHub-specific finding rules;
- a Jira↔GitHub one-to-one data model;
- a universal PR/review/staleness score;
- replacing Jira as the V0 source boundary;
- changing the locked V0 scope.

### Next validation gate

The next step is to reconstruct a small number of GoGreen cross-system cases from Jira + GitHub evidence and then validate whether a real manager actually uses the additional GitHub evidence in weekly review preparation, discussion, decisions, or follow-through. The same questions should subsequently be tested in TrueTenant before any V0 scope amendment is locked.

No new locked decision number is created by this section.

## 14G.22 Tecblic engineering-workflow discovery — organization-specific process variance and anti-overfitting principle

This section records the completed comparative GitHub discovery across the TecblicInternal `ActionEdge`, `EKFC`, and `Entitle` project families. It is research evidence about the observed organization/project environment, not a new ORBIT engineering decision.

### Comparative GitHub evidence

The deep scan covered 17 repositories, 229 branches, 406 pull requests, 2,127 analyzed commits, and 4 recorded GitHub review events. Pagination completed successfully and no GitHub API errors were reported.

The scan found the following recurring organization-specific signals across the three project families:

- No GitHub branch-protection rules were enabled in any of the 17 scanned repositories.
- Formal GitHub review records were rare; the majority of merged pull requests had no recorded GitHub review submission/approval.
- No active `.github/workflows` configurations were found in the scanned repositories.
- Significant branch residue/staleness was present; many historical branches remain remotely visible long after their latest activity.
- Multiple projects use non-`main` default branches or environment-specific branches that appear to reflect actual development/release activity more closely than the repository's nominal default.
- Contribution and merge activity is concentrated among a small number of maintainers in each family.

The GitHub evidence therefore supports the narrower conclusion that **the scanned Tecblic projects do not use GitHub itself as a complete or reliably enforced representation of code review, CI/CD, deployment, governance, or current engineering state**.

### Organization-context observation

Current user-provided organizational knowledge, combined with the GitHub evidence above, indicates that Tecblic engineering teams may rely on workflows outside these repositories for activities such as code review, deployment coordination, CI/test execution, and recording gaps or missing context. Excel-based tracking is one known organizational mechanism for recording gaps discovered during engineering/research work.

This should be treated carefully:

- GitHub cannot prove that code review never occurs; it can only show that formal GitHub review evidence is sparse or absent in the sampled projects.
- GitHub cannot prove that deployments never occur; the scanned repositories do not provide sufficient in-repository CI/CD/deployment evidence to reconstruct them.
- Excel usage is an observed company-specific workflow mechanism, not a universal engineering pattern.
- The absence of evidence in a source must not automatically be interpreted as evidence that the activity does not exist.

### Critical product-research interpretation

This discovery materially strengthens the principle that **every organization is not the same and ORBIT must not be designed around Tecblic's current engineering workflow as though it were a universal operating model**. Other organizations may use substantially more structured combinations of protected branches, mandatory reviews, CI/CD, automated testing, deployment telemetry, issue trackers, documentation systems, or other governance mechanisms.

Accordingly, ORBIT research and future architecture should distinguish between:

1. **Durable organizational concepts** — work, people, ownership, relationships, evidence, time, decisions, commitments, state, provenance, and verification.
2. **Source-system-specific representations** — Jira statuses, GitHub branches, PR reviews, CI checks, deployment records, spreadsheets, Slack/Teams messages, etc.
3. **Organization-specific operating practices** — how a particular company chooses to review, deploy, approve, reconcile, document, and manage work.

The third category must not be silently promoted into a universal ORBIT workflow.

### Anti-overfitting principle — working principle, NOT LOCKED

> **ORBIT must model durable organizational concepts while remaining adaptable to materially different operating practices, source semantics, governance mechanisms, and evidence availability across organizations.**

A customer's current process may be informal, highly structured, partially automated, spreadsheet-driven, or distributed across several systems. ORBIT should be able to consume and reason over the available evidence without requiring one company's process to become the product's canonical workflow.

At the same time, flexibility must not mean reproducing arbitrary customer disorder as product semantics. The existing working principle remains:

> **Flexible at the boundary, structured at the core.**

This is a discovery/architecture working principle and is **not a new locked decision**. It must be validated across independent organizations before it is treated as a product requirement.

### Important separation from ORBIT's own engineering standards

The Tecblic discovery does **not** amend ORBIT's locked engineering standards. In particular, observed absence of branch protection, formal review, or in-repository CI/CD in Tecblic projects must not be used as justification to weaken or reverse ORBIT's own S-030/S-031 engineering, deployment, testing, security, or observability decisions.

ORBIT is a product and engineering-system experiment conducted in the Tecblic environment; it is not required to reproduce Tecblic's engineering practices. The host organization's current workflow is a research environment, not the canonical design target for the product.

### Research implications

The next research phase should therefore prioritize **cross-organization validation**, not additional optimization for Tecblic-specific workflow quirks. In particular:

- compare at least one materially more structured engineering environment against the Tecblic examples;
- test whether the same durable concepts remain useful when review, CI/CD, deployment, and governance are represented differently;
- identify which differences are best handled through source adapters, configuration, evidence-confidence semantics, or genuinely different workflows;
- preserve explicit evidence gaps instead of inventing missing organizational context;
- avoid treating Excel, GitHub, Jira, branch names, or any other single tool as a universal organizational primitive.

No new locked decision number is created by this section.


## 14G.23 GoGreen Jira + GitHub cross-system projection — research-harness findings

### Status
**WORKING RESEARCH RECORD — NOT A NEW LOCKED DECISION NUMBER**

This section records the September 2026 GoGreen cross-system research package produced by the external Antigravity research harness/scripts. The package was created by running read-only Python/shell research commands against previously captured Jira/GitHub evidence and storing the resulting artifacts outside the ORBIT application/repository. It did **not** modify ORBIT product code, add a GitHub connector, or change the V0 implementation boundary.

### Research package and scope

- Jira snapshot: 317 issues, review cutoff `2026-09-12`.
- GitHub snapshot: `GoGreenDjango` + `GoGreeen-React`, including 237 branches, selected active-window PR/commit/timeline evidence.
- V0 comparison boundary: 115 manager-selected `Highest`-priority Jira issues for the relevant review period.
- Research period: `2026-09-07T00:00:00+05:30` → `2026-09-12T00:00:00+05:30` (Asia/Kolkata).
- Cross-system projection produced six candidate signals, with relationship and evidence-gap artifacts and validation checks.

### V0 Jira-only result

For the bounded V0 Jira projection over the selected manager boundary:

- zero automated findings were produced;
- due dates were absent in the inspected dataset;
- sprint information was not operationally useful for this projection;
- stalled-work detection was suppressed for five partial-history records.

This is a technical/result observation for the research period, not evidence that the broader workflow contains no management-relevant issues.

### Cross-system candidate signals — NOT VALIDATED AS MANAGER FINDINGS

The research harness surfaced six candidate signals:

1. `GG-191`, `GG-243`, and `GG-239` were associated with one billing fix represented by PR `#2151` / commit `e8b6def`.
2. `GG-321` was still `In Review` while PR `#2154` showed active insurance rework.
3. PR `#2150` contained a billing fix with no Jira key in the observed evidence.
4. PR `#2152` represented `develop` → `staging` promotion activity.
5. No frontend PR/commit activity was observed in the selected window.
6. The `production` branch showed no observed change in the selected window.

These are **candidate research signals**, not confirmed ORBIT findings and not evidence that the manager considered them important. The package explicitly recorded the manager comparison state as not yet available / not evaluated for the exact period, so these signals must not be represented as the result of a blind unaided manager review.

### Relationship findings

The package recorded six Jira↔GitHub relationships in total, of which four were explicit, one was assessed as strong, and one as weak within the available evidence.

The evidence reinforces several existing cross-system hypotheses:

- one engineering change can map to multiple Jira work items;
- Jira/GitHub linkage may exist in branch names, commit messages, or timeline evidence rather than PR titles/bodies;
- a change can exist without an explicit Jira key;
- source-state and implementation-state can diverge without either source being inherently wrong;
- cross-system evidence can expose a management-relevant thread larger than an individual Jira issue.

### Conflict and reconciliation observations

Three notable conflicts/relationships were recorded:

- **CONF-01:** `GG-321` was `In Review` in Jira while PR `#2154` showed active insurance rework. This remains unresolved without manager/context validation.
- **CONF-02:** `GG-239` was marked `Close` on August 31 while PR `#2151` activity appeared on September 11. This was reconciled as branch/implementation lag rather than an immediate contradiction in the sources.
- **CONF-03:** three Jira issues were associated with one GitHub engineering fix. This was treated as a one-to-many relationship rather than forcing a one-to-one mapping.

These cases strengthen the importance of temporal alignment and explicit provenance when combining operational systems.

### Source contribution and evidence gaps

The research package classified signal contribution as:

- Jira-only: 1;
- GitHub-only: 3;
- Jira + GitHub: 2;
- outside-context information required: 2.

Important unresolved evidence gaps included:

- actual production-server deployment/health telemetry;
- client verbal/email escalations;
- out-of-band code/design review evidence;
- client acceptance or testing evidence.

Therefore, ORBIT should not infer complete organizational state from Jira + GitHub alone when material context is known to exist elsewhere.

### Manager-behavior validation requirement

The critical experimental gap is now explicit:

> **We do not yet have a genuine blind comparison between (a) unaided manager attention, (b) Jira-only V0 output, and (c) Jira + GitHub cross-system projection for the same historical review period.**

The next validation step is to capture the real manager's unaided review for the exact period **before** revealing the cross-system signals, then classify each candidate as accepted, rejected, already known, useful-but-not-review-worthy, or missing context. This is the behavioral test of whether additional GitHub evidence actually improves the weekly review rather than merely producing technically interesting correlations.

### Research implications — NOT LOCKED

The combined Jira + GitHub experiment currently supports the following working hypotheses:

1. **Engineering Weekly Review may eventually benefit from multiple evidence systems**, but Jira remains the current V0 source boundary until manager value is demonstrated.
2. **Cross-system relationships should be temporal and evidence-backed**, not simple foreign-key assumptions between providers.
3. **Source truth, attention relevance, and implementation state are distinct concepts.** A Jira status or GitHub state should not automatically become a management finding.
4. **Candidate signals need explicit validation status.** ORBIT should distinguish observed evidence, inferred relationships, candidate signals, validated findings, and manager decisions.
5. **Evidence gaps are first-class research outputs.** Missing deployment, acceptance, or out-of-band workflow evidence should be represented as unknown rather than guessed.
6. **The useful management object may be a recurring problem, delivery thread, or engineering change spanning several work items.** This remains a hypothesis rather than a domain-model amendment.

### Boundary / non-authorization

This research does **not** authorize:

- implementing a GitHub connector;
- widening V0 beyond the locked Jira boundary;
- adding GitHub-specific deterministic finding rules;
- inventing a Jira↔GitHub one-to-one persistence model;
- treating repository inactivity as proof of no work;
- treating candidate cross-system signals as validated manager findings;
- changing S-001–S-033;
- creating S-034.

### Research posture

The correct posture is:

> **Validate the behavior before changing the product.**

The immediate next research target is the blind manager comparison for the same GoGreen period, followed by testing the resulting pattern in a materially different and more structured organization/workflow. Tecblic/GoGreen remains a research environment, not the canonical definition of how organizations operate.

No new locked decision number is created by this section.


## 14G.23 GoGreen deployment-process clarification and weekly engineering cadence — September 2026

This section records newly established organization/project context that clarifies several previously unresolved GitHub-discovery observations. It is **project/organization-specific research evidence**, not a new ORBIT engineering or product decision.

### Deployment and CI/CD clarification

The earlier GitHub scan showed no in-repository CI/CD workflows, no branch-protection rules, and no deployment telemetry. That absence is now partially explained by the observed GoGreen operating process:

- GoGreen deployment is performed manually.
- There is no dedicated QA assigned to the project.
- After changes are merged from `staging` to `production` on GitHub, the resulting code is manually deployed to the production server.
- Therefore, the GitHub repository itself is not expected to contain a conventional automated deployment runner/workflow for this project.

This resolves an important portion of the previous evidence gap. The correct interpretation is not that deployment does not occur; rather, **deployment occurs outside GitHub's automated workflow surface and is manually executed after production-branch promotion**.

The absence of GitHub Actions/workflows therefore provides evidence about the project's delivery mechanism, while remaining insufficient to generalize to all Tecblic projects or to other organizations.

### Dedicated QA and verification-process clarification

The lack of a dedicated QA role means verification responsibility is embedded in the engineering/project workflow rather than represented by a separate QA function in the repository evidence. This is an organization/project-specific process characteristic.

ORBIT must therefore avoid assuming that every organization's delivery workflow contains a separately identifiable QA actor, formal test stage, or machine-readable verification gate. At the same time, absence of a dedicated QA role must not be treated as evidence that no testing or validation occurs.

### Friday merge-surge clarification

The concentrated merge activity on **Friday, September 11, 2026** — including PRs `#2150`, `#2151`, `#2152`, and `#2153` — is now understood in the GoGreen context as a weekly operating-cadence effect:

- Friday is the last working day of the week for the team.
- Saturday and Sunday are non-working days.
- Changes were therefore consolidated/promoted before the weekend.

This provides a concrete temporal explanation for the observed burst of promotion/merge activity and is a useful reminder that **raw activity concentration should be interpreted in the context of organizational calendars and operating rhythms** rather than automatically treated as abnormal delivery behavior.

This strengthens the hypothesis that temporal context is necessary when interpreting engineering activity, but it does not authorize a universal rule such as “Friday merge spikes are healthy” or “weekday-end activity is always a release cadence.”

### Manager-attention priority clarification

The previously recorded hypothesis that practical management attention can differ from source-system priority is further corroborated by the current GoGreen project context. Recent engineering changes have been concentrated around:

- billing calculations;
- invoice-format changes; and
- invoice/business-logic changes.

These are consistent with the earlier observation that billing/service-contract/insurance work received manager attention because of recurrence and client/business importance rather than Jira priority alone.

The stronger interpretation is:

> **Management attention is influenced by the business consequences and recurrence of a problem/workstream, not merely by the priority label assigned in the source system.**

This remains a cross-context product hypothesis rather than a universal deterministic rule. The GoGreen evidence is corroborating project evidence, not independent external customer validation.

### Research interpretation

These clarifications improve the causal interpretation of the earlier GitHub findings:

- missing CI/CD workflow evidence has a known project-specific explanation;
- deployment is a real activity but is manually performed outside GitHub automation;
- the lack of dedicated QA is an organizational-process characteristic, not proof of absent verification;
- merge concentration can be explained by the team's working calendar and release cadence;
- business/domain importance can explain why certain engineering changes receive disproportionate management attention.

The resulting research principle is:

> **ORBIT should model organizational activity together with its temporal, process, and business context; raw source activity should not be interpreted in isolation.**

This remains a working research principle. It must be tested in materially different organizations/workflows before influencing foundational product semantics.

### Boundary / non-authorization

These findings do **not** authorize:

- changing ORBIT's locked CI/CD, deployment, testing, security, or observability decisions;
- assuming every customer performs manual deployment;
- assuming every customer lacks dedicated QA;
- encoding Friday/weekend behavior as a universal finding rule;
- treating billing/invoicing as a universal management-priority domain;
- widening V0 to GitHub or production telemetry;
- creating S-034.

No new locked decision number is created by this section.


## 14G.24 GoGreen verification and approval workflow clarification — September 2026

This section records newly established GoGreen project-context information about how verification, client acceptance, and production approval occur. It is **organization/project-specific research evidence**, not a new ORBIT engineering or product decision.

### No dedicated internal QA stage

The absence of a structured QA pass in Jira and the absence of formal review records in GitHub are now consistent with the known GoGreen operating model:

- the project does not have a dedicated QA role assigned to it;
- there is therefore no separate QA team/stage expected to leave a standardized Jira QA trail;
- formal code-review evidence is not part of the normal observed workflow in either Jira or GitHub;
- verification is instead embedded in the delivery process through staging and client acceptance.

This provides a stronger explanation for why the earlier Jira/GitHub research did not reveal a conventional QA state transition or formal reviewer trail.

### Client-led staging validation

The current GoGreen process is understood to work approximately as follows:

1. engineering changes are developed and promoted to `staging`;
2. the client performs the QA/acceptance validation on the staging server;
3. once the client approves the changes, the work is merged/promoted to `production`;
4. the production code is then manually deployed to the production server.

The approval itself is not necessarily represented as a structured Jira or GitHub event. Based on current organizational knowledge, client approval/feedback may be communicated through **Gmail, Microsoft Teams, WhatsApp, or verbal calls**, depending on the situation.

Because the exact communication channel is not consistently captured in the source systems, ORBIT research should treat this as **out-of-band approval evidence** rather than inventing a specific canonical approval source.

### Important distinction: verification exists without a dedicated QA artifact

The absence of a `QA Passed` status, formal review record, or automated CI gate does **not** mean that the GoGreen workflow lacks verification. It means that verification is performed through a different organizational mechanism:

> **engineering implementation → staging → client validation/approval → production promotion → manual deployment**

This is a useful example of why ORBIT must model **verification as a durable organizational concept** while allowing the representation of verification to vary by organization.

A structured organization might represent verification through automated test results, required reviews, QA sign-offs, deployment gates, or approval workflows. GoGreen instead relies substantially on staging validation and client acceptance, with some approval context existing outside Jira/GitHub.

### Resolution of earlier evidence gaps

This new context partially resolves three previously identified evidence gaps in the GoGreen cross-system research:

- **Out-of-band review/approval evidence:** approval can occur outside Jira/GitHub and may therefore be absent from those systems.
- **Client acceptance/testing evidence:** client validation occurs on staging, but the result may not be represented as a machine-readable Jira/GitHub event.
- **Deployment evidence:** production deployment occurs manually after production promotion rather than through an in-repository automated runner.

The evidence gap is therefore better described as **missing structured/source-visible representation of verification and approval**, rather than absence of verification itself.

### Research implication for ORBIT

This strengthens the working hypothesis that **evidence provenance must include evidence outside traditional engineering systems when that evidence materially determines organizational state**. Email, chat, calls, spreadsheets, approval messages, and other external artifacts may sometimes contain decisive context that Jira/GitHub alone cannot reconstruct.

However, this does **not** imply that ORBIT should ingest Gmail, Teams, WhatsApp, or call records into V0. It only establishes that the broader organizational-context model may eventually need to represent evidence whose authoritative source is outside the primary work-management or code-hosting system.

The research question remains:

> **Can ORBIT reliably represent and reason about verification, approval, and follow-through when the authoritative evidence is distributed across structured systems and informal communication channels?**

This must be tested across materially different organizations before becoming a product requirement or architectural amendment.

### Anti-overfitting boundary

The GoGreen workflow is one concrete example of an organization operating with informal/out-of-band verification. ORBIT must not assume:

- every organization lacks dedicated QA;
- every organization uses client-led staging validation;
- every organization approves production through email/chat/calls;
- every organization lacks formal code review;
- every organization deploys manually.

The durable concept is **verification/approval with provenance**, not the particular mechanism GoGreen uses to perform it.

No new locked decision number is created by this section.


## 14G.25 GoGreen manager validation and operating-rhythm discovery — September 2026

This section records the first completed behavioral validation of the GoGreen Jira + GitHub research projection, together with newly established context about the team's actual recurring operating rhythm. It is **research evidence, not a new ORBIT product or engineering decision**.

### Manager validation of the cross-system projection

The manager did not prepare a formal written weekly-review artifact for the Sep 7–12 period. The GoGreen team is small, the meeting was internal, and the manager did not need to prepare a presentation or pre-read for higher-level review. Therefore Track B is treated as an **oral retrospective / natural-language reconstruction of manager attention**, not as a missing document.

The manager's retrospective established that:

- the closed GitHub PRs were discussed during the meeting;
- an earlier PR from September 1 was also considered relevant because its branch was subsequently integrated into `develop` during the review period;
- the previously identified billing/invoicing engineering activity aligned closely with what the manager considered important;
- the cross-system Jira↔GitHub relationships identified by the research were substantively aligned with the manager's actual discussion;
- frontend inactivity was not treated as a discussion topic because no frontend work occurred in the period;
- the manager expected relatively few new GoGreen change requests/bugs in the following week and therefore expected the team to shift attention toward another project.

This provides behavioral support for the hypothesis that combining work-management and engineering-execution evidence can reconstruct topics that a manager actually considers relevant. It does **not** establish that every one of the six candidate signals should become an ORBIT finding or agenda item.

### Important temporal-boundary discovery

The manager's inclusion of a September 1 PR, despite the formal review window beginning September 7, is significant. The older PR was relevant because the associated branch became part of a meaningful engineering event during the review period.

This supports a working hypothesis:

> **Review relevance is not always identical to event timestamp. A historical engineering event can become newly relevant when a later merge, promotion, dependency, rework, release, or other lifecycle event occurs inside the current review context.**

Future ORBIT research should therefore distinguish, where justified:

- event time;
- source-observation time;
- integration/promotion time;
- review-relevance time.

No temporal model amendment is authorized by this finding alone.

### Billing/invoicing pattern corroboration

The manager's discussion and the detailed engineering reconstruction both point toward billing/invoicing as the dominant engineering concern during this period. The inspected commits include duplicate-billing prevention, contract-modification billing logic, dynamic invoice bank details, and billing-date/truncation corrections. The research therefore has corroborating project evidence that recent GoGreen engineering attention was concentrated around billing correctness and invoice behavior.

This remains **project-specific corroboration**, not a universal rule that billing domains deserve elevated management priority.

### Frontend inactivity interpretation

The lack of frontend discussion is consistent with the captured GitHub evidence showing no frontend PR/commit activity in the review period. The correct interpretation is limited to **no observed frontend repository activity in the captured window**; it is not evidence that frontend work could never have occurred outside the observed repository history.

### Manager attention is forward-looking, not purely retrospective

The manager's expectation that GoGreen would have relatively few new changes/bugs in the next week and that the team would focus on another project shows that the meeting is not purely a historical status review. It also serves as an **attention-allocation and next-focus discussion**.

This strengthens a working hypothesis:

> **Organizational operating rhythms may combine retrospective evidence review with forward-looking attention allocation and work-priority decisions.**

Whether this is a durable organizational pattern or a characteristic of small-team management remains to be tested outside GoGreen.

### GoGreen's actual recurring operating rhythm

New context establishes that GoGreen does **not** operate a formal weekly engineering review as its primary recurring management ceremony. Instead, the recurring day-to-day rhythm is substantially:

> **Start-of-day standup → discuss available/current work → decide task assignment → assign work in Jira → execute.**

The previously observed discussion of PRs, billing changes, staging state, and expected future workload occurs within a broader small-team coordination context rather than a standardized weekly review ceremony.

This is an important distinction between:

- **ORBIT's deliberately chosen V0 experiment:** Engineering Weekly Review; and
- **Tecblic/GoGreen's observed operating rhythm:** daily standup-driven work allocation with additional engineering/client coordination.

The difference does not invalidate the V0 experiment. It demonstrates why the host organization's current process must not be treated as the canonical ORBIT product model.

### New working hypothesis — operating rhythm is not necessarily meeting-centric

The evidence now supports a broader research question:

> **The durable ORBIT primitive may be organizational attention and execution management rather than a specific meeting cadence such as a weekly review.**

Possible recurring rhythms include daily standups, weekly reviews, delivery checkpoints, release readiness sessions, project triage, or other customer-specific operating practices.

This is **not** a proposal to replace Engineering Weekly Review in V0. It is a hypothesis for cross-organization research.

### Revised interpretation of the Shadow ORBIT experiment

The GoGreen experiment should now be regarded as having produced three distinct kinds of evidence:

1. **Technical evidence:** Jira-only data can be insufficient to surface engineering activity that is visible in GitHub.
2. **Behavioral evidence:** the manager's actual discussion substantially overlapped with the cross-system signals produced before the retrospective was captured.
3. **Organizational-process evidence:** the same organization may conduct meaningful management coordination without a formal weekly-review artifact, dedicated QA stage, formal code-review trail, or automated deployment pipeline.

The experiment therefore supports continued investigation of **evidence-backed organizational context**, while leaving the exact first repeatable workflow unresolved pending evidence from materially different environments.

### Research boundaries / non-authorization

These findings do **not** authorize:

- changing the locked V0 workflow;
- replacing Engineering Weekly Review with daily standups;
- treating daily standups as a universal operating rhythm;
- introducing a GitHub connector;
- adding automatic temporal-expansion rules based on this one example;
- treating billing/invoicing as a universal management-priority domain;
- treating frontend inactivity as a default management finding;
- treating client communication channels or manual process mechanisms as universal;
- creating S-034 or any other new locked decision.

The durable concepts to carry forward are **attention, work, relationships, time, evidence, provenance, verification, and execution state**, while the surrounding workflow remains organization-specific until independently validated.

No new locked decision number is created by this section.


## 14G.26 Cross-Context Validation #1 — EKFC and durable-concept synthesis — September 2026

### Status
**WORKING RESEARCH RECORD — NOT A NEW LOCKED DECISION NUMBER**

This section records the completed first cross-context validation experiment conducted against the TecblicInternal EKFC project family. The experiment was designed to test whether the deeper organizational concepts observed in GoGreen remain meaningful when the project domain, repository topology, management rhythm, verification mechanism, Jira/GitHub relationship, and deployment environment are materially different.

The EKFC research was performed as research-only work outside the ORBIT application/repository. It did not modify ORBIT product code, change the V0 boundary, or create a new locked decision.

### EKFC research boundary

- Target family: **EKFC (Emirates Flight Catering)**.
- Domain: industrial Computer Vision / IoT edge meal-tray inspection.
- Research window: `2026-06-15T00:00:00+05:30` → `2026-06-26T23:59:59+05:30` (10 working days).
- Repositories audited: 6.
- Branches analyzed: 17.
- Pull requests analyzed: 77; 7 fell within the selected research window.
- Commits in the selected window: 12.
- Jira issue keys found in GitHub artifacts: **0**.
- Candidate signals generated: 6.
- Human/manager validation: **not available**.
- Research comparison status: **complete as research validation**, with behavioral validation intentionally unavailable.

The research package was integrity-checked and stored outside the ORBIT repository. Its manifest records the generated research artifacts and SHA256 hashes.

### What was actually observed

The EKFC product family differs materially from GoGreen. It spans six repositories across two generations: a legacy Python prototype, Phase 1 frontend/backend repositories, and Phase 2 frontend/backend/Computer Vision model repositories. The active Phase 2 work includes React, NestJS, FastAPI, YOLOv8, and ByteTrack components. The delivery environment is an industrial edge system rather than a web SaaS application.

The reconstructed workflow is substantially different from GoGreen:

1. **Work intake:** requirements originate from airline catering requirements, meal specifications, and physical conveyor/camera constraints.
2. **Work prioritization:** functional progress is constrained by physical/model dependencies such as plate-detection accuracy and tracking stability.
3. **Task assignment:** work is strongly domain-segregated across AI/model, backend, frontend, and lead/reviewer responsibilities.
4. **Engineering execution:** local model training and video simulation coexist with feature-branch development and direct pushes.
5. **Code review:** governance differs by technology tier. The AI model repository has a two-person PR review/merge path; the Phase 2 backend and frontend have zero PRs and direct branch pushes.
6. **QA/testing:** verification includes video playback, physical test-line feeds, and temperature-safety threshold checks.
7. **Client validation:** validation is tied to the real catering/conveyor environment rather than conventional web staging.
8. **Staging:** the relevant pre-production environment is an edge/video or physical-camera simulation context.
9. **Approval:** GitHub does not provide enough evidence to reconstruct the full operational approval path.
10. **Production deployment:** deployment is manual to on-premise industrial line computers; no GitHub Actions workflow was present in the audited repositories.
11. **Post-release handling:** rapid patches address physical/operational edge cases such as misplaced alerts and meal-specific temperature rules.
12. **Management attention:** technical attention centers on model accuracy, conveyor-speed compatibility, synchronization, and integration rather than Jira burndown.

These workflow findings are source-derived and must not be generalized into universal customer behavior without further independent validation.

### Jira/GitHub decoupling finding

The strongest cross-context contrast with GoGreen is that EKFC contained **zero Jira issue-key references anywhere in the six GitHub repositories**: no keys in branch names, PR titles/bodies, or commit messages.

Therefore a cross-system engine that assumes Jira issue keys are the primary join key would effectively see no direct Jira↔Git delivery relationships, despite active engineering work occurring across multiple repositories.

The research package records the Jira/Git relationship as explicitly decoupled/unlinked. The actual management/task system behind that work was not established with sufficient evidence and remains unknown.

### Cross-system signals

Six candidate signals were identified:

1. **Plate classifier & tray tracking convergence** — multiple PRs combined YOLOv8 detection, ByteTrack persistence, and sector mapping into a core Phase 2 model milestone.
2. **Superseded/rapid re-authoring of unmerged model PRs** — several closed-unmerged PRs were followed by an optimized merged implementation, showing that closed-unmerged does not necessarily mean abandoned functionality.
3. **Backend authentication modernization** — refresh-token implementation in the Phase 2 backend.
4. **Multi-generational codebase forking** — Phase 1 repositories were effectively inactive while dedicated Phase 2 repositories absorbed active development.
5. **Bypassed PR governance in backend/frontend tiers** — those repositories had zero pull requests despite active development, contrasting with the AI model repository's review gate.
6. **Azure Service Bus telemetry preparation** — a dedicated branch indicated preparation for cloud telemetry integration.

These are research signals, not ORBIT findings and not manager-validated agenda items.

### Cross-context hypothesis evaluation

The EKFC experiment independently evaluated the ten GoGreen-derived hypotheses:

| Hypothesis | EKFC result | Interpretation |
|---|---|---|
| H1 — Important management context exists outside the primary system of record | **SUPPORTS** | GitHub had zero Jira keys and important domain/operational context was not reconstructable from GitHub/Jira alone. |
| H2 — Source-system status does not necessarily equal actual execution state | **SUPPORTS** | Closed/unmerged PRs could represent superseded iterations rather than abandoned work. |
| H3 — Source priority does not necessarily equal management attention | **NOT TESTABLE** | No Jira↔Git linkage existed, so the priority-to-execution comparison could not be performed. |
| H4 — A useful management unit can span multiple Jira issues / engineering changes | **SUPPORTS** | The functional milestone spanned multiple PRs, commits, repositories, and technical dependencies. |
| H5 — Engineering evidence can make earlier events relevant to current discussion | **SUPPORTS** | Earlier ByteTrack work became relevant to later plate-classifier integration. |
| H6 — Verification mechanisms vary by organization/domain | **SUPPORTS** | EKFC verification is built around physical/video conveyor environments rather than web staging. |
| H7 — Approval/validation may occur outside formal engineering systems | **SUPPORTS** | Operational deployment and acceptance were not reconstructable from GitHub; no formal universal approval trail was present in the inspected data. |
| H8 — Useful management attention may be forward-looking rather than historical-status-focused | **SUPPORTS** | Technical attention is driven by upcoming model/conveyor/integration requirements rather than ticket history alone. |
| H9 — Multiple evidence systems materially improve reconstruction | **MIXED** | Multiple sources add information, but absence of shared identifiers means semantic/temporal reconciliation is required. |
| H10 — A recurring weekly review is not a universal organizational primitive | **SUPPORTS** | EKFC is organized around milestone/model-convergence cycles rather than a standard weekly review cadence. |

### GoGreen vs EKFC — cross-context matrix

The following matrix records the current comparison without promoting the right-hand column to locked architecture:

| Dimension | GoGreen | EKFC | Current research interpretation |
|---|---|---|---|
| Business/runtime | Multi-client web WMS SaaS | Industrial Computer Vision / edge IoT | Delivery semantics are strongly shaped by the runtime and deployment environment. |
| Management rhythm | Daily standups with additional weekly/client-cycle context | Milestone and model-convergence cycles | A weekly review is not a universal organizational primitive. |
| Jira/Git traceability | Jira keys sometimes manually appear in Git | Zero Jira keys observed in GitHub | ORBIT cannot assume provider-key traceability. |
| Repository topology | Frontend + backend | Six repositories across two generations plus model tier | Repository shape varies substantially with architecture and product evolution. |
| Review governance | PRs primarily used as merge/integration vehicles; formal review sparse | AI model uses a two-person PR gate; backend/frontend direct-push pattern | Review/approval mechanisms can differ even within one project family. |
| Verification | Client validation on web staging | Video/physical conveyor validation | Verification is domain- and environment-dependent. |
| Deployment | Manual web-server deployment after promotion | Manual on-premise edge deployment | Deployment can exist entirely outside GitHub automation telemetry. |
| Cross-repo coordination | Jira keys/commit messages in some cases | API/WebSocket interfaces, shared models, contributor overlap, direct communication | Relationship evidence must support multiple correlation mechanisms. |
| Management attention | Billing/client-impact and near-term delivery focus | Model accuracy, conveyor compatibility, integration milestones | Management attention may be driven by operational consequences and next constraints rather than ticket counts. |

### Candidate durable concepts — not yet universal requirements

The two contexts together strengthen the following **candidate durable concepts**:

1. **Organizational execution has a runtime-dependent verification and deployment shape.** A web application and an industrial edge system cannot be assumed to share the same staging, QA, or deployment semantics.
2. **Source-system representations are not the organizational concepts themselves.** Jira status, GitHub PR state, branch names, and deployment records are representations of parts of a larger process.
3. **Shared identifiers are optional rather than guaranteed.** Cross-system context may require explicit keys, temporal correlation, semantic matching, relationship metadata, or other evidence-backed mechanisms.
4. **Source state, execution state, and management attention are distinct concepts.** A source status must not automatically become a management finding.
5. **Management context can extend across time.** A previous event can become relevant because of later integration, dependency, convergence, rework, promotion, or other lifecycle activity.
6. **The management unit may span multiple work items, repositories, or technical changes.** One Jira item is not necessarily the permanent unit of management attention.
7. **Verification is durable, but its mechanism is contextual.** Verification may be client-led, automated, physical, simulated, human-reviewed, or some combination.
8. **Human/out-of-band context can materially affect organizational state.** The absence of structured evidence does not establish that the activity or decision did not happen.
9. **Forward-looking attention is part of execution management.** Managers may use available evidence to decide what deserves attention next, not only reconstruct what already happened.
10. **Operating rhythm itself should remain a boundary-level concept.** Daily standups, weekly reviews, milestone gates, release checkpoints, and other rhythms should be treated as configurable/organization-specific until broader evidence supports stronger abstraction.

These concepts are stronger than the individual GoGreen or EKFC workflow details, but after only two project families inside one company they remain **candidate durable concepts**, not universal product requirements.

### What the combined research does and does not establish

The GoGreen and EKFC experiments now provide repeated cross-project evidence that:

- important organizational context can exist outside the primary system of record;
- Jira/GitHub traceability cannot be assumed;
- source status and actual execution can diverge in meaningful ways;
- management relevance can depend on lifecycle relationships and time, not simply event timestamps;
- verification and deployment semantics vary materially with the operating environment;
- management attention can be forward-looking and need not follow a fixed meeting cadence.

The evidence does **not** establish that these patterns are universal across organizations, nor does it establish which product workflow should replace or amend the current V0.

### Research boundary / non-authorization

This cross-context synthesis does **not** authorize:

- changing the locked V0 workflow;
- replacing Engineering Weekly Review with a daily or milestone-based workflow;
- implementing a GitHub connector;
- implementing universal Jira↔Git semantic correlation;
- implementing automatic temporal expansion of review windows;
- implementing Gmail/Teams/WhatsApp or other communication ingestion;
- implementing a generic organizational-attention engine;
- converting the candidate durable concepts above into locked domain rules;
- changing S-001–S-033;
- creating S-034.

### Next validation gate — External Validation #1

The next research phase should move **outside Tecblic**.

The objective is to test whether the candidate durable concepts survive an actually independent organizational environment rather than continuing to accumulate evidence from the host company.

The external experiment should:

1. reconstruct the organization's actual operating rhythm without assuming a weekly review;
2. map where work, ownership, execution, verification, approval, and deployment evidence actually live;
3. determine which system relationships are explicit and which require human/semantic reconstruction;
4. capture the manager/lead's natural account of what receives attention before exposing ORBIT-style candidate signals where possible;
5. compare the resulting behavior against the candidate concepts above;
6. classify each concept as **supported, contradicted, mixed, organization-specific, or unresolved**.

No product-scope amendment should be made solely from the GoGreen + EKFC pair.

No new locked decision number is created by this section.

# 15. CURRENT PROJECT STATE

## Locked decisions

S-001
S-003
S-004
S-005
S-006
S-007
S-008
S-009
S-010
S-011
S-012
S-013
S-013 Amendment A
S-014
S-015
S-016
S-017
S-018
S-019
S-020
S-021
S-022
S-023
S-024
S-025
S-026
S-027
S-028
S-029
S-030
S-031
S-032
S-033
S-034

## Working hypothesis

S-002 — ICP / market segmentation

## Decision-integrity checkpoint

S-034 is locked.

The next decision must first be checked against S-001–S-034 and must be genuinely new.

## Active research gate

**Cross-Context Validation #1 — EKFC: COMPLETE AS RESEARCH VALIDATION**

- GoGreen manager behavioral validation: completed for the bounded September 2026 case.
- EKFC human/manager validation: not available; research remains source-derived.
- Cross-context synthesis: complete at the candidate-concept level.
- **Next gate: External Validation #1 — independent organization.**
- No product or engineering implementation change is authorized by the completed internal cross-context research alone.

# 16. CURRENT ROADMAP TRACKER

## Product roadmap

[CURRENT / LOCKED] Stage 0 — Engineering Weekly Review
[DEFERRED] Stage 1 — Review Memory
[DEFERRED] Stage 2 — Cross-System Context
[DEFERRED] Stage 3 — Deterministic Exception / Blocker Resolution
[DEFERRED] Stage 4 — Cross-System Actions
[DEFERRED] Stage 5 — Multiple Operating Rhythms
[DEFERRED] Stage 6 — Organizational Context Layer
[DEFERRED] Stage 7 — Governed AI
[DEFERRED] Stage 8 — AI-Assisted Execution
[DEFERRED] Stage 9 — Governed Organizational Automation

## Engineering roadmap

[LOCKED] S-016 — v0 Persistence & Data Architecture
[LOCKED] S-017 — Concrete Persistence / Database Technology
[LOCKED] S-018 — v0 Application Architecture
[LOCKED] S-019 — v0 Technology Stack
[LOCKED] S-020 — Authentication & Authorization
[LOCKED] S-021 — Development Environment & Developer Workflow
[LOCKED] S-022 — v0 Jira Integration Implementation
[LOCKED] S-023 — Deterministic Metric & Snapshot Engine
[LOCKED] S-024 — Deterministic Finding Engine
[LOCKED] S-025 — Review Workspace & Frontend Architecture
[LOCKED] S-026 — API Contract & Application-Service Boundary
[LOCKED] S-027 — Django ORM, Domain Model & Persistence Implementation
[LOCKED] S-028 — Automated Testing Strategy
[LOCKED] S-029 — Frontend Architecture & Implementation Structure
[LOCKED] S-030 — CI/CD & Engineering Workflow
[LOCKED] S-031 — Deployment & Hosting Architecture
[LOCKED] S-032 — Observability & Operational Health Architecture
[LOCKED] S-033 — Application Security, Trust Boundaries & Threat Model

Likely later engineering areas:
- observability/SRE
- production security hardening
- scaling
- AI architecture

# 20. LATEST AMENDMENT / UPDATE HISTORY

## v36 context update — September 2026 EKFC cross-context validation and durable-concept synthesis

- Recorded the completed Cross-Context Validation #1 against the EKFC (Emirates Flight Catering) project family.
- Recorded the research boundary: 6 repositories, 17 branches, 77 analyzed PRs, 7 PRs in the selected 10-working-day window, 12 commits in-window, zero Jira issue keys found in GitHub artifacts, and 6 candidate signals.
- Recorded the materially different EKFC operating model: industrial Computer Vision/edge IoT runtime, milestone/model-convergence management rhythm, domain-specialized ownership, mixed PR/direct-push governance by technology tier, physical/video verification, and manual on-premise deployment.
- Recorded that Jira↔GitHub traceability was completely absent in the inspected EKFC GitHub artifacts, demonstrating that provider-key linkage cannot be assumed as a universal organizational primitive.
- Recorded the six EKFC candidate signals and three major source-level ambiguities/conflicts, without converting them into product findings.
- Recorded the ten-hypothesis evaluation: H1, H2, H4, H5, H6, H7, H8, and H10 supported; H3 not testable because Jira/Git linkage was absent; H9 mixed because multiple systems add information but require semantic/temporal reconciliation.
- Recorded that no unaided EKFC manager validation was available; therefore EKFC results remain source-derived research evidence rather than behavioral validation.
- Added a GoGreen-vs-EKFC cross-context matrix separating organization/project-specific practices from candidate durable concepts.
- Strengthened the candidate durable concepts around runtime-dependent execution, source-vs-organizational semantics, non-guaranteed cross-system identifiers, separation of source/execution/attention state, temporal relevance, multi-item management units, contextual verification, out-of-band evidence, forward-looking attention, and non-universal operating cadence.
- Explicitly classified these concepts as candidate durable concepts rather than universal product requirements because both validating contexts are still within Tecblic.
- Marked the internal cross-context synthesis complete and moved the next research gate to **External Validation #1** with an independent organization.
- Added an active research-gate status to the current project state; no V0 or engineering roadmap change was made.
- No new locked decision number was created; S-001–S-033 remain canonical and unchanged.

## v35 context update — September 2026 GoGreen manager validation and operating-rhythm discovery

- Recorded the completed behavioral validation of the GoGreen Jira + GitHub projection from an oral manager retrospective rather than a formal review artifact, reflecting the small internal team context.
- Recorded that the manager discussed the closed GitHub PRs and that an earlier September 1 PR was considered relevant because its associated branch was integrated into `develop` during the review period.
- Recorded substantial alignment between the previously generated cross-system signals and the manager's actual discussion, while preserving the distinction between behavioral validation and automatic promotion of every candidate signal into a product finding.
- Recorded that frontend inactivity was not a management discussion topic because no frontend work occurred in the captured period, reinforcing that source-observable activity is not automatically agenda-worthy.
- Recorded the manager's forward-looking expectation of fewer GoGreen changes/bugs in the following week and planned attention toward another project, strengthening the hypothesis that recurring management coordination includes attention allocation as well as retrospective review.
- Recorded the temporal-boundary discovery that review relevance can extend beyond a fixed event-time window when a historical artifact becomes relevant through later merge, integration, promotion, rework, dependency, or other lifecycle events.
- Recorded corroborating project evidence that recent GoGreen engineering activity is concentrated around billing calculations and invoice behavior, while explicitly avoiding a universal billing-priority rule.
- Recorded the newly established fact that GoGreen does not use a formal weekly engineering review as its primary recurring management ceremony; its recurring day-to-day rhythm is substantially start-of-day standup → task discussion → assignment → Jira assignment → execution.
- Distinguished the ORBIT V0 experimental workflow (Engineering Weekly Review) from the observed GoGreen operating rhythm and reinforced that the host organization's process is a research environment, not the canonical ORBIT product model.
- Added the working hypothesis that organizational operating rhythms may be meeting-centric, daily, event-driven, or otherwise varied, and that the durable ORBIT primitive may be organizational attention/execution management rather than one universal meeting cadence.
- Preserved the research posture that V0 remains unchanged until evidence from materially different environments establishes whether the first repeatable workflow should remain Engineering Weekly Review or evolve.
- No new locked decision number was created; S-001–S-033 remain canonical and unchanged.


## v34 context update — September 2026 GoGreen verification, client-acceptance, and out-of-band approval clarification

- Recorded that GoGreen has no dedicated QA role assigned to the project and therefore should not be expected to produce a conventional standalone QA trail in Jira.
- Recorded that formal code-review evidence is absent from the normal observed Jira/GitHub workflow, while verification still occurs through staging and client acceptance.
- Clarified the GoGreen delivery sequence as engineering → staging → client validation/approval → production promotion → manual production deployment.
- Recorded that client approval/feedback may occur through Gmail, Microsoft Teams, WhatsApp, or verbal calls and may therefore be absent from Jira/GitHub as structured events.
- Reclassified the relevant research gap from “no verification/acceptance” to “verification/acceptance exists but is not consistently represented in the inspected source systems.”
- Strengthened the durable ORBIT hypothesis that verification/approval should be modeled independently from the mechanism used to perform it and should preserve provenance when evidence exists outside the primary source systems.
- Explicitly preserved the anti-overfitting boundary: GoGreen's informal/client-led process must not become a universal ORBIT workflow assumption.
- No new locked decision number was created; S-001–S-033 remain canonical and unchanged.



## v33 context update — September 2026 GoGreen deployment-process, cadence, and manager-attention clarification

- Recorded the newly established GoGreen project context that deployment is manual: after `staging` is merged to `production` on GitHub, the code is manually deployed to the production server.
- Recorded that the project has no dedicated QA role, and classified this as an organization/project-specific process characteristic rather than evidence that no testing or validation occurs.
- Clarified the prior GitHub evidence gap: the absence of GitHub Actions/workflows is now partially explained by the project's manual deployment process and therefore should not be interpreted as proof that deployment does not happen.
- Recorded the Friday, September 11, 2026 merge concentration (`#2150`, `#2151`, `#2152`, `#2153`) as a weekly cadence effect because Friday is the team's last working day before a Saturday/Sunday non-working period.
- Strengthened the research principle that engineering activity must be interpreted with temporal/process context rather than from raw activity counts alone.
- Recorded additional GoGreen corroboration that recent engineering changes have concentrated around billing calculations and invoice-format/business-logic changes.
- Reinforced the working hypothesis that management attention is influenced by recurrence and business/client impact rather than source-system priority alone.
- Explicitly classified this GoGreen corroboration as project/company evidence, not independent external customer validation, and preserved the requirement for cross-organization validation.
- Reinforced the distinction between organization-specific operating practices and ORBIT's own locked engineering standards.
- No new locked decision number was created; S-001–S-033 remain canonical and unchanged.

## v32 context update — September 2026 GoGreen Jira + GitHub cross-system research-harness findings

- Recorded the completed Antigravity-generated cross-system research package combining the bounded GoGreen Jira snapshot with GoGreen GitHub evidence, explicitly separated from ORBIT application code and from locked product decisions.
- Recorded the bounded V0 Jira-only result for the selected period: 0 automated findings, absent due-date data, non-operational sprint data, and stalled-work suppression on five partial-history records.
- Recorded six cross-system candidate signals spanning Jira/GitHub relationships, implementation-state divergence, promotion activity, frontend inactivity in the observed window, and production-branch inactivity.
- Recorded six Jira↔GitHub relationships (four explicit, one strong, one weak) and the three principal conflict/reconciliation cases, including the one-to-many relationship between multiple Jira items and a single engineering change.
- Recorded source-contribution and evidence-gap results showing that some potentially useful signals are GitHub-only and that deployment telemetry, client escalation/acceptance, and out-of-band review evidence remain outside the captured systems.
- Explicitly corrected the methodological interpretation: the package does **not** contain a blind unaided manager comparison for the same period. Candidate signals and “manager relevance” fields must therefore not be treated as manager-validated findings.
- Established the next validation gate as a blind manager comparison for the exact review period, followed by cross-organization validation before any V0 scope or connector decision.
- Reinforced the distinction between source-state, implementation-state, attention relevance, inferred relationships, validated findings, and manager decisions.
- Reinforced that evidence gaps are first-class research outputs and that absence of evidence in one source must not be treated as proof of absence.
- No new locked decision number was created; S-001–S-033 remain canonical and unchanged.

## v31 context update — September 2026 GitHub comparative discovery and anti-overfitting clarification

- Recorded the completed deep GitHub scan across ActionEdge, EKFC, and Entitle: 17 repositories, 229 branches, 406 PRs, 2,127 analyzed commits, 4 recorded GitHub review events, complete pagination, and 0 API errors.
- Recorded cross-project evidence that the scanned Tecblic repositories do not use GitHub itself as a complete/enforced representation of code review, CI/CD, deployment, governance, or current engineering state.
- Recorded that formal GitHub review records were rare, branch protection was absent across the scanned set, and no active `.github/workflows` configurations were found in the scanned repositories.
- Recorded significant branch staleness/residue and concentration of contribution/merge activity among a small number of maintainers.
- Recorded the important distinction between “GitHub does not show evidence” and “the organization does not perform the activity”; informal/out-of-band review, external CI/CD, external deployment mechanisms, and other processes remain possible where GitHub evidence is insufficient.
- Recorded current company-specific knowledge that Excel is used to track discovered gaps / missing context; explicitly classified this as an organization-specific workflow mechanism rather than a universal engineering pattern.
- Strengthened the discovery principle that organizations may follow materially different engineering operating models, even within the same general software category, and that ORBIT must not overfit to Tecblic’s current practices.
- Added the working principle: **ORBIT must model durable organizational concepts while remaining adaptable to materially different operating practices, source semantics, governance mechanisms, and evidence availability across organizations.**
- Reinforced **“Flexible at the boundary, structured at the core”** as a non-locked working principle.
- Explicitly separated host-company practices from ORBIT’s own engineering standards: Tecblic’s observed workflow does not amend S-030/S-031 or justify weakening ORBIT’s protected-mainline, review, CI/CD, deployment, security, testing, or observability standards.
- Changed the immediate research emphasis from further Tecblic-specific repository archaeology toward cross-organization validation and identification of durable, organization-agnostic concepts.
- No new locked decision number was created; S-001–S-033 remain canonical and unchanged.

## v29 context update — September 2026 manager-validation discovery

- Recorded the first direct, unaided GoGreen manager validation of ORBIT's emerging attention model: Samyak independently prioritized recurring billing, service-contract, and insurance-related problems because they are client-important and should not keep recurring.
- Elevated recurrence + client/business importance as a major **customer-validated discovery hypothesis** for management attention, while explicitly avoiding universal hard-coded domain rules.
- Recorded the emerging product hypothesis **“ORBIT should help managers reveal what keeps happening that should not keep happening.”** and connected it to the existing evidence → attention → decision → commitment → verified follow-through chain.
- Reinforced the distinction between source-system priority/status and real management attention, and between individual issues and recurring problem patterns.
- Preserved the boundary that no current deterministic V0 rule, schema, or connector implementation is changed by this discovery alone; additional review periods and different managers/projects must validate generality and detection method.

## v28 context update — September 2026 discovery consolidation

- Consolidated the completed Shadow ORBIT milestone state, including M0, 1A, 1B, 1C, real Jira 2A inspection, and the first bounded GoGreen manual projection as experiment history rather than new product decisions.
- Added direct GoGreen manager discovery covering project-specific Jira status semantics, client-driven urgency, the distinction between source-state semantics and attention semantics, and materially different operating styles across projects.
- Recorded the working discovery principle **“Flexible at the boundary, structured at the core”** as a hypothesis rather than a new locked decision.
- Recorded the GoGreen projection reconciliation lesson that `Highest → high` is already an approved/direct mapping; the zero-finding outcome must not be attributed to a missing priority mapping without forensic run-artifact evidence.
- Preserved the distinction between technical projection correctness and manager usefulness; the first real manager review remains the critical behavioral validation step.
- Added a second informal adjacent-market interview covering fragmented SaaS, meeting-preparation time, appraisal evidence assembly, cross-system retrieval, and historical project-evidence reconstruction.
- Connected these observations to potential future workflows—appraisal evidence, organizational retrieval, and historical reconstruction—without widening V0 or authorizing universal search/appraisal automation.
- Added Gitmore as a competitive discovery signal showing that source-specific (Git-only) and AI-narrative-first approaches are live market variants; removed any implication that Jira+Git is universally required.
- Added a configurable-enterprise-solution hypothesis: productized common core + customer-specific configuration + narrow initial workflow, explicitly distinguished from uncontrolled bespoke development.
- Updated the immediate validation gate toward real manager behavior, contrasting organizational operating models, repeated workflow use, and eventual paid-pilot evidence.
- No new locked decision number was created; S-001–S-033 remain canonical and unchanged.

## v27 context update — September 2026 discovery and deep-research pass

- Added a dedicated customer-discovery and market-research evidence section without creating a new locked decision.
- Recorded one informal import/export-company conversation as a weak adjacent-market signal only; explicitly excluded it from the formal 5–12 interview/falsification threshold.
- Recorded the recurring pattern observed in that anecdote: multi-SaaS environment, existing AI access, substantial meeting preparation, human validation burden, and interest in organized review preparation.
- Recorded the current research finding that Rhythms.ai is a direct long-term category competitor with public claims spanning pre-reads, risk surfacing, source traceability, decisions, action carry-forward, and compounding context.
- Recorded Microsoft Copilot/Facilitator and Atlassian Rovo as increasingly credible before/during/after workflow and platform competitors.
- Recorded WorkBoard’s acquisition of Quantive and the expanded AI capabilities of engineering-intelligence competitors.
- Reframed prospective ORBIT differentiation away from generic AI summaries/meeting notes/memory and toward reproducible, evidence-backed, temporally stable review state with explicit decision and commitment continuity.
- Recorded reconciliation/trust as an important hypothesis requiring direct customer validation rather than treating it as the proven V0 problem.
- Recorded a working AI narration architecture: model-agnostic adapter, minimum structured context, claim-level support IDs, deterministic verification, abstention, provenance, and adversarial testing.
- Recorded current research indicating that API narration cost is unlikely to be a material early gross-margin risk and that self-hosting/training is not justified pre-pilot.
- Recorded the need to treat external LLM narration as an explicit trust-boundary/data-disclosure path when it becomes a real product capability.
- Added lightweight pilot procurement/trust-package guidance without claiming SOC 2/ISO certification prematurely.
- Added India GCCs as a discovery sampling stratum rather than declaring them the ICP.
- Added a proposed hands-on competitive workflow benchmark across Rhythms, Microsoft/Copilot, Rovo/Jira/Confluence, selected engineering-intelligence products, and ORBIT.
- Added paid-pilot and offline narration-evaluation experiments as future validation mechanisms.
- Confirmed that this research does not justify widening V0, changing the current architecture, or creating S-034.
- Current research posture: **CONTINUE AS A DISCIPLINED EXPERIMENT**.

## S-034 — Jira + GitHub Cross-System Evidence Direction — LOCKED

**STATUS: LOCKED**
**TYPE: Product / Foundational boundary**

### Locked decision

Jira + GitHub is now a locked ORBIT cross-system direction. Future ORBIT validation and product evolution should treat the combination of Jira and GitHub evidence as an intentional part of the evidence model rather than as an exploratory integration that may be discarded solely because the first proving corpus is Jira-only.

This does **not** mean every customer must use Jira + GitHub, nor does it authorize arbitrary cross-system inference. The existing EvidenceBundle, provenance, explicit-vs-declared-link, temporal/state separation, anti-inference, and customer-validation boundaries remain authoritative.

### Parallel Track A / Track B operating model

ORBIT deliberately runs two tracks simultaneously:

- **Track A — Engineering robustness:** continue hardening deterministic evidence handling, provenance, validation, cross-system semantics, test coverage, safety, and architectural boundaries against real public corpora.
- **Track B — Customer discovery:** simultaneously test whether engineering managers actually value the resulting evidence, which workflows matter, what should become a V0 product capability, and what customers would pay for.

This parallelism is intentional. ORBIT should not build a product surface in the absence of evidence that somebody wants it, but customer discovery must not unnecessarily stop foundational engineering work that is unlikely to be invalidated by customer evidence.

### Current proving corpus and future corpus strategy

- **Mahout is the current proving project/corpus.** The existing qualification boundary remains the frozen Mahout corpus: 2,121 source documents → 400 primary + 12 structural dependencies → 412 selected; 412 accepted; 0 quarantined; 12 `STALLED_WORK`; 56 incomplete; 370 missing due dates; 0 Jira mutations; repeatable qualification.
- Mahout is **not** intended to be the only proving corpus. Once the engine's current contracts are stable, ORBIT should test against additional useful public datasets/projects containing both Jira and GitHub evidence (or a Jira corpus plus independently collected public GitHub history) to test whether the semantics generalize beyond one project.
- The purpose of additional corpora is engineering robustness and empirical generalization, not cherry-picking projects that make ORBIT look successful.

### Public Jira Dataset research context

The current research identifies `JiraReposAnon.Apache` as one collection inside **The Public Jira Dataset** (Montgomery, Lüders & Maalej, MSR 2022, Zenodo, CC BY 4.0), rather than a standalone Mahout-only dataset. The research notes that the dataset covers **16 public Jira repositories, 1,822 projects, and approximately 2.7 million issues**, with Apache containing **657 distinct sub-projects**. The other top-level repositories identified in the current research are:

- Hyperledger
- IntelDAOS
- JFrog
- Jira
- JiraEcosystem
- MariaDB
- Mindville
- Mojang
- MongoDB
- Qt
- RedHat
- Sakai
- SecondLife
- Sonatype
- Spring

This means additional Jira projects can be selected through different project filters within the existing downloaded corpus rather than requiring a new dataset acquisition, credentialing flow, or MongoDB installation.

### Dataset caveat

The current research also establishes an important limitation: this public dataset is **Jira-only**. It does not provide a bundled GitHub history for the same projects. Therefore Jira + GitHub validation requires separately sourced public GitHub history and correlation through whatever traceability evidence the project actually exposes.

The existing ORBIT `github_mentions.py` / GitHub evidence path should therefore be treated as a normal research-harness approach, not as a temporary workaround. The current research references comparable academic traceability work that similarly correlates independently collected GitHub history with Jira keys in commits.

### Candidate expansion corpus

The current research identifies the following candidate projects, in the stated priority grouping:

**Tier 1 — Apache collection, zero new dataset acquisition cost:**
- Kafka (`KAFKA-1234`)
- Camel (`CAMEL-1234`)
- Spark (`SPARK-1234`)
- Flink (`FLINK-1234`)
- Cassandra
- Airflow
- Groovy
- Giraph

These are identified as substantially more active than Mahout and therefore potentially useful for stressing volume, relationship density, and traceability handling. The current research also notes existing academic traceability work for Flink, Groovy, and Giraph.

**Tier 2 — other top-level repositories already present in the same MongoDB dump:**
- MongoDB (`SERVER-XXXX`)
- MariaDB (`MDEV-XXXX`)
- Qt (`QTBUG-XXXX`)

The current research describes these as useful organizational/convention contrasts, while explicitly retaining a caveat that the present research has not independently confirmed that each project's Jira-GitHub linkage convention remains active today.

**Tier 3 — outside the current dataset:**
The current research identifies projects such as Maven and Keycloak, among others, as later candidates if ORBIT eventually needs corpora beyond the existing Public Jira Dataset. These are intentionally not the immediate expansion path because they lose the existing corpus's zero-acquisition-cost advantage.

### Current research direction

The immediate research direction identified by the current work is to evaluate a higher-volume Apache project such as **Kafka or Camel** after the current Mahout proving boundary is sufficiently established. The selection is an engineering-test choice, not a product-success claim or an assertion that one project is universally superior.

### Relationship to customer discovery

Locking Jira + GitHub as an evidence direction does **not** remove the Customer Discovery & V0 Decision Gate. Track A asks whether the engine is technically robust and semantically defensible across real corpora; Track B asks whether managers actually use and value the resulting evidence. Both must progress together before customer-facing scope is treated as validated.

### Non-inference requirements preserved

S-034 does not permit:
- assuming one Jira issue maps to exactly one GitHub PR or commit;
- treating a Jira key mention as an explicit/native relationship unless the source schema establishes one;
- inferring actor identity or responsibility from cross-system activity;
- inferring completion, lateness, fault, productivity, or organizational health from GitHub/Jira state alone;
- treating absence of GitHub evidence as proof that work did not happen;
- replacing provenance or EvidenceBundle validation with direct raw-fixture pairing.

The existing Pass 4 cross-system architecture and its conservative evidence taxonomy remain the implementation boundary.

## S-033 locked

- Locked the system-wide, threat-model-driven application security architecture as a foundational decision composed from S-015, S-020, S-026, S-027, S-030, S-031, and S-032.
- Established Organization/tenant isolation as a security invariant, with server-side authorization authoritative across API, object, background-job, and resource boundaries.
- Established explicit trust boundaries and worker security properties: system actor, organization scope, no ambient authority, and no authority derivation from untrusted task parameters.
- Established that external provider data is untrusted until validated, normalized, and mapped; normal Jira operations remain worker-driven and API-to-Jira access is limited to credential validation.
- Simplified V0 Jira outbound-network security by accepting a Jira site identifier rather than an administrator-supplied arbitrary base URL and constructing the approved Jira Cloud destination internally.
- Added explicit V0 authentication rate limiting / brute-force protection and corresponding security-test coverage.
- Established protection of Finding→Evidence provenance and immutable/historical records as security-sensitive assets, with violations blocked and observable.
- Established sensitive-data classification, secret-safe telemetry, browser/session/CSRF requirements, dependency/build hygiene, and explicit V0 security invariants.
- Added a threat-model artifact structure and acceptance criteria covering tenant isolation, authorization, worker scope, credential non-exposure, hostile external input, browser security, outbound safety, history integrity, logging, and supply-chain hygiene.
- Explicitly deferred enterprise SSO/SCIM/IAM, customer-managed keys/HSM, full SIEM/DLP, formal certification programs, service mesh/Kubernetes network policy, multi-region security architecture, and dedicated SecOps machinery.

## S-032 locked

- Locked provider-neutral layered observability distinguishing system/application health, data/domain health, and user impact.
- Added `evaluation_id` as a distinct correlation identifier for every Finding evaluation attempt, independent of trigger.
- Reserved `IMMUTABLE_HISTORY_VIOLATION` as a first-class, non-routinely-suppressible error category.
- Clarified local telemetry isolation when real sandbox integrations are exercised.
- Preserved the S-031 deployment refinements: controlled worker restart for credential replacement, Task Backend inside canonical PostgreSQL, Web/API/Worker as one built artifact with different entrypoints, separate staging/CI Jira sandboxes, and future-compatible hosting-region selection.

## S-030 locked

- Established protected mainline development with pull-request-based collaboration and mandatory CI/code review.
- Selected a single repository for frontend/backend source while preserving independent deployment as a future possibility.
- Defined PR-blocking, broader integration, and scheduled external Jira sandbox test tiers.
- Moved real Jira sandbox validation off the PR-critical path and onto scheduled/nightly execution.
- Added automated OpenAPI-to-frontend generated-type drift detection.
- Replaced unreliable migration-source pattern matching with accumulated-history database-state checksum verification for immutable/historical tables.
- Made old-code/new-schema compatibility testing executable using the previous release tag and the current migration set.
- Established expand/contract migration discipline for deployment windows.
- Added explicit CI enforcement coverage for S-020 command authorization, query scope filtering, and system-actor permissions.
- Preserved S-021 fixture-first development, S-022 sandbox isolation, S-027 historical migration governance, and S-028 layered testing strategy.
- Deferred hosting, deployment platform, observability, infrastructure-as-code, E2E framework, Kubernetes/GitOps, and advanced deployment strategies to later decisions.

## S-031 locked

- Locked the production deployment model as Next.js Web + Django API + background Worker within the modular-monolith architecture.
- Scoped the API-to-Jira path to S-015 credential validation only; normal Jira data operations remain worker-driven.
- Established that Web/API/Worker use one built application artifact with different runtime entrypoints rather than independently built application images.
- Explicitly placed the v0 database-backed task backend inside the canonical PostgreSQL instance rather than as a separate queue service.
- Defined controlled worker restart as the v0 mechanism for propagating activated credential replacements to running workers.
- Required separate ORBIT-owned Jira sandboxes for staging and scheduled/nightly CI validation.
- Required a real worker liveness/health signal without mandating an HTTP endpoint.
- Preserved managed infrastructure, isolated environments, controlled migrations, automated backups, stateless application runtime, and least-privileged production access.
- Added a hosting-region requirement that preserves future data-residency options without prematurely locking a provider or compliance architecture.
- Deferred exact hosting provider, Kubernetes, multi-region, autoscaling, advanced traffic management, formal SLO/SLA, and detailed SRE implementation.

## v23 context update

- Formalized the decision-making balance established after customer-discovery planning: continue durable foundational/implementation work while gating customer-dependent product decisions on direct evidence.
- Explicitly classified future proposals as **Foundational**, **Product**, or **Implementation**, with customer validation required where product correctness depends on real user evidence.
- Established the principle: **customer research determines what ORBIT should build first; foundational architecture determines how ORBIT can evolve without being trapped by that first product.**
- Clarified that a strong existing foundation is not a reason to continue speculative product-surface work while customer discovery is incomplete.
- Elevated **removability** alongside extensibility: V0 mechanisms may be added, changed, simplified, replaced, or removed when broader cross-system capabilities or customer evidence make them unnecessary.
- Clarified that foundational architecture should be future-compatible, not future-complete: preserve durable seams and boundaries without prematurely implementing the full ORBIT vision.

## v22 context update

- Added the formal **Customer Discovery & V0 Decision Gate** as an active working principle rather than a new numbered decision.
- Clarified that ORBIT's foundational architecture should remain compatible with the eventual full-scale platform vision, while V0 product scope remains a provisional learning wedge.
- Explicitly established that V0 capabilities may be added, changed, simplified, replaced, or removed; extensibility includes the ability to remove obsolete mechanisms once broader cross-system capabilities make them unnecessary.
- Established that customer discovery should run in parallel with safe foundational/implementation work rather than freezing the roadmap.
- Established that major unvalidated V0 product-scope decisions should be provisional or deferred until direct customer evidence exists.
- Added the Foundational / Product / Implementation classification to future decision-making.
- Corrected the stale S-029 checkpoint so S-030 is consistently recorded as the latest locked decision.

## v21 context update

- Added the explicit **foundational architecture vs v0 feature scope** principle.
- Clarified that v0 is a narrow proof-of-concept wedge while foundational domain and architectural boundaries should remain compatible with the eventual full-scale ORBIT product.
- Clarified that v0-specific mechanisms, including any future manually entered engineering-adjacent metrics, are not assumed to survive into the eventual Operating Rhythm product; later cross-system capabilities may replace or remove them.
- Preserved S-030 as the latest locked decision before S-031 was explicitly locked; this update now records S-031 as the latest locked decision.

## v37 context update — September 2026 Pass 4 consolidation and locked Jira + GitHub direction

- Updated the canonical context version from v36 to **v37**.
- Locked **S-034 — Jira + GitHub Cross-System Evidence Direction** as the latest decision. Jira + GitHub is now a canonical direction for ORBIT's cross-system evidence model and future validation strategy.
- Recorded the operating model that **Track A (engineering robustness)** and **Track B (customer discovery)** proceed simultaneously. Track A validates deterministic/provenance-safe engineering foundations while Track B validates whether the resulting management workflow is actually wanted and valuable.
- Recorded that **Mahout remains the current proving corpus**, while additional public corpora/projects are required to test generalization and volume handling.
- Recorded the current Public Jira Dataset research context: `JiraReposAnon.Apache` is one collection within the MSR 2022 Public Jira Dataset, with the broader dataset described as covering 16 top-level public Jira repositories, 1,822 projects, and approximately 2.7 million issues.
- Recorded the other 15 top-level repositories identified in the current research: Hyperledger, IntelDAOS, JFrog, Jira, JiraEcosystem, MariaDB, Mindville, Mojang, MongoDB, Qt, RedHat, Sakai, SecondLife, Sonatype, and Spring.
- Recorded the key caveat that the current public dataset is **Jira-only** and that GitHub evidence must be separately sourced and correlated.
- Recorded candidate expansion projects: Apache Tier 1 candidates Kafka, Camel, Spark, Flink, Cassandra, Airflow, Groovy, and Giraph; Tier 2 candidates MongoDB, MariaDB, and Qt; later outside-dataset candidates including Maven and Keycloak.
- Recorded the current research direction to consider Kafka or Camel as higher-volume Apache proving projects after the current Mahout proving boundary, without treating that choice as a product ranking or success prediction.
- Preserved the existing Pass 4 implementation boundary: Wave 1 provenance dereferencing; Wave 2 EvidenceBundle validation; Wave 3 cross-system fusion and state/temporal alignment; Wave 5 Track B evaluator implementing XB-01, XB-02, and observational XB-03; XB-04 through XB-08 remain deferred/prohibited.
- Recorded Pass 4 consolidation completion: technical implementation/test consolidation in `5a9e32d`, documentation/ADR archival in `e867258`, with the working tree clean after push.
- Preserved the final Pass 4 verification state: 711 collected, 699 passed, 12 skipped, 0 failed, 3 warnings; Mahout 412 accepted, 12 `STALLED_WORK`, 0 quarantined, 0 mutations, repeatable qualification; Track A frozen.
- Preserved the qualification that `FROZEN_ENGINE_COMMIT=6d82d12` is the historical governing Mahout baseline and must remain distinct from the runtime/consolidation commits.
- Preserved the qualification that `ReadOnlyJiraGuard` is a harness-level mutation guard within the offline proving boundary, not a universal live HTTP interception mechanism.
- Preserved the remaining pytest deprecation warnings and MongoDB-dependent skipped qualification tests as known, documented qualifications rather than silently treating them as resolved.

## Process governance

Whenever a decision is locked, the following are mandatory lock-finalization actions:

1. Update the top-of-file **Latest locked decision** banner.
2. Update the locked decision register.
3. Update the decision-integrity checkpoint.
4. Update the current engineering roadmap status.
5. Add the decision to the amendment/update history.
6. Verify that no stale earlier-decision banner or duplicated decision section remains.

These are mechanical completion steps, not optional documentation cleanup.


# v37 context update — 30 September 2026 — Phase 3A/3B cross-system qualification and current engine state

### Status
**WORKING RESEARCH / ENGINEERING STATE RECORD — NOT A NEW LOCKED DECISION NUMBER**

This update records the controlled cross-system qualification work completed after the previous canonical context revision. It updates the factual state of the ORBIT deterministic evidence engine, the evidence boundary established by the Phase 3 experiments, and the immediate engineering/research sequence. It does **not** create S-034, widen V0, authorize a universal connector architecture, or change the locked architectural decisions S-001–S-033.

## 1. Current ORBIT engineering state

The ORBIT deterministic evidence engine has now progressed materially beyond the original Jira-only proving boundary.

The current protected engineering baseline remains:

- Repository: `/home/tecblic/orbit`
- Protected `develop` / governing semantic baseline: `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)
- Current controlled-hardening/consolidation HEAD: `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`
- Current branch: `remediation/pass3-controlled-hardening`
- Working tree at the end of Phase 3B: clean
- ORBIT semantic-engine modifications during Phase 3A/3B: **0 bytes**
- Phase 3A/3B were research/qualification experiments, not product-feature implementation.

The semantic core now has an exercised canonical evidence path spanning:

`source observations → canonical state models → evidence relationships → CrossSystemStateAlignment → EvidenceBundle → deterministic Track B evaluation → provenance dereference`

The principal canonical models used in the cross-system qualification are `WorkItemState`, `CodeChangeState`, `CrossSystemStateAlignment`, and `EvidenceBundle`. Provider-specific identity is kept at the boundary; the evaluator does not treat Jira, GitHub, or PR-number vocabulary as universal domain primitives.

The governing engineering invariants remain unchanged:

- deterministic facts first;
- evidence before confidence;
- unknown != false;
- missing != complete;
- unmapped != normal;
- invalid != absent;
- quarantined != accepted;
- unsupported inference != deterministic fact;
- provenance must remain dereferenceable;
- temporal proximity must not be converted into causality;
- lexical declaration must not be silently promoted into explicit linkage;
- source-system state differences must not automatically become contradictions.

## 2. Phase 3A — Controlled Corroborating-Evidence Acquisition

Phase 3A is **PASS — CONTROLLED EVIDENCE ACQUISITION COMPLETE**.

A frozen population-derived cohort of 100 Jira→GitHub candidate relationships was selected from the Phase 2 population using deterministic project-stratified sampling with seed `42`. The frozen cohort manifest SHA-256 is:

`3aa4ebabefa84e95dd433d20ba82c852cce4a1bfe7a4f246bb9c01873f077775`

Allocation:

| Project | Frozen candidates | Eligible population |
|---|---:|---:|
| PARQUET | 7 | 102 |
| KAFKA | 26 | 370 |
| AVRO | 6 | 78 |
| FLINK | 56 | 779 |
| ZOOKEEPER | 5 | 74 |
| **Total** | **100** | **1,403** |

One AVRO candidate was excluded from the new cohort because `AVRO-3234 ↔ apache/avro#1370` had already been acquired and qualified in Phase 1A.

Acquisition results:

- 98/100 candidates acquired successfully (98.0%).
- 2/100 remained `NOT_FOUND` because historical incubation-mirror PRs returned HTTP 404:
  - `PARQUET-171 ↔ apache/incubator-parquet-mr#107`
  - `PARQUET-88 ↔ apache/incubator-parquet-mr#53`
- 0 access-denied outcomes.
- 0 rate-limit outcomes.
- 0 API/network errors.
- No substitution, synthetic reconstruction, or web replacement was performed for the two missing historical PRs.
- 288 raw artifacts were captured and hashed: 96 PR metadata files, 96 commit files, and 96 review files.
- Raw artifact hash manifest: `qualification/wave3/phase3a_acquisition/hashes/raw_sha256.json`.

Identity qualification was deterministic:

- PR number matched the requested candidate in 98/98 acquired records.
- Base-repository identity matched directly in 97/98.
- The single exception was `FLINK-1359`, where the requested historical `apache/incubator-flink#254` reference redirected to `apache/flink#254`; the redirect preserved repository/PR identity continuity.

Phase 3A therefore established a cryptographically frozen, authentic corroborating-evidence cohort suitable for semantic qualification without modifying the engine.

## 3. Phase 3B — Controlled Semantic Qualification

Phase 3B is **PASS WITH QUALIFICATIONS — CONTROLLED SEMANTIC QUALIFICATION COMPLETE**.

The experiment was offline/read-only. The Phase 3A cohort and all 288 raw artifacts were revalidated before evaluation:

- cohort expected SHA == actual SHA: `3aa4ebabefa84e95dd433d20ba82c852cce4a1bfe7a4f246bb9c01873f077775`;
- 288/288 raw artifact hashes recomputed successfully;
- 0 missing artifacts;
- 0 hash mismatches;
- 100% raw-artifact integrity.

All 100 frozen candidates were reconciled without changing their acquisition outcome. The canonical projection contained:

- 100 Jira observations;
- 96 unique GitHub observations, because two PRs were legitimately shared by multiple Jira issues;
- 196 unique observations in total;
- 98 EvidenceRelationship records;
- 98 CrossSystemStateAlignment records;
- 0 canonical validation issues after identity deduplication;
- 196/196 provenance references resolved through the existing provenance taxonomy.

### Linkage semantics

The engine deliberately retained all 98 acquired relationships as `DECLARED_MENTION`. None were promoted to `EXPLICIT_LINK` merely because Jira keys appeared in PR titles, commits, or other text. Native Jira remote-link data was not present in the anonymous Mongo dump used for the population survey.

This establishes a critical boundary:

> **A Jira description containing a GitHub PR URL is source evidence of a declared relationship, not universal ground truth of semantic linkage.**

Universal cross-system precision/recall remains unsupported until independent ground truth and/or sufficiently complete native relationship evidence are available.

### Repository identity and cardinality

The canonical model correctly preserves repository-scoped PR identity. Numeric PR identifiers are never treated as globally unique.

The cohort exercised legitimate many-to-one relationships:

- `KAFKA-12770` + `KAFKA-12771` → `apache/kafka#10656`;
- `FLINK-126` + `FLINK-236` → `stratosphere/stratosphere#126`.

Each Jira issue retains an independent alignment to the single canonical PR observation. One-to-many relationships were already exercised in Phase 1A, including `FLINK-24409 → #17401/#17773/#17799`.

Historical predecessor repositories and external dependencies were preserved as authentic repository identities rather than normalized away. Approximately 23% of the cohort involved historical incubation/predecessor or external repositories; this is now a confirmed architectural consideration, not yet an authorization to implement an alias/dependency taxonomy.

### State alignment

The cohort produced:

- `CONSISTENT`: 30 (30.6%);
- `INSUFFICIENT_EVIDENCE`: 68 (69.4%);
- `CONFLICTING`: 0.

The large insufficient-evidence population is an intentional result of conservative semantics, not a failure condition. In particular, 62 closed-but-unmerged PRs were not converted into false contradictions.

The evaluator surfaced one important lifecycle case: `KAFKA-12770` remained open/Patch Available/in-progress while `apache/kafka#10656` had merged. This was recognized through existing Track B semantics without introducing a new rule.

### Temporal alignment

The cohort produced:

- `COHERENT`: 30 (30.6%);
- `INDETERMINATE`: 66 (67.3%);
- `INVERTED`: 2 (2.0%).

The two inverted cases were genuine source-time relationships detected by existing semantics:

- `FLINK-13730 ↔ apache/flink#7605`: PR merged `2019-11-15T19:57:31Z`, Jira resolution `2019-08-15T10:04:02Z`, approximately +92 days;
- `FLINK-20650 ↔ docker-library/official-images#9249`: PR merged `2021-01-28T20:45:19Z`, Jira resolution `2020-12-23T09:25:10Z`, approximately +36 days.

These generated the existing `ORBIT-XB-03` temporal condition. The engine did not infer causality from timestamp proximity, and it did not conflate `merged_at` with `committed_at`.

### Provenance

All 196 canonical provenance references resolved successfully:

- `RESOLVED`: 196;
- `NOT_FOUND`: 0;
- `ACCESS_DENIED`: 0;
- `UNAVAILABLE`: 0;
- `MALFORMED_LOCATOR`: 0;
- `UNSUPPORTED_LOCATOR`: 0;
- `STALE`: 0;
- `AMBIGUOUS`: 0;
- `INVALID`: 0.

This is a qualification of the existing provenance mechanism, not evidence that all future live-provider data will always be resolvable.

### Negative controls

The existing negative controls remained clean, including `PARQUET-1812`, `ZOOKEEPER-4348`, `parquet-java#3822`, and the Snyk/CVE-like `AXIOS-12613773` control. No spurious cross-system relationship was produced. A bot/template-style Jira-key mimic was rejected by the Apache Jira-key validator.

### Manual adjudication

A blinded 28-item manual sample produced 27/28 agreement (96.4%) with the evaluator. This is **adjudication agreement**, not independently established accuracy. The single disagreement was `FLINK-13730`; the human classified the state as consistent because both records were closed/merged, while the evaluator remained conservative because the PR merged approximately 92 days after Jira resolution.

### Determinism and regression

Phase 3B was deterministic across repeated and permuted evaluation:

- Run 1 bundle digest: `504b2f03d86090cfb2e617d911b3bc58b292e9dbba068f230da37197b0a701df`;
- Run 2 bundle digest: identical;
- Run 1 evaluation digest: `7fc973824bd228b8cf5b2cbfe665d95d430c5e3170e28fcf52243d4c3a2688ca`;
- Run 2 evaluation digest: identical;
- permuted Run 3 evaluation digest: identical;
- permutation invariance: true.

Full regression remained green at 817 passed / 0 failed. The protected Track A baseline produced zero diff. Mahout remained 412 accepted, 0 quarantined, 12 STALLED_WORK, 56 non-terminal period-end incomplete, 370 missing due dates, repeatable, with 0 Jira mutations. TrueTenant remained 112 accepted, 0 quarantined, 33 unknown/indeterminate canonical categories, 1 STALLED_WORK, deterministic. Apache Phase 1A/1B/1C qualification invariants remained unchanged.

## 4. What is now genuinely proven

The current evidence supports the following as **PROVEN** within the stated experimental boundaries:

1. Population-derived authentic GitHub evidence can be projected into the existing canonical `CodeChangeState`/evidence model without loss of relevant PR, commit, and review metadata.
2. Repository-scoped identity prevents PR-number collisions across repositories and preserves historical repository redirects.
3. One-to-many and many-to-one Jira↔GitHub cardinalities can be represented without collapsing distinct relationships.
4. Conservative state alignment correctly preserves `INSUFFICIENT_EVIDENCE` instead of manufacturing contradictions from incomplete lifecycle information.
5. Temporal semantics detect genuine post-resolution merges without treating temporal proximity as causality.
6. Existing Track B evaluation can surface real cross-system lifecycle conditions on authentic corroborating evidence.
7. Existing provenance dereferencing resolved all canonical references in the Phase 3B cohort.
8. Determinism and permutation invariance hold for the qualified experiment.
9. The Phase 3 cross-system proving sequence did not regress the protected Jira-only deterministic engine.

The following remains **SUPPORTED BUT NOT INDEPENDENTLY PROVEN**:

- Jira-embedded GitHub URLs appear to represent meaningful developer-declared relationships in the acquired cohort; however, there is no independent universal ground truth establishing semantic linkage precision/recall.

The following remains **PARTIALLY PROVEN**:

- historical repository evolution/alias handling. Redirect continuity is proven for the exercised case, but no explicit repository-alias configuration layer exists and none is authorized by this research alone.

The following remains **UNSUPPORTED**:

- universal automatic cross-system linkage precision/recall from raw Jira/GitHub population data.

The following remains **NOT TESTED**:

- live bidirectional synchronization;
- webhook-driven updates;
- live provider writes;
- automated large-scale live retrieval.

## 5. Current engine boundary — important interpretation

ORBIT is now best described as a **deterministic evidence and review-state engine with a qualified cross-system evidence model**, not as a universal engineering-data integration platform.

The current work has demonstrated that the canonical model can represent authentic Jira/GitHub evidence beyond the original Jira-only proving corpus. It has **not** demonstrated that ORBIT should automatically ingest every enterprise engineering system, resolve every cross-system relationship, or infer organizational truth from arbitrary tool data.

The correct architectural posture remains:

**stable canonical semantics at the core + provider-specific validation/adaptation at boundaries + explicit evidence gaps + deterministic evaluation + human-verifiable provenance.**

No universal `ConnectorRegistry`, `ProviderRegistry`, `PluginManager`, `OAuthManager`, or capability framework is authorized by these experiments.

## 6. Immediate next steps

### Step 1 — Controlled consolidation of the Wave 3 qualification record

Consolidate the Phase 3A/3B research artifacts and qualification record into the controlled engineering branch while preserving the governing semantic baseline. This is a documentation/evidence-consolidation gate, not a request to alter production semantics.

Required controls:

- preserve the Phase 3A cohort manifest and raw hash manifest;
- preserve the Phase 3B reconciliation and evaluation artifacts;
- preserve the qualification report and exact digests;
- keep the protected `6d82d12` semantic baseline identifiable;
- keep research-only harness code/data separate from production engine code;
- rerun the regression suite after consolidation;
- verify the working tree is clean.

### Step 2 — Prepare Phase 4 design questions, without implementing them

The next research/design gate should investigate two questions raised by the real evidence:

1. **Repository evolution:** how should ORBIT represent historical repository moves, aliases, predecessor namespaces, and official redirects without contaminating deterministic identity semantics?
2. **Dependency taxonomy:** how should external repositories and dependency-oriented code changes be represented when they are authentic evidence but are not necessarily first-party implementation work for the Jira project?

These should first be expressed as ADR-level questions with alternatives, invariants, evidence requirements, and explicit non-goals. They are not yet implementation tasks.

### Step 3 — If semantic generalization is pursued, acquire corroborating evidence deliberately

The population study established a large reservoir of declared Jira→GitHub references, but semantic precision/recall remains unproven. Any next experiment should therefore acquire an independently adjudicable sample with enough native/complete GitHub and Jira relationship evidence to distinguish:

- declaration detection;
- semantic linkage correctness;
- state alignment correctness;
- temporal alignment correctness;
- provenance resolution;
- acquisition coverage.

These metrics must remain separate. No single aggregate “accuracy” number should be introduced.

### Step 4 — Keep customer validation running in parallel

The engineering proving work does not answer the central product question: whether real Engineering/Delivery Managers repeatedly prefer the ORBIT review workflow and whether a buyer will pay for it. Cross-system technical qualification therefore does not justify widening the product surface by itself.

The customer-validation track remains responsible for validating:

- repeated real review usage;
- preparation/reconciliation work removed;
- findings that materially affect the review agenda or investigation;
- decisions and commitments captured and revisited;
- correction rate and founder dependence;
- security/procurement feasibility;
- willingness to continue on a paid basis.

### Step 5 — Do not implement speculative integration architecture yet

The following remain explicitly deferred unless new evidence/decisions authorize them:

- universal connector/plugin framework;
- repository alias normalization as a core automatic heuristic;
- template filtering as a universal linkage heuristic;
- automated identity resolution;
- live GitHub/Jira synchronization;
- Jira write-back;
- full organizational graph;
- broad multi-provider ingestion;
- AI-driven inference as a replacement for deterministic evidence;
- widening V0 solely because cross-system technical feasibility has improved.

## 7. Current research posture

The project remains in the posture:

> **CONTINUE AS A DISCIPLINED EXPERIMENT.**

The engineering uncertainty has narrowed substantially: the canonical evidence model, deterministic evaluation discipline, provenance path, cross-system identity/cardinality handling, and conservative state/temporal semantics have now been exercised against authentic population-derived Jira/GitHub evidence.

The remaining high-value uncertainties are primarily:

- whether the cross-system semantics generalize with independently verifiable relationship evidence;
- how repository evolution/dependencies should be modeled without weakening identity semantics;
- whether managers actually derive repeated value from the resulting review state;
- whether that value is sufficient for adoption, security approval, and payment.

The central principle remains unchanged:

**Build durable evidence and execution-state foundations; let customer behavior determine which workflow becomes the product.**

No new locked decision number is created by this update.

## v38 context update — Phase 4A Wave 3 consolidation & governance audit — September 2026

### Status

**PASS WITH QUALIFICATIONS — EVIDENCE CONSOLIDATION VERIFIED; LOCAL GIT CLOSURE AND REPORT-DIGEST ERRATUM REMAIN**

Phase 4A was conducted as a governance/consolidation audit over the completed Wave 3 qualification record. It did not alter ORBIT semantic engine behavior.

### Verified preservation

- Phase 3A frozen cohort remains 100 candidates.
- Phase 3A selection remains seed 42 with 1,403 eligible candidates and 1 documented exclusion.
- Acquisition remains 98 `ACQUIRED` / 2 `NOT_FOUND`.
- Phase 3B reconciliation remains 100 candidates with the same 98/2 outcome split.
- Phase 3B raw artifact integrity remains:
  - cohort SHA `3aa4ebabefa84e95dd433d20ba82c852cce4a1bfe7a4f246bb9c01873f077775`;
  - 288/288 raw artifacts recomputed;
  - 0 missing;
  - 0 mismatches.
- All 14 entries in the Phase 3B artifact hash manifest independently match their recorded SHA-256 values.
- Machine-readable Phase 3B determinism remains true across repeated and permuted evaluation.
- Regression record remains green at 817 passed / 0 failed, with protected Track A and Apache/Mahout/TrueTenant invariants preserved.

### Phase 3B documentation erratum

Phase 4A identified a reporting artifact inconsistency: `phase3b_report.md` contains bundle/evaluation digest strings that differ from `phase3b_determinism.json`.

The machine-readable determinism artifact records:

- bundle digest: `504b2f03d86090cf40e23b76f8c46123b07dc222275aeea9ac081460b3420bed`;
- evaluation digest: `7fc973824bd228b8db298d4a26d3ae310e4cd3987f3f10183c568d75fa7222a0`;
- repeated evaluation match: `true`;
- permutation match: `true`.

The formal report records different digest strings.

This is classified as a **documentation/reporting artifact defect only**. It does not constitute an engine semantic defect or a determinism failure. The original Phase 3B report remains frozen; the discrepancy is recorded in `PHASE3B_DETERMINISM_DIGEST_ERRATUM.md`.

### Git qualification

The recorded consolidation HEAD remains `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`, with governing baseline `6d82d123f8bf50316d2b1ab7a025bc5862a474ed`.

The actual current local `/home/tecblic/orbit` checkout was not available in the Phase 4A execution environment, and the recorded `ea464540` object is not present in the connected GitHub remote. Therefore Phase 4A does not independently certify local branch ancestry or working-tree cleanliness.

That local verification is a closure condition, not an authorization to change the engine.

### Phase 4A closure requirements

Before Phase 4A is declared fully closed from the actual repository checkout:

1. verify the working tree is clean;
2. verify `HEAD == ea464540`;
3. verify `develop == 6d82d12`;
4. verify `ea464540` descends from the governing baseline;
5. rerun the protected regression suite after consolidation;
6. preserve the Phase 3B report/hash manifest and the determinism erratum.

No new locked decision is created.

### Next phase gate

After the local Git closure checks pass, proceed to **Phase 4B — Repository Identity & Evolution ADR**, followed by the separate dependency-taxonomy design question. Neither question authorizes implementation until the ADR evidence gate is completed.

The following remain explicitly unapproved:

- universal connector/provider framework;
- automatic repository alias normalization;
- dependency taxonomy implementation;
- live cross-system synchronization;
- Jira write-back;
- new cross-system inference rules.




## v39 context update — Phase 4D reconciliation, Phase 4E-B integration/hardening, and Phase 4E-C gate — 2026-10-01

### Governance / status

This update records the completed Phase 4D reconciliation and the subsequent Phase 4E-A / 4E-B work. It does **not** create a new locked decision number.

Current governing semantic baseline remains:

- `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)

Current execution/integration HEAD:

- `af0f0a744b6259b85bd5fd29243fab82d49608e9` (`af0f0a7`)
- branch: `develop`
- pushed to `origin/develop`
- working tree: clean

Consolidation lineage remains:

- `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`

Important distinction remains:

**governing semantic baseline ≠ consolidation HEAD ≠ current execution HEAD.**

---

# Phase 4D — Controlled Prototype Qualification — CLOSED

### Final status

**PASS / QUALIFIED**

Phase 4D demonstrated that the qualified `RepositoryEvolutionRelationship` contract can be instantiated and exercised against authentic repository-evolution cases while preserving repository identity, linkage neutrality, state separation, temporal separation, graph constraints, and provenance semantics.

Final reconciliation:

- invariant count corrected from 15 to **16**;
- authentic fixture provenance was cryptographically grounded;
- empty-string SHA-256 provenance was eliminated;
- authentic Phase 3A raw fixtures were wired into the four repository-evolution cases;
- full suite after reconciliation: **847 passed, 12 skipped, 0 failed**;
- qualification battery: **38/38 passed**.

### Authentic cases

1. `FLINK-1359`
   - `incubator-flink → flink`
   - relationship type: `REDIRECT`
   - HTTP redirect and GitHub repository identity evidence used for grounding
   - repository identity remains distinct from cross-system linkage

2. `stratosphere#126`
   - `stratosphere/stratosphere → apache/flink`
   - relationship type: `PREDECESSOR_SUCCESSOR`
   - historical donation/migration evidence
   - predecessor and successor repository identities remain distinct

3. `KAFKA-9168`
   - `kafka → rocksdb`
   - relationship type: `EXTERNAL_DEPENDENCY`
   - dependency evidence does not transfer lifecycle state between repositories

4. `FLINK-20650`
   - `flink → docker`
   - relationship type: `ECOSYSTEM_PACKAGING`
   - independent Jira/GitHub timelines remain separate
   - temporal classification preserves an observational `INVERTED` outcome rather than manufacturing causality

### Phase 4D invariant set

The formal set is **16 invariants**:

- `INV-ID-01` — identity immutability
- `INV-ID-02` — strict repository kind
- `INV-ID-03` — PR/repository collision isolation
- `INV-ID-04` — deterministic SHA-256 relationship identity
- `INV-EV-01` — mandatory cryptographic provenance / empty digest rejection
- `INV-EV-02` — no plain-URL lineage
- `INV-EV-03` — honest missing-evidence gaps
- `INV-LK-01` — linkage neutrality
- `INV-LK-02` — separation of repository and cross-system linkage
- `INV-ST-01` — no cross-repository state transfer
- `INV-ST-02` — external dependency state isolation
- `INV-TM-01` — temporal proximity is not causality
- `INV-TM-02` — temporal coherence remains separated across repositories
- `INV-GR-01` — lineage DAG acyclicity
- `INV-GR-02` — routing acyclicity / loop prevention
- `INV-GR-03` — dependency/fork non-transitivity

### Authentic fixture digests reconciled in Phase 4D

- `FLINK-1359`: `85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b`
- `stratosphere#126`: `24a167fa...` (full digest retained in the authoritative reconciliation artifact)
- `KAFKA-9168`: `a7f34525...` (full digest retained in the authoritative reconciliation artifact)
- `FLINK-20650`: `0a4625bf...` (full digest retained in the authoritative reconciliation artifact)

The key reconciliation outcome is that the previous empty SHA-256 placeholder was removed and authentic acquisition fixtures became the provenance basis.

---

# Phase 4E-A — Production Integration Design — CLOSED

### Status

**DESIGN COMPLETE**

Forensic inspection established the minimum production integration surface rather than assuming a new architecture.

The design preserves the existing architecture:

- canonical evidence types remain authoritative;
- evidence assembly remains the validation/assembly boundary;
- evaluator semantics remain frozen;
- cross-system fusion remains frozen;
- provider adapters remain untouched;
- repository evolution remains additive evidence context.

The design does **not** authorize:

- universal `ConnectorRegistry`;
- universal provider/plugin framework;
- automatic repository alias normalization;
- broad Stage 2 expansion;
- live provider synchronization;
- Jira write-back;
- new cross-system inference rules.

---

# Phase 4E-B — Controlled Production Integration — INITIAL INTEGRATION

### Initial implementation

Starting point:

- `3fd88fb8458caa6c3f2fd401ee0cdaf013843516`

Initial integration commit:

- `d4788809e437f652b999c811baa74b0d82db0ccd`

The implementation integrated the qualified repository-evolution contract into the canonical evidence domain.

Production surface was limited to:

- `src/shadow_orbit/evidence_types.py`
- `src/shadow_orbit/evidence_assembly.py`

with a thin qualification-schema adapter and dedicated integration tests.

### Initial integration result

- pre-integration: **847 passed, 12 skipped, 0 failed**
- post-integration: **865 passed, 12 skipped, 0 failed**
- added integration tests: **18**
- net regressions: **0**

Frozen boundaries remained untouched, including evaluator/evidence-evaluation/cross-system-fusion semantics and provider adapters.

---

# Phase 4E-B — Hardening Gate — CLOSED

### Final status

**PASS / HARDENED / QUALIFIED**

The initial integration underwent a forensic review. Four concrete findings were identified and subsequently remediated.

## H1 — Provenance type loophole and cryptographic validation

### Finding

Repository evolution provenance could previously accept a broader provenance type that did not guarantee the repository-specific cryptographic fields.

### Resolution

`RepositoryEvolutionRelationship.provenance_refs` is now restricted to:

`RepositoryProvenanceRef`

Validation enforces:

- correct provenance type;
- non-empty `instance_id`;
- non-empty `fixture_id`;
- non-empty `record_locator`;
- exactly 64 lowercase hexadecimal SHA-256 characters;
- rejection of the empty-string SHA-256 digest.

`verify_provenance_file_digest` is restricted to the repository provenance contract and guards invalid types, paths, and I/O failures.

## H2 — Lossless provenance serialization

### Finding

Repository provenance serialization did not previously preserve all repository-specific provenance fields losslessly and used fabricated fallback values during reconstruction.

### Resolution

`RepositoryProvenanceRef` now preserves:

- `fixture_id`;
- `record_locator`;
- `sha256_digest`;
- `observation_id`;
- `source_field_path`.

Fabricated provenance fallbacks were removed.

Round-trip serialization/deserialization is now explicitly tested.

## H3 — Silent semantic conflict collapse during deduplication

### Finding

Duplicate relationship IDs could previously cause semantically different records to collapse while retaining only the first semantic record and merging provenance.

### Resolution

A semantic-conflict check now compares:

- relationship family;
- relationship type;
- source/target repositories;
- directionality;
- transitivity rule;
- verification status;
- observation timestamp;
- validity interval;
- family payload;
- semantic firewall.

Identical semantic duplicates may merge provenance deterministically.

Semantically conflicting duplicates **fail closed** rather than being silently collapsed.

`validate_evidence_bundle` surfaces contradictory relationship conditions explicitly.

## H4 — Cross-provider graph endpoint identity

### Finding

Graph validation previously keyed repository endpoints only by `entity_id`, creating a potential false cycle/self-loop across providers or instances.

### Resolution

Graph endpoint identity now uses the composite:

`source_kind:instance_id:entity_id`

The Phase 4C relationship-ID formula remains unchanged.

Graph cycle/self-loop checks therefore preserve provider/instance identity boundaries.

---

# Phase 4E-B — Final qualification results

Final hardening HEAD:

- `af0f0a744b6259b85bd5fd29243fab82d49608e9`
- commit message: `feat(phase4e): harden repository evolution contract and deduplication`

Repository state:

- branch: `develop`
- pushed to `origin/develop`
- clean working tree

Final regression result:

- **873 passed**
- **12 skipped**
- **0 failed**
- **3 warnings**

Phase-specific results:

- Phase 4D qualification: **38/38**
- Phase 4E-B integration/hardening: **26/26**
- Mahout qualification: **28 passed / 12 skipped / 0 failed**
- TrueTenant: **34/34**
- Apache: **21/21**
- all 16 Phase 4D invariants exercised
- determinism checks green
- production-scope diff check clean

Regression progression:

`847 → 865 → 873`

with **0 net regressions**.

### Production boundary preserved

The hardening work modified only the authorized repository-evolution/evidence integration surface and its qualification tests/documentation.

Frozen evaluator, evidence-evaluation, cross-system-fusion, and provider-adapter boundaries remained untouched.

No live provider mutation was introduced.

---

# Phase 4E-B — Current semantic interpretation

The repository-evolution contract is now not merely a qualification-only schema. It is integrated into the canonical evidence infrastructure.

However:

**repository evolution remains evidence context, not automatic inference.**

The following remain distinct:

- repository identity;
- repository evolution;
- cross-system linkage;
- work-item state;
- code-change state;
- temporal ordering;
- causal interpretation.

Repository evolution does not by itself:

- transfer issue state;
- transfer PR ownership;
- create Jira↔GitHub linkage;
- establish causality;
- establish completion;
- establish blockage;
- establish organizational responsibility.

This distinction is now enforced by both contract validation and integration/hardening tests.

---

# Phase 4E-C — Integrated Evidence-Pipeline Qualification

### Status

**PROVING SPECIFICATION DRAFT — NO IMPLEMENTATION AUTHORIZED**

Phase 4E-C is the next proving gate.

### Objective

Determine whether the hardened `RepositoryEvolutionRelationship` representation remains semantically isolated and deterministic when repository-evolution evidence participates in the broader ORBIT evidence/evaluation pipeline.

The central hypothesis is:

> **Repository evolution may enrich evidence context, but must not silently upgrade the evidentiary status of an observation, relationship, state, temporal conclusion, or organizational finding.**

### 4E-C proving gates

#### Gate 4E-C-01 — Evidence assembly integrity

Verify:

- repository evolution survives ordinary `EvidenceBundle` assembly;
- ordinary observations remain unchanged;
- ordinary relationships remain unchanged;
- cross-system alignments remain unchanged;
- provenance remains lossless;
- ordering remains deterministic;
- identical duplicates deduplicate safely;
- conflicting duplicates fail closed.

#### Gate 4E-C-02 — Linkage isolation

Explicitly test that:

- repository redirect + target PR does not create Jira↔PR linkage;
- predecessor/successor relationships do not transfer issue ownership;
- repository evolution does not upgrade lexical/mention relationships;
- existing explicit Jira↔GitHub relationships remain authoritative.

#### Gate 4E-C-03 — State isolation

Verify that repository evolution never transfers:

- work-item state;
- code-change state;
- completion;
- blockage;
- ownership;
- lifecycle status.

#### Gate 4E-C-04 — Temporal isolation

Verify that temporal ordering remains distinct from causality.

Temporal proximity must not independently establish causal relationships.

#### Gate 4E-C-05 — Evaluation isolation

Compare equivalent evidence with and without repository-evolution metadata.

If the addition of repository evolution changes evaluation output, the change must be:

1. attributable to an explicit existing rule;
2. traceable to an explicit evidence dependency;
3. deterministic;
4. provenance-backed;
5. semantically explainable.

An unexplained new finding is a qualification failure.

### Mandatory adversarial cases

At minimum:

- redirect + target PR;
- redirect + target Jira issue;
- predecessor/successor repositories with colliding PR numbers;
- external dependency + merged dependency PR;
- packaging relationship + later package merge;
- repository evolution + explicit Jira↔PR relationship;
- repository evolution + lexical similarity;
- repository evolution + temporal proximity;
- repository evolution + missing provenance;
- same repository name across providers;
- conflicting duplicate relationship IDs;
- evidence-order permutation;
- repository evolution removal;
- repository evolution addition;
- malformed repository-evolution metadata.

### 4E-C non-goals

The phase does not authorize:

- new connector architecture;
- new provider integrations;
- automatic alias normalization;
- automatic identity resolution;
- live synchronization;
- Jira write-back;
- new cross-system inference rules;
- dependency-taxonomy implementation;
- customer-facing V0 expansion.

### Required qualification artifacts

The eventual qualification must produce machine-readable evidence covering:

- qualification manifest;
- input manifest;
- expected invariants;
- adversarial cases;
- results;
- determinism;
- provenance verification;
- evaluation comparison;
- regression summary;
- final forensic report.

Every conclusion must remain classified as:

- **PROVEN**
- **SUPPORTED**
- **UNSUPPORTED**
- **NOT TESTED**
- **FAILED**

### 4E-C implementation boundary

This specification does **not** authorize production changes.

The default assumption is:

> **No production semantic changes unless the proving experiment demonstrates that an existing production boundary is insufficient.**

Any proposed production change must first identify:

1. file;
2. symbol;
3. semantic purpose;
4. why qualification-only code is insufficient;
5. invariant affected;
6. regression test;
7. rollback boundary.

---

# Updated phase state

| Phase | Current state |
|---|---|
| Phase 4D — Controlled Prototype Qualification | **CLOSED — PASS / QUALIFIED** |
| Phase 4E-A — Production Integration Design | **CLOSED — DESIGN COMPLETE** |
| Phase 4E-B — Initial Production Integration | **SUPERSEDED BY HARDENED REVISION** |
| Phase 4E-B — Hardening Gate | **CLOSED — PASS / HARDENED / QUALIFIED** |
| Phase 4E-C — Integrated Evidence-Pipeline Qualification | **DRAFT SPECIFICATION — PENDING AUTHORIZATION** |

### Current engineering state

**Governing semantic baseline:** `6d82d12`

**Current execution HEAD:** `af0f0a7`

**Branch:** `develop`

**Working tree:** clean

**Current full regression:** `873 passed / 12 skipped / 0 failed`

### Governance state

No new locked decision is created by the Phase 4D/4E work or by the Phase 4E-C specification.

The core principle remains:

> **Build durable evidence and execution-state foundations; let customer behavior determine which workflow becomes the product.**

The immediate next action is the review/authorization decision for the Phase 4E-C proving specification. No production implementation should begin until that gate is explicitly authorized.


END OF CANONICAL PROJECT ORBIT CONTEXT
