"""Synthetic offline adapters for third-party providers (Linear and GitLab).

These adapters are pure transformation helpers used for offline proving of
Project ORBIT's canonical evidence path. They convert synthetic provider-native
records into canonical WorkItemState, CodeChangeState, and EvidenceObservation
instances without network I/O, credentials, or live APIs.

Governing Principles:
    - deterministic facts first
    - evidence before confidence
    - unknown != false
    - missing != complete
    - unmapped != normal
    - invalid != absent
    - unsupported inference != deterministic fact
    - NEVER manufacture timestamps (e.g. NEVER merged_at -> committed_at)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shadow_orbit.evidence_types import (
    CodeChangeState,
    EntityRef,
    EvidenceObservation,
    ObservationContext,
    QualityIssue,
    SourceInstance,
    WorkItemState,
)


def _parse_datetime(val: Any) -> datetime | None:
    """Parse an ISO-8601 string or datetime object deterministically.

    Returns None if val is None, empty, or unparseable.
    Never manufactures a timestamp or defaults to current time.
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    return None


# ── Linear Work Item Adapter ──────────────────────────────────────────

_LINEAR_STATE_CATEGORY_MAP: dict[str, str] = {
    "completed": "done",
    "done": "done",
    "started": "in_progress",
    "in_progress": "in_progress",
    "unstarted": "to_do",
    "triage": "to_do",
    "backlog": "to_do",
    "to_do": "to_do",
    "canceled": "rejected",
    "cancelled": "rejected",
    "rejected": "rejected",
}


def adapt_linear_issue_to_state(record: dict[str, Any]) -> WorkItemState:
    """Map a synthetic Linear issue record to canonical WorkItemState.

    Preserves observed timestamps and values faithfully without manufacturing.
    Missing information remains None.
    """
    ident = str(record.get("identifier") or record.get("id") or record.get("key") or "")
    if not ident:
        raise ValueError("Linear record must contain 'identifier', 'id', or 'key'")

    raw_state = record.get("state")
    if isinstance(raw_state, dict):
        source_status = str(raw_state.get("name") or "Unknown")
        state_type = str(raw_state.get("type") or "").lower()
    else:
        source_status = str(record.get("status") or raw_state or "Unknown")
        state_type = str(record.get("status_type") or record.get("status_category") or source_status).lower()

    status_category = _LINEAR_STATE_CATEGORY_MAP.get(state_type, "unknown")

    raw_prio = record.get("priority")
    prio_label = record.get("priority_label")
    source_priority = str(prio_label) if prio_label is not None else (str(raw_prio) if raw_prio is not None else None)

    priority_band = record.get("priority_band")
    if priority_band is None and raw_prio is not None:
        # Linear standard priority numbers: 1=Urgent, 2=High, 3=Medium, 4=Low, 0=No priority
        prio_bands = {1: "urgent", 2: "high", 3: "medium", 4: "low"}
        priority_band = prio_bands.get(raw_prio)

    created_at = _parse_datetime(record.get("created_at"))
    updated_at = _parse_datetime(record.get("updated_at"))
    resolved_at = _parse_datetime(
        record.get("completed_at") or record.get("resolved_at") or record.get("canceled_at")
    )
    due_at = _parse_datetime(record.get("due_date") or record.get("due_at"))

    if created_at is None:
        raise ValueError("Linear record must contain 'created_at'")

    raw_assignee = record.get("assignee")
    assignee = raw_assignee.get("name") if isinstance(raw_assignee, dict) else (str(raw_assignee) if raw_assignee else None)
    title = str(record.get("title") or record.get("summary") or "")

    extras = dict(record.get("extra_properties", {}))
    if title:
        extras["title"] = title

    return WorkItemState(
        identifier=ident,
        source_status=source_status,
        status_category=status_category,
        source_priority=source_priority or "",
        priority_band=priority_band or "medium",
        created_at=created_at,
        updated_at=updated_at,
        resolved_at=resolved_at,
        due_at=due_at,
        assignee=assignee,
        extra_properties=extras,
    )


def adapt_linear_work_item(
    record: dict[str, Any],
    context: ObservationContext,
    source_instance: SourceInstance | None = None,
    quality_issues: tuple[QualityIssue, ...] = (),
) -> EvidenceObservation:
    """Adapt a synthetic Linear record into a canonical EvidenceObservation."""
    state = adapt_linear_issue_to_state(record)
    src = source_instance or context.source_instance
    entity_ref = EntityRef(
        source_instance=src,
        entity_kind="work_item",
        entity_id=state.identifier,
    )
    return EvidenceObservation(
        entity_ref=entity_ref,
        observation_context=context,
        observed_state=state,
        quality_issues=quality_issues,
    )


# ── GitLab Code Change Adapter ─────────────────────────────────────────

_GITLAB_STATE_MAP: dict[str, str] = {
    "merged": "merged",
    "opened": "open",
    "open": "open",
    "closed": "closed",
    "locked": "closed",
}


def adapt_gitlab_mr_to_state(record: dict[str, Any]) -> CodeChangeState:
    """Map a synthetic GitLab merge request record to canonical CodeChangeState.

    CRITICAL INVARIANT:
        committed_at is ALWAYS None for merge requests unless explicitly and
        independently observed in a commit record.
        NEVER infer or manufacture committed_at from merged_at.
    """
    iid = record.get("iid") or record.get("id") or record.get("identifier")
    if iid is None:
        raise ValueError("GitLab MR record must contain 'iid', 'id', or 'identifier'")
    identifier = str(iid)

    raw_state = str(record.get("state") or "opened").lower()
    state = _GITLAB_STATE_MAP.get(raw_state, "unknown")

    title = str(record.get("title") or "")
    created_at = _parse_datetime(record.get("created_at"))
    merged_at = _parse_datetime(record.get("merged_at"))

    # INVARIANT: committed_at is None on merge requests. No merged_at -> committed_at inference.
    committed_at = None

    raw_author = record.get("author")
    author = raw_author.get("username") if isinstance(raw_author, dict) else (str(raw_author) if raw_author else None)

    return CodeChangeState(
        change_type="merge_request",
        identifier=identifier,
        state=state,
        title=title,
        created_at=created_at,
        merged_at=merged_at,
        committed_at=committed_at,
        author=author,
        source_branch=record.get("source_branch"),
        target_branch=record.get("target_branch"),
        head_commit_sha=record.get("sha") or record.get("head_commit_sha"),
        base_commit_sha=record.get("base_commit_sha"),
        extra_properties=record.get("extra_properties", {}),
    )


def adapt_gitlab_merge_request(
    record: dict[str, Any],
    context: ObservationContext,
    source_instance: SourceInstance | None = None,
    quality_issues: tuple[QualityIssue, ...] = (),
) -> EvidenceObservation:
    """Adapt a synthetic GitLab MR into a canonical EvidenceObservation."""
    state = adapt_gitlab_mr_to_state(record)
    src = source_instance or context.source_instance
    entity_ref = EntityRef(
        source_instance=src,
        entity_kind="code_change",
        entity_id=state.identifier,
    )
    return EvidenceObservation(
        entity_ref=entity_ref,
        observation_context=context,
        observed_state=state,
        quality_issues=quality_issues,
    )


def adapt_gitlab_commit_to_state(record: dict[str, Any]) -> CodeChangeState:
    """Map a synthetic GitLab commit record to canonical CodeChangeState.

    Used when a commit is independently observed, supplying committed_at.
    """
    cid = record.get("id") or record.get("sha") or record.get("identifier")
    if cid is None:
        raise ValueError("GitLab commit record must contain 'id', 'sha', or 'identifier'")
    identifier = str(cid)

    title = str(record.get("title") or record.get("message") or "")
    created_at = _parse_datetime(record.get("created_at"))
    committed_at = _parse_datetime(record.get("committed_date") or record.get("committed_at"))

    raw_author = record.get("author_name") or record.get("author")
    author = str(raw_author) if raw_author else None

    return CodeChangeState(
        change_type="commit",
        identifier=identifier,
        state="committed",
        title=title,
        created_at=created_at,
        merged_at=None,
        committed_at=committed_at,
        author=author,
        extra_properties=record.get("extra_properties", {}),
    )


def adapt_gitlab_commit(
    record: dict[str, Any],
    context: ObservationContext,
    source_instance: SourceInstance | None = None,
    quality_issues: tuple[QualityIssue, ...] = (),
) -> EvidenceObservation:
    """Adapt a synthetic GitLab commit into a canonical EvidenceObservation."""
    state = adapt_gitlab_commit_to_state(record)
    src = source_instance or context.source_instance
    entity_ref = EntityRef(
        source_instance=src,
        entity_kind="code_change",
        entity_id=state.identifier,
    )
    return EvidenceObservation(
        entity_ref=entity_ref,
        observation_context=context,
        observed_state=state,
        quality_issues=quality_issues,
    )
