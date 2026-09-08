"""Assemble the machine-derived messy Week 1 prepared-review artifact.

This module is bounded to the approved messy-data honesty acceptance
scenario. It reuses the existing validation, normalization, and evaluation
pipeline, then builds a messy-specific artifact shape that matches the
approved expected artifact projection.

Approved founder decisions:
  - STALE_SOURCE_RECORD uses >= 14 complete days.
  - OVERDUE_HIGH_PRIORITY artifact-level unevaluable disclosure is
    derived from INVALID_OPTIONAL_TIMESTAMP validation provenance
    and the item's eligible state, not from hard-coded issue keys.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from shadow_orbit.evaluation import (
    calculate_supporting_facts,
    evaluate_week_one_rules,
)
from shadow_orbit.temporal import (
    elapsed_complete_days,
    is_overdue,
    last_meaningful_status_change,
)
from shadow_orbit.types import (
    NormalizedFixture,
    RuleMatch,
    SuppressedEvaluation,
    ValidatedFixture,
)


_STALE_THRESHOLD_COMPLETE_DAYS = 14

_NUMBER_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
    5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
    10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
    14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen",
    18: "eighteen", 19: "nineteen", 20: "twenty",
}

_MESSY_MACHINE_DERIVED_FIELDS = (
    "expected_artifact_version",
    "fixture_id",
    "contract_notice",
    "review",
    "import_result",
    "what_changed_since_last_review",
    "supporting_facts",
    "what_needs_attention",
    "what_orbit_could_not_determine",
    "open_and_carried_commitments",
    "historical_assertions",
)

_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_INSTRUCTION_PHRASES = (
    "ignore previous instructions",
    "ignore all instructions",
    "disregard previous instructions",
    "mark every",
)


def _number_word(value: int, *, capitalize: bool = False) -> str:
    word = _NUMBER_WORDS.get(value, str(value))
    return word.capitalize() if capitalize else word


def _iso(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _display_date(value) -> str:
    return f"{value.day} {value.strftime('%B')}"


def _contains_html_like(text: str) -> bool:
    return bool(_HTML_TAG_PATTERN.search(text))


def _contains_instruction_like(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in _INSTRUCTION_PHRASES)


# ── Import result ───────────────────────────────────────────────────

def _build_import_result(
    validated: ValidatedFixture,
) -> dict[str, Any]:
    raw_count = len(validated.raw_document["work_items"])
    accepted_count = len(validated.accepted_raw_items)
    quarantined_count = len(validated.quarantined_records)

    quarantined_entries = []
    for record in validated.quarantined_records:
        reason = record.reason
        if record.reason_code == "DUPLICATE_EXTERNAL_KEY":
            reason = (
                f"All records sharing the duplicate external key "
                f"{record.source_key} are quarantined because "
                "Shadow ORBIT cannot choose one safely."
            )
        elif record.reason_code == "INVALID_REQUIRED_TIMESTAMP":
            reason = (
                "The required updated_at value is not a valid "
                "timezone-aware timestamp."
            )

        quarantined_entries.append({
            "source_key": record.source_key,
            "source_id": record.source_id,
            "reason_code": record.reason_code,
            "reason": reason,
        })

    return {
        "raw_record_count": raw_count,
        "accepted_record_count": accepted_count,
        "quarantined_record_count": quarantined_count,
        "quarantined_records": quarantined_entries,
    }


# ── Supporting facts ────────────────────────────────────────────────

def _build_messy_supporting_facts(
    fixture: NormalizedFixture,
) -> dict[str, Any]:
    items = fixture.work_items
    conditions = fixture.data_quality_conditions

    invalid_due_keys = sorted(
        cond.subject_key
        for cond in conditions
        if (
            cond.code == "INVALID_OPTIONAL_TIMESTAMP"
            and cond.subject_key is not None
            and "due_at" in cond.message
        )
    )

    missing_due_keys = sorted(
        item.key
        for item in items
        if item.due_at is None and item.key not in invalid_due_keys
    )

    known_planning = sorted(
        item.key
        for item in items
        if item.planned_at_period_start is not None
    )
    unknown_planning_keys = sorted(
        item.key
        for item in items
        if item.planned_at_period_start is None
    )

    return {
        "accepted_work_item_count": len(items),
        "known_missing_due_date_count": len(missing_due_keys),
        "invalid_due_date_count": len(invalid_due_keys),
        "invalid_due_date_keys": invalid_due_keys,
        "known_planning_classification_count": len(known_planning),
        "unknown_planning_classification_count": len(
            unknown_planning_keys
        ),
        "unknown_planning_classification_keys": unknown_planning_keys,
        "manager_facing_completion_percentage": None,
        "manager_facing_completion_percentage_reason": (
            "Planning classification is incomplete, and the "
            "planning basis has not been validated with a real "
            "manager."
        ),
    }


# ── Findings ────────────────────────────────────────────────────────

def _messy_blocked_explanation(
    item,
    fixture: NormalizedFixture,
) -> str:
    """Build blocked explanation using mapped-blocked status transitions."""
    status_mapping = fixture.raw_document["configuration"]["status_mapping"]
    blocked_change = None
    for change in item.changes:
        if change.field == "status":
            mapped = status_mapping.get(change.to_value)
            if mapped == "blocked":
                if (
                    blocked_change is None
                    or change.changed_at > blocked_change.changed_at
                ):
                    blocked_change = change

    if blocked_change is not None:
        if blocked_change.to_value.lower() == "blocked":
            return (
                f"{item.key} became blocked on "
                f"{_display_date(blocked_change.changed_at)} and "
                "remained blocked in the source snapshot."
            )
        return (
            f"{item.key} has been in the mapped blocked status "
            f"'{blocked_change.to_value}' since "
            f"{_display_date(blocked_change.changed_at)} and "
            "remained in that status in the source snapshot."
        )

    return (
        f"{item.key} was blocked in the source snapshot used for "
        f"the {_display_date(fixture.review_period.review_cutoff_at)} "
        "review."
    )


def _messy_overdue_explanation(
    item,
    fixture: NormalizedFixture,
) -> str:
    return (
        f"{item.key} was due on {_display_date(item.due_at)} and "
        f"remained in {item.source_status} in the source snapshot "
        "used for the "
        f"{_display_date(fixture.review_period.review_cutoff_at)} "
        "review."
    )


def _messy_stalled_explanation(
    item,
    fixture: NormalizedFixture,
) -> str:
    last_change = last_meaningful_status_change(item)
    if last_change is None:
        return (
            f"{item.key} remained in progress in the source snapshot."
        )

    to_status = None
    for change in item.changes:
        if (
            change.field == "status"
            and change.changed_at == last_change
        ):
            to_status = change.to_value
            break

    verb = "entered"
    status_name = to_status or item.source_status
    return (
        f"{item.key} {verb} {status_name} on "
        f"{_display_date(last_change)} and remained in progress "
        "in the source snapshot used for the "
        f"{_display_date(fixture.review_period.review_cutoff_at)} "
        "review."
    )


def _messy_blocked_evidence(item, match: RuleMatch) -> list[str]:
    refs = [f"work_item:{item.key}"]
    status_mapping = None
    for change in item.changes:
        if change.field == "status":
            refs.append(
                f"change:{item.key}:status:{_iso(change.changed_at)}"
            )
            break
    return refs


def _messy_overdue_evidence(item) -> list[str]:
    return [
        f"work_item:{item.key}",
        f"field:{item.key}:due_at",
    ]


def _messy_stalled_evidence(item) -> list[str]:
    refs = [f"work_item:{item.key}"]
    last_change = last_meaningful_status_change(item)
    if last_change is not None:
        refs.append(
            f"change:{item.key}:status:{_iso(last_change)}"
        )
    return refs


def _condition_summary_for_rule(rule_key: str) -> str:
    if rule_key == "BLOCKED_HIGH_PRIORITY":
        return "High-priority work remains blocked."
    if rule_key == "OVERDUE_HIGH_PRIORITY":
        return (
            "High-priority work remains incomplete after its "
            "due date."
        )
    if rule_key == "STALLED_WORK":
        return (
            "Work has remained in progress beyond the configured "
            "stalled-work threshold."
        )
    raise ValueError(f"Unsupported rule: {rule_key}")


def _build_messy_findings(
    fixture: NormalizedFixture,
    matches: tuple[RuleMatch, ...],
) -> dict[str, Any]:
    items_by_key = {item.key: item for item in fixture.work_items}

    grouped: dict[str, list[RuleMatch]] = defaultdict(list)
    for match in matches:
        grouped[match.subject_key].append(match)

    output = []
    for subject_key in sorted(grouped):
        subject_matches = sorted(
            grouped[subject_key],
            key=lambda m: m.rule_key,
        )
        item = items_by_key[subject_key]
        primary = subject_matches[0]

        if primary.rule_key == "BLOCKED_HIGH_PRIORITY":
            explanation = _messy_blocked_explanation(item, fixture)
            evidence = _messy_blocked_evidence(item, primary)
        elif primary.rule_key == "OVERDUE_HIGH_PRIORITY":
            explanation = _messy_overdue_explanation(item, fixture)
            evidence = _messy_overdue_evidence(item)
        elif primary.rule_key == "STALLED_WORK":
            explanation = _messy_stalled_explanation(item, fixture)
            evidence = _messy_stalled_evidence(item)
        else:
            raise ValueError(
                f"Unsupported rule: {primary.rule_key}"
            )

        output.append({
            "subject_key": subject_key,
            "title": item.title,
            "condition_summary": _condition_summary_for_rule(
                primary.rule_key
            ),
            "deterministic_explanation": explanation,
            "underlying_matches": [
                {
                    "rule_key": m.rule_key,
                    "rule_version": m.rule_version,
                }
                for m in subject_matches
            ],
            "evidence_references": evidence,
            "data_quality_state": "complete",
        })

    return {
        "grouped_work_item_count": len(output),
        "underlying_finding_count": len(matches),
        "items": output,
    }


# ── Limitations / what_orbit_could_not_determine ───────────────────

def _build_messy_limitations(
    fixture: NormalizedFixture,
    validated: ValidatedFixture,
    suppressed: tuple[SuppressedEvaluation, ...],
) -> dict[str, Any]:
    conditions_list = list(fixture.data_quality_conditions)
    items = fixture.work_items
    items_by_key = {item.key: item for item in items}
    status_mapping = fixture.raw_document["configuration"]["status_mapping"]

    # ── Collect condition groups ──

    unknown_status_keys = sorted(
        c.subject_key
        for c in conditions_list
        if c.code == "UNKNOWN_STATUS" and c.subject_key
    )

    partial_history_keys = sorted(
        c.subject_key
        for c in conditions_list
        if c.code == "PARTIAL_HISTORY" and c.subject_key
    )

    unknown_priority_keys = sorted(
        c.subject_key
        for c in conditions_list
        if c.code == "UNKNOWN_PRIORITY" and c.subject_key
    )
    unknown_priority_source = []
    for key in unknown_priority_keys:
        item = items_by_key.get(key)
        if item:
            unknown_priority_source.append(item.source_priority)

    invalid_optional_keys = sorted(
        c.subject_key
        for c in conditions_list
        if (
            c.code == "INVALID_OPTIONAL_TIMESTAMP"
            and c.subject_key
        )
    )

    missing_due_count = sum(
        1
        for item in items
        if item.due_at is None and item.key not in invalid_optional_keys
    )

    # Status-category contradiction: source status maps to one
    # category but provider_status_category suggests another.
    contradiction_keys = []
    for item in items:
        raw = next(
            (
                r
                for r in validated.accepted_raw_items
                if r["key"] == item.key
            ),
            None,
        )
        if raw is None:
            continue
        provider_cat = raw.get("provider_status_category")
        if provider_cat is None or provider_cat == "indeterminate":
            continue
        mapped_cat = status_mapping.get(item.source_status, "unknown")
        if mapped_cat == "done" and provider_cat != "done":
            contradiction_keys.append(item.key)
        elif mapped_cat != "done" and provider_cat == "done":
            contradiction_keys.append(item.key)
    contradiction_keys.sort()

    unknown_planning_keys = sorted(
        item.key
        for item in items
        if item.planned_at_period_start is None
    )

    # Stale records: >= 14 complete days before source_cutoff_at
    source_cutoff = fixture.review_period.source_cutoff_at
    stale_keys = sorted(
        item.key
        for item in items
        if (
            elapsed_complete_days(item.updated_at, source_cutoff)
            >= _STALE_THRESHOLD_COMPLETE_DAYS
        )
    )

    # Unsafe source text
    markup_keys = sorted(
        item.key
        for item in items
        if _contains_html_like(item.title)
    )

    instruction_keys = sorted(
        item.key
        for item in items
        if _contains_instruction_like(item.title)
    )

    # ── Build summary ──

    summary_lines = []
    if missing_due_count > 0:
        summary_lines.append(
            f"{_number_word(missing_due_count, capitalize=True)} "
            "accepted work items have no due date."
        )
    for key in invalid_optional_keys:
        summary_lines.append(
            f"{key} has a due date without timezone information."
        )
    for key in unknown_status_keys:
        summary_lines.append(f"{key} has an unmapped status.")
    if partial_history_keys:
        summary_lines.append(
            f"{_number_word(len(partial_history_keys), capitalize=True)} "
            "accepted work items have incomplete status history."
        )
    if unknown_priority_keys:
        summary_lines.append(
            f"{_number_word(len(unknown_priority_keys), capitalize=True)} "
            "accepted work items use unmapped priority values."
        )
    if contradiction_keys:
        summary_lines.append(
            f"{_number_word(len(contradiction_keys), capitalize=True)} "
            "accepted work item has contradictory status-category "
            "metadata."
        )
    if unknown_planning_keys:
        summary_lines.append(
            f"{_number_word(len(unknown_planning_keys), capitalize=True)} "
            "accepted work items have no explicit planning "
            "classification."
        )
    quarantine_count = len(validated.quarantined_records)
    if quarantine_count > 0:
        summary_lines.append(
            f"{_number_word(quarantine_count, capitalize=True)} "
            "source records were quarantined."
        )

    # ── Build conditions ──

    conditions = []

    if unknown_status_keys:
        conditions.append({
            "code": "UNKNOWN_STATUS",
            "subject_keys": unknown_status_keys,
            "effect": (
                "Completion-dependent evaluations are suppressed."
            ),
        })

    if partial_history_keys:
        conditions.append({
            "code": "PARTIAL_HISTORY",
            "subject_keys": partial_history_keys,
            "effect": (
                "STALLED_WORK is suppressed where a reliable last "
                "meaningful transition cannot be established."
            ),
        })

    if unknown_priority_keys:
        conditions.append({
            "code": "UNKNOWN_PRIORITY",
            "subject_keys": unknown_priority_keys,
            "source_values": unknown_priority_source,
            "effect": (
                "High-priority rules are suppressed for these items."
            ),
        })

    if missing_due_count > 0:
        conditions.append({
            "code": "MISSING_DUE_DATE",
            "affected_count": missing_due_count,
            "effect": (
                "Overdue conditions cannot be evaluated for "
                "affected items."
            ),
        })

    if invalid_optional_keys:
        conditions.append({
            "code": "INVALID_OPTIONAL_TIMESTAMP",
            "subject_keys": invalid_optional_keys,
            "field": "due_at",
            "effect": (
                "The item may be imported, but its due date is "
                "treated as unknown and no overdue finding is "
                "produced."
            ),
        })

    if contradiction_keys:
        for key in contradiction_keys:
            item = items_by_key[key]
            raw = next(
                r
                for r in validated.accepted_raw_items
                if r["key"] == key
            )
            provider_cat = raw.get("provider_status_category", "")
            conditions.append({
                "code": "STATUS_CATEGORY_CONTRADICTION",
                "subject_keys": [key],
                "message": (
                    f"{key} has source status '{item.source_status}' "
                    f"while provider_status_category says "
                    f"'{provider_cat}'."
                ),
                "effect": (
                    "The contradiction is shown. The bounded status "
                    "history and resolved timestamp support "
                    "completion, but the supporting count is "
                    "qualified."
                ),
            })

    if unknown_planning_keys:
        conditions.append({
            "code": "UNKNOWN_PLANNING_CLASSIFICATION",
            "subject_keys": unknown_planning_keys,
            "effect": (
                "No planned-work percentage is calculated."
            ),
        })

    if stale_keys:
        conditions.append({
            "code": "STALE_SOURCE_RECORD",
            "subject_keys": stale_keys,
            "definition": (
                "updated_at is more than 14 complete days before "
                "source_cutoff_at"
            ),
            "effect": (
                "The artifact discloses that these records may "
                "not reflect recent operational context."
            ),
        })

    if markup_keys:
        conditions.append({
            "code": "UNTRUSTED_MARKUP_ESCAPED",
            "subject_keys": markup_keys,
            "effect": (
                "The title is rendered as inert text and is "
                "never executed as HTML or script."
            ),
        })

    if instruction_keys:
        conditions.append({
            "code": "UNTRUSTED_INSTRUCTION_TEXT_PRESERVED",
            "subject_keys": instruction_keys,
            "effect": (
                "The title is treated only as source text and "
                "cannot affect deterministic rules."
            ),
        })

    # ── Build suppressed rule evaluations ──

    # Start with raw engine suppressions.
    suppressed_entries = []
    for s in suppressed:
        reason = s.reason
        if (
            s.rule_key == "OVERDUE_HIGH_PRIORITY"
            and "completion state is unknown because its status is unmapped" in reason
        ):
            reason = (
                "The due date has passed, but completion state cannot be "
                "established because the status is unmapped."
            )
        suppressed_entries.append({
            "subject_key": s.subject_key,
            "rule_key": s.rule_key,
            "reason": reason,
        })

    # Artifact-level unevaluable-rule disclosure: items with
    # INVALID_OPTIONAL_TIMESTAMP on due_at that are high-priority
    # and known-incomplete would be eligible for OVERDUE if they
    # had a valid due date.
    invalid_due_item_keys = {
        c.subject_key
        for c in fixture.data_quality_conditions
        if (
            c.code == "INVALID_OPTIONAL_TIMESTAMP"
            and c.subject_key is not None
            and "due_at" in c.message
        )
    }
    already_suppressed = {
        (s["subject_key"], s["rule_key"])
        for s in suppressed_entries
    }
    for item in fixture.work_items:
        if item.key not in invalid_due_item_keys:
            continue
        if item.priority_band != "high":
            continue
        if item.status_category == "done":
            continue
        pair = (item.key, "OVERDUE_HIGH_PRIORITY")
        if pair in already_suppressed:
            continue
        suppressed_entries.append({
            "subject_key": item.key,
            "rule_key": "OVERDUE_HIGH_PRIORITY",
            "reason": (
                "The due date is not timezone-aware and is "
                "treated as unknown."
            ),
        })

    suppressed_entries.sort(
        key=lambda s: (s["subject_key"], s["rule_key"])
    )

    return {
        "summary": summary_lines,
        "conditions": conditions,
        "suppressed_rule_evaluations": suppressed_entries,
    }


# ── Projection ─────────────────────────────────────────────────────

def messy_machine_derived_projection(
    artifact: dict[str, Any],
) -> dict[str, Any]:
    """Positively select the approved messy machine-derived boundary."""
    missing = [
        key
        for key in _MESSY_MACHINE_DERIVED_FIELDS
        if key not in artifact
    ]
    if missing:
        raise ValueError(
            f"Messy artifact missing machine-derived fields: {missing}"
        )

    return {
        key: artifact[key]
        for key in _MESSY_MACHINE_DERIVED_FIELDS
    }


# ── Top-level assembly ─────────────────────────────────────────────

def build_messy_week_one_artifact(
    validated: ValidatedFixture,
    fixture: NormalizedFixture,
) -> dict[str, Any]:
    """Assemble the complete messy Week 1 machine-derived artifact.

    This function derives all output from runtime inputs. It does not
    read or hard-code the expected artifact.
    """
    document = fixture.raw_document
    period = fixture.review_period
    matches, suppressed = evaluate_week_one_rules(fixture)

    def iso(value):
        return value.isoformat().replace("+00:00", "Z")

    artifact = {
        "expected_artifact_version": "shadow-review-expected-v1",
        "fixture_id": document["fixture_id"],
        "contract_notice": (
            "This expected artifact tests honest handling of "
            "imperfect source data. It does not require the "
            "prototype to resolve every source defect."
        ),
        "review": {
            "organization_key": document["organization"][
                "external_key"
            ],
            "team_key": document["team"]["external_key"],
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
        "import_result": _build_import_result(validated),
        "what_changed_since_last_review": {
            "available": False,
            "message": (
                "No prior Shadow ORBIT review is available for "
                "comparison."
            ),
            "deltas": [],
        },
        "supporting_facts": _build_messy_supporting_facts(fixture),
        "what_needs_attention": _build_messy_findings(
            fixture, matches
        ),
        "what_orbit_could_not_determine": _build_messy_limitations(
            fixture, validated, suppressed
        ),
        "open_and_carried_commitments": {
            "count": 0,
            "items": [],
        },
        "historical_assertions": [
            (
                "The expected result is allowed to contain few "
                "findings despite many source records."
            ),
            (
                "Quarantined records do not contribute to metrics "
                "or findings."
            ),
            (
                "Missing and malformed data are never silently "
                "defaulted."
            ),
            "Markup and instruction-like text remain inert.",
            "No completion percentage is presented.",
        ],
    }

    return messy_machine_derived_projection(artifact)
