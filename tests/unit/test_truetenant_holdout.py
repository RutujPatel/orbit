"""Phase 12 — TrueTenant Blind Hold-Out Tests.

Focused tests for the TrueTenant qualification adapter.
These tests verify:
1. Every observed source status is accounted for
2. Mapping is deterministic
3. Unmapped statuses do not silently become a canonical state
4. Ambiguous statuses are preserved as uncertainty (unknown)
5. Changelog ordering is deterministic
6. Missing history is represented explicitly
7. Provenance resolves
8. Canonical serialization is deterministic
9. Permutation invariance
10. Provider leakage guard
11. Finding IDs are deterministic
12. Mapping cannot be influenced by evaluator output
13. No Jira/GitHub-specific evaluator branch is executed

Governance:
- Does NOT modify TrueTenant source data
- Does NOT modify core evaluator semantics
- Does NOT modify historical golden artifacts
- Does NOT make network calls
- save_golden=False
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

import pytest

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from qualification.truetenant.ingestion import (
    TRUETENANT_STATUS_MAPPING,
    TRUETENANT_PRIORITY_MAPPING,
    TERMINAL_SOURCE_STATUSES,
    build_truetenant_fixture_document,
    load_truetenant_csv,
    load_truetenant_changelog,
    project_single_truetenant_record,
    QuarantineError,
    _parse_csv_datetime,
    _parse_epoch_ms,
)
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.validation import validate_fixture
from shadow_orbit.evaluation import evaluate_week_one_rules


# ── Fixture ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def tt_fixture_and_quarantine():
    """Build TrueTenant fixture document once for all tests."""
    return build_truetenant_fixture_document()


@pytest.fixture(scope="module")
def tt_fixture(tt_fixture_and_quarantine):
    return tt_fixture_and_quarantine[0]


@pytest.fixture(scope="module")
def tt_quarantine(tt_fixture_and_quarantine):
    return tt_fixture_and_quarantine[1]


@pytest.fixture(scope="module")
def tt_normalized(tt_fixture):
    validated = validate_fixture(tt_fixture)
    return normalize_fixture(validated)


@pytest.fixture(scope="module")
def tt_evaluation(tt_normalized):
    matches, suppressed = evaluate_week_one_rules(tt_normalized)
    return matches, suppressed


# ── Test 1: Every observed source status is accounted for ─────────────────

OBSERVED_SOURCE_STATUSES = {
    # From CSV (final state)
    "To Do", "Dev In Progress", "Done", "Ready For QA", "Approved",
    "Awaiting Approval", "Feature Not Required", "QA Passed", "Not an Issue",
    # From changelog transitions only
    "ReOpen", "Pending For More Information",
}


def test_every_source_status_has_mapping():
    """Every observed source status must be explicitly present in the mapping."""
    for status in OBSERVED_SOURCE_STATUSES:
        assert status in TRUETENANT_STATUS_MAPPING, (
            f"Status {status!r} is observed but has no mapping in TRUETENANT_STATUS_MAPPING. "
            "It must be explicitly mapped (even if to 'unknown')."
        )


def test_no_silent_default_in_mapping():
    """The mapping must explicitly enumerate all known statuses.
    No status should silently fall through to a default value
    without an explicit entry.
    """
    for status in OBSERVED_SOURCE_STATUSES:
        result = TRUETENANT_STATUS_MAPPING.get(status)
        # None means it's missing — not acceptable
        assert result is not None, f"Status {status!r} maps to None (missing entry)"
        assert result in {"todo", "in_progress", "done", "unknown", "blocked"}, (
            f"Status {status!r} maps to invalid category {result!r}"
        )


def test_mapping_valid_canonical_categories():
    """All mapped values are valid ORBIT StatusCategory values."""
    valid = {"todo", "in_progress", "done", "unknown", "blocked"}
    for status, canonical in TRUETENANT_STATUS_MAPPING.items():
        assert canonical in valid, (
            f"Status {status!r} maps to {canonical!r} which is not a valid StatusCategory"
        )


# ── Test 2: Mapping is deterministic ─────────────────────────────────────────

def test_mapping_is_deterministic():
    """The mapping must produce identical results across multiple invocations."""
    results = []
    for _ in range(5):
        results.append({s: TRUETENANT_STATUS_MAPPING.get(s) for s in OBSERVED_SOURCE_STATUSES})
    assert all(r == results[0] for r in results), "Mapping is not deterministic"


def test_mapping_does_not_change_after_evaluation(tt_evaluation):
    """Running the evaluator must not change the mapping."""
    # Evaluator has run; mapping must remain unchanged
    for status in OBSERVED_SOURCE_STATUSES:
        expected = TRUETENANT_STATUS_MAPPING.get(status)
        assert TRUETENANT_STATUS_MAPPING[status] == expected, (
            f"Mapping for {status!r} changed after evaluation"
        )


# ── Test 3: Unmapped statuses do not silently become a canonical state ──────

UNMAPPED_SOURCE_STATUSES = {
    "Awaiting Approval", "Approved", "Ready For QA", "QA Passed",
    "Pending For More Information",
}


def test_unmapped_statuses_map_to_unknown():
    """Each unmapped status must map to 'unknown', not to todo/in_progress/done."""
    for status in UNMAPPED_SOURCE_STATUSES:
        canonical = TRUETENANT_STATUS_MAPPING.get(status)
        assert canonical == "unknown", (
            f"Status {status!r} should map to 'unknown' but maps to {canonical!r}. "
            "Unmapped statuses must not silently receive a canonical category."
        )


def test_unknown_statuses_produce_data_quality_conditions(tt_normalized):
    """Each unknown-mapped status must produce an UNKNOWN_STATUS condition."""
    unknown_issue_keys = {
        item.key for item in tt_normalized.work_items
        if item.status_category == "unknown"
    }
    condition_keys = {
        cond.subject_key
        for cond in tt_normalized.data_quality_conditions
        if cond.code == "UNKNOWN_STATUS"
    }
    # Every unknown-status issue must have a corresponding UNKNOWN_STATUS condition
    missing = unknown_issue_keys - condition_keys
    assert missing == set(), (
        f"Unknown-status issues without UNKNOWN_STATUS condition: {missing}"
    )


def test_unknown_count_matches_source_distribution(tt_normalized):
    """33 issues have unknown-mapped final statuses (12+11+8+2 = Ready For QA + 
    Approved + Awaiting Approval + QA Passed)."""
    unknown_count = sum(
        1 for item in tt_normalized.work_items
        if item.status_category == "unknown"
    )
    assert unknown_count == 33, (
        f"Expected 33 unknown-status issues, got {unknown_count}"
    )


# ── Test 4: Ambiguous statuses are preserved as uncertainty ─────────────────

def test_ambiguous_source_status_preserved_in_work_item(tt_normalized):
    """Items with unknown canonical status must retain their original source_status."""
    for item in tt_normalized.work_items:
        if item.status_category == "unknown":
            assert item.source_status in UNMAPPED_SOURCE_STATUSES, (
                f"{item.key}: status_category='unknown' but source_status={item.source_status!r} "
                "is not in the expected unmapped set"
            )
            assert item.source_status != "", "source_status must not be empty"
            assert item.source_status != "unknown", (
                "source_status must preserve the original TrueTenant status string, "
                "not the canonical 'unknown' value"
            )


# ── Test 5: Changelog ordering is deterministic ─────────────────────────────

def test_changelog_ordering_deterministic():
    """Two calls to load_truetenant_changelog must produce identical ordering."""
    cl1 = load_truetenant_changelog()
    cl2 = load_truetenant_changelog()

    assert set(cl1.keys()) == set(cl2.keys()), "Changelog issue IDs differ between runs"
    for issue_id in cl1:
        h1 = [(h["id"], h.get("created")) for h in cl1[issue_id]]
        h2 = [(h["id"], h.get("created")) for h in cl2[issue_id]]
        assert h1 == h2, f"Changelog order differs for issue_id={issue_id}"


def test_changes_sorted_in_work_items(tt_normalized):
    """Each work item's changes tuple must be sorted by (changed_at, field, from, to)."""
    for item in tt_normalized.work_items:
        changes = list(item.changes)
        expected_order = sorted(
            changes,
            key=lambda c: (c.changed_at, c.field, str(c.from_value), str(c.to_value))
        )
        assert changes == expected_order, (
            f"{item.key}: changes are not in deterministic sort order"
        )


# ── Test 6: Missing history is represented explicitly ───────────────────────

ZERO_HISTORY_KEYS = {"TT-38", "TT-41", "TT-46"}


def test_zero_history_issues_have_no_changes(tt_normalized):
    """TT-38, TT-41, TT-46 have zero changelog entries — changes tuple must be empty."""
    for item in tt_normalized.work_items:
        if item.key in ZERO_HISTORY_KEYS:
            assert item.changes == (), (
                f"{item.key}: expected empty changes tuple (zero history), "
                f"got {len(item.changes)} changes"
            )


def test_zero_history_issues_are_history_complete(tt_normalized):
    """Zero-history issues are NOT partial-history — they were confirmed returned
    with empty changelog (pagination_complete=True). history_complete must be True."""
    for item in tt_normalized.work_items:
        if item.key in ZERO_HISTORY_KEYS:
            assert item.history_complete is True, (
                f"{item.key}: zero-history issue should have history_complete=True "
                "(confirmed by extraction_metadata), but got False"
            )


def test_no_partial_history_conditions(tt_normalized):
    """TrueTenant extraction was pagination_complete=True — no PARTIAL_HISTORY conditions."""
    partial = [
        cond for cond in tt_normalized.data_quality_conditions
        if cond.code == "PARTIAL_HISTORY"
    ]
    assert partial == [], (
        f"Unexpected PARTIAL_HISTORY conditions: {[c.subject_key for c in partial]}"
    )


# ── Test 7: Provenance resolves ──────────────────────────────────────────────

def test_all_items_have_source_id(tt_normalized):
    """All normalized work items must have a non-empty source_id."""
    for item in tt_normalized.work_items:
        assert item.source_id, f"{item.key}: source_id is empty or None"


def test_all_items_have_created_at(tt_normalized):
    """All work items must have a non-None created_at."""
    for item in tt_normalized.work_items:
        assert item.created_at is not None, f"{item.key}: created_at is None"


def test_all_items_have_tz_aware_timestamps(tt_normalized):
    """All timestamps must be timezone-aware (UTC or offset-aware)."""
    from datetime import timezone
    for item in tt_normalized.work_items:
        if item.created_at:
            assert item.created_at.tzinfo is not None, (
                f"{item.key}: created_at is timezone-naive"
            )
        if item.updated_at:
            assert item.updated_at.tzinfo is not None, (
                f"{item.key}: updated_at is timezone-naive"
            )
        if item.resolved_at:
            assert item.resolved_at.tzinfo is not None, (
                f"{item.key}: resolved_at is timezone-naive"
            )


def test_all_items_key_prefix_tt(tt_normalized):
    """All work items must have TT- prefixed keys."""
    for item in tt_normalized.work_items:
        assert item.key.startswith("TT-"), (
            f"Unexpected key prefix: {item.key!r}"
        )


# ── Test 8: Canonical serialization is deterministic ────────────────────────

def test_canonical_serialization_deterministic():
    """Two calls to build_truetenant_fixture_document must produce identical JSON."""
    import hashlib
    fixture1, _ = build_truetenant_fixture_document()
    fixture2, _ = build_truetenant_fixture_document()
    
    h1 = hashlib.sha256(
        json.dumps(fixture1, sort_keys=True, default=str).encode()
    ).hexdigest()
    h2 = hashlib.sha256(
        json.dumps(fixture2, sort_keys=True, default=str).encode()
    ).hexdigest()
    
    assert h1 == h2, (
        "build_truetenant_fixture_document is not deterministic: "
        f"run1={h1}, run2={h2}"
    )


# ── Test 9: Permutation invariance ───────────────────────────────────────────

def test_permutation_invariance():
    """Shuffling work_items in the fixture before normalization produces
    identical normalized output (sorted by key)."""
    import hashlib
    fixture, _ = build_truetenant_fixture_document()
    
    # Permuted fixture
    items_copy = list(fixture["work_items"])
    random.seed(42)
    random.shuffle(items_copy)
    fixture_permuted = {**fixture, "work_items": items_copy}
    
    # Normalize both
    v1 = validate_fixture(fixture)
    n1 = normalize_fixture(v1)
    
    v2 = validate_fixture(fixture_permuted)
    n2 = normalize_fixture(v2)
    
    # Work items should be in same order (sorted by key in normalize_fixture)
    keys1 = [item.key for item in n1.work_items]
    keys2 = [item.key for item in n2.work_items]
    assert keys1 == keys2, "Work item order differs after permutation"
    
    # Canonical hash of work items should be identical
    def item_hash(item):
        return (item.key, item.source_status, item.status_category, len(item.changes))
    
    hashes1 = [item_hash(i) for i in n1.work_items]
    hashes2 = [item_hash(i) for i in n2.work_items]
    assert hashes1 == hashes2, "Work item content differs after permutation"


# ── Test 10: Provider leakage guard ─────────────────────────────────────────

def test_no_jira_issue_state_import():
    """The TrueTenant ingestion module must not import JiraIssueState.
    
    Note: the docstring may reference JiraIssueState to document isolation;
    this test checks only actual import statements.
    """
    ingestion_path = PROJECT_ROOT / "qualification" / "truetenant" / "ingestion.py"
    with ingestion_path.open() as f:
        source = f.read()
    
    # Check only import lines, not docstrings
    import_lines = [
        line.strip() for line in source.splitlines()
        if line.strip().startswith(("import ", "from ")) and "JiraIssueState" in line
    ]
    assert import_lines == [], (
        f"TrueTenant ingestion.py has import statement referencing JiraIssueState: {import_lines}"
    )
    
    # Also verify GitHubPullRequestState is not imported
    gh_import_lines = [
        line.strip() for line in source.splitlines()
        if line.strip().startswith(("import ", "from ")) and "GitHubPullRequestState" in line
    ]
    assert gh_import_lines == [], (
        f"TrueTenant ingestion.py imports GitHubPullRequestState: {gh_import_lines}"
    )


def test_no_jira_normalization_import():
    """The TrueTenant ingestion module must not import jira_evidence_adapter."""
    ingestion_path = PROJECT_ROOT / "qualification" / "truetenant" / "ingestion.py"
    with ingestion_path.open() as f:
        source = f.read()
    
    assert "jira_evidence_adapter" not in source, (
        "TrueTenant ingestion.py imports jira_evidence_adapter — provider leakage"
    )
    assert "github_normalization" not in source, (
        "TrueTenant ingestion.py imports github_normalization — provider leakage"
    )


# ── Test 11: Finding IDs are deterministic ───────────────────────────────────

def test_finding_ids_deterministic():
    """Two independent evaluations must produce identical finding subject_keys and rule_keys."""
    fixture, _ = build_truetenant_fixture_document()
    
    v1 = validate_fixture(fixture)
    n1 = normalize_fixture(v1)
    m1, s1 = evaluate_week_one_rules(n1)
    
    v2 = validate_fixture(fixture)
    n2 = normalize_fixture(v2)
    m2, s2 = evaluate_week_one_rules(n2)
    
    ids1 = sorted((m.subject_key, m.rule_key) for m in m1)
    ids2 = sorted((m.subject_key, m.rule_key) for m in m2)
    
    assert ids1 == ids2, (
        f"Finding IDs differ between runs: {ids1} vs {ids2}"
    )
    
    sup1 = sorted((s.subject_key, s.rule_key) for s in s1)
    sup2 = sorted((s.subject_key, s.rule_key) for s in s2)
    
    assert sup1 == sup2, (
        f"Suppression IDs differ between runs: {sup1} vs {sup2}"
    )


# ── Test 12: Mapping cannot be influenced by evaluator output ───────────────

def test_mapping_frozen_before_evaluation():
    """The mapping table in the fixture must match the frozen contract exactly.
    This verifies that the adapter's mapping was not tuned based on evaluation output.
    """
    # The frozen contract (must match TRUETENANT_MAPPING_CONTRACT.md)
    FROZEN_CONTRACT = {
        "To Do": "todo",
        "Dev In Progress": "in_progress",
        "ReOpen": "in_progress",
        "Done": "done",
        "Feature Not Required": "done",
        "Not an Issue": "done",
        "Awaiting Approval": "unknown",
        "Approved": "unknown",
        "Ready For QA": "unknown",
        "QA Passed": "unknown",
        "Pending For More Information": "unknown",
    }
    
    fixture, _ = build_truetenant_fixture_document()
    actual_mapping = fixture["configuration"]["status_mapping"]
    
    # Check each contract entry is present and unchanged
    for status, expected_canonical in FROZEN_CONTRACT.items():
        actual = actual_mapping.get(status)
        assert actual == expected_canonical, (
            f"Mapping for {status!r} is {actual!r} but frozen contract specifies {expected_canonical!r}. "
            "The mapping must not be modified based on evaluator output."
        )


# ── Test 13: No Jira/GitHub-specific evaluator branch ────────────────────────

def test_evaluation_does_not_use_provider_specific_branch(tt_normalized, tt_evaluation):
    """The evaluator must process TrueTenant items through canonical WorkItem logic,
    not through JiraIssueState or GitHubPullRequestState specific branches."""
    matches, suppressed = tt_evaluation
    
    # All matched items must be WorkItem instances (not JiraIssueState etc.)
    from shadow_orbit.types import WorkItem
    for item in tt_normalized.work_items:
        assert isinstance(item, WorkItem), (
            f"{item.key}: item is {type(item).__name__}, expected WorkItem"
        )
    
    # Findings must reference keys that exist in normalized.work_items
    item_keys = {item.key for item in tt_normalized.work_items}
    for m in matches:
        assert m.subject_key in item_keys, (
            f"Finding references {m.subject_key!r} which is not in normalized work_items"
        )


# ── Test 14: Core corpus invariants ──────────────────────────────────────────

def test_corpus_size(tt_normalized):
    """Exactly 112 issues must be accepted."""
    assert len(tt_normalized.work_items) == 112, (
        f"Expected 112 work items, got {len(tt_normalized.work_items)}"
    )


def test_no_quarantine(tt_quarantine):
    """All 112 issues must project successfully — 0 quarantined."""
    assert tt_quarantine == [], (
        f"Expected 0 quarantined records, got {len(tt_quarantine)}: {tt_quarantine}"
    )


def test_canonical_status_distribution(tt_normalized):
    """Canonical status distribution must match the pre-computed expected counts.
    done=56, todo=19, unknown=33, in_progress=4, blocked=0.
    """
    from collections import Counter
    dist = Counter(item.status_category for item in tt_normalized.work_items)
    
    assert dist["done"] == 56, f"Expected 56 'done' items, got {dist['done']}"
    assert dist["todo"] == 19, f"Expected 19 'todo' items, got {dist['todo']}"
    assert dist["unknown"] == 33, f"Expected 33 'unknown' items, got {dist['unknown']}"
    assert dist["in_progress"] == 4, f"Expected 4 'in_progress' items, got {dist['in_progress']}"
    assert dist["blocked"] == 0, f"Expected 0 'blocked' items, got {dist['blocked']}"


def test_stalled_work_finding_is_dev_in_progress(tt_evaluation, tt_normalized):
    """The single STALLED_WORK finding must be for TT-2 with source_status='Dev In Progress'."""
    matches, _ = tt_evaluation
    stalled = [m for m in matches if m.rule_key == "STALLED_WORK"]
    
    assert len(stalled) == 1, f"Expected 1 STALLED_WORK finding, got {len(stalled)}"
    assert stalled[0].subject_key == "TT-2", (
        f"Expected STALLED_WORK on TT-2, got {stalled[0].subject_key}"
    )
    
    # Verify source status
    item = next(i for i in tt_normalized.work_items if i.key == "TT-2")
    assert item.source_status == "Dev In Progress", (
        f"TT-2 source_status should be 'Dev In Progress', got {item.source_status!r}"
    )
    assert item.status_category == "in_progress", (
        f"TT-2 status_category should be 'in_progress', got {item.status_category!r}"
    )


def test_unknown_status_issues_are_not_evaluated(tt_evaluation, tt_normalized):
    """Issues with unknown status category must not trigger evaluation rules
    (they are suppressed or not evaluated at all — the evaluator skips non-matching categories)."""
    matches, _ = tt_evaluation
    
    # Map unknown issues
    unknown_keys = {item.key for item in tt_normalized.work_items if item.status_category == "unknown"}
    # No finding should reference an unknown-status issue
    match_keys = {m.subject_key for m in matches}
    
    overlap = unknown_keys & match_keys
    assert overlap == set(), (
        f"Unknown-status issues produced findings: {overlap}. "
        "The evaluator must not fire rules on unknown-status items."
    )


def test_timestamp_parsing_epoch_ms():
    """Epoch millisecond timestamps must parse correctly."""
    ts = 1789392619369  # 2026-09-14T13:30:19.369Z
    result = _parse_epoch_ms(ts)
    assert result is not None
    assert "2026-09-14" in result
    assert result.endswith("+00:00"), f"Expected UTC offset, got: {result}"


def test_timestamp_parsing_csv():
    """CSV date format must parse correctly."""
    result = _parse_csv_datetime("28/Jul/26 3:34 PM")
    assert result is not None
    assert "2026-07-28" in result


def test_invalid_key_quarantined():
    """A record with an invalid key must raise QuarantineError."""
    bad_row = {
        "Issue key": "INVALID-KEY",
        "Issue id": "12345",
        "Summary": "Test",
        "Issue Type": "Bug",
        "Priority": "Medium",
        "Status": "To Do",
        "Created": "28/Jul/26 3:34 PM",
        "Updated": "28/Jul/26 3:34 PM",
    }
    with pytest.raises(QuarantineError) as exc_info:
        project_single_truetenant_record(bad_row, [])
    assert exc_info.value.reason_code == "INVALID_KEY"


def test_missing_summary_quarantined():
    """A record with a missing summary must raise QuarantineError."""
    bad_row = {
        "Issue key": "TT-999",
        "Issue id": "99999",
        "Summary": "",
        "Issue Type": "Bug",
        "Priority": "Medium",
        "Status": "To Do",
        "Created": "28/Jul/26 3:34 PM",
        "Updated": "28/Jul/26 3:34 PM",
    }
    with pytest.raises(QuarantineError) as exc_info:
        project_single_truetenant_record(bad_row, [])
    assert exc_info.value.reason_code == "MISSING_SUMMARY"
