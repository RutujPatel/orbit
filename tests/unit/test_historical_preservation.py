from __future__ import annotations

from copy import deepcopy

from shadow_orbit.acceptance import (
    execute_clean_week_one,
    execute_clean_week_two,
)
from shadow_orbit.artifact import (
    serialize_deterministically,
)


def test_week_one_artifact_is_unchanged_after_week_two_preparation(
    clean_week_one_path,
    clean_week_two_path,
    clean_week_one_human_state_path,
):
    week_one_before = execute_clean_week_one(
        clean_week_one_path
    )
    copied_before = deepcopy(
        week_one_before
    )
    serialized_before = serialize_deterministically(
        week_one_before
    )

    week_two = execute_clean_week_two(
        prior_fixture_path=clean_week_one_path,
        current_fixture_path=clean_week_two_path,
        human_state_path=(
            clean_week_one_human_state_path
        ),
    )

    week_one_after = execute_clean_week_one(
        clean_week_one_path
    )

    assert week_one_before == copied_before
    assert week_one_after == week_one_before
    assert (
        serialize_deterministically(week_one_after)
        == serialized_before
    )
    assert week_two is not week_one_before


def test_week_one_plat_104_state_remains_preserved(
    clean_week_one_actual,
    clean_week_two_actual,
):
    week_one_item = next(
        item
        for item in clean_week_one_actual[
            "what_needs_attention"
        ]["items"]
        if item["subject_key"] == "PLAT-104"
    )
    week_two_item = next(
        item
        for item in clean_week_two_actual[
            "what_needs_attention"
        ]["items"]
        if item["subject_key"] == "PLAT-104"
    )

    assert (
        week_one_item["material_values"]["status"]
        == "Blocked"
    )
    assert (
        week_one_item["material_values"]["due_at"]
        == "2026-02-08T17:00:00Z"
    )

    assert (
        week_two_item["material_values"]["status"]
        == "In Progress"
    )
    assert (
        week_two_item["material_values"]["due_at"]
        == "2026-02-15T17:00:00Z"
    )


def test_plat_107_remains_known_incomplete_at_week_one_period_end(
    clean_week_one_actual,
):
    facts = clean_week_one_actual[
        "supporting_facts"
    ]

    assert "PLAT-107" in facts[
        "known_incomplete_at_period_end_keys"
    ]
    assert "PLAT-107" not in facts[
        "completed_during_period_keys"
    ]
