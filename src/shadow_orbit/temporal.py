"""Pure temporal functions for explicit review-period evaluation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shadow_orbit.types import Change, ReviewPeriod, WorkItem


def is_within_half_open_period(
    timestamp: datetime,
    period: ReviewPeriod,
) -> bool:
    return period.starts_at <= timestamp < period.ends_at_exclusive


def elapsed_complete_days(
    start: datetime,
    end: datetime,
) -> int:
    if end < start:
        raise ValueError("end must not precede start")
    return int((end - start).total_seconds() // 86_400)


def is_overdue(
    due_at: datetime,
    review_cutoff_at: datetime,
) -> bool:
    return due_at < review_cutoff_at


def completion_time(
    item: WorkItem,
    status_mapping: dict[str, str] | None = None,
) -> datetime | None:
    def _is_done(status: Any) -> bool:
        if not isinstance(status, str):
            return False
        if status_mapping is not None:
            return status_mapping.get(status) == "done"
        return status == "Done"

    # 1. Current status check: If the item is not currently completed, completion_time is None.
    current_is_done = _is_done(item.source_status)
    if not current_is_done and status_mapping is None and item.status_category == "done":
        current_is_done = True

    if not current_is_done:
        return None

    # 2. Extract and sort all status changes chronologically.
    status_changes = sorted(
        [change for change in item.changes if change.field == "status"],
        key=lambda change: change.changed_at,
    )

    # 3. If there are status changes, find the latest transition that established
    #    the current terminal completed state (i.e. not superseded by a non-done status).
    if status_changes:
        terminal_done_changes: list[Change] = []
        for change in reversed(status_changes):
            if _is_done(change.to_value):
                terminal_done_changes.append(change)
                if not _is_done(change.from_value):
                    break
            else:
                break

        if terminal_done_changes:
            return terminal_done_changes[-1].changed_at

    # 4. Fallback to resolved_at if no transition established the terminal completed state.
    return item.resolved_at


def completed_during_period(
    item: WorkItem,
    period: ReviewPeriod,
    status_mapping: dict[str, str] | None = None,
) -> bool:
    completed_at = completion_time(item, status_mapping=status_mapping)
    return (
        completed_at is not None
        and is_within_half_open_period(completed_at, period)
    )


def introduced_during_period(
    item: WorkItem,
    period: ReviewPeriod,
) -> bool:
    return is_within_half_open_period(item.created_at, period)


def status_at_period_end(
    item: WorkItem,
    period: ReviewPeriod,
    status_mapping: dict[str, str],
) -> str:
    """
    Reconstruct supported status at period end.

    A complete history is required. Changes after period end are reversed
    from the current source status. Unknown mappings remain indeterminate.
    """
    if not item.history_complete:
        return "unknown"

    current_source_status = item.source_status

    for change in sorted(
        (
            value
            for value in item.changes
            if (
                value.field == "status"
                and value.changed_at >= period.ends_at_exclusive
            )
        ),
        key=lambda value: value.changed_at,
        reverse=True,
    ):
        if current_source_status == change.to_value:
            current_source_status = change.from_value

    return status_mapping.get(current_source_status, "unknown")


def last_meaningful_status_change(
    item: WorkItem,
) -> datetime | None:
    status_changes = [
        change.changed_at
        for change in item.changes
        if change.field == "status"
    ]
    return max(status_changes) if status_changes else None


def blocked_since(
    item: WorkItem,
    status_mapping: dict[str, str] | None = None,
) -> datetime | None:
    transitions = [
        change.changed_at
        for change in item.changes
        if change.field == "status"
        and (
            (status_mapping is not None and status_mapping.get(change.to_value) == "blocked")
            or (status_mapping is None and change.to_value == "Blocked")
        )
    ]
    return max(transitions) if transitions else None
