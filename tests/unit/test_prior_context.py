def _item(
    artifact,
    subject_key,
):
    return next(
        item
        for item in artifact[
            "what_needs_attention"
        ]["items"]
        if item["subject_key"] == subject_key
    )


def test_plat_105_refires_with_prior_context(
    clean_week_two_actual,
):
    item = _item(
        clean_week_two_actual,
        "PLAT-105",
    )

    assert [
        match["rule_key"]
        for match in item["underlying_matches"]
    ] == ["STALLED_WORK"]

    assert item["prior_disposition"] == {
        "prior_review_label": "2026-W06",
        "related_prior_rules": [
            "STALLED_WORK"
        ],
        "product_disposition": "not_for_this_week",
        "learning_classification": "not_relevant",
        "reason": (
            "Waiting for a scheduled architecture decision."
        ),
        "manager_message": (
            "Last review, you marked this as "
            "not for this week: "
            "'Waiting for a scheduled architecture decision.' "
            "The condition still exists."
        ),
    }


def test_plat_104_receives_overlapping_prior_context(
    clean_week_two_actual,
):
    item = _item(
        clean_week_two_actual,
        "PLAT-104",
    )

    assert [
        match["rule_key"]
        for match in item["underlying_matches"]
    ] == ["OVERDUE_HIGH_PRIORITY"]

    assert item["prior_disposition"] == {
        "prior_review_label": "2026-W06",
        "related_prior_rules": [
            "BLOCKED_HIGH_PRIORITY",
            "OVERDUE_HIGH_PRIORITY",
        ],
        "product_disposition": "included",
        "learning_classification": "already_known",
        "reason": None,
    }


def test_prior_human_context_does_not_suppress_findings(
    clean_week_two_actual,
):
    subjects = {
        item["subject_key"]
        for item in clean_week_two_actual[
            "what_needs_attention"
        ]["items"]
    }

    assert "PLAT-104" in subjects
    assert "PLAT-105" in subjects


def test_human_context_is_not_jira_source_evidence(
    clean_week_two_actual,
):
    for item in clean_week_two_actual[
        "what_needs_attention"
    ]["items"]:
        for evidence in item["evidence_references"]:
            assert not evidence["reference"].startswith(
                "human_state:"
            )

    plat_105 = _item(
        clean_week_two_actual,
        "PLAT-105",
    )

    assert (
        plat_105["prior_disposition"][
            "learning_classification"
        ]
        == "not_relevant"
    )
