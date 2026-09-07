from __future__ import annotations

from shadow_orbit.evaluation import (
    calculate_supporting_facts,
    evaluate_week_one_rules,
)


def test_week_one_supporting_facts(clean_week_one_normalized):
    facts = calculate_supporting_facts(clean_week_one_normalized)

    assert facts["accepted_work_item_count"] == 12
    assert facts["planned_at_period_start_count"] == 10
    assert facts["introduced_during_period_count"] == 2
    assert facts["completed_during_period_count"] == 3
    assert facts["planned_completed_during_period_count"] == 2
    assert facts["known_incomplete_at_period_end_count"] == 7
    assert facts["indeterminate_at_period_end_count"] == 2
    assert facts["blocked_at_source_cutoff_count"] == 1
    assert facts["missing_due_date_count"] == 5

    assert facts["planned_at_period_start_keys"] == [
        "PLAT-101",
        "PLAT-102",
        "PLAT-104",
        "PLAT-105",
        "PLAT-106",
        "PLAT-107",
        "PLAT-108",
        "PLAT-109",
        "PLAT-110",
        "PLAT-112",
    ]
    assert facts["introduced_during_period_keys"] == [
        "PLAT-103",
        "PLAT-111",
    ]
    assert facts["completed_during_period_keys"] == [
        "PLAT-101",
        "PLAT-103",
        "PLAT-106",
    ]
    assert facts["manager_facing_completion_percentage"] is None


def test_expected_week_one_rule_matches(clean_week_one_normalized):
    matches, _ = evaluate_week_one_rules(clean_week_one_normalized)

    assert [
        (match.subject_key, match.rule_key, match.rule_version)
        for match in matches
    ] == [
        ("PLAT-104", "BLOCKED_HIGH_PRIORITY", "1"),
        ("PLAT-104", "OVERDUE_HIGH_PRIORITY", "1"),
        ("PLAT-105", "STALLED_WORK", "1"),
    ]


def test_expected_week_one_suppressions(
    clean_week_one_normalized,
):
    _, suppressed = evaluate_week_one_rules(
        clean_week_one_normalized
    )

    assert [
        (value.subject_key, value.rule_key)
        for value in suppressed
    ] == [
        ("PLAT-109", "OVERDUE_HIGH_PRIORITY"),
        ("PLAT-110", "STALLED_WORK"),
    ]


def test_explanations_are_deterministic_and_non_ai(
    clean_week_one_normalized,
):
    first, _ = evaluate_week_one_rules(clean_week_one_normalized)
    second, _ = evaluate_week_one_rules(clean_week_one_normalized)

    assert [
        match.deterministic_explanation for match in first
    ] == [
        match.deterministic_explanation for match in second
    ]

    assert all(
        match.deterministic_explanation
        for match in first
    )


def test_every_match_has_minimum_provenance(
    clean_week_one_normalized,
):
    matches, _ = evaluate_week_one_rules(clean_week_one_normalized)

    for match in matches:
        assert match.subject_key
        assert match.rule_key
        assert match.rule_version == "1"
        assert match.observed
        assert match.threshold
        assert match.calculation
        assert match.evidence_references
