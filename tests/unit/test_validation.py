from __future__ import annotations

from copy import deepcopy

import pytest

from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.validation import validate_fixture


def test_valid_week_one_fixture_accepts_all_records(
    clean_week_one_document,
):
    result = validate_fixture(clean_week_one_document)

    assert len(result.accepted_raw_items) == 12
    assert result.quarantined_records == ()


def test_missing_required_top_level_field_fails(
    clean_week_one_document,
):
    document = deepcopy(clean_week_one_document)
    del document["project"]

    with pytest.raises(ValueError, match="Missing required"):
        validate_fixture(document)


def test_invalid_required_timestamp_quarantines_record(
    clean_week_one_document,
):
    document = deepcopy(clean_week_one_document)
    document["work_items"][0]["updated_at"] = "not-a-timestamp"

    result = validate_fixture(document)

    assert len(result.accepted_raw_items) == 11
    assert result.quarantined_records[0].reason_code == (
        "INVALID_REQUIRED_TIMESTAMP"
    )


def test_source_cutoff_must_not_follow_review_cutoff(
    clean_week_one_document,
):
    document = deepcopy(clean_week_one_document)
    document["review_period"]["source_cutoff_at"] = (
        "2026-02-09T09:00:01Z"
    )

    with pytest.raises(ValueError, match="must not be later"):
        validate_fixture(document)


def test_duplicate_keys_quarantine_every_duplicate(
    clean_week_one_document,
):
    document = deepcopy(clean_week_one_document)
    duplicate = deepcopy(document["work_items"][0])
    duplicate["source_id"] = "duplicate-source-id"
    document["work_items"].append(duplicate)

    result = validate_fixture(document)

    assert len(result.accepted_raw_items) == 11
    assert len(result.quarantined_records) == 2
    assert {
        record.reason_code for record in result.quarantined_records
    } == {"DUPLICATE_EXTERNAL_KEY"}


def test_unmapped_status_remains_explicit(
    clean_week_one_document,
):
    normalized = normalize_fixture(
        validate_fixture(clean_week_one_document)
    )
    item = next(
        value
        for value in normalized.work_items
        if value.key == "PLAT-109"
    )

    assert item.status_category == "unknown"
    assert any(
        condition.code == "UNKNOWN_STATUS"
        and condition.subject_key == "PLAT-109"
        for condition in normalized.data_quality_conditions
    )


def test_invalid_optional_timestamp_is_treated_as_unknown(
    clean_week_one_document,
):
    document = deepcopy(clean_week_one_document)
    document["work_items"][0]["due_at"] = (
        "2026-02-07T17:00:00"
    )

    validated = validate_fixture(document)

    assert len(validated.accepted_raw_items) == 12
    accepted = next(
        item
        for item in validated.accepted_raw_items
        if item["key"] == "PLAT-101"
    )
    assert accepted["due_at"] is None
    assert any(
        condition.code == "INVALID_OPTIONAL_TIMESTAMP"
        and condition.subject_key == "PLAT-101"
        for condition in validated.validation_conditions
    )


def test_plat_111_is_introduced_and_not_planned(
    clean_week_one_document,
):
    item = next(
        value
        for value in clean_week_one_document["work_items"]
        if value["key"] == "PLAT-111"
    )

    assert item["planned_at_period_start"] is False
    assert item["status_at_period_start"] is None
    assert item["created_at"] == "2026-02-06T10:00:00Z"
