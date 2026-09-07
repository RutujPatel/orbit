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
