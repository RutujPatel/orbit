import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from datetime import datetime, timezone

from qualification.config import (
    GoGreenJiraConfig,
    FROZEN_ALLOWLIST_PATH,
    FROZEN_ALLOWLIST_SHA256,
    FROZEN_ALLOWLIST_COUNT,
    create_populated_qualification_identity,
)
from qualification.policy import (
    canonical_record_hash,
    redact_sensitive_text,
    sanitize_source_excerpt,
)
from qualification.projection.jira_projection import (
    generate_jira_fixture_id,
    load_frozen_allowlist,
    parse_source_datetime_to_iso,
    project_single_work_item,
    project_gogreen_jira,
)
from shadow_orbit.validation import validate_fixture


def test_deterministic_fixture_id():
    fid1 = generate_jira_fixture_id("pilot115", "r2", "dev")
    fid2 = generate_jira_fixture_id("pilot115", "r2", "dev")
    assert fid1 == fid2
    assert fid1 == "gogreen-jira-pilot115-r2-dev"
    assert "2026" not in fid1


def test_canonical_record_hashing_nested_dicts_and_lists():
    doc1 = {"b": 2, "a": 1, "nested": {"y": [1, 2], "x": "hello"}}
    doc2 = {"nested": {"x": "hello", "y": [1, 2]}, "a": 1, "b": 2}
    hash1 = canonical_record_hash(doc1)
    hash2 = canonical_record_hash(doc2)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_frozen_allowlist_loading_and_digest():
    allowlist = load_frozen_allowlist(FROZEN_ALLOWLIST_PATH)
    assert len(allowlist) == FROZEN_ALLOWLIST_COUNT
    assert "GG-103" in allowlist
    assert "GG-12" in allowlist


def test_frozen_allowlist_digest_mismatch_raises(tmp_path):
    bad_allowlist = tmp_path / "bad_allowlist.txt"
    bad_allowlist.write_text("GG-999\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="digest mismatch"):
        load_frozen_allowlist(bad_allowlist, expected_sha256="badhash123", expected_count=1)


def test_parse_source_datetime_to_iso():
    iso_str = "2026-06-04T18:24:12.964000+05:30"
    assert parse_source_datetime_to_iso(iso_str) == iso_str

    csv_str = "19/May/26 12:28 PM"
    parsed = parse_source_datetime_to_iso(csv_str)
    assert parsed == "2026-05-19T12:28:00+05:30"

    assert parse_source_datetime_to_iso(None) is None
    assert parse_source_datetime_to_iso("") is None

    with pytest.raises(ValueError, match="Unable to parse timestamp"):
        parse_source_datetime_to_iso("not-a-date")


def test_project_single_work_item_honest_null_and_source_id():
    config = GoGreenJiraConfig()
    record = {
        "key": "GG-101",
        "id": "10001",
        "fields": {
            "summary": "Test bug for qualification",
            "issuetype": {"name": "Bug"},
            "priority": {"name": "Highest"},
            "status": {"name": "In Progress"},
            "created": "2026-05-19T12:28:00+05:30",
            "updated": "2026-05-19T12:45:00+05:30",
        },
    }
    item, raw_changes = project_single_work_item(record, config)
    assert item["key"] == "GG-101"
    assert item["source_id"] == "10001"
    assert item["planned_at_period_start"] is None
    assert item["priority"] == "Highest"
    assert item["status"] == "In Progress"
    assert item["item_type"] == "Bug"
    assert raw_changes == []


def test_no_silent_defaults_for_missing_source_fields():
    config = GoGreenJiraConfig()
    # Missing priority must raise ValueError (not default to 'Medium')
    record_no_priority = {
        "key": "GG-101",
        "id": "10001",
        "fields": {
            "summary": "Bug missing priority",
            "issuetype": {"name": "Bug"},
            "status": {"name": "In Progress"},
            "created": "2026-05-19T12:28:00+05:30",
            "updated": "2026-05-19T12:45:00+05:30",
        },
    }
    with pytest.raises(ValueError, match="Missing required source field 'priority'"):
        project_single_work_item(record_no_priority, config)

    # Missing status must raise ValueError (not default to 'To Do')
    record_no_status = {
        "key": "GG-101",
        "id": "10001",
        "fields": {
            "summary": "Bug missing status",
            "issuetype": {"name": "Bug"},
            "priority": {"name": "High"},
            "created": "2026-05-19T12:28:00+05:30",
            "updated": "2026-05-19T12:45:00+05:30",
        },
    }
    with pytest.raises(ValueError, match="Missing required source field 'status'"):
        project_single_work_item(record_no_status, config)

    # Missing issuetype must raise ValueError (not default to 'Task')
    record_no_type = {
        "key": "GG-101",
        "id": "10001",
        "fields": {
            "summary": "Bug missing type",
            "priority": {"name": "High"},
            "status": {"name": "In Progress"},
            "created": "2026-05-19T12:28:00+05:30",
            "updated": "2026-05-19T12:45:00+05:30",
        },
    }
    with pytest.raises(ValueError, match="Missing required source field 'item_type'"):
        project_single_work_item(record_no_type, config)


def test_no_silent_change_drops_malformed_changelog_raises():
    config = GoGreenJiraConfig()
    record = {
        "key": "GG-101",
        "id": "10001",
        "fields": {
            "summary": "Bug with malformed changelog",
            "issuetype": {"name": "Bug"},
            "priority": {"name": "High"},
            "status": {"name": "In Progress"},
            "created": "2026-05-19T12:28:00+05:30",
            "updated": "2026-05-19T12:45:00+05:30",
        },
        "changes": [
            {"field": "status", "from": "To Do"},  # Missing 'to' and 'changed_at'
        ],
    }
    with pytest.raises(ValueError, match="Malformed changelog event"):
        project_single_work_item(record, config)


def test_missing_source_id_raises_value_error_without_fallback():
    config = GoGreenJiraConfig()
    record = {
        "key": "GG-191",
        "fields": {
            "summary": "Bug without source id",
            "issuetype": {"name": "Bug"},
            "priority": {"name": "Highest"},
            "status": {"name": "In Progress"},
            "created": "2026-05-19T12:28:00+05:30",
            "updated": "2026-05-19T12:45:00+05:30",
        },
    }
    with pytest.raises(ValueError, match="Missing immutable source_id"):
        project_single_work_item(record, config)


def test_populated_qualification_identity():
    config = GoGreenJiraConfig()
    identity = create_populated_qualification_identity(config, projection_revision="r2")
    data = identity.to_dict()

    assert data["engine_commit"] == "6d82d12"
    assert data["projection_revision"] == "r2"
    assert "csv_source_export" in data["dataset_hashes"]
    assert "frozen_allowlist" in data["dataset_hashes"]
    assert "source_manifest" in data["dataset_hashes"]
    assert "historical_reference_fixture" in data["dataset_hashes"]
    assert len(data["configuration_digest"]) == 64
    assert data["sampling_seed"] == 42
