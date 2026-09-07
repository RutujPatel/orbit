from __future__ import annotations

from pathlib import Path

import pytest

from shadow_orbit.acceptance import execute_clean_week_one
from shadow_orbit.fixture_io import (
    load_expected_artifact,
    load_fixture,
)
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.validation import validate_fixture


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CLEAN_WEEK_ONE_FIXTURE = (
    REPOSITORY_ROOT
    / "fixtures"
    / "jira"
    / "northstar_clean_week_1.json"
)
CLEAN_WEEK_ONE_EXPECTED = (
    REPOSITORY_ROOT
    / "fixtures"
    / "jira"
    / "expected"
    / "clean_week_1_review.json"
)


@pytest.fixture
def clean_week_one_path() -> Path:
    return CLEAN_WEEK_ONE_FIXTURE


@pytest.fixture
def clean_week_one_expected_path() -> Path:
    return CLEAN_WEEK_ONE_EXPECTED


@pytest.fixture
def clean_week_one_document():
    return load_fixture(CLEAN_WEEK_ONE_FIXTURE)


@pytest.fixture
def clean_week_one_normalized(clean_week_one_document):
    return normalize_fixture(validate_fixture(clean_week_one_document))


@pytest.fixture
def clean_week_one_actual():
    return execute_clean_week_one(CLEAN_WEEK_ONE_FIXTURE)


@pytest.fixture
def clean_week_one_expected():
    return load_expected_artifact(CLEAN_WEEK_ONE_EXPECTED)
