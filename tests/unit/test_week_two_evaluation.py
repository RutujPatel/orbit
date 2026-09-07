from shadow_orbit.evaluation import evaluate_week_one_rules


def test_raw_week_two_evaluator_independent_matches(
    clean_week_two_normalized,
):
    """Raw rule evaluator produces independent matches without continuity selection."""
    matches, _ = evaluate_week_one_rules(
        clean_week_two_normalized
    )

    assert [
        (
            match.subject_key,
            match.rule_key,
            match.rule_version,
        )
        for match in matches
    ] == [
        (
            "PLAT-104",
            "OVERDUE_HIGH_PRIORITY",
            "1",
        ),
        (
            "PLAT-105",
            "STALLED_WORK",
            "1",
        ),
        (
            "PLAT-112",
            "OVERDUE_HIGH_PRIORITY",
            "1",
        ),
        (
            "PLAT-112",
            "STALLED_WORK",
            "1",
        ),
        (
            "PLAT-113",
            "BLOCKED_HIGH_PRIORITY",
            "1",
        ),
    ]

    plat_112_rules = {
        match.rule_key
        for match in matches
        if match.subject_key == "PLAT-112"
    }
    assert plat_112_rules == {
        "OVERDUE_HIGH_PRIORITY",
        "STALLED_WORK",
    }


def test_exact_week_two_suppressions(
    clean_week_two_normalized,
):
    _, suppressed = evaluate_week_one_rules(
        clean_week_two_normalized
    )

    assert [
        (
            result.subject_key,
            result.rule_key,
        )
        for result in suppressed
    ] == [
        (
            "PLAT-109",
            "OVERDUE_HIGH_PRIORITY",
        ),
        (
            "PLAT-110",
            "STALLED_WORK",
        ),
    ]
    assert not any(
        result.subject_key == "PLAT-112"
        for result in suppressed
    )


def test_plat_104_is_overdue_but_no_longer_blocked(
    clean_week_two_normalized,
):
    matches, _ = evaluate_week_one_rules(
        clean_week_two_normalized
    )

    rules = {
        match.rule_key
        for match in matches
        if match.subject_key == "PLAT-104"
    }

    assert rules == {"OVERDUE_HIGH_PRIORITY"}


def test_plat_113_is_blocked_but_not_overdue(
    clean_week_two_normalized,
):
    matches, _ = evaluate_week_one_rules(
        clean_week_two_normalized
    )

    rules = {
        match.rule_key
        for match in matches
        if match.subject_key == "PLAT-113"
    }

    assert rules == {"BLOCKED_HIGH_PRIORITY"}


def test_week_two_continuity_manager_facing_findings_and_precedence(
    clean_week_two_actual,
):
    """Week 2 continuity selects manager-facing findings with overdue precedence for PLAT-112."""
    attention = clean_week_two_actual[
        "what_needs_attention"
    ]

    assert attention["grouped_work_item_count"] == 4
    assert (
        attention["underlying_work_item_finding_count"]
        == 4
    )
    assert [
        item["subject_key"]
        for item in attention["items"]
    ] == [
        "PLAT-104",
        "PLAT-105",
        "PLAT-112",
        "PLAT-113",
    ]

    plat_112_items = [
        item
        for item in attention["items"]
        if item["subject_key"] == "PLAT-112"
    ]
    assert len(plat_112_items) == 1
    plat_112 = plat_112_items[0]

    assert plat_112["condition_summary"] == (
        "High-priority work remains incomplete after its due date."
    )
    assert [
        m["rule_key"] for m in plat_112["underlying_matches"]
    ] == ["OVERDUE_HIGH_PRIORITY"]

    # Verify STALLED_WORK does not appear as a separate manager-facing item or underlying match
    all_attention_rules = [
        match["rule_key"]
        for item in attention["items"]
        for match in item["underlying_matches"]
    ]
    assert all_attention_rules == [
        "OVERDUE_HIGH_PRIORITY",
        "STALLED_WORK",
        "OVERDUE_HIGH_PRIORITY",
        "BLOCKED_HIGH_PRIORITY",
    ]
