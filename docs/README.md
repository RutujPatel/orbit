# Project ORBIT — Documentation Index

Welcome to the Project ORBIT documentation repository. This directory serves as the centralized, structured knowledge base for all architecture decisions, engineering specifications, operational runbooks, milestone handoffs, and audit records across the system.

---

## Directory Overview

```
docs/
├── README.md               # Master documentation index (this document)
├── adr/                    # Architecture Decision Records (formal design baselines)
├── pass4/                  # Pass 4 wave execution reports, reconnaissance & forensic audits
├── specifications/         # Engine designs, input contracts, schemas & rule catalogs
├── operations/             # Runbooks, debrief scripts, observation logs & change histories
└── handoffs/               # Milestone onboarding handoffs & phase-gate transitions
```

---

## 1. Architecture Decision Records (`docs/adr/`)

Formal architectural decisions governing the Cross-System Evidence (Track B) engine:

| Document | Title | Scope & Key Decisions |
| :--- | :--- | :--- |
| [ADR-004](adr/ADR-004_PROVENANCE_DEREFERENCING.md) | Provenance Dereferencing Architecture | Defines the closed 7-outcome taxonomy (`RESOLVED`, `UNRESOLVED_ABSENT`, `UNRESOLVED_AMBIGUOUS`, etc.) for dereferencing `ProvenanceRef` and `EntityRef` within an `EvidenceBundle`. |
| [ADR-005](adr/ADR-005_CROSS_SYSTEM_EVIDENCE_FUSION.md) | Cross-System Evidence Fusion Architecture | Establishes pairwise entity matching (explicit links, key-in-branch, key-in-title, key-in-commit), 4-quadrant state comparisons, and 6-outcome temporal alignment. Prohibits Cartesian pairing and transitive linking. |
| [ADR-006](adr/ADR-006_TRACK_B_EVIDENCE_BUNDLE_EVALUATION.md) | Track B EvidenceBundle Evaluation Architecture | Establishes the Pass 4 Track B evaluator boundary. Implements rules XB-01 (PR review correlation), XB-02 (cross-system status alignment), and XB-03 (merge temporal alignment). Deferrals XB-04 through XB-08 explicitly governed. |

---

## 2. Pass 4 Engineering Reports & Forensic Audits (`docs/pass4/`)

Chronological wave execution logs, reconnaissance documents, and forensic audit reports for Pass 4 (Cross-System Evidence Engine):

| Wave / Stage | Document | Purpose & Outcomes |
| :--- | :--- | :--- |
| Reconnaissance | [PASS4_REPOSITORY_RECONNAISSANCE.md](pass4/PASS4_REPOSITORY_RECONNAISSANCE.md) | Baseline reconnaissance of repository structure, verification of frozen Track A boundary, and Pass 4 workstream definition. |
| Wave 1 | [PASS4_WAVE1_EXECUTION_REPORT.md](pass4/PASS4_WAVE1_EXECUTION_REPORT.md) | Isolation and hardening of Jira and GitHub evidence adapters; typing and schema contract preservation. |
| Wave 2 | [PASS4_WAVE2_EXECUTION_REPORT.md](pass4/PASS4_WAVE2_EXECUTION_REPORT.md) | Implementation of the provenance dereferencing engine (`provenance_dereference.py`) with full ADR-004 taxonomy coverage. |
| Wave 3 Recon | [PASS4_WAVE3_RECONNAISSANCE.md](pass4/PASS4_WAVE3_RECONNAISSANCE.md) | Structural reconnaissance of GitHub mention extraction and cross-system correlation requirements. |
| Wave 3 | [PASS4_WAVE3_EXECUTION_REPORT.md](pass4/PASS4_WAVE3_EXECUTION_REPORT.md) | Cross-system evidence fusion engine (`cross_system_fusion.py`); deterministic relationship resolution and comparison matrices. |
| Wave 4 Recon | [PASS4_WAVE4_RECONNAISSANCE.md](pass4/PASS4_WAVE4_RECONNAISSANCE.md) | Evaluation boundary reconnaissance for rules XB-01 through XB-08. |
| Wave 4A | [PASS4_WAVE4A_CONTRACT_RECONCILIATION.md](pass4/PASS4_WAVE4A_CONTRACT_RECONCILIATION.md) | Contract reconciliation between Track A and Track B; temporal investigation and formal deferral of XB-04. |
| Wave 5 | [PASS4_WAVE5_EXECUTION_REPORT.md](pass4/PASS4_WAVE5_EXECUTION_REPORT.md) | Track B evidence evaluator implementation (`evidence_evaluation.py`) for XB-01, XB-02, and XB-03. |
| Wave 5.1 Audit | [PASS4_WAVE5_1_FORENSIC_AUDIT.md](pass4/PASS4_WAVE5_1_FORENSIC_AUDIT.md) | Independent forensic audit of Wave 5 implementation, identifying 9 code and test quality findings. |
| Wave 5.2 Remediation | [PASS4_WAVE5_2_REMEDIATION_REPORT.md](pass4/PASS4_WAVE5_2_REMEDIATION_REPORT.md) | Full remediation and verification of the 9 audit findings, including 8 new adversarial test fixtures. |
| Pre-Consolidation Audit | [PASS4_FINAL_PRE_CONSOLIDATION_FORENSIC_AUDIT.md](pass4/PASS4_FINAL_PRE_CONSOLIDATION_FORENSIC_AUDIT.md) | Final forensic gate audit establishing `CONSOLIDATION READY WITH QUALIFICATIONS` prior to merging Pass 4. |

---

## 3. Core Specifications & Contracts (`docs/specifications/`)

System architecture designs, ingestion contracts, and rule catalogs:

| Specification | Document | Description |
| :--- | :--- | :--- |
| CSE-1 Design | [cse1-design.md](specifications/cse1-design.md) | High-level architectural specification for the Cross-System Evidence (CSE-1) Foundation, data models, and pipeline invariants. |
| GitHub Ingestion Contract | [github-input-contract.md](specifications/github-input-contract.md) | Ingestion schema, required/optional fields, and normalization rules for GitHub pull requests, commits, and reviews. |
| Jira Ingestion Contract | [jira-input-contract.md](specifications/jira-input-contract.md) | Ingestion schema, changelog interpretation, and normalization rules for Jira issues and sprint boundaries. |
| Initial Rule Catalog | [initial-rule-catalog.md](specifications/initial-rule-catalog.md) | Track A baseline rule catalog (R1 through R13) defining commitment integrity, scope creep, and delivery status evaluation. |
| Shadow Scope | [shadow-scope.md](specifications/shadow-scope.md) | Boundaries, invariants, and operational principles of running Shadow ORBIT non-intrusively alongside production systems. |

---

## 4. Operational Runbooks & Logs (`docs/operations/`)

Procedures, runbooks, and historical observation records:

| Document | Title | Purpose |
| :--- | :--- | :--- |
| [review-runbook.md](operations/review-runbook.md) | Review Runbook | Step-by-step procedures for reviewing shadow evaluations, verifying artifacts, and identifying pipeline divergences. |
| [debrief-script.md](operations/debrief-script.md) | Pilot Debrief Script | Protocol and questionnaire for conducting weekly engineering debriefs on delivery integrity observations. |
| [observation-log.md](operations/observation-log.md) | Shadow Run Observation Log | Empirical log of real-world observations, edge cases, and behavioral divergences recorded during pilot runs. |
| [system-change-log.md](operations/system-change-log.md) | System Change Log | Chronological register of system modifications, schema adjustments, and version increments. |

---

## 5. Milestone & Transition Handoffs (`docs/handoffs/`)

Agent onboarding briefs and milestone phase-gate transition documents:

| Document | Title | Scope |
| :--- | :--- | :--- |
| [HANDOFF_CSE1_TO_GATE2.md](handoffs/HANDOFF_CSE1_TO_GATE2.md) | CSE-1 to Gate 2 Transition Handoff | Comprehensive engineering handoff documenting CSE-1 foundation completion, Gate 1 closure, and roadmap for Gate 2. |
| [MILESTONE_1C_AGENT_HANDOFF.md](handoffs/MILESTONE_1C_AGENT_HANDOFF.md) | Milestone 1C Agent Handoff | Onboarding brief for Milestone 1C: Messy-Data Honesty Acceptance and resilience testing. |
| [MILESTONE_2A_AGENT_HANDOFF.md](handoffs/MILESTONE_2A_AGENT_HANDOFF.md) | Milestone 2A Agent Handoff | Instructions and strict authority boundaries for Milestone 2A restricted real Jira data inspection. |
