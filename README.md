# Project ORBIT

**Objective Reality & Baseline Integrity Tracking**

Project ORBIT (and its Shadow ORBIT evaluation subsystem) is a high-assurance delivery verification engine designed to evaluate engineering commitments, cross-system activity, and delivery reality across Jira and GitHub without unwarranted inferences.

---

## Architecture Overview

ORBIT is organized into two distinct evaluation tracks:

- **Track A (Frozen Baseline Engine):** Evaluates single-system (Jira) sprint commitments, scope stability, due date fidelity, and delivery integrity according to rules R1 through R13. Track A code is strictly frozen and preserved against regression.
- **Track B (Cross-System Evidence Engine):** Ingests, normalizes, dereferences, fuses, and evaluates multi-system evidence (Jira issues, GitHub pull requests, commits, and reviews) to produce verifiable delivery reality evaluations according to rules XB-01 through XB-03:
  - **Adapters:** Independent Jira and GitHub normalizers emitting strictly-typed observations.
  - **EvidenceBundle:** Consolidated multi-system container with canonical sorting and determinism.
  - **Provenance Dereferencing (`provenance_dereference.py`):** Closed 7-outcome taxonomy resolving entity and field-level evidence sources.
  - **Cross-System Fusion (`cross_system_fusion.py`):** Deterministic pairwise matching, state alignment matrices, and temporal ordering checks (anti-Cartesian, anti-transitive, anti-actor matching).
  - **Evidence Evaluator (`evidence_evaluation.py`):** Deterministic multi-system evaluation rules with anti-completion and anti-absence-as-failure safeguards.

---

## Directory Structure

```
.
├── docs/                       # Project documentation, specifications & ADRs
│   ├── README.md               # Master documentation index & navigation guide
│   ├── adr/                    # Architecture Decision Records (ADR-004 through ADR-006)
│   ├── pass4/                  # Pass 4 wave execution reports & forensic audits
│   ├── specifications/         # Engine designs, input contracts, rule catalogs & scope
│   ├── operations/             # Review runbooks, debrief scripts & observation logs
│   └── handoffs/               # Milestone agent onboarding & phase-gate transitions
├── fixtures/                   # Test fixtures (Jira, GitHub, experiments)
│   ├── jira/                   # Jira normalized test fixtures (clean & messy)
│   ├── github/                 # GitHub normalized test fixtures (clean & messy)
│   └── experiments/            # Multi-week experiment & state fixtures
├── src/
│   └── shadow_orbit/           # Core engine source code
│       ├── types.py            # Track A core domain types
│       ├── evaluation.py       # Track A evaluation engine (frozen)
│       ├── continuity.py       # Track A commitment continuity tracking
│       ├── deltas.py           # Track A state deltas & changes
│       ├── evidence_types.py   # Track B evidence dataclasses & enums
│       ├── evidence_assembly.py# Track B EvidenceBundle construction & validation
│       ├── jira_evidence_adapter.py    # Jira observation extraction adapter
│       ├── github_normalization.py     # GitHub normalization adapter
│       ├── github_relationships.py     # Intra-system GitHub relationship resolution
│       ├── github_mentions.py          # GitHub-to-Jira mention extraction
│       ├── provenance_dereference.py   # Track B provenance dereferencing engine
│       ├── cross_system_fusion.py      # Track B cross-system evidence fusion engine
│       └── evidence_evaluation.py      # Track B evidence evaluation engine (XB-01..XB-03)
└── tests/
    ├── conftest.py             # Pytest fixtures and shared configuration
    ├── acceptance/             # End-to-end acceptance tests (Track A clean & messy)
    └── unit/                   # Unit test suite for Track A & Track B engines
```

---

## Documentation

For full architectural records, specifications, runbooks, and audit histories, see the [Documentation Index](docs/README.md).

Key sections:
- [Architecture Decision Records (ADRs)](docs/adr/)
- [Pass 4 Wave Reports & Forensic Audits](docs/pass4/)
- [Specifications & Input Contracts](docs/specifications/)
- [Operational Runbooks & Logs](docs/operations/)
- [Milestone Handoffs](docs/handoffs/)

---

## Running Tests

ORBIT uses `pytest` with 100% deterministic test execution (no external network calls, no system clock dependencies):

```bash
# Run the entire test suite
pytest tests/ -v

# Run Track A acceptance tests
pytest tests/acceptance/ -v

# Run Track B Pass 4 unit & evaluation tests
pytest tests/unit/test_p4_* -v
```
