from __future__ import annotations

from pathlib import Path

import pytest

from shadow_orbit.acceptance import (
    execute_clean_week_one,
    execute_clean_week_two,
)
from shadow_orbit.evaluation import evaluate_week_one_rules
from shadow_orbit.fixture_io import (
    load_expected_artifact,
    load_fixture,
)
from shadow_orbit.human_state import validate_human_state
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.validation import validate_fixture


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

CLEAN_WEEK_ONE_FIXTURE = (
    REPOSITORY_ROOT
    / "fixtures"
    / "jira"
    / "northstar_clean_week_1.json"
)

CLEAN_WEEK_TWO_FIXTURE = (
    REPOSITORY_ROOT
    / "fixtures"
    / "jira"
    / "northstar_clean_week_2.json"
)

CLEAN_WEEK_ONE_EXPECTED = (
    REPOSITORY_ROOT
    / "fixtures"
    / "jira"
    / "expected"
    / "clean_week_1_review.json"
)

CLEAN_WEEK_TWO_EXPECTED = (
    REPOSITORY_ROOT
    / "fixtures"
    / "jira"
    / "expected"
    / "clean_week_2_review.json"
)

CLEAN_WEEK_ONE_HUMAN_STATE = (
    REPOSITORY_ROOT
    / "fixtures"
    / "experiments"
    / "northstar_clean_week_1_human_state_for_week_2.json"
)


@pytest.fixture
def clean_week_one_path() -> Path:
    return CLEAN_WEEK_ONE_FIXTURE


@pytest.fixture
def clean_week_two_path() -> Path:
    return CLEAN_WEEK_TWO_FIXTURE


@pytest.fixture
def clean_week_one_expected_path() -> Path:
    return CLEAN_WEEK_ONE_EXPECTED


@pytest.fixture
def clean_week_two_expected_path() -> Path:
    return CLEAN_WEEK_TWO_EXPECTED


@pytest.fixture
def clean_week_one_human_state_path() -> Path:
    return CLEAN_WEEK_ONE_HUMAN_STATE


@pytest.fixture
def clean_week_one_document():
    return load_fixture(CLEAN_WEEK_ONE_FIXTURE)


@pytest.fixture
def clean_week_two_document():
    return load_fixture(CLEAN_WEEK_TWO_FIXTURE)


@pytest.fixture
def clean_week_one_human_document():
    return load_fixture(CLEAN_WEEK_ONE_HUMAN_STATE)


@pytest.fixture
def clean_week_one_normalized(
    clean_week_one_document,
):
    return normalize_fixture(
        validate_fixture(clean_week_one_document)
    )


@pytest.fixture
def clean_week_two_normalized(
    clean_week_two_document,
):
    return normalize_fixture(
        validate_fixture(clean_week_two_document)
    )


@pytest.fixture
def clean_week_one_prior_matches(
    clean_week_one_normalized,
):
    matches, _ = evaluate_week_one_rules(
        clean_week_one_normalized
    )
    return matches


@pytest.fixture
def clean_week_one_human_state(
    clean_week_one_human_document,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_prior_matches,
):
    return validate_human_state(
        clean_week_one_human_document,
        prior_fixture=clean_week_one_normalized,
        current_fixture=clean_week_two_normalized,
        prior_matches=clean_week_one_prior_matches,
    )


@pytest.fixture
def clean_week_one_actual():
    return execute_clean_week_one(
        CLEAN_WEEK_ONE_FIXTURE
    )


@pytest.fixture
def clean_week_two_actual():
    return execute_clean_week_two(
        prior_fixture_path=CLEAN_WEEK_ONE_FIXTURE,
        current_fixture_path=CLEAN_WEEK_TWO_FIXTURE,
        human_state_path=CLEAN_WEEK_ONE_HUMAN_STATE,
    )


@pytest.fixture
def clean_week_one_expected():
    return load_expected_artifact(
        CLEAN_WEEK_ONE_EXPECTED
    )


@pytest.fixture
def clean_week_two_expected():
    return load_expected_artifact(
        CLEAN_WEEK_TWO_EXPECTED
    )
