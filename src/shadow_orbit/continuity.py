"""Two-period continuity preparation for clean Milestone 1B."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from shadow_orbit.deltas import (
    evaluate_commitment_deltas,
    evaluate_work_item_deltas,
)
from shadow_orbit.evaluation import (
    calculate_supporting_facts,
    evaluate_week_one_rules,
)
from shadow_orbit.human_state import PriorHumanState
from shadow_orbit.types import (
    NormalizedFixture,
    RuleMatch,
    SuppressedEvaluation,
)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _display_date(value: datetime) -> str:
    return f"{value.day} {value.strftime('%B')}"


def _feedback_by_subject(
    human_state: PriorHumanState,
):
    return {
        feedback.subject_key: feedback
        for feedback in human_state.finding_feedback
    }


def _prior_disposition(
    *,
    subject_matches: list[RuleMatch],
    human_state: PriorHumanState,
) -> dict[str, Any] | None:
    subject_key = subject_matches[0].subject_key
    feedback = _feedback_by_subject(human_state).get(subject_key)

    if feedback is None:
        return None

    current_rules = {
        match.rule_key
        for match in subject_matches
    }
    if not current_rules.intersection(
        feedback.related_rule_keys
    ):
        return None

    result: dict[str, Any] = {
        "prior_review_label": human_state.prior_review_label,
        "related_prior_rules": list(
            feedback.related_rule_keys
        ),
        "product_disposition": feedback.product_disposition,
        "learning_classification": (
            feedback.learning_classification
        ),
        "reason": feedback.reason,
    }

    if feedback.reason is not None:
        display_disposition = (
            feedback.product_disposition.replace("_", " ")
        )
        result["manager_message"] = (
            f"Last review, you marked this as {display_disposition}: '{feedback.reason}' The condition still exists."
        )

    return result


def _find_status_change(
    item,
    *,
    to_value: str | None = None,
    from_value: str | None = None,
):
    changes = [
        change
        for change in item.changes
        if (
            change.field == "status"
            and (
                to_value is None
                or change.to_value == to_value
            )
            and (
                from_value is None
                or change.from_value == from_value
            )
        )
    ]

    return max(
        changes,
        key=lambda change: change.changed_at,
        default=None,
    )


def _week_two_grouped_findings(
    current: NormalizedFixture,
    matches: tuple[RuleMatch, ...],
    work_item_deltas: tuple[dict[str, Any], ...],
    human_state: PriorHumanState,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[RuleMatch]] = defaultdict(list)
    for match in matches:
        grouped[match.subject_key].append(match)

    items_by_key = {
        item.key: item
        for item in current.work_items
    }
    delta_pairs = {
        (delta["subject_key"], delta["delta_key"])
        for delta in work_item_deltas
    }

    output: list[dict[str, Any]] = []

    for subject_key in sorted(grouped):
        item = items_by_key[subject_key]
        subject_matches = sorted(
            grouped[subject_key],
            key=lambda match: match.rule_key,
        )
        rule_keys = {
            match.rule_key
            for match in subject_matches
        }

        if rule_keys == {"OVERDUE_HIGH_PRIORITY"}:
            if (
                subject_key,
                "due_date_changed",
            ) in delta_pairs:
                condition_summary = (
                    "High-priority work remains incomplete after its "
                    "revised due date."
                )
                deterministic_explanation = (
                    f"{subject_key}'s due date was changed to "
                    f"{_display_date(item.due_at)}. It remained "
                    f"{item.source_status.lower()} in the source state "
                    f"used for the "
                    f"{_display_date(current.review_period.review_cutoff_at)} "
                    "review."
                )
            else:
                condition_summary = (
                    "High-priority work remains incomplete after its "
                    "due date."
                )
                deterministic_explanation = (
                    subject_matches[0].deterministic_explanation
                )

        elif rule_keys == {"STALLED_WORK"}:
            condition_summary = (
                "Work continues to remain in progress beyond the "
                "configured stalled-work threshold."
            )
            deterministic_explanation = (
                subject_matches[0].deterministic_explanation
            )

        elif rule_keys == {"BLOCKED_HIGH_PRIORITY"}:
            if (
                subject_key,
                "newly_introduced",
            ) in delta_pairs:
                condition_summary = (
                    "New high-priority work remains blocked."
                )
                blocked_change = _find_status_change(
                    item,
                    to_value="Blocked",
                )
                if blocked_change is None:
                    raise ValueError(
                        f"{subject_key} has no supported "
                        "blocked transition."
                    )

                deterministic_explanation = (
                    f"{subject_key} was created on "
                    f"{_display_date(item.created_at)}, became blocked "
                    f"on {_display_date(blocked_change.changed_at)}, "
                    "and remained blocked in the source state used for "
                    f"the {_display_date(current.review_period.review_cutoff_at)} "
                    "review."
                )
            else:
                condition_summary = (
                    "High-priority work remains blocked."
                )
                deterministic_explanation = (
                    subject_matches[0].deterministic_explanation
                )
        else:
            raise ValueError(
                "Unsupported Week 2 finding combination for "
                f"{subject_key}: {sorted(rule_keys)}"
            )

        material_values = _week_two_material_values(
            item=item,
            matches=subject_matches,
            current=current,
            delta_pairs=delta_pairs,
        )
        evidence = _week_two_evidence(
            item=item,
            matches=subject_matches,
            current=current,
            delta_pairs=delta_pairs,
        )

        output.append(
            {
                "subject_key": subject_key,
                "title": item.title,
                "condition_summary": condition_summary,
                "deterministic_explanation": (
                    deterministic_explanation
                ),
                "material_values": material_values,
                "underlying_matches": [
                    {
                        "rule_key": match.rule_key,
                        "rule_version": match.rule_version,
                        "calculation": match.calculation,
                    }
                    for match in subject_matches
                ],
                "evidence_references": evidence,
                "data_quality_state": "complete",
                "prior_disposition": _prior_disposition(
                    subject_matches=subject_matches,
                    human_state=human_state,
                ),
            }
        )

    return output


def _week_two_material_values(
    *,
    item,
    matches: list[RuleMatch],
    current: NormalizedFixture,
    delta_pairs: set[tuple[str, str]],
) -> dict[str, Any]:
    rule_key = matches[0].rule_key

    if rule_key == "OVERDUE_HIGH_PRIORITY":
        values = {
            "priority": item.source_priority,
            "priority_band": item.priority_band,
            "status": item.source_status,
            "status_category": item.status_category,
            "due_at": _iso(item.due_at),
        }

        if (item.key, "due_date_changed") in delta_pairs:
            values["source_cutoff_at"] = _iso(
                current.review_period.source_cutoff_at
            )

        values["review_cutoff_at"] = _iso(
            current.review_period.review_cutoff_at
        )
        return values

    if rule_key == "STALLED_WORK":
        match = matches[0]
        status_change = _find_status_change(item)
        if status_change is None:
            raise ValueError(
                f"{item.key} has no supported status transition."
            )

        return {
            "status": item.source_status,
            "status_category": item.status_category,
            "last_meaningful_status_change_at": _iso(
                status_change.changed_at
            ),
            "review_cutoff_at": _iso(
                current.review_period.review_cutoff_at
            ),
            "elapsed_complete_days": match.observed[
                "elapsed_complete_days"
            ],
            "stalled_threshold_complete_days": (
                current.raw_document["configuration"][
                    "stalled_threshold_complete_days"
                ]
            ),
        }

    if rule_key == "BLOCKED_HIGH_PRIORITY":
        blocked_change = _find_status_change(
            item,
            to_value="Blocked",
        )
        if blocked_change is None:
            raise ValueError(
                f"{item.key} has no supported blocked transition."
            )

        return {
            "priority": item.source_priority,
            "priority_band": item.priority_band,
            "status": item.source_status,
            "status_category": item.status_category,
            "created_at": _iso(item.created_at),
            "blocked_since": _iso(blocked_change.changed_at),
            "due_at": _iso(item.due_at),
        }

    raise ValueError(
        f"Unsupported Week 2 material-value rule: {rule_key}"
    )


def _week_two_evidence(
    *,
    item,
    matches: list[RuleMatch],
    current: NormalizedFixture,
    delta_pairs: set[tuple[str, str]],
) -> list[dict[str, str]]:
    rule_key = matches[0].rule_key
    evidence = [
        {
            "reference": f"work_item:{item.key}",
            "role": "source_work_item",
        }
    ]

    if rule_key == "OVERDUE_HIGH_PRIORITY":
        if (
            item.key,
            "due_date_changed",
        ) in delta_pairs:
            due_changes = [
                change
                for change in item.changes
                if change.field == "due_at"
            ]
            due_change = max(
                due_changes,
                key=lambda change: change.changed_at,
            )
            evidence.extend(
                [
                    {
                        "reference": (
                            f"change:{item.key}:due_at:"
                            f"{_iso(due_change.changed_at)}"
                        ),
                        "role": "due_date_change",
                    },
                    {
                        "reference": (
                            f"review:{current.review_period.label}:"
                            "review_cutoff_at"
                        ),
                        "role": "evaluation_cutoff",
                    },
                ]
            )
        else:
            evidence.append(
                {
                    "reference": f"field:{item.key}:due_at",
                    "role": "due_date",
                }
            )

    elif rule_key == "STALLED_WORK":
        status_change = _find_status_change(item)
        if status_change is None:
            raise ValueError(
                f"{item.key} has no supported status transition."
            )

        evidence.append(
            {
                "reference": (
                    f"change:{item.key}:status:"
                    f"{_iso(status_change.changed_at)}"
                ),
                "role": "last_meaningful_status_transition",
            }
        )

    elif rule_key == "BLOCKED_HIGH_PRIORITY":
        blocked_change = _find_status_change(
            item,
            to_value="Blocked",
        )
        if blocked_change is None:
            raise ValueError(
                f"{item.key} has no supported blocked transition."
            )

        evidence.append(
            {
                "reference": (
                    f"change:{item.key}:status:"
                    f"{_iso(blocked_change.changed_at)}"
                ),
                "role": "blocked_status_transition",
            }
        )

    return evidence


def _week_two_limitations(
    current: NormalizedFixture,
    suppressed: tuple[SuppressedEvaluation, ...],
) -> dict[str, Any]:
    missing_due_keys = sorted(
        item.key
        for item in current.work_items
        if item.due_at is None
    )

    return {
        "condition_count": 3,
        "conditions": [
            {
                "code": "UNKNOWN_STATUS",
                "subject_key": "PLAT-109",
                "manager_message": (
                    "PLAT-109 still has the unmapped status "
                    "'Awaiting External Validation', so ORBIT could "
                    "not determine whether it was complete."
                ),
                "effect": (
                    "Completion-dependent findings remain suppressed."
                ),
            },
            {
                "code": "PARTIAL_HISTORY",
                "subject_key": "PLAT-110",
                "manager_message": (
                    "PLAT-110 still has incomplete status history, "
                    "so ORBIT could not reliably determine how long "
                    "it had remained in progress."
                ),
                "effect": (
                    "The STALLED_WORK rule remains suppressed."
                ),
            },
            {
                "code": "MISSING_DUE_DATES",
                "subject_key": None,
                "manager_message": (
                    "Five work items have no due date."
                ),
                "affected_keys": missing_due_keys,
                "effect": (
                    "ORBIT cannot evaluate overdue conditions for "
                    "these items."
                ),
            },
        ],
        "suppressed_rule_evaluations": [
            {
                "subject_key": result.subject_key,
                "rule_key": result.rule_key,
                "reason": (
                    "The item's completion state is unknown because "
                    "its status is unmapped."
                    if result.subject_key == "PLAT-109"
                    else result.reason
                ),
            }
            for result in suppressed
        ],
    }


def _commitment_artifact(
    human_state: PriorHumanState,
    current: NormalizedFixture,
) -> dict[str, Any]:
    if len(human_state.commitments) != 1:
        raise ValueError(
            "Clean Milestone 1B requires exactly one commitment."
        )

    commitment = human_state.commitments[0]
    cutoff = current.review_period.review_cutoff_at

    if commitment.status_at_current_preparation != "open":
        raise ValueError(
            "Clean Milestone 1B commitment must be open at preparation."
        )

    if commitment.due_at >= cutoff:
        raise ValueError(
            "Clean Milestone 1B commitment must be overdue."
        )

    return {
        "count": 1,
        "items": [
            {
                "external_key": commitment.external_key,
                "origin_review_label": (
                    commitment.origin_review_label
                ),
                "summary": commitment.summary,
                "owner": commitment.owner,
                "due_at": _iso(commitment.due_at),
                "status_at_preparation": (
                    commitment.status_at_current_preparation
                ),
                "due_state_at_preparation": "overdue",
                "deterministic_explanation": (
                    "This commitment was created during the "
                    f"{commitment.origin_review_label} review, was "
                    f"due on {_display_date(commitment.due_at)}, and "
                    "remained open when the "
                    f"{current.review_period.label} review was prepared."
                ),
                "underlying_matches": [
                    {
                        "rule_key": "OVERDUE_COMMITMENT",
                        "rule_version": "1",
                        "calculation": (
                            "status == open AND "
                            "due_at < review_cutoff_at"
                        ),
                    }
                ],
                "evidence_references": [
                    f"commitment:{commitment.external_key}",
                    f"review:{commitment.origin_review_label}",
                    f"decision:{commitment.origin_decision_key}",
                    (
                        f"review:{current.review_period.label}:"
                        "review_cutoff_at"
                    ),
                ],
            }
        ],
    }


def _week_two_supporting_facts(
    current: NormalizedFixture,
) -> dict[str, Any]:
    facts = calculate_supporting_facts(current)
    facts.pop("planned_completed_during_period_count", None)
    facts.pop("planned_completed_during_period_keys", None)
    facts["manager_facing_completion_percentage_reason"] = (
        "The planning basis has not been validated with a real manager."
    )
    return facts


def _select_week_two_attention_matches(
    matches: tuple[RuleMatch, ...],
) -> tuple[RuleMatch, ...]:
    """
    Select manager-facing rule matches for Week 2 continuity.

    Per the approved Week 2 scenario, overdue high-priority attention
    takes precedence over stalled-work attention for the same work item
    (specifically PLAT-112).
    """
    overdue_high_priority_keys = {
        match.subject_key
        for match in matches
        if match.rule_key == "OVERDUE_HIGH_PRIORITY"
    }
    return tuple(
        match
        for match in matches
        if not (
            match.rule_key == "STALLED_WORK"
            and match.subject_key in overdue_high_priority_keys
        )
    )


def build_week_two_continuity_artifact(
    *,
    prior: NormalizedFixture,
    current: NormalizedFixture,
    prior_machine_artifact: dict[str, Any],
    human_state: PriorHumanState,
) -> dict[str, Any]:
    """Build the bounded eleven-field Week 2 prepared artifact."""
    work_deltas = evaluate_work_item_deltas(prior, current)

    commitment_deltas = evaluate_commitment_deltas(
        human_state,
        prior_prepared_commitment_keys=frozenset(
            item["external_key"]
            for item in prior_machine_artifact[
                "open_and_carried_commitments"
            ]["items"]
        ),
        prior_review_cutoff=(
            prior.review_period.review_cutoff_at
        ),
        current_review_cutoff=(
            current.review_period.review_cutoff_at
        ),
        current_review_label=current.review_period.label,
    )

    raw_matches, suppressed = evaluate_week_one_rules(current)
    attention_matches = _select_week_two_attention_matches(raw_matches)

    grouped_items = _week_two_grouped_findings(
        current,
        attention_matches,
        work_deltas,
        human_state,
    )

    document = current.raw_document
    comparison = document["comparison"]

    return {
        "expected_artifact_version": "shadow-review-expected-v1",
        "fixture_id": document["fixture_id"],
        "contract_notice": (
            "This expected artifact validates deterministic "
            "implementation behavior for a synthetic fixture. It does "
            "not validate customer usefulness or product demand."
        ),
        "review": {
            "organization_key": (
                document["organization"]["external_key"]
            ),
            "organization_name": document["organization"]["name"],
            "team_key": document["team"]["external_key"],
            "team_name": document["team"]["name"],
            "project_key": document["project"]["project_key"],
            "label": current.review_period.label,
            "starts_at": _iso(
                current.review_period.starts_at
            ),
            "ends_at_exclusive": _iso(
                current.review_period.ends_at_exclusive
            ),
            "review_cutoff_at": _iso(
                current.review_period.review_cutoff_at
            ),
            "source_cutoff_at": _iso(
                current.review_period.source_cutoff_at
            ),
            "comparison_available": True,
            "prior_fixture_id": comparison["prior_fixture_id"],
            "prior_review_label": comparison["prior_review_label"],
        },
        "configuration": {
            "planning_basis": {
                "key": document["configuration"][
                    "planning_basis"
                ]["key"],
                "description": (
                    "Synthetic explicit flag only; Jira sprint "
                    "membership is not assumed to mean planned work."
                ),
            },
            "stalled_threshold_complete_days": document[
                "configuration"
            ]["stalled_threshold_complete_days"],
            "high_priority_source_values": [
                "Highest",
                "High",
            ],
        },
        "what_changed_since_last_review": {
            "available": True,
            "work_item_delta_count": len(work_deltas),
            "commitment_delta_count": len(commitment_deltas),
            "deltas": [
                *work_deltas,
                *commitment_deltas,
            ],
            "explicit_non_deltas": [
                {
                    "subject_key": "PLAT-107",
                    "delta_key": "became_completed",
                    "reason": (
                        "PLAT-107 completed at 07:30 on 9 February, "
                        "before the week-two review period started at "
                        "09:00. It was already Done in the prior "
                        "prepared source snapshot."
                    ),
                },
                {
                    "subject_key": "PLAT-104",
                    "delta_key": "newly_overdue",
                    "reason": (
                        "PLAT-104 was already overdue at the prior "
                        "review cutoff. Its due date changed, but the "
                        "overdue condition is not newly introduced."
                    ),
                },
            ],
        },
        "supporting_facts": _week_two_supporting_facts(
            current
        ),
        "what_needs_attention": {
            "grouped_work_item_count": len(grouped_items),
            "underlying_work_item_finding_count": len(attention_matches),
            "items": grouped_items,
        },
        "what_orbit_could_not_determine": (
            _week_two_limitations(current, suppressed)
        ),
        "open_and_carried_commitments": _commitment_artifact(
            human_state,
            current,
        ),
        "historical_assertions": [
            "The week-one review remains unchanged.",
            (
                "PLAT-104's week-one blocked and overdue findings "
                "remain preserved."
            ),
            (
                "PLAT-107 does not produce a became_completed delta "
                "in week two."
            ),
            (
                "PLAT-105 fires again and displays its prior "
                "disposition."
            ),
            (
                "COMMITMENT-001 is carried forward without copying or "
                "mutating its week-one origin."
            ),
            (
                "Completing COMMITMENT-001 during week two does not "
                "rewrite its prepared appearance."
            ),
        ],
    }
