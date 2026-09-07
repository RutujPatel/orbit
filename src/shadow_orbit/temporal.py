"""Pure temporal functions for explicit review-period evaluation."""

from __future__ import annotations

from datetime import datetime

from shadow_orbit.types import ReviewPeriod, WorkItem


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


def completion_time(item: WorkItem) -> datetime | None:
    done_transitions = [
        change.changed_at
        for change in item.changes
        if change.field == "status" and change.to_value == "Done"
    ]

    candidates = done_transitions[:]
    if item.resolved_at is not None:
        candidates.append(item.resolved_at)

    return min(candidates) if candidates else None


def completed_during_period(
    item: WorkItem,
    period: ReviewPeriod,
) -> bool:
    completed_at = completion_time(item)
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


def blocked_since(item: WorkItem) -> datetime | None:
    transitions = [
        change.changed_at
        for change in item.changes
        if change.field == "status" and change.to_value == "Blocked"
    ]
    return max(transitions) if transitions else None
