"""Pure two-period delta evaluation for Milestone 1B."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shadow_orbit.human_state import Commitment, PriorHumanState
from shadow_orbit.temporal import (
    completion_time,
    is_overdue,
    is_within_half_open_period,
)
from shadow_orbit.types import NormalizedFixture, WorkItem


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _display_date(value: datetime) -> str:
    return f"{value.day} {value.strftime('%B')}"


def _items_by_key(
    fixture: NormalizedFixture,
) -> dict[str, WorkItem]:
    return {
        item.key: item
        for item in fixture.work_items
    }


def _known_incomplete(item: WorkItem) -> bool:
    return item.status_category in {
        "todo",
        "in_progress",
        "blocked",
    }


def _known_complete(item: WorkItem) -> bool:
    return item.status_category == "done"


def _status_transition(
    item: WorkItem,
    *,
    after: datetime,
    no_later_than: datetime,
    from_value: str | None = None,
    to_value: str | None = None,
):
    matches = [
        change
        for change in item.changes
        if (
            change.field == "status"
            and change.changed_at > after
            and change.changed_at <= no_later_than
            and (
                from_value is None
                or change.from_value == from_value
            )
            and (
                to_value is None
                or change.to_value == to_value
            )
        )
    ]

    return min(
        matches,
        key=lambda change: change.changed_at,
        default=None,
    )


def evaluate_work_item_deltas(
    prior: NormalizedFixture,
    current: NormalizedFixture,
) -> tuple[dict[str, Any], ...]:
    """Evaluate the six bounded Week 2 work-item delta types."""
    prior_items = _items_by_key(prior)
    current_items = _items_by_key(current)
    deltas: list[dict[str, Any]] = []

    for key in sorted(current_items):
        current_item = current_items[key]
        prior_item = prior_items.get(key)

        if prior_item is None:
            if is_within_half_open_period(
                current_item.created_at,
                current.review_period,
            ):
                deltas.append(
                    {
                        "delta_key": "newly_introduced",
                        "delta_version": "1",
                        "subject_type": "work_item",
                        "subject_key": key,
                        "deterministic_explanation": (
                            f"{key} was created on "
                            f"{_display_date(current_item.created_at)} "
                            "during this review period."
                        ),
                        "previous_values": None,
                        "current_values": {
                            "created_at": _iso(
                                current_item.created_at
                            ),
                            "status": current_item.source_status,
                            "priority": current_item.source_priority,
                        },
                        "evidence_references": [
                            f"work_item:{key}"
                        ],
                    }
                )

            blocked_change = _status_transition(
                current_item,
                to_value="Blocked",
                after=prior.review_period.source_cutoff_at,
                no_later_than=(
                    current.review_period.source_cutoff_at
                ),
            )
            if (
                current_item.status_category == "blocked"
                and blocked_change is not None
            ):
                deltas.append(
                    {
                        "delta_key": "newly_blocked",
                        "delta_version": "1",
                        "subject_type": "work_item",
                        "subject_key": key,
                        "deterministic_explanation": (
                            f"{key} became blocked on "
                            f"{_display_date(blocked_change.changed_at)} "
                            "and remained blocked in the current "
                            "source snapshot."
                        ),
                        "previous_values": {
                            "status": blocked_change.from_value
                        },
                        "current_values": {
                            "status": current_item.source_status,
                            "status_category": "blocked",
                            "blocked_since": _iso(
                                blocked_change.changed_at
                            ),
                        },
                        "evidence_references": [
                            f"work_item:{key}",
                            (
                                f"change:{key}:status:"
                                f"{_iso(blocked_change.changed_at)}"
                            ),
                        ],
                    }
                )

            continue

        completed_at = completion_time(current_item)
        if (
            _known_incomplete(prior_item)
            and _known_complete(current_item)
            and completed_at is not None
            and is_within_half_open_period(
                completed_at,
                current.review_period,
            )
        ):
            deltas.append(
                {
                    "delta_key": "became_completed",
                    "delta_version": "1",
                    "subject_type": "work_item",
                    "subject_key": key,
                    "deterministic_explanation": (
                        f"{key} moved from "
                        f"{prior_item.source_status} to Done on "
                        f"{_display_date(completed_at)} and became "
                        "completed during this review period."
                    ),
                    "previous_values": {
                        "status": prior_item.source_status,
                        "status_category": (
                            prior_item.status_category
                        ),
                    },
                    "current_values": {
                        "status": current_item.source_status,
                        "status_category": (
                            current_item.status_category
                        ),
                        "resolved_at": _iso(completed_at),
                    },
                    "evidence_references": [
                        f"work_item:{key}",
                        (
                            f"change:{key}:status:"
                            f"{_iso(completed_at)}"
                        ),
                    ],
                }
            )

        unblocked_change = _status_transition(
            current_item,
            from_value="Blocked",
            after=prior.review_period.source_cutoff_at,
            no_later_than=current.review_period.source_cutoff_at,
        )
        if (
            prior_item.status_category == "blocked"
            and current_item.status_category
            not in {"blocked", "unknown"}
            and unblocked_change is not None
        ):
            deltas.append(
                {
                    "delta_key": "newly_unblocked",
                    "delta_version": "1",
                    "subject_type": "work_item",
                    "subject_key": key,
                    "deterministic_explanation": (
                        f"{key} changed from Blocked to "
                        f"{current_item.source_status} on "
                        f"{_display_date(unblocked_change.changed_at)} "
                        "and was no longer blocked in the current "
                        "source snapshot."
                    ),
                    "previous_values": {
                        "status": prior_item.source_status,
                        "status_category": (
                            prior_item.status_category
                        ),
                    },
                    "current_values": {
                        "status": current_item.source_status,
                        "status_category": (
                            current_item.status_category
                        ),
                    },
                    "evidence_references": [
                        f"work_item:{key}",
                        (
                            f"change:{key}:status:"
                            f"{_iso(unblocked_change.changed_at)}"
                        ),
                    ],
                }
            )

        if prior_item.due_at != current_item.due_at:
            due_changes = [
                change
                for change in current_item.changes
                if (
                    change.field == "due_at"
                    and change.changed_at
                    > prior.review_period.source_cutoff_at
                    and change.changed_at
                    <= current.review_period.source_cutoff_at
                )
            ]

            if due_changes:
                due_change = min(
                    due_changes,
                    key=lambda change: change.changed_at,
                )

                prior_text = (
                    _display_date(prior_item.due_at)
                    if prior_item.due_at is not None
                    else None
                )
                current_text = (
                    _display_date(current_item.due_at)
                    if current_item.due_at is not None
                    else None
                )

                if prior_text and current_text:
                    explanation = (
                        f"{key}'s due date changed from "
                        f"{prior_text} to {current_text}."
                    )
                elif current_text:
                    explanation = (
                        f"{key} received a due date of "
                        f"{current_text}."
                    )
                else:
                    explanation = (
                        f"{key}'s previous due date of "
                        f"{prior_text} was removed."
                    )

                deltas.append(
                    {
                        "delta_key": "due_date_changed",
                        "delta_version": "1",
                        "subject_type": "work_item",
                        "subject_key": key,
                        "deterministic_explanation": explanation,
                        "previous_values": {
                            "due_at": (
                                _iso(prior_item.due_at)
                                if prior_item.due_at is not None
                                else None
                            )
                        },
                        "current_values": {
                            "due_at": (
                                _iso(current_item.due_at)
                                if current_item.due_at is not None
                                else None
                            )
                        },
                        "evidence_references": [
                            f"work_item:{key}",
                            (
                                f"change:{key}:due_at:"
                                f"{_iso(due_change.changed_at)}"
                            ),
                        ],
                    }
                )

        prior_overdue = (
            prior_item.due_at is not None
            and _known_incomplete(prior_item)
            and is_overdue(
                prior_item.due_at,
                prior.review_period.review_cutoff_at,
            )
        )
        current_overdue = (
            current_item.due_at is not None
            and _known_incomplete(current_item)
            and is_overdue(
                current_item.due_at,
                current.review_period.review_cutoff_at,
            )
        )

        if not prior_overdue and current_overdue:
            deltas.append(
                {
                    "delta_key": "newly_overdue",
                    "delta_version": "1",
                    "subject_type": "work_item",
                    "subject_key": key,
                    "deterministic_explanation": (
                        f"{key} was not overdue at the previous "
                        "review cutoff. Its due date passed on "
                        f"{_display_date(current_item.due_at)}, "
                        "and it remained incomplete in the current "
                        "source snapshot."
                    ),
                    "previous_values": {
                        "due_at": (
                            _iso(prior_item.due_at)
                            if prior_item.due_at is not None
                            else None
                        ),
                        "was_overdue_at_prior_review_cutoff": False,
                    },
                    "current_values": {
                        "due_at": _iso(current_item.due_at),
                        "is_overdue_at_current_review_cutoff": True,
                        "status": current_item.source_status,
                    },
                    "evidence_references": [
                        f"work_item:{key}",
                        (
                            f"review:{prior.review_period.label}:"
                            "review_cutoff_at"
                        ),
                        (
                            f"review:{current.review_period.label}:"
                            "review_cutoff_at"
                        ),
                    ],
                }
            )

    order = {
        "became_completed": 0,
        "newly_unblocked": 1,
        "due_date_changed": 2,
        "newly_overdue": 3,
        "newly_introduced": 4,
        "newly_blocked": 5,
    }

    deltas.sort(
        key=lambda delta: (
            order[delta["delta_key"]],
            delta["subject_key"],
        )
    )

    return tuple(deltas)


def evaluate_commitment_deltas(
    human_state: PriorHumanState,
    *,
    prior_prepared_commitment_keys: frozenset[str],
    prior_review_cutoff: datetime,
    current_review_cutoff: datetime,
    current_review_label: str,
) -> tuple[dict[str, Any], ...]:
    """Evaluate the three bounded commitment continuity deltas."""
    deltas: list[dict[str, Any]] = []

    for commitment in human_state.commitments:
        if (
            commitment.external_key
            not in prior_prepared_commitment_keys
        ):
            deltas.append(
                _commitment_created_delta(commitment)
            )

        if (
            commitment.status_at_current_preparation == "open"
            and prior_review_cutoff <= commitment.due_at
            < current_review_cutoff
        ):
            deltas.append(
                _commitment_newly_overdue_delta(
                    commitment,
                    current_review_cutoff=current_review_cutoff,
                    current_review_label=current_review_label,
                )
            )

        if commitment.status_at_current_preparation == "open":
            deltas.append(
                _commitment_still_open_delta(commitment)
            )

    order = {
        "commitment_created": 0,
        "commitment_newly_overdue": 1,
        "commitment_still_open": 2,
    }

    deltas.sort(
        key=lambda delta: (
            order[delta["delta_key"]],
            delta["subject_key"],
        )
    )

    return tuple(deltas)


def _commitment_created_delta(
    commitment: Commitment,
) -> dict[str, Any]:
    return {
        "delta_key": "commitment_created",
        "delta_version": "1",
        "subject_type": "commitment",
        "subject_key": commitment.external_key,
        "semantic_definition": (
            "The commitment was absent from the prior prepared review "
            "and is present in the current prepared review, with its "
            "historical origin and creation metadata preserved."
        ),
        "deterministic_explanation": (
            f"{commitment.external_key} was absent from the prior "
            "prepared review and first appears in the current prepared "
            f"review. It originated during the "
            f"{commitment.origin_review_label} review and was created "
            f"on {_display_date(commitment.created_at)}."
        ),
        "previous_values": None,
        "current_values": {
            "origin_review_label": commitment.origin_review_label,
            "created_at": _iso(commitment.created_at),
            "status": commitment.status_at_current_preparation,
        },
        "evidence_references": [
            f"commitment:{commitment.external_key}",
            f"review:{commitment.origin_review_label}",
        ],
    }


def _commitment_newly_overdue_delta(
    commitment: Commitment,
    *,
    current_review_cutoff: datetime,
    current_review_label: str,
) -> dict[str, Any]:
    return {
        "delta_key": "commitment_newly_overdue",
        "delta_version": "1",
        "subject_type": "commitment",
        "subject_key": commitment.external_key,
        "deterministic_explanation": (
            "The commitment was due on "
            f"{_display_date(commitment.due_at)} and remained open at "
            f"the {_display_date(current_review_cutoff)} review cutoff."
        ),
        "previous_values": {
            "was_overdue_at_prior_review_cutoff": False
        },
        "current_values": {
            "due_at": _iso(commitment.due_at),
            "status": commitment.status_at_current_preparation,
            "is_overdue_at_current_review_cutoff": True,
        },
        "evidence_references": [
            f"commitment:{commitment.external_key}",
            f"review:{current_review_label}:review_cutoff_at",
        ],
    }


def _commitment_still_open_delta(
    commitment: Commitment,
) -> dict[str, Any]:
    return {
        "delta_key": "commitment_still_open",
        "delta_version": "1",
        "subject_type": "commitment",
        "subject_key": commitment.external_key,
        "deterministic_explanation": (
            "The commitment remained open when the week-two review "
            "was prepared."
        ),
        "previous_values": {
            "status": commitment.status_at_prior_review_completion
        },
        "current_values": {
            "status": commitment.status_at_current_preparation
        },
        "evidence_references": [
            f"commitment:{commitment.external_key}"
        ],
    }
