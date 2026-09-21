"""Structural relationship resolver for GitHub evidence observations (CSE-1.5).

Resolves structural associations from normalized GitHub fixtures into
strongly typed EvidenceRelationship instances and explicit UnresolvedReference
instances.

Supported structural relationships:
  - belongs_to_repository (branch -> repo, commit -> repo, PR -> repo)
  - review_of (review -> PR)
  - has_head_branch (PR -> head branch, fork-aware)
  - has_base_branch (PR -> base branch)
  - contains_commit (PR -> commit, from explicit pull_request_commits associations)
  - has_head_commit (PR -> head commit, from explicit head_commit_sha)
  - has_base_commit (PR -> base commit, from explicit base_commit_sha)

All resolved relationships carry:
  - subject EntityRef and object EntityRef
  - relationship kind and basis ("structural_association")
  - subject_observation_id and object_observation_id
  - supporting ProvenanceRef instances
  - applicable QualityIssue instances

Unresolved references are emitted when a referenced endpoint does not
correspond to an accepted EvidenceObservation (missing, quarantined, or
ambiguous).

Zero Jira key extraction, text matching, mentions, temporal correlation,
transitive derivation, scoring, or management interpretation.
"""

from __future__ import annotations

from typing import Any

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    EvidenceRelationship,
    GitHubBranchState,
    GitHubCommitState,
    GitHubPullRequestState,
    GitHubRepositoryState,
    GitHubReviewState,
    ProvenanceRef,
    QualityIssue,
    RelationshipBasis,
    RelationshipKind,
    SourceInstance,
    UnresolvedReference,
)
from shadow_orbit.github_normalization import NormalizedGitHubFixture


RELATIONSHIP_BASIS: RelationshipBasis = "structural_association"


def _sort_provenance_key(p: ProvenanceRef) -> tuple[str, str, str, str, str]:
    return (
        p.source_instance.instance_id,
        p.observation_id,
        p.fixture_id or "",
        p.record_locator or "",
        p.source_field_path or "",
    )


def _sort_relationship_key(
    rel: EvidenceRelationship,
) -> tuple[str, str, str, str, str]:
    return (
        rel.kind,
        rel.subject_ref.entity_id,
        rel.object_ref.entity_id,
        rel.subject_observation_id,
        rel.object_observation_id,
    )


def _sort_unresolved_key(
    unres: UnresolvedReference,
) -> tuple[str, str, str, str, str]:
    return (
        unres.relationship_kind,
        unres.source_ref.entity_id,
        unres.target_entity_kind,
        unres.target_identifier,
        unres.reason,
    )


def resolve_github_relationships(
    normalized: NormalizedGitHubFixture,
) -> tuple[tuple[EvidenceRelationship, ...], tuple[UnresolvedReference, ...]]:
    """Resolve all structural relationships from a normalized GitHub fixture.

    Parameters
    ----------
    normalized:
        An immutable NormalizedGitHubFixture produced by normalize_github_fixture.

    Returns
    -------
    tuple of (relationships, unresolved_references):
        relationships:
            Resolved structural relationships whose endpoints both exist in
            accepted observations. Deterministically ordered and deduplicated.
        unresolved_references:
            Explicit evidence for references that could not be resolved against
            accepted observations. Deterministically ordered.
    """
    source_instance = normalized.source_instance
    fixture_id = str(normalized.raw_document.get("fixture_id", ""))

    # ── Index accepted observations by (entity_kind, entity_id) ──────
    obs_by_kind_and_id: dict[tuple[str, str], EvidenceObservation] = {}
    for obs in normalized.observations:
        key = (obs.entity_ref.entity_kind, obs.entity_ref.entity_id)
        obs_by_kind_and_id[key] = obs

    # ── Index quarantined records by (entity_kind, source_id) ────────
    quarantined_by_kind_and_id: dict[tuple[str, str], str] = {}
    for q in normalized.quarantined_records:
        if q.source_id is not None:
            quarantined_by_kind_and_id[(q.entity_kind, q.source_id)] = (
                q.reason_code
            )

    relationships: list[EvidenceRelationship] = []
    unresolved_list: list[UnresolvedReference] = []

    # Map for deduplicating logical edges while aggregating provenance
    # Key: (subject_ref, kind, object_ref, basis, subject_obs_id, object_obs_id)
    # Value: list[ProvenanceRef]
    dedup_relationships: dict[
        tuple[EntityRef, RelationshipKind, EntityRef, RelationshipBasis, str, str],
        list[ProvenanceRef],
    ] = {}

    # Map for deduplicating unresolved references while aggregating provenance
    # Key: (source_ref, source_obs_id, target_entity_kind, target_identifier, relationship_kind, reason)
    # Value: list[ProvenanceRef]
    dedup_unresolved: dict[
        tuple[EntityRef, str, str, str, RelationshipKind, str],
        list[ProvenanceRef],
    ] = {}

    def _record_relationship(
        subject_ref: EntityRef,
        object_ref: EntityRef,
        kind: RelationshipKind,
        subject_obs_id: str,
        object_obs_id: str,
        prov_refs: tuple[ProvenanceRef, ...],
        quality_issues: tuple[QualityIssue, ...] = (),
    ) -> None:
        key = (
            subject_ref,
            kind,
            object_ref,
            RELATIONSHIP_BASIS,
            subject_obs_id,
            object_obs_id,
        )
        if key not in dedup_relationships:
            dedup_relationships[key] = list(prov_refs)
        else:
            for p in prov_refs:
                if p not in dedup_relationships[key]:
                    dedup_relationships[key].append(p)

    def _record_unresolved(
        source_ref: EntityRef,
        source_obs_id: str,
        target_entity_kind: str,
        target_identifier: str,
        kind: RelationshipKind,
        reason: str,
        prov_refs: tuple[ProvenanceRef, ...],
    ) -> None:
        key = (
            source_ref,
            source_obs_id,
            target_entity_kind,
            target_identifier,
            kind,
            reason,
        )
        if key not in dedup_unresolved:
            dedup_unresolved[key] = list(prov_refs)
        else:
            for p in prov_refs:
                if p not in dedup_unresolved[key]:
                    dedup_unresolved[key].append(p)

    for obs in normalized.observations:
        ref = obs.entity_ref
        kind = ref.entity_kind
        eid = ref.entity_id
        obs_id = obs.observation_context.observation_id
        base_prov = obs.provenance_refs[0] if obs.provenance_refs else ProvenanceRef(
            source_instance=source_instance,
            observation_id=obs_id,
            fixture_id=fixture_id,
        )

        # ── 1. belongs_to_repository ─────────────────────────────────
        if kind in ("github_branch", "github_commit", "github_pull_request"):
            # Entity IDs are scoped as: f"{repo_id}/{child_id}"
            repo_id = eid.split("/")[0]
            repo_key = ("github_repository", repo_id)
            repo_obs = obs_by_kind_and_id.get(repo_key)

            if repo_obs is not None:
                _record_relationship(
                    subject_ref=ref,
                    object_ref=repo_obs.entity_ref,
                    kind="belongs_to_repository",
                    subject_obs_id=obs_id,
                    object_obs_id=repo_obs.observation_context.observation_id,
                    prov_refs=obs.provenance_refs,
                )
            else:
                q_reason = quarantined_by_kind_and_id.get(repo_key)
                if q_reason:
                    reason = (
                        f"Containing repository '{repo_id}' was quarantined ({q_reason})."
                    )
                else:
                    reason = (
                        f"Containing repository '{repo_id}' was not observed."
                    )
                _record_unresolved(
                    source_ref=ref,
                    source_obs_id=obs_id,
                    target_entity_kind="github_repository",
                    target_identifier=repo_id,
                    kind="belongs_to_repository",
                    reason=reason,
                    prov_refs=obs.provenance_refs,
                )

        # ── 2. review_of ─────────────────────────────────────────────
        elif kind == "github_review":
            # Review IDs are scoped as: f"{repo_id}/{pr_number}/{review_id}"
            parts = eid.split("/")
            if len(parts) >= 3:
                pr_entity_id = f"{parts[0]}/{parts[1]}"
                pr_key = ("github_pull_request", pr_entity_id)
                pr_obs = obs_by_kind_and_id.get(pr_key)

                if pr_obs is not None:
                    _record_relationship(
                        subject_ref=ref,
                        object_ref=pr_obs.entity_ref,
                        kind="review_of",
                        subject_obs_id=obs_id,
                        object_obs_id=pr_obs.observation_context.observation_id,
                        prov_refs=obs.provenance_refs,
                    )
                else:
                    q_reason = quarantined_by_kind_and_id.get(pr_key)
                    if q_reason:
                        reason = (
                            f"Target pull request '{pr_entity_id}' was quarantined ({q_reason})."
                        )
                    else:
                        reason = (
                            f"Target pull request '{pr_entity_id}' was not observed."
                        )
                    _record_unresolved(
                        source_ref=ref,
                        source_obs_id=obs_id,
                        target_entity_kind="github_pull_request",
                        target_identifier=pr_entity_id,
                        kind="review_of",
                        reason=reason,
                        prov_refs=obs.provenance_refs,
                    )

        # ── PR-specific relationships ────────────────────────────────
        if kind == "github_pull_request" and isinstance(
            obs.observed_state, GitHubPullRequestState
        ):
            pr_state = obs.observed_state
            repo_id = eid.split("/")[0]

            # ── 3. has_base_branch ───────────────────────────────────
            if pr_state.target_branch is not None:
                base_branch_id = f"{repo_id}/{pr_state.target_branch}"
                branch_key = ("github_branch", base_branch_id)
                target_branch_obs = obs_by_kind_and_id.get(branch_key)
                field_prov = ProvenanceRef(
                    source_instance=source_instance,
                    observation_id=obs_id,
                    fixture_id=fixture_id,
                    record_locator=base_prov.record_locator,
                    source_field_path="target_branch",
                )

                if target_branch_obs is not None:
                    _record_relationship(
                        subject_ref=ref,
                        object_ref=target_branch_obs.entity_ref,
                        kind="has_base_branch",
                        subject_obs_id=obs_id,
                        object_obs_id=target_branch_obs.observation_context.observation_id,
                        prov_refs=(field_prov,),
                    )
                else:
                    q_reason = quarantined_by_kind_and_id.get(branch_key)
                    if q_reason:
                        reason = (
                            f"Base branch '{base_branch_id}' was quarantined ({q_reason})."
                        )
                    else:
                        reason = (
                            f"Base branch '{base_branch_id}' was not observed."
                        )
                    _record_unresolved(
                        source_ref=ref,
                        source_obs_id=obs_id,
                        target_entity_kind="github_branch",
                        target_identifier=base_branch_id,
                        kind="has_base_branch",
                        reason=reason,
                        prov_refs=(field_prov,),
                    )

            # ── 4. has_head_branch (fork-aware) ──────────────────────
            if pr_state.source_branch is not None:
                field_prov = ProvenanceRef(
                    source_instance=source_instance,
                    observation_id=obs_id,
                    fixture_id=fixture_id,
                    record_locator=base_prov.record_locator,
                    source_field_path="source_branch",
                )

                # Fork check: if explicitly marked as fork with no head_repository_id
                if pr_state.is_fork is True and pr_state.head_repository_id is None:
                    _record_unresolved(
                        source_ref=ref,
                        source_obs_id=obs_id,
                        target_entity_kind="github_branch",
                        target_identifier=pr_state.source_branch,
                        kind="has_head_branch",
                        reason=(
                            f"PR #{pr_state.number} originates from a fork but has "
                            "no explicit head_repository_id scope."
                        ),
                        prov_refs=(field_prov,),
                    )
                else:
                    head_repo_id = pr_state.head_repository_id or repo_id
                    head_branch_id = f"{head_repo_id}/{pr_state.source_branch}"
                    head_branch_key = ("github_branch", head_branch_id)
                    head_branch_obs = obs_by_kind_and_id.get(head_branch_key)

                    if head_branch_obs is not None:
                        _record_relationship(
                            subject_ref=ref,
                            object_ref=head_branch_obs.entity_ref,
                            kind="has_head_branch",
                            subject_obs_id=obs_id,
                            object_obs_id=head_branch_obs.observation_context.observation_id,
                            prov_refs=(field_prov,),
                        )
                    else:
                        q_reason = quarantined_by_kind_and_id.get(head_branch_key)
                        if q_reason:
                            reason = (
                                f"Head branch '{head_branch_id}' was quarantined ({q_reason})."
                            )
                        else:
                            reason = (
                                f"Head branch '{head_branch_id}' was not observed."
                            )
                        _record_unresolved(
                            source_ref=ref,
                            source_obs_id=obs_id,
                            target_entity_kind="github_branch",
                            target_identifier=head_branch_id,
                            kind="has_head_branch",
                            reason=reason,
                            prov_refs=(field_prov,),
                        )

            # ── 5. contains_commit ───────────────────────────────────
            # Only from explicit pull_request_commit_shas
            for c_sha in pr_state.pull_request_commit_shas:
                commit_prov = ProvenanceRef(
                    source_instance=source_instance,
                    observation_id=obs_id,
                    fixture_id=fixture_id,
                    record_locator=base_prov.record_locator,
                    source_field_path="pull_request_commits",
                )
                commit_id = f"{repo_id}/{c_sha}"
                commit_key = ("github_commit", commit_id)
                commit_obs = obs_by_kind_and_id.get(commit_key)

                # If fork PR, also check head_repository_id if different
                if commit_obs is None and pr_state.head_repository_id:
                    fork_commit_id = f"{pr_state.head_repository_id}/{c_sha}"
                    fork_commit_key = ("github_commit", fork_commit_id)
                    commit_obs = obs_by_kind_and_id.get(fork_commit_key)
                    if commit_obs is not None:
                        commit_id = fork_commit_id
                        commit_key = fork_commit_key

                if commit_obs is not None:
                    _record_relationship(
                        subject_ref=ref,
                        object_ref=commit_obs.entity_ref,
                        kind="contains_commit",
                        subject_obs_id=obs_id,
                        object_obs_id=commit_obs.observation_context.observation_id,
                        prov_refs=(commit_prov,),
                    )
                else:
                    q_reason = quarantined_by_kind_and_id.get(commit_key)
                    if q_reason:
                        reason = (
                            f"Associated commit '{commit_id}' was quarantined ({q_reason})."
                        )
                    else:
                        reason = (
                            f"Associated commit '{commit_id}' was not observed."
                        )
                    _record_unresolved(
                        source_ref=ref,
                        source_obs_id=obs_id,
                        target_entity_kind="github_commit",
                        target_identifier=commit_id,
                        kind="contains_commit",
                        reason=reason,
                        prov_refs=(commit_prov,),
                    )

            # ── 6. has_head_commit ───────────────────────────────────
            if pr_state.head_commit_sha is not None:
                head_repo_id = pr_state.head_repository_id or repo_id
                head_commit_id = f"{head_repo_id}/{pr_state.head_commit_sha}"
                head_commit_key = ("github_commit", head_commit_id)
                head_commit_obs = obs_by_kind_and_id.get(head_commit_key)
                field_prov = ProvenanceRef(
                    source_instance=source_instance,
                    observation_id=obs_id,
                    fixture_id=fixture_id,
                    record_locator=base_prov.record_locator,
                    source_field_path="head_commit_sha",
                )

                if head_commit_obs is not None:
                    _record_relationship(
                        subject_ref=ref,
                        object_ref=head_commit_obs.entity_ref,
                        kind="has_head_commit",
                        subject_obs_id=obs_id,
                        object_obs_id=head_commit_obs.observation_context.observation_id,
                        prov_refs=(field_prov,),
                    )
                else:
                    q_reason = quarantined_by_kind_and_id.get(head_commit_key)
                    if q_reason:
                        reason = (
                            f"Head commit '{head_commit_id}' was quarantined ({q_reason})."
                        )
                    else:
                        reason = (
                            f"Head commit '{head_commit_id}' was not observed."
                        )
                    _record_unresolved(
                        source_ref=ref,
                        source_obs_id=obs_id,
                        target_entity_kind="github_commit",
                        target_identifier=head_commit_id,
                        kind="has_head_commit",
                        reason=reason,
                        prov_refs=(field_prov,),
                    )

            # ── 7. has_base_commit ───────────────────────────────────
            if pr_state.base_commit_sha is not None:
                base_commit_id = f"{repo_id}/{pr_state.base_commit_sha}"
                base_commit_key = ("github_commit", base_commit_id)
                base_commit_obs = obs_by_kind_and_id.get(base_commit_key)
                field_prov = ProvenanceRef(
                    source_instance=source_instance,
                    observation_id=obs_id,
                    fixture_id=fixture_id,
                    record_locator=base_prov.record_locator,
                    source_field_path="base_commit_sha",
                )

                if base_commit_obs is not None:
                    _record_relationship(
                        subject_ref=ref,
                        object_ref=base_commit_obs.entity_ref,
                        kind="has_base_commit",
                        subject_obs_id=obs_id,
                        object_obs_id=base_commit_obs.observation_context.observation_id,
                        prov_refs=(field_prov,),
                    )
                else:
                    q_reason = quarantined_by_kind_and_id.get(base_commit_key)
                    if q_reason:
                        reason = (
                            f"Base commit '{base_commit_id}' was quarantined ({q_reason})."
                        )
                    else:
                        reason = (
                            f"Base commit '{base_commit_id}' was not observed."
                        )
                    _record_unresolved(
                        source_ref=ref,
                        source_obs_id=obs_id,
                        target_entity_kind="github_commit",
                        target_identifier=base_commit_id,
                        kind="has_base_commit",
                        reason=reason,
                        prov_refs=(field_prov,),
                    )

    # ── Materialize and sort relationships ───────────────────────────
    for (
        subject_ref,
        rel_kind,
        object_ref,
        basis,
        sub_obs_id,
        obj_obs_id,
    ), prov_list in dedup_relationships.items():
        sorted_prov = tuple(sorted(prov_list, key=_sort_provenance_key))
        relationships.append(
            EvidenceRelationship(
                subject_ref=subject_ref,
                object_ref=object_ref,
                kind=rel_kind,
                basis=basis,
                subject_observation_id=sub_obs_id,
                object_observation_id=obj_obs_id,
                provenance_refs=sorted_prov,
            )
        )

    # ── Materialize and sort unresolved references ───────────────────
    for (
        source_ref,
        src_obs_id,
        target_entity_kind,
        target_identifier,
        rel_kind,
        reason,
    ), prov_list in dedup_unresolved.items():
        sorted_prov = tuple(sorted(prov_list, key=_sort_provenance_key))
        unresolved_list.append(
            UnresolvedReference(
                source_ref=source_ref,
                source_observation_id=src_obs_id,
                target_entity_kind=target_entity_kind,
                target_identifier=target_identifier,
                relationship_kind=rel_kind,
                reason=reason,
                provenance_refs=sorted_prov,
            )
        )

    sorted_relationships = tuple(
        sorted(relationships, key=_sort_relationship_key)
    )
    sorted_unresolved = tuple(
        sorted(unresolved_list, key=_sort_unresolved_key)
    )

    return sorted_relationships, sorted_unresolved
