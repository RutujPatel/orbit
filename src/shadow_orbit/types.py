"""Small immutable values used by the deterministic acceptance engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


StatusCategory = Literal["todo", "in_progress", "blocked", "done", "unknown"]
PriorityBand = Literal["high", "ordinary", "unknown"]


@dataclass(frozen=True, slots=True)
class ReviewPeriod:
    label: str
    starts_at: datetime
    ends_at_exclusive: datetime
    review_cutoff_at: datetime
    source_cutoff_at: datetime


@dataclass(frozen=True, slots=True)
class Change:
    field: str
    from_value: Any
    to_value: Any
    changed_at: datetime


@dataclass(frozen=True, slots=True)
class WorkItem:
    source_id: str
    key: str
    title: str
    item_type: str
    source_priority: str
    priority_band: PriorityBand
    source_status: str
    status_category: StatusCategory
    assignee: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    due_at: datetime | None
    planned_at_period_start: bool | None
    history_complete: bool
    source_status_at_period_start: str | None
    changes: tuple[Change, ...]


@dataclass(frozen=True, slots=True)
class DataQualityCondition:
    code: str
    subject_key: str | None
    message: str


@dataclass(frozen=True, slots=True)
class QuarantinedRecord:
    source_key: str | None
    source_id: str | None
    reason_code: str
    reason: str


@dataclass(frozen=True, slots=True)
class ValidatedFixture:
    raw_document: dict[str, Any]
    accepted_raw_items: tuple[dict[str, Any], ...]
    quarantined_records: tuple[QuarantinedRecord, ...]
    validation_conditions: tuple[DataQualityCondition, ...]


@dataclass(frozen=True, slots=True)
class NormalizedFixture:
    raw_document: dict[str, Any]
    review_period: ReviewPeriod
    work_items: tuple[WorkItem, ...]
    quarantined_records: tuple[QuarantinedRecord, ...]
    data_quality_conditions: tuple[DataQualityCondition, ...]


@dataclass(frozen=True, slots=True)
class RuleMatch:
    subject_key: str
    rule_key: str
    rule_version: str
    observed: dict[str, Any]
    threshold: dict[str, Any]
    calculation: str
    deterministic_explanation: str
    evidence_references: tuple[dict[str, str], ...]
    data_quality_state: str = "complete"


@dataclass(frozen=True, slots=True)
class SuppressedEvaluation:
    subject_key: str
    rule_key: str
    reason: str
