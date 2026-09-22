"""Explicit Jira mention resolver for GitHub evidence observations (CSE-1.6).

Resolves literal textual Jira mentions from normalized GitHub fixture fields
(PR titles, commit messages, branch names) against accepted Jira observations
under a configured lexical policy.

Supported mention relationships:
  - mentions (GitHub PR -> Jira issue, GitHub commit -> Jira issue,
    GitHub branch -> Jira issue)

All resolved relationships carry:
  - subject EntityRef (GitHub entity) and object EntityRef (Jira issue)
  - relationship kind ("mentions") and basis ("lexical_match")
  - subject_observation_id (GitHub) and object_observation_id (Jira)
  - supporting ProvenanceRef instances identifying the inspected field(s)
  - empty quality_issues

Unresolved references are emitted when a mentioned Jira key does not
correspond to an accepted Jira observation (missing or ambiguous).

Zero semantic inference, scoring, confidence, risk, sentiment, predictions,
or managerial interpretation. "mentions" remains strictly literal.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    EvidenceRelationship,
    GitHubBranchState,
    GitHubCommitState,
    GitHubPullRequestState,
    ProvenanceRef,
    QualityIssue,
    RelationshipBasis,
    RelationshipKind,
    SourceInstance,
    UnresolvedReference,
)
from shadow_orbit.github_normalization import NormalizedGitHubFixture


RELATIONSHIP_BASIS: RelationshipBasis = "lexical_match"
RELATIONSHIP_KIND: RelationshipKind = "mentions"


@dataclass(frozen=True, slots=True)
class MentionLexicalPolicy:
    """Configured lexical policy for Jira mention extraction.

    V0 Contract Grammar Assumption:
        Each project key prefix must consist of uppercase ASCII letters only
        (^[A-Z]+$). This is a V0 contract constraint to prevent open-ended regex
        matching from turning arbitrary strings into issue keys. It is not a
        claim of universal truth for all possible Jira installations.
    """

    project_key_prefixes: frozenset[str]

    def __post_init__(self) -> None:
        if not self.project_key_prefixes:
            raise ValueError(
                "MentionLexicalPolicy requires a non-empty set of "
                "project_key_prefixes."
            )
        for prefix in self.project_key_prefixes:
            if not isinstance(prefix, str):
                raise TypeError(
                    f"Project key prefix must be a string, got "
                    f"{type(prefix).__name__!r}."
                )
            if not prefix:
                raise ValueError("Project key prefix cannot be empty.")
            if not re.fullmatch(r"[A-Z]+", prefix):
                raise ValueError(
                    f"Project key prefix {prefix!r} violates V0 contract grammar: "
                    "must consist of uppercase ASCII letters only (^[A-Z]+$)."
                )

    @property
    def fingerprint(self) -> str:
        """Deterministic policy identity fingerprint for qualification tracking."""
        sorted_prefixes = ",".join(sorted(self.project_key_prefixes))
        return f"jira-prefix-v0:{sorted_prefixes}"

    @property
    def policy_id(self) -> str:
        """Alias for policy fingerprint."""
        return self.fingerprint


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


def resolve_github_jira_mentions(
    normalized: NormalizedGitHubFixture,
    jira_observations: tuple[EvidenceObservation, ...],
    jira_source_instance: SourceInstance,
    policy: MentionLexicalPolicy,
) -> tuple[tuple[EvidenceRelationship, ...], tuple[UnresolvedReference, ...]]:
    """Extract explicit textual Jira mentions and resolve against Jira observations.

    Parameters
    ----------
    normalized:
        An immutable NormalizedGitHubFixture containing accepted GitHub
        observations.
    jira_observations:
        Tuple of accepted Jira EvidenceObservation instances for target
        resolution.
    jira_source_instance:
        SourceInstance representing the authoritative Jira deployment.
        Must have source_kind='jira'.
    policy:
        Configured MentionLexicalPolicy defining allowed Jira project key
        prefixes.

    Returns
    -------
    tuple of (relationships, unresolved_references):
        relationships:
            Resolved EvidenceRelationship instances with kind='mentions' and
            basis='lexical_match'.
        unresolved_references:
            UnresolvedReference instances for mentioned Jira keys that could
            not be resolved to an unambiguous accepted Jira observation.

    Raises
    ------
    ValueError:
        If jira_source_instance does not have source_kind='jira', or if
        normalized does not have source_kind='github'.
    """
    if jira_source_instance.source_kind != "jira":
        raise ValueError(
            f"Jira source instance must have source_kind='jira', "
            f"got {jira_source_instance.source_kind!r}."
        )
    if normalized.source_instance.source_kind != "github":
        raise ValueError(
            f"Normalized fixture must have source_kind='github', "
            f"got {normalized.source_instance.source_kind!r}."
        )

    # ── Compile lexical mention pattern ──────────────────────────────
    # Sort prefixes by descending length, then alphabetically for deterministic
    # longest-match alternation.
    sorted_prefixes = sorted(
        policy.project_key_prefixes, key=lambda x: (-len(x), x)
    )
    pattern_str = (
        r"\b(?:"
        + "|".join(re.escape(p) for p in sorted_prefixes)
        + r")-\d+\b"
    )
    mention_pattern = re.compile(pattern_str)

    # ── Index Jira observations by entity_id ─────────────────────────
    # Strict identity: source_instance == jira_source_instance and entity_kind == 'jira_issue'.
    # We collect all observations per key to detect ambiguous targets.
    jira_obs_by_key: dict[str, list[EvidenceObservation]] = {}
    for obs in jira_observations:
        if (
            obs.entity_ref.source_instance == jira_source_instance
            and obs.entity_ref.entity_kind == "jira_issue"
        ):
            key = obs.entity_ref.entity_id
            if key not in jira_obs_by_key:
                jira_obs_by_key[key] = []
            jira_obs_by_key[key].append(obs)

    github_source_instance = normalized.source_instance
    fixture_id = str(normalized.raw_document.get("fixture_id", ""))

    # ── Map for aggregating provenance per distinct target reference ──
    # Key: (source_ref, source_obs_id, jira_key)
    # Value: list[ProvenanceRef]
    distinct_target_refs: dict[
        tuple[EntityRef, str, str], list[ProvenanceRef]
    ] = {}

    def _record_mention_occurrence(
        source_ref: EntityRef,
        source_obs_id: str,
        jira_key: str,
        prov: ProvenanceRef,
    ) -> None:
        target_ref_key = (source_ref, source_obs_id, jira_key)
        if target_ref_key not in distinct_target_refs:
            distinct_target_refs[target_ref_key] = [prov]
        else:
            if prov not in distinct_target_refs[target_ref_key]:
                distinct_target_refs[target_ref_key].append(prov)

    # ── Scan GitHub observations for text fields ─────────────────────
    for obs in normalized.observations:
        ref = obs.entity_ref
        kind = ref.entity_kind
        obs_id = obs.observation_context.observation_id
        base_locator = (
            obs.provenance_refs[0].record_locator
            if obs.provenance_refs
            else None
        )

        candidate_fields: list[tuple[str, str | None]] = []

        if kind == "github_pull_request" and isinstance(
            obs.observed_state, GitHubPullRequestState
        ):
            pr_state = obs.observed_state
            candidate_fields.append(("title", pr_state.title))
            candidate_fields.append(("source_branch", pr_state.source_branch))
            candidate_fields.append(("target_branch", pr_state.target_branch))

        elif kind == "github_commit" and isinstance(
            obs.observed_state, GitHubCommitState
        ):
            c_state = obs.observed_state
            candidate_fields.append(("message", c_state.message))

        elif kind == "github_branch" and isinstance(
            obs.observed_state, GitHubBranchState
        ):
            b_state = obs.observed_state
            candidate_fields.append(("name", b_state.name))

        # Inspect candidate fields
        for field_path, text_val in candidate_fields:
            if not text_val or not isinstance(text_val, str):
                continue

            matches = mention_pattern.findall(text_val)
            if not matches:
                continue

            field_prov = ProvenanceRef(
                source_instance=github_source_instance,
                observation_id=obs_id,
                fixture_id=fixture_id,
                record_locator=base_locator,
                source_field_path=field_path,
            )

            # Deduplicate occurrences within the same field:
            # multiple occurrences in the same field produce one ProvenanceRef
            # for this field.
            unique_keys_in_field = set(matches)
            for jira_key in unique_keys_in_field:
                _record_mention_occurrence(
                    source_ref=ref,
                    source_obs_id=obs_id,
                    jira_key=jira_key,
                    prov=field_prov,
                )

    # ── Resolve distinct target references ───────────────────────────
    relationships: list[EvidenceRelationship] = []
    unresolved_list: list[UnresolvedReference] = []

    for (
        source_ref,
        src_obs_id,
        jira_key,
    ), prov_list in distinct_target_refs.items():
        sorted_prov = tuple(sorted(prov_list, key=_sort_provenance_key))
        matching_obs = jira_obs_by_key.get(jira_key, [])

        if len(matching_obs) == 1:
            # Unambiguous accepted target
            target_obs = matching_obs[0]
            relationships.append(
                EvidenceRelationship(
                    subject_ref=source_ref,
                    object_ref=target_obs.entity_ref,
                    kind=RELATIONSHIP_KIND,
                    basis=RELATIONSHIP_BASIS,
                    subject_observation_id=src_obs_id,
                    object_observation_id=(
                        target_obs.observation_context.observation_id
                    ),
                    provenance_refs=sorted_prov,
                )
            )
        elif len(matching_obs) > 1:
            # Ambiguous: multiple observations for the same Jira identity
            unresolved_list.append(
                UnresolvedReference(
                    source_ref=source_ref,
                    source_observation_id=src_obs_id,
                    target_entity_kind="jira_issue",
                    target_identifier=jira_key,
                    relationship_kind=RELATIONSHIP_KIND,
                    reason=(
                        f"Ambiguous Jira target: multiple observations "
                        f"found for '{jira_key}'."
                    ),
                    provenance_refs=sorted_prov,
                )
            )
        else:
            # Not observed
            unresolved_list.append(
                UnresolvedReference(
                    source_ref=source_ref,
                    source_observation_id=src_obs_id,
                    target_entity_kind="jira_issue",
                    target_identifier=jira_key,
                    relationship_kind=RELATIONSHIP_KIND,
                    reason=f"Mentioned Jira key '{jira_key}' was not observed.",
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
