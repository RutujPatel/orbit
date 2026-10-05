# Project ORBIT — Phase 4F Specification Forensic Review
## Methodology Reconciliation & Pre-Authorization Audit

**Document ID:** `AUDIT-SPEC-4F-01`
**Review Target:** `docs/specifications/phase4f_managerial_utility_proving_specification.md` (Specification v1)
**Status:** **REVIEW COMPLETED — SPECIFICATION V2 REQUIRED**
**Date:** 2026-10-05
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)
**Current HEAD:** `1bfad1c6c81ad488fe11fa1e0a75903466cfe152` (`1bfad1c`)
**Branch:** `develop`
**Decision Ceiling:** `S-034`
**Implementation Authorization:** **NOT YET AUTHORIZED**

---

## 1. Executive Assessment

Specification v1 of Phase 4F (`SPEC-PHASE-4F-01`) successfully captures the strategic, architectural, and governance posture required for the transition from semantic proving to product-wedge qualification:
1. It correctly establishes Phase 4F as an empirical **utility qualification** rather than another infrastructure-hardening exercise.
2. It strictly enforces `S-034` by bounding evidence sources to Jira Cloud and GitHub, preserving the frozen semantic core in `src/shadow_orbit/`.
3. It mandates a dual-track experimental architecture (Track A Engineering vs. Track B Customer Validation) and prohibits synthetic personas or LLM simulations from masquerading as customer validation.
4. It places AI strictly downstream of verified deterministic facts and explicitly defines falsification conditions.

However, a forensic review reveals critical **methodological and measurement flaws** in Specification v1. Specifically, the document suffers from **premature precision**: treating exploratory targets as hard qualification thresholds, over-confidently stating baseline workflow timings from anecdotal discovery signals, and introducing a severe **learning/familiarity confound** in its comparative experimental design.

**Verdict:** **SPECIFICATION V1 REQUIRES RECONCILIATION. SPECIFICATION V2 MUST BE ADOPTED BEFORE AUTHORIZING IMPLEMENTATION.**

---

## 2. Methodology Defects Found in Specification v1

| Defect ID | Severity | Location in v1 | Core Methodological Issue |
|---|---|---|---|
| **DEF-01** | **HIGH** | Section 9, 16 (Gates 4F-02, 03, 04) | **Arbitrary Thresholds as Hard Gates:** Arbitrary targets (`\ge 40%` prep reduction, `\ge 70%` precision, `\le 45s` verification, `\ge 2` decisions/session) were declared hard PASS criteria without statistical or empirical grounding. |
| **DEF-02** | **HIGH** | Section 11 | **Over-Confident Baseline Claims:** A detailed 3–5 hour weekly preparation breakdown was labeled as `[CUSTOMER-VALIDATED EVIDENCE]` when it was derived from informal adjacent-market anecdotes rather than measured participant baselines. |
| **DEF-03** | **CRITICAL** | Section 13.2 | **Learning Confound in Comparative Protocol:** In the single-session Part 1 (unaided) $\rightarrow$ Part 2 (aided) protocol, the manager performs 30 minutes of deep discovery in Part 1. Part 2 preparation time cannot cleanly measure total savings because the manager already possesses current-state familiarity. |
| **DEF-04** | **MEDIUM** | Section 9, 16 (Gate 4F-04) | **Distortive Decision Count Metric:** "$\ge 2$ decisions per session" is an artificial requirement. A review where zero new decisions are made, 3 commitments are confirmed, and 1 risk is accepted can be highly valuable. |
| **DEF-05** | **MEDIUM** | Section 9, 16 (Gate 4F-02) | **Unstratified Blind-Spot Metric:** "Previously unobserved" is vulnerable to hindsight rationalization (*"I knew about this, I just didn't write it down"*). It failed to differentiate between forgotten items, deprioritized items, and genuine delivery blind spots. |
| **DEF-06** | **HIGH** | Section 16 (Gate 4F-05) | **Stated Intent vs. Behavioral Proof:** Gate 4F-05 evaluated commercial adoption based primarily on stated willingness (*"Would you use this next week?"*), which is notoriously weak compared to observed next-review execution. |

---

## 3. Threshold Reconciliation Table

Every quantitative threshold in Specification v1 has been audited and reconciled into one of four formal scientific categories:
- **Category A (Evidence-Backed Threshold):** Grounded in historical data or established empirical baselines.
- **Category B (Pre-Registered Experimental Target):** A defined operational goal with an explicit rationale, evaluated flexibly rather than as a brittle pass/fail binary.
- **Category C (Exploratory / Descriptive Metric):** Logged for characterization; does not govern pass/fail verdicts.
- **Category D (Unsupported / Arbitrary Threshold):** Rejected or refactored.

| Threshold in v1 | Category in v1 | Reconciled Category in v2 | Rationale & Reconciled Operational Definition in v2 |
|---|---|---|---|
| **$\ge 40\%$ Preparation Time Reduction** | Hard Gate | **Category B (Pre-Registered Target)** | Reconciled: Cohort Median $\Delta T \ge 35\%$ target; minimum viability is Cohort Median $\Delta T > 0\%$ (ORBIT must not increase effort for the cohort as a whole). Individual participant regressions are investigated and classified, eliminating brittle single-outlier failures. Decoupled into Sub-Gate 4F-04A. |
| **$\ge 70\%$ Finding Precision** | Hard Gate | **Category B (Pre-Registered Target)** | Derived from general notification-fatigue research ($<30\%$ noise). Reconciled: Evaluated as pre-registered target; hard fail-closed gate is set at noise $> 50\%$. |
| **$\le 45$ Seconds Verification Time** | Hard Gate | **Category C (Exploratory Metric)** | Arbitrary human timing heuristic. Reconciled: Track mean audit time descriptively; hard gate requires 100% of challenged findings to have verifiable provenance links. |
| **$\ge 4.0 / 5.0$ Evidence Trust Rating** | Hard Gate | **Category B (Pre-Registered Target)** | Standard Likert satisfaction threshold. Maintained as pre-registered qualitative target. |
| **$\ge 2$ Decisions / Commitments per Session** | Hard Gate | **Category D $\rightarrow$ Replaced by Category B** | Raw decision counts distort natural managerial rhythms. Replaced by the **Managerial Action Impact Hierarchy** (requiring Level $\ge 3$ impact). |
| **$\ge 3$ of 4 Participants Adopting** | Hard Gate | **Category B (Pre-Registered Target)** | High bar for initial cohort. Reconciled to require actual live trial execution rather than stated willingness. |
| **$\ge 2$ Continuous Trial Requests** | Hard Gate | **Category C (Exploratory Metric)** | Strong commercial signal, but procurement/token constraints may delay trials. Retained as commercial indicator. |

---

## 4. Baseline Correction: Measuring Real Participant Workflows

Specification v1 incorrectly stated a 3–5 hour industry workflow as an established baseline fact. In Specification v2:
1. **Epistemic Reclassification:** The 3–5 hour weekly baseline is reclassified as `[SUPPORTED HYPOTHESIS]` based on preliminary discovery conversations (Context 14G.1, 14G.18), not verified fact.
2. **Mandatory Participant Baseline Measurement:** Phase 4F must measure each individual participant's actual baseline workflow before evaluating ORBIT.
3. **Decomposed Effort Accounting:** Effort is partitioned into four distinct phases:
   - $T_{\text{discovery}}$: Time spent searching, querying, cross-checking Jira, GitHub, Slack, and asking engineers.
   - $T_{\text{synthesis}}$: Time spent assembling, formatting, and drafting the agenda or review notes.
   - $T_{\text{orbit\_verify}}$: Time spent auditing and checking the claims in ORBIT's pre-generated artifact.
   - $T_{\text{orbit\_review}}$: Time spent reading, contextualizing, and using ORBIT's artifact to conduct the review.
4. **End-to-End Preparation Calculation:**
   $$T_{\text{baseline}} = T_{\text{discovery}} + T_{\text{synthesis}}$$
   $$T_{\text{orbit\_total}} = T_{\text{orbit\_verify}} + T_{\text{orbit\_review}}$$
   $$\Delta T = \frac{T_{\text{baseline}} - T_{\text{orbit\_total}}}{T_{\text{baseline}}}$$

---

## 5. Experimental-Design Correction: Resolving the Learning Confound

The single-session design in v1 suffered from an inevitable learning confound: running Part 1 (unaided agenda drafting) for 30 minutes meant the participant had already completed the discovery phase before looking at ORBIT in Part 2. Comparing Part 1 time to Part 2 time was scientifically invalid.

Specification v2 resolves this by decoupling the testing into a **Two-Stage Hybrid Protocol**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│               PHASE 4F TWO-STAGE EXPERIMENTAL PROTOCOL                 │
├────────────────────────────────────────────────────────────────────────┤
│ STAGE 1: HISTORICAL CROSS-SECTIONAL SESSION (Review Period N-1)        │
│ Purpose: Evaluate Coverage, Saliency, Trust, and Blind-Spot Detection  │
│                                                                        │
│ Step 1 (Unaided): Manager drafts review agenda for period N-1 using    │
│                   their traditional tools and memory (logged).         │
│ Step 2 (Aided):   Manager inspects ORBIT artifact for period N-1.      │
│ Step 3 (Audit):   Blind-spot classification and trust audit challenge. │
│ Note: Effort in Step 2 is explicitly logged as VERIFICATION ONLY,      │
│       not total preparation savings.                                   │
├────────────────────────────────────────────────────────────────────────┤
│ STAGE 2: PROSPECTIVE IN-SITU WORKFLOW TRIAL (Live Review Period N)     │
│ Purpose: Evaluate End-to-End Preparation Efficiency & Decision Impact  │
│                                                                        │
│ Step 1: ORBIT generates the review artifact prior to the manager's     │
│         normal weekly prep window.                                     │
│ Step 2: Manager receives ORBIT artifact as their primary starting point.│
│ Step 3: Measure actual elapsed time to verify, annotate, and finalize  │
│         the agenda (T_orbit_total).                                    │
│ Step 4: Compare T_orbit_total against the manager's measured baseline  │
│         T_baseline from normal unassisted operations.                  │
│ Step 5: Track actual managerial decisions made during the live review. │
└────────────────────────────────────────────────────────────────────────┘
```

This design cleanly isolates **blind-spot discovery** in Stage 1 from **preparation efficiency** in Stage 2.

---

## 6. Decision-Impact Metric Correction

Specification v2 replaces the crude "$\ge 2$ decisions per session" metric with the **Managerial Action Impact Hierarchy**:

```text
Level 5: Consequential Course Correction
         (Exposed a critical delivery blocker, scope creep, or invalid status that altered
          team resource allocation, sprint commitments, or release plans)
   ▲
   │
Level 4: New Action / Follow-Up Created
         (Prompted a new operational task, escalation, or specific assignee commitment)
   ▲
   │
Level 3: Existing Decision Strengthened / Accelerated
         (Evidence removed uncertainty, enabling immediate resolution of a pending debate)
   ▲
   │
Level 2: Detail Sharpened / Contextualized
         (Existing agenda item corrected with exact PR link, commit timestamp, or dependency)
   ▲
   │
Level 1: Operational State Confirmed
         (Verified known status with zero cognitive friction; zero change to decisions)
   ▲
   │
Level 0: No Impact / Ignored
         (Finding dismissed as irrelevant, pedantic, or unhelpful)
```

**Reconciled Structure (Gate 4F-04 Decoupled):**
Gate 4F-04 is explicitly partitioned into two independent sub-dimensions:
1. **Sub-Gate 4F-04A (Preparation Efficiency):** Cohort median preparation efficiency $\text{Median}(\Delta T) \ge 35\%$ (target), with $\text{Median}(\Delta T) > 0\%$ (minimum viability). Participant-level outliers are investigated and classified rather than causing brittle gate failure.
2. **Sub-Gate 4F-04B (Managerial Action Impact):** Evaluated independently of preparation time. ORBIT must demonstrate at least **one Level 4 or Level 5 impact**, or at least **two Level 3 impacts** per evaluation session. Raw decision count is retained purely as a descriptive observation.

This decoupling ensures that a session which uncovers a critical Level 5 risk (requiring time to investigate) is not penalized as an efficiency failure, while high time savings with zero decision impact (Level 0) is correctly flagged as empty administrative automation.

---

## 7. Blind-Spot Classification Correction

Specification v2 replaces the binary "previously unobserved" classification with the **Saliency & Awareness Matrix**:

| Category | Designation | Operational Definition | Evidentiary Significance |
|---|---|---|---|
| **Category A** | **Known & Prioritized** | Manager was fully aware and already had it on their agenda. | Neutral baseline; confirms ORBIT does not miss obvious core work. |
| **Category B** | **Known but Omitted** | Manager knew about it, but forgot or omitted it from the agenda due to cognitive fatigue. | **Moderate Value:** Proves ORBIT acts as an effective operational safety net. |
| **Category C** | **Known & Deprioritized** | Manager knew about it, but intentionally chose not to discuss it. | Contextual Noise: Highlights where ORBIT's attention model needs tuning. |
| **Category D** | **New Context** | Manager did not know about it, but it requires no operational intervention. | Informational Context. |
| **Category E** | **New Actionable Issue** | Manager was unaware of the discrepancy; upon seeing evidence, agrees it requires investigation. | **High Value:** Directly uncovers unevidenced work or status drift. |
| **Category F** | **Consequential Blind Spot** | Manager was unaware of a critical cross-system conflict that alters delivery health. | **Maximum Value:** Definitive proof of the cross-system evidence foundation. |

**Reconciled Success Criterion (Gate 4F-02):**
ORBIT must surface at least **one Category E or Category F item**, or at least **two Category B items** per participant review.

---

## 8. Product-Wedge Behavioral Evidence Correction

Specification v2 establishes the **Behavioral Evidence Ladder** to prevent stated intent from being confused with genuine commercial utility:

```text
Level 5: Multi-Cycle Retention
         (Participant uses ORBIT across 2+ consecutive live weekly reviews)
   ▲
   │
Level 4: Live Review Execution
         (Participant actually uses the ORBIT artifact to conduct their live team review)
   ▲
   │
Level 3: Trial Commitment
         (Participant authorizes continuous read-only API access to run ORBIT on their repo)
   ▲
   │
Level 2: Stated Intent
         (Participant states in an interview: "I would use this next week")
   ▲
   │
Level 1: Aesthetic / Conceptual Approval
         (Participant states: "This looks cool / I like the idea")
```

**Reconciled Boundary:**
- Level 1 and Level 2 are classified as `[SUPPORTED HYPOTHESIS]`.
- Level 3 and Level 4 are required to achieve a **PASS** on Gate 4F-05.
- Multi-cycle retention (Level 5) is recognized as a post-qualification product milestone, not a prerequisite for closing Phase 4F.

---

## 9. Remaining Open Questions

1. **Recurrence Detection Mechanism:** Does recurring domain attention (e.g., GoGreen billing/service contracts) require semantic keyword clustering, or can it be surfaced deterministically through component/label frequencies?
2. **Team Operational Maturity Variance:** How widely will saliency precision vary between informal, client-driven engineering teams (like GoGreen) versus structured enterprise PMO environments?
3. **API Access Procurement Friction:** In external participant testing, will corporate OAuth / PAT security policies delay live Stage 2 trials?

---

## 10. Authorization Recommendation

```text
══════════════════════════════════════════════════════════════════════════════
RECOMMENDATION: ADOPT SPECIFICATION V2
══════════════════════════════════════════════════════════════════════════════
1. Specification v1 is formally preserved for historical auditability.
2. Specification v2 (docs/specifications/phase4f_managerial_utility_proving_specification_v2.md)
   must be established as the authoritative qualification contract.
3. Phase 4F implementation remains NOT AUTHORIZED until Specification v2
   is reviewed and authorized by project leadership.
4. Production code (src/shadow_orbit/) remains strictly FROZEN.
══════════════════════════════════════════════════════════════════════════════
```
