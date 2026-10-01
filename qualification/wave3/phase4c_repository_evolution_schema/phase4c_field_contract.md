# Phase 4C — Field-by-Field Canonical Contract Specification

**Date:** 2026-09-30  
**Phase:** Pass 5 / Wave 3 / Phase 4C — Formal Repository Evolution Schema Specification  
**Governing Semantic Baseline:** `6d82d123f8bf50316d2b1ab7a025bc5862a474ed` (`6d82d12`)  
**Status:** **SPECIFICATION SPECIFICATION COMPLETE**  

---

## 1. Overview

This document specifies the exact contract for every field in `RepositoryEvolutionRelationship`. For each field, the specification defines its type, nullability, authority, semantic purpose, identity impact, temporal semantics, and serialization constraints.

---

## 2. Field Specifications

---

### Field 1: `relationship_id`
* **Type:** `str` (64-character lowercase hex string).
* **Required:** **YES**.
* **Nullable:** **NO**.
* **Authoritative Source:** Computed deterministically by the evidence ingestion adapter.
* **Deterministic Derivation Rule:**
  $$\text{relationship\_id} = \text{SHA-256}\left(\texttt{source\_instance.instance\_id} + \texttt{"\|"} + \texttt{relationship\_type} + \texttt{"\|"} + \texttt{source\_repository.entity\_id} + \texttt{"\|"} + \texttt{target\_repository.entity\_id}\right)$$
* **Identity Impact:** Primary key for the relationship. Identical relationship definitions produce identical IDs.
* **Temporal Semantics:** None (must not incorporate timestamps).
* **Provenance Requirements:** Grounded through the relationship record's `provenance_refs`.
* **Serialization:** Serialized as string property `"relationship_id"`.

---

### Field 2: `relationship_family`
* **Type:** `Literal["NAVIGATION_ROUTING", "PROJECT_LINEAGE", "REPOSITORY_TOPOLOGY", "ECOSYSTEM_DEPENDENCY"]`.
* **Required:** **YES**.
* **Nullable:** **NO**.
* **Authoritative Source:** Canonical relationship taxonomy specification.
* **Semantic Meaning:** Discriminator partitioning repository relationships into four distinct semantic families with mutually distinct graph and direction rules:
  1. `NAVIGATION_ROUTING`: HTTP/VCS transport routing (`REDIRECT`, `RENAME`, `NAMESPACE_MOVE`).
  2. `PROJECT_LINEAGE`: Historical codebase succession (`PREDECESSOR_SUCCESSOR`).
  3. `REPOSITORY_TOPOLOGY`: Branching/mirroring graph structure (`FORK`, `MIRROR`, `VENDOR_MIRROR`).
  4. `ECOSYSTEM_DEPENDENCY`: Inter-project component consumption (`EXTERNAL_DEPENDENCY`, `ECOSYSTEM_PACKAGING`, `COMPANION_SPECIFICATION`).
* **Identity Impact:** Structural partition; discriminates `family_payload` validation.
* **Temporal Semantics:** None.
* **Provenance Requirements:** Inferred from the nature of the primary source evidence.
* **Serialization:** String enum value.

---

### Field 3: `relationship_type`
* **Type:** `Literal["RENAME", "NAMESPACE_MOVE", "REDIRECT", "PREDECESSOR_SUCCESSOR", "FORK", "MIRROR", "VENDOR_MIRROR", "EXTERNAL_DEPENDENCY", "ECOSYSTEM_PACKAGING", "COMPANION_SPECIFICATION"]`.
* **Required:** **YES**.
* **Nullable:** **NO**.
* **Authoritative Source:** Ingestion adapter based on verified evidence.
* **Allowed Values:** Strictly restricted to the closed 10-value taxonomy.
* **Identity Impact:** Component of the deterministic `relationship_id`.
* **Temporal Semantics:** None.
* **Provenance Requirements:** Requires corresponding primary evidence fixture.
* **Serialization:** String enum value.

---

### Field 4: `source_repository`
* **Type:** `EntityRef`.
* **Required:** **YES**.
* **Nullable:** **NO**.
* **Authoritative Source:** Source evidence fixture.
* **Constraint:** `source_repository.entity_kind == "repository"`. (Enforced by validator; `code_change` or `work_item` strictly prohibited).
* **Semantic Meaning:**
  - For `NAVIGATION_ROUTING`: The requested/origin repository path.
  - For `PROJECT_LINEAGE`: The historical predecessor repository (`stratosphere/stratosphere`).
  - For `REPOSITORY_TOPOLOGY`: The downstream/fork repository.
  - For `ECOSYSTEM_DEPENDENCY`: The consuming project repository (`apache/kafka`).
* **Identity Impact:** Component of `relationship_id`. Does not mutate `source_repository.entity_id`.
* **Temporal Semantics:** Represents the repository identity at the time of observation.
* **Serialization:** Serialized as nested canonical `EntityRef` object.

---

### Field 5: `target_repository`
* **Type:** `EntityRef`.
* **Required:** **YES**.
* **Nullable:** **NO**.
* **Authoritative Source:** Source evidence fixture.
* **Constraint:** `target_repository.entity_kind == "repository"`. (Strictly prohibited from referencing pull requests).
* **Semantic Meaning:**
  - For `NAVIGATION_ROUTING`: The destination canonical repository path (`apache/flink`).
  - For `PROJECT_LINEAGE`: The successor repository (`apache/flink`).
  - For `REPOSITORY_TOPOLOGY`: The upstream parent repository.
  - For `ECOSYSTEM_DEPENDENCY`: The external consumed repository (`facebook/rocksdb`).
* **Identity Impact:** Component of `relationship_id`.
* **Temporal Semantics:** Represents the target repository identity.
* **Serialization:** Serialized as nested canonical `EntityRef` object.

---

### Field 6: `directionality`
* **Type:** `Literal["DIRECTED_FORWARD", "BIDIRECTIONAL_SYMMETRIC"]`.
* **Required:** **YES**.
* **Nullable:** **NO**.
* **Authoritative Source:** Relationship taxonomy specification.
* **Allowed Values:**
  - `BIDIRECTIONAL_SYMMETRIC` ONLY for `MIRROR`.
  - `DIRECTED_FORWARD` for all other 9 relationship types.
* **Identity Impact:** Invariant enforcement; prevents false symmetric reasoning on asymmetric links (e.g. parent is NOT fork of child).
* **Serialization:** String enum value.

---

### Field 7: `transitivity_rule`
* **Type:** `Literal["TRANSITIVE_PERMITTED", "STRICTLY_NON_TRANSITIVE"]`.
* **Required:** **YES**.
* **Nullable:** **NO**.
* **Allowed Values:**
  - `TRANSITIVE_PERMITTED` for `REDIRECT`, `RENAME`, `NAMESPACE_MOVE`, `PREDECESSOR_SUCCESSOR`.
  - `STRICTLY_NON_TRANSITIVE` for `FORK`, `MIRROR`, `VENDOR_MIRROR`, `EXTERNAL_DEPENDENCY`, `ECOSYSTEM_PACKAGING`, `COMPANION_SPECIFICATION`.
* **Semantic Meaning:** Prevents transitive leakage in evaluator queries. For example, Project A depends on B, and B depends on C; A does NOT depend on C's PRs.
* **Serialization:** String enum value.

---

### Field 8: `verification_status`
* **Type:** `Literal["PROVEN", "SUPPORTED", "PARTIALLY_PROVEN", "UNVERIFIED"]`.
* **Required:** **YES**.
* **Nullable:** **NO**.
* **Authoritative Source:** Evidentiary qualification engine.
* **Semantic Meaning:** Standard ORBIT epistemological confidence rating based on source evidence strength.
* **Serialization:** String enum value.

---

### Field 9: `observed_at`
* **Type:** `datetime` (UTC, timezone-aware).
* **Required:** **YES**.
* **Nullable:** **NO**.
* **Authoritative Source:** ObservationContext / Ingestion timestamp.
* **Semantic Meaning:** The exact point in time when the relationship evidence was captured.
* **Invariants:** Must have `tzinfo=timezone.utc`. Never use `datetime.now()` at evaluation time.
* **Serialization:** ISO 8601 string (e.g. `"2026-09-30T16:00:00Z"`).

---

### Field 10: `valid_from`
* **Type:** `datetime | None`.
* **Required:** **NO** (Defaults to `None`).
* **Nullable:** **YES**.
* **Authoritative Source:** Source historical record (e.g. ASF board resolution timestamp, Git import commit timestamp).
* **Semantic Meaning:** Real-world effective beginning of the relationship. `None` indicates effective start date is unrecorded.
* **Invariants:** Must not be synthesized or guessed.
* **Serialization:** ISO 8601 string or `null`.

---

### Field 11: `valid_to`
* **Type:** `datetime | None`.
* **Required:** **NO** (Defaults to `None`).
* **Nullable:** **YES**.
* **Authoritative Source:** Source historical record.
* **Semantic Meaning:** Real-world effective end of the relationship (e.g. dependency replaced or removed). `None` indicates relationship remains active.
* **Serialization:** ISO 8601 string or `null`.

---

### Field 12: `provenance_refs`
* **Type:** `tuple[ProvenanceRef, ...]`.
* **Required:** **YES**.
* **Nullable:** **NO** (Must contain at least 1 `ProvenanceRef`).
* **Authoritative Source:** Ingestion adapter pointing to raw fixture file and JSON locator.
* **Semantic Meaning:** Cryptographic trail to the exact raw evidence file proving this relationship.
* **Serialization:** Array of serialized `ProvenanceRef` objects.

---

### Field 13: `family_payload`
* **Type:** `dict[str, Any]` (Strictly constrained schema).
* **Required:** **YES** (Defaults to empty dict if family requires no extra fields).
* **Nullable:** **NO**.
* **Family Schemas:**
  - `NAVIGATION_ROUTING`: `{"http_status_code": int, "underlying_vcs_id_matched": bool}`
  - `PROJECT_LINEAGE`: `{"governance_event": str}`
  - `REPOSITORY_TOPOLOGY`: `{"fork_point_commit_sha": str}`
  - `ECOSYSTEM_DEPENDENCY`: `{"dependency_scope": str}`
* **Serialization:** JSON object.

---

### Field 14: `semantic_firewall`
* **Type:** `dict[str, bool]`.
* **Required:** **YES**.
* **Nullable:** **NO**.
* **Enforced Values:**
  - `entity_ref_mutation_forbidden`: `True`
  - `linkage_auto_upgrade_forbidden`: `True`
  - `state_transfer_forbidden`: `True`
  - `temporal_causality_inference_forbidden`: `True`
* **Semantic Meaning:** Explicit machine-enforced safety firewall flags preventing the evaluator from misinterpreting repository evolution as entity identity or linkage.
* **Serialization:** JSON object with all booleans set to `true`.
