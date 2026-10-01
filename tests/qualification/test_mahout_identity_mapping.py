"""Qualification Tests for Source-to-Destination Identity Mapping.

Tests:
1. Destination keys must come from Jira create response, never derived from source keys.
2. Explicit mapping records source_key, source_issue_id, destination_key, destination_issue_id.
3. Idempotent registration prevents duplicate or conflicting entries.
4. Persistence round-trip verifies disk serialization and hash binding.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from qualification.mahout.identity_mapping import (
    SourceDestinationRecord,
    SourceDestinationRegistry,
)


def test_identity_mapping_from_jira_response(tmp_path: Path) -> None:
    mapping_file = tmp_path / "test_identity_mapping.json"
    registry = SourceDestinationRegistry(mapping_path=mapping_file)

    # Simulated Jira create responses
    jira_resp1 = {"id": "10045", "key": "ORBITLAB-1", "self": "https://tecblic.atlassian.net/rest/api/3/issue/10045"}
    jira_resp2 = {"id": "10046", "key": "ORBITLAB-2", "self": "https://tecblic.atlassian.net/rest/api/3/issue/10046"}

    rec1 = registry.register_creation(
        source_key="MAHOUT-1465",
        source_issue_id="126789",
        jira_create_response=jira_resp1,
        initial_status="To Do",
        created_at_iso="2026-09-24T12:00:00Z",
    )

    rec2 = registry.register_creation(
        source_key="MAHOUT-979",
        source_issue_id="125432",
        jira_create_response=jira_resp2,
        initial_status="To Do",
        created_at_iso="2026-09-24T12:01:00Z",
    )

    # Destination keys MUST NOT match numeric suffix of source keys
    assert rec1.source_key == "MAHOUT-1465"
    assert rec1.destination_key == "ORBITLAB-1"
    assert rec1.destination_key != "ORBITLAB-1465"

    assert rec2.source_key == "MAHOUT-979"
    assert rec2.destination_key == "ORBITLAB-2"
    assert rec2.destination_key != "ORBITLAB-979"

    # Idempotent lookup
    assert registry.get_by_source_key("MAHOUT-1465") == rec1
    assert registry.get_by_destination_key("ORBITLAB-1") == rec1


def test_identity_mapping_idempotency_and_conflict_detection(tmp_path: Path) -> None:
    registry = SourceDestinationRegistry(mapping_path=tmp_path / "mapping.json")

    jira_resp = {"id": "10045", "key": "ORBITLAB-1"}
    rec1 = registry.register_creation("MAHOUT-101", "101", jira_resp, "To Do", "2026-09-24T12:00:00Z")

    # Re-registering exact same issue returns existing record idempotently
    rec2 = registry.register_creation("MAHOUT-101", "101", jira_resp, "To Do", "2026-09-24T12:00:00Z")
    assert rec1 == rec2

    # Attempting to map same source key to a different destination key raises ValueError
    conflicting_resp = {"id": "99999", "key": "ORBITLAB-999"}
    with pytest.raises(ValueError, match="Conflict for source_key"):
        registry.register_creation("MAHOUT-101", "101", conflicting_resp, "To Do", "2026-09-24T12:00:00Z")


def test_identity_mapping_persistence_roundtrip(tmp_path: Path) -> None:
    mapping_file = tmp_path / "mapping.json"
    reg1 = SourceDestinationRegistry(mapping_path=mapping_file)

    reg1.register_creation("MAHOUT-1", "1", {"id": "100", "key": "ORBITLAB-10"}, "To Do", "2026-09-24T12:00:00Z")
    reg1.register_creation("MAHOUT-2", "2", {"id": "101", "key": "ORBITLAB-11"}, "To Do", "2026-09-24T12:01:00Z")

    digest = reg1.save()
    assert mapping_file.exists()
    assert digest

    reg2 = SourceDestinationRegistry(mapping_path=mapping_file)
    reg2.load()

    assert reg2.count() == 2
    assert reg2.get_by_source_key("MAHOUT-1").destination_key == "ORBITLAB-10"
    assert reg2.get_by_source_key("MAHOUT-2").destination_key == "ORBITLAB-11"
