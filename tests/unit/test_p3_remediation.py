"""Unit and adversarial tests for Pass 3 controlled hardening remediations.

Covers:
- P3-01: Reopen-cycle completion timestamp semantics
- P3-02: Post-cutoff record handling in messy acceptance
- P3-03: Strict boolean primitive type safety
- P3-04: Chronological coherence enforcement
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

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


# ============================================================================
# P3-03: Strict Boolean Primitive Type Safety
# ============================================================================


class TestP303BooleanPrimitiveTypeSafety:
    """Tests for P3-03 strict boolean primitive type safety in validation."""

    def test_boolean_field_string_false_quarantined(
        self,
        clean_week_one_document,
    ):
        """String 'false' for history_complete must be quarantined, not coerced to True."""
        import copy
        from shadow_orbit.validation import validate_fixture

        doc = copy.deepcopy(clean_week_one_document)
        target_key = doc["work_items"][0]["key"]
        doc["work_items"][0]["history_complete"] = "false"

        result = validate_fixture(doc)
        quarantined = [q for q in result.quarantined_records if q.source_key == target_key]
        assert len(quarantined) == 1
        assert quarantined[0].reason_code == "INVALID_PRIMITIVE_TYPE"
        assert "history_complete" in quarantined[0].reason

    def test_boolean_field_string_true_quarantined(
        self,
        clean_week_one_document,
    ):
        """String 'true' for history_complete must be quarantined."""
        import copy
        from shadow_orbit.validation import validate_fixture

        doc = copy.deepcopy(clean_week_one_document)
        target_key = doc["work_items"][0]["key"]
        doc["work_items"][0]["history_complete"] = "true"

        result = validate_fixture(doc)
        quarantined = [q for q in result.quarantined_records if q.source_key == target_key]
        assert len(quarantined) == 1
        assert quarantined[0].reason_code == "INVALID_PRIMITIVE_TYPE"

    def test_boolean_field_integer_quarantined(
        self,
        clean_week_one_document,
    ):
        """Integers 1 and 0 for history_complete must be quarantined."""
        import copy
        from shadow_orbit.validation import validate_fixture

        for val in (1, 0):
            doc = copy.deepcopy(clean_week_one_document)
            target_key = doc["work_items"][0]["key"]
            doc["work_items"][0]["history_complete"] = val

            result = validate_fixture(doc)
            quarantined = [q for q in result.quarantined_records if q.source_key == target_key]
            assert len(quarantined) == 1, f"Expected integer {val} to be quarantined"
            assert quarantined[0].reason_code == "INVALID_PRIMITIVE_TYPE"

    def test_boolean_field_genuine_bool_accepted(
        self,
        clean_week_one_document,
    ):
        """Genuine booleans True and False must be accepted without quarantine."""
        import copy
        from shadow_orbit.validation import validate_fixture

        for val in (True, False):
            doc = copy.deepcopy(clean_week_one_document)
            target_key = doc["work_items"][0]["key"]
            doc["work_items"][0]["history_complete"] = val

            result = validate_fixture(doc)
            quarantined = [q for q in result.quarantined_records if q.source_key == target_key]
            assert len(quarantined) == 0

    def test_adversarial_non_boolean_structures(
        self,
        clean_week_one_document,
    ):
        """Adversarial values (None, empty string, list, dict) for history_complete must be quarantined."""
        import copy
        from shadow_orbit.validation import validate_fixture

        for bad_val in (None, "", [], {}):
            doc = copy.deepcopy(clean_week_one_document)
            target_key = doc["work_items"][0]["key"]
            doc["work_items"][0]["history_complete"] = bad_val

            result = validate_fixture(doc)
            quarantined = [q for q in result.quarantined_records if q.source_key == target_key]
            assert len(quarantined) == 1, f"Expected {bad_val!r} to be quarantined"
            assert quarantined[0].reason_code == "INVALID_PRIMITIVE_TYPE"

    def test_planned_at_period_start_strict_boolean(
        self,
        clean_week_one_document,
    ):
        """Integer 1 or string 'true' for planned_at_period_start must be quarantined."""
        import copy
        from shadow_orbit.validation import validate_fixture

        for bad_val in (1, 0, "true", "false"):
            doc = copy.deepcopy(clean_week_one_document)
            target_key = doc["work_items"][0]["key"]
            doc["work_items"][0]["planned_at_period_start"] = bad_val

            result = validate_fixture(doc)
            quarantined = [q for q in result.quarantined_records if q.source_key == target_key]
            assert len(quarantined) == 1, f"Expected {bad_val!r} for planned to be quarantined"


# ============================================================================
# P3-04: Chronological Coherence Enforcement
# ============================================================================


class TestP304ChronologicalCoherence:
    """Tests for P3-04 chronological coherence enforcement in validation."""

    def test_updated_before_created_quarantined(
        self,
        clean_week_one_document,
    ):
        """A record where updated_at < created_at must be quarantined with CHRONOLOGICAL_INCOHERENCE."""
        import copy
        from shadow_orbit.validation import validate_fixture

        doc = copy.deepcopy(clean_week_one_document)
        target_key = doc["work_items"][0]["key"]
        doc["work_items"][0]["created_at"] = "2021-05-10T10:00:00Z"
        doc["work_items"][0]["updated_at"] = "2021-05-01T10:00:00Z"

        result = validate_fixture(doc)
        quarantined = [q for q in result.quarantined_records if q.source_key == target_key]
        assert len(quarantined) == 1
        assert quarantined[0].reason_code == "CHRONOLOGICAL_INCOHERENCE"
        assert "precedes created_at" in quarantined[0].reason

    def test_updated_equal_created_accepted(
        self,
        clean_week_one_document,
    ):
        """A record where updated_at == created_at must be accepted."""
        import copy
        from shadow_orbit.validation import validate_fixture

        doc = copy.deepcopy(clean_week_one_document)
        target_key = doc["work_items"][0]["key"]
        doc["work_items"][0]["created_at"] = "2021-05-10T10:00:00Z"
        doc["work_items"][0]["updated_at"] = "2021-05-10T10:00:00Z"

        result = validate_fixture(doc)
        quarantined = [q for q in result.quarantined_records if q.source_key == target_key]
        assert len(quarantined) == 0

    def test_updated_after_created_accepted(
        self,
        clean_week_one_document,
    ):
        """Standard record with updated_at > created_at is accepted."""
        import copy
        from shadow_orbit.validation import validate_fixture

        doc = copy.deepcopy(clean_week_one_document)
        target_key = doc["work_items"][0]["key"]
        doc["work_items"][0]["created_at"] = "2021-05-10T10:00:00Z"
        doc["work_items"][0]["updated_at"] = "2021-05-10T10:01:00Z"

        result = validate_fixture(doc)
        quarantined = [q for q in result.quarantined_records if q.source_key == target_key]
        assert len(quarantined) == 0

    def test_adversarial_microsecond_incoherence(
        self,
        clean_week_one_document,
    ):
        """Even a 1-microsecond backward timestamp must be quarantined."""
        import copy
        from shadow_orbit.validation import validate_fixture

        doc = copy.deepcopy(clean_week_one_document)
        target_key = doc["work_items"][0]["key"]
        doc["work_items"][0]["created_at"] = "2021-05-10T10:00:00.000002Z"
        doc["work_items"][0]["updated_at"] = "2021-05-10T10:00:00.000001Z"

        result = validate_fixture(doc)
        quarantined = [q for q in result.quarantined_records if q.source_key == target_key]
        assert len(quarantined) == 1
        assert quarantined[0].reason_code == "CHRONOLOGICAL_INCOHERENCE"

    def test_adversarial_timezone_offsets(
        self,
        clean_week_one_document,
    ):
        """Chronological comparison must be normalized across differing timezone offsets."""
        import copy
        from shadow_orbit.validation import validate_fixture

        # 12:00:00+05:30 is 06:30:00 UTC.
        # Updated at 07:00:00Z is after created -> Accepted.
        doc1 = copy.deepcopy(clean_week_one_document)
        target_key = doc1["work_items"][0]["key"]
        doc1["work_items"][0]["created_at"] = "2021-05-10T12:00:00+05:30"
        doc1["work_items"][0]["updated_at"] = "2021-05-10T07:00:00Z"

        res1 = validate_fixture(doc1)
        assert len([q for q in res1.quarantined_records if q.source_key == target_key]) == 0

        # Updated at 06:00:00Z is before created (06:30:00 UTC) -> Quarantined.
        doc2 = copy.deepcopy(clean_week_one_document)
        doc2["work_items"][0]["created_at"] = "2021-05-10T12:00:00+05:30"
        doc2["work_items"][0]["updated_at"] = "2021-05-10T06:00:00Z"

        res2 = validate_fixture(doc2)
        quarantined2 = [q for q in res2.quarantined_records if q.source_key == target_key]
        assert len(quarantined2) == 1
        assert quarantined2[0].reason_code == "CHRONOLOGICAL_INCOHERENCE"


# ============================================================================
# P3-08: Measurable Safety Invariant Instrumentation
# ============================================================================


class TestP308ActiveMutationGuard:
    """Tests for P3-08 active runtime mutation guard instrumentation in runner.py."""

    def test_jira_write_attempt_raises_fatal_guard_violation(self):
        """Any attempt to mutate Jira resources through the guard must raise SecurityViolationError."""
        from qualification.mahout.runner import ReadOnlyJiraGuard, SecurityViolationError

        guard = ReadOnlyJiraGuard()
        with pytest.raises(SecurityViolationError, match="unauthorized Jira mutation"):
            guard.record_mutation_attempt("create_issue", project="ORBITLAB")

        assert guard.mutations_attempted == 1

    def test_jira_configuration_write_attempt_raises_fatal_guard_violation(self):
        """Any attempt to mutate Jira configuration through the guard must raise SecurityViolationError."""
        from qualification.mahout.runner import ReadOnlyJiraGuard, SecurityViolationError

        guard = ReadOnlyJiraGuard()
        with pytest.raises(SecurityViolationError, match="unauthorized Jira configuration mutation"):
            guard.record_configuration_mutation_attempt("update_workflow", workflow="ORBIT-WF")

        assert guard.configuration_mutations_attempted == 1

    def test_runner_verifies_zero_mutations_dynamically(self):
        """The qualification runner must execute with active guard and record 0 mutations dynamically."""
        from qualification.mahout.runner import run_mahout_qualification

        result = run_mahout_qualification(save_golden=False)
        assert getattr(result, "mutation_guard_active", False) is True
        assert getattr(result, "jira_mutation_count", -1) == 0
        assert getattr(result, "jira_configuration_mutation_count", -1) == 0

        summary = result.to_summary_dict()
        assert summary.get("mutation_guard_active") is True
        assert summary.get("jira_mutation_count") == 0
        assert summary.get("jira_configuration_mutation_count") == 0




