"""Validation of the bounded Shadow ORBIT fixture contract."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime
from typing import Any

from shadow_orbit.types import (
    DataQualityCondition,
    QuarantinedRecord,
    ValidatedFixture,
)


CONTRACT_VERSION = "shadow-jira-fixture-v1"

_REQUIRED_TOP_LEVEL = {
    "contract_version",
    "fixture_id",
    "organization",
    "team",
    "project",
    "timezone",
    "review_period",
    "configuration",
    "source_completeness",
    "work_items",
}

_REQUIRED_PERIOD_FIELDS = {
    "label",
    "starts_at",
    "ends_at_exclusive",
    "review_cutoff_at",
    "source_cutoff_at",
}

_REQUIRED_ITEM_FIELDS = {
    "source_id",
    "key",
    "title",
    "item_type",
    "priority",
    "status",
    "created_at",
    "updated_at",
    "planned_at_period_start",
    "history_complete",
    "changes",
}

_REQUIRED_CHANGE_FIELDS = {"field", "from", "to", "changed_at"}


def parse_aware_datetime(value: Any, field_path: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field_path} must be an ISO 8601 string.")

    candidate = value.replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(
            f"{field_path} must be a valid ISO 8601 timestamp."
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_path} must include timezone information.")

    return parsed


def _require_mapping(document: dict[str, Any], field: str) -> dict[str, Any]:
    value = document.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object.")
    return value


def _validate_document_structure(document: dict[str, Any]) -> None:
    missing = sorted(_REQUIRED_TOP_LEVEL - document.keys())
    if missing:
        raise ValueError(f"Missing required top-level fields: {missing}")

    if document["contract_version"] != CONTRACT_VERSION:
        raise ValueError(
            f"Unsupported contract_version: {document['contract_version']!r}"
        )

    organization = _require_mapping(document, "organization")
    team = _require_mapping(document, "team")
    project = _require_mapping(document, "project")
    period = _require_mapping(document, "review_period")
    configuration = _require_mapping(document, "configuration")

    for label, value in (
        ("organization.external_key", organization.get("external_key")),
        ("organization.name", organization.get("name")),
        ("team.external_key", team.get("external_key")),
        ("team.name", team.get("name")),
        ("project.site_key", project.get("site_key")),
        ("project.project_key", project.get("project_key")),
        ("project.name", project.get("name")),
    ):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{label} must be a non-empty string.")

    if project.get("provider") != "jira":
        raise ValueError("project.provider must equal 'jira'.")

    missing_period = sorted(_REQUIRED_PERIOD_FIELDS - period.keys())
    if missing_period:
        raise ValueError(
            f"Missing required review_period fields: {missing_period}"
        )

    starts_at = parse_aware_datetime(
        period["starts_at"], "review_period.starts_at"
    )
    ends_at = parse_aware_datetime(
        period["ends_at_exclusive"],
        "review_period.ends_at_exclusive",
    )
    review_cutoff = parse_aware_datetime(
        period["review_cutoff_at"],
        "review_period.review_cutoff_at",
    )
    source_cutoff = parse_aware_datetime(
        period["source_cutoff_at"],
        "review_period.source_cutoff_at",
    )

    if starts_at >= ends_at:
        raise ValueError(
            "review_period.starts_at must precede ends_at_exclusive."
        )
    if source_cutoff > review_cutoff:
        raise ValueError(
            "review_period.source_cutoff_at must not be later than "
            "review_cutoff_at."
        )

    if not isinstance(document["work_items"], list):
        raise ValueError("work_items must be an array.")

    active_configuration = {
        "planning_basis",
        "stalled_threshold_complete_days",
        "status_mapping",
        "priority_mapping",
    }
    missing_configuration = sorted(
        active_configuration - configuration.keys()
    )
    if missing_configuration:
        raise ValueError(
            f"Missing active configuration fields: {missing_configuration}"
        )


def validate_fixture(document: dict[str, Any]) -> ValidatedFixture:
    """
    Validate a fixture without mutating its caller-owned representation.

    Structurally invalid records are quarantined. Unknown source values remain
    accepted and are represented later as explicit data-quality conditions.
    """
    working = deepcopy(document)
    _validate_document_structure(working)

    project_key = working["project"]["project_key"]
    raw_items = working["work_items"]

    keys = [
        item.get("key")
        for item in raw_items
        if isinstance(item, dict) and isinstance(item.get("key"), str)
    ]
    duplicate_keys = {
        key for key, count in Counter(keys).items() if count > 1
    }

    accepted: list[dict[str, Any]] = []
    quarantined: list[QuarantinedRecord] = []
    conditions: list[DataQualityCondition] = []

    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            quarantined.append(
                QuarantinedRecord(
                    source_key=None,
                    source_id=None,
                    reason_code="INVALID_RECORD",
                    reason=f"work_items[{index}] must be an object.",
                )
            )
            continue

        source_key = item.get("key")
        source_id = item.get("source_id")

        if source_key in duplicate_keys:
            quarantined.append(
                QuarantinedRecord(
                    source_key=source_key,
                    source_id=source_id,
                    reason_code="DUPLICATE_EXTERNAL_KEY",
                    reason=(
                        f"All records sharing duplicate key {source_key} "
                        "are quarantined."
                    ),
                )
            )
            continue

        missing = sorted(_REQUIRED_ITEM_FIELDS - item.keys())
        if missing:
            quarantined.append(
                QuarantinedRecord(
                    source_key=source_key,
                    source_id=source_id,
                    reason_code="MISSING_REQUIRED_FIELD",
                    reason=f"Missing required fields: {missing}",
                )
            )
            continue

        if (
            not isinstance(source_key, str)
            or not source_key.startswith(f"{project_key}-")
        ):
            quarantined.append(
                QuarantinedRecord(
                    source_key=source_key,
                    source_id=source_id,
                    reason_code="PROJECT_KEY_MISMATCH",
                    reason=(
                        f"Work-item key must begin with {project_key}-."
                    ),
                )
            )
            continue

        try:
            parse_aware_datetime(
                item["created_at"], f"{source_key}.created_at"
            )
            parse_aware_datetime(
                item["updated_at"], f"{source_key}.updated_at"
            )

            for change_index, change in enumerate(item["changes"]):
                if not isinstance(change, dict):
                    raise ValueError(
                        f"{source_key}.changes[{change_index}] "
                        "must be an object."
                    )

                missing_change = sorted(
                    _REQUIRED_CHANGE_FIELDS - change.keys()
                )
                if missing_change:
                    raise ValueError(
                        f"{source_key}.changes[{change_index}] "
                        f"missing fields: {missing_change}"
                    )

                parse_aware_datetime(
                    change["changed_at"],
                    f"{source_key}.changes[{change_index}].changed_at",
                )
        except ValueError as exc:
            quarantined.append(
                QuarantinedRecord(
                    source_key=source_key,
                    source_id=source_id,
                    reason_code="INVALID_REQUIRED_TIMESTAMP",
                    reason=str(exc),
                )
            )
            continue

        accepted_item = deepcopy(item)

        for optional_field in ("resolved_at", "due_at"):
            value = accepted_item.get(optional_field)
            if value is None:
                continue
            try:
                parse_aware_datetime(
                    value, f"{source_key}.{optional_field}"
                )
            except ValueError:
                accepted_item[optional_field] = None
                conditions.append(
                    DataQualityCondition(
                        code="INVALID_OPTIONAL_TIMESTAMP",
                        subject_key=source_key,
                        message=(
                            f"{source_key}.{optional_field} is invalid and "
                            "is treated as unknown."
                        ),
                    )
                )

        planned = accepted_item["planned_at_period_start"]
        if planned not in (True, False, None):
            quarantined.append(
                QuarantinedRecord(
                    source_key=source_key,
                    source_id=source_id,
                    reason_code="INVALID_PLANNING_CLASSIFICATION",
                    reason=(
                        "planned_at_period_start must be true, false, or null."
                    ),
                )
            )
            continue

        accepted.append(accepted_item)

    return ValidatedFixture(
        raw_document=working,
        accepted_raw_items=tuple(accepted),
        quarantined_records=tuple(quarantined),
        validation_conditions=tuple(conditions),
    )
