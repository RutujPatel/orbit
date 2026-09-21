"""Validation of the bounded Shadow ORBIT GitHub fixture contract.

Validates raw JSON against the shadow-github-fixture-v1 specification.
Structurally invalid records are quarantined; unparseable optional values
are represented as explicit QualityIssue instances.

Source Independence:
This module does NOT import or reference any Jira modules or Jira domain types.
No person identity resolution is performed.
No Jira keys or mention extraction is performed.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from shadow_orbit.evidence_types import (
    EntityRef,
    ObservationContext,
    QualityIssue,
    SourceInstance,
)


CONTRACT_VERSION = "shadow-github-fixture-v1"

_REQUIRED_TOP_LEVEL = {
    "contract_version",
    "fixture_id",
    "source_instance",
    "observation_context",
    "repositories",
}

_REQUIRED_SOURCE_INSTANCE = {"source_kind", "instance_id"}

_REQUIRED_OBSERVATION_CONTEXT = {"observation_id"}

_KNOWN_SOURCE_COMPLETENESS_FIELDS = {
    "repositories_complete",
    "branches_complete",
    "commits_complete",
    "pull_requests_complete",
    "reviews_complete",
}

_REQUIRED_REPO_FIELDS = {"repo_id", "owner", "name"}

_REQUIRED_BRANCH_FIELDS = {"name"}

_REQUIRED_COMMIT_FIELDS = {"sha", "message"}

_REQUIRED_PR_FIELDS = {"number", "title", "state"}

_REQUIRED_REVIEW_FIELDS = {"review_id", "state"}


@dataclass(frozen=True, slots=True)
class GitHubQuarantinedRecord:
    """An invalid GitHub record isolated from normalized evidence."""

    source_id: str | None
    entity_kind: str
    reason_code: str
    reason: str
    record_locator: str | None = None


@dataclass(frozen=True, slots=True)
class ValidatedGitHubFixture:
    """Validated representation of a GitHub fixture.

    Container immutability: this object is frozen and slotted, and all
    collection attributes are immutable tuples. The raw JSON-compatible
    dictionaries (raw_document, accepted_repositories) are preserved for
    source auditability.
    """

    raw_document: dict[str, Any]
    source_instance: SourceInstance
    observation_context: ObservationContext
    accepted_repositories: tuple[dict[str, Any], ...]
    quarantined_records: tuple[GitHubQuarantinedRecord, ...]
    quality_issues: tuple[QualityIssue, ...]


def _is_exact_str(val: Any) -> bool:
    return isinstance(val, str)


def _is_non_empty_str(val: Any) -> bool:
    return isinstance(val, str) and bool(val.strip())


def _is_exact_int(val: Any) -> bool:
    return isinstance(val, int) and not isinstance(val, bool)


def _is_valid_id(val: Any) -> bool:
    if isinstance(val, bool):
        return False
    if isinstance(val, int):
        return True
    if isinstance(val, str) and bool(val.strip()):
        return True
    return False


def _parse_aware_datetime(value: Any, field_path: str) -> datetime:
    """Parse an ISO 8601 string requiring timezone awareness.

    Pure function implemented directly to avoid importing Jira validation.
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_path} must be an ISO 8601 string.")

    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(
            f"{field_path} must be a valid ISO 8601 timestamp."
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_path} must include timezone information.")

    return parsed


def _require_mapping(document: dict[str, Any], field: str) -> dict[str, Any]:
    value = document.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object.")
    return value


def _validate_document_structure(document: dict[str, Any]) -> None:
    missing = sorted(_REQUIRED_TOP_LEVEL - document.keys())
    if missing:
        raise ValueError(f"Missing required top-level fields: {missing}")

    if document["contract_version"] != CONTRACT_VERSION:
        raise ValueError(
            f"Unsupported contract_version: {document['contract_version']!r}"
        )

    if not _is_non_empty_str(document["fixture_id"]):
        raise ValueError("fixture_id must be a non-empty string.")

    source_instance = _require_mapping(document, "source_instance")
    missing_instance = sorted(_REQUIRED_SOURCE_INSTANCE - source_instance.keys())
    if missing_instance:
        raise ValueError(
            f"Missing required source_instance fields: {missing_instance}"
        )

    if source_instance["source_kind"] != "github":
        raise ValueError("source_instance.source_kind must equal 'github'.")

    if not _is_non_empty_str(source_instance["instance_id"]):
        raise ValueError("source_instance.instance_id must be a non-empty string.")

    obs_context = _require_mapping(document, "observation_context")
    missing_obs = sorted(_REQUIRED_OBSERVATION_CONTEXT - obs_context.keys())
    if missing_obs:
        raise ValueError(
            f"Missing required observation_context fields: {missing_obs}"
        )

    if not _is_non_empty_str(obs_context["observation_id"]):
        raise ValueError(
            "observation_context.observation_id must be a non-empty string."
        )

    if not isinstance(document["repositories"], list):
        raise ValueError("repositories must be an array.")


def validate_github_fixture(document: dict[str, Any]) -> ValidatedGitHubFixture:
    """Validate a GitHub fixture document without mutating caller state."""
    working = deepcopy(document)
    _validate_document_structure(working)

    inst_data = working["source_instance"]
    source_instance = SourceInstance(
        source_kind="github",
        instance_id=str(inst_data["instance_id"]),
    )

    obs_data = working["observation_context"]
    obs_id = str(obs_data["observation_id"])

    # Validate observation timestamps
    obs_starts = None
    obs_ends = None
    source_cutoff = None
    quality_issues: list[QualityIssue] = []

    for ts_field, attr_name in (
        ("observed_interval_starts_at", "obs_starts"),
        ("observed_interval_ends_at_exclusive", "obs_ends"),
        ("source_cutoff_at", "source_cutoff"),
    ):
        val = obs_data.get(ts_field)
        if val is not None:
            try:
                parsed = _parse_aware_datetime(val, f"observation_context.{ts_field}")
                if attr_name == "obs_starts":
                    obs_starts = parsed
                elif attr_name == "obs_ends":
                    obs_ends = parsed
                elif attr_name == "source_cutoff":
                    source_cutoff = parsed
            except ValueError as exc:
                quality_issues.append(
                    QualityIssue(
                        code="invalid",
                        message=str(exc),
                        subject_scope=f"observation_context:{ts_field}",
                    )
                )

    if obs_starts and obs_ends and obs_starts >= obs_ends:
        quality_issues.append(
            QualityIssue(
                code="contradictory",
                message="observed_interval_starts_at must precede observed_interval_ends_at_exclusive.",
                subject_scope="observation_context:interval",
            )
        )

    coverage_note = obs_data.get("coverage_note")
    if coverage_note is not None and not isinstance(coverage_note, str):
        quality_issues.append(
            QualityIssue(
                code="invalid",
                message="observation_context.coverage_note must be a string.",
                subject_scope="observation_context:coverage_note",
            )
        )
        coverage_note = None

    observation_context = ObservationContext(
        observation_id=obs_id,
        source_instance=source_instance,
        observed_interval_starts_at=obs_starts,
        observed_interval_ends_at_exclusive=obs_ends,
        source_cutoff_at=source_cutoff,
        coverage_note=coverage_note,
    )

    # ── Source Completeness Validation ───────────────────────────────
    if "source_completeness" in working:
        sc = working["source_completeness"]
        if not isinstance(sc, dict):
            quality_issues.append(
                QualityIssue(
                    code="invalid",
                    message="source_completeness must be an object.",
                    subject_scope="document:source_completeness",
                )
            )
        else:
            for sc_key, sc_val in sc.items():
                if sc_key not in _KNOWN_SOURCE_COMPLETENESS_FIELDS:
                    quality_issues.append(
                        QualityIssue(
                            code="unsupported_value",
                            message=f"Unrecognized source_completeness field: {sc_key!r}",
                            subject_scope=f"source_completeness:{sc_key}",
                        )
                    )
                elif sc_val is not None and (not isinstance(sc_val, bool) or isinstance(sc_val, (int, str)) and not isinstance(sc_val, bool)):
                    quality_issues.append(
                        QualityIssue(
                            code="unsupported_value",
                            message=f"source_completeness.{sc_key} must be a boolean or null.",
                            subject_scope=f"source_completeness:{sc_key}",
                        )
                    )

    # ── Repositories Validation ──────────────────────────────────────
    raw_repos = working["repositories"]
    repo_ids = [
        str(r.get("repo_id"))
        for r in raw_repos
        if isinstance(r, dict) and _is_valid_id(r.get("repo_id"))
    ]
    duplicate_repo_ids = {
        rid for rid, count in Counter(repo_ids).items() if count > 1
    }

    accepted_repos: list[dict[str, Any]] = []
    quarantined: list[GitHubQuarantinedRecord] = []

    for r_idx, repo in enumerate(raw_repos):
        raw_repo_locator = f"repositories[{r_idx}]"
        if not isinstance(repo, dict):
            quarantined.append(
                GitHubQuarantinedRecord(
                    source_id=None,
                    entity_kind="github_repository",
                    reason_code="INVALID_RECORD",
                    reason=f"{raw_repo_locator} must be an object.",
                    record_locator=raw_repo_locator,
                )
            )
            continue

        raw_rid = repo.get("repo_id")
        if not _is_valid_id(raw_rid):
            quarantined.append(
                GitHubQuarantinedRecord(
                    source_id=str(raw_rid) if raw_rid is not None else None,
                    entity_kind="github_repository",
                    reason_code="INVALID_FIELD_TYPE",
                    reason=f"{raw_repo_locator}.repo_id must be a non-empty string or integer (not boolean).",
                    record_locator=raw_repo_locator,
                )
            )
            continue

        repo_id = str(raw_rid)

        if repo_id in duplicate_repo_ids:
            quarantined.append(
                GitHubQuarantinedRecord(
                    source_id=repo_id,
                    entity_kind="github_repository",
                    reason_code="DUPLICATE_REPOSITORY_ID",
                    reason=f"All repositories sharing duplicate repo_id {repo_id!r} are quarantined.",
                    record_locator=raw_repo_locator,
                )
            )
            continue

        missing_repo = sorted(_REQUIRED_REPO_FIELDS - repo.keys())
        if missing_repo:
            quarantined.append(
                GitHubQuarantinedRecord(
                    source_id=repo_id,
                    entity_kind="github_repository",
                    reason_code="MISSING_REQUIRED_FIELD",
                    reason=f"Repository missing required fields: {missing_repo}",
                    record_locator=raw_repo_locator,
                )
            )
            continue

        # Check types of required fields
        if not _is_non_empty_str(repo["owner"]):
            quarantined.append(
                GitHubQuarantinedRecord(
                    source_id=repo_id,
                    entity_kind="github_repository",
                    reason_code="INVALID_FIELD_TYPE",
                    reason=f"{raw_repo_locator}.owner must be a non-empty string.",
                    record_locator=raw_repo_locator,
                )
            )
            continue

        if not _is_non_empty_str(repo["name"]):
            quarantined.append(
                GitHubQuarantinedRecord(
                    source_id=repo_id,
                    entity_kind="github_repository",
                    reason_code="INVALID_FIELD_TYPE",
                    reason=f"{raw_repo_locator}.name must be a non-empty string.",
                    record_locator=raw_repo_locator,
                )
            )
            continue

        repo_ref = EntityRef(
            source_instance=source_instance,
            entity_kind="github_repository",
            entity_id=repo_id,
        )

        accepted_repo = deepcopy(repo)
        accepted_repo["repo_id"] = str(repo_id)
        accepted_repo["_raw_locator"] = raw_repo_locator

        # Check default_branch optional type
        if "default_branch" in repo and repo["default_branch"] is not None:
            if not _is_exact_str(repo["default_branch"]):
                accepted_repo["default_branch"] = None
                quality_issues.append(
                    QualityIssue(
                        code="invalid",
                        message=f"{raw_repo_locator}.default_branch must be a string or null.",
                        subject_ref=repo_ref,
                        subject_scope="field:default_branch",
                    )
                )

        # ── Branches ─────────────────────────────────────────────────
        if "branches" in repo:
            if not isinstance(repo["branches"], list):
                quality_issues.append(
                    QualityIssue(
                        code="invalid",
                        message=f"{raw_repo_locator}.branches must be an array.",
                        subject_ref=repo_ref,
                        subject_scope="collection:branches",
                    )
                )
                accepted_repo["branches"] = None
            else:
                accepted_branches = []
                raw_branches = repo["branches"]
                b_names = [
                    b.get("name")
                    for b in raw_branches
                    if isinstance(b, dict) and _is_non_empty_str(b.get("name"))
                ]
                dup_branches = {
                    bn for bn, count in Counter(b_names).items() if count > 1
                }

                for b_idx, branch in enumerate(raw_branches):
                    raw_branch_locator = f"{raw_repo_locator}.branches[{b_idx}]"
                    if not isinstance(branch, dict):
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=None,
                                entity_kind="github_branch",
                                reason_code="INVALID_BRANCH_RECORD",
                                reason=f"{raw_branch_locator} must be an object.",
                                record_locator=raw_branch_locator,
                            )
                        )
                        continue

                    if "name" not in branch:
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=None,
                                entity_kind="github_branch",
                                reason_code="MISSING_REQUIRED_FIELD",
                                reason=f"{raw_branch_locator} missing required field 'name'.",
                                record_locator=raw_branch_locator,
                            )
                        )
                        continue

                    if not _is_non_empty_str(branch["name"]):
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=None,
                                entity_kind="github_branch",
                                reason_code="INVALID_FIELD_TYPE",
                                reason=f"{raw_branch_locator}.name must be a non-empty string.",
                                record_locator=raw_branch_locator,
                            )
                        )
                        continue

                    b_name = branch["name"]
                    if b_name in dup_branches:
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=f"{repo_id}/{b_name}",
                                entity_kind="github_branch",
                                reason_code="DUPLICATE_BRANCH_NAME",
                                reason=f"All branches sharing duplicate name {b_name!r} in repository {repo_id} are quarantined.",
                                record_locator=raw_branch_locator,
                            )
                        )
                        continue

                    branch_ref = EntityRef(
                        source_instance=source_instance,
                        entity_kind="github_branch",
                        entity_id=f"{repo_id}/{b_name}",
                    )

                    accepted_branch = deepcopy(branch)
                    accepted_branch["_raw_locator"] = raw_branch_locator

                    if "head_commit_id" in branch and branch["head_commit_id"] is not None:
                        if not _is_exact_str(branch["head_commit_id"]):
                            accepted_branch["head_commit_id"] = None
                            quality_issues.append(
                                QualityIssue(
                                    code="invalid",
                                    message=f"{raw_branch_locator}.head_commit_id must be a string or null.",
                                    subject_ref=branch_ref,
                                    subject_scope="field:head_commit_id",
                                )
                            )

                    accepted_branches.append(accepted_branch)
                accepted_repo["branches"] = accepted_branches
        else:
            accepted_repo["branches"] = []

        # ── Commits ──────────────────────────────────────────────────
        if "commits" in repo:
            if not isinstance(repo["commits"], list):
                quality_issues.append(
                    QualityIssue(
                        code="invalid",
                        message=f"{raw_repo_locator}.commits must be an array.",
                        subject_ref=repo_ref,
                        subject_scope="collection:commits",
                    )
                )
                accepted_repo["commits"] = None
            else:
                accepted_commits = []
                raw_commits = repo["commits"]
                c_shas = [
                    c.get("sha")
                    for c in raw_commits
                    if isinstance(c, dict) and _is_non_empty_str(c.get("sha"))
                ]
                dup_shas = {
                    sha for sha, count in Counter(c_shas).items() if count > 1
                }

                for c_idx, commit in enumerate(raw_commits):
                    raw_commit_locator = f"{raw_repo_locator}.commits[{c_idx}]"
                    if not isinstance(commit, dict):
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=None,
                                entity_kind="github_commit",
                                reason_code="INVALID_COMMIT_RECORD",
                                reason=f"{raw_commit_locator} must be an object.",
                                record_locator=raw_commit_locator,
                            )
                        )
                        continue

                    missing_c = sorted(_REQUIRED_COMMIT_FIELDS - commit.keys())
                    if missing_c:
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=None,
                                entity_kind="github_commit",
                                reason_code="MISSING_REQUIRED_FIELD",
                                reason=f"{raw_commit_locator} missing required fields: {missing_c}",
                                record_locator=raw_commit_locator,
                            )
                        )
                        continue

                    if not _is_non_empty_str(commit["sha"]):
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=None,
                                entity_kind="github_commit",
                                reason_code="INVALID_FIELD_TYPE",
                                reason=f"{raw_commit_locator}.sha must be a non-empty string.",
                                record_locator=raw_commit_locator,
                            )
                        )
                        continue

                    if not _is_exact_str(commit["message"]):
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=str(commit["sha"]),
                                entity_kind="github_commit",
                                reason_code="INVALID_FIELD_TYPE",
                                reason=f"{raw_commit_locator}.message must be a string.",
                                record_locator=raw_commit_locator,
                            )
                        )
                        continue

                    c_sha = commit["sha"]
                    if c_sha in dup_shas:
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=f"{repo_id}/{c_sha}",
                                entity_kind="github_commit",
                                reason_code="DUPLICATE_COMMIT_SHA",
                                reason=f"All commits sharing duplicate SHA {c_sha!r} in repository {repo_id} are quarantined.",
                                record_locator=raw_commit_locator,
                            )
                        )
                        continue

                    commit_ref = EntityRef(
                        source_instance=source_instance,
                        entity_kind="github_commit",
                        entity_id=f"{repo_id}/{c_sha}",
                    )

                    clean_commit = deepcopy(commit)
                    clean_commit["_raw_locator"] = raw_commit_locator

                    if "author_login" in commit and commit["author_login"] is not None:
                        if not _is_exact_str(commit["author_login"]):
                            clean_commit["author_login"] = None
                            quality_issues.append(
                                QualityIssue(
                                    code="invalid",
                                    message=f"{raw_commit_locator}.author_login must be a string or null.",
                                    subject_ref=commit_ref,
                                    subject_scope="field:author_login",
                                )
                            )

                    if clean_commit.get("committed_at") is not None:
                        try:
                            _parse_aware_datetime(
                                clean_commit["committed_at"],
                                f"{raw_commit_locator}.committed_at",
                            )
                        except ValueError as exc:
                            clean_commit["committed_at"] = None
                            quality_issues.append(
                                QualityIssue(
                                    code="invalid",
                                    message=str(exc),
                                    subject_ref=commit_ref,
                                    subject_scope="field:committed_at",
                                )
                            )

                    accepted_commits.append(clean_commit)
                accepted_repo["commits"] = accepted_commits
        else:
            accepted_repo["commits"] = []

        # ── Pull Requests ────────────────────────────────────────────
        if "pull_requests" in repo:
            if not isinstance(repo["pull_requests"], list):
                quality_issues.append(
                    QualityIssue(
                        code="invalid",
                        message=f"{raw_repo_locator}.pull_requests must be an array.",
                        subject_ref=repo_ref,
                        subject_scope="collection:pull_requests",
                    )
                )
                accepted_repo["pull_requests"] = None
            else:
                accepted_prs = []
                raw_prs = repo["pull_requests"]
                pr_numbers = [
                    p.get("number")
                    for p in raw_prs
                    if isinstance(p, dict) and _is_exact_int(p.get("number")) and p.get("number") > 0
                ]
                dup_pr_numbers = {
                    num for num, count in Counter(pr_numbers).items() if count > 1
                }

                for p_idx, pr in enumerate(raw_prs):
                    raw_pr_locator = f"{raw_repo_locator}.pull_requests[{p_idx}]"
                    if not isinstance(pr, dict):
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=None,
                                entity_kind="github_pull_request",
                                reason_code="INVALID_PR_RECORD",
                                reason=f"{raw_pr_locator} must be an object.",
                                record_locator=raw_pr_locator,
                            )
                        )
                        continue

                    pr_num = pr.get("number")
                    if not _is_exact_int(pr_num) or pr_num <= 0:
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=str(pr_num) if pr_num is not None else None,
                                entity_kind="github_pull_request",
                                reason_code="INVALID_PR_NUMBER",
                                reason=f"{raw_pr_locator}.number must be a positive integer (not boolean).",
                                record_locator=raw_pr_locator,
                            )
                        )
                        continue

                    if pr_num in dup_pr_numbers:
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=f"{repo_id}/{pr_num}",
                                entity_kind="github_pull_request",
                                reason_code="DUPLICATE_PR_NUMBER",
                                reason=f"All pull requests sharing duplicate number #{pr_num} in repository {repo_id} are quarantined.",
                                record_locator=raw_pr_locator,
                            )
                        )
                        continue

                    missing_pr = sorted(_REQUIRED_PR_FIELDS - pr.keys())
                    if missing_pr:
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=f"{repo_id}/{pr_num}",
                                entity_kind="github_pull_request",
                                reason_code="MISSING_REQUIRED_FIELD",
                                reason=f"{raw_pr_locator} missing required fields: {missing_pr}",
                                record_locator=raw_pr_locator,
                            )
                        )
                        continue

                    if not _is_exact_str(pr["title"]):
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=f"{repo_id}/{pr_num}",
                                entity_kind="github_pull_request",
                                reason_code="INVALID_FIELD_TYPE",
                                reason=f"{raw_pr_locator}.title must be a string.",
                                record_locator=raw_pr_locator,
                            )
                        )
                        continue

                    if not _is_non_empty_str(pr["state"]):
                        quarantined.append(
                            GitHubQuarantinedRecord(
                                source_id=f"{repo_id}/{pr_num}",
                                entity_kind="github_pull_request",
                                reason_code="INVALID_FIELD_TYPE",
                                reason=f"{raw_pr_locator}.state must be a non-empty string.",
                                record_locator=raw_pr_locator,
                            )
                        )
                        continue

                    pr_ref = EntityRef(
                        source_instance=source_instance,
                        entity_kind="github_pull_request",
                        entity_id=f"{repo_id}/{pr_num}",
                    )

                    clean_pr = deepcopy(pr)
                    clean_pr["_raw_locator"] = raw_pr_locator

                    for str_opt in ("author_login", "target_branch", "source_branch"):
                        if str_opt in pr and pr[str_opt] is not None:
                            if not _is_exact_str(pr[str_opt]):
                                clean_pr[str_opt] = None
                                quality_issues.append(
                                    QualityIssue(
                                        code="invalid",
                                        message=f"{raw_pr_locator}.{str_opt} must be a string or null.",
                                        subject_ref=pr_ref,
                                        subject_scope=f"field:{str_opt}",
                                    )
                                )

                    for ts_name in ("created_at", "merged_at"):
                        ts_val = clean_pr.get(ts_name)
                        if ts_val is not None:
                            try:
                                _parse_aware_datetime(
                                    ts_val, f"{raw_pr_locator}.{ts_name}"
                                )
                            except ValueError as exc:
                                clean_pr[ts_name] = None
                                quality_issues.append(
                                    QualityIssue(
                                        code="invalid",
                                        message=str(exc),
                                        subject_ref=pr_ref,
                                        subject_scope=f"field:{ts_name}",
                                    )
                                )

                    # ── Reviews ──────────────────────────────────────────
                    if "reviews" in pr:
                        if not isinstance(pr["reviews"], list):
                            quality_issues.append(
                                QualityIssue(
                                    code="invalid",
                                    message=f"{raw_pr_locator}.reviews must be an array.",
                                    subject_ref=pr_ref,
                                    subject_scope="collection:reviews",
                                )
                            )
                            clean_pr["reviews"] = None
                        else:
                            accepted_reviews = []
                            raw_reviews = pr["reviews"]
                            rev_ids = [
                                str(rev.get("review_id"))
                                for rev in raw_reviews
                                if isinstance(rev, dict) and _is_valid_id(rev.get("review_id"))
                            ]
                            dup_rev_ids = {
                                rid for rid, count in Counter(rev_ids).items() if count > 1
                            }

                            for rev_idx, review in enumerate(raw_reviews):
                                raw_rev_locator = f"{raw_pr_locator}.reviews[{rev_idx}]"
                                if not isinstance(review, dict):
                                    quarantined.append(
                                        GitHubQuarantinedRecord(
                                            source_id=None,
                                            entity_kind="github_review",
                                            reason_code="INVALID_REVIEW_RECORD",
                                            reason=f"{raw_rev_locator} must be an object.",
                                            record_locator=raw_rev_locator,
                                        )
                                    )
                                    continue

                                raw_revid = review.get("review_id")
                                if not _is_valid_id(raw_revid):
                                    quarantined.append(
                                        GitHubQuarantinedRecord(
                                            source_id=str(raw_revid) if raw_revid is not None else None,
                                            entity_kind="github_review",
                                            reason_code="INVALID_FIELD_TYPE",
                                            reason=f"{raw_rev_locator}.review_id must be a string or integer (not boolean).",
                                            record_locator=raw_rev_locator,
                                        )
                                    )
                                    continue

                                rev_id = str(raw_revid)
                                if rev_id in dup_rev_ids:
                                    quarantined.append(
                                        GitHubQuarantinedRecord(
                                            source_id=f"{repo_id}/{pr_num}/{rev_id}",
                                            entity_kind="github_review",
                                            reason_code="DUPLICATE_REVIEW_ID",
                                            reason=f"All reviews sharing duplicate review_id {rev_id!r} in PR #{pr_num} are quarantined.",
                                            record_locator=raw_rev_locator,
                                        )
                                    )
                                    continue

                                missing_rev = sorted(_REQUIRED_REVIEW_FIELDS - review.keys())
                                if missing_rev:
                                    quarantined.append(
                                        GitHubQuarantinedRecord(
                                            source_id=f"{repo_id}/{pr_num}/{rev_id}",
                                            entity_kind="github_review",
                                            reason_code="MISSING_REQUIRED_FIELD",
                                            reason=f"{raw_rev_locator} missing required fields: {missing_rev}",
                                            record_locator=raw_rev_locator,
                                        )
                                    )
                                    continue

                                if not _is_non_empty_str(review["state"]):
                                    quarantined.append(
                                        GitHubQuarantinedRecord(
                                            source_id=f"{repo_id}/{pr_num}/{rev_id}",
                                            entity_kind="github_review",
                                            reason_code="INVALID_FIELD_TYPE",
                                            reason=f"{raw_rev_locator}.state must be a non-empty string.",
                                            record_locator=raw_rev_locator,
                                        )
                                    )
                                    continue

                                rev_ref = EntityRef(
                                    source_instance=source_instance,
                                    entity_kind="github_review",
                                    entity_id=f"{repo_id}/{pr_num}/{rev_id}",
                                )

                                clean_review = deepcopy(review)
                                clean_review["review_id"] = rev_id
                                clean_review["_raw_locator"] = raw_rev_locator

                                if "reviewer_login" in review and review["reviewer_login"] is not None:
                                    if not _is_exact_str(review["reviewer_login"]):
                                        clean_review["reviewer_login"] = None
                                        quality_issues.append(
                                            QualityIssue(
                                                code="invalid",
                                                message=f"{raw_rev_locator}.reviewer_login must be a string or null.",
                                                subject_ref=rev_ref,
                                                subject_scope="field:reviewer_login",
                                            )
                                        )

                                if clean_review.get("submitted_at") is not None:
                                    try:
                                        _parse_aware_datetime(
                                            clean_review["submitted_at"],
                                            f"{raw_rev_locator}.submitted_at",
                                        )
                                    except ValueError as exc:
                                        clean_review["submitted_at"] = None
                                        quality_issues.append(
                                            QualityIssue(
                                                code="invalid",
                                                message=str(exc),
                                                subject_ref=rev_ref,
                                                subject_scope="field:submitted_at",
                                            )
                                        )

                                accepted_reviews.append(clean_review)
                            clean_pr["reviews"] = accepted_reviews
                    else:
                        clean_pr["reviews"] = []

                    accepted_prs.append(clean_pr)

                accepted_repo["pull_requests"] = accepted_prs
        else:
            accepted_repo["pull_requests"] = []

        accepted_repos.append(accepted_repo)

    return ValidatedGitHubFixture(
        raw_document=working,
        source_instance=source_instance,
        observation_context=observation_context,
        accepted_repositories=tuple(accepted_repos),
        quarantined_records=tuple(quarantined),
        quality_issues=tuple(quality_issues),
    )
