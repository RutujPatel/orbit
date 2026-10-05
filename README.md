# Project ORBIT

**Organizational Review & Business Intelligence Toolkit**<br/>
*Deterministic, Evidence-Grounded Cross-System Delivery Verification Engine*

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()
[![Status](https://img.shields.io/badge/Status-Pass%205%20Wave%203%20%2F%20Phase%204E--B%20(Hardened)-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/Tests-873%20passed%20%2F%2012%20skipped%20%2F%200%20failed-success.svg)]()
[![Determinism](https://img.shields.io/badge/Determinism-100%25%20Offline%20%2F%20Zero--IO-blueviolet.svg)]()

---

## Table of Contents

1. [Executive Summary & Project Identity](#1-executive-summary--project-identity)
2. [The Product Problem & Strategic Wedge](#2-the-product-problem--strategic-wedge)
3. [Architecture Overview: The Dual-Track Engine](#3-architecture-overview-the-dual-track-engine)
   - [Track A: Frozen Baseline Engine (Jira)](#track-a-frozen-baseline-engine-jira)
   - [Track B: Cross-System Evidence Engine (Jira + GitHub)](#track-b-cross-system-evidence-engine-jira--github)
   - [The Common Evidence Layer](#the-common-evidence-layer)
4. [Repository Identity & Evolution Subsystem (Pass 5 / Wave 3)](#4-repository-identity--evolution-subsystem-pass-5--wave-3)
   - [Closed Taxonomies & Cardinality](#closed-taxonomies--cardinality)
   - [The 16 Formal Invariants](#the-16-formal-invariants)
   - [Architectural Semantic Firewall](#architectural-semantic-firewall)
   - [Phase 4E-B Hardening Gate](#phase-4e-b-hardening-gate)
5. [Empirical Qualification & Benchmark Datasets](#5-empirical-qualification--benchmark-datasets)
   - [Authentic Apache Cases](#authentic-apache-cases)
   - [Mahout Qualification Specimen](#mahout-qualification-specimen)
   - [TrueTenant Blind Holdout](#truetenant-blind-holdout)
   - [GoGreen Pilot Dataset](#gogreen-pilot-dataset)
6. [Repository & Directory Structure](#6-repository--directory-structure)
7. [Running Tests & Verification Gates](#7-running-tests--verification-gates)
8. [Decision Governance & Phase Roadmap](#8-decision-governance--phase-roadmap)
9. [Documentation Index](#9-documentation-index)

---

## 1. Executive Summary & Project Identity

**Project ORBIT** (Organizational Review & Business Intelligence Toolkit) is a high-assurance delivery verification engine designed to evaluate engineering commitments, cross-system activity, and delivery reality across Jira and GitHub without unwarranted inferences.

ORBIT operates under a dual nature:
1. **An Enterprise-Grade Product Simulation:** Building an industrial-strength, fail-closed platform that reconciles disparate enterprise software systems into a singular, cryptographically authenticated, deterministic operational record.
2. **A Long-Form Staff-Level Software Engineering Curriculum:** Modeling how mature engineering organizations define products, design domain models, enforce architectural boundaries, secure data, maintain backward compatibility, and evolve complex distributed data systems over years.

### Key Operational Metrics (Phase 4E-B Hardened Baseline)
- **Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed`
- **Consolidation Lineage HEAD:** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`
- **Current HEAD:** `af0f0a744b6259b85bd5fd29243fab82d49608e9`
- **Test Battery:** **873 passed, 12 skipped (unreachable local MongoDB), 0 failed** across 10 qualification gates.
- **Determinism:** 100% offline, zero network I/O, zero system-clock dependencies, byte-identical JSON serialization across permutations.

---

## 2. The Product Problem & Strategic Wedge

### The Enterprise Fragmentation Problem
Modern software organizations rely on deeply disconnected systems of record:
- Work planning & issue tracking: **Jira, Linear, Azure DevOps**
- Code execution & version control: **GitHub, GitLab, Bitbucket**
- Operational communications & messaging: **Slack, Microsoft Teams**
- Business operations & CRM: **Salesforce, SAP, ServiceNow, Odoo**

This fragmentation creates a persistent illusion gap: **what teams say is happening in project trackers regularly diverges from what code repositories and CI/CD pipelines actually prove.** Teams suffer from manual status compilation, ungrounded reviews, and "watermelon projects" (green on the outside, red on the inside).

### Strategic Wedge (v0): Engineering Weekly Review
Rather than attempting a premature, sprawling "enterprise control plane," ORBIT begins with a focused, high-value wedge: **The Engineering Weekly Review**.
- Ingests sprint commitments, scope stability, due date fidelity, and delivery metrics.
- Reconciles claimed work item completions against corroborated version control evidence (PRs, commits, reviews, merges).
- Applies deterministic evaluation rules to highlight stalled work, uncorroborated closures, and review deficits.

### Long-Term Vision: Organizational Operating & Execution Layer
Over time, ORBIT evolves into an organizational memory and execution plane that maintains a deterministic, permission-aware understanding of people, work, commitments, external events, and system state.
- **AI Principle:** Artificial Intelligence operates exclusively as a **governed reasoning and narration layer**. AI is never the authoritative source of facts, state, or truth. All conclusions rest on cryptographically verifiable, provenance-backed deterministic evidence.

---

## 3. Architecture Overview: The Dual-Track Engine

ORBIT enforces strict operational decoupling through two distinct evaluation tracks:

```
┌────────────────────────────────────────────────────────────────────────┐
│                              PROJECT ORBIT                             │
├──────────────────────────────────┬─────────────────────────────────────┤
│   TRACK A: Frozen Baseline       │   TRACK B: Cross-System Evidence    │
│   (Single-System Jira)           │   (Multi-System Jira + GitHub)      │
├──────────────────────────────────┼─────────────────────────────────────┤
│ • WorkItem / Change / Snapshot   │ • ObservationContext / EvidenceObs  │
│ • Rules R1 through R13           │ • Rules XB-01 through XB-03         │
│ • Sprint Continuity & Deltas     │ • Provenance Dereferencing (ADR-004)│
│ • Strictly Frozen Semantic Base  │ • Cross-System Fusion (ADR-005)     │
│ • Zero modification permitted    │ • Repository Evolution (ADR-006+)   │
└──────────────────────────────────┴─────────────────────────────────────┘
```

### Track A: Frozen Baseline Engine (Jira)
Evaluates single-system Jira sprint commitments, scope stability, due date fidelity, and delivery integrity according to rules **R1 through R13**:
- Core modules: `src/shadow_orbit/types.py`, `evaluation.py`, `continuity.py`, `deltas.py`, `temporal.py`, `normalization.py`.
- Evaluates `WorkItem` records against sprint snapshots, computing commitment carryover, scope changes, and completion rates.
- **Governance Constraint:** Track A code is strictly frozen. No Track B or Pass 5 changes are permitted to alter Track A types, signatures, or evaluation outcomes.

### Track B: Cross-System Evidence Engine (Jira + GitHub)
Ingests, normalizes, dereferences, fuses, and evaluates multi-system evidence to produce verifiable delivery reality evaluations according to rules **XB-01 through XB-03**:
- **Rules XB-01..XB-03:**
  - `ORBIT-XB-01`: Pull Request Review Deficit (claimed resolved issue backed by unapproved or open PR).
  - `ORBIT-XB-02`: Cross-System Status Contradiction (issue closed but code activity ongoing, or vice-versa).
  - `ORBIT-XB-03`: Premature Closure / Merge Temporal Inversion (issue resolved before code was merged).
- **Rules XB-04..XB-08:** Explicitly governed and deferred until empirical corroboration warrants activation.
- **Provenance Dereferencing (`provenance_dereference.py`):** Closed 7-outcome taxonomy (`RESOLVED`, `UNRESOLVED_ABSENT`, `UNRESOLVED_AMBIGUOUS`, etc.) resolving entity and field-level evidence sources against raw JSON payloads.
- **Cross-System Evidence Fusion (`cross_system_fusion.py`):** Deterministic pairwise matching (explicit links, branch naming keys, PR title tokens, commit message tokens), 4-quadrant state matrices, and 6-outcome temporal alignment. Prohibits Cartesian pairing, transitive chaining, and actor conflation.

### The Common Evidence Layer
All multi-system observations are unified into immutable, frozen dataclasses in `src/shadow_orbit/evidence_types.py`:
- `SourceInstance`: Provider identification (`source_kind`, `instance_id`).
- `EntityRef`: Provider-scoped entity pointer (`source_instance`, `entity_kind`, `entity_id`).
- `ObservationContext`: Envelope recording acquisition metadata and source timestamps.
- `EvidenceObservation`: Concrete observed entity state (Jira issue state, GitHub PR state, commit state).
- `EvidenceRelationship`: Resolved link between two entities with supporting provenance.
- `UnresolvedReference`: Unresolvable external reference with explicit failure reason.
- `CrossSystemStateAlignment`: Corroborated alignment between Jira and GitHub entities.
- `QualityIssue`: Structured data quality defect (`missing`, `malformed`, `invalid`, `unresolved`, `ambiguous`, `contradictory`, `stale`).
- `EvidenceBundle`: Immutable container assembling all contexts, observations, relationships, alignments, quality issues, and repository evolution relationships.

---

## 4. Repository Identity & Evolution Subsystem (Pass 5 / Wave 3)

In real-world enterprise engineering, code repositories do not remain static: they are renamed, moved across GitHub organizations, split, merged, forked, or replaced.

If an evidence engine treats repository names as naive strings, repository renames shatter commit and PR linkage. Conversely, if an engine naively merges repository identities, it conflates separate codebases, creates false dependency cycles, and transfers state inappropriately.

Project ORBIT resolves this via **Option B: Immutable EntityRef + Typed Repository Evolution Relationships** (formalized in ADR-006 and Phase 4B/4C/4D/4E).

### Closed Taxonomies & Cardinality
Every repository relationship belongs to a closed taxonomy in `src/shadow_orbit/evidence_types.py`:

```
┌────────────────────────────────────────────────────────────────────────┐
│                  REPOSITORY EVOLUTION RELATIONSHIPS                    │
├────────────────────────┬───────────────────────────────────────────────┤
│ Relationship Family    │ Permitted Types                               │
├────────────────────────┼───────────────────────────────────────────────┤
│ NAVIGATION_ROUTING     │ • RENAME (name change within namespace)       │
│                        │ • NAMESPACE_MOVE (transfer across orgs)       │
│                        │ • REDIRECT (VCS hosting redirect pointer)     │
├────────────────────────┼───────────────────────────────────────────────┤
│ PROJECT_LINEAGE        │ • PREDECESSOR_SUCCESSOR (ancestor lineage)    │
├────────────────────────┼───────────────────────────────────────────────┤
│ REPOSITORY_TOPOLOGY    │ • FORK (divergent codebase copy)              │
│                        │ • MIRROR (read-only replica)                  │
│                        │ • VENDOR_MIRROR (vendored dependency copy)    │
├────────────────────────┼───────────────────────────────────────────────┤
│ ECOSYSTEM_DEPENDENCY   │ • EXTERNAL_DEPENDENCY (library requirement)   │
│                        │ • ECOSYSTEM_PACKAGING (Docker, Helm, wrapper) │
│                        │ • COMPANION_SPECIFICATION (RFC, standards)    │
└────────────────────────┴───────────────────────────────────────────────┘
```

- **Deterministic ID Formula:**
  $$\text{relationship\_id} = \text{SHA-256}(\text{instance\_id} \parallel \text{relationship\_type} \parallel \text{source\_repo\_id} \parallel \text{target\_repo\_id})$$
- **Directionality:** `DIRECTED_FORWARD` (default) or `BIDIRECTIONAL_SYMMETRIC` (strictly for `MIRROR`).
- **Transitivity:** `TRANSITIVE_PERMITTED` (routing, lineage) or `STRICTLY_NON_TRANSITIVE` (topology, dependencies).
- **Verification Status:** `PROVEN`, `SUPPORTED`, `PARTIALLY_PROVEN`, `UNVERIFIED`.

### The 16 Formal Invariants
The engine strictly enforces 16 formal invariants across all operations:

| Category | Invariant | Description |
| :--- | :--- | :--- |
| **Identity** | `INV-ID-01` | EntityRef immutability; repository entities are never overwritten in-place. |
| | `INV-ID-02` | Strict repository kind: endpoints must have `entity_kind="repository"`. |
| | `INV-ID-03` | Collision isolation: colliding PR numbers across ancestor repositories remain isolated. |
| | `INV-ID-04` | Deterministic SHA-256 relationship identifier derivation. |
| **Evidence** | `INV-EV-01` | Mandatory cryptographic provenance; empty-string SHA-256 digests are rejected. |
| | `INV-EV-02` | Grounded provenance: repository relationships cannot be asserted from plain URLs alone. |
| | `INV-EV-03` | Honest missing-evidence gaps: unobserved relationships remain unverified. |
| **Linkage** | `INV-LK-01` | Linkage neutrality: repository redirects do not synthesize Jira↔GitHub links. |
| | `INV-LK-02` | Linkage separation: repository evolution is evidence context, not automatic cross-system linkage. |
| **State** | `INV-ST-01` | Zero state transfer: repository relationships never transfer work-item or PR status. |
| | `INV-ST-02` | Dependency state isolation: merged external dependency PRs do not resolve downstream issues. |
| **Temporal** | `INV-TM-01` | Temporal proximity is not causality: proximity never manufactures linkage. |
| | `INV-TM-02` | Temporal coherence separation: independent repository timelines remain uncoupled. |
| **Graph** | `INV-GR-01` | Lineage acyclicity: `PROJECT_LINEAGE` must form a strict Directed Acyclic Graph (DAG). |
| | `INV-GR-02` | Routing acyclicity: `NAVIGATION_ROUTING` must be strictly acyclic (no self-loops or cycles). |
| | `INV-GR-03` | Non-transitivity: ecosystem dependencies and forks are strictly non-transitive for evaluation. |

### Architectural Semantic Firewall
Every `RepositoryEvolutionRelationship` carries an architectural `SemanticFirewall` enforcing 4 fail-closed assertions:
```python
@dataclass(frozen=True, slots=True)
class SemanticFirewall:
    entity_ref_mutation_forbidden: bool = True
    linkage_auto_upgrade_forbidden: bool = True
    state_transfer_forbidden: bool = True
    temporal_causality_inference_forbidden: bool = True
```
Any attempt to relax these booleans to `False` immediately raises a fatal `ValueError`.

### Phase 4E-B Hardening Gate
Following initial production integration, a forensic code audit established the Phase 4E-B Hardening Gate, resolving 4 contract-level vulnerabilities:
1. **H1 — Provenance Type Loophole Closed:** Restricted `provenance_refs` strictly to `tuple[RepositoryProvenanceRef, ...]`. Validated 64-hex lowercase SHA-256 regex, non-empty fixture/record locators, and hardened file verification guards.
2. **H2 — Lossless Provenance Serialization:** Preserved `observation_id` and `source_field_path` through roundtrip serialization without fabricated fallback strings.
3. **H3 — Anti-Conflict Deduplication:** Implemented `_repository_relationships_semantically_conflict`. Conflicting duplicate IDs fail closed with `ValueError` during assembly and emit `QualityIssue(code="contradictory", ...)` during bundle validation.
4. **H4 — Cross-Provider Identity Scoping:** Scoped graph cycle validation to the full composite key (`source_kind:instance_id:entity_id`), preventing false cycle detection across distinct hosting providers while keeping the Phase 4C relationship-ID formula intact.

---

## 5. Empirical Qualification & Benchmark Datasets

ORBIT rejects toy mock testing. The engine is qualified against authentic enterprise software artifacts:

### Authentic Apache Cases
Four empirical cases from the Apache Software Foundation are qualified in `tests/qualification/repository_evolution/`:
- **`FLINK-1359` (Routing):** Transition from `apache/incubator-flink` to `apache/flink`. Validates navigation redirect preservation and PR review correlation without mutating source repository references.
- **`stratosphere#126` (Lineage):** Pre-Apache predecessor repository (`stratosphere/stratosphere`) colliding on PR #126 with `apache/flink#126`. Demonstrates absolute entity isolation (`INV-ID-03`).
- **`KAFKA-9168` (External Dependency):** Kafka issue dependent on RocksDB PR. Demonstrates that merged external dependency PRs do not transfer completion state to in-progress Jira issues (`INV-ST-02`).
- **`FLINK-20650` (Ecosystem Packaging):** Flink issue coupled with `apache/flink-docker` packaging PR. Demonstrates that independent repository timelines remain temporally isolated (`INV-TM-02`).

### Mahout Qualification Specimen
- Ground-truth enterprise dataset of 412 Jira issues and historical changelogs.
- Proves zero regression across historical projection, identity mapping, and pipeline execution.

### TrueTenant Blind Holdout
- Ingestion and projection of 34 real-world Jira issues from an external customer environment.
- Proves that Jira status mapping, priority banding, and issue normalization function without provider leakage.

### GoGreen Pilot Dataset
- Real-world multi-week engineering dataset validating manager attention models, review cadences, and cross-system activity patterns.

---

## 6. Repository & Directory Structure

```
.
├── docs/                       # Comprehensive documentation & architectural records
│   ├── README.md               # Master documentation index & navigation sitemap
│   ├── adr/                    # Architecture Decision Records (ADR-004..ADR-006, repo identity)
│   ├── pass4/                  # Pass 4 wave execution reports & forensic audits (Waves 1-5)
│   ├── pass5/                  # Pass 5 wave reports, qualification audits & benchmarks
│   │   ├── phase4d_report.md   # Phase 4D prototype qualification report
│   │   └── phase4e_implementation_report.md # Phase 4E-B production & hardening report
│   ├── context/                # Canonical project context checkpoints (v1..v39)
│   ├── specifications/         # Engine designs, input contracts, schemas & rule catalogs
│   ├── operations/             # Review runbooks, debrief scripts & observation logs
│   └── handoffs/               # Milestone agent onboarding & phase-gate transitions
├── fixtures/                   # Deterministic offline test fixtures
│   ├── jira/                   # Jira normalized fixtures (clean & messy weeks)
│   ├── github/                 # GitHub normalized fixtures (clean & messy weeks)
│   └── experiments/            # Multi-week state & transition fixtures
├── qualification/              # Qualification suites, schemas & empirical corpora
│   ├── repository_evolution/   # Re-export adapter & authentic Apache case generators
│   ├── truetenant/             # TrueTenant holdout adapter & mapping contract
│   └── wave3/                  # Phase 4C schemas, acquisition raw data & reports
├── src/
│   └── shadow_orbit/           # Core engine implementation
│       ├── types.py            # Track A core domain types (frozen)
│       ├── evaluation.py       # Track A evaluation engine (frozen, R1-R13)
│       ├── continuity.py       # Track A commitment continuity tracking (frozen)
│       ├── deltas.py           # Track A state delta calculation (frozen)
│       ├── temporal.py         # Timestamp & period boundary calculations (frozen)
│       ├── normalization.py    # Track A Jira normalization (frozen)
│       ├── validation.py       # Track A fixture validation (frozen)
│       ├── fixture_io.py       # Deterministic JSON fixture loader (frozen)
│       ├── artifact.py         # Review artifact builder & serializer (frozen)
│       ├── evidence_types.py   # Track B evidence dataclasses, taxonomies & validators
│       ├── evidence_assembly.py# Track B EvidenceBundle assembly, dedup & validation
│       ├── jira_evidence_adapter.py    # Jira observation extraction adapter
│       ├── github_normalization.py     # GitHub fixture normalization adapter
│       ├── github_relationships.py     # Intra-system GitHub relationship resolution
│       ├── github_mentions.py          # GitHub-to-Jira mention extraction
│       ├── provenance_dereference.py   # Provenance dereferencing engine (ADR-004)
│       ├── cross_system_fusion.py      # Cross-system evidence fusion engine (ADR-005)
│       └── evidence_evaluation.py      # Evidence evaluation engine (ADR-006, XB-01..XB-03)
└── tests/
    ├── conftest.py             # Pytest fixtures and shared testing setup
    ├── acceptance/             # End-to-end acceptance tests (Track A clean & messy)
    ├── qualification/          # Forensic qualification tests (Mahout, GoGreen, Phase 4D)
    │   └── repository_evolution/ # Phase 4D 16-invariant qualification suite (38 tests)
    └── unit/                   # Unit test suite for Track A & Track B engines
        ├── test_p4e_repository_evolution_integration.py # Phase 4E-B suite (26 tests)
        └── test_truetenant_holdout.py                   # TrueTenant holdout (34 tests)
```

---

## 7. Running Tests & Verification Gates

ORBIT requires **Python 3.12+** (tested through 3.13). All tests are 100% deterministic, require no network connection, and generate zero live provider mutations.

### Running the Full Test Suite
```bash
pytest
```
*Expected Result:* `873 passed, 12 skipped (local MongoDB), 0 failed in ~78s`

### Running Track-Specific Batteries
```bash
# Track A Acceptance Tests
pytest tests/acceptance/ -v

# Track B Evidence Engine Unit Tests
pytest tests/unit/test_p4_* -v

# Phase 4D Repository Evolution Qualification Suite (38 tests)
pytest tests/qualification/repository_evolution/ -v

# Phase 4E-B Production Integration & Hardening Suite (26 tests)
pytest tests/unit/test_p4e_repository_evolution_integration.py -v

# TrueTenant Blind Holdout Suite (34 tests)
pytest tests/unit/test_truetenant_holdout.py -v

# Mahout Offline Specimen Qualification
pytest tests/qualification/test_mahout_history_model.py tests/qualification/test_mahout_identity_mapping.py -v
```

### Determinism & Permutation Gates
```bash
# Verify byte-identical serialization across random observation & relationship reorderings
pytest tests/unit/test_p4e_repository_evolution_integration.py -k test_determinism
```

### Git Hygiene & Whitespace Gate
```bash
git diff --check
```

---

## 8. Decision Governance & Phase Roadmap

ORBIT enforces strict decision discipline through its authoritative context file: [`Project_ORBIT_Canonical_Context_v40.md`](docs/context/Project_ORBIT_Canonical_Context_v40.md). Decisions are numbered, immutable once locked, and never silently rewritten.

### Key Architectural Decisions
- **S-001..S-006:** Problem definition, target customer, and the v0 Engineering Weekly Review product wedge.
- **S-007..S-010:** Deterministic intelligence, provenance requirement, and review lifecycle.
- **S-011..S-015:** Minimal v0 domain model, Jira projection contract, credential security.
- **S-016..S-020:** Logical PostgreSQL persistence, Django modularity, and RBAC authorization.
- **S-021..S-024:** Fixture-first development, Jira sync adapter, deterministic metric & finding engines.
- **S-025..S-033:** Review workspace UX, API service boundaries, CI/CD pipeline, and threat models.
- **S-034 (LOCKED):** Jira + GitHub Cross-System Evidence Direction. Parallel Track A / Track B operating model.

### Phase Evolution & Status
- **Pass 4 (Waves 1–5):** Completed & Consolidated. Implemented Track B evidence layer, provenance dereferencing (ADR-004), cross-system fusion (ADR-005), and evidence evaluation (ADR-006: XB-01..XB-03).
- **Pass 5 (Waves 0–3):** Universal connected systems reconnaissance, empirical Apache/Mahout candidate acquisition, population qualification.
- **Phase 4A:** Consolidation and governance audit. Reconciled Phase 3B documentation erratum.
- **Phase 4B:** Repository Identity & Evolution architecture (Option B selected).
- **Phase 4C:** Formal Repository Evolution Schema Specification (16 invariants, JSON schema).
- **Phase 4D:** Prototype Qualification (CLOSED / PASS). Qualified authentic Apache cases with real cryptographic fixture digests.
- **Phase 4E-A:** Production Integration Design (CLOSED). Minimum production integration surface identified.
- **Phase 4E-B:** Production Integration & Hardening (CLOSED / PASS / HARDENED). Integrated into `evidence_types.py` and `evidence_assembly.py`. Resolved findings H1–H4 with 8 hardening tests.
- **Phase 4E-C:** Integrated Evidence-Pipeline Qualification (CLOSED / PASS). Qualified evidence pipeline integration across 5 gates, 15 scenarios, and 20 invariants.
- **Phase 4E-D:** Multi-System Evidence Composition (CLOSED / PASS WITH DOCUMENTATION QUALIFICATION). Qualified heterogeneous evidence composition across 5 gates, 15 execution-derived scenarios, and 24 formal invariants with zero production code changes (913 passed, 12 skipped, 0 failed).
- **Phase 4F:** Managerial Utility / Product-Wedge Qualification (NEXT AUTHORIZED WORKSTREAM — PENDING SPECIFICATION).

---

## 9. Documentation Index

For detailed architectural records, specifications, and audit reports, refer to:
- [Master Documentation Index](docs/README.md)
- [Canonical Context Checkpoint v40](docs/context/Project_ORBIT_Canonical_Context_v40.md) (and [v39](docs/context/Project_ORBIT_Canonical_Context_v39.md))
- [Phase 4E-D Closure Report](docs/pass5/phase4e_d_closure_report.md)
- [Phase 4E-D Qualification Report](docs/pass5/phase4e_d_report.md)
- [Phase 4E Implementation & Hardening Report](docs/pass5/phase4e_implementation_report.md)
- [Phase 4D Prototype Qualification Report](docs/pass5/phase4d_report.md)
- [Phase 4C Schema Specification](qualification/wave3/phase4c_repository_evolution_schema/ADR-REPOSITORY-EVOLUTION-SCHEMA.md)
- [Architecture Decision Records](docs/adr/)
- [Pass 4 Forensic Audit Series](docs/pass4/)
- [Pass 5 Engineering Reports](docs/pass5/)

---

*Project ORBIT is developed under a high-assurance forensic engineering governance process. All evidence is cryptographically authenticated, deterministic, and strictly fail-closed.*
