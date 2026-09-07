from __future__ import annotations

from copy import deepcopy

import pytest

from shadow_orbit.human_state import validate_human_state


def _validate(
    document,
    prior,
    current,
    matches,
):
    return validate_human_state(
        document,
        prior_fixture=prior,
        current_fixture=current,
        prior_matches=matches,
    )


def test_valid_human_state_loads(
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    state = _validate(
        clean_week_one_human_document,
        clean_week_one_normalized,
        clean_week_two_normalized,
        clean_week_one_prior_matches,
    )

    assert len(state.finding_feedback) == 2
    assert len(state.commitments) == 1
    assert state.commitments[0].external_key == "COMMITMENT-001"
    assert (
        state.commitments[0].status_at_current_preparation
        == "open"
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "contract_version",
            "unsupported",
            "Unsupported",
        ),
        (
            "organization_key",
            "other-organization",
            "organization",
        ),
        (
            "team_key",
            "other-team",
            "team",
        ),
        (
            "prior_review_label",
            "other-prior-review",
            "prior review label",
        ),
        (
            "current_review_label",
            "other-current-review",
            "current review label",
        ),
    ],
)
def test_invalid_scope_or_contract_fails(
    field,
    value,
    message,
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    document = deepcopy(
        clean_week_one_human_document
    )
    document[field] = value

    with pytest.raises(ValueError, match=message):
        _validate(
            document,
            clean_week_one_normalized,
            clean_week_two_normalized,
            clean_week_one_prior_matches,
        )


def test_current_fixture_predecessor_identity_must_match(
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_document,
    clean_week_one_prior_matches,
):
    current_document = deepcopy(
        clean_week_two_document
    )
    current_document["comparison"]["prior_fixture_id"] = (
        "different-prior-fixture"
    )

    current = normalize_fixture_for_test(
        current_document
    )

    with pytest.raises(
        ValueError,
        match="predecessor identity",
    ):
        _validate(
            clean_week_one_human_document,
            clean_week_one_normalized,
            current,
            clean_week_one_prior_matches,
        )


def normalize_fixture_for_test(document):
    from shadow_orbit.normalization import (
        normalize_fixture,
    )
    from shadow_orbit.validation import validate_fixture

    return normalize_fixture(
        validate_fixture(document)
    )


def test_unknown_feedback_subject_fails(
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    document = deepcopy(
        clean_week_one_human_document
    )
    document["finding_feedback"][0][
        "subject_key"
    ] = "PLAT-999"

    with pytest.raises(ValueError, match="does not exist"):
        _validate(
            document,
            clean_week_one_normalized,
            clean_week_two_normalized,
            clean_week_one_prior_matches,
        )


def test_feedback_must_reference_rule_that_fired_previously(
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    document = deepcopy(
        clean_week_one_human_document
    )
    document["finding_feedback"][1][
        "related_rule_keys"
    ] = ["OVERDUE_HIGH_PRIORITY"]

    with pytest.raises(ValueError, match="did not fire"):
        _validate(
            document,
            clean_week_one_normalized,
            clean_week_two_normalized,
            clean_week_one_prior_matches,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "product_disposition",
            "unsupported-disposition",
        ),
        (
            "learning_classification",
            "unsupported-classification",
        ),
    ],
)
def test_unsupported_feedback_vocabulary_fails(
    field,
    value,
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    document = deepcopy(
        clean_week_one_human_document
    )
    document["finding_feedback"][0][field] = value

    with pytest.raises(ValueError, match="unsupported"):
        _validate(
            document,
            clean_week_one_normalized,
            clean_week_two_normalized,
            clean_week_one_prior_matches,
        )


def test_duplicate_commitment_key_fails(
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    document = deepcopy(
        clean_week_one_human_document
    )
    document["commitments"].append(
        deepcopy(document["commitments"][0])
    )

    with pytest.raises(
        ValueError,
        match="Duplicate commitment",
    ):
        _validate(
            document,
            clean_week_one_normalized,
            clean_week_two_normalized,
            clean_week_one_prior_matches,
        )


def test_invalid_commitment_timestamp_fails(
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    document = deepcopy(
        clean_week_one_human_document
    )
    document["commitments"][0]["due_at"] = (
        "not-a-timestamp"
    )

    with pytest.raises(
        ValueError,
        match="valid ISO 8601",
    ):
        _validate(
            document,
            clean_week_one_normalized,
            clean_week_two_normalized,
            clean_week_one_prior_matches,
        )


def test_timezone_naive_commitment_timestamp_fails(
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    document = deepcopy(
        clean_week_one_human_document
    )
    document["commitments"][0]["created_at"] = (
        "2026-02-09T10:15:00"
    )

    with pytest.raises(
        ValueError,
        match="timezone information",
    ):
        _validate(
            document,
            clean_week_one_normalized,
            clean_week_two_normalized,
            clean_week_one_prior_matches,
        )


def test_inconsistent_commitment_origin_review_fails(
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    document = deepcopy(
        clean_week_one_human_document
    )
    document["commitments"][0][
        "origin_review_label"
    ] = "2026-W05"

    with pytest.raises(
        ValueError,
        match="must match the prior review",
    ):
        _validate(
            document,
            clean_week_one_normalized,
            clean_week_two_normalized,
            clean_week_one_prior_matches,
        )


def test_unsupported_current_commitment_status_fails(
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    document = deepcopy(
        clean_week_one_human_document
    )
    document["commitments"][0][
        "status_at_current_preparation"
    ] = "unknown"

    with pytest.raises(
        ValueError,
        match="status_at_current_preparation is unsupported",
    ):
        _validate(
            document,
            clean_week_one_normalized,
            clean_week_two_normalized,
            clean_week_one_prior_matches,
        )
