"""Pure supporting-fact and Week 1 rule evaluation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shadow_orbit.temporal import (
    blocked_since,
    completed_during_period,
    elapsed_complete_days,
    introduced_during_period,
    is_overdue,
    last_meaningful_status_change,
    status_at_period_end,
)
from shadow_orbit.types import (
    NormalizedFixture,
    RuleMatch,
    SuppressedEvaluation,
    WorkItem,
)


_NUMBER_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
    5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
    10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
    14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen",
    18: "eighteen", 19: "nineteen", 20: "twenty",
}


def _number_word(value: int) -> str:
    return _NUMBER_WORDS.get(value, str(value))


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _display_date(value: datetime) -> str:
    return f"{value.day} {value.strftime('%B')}"


def _work_item_by_key(
    fixture: NormalizedFixture,
) -> dict[str, WorkItem]:
    return {item.key: item for item in fixture.work_items}


def calculate_supporting_facts(
    fixture: NormalizedFixture,
) -> dict[str, Any]:
    period = fixture.review_period
    status_mapping = fixture.raw_document["configuration"][
        "status_mapping"
    ]

    planned = sorted(
        item.key
        for item in fixture.work_items
        if item.planned_at_period_start is True
    )

    introduced = sorted(
        item.key
        for item in fixture.work_items
        if introduced_during_period(item, period)
    )

    completed = sorted(
        item.key
        for item in fixture.work_items
        if completed_during_period(item, period)
    )

    planned_completed = sorted(set(planned) & set(completed))

    period_end_states = {
        item.key: status_at_period_end(
            item,
            period,
            status_mapping,
        )
        for item in fixture.work_items
    }

    indeterminate = sorted(
        key
        for key, status in period_end_states.items()
        if status == "unknown"
    )

    known_incomplete = sorted(
        key
        for key, status in period_end_states.items()
        if status in {"todo", "in_progress", "blocked"}
    )

    blocked = sorted(
        item.key
        for item in fixture.work_items
        if item.status_category == "blocked"
    )

    missing_due_dates = sorted(
        item.key
        for item in fixture.work_items
        if item.due_at is None
    )

    return {
        "accepted_work_item_count": len(fixture.work_items),
        "planned_at_period_start_count": len(planned),
        "planned_at_period_start_keys": planned,
        "introduced_during_period_count": len(introduced),
        "introduced_during_period_keys": introduced,
        "completed_during_period_count": len(completed),
        "completed_during_period_keys": completed,
        "planned_completed_during_period_count": len(
            planned_completed
        ),
        "planned_completed_during_period_keys": planned_completed,
        "known_incomplete_at_period_end_count": len(
            known_incomplete
        ),
        "known_incomplete_at_period_end_keys": known_incomplete,
        "indeterminate_at_period_end_count": len(indeterminate),
        "indeterminate_at_period_end_keys": indeterminate,
        "blocked_at_source_cutoff_count": len(blocked),
        "blocked_at_source_cutoff_keys": blocked,
        "missing_due_date_count": len(missing_due_dates),
        "missing_due_date_keys": missing_due_dates,
        "manager_facing_completion_percentage": None,
        "manager_facing_completion_percentage_reason": (
            "The planning basis has not been validated with a real "
            "manager. Counts may be inspected, but no completion "
            "percentage is presented."
        ),
    }


def evaluate_blocked_high_priority(
    item: WorkItem,
    fixture: NormalizedFixture,
) -> RuleMatch | None:
    if item.priority_band != "high":
        return None
    if item.status_category != "blocked":
        return None

    began_at = blocked_since(item)
    review_date = _display_date(
        fixture.review_period.review_cutoff_at
    )

    if began_at is None:
        explanation = (
            f"{item.key} was blocked in the source state used for the "
            f"{review_date} review. ORBIT could not determine when the "
            "blocked condition began."
        )
    else:
        explanation = (
            f"{item.key} has been blocked since "
            f"{_display_date(began_at)} and remained blocked in the "
            f"source state used for the {review_date} review."
        )

    evidence: list[dict[str, str]] = [
        {
            "reference": f"work_item:{item.key}",
            "role": "source_work_item",
        }
    ]
    if began_at is not None:
        evidence.append(
            {
                "reference": (
                    f"change:{item.key}:status:{_iso(began_at)}"
                ),
                "role": "blocked_status_transition",
            }
        )
    evidence.extend(
        [
            {
                "reference": f"field:{item.key}:priority",
                "role": "priority_value",
            },
            {
                "reference": (
                    f"review:{fixture.review_period.label}:"
                    "review_cutoff_at"
                ),
                "role": "evaluation_cutoff",
            },
        ]
    )

    return RuleMatch(
        subject_key=item.key,
        rule_key="BLOCKED_HIGH_PRIORITY",
        rule_version="1",
        observed={
            "priority_band": "high",
            "status_category": "blocked",
        },
        threshold={
            "required_priority_band": "high",
            "required_status_category": "blocked",
        },
        calculation=(
            "priority_band == high AND status_category == blocked "
            "at the source cutoff"
        ),
        deterministic_explanation=explanation,
        evidence_references=tuple(evidence),
    )


def evaluate_overdue_high_priority(
    item: WorkItem,
    fixture: NormalizedFixture,
) -> RuleMatch | SuppressedEvaluation | None:
    if item.priority_band != "high":
        return None
    if item.due_at is None:
        return None

    if item.status_category == "unknown":
        if is_overdue(
            item.due_at,
            fixture.review_period.review_cutoff_at,
        ):
            return SuppressedEvaluation(
                subject_key=item.key,
                rule_key="OVERDUE_HIGH_PRIORITY",
                reason=(
                    "The due date has passed, but the item's completion "
                    "state is unknown because its status is unmapped."
                ),
            )
        return None

    if item.status_category == "done":
        return None

    if not is_overdue(
        item.due_at,
        fixture.review_period.review_cutoff_at,
    ):
        return None

    explanation = (
        f"{item.key} was due on {_display_date(item.due_at)} and "
        f"remained {item.source_status.lower()} in the source state "
        f"used for the "
        f"{_display_date(fixture.review_period.review_cutoff_at)} "
        "review."
    )

    return RuleMatch(
        subject_key=item.key,
        rule_key="OVERDUE_HIGH_PRIORITY",
        rule_version="1",
        observed={
            "priority_band": "high",
            "due_at": _iso(item.due_at),
            "known_complete_at_source_cutoff": False,
        },
        threshold={
            "required_priority_band": "high",
            "due_at_comparison": "due_at < review_cutoff_at",
            "requires_known_incomplete_state": True,
        },
        calculation=(
            "priority_band == high AND due_at < review_cutoff_at "
            "AND work item is known not to be complete in the "
            "source snapshot"
        ),
        deterministic_explanation=explanation,
        evidence_references=(
            {
                "reference": f"work_item:{item.key}",
                "role": "source_work_item",
            },
            {
                "reference": f"field:{item.key}:priority",
                "role": "priority_value",
            },
            {
                "reference": f"field:{item.key}:due_at",
                "role": "due_date",
            },
            {
                "reference": (
                    f"review:{fixture.review_period.label}:"
                    "review_cutoff_at"
                ),
                "role": "evaluation_cutoff",
            },
        ),
    )


def evaluate_stalled_work(
    item: WorkItem,
    fixture: NormalizedFixture,
) -> RuleMatch | SuppressedEvaluation | None:
    if item.status_category != "in_progress":
        return None

    if not item.history_complete:
        return SuppressedEvaluation(
            subject_key=item.key,
            rule_key="STALLED_WORK",
            reason="Relevant status history is incomplete.",
        )

    last_change = last_meaningful_status_change(item)
    if last_change is None:
        return SuppressedEvaluation(
            subject_key=item.key,
            rule_key="STALLED_WORK",
            reason=(
                "A reliable last meaningful status transition "
                "could not be established."
            ),
        )

    threshold = fixture.raw_document["configuration"][
        "stalled_threshold_complete_days"
    ]
    complete_days = elapsed_complete_days(
        last_change,
        fixture.review_period.review_cutoff_at,
    )

    if complete_days <= threshold:
        return None

    explanation = (
        f"{item.key} remained in progress in the source state used "
        "for the review. Its last known relevant status change was "
        f"on {_display_date(last_change)}, more than "
        f"{_number_word(threshold)} complete days before the "
        f"{_display_date(fixture.review_period.review_cutoff_at)} "
        "review cutoff."
    )

    return RuleMatch(
        subject_key=item.key,
        rule_key="STALLED_WORK",
        rule_version="1",
        observed={
            "status_category": "in_progress",
            "elapsed_complete_days": complete_days,
            "history_complete": True,
        },
        threshold={
            "required_status_category": "in_progress",
            "complete_days_comparison": (
                f"elapsed_complete_days > {threshold}"
            ),
            "requires_complete_relevant_history": True,
        },
        calculation=(
            "status_category == in_progress AND history_complete "
            "== true AND floor((review_cutoff_at - "
            "last_meaningful_status_change_at) / 24 hours) "
            f"> {threshold}"
        ),
        deterministic_explanation=explanation,
        evidence_references=(
            {
                "reference": f"work_item:{item.key}",
                "role": "source_work_item",
            },
            {
                "reference": (
                    f"change:{item.key}:status:{_iso(last_change)}"
                ),
                "role": "last_meaningful_status_transition",
            },
            {
                "reference": (
                    f"review:{fixture.review_period.label}:"
                    "review_cutoff_at"
                ),
                "role": "evaluation_cutoff",
            },
        ),
    )


def evaluate_week_one_rules(
    fixture: NormalizedFixture,
) -> tuple[tuple[RuleMatch, ...], tuple[SuppressedEvaluation, ...]]:
    matches: list[RuleMatch] = []
    suppressed: list[SuppressedEvaluation] = []

    evaluators = (
        evaluate_blocked_high_priority,
        evaluate_overdue_high_priority,
        evaluate_stalled_work,
    )

    for item in fixture.work_items:
        for evaluator in evaluators:
            result = evaluator(item, fixture)
            if isinstance(result, RuleMatch):
                matches.append(result)
            elif isinstance(result, SuppressedEvaluation):
                suppressed.append(result)

    matches.sort(key=lambda value: (value.subject_key, value.rule_key))
    suppressed.sort(
        key=lambda value: (value.subject_key, value.rule_key)
    )

    return tuple(matches), tuple(suppressed)
