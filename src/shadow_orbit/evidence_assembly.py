"""Cross-system manifest and EvidenceBundle orchestration.

Assembles independently produced Jira and GitHub evidence artifacts into
the canonical EvidenceBundle container without modifying or re-invoking
any source-specific pipeline.

Pure orchestration and structural assembly:
- No findings, scoring, severity, confidence, risk, or recommendations.
- No semantic inference or transitive relationship discovery.
- Fully deterministic: equivalent inputs produce equivalent canonical output.
- Joint endpoint-observation validation directly links relationship endpoints
  to corresponding accepted observations.

Design reference: docs/cse1-design.md
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceBundle,
    EvidenceObservation,
    EvidenceRelationship,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    RelationshipBasis,
    RelationshipKind,
    SourceInstance,
    UnresolvedReference,
)
from shadow_orbit.github_normalization import NormalizedGitHubFixture


# ── Authorized Predicate and Entity Vocabularies ─────────────────────

_CSE_1_5_STRUCTURAL_PREDICATES: frozenset[RelationshipKind] = frozenset({
    "belongs_to_repository",
    "review_of",
    "has_head_branch",
    "has_base_branch",
    "contains_commit",
    "has_head_commit",
    "has_base_commit",
})

_JIRA_ENTITY_KINDS: frozenset[str] = frozenset({"jira_issue"})

_GITHUB_ENTITY_KINDS: frozenset[str] = frozenset({
    "github_repository",
    "github_branch",
    "github_commit",
    "github_pull_request",
    "github_review",
})


# ── Internal Deterministic Sorting and Key Helpers ───────────────────

def _provenance_sort_key(p: ProvenanceRef) -> tuple[str, str, str, str, str]:
    """Deterministic sort key for a ProvenanceRef."""
    return (
        p.source_instance.instance_id,
        p.observation_id,
        p.fixture_id or "",
        p.record_locator or "",
        p.source_field_path or "",
    )


def _quality_issue_sort_key(q: QualityIssue) -> tuple[str, str]:
    """Deterministic sort key for a QualityIssue."""
    return (q.code, q.message)


def _deduplicate_relationships(
    relationships: tuple[EvidenceRelationship, ...],
) -> tuple[EvidenceRelationship, ...]:
    """Deduplicate relationships with identical logical endpoints and basis.

    Merges provenance_refs (union, deterministically sorted) and quality_issues.
    """
    # Key: (subject_ref, object_ref, kind, basis, subject_obs_id, object_obs_id)
    # Value: (EvidenceRelationship prototype, set[ProvenanceRef], set[QualityIssue])
    dedup: dict[
        tuple[EntityRef, EntityRef, RelationshipKind, RelationshipBasis, str, str],
        tuple[EvidenceRelationship, list[ProvenanceRef], list[QualityIssue]],
    ] = {}

    for rel in relationships:
        key = (
            rel.subject_ref,
            rel.object_ref,
            rel.kind,
            rel.basis,
            rel.subject_observation_id,
            rel.object_observation_id,
        )
        if key not in dedup:
            dedup[key] = (rel, list(rel.provenance_refs), list(rel.quality_issues))
        else:
            _, prov_list, qi_list = dedup[key]
            for p in rel.provenance_refs:
                if p not in prov_list:
                    prov_list.append(p)
            for q in rel.quality_issues:
                if q not in qi_list:
                    qi_list.append(q)

    result: list[EvidenceRelationship] = []
    for base_rel, prov_list, qi_list in dedup.values():
        sorted_prov = tuple(sorted(prov_list, key=_provenance_sort_key))
        sorted_qi = tuple(sorted(qi_list, key=_quality_issue_sort_key))
        result.append(
            EvidenceRelationship(
                subject_ref=base_rel.subject_ref,
                object_ref=base_rel.object_ref,
                kind=base_rel.kind,
                basis=base_rel.basis,
                subject_observation_id=base_rel.subject_observation_id,
                object_observation_id=base_rel.object_observation_id,
                provenance_refs=sorted_prov,
                quality_issues=sorted_qi,
            )
        )

    result.sort(
        key=lambda r: (
            r.kind,
            r.basis,
            r.subject_ref.entity_id,
            r.object_ref.entity_id,
            r.subject_observation_id,
            r.object_observation_id,
        )
    )
    return tuple(result)


def _deduplicate_unresolved(
    unresolved: tuple[UnresolvedReference, ...],
) -> tuple[UnresolvedReference, ...]:
    """Deduplicate unresolved references with identical logical target and reason.

    Reason is explicitly part of the logical identity key; different reasons
    represent materially different evidence states and are preserved separately.
    Merges provenance_refs (union, deterministically sorted).
    """
    # Key: (source_ref, source_obs_id, target_entity_kind, target_identifier, kind, reason)
    # Value: (UnresolvedReference prototype, list[ProvenanceRef])
    dedup: dict[
        tuple[EntityRef, str, str, str, RelationshipKind, str],
        tuple[UnresolvedReference, list[ProvenanceRef]],
    ] = {}

    for unres in unresolved:
        key = (
            unres.source_ref,
            unres.source_observation_id,
            unres.target_entity_kind,
            unres.target_identifier,
            unres.relationship_kind,
            unres.reason,
        )
        if key not in dedup:
            dedup[key] = (unres, list(unres.provenance_refs))
        else:
            _, prov_list = dedup[key]
            for p in unres.provenance_refs:
                if p not in prov_list:
                    prov_list.append(p)

    result: list[UnresolvedReference] = []
    for base_unres, prov_list in dedup.values():
        sorted_prov = tuple(sorted(prov_list, key=_provenance_sort_key))
        result.append(
            UnresolvedReference(
                source_ref=base_unres.source_ref,
                source_observation_id=base_unres.source_observation_id,
                target_entity_kind=base_unres.target_entity_kind,
                target_identifier=base_unres.target_identifier,
                relationship_kind=base_unres.relationship_kind,
                reason=base_unres.reason,
                provenance_refs=sorted_prov,
            )
        )

    result.sort(
        key=lambda u: (
            u.relationship_kind,
            u.source_ref.entity_id,
            u.target_entity_kind,
            u.target_identifier,
            u.reason,
        )
    )
    return tuple(result)


# ── Public Assembly Function ─────────────────────────────────────────

def assemble_evidence_bundle(
    bundle_id: str,
    bundle_version: str,
    jira_context: ObservationContext | None = None,
    jira_observations: tuple[EvidenceObservation, ...] = (),
    jira_quality_issues: tuple[QualityIssue, ...] = (),
    github_fixture: NormalizedGitHubFixture | None = None,
    github_structural_relationships: tuple[EvidenceRelationship, ...] = (),
    github_structural_unresolved: tuple[UnresolvedReference, ...] = (),
    github_mention_relationships: tuple[EvidenceRelationship, ...] = (),
    github_mention_unresolved: tuple[UnresolvedReference, ...] = (),
) -> EvidenceBundle:
    """Assemble independently produced evidence artifacts into an EvidenceBundle.

    Parameters
    ----------
    bundle_id:
        Non-empty caller-assigned bundle identifier.
    bundle_version:
        Non-empty caller-assigned bundle version string.
    jira_context:
        ObservationContext produced by the Jira pipeline (source_kind="jira").
    jira_observations:
        EvidenceObservation instances for Jira issues.
    jira_quality_issues:
        Quality issues from Jira adaptation.
    github_fixture:
        NormalizedGitHubFixture produced by GitHub normalization.
    github_structural_relationships:
        Structural relationships resolved from GitHub fixture (CSE-1.5).
    github_structural_unresolved:
        Unresolved structural references from GitHub fixture (CSE-1.5).
    github_mention_relationships:
        Cross-system lexical mentions resolved between GitHub and Jira (CSE-1.6).
    github_mention_unresolved:
        Unresolved mention references from GitHub fixture (CSE-1.6).

    Returns
    -------
    EvidenceBundle
        Immutable, canonically sorted cross-system evidence container.
    """
    # ── 1. Input Validation ──────────────────────────────────────────
    if not isinstance(bundle_id, str) or not bundle_id.strip():
        raise ValueError("bundle_id must be a non-empty string.")
    if not isinstance(bundle_version, str) or not bundle_version.strip():
        raise ValueError("bundle_version must be a non-empty string.")

    if jira_context is not None:
        if jira_context.source_instance.source_kind != "jira":
            raise ValueError(
                f"jira_context must have source_kind='jira', "
                f"got {jira_context.source_instance.source_kind!r}."
            )
    elif jira_observations:
        raise ValueError(
            "jira_observations supplied but jira_context is None."
        )

    if github_fixture is not None:
        if github_fixture.source_instance.source_kind != "github":
            raise ValueError(
                f"github_fixture must have source_kind='github', "
                f"got {github_fixture.source_instance.source_kind!r}."
            )
    elif (
        github_structural_relationships
        or github_structural_unresolved
        or github_mention_relationships
        or github_mention_unresolved
    ):
        raise ValueError(
            "GitHub relationships or unresolved references supplied "
            "but github_fixture is None."
        )

    # ── 2. Collect Observation Contexts ──────────────────────────────
    contexts: list[ObservationContext] = []
    if jira_context is not None:
        contexts.append(jira_context)
    if github_fixture is not None:
        contexts.append(github_fixture.observation_context)

    # Check context ID uniqueness
    context_ids = [c.observation_id for c in contexts]
    if len(set(context_ids)) != len(context_ids):
        raise ValueError(
            "Duplicate observation_id across supplied observation contexts."
        )

    sorted_contexts = sorted(
        contexts,
        key=lambda c: (c.source_instance.instance_id, c.observation_id),
    )

    # ── 3. Collect Observations (no dedup, sorted canonically) ────────
    all_observations: list[EvidenceObservation] = list(jira_observations)
    if github_fixture is not None:
        all_observations.extend(github_fixture.observations)

    sorted_observations = sorted(
        all_observations,
        key=lambda o: (
            o.entity_ref.source_instance.instance_id,
            o.entity_ref.entity_kind,
            o.entity_ref.entity_id,
        ),
    )

    # ── 4. Combine & Deduplicate Relationships ───────────────────────
    raw_relationships = (
        github_structural_relationships + github_mention_relationships
    )
    deduped_relationships = _deduplicate_relationships(raw_relationships)

    # ── 5. Combine & Deduplicate Unresolved References ───────────────
    raw_unresolved = (
        github_structural_unresolved + github_mention_unresolved
    )
    deduped_unresolved = _deduplicate_unresolved(raw_unresolved)

    # ── 6. Combine Quality Issues ────────────────────────────────────
    all_quality_issues: list[QualityIssue] = list(jira_quality_issues)
    if github_fixture is not None:
        all_quality_issues.extend(github_fixture.quality_issues)

    # Deduplicate quality issues by (code, message, subject_ref, subject_scope)
    deduped_quality: list[QualityIssue] = []
    for q in all_quality_issues:
        if q not in deduped_quality:
            deduped_quality.append(q)
    deduped_quality.sort(key=_quality_issue_sort_key)

    # ── 7. Construct and Return Frozen Bundle ────────────────────────
    return EvidenceBundle(
        bundle_id=bundle_id,
        bundle_version=bundle_version,
        observation_contexts=tuple(sorted_contexts),
        observations=tuple(sorted_observations),
        relationships=deduped_relationships,
        unresolved_references=deduped_unresolved,
        quality_issues=tuple(deduped_quality),
    )


# ── Public Validation Function ───────────────────────────────────────

def validate_evidence_bundle(
    bundle: EvidenceBundle,
) -> tuple[QualityIssue, ...]:
    """Validate internal consistency and integrity of an assembled EvidenceBundle.

    Performs direct verification of:
    1. Joint endpoint-observation pairing: subject_observation_id and
       object_observation_id must resolve to accepted observations whose
       entity_ref matches the corresponding endpoint ref.
    2. Observation context resolution for observations and provenance.
    3. Basis-predicate compatibility (CSE-1.5 structural vs CSE-1.6 lexical).
    4. Provenance observation context existence.
    5. Prevention of cross-system entity kind contamination.
    6. Prevention of contradictory resolved-vs-unresolved references.
    7. Accidental duplicate observation identity detection.
    8. Observation context uniqueness.

    Returns
    -------
    tuple[QualityIssue, ...]
        Structured quality issues detailing any contract discrepancies.
        Returns empty tuple when bundle is internally consistent.
        Does not raise exceptions.
    """
    issues: list[QualityIssue] = []

    # Map observation_id to registered ObservationContext
    contexts_by_id: dict[str, ObservationContext] = {}
    for c in bundle.observation_contexts:
        if c.observation_id not in contexts_by_id:
            contexts_by_id[c.observation_id] = c

    # Context uniqueness check
    context_id_counts = Counter(
        c.observation_id for c in bundle.observation_contexts
    )
    for ctx_id, count in context_id_counts.items():
        if count > 1:
            issues.append(
                QualityIssue(
                    code="invalid",
                    message=f"Duplicate observation context ID '{ctx_id}' found {count} times.",
                    subject_scope="observation_context:identity",
                )
            )

    # Observation lookup: (EntityRef, observation_id)
    obs_identity_counts = Counter(
        (o.entity_ref, o.observation_context.observation_id)
        for o in bundle.observations
    )
    for (ref, obs_id), count in obs_identity_counts.items():
        if count > 1:
            issues.append(
                QualityIssue(
                    code="invalid",
                    message=(
                        f"Duplicate observation identity for entity '{ref.entity_id}' "
                        f"in observation context '{obs_id}' ({count} occurrences)."
                    ),
                    subject_ref=ref,
                    subject_scope="observation:identity",
                )
            )

    # Helper to validate supporting provenance references
    def _validate_provenance_refs(
        prov_refs: tuple[ProvenanceRef, ...],
        subject_ref: EntityRef | None,
        scope: str,
        owner_desc: str,
        require_non_empty: bool = True,
    ) -> None:
        if require_non_empty and not prov_refs:
            issues.append(
                QualityIssue(
                    code="missing",
                    message=f"{owner_desc} has no supporting provenance.",
                    subject_ref=subject_ref,
                    subject_scope=scope,
                )
            )
        for p in prov_refs:
            reg_ctx = contexts_by_id.get(p.observation_id)
            if reg_ctx is None:
                issues.append(
                    QualityIssue(
                        code="invalid",
                        message=(
                            f"{owner_desc} provenance references unknown "
                            f"observation_id '{p.observation_id}'."
                        ),
                        subject_ref=subject_ref,
                        subject_scope="provenance:context",
                    )
                )
            elif p.source_instance != reg_ctx.source_instance:
                issues.append(
                    QualityIssue(
                        code="invalid",
                        message=(
                            f"{owner_desc} provenance source_instance '{p.source_instance.instance_id}' "
                            f"does not match registered context source_instance "
                            f"'{reg_ctx.source_instance.instance_id}' for observation_id '{p.observation_id}'."
                        ),
                        subject_ref=subject_ref,
                        subject_scope="provenance:context",
                    )
                )

    # Observation context resolution & identity contamination
    for obs in bundle.observations:
        ref = obs.entity_ref
        obs_ctx_id = obs.observation_context.observation_id
        reg_ctx = contexts_by_id.get(obs_ctx_id)

        if reg_ctx is None:
            issues.append(
                QualityIssue(
                    code="unresolved",
                    message=(
                        f"Observation '{ref.entity_id}' references observation context "
                        f"'{obs_ctx_id}' which is not in bundle.observation_contexts."
                    ),
                    subject_ref=ref,
                    subject_scope="observation:context",
                )
            )
        elif obs.observation_context.source_instance != reg_ctx.source_instance:
            issues.append(
                QualityIssue(
                    code="invalid",
                    message=(
                        f"Observation '{ref.entity_id}' context source_instance "
                        f"'{obs.observation_context.source_instance.instance_id}' does not match "
                        f"registered context source_instance '{reg_ctx.source_instance.instance_id}' "
                        f"for observation_id '{obs_ctx_id}'."
                    ),
                    subject_ref=ref,
                    subject_scope="observation:context",
                )
            )

        # Cross-system entity contamination check
        if ref.source_instance.source_kind == "jira":
            if ref.entity_kind not in _JIRA_ENTITY_KINDS:
                issues.append(
                    QualityIssue(
                        code="invalid",
                        message=(
                            f"Entity '{ref.entity_id}' has source_kind 'jira' "
                            f"but invalid entity_kind '{ref.entity_kind}'."
                        ),
                        subject_ref=ref,
                        subject_scope="entity:identity",
                    )
                )
        elif ref.source_instance.source_kind == "github":
            if ref.entity_kind not in _GITHUB_ENTITY_KINDS:
                issues.append(
                    QualityIssue(
                        code="invalid",
                        message=(
                            f"Entity '{ref.entity_id}' has source_kind 'github' "
                            f"but invalid entity_kind '{ref.entity_kind}'."
                        ),
                        subject_ref=ref,
                        subject_scope="entity:identity",
                    )
                )

        # Provenance context and source instance check
        _validate_provenance_refs(
            obs.provenance_refs,
            subject_ref=ref,
            scope="provenance:context",
            owner_desc=f"Observation '{ref.entity_id}'",
            require_non_empty=False,
        )

    # ── Relationship validation ──────────────────────────────────────
    # Lookup for joint pairing: (EntityRef, observation_id)
    known_obs_pairs: set[tuple[EntityRef, str]] = set(obs_identity_counts.keys())

    for rel in bundle.relationships:
        # Invariant 1: Joint endpoint-observation pairing
        subject_pair = (rel.subject_ref, rel.subject_observation_id)
        if subject_pair not in known_obs_pairs:
            issues.append(
                QualityIssue(
                    code="unresolved",
                    message=(
                        f"Relationship subject endpoint '{rel.subject_ref.entity_id}' "
                        f"does not resolve to an accepted observation in observation "
                        f"context '{rel.subject_observation_id}'."
                    ),
                    subject_ref=rel.subject_ref,
                    subject_scope="relationship:endpoint",
                )
            )

        object_pair = (rel.object_ref, rel.object_observation_id)
        if object_pair not in known_obs_pairs:
            issues.append(
                QualityIssue(
                    code="unresolved",
                    message=(
                        f"Relationship object endpoint '{rel.object_ref.entity_id}' "
                        f"does not resolve to an accepted observation in observation "
                        f"context '{rel.object_observation_id}'."
                    ),
                    subject_ref=rel.object_ref,
                    subject_scope="relationship:endpoint",
                )
            )

        # Invariant 3: Basis-predicate compatibility
        if rel.basis == "structural_association":
            if rel.kind not in _CSE_1_5_STRUCTURAL_PREDICATES:
                issues.append(
                    QualityIssue(
                        code="invalid",
                        message=(
                            f"Relationship kind '{rel.kind}' is not a valid structural "
                            f"predicate for basis 'structural_association'."
                        ),
                        subject_ref=rel.subject_ref,
                        subject_scope="relationship:basis",
                    )
                )
        elif rel.basis == "lexical_match":
            if rel.kind != "mentions":
                issues.append(
                    QualityIssue(
                        code="invalid",
                        message=(
                            f"Relationship kind '{rel.kind}' is invalid for basis "
                            f"'lexical_match'; expected 'mentions'."
                        ),
                        subject_ref=rel.subject_ref,
                        subject_scope="relationship:basis",
                    )
                )
        else:
            issues.append(
                QualityIssue(
                    code="invalid",
                    message=f"Unsupported relationship basis '{rel.basis}'.",
                    subject_ref=rel.subject_ref,
                    subject_scope="relationship:basis",
                )
            )

        # Invariant 4: Relationship supporting provenance check
        _validate_provenance_refs(
            rel.provenance_refs,
            subject_ref=rel.subject_ref,
            scope="relationship:provenance",
            owner_desc=f"Relationship '{rel.kind}'",
            require_non_empty=True,
        )

    # ── Unresolved reference validation ──────────────────────────────
    for unres in bundle.unresolved_references:
        # Invariant 2: Joint source endpoint pairing for unresolved reference
        source_pair = (unres.source_ref, unres.source_observation_id)
        if source_pair not in known_obs_pairs:
            issues.append(
                QualityIssue(
                    code="unresolved",
                    message=(
                        f"Unresolved reference source endpoint '{unres.source_ref.entity_id}' "
                        f"does not resolve to an accepted observation in observation "
                        f"context '{unres.source_observation_id}'."
                    ),
                    subject_ref=unres.source_ref,
                    subject_scope="unresolved_reference:source",
                )
            )

        # Invariant 4: Unresolved reference supporting provenance check
        _validate_provenance_refs(
            unres.provenance_refs,
            subject_ref=unres.source_ref,
            scope="unresolved_reference:provenance",
            owner_desc=f"Unresolved reference '{unres.relationship_kind}'",
            require_non_empty=True,
        )

        # Invariant 6: No unresolved-as-resolved contradiction
        for rel in bundle.relationships:
            if (
                rel.subject_ref == unres.source_ref
                and rel.kind == unres.relationship_kind
                and rel.object_ref.entity_kind == unres.target_entity_kind
            ):
                # Check target identifier match
                target_id = unres.target_identifier
                obj_id = rel.object_ref.entity_id
                if (
                    obj_id == target_id
                    or obj_id.endswith("/" + target_id)
                ):
                    issues.append(
                        QualityIssue(
                            code="contradictory",
                            message=(
                                f"Reference from '{unres.source_ref.entity_id}' to "
                                f"'{target_id}' ({unres.relationship_kind}) is recorded "
                                f"as both resolved and unresolved."
                            ),
                            subject_ref=unres.source_ref,
                            subject_scope="relationship:resolution",
                        )
                    )

    issues.sort(key=_quality_issue_sort_key)
    return tuple(issues)
