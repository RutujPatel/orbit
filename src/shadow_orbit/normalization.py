"""Normalize validated fixture values into a bounded internal projection."""

from __future__ import annotations

from shadow_orbit.types import (
    Change,
    DataQualityCondition,
    NormalizedFixture,
    ReviewPeriod,
    WorkItem,
)
from shadow_orbit.validation import parse_aware_datetime


def normalize_fixture(validated) -> NormalizedFixture:
    document = validated.raw_document
    period_data = document["review_period"]
    configuration = document["configuration"]

    period = ReviewPeriod(
        label=period_data["label"],
        starts_at=parse_aware_datetime(
            period_data["starts_at"], "review_period.starts_at"
        ),
        ends_at_exclusive=parse_aware_datetime(
            period_data["ends_at_exclusive"],
            "review_period.ends_at_exclusive",
        ),
        review_cutoff_at=parse_aware_datetime(
            period_data["review_cutoff_at"],
            "review_period.review_cutoff_at",
        ),
        source_cutoff_at=parse_aware_datetime(
            period_data["source_cutoff_at"],
            "review_period.source_cutoff_at",
        ),
    )

    status_mapping = configuration["status_mapping"]
    priority_mapping = configuration["priority_mapping"]

    conditions = list(validated.validation_conditions)
    normalized_items: list[WorkItem] = []

    for item in validated.accepted_raw_items:
        key = item["key"]
        source_status = item["status"]
        source_priority = item["priority"]

        status_category = status_mapping.get(source_status, "unknown")
        priority_band = priority_mapping.get(source_priority, "unknown")

        if status_category == "unknown":
            conditions.append(
                DataQualityCondition(
                    code="UNKNOWN_STATUS",
                    subject_key=key,
                    message=(
                        f"{key} has the unmapped status "
                        f"{source_status!r}."
                    ),
                )
            )

        if priority_band == "unknown":
            conditions.append(
                DataQualityCondition(
                    code="UNKNOWN_PRIORITY",
                    subject_key=key,
                    message=(
                        f"{key} has the unmapped priority "
                        f"{source_priority!r}."
                    ),
                )
            )

        if not item["history_complete"]:
            conditions.append(
                DataQualityCondition(
                    code="PARTIAL_HISTORY",
                    subject_key=key,
                    message=f"{key} has incomplete status history.",
                )
            )

        changes = tuple(
            sorted(
                (
                    Change(
                        field=change["field"],
                        from_value=change["from"],
                        to_value=change["to"],
                        changed_at=parse_aware_datetime(
                            change["changed_at"],
                            f"{key}.changes.changed_at",
                        ),
                    )
                    for change in item["changes"]
                ),
                key=lambda value: (
                    value.changed_at,
                    value.field,
                    str(value.from_value),
                    str(value.to_value),
                ),
            )
        )

        normalized_items.append(
            WorkItem(
                source_id=item["source_id"],
                key=key,
                title=item["title"],
                item_type=item["item_type"],
                source_priority=source_priority,
                priority_band=priority_band,
                source_status=source_status,
                status_category=status_category,
                assignee=item.get("assignee"),
                created_at=parse_aware_datetime(
                    item["created_at"], f"{key}.created_at"
                ),
                updated_at=parse_aware_datetime(
                    item["updated_at"], f"{key}.updated_at"
                ),
                resolved_at=(
                    parse_aware_datetime(
                        item["resolved_at"], f"{key}.resolved_at"
                    )
                    if item.get("resolved_at") is not None
                    else None
                ),
                due_at=(
                    parse_aware_datetime(
                        item["due_at"], f"{key}.due_at"
                    )
                    if item.get("due_at") is not None
                    else None
                ),
                planned_at_period_start=item[
                    "planned_at_period_start"
                ],
                history_complete=item["history_complete"],
                source_status_at_period_start=item.get(
                    "status_at_period_start"
                ),
                changes=changes,
            )
        )

    return NormalizedFixture(
        raw_document=document,
        review_period=period,
        work_items=tuple(
            sorted(normalized_items, key=lambda value: value.key)
        ),
        quarantined_records=validated.quarantined_records,
        data_quality_conditions=tuple(
            sorted(
                conditions,
                key=lambda value: (
                    value.code,
                    value.subject_key or "",
                    value.message,
                ),
            )
        ),
    )
