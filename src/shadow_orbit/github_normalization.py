"""Normalize validated GitHub fixture data into typed EvidenceObservation instances.

Converts accepted GitHub repositories, branches, commits, pull requests,
and reviews into strongly typed EvidenceObservation instances wrapped with
canonical EntityRef, ProvenanceRef, ObservationContext, and QualityIssue data.

Provenance record locators strictly address the original raw fixture document
before validation/quarantine filtering.

Supported State Recognition:
- PR states: "open", "closed", "merged" (case-insensitive).
  Unsupported/unknown PR state -> raw value preserved in validated dict;
  normalized state = "unknown" + QualityIssue(code="unsupported_value").
- Review states: "APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED", "PENDING"
  Unsupported/unknown review state -> raw value preserved in validated dict;
  normalized state = "unknown" + QualityIssue(code="unsupported_value").

Source Independence:
This module does NOT import or reference any Jira modules or Jira domain types.
No Jira WorkItem instances are constructed.
Zero Jira key parsing or mention detection is performed.
No person identity resolution is performed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    GitHubBranchState,
    GitHubCommitState,
    GitHubPullRequestState,
    GitHubRepositoryState,
    GitHubReviewState,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    SourceInstance,
)
from shadow_orbit.github_validation import (
    GitHubQuarantinedRecord,
    ValidatedGitHubFixture,
    _parse_aware_datetime,
)

SUPPORTED_PR_STATES: frozenset[str] = frozenset({"open", "closed", "merged"})

SUPPORTED_REVIEW_STATES: frozenset[str] = frozenset({
    "APPROVED",
    "CHANGES_REQUESTED",
    "COMMENTED",
    "DISMISSED",
    "PENDING",
})


@dataclass(frozen=True, slots=True)
class NormalizedGitHubFixture:
    """Normalized projection of validated GitHub evidence.

    Container immutability: this object is frozen and slotted, and all
    collection attributes are immutable tuples. All EvidenceObservation
    items and their payloads are deeply frozen dataclasses.
    """

    raw_document: dict[str, Any]
    source_instance: SourceInstance
    observation_context: ObservationContext
    observations: tuple[EvidenceObservation, ...]
    quality_issues: tuple[QualityIssue, ...]
    quarantined_records: tuple[GitHubQuarantinedRecord, ...]


def normalize_github_fixture(
    validated: ValidatedGitHubFixture,
) -> NormalizedGitHubFixture:
    """Transform validated GitHub data into canonical EvidenceObservation items."""
    fixture_id = str(validated.raw_document.get("fixture_id", ""))
    source_instance = validated.source_instance
    obs_context = validated.observation_context
    obs_id = obs_context.observation_id

    # Working list of all quality issues (from validation + any normalization issues)
    all_issues: list[QualityIssue] = list(validated.quality_issues)

    # Group quality issues by subject_ref for attachment to observations
    issues_by_entity: dict[EntityRef, list[QualityIssue]] = {}
    for issue in all_issues:
        if issue.subject_ref is not None:
            issues_by_entity.setdefault(issue.subject_ref, []).append(issue)

    observations: list[EvidenceObservation] = []

    for repo in validated.accepted_repositories:
        repo_id = str(repo["repo_id"])
        repo_locator = str(repo.get("_raw_locator", f"repositories[{repo_id}]"))

        repo_ref = EntityRef(
            source_instance=source_instance,
            entity_kind="github_repository",
            entity_id=repo_id,
        )
        repo_prov = ProvenanceRef(
            source_instance=source_instance,
            observation_id=obs_id,
            fixture_id=fixture_id,
            record_locator=repo_locator,
        )
        repo_state = GitHubRepositoryState(
            owner=str(repo["owner"]),
            name=str(repo["name"]),
            default_branch=(
                str(repo["default_branch"])
                if repo.get("default_branch") is not None
                else None
            ),
        )
        observations.append(
            EvidenceObservation(
                entity_ref=repo_ref,
                observation_context=obs_context,
                observed_state=repo_state,
                quality_issues=tuple(issues_by_entity.get(repo_ref, ())),
                provenance_refs=(repo_prov,),
            )
        )

        # ── Branches ─────────────────────────────────────────────────
        raw_branches = repo.get("branches")
        for branch in (raw_branches if isinstance(raw_branches, list) else ()):
            b_name = str(branch["name"])
            b_locator = str(branch.get("_raw_locator", f"{repo_locator}.branches[{b_name}]"))
            branch_ref = EntityRef(
                source_instance=source_instance,
                entity_kind="github_branch",
                entity_id=f"{repo_id}/{b_name}",
            )
            branch_prov = ProvenanceRef(
                source_instance=source_instance,
                observation_id=obs_id,
                fixture_id=fixture_id,
                record_locator=b_locator,
            )
            branch_state = GitHubBranchState(
                name=b_name,
                head_commit_id=(
                    str(branch["head_commit_id"])
                    if branch.get("head_commit_id") is not None
                    else None
                ),
            )
            observations.append(
                EvidenceObservation(
                    entity_ref=branch_ref,
                    observation_context=obs_context,
                    observed_state=branch_state,
                    quality_issues=tuple(issues_by_entity.get(branch_ref, ())),
                    provenance_refs=(branch_prov,),
                )
            )

        # ── Commits ──────────────────────────────────────────────────
        raw_commits = repo.get("commits")
        for commit in (raw_commits if isinstance(raw_commits, list) else ()):
            c_sha = str(commit["sha"])
            c_locator = str(commit.get("_raw_locator", f"{repo_locator}.commits[{c_sha}]"))
            commit_ref = EntityRef(
                source_instance=source_instance,
                entity_kind="github_commit",
                entity_id=f"{repo_id}/{c_sha}",
            )
            commit_prov = ProvenanceRef(
                source_instance=source_instance,
                observation_id=obs_id,
                fixture_id=fixture_id,
                record_locator=c_locator,
            )

            committed_at = None
            if commit.get("committed_at") is not None:
                try:
                    committed_at = _parse_aware_datetime(
                        commit["committed_at"], f"{c_locator}.committed_at"
                    )
                except ValueError:
                    committed_at = None

            commit_state = GitHubCommitState(
                sha=c_sha,
                message=str(commit.get("message", "")),
                author_login=(
                    str(commit["author_login"])
                    if commit.get("author_login") is not None
                    else None
                ),
                committed_at=committed_at,
            )
            observations.append(
                EvidenceObservation(
                    entity_ref=commit_ref,
                    observation_context=obs_context,
                    observed_state=commit_state,
                    quality_issues=tuple(issues_by_entity.get(commit_ref, ())),
                    provenance_refs=(commit_prov,),
                )
            )

        # ── Pull Requests ────────────────────────────────────────────
        raw_prs = repo.get("pull_requests")
        for pr in (raw_prs if isinstance(raw_prs, list) else ()):
            pr_num = int(pr["number"])
            pr_locator = str(pr.get("_raw_locator", f"{repo_locator}.pull_requests[{pr_num}]"))
            pr_ref = EntityRef(
                source_instance=source_instance,
                entity_kind="github_pull_request",
                entity_id=f"{repo_id}/{pr_num}",
            )
            pr_prov = ProvenanceRef(
                source_instance=source_instance,
                observation_id=obs_id,
                fixture_id=fixture_id,
                record_locator=pr_locator,
            )

            # State recognition: supported vs unknown
            raw_pr_state = str(pr.get("state", ""))
            clean_pr_state = raw_pr_state.strip().lower()
            if clean_pr_state in SUPPORTED_PR_STATES:
                normalized_pr_state = clean_pr_state
            else:
                normalized_pr_state = "unknown"
                state_issue = QualityIssue(
                    code="unsupported_value",
                    message=f"Unsupported pull request state {raw_pr_state!r}; normalized to 'unknown'.",
                    subject_ref=pr_ref,
                    subject_scope="field:state",
                )
                all_issues.append(state_issue)
                issues_by_entity.setdefault(pr_ref, []).append(state_issue)

            created_at = None
            if pr.get("created_at") is not None:
                try:
                    created_at = _parse_aware_datetime(
                        pr["created_at"], f"{pr_locator}.created_at"
                    )
                except ValueError:
                    created_at = None

            merged_at = None
            if pr.get("merged_at") is not None:
                try:
                    merged_at = _parse_aware_datetime(
                        pr["merged_at"], f"{pr_locator}.merged_at"
                    )
                except ValueError:
                    merged_at = None

            pr_state = GitHubPullRequestState(
                number=pr_num,
                title=str(pr.get("title", "")),
                state=normalized_pr_state,
                author_login=(
                    str(pr["author_login"])
                    if pr.get("author_login") is not None
                    else None
                ),
                created_at=created_at,
                merged_at=merged_at,
                target_branch=(
                    str(pr["target_branch"])
                    if pr.get("target_branch") is not None
                    else None
                ),
                source_branch=(
                    str(pr["source_branch"])
                    if pr.get("source_branch") is not None
                    else None
                ),
            )
            observations.append(
                EvidenceObservation(
                    entity_ref=pr_ref,
                    observation_context=obs_context,
                    observed_state=pr_state,
                    quality_issues=tuple(issues_by_entity.get(pr_ref, ())),
                    provenance_refs=(pr_prov,),
                )
            )

            # ── Reviews ──────────────────────────────────────────────
            raw_reviews = pr.get("reviews")
            for review in (raw_reviews if isinstance(raw_reviews, list) else ()):
                rev_id = str(review["review_id"])
                rev_locator = str(review.get("_raw_locator", f"{pr_locator}.reviews[{rev_id}]"))
                rev_ref = EntityRef(
                    source_instance=source_instance,
                    entity_kind="github_review",
                    entity_id=f"{repo_id}/{pr_num}/{rev_id}",
                )
                rev_prov = ProvenanceRef(
                    source_instance=source_instance,
                    observation_id=obs_id,
                    fixture_id=fixture_id,
                    record_locator=rev_locator,
                )

                # State recognition: supported vs unknown
                raw_rev_state = str(review.get("state", ""))
                clean_rev_state = raw_rev_state.strip().upper()
                if clean_rev_state in SUPPORTED_REVIEW_STATES:
                    normalized_rev_state = clean_rev_state
                else:
                    normalized_rev_state = "unknown"
                    rev_state_issue = QualityIssue(
                        code="unsupported_value",
                        message=f"Unsupported review state {raw_rev_state!r}; normalized to 'unknown'.",
                        subject_ref=rev_ref,
                        subject_scope="field:state",
                    )
                    all_issues.append(rev_state_issue)
                    issues_by_entity.setdefault(rev_ref, []).append(rev_state_issue)

                submitted_at = None
                if review.get("submitted_at") is not None:
                    try:
                        submitted_at = _parse_aware_datetime(
                            review["submitted_at"], f"{rev_locator}.submitted_at"
                        )
                    except ValueError:
                        submitted_at = None

                rev_state = GitHubReviewState(
                    review_id=rev_id,
                    state=normalized_rev_state,
                    reviewer_login=(
                        str(review["reviewer_login"])
                        if review.get("reviewer_login") is not None
                        else None
                    ),
                    submitted_at=submitted_at,
                )
                observations.append(
                    EvidenceObservation(
                        entity_ref=rev_ref,
                        observation_context=obs_context,
                        observed_state=rev_state,
                        quality_issues=tuple(issues_by_entity.get(rev_ref, ())),
                        provenance_refs=(rev_prov,),
                    )
                )

    # Sort observations deterministically
    sorted_observations = tuple(
        sorted(
            observations,
            key=lambda o: (
                o.entity_ref.source_instance.instance_id,
                o.entity_ref.entity_kind,
                o.entity_ref.entity_id,
            ),
        )
    )

    # Sort all quality issues deterministically
    all_quality_issues = tuple(
        sorted(
            all_issues,
            key=lambda q: (
                q.code,
                q.subject_ref.entity_id if q.subject_ref else "",
                q.subject_scope or "",
                q.message,
            ),
        )
    )

    # Sort quarantined records deterministically
    sorted_quarantined = tuple(
        sorted(
            validated.quarantined_records,
            key=lambda r: (
                r.entity_kind,
                r.reason_code,
                r.source_id or "",
                r.record_locator or "",
            ),
        )
    )

    return NormalizedGitHubFixture(
        raw_document=validated.raw_document,
        source_instance=source_instance,
        observation_context=obs_context,
        observations=sorted_observations,
        quality_issues=all_quality_issues,
        quarantined_records=sorted_quarantined,
    )
