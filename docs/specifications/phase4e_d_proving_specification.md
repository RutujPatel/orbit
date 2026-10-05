# Project ORBIT — Phase 4E-D Proving Specification

**Phase:** 4E-D — Multi-System Evidence Composition & Contextual Utility Qualification  
**Status:** **DRAFT — AWAITING REVIEW / AUTHORIZATION**  
**Date:** 2026-10-05  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed`  
**Current Execution HEAD:** `6c59470`  
**Branch:** `develop`  
**Predecessor:** Phase 4E-C Integrated Evidence-Pipeline Qualification — PASS / QUALIFIED  

---

## 1. Purpose & Strategic Context

Phase 4D qualified the formal `RepositoryEvolutionRelationship` contract against authentic empirical cases.  
Phase 4E-B integrated and hardened the contract within the production `EvidenceBundle` domain model.  
Phase 4E-C proved that repository evolution remains **strictly isolated, non-contaminating, and neutral** when coexisting in the evidence pipeline.

**Phase 4E-D moves from isolation proving to composition proving:**

> When realistic, heterogeneous multi-system evidence coexists simultaneously — comprising Jira `WorkItemState`, GitHub `CodeChangeState`, explicit cross-system linkage, lexical mentions, repository evolution, temporal observations, state alignments, and unresolved references — can Project ORBIT assemble and evaluate a richer composite evidence state **without turning contextual relationships into unsupported conclusions**?

This is an integration qualification and compositional utility exercise, not an architectural redesign or a product expansion.

---

## 2. Core Hypothesis

The phase will attempt to prove:

> **Rich multi-system evidence composition provides essential disambiguation context for cross-system delivery health, while ORBIT's formal firewall and anti-inference invariants strictly prevent contextual metadata from manufacturing unevidenced linkage, state transfer, causality, or organizational findings.**

This directly honors the core ORBIT operating principle:

$$\text{observe} \longrightarrow \text{validate} \longrightarrow \text{preserve} \longrightarrow \text{classify} \longrightarrow \text{evaluate only when justified} \longrightarrow \text{disclose what cannot be determined}$$

---

## 3. What Phase 4E-D Is Proving

Phase 4E-D qualifies five specific compositional capabilities and boundaries:

### 3.1 Composite Evidence Coexistence
Can an `EvidenceBundle` hold the full spectrum of evidence types simultaneously:
- Jira work-item observations (`jira_issue`, `work_item`);
- GitHub code-change observations (`github_pull_request`, `code_change`, `commit`);
- Explicit metadata relationships (`explicit_link` / `explicit_metadata`);
- Lexical cross-system mentions (`mentions` / `lexical_match`);
- Cross-system state alignments (`CrossSystemStateAlignment`);
- Unresolved references (`UnresolvedReference`);
- Repository evolution relationships (`NAVIGATION_ROUTING`, `PROJECT_LINEAGE`, `ECOSYSTEM_DEPENDENCY`);
- Quality conditions (`QualityIssue`);
without any field clobbering, type confusion, or ordering instability?

### 3.2 Contextual Disambiguation vs. Linkage Upgrades
When a Jira issue cites a PR in a predecessor repository that redirected to a target repository, does the repository-evolution metadata explain the navigation path **without**:
1. rewriting the PR endpoint;
2. manufacturing a false Jira↔predecessor link;
3. silently upgrading a lexical mention into an explicit link?

### 3.3 State & Lifecycle Integrity under Full Composition
When multiple work items and PRs coexist across evolved repository boundaries, does each entity retain its own lifecycle state without:
1. transferring `done` or `merged` status across boundaries;
2. interpreting third-party/dependency PR merges as first-party completion;
3. manufacturing false blockers?

### 3.4 Temporal Disclosure without Causal Leap
When independent timelines are recorded across work management, code changes, and repository milestones, does ORBIT preserve the temporal order and compute tracking lag (e.g. `elapsed_complete_days`) **without**:
1. inferring causal links;
2. asserting defect or blame on observational findings;
3. treating temporal proximity as contradiction?

### 3.5 Disclosing Gaps & Unresolved References in Complex Graphs
When composite bundles contain dangling citations, missing observations, or ambiguous contexts, does ORBIT:
1. emit deterministic `UNRESOLVED` or `AMBIGUOUS` suppressions;
2. isolate the failure to the affected candidate pair;
3. evaluate all well-formed pairs normally without cascade failure?

---

## 4. Explicit Non-Goals

Phase 4E-D does **not** authorize:
- universal connector / provider frameworks;
- live provider synchronization or network polling;
- automatic alias normalization;
- Jira write-back or mutation of source systems;
- new candidate evaluation rules beyond authorized `ORBIT-XB-01`, `XB-02`, `XB-03`;
- developer identity resolution or actor attribution;
- customer-facing UI or product workflow expansion;
- changes to the governing semantic baseline (`6d82d123f8bf50316d2b1ab7a025bc5862a474ed`).

---

## 5. Five Proving Gates

### Gate 4E-D-01 — Full Composite Bundle Assembly & Preservation
**Objective:** Assemble fully populated, heterogeneous evidence bundles containing all 8 canonical fields simultaneously. Verify:
- Zero cross-field leakage or type mutation;
- Lossless serialization and round-trip fidelity;
- Deterministic canonical sorting across all composite collections;
- Idempotent deduplication of composite relationships.

### Gate 4E-D-02 — Contextual Disambiguation vs. Linkage Neutrality
**Objective:** Test compound graphs where repository evolution provides routing context for cross-system citations. Verify:
- Explicit linkage remains strictly authoritative (`PROVEN`);
- Lexical mentions remain strictly `SUPPORTED` and are never promoted;
- Repository evolution relationships never act as cross-system candidate pairs;
- Third-provider boundaries (`github` vs `gitlab`) prevent identity collapse.

### Gate 4E-D-03 — Multi-System State & Temporal Coherence
**Objective:** Exercise heterogeneous lifecycle combinations across related repositories. Verify:
- Issue status (`todo`, `in_progress`, `done`) never transfers across repository links;
- Code-change status (`open`, `closed`, `merged`) never transfers across repository links;
- Dependency PR merges never complete first-party tickets;
- Observational temporal lag (`ORBIT-XB-03`) is recorded without inferring defect or fault.

### Gate 4E-D-04 — Resilient Gaps & Explicit Ambiguity Scoping
**Objective:** Subject compound bundles to partial, missing, or contradictory evidence. Verify:
- Dangling Jira references cite `UNRESOLVED` without crashing evaluation;
- Ambiguous observations (>1 match per entity) emit `AMBIGUOUS` suppressions;
- Stale observations emit `STALE` suppressions;
- Semantic conflicts in duplicate IDs fail closed (`ValueError` on assembly, `contradictory` QualityIssue on validation).

### Gate 4E-D-05 — Composite Evaluator Isolation & Permutation Invariance
**Objective:** Run the full Track B evaluator (`evaluate_evidence_bundle`) across the complete compound evidence space. Verify:
- Only authorized candidate rules (`ORBIT-XB-01`, `XB-02`, `XB-03`) are evaluated;
- Unlinked or repository-only entities produce zero candidate pairs (Anti-Cartesian invariant);
- Permuting input ordering across 5 randomized permutations produces byte-identical evaluation summaries and finding digests;
- Finding IDs and evaluation IDs remain strictly deterministic.

---

## 6. Adversarial Scenario Matrix (D-01 through D-15)

| Case ID | Gate | Condition | Expected Behavior | Failure Class |
|---|---|---|---|---|
| **D-01** | 4E-D-02 | Redirected repo citation with resolved issue and open PR | `ORBIT-XB-01` triggered on valid pair; PR endpoint unchanged; zero ownership transfer | F2 / F3 |
| **D-02** | 4E-D-02 | Predecessor repo lineage with successor merged PR and open issue | `ORBIT-XB-02` triggered; cross-lineage provenance preserved; distinct identities | F2 / F3 |
| **D-03** | 4E-D-03 | External dependency merged PR with in-progress first-party issue | No completion manufactured; Jira issue remains `in_progress`; zero defect finding | F3 |
| **D-04** | 4E-D-03 | Packaging PR merged 36 days post-resolution | Observational lag recorded; zero defect, fault, or blame inferred | F3 |
| **D-05** | 4E-D-04 | Compound bundle with both valid link and dangling unresolved citation | Valid pair evaluated; dangling citation emits `UNRESOLVED` suppression; zero cascade failure | F2 / F4 |
| **D-06** | 4E-D-02 | Dual-PR association across predecessor and target repositories | Independent evaluation of both pairs; no Cartesian explosion; zero false contradiction | F2 / F5 |
| **D-07** | 4E-D-04 | Ambiguous observation context (multiple observations for same entity) | Evaluator emits `AMBIGUOUS` suppression; zero silent selection | F2 / F3 |
| **D-08** | 4E-D-04 | Stale Jira observation paired with recent GitHub PR | Evaluator emits `STALE` suppression; zero active finding triggered | F2 / F3 |
| **D-09** | 4E-D-01 | Precomputed `CrossSystemStateAlignment` alongside repository topology | Alignment preserved intact; repository topology does not rewrite alignment basis | F2 |
| **D-10** | 4E-D-02 | Multi-provider identity partitioning under identical repository slugs | Composite key scoping (`source_kind:instance_id:entity_id`) prevents false cycles | F2 / F5 |
| **D-11** | 4E-D-04 | Compound quality issue coexistence (`unresolved`, `stale`, `contradictory`) | Canonical sorting and preservation; zero dropped issues | F1 / F5 |
| **D-12** | 4E-D-05 | Full composite bundle under 5 randomized permutation sequences | 100% byte-identical serialized JSON and evaluation summaries | F5 |
| **D-13** | 4E-D-02 | Negative linkage firewall under lexical mention saturation | Mentions remain `mentions`; zero promotion to `explicit_link`; zero transitive linking | F3 |
| **D-14** | 4E-D-01 | Cryptographic chain of custody across compound provenance graph | All provenance refs verified against on-disk SHA-256 digests; zero empty fallbacks | F4 |
| **D-15** | 4E-D-05 | Compound bundle evaluation restricting findings to authorized candidate rules | Zero findings outside `ORBIT-XB-01`, `XB-02`, `XB-03`; zero phantom rules | F1 / F3 |

---

## 7. Methodological Invariant & Generation Contract

Addressing the forensic note recorded at the close of Phase 4E-C:

> **Execution-Derived Artifact Contract:**  
> The qualification generator (`generate_artifacts.py`) must **derive** `verification_status` and `observed_behavior` directly from programmatic assertion execution, rather than declaratively copying `required_behavior`.

Every adversarial case in `adversarial_cases.json` must record:
1. `case_id`
2. `gate`
3. `condition`
4. `required_behavior`
5. `execution_verified` (Boolean derived from live assertion outcome)
6. `observed_behavior` (Extracted dynamically from execution output)
7. `verdict` (`PROVEN` / `FAILED`)

---

## 8. Formal Invariants to Verify

Phase 4E-D verifies the complete set of 20 existing invariants plus 4 new compositional invariants:

### Existing Formal Invariants (20)
- **INV-ID-01 .. INV-ID-04:** Identity isolation & deterministic IDs
- **INV-EV-01 .. INV-EV-03:** Provenance grounding, authentic fixtures & empty digest rejection
- **INV-LK-01 .. INV-LK-02:** Linkage neutrality & explicit link authority
- **INV-ST-01 .. INV-ST-02:** State isolation & external dependency non-completion
- **INV-TM-01 .. INV-TM-02:** Temporal ordering preservation & proximity != causality
- **INV-GR-01 .. INV-GR-03:** Lineage DAG, routing acyclicity & provider-scoped composite keys
- **INV-FW-01 .. INV-FW-04:** Evaluator firewall, anti-Cartesian pairing, fail-closed conflicts & Path A/B isolation

### Compositional Formal Invariants (4 New)
- **INV-CMP-01 (Composite Coexistence):** Simultaneous presence of all 8 evidence collection types in `EvidenceBundle` preserves pairwise orthogonality and byte-identical serialization.
- **INV-CMP-02 (Routing Transparency):** Navigation routing records contextual repository evolution without altering referenced code change or work item endpoints.
- **INV-CMP-03 (Gap Resilience):** Unresolved references, stale observations, and ambiguous observations are scoped to their respective candidate pairs without suppressing independent valid pairs.
- **INV-CMP-04 (Compound Permutation Invariance):** Arbitrary permutation of compound evidence collections produces strictly identical evaluation results and cryptographic digests.

---

## 9. Pass / Acceptance Criteria

Phase 4E-D may be declared **PASS / QUALIFIED** only if all of the following criteria are satisfied:

1. **All 5 Proving Gates PASS** with 100% assertion success.
2. **All 15 Adversarial Scenarios (D-01 to D-15) PROVEN** via executed test assertions.
3. **All 24 Formal Invariants Verified** with machine-readable proof.
4. **Execution-Derived Artifacts:** `adversarial_cases.json` derives outcomes from assertion results.
5. **Zero Production Code Changes:** Qualification operates purely within test and qualification trees unless an existing boundary defect is discovered and authorized.
6. **Full Regression Suite Green:** Total passing tests $\ge 891$ with 0 failures and 0 regressions.
7. **Lossless Provenance:** All supporting fixtures verified on disk with valid SHA-256 digests.
8. **Permutation Determinism:** 5-way permutation trials produce byte-identical serialized bundles and evaluation summaries.

---

## 10. Failure Classification

Any failure encountered during qualification must be classified under the established ORBIT forensic taxonomy:

- **F1 — Contract Violation:** The evidence domain model or type specification is violated.
- **F2 — Integration Violation:** Coexistence of valid evidence types mutates existing semantics.
- **F3 — Inference Leakage:** Contextual metadata causes an unevidenced conclusion or state upgrade.
- **F4 — Provenance Failure:** Claims cannot be cryptographically grounded in authentic evidence.
- **F5 — Determinism Failure:** Equivalent inputs produce divergent digests or finding orders.
- **F6 — Regression:** Previously passing test suites fail or change behavior unexpectedly.
- **F7 — Harness Defect:** The test fixture or assertion logic is defective rather than the engine.

---

## 11. Forbidden Changes During Qualification

The implementing agent must **not**:
- modify `src/shadow_orbit/evaluation.py` (Track A frozen);
- modify `src/shadow_orbit/evidence_evaluation.py` (Track B evaluator frozen);
- modify `src/shadow_orbit/cross_system_fusion.py` (Fusion engine frozen);
- modify Jira or GitHub adapter source files;
- modify the deterministic relationship-ID formula;
- introduce live network calls or database dependencies (MongoDB skips remain expected);
- rewrite locked decisions S-001 through S-034.

---

## 12. Required Machine-Readable Artifacts

The qualification must generate the following artifacts under `qualification/phase4e_d/`:

```text
qualification/phase4e_d/
├── qualification_manifest.json       # Top-level qualification record and gate results
├── input_manifest.json               # Composite fixtures, empirical anchors, and scenario metadata
├── expected_invariants.json          # Formal definitions and statuses for all 24 invariants
├── adversarial_cases.json            # Execution-derived verification records for D-01 through D-15
├── results.json                      # Comprehensive execution verdict and summary metrics
├── determinism.json                  # Multi-permutation cryptographic stability proofs
├── provenance_verification.json      # On-disk SHA-256 fixture verification results
├── composite_evaluation_matrix.json  # Comprehensive compound evaluation comparison data
├── regression_summary.json           # Full regression test counts and baseline comparison
└── phase4e_d_report.md               # Forensic qualification report (mirrored to docs/pass5/)
```

---

## 13. Governance Boundary

This specification defines a **proving experiment**, not a product expansion.

If Phase 4E-D reveals that the existing production integration cleanly handles multi-system composition without semantic leakage, that evidence will be formally recorded to close the milestone.

If a genuine semantic deficiency is uncovered, it must be documented as an explicit forensic finding and returned through the standard ORBIT decision lifecycle before any production code is touched.

**Current State:** **SPECIFICATION DRAFT — NO IMPLEMENTATION AUTHORIZED**
