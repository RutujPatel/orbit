"""Canonical CodeChangeState adapter for Apache GitHub pull requests, commits, and reviews.

Transforms verified raw GitHub JSON records (from official Apache mirrors)
into ORBIT's canonical CodeChangeState and EvidenceObservation models without
modifying engine semantics or inventing missing data.

Preserved Invariants:
    - Rule 6: NEVER convert closed + merged=false into merged (e.g. PR #10123, PR #17401)
    - Rule 7: committed_at is None for pull requests; committed_at is set for commits;
      never map commit timestamp -> merged_at or vice versa
    - Repository-scoped entity identity: base repository (upstream) is canonical scope
    - Fork awareness: tracks head_repo fork vs base_repo canonical upstream
    - Immutable provenance references to acquired artifacts
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shadow_orbit.evidence_types import (
    CodeChangeState,
    EntityRef,
    EvidenceObservation,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    SourceInstance,
)

from .apache_jira_adapter import parse_iso_datetime

APACHE_GITHUB_SOURCE = SourceInstance(source_kind="github", instance_id="github.com/apache")


def adapt_apache_github_pr_to_state(
    raw_pr: dict[str, Any],
    commits: list[dict[str, Any]] | None = None,
    reviews: list[dict[str, Any]] | None = None,
) -> CodeChangeState:
    """Map a raw Apache GitHub pull request record into canonical CodeChangeState.

    Strictly preserves:
    - identifier: string PR number (e.g. "885", "11617", "10123")
    - state: "merged" ONLY if raw_pr['merged'] is True AND raw_pr['merged_at'] is not None.
      If closed and merged is False, state is strictly "closed".
    - created_at, closed_at timestamps
    - merged_at: None if unmerged, exact UTC timestamp if merged
    - committed_at: strictly None for PR-level entities (no timestamp conflation)
    - author: user login
    - source_branch / target_branch
    - head_commit_sha / base_commit_sha
    - extra_properties: upstream repo, head repo, merge_commit_sha, commit list, review list
    """
    number = raw_pr.get("number")
    if number is None:
        raise ValueError("Raw GitHub PR record missing 'number'")
    identifier = str(number)

    created_at = parse_iso_datetime(raw_pr.get("created_at"))
    if created_at is None:
        raise ValueError(f"GitHub PR #{identifier} missing required 'created_at' timestamp")

    title = str(raw_pr.get("title") or "")
    closed_at = parse_iso_datetime(raw_pr.get("closed_at"))

    raw_merged = bool(raw_pr.get("merged", False))
    raw_merged_at = parse_iso_datetime(raw_pr.get("merged_at"))

    # INVARIANT (Rule 6): A closed PR is NOT merged unless GitHub explicitly verified the merge.
    # FLINK-14386 / PR #10123 is closed with merged=False; it must remain closed in state.
    if raw_merged and raw_merged_at is not None:
        state = "merged"
        merged_at = raw_merged_at
    elif raw_pr.get("state") == "closed":
        state = "closed"
        merged_at = None
    elif raw_pr.get("state") == "open":
        state = "open"
        merged_at = None
    else:
        state = str(raw_pr.get("state") or "unknown").lower()
        merged_at = None

    # INVARIANT (Rule 7): committed_at is None for PR entities.
    committed_at = None

    raw_user = raw_pr.get("user")
    author = (
        raw_user.get("login")
        if isinstance(raw_user, dict)
        else (str(raw_user) if raw_user else None)
    )

    source_branch = raw_pr.get("head", {}).get("ref")
    target_branch = raw_pr.get("base", {}).get("ref")
    head_commit_sha = raw_pr.get("head", {}).get("sha")
    base_commit_sha = raw_pr.get("base", {}).get("sha")

    base_repo_obj = raw_pr.get("base", {}).get("repo")
    base_repo = (
        base_repo_obj.get("full_name")
        if isinstance(base_repo_obj, dict)
        else None
    )

    head_repo_obj = raw_pr.get("head", {}).get("repo")
    head_repo = (
        head_repo_obj.get("full_name")
        if isinstance(head_repo_obj, dict)
        else None
    )

    extra_properties: dict[str, Any] = {
        "repo": base_repo,
        "head_repo": head_repo,
        "html_url": raw_pr.get("html_url"),
        "closed_at": raw_pr.get("closed_at"),
        "merge_commit_sha": raw_pr.get("merge_commit_sha"),
        "is_fork": head_repo != base_repo if (head_repo and base_repo) else False,
    }

    if commits:
        extra_properties["commit_shas"] = [
            c.get("sha") for c in commits if isinstance(c, dict) and c.get("sha")
        ]
        extra_properties["commit_count"] = len(commits)

    if reviews:
        extra_properties["review_states"] = [
            r.get("state") for r in reviews if isinstance(r, dict) and r.get("state")
        ]
        extra_properties["review_count"] = len(reviews)

    return CodeChangeState(
        change_type="pull_request",
        identifier=identifier,
        state=state,
        title=title,
        created_at=created_at,
        merged_at=merged_at,
        committed_at=committed_at,
        author=author,
        source_branch=source_branch,
        target_branch=target_branch,
        head_commit_sha=head_commit_sha,
        base_commit_sha=base_commit_sha,
        extra_properties=extra_properties,
    )


def adapt_apache_github_pr(
    raw_pr: dict[str, Any],
    context: ObservationContext,
    fixture_id: str | None = None,
    repo: str | None = None,
    commits: list[dict[str, Any]] | None = None,
    reviews: list[dict[str, Any]] | None = None,
    quality_issues: tuple[QualityIssue, ...] = (),
) -> EvidenceObservation:
    """Adapt a raw Apache GitHub PR into a canonical EvidenceObservation."""
    state = adapt_apache_github_pr_to_state(raw_pr, commits=commits, reviews=reviews)
    eff_repo = repo or state.extra_properties.get("repo") or "apache/unknown"
    entity_id = f"{eff_repo}/{state.identifier}"

    entity_ref = EntityRef(
        source_instance=context.source_instance,
        entity_kind="code_change",
        entity_id=entity_id,
    )

    repo_short = eff_repo.split("/")[-1] if "/" in eff_repo else eff_repo
    eff_fixture_id = (
        fixture_id or f"qualification/wave3/apache_real/github/{repo_short}/pull_{state.identifier}.json"
    )
    provenance = ProvenanceRef(
        source_instance=context.source_instance,
        observation_id=context.observation_id,
        fixture_id=eff_fixture_id,
        record_locator=f"pull_requests[{state.identifier}]",
        source_field_path="number",
    )
    return EvidenceObservation(
        entity_ref=entity_ref,
        observation_context=context,
        observed_state=state,
        quality_issues=quality_issues,
        provenance_refs=(provenance,),
    )


def adapt_apache_github_commit_to_state(
    raw_commit: dict[str, Any],
    repo: str,
) -> CodeChangeState:
    """Map a raw GitHub commit record into canonical CodeChangeState.

    INVARIANT (Rule 7):
    - committed_at is populated from committer date (or author date).
    - merged_at is strictly None. A commit is NOT a merge.
    - state is "committed".
    - change_type is "commit".
    """
    sha = raw_commit.get("sha")
    if not sha:
        raise ValueError("Raw commit missing 'sha'")

    commit_info = raw_commit.get("commit") or {}
    message = str(commit_info.get("message") or "")
    first_line = message.split("\n", 1)[0] if message else ""

    committer_info = commit_info.get("committer") or {}
    author_info = commit_info.get("author") or {}

    committed_at = parse_iso_datetime(committer_info.get("date")) or parse_iso_datetime(
        author_info.get("date")
    )
    created_at = parse_iso_datetime(author_info.get("date")) or committed_at

    raw_author = raw_commit.get("author")
    author = (
        raw_author.get("login")
        if isinstance(raw_author, dict)
        else (author_info.get("name") if isinstance(author_info, dict) else None)
    )

    return CodeChangeState(
        change_type="commit",
        identifier=sha,
        state="committed",
        title=first_line,
        created_at=created_at,
        merged_at=None,
        committed_at=committed_at,
        author=author,
        extra_properties={"repo": repo, "full_message": message},
    )


def adapt_apache_github_commit(
    raw_commit: dict[str, Any],
    repo: str,
    context: ObservationContext,
    fixture_id: str | None = None,
    quality_issues: tuple[QualityIssue, ...] = (),
) -> EvidenceObservation:
    """Adapt a raw Apache GitHub commit into a canonical EvidenceObservation."""
    state = adapt_apache_github_commit_to_state(raw_commit, repo=repo)
    entity_id = f"{repo}/{state.identifier}"
    entity_ref = EntityRef(
        source_instance=context.source_instance,
        entity_kind="github_commit",
        entity_id=entity_id,
    )
    provenance = ProvenanceRef(
        source_instance=context.source_instance,
        observation_id=context.observation_id,
        fixture_id=fixture_id,
        record_locator=f"commits[{state.identifier}]",
        source_field_path="sha",
    )
    return EvidenceObservation(
        entity_ref=entity_ref,
        observation_context=context,
        observed_state=state,
        quality_issues=quality_issues,
        provenance_refs=(provenance,),
    )
