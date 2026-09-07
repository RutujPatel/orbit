from __future__ import annotations

from dataclasses import replace

from shadow_orbit.deltas import (
    evaluate_commitment_deltas,
    evaluate_work_item_deltas,
)
from shadow_orbit.types import QuarantinedRecord


def _commitment_deltas(
    human_state,
    prior,
    current,
):
    return evaluate_commitment_deltas(
        human_state,
        prior_prepared_commitment_keys=frozenset(),
        prior_review_cutoff=(
            prior.review_period.review_cutoff_at
        ),
        current_review_cutoff=(
            current.review_period.review_cutoff_at
        ),
        current_review_label=current.review_period.label,
    )


def test_exact_work_item_deltas(
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    deltas = evaluate_work_item_deltas(
        clean_week_one_normalized,
        clean_week_two_normalized,
    )

    assert [
        (delta["subject_key"], delta["delta_key"])
        for delta in deltas
    ] == [
        ("PLAT-102", "became_completed"),
        ("PLAT-104", "newly_unblocked"),
        ("PLAT-104", "due_date_changed"),
        ("PLAT-112", "newly_overdue"),
        ("PLAT-113", "newly_introduced"),
        ("PLAT-113", "newly_blocked"),
    ]


def test_required_non_deltas(
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    pairs = {
        (
            delta["subject_key"],
            delta["delta_key"],
        )
        for delta in evaluate_work_item_deltas(
            clean_week_one_normalized,
            clean_week_two_normalized,
        )
    }

    assert (
        "PLAT-107",
        "became_completed",
    ) not in pairs
    assert (
        "PLAT-104",
        "newly_overdue",
    ) not in pairs
    assert (
        "PLAT-113",
        "newly_high_priority",
    ) not in pairs


def test_exact_commitment_deltas(
    clean_week_one_human_state,
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    deltas = _commitment_deltas(
        clean_week_one_human_state,
        clean_week_one_normalized,
        clean_week_two_normalized,
    )

    assert [
        (delta["subject_key"], delta["delta_key"])
        for delta in deltas
    ] == [
        (
            "COMMITMENT-001",
            "commitment_created",
        ),
        (
            "COMMITMENT-001",
            "commitment_newly_overdue",
        ),
        (
            "COMMITMENT-001",
            "commitment_still_open",
        ),
    ]


def test_commitment_created_preserves_historical_origin(
    clean_week_one_human_state,
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    deltas = _commitment_deltas(
        clean_week_one_human_state,
        clean_week_one_normalized,
        clean_week_two_normalized,
    )

    created = next(
        delta
        for delta in deltas
        if delta["delta_key"] == "commitment_created"
    )

    assert created["subject_key"] == "COMMITMENT-001"
    assert created["current_values"] == {
        "origin_review_label": "2026-W06",
        "created_at": "2026-02-09T10:15:00Z",
        "status": "open",
    }
    assert (
        "absent from the prior prepared review"
        in created["semantic_definition"]
    )
    assert (
        "first appears in the current prepared review"
        in created["deterministic_explanation"]
    )


def test_commitment_due_exactly_at_current_cutoff_is_not_overdue(
    clean_week_one_human_state,
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    original = (
        clean_week_one_human_state.commitments[0]
    )
    at_cutoff = replace(
        original,
        due_at=(
            clean_week_two_normalized
            .review_period
            .review_cutoff_at
        ),
    )
    human_state = replace(
        clean_week_one_human_state,
        commitments=(at_cutoff,),
    )

    delta_keys = {
        delta["delta_key"]
        for delta in _commitment_deltas(
            human_state,
            clean_week_one_normalized,
            clean_week_two_normalized,
        )
    }

    assert "commitment_created" in delta_keys
    assert "commitment_still_open" in delta_keys
    assert "commitment_newly_overdue" not in delta_keys


def test_unknown_current_completion_prevents_newly_overdue(
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    altered_items = tuple(
        replace(
            item,
            status_category="unknown",
        )
        if item.key == "PLAT-112"
        else item
        for item in clean_week_two_normalized.work_items
    )

    altered_current = replace(
        clean_week_two_normalized,
        work_items=altered_items,
    )

    pairs = {
        (
            delta["subject_key"],
            delta["delta_key"],
        )
        for delta in evaluate_work_item_deltas(
            clean_week_one_normalized,
            altered_current,
        )
    }

    assert (
        "PLAT-112",
        "newly_overdue",
    ) not in pairs


def test_quarantined_current_record_produces_no_delta(
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    quarantined = QuarantinedRecord(
        source_key="PLAT-113",
        source_id="10013",
        reason_code="INVALID_REQUIRED_TIMESTAMP",
        reason=(
            "PLAT-113 is explicitly represented as quarantined "
            "for this focused delta test."
        ),
    )

    altered_current = replace(
        clean_week_two_normalized,
        work_items=tuple(
            item
            for item in clean_week_two_normalized.work_items
            if item.key != "PLAT-113"
        ),
        quarantined_records=(
            *clean_week_two_normalized.quarantined_records,
            quarantined,
        ),
    )

    assert any(
        record.source_key == "PLAT-113"
        for record in altered_current.quarantined_records
    )
    assert all(
        item.key != "PLAT-113"
        for item in altered_current.work_items
    )

    pairs = {
        (
            delta["subject_key"],
            delta["delta_key"],
        )
        for delta in evaluate_work_item_deltas(
            clean_week_one_normalized,
            altered_current,
        )
    }

    assert (
        "PLAT-113",
        "newly_introduced",
    ) not in pairs
    assert (
        "PLAT-113",
        "newly_blocked",
    ) not in pairs


def test_completion_at_current_period_start_is_included(
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    period_start = (
        clean_week_two_normalized
        .review_period
        .starts_at
    )

    altered_items = []

    for item in clean_week_two_normalized.work_items:
        if item.key != "PLAT-102":
            altered_items.append(item)
            continue

        altered_changes = tuple(
            replace(
                change,
                changed_at=period_start,
            )
            if (
                change.field == "status"
                and change.to_value == "Done"
            )
            else change
            for change in item.changes
        )

        altered_items.append(
            replace(
                item,
                resolved_at=period_start,
                changes=altered_changes,
            )
        )

    altered_current = replace(
        clean_week_two_normalized,
        work_items=tuple(altered_items),
    )

    pairs = {
        (
            delta["subject_key"],
            delta["delta_key"],
        )
        for delta in evaluate_work_item_deltas(
            clean_week_one_normalized,
            altered_current,
        )
    }

    assert (
        "PLAT-102",
        "became_completed",
    ) in pairs


def test_completion_at_current_period_end_is_excluded(
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    period_end = (
        clean_week_two_normalized
        .review_period
        .ends_at_exclusive
    )

    altered_items = []

    for item in clean_week_two_normalized.work_items:
        if item.key != "PLAT-102":
            altered_items.append(item)
            continue

        altered_changes = tuple(
            replace(
                change,
                changed_at=period_end,
            )
            if (
                change.field == "status"
                and change.to_value == "Done"
            )
            else change
            for change in item.changes
        )

        altered_items.append(
            replace(
                item,
                resolved_at=period_end,
                changes=altered_changes,
            )
        )

    altered_current = replace(
        clean_week_two_normalized,
        work_items=tuple(altered_items),
    )

    pairs = {
        (
            delta["subject_key"],
            delta["delta_key"],
        )
        for delta in evaluate_work_item_deltas(
            clean_week_one_normalized,
            altered_current,
        )
    }

    assert (
        "PLAT-102",
        "became_completed",
    ) not in pairs
