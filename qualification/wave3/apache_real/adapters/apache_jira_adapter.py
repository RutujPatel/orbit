"""Canonical WorkItemState adapter for Apache Software Foundation Jira raw records.

Transforms verified raw Jira JSON records (from The Public Jira Dataset)
into ORBIT's canonical WorkItemState and EvidenceObservation models without
modifying engine semantics or inventing missing data.

Preserved Invariants:
    - deterministic facts first
    - missing values remain None (no manufactured timestamps, assignees, or sprints)
    - strict project key validation rejecting non-Jira tokens (e.g. AXIOS-12613773)
    - timezone-aware UTC datetime normalization
    - immutable provenance references to acquired artifacts
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    SourceInstance,
    WorkItemState,
)

APACHE_JIRA_SOURCE = SourceInstance(source_kind="jira", instance_id="issues.apache.org")

# Authorized Apache projects present in the Wave 3 acquired corpus
SUPPORTED_APACHE_PROJECTS: frozenset[str] = frozenset(
    {"PARQUET", "KAFKA", "AVRO", "FLINK", "ZOOKEEPER"}
)

_STATUS_CATEGORY_MAP: dict[str, str] = {
    "done": "done",
    "new": "to_do",
    "indeterminate": "in_progress",
}

_STATUS_NAME_MAP: dict[str, str] = {
    "resolved": "done",
    "closed": "done",
    "done": "done",
    "open": "to_do",
    "reopened": "to_do",
    "in progress": "in_progress",
    "patch available": "in_progress",
}

_PRIORITY_BAND_MAP: dict[str, str] = {
    "blocker": "high",
    "critical": "high",
    "major": "medium",
    "minor": "low",
    "trivial": "low",
}


def parse_iso_datetime(val: Any) -> datetime | None:
    """Parse an ISO-8601 string or datetime object into a timezone-aware UTC datetime.

    Returns None if val is None, empty, or unparseable.
    Never manufactures a timestamp or defaults to current time.
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            return None
    return None


def is_valid_apache_jira_key(key: Any) -> bool:
    """Validate that a key conforms to an authorized Apache Jira issue key.

    Rejects:
    - Non-string or empty keys
    - Keys without a hyphen
    - Project keys not in SUPPORTED_APACHE_PROJECTS (e.g. Snyk/CVE bot keys like AXIOS-12613773)
    - Keys where the issue sequence is not an integer
    """
    if not isinstance(key, str):
        return False
    key = key.strip()
    if "-" not in key:
        return False
    parts = key.split("-", 1)
    project, seq = parts[0], parts[1]
    if project not in SUPPORTED_APACHE_PROJECTS:
        return False
    if not seq.isdigit():
        return False
    return True


def adapt_apache_jira_issue_to_state(raw: dict[str, Any]) -> WorkItemState:
    """Map a raw Apache Jira issue record into canonical WorkItemState.

    Extracts:
    - issue key (validated against Apache project allowlist)
    - status and status_category (done, in_progress, to_do)
    - created_at, updated_at, resolved_at, due_at timestamps
    - priority and priority_band
    - assignee (preserving None if unassigned)
    - extra_properties (project_key, issue_id, summary, changelog count)
    """
    key = raw.get("key")
    if not key:
        raise ValueError("Raw Jira record missing 'key'")
    if not is_valid_apache_jira_key(key):
        raise ValueError(
            f"Invalid or unauthorized Jira issue key '{key}'. "
            f"Key must belong to authorized projects: {sorted(SUPPORTED_APACHE_PROJECTS)}"
        )

    fields = raw.get("fields", {})
    created_at = parse_iso_datetime(fields.get("created"))
    if created_at is None:
        raise ValueError(f"Jira issue '{key}' missing required 'created' timestamp")

    updated_at = parse_iso_datetime(fields.get("updated"))
    resolved_at = parse_iso_datetime(fields.get("resolutiondate"))
    due_at = parse_iso_datetime(fields.get("duedate"))

    # Status category extraction
    status_dict = fields.get("status", {})
    source_status = str(status_dict.get("name") or "Unknown")
    sc_key = str(status_dict.get("statusCategory", {}).get("key") or "").lower()
    status_category = _STATUS_CATEGORY_MAP.get(
        sc_key, _STATUS_NAME_MAP.get(source_status.lower(), "unknown")
    )

    # Priority extraction
    prio_dict = fields.get("priority") or {}
    source_priority = str(prio_dict.get("name") or "") if prio_dict else ""
    priority_band = _PRIORITY_BAND_MAP.get(source_priority.lower(), "medium")

    # Assignee extraction (preserves None if unassigned)
    raw_assignee = fields.get("assignee")
    assignee: str | None = None
    if isinstance(raw_assignee, dict):
        assignee = raw_assignee.get("displayName") or raw_assignee.get("name")
    elif raw_assignee:
        assignee = str(raw_assignee)

    # Extra properties
    project_key = key.split("-")[0]
    extra_properties: dict[str, Any] = {
        "project_key": project_key,
        "issue_id": str(raw.get("id") or ""),
        "summary": str(fields.get("summary") or ""),
    }
    changelog = raw.get("changelog")
    if isinstance(changelog, dict):
        extra_properties["changelog_total"] = changelog.get("total", 0)

    return WorkItemState(
        key=key,
        source_status=source_status,
        status_category=status_category,
        created_at=created_at,
        updated_at=updated_at,
        resolved_at=resolved_at,
        due_at=due_at,
        source_priority=source_priority,
        priority_band=priority_band,
        assignee=assignee,
        extra_properties=extra_properties,
    )


def adapt_apache_jira_issue(
    raw: dict[str, Any],
    context: ObservationContext,
    fixture_id: str | None = None,
    quality_issues: tuple[QualityIssue, ...] = (),
) -> EvidenceObservation:
    """Adapt a raw Apache Jira issue record into a canonical EvidenceObservation."""
    state = adapt_apache_jira_issue_to_state(raw)
    entity_ref = EntityRef(
        source_instance=context.source_instance,
        entity_kind="work_item",
        entity_id=state.key,
    )
    eff_fixture_id = fixture_id or f"qualification/wave3/apache_real/jira/{state.key}.json"
    provenance = ProvenanceRef(
        source_instance=context.source_instance,
        observation_id=context.observation_id,
        fixture_id=eff_fixture_id,
        record_locator=f"work_items[{state.key}]",
        source_field_path="key",
    )
    return EvidenceObservation(
        entity_ref=entity_ref,
        observation_context=context,
        observed_state=state,
        quality_issues=quality_issues,
        provenance_refs=(provenance,),
    )
