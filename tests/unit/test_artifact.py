from __future__ import annotations

from shadow_orbit.artifact import (
    machine_derived_projection,
    serialize_deterministically,
)


def test_findings_are_grouped_without_losing_matches(
    clean_week_one_actual,
):
    attention = clean_week_one_actual["what_needs_attention"]

    assert attention["grouped_work_item_count"] == 2
    assert attention["underlying_finding_count"] == 3

    plat_104 = next(
        item
        for item in attention["items"]
        if item["subject_key"] == "PLAT-104"
    )

    assert [
        match["rule_key"]
        for match in plat_104["underlying_matches"]
    ] == [
        "BLOCKED_HIGH_PRIORITY",
        "OVERDUE_HIGH_PRIORITY",
    ]


def test_artifact_contains_no_severity_or_completion_percentage(
    clean_week_one_actual,
):
    serialized = serialize_deterministically(clean_week_one_actual)

    assert '"severity"' not in serialized
    assert '"risk"' not in serialized
    assert (
        clean_week_one_actual["supporting_facts"][
            "manager_facing_completion_percentage"
        ]
        is None
    )


def test_artifact_does_not_fabricate_human_state(
    clean_week_one_actual,
):
    assert "synthetic_human_review_state" not in clean_week_one_actual
    assert "unaided_agenda" not in clean_week_one_actual
    assert "decisions" not in clean_week_one_actual
    assert "commitments_created" not in clean_week_one_actual


def test_machine_projection_is_explicit(
    clean_week_one_expected,
):
    projection = machine_derived_projection(
        clean_week_one_expected
    )

    assert "synthetic_human_review_state" not in projection
    assert set(projection) == {
        "expected_artifact_version",
        "fixture_id",
        "contract_notice",
        "review",
        "configuration",
        "what_changed_since_last_review",
        "supporting_facts",
        "what_needs_attention",
        "what_orbit_could_not_determine",
        "open_and_carried_commitments",
        "historical_assertions",
    }


def test_serialization_is_stable(clean_week_one_actual):
    first = serialize_deterministically(clean_week_one_actual)
    second = serialize_deterministically(clean_week_one_actual)

    assert first == second


def test_stalled_work_material_values_uses_latest_meaningful_status_change(
    clean_week_one_normalized,
):
    from dataclasses import replace
    from datetime import datetime, timezone
    from shadow_orbit.artifact import build_machine_review_artifact
    from shadow_orbit.types import Change

    plat_105 = next(
        item for item in clean_week_one_normalized.work_items if item.key == "PLAT-105"
    )
    earlier = Change(
        field="status",
        from_value="To Do",
        to_value="In Progress",
        changed_at=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc),
    )
    later = Change(
        field="status",
        from_value="In Progress",
        to_value="In Progress",
        changed_at=datetime(2026, 1, 27, 14, 0, tzinfo=timezone.utc),
    )
    updated_105 = replace(plat_105, changes=(earlier, later))
    updated_items = tuple(
        updated_105 if item.key == "PLAT-105" else item
        for item in clean_week_one_normalized.work_items
    )
    fixture = replace(clean_week_one_normalized, work_items=updated_items)

    artifact = build_machine_review_artifact(fixture)
    attention_105 = next(
        item
        for item in artifact["what_needs_attention"]["items"]
        if item["subject_key"] == "PLAT-105"
    )
    assert (
        attention_105["material_values"]["last_meaningful_status_change_at"]
        == "2026-01-27T14:00:00Z"
    )


def test_blocked_and_overdue_without_blocked_transition_does_not_crash(
    clean_week_one_normalized,
):
    from dataclasses import replace
    from shadow_orbit.artifact import build_machine_review_artifact

    plat_104 = next(
        item for item in clean_week_one_normalized.work_items if item.key == "PLAT-104"
    )
    updated_104 = replace(plat_104, changes=())
    updated_items = tuple(
        updated_104 if item.key == "PLAT-104" else item
        for item in clean_week_one_normalized.work_items
    )
    fixture = replace(clean_week_one_normalized, work_items=updated_items)

    artifact = build_machine_review_artifact(fixture)
    attention_104 = next(
        item
        for item in artifact["what_needs_attention"]["items"]
        if item["subject_key"] == "PLAT-104"
    )
    assert (
        "ORBIT could not determine when the blocked condition began"
        in attention_104["deterministic_explanation"]
    )
    assert attention_104["material_values"]["blocked_since"] is None

