"""Regression tests for the due-at-None crash and status-mapping propagation."""

from __future__ import annotations


def test_week_two_blocked_high_priority_with_no_due_date(
    clean_week_one_actual,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_human_state,
):
    """A blocked/high-priority item with due_at=None must not crash continuity.

    PLAT-113 in Week 2 is blocked/highest but the fixture gives it a due date.
    This test removes due_at to trigger the _iso(None) crash in
    continuity.py's _week_two_material_values BLOCKED_HIGH_PRIORITY path.
    """
    from dataclasses import replace
    from shadow_orbit.continuity import build_week_two_continuity_artifact

    plat_113 = next(
        item
        for item in clean_week_two_normalized.work_items
        if item.key == "PLAT-113"
    )
    # Remove the due date — this is the trigger for the crash.
    updated_113 = replace(plat_113, due_at=None)
    updated_items = tuple(
        updated_113 if item.key == "PLAT-113" else item
        for item in clean_week_two_normalized.work_items
    )
    current = replace(clean_week_two_normalized, work_items=updated_items)

    artifact = build_week_two_continuity_artifact(
        prior=clean_week_one_normalized,
        current=current,
        prior_machine_artifact=clean_week_one_actual,
        human_state=clean_week_one_human_state,
    )

    # The finding must still be emitted.
    attention_113 = next(
        item
        for item in artifact["what_needs_attention"]["items"]
        if item["subject_key"] == "PLAT-113"
    )
    assert attention_113["subject_key"] == "PLAT-113"
    # due_at must be None in the material values, not fabricated.
    assert attention_113["material_values"]["due_at"] is None


def test_blocked_since_uses_status_mapping_through_evaluator(
    clean_week_one_normalized,
):
    """blocked_since() must use the configured status_mapping, not hardcoded 'Blocked'.

    This test replaces the provider vocabulary: instead of 'Blocked' → 'blocked',
    the mapping uses 'On Hold' → 'blocked'. The work item's status and change
    history use 'On Hold'. The evaluator must still detect the blocked condition
    and determine when the blocked state began.
    """
    from copy import deepcopy
    from dataclasses import replace
    from datetime import datetime, timezone
    from shadow_orbit.evaluation import evaluate_week_one_rules
    from shadow_orbit.types import Change

    # Build an alternative status_mapping where blocked is "On Hold" not "Blocked".
    alt_doc = deepcopy(clean_week_one_normalized.raw_document)
    alt_doc["configuration"]["status_mapping"] = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "On Hold": "blocked",
        "Done": "done",
    }

    # Create a high-priority blocked item using the alternative vocabulary.
    blocked_item = next(
        item
        for item in clean_week_one_normalized.work_items
        if item.key == "PLAT-104"
    )
    blocked_at = datetime(2026, 1, 20, 10, 0, tzinfo=timezone.utc)
    alt_item = replace(
        blocked_item,
        source_status="On Hold",
        status_category="blocked",
        changes=(
            Change(
                field="status",
                from_value="In Progress",
                to_value="On Hold",
                changed_at=blocked_at,
            ),
        ),
    )
    updated_items = tuple(
        alt_item if item.key == "PLAT-104" else item
        for item in clean_week_one_normalized.work_items
    )
    fixture = replace(
        clean_week_one_normalized,
        raw_document=alt_doc,
        work_items=updated_items,
    )

    matches, _ = evaluate_week_one_rules(fixture)

    blocked_match = next(
        (
            match
            for match in matches
            if match.subject_key == "PLAT-104"
            and match.rule_key == "BLOCKED_HIGH_PRIORITY"
        ),
        None,
    )
    assert blocked_match is not None, (
        "BLOCKED_HIGH_PRIORITY must fire for an item with status_category='blocked' "
        "even when the provider string is 'On Hold' instead of 'Blocked'."
    )

    # The explanation must include the blocked-since date, not the fallback.
    assert "20 January" in blocked_match.deterministic_explanation, (
        "blocked_since() must detect the 'On Hold' transition via status_mapping "
        "and include the blocked-since date in the explanation. "
        f"Got: {blocked_match.deterministic_explanation}"
    )


def test_completion_time_uses_status_mapping_through_deltas(
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    """completion_time() must use the configured status_mapping, not hardcoded 'Done'.

    This test replaces the provider vocabulary: instead of 'Done' → 'done',
    the mapping uses 'Completed' → 'done'. The item transitions from
    'In Progress' to 'Completed' during the review period. The delta evaluator
    must still emit a became_completed delta.
    """
    from copy import deepcopy
    from dataclasses import replace
    from datetime import datetime, timezone
    from shadow_orbit.deltas import evaluate_work_item_deltas
    from shadow_orbit.types import Change

    # Build alternative fixtures with "Completed" → "done" mapping.
    alt_doc_prior = deepcopy(clean_week_one_normalized.raw_document)
    alt_doc_prior["configuration"]["status_mapping"] = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "On Hold": "blocked",
        "Completed": "done",
    }
    alt_doc_current = deepcopy(clean_week_two_normalized.raw_document)
    alt_doc_current["configuration"]["status_mapping"] = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "On Hold": "blocked",
        "Completed": "done",
    }

    # PLAT-105 in week 1 is in_progress. Make it transition to "Completed"
    # during the week 2 period.
    prior_105 = next(
        item
        for item in clean_week_one_normalized.work_items
        if item.key == "PLAT-105"
    )
    current_105 = next(
        item
        for item in clean_week_two_normalized.work_items
        if item.key == "PLAT-105"
    )
    completed_at = datetime(2026, 2, 12, 14, 0, tzinfo=timezone.utc)

    alt_current_105 = replace(
        current_105,
        source_status="Completed",
        status_category="done",
        resolved_at=None,
        changes=current_105.changes + (
            Change(
                field="status",
                from_value="In Progress",
                to_value="Completed",
                changed_at=completed_at,
            ),
        ),
    )

    prior_items = tuple(
        item for item in clean_week_one_normalized.work_items
    )
    current_items = tuple(
        alt_current_105 if item.key == "PLAT-105" else item
        for item in clean_week_two_normalized.work_items
    )

    prior = replace(
        clean_week_one_normalized,
        raw_document=alt_doc_prior,
        work_items=prior_items,
    )
    current = replace(
        clean_week_two_normalized,
        raw_document=alt_doc_current,
        work_items=current_items,
    )

    deltas = evaluate_work_item_deltas(prior, current)

    completed_delta = next(
        (
            d
            for d in deltas
            if d["subject_key"] == "PLAT-105"
            and d["delta_key"] == "became_completed"
        ),
        None,
    )
    assert completed_delta is not None, (
        "A became_completed delta must be emitted when the item transitions "
        "to 'Completed' and the status_mapping maps 'Completed' → 'done'. "
        f"Got deltas: {[d['delta_key'] + ':' + d['subject_key'] for d in deltas]}"
    )


def test_completed_during_period_uses_status_mapping_in_supporting_facts(
    clean_week_one_normalized,
):
    """completed_during_period() in calculate_supporting_facts must use status_mapping."""
    from copy import deepcopy
    from dataclasses import replace
    from datetime import datetime, timezone
    from shadow_orbit.evaluation import calculate_supporting_facts
    from shadow_orbit.types import Change

    alt_doc = deepcopy(clean_week_one_normalized.raw_document)
    alt_doc["configuration"]["status_mapping"] = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "Blocked": "blocked",
        "Shipped": "done",
    }

    # PLAT-101 completed during the period using "Shipped" instead of "Done"
    completed_at = datetime(2026, 2, 5, 12, 0, tzinfo=timezone.utc)
    plat_101 = next(
        item
        for item in clean_week_one_normalized.work_items
        if item.key == "PLAT-101"
    )
    alt_101 = replace(
        plat_101,
        source_status="Shipped",
        status_category="done",
        resolved_at=None,
        changes=(
            Change(
                field="status",
                from_value="In Progress",
                to_value="Shipped",
                changed_at=completed_at,
            ),
        ),
    )
    updated_items = tuple(
        alt_101 if item.key == "PLAT-101" else item
        for item in clean_week_one_normalized.work_items
    )
    fixture = replace(
        clean_week_one_normalized,
        raw_document=alt_doc,
        work_items=updated_items,
    )

    facts = calculate_supporting_facts(fixture)
    assert "PLAT-101" in facts["completed_during_period_keys"], (
        "PLAT-101 should be counted in completed_during_period_keys when using 'Shipped' -> 'done'"
    )


def test_status_transition_newly_blocked_uses_status_mapping(
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    """_status_transition() in deltas.py must use status_mapping for newly_blocked."""
    from copy import deepcopy
    from dataclasses import replace
    from datetime import datetime, timezone
    from shadow_orbit.deltas import evaluate_work_item_deltas
    from shadow_orbit.types import Change

    alt_doc_prior = deepcopy(clean_week_one_normalized.raw_document)
    alt_doc_prior["configuration"]["status_mapping"] = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "On Hold": "blocked",
        "Done": "done",
    }
    alt_doc_current = deepcopy(clean_week_two_normalized.raw_document)
    alt_doc_current["configuration"]["status_mapping"] = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "On Hold": "blocked",
        "Done": "done",
    }

    # PLAT-113 is introduced in week 2 (created 2026-02-12, not in prior).
    # It transitions from "To Do" to "On Hold" on 2026-02-14.
    plat_113 = next(
        item for item in clean_week_two_normalized.work_items if item.key == "PLAT-113"
    )
    blocked_at = datetime(2026, 2, 14, 13, 0, tzinfo=timezone.utc)
    alt_113 = replace(
        plat_113,
        source_status="On Hold",
        status_category="blocked",
        changes=(
            Change(
                field="status",
                from_value="To Do",
                to_value="On Hold",
                changed_at=blocked_at,
            ),
        ),
    )

    prior = replace(
        clean_week_one_normalized,
        raw_document=alt_doc_prior,
    )
    current_items = tuple(
        alt_113 if item.key == "PLAT-113" else item
        for item in clean_week_two_normalized.work_items
    )
    current = replace(
        clean_week_two_normalized,
        raw_document=alt_doc_current,
        work_items=current_items,
    )

    deltas = evaluate_work_item_deltas(prior, current)
    newly_blocked = next(
        (
            d
            for d in deltas
            if d["subject_key"] == "PLAT-113" and d["delta_key"] == "newly_blocked"
        ),
        None,
    )
    assert newly_blocked is not None, (
        "newly_blocked delta must be emitted for an item that transitioned to 'On Hold' "
        f"with status_mapping {{'On Hold': 'blocked'}}. Emitted deltas: {[d['delta_key'] + ':' + d['subject_key'] for d in deltas]}"
    )
    assert newly_blocked["current_values"]["status"] == "On Hold"
    assert newly_blocked["current_values"]["status_category"] == "blocked"


def test_status_transition_newly_unblocked_uses_status_mapping(
    clean_week_one_normalized,
    clean_week_two_normalized,
):
    """_status_transition() in deltas.py must use status_mapping for newly_unblocked."""
    from copy import deepcopy
    from dataclasses import replace
    from datetime import datetime, timezone
    from shadow_orbit.deltas import evaluate_work_item_deltas
    from shadow_orbit.types import Change

    alt_doc_prior = deepcopy(clean_week_one_normalized.raw_document)
    alt_doc_prior["configuration"]["status_mapping"] = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "On Hold": "blocked",
        "Done": "done",
    }
    alt_doc_current = deepcopy(clean_week_two_normalized.raw_document)
    alt_doc_current["configuration"]["status_mapping"] = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "On Hold": "blocked",
        "Done": "done",
    }

    # In prior (week 1), PLAT-104 is on hold (blocked).
    plat_104_prior = next(
        item for item in clean_week_one_normalized.work_items if item.key == "PLAT-104"
    )
    alt_104_prior = replace(
        plat_104_prior,
        source_status="On Hold",
        status_category="blocked",
    )
    prior_items = tuple(
        alt_104_prior if item.key == "PLAT-104" else item
        for item in clean_week_one_normalized.work_items
    )
    prior = replace(
        clean_week_one_normalized,
        raw_document=alt_doc_prior,
        work_items=prior_items,
    )

    # In current (week 2), PLAT-104 changed from "On Hold" to "In Progress" on 2026-02-09.
    plat_104_current = next(
        item for item in clean_week_two_normalized.work_items if item.key == "PLAT-104"
    )
    unblocked_at = datetime(2026, 2, 9, 10, 0, tzinfo=timezone.utc)
    alt_104_current = replace(
        plat_104_current,
        source_status="In Progress",
        status_category="in_progress",
        changes=(
            Change(
                field="status",
                from_value="On Hold",
                to_value="In Progress",
                changed_at=unblocked_at,
            ),
        ),
    )
    current_items = tuple(
        alt_104_current if item.key == "PLAT-104" else item
        for item in clean_week_two_normalized.work_items
    )
    current = replace(
        clean_week_two_normalized,
        raw_document=alt_doc_current,
        work_items=current_items,
    )

    deltas = evaluate_work_item_deltas(prior, current)
    newly_unblocked = next(
        (
            d
            for d in deltas
            if d["subject_key"] == "PLAT-104" and d["delta_key"] == "newly_unblocked"
        ),
        None,
    )
    assert newly_unblocked is not None, (
        "newly_unblocked delta must be emitted when item transitioned from 'On Hold' "
        f"with status_mapping {{'On Hold': 'blocked'}}. Emitted deltas: {[d['delta_key'] + ':' + d['subject_key'] for d in deltas]}"
    )


def test_continuity_find_status_change_uses_status_mapping(
    clean_week_one_actual,
    clean_week_one_normalized,
    clean_week_two_normalized,
    clean_week_one_human_state,
):
    """_find_status_change() in continuity.py must use status_mapping for BLOCKED_HIGH_PRIORITY."""
    from copy import deepcopy
    from dataclasses import replace
    from datetime import datetime, timezone
    from shadow_orbit.continuity import build_week_two_continuity_artifact
    from shadow_orbit.types import Change

    alt_doc_prior = deepcopy(clean_week_one_normalized.raw_document)
    alt_doc_prior["configuration"]["status_mapping"] = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "On Hold": "blocked",
        "Done": "done",
    }
    alt_doc_current = deepcopy(clean_week_two_normalized.raw_document)
    alt_doc_current["configuration"]["status_mapping"] = {
        "To Do": "todo",
        "In Progress": "in_progress",
        "On Hold": "blocked",
        "Done": "done",
    }

    # PLAT-113 is introduced in week 2 and transitions from "To Do" to "On Hold"
    plat_113 = next(
        item for item in clean_week_two_normalized.work_items if item.key == "PLAT-113"
    )
    blocked_at = datetime(2026, 2, 14, 13, 0, tzinfo=timezone.utc)
    alt_113 = replace(
        plat_113,
        source_status="On Hold",
        status_category="blocked",
        changes=(
            Change(
                field="status",
                from_value="To Do",
                to_value="On Hold",
                changed_at=blocked_at,
            ),
        ),
    )

    prior = replace(
        clean_week_one_normalized,
        raw_document=alt_doc_prior,
    )
    current_items = tuple(
        alt_113 if item.key == "PLAT-113" else item
        for item in clean_week_two_normalized.work_items
    )
    current = replace(
        clean_week_two_normalized,
        raw_document=alt_doc_current,
        work_items=current_items,
    )

    artifact = build_week_two_continuity_artifact(
        prior=prior,
        current=current,
        prior_machine_artifact=clean_week_one_actual,
        human_state=clean_week_one_human_state,
    )

    attention_113 = next(
        item
        for item in artifact["what_needs_attention"]["items"]
        if item["subject_key"] == "PLAT-113"
    )

    # 1. Explanation must include transition date, not fallback
    assert "became blocked on 14 February" in attention_113["deterministic_explanation"], (
        "Explanation must use transition date for 'On Hold' transition, not fallback. "
        f"Got: {attention_113['deterministic_explanation']}"
    )

    # 2. Material values must record blocked_since
    assert (
        attention_113["material_values"]["blocked_since"] == "2026-02-14T13:00:00Z"
    ), f"blocked_since must be recorded, got {attention_113['material_values']['blocked_since']}"

    # 3. Evidence must include blocked_status_transition
    roles = [ref["role"] for ref in attention_113["evidence_references"]]
    assert "blocked_status_transition" in roles, (
        f"Evidence references must include blocked_status_transition role. Got roles: {roles}"
    )


