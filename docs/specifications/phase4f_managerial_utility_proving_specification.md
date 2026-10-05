# Project ORBIT — Phase 4F Proving Specification
## Managerial Utility & Product-Wedge Qualification

**Document ID:** `SPEC-PHASE-4F-01`
**Phase:** Phase 4F — Managerial Utility / Product-Wedge Qualification
**Status:** **PROPOSAL / DRAFT — AWAITING REVIEW & EXPLICIT AUTHORIZATION**
**Date:** 2026-10-05
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)
**Consolidation Lineage:** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab` (`ea46454`)
**Predecessor Phase:** Phase 4E-D Multi-System Evidence Composition — CLOSED / PASS WITH DOCUMENTATION QUALIFICATION
**Current Execution HEAD:** `1bfad1c6c81ad488fe11fa1e0a75903466cfe152` (`1bfad1c`)
**Branch:** `develop`
**Decision Ceiling:** `S-034` (No new architectural decisions authorized)
**Implementation Authorization:** **NONE — SPECIFICATION DRAFT ONLY**

---

## Epistemic Classification Taxonomy

To ensure forensic rigor and prevent narrative inflation, every major proposition, requirement, and observation in this specification is explicitly classified using the following seven epistemic categories:

- `[CANONICAL FACT]`: Established, locked project decisions (S-001 through S-034) and authoritative baseline contracts.
- `[OBSERVED ENGINEERING EVIDENCE]`: Direct, cryptographically verified empirical results from tests, fixtures, and code executions in the repository.
- `[CUSTOMER-VALIDATED EVIDENCE]`: Direct observations, quotes, and workflow demonstrations from real human practitioners (e.g., GoGreen Engineering Manager discovery).
- `[SUPPORTED HYPOTHESIS]`: Hypotheses backed by multiple converging signals or adjacent-market evidence, but not yet formally validated as market-wide truths.
- `[UNVALIDATED HYPOTHESIS]`: Product, behavioral, or commercial assumptions that require empirical qualification in Phase 4F.
- `[PROPOSED METHODOLOGY]`: The experimental protocols, measurement criteria, and testing procedures defined in this specification.
- `[OPEN QUESTION]`: Explicitly acknowledged unknowns that must be investigated and answered through Phase 4F qualification.

---

## 1. Purpose

`[PROPOSED METHODOLOGY]` Phase 4F transitions Project ORBIT from **foundational semantic qualification** to **managerial utility and product-wedge qualification**.

`[OBSERVED ENGINEERING EVIDENCE]` Across Pass 4 (Waves 1–5) and Pass 5 (Phases 4D, 4E-A, 4E-B, 4E-C, and 4E-D), ORBIT conclusively proved that its evidence pipeline can:
1. Ingest, normalize, and validate heterogeneous records from Jira, GitHub, and legacy repositories.
2. Build unified, compound `EvidenceBundle` representations with 100% cryptographic provenance.
3. Formally isolate identity, linkage, state, temporal ordering, and dependency graphs across systems.
4. Evaluate cross-system health rules (`ORBIT-XB-01`, `ORBIT-XB-02`, `ORBIT-XB-03`) deterministically without false inference, causality fabrication, or Cartesian explosion.

`[CANONICAL FACT]` However, technical correctness is not customer value. As established in Decision `S-006` and Canonical Context Section 14F, ORBIT is built to serve a specific human customer: the **Engineering Manager / Delivery Manager**.

`[PROPOSED METHODOLOGY]` Phase 4F will determine whether the verified evidence foundation produces materially useful managerial understanding and decisions, or whether the current product wedge fails to deliver sufficient customer utility. Phase 4F is an experimental proving gate designed to validate or falsify the v0 product wedge before authorizing productization.

---

## 2. Current Project State

- `[CANONICAL FACT]` **Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`).
- `[OBSERVED ENGINEERING EVIDENCE]` **Repository Checkout:** `develop` at `1bfad1c6c81ad488fe11fa1e0a75903466cfe152` (clean, synchronized with `origin/develop`).
- `[OBSERVED ENGINEERING EVIDENCE]` **Predecessor Milestones:**
  - Phase 4D (Prototype Qualification): CLOSED — PASS / QUALIFIED (16 invariants, authentic Apache cases).
  - Phase 4E-A (Production Integration Design): CLOSED — DESIGN COMPLETE.
  - Phase 4E-B (Production Integration & Hardening): CLOSED — PASS / HARDENED / QUALIFIED (26/26 tests, H1–H4 hardened).
  - Phase 4E-C (Integrated Pipeline Qualification): CLOSED — PASS / QUALIFIED (5 gates, 15 scenarios, 20 invariants).
  - Phase 4E-D (Multi-System Evidence Composition): CLOSED — PASS WITH DOCUMENTATION QUALIFICATION (5 gates, 15 execution-derived scenarios, 24 formal invariants, Git identity fully reconciled).
- `[OBSERVED ENGINEERING EVIDENCE]` **Regression State:** 913 passed, 12 skipped (offline MongoDB daemon), 0 failed.
- `[OBSERVED ENGINEERING EVIDENCE]` **Production Code State:** Zero production code modifications in `src/shadow_orbit/` since semantic baseline `6d82d12`.
- `[CANONICAL FACT]` **Decision Ceiling:** Locked at `S-034`. No new architectural decisions are authorized or created.

---

## 3. Problem Hypothesis

- `[CANONICAL FACT]` Organizations suffer from fragmented tools, duplicated context, disconnected workflows, and coordination overhead (`S-001`).
- `[SUPPORTED HYPOTHESIS]` In growth-stage engineering organizations (20–150 employees, `S-002`), Engineering Managers and Delivery Managers spend significant manual effort (typically 3 to 7 hours per week per team) preparing for recurring weekly engineering reviews.
- `[CUSTOMER-VALIDATED EVIDENCE]` This preparation involves manually collating Jira sprint boards, inspecting GitHub pull request activity, querying developers on Slack, and reconciling discrepancies between nominal ticket status and physical code changes.
- `[CUSTOMER-VALIDATED EVIDENCE]` Despite this manual effort, reviews remain vulnerable to high-consequence blind spots:
  1. Work items marked `Done` in Jira whose corresponding GitHub PRs were never merged or closed without shipping (`ORBIT-XB-01`).
  2. Code merged into production branches without an associated or resolved Jira ticket, creating untracked scope creep and unreviewed delivery commitments (`ORBIT-XB-02`).
  3. Work items closed weeks before code changes merge, representing observational lag, unverified handoffs, or premature administrative sign-offs (`ORBIT-XB-03`).
  4. Chronic, recurring problems in business-critical operational domains (e.g., billing, service contracts) that are repeatedly handled as isolated tickets rather than recognized as organizational patterns.
- `[UNVALIDATED HYPOTHESIS]` An automated, evidence-backed review preparation engine will reduce weekly preparation time by at least 40%, eliminate cross-system delivery blind spots, and improve the consistency and follow-through of managerial commitments.

---

## 4. Core Proving Question

The central question that Phase 4F must answer is:

> **Does the verified ORBIT evidence foundation materially improve the Engineering Weekly Review for an Engineering / Delivery Manager?**

This breaks down into five sub-questions:
1. **Preparation Efficiency:** Does ORBIT measurably reduce the manual time and friction required to prepare an accurate operating review?
2. **Signal Saliency:** Does ORBIT surface items that managers agree genuinely require operational attention, while keeping irrelevant noise low?
3. **Evidence Trust:** Can a manager verify, understand, and defend every surfaced finding directly from raw source evidence without algorithmic opacity?
4. **Decision Utility:** Does the review artifact lead to concrete, actionable managerial decisions, risk mitigations, or follow-up commitments?
5. **Wedge Viability:** Is the Engineering Weekly Review sufficiently recurring and consequential to serve as ORBIT's commercial foundation, or does evidence dictate an alternative product wedge?

---

## 5. Scope

`[CANONICAL FACT]` The scope of Phase 4F is strictly bounded by existing canonical architecture and locked decisions:

1. **Target Product Wedge:** The **Engineering Weekly Review** for Engineering Managers and Delivery Managers (`S-004`, `S-006`).
2. **Core Value Promise:** *"Your weekly engineering operating review prepares itself."* (`S-006`).
3. **Evidence Sources:** Native Jira Cloud / Software work items and GitHub repository code changes / pull requests (`S-034`).
4. **Target Users:**
   - Primary: Engineering Managers (EMs) and Delivery Managers (DMs) with direct delivery accountability.
   - Secondary: Technical Leads (Tech Leads) responsible for sprint execution.
5. **Operating Cycles:** Weekly operating reviews and bi-weekly sprint boundaries.
6. **Delivery Artifact:** A structured, deterministic, human-readable review document (Markdown / JSON) containing verified status, cross-system exceptions, recurring domain patterns, and carry-forward commitments.

---

## 6. Non-Goals

`[CANONICAL FACT]` To preserve architectural discipline, Phase 4F explicitly excludes:

1. **No Production Code Modifications:** `src/shadow_orbit/` remains frozen under semantic baseline `6d82d12`.
2. **No Connector Expansion:** No implementation of third-party connectors for Slack, Microsoft Teams, Salesforce, SAP, Linear, or GitLab (`S-003`).
3. **No Autonomous Actions or Write-Back:** ORBIT remains strictly read-only; no automated writing back to Jira (e.g., auto-transitioning tickets) or GitHub (`S-008`).
4. **No Generic Enterprise Search:** No implementation of unstructured organizational search or indexing (`S-004`).
5. **No Automated Employee Performance Evaluation:** ORBIT evaluates cross-system work-state integrity, not developer competence, speed, or performance. No employee scoring or stack ranking (`14G.18`).
6. **No LLM Source-of-Truth:** LLMs are strictly forbidden from acting as a source of facts, calculating metrics, or manufacturing findings (`S-007`).
7. **No Broad Stage 2/3/4 Capabilities:** No expansion into universal workflow engines, automated blocker removal, or multi-department orchestration (`S-005`).

---

## 7. Existing Evidence Base

The specification grounds itself in the empirical record accumulated across Passes 1 through 5:

### 7.1 Canonical Architecture & Governance
- `[CANONICAL FACT]` `S-001` through `S-006`: Core problem, growth-stage ICP, progressive consolidation, recurring operating rhythm wedge, 7-step execution loop, and v0 EWR definition.
- `[CANONICAL FACT]` `S-007`: Deterministic intelligence principle (Finding → Evidence → Source/Rule/Calculation). AI is strictly downstream narration.
- `[CANONICAL FACT]` `S-008`: Hybrid ownership and provenance model. External systems own native records; ORBIT owns synthesized cross-system relationships and evaluations.
- `[CANONICAL FACT]` `S-034`: Jira + GitHub dual-track cross-system evidence direction.

### 7.2 Verified Engineering Pipeline
- `[OBSERVED ENGINEERING EVIDENCE]` **913 Passed Automated Tests:** Complete regression suite verifying Track A deterministic engines, normalization, temporal models, and cross-system correlation.
- `[OBSERVED ENGINEERING EVIDENCE]` **24 Formal Invariants PROVEN:**
  - Identity (INV-ID-01..04)
  - Provenance & Digest Integrity (INV-EV-01..03)
  - Linkage Neutrality (INV-LK-01..02)
  - State Isolation (INV-ST-01..02)
  - Temporal Non-Causality (INV-TM-01..02)
  - Acyclic Graph Boundaries (INV-GR-01..03)
  - Semantic Firewall & Evaluation Equivalence (INV-FW-01..04)
  - Multi-System Compositional Orthogonality (INV-CMP-01..04)
- `[OBSERVED ENGINEERING EVIDENCE]` **Cryptographic Determinism:** 5-way randomized sequence trials produce byte-identical serialized JSON digests (`652808c29ae356...`) and stable finding digests.
- `[OBSERVED ENGINEERING EVIDENCE]` **100% Provenance Verification:** All raw source fixtures independently verified against on-disk SHA-256 digests.

### 7.3 Direct Customer Discovery Evidence
- `[CUSTOMER-VALIDATED EVIDENCE]` **GoGreen EM Discovery (Samyak, Context 14G.15–14G.17):**
  - *Source Status ≠ Attention Semantics:* A ticket in `Waiting for Additional Information` is semantically blocked, but the EM does not consider it an automatic review agenda item. Similarly, `In Review` represents client staging feedback and is not an operational failure.
  - *Jira Priority ≠ Organizational Urgency:* `Highest` priority tickets are frequently overridden by immediate verbal or email client requests.
  - *Recurrence as Primary Signal:* The manager independently prioritized tickets in **billing, service contracts, and insurance** because they occur repeatedly and represent client-critical friction. The core managerial need is: *"Reveal what keeps happening that should not keep happening."*
  - *Data Quality Realities:* Commercial project Jira data exhibits absent due dates, sparse changelogs, unmapped statuses, and minimal explicit GitHub PR links.
- `[SUPPORTED HYPOTHESIS]` **Adjacent Market & Discovery Signals (Context 14G.1, 14G.18):**
  - Multiple enterprise practitioners confirm spending 0.5 to 1.0 days preparing for weekly operational reviews.
  - Practitioners using Microsoft Copilot and Claude note that while AI retrieves information, human validation remains mandatory because LLM outputs require manual verification.
  - Cross-system reconstruction (linking Jira tickets to GitHub PRs) is painful and manually intensive during project audits and handoffs.

---

## 8. Critical Evidence Gaps

`[OPEN QUESTION]` While the evidence pipeline is technically proven, the following product hypotheses remain entirely unevidenced:

| Gap ID | Dimension | Critical Unknown | Risk if Unaddressed |
|---|---|---|---|
| **GAP-01** | **Managerial Relevance** | Do real managers actually care about `ORBIT-XB-01`, `XB-02`, and `XB-03` findings during a weekly review, or are they viewed as administrative nitpicks? | Building high-assurance detection for issues managers ignore. |
| **GAP-02** | **Preparation Time** | Does ORBIT's review artifact actually save measurable preparation time in a live workflow, or does reviewing ORBIT's output add cognitive overhead? | Value proposition fails; managers abandon tool due to review friction. |
| **GAP-03** | **Signal-to-Noise Ratio** | What proportion of surfaced findings are dismissed by managers as expected, acceptable, or irrelevant operational noise? | False-positive fatigue leads to notification blindness. |
| **GAP-04** | **Unaided vs Aided Saliency** | When an EM selects their weekly review agenda unaided, how closely does it overlap with ORBIT's deterministically surfaced findings? | Mismatch between ORBIT's rule engine and human managerial priorities. |
| **GAP-05** | **Decision Impact** | Does an evidence-backed review artifact change what decisions are made, or does it merely document what the team was already doing? | Tool provides reporting without providing actionable utility. |
| **GAP-06** | **Wedge Falsification** | Is the Engineering Weekly Review a sufficiently painful and recurring problem to drive software adoption, or is another workflow (e.g., continuous PR triage, audit logging) the true wedge? | Commercial dead end; investing in the wrong product wedge. |

---

## 9. Multidimensional Utility Model

`[PROPOSED METHODOLOGY]` To qualify managerial utility rigorously, Phase 4F evaluates seven explicit operational dimensions. Utility is not defined as aesthetic satisfaction; it is defined as measurable workflow improvement.

```text
                                 ┌─────────────────────────────────────────┐
                                 │       ORBIT MANAGERIAL UTILITY          │
                                 └────────────────────┬────────────────────┘
                                                      │
         ┌───────────────────┬────────────────────────┼────────────────────────┬───────────────────┐
         ▼                   ▼                        ▼                        ▼                   ▼
┌─────────────────┐ ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐ ┌─────────────────┐
│ A. Preparation  │ │   B. Coverage   │      │C. Prioritization│      │   D. Decision   │ │   E. Evidence   │
│   Efficiency    │ │   & Blind-Spots │      │   & Saliency    │      │   Usefulness    │ │      Trust      │
└─────────────────┘ └─────────────────┘      └─────────────────┘      └─────────────────┘ └─────────────────┘
         │                   │                        │                        │                   │
         ▼                   ▼                        ▼                        ▼                   ▼
  - Elapsed prep      - High-impact items      - Actionable findings   - Escalations     - Source citation
    time reduction      surfaced                 vs background noise    prompted           verifiability
  - Manual steps      - Unlinked PRs           - Saliency score        - Follow-up       - Transparency on
    eliminated          detected                 (1 to 5 scale)         commitments        unknowns/gaps
```

### Dimension A: Preparation Efficiency
- **Definition:** The reduction in manual effort and elapsed time required by an EM/DM to prepare the weekly review agenda, status summary, and risk register.
- **Metric:** Pre-review preparation time (minutes) using baseline tools vs. ORBIT-assisted workflow.
- **Target:** $\ge 40\%$ reduction in manual preparation time.

### Dimension B: Coverage & Blind-Spot Detection
- **Definition:** The ability to surface high-consequence operational and delivery discrepancies that would have been missed in the manager's normal manual review.
- **Metric:** Number of verified cross-system discrepancies (`ORBIT-XB-01..03`) acknowledged by the manager as consequential but absent from their unaided notes.
- **Target:** At least 1 confirmed, previously unobserved cross-system blind spot surfaced per review cycle.

### Dimension C: Prioritization & Saliency
- **Definition:** The degree to which surfaced findings align with real organizational urgency rather than raw ticket metadata.
- **Metric:** Precision of surfaced attention items ($P = \frac{\text{Accepted Actionable Findings}}{\text{Total Surfaced Findings}}$).
- **Target:** $P \ge 70\%$ (less than 30% dismissed as irrelevant noise).

### Dimension D: Decision Usefulness & Actionability
- **Definition:** The extent to which the review artifact prompts concrete managerial interventions, escalations, resource reallocations, or formal carry-forward commitments.
- **Metric:** Count of documented managerial decisions or action items directly attributable to ORBIT findings.
- **Target:** At least 2 actionable decisions/commitments recorded per review session.

### Dimension E: Evidence Trust & Auditability
- **Definition:** The manager's ability to inspect, comprehend, and defend a finding to engineering directors, clients, or engineers by following direct provenance links to raw source fields.
- **Metric:** Audit success rate ($100\%$ of challenged findings traceable to source records in $< 30$ seconds).
- **Target:** Zero unexplained, unevidenced, or fabricated claims.

### Dimension F: Temporal Carry-Forward & Recurrence Tracking
- **Definition:** The preservation of commitment trajectory across review cycles, explicitly distinguishing new, ongoing, resolved, and recurring organizational issues.
- **Metric:** Percentage of previous-period commitments accounted for in the subsequent review (zero dropped commitments).
- **Target:** $100\%$ carry-forward accounting.

### Dimension G: Cognitive Burden & Noise Resistance
- **Definition:** The cognitive load imposed by reviewing ORBIT's output, ensuring that reviewing findings does not create more friction than manual preparation.
- **Metric:** Human qualitative rating of cognitive fatigue and usability (1 to 5 scale).
- **Target:** Qualitative rating $\ge 4.0$.

---

## 10. Weekly Review Artifact Definition

`[PROPOSED METHODOLOGY]` For Phase 4F, the Engineering Weekly Review artifact is formalized as a deterministic, human-readable markdown document generated directly from an authoritative `EvidenceBundle`. It consists of seven standardized sections:

```text
┌────────────────────────────────────────────────────────────────────────┐
│               ENGINEERING WEEKLY REVIEW ARTIFACT STRUCTURE             │
├────────────────────────────────────────────────────────────────────────┤
│ 1. REVIEW METADATA & SCOPE                                             │
│    - Team / Project Identifier, Review Period Dates, Extraction Cutoff │
├────────────────────────────────────────────────────────────────────────┤
│ 2. EXECUTIVE DELIVERY SUMMARY                                          │
│    - Planned vs Completed Work Items, Committed vs Shipped Scope       │
│    - Active Contributor Headcount, Primary Operational Branches        │
├────────────────────────────────────────────────────────────────────────┤
│ 3. CROSS-SYSTEM DELIVERY EXCEPTIONS (DETERMINISTIC FINDINGS)           │
│    - ORBIT-XB-01: Resolved Tickets with Open/Unmerged Code             │
│    - ORBIT-XB-02: Merged/Shipped Code without Tracked Ticket           │
│    - ORBIT-XB-03: Observational Lag & Premature Closures               │
├────────────────────────────────────────────────────────────────────────┤
│ 4. RECURRING DOMAIN ATTENTION (PATTERN DISCOVERY)                      │
│    - Clustered Activity in Critical Business Modules (Billing/Auth)   │
│    - Repeated Re-opened Items and Chronic Blockers                     │
├────────────────────────────────────────────────────────────────────────┤
│ 5. PREVIOUS COMMITMENT RECONCILIATION                                  │
│    - Status of Decisions and Action Items from Preceding Review Cycle  │
├────────────────────────────────────────────────────────────────────────┤
│ 6. NEW MANAGERIAL DECISIONS & COMMITTED ACTIONS                        │
│    - Structured Capture: Decision, Owner, Evidence Basis, Target Date │
├────────────────────────────────────────────────────────────────────────┤
│ 7. EVIDENCE AUDIT & UNCERTAINTY LEDGER                                 │
│    - Cryptographic Fixture SHA-256 Hashes, Provenance Source Links     │
│    - Explicit Boundary Disclosure: What ORBIT Does NOT Know            │
└────────────────────────────────────────────────────────────────────────┘
```

### Artifact Design Rules
1. **Fact-First Presentation:** Every metric and finding must cite its source entity (`EntityRef`) and observation (`ObservationId`).
2. **Deterministic Synthesis:** Running the generator on the same `EvidenceBundle` must produce the exact same text and hash.
3. **Explicit Uncertainty Disclosure:** If changelogs were omitted, commit dates are ambiguous, or PR reviews are unrecorded, the artifact must prominently declare these gaps in Section 7.
4. **No Unattributed Text:** If automated narration is evaluated (in Gate 4F-04), it must be visually segregated and explicitly linked to underlying factual claim IDs.

---

## 11. Baseline Workflow Definition

`[CUSTOMER-VALIDATED EVIDENCE]` To establish a credible basis of comparison, ORBIT is evaluated against the real-world baseline workflow currently practiced by engineering managers:

### 11.1 The Existing Manual Workflow
1. **Jira Inspection (60–90 min):**
   - EM opens Jira sprint board, filters by `Sprint = Current` or `Status != Closed`.
   - Manually reviews 30–80 tickets to identify stalled items, missing estimates, or overdue dates.
   - Manually clicks through individual ticket changelogs to check recent developer comments.
2. **GitHub Cross-Checking (45–75 min):**
   - EM opens GitHub Pull Requests tab across 1–3 primary team repositories.
   - Scans open PRs for review lag, failing CI builds, or inactive branches.
   - Attempts to match PR branch names or commit messages to Jira issue keys manually.
3. **Standup / Chat Reconciliation (30–60 min):**
   - EM checks Slack / Teams channel history or asks engineers directly: *"Did PR #123 actually ship?"* or *"Why is GG-456 still in progress?"*
4. **Report / Agenda Drafting (45–60 min):**
   - EM manually compiles findings, bullet points, and status into a Google Doc, Confluence page, or presentation slide deck for the weekly team or leadership review.
5. **Total Baseline Investment:** **3.0 to 5.0 hours per week** for a single engineering team of 6–10 engineers.

### 11.2 Baseline Vulnerabilities
- **Memory Fatigue:** The EM relies on personal memory to recall commitments made in the previous week.
- **Silo Blindness:** A PR merged by a senior developer directly into staging without a ticket is completely invisible on the Jira board.
- **Administrative Deception:** Tickets transitioned to `Closed` by developers on Friday afternoon to meet sprint velocity targets, despite PRs remaining unmerged, are accepted at face value.

---

## 12. Qualification Methodology

`[PROPOSED METHODOLOGY]` Phase 4F executes a **dual-track experimental methodology** that strictly separates software engineering qualification from human behavioral validation:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   PHASE 4F DUAL-TRACK ARCHITECTURE                     │
├───────────────────────────────────┬────────────────────────────────────┤
│ TRACK A: ENGINEERING PROVING      │ TRACK B: MANAGERIAL VALIDATION     │
├───────────────────────────────────┼────────────────────────────────────┤
│ - Deterministic Artifact Pipeline │ - Human Engineering Managers       │
│ - Schema Validation & Integrity   │ - Real Commercial Operating Data   │
│ - Provenance & Traceability Check │ - Comparative Workflow Sessions    │
│ - Performance & Invariant Safety  │ - Unaided vs Aided Saliency Tests  │
│ - Zero Production Semantic Change │ - Structured Decision Auditing     │
├───────────────────────────────────┴────────────────────────────────────┤
│                       SYNTHESIS & GATE EVALUATION                      │
│            Does technical capability translate to customer value?      │
└────────────────────────────────────────────────────────────────────────┘
```

### Strict Separation Principle
- `[CANONICAL FACT]` **Track A PASS $\neq$ Track B PASS:** A technically flawless, deterministically generated review document is a failure if managers find it irrelevant, noisy, or unhelpful.
- `[CANONICAL FACT]` **Track B PASS $\neq$ Architecture Approved:** A positive manager reaction to an ad-hoc or ungrounded prototype cannot authorize architectural compromises or unevidenced production changes.
- Both tracks must pass independently for Phase 4F to achieve an overall qualification verdict of **PASS**.

---

## 13. Track B: Participant & Customer Validation Methodology

`[PROPOSED METHODOLOGY]`

### 13.1 Participant Cohort & Selection Criteria
The validation cohort must comprise **3 to 5 practicing managers** across at least **two independent organizational environments**:
1. **Cohort Stratum 1 (Commercial SaaS / WMS):** 1–2 EMs from internal enterprise development (e.g., GoGreen WMS team at Tecblic).
2. **Cohort Stratum 2 (Independent External Product Team):** 2–3 EMs / DMs from external growth-stage software companies (20–150 employees, matching `S-002`).

**Mandatory Participant Prerequisites:**
- Must currently lead a team of $\ge 4$ software engineers.
- Must hold direct accountability for delivery outcomes in recurring weekly operating reviews.
- Team must actively use Jira (Cloud or Data Center) for work tracking and GitHub for version control.
- Must be willing to participate in a 90-minute comparative workflow evaluation session over recent, real project evidence.

### 13.2 Comparative Evaluation Protocol
Each participant undergoes a two-part comparative protocol using authoritative data from their own project:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                  COMPARATIVE EVALUATION PROTOCOL                       │
├────────────────────────────────────────────────────────────────────────┤
│ PART 1: UNAIDED AGENDA SELECTION (30 minutes)                          │
│ 1. Participant is provided the review cutoff timestamp.               │
│ 2. Using their existing tools (Jira, GitHub, Slack, Confluence), the   │
│    manager independently drafts their weekly review agenda:            │
│    - Top 3–5 items requiring discussion/attention                      │
│    - Key delivery risks / blockers                                     │
│    - Status of planned sprint commitments                             │
│ 3. Observer logs: Elapsed time, manual clicks, external queries.       │
├────────────────────────────────────────────────────────────────────────┤
│ PART 2: AIDED EVALUATION WITH ORBIT ARTIFACT (45 minutes)              │
│ 1. Participant is presented with the generated ORBIT Review Artifact.  │
│ 2. Think-aloud protocol: Participant reviews each section aloud.       │
│ 3. For every surfaced ORBIT finding, participant classifies:           │
│    - [ACTIONABLE]: Consequential item that warrants team discussion.  │
│    - [KNOWN/ACCEPTED]: Real discrepancy, but already understood/OK.   │
│    - [IRRELEVANT NOISE]: Trivial or false-positive administrative item.│
│ 4. Blind-Spot Audit: Did ORBIT surface consequential items missed      │
│    in Part 1? Did ORBIT omit critical items identified in Part 1?     │
│ 5. Audit Challenge: Participant selects 2 findings and attempts to     │
│    verify their truth using ORBIT's raw evidence links.                │
├────────────────────────────────────────────────────────────────────────┤
│ PART 3: STRUCTURED POST-SESSION RUBRIC (15 minutes)                    │
│ 1. Quantitative Likert scoring across all 7 utility dimensions.        │
│ 2. Qualitative debrief on decision impact and repeat willingness.      │
└────────────────────────────────────────────────────────────────────────┘
```

### 13.3 Bias & Observer Controls
1. **Order Control / Blinding:** Part 1 (unaided) MUST strictly precede Part 2 (aided). The manager must commit to their unaided agenda before seeing ORBIT's output to prevent hindsight bias.
2. **Non-Leading Facilitation:** Observers must not defend ORBIT findings, explain why an invariant exists, or prompt the manager toward positive ratings. If an EM calls a finding "useless noise," it is logged as noise.
3. **No Synthetic Personas:** Testing is strictly restricted to real human practitioners operating on real historical or current project evidence. Synthetic agents, simulated managers, and LLM roleplay are strictly prohibited.

---

## 14. Track A: Engineering Qualification Methodology

`[PROPOSED METHODOLOGY]`

### 14.1 Review Generation Pipeline Specification
Track A qualifies the software pipeline that transforms a validated `EvidenceBundle` into an authoritative `WeeklyReviewArtifact`:

```python
# Specification Signature
def generate_weekly_review_artifact(
    bundle: EvidenceBundle,
    template_config: ReviewTemplateConfig,
) -> WeeklyReviewArtifact:
    """
    Deterministically transforms a validated EvidenceBundle into a structured
    WeeklyReviewArtifact compliant with SPEC-PHASE-4F-01.

    Invariants Enforced:
    1. Zero inference: All metrics and findings derive strictly from bundle.
    2. Strict provenance: Every finding links to an explicit EntityRef.
    3. Permutation invariance: Input collection ordering does not alter output.
    4. Deterministic text: Serialized output produces identical SHA-256 digests.
    """
```

### 14.2 Engineering Proving Tests
1. **Schema Compliance:** The generated artifact parses cleanly against the formal `WeeklyReviewArtifact` JSON Schema.
2. **Permutation Determinism:** Shuffling the observations, relationships, and findings in the source `EvidenceBundle` across 5 randomized trials produces byte-identical rendered Markdown text.
3. **Zero Phantom Findings:** The review artifact contains zero findings that are not explicitly present in `bundle.findings`.
4. **Audit Traceability:** 100% of findings rendered in the Markdown output embed valid HTML/Markdown links referencing raw source evidence records.
5. **Execution Latency:** Generating the review artifact for an enterprise-scale cohort (100 issues, 200 PRs, 50 relationships) takes $< 1.5$ seconds on standard hardware.

---

## 15. Candidate Phase 4F Proving Gates

`[PROPOSED METHODOLOGY]` Phase 4F defines five rigorous, falsifiable qualification gates:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                     PHASE 4F QUALIFICATION GATES                       │
├────────────────────────────────────────────────────────────────────────┤
│ Gate 4F-01: Review Generation & Deterministic Integrity (Track A)      │
│   → Can ORBIT deterministically generate schema-compliant review      │
│     artifacts from authoritative multi-system evidence?                │
├────────────────────────────────────────────────────────────────────────┤
│ Gate 4F-02: Managerial Saliency & Signal Quality (Track B)             │
│   → Do managers confirm that surfaced findings represent genuine,      │
│     consequential operational issues rather than noise?                │
├────────────────────────────────────────────────────────────────────────┤
│ Gate 4F-03: Evidence Trust & Verification Speed (Track B)              │
│   → Can managers rapidly inspect and defend surfaced findings to       │
│     peers and leadership using raw cryptographic evidence links?       │
├────────────────────────────────────────────────────────────────────────┤
│ Gate 4F-04: Preparation Efficiency & Decision Impact (Track B)         │
│   → Does the artifact measurably reduce prep time and directly trigger │
│     actionable managerial decisions and carry-forward commitments?     │
├────────────────────────────────────────────────────────────────────────┤
│ Gate 4F-05: Product-Wedge Viability & Falsification (Synthesis)        │
│   → Does the evidence justify commercial productization of the EWR,   │
│     or does it conclusively falsify the initial wedge hypothesis?      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Detailed Gate Evidence & Acceptance Criteria

### Gate 4F-01 — Review Generation & Deterministic Integrity (Track A)
- `[PROPOSED METHODOLOGY]` **Hypothesis:** The ORBIT evidence foundation can deterministically synthesize multi-system evidence into a fully formatted, schema-compliant weekly review artifact.
- **Evidence Required:**
  - Automated test suite executing artifact generation across authentic multi-project fixtures (GoGreen, Apache Mahout, Apache Flink).
  - Schema validation logs, 5-way permutation SHA-256 hashes, execution benchmark traces.
- **Measurement Method:** Automated pytest suite executing in CI.
- **Acceptance Criteria (PASS):**
  - 100% valid JSON schema validation.
  - 5-way randomized sequence permutation produces 100% identical SHA-256 rendered digests.
  - 100% of surfaced findings cite existing, valid `EntityRef` targets.
  - Pipeline execution latency $\le 2.0$ seconds.
- **Failure Interpretation:** Pipeline cannot reliably or deterministically represent evidence as a human document; Track A fails.

### Gate 4F-02 — Managerial Saliency & Signal Quality (Track B)
- `[PROPOSED METHODOLOGY]` **Hypothesis:** ORBIT's deterministic cross-system rules (`XB-01..03`) identify consequential operational discrepancies that managers agree warrant review attention.
- **Evidence Required:**
  - Evaluated finding matrices from 3–5 independent EM validation sessions.
  - Quantitative classification of every surfaced item as `Actionable`, `Known/Accepted`, or `Noise`.
- **Measurement Method:** Structured interview rubric and precision calculation ($P = \frac{\text{Actionable}}{\text{Total Surfaced}}$).
- **Acceptance Criteria (PASS):**
  - Precision $P \ge 70\%$ across the participant cohort.
  - Less than $30\%$ of surfaced findings classified as irrelevant noise.
  - At least 1 previously unobserved high-consequence delivery blind spot identified per participant.
- **Failure Interpretation:** The rule engine detects technical edge cases that human managers do not care about. Findings are dismissed as pedantic noise.

### Gate 4F-03 — Evidence Trust & Verification Speed (Track B)
- `[PROPOSED METHODOLOGY]` **Hypothesis:** EMs can independently verify and defend ORBIT findings because provenance links directly to authentic raw source fields.
- **Evidence Required:**
  - Timestamped screen recordings / observer logs of live audit challenges where the manager verifies 2 random findings down to the raw Jira / GitHub record.
  - Post-session trust survey scores (1–5 scale).
- **Measurement Method:** Time-to-verify measurement (seconds) and qualitative trust rating.
- **Acceptance Criteria (PASS):**
  - 100% of challenged findings successfully verified to raw source data.
  - Mean time-to-verify $\le 45$ seconds per finding.
  - Mean evidence trust score $\ge 4.0$ out of 5.0.
  - Zero unverified or disputed claims.
- **Failure Interpretation:** The evidence chain is too complex or opaque for managers to trust under real operating conditions; auditability fails.

### Gate 4F-04 — Preparation Efficiency & Decision Impact (Track B)
- `[PROPOSED METHODOLOGY]` **Hypothesis:** ORBIT reduces manual review preparation time while directly driving actionable managerial decisions.
- **Evidence Required:**
  - Measured preparation time comparison logs (Part 1 baseline vs. Part 2 ORBIT).
  - Documented managerial decisions, escalations, or task assignments directly triggered by review findings.
- **Measurement Method:** Time difference ($\Delta T = \frac{T_{\text{baseline}} - T_{\text{orbit}}}{T_{\text{baseline}}}$) and logged decision count.
- **Acceptance Criteria (PASS):**
  - Preparation time reduction $\Delta T \ge 40\%$ (e.g., from 90 minutes to $\le 54$ minutes).
  - At least 2 concrete managerial decisions / follow-up commitments recorded per session.
  - Participant confirms that the resulting review agenda is complete and operational.
- **Failure Interpretation:** Reviewing ORBIT's output takes as long as manual compilation, or output is purely informational and prompts no action.

### Gate 4F-05 — Product-Wedge Viability & Falsification (Synthesis)
- `[PROPOSED METHODOLOGY]` **Hypothesis:** The Engineering Weekly Review provides sufficient standalone commercial value to serve as ORBIT's initial v0 product wedge.
- **Evidence Required:**
  - Synthesized cohort evaluation report.
  - Qualitative answers to commercial intent questions:
    - *"Would you use this artifact in your actual team review next week?"*
    - *"Would you grant read-only Jira/GitHub API access to run this continuously?"*
    - *"What would you pay, or sponsor budget for, to eliminate this manual workflow?"*
- **Measurement Method:** Structured synthesis scoring by founders / core team against falsification criteria.
- **Acceptance Criteria (PASS):**
  - At least 3 of 4 participants state they would use the artifact in their live weekly review.
  - At least 2 participants request an ongoing trial or continuous pilot over their live repositories.
  - Zero participants report that the weekly review is an irrelevant operating cadence.
- **Failure Interpretation:** The weekly review is not a sufficiently painful or urgent problem. The wedge is falsified and must pivot.

---

## 17. Explicit Failure Criteria

`[PROPOSED METHODOLOGY]` Any of the following empirical outcomes constitutes an immediate **FAILURE** of the corresponding gate and blocks productization:

1. **Gate 4F-01 Fail:** Rendered Markdown text differs across randomized permutation trials, or generation fails schema validation.
2. **Gate 4F-02 Fail:** Noise rate exceeds 40% (managers dismiss more than 4 in 10 findings as irrelevant or trivial).
3. **Gate 4F-03 Fail:** A manager cannot verify a finding from the provided provenance links within 3 minutes, or identifies a hallucinated/ungrounded claim.
4. **Gate 4F-04 Fail:** Time savings is less than 20%, or managers state that ORBIT output requires full manual re-verification.
5. **Gate 4F-05 Fail:** Participants reject the review artifact in favor of their existing Jira board or Confluence template.

---

## 18. Bias & Confounder Controls

`[PROPOSED METHODOLOGY]`

| Confounder / Bias | Risk Description | Control Mechanism in Phase 4F |
|---|---|---|
| **Novelty Bias** | Managers praise the tool because it is new, AI-associated, or novel, rather than genuinely useful. | Ground testing in real, messy historical project data; demand concrete decision identification rather than aesthetic ratings. |
| **Hawthorne Effect** | Managers perform better review preparation simply because they are being observed by researchers. | Unaided baseline (Part 1) and aided session (Part 2) are conducted under identical observation conditions. |
| **Leading Questions** | Interviewers inadvertently steer the manager toward agreeing with ORBIT's findings. | Observers follow strict scripted protocols; unaided agenda drafting strictly precedes exposure to ORBIT artifacts. |
| **Declarative Inflation** | Recording that an invariant or finding occurred merely because it was expected (the Phase 4E-C flaw). | All qualitative claims must cite transcribed participant quotes; all quantitative claims must cite timestamped logs. |
| **Data Cherry-Picking** | Testing only on pristine, well-maintained repositories where Jira keys perfectly match PR titles. | Mandatory testing on messy commercial data (e.g., GoGreen with 237 branches, unmapped statuses, sparse changelogs). |

---

## 19. AI Boundary & Downstream Narration Protocol

`[CANONICAL FACT]` Phase 4F strictly maintains the intelligence boundary established in `S-007` and Context Section 14G.5:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                       ORBIT INTELLIGENCE PIPELINE                      │
├────────────────────────────────────────────────────────────────────────┤
│ 1. AUTHORITATIVE OPERATIONAL SYSTEMS (Jira, GitHub, Git)               │
│    - Read-only capture, cryptographic hashing, cutoff boundary         │
├────────────────────────────────────────────────────────────────────────┤
│ 2. DETERMINISTIC CORE PIPELINE (Shadow ORBIT)                         │
│    - Normalization → EvidenceAssembly → Conservative Evaluator         │
│    - Pure functions: Zero ML, zero LLM, 100% deterministic rules       │
│    - Emits: Formally verified EvidenceBundle + Findings                │
├────────────────────────────────────────────────────────────────────────┤
│ 3. STRUCTURED FACT PACKET GENERATION (Track A)                         │
│    - Curated, tenant-isolated JSON containing verified claims          │
├────────────────────────────────────────────────────────────────────────┤
│ 4. OPTIONAL DOWNSTREAM NARRATION LAYER (EXPERIMENTAL ONLY)             │
│    - Input: Curated Fact Packet ONLY (never raw API streams)           │
│    - Model: Replaceable external LLM adapter (e.g., Claude, Gemini)    │
│    - Constraint: Claim-level support links back to Finding IDs         │
│    - Verification: Deterministic assertion engine checks numbers/dates │
├────────────────────────────────────────────────────────────────────────┤
│ 5. HUMAN MANAGER REVIEW & AUTHORIZATION                                │
│    - Human reviews verified facts + optional narration                │
└────────────────────────────────────────────────────────────────────────┘
```

### Strict Anti-Hallucination Constraints
- **No Uncited Facts:** An LLM may not introduce dates, ticket counts, developer names, or status assertions that do not exist in the structured fact packet.
- **Fail-Closed Verification:** If the downstream narration layer asserts a metric that contradicts the deterministic calculation, the narrative is rejected and pure deterministic Markdown is rendered.
- **AI Is Optional:** Phase 4F must achieve its utility pass criteria **without requiring an LLM**. Narration is evaluated strictly as a secondary enhancement.

---

## 20. Data, Security & Privacy Considerations

`[CANONICAL FACT]` All Phase 4F qualification activities must strictly adhere to the system security architecture established in `S-033`:

1. **Read-Only Ingestion:** All access to Jira Cloud and GitHub is strictly read-only. No write tokens, webhooks with modify permissions, or state-altering API scopes.
2. **Milestone 2A Line 79 Compliance:** Raw REST HTTP responses containing unvetted customer payloads are not persisted to unencrypted disk (`qualification/config.py`).
3. **Tenant & Project Scoping:** In multi-project evaluations, evidence bundles must remain strictly isolated by `source_kind:instance_id:project_id` to prevent cross-tenant leakage.
4. **Customer Data Hygiene:** If external participant repositories are ingested for Track B validation, credentials must use ephemeral, read-only personal access tokens (PATs) that are wiped immediately post-evaluation.
5. **No Third-Party Model Training:** Customer operational evidence must never be transmitted to public LLM endpoints that retain data for model training.

---

## 21. Engineering vs Customer Evidence Separation

`[PROPOSED METHODOLOGY]` To preserve absolute forensic clarity in reporting, Phase 4F results will be reported in two distinct, non-interchangeable evidence files:

### Track A Evidence Document: `qualification/phase4f/engineering_evidence.json`
- Contains: Unit test execution traces, JSON schema validation results, permutation hash matrices, execution latency benchmarks, and formal invariant checks.
- Epistemic Status: `[OBSERVED ENGINEERING EVIDENCE]`.

### Track B Evidence Document: `qualification/phase4f/customer_validation_records.json`
- Contains: Participant profiles, timestamped preparation logs, unaided vs. aided comparison tables, precision calculations, audit challenge transcripts, and qualitative survey rubrics.
- Epistemic Status: `[CUSTOMER-VALIDATED EVIDENCE]`.

Neither document may cite the other as proof of its own domain. Engineering correctness cannot prove customer delight; customer enthusiasm cannot prove cryptographic determinism.

---

## 22. Stop & Fail Conditions (Wedge Falsification)

`[PROPOSED METHODOLOGY]` A core requirement of scientific inquiry is the willingness to falsify the hypothesis. Phase 4F specifies explicit conditions under which ORBIT must **HALT** productization of the Engineering Weekly Review:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   STOP / WEDGE FALSIFICATION CONDITIONS                │
├────────────────────────────────────────────────────────────────────────┤
│ 1. THE NOISE BARRIER (Saliency Falsification)                          │
│    - Over 40% of surfaced findings are dismissed as irrelevant.       │
│    - Managers report: "This is telling me things I don't care about."  │
│    → ACTION: Halt EWR build; re-evaluate whether cross-system rules    │
│      belong in an audit/compliance tool rather than a weekly review.   │
├────────────────────────────────────────────────────────────────────────┤
│ 2. THE EFFICIENCY PARADOX (Workflow Falsification)                     │
│    - Reviewing and verifying ORBIT findings takes longer than the      │
│      manager's existing manual preparation.                            │
│    → ACTION: Falsify "prepares itself" promise; investigate whether    │
│      continuous push alerts (Slack) are required instead of review doc.│
├────────────────────────────────────────────────────────────────────────┤
│ 3. THE DISCONNECT TRAP (Decision Falsification)                        │
│    - Managers acknowledge findings as accurate, but take zero action   │
│      or decisions as a result.                                         │
│    → ACTION: Falsify EWR as an execution driver; investigate whether   │
│      the true customer is executive leadership (VP/CTO) rather than EM.│
├────────────────────────────────────────────────────────────────────────┤
│ 4. THE TRUST DEFICIT (Explainability Falsification)                    │
│    - Managers refuse to present findings to their teams because they   │
│      cannot quickly understand or defend how ORBIT derived them.       │
│    → ACTION: Halt productization; redesign provenance visualization.   │
└────────────────────────────────────────────────────────────────────────┘
```

If any two stop conditions are met, the Engineering Weekly Review product wedge is considered **FALSIFIED**, and the project team must convene a formal strategy review before writing further code.

---

## 23. Required Qualification Artifacts

`[PROPOSED METHODOLOGY]` Upon execution, Phase 4F must generate the following complete set of machine-readable artifacts under `qualification/phase4f/`:

```text
qualification/phase4f/
├── qualification_manifest.json          # Overall phase metadata, gate verdicts, participant count
├── review_artifact_schema.json          # Formal JSON Schema for WeeklyReviewArtifact
├── golden_review_artifact.md            # Reference rendered markdown review artifact
├── golden_review_artifact.json          # Reference serialized JSON review artifact
├── engineering_evidence.json            # Track A deterministic proving logs and benchmarks
├── customer_validation_records.json     # Track B participant sessions, scores, and classifications
├── unaided_vs_aided_matrix.json         # Direct item-by-item comparison of human vs ORBIT agendas
├── decision_impact_log.json             # Concrete managerial decisions prompted by review
├── determinism_permutation_trials.json  # 5-way sequence permutation byte-identity proofs
└── phase4f_qualification_report.md      # Comprehensive forensic qualification report
```

---

## 24. Reporting Format

`[PROPOSED METHODOLOGY]` The final qualification report must be delivered as:

```text
docs/pass5/phase4f_managerial_utility_report.md
```

It must follow the strict 10-section structure established across Pass 5:
1. Executive Summary & Core Proving Question Answer
2. Governance & Lineage Reconciliation
3. Track A: Engineering Proving Results (Gates 4F-01)
4. Track B: Customer Validation Results (Gates 4F-02 through 4F-04)
5. Saliency & Noise Analysis (Precision metrics, false-positive breakdown)
6. Decision Impact & Follow-Up Case Studies
7. Unaided vs. Aided Delivery Blind-Spot Findings
8. Wedge Viability Synthesis & Falsification Audit (Gate 4F-05)
9. Known Limitations & Threat Model Review
10. Final Phase Verdict & Next Authorized Stage

---

## 25. Governance & Decision Implications

- `[CANONICAL FACT]` **Decision Ceiling Preservation:** `S-034` remains the latest locked architectural decision. Phase 4F qualification does NOT create decision `S-035`.
- `[PROPOSED METHODOLOGY]` **Decision Gate Trigger:** If Phase 4F results demonstrate that:
  - The EWR is validated $\rightarrow$ Propose `S-035 (Engineering Weekly Review Product Freeze & Pilot Architecture)`.
  - The EWR is falsified $\rightarrow$ Propose `S-035 (Product Wedge Pivot: Alternative Workflow Selection)`.
- No architectural changes or product pivots may occur without a formal, reviewed ADR.

---

## 26. Explicit Authorization Boundary

```text
══════════════════════════════════════════════════════════════════════════════
                      AUTHORIZATION GATE: STRICT FREEZE
══════════════════════════════════════════════════════════════════════════════
THIS SPECIFICATION IS A GOVERNANCE AND METHODOLOGY PROPOSAL.
NO IMPLEMENTATION IS CURRENTLY AUTHORIZED.

PROHIBITED ACTIONS IN CURRENT TURN:
- NO production code modifications in src/shadow_orbit/
- NO test implementations in tests/
- NO qualification script generation in qualification/phase4f/
- NO customer interviews conducted under false authority
- NO synthetic customer evidence manufactured

NEXT REQUIRED STEP:
Review this proving specification, confirm experimental protocols and
acceptance thresholds, and issue formal authorization before implementation.
══════════════════════════════════════════════════════════════════════════════
```
