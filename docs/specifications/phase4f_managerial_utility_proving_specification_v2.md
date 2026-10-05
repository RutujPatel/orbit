# Project ORBIT — Phase 4F Proving Specification (v2)
## Managerial Utility & Product-Wedge Qualification

**Document ID:** `SPEC-PHASE-4F-02` (Reconciled Version 2)
**Supersedes:** `SPEC-PHASE-4F-01` (Preserved in repository for auditability)
**Governing Review:** `AUDIT-SPEC-4F-01` (`docs/pass5/phase4f_specification_review.md`)
**Phase:** Phase 4F — Managerial Utility / Product-Wedge Qualification
**Status:** **RECONCILED PROPOSAL — AWAITING FORMAL IMPLEMENTATION AUTHORIZATION**
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

To ensure forensic rigor, every major proposition, requirement, and observation in this specification is explicitly classified using the following seven epistemic categories:

- `[CANONICAL FACT]`: Established, locked project decisions (S-001 through S-034) and authoritative baseline contracts.
- `[OBSERVED ENGINEERING EVIDENCE]`: Direct, cryptographically verified empirical results from tests, fixtures, and code executions in the repository.
- `[CUSTOMER-VALIDATED EVIDENCE]`: Direct observations, quotes, and workflow demonstrations from real human practitioners (e.g., GoGreen Engineering Manager discovery).
- `[SUPPORTED HYPOTHESIS]`: Hypotheses backed by multiple converging signals or adjacent-market evidence, but not yet formally validated as market-wide truths.
- `[UNVALIDATED HYPOTHESIS]`: Product, behavioral, or commercial assumptions that require empirical qualification in Phase 4F.
- `[PROPOSED METHODOLOGY]`: The experimental protocols, measurement criteria, and testing procedures defined in this specification.
- `[OPEN QUESTION]`: Explicitly acknowledged unknowns that must be investigated and answered through Phase 4F qualification.

---

## 1. Purpose & Reconciled Scope

`[PROPOSED METHODOLOGY]` Phase 4F transitions Project ORBIT from **foundational semantic qualification** to **managerial utility and product-wedge qualification**.

`[OBSERVED ENGINEERING EVIDENCE]` Across Pass 4 (Waves 1–5) and Pass 5 (Phases 4D, 4E-A, 4E-B, 4E-C, and 4E-D), ORBIT conclusively proved that its evidence pipeline can ingest, normalize, assemble, and evaluate heterogeneous Jira and GitHub evidence while strictly preserving identity, linkage, state, temporal ordering, and graph firewalls.

`[CANONICAL FACT]` However, technical correctness is not customer value. As established in Decision `S-006` and Canonical Context Section 14F, ORBIT is built to serve a specific human customer: the **Engineering Manager / Delivery Manager**.

`[PROPOSED METHODOLOGY]` Phase 4F will determine whether the verified evidence foundation produces materially useful managerial understanding and decisions, or whether the current product wedge fails to deliver sufficient customer utility. Phase 4F is an experimental proving gate designed to validate or falsify the v0 product wedge before authorizing productization.

### Key Version 2 Reconciliations (Post-Audit)
Following the forensic review in `AUDIT-SPEC-4F-01`, this v2 specification resolves four major methodological defects:
1. **De-arbitrated Thresholds:** Arbitrary hard thresholds have been de-escalated to pre-registered targets with explicit rationale.
2. **Measured Participant Baselines:** Replaced presumptive 3–5 hour industry timing with mandatory measurement of each participant's actual baseline workflow.
3. **Two-Stage Experimental Protocol:** Decoupled blind-spot discovery from preparation efficiency to eliminate the learning/familiarity confound.
4. **Structured Decision & Saliency Matrices:** Replaced raw decision counts and binary blind-spot metrics with stratified impact hierarchies.

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
- `[SUPPORTED HYPOTHESIS]` In growth-stage engineering organizations (20–150 employees, `S-002`), Engineering Managers and Delivery Managers spend substantial manual effort preparing for recurring weekly engineering reviews.
- `[CUSTOMER-VALIDATED EVIDENCE]` This preparation involves manually collating Jira sprint boards, inspecting GitHub pull request activity, querying developers on Slack, and reconciling discrepancies between nominal ticket status and physical code changes.
- `[CUSTOMER-VALIDATED EVIDENCE]` Despite this manual effort, reviews remain vulnerable to high-consequence blind spots:
  1. Work items marked `Done` in Jira whose corresponding GitHub PRs were never merged or closed without shipping (`ORBIT-XB-01`).
  2. Code merged into production branches without an associated or resolved Jira ticket, creating untracked scope creep and unreviewed delivery commitments (`ORBIT-XB-02`).
  3. Work items closed weeks before code changes merge, representing observational lag, unverified handoffs, or premature administrative sign-offs (`ORBIT-XB-03`).
  4. Chronic, recurring problems in business-critical operational domains (e.g., billing, service contracts) that are repeatedly handled as isolated tickets rather than recognized as organizational patterns.
- `[UNVALIDATED HYPOTHESIS]` An automated, evidence-backed review preparation engine will reduce weekly preparation time, eliminate cross-system delivery blind spots, and improve the consistency and follow-through of managerial commitments.

---

## 4. Core Proving Question

The central question that Phase 4F must answer is:

> **Does the verified ORBIT evidence foundation materially improve the Engineering Weekly Review for an Engineering / Delivery Manager?**

This breaks down into five sub-questions:
1. **Preparation Efficiency:** Does ORBIT measurably reduce the manual time and friction required to prepare an accurate operating review when evaluated against an independent baseline?
2. **Signal Saliency:** Does ORBIT surface items that managers agree genuinely require operational attention, while keeping irrelevant noise low?
3. **Evidence Trust:** Can a manager verify, understand, and defend every surfaced finding directly from raw source evidence without algorithmic opacity?
4. **Decision Utility:** Does the review artifact lead to concrete, actionable managerial decisions, risk mitigations, or follow-up commitments?
5. **Wedge Viability:** Is the Engineering Weekly Review sufficiently recurring and consequential to serve as ORBIT's commercial foundation, or does evidence dictate an alternative product wedge?

---

## 5. Scope & Non-Goals

### 5.1 In-Scope Boundary
`[CANONICAL FACT]` Bounded strictly by existing canonical architecture and locked decisions:
1. **Target Product Wedge:** The **Engineering Weekly Review** for Engineering Managers and Delivery Managers (`S-004`, `S-006`).
2. **Core Value Promise:** *"Your weekly engineering operating review prepares itself."* (`S-006`).
3. **Evidence Sources:** Native Jira Cloud / Software work items and GitHub repository code changes / pull requests (`S-034`).
4. **Target Users:** Engineering Managers (EMs) and Delivery Managers (DMs) with direct delivery accountability.
5. **Operating Cycles:** Weekly operating reviews and bi-weekly sprint boundaries.
6. **Delivery Artifact:** A structured, deterministic, human-readable review document (Markdown / JSON).

### 5.2 Strict Non-Goals
`[CANONICAL FACT]` Explicitly excluded:
1. **No Production Code Modifications:** `src/shadow_orbit/` remains strictly frozen under semantic baseline `6d82d12`.
2. **No Connector Expansion:** No third-party connectors for Slack, Teams, Salesforce, SAP, Linear, or GitLab (`S-003`).
3. **No Autonomous Actions or Write-Back:** ORBIT remains strictly read-only; no writing back to Jira or GitHub (`S-008`).
4. **No Generic Enterprise Search:** No implementation of unstructured organizational search or indexing (`S-004`).
5. **No Automated Employee Performance Evaluation:** ORBIT evaluates cross-system work-state integrity, not developer competence or speed (`14G.18`).
6. **No LLM Source-of-Truth:** LLMs are strictly forbidden from calculating metrics or manufacturing findings (`S-007`).
7. **No Broad Stage 2/3/4 Capabilities:** No expansion into universal workflow engines or multi-department orchestration (`S-005`).

---

## 6. Existing Evidence & Forensic Reclassification

### 6.1 Canonical Governance & Engineering State
- `[CANONICAL FACT]` `S-001..S-008`, `S-034`: Locked product wedge, deterministic intelligence, hybrid ownership, and Jira + GitHub scope.
- `[OBSERVED ENGINEERING EVIDENCE]` **913 Automated Tests & 24 Formal Invariants PROVEN:** Cryptographic fixture provenance (100% on-disk match) and 5-way sequence permutation determinism.

### 6.2 Customer Discovery Evidence Audit (Epistemic Hygiene)
- `[CUSTOMER-VALIDATED EVIDENCE]` **GoGreen EM Discovery (Samyak, Context 14G.15–14G.17):**
  - *Status $\neq$ Attention:* Semantically blocked tickets (e.g., `Waiting for Additional Information`) do not automatically require review discussion. `In Review` represents client testing on staging.
  - *Priority $\neq$ Urgency:* `Highest` Jira priority is frequently overridden by verbal/email client direction.
  - *Recurrence Over Individual Status:* The manager independently prioritized tickets in **billing, service contracts, and insurance** because they occur repeatedly and represent client-critical friction. The core need is: *"Reveal what keeps happening that should not keep happening."*
  - *Data Reality:* Commercial Jira data exhibits missing due dates, sparse changelogs, unmapped statuses, and sparse GitHub PR links.
- `[SUPPORTED HYPOTHESIS]` **Adjacent Market & Discovery Signals (Context 14G.1, 14G.18):**
  - Review preparation consumes 0.5 to 1.0 days/week across multiple organizations.
  - Practitioners using Copilot/Claude report that LLM outputs require mandatory manual checking.
  - Cross-system reconstruction is manually intensive during audits and handoffs.
- `[UNVALIDATED HYPOTHESIS]` **Baseline Workflow Timings:**
  - The previously asserted breakdown (Jira 60–90m, GH 45–75m, Slack 30–60m, Report 45–60m) is **downgraded** from fact to `[UNVALIDATED HYPOTHESIS]`. It must be measured empirically for each participant.

---

## 7. Critical Evidence Gaps

`[OPEN QUESTION]` The following product hypotheses remain entirely unevidenced:
- **GAP-01 (Relevance):** Do real EMs care about `ORBIT-XB-01`, `XB-02`, and `XB-03` findings during a weekly review, or are they viewed as administrative nitpicks?
- **GAP-02 (Efficiency):** Does ORBIT's review artifact actually save measurable preparation time in a live workflow, or does verifying ORBIT's output introduce cognitive overhead?
- **GAP-03 (Noise):** What proportion of surfaced findings are dismissed by managers as expected, acceptable, or irrelevant operational noise?
- **GAP-04 (Overlap):** How closely does an unaided human manager agenda overlap with ORBIT's deterministically surfaced findings?
- **GAP-05 (Actionability):** Does an evidence-backed review artifact change what decisions are made, or does it merely document existing status?
- **GAP-06 (Wedge Validity):** Is the Engineering Weekly Review a sufficiently painful and recurring problem to drive software adoption, or is another workflow the true commercial wedge?

---

## 8. Multidimensional Utility Model

`[PROPOSED METHODOLOGY]` Phase 4F evaluates seven explicit operational dimensions, stratified by role in qualification:

### 8.1 Primary Qualification Dimensions (Governing Gates)
1. **Dimension A: Preparation Efficiency**
   - Measured time reduction in weekly preparation effort without sacrificing operational coverage.
2. **Dimension B: Saliency & Noise Resistance**
   - High ratio of actionable operational findings versus irrelevant noise.
3. **Dimension C: Evidence Trust & Auditability**
   - Rapid, friction-free verification of findings down to raw source fields.
4. **Dimension D: Decision Impact**
   - Concrete managerial interventions, escalations, or follow-up commitments directly driven by review findings.
5. **Dimension E: Wedge Viability & Behavioral Adoption**
   - Willingness to execute live team reviews using the artifact.

### 8.2 Secondary & Descriptive Dimensions (Informational)
6. **Dimension F: Temporal Carry-Forward & Recurrence Tracking**
   - Accounting for prior commitments across review boundaries.
7. **Dimension G: Cognitive Burden & Usability**
   - Qualitative cognitive fatigue rating.

---

## 9. Reconciled Measurement Baselines

`[PROPOSED METHODOLOGY]` To prevent distorted preparation savings claims, Phase 4F institutes **mandatory participant-specific baseline measurement**.

### 9.1 Decomposed Effort Model
For each participant $i$, effort is measured across four distinct components:
- $T_{\text{discovery}}^{(i)}$: Time spent searching, filtering, and cross-referencing Jira, GitHub, Slack, and asking engineers.
- $T_{\text{synthesis}}^{(i)}$: Time spent compiling, formatting, and drafting the agenda or notes.
- $T_{\text{orbit\_verify}}^{(i)}$: Time spent auditing and checking the claims in ORBIT's pre-generated artifact.
- $T_{\text{orbit\_review}}^{(i)}$: Time spent reading, contextualizing, and using ORBIT's artifact to conduct the review.

### 9.2 Measured Baseline vs. Measured ORBIT Effort
The participant's actual baseline preparation time is measured over an unassisted review cycle:
$$T_{\text{baseline}}^{(i)} = T_{\text{discovery}}^{(i)} + T_{\text{synthesis}}^{(i)}$$

Total ORBIT preparation time is measured when ORBIT's artifact is provided as the starting point:
$$T_{\text{orbit\_total}}^{(i)} = T_{\text{orbit\_verify}}^{(i)} + T_{\text{orbit\_review}}^{(i)}$$

The true preparation efficiency delta is:
$$\Delta T^{(i)} = \frac{T_{\text{baseline}}^{(i)} - T_{\text{orbit\_total}}^{(i)}}{T_{\text{baseline}}^{(i)}}$$

---

## 10. Reconciled Two-Stage Experimental Protocol

`[PROPOSED METHODOLOGY]` To resolve the learning/familiarity confound identified in review `AUDIT-SPEC-4F-01`, Phase 4F decouples evaluation into two distinct stages across two review cycles:

```text
┌────────────────────────────────────────────────────────────────────────┐
│               PHASE 4F TWO-STAGE EXPERIMENTAL PROTOCOL                 │
├────────────────────────────────────────────────────────────────────────┤
│ STAGE 1: HISTORICAL CROSS-SECTIONAL AUDIT (Review Period N-1)          │
│ Focus: Saliency, Trust, and Blind-Spot Discovery                       │
│                                                                        │
│ Step 1.1 (Unaided Baseline): Manager independently drafts their review │
│             agenda for period N-1 using existing tools/notes (logged). │
│ Step 1.2 (Aided Inspection): Manager inspects ORBIT artifact for N-1.  │
│ Step 1.3 (Blind-Spot Audit): Discrepancies mapped against the Saliency │
│             & Awareness Matrix (Categories A through F).               │
│ Step 1.4 (Trust Audit): Manager challenges 2 findings; time to verify  │
│             down to raw source fields is measured.                     │
│ Note: Effort in Step 1.2 is explicitly logged as VERIFICATION ONLY.   │
├────────────────────────────────────────────────────────────────────────┤
│ STAGE 2: PROSPECTIVE IN-SITU WORKFLOW TRIAL (Live Review Period N)     │
│ Focus: Preparation Efficiency & Live Decision Impact                   │
│                                                                        │
│ Step 2.1: Prior to the manager's normal weekly preparation window,     │
│           ORBIT automatically generates the artifact for Period N.     │
│ Step 2.2: Manager uses ORBIT artifact as their primary starting point. │
│ Step 2.3: Observer logs exact elapsed time: T_orbit_verify and         │
│           T_orbit_review (T_orbit_total).                              │
│ Step 2.4: Compare T_orbit_total directly against measured T_baseline.  │
│ Step 2.5: Manager conducts live team review using the artifact;        │
│           concrete decisions and actions are logged and classified.    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Stratified Saliency & Decision Impact Matrices

### 11.1 Saliency & Awareness Matrix (Blind-Spot Classification)
`[PROPOSED METHODOLOGY]` Replaces the binary "previously unobserved" classification:

| Category | Designation | Operational Definition | Evidentiary Significance |
|---|---|---|---|
| **Cat A** | **Known & Prioritized** | Manager was fully aware and had it on their unaided agenda. | Baseline validation; confirms ORBIT surfaces core work. |
| **Cat B** | **Known but Omitted** | Manager was aware, but forgot or omitted it from the agenda. | **Moderate Value:** Proves cognitive offloading / safety net. |
| **Cat C** | **Known & Deprioritized** | Manager was aware, but intentionally chose not to discuss it. | Contextual Noise: Indicates need for attention tuning. |
| **Cat D** | **New Context** | Discrepancy unknown to manager, but requires no intervention. | Informational Context. |
| **Cat E** | **New Actionable Issue** | Manager was unaware; upon seeing evidence, opens investigation. | **High Value:** Directly uncovers unevidenced work or drift. |
| **Cat F** | **Consequential Blind Spot** | Critical cross-system conflict altering delivery health. | **Maximum Value:** Definitive proof of cross-system utility. |

### 11.2 Managerial Action Impact Hierarchy
`[PROPOSED METHODOLOGY]` Replaces the crude "$\ge 2$ decisions per session" count:

- **Level 5: Consequential Course Correction:** Exposed a critical delivery blocker, scope creep, or invalid status that altered team allocation, sprint commitments, or release plans.
- **Level 4: New Action / Follow-Up Created:** Prompted a new operational follow-up task, escalation, or specific assignee commitment.
- **Level 3: Existing Decision Strengthened / Accelerated:** Evidence removed ambiguity, enabling immediate executive resolution of a pending debate.
- **Level 2: Detail Sharpened / Contextualized:** Existing agenda item corrected with exact PR link, commit timestamp, or dependency context.
- **Level 1: Operational State Confirmed:** Verified known status with zero cognitive friction; zero change to decisions.
- **Level 0: No Impact / Ignored:** Finding dismissed as irrelevant, pedantic, or unhelpful noise.

---

## 12. Behavioral Evidence Ladder (Product-Wedge Validation)

`[PROPOSED METHODOLOGY]` To prevent stated intent from masquerading as commercial validation, Gate 4F-05 enforces the Behavioral Evidence Ladder:

```text
Level 5: Multi-Cycle Retention
         (Participant voluntarily uses ORBIT across 2+ consecutive live reviews)
   ▲
   │
Level 4: Live Review Execution
         (Participant conducts their actual team operating review using the ORBIT artifact)
   ▲
   │
Level 3: Trial Authorization
         (Participant authorizes continuous read-only API access to run ORBIT on their repos)
   ▲
   │
Level 2: Stated Intent
         (Participant states in an interview: "I would use this next week")
   ▲
   │
Level 1: Aesthetic Approval
         (Participant states: "This looks cool / I like the concept")
```

- **Qualification Standard:** Level 3 (Trial Authorization) and Level 4 (Live Review Execution) are required to pass Gate 4F-05.
- Level 1 and Level 2 are classified strictly as `[SUPPORTED HYPOTHESIS]` and are insufficient to close the gate.

---

## 13. Reconciled Threshold Framework

`[PROPOSED METHODOLOGY]` The quantitative thresholds governing Phase 4F are explicitly partitioned:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   PHASE 4F RECONCILED THRESHOLDS                       │
├───────────────────────────────────┬────────────────────────────────────┤
│ PRE-REGISTERED TARGETS            │ FAIL-CLOSED BOUNDARIES (HARD GATES)│
├───────────────────────────────────┼────────────────────────────────────┤
│ - Prep Time Reduction:            │ - Prep Time Regression:            │
│   Cohort Median ΔT ≥ 35%          │   Cohort Median ΔT ≤ 0%            │
│ - Finding Precision: P ≥ 70%      │ - Excessive Noise: Noise > 50%     │
│ - Trust Score: ≥ 4.0 / 5.0        │ - Provenance Failure: > 0 unproven │
│ - Decision Impact: Level ≥ 4      │ - Decision Impact: 100% Level 0    │
│ - Live Adoption: ≥ 2 EMs execute  │ - Rejection: 100% reject artifact  │
├───────────────────────────────────┴────────────────────────────────────┤
│ EXPLORATORY / DESCRIPTIVE METRICS (NON-BLOCKING)                       │
│ - Mean Audit Time (target ≤ 60s)   - Total raw decision count          │
│ - Category B omission frequency    - Multi-cycle retention (Level 5)   │
│ - Participant-level ΔT outlier investigations                          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Phase 4F Proving Gates & Acceptance Criteria

### Gate 4F-01 — Review Generation & Deterministic Integrity (Track A)
- `[PROPOSED METHODOLOGY]` **Hypothesis:** Pipeline deterministically transforms an `EvidenceBundle` into a schema-compliant `WeeklyReviewArtifact`.
- **Measurement Method:** Automated CI pytest suite across authentic multi-project fixtures (GoGreen, Apache Mahout, Apache Flink).
- **Acceptance Criteria (PASS):**
  - 100% valid JSON schema parsing.
  - 5-way randomized sequence permutation produces 100% identical SHA-256 rendered digests.
  - 100% of surfaced findings cite existing, valid `EntityRef` targets.
  - Execution latency $\le 2.0$ seconds.
- **Fail-Closed Boundary:** Output permutation mismatch, schema failure, or phantom finding.

### Gate 4F-02 — Managerial Saliency & Signal Quality (Track B)
- `[PROPOSED METHODOLOGY]` **Hypothesis:** ORBIT's cross-system findings identify genuine delivery discrepancies without generating unacceptable noise.
- **Measurement Method:** Saliency & Awareness Matrix classification across 3–5 independent participant sessions.
- **Acceptance Criteria (PASS):**
  - Pre-registered target: Precision $P \ge 70\%$.
  - Mandatory minimum: Surfaced at least **one Category E or Category F item**, or at least **two Category B items** per participant.
- **Fail-Closed Boundary:** Irrelevant noise exceeds $50\%$ (more than half of findings dismissed as useless).

### Gate 4F-03 — Evidence Trust & Verification Speed (Track B)
- `[PROPOSED METHODOLOGY]` **Hypothesis:** EMs can independently verify and defend ORBIT findings using direct source links.
- **Measurement Method:** Timestamped audit challenges where participant verifies 2 random findings down to raw Jira/GitHub records.
- **Acceptance Criteria (PASS):**
  - 100% of challenged findings verified to raw source data.
  - Mean trust score $\ge 4.0 / 5.0$.
  - Exploratory target: Mean time-to-verify $\le 60$ seconds.
- **Fail-Closed Boundary:** Any finding contains ungrounded, fabricated, or unverifiable claims.

### Gate 4F-04 — Preparation Efficiency & Decision Impact (Track B)
`[PROPOSED METHODOLOGY]` Gate 4F-04 evaluates the operational value of ORBIT across two conceptually independent sub-dimensions: **Sub-Gate 4F-04A (Preparation Efficiency)** and **Sub-Gate 4F-04B (Managerial Action Impact)**. They are measured independently, then synthesized at the phase level to prevent cross-contamination.

#### Sub-Gate 4F-04A: Preparation Efficiency (Elapsed Workflow Savings)
- **Hypothesis:** ORBIT reduces net weekly preparation time for the manager cohort as a whole.
- **Measurement Method:** Decomposed $T_{\text{baseline}}$ vs. $T_{\text{orbit\_total}}$ measured across Stage 2 live trials.
- **Acceptance Criteria (PASS):**
  - **Pre-Registered Performance Target:** Cohort median preparation-efficiency improvement $\text{Median}(\Delta T) \ge 35\%$.
  - **Minimum Viability Threshold (Hard Gate):** Cohort median $\text{Median}(\Delta T) > 0\%$ (ORBIT must not increase net preparation effort for the cohort as a whole).
  - **Participant-Level Outlier Rule:** Any individual participant regression ($\Delta T^{(i)} \le 0\%$) does not automatically fail the gate, but must be explicitly investigated and classified (e.g., whether additional time was driven by productive deep investigation of a Level 5 finding vs. excessive review verification friction).
- **Fail-Closed Boundary:** Cohort median preparation time increases ($\text{Median}(\Delta T) \le 0\%$, indicating that ORBIT systematically adds net operational friction).

#### Sub-Gate 4F-04B: Managerial Action Impact (Consequential Utility)
- **Hypothesis:** Review findings directly drive consequential managerial actions, follow-ups, or risk decisions.
- **Measurement Method:** Classification of meeting outcomes against the Managerial Action Impact Hierarchy (Levels 0 through 5).
- **Acceptance Criteria (PASS):**
  - **Pre-Registered Performance Target:** At least **one Level 4 (New Action Created)** or **Level 5 (Course Correction)** impact, or at least **two Level 3 (Decision Accelerated)** impacts logged per review session.
  - **Independence from Efficiency:** Evaluated independently of preparation time. A session with $\Delta T \le 0\%$ that exposes a Level 5 critical blind spot is recognized as high-value diagnostic intervention, not an efficiency failure. Conversely, high time savings ($\Delta T > 50\%$) resulting in 100% Level 0/1 impact is classified as administrative automation without managerial utility.
- **Fail-Closed Boundary:** 100% of surfaced findings result in Level 0 (no impact, ignored, or dismissed as noise across all participants).

### Gate 4F-05 — Product-Wedge Viability & Falsification (Synthesis)
- `[PROPOSED METHODOLOGY]` **Hypothesis:** The Engineering Weekly Review provides sufficient recurring value to serve as ORBIT's commercial wedge.
- **Measurement Method:** Behavioral Evidence Ladder evaluation across the participant cohort.
- **Acceptance Criteria (PASS):**
  - At least 2 participants achieve **Level 4** (actually conduct their live weekly review using the artifact).
  - At least 3 participants achieve **Level 3** (authorize continuous trial).
  - Zero stop conditions triggered.
- **Fail-Closed Boundary:** Participants refuse to use the artifact in live operations, preferring existing manual processes.

---

## 15. Explicit Falsification & Stop Conditions

`[PROPOSED METHODOLOGY]` If any of the following four conditions occur during Phase 4F qualification, the Engineering Weekly Review wedge is declared **FALSIFIED**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   STOP / WEDGE FALSIFICATION CONDITIONS                │
├────────────────────────────────────────────────────────────────────────┤
│ 1. THE NOISE BARRIER                                                   │
│    - Irrelevant noise exceeds 50% across multiple participants.        │
│    → VERDICT: Cross-system findings are too pedantic for weekly reviews│
│      Action: Falsify EWR; evaluate compliance/audit tooling instead.   │
├────────────────────────────────────────────────────────────────────────┤
│ 2. THE EFFICIENCY PARADOX                                              │
│    - Verifying ORBIT findings takes longer than manual compilation.    │
│    → VERDICT: "Prepares itself" value proposition is false.            │
│      Action: Falsify static document wedge; investigate real-time bots.│
├────────────────────────────────────────────────────────────────────────┤
│ 3. THE DISCONNECT TRAP                                                 │
│    - Findings are acknowledged as true, but 100% result in Level 0/1   │
│      (zero decisions, zero follow-ups, zero escalations).              │
│    → VERDICT: Accurate data does not produce managerial utility.       │
│      Action: Falsify EM as buyer; investigate executive/VP reporting.  │
├────────────────────────────────────────────────────────────────────────┤
│ 4. THE TRUST DEFICIT                                                   │
│    - Managers refuse to present findings because provenance is too     │
│      complex or opaque to defend to leadership.                        │
│    → VERDICT: Evidence foundation fails human explainability.          │
│      Action: Redesign provenance representation before continuing.     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Participant Cohort Specification (Track B)

`[PROPOSED METHODOLOGY]`
- **Cohort Size:** 3 to 5 practicing Engineering Managers / Delivery Managers.
- **Organizational Stratification:**
  - *Internal Commercial SaaS:* 1–2 EMs from internal enterprise development (e.g., GoGreen WMS team at Tecblic).
  - *External Growth-Stage SaaS:* 2–3 EMs from independent growth-stage organizations (20–150 employees, matching `S-002`).
- **Prerequisites:** Must lead $\ge 4$ engineers, run recurring weekly operating reviews, and actively use Jira + GitHub.
- **Strict Prohibition:** Zero synthetic agents, zero simulated personas, zero LLM roleplay.

---

## 17. Engineering Track Boundary (Track A)

`[CANONICAL FACT]` Track A remains strictly within qualification space:
- **No changes to `src/shadow_orbit/`.**
- Review artifact generation functions reside strictly in `qualification/phase4f/artifact_generator.py`.
- Formal schema resides in `qualification/phase4f/review_artifact_schema.json`.
- Automated proving tests reside in `tests/qualification/test_phase4f_engineering_proving.py`.

---

## 18. AI Downstream Narration Protocol

`[CANONICAL FACT]`
- Facts, metrics, and findings derive 100% deterministically from `EvidenceBundle`.
- AI narration is strictly optional and downstream:
  $$\text{Verified Bundle} \longrightarrow \text{Structured Fact Packet} \longrightarrow \text{LLM Narration} \longrightarrow \text{Claim-Level Verification}$$
- The core qualification passes or fails **entirely on deterministic Markdown output**. Narration is evaluated only as an experimental add-on.

---

## 19. Required Qualification Artifacts

`[PROPOSED METHODOLOGY]` Upon execution, Phase 4F must produce:
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

## 20. Governance & Decision Boundary

- `[CANONICAL FACT]` **Decision Ceiling:** Locked at `S-034`.
- If Phase 4F passes $\rightarrow$ Propose `S-035 (Engineering Weekly Review Product Freeze & Pilot Architecture)`.
- If Phase 4F is falsified $\rightarrow$ Propose `S-035 (Product Wedge Pivot: Alternative Workflow Selection)`.
- No architectural changes or product pivots may occur without a formal, reviewed ADR.

---

## 21. Explicit Authorization Boundary

```text
══════════════════════════════════════════════════════════════════════════════
                      AUTHORIZATION GATE: STRICT FREEZE
══════════════════════════════════════════════════════════════════════════════
THIS SPECIFICATION (V2) IS A RECONCILED GOVERNANCE AND METHODOLOGY CONTRACT.
NO IMPLEMENTATION IS CURRENTLY AUTHORIZED.

PROHIBITED ACTIONS:
- NO production code modifications in src/shadow_orbit/
- NO qualification harness creation in qualification/phase4f/
- NO test implementations in tests/
- NO live participant testing initiated under false authority

NEXT REQUIRED ACTION:
Present Specification v2 and Audit Review AUDIT-SPEC-4F-01 for stakeholder
review and formal implementation authorization.
══════════════════════════════════════════════════════════════════════════════
```
