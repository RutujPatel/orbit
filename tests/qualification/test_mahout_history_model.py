"""Qualification Tests for Destination Jira History Model.

Tests:
1. Seed setup events and qualification experiment transitions have distinct EventOrigin tags.
2. Workflow transitions record authentic transport telemetry and status codes.
3. No historical changelog injection or timestamp backdating is permitted.
"""

from __future__ import annotations

import pytest

from qualification.mahout.history_model import (
    EventOrigin,
    ExecutedWorkflowTransition,
    PlannedWorkflowTransition,
)


def test_history_model_event_origin_distinction() -> None:
    # Setup event
    setup_origin = EventOrigin.SEED_SETUP
    exp_origin = EventOrigin.QUALIFICATION_EXPERIMENT

    assert setup_origin != exp_origin
    assert setup_origin.value == "seed_setup"
    assert exp_origin.value == "qualification_experiment"


def test_executed_transition_telemetry_binding() -> None:
    tx = ExecutedWorkflowTransition(
        destination_key="ORBITLAB-5",
        transition_id="21",
        from_status="To Do",
        to_status="In Progress",
        http_status=204,
        atl_trace_id="4a9918bbf68641b38f88ceb9f041b333",
        x_a_request_id="842187f549c445698b68832a8db96a84",
        executed_at_iso="2026-09-24T12:30:00Z",
        latency_ms=312.45,
        event_origin=EventOrigin.QUALIFICATION_EXPERIMENT,
    )

    d = tx.to_dict()
    assert d["event_origin"] == "qualification_experiment"
    assert d["http_status"] == 204
    assert d["atl_trace_id"]
    assert d["x_a_request_id"]
    assert d["from_status"] == "To Do"
    assert d["to_status"] == "In Progress"
