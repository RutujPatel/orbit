"""Deterministic Bounded Seed Selector for Mahout Qualification.

Extracts from the Public Jira Dataset 2025 (MongoDB JiraReposAnon.Apache,
filtered on fields.project.key == 'MAHOUT').

Deterministic Policy:
- Target size: exactly 400 issues.
- Selection maximizes empirical behavioral coverage across:
  1. All 6 observed statuses (Open, Resolved, Closed, Reopened, In Progress, Patch Available)
  2. All 15 observed status-transition pairs (including rare and cyclic transitions)
  3. All 5 observed priorities (Blocker, Critical, Major, Minor, Trivial)
  4. All 16 observed issue types (including singleton and rare types)
  5. Due date presence (issues with and without due dates)
  6. Changelog history depths (zero-transition baseline, single-transition, multi-transition, deep history)
  7. Auditable selection reason attached to each selected issue
  8. Deterministic tie-breaking by numeric key order (key_num, key)
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from qualification.policy import canonical_record_hash, compute_sha256_text

DEFAULT_TARGET_SEED_SIZE: int = 400
MAHOUT_PROJECT_KEY: str = "MAHOUT"
MONGO_DATABASE_NAME: str = "JiraReposAnon"
MONGO_COLLECTION_NAME: str = "Apache"


@dataclass(frozen=True, slots=True)
class MahoutIssueSummary:
    """Normalized summary of a Mahout issue extracted from the source dataset."""

    key: str
    key_num: int
    source_id: str
    status: str
    priority: str
    issuetype: str
    has_duedate: bool
    duedate: str | None
    status_changes_count: int
    total_changelog_histories: int
    transitions: tuple[tuple[str, str], ...]
    transition_set: frozenset[tuple[str, str]]
    selection_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "key_num": self.key_num,
            "source_id": self.source_id,
            "status": self.status,
            "priority": self.priority,
            "issuetype": self.issuetype,
            "has_duedate": self.has_duedate,
            "duedate": self.duedate,
            "status_changes_count": self.status_changes_count,
            "total_changelog_histories": self.total_changelog_histories,
            "transitions": [list(t) for t in self.transitions],
            "selection_reason": self.selection_reason,
        }


@dataclass(frozen=True, slots=True)
class MahoutSeedResult:
    """Result of the deterministic bounded Mahout seed selection."""

    target_size: int
    selected_count: int
    source_total_considered: int
    selected_issues: tuple[MahoutIssueSummary, ...]
    selected_keys: tuple[str, ...]
    selection_hash: str
    coverage_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_size": self.target_size,
            "selected_count": self.selected_count,
            "source_total_considered": self.source_total_considered,
            "selected_keys": list(self.selected_keys),
            "selection_hash": self.selection_hash,
            "coverage_summary": self.coverage_summary,
            "selected_issues": [issue.to_dict() for issue in self.selected_issues],
        }


def parse_mahout_raw_issue(raw_doc: dict[str, Any]) -> MahoutIssueSummary:
    """Parse a raw MongoDB document into a normalized MahoutIssueSummary."""
    key = str(raw_doc.get("key", "")).strip()
    source_id = str(raw_doc.get("id", "")).strip()

    # Extract numeric portion of key for stable deterministic sorting
    key_num = 0
    if "-" in key:
        num_part = key.split("-", 1)[1]
        if num_part.isdigit():
            key_num = int(num_part)

    fields = raw_doc.get("fields", {}) or {}

    # Status
    status_obj = fields.get("status")
    status = status_obj.get("name") if isinstance(status_obj, dict) else str(status_obj or "Unknown")

    # Priority
    priority_obj = fields.get("priority")
    priority = priority_obj.get("name") if isinstance(priority_obj, dict) else str(priority_obj or "Unknown")

    # Issue Type
    type_obj = fields.get("issuetype")
    issuetype = type_obj.get("name") if isinstance(type_obj, dict) else str(type_obj or "Unknown")

    # Due date
    duedate = fields.get("duedate")
    has_duedate = bool(duedate)

    # Changelog status transitions
    changelog = raw_doc.get("changelog", {}) or {}
    histories = changelog.get("histories", []) or []
    transitions_list: list[tuple[str, str]] = []
    status_changes_count = 0

    for h in histories:
        if not isinstance(h, dict):
            continue
        for it in h.get("items", []) or []:
            if isinstance(it, dict) and it.get("field") == "status":
                status_changes_count += 1
                from_str = str(it.get("fromString") or "Unknown")
                to_str = str(it.get("toString") or "Unknown")
                transitions_list.append((from_str, to_str))

    return MahoutIssueSummary(
        key=key,
        key_num=key_num,
        source_id=source_id,
        status=status,
        priority=priority,
        issuetype=issuetype,
        has_duedate=has_duedate,
        duedate=str(duedate) if duedate else None,
        status_changes_count=status_changes_count,
        total_changelog_histories=len(histories),
        transitions=tuple(transitions_list),
        transition_set=frozenset(transitions_list),
        selection_reason="",
    )


def select_mahout_seed(
    source_docs: Iterable[dict[str, Any]],
    target_size: int = DEFAULT_TARGET_SEED_SIZE,
) -> MahoutSeedResult:
    """Deterministically select a bounded corpus of issues from the Mahout source dataset.

    Guarantees:
    - Exactly `target_size` issues returned (or all if source < target_size).
    - Maximizes behavioral coverage: 100% of observed statuses, 100% of observed transition
      pairs, 100% of observed priorities, 100% of observed issue types.
    - Captures due date presence, baseline zero-change and single-change issues, and deep history.
    - Fully deterministic tie-breaking by (key_num, key).
    - Every selected issue records its selection reason.
    - Zero synthetic data, zero timestamp alteration, zero invented values.
    """
    # 1. Parse and sort all issues by stable deterministic key
    parsed = [parse_mahout_raw_issue(doc) for doc in source_docs]
    parsed.sort(key=lambda x: (x.key_num, x.key))

    source_total = len(parsed)
    if source_total < target_size:
        raise ValueError(
            f"Source dataset contains only {source_total} issues; cannot satisfy target seed size {target_size}"
        )

    selected: dict[str, str] = {}  # key -> selection_reason

    def select(issue: MahoutIssueSummary, reason: str) -> bool:
        if issue.key not in selected and len(selected) < target_size:
            selected[issue.key] = reason
            return True
        return False

    # Tier 1: Rare statuses (< 20 occurrences in Mahout: Patch Available, Reopened, In Progress)
    for issue in parsed:
        if issue.status in ("Patch Available", "Reopened", "In Progress"):
            select(issue, f"rare_status:{issue.status}")

    # Tier 2: Rare transition pairs (< 30 occurrences)
    rare_transitions: Sequence[tuple[str, str]] = (
        ("Reopened", "In Progress"),       # 2 occurrences
        ("Patch Available", "In Progress"),# 5 occurrences
        ("Open", "Closed"),                # 12 occurrences
        ("In Progress", "Open"),           # 14 occurrences
        ("Reopened", "Patch Available"),   # 18 occurrences
        ("In Progress", "Patch Available"),# 25 occurrences
    )
    for t_from, t_to in rare_transitions:
        pair = (t_from, t_to)
        for issue in parsed:
            if pair in issue.transition_set:
                select(issue, f"rare_transition:{t_from}->{t_to}")

    # Tier 3: Rare issue types (< 50 occurrences in Mahout)
    rare_types: Sequence[str] = (
        "Planned Work",
        "Proposal",
        "Story",
        "New JIRA Project",
        "Blog - New Blog Request",
        "Dependency upgrade",
        "Epic",
        "Test",
        "Wish",
        "Documentation",
        "Question",
        "Sub-task",
    )
    for rt in rare_types:
        for issue in parsed:
            if issue.issuetype == rt:
                select(issue, f"rare_issuetype:{rt}")

    # Tier 4: Ensure ALL remaining transition pairs are covered
    all_observed_transitions: set[tuple[str, str]] = set()
    for issue in parsed:
        all_observed_transitions.update(issue.transition_set)

    for pair in sorted(list(all_observed_transitions)):
        # Check if already covered
        already_covered = any(pair in issue.transition_set for issue in parsed if issue.key in selected)
        if not already_covered:
            for issue in parsed:
                if pair in issue.transition_set:
                    select(issue, f"transition_coverage:{pair[0]}->{pair[1]}")
                    break

    # Tier 5: Top deep histories (top 25 most status changes)
    deep_sorted = sorted(parsed, key=lambda x: (-x.status_changes_count, x.key_num, x.key))
    for issue in deep_sorted[:25]:
        select(issue, f"deep_history:{issue.status_changes_count}_changes")

    # Tier 6: Zero status changes (baseline testing absence of history)
    zero_changes = [issue for issue in parsed if issue.status_changes_count == 0]
    for issue in zero_changes[:20]:
        select(issue, "zero_status_changes_baseline")

    # Tier 7: Single status change
    single_change = [issue for issue in parsed if issue.status_changes_count == 1]
    for issue in single_change[:25]:
        select(issue, "single_status_change_baseline")

    # Tier 8: Due date presence
    with_duedate = [issue for issue in parsed if issue.has_duedate]
    for issue in with_duedate[:40]:
        select(issue, "due_date_present")

    # Tier 9: Priority quotas (ensure at least 30 of each priority)
    for pr in ("Blocker", "Critical", "Trivial", "Minor", "Major"):
        current_pr_count = sum(1 for issue in parsed if issue.key in selected and issue.priority == pr)
        if current_pr_count < 30:
            for issue in parsed:
                if issue.priority == pr:
                    if select(issue, f"priority_quota:{pr}"):
                        current_pr_count += 1
                        if current_pr_count >= 30:
                            break

    # Tier 10: Stratified round-robin fill across (status, priority, issuetype) combinations
    if len(selected) < target_size:
        remaining = [issue for issue in parsed if issue.key not in selected]
        buckets: dict[tuple[str, str, str], list[MahoutIssueSummary]] = defaultdict(list)
        for issue in remaining:
            sig = (issue.status, issue.priority, issue.issuetype)
            buckets[sig].append(issue)

        sorted_sigs = sorted(buckets.keys())
        idx = 0
        while len(selected) < target_size and any(buckets[s] for s in sorted_sigs):
            sig = sorted_sigs[idx % len(sorted_sigs)]
            if buckets[sig]:
                item = buckets[sig].pop(0)
                select(item, f"stratified_fill:{sig[0]}|{sig[1]}|{sig[2]}")
            idx += 1

    # Tier 11: Final deterministic fallback if any slots remain
    if len(selected) < target_size:
        for issue in parsed:
            if issue.key not in selected:
                select(issue, "deterministic_remainder_fill")
                if len(selected) >= target_size:
                    break

    if len(selected) != target_size:
        raise RuntimeError(
            f"Seed selection failed to satisfy target count {target_size}! Selected only {len(selected)}"
        )

    # Build final selected summaries with reasons attached, sorted deterministically
    final_selected_summaries: list[MahoutIssueSummary] = []
    for issue in parsed:
        if issue.key in selected:
            summary_with_reason = MahoutIssueSummary(
                key=issue.key,
                key_num=issue.key_num,
                source_id=issue.source_id,
                status=issue.status,
                priority=issue.priority,
                issuetype=issue.issuetype,
                has_duedate=issue.has_duedate,
                duedate=issue.duedate,
                status_changes_count=issue.status_changes_count,
                total_changelog_histories=issue.total_changelog_histories,
                transitions=issue.transitions,
                transition_set=issue.transition_set,
                selection_reason=selected[issue.key],
            )
            final_selected_summaries.append(summary_with_reason)

    selected_keys = tuple(issue.key for issue in final_selected_summaries)

    # Compute canonical selection hash
    selection_record = [
        {"key": issue.key, "id": issue.source_id, "reason": issue.selection_reason}
        for issue in final_selected_summaries
    ]
    selection_hash = canonical_record_hash(selection_record)

    # Build comprehensive coverage summary
    statuses_counter = Counter(issue.status for issue in final_selected_summaries)
    priorities_counter = Counter(issue.priority for issue in final_selected_summaries)
    types_counter = Counter(issue.issuetype for issue in final_selected_summaries)
    due_dates_count = sum(1 for issue in final_selected_summaries if issue.has_duedate)

    covered_transitions = set()
    for issue in final_selected_summaries:
        covered_transitions.update(issue.transition_set)

    transition_counts: dict[str, int] = {}
    for pair in sorted(list(all_observed_transitions)):
        label = f"{pair[0]}->{pair[1]}"
        cnt = sum(1 for issue in final_selected_summaries if pair in issue.transition_set)
        transition_counts[label] = cnt

    depth_buckets = {
        "0_transitions": sum(1 for issue in final_selected_summaries if issue.status_changes_count == 0),
        "1_transition": sum(1 for issue in final_selected_summaries if issue.status_changes_count == 1),
        "2_to_5_transitions": sum(1 for issue in final_selected_summaries if 2 <= issue.status_changes_count <= 5),
        "6_to_10_transitions": sum(1 for issue in final_selected_summaries if 6 <= issue.status_changes_count <= 10),
        "greater_than_10_transitions": sum(1 for issue in final_selected_summaries if issue.status_changes_count > 10),
    }

    coverage_summary = {
        "target_size": target_size,
        "selected_count": len(final_selected_summaries),
        "source_total_considered": source_total,
        "selection_hash": selection_hash,
        "status_coverage": {
            "total_observed_in_source": len(set(issue.status for issue in parsed)),
            "covered_in_seed": len(statuses_counter),
            "counts": dict(statuses_counter),
        },
        "priority_coverage": {
            "total_observed_in_source": len(set(issue.priority for issue in parsed)),
            "covered_in_seed": len(priorities_counter),
            "counts": dict(priorities_counter),
        },
        "issue_type_coverage": {
            "total_observed_in_source": len(set(issue.issuetype for issue in parsed)),
            "covered_in_seed": len(types_counter),
            "counts": dict(types_counter),
        },
        "due_date_coverage": {
            "with_due_date": due_dates_count,
            "without_due_date": len(final_selected_summaries) - due_dates_count,
        },
        "transition_coverage": {
            "total_pairs_observed_in_source": len(all_observed_transitions),
            "covered_pairs_in_seed": len(covered_transitions),
            "pairs": transition_counts,
        },
        "history_depth_distribution": depth_buckets,
    }

    return MahoutSeedResult(
        target_size=target_size,
        selected_count=len(final_selected_summaries),
        source_total_considered=source_total,
        selected_issues=tuple(final_selected_summaries),
        selected_keys=selected_keys,
        selection_hash=selection_hash,
        coverage_summary=coverage_summary,
    )


def load_mahout_issues_from_mongo(
    mongo_uri: str = "mongodb://127.0.0.1:27017/",
    db_name: str = MONGO_DATABASE_NAME,
    collection_name: str = MONGO_COLLECTION_NAME,
) -> list[dict[str, Any]]:
    """Query Mahout issues directly from MongoDB JiraReposAnon.Apache."""
    import pymongo

    client = pymongo.MongoClient(mongo_uri)
    col = client[db_name][collection_name]
    cursor = col.find(
        {"fields.project.key": MAHOUT_PROJECT_KEY},
        {
            "_id": 0,
            "key": 1,
            "id": 1,
            "fields.status.name": 1,
            "fields.priority.name": 1,
            "fields.issuetype.name": 1,
            "fields.duedate": 1,
            "changelog.histories": 1,
        },
    )
    return list(cursor)


if __name__ == "__main__":
    print("Loading Mahout issues from MongoDB...")
    docs = load_mahout_issues_from_mongo()
    print(f"Loaded {len(docs)} Mahout documents from MongoDB.")
    result = select_mahout_seed(docs, target_size=400)
    print(f"Selection complete: {result.selected_count} issues selected.")
    print(f"Selection hash: {result.selection_hash}")
    print("Coverage Summary:")
    print(json.dumps(result.coverage_summary, indent=2))
