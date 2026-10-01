"""Qualification Tests for Deterministic Bounded Mahout Seed Selection.

Tests:
1. Exact target size (400 issues).
2. Determinism across repeated executions (identical keys, order, and selection hash).
3. 100% coverage of all 6 observed statuses.
4. 100% coverage of all 15 observed transition pairs.
5. 100% coverage of all 5 observed priorities.
6. 100% coverage of all 16 observed issue types.
7. Due date coverage (both present and absent).
8. History depth distribution (zero-change baseline, single-change, multi-change, deep history).
9. Non-empty, auditable selection reasons on all selected issues.
10. Offline behavior with hermetic synthetic test records.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from qualification.mahout.selector import (
    DEFAULT_TARGET_SEED_SIZE,
    MahoutIssueSummary,
    MahoutSeedResult,
    load_mahout_issues_from_mongo,
    parse_mahout_raw_issue,
    select_mahout_seed,
)


@pytest.fixture(scope="module")
def mahout_source_docs() -> list[dict[str, Any]]:
    """Fixture providing raw Mahout issues from MongoDB or failing gracefully if offline."""
    try:
        docs = load_mahout_issues_from_mongo()
        if not docs:
            pytest.skip("No Mahout issues found in MongoDB JiraReposAnon.Apache")
        return docs
    except Exception as exc:
        pytest.skip(f"MongoDB not available for live Mahout tests: {exc}")


def test_mahout_selector_exact_count_and_determinism(mahout_source_docs: list[dict[str, Any]]) -> None:
    """Selection must return exactly 400 issues and be bit-for-bit deterministic."""
    res1 = select_mahout_seed(mahout_source_docs, target_size=DEFAULT_TARGET_SEED_SIZE)
    res2 = select_mahout_seed(mahout_source_docs, target_size=DEFAULT_TARGET_SEED_SIZE)

    assert res1.selected_count == 400
    assert len(res1.selected_keys) == 400
    assert len(res1.selected_issues) == 400
    assert res1.source_total_considered == len(mahout_source_docs)

    # Determinism
    assert res1.selection_hash == res2.selection_hash
    assert res1.selected_keys == res2.selected_keys
    for i1, i2 in zip(res1.selected_issues, res2.selected_issues):
        assert i1.key == i2.key
        assert i1.source_id == i2.source_id
        assert i1.selection_reason == i2.selection_reason


def test_mahout_selector_status_coverage(mahout_source_docs: list[dict[str, Any]]) -> None:
    """Must achieve 100% coverage of all 6 observed Mahout statuses."""
    result = select_mahout_seed(mahout_source_docs, target_size=400)
    expected_statuses = {"Closed", "Resolved", "Open", "Reopened", "In Progress", "Patch Available"}

    observed_statuses = {issue.status for issue in result.selected_issues}
    assert observed_statuses == expected_statuses

    status_counts = result.coverage_summary["status_coverage"]["counts"]
    # Rare statuses must all be fully represented
    assert status_counts["Patch Available"] == 3
    assert status_counts["Reopened"] == 4
    assert status_counts["In Progress"] == 9


def test_mahout_selector_transition_pair_coverage(mahout_source_docs: list[dict[str, Any]]) -> None:
    """Must achieve 100% coverage of all 15 observed Mahout status-transition pairs."""
    result = select_mahout_seed(mahout_source_docs, target_size=400)
    expected_pairs = {
        ("Resolved", "Closed"),
        ("Open", "Resolved"),
        ("Open", "Patch Available"),
        ("Patch Available", "Resolved"),
        ("Open", "In Progress"),
        ("In Progress", "Resolved"),
        ("Resolved", "Reopened"),
        ("Reopened", "Resolved"),
        ("Patch Available", "Open"),
        ("In Progress", "Patch Available"),
        ("Reopened", "Patch Available"),
        ("In Progress", "Open"),
        ("Open", "Closed"),
        ("Patch Available", "In Progress"),
        ("Reopened", "In Progress"),
    }

    observed_pairs = set()
    for issue in result.selected_issues:
        observed_pairs.update(issue.transition_set)

    assert observed_pairs == expected_pairs

    # Verify rare transition counts in coverage summary
    pairs_summary = result.coverage_summary["transition_coverage"]["pairs"]
    assert pairs_summary["Reopened->In Progress"] == 2
    assert pairs_summary["Patch Available->In Progress"] == 5
    assert pairs_summary["Open->Closed"] == 12
    assert pairs_summary["In Progress->Open"] == 14
    assert pairs_summary["Reopened->Patch Available"] == 18


def test_mahout_selector_priority_coverage(mahout_source_docs: list[dict[str, Any]]) -> None:
    """Must achieve 100% coverage of all 5 observed priorities with >= 30 quota."""
    result = select_mahout_seed(mahout_source_docs, target_size=400)
    expected_priorities = {"Major", "Minor", "Critical", "Trivial", "Blocker"}

    observed_priorities = {issue.priority for issue in result.selected_issues}
    assert observed_priorities == expected_priorities

    counts = result.coverage_summary["priority_coverage"]["counts"]
    for p in expected_priorities:
        assert counts[p] >= 30, f"Priority {p} has fewer than 30 occurrences: {counts[p]}"


def test_mahout_selector_issue_type_coverage(mahout_source_docs: list[dict[str, Any]]) -> None:
    """Must achieve 100% coverage of all 16 observed Mahout issue types."""
    result = select_mahout_seed(mahout_source_docs, target_size=400)
    expected_types = {
        "Bug",
        "Improvement",
        "New Feature",
        "Task",
        "Documentation",
        "Question",
        "Sub-task",
        "Wish",
        "Test",
        "Epic",
        "Dependency upgrade",
        "Blog - New Blog Request",
        "New JIRA Project",
        "Story",
        "Planned Work",
        "Proposal",
    }

    observed_types = {issue.issuetype for issue in result.selected_issues}
    assert observed_types == expected_types

    counts = result.coverage_summary["issue_type_coverage"]["counts"]
    # Rare/singleton types must be preserved
    assert counts["Planned Work"] == 1
    assert counts["Proposal"] == 1
    assert counts["Story"] == 2
    assert counts["New JIRA Project"] == 2
    assert counts["Blog - New Blog Request"] == 3


def test_mahout_selector_due_date_and_history_depth(mahout_source_docs: list[dict[str, Any]]) -> None:
    """Must cover issues with and without due dates, plus full spectrum of history depth."""
    result = select_mahout_seed(mahout_source_docs, target_size=400)

    # Due dates
    with_dd = sum(1 for it in result.selected_issues if it.has_duedate)
    without_dd = sum(1 for it in result.selected_issues if not it.has_duedate)
    assert with_dd >= 30
    assert without_dd >= 300

    # History depths
    depth_dist = result.coverage_summary["history_depth_distribution"]
    assert depth_dist["0_transitions"] >= 20
    assert depth_dist["1_transition"] >= 25
    assert depth_dist["2_to_5_transitions"] >= 100
    assert depth_dist["6_to_10_transitions"] >= 15


def test_mahout_selector_auditable_selection_reasons(mahout_source_docs: list[dict[str, Any]]) -> None:
    """Every selected issue must have a valid non-empty selection reason."""
    result = select_mahout_seed(mahout_source_docs, target_size=400)

    for issue in result.selected_issues:
        assert issue.selection_reason, f"Issue {issue.key} has empty selection reason"
        assert isinstance(issue.selection_reason, str)


def test_mahout_selector_offline_synthetic_records() -> None:
    """Selector works deterministically on synthetic records without database."""
    synthetic_docs = []
    statuses = ["Open", "In Progress", "Resolved", "Closed"]
    for i in range(1, 21):
        st = statuses[i % len(statuses)]
        synthetic_docs.append({
            "key": f"MAHOUT-{i}",
            "id": f"100{i}",
            "fields": {
                "status": {"name": st},
                "priority": {"name": "Major"},
                "issuetype": {"name": "Bug"},
                "duedate": "2026-10-01" if i % 2 == 0 else None,
            },
            "changelog": {
                "histories": [
                    {
                        "items": [
                            {"field": "status", "fromString": "Open", "toString": st}
                        ]
                    }
                ] if st != "Open" else []
            },
        })

    res = select_mahout_seed(synthetic_docs, target_size=10)
    assert res.selected_count == 10
    assert len(res.selected_keys) == 10
    assert res.target_size == 10
    assert res.source_total_considered == 20
    assert res.selection_hash
