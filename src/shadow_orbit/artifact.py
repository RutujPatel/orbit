"""Assemble the machine-derived clean Week 1 prepared-review artifact."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from shadow_orbit.evaluation import (
    calculate_supporting_facts,
    evaluate_week_one_rules,
)
from shadow_orbit.types import (
    NormalizedFixture,
    RuleMatch,
    SuppressedEvaluation,
)


_NUMBER_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
    5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
    10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
    14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen",
    18: "eighteen", 19: "nineteen", 20: "twenty",
}


def _number_word(value: int, *, capitalize: bool = False) -> str:
    word = _NUMBER_WORDS.get(value, str(value))
    return word.capitalize() if capitalize else word


_MACHINE_DERIVED_TOP_LEVEL_FIELDS = (
    "expected_artifact_version",
    "fixture_id",
    "contract_notice",
    "review",
    "configuration",
    "what_changed_since_last_review",
    "supporting_facts",
    "what_needs_attention",
    "what_orbit_could_not_determine",
    "open_and_carried_commitments",
    "historical_assertions",
)


def machine_derived_projection(
    artifact: dict[str, Any],
) -> dict[str, Any]:
    """
    Select the explicit machine-derived acceptance boundary.

    Human-entered state is intentionally excluded. This function does not
    delete arbitrary keys; it positively selects the approved boundary.
    """
    missing = [
        key
        for key in _MACHINE_DERIVED_TOP_LEVEL_FIELDS
        if key not in artifact
    ]
    if missing:
        raise ValueError(
            f"Artifact is missing machine-derived fields: {missing}"
        )

    return {
        key: artifact[key]
        for key in _MACHINE_DERIVED_TOP_LEVEL_FIELDS
    }


def _group_summary(matches: list[RuleMatch]) -> str:
    keys = {match.rule_key for match in matches}

    if keys == {
        "BLOCKED_HIGH_PRIORITY",
        "OVERDUE_HIGH_PRIORITY",
    }:
        return (
            "High-priority work remains blocked and is past its "
            "due date."
        )
    if keys == {"BLOCKED_HIGH_PRIORITY"}:
        return "High-priority work remains blocked."
    if keys == {"OVERDUE_HIGH_PRIORITY"}:
        return (
            "High-priority work remains incomplete after its due date."
        )
    if keys == {"STALLED_WORK"}:
        return (
            "Work has remained in progress without a relevant status "
            "change for longer than the configured threshold."
        )

    raise ValueError(f"Unsupported Week 1 finding combination: {keys}")


def _combined_explanation(
    subject_key: str,
    matches: list[RuleMatch],
    fixture: NormalizedFixture,
) -> str:
    item = next(
        value
        for value in fixture.work_items
        if value.key == subject_key
    )
    keys = {match.rule_key for match in matches}

    if keys == {
        "BLOCKED_HIGH_PRIORITY",
        "OVERDUE_HIGH_PRIORITY",
    }:
        blocked_change = next(
            change
            for change in item.changes
            if (
                change.field == "status"
                and change.to_value == "Blocked"
            )
        )

        return (
            f"{item.key} has been blocked since "
            f"{blocked_change.changed_at.day} "
            f"{blocked_change.changed_at.strftime('%B')} and was due "
            f"on {item.due_at.day} {item.due_at.strftime('%B')}. It "
            "remained blocked in the source state used for the "
            f"{fixture.review_period.review_cutoff_at.day} "
            f"{fixture.review_period.review_cutoff_at.strftime('%B')} "
            "review."
        )

    return matches[0].deterministic_explanation


def _material_values(
    subject_key: str,
    matches: list[RuleMatch],
    fixture: NormalizedFixture,
) -> dict[str, Any]:
    item = next(
        value
        for value in fixture.work_items
        if value.key == subject_key
    )

    def iso(value):
        return (
            value.isoformat().replace("+00:00", "Z")
            if value is not None
            else None
        )

    keys = {match.rule_key for match in matches}

    if keys == {
        "BLOCKED_HIGH_PRIORITY",
        "OVERDUE_HIGH_PRIORITY",
    }:
        blocked_change = next(
            change
            for change in item.changes
            if change.field == "status" and change.to_value == "Blocked"
        )
        return {
            "priority": item.source_priority,
            "priority_band": item.priority_band,
            "status": item.source_status,
            "status_category": item.status_category,
            "blocked_since": iso(blocked_change.changed_at),
            "due_at": iso(item.due_at),
            "source_cutoff_at": iso(
                fixture.review_period.source_cutoff_at
            ),
            "review_cutoff_at": iso(
                fixture.review_period.review_cutoff_at
            ),
        }

    if keys == {"STALLED_WORK"}:
        match = matches[0]
        transition = next(
            change
            for change in item.changes
            if change.field == "status"
        )
        elapsed_seconds = int(
            (
                fixture.review_period.review_cutoff_at
                - transition.changed_at
            ).total_seconds()
        )
        return {
            "status": item.source_status,
            "status_category": item.status_category,
            "last_meaningful_status_change_at": iso(
                transition.changed_at
            ),
            "review_cutoff_at": iso(
                fixture.review_period.review_cutoff_at
            ),
            "elapsed_seconds": elapsed_seconds,
            "elapsed_complete_days": match.observed[
                "elapsed_complete_days"
            ],
            "stalled_threshold_complete_days": (
                fixture.raw_document["configuration"][
                    "stalled_threshold_complete_days"
                ]
            ),
        }

    raise ValueError(f"Unsupported material values for {keys}")


def _group_findings(
    fixture: NormalizedFixture,
    matches: tuple[RuleMatch, ...],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[RuleMatch]] = defaultdict(list)
    for match in matches:
        grouped[match.subject_key].append(match)

    items_by_key = {item.key: item for item in fixture.work_items}
    output: list[dict[str, Any]] = []

    for subject_key in sorted(grouped):
        subject_matches = sorted(
            grouped[subject_key],
            key=lambda match: match.rule_key,
        )
        item = items_by_key[subject_key]

        evidence: list[dict[str, str]] = []
        seen_references: set[tuple[str, str]] = set()

        for match in subject_matches:
            for reference in match.evidence_references:
                identity = (
                    reference["reference"],
                    reference["role"],
                )
                if identity not in seen_references:
                    evidence.append(dict(reference))
                    seen_references.add(identity)

        evidence_role_order = {
            "source_work_item": 0,
            "blocked_status_transition": 1,
            "last_meaningful_status_transition": 1,
            "priority_value": 2,
            "due_date": 3,
            "evaluation_cutoff": 4,
        }
        evidence.sort(
            key=lambda reference: (
                evidence_role_order.get(reference["role"], 99),
                reference["reference"],
            )
        )

        output.append(
            {
                "subject_key": subject_key,
                "title": item.title,
                "condition_summary": _group_summary(subject_matches),
                "deterministic_explanation": _combined_explanation(
                    subject_key,
                    subject_matches,
                    fixture,
                ),
                "material_values": _material_values(
                    subject_key,
                    subject_matches,
                    fixture,
                ),
                "underlying_matches": [
                    {
                        "rule_key": match.rule_key,
                        "rule_version": match.rule_version,
                        "observed": match.observed,
                        "threshold": match.threshold,
                        "calculation": match.calculation,
                    }
                    for match in subject_matches
                ],
                "evidence_references": evidence,
                "data_quality_state": "complete",
                "prior_disposition": None,
            }
        )

    return output


def _limitations(
    fixture: NormalizedFixture,
    suppressed: tuple[SuppressedEvaluation, ...],
) -> dict[str, Any]:
    missing_due_keys = sorted(
        item.key for item in fixture.work_items if item.due_at is None
    )

    return {
        "condition_count": 3,
        "conditions": [
            {
                "code": "UNKNOWN_STATUS",
                "subject_key": "PLAT-109",
                "manager_message": (
                    "PLAT-109 has the unmapped status 'Awaiting "
                    "External Validation', so ORBIT could not determine "
                    "whether it was complete at the review boundary."
                ),
                "effect": (
                    "Completion-dependent findings and counts are "
                    "suppressed or marked indeterminate for this item."
                ),
            },
            {
                "code": "PARTIAL_HISTORY",
                "subject_key": "PLAT-110",
                "manager_message": (
                    "PLAT-110 has incomplete status history, so ORBIT "
                    "could not reliably determine how long it had "
                    "remained in progress."
                ),
                "effect": (
                    "The STALLED_WORK rule is suppressed for this item."
                ),
            },
            {
                "code": "MISSING_DUE_DATES",
                "subject_key": None,
                "manager_message": (
                    f"{_number_word(len(missing_due_keys), capitalize=True)} "
                    "work items have no due date."
                ),
                "affected_keys": missing_due_keys,
                "effect": (
                    "ORBIT cannot evaluate overdue conditions for these "
                    "items."
                ),
            },
        ],
        "suppressed_rule_evaluations": [
            {
                "subject_key": value.subject_key,
                "rule_key": value.rule_key,
                "reason": value.reason,
            }
            for value in suppressed
        ],
    }


def build_machine_review_artifact(
    fixture: NormalizedFixture,
) -> dict[str, Any]:
    document = fixture.raw_document
    period = fixture.review_period
    matches, suppressed = evaluate_week_one_rules(fixture)
    grouped_items = _group_findings(fixture, matches)

    def iso(value):
        return value.isoformat().replace("+00:00", "Z")

    artifact = {
        "expected_artifact_version": "shadow-review-expected-v1",
        "fixture_id": document["fixture_id"],
        "contract_notice": (
            "This expected artifact validates deterministic "
            "implementation behavior for a synthetic fixture. It does "
            "not validate customer usefulness or product demand."
        ),
        "review": {
            "organization_key": document["organization"]["external_key"],
            "organization_name": document["organization"]["name"],
            "team_key": document["team"]["external_key"],
            "team_name": document["team"]["name"],
            "project_key": document["project"]["project_key"],
            "label": period.label,
            "starts_at": iso(period.starts_at),
            "ends_at_exclusive": iso(period.ends_at_exclusive),
            "review_cutoff_at": iso(period.review_cutoff_at),
            "source_cutoff_at": iso(period.source_cutoff_at),
            "comparison_available": False,
            "comparison_message": (
                "No prior Shadow ORBIT review is available for "
                "comparison."
            ),
        },
        "configuration": {
            "planning_basis": {
                "key": document["configuration"]["planning_basis"]["key"],
                "description": (
                    "Synthetic explicit flag only; Jira sprint membership "
                    "is not assumed to mean planned work."
                ),
            },
            "stalled_threshold_complete_days": document[
                "configuration"
            ]["stalled_threshold_complete_days"],
            "high_priority_source_values": ["Highest", "High"],
        },
        "what_changed_since_last_review": {
            "available": False,
            "message": (
                "No prior Shadow ORBIT review is available for "
                "comparison."
            ),
            "deltas": [],
        },
        "supporting_facts": calculate_supporting_facts(fixture),
        "what_needs_attention": {
            "grouped_work_item_count": len(grouped_items),
            "underlying_finding_count": len(matches),
            "items": grouped_items,
        },
        "what_orbit_could_not_determine": _limitations(
            fixture,
            suppressed,
        ),
        "open_and_carried_commitments": {
            "count": 0,
            "items": [],
        },
        "historical_assertions": [
            (
                "PLAT-107 is not counted as completed during week one "
                "because its completion occurred after the period ended."
            ),
            (
                "PLAT-104 appears once in the manager-facing artifact "
                "despite producing two underlying rule matches."
            ),
            (
                "PLAT-109 and PLAT-110 do not produce unsupported "
                "confident findings."
            ),
            "No manager-facing completion percentage is present.",
        ],
    }

    return machine_derived_projection(artifact)


def serialize_deterministically(
    artifact: dict[str, Any],
) -> str:
    return json.dumps(
        artifact,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
