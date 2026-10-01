"""Qualification Tests for ORBITLAB Vocabulary Compatibility & Readiness Gate.

Tests:
1. Live probe records authentic Atlassian transport telemetry.
2. Complete vocabulary evaluation over all 16 Mahout issue types.
3. Complete vocabulary evaluation over all 5 Mahout priorities.
4. Complete vocabulary evaluation over all 6 Mahout statuses.
5. Complete evaluation over all 15 Mahout transition pairs.
6. Required fields and constraints inspection.
7. Readiness Gate decision logic (READY, BLOCKED, BLOCKED_REQUIRES_CONFIGURATION_REVIEW).
8. Strict absence of credential leakage in saved artifacts.
9. Zero mutations asserted during inspection.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from qualification.mahout.compatibility import (
    CompatibilityClassification,
    CompatibilityMatrix,
    ImportReadinessGate,
    MAHOUT_SOURCE_PRIORITIES,
    MAHOUT_SOURCE_STATUSES,
    MAHOUT_SOURCE_TRANSITIONS,
    MAHOUT_SOURCE_TYPES,
    evaluate_compatibility,
    generate_compatibility_markdown_report,
    write_compatibility_reports,
)
from qualification.mahout.inspect_orbitlab import execute_orbitlab_inspection
from qualification.policy import compute_sha256_file


def test_orbitlab_live_probe_telemetry(tmp_path: Path) -> None:
    """Live unauthenticated probe records genuine Atlassian Edge network telemetry."""
    ev_path = tmp_path / "evidence.json"
    json_path = tmp_path / "compat.json"
    md_path = tmp_path / "compat.md"

    res = execute_orbitlab_inspection(
        base_url="https://tecblic.atlassian.net",
        evidence_path=ev_path,
        compatibility_json_path=json_path,
        compatibility_md_path=md_path,
    )

    assert ev_path.exists()
    assert json_path.exists()
    assert md_path.exists()

    with ev_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["project_key"] == "ORBITLAB"
    assert data["zero_mutations_asserted"] is True
    assert data["readiness_gate"] == "BLOCKED"
    assert len(data["telemetry_records"]) >= 1

    tx = data["telemetry_records"][0]
    assert tx["status"] in (401, 403, 404)
    th = tx["transport_headers"]
    assert th["server"]
    assert th["atl_trace_id"]
    assert th["x_a_request_id"]


def test_no_credential_persistence_in_artifacts(tmp_path: Path) -> None:
    """Verifies that sensitive credentials, tokens, and authorization headers are never persisted."""
    ev_path = tmp_path / "evidence.json"
    json_path = tmp_path / "compat.json"
    md_path = tmp_path / "compat.md"

    execute_orbitlab_inspection(
        base_url="https://tecblic.atlassian.net",
        evidence_path=ev_path,
        compatibility_json_path=json_path,
        compatibility_md_path=md_path,
    )

    for path in (ev_path, json_path, md_path):
        content = path.read_text(encoding="utf-8").lower()
        for forbidden in ("bearer ", "basic ", "password", "atlassian_token", "api_token\":"):
            assert forbidden not in content, f"Forbidden credential pattern {forbidden!r} found in {path}"


def test_complete_vocabulary_matrix_evaluation() -> None:
    """Tests evaluation against sample Jira Cloud createmeta, statuses, and priorities."""
    # Synthetic project metadata representing a standard Jira Cloud team-managed project
    project_meta = {
        "key": "ORBITLAB",
        "id": "10020",
        "name": "Shadow ORBIT Qualification Lab",
        "projectTypeKey": "software",
        "simplified": True,
        "style": "next-gen",
        "self": "https://tecblic.atlassian.net/rest/api/3/project/10020",
    }

    # Default next-gen createmeta (typically only Task, Bug)
    createmeta = {
        "projects": [
            {
                "key": "ORBITLAB",
                "issuetypes": [
                    {
                        "name": "Task",
                        "fields": {
                            "summary": {"name": "Summary", "required": True, "schema": {"type": "string"}},
                            "description": {"name": "Description", "required": False, "schema": {"type": "string"}},
                            "duedate": {"name": "Due date", "required": False, "schema": {"type": "date"}},
                        },
                    },
                    {
                        "name": "Bug",
                        "fields": {
                            "summary": {"name": "Summary", "required": True, "schema": {"type": "string"}},
                        },
                    },
                ],
            }
        ]
    }

    # Default statuses in next-gen project
    statuses_meta = [
        {
            "statuses": [
                {"name": "To Do", "id": "1"},
                {"name": "In Progress", "id": "2"},
                {"name": "Done", "id": "3"},
            ]
        }
    ]

    # Standard Jira Cloud priorities
    priorities_meta = [
        {"name": "Highest", "id": "1"},
        {"name": "High", "id": "2"},
        {"name": "Medium", "id": "3"},
        {"name": "Low", "id": "4"},
        {"name": "Lowest", "id": "5"},
    ]

    matrix = evaluate_compatibility(
        project_meta=project_meta,
        createmeta=createmeta,
        statuses_meta=statuses_meta,
        priorities_meta=priorities_meta,
    )

    # 1. Issue Types: 16 evaluated
    assert len(matrix.issue_types) == 16
    types_by_name = {it.source_value: it for it in matrix.issue_types}
    assert types_by_name["Task"].classification == CompatibilityClassification.EXACT
    assert types_by_name["Bug"].classification == CompatibilityClassification.EXACT
    assert types_by_name["Documentation"].classification == CompatibilityClassification.UNAVAILABLE
    assert types_by_name["Question"].classification == CompatibilityClassification.UNAVAILABLE
    assert types_by_name["Wish"].classification == CompatibilityClassification.UNAVAILABLE
    assert types_by_name["Planned Work"].classification == CompatibilityClassification.UNAVAILABLE

    # 2. Priorities: 5 evaluated
    assert len(matrix.priorities) == 5
    prios_by_name = {p.source_value: p for p in matrix.priorities}
    # Blocker maps approximately to Highest
    assert prios_by_name["Blocker"].classification == CompatibilityClassification.APPROXIMATE_SEMANTIC_MAPPING
    assert prios_by_name["Blocker"].destination_value == "Highest"

    # 3. Statuses: 6 evaluated
    assert len(matrix.statuses) == 6
    st_by_name = {s.source_value: s for s in matrix.statuses}
    assert st_by_name["In Progress"].classification == CompatibilityClassification.EXACT
    assert st_by_name["Open"].classification == CompatibilityClassification.REPRESENTABLE_BY_DESTINATION_STATE
    assert st_by_name["Open"].destination_value == "To Do"
    # Patch Available has no counterpart in default next-gen
    assert st_by_name["Patch Available"].classification == CompatibilityClassification.UNAVAILABLE
    assert st_by_name["Reopened"].classification == CompatibilityClassification.UNAVAILABLE

    # 4. Transitions: 15 evaluated
    assert len(matrix.transitions) == 15
    trans_by_name = {f"{t.source_from}->{t.source_to}": t for t in matrix.transitions}
    # Resolved -> Closed: both map to Done -> CONTRACT_NOT_REPRESENTABLE (collapses into self-loop)
    assert trans_by_name["Resolved->Closed"].classification == CompatibilityClassification.CONTRACT_NOT_REPRESENTABLE
    # Patch Available -> Resolved: Patch Available is unavailable -> UNAVAILABLE
    assert trans_by_name["Patch Available->Resolved"].classification == CompatibilityClassification.UNAVAILABLE

    # 5. Readiness Gate: Since types and statuses are unavailable, must flag configuration review
    assert matrix.readiness_gate == ImportReadinessGate.BLOCKED_REQUIRES_CONFIGURATION_REVIEW
    assert len(matrix.readiness_reasons) > 0


def test_import_readiness_gate_ready_when_all_exact() -> None:
    """When a customized Jira project supports all 16 types, 5 priorities, and 6 statuses, gate is READY."""
    project_meta = {"key": "ORBITLAB", "id": "10020", "name": "Shadow ORBIT Qualification Lab"}

    # Project configured with all 16 issue types
    createmeta = {
        "projects": [
            {
                "key": "ORBITLAB",
                "issuetypes": [
                    {
                        "name": t_name,
                        "fields": {
                            "summary": {"name": "Summary", "required": True, "schema": {"type": "string"}},
                            "duedate": {"name": "Due date", "required": False, "schema": {"type": "date"}},
                        },
                    }
                    for t_name in MAHOUT_SOURCE_TYPES
                ],
            }
        ]
    }

    # Project configured with all 6 statuses
    statuses_meta = [
        {
            "statuses": [
                {"name": s_name, "id": str(idx + 1)}
                for idx, s_name in enumerate(MAHOUT_SOURCE_STATUSES)
            ]
        }
    ]

    # Jira configured with exact priorities
    priorities_meta = [
        {"name": p_name, "id": str(idx + 1)}
        for idx, p_name in enumerate(MAHOUT_SOURCE_PRIORITIES)
    ]

    matrix = evaluate_compatibility(
        project_meta=project_meta,
        createmeta=createmeta,
        statuses_meta=statuses_meta,
        priorities_meta=priorities_meta,
    )

    assert matrix.readiness_gate == ImportReadinessGate.READY
    assert len(matrix.readiness_reasons) == 0


def test_write_compatibility_reports(tmp_path: Path) -> None:
    """Verifies that compatibility reports serialize and hash properly."""
    matrix = CompatibilityMatrix(
        project_identity={"key": "ORBITLAB"},
        issue_types=(),
        priorities=(),
        statuses=(),
        transitions=(),
        fields=(),
        readiness_gate=ImportReadinessGate.BLOCKED,
        readiness_reasons=("Awaiting authenticated inspection",),
    )

    j_path = tmp_path / "compat.json"
    m_path = tmp_path / "compat.md"

    res = write_compatibility_reports(matrix, json_path=j_path, md_path=m_path)

    assert j_path.exists()
    assert m_path.exists()
    assert compute_sha256_file(j_path) == res["json_sha256"]
    assert compute_sha256_file(m_path) == res["md_sha256"]


def test_orbitlab_live_metadata_evaluation_blocks_on_missing_vocabulary() -> None:
    """Verifies that live ORBITLAB project configuration correctly triggers BLOCKED_REQUIRES_CONFIGURATION_REVIEW."""
    live_project_meta = {
        "key": "ORBITLAB",
        "id": "10001",
        "name": "Shadow ORBIT Qualification Lab",
        "projectTypeKey": "software",
        "simplified": True,
        "style": "next-gen",
        "self": "https://rutujpateltecblic.atlassian.net/rest/api/3/project/10001",
    }

    live_createmeta = {
        "projects": [
            {
                "key": "ORBITLAB",
                "issuetypes": [
                    {
                        "name": "Task",
                        "fields": {
                            "summary": {"name": "Summary", "required": True, "schema": {"type": "string"}},
                            "description": {"name": "Description", "required": False, "schema": {"type": "string"}},
                            "duedate": {"name": "Due date", "required": False, "schema": {"type": "date"}},
                            "reporter": {"name": "Reporter", "required": True, "schema": {"type": "user"}},
                        },
                    },
                    {"name": "Epic", "fields": {"summary": {"name": "Summary", "required": True, "schema": {"type": "string"}}}},
                    {"name": "Subtask", "fields": {"summary": {"name": "Summary", "required": True, "schema": {"type": "string"}}}},
                    {"name": "Story", "fields": {"summary": {"name": "Summary", "required": True, "schema": {"type": "string"}}}},
                ],
            }
        ]
    }

    live_statuses = [
        {
            "statuses": [
                {"name": "To Do", "id": "10004"},
                {"name": "In Progress", "id": "10005"},
                {"name": "In Review", "id": "10006"},
                {"name": "Blocked", "id": "10007"},
                {"name": "Done", "id": "10008"},
            ]
        }
    ]

    live_priorities = [
        {"name": "Highest", "id": "1"},
        {"name": "High", "id": "2"},
        {"name": "Medium", "id": "3"},
        {"name": "Low", "id": "4"},
        {"name": "Lowest", "id": "5"},
    ]

    matrix = evaluate_compatibility(
        project_meta=live_project_meta,
        createmeta=live_createmeta,
        statuses_meta=live_statuses,
        priorities_meta=live_priorities,
    )

    assert matrix.readiness_gate == ImportReadinessGate.BLOCKED_REQUIRES_CONFIGURATION_REVIEW
    # 4 exact types (Task, Epic, Sub-task, Story), 12 unavailable types (Bug, Improvement, etc.)
    types_by_name = {it.source_value: it for it in matrix.issue_types}
    assert types_by_name["Bug"].classification == CompatibilityClassification.UNAVAILABLE
    assert types_by_name["Task"].classification == CompatibilityClassification.EXACT
    assert types_by_name["Sub-task"].classification == CompatibilityClassification.EXACT
    assert types_by_name["Epic"].classification == CompatibilityClassification.EXACT
    assert types_by_name["Story"].classification == CompatibilityClassification.EXACT

    assert matrix.issue_type_accounting["exact"] == 4
    assert matrix.issue_type_accounting["unavailable"] == 12
    assert matrix.issue_type_accounting["total"] == 16

    # Status accounting
    assert matrix.status_accounting["exact"] == 1
    assert matrix.status_accounting["representable_by_destination_state"] == 3
    assert matrix.status_accounting["unavailable"] == 2
    assert matrix.status_accounting["total"] == 6

    # Transition accounting: 0 exact + 5 representable + 1 collapse + 9 unavailable = 15 total
    assert matrix.transition_accounting["exact"] == 0
    assert matrix.transition_accounting["representable_by_destination_state"] == 5
    assert matrix.transition_accounting["contract_not_representable"] == 1
    assert matrix.transition_accounting["unavailable"] == 9
    assert matrix.transition_accounting["ambiguous"] == 0
    assert matrix.transition_accounting["total"] == 15

    # Reporter required field detected
    reasons_text = " ".join(matrix.readiness_reasons)
    assert "Reporter" in reasons_text
    assert "12 Mahout issue types unavailable" in reasons_text

