# ADR-REPOSITORY-EVOLUTION-SCHEMA: Canonical Data Contract for Repository Evolution

* **Status:** **PROPOSED / SPECIFICATION COMPLETE — IMPLEMENTATION NOT AUTHORIZED IN PHASE 4C**
* **Date:** 2026-09-30
* **Author:** Project ORBIT Forensic Architecture Team
* **Deciders:** Founding Software Engineer & Lead Architect
* **Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)
* **Consolidation HEAD:** `ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab`
* **Direct Parent Decision:** `ADR-REPOSITORY-IDENTITY-EVOLUTION.md` (Phase 4B, Option B Adoption)
* **Related ADRs:** ADR-001 (Provenance & Determinism), ADR-005 (Cross-System Alignments), ADR-006 (Track B Evidence Evaluation)

---

## 1. Context & Architectural Lineage

In Phase 4B, Project ORBIT resolved the fundamental research question of repository identity under real-world evolution by adopting **Option B: Minimal Evolution Metadata**:
> *"Retain immutable `EntityRef` (`owner/repo/number`) as primary identity. Model verified evolution as an explicit, typed, directional metadata relationship without modifying core evaluator semantics or auto-upgrading linkage."*

Phase 4C now establishes the exact, formal data contract required to specify Option B without ambiguity.

---

## 2. Decision

We define the canonical schema contract for repository evolution as a dedicated canonical dataclass:
$$\mathbf{RepositoryEvolutionRelationship}$$

### Key Architectural Specifications:
1. **Schema Placement:** Placed in a dedicated optional collection on `EvidenceBundle`:
   ```python
   repository_relationships: tuple[RepositoryEvolutionRelationship, ...] = ()
   ```
2. **Strict Repository-Level Endpoints:** Both `source_repository` and `target_repository` MUST have `entity_kind == "repository"`. Passing a code change or work item entity is a fatal validation error (`INV-ID-02`).
3. **Four Relationship Families:** The contract groups the 10 Phase 4B evolution types into four distinct structural families:
   - `NAVIGATION_ROUTING`: `REDIRECT`, `RENAME`, `NAMESPACE_MOVE`
   - `PROJECT_LINEAGE`: `PREDECESSOR_SUCCESSOR`
   - `REPOSITORY_TOPOLOGY`: `FORK`, `MIRROR`, `VENDOR_MIRROR`
   - `ECOSYSTEM_DEPENDENCY`: `EXTERNAL_DEPENDENCY`, `ECOSYSTEM_PACKAGING`, `COMPANION_SPECIFICATION`
4. **Deterministic Identity:** Primary key `relationship_id` is computed deterministically via SHA-256 over invariant components:
   $$\text{relationship\_id} = \text{SHA-256}(\text{instance\_id} + \texttt{"\|"} + \text{type} + \texttt{"\|"} + \text{source\_id} + \texttt{"\|"} + \text{target\_id})$$
5. **Mandatory Cryptographic Provenance:** Every relationship carries at least one `ProvenanceRef` pointing to verified source evidence.
6. **Implementation Firewall:**  
   $$\mathbf{IMPLEMENTATION\ IS\ NOT\ AUTHORIZED\ IN\ PHASE\ 4C.}$$  
   Zero lines of code in `src/shadow_orbit/` are modified. Implementation requires separate authorization in a future phase.

---

## 3. Consequences

### Positive Consequences:
- **Zero Identity Mutation:** Code change `EntityRef` (`stratosphere/stratosphere/126` vs `apache/flink/126`) remains 100% immutable and collision-proof.
- **Linkage Neutrality Guaranteed:** `DECLARED_MENTION` is never upgraded to `EXPLICIT_LINK` by repository evolution metadata.
- **100% Backward Compatibility:** Historical bundles without `repository_relationships` deserialize with zero diff.
- **Complete Invariant Specification:** 11 formal invariants (`INV-ID-01` through `INV-GR-03`) define fail-closed behavior for future engineering.

### Negative Consequences / Trade-offs:
- Future evaluators must explicitly query `repository_relationships` when contextualizing external dependencies or predecessor project findings.

---

## 4. Explicit Non-Goals

The following remain **strictly prohibited**:
- No runtime `RepositoryAliasService` or `RepositoryRegistry` class.
- No `ProviderRegistry` or `PluginManager`.
- No fuzzy string distance matching or heuristic clustering.
- No automatic URL rewriting in raw evidence fixtures.
- No collapsing of forks or external dependencies into primary project codebases.

---

## 5. Phase 4D Qualification Requirement

Prior to production code implementation, Phase 4D must execute a controlled prototype qualification validating that the `RepositoryEvolutionRelationship` schema safely represents authentic cases (`FLINK-1359`, `stratosphere#126`, `KAFKA-9168`, `FLINK-20650`) without regressing the 817 passing tests.
