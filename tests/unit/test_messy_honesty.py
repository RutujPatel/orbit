"""Unit tests for messy-data honesty behaviors.

Each test explains why existing tests do not already prove it.
"""

from __future__ import annotations

from shadow_orbit.evaluation import evaluate_week_one_rules


class TestQuarantineIsolation:
    """Existing tests use clean data with no quarantined records.
    These tests prove quarantined records do not affect messy results.
    """

    def test_quarantined_records_not_in_accepted(
        self, messy_week_one_validated
    ):
        accepted_keys = {
            item["key"]
            for item in messy_week_one_validated.accepted_raw_items
        }
        quarantined_keys = {
            record.source_key
            for record in messy_week_one_validated.quarantined_records
        }
        # OPS-020 (both instances) and OPS-031 must be quarantined
        assert "OPS-020" not in accepted_keys
        assert "OPS-031" not in accepted_keys
        assert "OPS-020" in quarantined_keys
        assert "OPS-031" in quarantined_keys

    def test_exact_quarantine_count(
        self, messy_week_one_validated
    ):
        assert len(messy_week_one_validated.quarantined_records) == 3

    def test_exact_accepted_count(
        self, messy_week_one_validated
    ):
        assert len(messy_week_one_validated.accepted_raw_items) == 29

    def test_quarantined_do_not_affect_findings(
        self, messy_week_one_normalized
    ):
        matches, suppressed = evaluate_week_one_rules(
            messy_week_one_normalized
        )
        finding_keys = {m.subject_key for m in matches}
        suppressed_keys = {s.subject_key for s in suppressed}
        assert "OPS-020" not in finding_keys
        assert "OPS-031" not in finding_keys
        assert "OPS-020" not in suppressed_keys
        assert "OPS-031" not in suppressed_keys


class TestUnknownAndIncompleteStates:
    """Existing tests have clean status and priority mappings.
    These tests prove unmapped and incomplete records are handled.
    """

    def test_unknown_status_normalization(
        self, messy_week_one_normalized
    ):
        ops004 = next(
            item for item in messy_week_one_normalized.work_items
            if item.key == "OPS-004"
        )
        assert ops004.status_category == "unknown"
        assert ops004.source_status == "Awaiting External Validation"

    def test_unknown_priority_normalization(
        self, messy_week_one_normalized
    ):
        ops005 = next(
            item for item in messy_week_one_normalized.work_items
            if item.key == "OPS-005"
        )
        ops019 = next(
            item for item in messy_week_one_normalized.work_items
            if item.key == "OPS-019"
        )
        assert ops005.priority_band == "unknown"
        assert ops005.source_priority == "Urgent-ish"
        assert ops019.priority_band == "unknown"
        assert ops019.source_priority == "Unclear"

    def test_incomplete_history_preserved(
        self, messy_week_one_normalized
    ):
        incomplete_keys = sorted(
            item.key
            for item in messy_week_one_normalized.work_items
            if not item.history_complete
        )
        assert incomplete_keys == [
            "OPS-005", "OPS-006", "OPS-011", "OPS-012",
            "OPS-019", "OPS-021", "OPS-029",
        ]

    def test_planning_null_preserved(
        self, messy_week_one_normalized
    ):
        null_planning_keys = sorted(
            item.key
            for item in messy_week_one_normalized.work_items
            if item.planned_at_period_start is None
        )
        assert null_planning_keys == [
            "OPS-005", "OPS-011", "OPS-012",
            "OPS-019", "OPS-021", "OPS-029",
        ]

    def test_planning_null_not_converted_to_false(
        self, messy_week_one_normalized
    ):
        for item in messy_week_one_normalized.work_items:
            if item.key in (
                "OPS-005", "OPS-011", "OPS-012",
                "OPS-019", "OPS-021", "OPS-029",
            ):
                assert item.planned_at_period_start is None, (
                    f"{item.key} planned_at_period_start should be "
                    f"None, got {item.planned_at_period_start!r}"
                )


class TestInvalidOptionalTimestamp:
    """Existing tests have valid timestamps everywhere.
    This tests that invalid optional timestamps are cleared
    and produce the correct data-quality condition.
    """

    def test_ops025_due_at_cleared(
        self, messy_week_one_normalized
    ):
        ops025 = next(
            item for item in messy_week_one_normalized.work_items
            if item.key == "OPS-025"
        )
        assert ops025.due_at is None

    def test_ops025_invalid_timestamp_condition(
        self, messy_week_one_normalized
    ):
        conditions = [
            c for c in messy_week_one_normalized.data_quality_conditions
            if (
                c.code == "INVALID_OPTIONAL_TIMESTAMP"
                and c.subject_key == "OPS-025"
            )
        ]
        assert len(conditions) == 1


class TestOPS025ArtifactLevelSuppression:
    """Existing evaluator returns None for OPS-025 since due_at is
    cleared to None. This tests that the messy artifact assembler
    produces an explicit artifact-level unevaluable disclosure.
    """

    def test_ops025_not_in_raw_suppressions(
        self, messy_week_one_normalized
    ):
        _, suppressed = evaluate_week_one_rules(
            messy_week_one_normalized
        )
        ops025_suppressions = [
            s for s in suppressed
            if s.subject_key == "OPS-025"
        ]
        assert len(ops025_suppressions) == 0

    def test_ops025_in_artifact_suppressions(
        self, messy_week_one_actual
    ):
        suppressions = messy_week_one_actual[
            "what_orbit_could_not_determine"
        ]["suppressed_rule_evaluations"]
        ops025 = [
            s for s in suppressions
            if s["subject_key"] == "OPS-025"
        ]
        assert len(ops025) == 1
        assert ops025[0]["rule_key"] == "OVERDUE_HIGH_PRIORITY"
        assert "timezone" in ops025[0]["reason"].lower()


class TestStatusCategoryContradiction:
    """Existing tests have consistent status-category metadata.
    This tests that OPS-022's contradiction is detected.
    """

    def test_ops022_contradiction_in_artifact(
        self, messy_week_one_actual
    ):
        conditions = messy_week_one_actual[
            "what_orbit_could_not_determine"
        ]["conditions"]
        contradiction = [
            c for c in conditions
            if c["code"] == "STATUS_CATEGORY_CONTRADICTION"
        ]
        assert len(contradiction) == 1
        assert "OPS-022" in contradiction[0]["subject_keys"]
        assert "Done" in contradiction[0]["message"]
        assert "in_progress" in contradiction[0]["message"]


class TestStaleRecords:
    """Existing tests do not compute staleness. This tests that
    the approved stale-record threshold (>= 14 complete days)
    correctly identifies all 9 stale records.
    """

    def test_stale_records_in_artifact(
        self, messy_week_one_actual
    ):
        conditions = messy_week_one_actual[
            "what_orbit_could_not_determine"
        ]["conditions"]
        stale = [
            c for c in conditions
            if c["code"] == "STALE_SOURCE_RECORD"
        ]
        assert len(stale) == 1
        assert stale[0]["subject_keys"] == [
            "OPS-003", "OPS-005", "OPS-006",
            "OPS-011", "OPS-012", "OPS-019",
            "OPS-021", "OPS-025", "OPS-029",
        ]

    def test_boundary_records_included(
        self, messy_week_one_actual
    ):
        """OPS-003 and OPS-025 are at exactly 14 complete days.
        The approved threshold is >= 14, so they are stale."""
        conditions = messy_week_one_actual[
            "what_orbit_could_not_determine"
        ]["conditions"]
        stale = next(
            c for c in conditions
            if c["code"] == "STALE_SOURCE_RECORD"
        )
        assert "OPS-003" in stale["subject_keys"]
        assert "OPS-025" in stale["subject_keys"]


class TestUnsafeSourceText:
    """Existing tests use safe source text. These tests prove that
    markup and instruction-like text remain inert and are surfaced
    as data-quality conditions.
    """

    def test_ops009_markup_remains_inert(
        self, messy_week_one_normalized
    ):
        ops009 = next(
            item for item in messy_week_one_normalized.work_items
            if item.key == "OPS-009"
        )
        assert "<script>" in ops009.title
        assert ops009.status_category == "todo"

    def test_ops010_instruction_text_remains_inert(
        self, messy_week_one_normalized
    ):
        ops010 = next(
            item for item in messy_week_one_normalized.work_items
            if item.key == "OPS-010"
        )
        assert "ignore previous instructions" in ops010.title.lower()
        assert ops010.priority_band == "high"

    def test_ops009_markup_condition_in_artifact(
        self, messy_week_one_actual
    ):
        conditions = messy_week_one_actual[
            "what_orbit_could_not_determine"
        ]["conditions"]
        markup = [
            c for c in conditions
            if c["code"] == "UNTRUSTED_MARKUP_ESCAPED"
        ]
        assert len(markup) == 1
        assert "OPS-009" in markup[0]["subject_keys"]

    def test_ops010_instruction_condition_in_artifact(
        self, messy_week_one_actual
    ):
        conditions = messy_week_one_actual[
            "what_orbit_could_not_determine"
        ]["conditions"]
        instruction = [
            c for c in conditions
            if c["code"] == "UNTRUSTED_INSTRUCTION_TEXT_PRESERVED"
        ]
        assert len(instruction) == 1
        assert "OPS-010" in instruction[0]["subject_keys"]

    def test_ops010_instruction_does_not_affect_rules(
        self, messy_week_one_normalized
    ):
        """OPS-010 has high priority and is in To Do.
        Its instruction-like title must not change rule behavior."""
        matches, _ = evaluate_week_one_rules(
            messy_week_one_normalized
        )
        ops010_matches = [
            m for m in matches
            if m.subject_key == "OPS-010"
        ]
        # OPS-010 is To Do with no due date, so no findings
        assert len(ops010_matches) == 0


class TestExactFindingsAndSuppressions:
    """Existing tests verify clean findings. These verify the
    exact messy findings and suppressions.
    """

    def test_exact_finding_count(
        self, messy_week_one_actual
    ):
        attention = messy_week_one_actual["what_needs_attention"]
        assert attention["grouped_work_item_count"] == 5
        assert attention["underlying_finding_count"] == 5

    def test_exact_finding_keys(
        self, messy_week_one_actual
    ):
        keys = [
            item["subject_key"]
            for item in messy_week_one_actual[
                "what_needs_attention"
            ]["items"]
        ]
        assert keys == [
            "OPS-001", "OPS-002", "OPS-003",
            "OPS-018", "OPS-028",
        ]

    def test_exact_suppression_count(
        self, messy_week_one_actual
    ):
        suppressions = messy_week_one_actual[
            "what_orbit_could_not_determine"
        ]["suppressed_rule_evaluations"]
        assert len(suppressions) == 9

    def test_exact_suppression_keys_and_rules(
        self, messy_week_one_actual
    ):
        suppressions = messy_week_one_actual[
            "what_orbit_could_not_determine"
        ]["suppressed_rule_evaluations"]
        pairs = [
            (s["subject_key"], s["rule_key"])
            for s in suppressions
        ]
        assert pairs == [
            ("OPS-004", "OVERDUE_HIGH_PRIORITY"),
            ("OPS-005", "STALLED_WORK"),
            ("OPS-006", "STALLED_WORK"),
            ("OPS-011", "STALLED_WORK"),
            ("OPS-012", "STALLED_WORK"),
            ("OPS-019", "STALLED_WORK"),
            ("OPS-021", "STALLED_WORK"),
            ("OPS-025", "OVERDUE_HIGH_PRIORITY"),
            ("OPS-029", "STALLED_WORK"),
        ]
