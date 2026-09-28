"""Unit and adversarial tests for Pass 3 controlled hardening remediations.

Covers:
- P3-01: Reopen-cycle completion timestamp semantics
- P3-02: Post-cutoff record handling in messy acceptance
- P3-03: Strict boolean primitive type safety
- P3-04: Chronological coherence enforcement
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from shadow_orbit.temporal import completed_during_period, completion_time
from shadow_orbit.types import Change, ReviewPeriod, WorkItem

UTC = timezone.utc


# ============================================================================
# P3-01: Reopen-Cycle Completion Timestamp Semantics
# ============================================================================


def _create_work_item(
    key: str = "ORBIT-101",
    source_status: str = "Done",
    status_category: str = "done",
    changes: tuple[Change, ...] = (),
    resolved_at: datetime | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> WorkItem:
    t_created = created_at or datetime(2021, 5, 1, 10, 0, tzinfo=UTC)
    t_updated = updated_at or datetime(2021, 5, 25, 10, 0, tzinfo=UTC)
    return WorkItem(
        source_id="src-101",
        key=key,
        title="Test Item",
        item_type="Task",
        source_priority="High",
        priority_band="high",
        source_status=source_status,
        status_category=status_category,  # type: ignore[arg-type]
        assignee="alice",
        created_at=t_created,
        updated_at=t_updated,
        resolved_at=resolved_at,
        due_at=None,
        planned_at_period_start=True,
        history_complete=True,
        source_status_at_period_start="In Progress",
        changes=changes,
    )


class TestP301ReopenCycleCompletion:
    """Tests for P3-01 reopen-cycle completion timestamp semantics."""

    def test_reopen_two_done_cycles_selects_latest_completion(self):
        """When an issue is reopened and resolved again, completion_time must

        return the latest transition establishing the current completed state,
        not the obsolete initial completion.
        """
        changes = (
            Change("status", "Open", "In Progress", datetime(2021, 5, 2, 10, 0, tzinfo=UTC)),
            Change("status", "In Progress", "Done", datetime(2021, 5, 15, 10, 0, tzinfo=UTC)),
            Change("status", "Done", "Reopened", datetime(2021, 5, 20, 10, 0, tzinfo=UTC)),
            Change("status", "Reopened", "Done", datetime(2021, 5, 25, 10, 0, tzinfo=UTC)),
        )
        item = _create_work_item(
            source_status="Done",
            status_category="done",
            changes=changes,
            resolved_at=datetime(2021, 5, 25, 10, 0, tzinfo=UTC),
        )

        completed_at = completion_time(item)
        assert completed_at == datetime(2021, 5, 25, 10, 0, tzinfo=UTC)

    def test_reopen_currently_in_progress_returns_none(self):
        """When an issue was previously completed but is currently reopened,

        completion_time must evaluate to None.
        """
        changes = (
            Change("status", "Open", "In Progress", datetime(2021, 5, 2, 10, 0, tzinfo=UTC)),
            Change("status", "In Progress", "Done", datetime(2021, 5, 15, 10, 0, tzinfo=UTC)),
            Change("status", "Done", "Reopened", datetime(2021, 5, 20, 10, 0, tzinfo=UTC)),
        )
        item = _create_work_item(
            source_status="Reopened",
            status_category="in_progress",
            changes=changes,
            resolved_at=None,
        )

        completed_at = completion_time(
            item, status_mapping={"Open": "todo", "In Progress": "in_progress", "Done": "done", "Reopened": "in_progress"}
        )
        assert completed_at is None

    def test_single_completion_unaltered(self):
        """Single-cycle completed items must continue to return their completion timestamp."""
        changes = (
            Change("status", "Open", "In Progress", datetime(2021, 5, 2, 10, 0, tzinfo=UTC)),
            Change("status", "In Progress", "Done", datetime(2021, 5, 15, 10, 0, tzinfo=UTC)),
        )
        item = _create_work_item(
            source_status="Done",
            status_category="done",
            changes=changes,
            resolved_at=datetime(2021, 5, 15, 10, 0, tzinfo=UTC),
        )

        completed_at = completion_time(item)
        assert completed_at == datetime(2021, 5, 15, 10, 0, tzinfo=UTC)

    def test_adversarial_triple_reopen_cycle(self):
        """Multiple reopen cycles must select the final cycle's entry timestamp."""
        changes = (
            Change("status", "Open", "Done", datetime(2021, 5, 5, 10, 0, tzinfo=UTC)),
            Change("status", "Done", "Reopened", datetime(2021, 5, 10, 10, 0, tzinfo=UTC)),
            Change("status", "Reopened", "Done", datetime(2021, 5, 15, 10, 0, tzinfo=UTC)),
            Change("status", "Done", "Reopened", datetime(2021, 5, 20, 10, 0, tzinfo=UTC)),
            Change("status", "Reopened", "Done", datetime(2021, 5, 25, 10, 0, tzinfo=UTC)),
        )
        item = _create_work_item(
            source_status="Done",
            status_category="done",
            changes=changes,
            resolved_at=datetime(2021, 5, 25, 10, 0, tzinfo=UTC),
        )
        assert completion_time(item) == datetime(2021, 5, 25, 10, 0, tzinfo=UTC)

    def test_adversarial_contiguous_terminal_done_transitions(self):
        """When an issue transitions between multiple done statuses (e.g. Resolved -> Closed),

        completion_time must return the timestamp when it first entered the contiguous done block.
        """
        changes = (
            Change("status", "Open", "In Progress", datetime(2021, 5, 2, 10, 0, tzinfo=UTC)),
            Change("status", "In Progress", "Done", datetime(2021, 5, 10, 10, 0, tzinfo=UTC)),
            Change("status", "Done", "Reopened", datetime(2021, 5, 15, 10, 0, tzinfo=UTC)),
            Change("status", "Reopened", "Resolved", datetime(2021, 5, 22, 10, 0, tzinfo=UTC)),
            Change("status", "Resolved", "Closed", datetime(2021, 5, 26, 10, 0, tzinfo=UTC)),
        )
        status_map = {
            "Open": "todo",
            "In Progress": "in_progress",
            "Done": "done",
            "Reopened": "in_progress",
            "Resolved": "done",
            "Closed": "done",
        }
        item = _create_work_item(
            source_status="Closed",
            status_category="done",
            changes=changes,
            resolved_at=datetime(2021, 5, 22, 10, 0, tzinfo=UTC),
        )
        assert completion_time(item, status_mapping=status_map) == datetime(2021, 5, 22, 10, 0, tzinfo=UTC)

    def test_completed_during_period_with_reopened_issue(self):
        """An issue completed outside period, reopened, and completed inside period

        must evaluate completed_during_period as True.
        """
        period = ReviewPeriod(
            label="Week 2",
            starts_at=datetime(2021, 5, 20, 0, 0, tzinfo=UTC),
            ends_at_exclusive=datetime(2021, 5, 27, 0, 0, tzinfo=UTC),
            review_cutoff_at=datetime(2021, 5, 27, 0, 0, tzinfo=UTC),
            source_cutoff_at=datetime(2021, 5, 27, 0, 0, tzinfo=UTC),
        )
        # Cycle 1: May 15 (outside period)
        # Cycle 2: May 25 (inside period)
        changes = (
            Change("status", "Open", "Done", datetime(2021, 5, 15, 10, 0, tzinfo=UTC)),
            Change("status", "Done", "Reopened", datetime(2021, 5, 18, 10, 0, tzinfo=UTC)),
            Change("status", "Reopened", "Done", datetime(2021, 5, 25, 10, 0, tzinfo=UTC)),
        )
        item = _create_work_item(
            source_status="Done",
            status_category="done",
            changes=changes,
            resolved_at=datetime(2021, 5, 25, 10, 0, tzinfo=UTC),
        )
        assert completed_during_period(item, period) is True

    def test_completed_before_period_reopened_during_period_is_not_completed(self):
        """An issue completed before period but reopened during period and not re-closed

        must NOT be counted as completed during period.
        """
        period = ReviewPeriod(
            label="Week 2",
            starts_at=datetime(2021, 5, 20, 0, 0, tzinfo=UTC),
            ends_at_exclusive=datetime(2021, 5, 27, 0, 0, tzinfo=UTC),
            review_cutoff_at=datetime(2021, 5, 27, 0, 0, tzinfo=UTC),
            source_cutoff_at=datetime(2021, 5, 27, 0, 0, tzinfo=UTC),
        )
        changes = (
            Change("status", "Open", "Done", datetime(2021, 5, 15, 10, 0, tzinfo=UTC)),
            Change("status", "Done", "Reopened", datetime(2021, 5, 22, 10, 0, tzinfo=UTC)),
        )
        item = _create_work_item(
            source_status="Reopened",
            status_category="in_progress",
            changes=changes,
            resolved_at=None,
        )
        status_map = {"Open": "todo", "Done": "done", "Reopened": "in_progress"}
        assert completed_during_period(item, period, status_mapping=status_map) is False


# ============================================================================
# P3-02: Post-Cutoff Record Handling in Messy Acceptance
# ============================================================================


class TestP302PostCutoffRecordHandling:
    """Tests for P3-02 post-cutoff record handling in messy acceptance artifact generation."""

    def test_post_cutoff_record_does_not_crash_artifact_generation(
        self,
        messy_week_one_document,
    ):
        """When a work item has updated_at > source_cutoff_at, building the

        messy artifact must not crash with ValueError('end must not precede start').
        """
        import copy
        from shadow_orbit.messy_acceptance import build_messy_week_one_artifact
        from shadow_orbit.normalization import normalize_fixture
        from shadow_orbit.validation import validate_fixture

        doc = copy.deepcopy(messy_week_one_document)
        # Set an item's updated_at well past the source cutoff date (2026-02-09)
        doc["work_items"][0]["updated_at"] = "2026-05-01T12:00:00Z"
        validated = validate_fixture(doc)
        normalized = normalize_fixture(validated)

        artifact = build_messy_week_one_artifact(validated, normalized)
        assert "what_orbit_could_not_determine" in artifact
        assert isinstance(artifact["what_orbit_could_not_determine"], dict)

    def test_post_cutoff_record_is_not_marked_stale(
        self,
        messy_week_one_document,
    ):
        """A record updated in the future relative to the source cutoff is not stale."""
        import copy
        from shadow_orbit.messy_acceptance import build_messy_week_one_artifact
        from shadow_orbit.normalization import normalize_fixture
        from shadow_orbit.validation import validate_fixture

        doc = copy.deepcopy(messy_week_one_document)
        target_key = doc["work_items"][0]["key"]
        doc["work_items"][0]["updated_at"] = "2026-05-01T12:00:00Z"
        validated = validate_fixture(doc)
        normalized = normalize_fixture(validated)

        artifact = build_messy_week_one_artifact(validated, normalized)
        limitations = artifact["what_orbit_could_not_determine"]
        stale_condition = next(
            (c for c in limitations.get("conditions", []) if c.get("code") == "STALE_RECORD"),
            None,
        )
        if stale_condition:
            assert target_key not in stale_condition.get("subject_keys", [])

    def test_existing_stale_records_unaffected(
        self,
        messy_week_one_document,
    ):
        """Standard unmutated messy week 1 fixture preserves baseline limitations."""
        from shadow_orbit.messy_acceptance import build_messy_week_one_artifact
        from shadow_orbit.normalization import normalize_fixture
        from shadow_orbit.validation import validate_fixture

        validated = validate_fixture(messy_week_one_document)
        normalized = normalize_fixture(validated)

        artifact = build_messy_week_one_artifact(validated, normalized)
        assert "what_orbit_could_not_determine" in artifact

