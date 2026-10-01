"""Destination Jira History Model: Seed Setup vs. Qualification History.

Formalizes the architectural boundary between:
1. Seed Setup Events (EVENT_ORIGIN_SEED_SETUP):
   - Occur when seed issues are initially created in ORBITLAB via POST /rest/api/3/issue.
   - Jira places the issue in its project-configured initial workflow status (e.g. 'To Do').
   - These events are qualification infrastructure setup operations, NOT historical Mahout events.
   - Timestamps reflect the real-time server time of issue creation.

2. Qualification Experiment Transitions (EVENT_ORIGIN_QUALIFICATION_EXPERIMENT):
   - Deliberately executed transition programs using POST /rest/api/3/issue/{key}/transitions.
   - Run through Jira Cloud's genuine workflow engine.
   - Jira's server generates authentic changelog items with its own audit trail, account IDs, and timestamps.
   - Never backdated, never synthesized.

Invariants:
- Zero changelog JSON injection into Jira.
- Zero timestamp backdating or falsification.
- Zero synthetic transport headers or manufactured receipts.
- Clear event origin classification during extraction and qualification analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EventOrigin(str, Enum):
    """Categorization of events recorded in the destination Jira instance."""

    SEED_SETUP = "seed_setup"
    QUALIFICATION_EXPERIMENT = "qualification_experiment"


@dataclass(frozen=True, slots=True)
class PlannedWorkflowTransition:
    """A planned workflow transition to be executed in ORBITLAB."""

    destination_key: str
    from_status: str
    to_status: str
    transition_id: str
    transition_name: str
    execution_order: int
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "destination_key": self.destination_key,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "transition_id": self.transition_id,
            "transition_name": self.transition_name,
            "execution_order": self.execution_order,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class ExecutedWorkflowTransition:
    """Receipt for a workflow transition genuinely executed on Jira Cloud."""

    destination_key: str
    transition_id: str
    from_status: str
    to_status: str
    http_status: int
    atl_trace_id: str
    x_a_request_id: str
    executed_at_iso: str
    latency_ms: float
    event_origin: EventOrigin = EventOrigin.QUALIFICATION_EXPERIMENT

    def to_dict(self) -> dict[str, Any]:
        return {
            "destination_key": self.destination_key,
            "transition_id": self.transition_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "http_status": self.http_status,
            "atl_trace_id": self.atl_trace_id,
            "x_a_request_id": self.x_a_request_id,
            "executed_at_iso": self.executed_at_iso,
            "latency_ms": self.latency_ms,
            "event_origin": self.event_origin.value,
        }
