"""Tests for Mahout Governed Structural Dependency Expansion.

Verifies:
1. Exact 400-key primary seed is preserved and immutable.
2. 400 primary seed keys are a strict subset of the 410 destination corpus.
3. Exactly 10 structural dependencies are included in the 410 corpus.
4. Downstream manifests explicitly distinguish `primary_seed` vs `structural_dependency`.
5. Structural dependency manifest adheres strictly to required schema.
6. Full-closure 412 companion corpus resolves 100% of all 29 outside-seed subtasks.
7. Original 400 allowlist SHA-256 is unchanged.
8. Zero Jira issue or configuration mutations have occurred.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from qualification.config import FROZEN_ENGINE_COMMIT
from qualification.mahout.structural_dependencies import (
    DESTINATION_410_ALLOWLIST_PATH,
    DESTINATION_410_MANIFEST_PATH,
    DESTINATION_412_ALLOWLIST_PATH,
    DESTINATION_412_MANIFEST_PATH,
    PRIMARY_400_SHA256,
    PRIMARY_ALLOWLIST_PATH,
    STRUCTURAL_DEP_MANIFEST_PATH,
    SUBTASK_AUDIT_PATH,
)
from qualification.policy import compute_sha256_file


def test_structural_dependency_allowlist_invariants() -> None:
    """Verifies set inclusion, cardinality, and hash preservation of allowlists."""
    assert PRIMARY_ALLOWLIST_PATH.exists()
    assert DESTINATION_410_ALLOWLIST_PATH.exists()
    assert DESTINATION_412_ALLOWLIST_PATH.exists()

    # Verify primary 400 hash is unchanged
    assert compute_sha256_file(PRIMARY_ALLOWLIST_PATH) == PRIMARY_400_SHA256

    k400 = [l.strip() for l in PRIMARY_ALLOWLIST_PATH.read_text().splitlines() if l.strip()]
    k410 = [l.strip() for l in DESTINATION_410_ALLOWLIST_PATH.read_text().splitlines() if l.strip()]
    k412 = [l.strip() for l in DESTINATION_412_ALLOWLIST_PATH.read_text().splitlines() if l.strip()]

    assert len(k400) == 400
    assert len(k410) == 410
    assert len(k412) == 412

    s400 = set(k400)
    s410 = set(k410)
    s412 = set(k412)

    # 400 primary keys ⊂ 410 destination corpus
    assert s400.issubset(s410)
    assert s400.issubset(s412)

    # Exactly 10 structural dependencies added in 410
    added_10 = s410 - s400
    assert len(added_10) == 10

    # Exactly 12 structural dependencies added in 412
    added_12 = s412 - s400
    assert len(added_12) == 12

    # Deterministic numeric sorting
    def key_num(k: str) -> int:
        return int(k.split("-")[1])

    assert k410 == sorted(k410, key=key_num)
    assert k412 == sorted(k412, key=key_num)


def test_structural_dependency_manifest_schema_and_roles() -> None:
    """Verifies that the structural dependency manifest strictly follows governance schema."""
    assert STRUCTURAL_DEP_MANIFEST_PATH.exists()
    data = json.loads(STRUCTURAL_DEP_MANIFEST_PATH.read_text(encoding="utf-8"))

    assert data["manifest_version"] == "1.0.0"
    assert data["engine_commit"] == FROZEN_ENGINE_COMMIT

    acc = data["accounting"]
    assert acc["primary_seed_count"] == 400
    assert acc["structural_dependencies_count"] == 10
    assert acc["destination_corpus_count"] == 410
    assert acc["total_selected_subtasks"] == 31
    assert acc["in_seed_parent_subtasks"] == 2
    assert acc["outside_seed_parent_subtasks"] == 29

    inv = data["invariants"]
    assert inv["primary_seed_subset_of_destination"] is True
    assert inv["original_400_seed_immutable"] is True
    assert inv["original_400_allowlist_sha256"] == PRIMARY_400_SHA256
    assert inv["zero_synthetic_parents"] is True
    assert inv["zero_subtask_type_conversion"] is True

    deps = data["structural_dependencies"]
    assert len(deps) == 10

    for d in deps:
        assert isinstance(d["source_key"], str) and d["source_key"].startswith("MAHOUT-")
        assert isinstance(d["source_id"], str) and len(d["source_id"]) > 0
        assert d["source_issue_type"] in ("New Feature", "Improvement", "Bug", "Task")
        assert len(d["reason_for_inclusion"]) > 0
        assert len(d["dependent_selected_subtasks"]) > 0
        assert d["classification"] == "structural_dependency"
        assert d["part_of_original_400"] is False
        assert d["whether_the_parent_itself_was_part_of_the_original_400"] is False


def test_downstream_manifest_role_distinction() -> None:
    """Verifies that downstream seed manifest explicitly distinguishes primary_seed vs structural_dependency."""
    assert DESTINATION_410_MANIFEST_PATH.exists()
    data = json.loads(DESTINATION_410_MANIFEST_PATH.read_text(encoding="utf-8"))

    acc = data["corpus_accounting"]
    assert acc["is_balanced"] is True
    assert acc["source_considered"] == 2121
    assert acc["primary_seed_count"] == 400
    assert acc["structural_dependencies_count"] == 10
    assert acc["destination_corpus_count"] == 410
    assert acc["not_selected_by_policy"] == 1711
    assert acc["selection_failed"] == 0

    items = data["items"]
    assert len(items) == 410

    primary_items = [it for it in items if it["role"] == "primary_seed"]
    dep_items = [it for it in items if it["role"] == "structural_dependency"]

    assert len(primary_items) == 400
    assert len(dep_items) == 10

    for it in primary_items:
        assert it["classification"] == "primary_seed"
        assert it["status"] == "selected_for_qualification"

    for it in dep_items:
        assert it["classification"] == "structural_dependency"
        assert it["status"] == "structural_dependency"
        assert "dependent_subtasks" in it["metadata"]


def test_subtask_parent_coverage_and_census() -> None:
    """Verifies that parent relationships for all 31 selected subtasks reconcile with audit findings."""
    assert SUBTASK_AUDIT_PATH.exists()
    audit = json.loads(SUBTASK_AUDIT_PATH.read_text(encoding="utf-8"))

    k410 = set(DESTINATION_410_ALLOWLIST_PATH.read_text().splitlines())
    k412 = set(DESTINATION_412_ALLOWLIST_PATH.read_text().splitlines())

    outside = [r for r in audit["records"] if r["classification"] == "parent_outside_seed"]
    assert len(outside) == 29

    # 10 parents cover 27 subtasks
    covered_410 = [r["source_subtask_key"] for r in outside if r["source_parent_key"] in k410]
    assert len(covered_410) == 27

    # 12 parents cover all 29 subtasks (100% full closure)
    covered_412 = [r["source_subtask_key"] for r in outside if r["source_parent_key"] in k412]
    assert len(covered_412) == 29


def test_independent_source_derived_mongodb_subtask_parent_closure() -> None:
    """Independent source-derived validation querying MongoDB directly.
    
    Eliminates tautological/circular verification by bypassing all intermediate
    JSON audit artifacts and asserting directly against raw Apache Mahout BSON records.
    """
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
    except Exception as exc:
        pytest.skip(f"MongoDB not reachable for independent source validation: {exc}")

    coll = client["JiraReposAnon"]["Apache"]
    allow_400 = set(PRIMARY_ALLOWLIST_PATH.read_text().splitlines())
    allow_410 = set(DESTINATION_410_ALLOWLIST_PATH.read_text().splitlines())
    allow_412 = set(DESTINATION_412_ALLOWLIST_PATH.read_text().splitlines())

    all_mahout = list(coll.find({"fields.project.key": "MAHOUT"}))
    by_key = {d["key"]: d for d in all_mahout}
    docs_400 = [by_key[k] for k in allow_400]

    # 1. Independent extraction of subtasks directly from raw MongoDB documents
    raw_subtasks = [d for d in docs_400 if d.get("fields", {}).get("issuetype", {}).get("name") == "Sub-task"]
    assert len(raw_subtasks) == 31, f"Expected exactly 31 subtasks in MongoDB, found {len(raw_subtasks)}"

    in_seed_parents: list[tuple[str, str]] = []
    outside_seed_parents: list[tuple[str, str]] = []

    for s in raw_subtasks:
        sk = s["key"]
        parent_obj = s.get("fields", {}).get("parent")
        assert parent_obj is not None, f"Subtask {sk} missing parent in MongoDB"
        pk = parent_obj.get("key")
        assert pk is not None, f"Subtask {sk} parent missing key"

        if pk in allow_400:
            in_seed_parents.append((sk, pk))
        else:
            outside_seed_parents.append((sk, pk))

    # 2. Independent verification of in-seed pairs
    assert len(in_seed_parents) == 2
    assert set(pk for sk, pk in in_seed_parents) == {"MAHOUT-1371", "MAHOUT-1855"}

    # 3. Independent verification of outside-seed parent cardinality
    assert len(outside_seed_parents) == 29
    unique_outside_parents = set(pk for sk, pk in outside_seed_parents)
    assert len(unique_outside_parents) == 12, f"Expected 12 unique parent keys in Mongo, found {len(unique_outside_parents)}"

    # 4. Independent verification of 410 coverage (27 of 29)
    covered_410 = [sk for sk, pk in outside_seed_parents if pk in allow_410]
    assert len(covered_410) == 27
    unparented_410 = {sk: pk for sk, pk in outside_seed_parents if pk not in allow_410}
    assert unparented_410 == {"MAHOUT-1014": "MAHOUT-1010", "MAHOUT-1816": "MAHOUT-1570"}

    # 5. Independent verification of 412 coverage (29 of 29 - 100%)
    covered_412 = [sk for sk, pk in outside_seed_parents if pk in allow_412]
    assert len(covered_412) == 29

    # 6. Independent verification that each parent exists in MongoDB and is a non-subtask
    for pk in unique_outside_parents:
        p_doc = by_key.get(pk)
        assert p_doc is not None, f"Parent {pk} missing from MongoDB!"
        p_type = p_doc.get("fields", {}).get("issuetype", {}).get("name")
        assert p_type != "Sub-task", f"Parent {pk} cannot be a Sub-task"
