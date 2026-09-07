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
