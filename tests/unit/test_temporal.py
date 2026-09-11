from __future__ import annotations

from datetime import datetime, timezone

from shadow_orbit.temporal import (
    completed_during_period,
    elapsed_complete_days,
    introduced_during_period,
    is_overdue,
    is_within_half_open_period,
)


UTC = timezone.utc


def test_half_open_interval_includes_start_and_excludes_end(
    clean_week_one_normalized,
):
    period = clean_week_one_normalized.review_period

    assert is_within_half_open_period(period.starts_at, period)
    assert not is_within_half_open_period(
        period.ends_at_exclusive,
        period,
    )


def test_plat_106_completion_is_inside_week_one(
    clean_week_one_normalized,
):
    item = next(
        value
        for value in clean_week_one_normalized.work_items
        if value.key == "PLAT-106"
    )

    assert completed_during_period(
        item,
        clean_week_one_normalized.review_period,
    )


def test_plat_107_completion_is_outside_week_one(
    clean_week_one_normalized,
):
    item = next(
        value
        for value in clean_week_one_normalized.work_items
        if value.key == "PLAT-107"
    )

    assert not completed_during_period(
        item,
        clean_week_one_normalized.review_period,
    )


def test_plat_111_is_introduced_during_week_one(
    clean_week_one_normalized,
):
    item = next(
        value
        for value in clean_week_one_normalized.work_items
        if value.key == "PLAT-111"
    )

    assert introduced_during_period(
        item,
        clean_week_one_normalized.review_period,
    )


def test_due_exactly_at_cutoff_is_not_overdue():
    cutoff = datetime(2026, 2, 9, 9, 0, tzinfo=UTC)

    assert not is_overdue(cutoff, cutoff)


def test_plat_112_is_not_overdue_at_week_one_cutoff(
    clean_week_one_normalized,
):
    item = next(
        value
        for value in clean_week_one_normalized.work_items
        if value.key == "PLAT-112"
    )

    assert item.due_at is not None
    assert not is_overdue(
        item.due_at,
        clean_week_one_normalized.review_period.review_cutoff_at,
    )


def test_exactly_seven_complete_days_does_not_exceed_threshold():
    start = datetime(2026, 2, 2, 9, 0, tzinfo=UTC)
    end = datetime(2026, 2, 9, 9, 0, tzinfo=UTC)

    assert elapsed_complete_days(start, end) == 7
    assert not elapsed_complete_days(start, end) > 7


def test_more_than_seven_complete_days_exceeds_threshold():
    start = datetime(2026, 2, 1, 9, 0, tzinfo=UTC)
    end = datetime(2026, 2, 9, 9, 0, tzinfo=UTC)

    assert elapsed_complete_days(start, end) == 8
    assert elapsed_complete_days(start, end) > 7


def test_completion_time_respects_status_mapping():
    from shadow_orbit.temporal import completion_time
    from shadow_orbit.types import Change, WorkItem

    item = WorkItem(
        source_id="1",
        key="TEST-1",
        title="Test",
        item_type="Task",
        source_priority="High",
        priority_band="high",
        source_status="Close",
        status_category="done",
        assignee=None,
        created_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        updated_at=datetime(2026, 2, 5, 9, 0, tzinfo=UTC),
        resolved_at=None,
        due_at=None,
        planned_at_period_start=True,
        history_complete=True,
        source_status_at_period_start=None,
        changes=(
            Change(
                field="status",
                from_value="In Progress",
                to_value="Close",
                changed_at=datetime(2026, 2, 5, 9, 0, tzinfo=UTC),
            ),
        ),
    )
    completed_at = completion_time(item, status_mapping={"Close": "done"})
    assert completed_at == datetime(2026, 2, 5, 9, 0, tzinfo=UTC)


def test_blocked_since_respects_status_mapping():
    from shadow_orbit.temporal import blocked_since
    from shadow_orbit.types import Change, WorkItem

    item = WorkItem(
        source_id="2",
        key="TEST-2",
        title="Test",
        item_type="Task",
        source_priority="High",
        priority_band="high",
        source_status="Waiting",
        status_category="blocked",
        assignee=None,
        created_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
        updated_at=datetime(2026, 2, 4, 9, 0, tzinfo=UTC),
        resolved_at=None,
        due_at=None,
        planned_at_period_start=True,
        history_complete=True,
        source_status_at_period_start=None,
        changes=(
            Change(
                field="status",
                from_value="In Progress",
                to_value="Waiting",
                changed_at=datetime(2026, 2, 4, 9, 0, tzinfo=UTC),
            ),
        ),
    )
    blocked_at = blocked_since(item, status_mapping={"Waiting": "blocked"})
    assert blocked_at == datetime(2026, 2, 4, 9, 0, tzinfo=UTC)

