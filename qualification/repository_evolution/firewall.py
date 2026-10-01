"""Semantic firewall verification functions for Phase 4D qualification.

Authoritative reference:
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_semantic_contract.md
"""

from __future__ import annotations

from typing import Any

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    EvidenceRelationship,
    QualityIssue,
)
from qualification.repository_evolution.schema import (
    RepositoryEvolutionRelationship,
    SemanticFirewall,
)


def assert_entity_ref_immutability(
    observations: tuple[EvidenceObservation, ...],
    original_entity_refs: dict[str, EntityRef],
    relationships: tuple[RepositoryEvolutionRelationship, ...],
) -> None:
    """Verify INV-ID-01: No repository evolution relationship mutates any observation EntityRef."""
    for obs in observations:
        obs_id = obs.observation_context.observation_id
        orig = original_entity_refs.get(obs_id)
        if orig is None:
            continue
        if obs.entity_ref != orig:
            raise AssertionError(
                f"INV-ID-01 VIOLATION: Observation {obs_id} had its EntityRef "
                f"mutated from {orig} to {obs.entity_ref}!"
            )


def assert_linkage_firewall(
    cross_system_rel: EvidenceRelationship,
    repo_evolution_rel: RepositoryEvolutionRelationship,
    expected_kind: str = "mentions",
) -> None:
    """Verify INV-LK-01 & INV-LK-02: Evolution relationships never upgrade linkage kind.

    If cross_system_rel was established as 'mentions' (DECLARED_MENTION), it must
    STRICTLY remain 'mentions' and basis 'lexical_match' regardless of any verified
    predecessor or redirect evolution relationship between repositories.
    """
    if repo_evolution_rel.semantic_firewall.linkage_auto_upgrade_forbidden:
        if expected_kind == "mentions" and cross_system_rel.kind != "mentions":
            raise AssertionError(
                f"INV-LK-01 VIOLATION: Evolution relationship {repo_evolution_rel.relationship_id} "
                f"caused automatic upgrade of linkage kind to {cross_system_rel.kind}!"
            )
        if expected_kind == "mentions" and cross_system_rel.basis == "explicit_metadata":
            raise AssertionError(
                f"INV-LK-01 VIOLATION: Evolution relationship {repo_evolution_rel.relationship_id} "
                f"caused automatic upgrade of linkage basis to {cross_system_rel.basis}!"
            )


def assert_state_firewall(
    work_item_obs: EvidenceObservation,
    code_change_obs: EvidenceObservation,
    repo_evolution_rel: RepositoryEvolutionRelationship,
) -> None:
    """Verify INV-ST-01 & INV-ST-02: Repository evolution never transfers work state.

    Even if code_change_obs is merged in the target repository, work_item_obs
    must retain its authentic state_category (e.g. 'in_progress' or 'to_do') unless
    independently resolved in its native issue tracker.
    """
    work_state = work_item_obs.observed_state
    code_state = code_change_obs.observed_state

    is_pr_merged = (
        getattr(code_state, "is_merged", False)
        or getattr(code_state, "merged_at", None) is not None
        or getattr(code_state, "state", None) == "closed" and getattr(code_state, "merged_at", None) is not None
    )

    if repo_evolution_rel.semantic_firewall.state_transfer_forbidden:
        if is_pr_merged:
            if getattr(work_state, "status_category", None) == "done" and getattr(work_state, "resolved_at", None) is None:
                if repo_evolution_rel.relationship_type == "EXTERNAL_DEPENDENCY":
                    raise AssertionError(
                        "INV-ST-02 VIOLATION: Merged external dependency PR transferred "
                        "done state to unresolved work item!"
                    )
                else:
                    raise AssertionError(
                        f"INV-ST-01 VIOLATION: Merged PR in target repository {repo_evolution_rel.target_repository.entity_id} "
                        "transferred completion state to unresolved work item!"
                    )


def assert_temporal_firewall(
    work_item_obs: EvidenceObservation,
    packaging_code_obs: EvidenceObservation,
    repo_evolution_rel: RepositoryEvolutionRelationship,
) -> str:
    """Verify INV-TM-01 & INV-TM-02: Temporal proximity/order does not imply causality or data error.

    When downstream packaging PR merges after work item resolution, the temporal alignment
    is purely observational INVERTED without invalidating the work item resolution.
    """
    work_state = work_item_obs.observed_state
    code_state = packaging_code_obs.observed_state

    resolved_at = getattr(work_state, "resolved_at", None)
    merged_at = getattr(code_state, "merged_at", None)

    if resolved_at is not None and merged_at is not None:
        if merged_at > resolved_at:
            # Observational outcome is INVERTED for this cross-system pair
            # But work_item_obs is NOT marked invalid or corrupt!
            return "INVERTED"
        elif merged_at < resolved_at:
            return "COHERENT"
        else:
            return "COHERENT"
    return "INDETERMINATE"
