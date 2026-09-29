"""Pure, deterministic cross-system evidence fusion (CSE-1.8 / Milestone 2 / Wave 3).

Fuses independently produced Jira and GitHub evidence into a unified
CrossSystemFusionResult containing:
- declared_mentions: Explicit textual citations with basis="lexical_match" (DECLARED_MENTION)
- explicit_links: Structured native integration metadata links (EXPLICIT_LINK, empty in current schemas)
- unresolved_references: Unresolved or ambiguous mentions
- state_alignments: CrossSystemStateAlignment comparisons (state and temporal dimensions)
- quality_issues: Any contract or consistency issues

Guarantees:
- Pure in-memory computation: Zero external I/O, zero network, zero database access.
- Non-inferential: Never equates textual mentions with implementation responsibility,
  authorship, or ticket closure.
- Actor-disconnected: Never infers that matching usernames denote the same human actor.
- Non-transitive: Never infers multi-hop or transitive associations.
- Conservative contradiction: Temporal differences and missing data are never classified
  as CONFLICTING; CONFLICTING requires logically incompatible authoritative evidence.
- Permutation-invariant: Equivalent input produces bit-for-bit identical canonical output.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from shadow_orbit.evidence_types import (
    CrossSystemStateAlignment,
    CrossSystemStateComparison,
    CrossSystemTemporalComparison,
    EntityRef,
    EvidenceObservation,
    EvidenceRelationship,
    GitHubBranchState,
    GitHubCommitState,
    GitHubPullRequestState,
    JiraIssueState,
    QualityIssue,
    SourceInstance,
    UnresolvedReference,
)
from shadow_orbit.github_mentions import (
    MentionLexicalPolicy,
    resolve_github_jira_mentions,
)
from shadow_orbit.github_normalization import NormalizedGitHubFixture


@dataclass(frozen=True, slots=True)
class CrossSystemFusionResult:
    """Immutable result of cross-system evidence fusion."""

    declared_mentions: tuple[EvidenceRelationship, ...] = ()
    explicit_links: tuple[EvidenceRelationship, ...] = ()
    unresolved_references: tuple[UnresolvedReference, ...] = ()
    state_alignments: tuple[CrossSystemStateAlignment, ...] = ()
    quality_issues: tuple[QualityIssue, ...] = ()


def _sort_alignment_key(
    a: CrossSystemStateAlignment,
) -> tuple[str, str, str, str, str, str]:
    """Deterministic canonical sort key for CrossSystemStateAlignment."""
    return (
        a.subject_ref.entity_id,
        a.corroborating_ref.entity_id,
        a.relationship_kind,
        a.state_comparison,
        a.temporal_comparison,
        a.rationale,
    )


def correlate_cross_system_evidence(
    jira_observations: Sequence[EvidenceObservation],
    github_fixture: NormalizedGitHubFixture,
    mention_policy: MentionLexicalPolicy,
    jira_source_instance: SourceInstance | None = None,
    temporal_interval: tuple[datetime, datetime] | None = None,
) -> CrossSystemFusionResult:
    """Pure, deterministic fusion of Jira and GitHub evidence.

    Parameters
    ----------
    jira_observations:
        Accepted EvidenceObservation instances produced by the Jira pipeline.
    github_fixture:
        NormalizedGitHubFixture containing accepted GitHub observations.
    mention_policy:
        Configured MentionLexicalPolicy defining allowed Jira project key prefixes.
    jira_source_instance:
        Optional expected Jira SourceInstance. If None, inferred from the first
        Jira observation if available.
    temporal_interval:
        Optional review period bounds (starts_at, ends_at_exclusive).

    Returns
    -------
    CrossSystemFusionResult
        Immutable, canonically sorted cross-system fusion result.
    """
    # ── 1. Resolve Jira Source Instance ──────────────────────────────
    if jira_source_instance is None:
        if jira_observations:
            jira_source_instance = jira_observations[0].entity_ref.source_instance
        else:
            jira_source_instance = SourceInstance(source_kind="jira", instance_id="default")

    # ── 2. Index Jira observations by entity_id ──────────────────────
    jira_obs_by_id: dict[str, list[EvidenceObservation]] = {}
    for obs in jira_observations:
        if (
            obs.entity_ref.source_instance == jira_source_instance
            and obs.entity_ref.entity_kind == "jira_issue"
        ):
            key = obs.entity_ref.entity_id
            if key not in jira_obs_by_id:
                jira_obs_by_id[key] = []
            jira_obs_by_id[key].append(obs)

    # ── 3. Index GitHub observations by (entity_kind, entity_id) ─────
    gh_obs_by_key: dict[tuple[str, str], EvidenceObservation] = {}
    for obs in github_fixture.observations:
        k = (obs.entity_ref.entity_kind, obs.entity_ref.entity_id)
        gh_obs_by_key[k] = obs

    # ── 4. Resolve Declared Mentions (DECLARED_MENTION) ───────────────
    # Uses existing resolve_github_jira_mentions for exact lexical matching & provenance
    declared_mentions, unresolved_references = resolve_github_jira_mentions(
        normalized=github_fixture,
        jira_observations=tuple(jira_observations),
        jira_source_instance=jira_source_instance,
        policy=mention_policy,
    )

    # ── 5. Resolve Explicit Links (EXPLICIT_LINK) ─────────────────────
    # Current fixture schemas (shadow-jira-fixture-v1 & shadow-github-fixture-v1)
    # contain no native structured link metadata. In accordance with ADR-005 D2,
    # explicit_links is legitimately empty for the current corpus.
    explicit_links: tuple[EvidenceRelationship, ...] = ()

    # ── 6. Evaluate Cross-System State & Temporal Alignments ─────────
    state_alignments: list[CrossSystemStateAlignment] = []

    for rel in declared_mentions:
        gh_ref = rel.subject_ref
        jira_ref = rel.object_ref

        gh_obs = gh_obs_by_key.get((gh_ref.entity_kind, gh_ref.entity_id))
        matching_jira = jira_obs_by_id.get(jira_ref.entity_id, [])

        if len(matching_jira) != 1 or gh_obs is None:
            # Ambiguous or unobserved targets are handled in unresolved_references
            continue

        jira_obs = matching_jira[0]
        jira_state = jira_obs.observed_state
        gh_state = gh_obs.observed_state

        if not isinstance(jira_state, JiraIssueState):
            continue

        state_comp: CrossSystemStateComparison = "INSUFFICIENT_EVIDENCE"
        temporal_comp: CrossSystemTemporalComparison = "INDETERMINATE"
        rationale: str = ""

        # Case A: GitHub Pull Request
        if isinstance(gh_state, GitHubPullRequestState):
            pr_state = gh_state.state
            pr_created = gh_state.created_at
            pr_merged = gh_state.merged_at
            jira_resolved = jira_state.resolved_at
            jira_created = jira_state.created_at
            jira_cat = jira_state.status_category

            if pr_state == "merged" or pr_merged is not None:
                if pr_merged is not None and jira_resolved is not None:
                    if pr_merged <= jira_resolved:
                        temporal_comp = "COHERENT"
                        state_comp = "CONSISTENT"
                        rationale = "GitHub PR merged prior to or coincident with Jira issue resolution."
                    else:
                        temporal_comp = "INVERTED"
                        state_comp = "INSUFFICIENT_EVIDENCE"
                        rationale = "GitHub PR merged after Jira issue resolution (potential post-resolution activity; non-conflicting)."
                elif pr_merged is not None and jira_resolved is None:
                    if jira_cat == "done":
                        temporal_comp = "INDETERMINATE"
                        state_comp = "INSUFFICIENT_EVIDENCE"
                        rationale = "GitHub PR merged and Jira issue marked done without explicit resolved_at timestamp."
                    else:
                        temporal_comp = "INDETERMINATE"
                        state_comp = "INSUFFICIENT_EVIDENCE"
                        rationale = "GitHub PR merged while Jira issue remains unresolved/in progress."
                else:
                    temporal_comp = "INDETERMINATE"
                    state_comp = "INSUFFICIENT_EVIDENCE"
                    rationale = "GitHub PR recorded as merged but lacks explicit merged_at timestamp."

            elif pr_state == "open":
                if jira_cat == "done":
                    temporal_comp = "INDETERMINATE"
                    state_comp = "INSUFFICIENT_EVIDENCE"
                    rationale = "Jira issue marked done while referenced GitHub PR remains open (workflow discrepancy; non-conflicting)."
                else:
                    if pr_created is not None and jira_created is not None and pr_created >= jira_created:
                        temporal_comp = "COHERENT"
                    else:
                        temporal_comp = "INDETERMINATE"
                    state_comp = "CONSISTENT"
                    rationale = "Referenced GitHub PR and Jira issue both actively in progress."

            elif pr_state == "closed":
                temporal_comp = "INDETERMINATE"
                state_comp = "INSUFFICIENT_EVIDENCE"
                rationale = "Referenced GitHub PR closed without merge."

            else:
                temporal_comp = "INDETERMINATE"
                state_comp = "INSUFFICIENT_EVIDENCE"
                rationale = f"Referenced GitHub PR in state '{pr_state}' with indeterminate lifecycle alignment."

        # Case B: GitHub Commit
        elif isinstance(gh_state, GitHubCommitState):
            commit_time = gh_state.committed_at
            jira_created = jira_state.created_at
            jira_resolved = jira_state.resolved_at

            if commit_time is not None:
                if jira_resolved is not None:
                    if commit_time <= jira_resolved:
                        temporal_comp = "COHERENT"
                        state_comp = "CONSISTENT"
                        rationale = "GitHub commit timestamp precedes or coincides with Jira issue resolution."
                    else:
                        temporal_comp = "INVERTED"
                        state_comp = "INSUFFICIENT_EVIDENCE"
                        rationale = "GitHub commit postdates Jira issue resolution (potential post-resolution activity; non-conflicting)."
                else:
                    if jira_created is not None and commit_time >= jira_created:
                        temporal_comp = "COHERENT"
                        state_comp = "CONSISTENT"
                        rationale = "GitHub commit committed during active Jira issue lifecycle."
                    else:
                        temporal_comp = "INVERTED"
                        state_comp = "INSUFFICIENT_EVIDENCE"
                        rationale = "GitHub commit predates Jira issue creation (pre-existing work or retrospective ticket; non-conflicting)."
            else:
                temporal_comp = "INDETERMINATE"
                state_comp = "INSUFFICIENT_EVIDENCE"
                rationale = "GitHub commit timestamp missing; temporal comparison indeterminate."

        # Case C: GitHub Branch
        elif isinstance(gh_state, GitHubBranchState):
            temporal_comp = "INDETERMINATE"
            state_comp = "CONSISTENT"
            rationale = f"GitHub branch '{gh_state.name}' mentions Jira issue '{jira_state.key}'."

        # Case D: Other GitHub entities
        else:
            temporal_comp = "INDETERMINATE"
            state_comp = "INSUFFICIENT_EVIDENCE"
            rationale = f"Referenced GitHub entity '{gh_ref.entity_kind}' has no temporal state comparison rules."

        state_alignments.append(
            CrossSystemStateAlignment(
                subject_ref=jira_ref,
                corroborating_ref=gh_ref,
                relationship_kind=rel.kind,
                state_comparison=state_comp,
                temporal_comparison=temporal_comp,
                rationale=rationale,
                provenance_refs=rel.provenance_refs,
            )
        )

    # ── 7. Sort Output Canonically (Permutation Invariance) ───────────
    sorted_alignments = tuple(sorted(state_alignments, key=_sort_alignment_key))

    return CrossSystemFusionResult(
        declared_mentions=declared_mentions,
        explicit_links=explicit_links,
        unresolved_references=unresolved_references,
        state_alignments=sorted_alignments,
        quality_issues=(),
    )
