"""Tests for ORBITLAB Preflight Audit & Qualification Invariants.

Verifies:
1. Zero source provenance or qualification metadata injected into descriptions.
2. All selected subtasks have explicitly classified parent relationships (2 in-seed, 29 outside-seed).
3. Due-date support is evaluated strictly by issue type (0 on subtasks; 42 on Improvement/Bug/Task/Doc).
4. Priority mappings remain strictly non-exact (approximate_semantic_mapping).
5. Workflow readiness cannot be certified exact merely from status existence without empirical changelog observation.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from qualification.mahout.compatibility import (
    CompatibilityClassification,
    MAHOUT_SOURCE_PRIORITIES,
    evaluate_compatibility,
)
from qualification.mahout.description_projection import project_source_description_to_adf


SUBTASK_AUDIT_JSON = Path("/home/tecblic/orbit-private/mahout/mahout_subtask_parent_audit.json")
DUE_DATE_AUDIT_JSON = Path("/home/tecblic/orbit-private/mahout/mahout_due_date_audit.json")
CONFIG_JSON = Path("/home/tecblic/orbit-private/mahout/orbitlab_required_configuration.json")


def test_no_source_provenance_injected_into_description() -> None:
    """Verifies that projected descriptions contain pure source text only with zero metadata injection."""
    raw_desc = "Implement streaming k-means clustering in Spark."
    adf = project_source_description_to_adf(raw_desc)

    assert adf is not None
    assert adf["type"] == "doc"
    assert adf["version"] == 1
    content_nodes = adf["content"]
    assert len(content_nodes) == 1
    para = content_nodes[0]
    assert para["type"] == "paragraph"
    text_node = para["content"][0]
    assert text_node["type"] == "text"
    assert text_node["text"] == raw_desc

    # Assert strict absence of injected metadata
    adf_str = json.dumps(adf).lower()
    for forbidden in ("source key:", "provenance", "qualification header", "apache author", "reporter:"):
        assert forbidden not in adf_str, f"Forbidden provenance injection '{forbidden}' found in description ADF"

    # None and empty handling
    assert project_source_description_to_adf(None) is None
    assert project_source_description_to_adf("") is None
    assert project_source_description_to_adf("   ") is None


def test_all_selected_subtasks_have_explicitly_classified_parent_situation() -> None:
    """Verifies that all 31 selected Sub-tasks in the 400 seed have an explicit parent classification."""
    assert SUBTASK_AUDIT_JSON.exists(), f"Audit file {SUBTASK_AUDIT_JSON} must exist"
    data = json.loads(SUBTASK_AUDIT_JSON.read_text(encoding="utf-8"))

    acc = data["accounting"]
    assert acc["total_selected_subtasks"] == 31
    assert acc["parent_in_seed"] == 2
    assert acc["parent_outside_seed"] == 29
    assert acc["parent_missing"] == 0
    assert acc["parent_unrepresentable"] == 0

    assert len(data["records"]) == 31
    for r in data["records"]:
        assert r["classification"] in ("parent_in_seed", "parent_outside_seed", "parent_missing", "parent_unrepresentable")
        if r["classification"] == "parent_in_seed":
            assert r["destination_creation_legally_representable"] is True
            assert r["source_parent_key"] in ("MAHOUT-1371", "MAHOUT-1855")
        else:
            assert r["destination_creation_legally_representable"] is False
            assert "outside the 400 frozen seed" in r["consequence"]


def test_due_date_support_computed_by_selected_issue_type() -> None:
    """Verifies that due dates in the seed are audited by type and subtask due-date limitations cause zero loss."""
    assert DUE_DATE_AUDIT_JSON.exists(), f"Audit file {DUE_DATE_AUDIT_JSON} must exist"
    data = json.loads(DUE_DATE_AUDIT_JSON.read_text(encoding="utf-8"))

    assert data["total_selected_issues"] == 400
    assert data["total_with_duedate"] == 42
    assert data["subtasks_with_duedate"] == 0
    assert data["epics_with_duedate"] == 0
    assert data["stories_with_duedate"] == 0
    assert data["tasks_with_duedate"] == 3

    by_type = data["issues_with_duedate_by_type"]
    assert by_type["Improvement"] == 25
    assert by_type["Bug"] == 13
    assert by_type["Task"] == 3
    assert by_type["Documentation"] == 1

    # In team-managed projects, subtask schema lacks duedate; if a subtask had a due date it would be unrepresentable
    assert data["subtask_duedate_classification"] == "exact_zero_loss"


def test_approximate_priority_mappings_remain_non_exact() -> None:
    """Verifies that priority mappings are strictly classified as APPROXIMATE_SEMANTIC_MAPPING, never EXACT."""
    project_meta = {"key": "ORBITLAB", "id": "10001", "name": "Lab", "projectTypeKey": "software", "style": "next-gen"}
    createmeta = {"projects": [{"key": "ORBITLAB", "issuetypes": [{"name": "Task", "fields": {}}]}]}
    statuses_meta = [{"statuses": [{"name": "In Progress"}]}]
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

    for p in matrix.priorities:
        assert p.classification == CompatibilityClassification.APPROXIMATE_SEMANTIC_MAPPING
        assert p.classification != CompatibilityClassification.EXACT
        assert p.requires_review is True


def test_workflow_readiness_cannot_be_marked_exact_from_status_existence_alone() -> None:
    """Verifies that workflow transition readiness is governed by empirical verification requirements."""
    assert CONFIG_JSON.exists(), f"Configuration file {CONFIG_JSON} must exist"
    cfg = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))

    proto = cfg["empirical_workflow_verification_protocol"]
    assert proto["mandate"] == "Transition readiness cannot be marked exact from status existence alone."
    assert len(proto["test_procedure"]) >= 5
    assert any("changelog" in step.lower() for step in proto["test_procedure"])
    assert proto["zero_mutation_asserted_preflight"] is True
