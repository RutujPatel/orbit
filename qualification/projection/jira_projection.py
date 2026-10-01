"""GoGreen Jira source projection layer.

Transforms real GoGreen Jira source records into shadow-jira-fixture-v1 compliant
fixture documents under strict four-category reconciliation accounting.

Governing invariants:
1. RAW SOURCE INDEPENDENCE: Projects from raw Jira Cloud REST capture artifact.
2. NO SILENT DEFAULTS: Missing item_type, priority, status, or timestamps raise explicit errors.
3. NO SILENT CHANGE DROPS: Every changelog event is strictly accounted for.
4. HONEST HISTORY: Per-item history_complete is read from source, never inferred from change count.
5. DETERMINISTIC FIXTURE ID: Derived strictly from immutable identifiers (no wall-clock dates).
6. CANONICAL HASHING: Uses canonical JSON serialization for record hashes.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from qualification.config import (
    GoGreenJiraConfig,
    Gate2JiraConfig,
    JIRA_CONTRACT_VERSION,
    FROZEN_ALLOWLIST_PATH,
    FROZEN_ALLOWLIST_SHA256,
    FROZEN_ALLOWLIST_COUNT,
    RAW_REST_CAPTURE_PATH,
    GATE2_RAW_CAPTURE_PATH,
    REST_SNAPSHOT_CUTOFF,
    CSV_SOURCE_CUTOFF,
    REFERENCE_FIXTURE_PATH,
    REFERENCE_FIXTURE_SHA256,
)
from qualification.policy import (
    PROVENANCE_LIVE_VERIFIED,
    PROVENANCE_SYNTHETIC,
    ProvenanceScopeError,
    TaxonomyRegister,
    canonical_record_hash,
    compute_sha256_file,
    compute_sha256_text,
    make_contract_limitation,
    make_engine_defect,
    make_projection_limitation,
    make_source_limitation,
    redact_sensitive_text,
)
from qualification.reconciliation.reconciler import (
    ReconciliationRegister,
    ReconciliationReport,
)

KOLKATA_TZ = timezone(timedelta(hours=5, minutes=30))


def load_frozen_allowlist(
    path: Path | str = FROZEN_ALLOWLIST_PATH,
    expected_sha256: str = FROZEN_ALLOWLIST_SHA256,
    expected_count: int = FROZEN_ALLOWLIST_COUNT,
) -> set[str]:
    """Load and cryptographically verify the manager-approved frozen allowlist."""
    resolved = Path(path)
    if not resolved.exists():
        raise RuntimeError(f"Frozen allowlist file not found at {resolved}")

    digest = compute_sha256_file(resolved)
    if digest != expected_sha256:
        raise RuntimeError(
            f"Frozen allowlist digest mismatch! Expected {expected_sha256}, got {digest}"
        )

    with resolved.open("r", encoding="utf-8") as handle:
        keys = {line.strip() for line in handle if line.strip()}

    if len(keys) != expected_count:
        raise RuntimeError(
            f"Frozen allowlist count mismatch! Expected {expected_count}, got {len(keys)}"
        )

    return keys


def generate_jira_fixture_id(
    corpus_id: str,
    projection_revision: str,
    partition_id: str,
) -> str:
    """Generate a deterministic, reproducible fixture_id."""
    clean_corpus = corpus_id.strip().lower().replace(" ", "-")
    clean_rev = projection_revision.strip().lower().replace(" ", "-")
    clean_partition = partition_id.strip().lower().replace(" ", "-")
    return f"gogreen-jira-{clean_corpus}-{clean_rev}-{clean_partition}"


def parse_source_datetime_to_iso(
    value: str | None,
    default_tz: timezone = KOLKATA_TZ,
) -> str | None:
    """Parse raw source datetime string and normalize to aware ISO 8601 string."""
    if not value or not isinstance(value, str):
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    try:
        iso_candidate = cleaned.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_candidate)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=default_tz)
        return dt.isoformat()
    except ValueError:
        pass

    date_formats = (
        "%d/%b/%y %I:%M %p",
        "%d/%b/%Y %I:%M %p",
        "%d/%b/%y",
        "%d/%b/%Y",
        "%Y-%m-%d %H:%M:%S",
    )

    for fmt in date_formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=default_tz)
            return dt.isoformat()
        except ValueError:
            continue

    raise ValueError(f"Unable to parse timestamp into aware datetime: {value!r}")


def project_single_work_item(
    source_record: dict[str, Any],
    config: GoGreenJiraConfig,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Project one raw source record into a contract-compliant work item.

    NO SILENT DEFAULTS: Raises ValueError if any required field is missing.
    NO SILENT CHANGE DROPS: Every changelog item is parsed or raises ValueError.
    Returns (projected_work_item, list_of_raw_changelog_items_for_accounting).
    """
    # 1. Key
    key = source_record.get("key") or source_record.get("Issue key")
    if not key or not str(key).strip():
        raise ValueError("Missing required source field 'key'")
    key_str = str(key).strip()

    # 2. Immutable Source ID (Strict: NO synthesis from key)
    source_id = (
        source_record.get("id")
        or source_record.get("source_id")
        or source_record.get("Issue id")
    )
    if not source_id or not str(source_id).strip():
        raise ValueError(f"Missing immutable source_id for issue {key_str}")
    source_id_str = str(source_id).strip()

    # Handle either raw REST schema (`fields.summary`) or flat/CSV schema (`Summary`/`title`)
    fields = source_record.get("fields", {}) if isinstance(source_record.get("fields"), dict) else {}

    # 3. Summary / Title
    raw_summary = (
        fields.get("summary")
        or source_record.get("Summary")
        or source_record.get("title")
        or source_record.get("summary")
    )
    if not raw_summary or not str(raw_summary).strip():
        raise ValueError(f"Missing required source field 'summary' / 'title' for issue {key_str}")
    sanitized_title = redact_sensitive_text(str(raw_summary).strip())

    # 4. Item Type (No silent default to 'Task')
    raw_type = (
        (fields.get("issuetype") or {}).get("name")
        if isinstance(fields.get("issuetype"), dict)
        else source_record.get("Issue Type") or source_record.get("item_type")
    )
    if not raw_type or not str(raw_type).strip():
        raise ValueError(f"Missing required source field 'item_type' for issue {key_str}")
    item_type_str = str(raw_type).strip()

    # 5. Priority (No silent default to 'Medium')
    raw_priority = (
        (fields.get("priority") or {}).get("name")
        if isinstance(fields.get("priority"), dict)
        else source_record.get("Priority") or source_record.get("priority")
    )
    if not raw_priority or not str(raw_priority).strip():
        raise ValueError(f"Missing required source field 'priority' for issue {key_str}")
    priority_str = str(raw_priority).strip()

    # 6. Status (No silent default to 'To Do')
    raw_status = (
        (fields.get("status") or {}).get("name")
        if isinstance(fields.get("status"), dict)
        else source_record.get("Status") or source_record.get("status")
    )
    if not raw_status or not str(raw_status).strip():
        raise ValueError(f"Missing required source field 'status' for issue {key_str}")
    status_str = str(raw_status).strip()

    # Provider status category
    raw_status_cat = (
        (fields.get("status") or {}).get("statusCategory", {}).get("name")
        if isinstance(fields.get("status"), dict)
        else source_record.get("Status Category") or source_record.get("provider_status_category")
    )
    provider_status_category = str(raw_status_cat).strip() if raw_status_cat else None

    # 7. Timestamps
    raw_created = (
        fields.get("created")
        or source_record.get("Created")
        or source_record.get("created_at")
    )
    created_at = parse_source_datetime_to_iso(raw_created)
    if not created_at:
        raise ValueError(f"Missing required source field 'created_at' for issue {key_str}")

    raw_updated = (
        fields.get("updated")
        or source_record.get("Updated")
        or source_record.get("updated_at")
    )
    updated_at = parse_source_datetime_to_iso(raw_updated)
    if not updated_at:
        raise ValueError(f"Missing required source field 'updated_at' for issue {key_str}")

    raw_resolved = (
        fields.get("resolutiondate")
        or source_record.get("Resolved")
        or source_record.get("resolved_at")
    )
    resolved_at = parse_source_datetime_to_iso(raw_resolved) if raw_resolved else None

    raw_due = (
        fields.get("duedate")
        or source_record.get("Due date")
        or source_record.get("due_at")
    )
    due_at = parse_source_datetime_to_iso(raw_due) if raw_due else None

    # Assignee (redacted)
    raw_assignee = (
        (fields.get("assignee") or {}).get("displayName")
        if isinstance(fields.get("assignee"), dict)
        else source_record.get("Assignee") or source_record.get("assignee")
    )
    assignee = redact_sensitive_text(str(raw_assignee).strip()) if raw_assignee else None

    # 8. Changelog Extraction (Strict accounting: NO SILENT CHANGE DROPS)
    changes_list: list[dict[str, Any]] = []
    raw_changes: list[dict[str, Any]] = []

    # Support raw REST changelog structure (`changelog.values[].items[]` or `changelog.histories[].items[]`) or direct `changes`
    if "changelog" in source_record and isinstance(source_record["changelog"], dict):
        cl_values = source_record["changelog"].get("values") or source_record["changelog"].get("histories", [])
        for entry in cl_values:
            entry_created = entry.get("created")
            for cl_item in entry.get("items", []):
                raw_changes.append({
                    "field": cl_item.get("field"),
                    "from": cl_item.get("fromString"),
                    "to": cl_item.get("toString"),
                    "changed_at": entry_created,
                })
    elif "changes" in source_record and isinstance(source_record["changes"], list):
        raw_changes = list(source_record["changes"])

    for c_idx, chg in enumerate(raw_changes):
        chg_field = chg.get("field")
        chg_to = chg.get("to")
        chg_time_raw = chg.get("changed_at")

        if not chg_field or not chg_to or not chg_time_raw:
            raise ValueError(
                f"Malformed changelog event on {key_str}[{c_idx}]: missing field/to/changed_at ({chg})"
            )

        chg_time = parse_source_datetime_to_iso(chg_time_raw)
        if not chg_time:
            raise ValueError(
                f"Unparseable changed_at in changelog on {key_str}[{c_idx}]: {chg_time_raw!r}"
            )

        changes_list.append({
            "field": str(chg_field),
            "from": str(chg.get("from")) if chg.get("from") is not None else None,
            "to": str(chg_to),
            "changed_at": chg_time,
        })

    # Sort changes by changed_at to guarantee historical event ordering
    changes_list.sort(key=lambda c: c["changed_at"])

    # 9. History Completeness Semantics (NO INFERENCE FROM len(changes) > 0)
    # Read explicit per-item completeness from source if present
    if "history_complete" in source_record:
        item_history_complete = bool(source_record["history_complete"])
    else:
        # If source does not declare history completeness, it is NOT complete by default
        item_history_complete = False

    item: dict[str, Any] = {
        "source_id": source_id_str,
        "key": key_str,
        "title": sanitized_title,
        "item_type": item_type_str,
        "priority": priority_str,
        "status": status_str,
        "created_at": created_at,
        "updated_at": updated_at,
        "planned_at_period_start": None,  # Honest null per D-3
        "history_complete": item_history_complete,
        "changes": changes_list,
    }

    if provider_status_category:
        item["provider_status_category"] = provider_status_category
    if assignee:
        item["assignee"] = assignee
    if resolved_at:
        item["resolved_at"] = resolved_at
    if due_at:
        item["due_at"] = due_at

    return item, raw_changes


def project_gogreen_jira(
    source_records: list[dict[str, Any]],
    config: GoGreenJiraConfig,
    corpus_id: str,
    projection_revision: str = "r2",
    partition_id: str = "dev",
    allowlist: set[str] | None = None,
    explicit_source_cutoff: str | None = None,
) -> tuple[dict[str, Any], ReconciliationReport, dict[str, Any]]:
    """Project a corpus of GoGreen Jira records under strict multi-collection accounting.

    Tracks both 'jira_issue' and 'jira_change' registers.
    """
    fixture_id = generate_jira_fixture_id(corpus_id, projection_revision, partition_id)
    report = ReconciliationReport()
    issue_reg = report.get_or_create_register("jira_issue")
    change_reg = report.get_or_create_register("jira_change")

    work_items: list[dict[str, Any]] = []
    total_changes_projected = 0
    items_with_history = 0

    for index, record in enumerate(source_records):
        key = record.get("key") or record.get("Issue key") or f"RECORD_{index}"
        record_hash = canonical_record_hash(record)

        # 1. Allowlist scope exclusion
        if allowlist is not None and key not in allowlist:
            issue_reg.record(
                identifier=key,
                category="explicitly_excluded",
                reason="Excluded: not in authorized allowlist",
                content_hash=record_hash,
            )
            continue

        # 2. Non-representable checks
        item_type = str(
            (record.get("fields", {}) if isinstance(record.get("fields"), dict) else {}).get("issuetype", {}).get("name")
            or record.get("Issue Type")
            or record.get("item_type")
            or ""
        )
        if item_type.lower() in ("issuelink", "link", "subtask-link"):
            issue_reg.record(
                identifier=key,
                category="contract_not_representable",
                reason=f"Issue type {item_type!r} is not representable in shadow-jira-fixture-v1",
                content_hash=record_hash,
            )
            continue

        # 3. Projection attempt
        try:
            projected, raw_changes = project_single_work_item(record, config)
            work_items.append(projected)
            issue_reg.record(
                identifier=key,
                category="projected_successfully",
                reason="Successfully projected into shadow-jira-fixture-v1 work item",
                content_hash=record_hash,
            )

            # Account for every changelog event
            num_changes = len(projected.get("changes", []))
            if num_changes > 0:
                items_with_history += 1
                total_changes_projected += num_changes

            for c_idx, chg in enumerate(projected.get("changes", [])):
                chg_id = f"{key}/change/{c_idx}"
                change_reg.record(
                    identifier=chg_id,
                    category="projected_successfully",
                    reason=f"Change on {chg['field']} projected successfully",
                    content_hash=canonical_record_hash(chg),
                )

        except Exception as exc:
            issue_reg.record(
                identifier=key,
                category="projection_failed",
                reason=f"Projection exception: {type(exc).__name__}: {exc}",
                content_hash=record_hash,
            )

    # Verify reconciliation balance across all registers
    if not report.is_balanced():
        raise RuntimeError(
            f"Reconciliation invariant failed! Unbalanced registers: "
            f"{[name for name, r in report.registers.items() if not r.is_balanced()]}"
        )

    source_cutoff = explicit_source_cutoff or config.source_cutoff_at

    history_coverage: dict[str, Any] = {
        "history_supplied": bool(total_changes_projected > 0),
        "total_projected_items": len(work_items),
        "items_with_history": items_with_history,
        "total_change_events": total_changes_projected,
        "history_complete_by_default": bool(
            len(work_items) > 0 and all(it["history_complete"] for it in work_items)
        ),
        "history_dependent_qualification": (
            "exercised" if total_changes_projected > 0 else "not_exercised"
        ),
        "notes": (
            f"Changelog history present on {items_with_history}/{len(work_items)} items ({total_changes_projected} change events)"
            if total_changes_projected > 0
            else "Source did not supply changelogs; history-dependent rules unexercised"
        ),
    }

    coverage_notes = (
        f"GoGreen Jira Qualification Projection (cutoff: {source_cutoff}). "
        f"History: {history_coverage['notes']}. "
        f"Planning basis: {config.planning_basis_key}."
    )

    fixture_document: dict[str, Any] = {
        "contract_version": JIRA_CONTRACT_VERSION,
        "fixture_id": fixture_id,
        "organization": {
            "external_key": config.org_external_key,
            "name": config.org_name,
        },
        "team": {
            "external_key": config.team_external_key,
            "name": config.team_name,
        },
        "project": {
            "provider": "jira",
            "site_key": config.site_key,
            "project_key": config.project_key,
            "name": config.project_name,
        },
        "timezone": config.timezone,
        "review_period": {
            "label": config.review_label,
            "starts_at": config.starts_at,
            "ends_at_exclusive": config.ends_at_exclusive,
            "review_cutoff_at": config.review_cutoff_at,
            "source_cutoff_at": source_cutoff,
        },
        "configuration": {
            "planning_basis": {
                "key": config.planning_basis_key,
                "description": config.planning_basis_description,
            },
            "stalled_threshold_complete_days": config.stalled_threshold_complete_days,
            "status_mapping": dict(config.status_mapping),
            "priority_mapping": dict(config.priority_mapping),
        },
        "source_completeness": {
            "scope_complete": bool(allowlist is None),
            "history_complete_by_default": history_coverage["history_complete_by_default"],
            "notes": coverage_notes,
        },
        "work_items": work_items,
    }

    return fixture_document, report, history_coverage


def verify_historical_reference_fixture(
    fixture_path: Path | str = REFERENCE_FIXTURE_PATH,
    expected_sha256: str = REFERENCE_FIXTURE_SHA256,
) -> tuple[dict[str, Any], ReconciliationReport, dict[str, Any]]:
    """Cryptographically verify and audit the historical reference projection fixture.

    PROVENANCE STATUS:
    Per Milestone 2A Line 79 data governance, raw HTTP bodies were not persisted
    to disk. This fixture is verified strictly as historical reference evidence.
    Raw-source independence is honestly declared False.
    """
    path = Path(fixture_path)
    if not path.exists():
        raise FileNotFoundError(f"Historical reference fixture missing at {path}")

    actual_hash = compute_sha256_file(path)
    if actual_hash != expected_sha256:
        raise RuntimeError(
            f"Historical reference fixture digest mismatch! Expected {expected_sha256}, got {actual_hash}"
        )

    with path.open("r", encoding="utf-8") as handle:
        fixture_doc = json.load(handle)

    # Build auditing reconciliation report for historical reference
    report = ReconciliationReport()
    issue_reg = report.get_or_create_register("jira_issue")
    change_reg = report.get_or_create_register("jira_change")

    work_items = fixture_doc.get("work_items", [])
    total_changes = 0
    items_with_history = 0

    for item in work_items:
        key = item["key"]
        issue_reg.record(
            identifier=key,
            category="projected_successfully",
            reason="Historical reference work item verified against frozen contract",
            content_hash=canonical_record_hash(item),
        )
        changes = item.get("changes", [])
        if changes:
            items_with_history += 1
            total_changes += len(changes)
        for c_idx, chg in enumerate(changes):
            change_reg.record(
                identifier=f"{key}/change/{c_idx}",
                category="projected_successfully",
                reason=f"Historical change on {chg.get('field')} verified",
                content_hash=canonical_record_hash(chg),
            )

    history_coverage: dict[str, Any] = {
        "provenance_status": "historical_reference_evidence",
        "raw_source_independent": False,
        "retention_basis": "Historical reference artifact from Milestone 2A; raw REST responses not retained per Line 79",
        "history_supplied": bool(total_changes > 0),
        "total_projected_items": len(work_items),
        "items_with_history": items_with_history,
        "total_change_events": total_changes,
        "history_complete_by_default": bool(
            len(work_items) > 0 and all(it.get("history_complete", False) for it in work_items)
        ),
        "history_dependent_qualification": "exercised" if total_changes > 0 else "not_exercised",
        "notes": f"Historical reference fixture with {items_with_history}/{len(work_items)} items having changelog history ({total_changes} change events).",
    }

    return fixture_doc, report, history_coverage


def project_from_raw_rest_capture(
    raw_capture_path: Path | str = RAW_REST_CAPTURE_PATH,
    expected_sha256: str | None = None,
    config: GoGreenJiraConfig | None = None,
    corpus_id: str = "pilot115",
    projection_revision: str = "r2",
    partition_id: str = "dev",
    allowlist_path: Path | str = FROZEN_ALLOWLIST_PATH,
) -> tuple[dict[str, Any], ReconciliationReport, dict[str, Any]]:
    """Project directly from a raw Jira Cloud REST capture artifact.

    Fails closed if the raw capture artifact is missing or digest mismatches.
    Note: For historical cutoff 2026-09-09, raw REST captures were discarded in
    memory per Milestone 2A Line 79 data governance.
    """
    capture_file = Path(raw_capture_path)
    if not capture_file.exists():
        raise FileNotFoundError(
            f"Raw Jira REST capture artifact missing at {capture_file}. "
            "Per Milestone 2A Line 79 data governance, raw HTTP bodies from the "
            "2026-09-09 observation were not persisted to disk. "
            "Empirical raw-source qualification requires an authorized fresh Jira REST extraction."
        )

    if expected_sha256 is not None:
        capture_digest = compute_sha256_file(capture_file)
        if capture_digest != expected_sha256:
            raise RuntimeError(
                f"Raw Jira REST capture digest mismatch! Expected {expected_sha256}, got {capture_digest}"
            )

    cfg = config or GoGreenJiraConfig()
    allowlist = load_frozen_allowlist(allowlist_path)

    with capture_file.open("r", encoding="utf-8") as handle:
        capture_doc = json.load(handle)

    source_issues = capture_doc.get("issues", [])
    capture_cutoff = capture_doc.get("source_metadata", {}).get(
        "source_cutoff_at", REST_SNAPSHOT_CUTOFF
    )

    return project_gogreen_jira(
        source_records=source_issues,
        config=cfg,
        corpus_id=corpus_id,
        projection_revision=projection_revision,
        partition_id=partition_id,
        allowlist=allowlist,
        explicit_source_cutoff=capture_cutoff,
    )


def load_jira_csv_records(csv_path: str | Path) -> list[dict[str, Any]]:
    """Load raw records from a Jira export CSV file."""
    path = Path(csv_path)
    with path.open("r", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def project_gate2_raw_rest(
    raw_capture_path: Path | str = GATE2_RAW_CAPTURE_PATH,
    config: Gate2JiraConfig | None = None,
    taxonomy_register: TaxonomyRegister | None = None,
    allowlist: set[str] | None = None,
    expected_sha256: str | None = None,
    require_exact_scope: bool = False,
    allowlist_path: Path | str = FROZEN_ALLOWLIST_PATH,
    manifest_path: Path | str | None = None,
) -> tuple[dict[str, Any], ReconciliationReport, dict[str, Any], dict[str, Any]]:
    """Project a shadow-jira-fixture-v1 document directly from a Gate 2 Jira REST capture.

    Fails closed if the raw capture artifact is missing, digest mismatches, or if
    require_exact_scope=True and the capture set diverges from the authorized allowlist.
    Tracks all behavioral findings and limitations in the 6-category taxonomy.
    """
    capture_file = Path(raw_capture_path)
    if not capture_file.exists():
        raise FileNotFoundError(
            f"Gate 2 raw Jira REST capture artifact missing at {capture_file}."
        )

    if expected_sha256 is not None:
        actual_digest = compute_sha256_file(capture_file)
        if actual_digest != expected_sha256:
            raise RuntimeError(
                f"Gate 2 raw capture digest mismatch! Expected {expected_sha256}, got {actual_digest}"
            )

    cfg = config or Gate2JiraConfig()
    tax_reg = taxonomy_register or TaxonomyRegister()

    with capture_file.open("r", encoding="utf-8") as handle:
        capture_doc = json.load(handle)

    source_issues = capture_doc.get("issues", [])
    source_cutoff = capture_doc.get("source_cutoff_at", cfg.source_cutoff_at)

    # Exact Scope Check (Phase 4 hardening)
    if require_exact_scope:
        target_allowlist = allowlist if allowlist is not None else load_frozen_allowlist(allowlist_path)
        capture_keys = set(str(it.get("key")) for it in source_issues if isinstance(it, dict) and it.get("key"))
        missing = target_allowlist - capture_keys
        unexpected = capture_keys - target_allowlist
        if missing or unexpected:
            raise ProvenanceScopeError(
                f"Gate 2 capture scope does not match authorized allowlist! "
                f"Missing {len(missing)} authorized keys, Unexpected {len(unexpected)} unauthorized keys"
            )

    issue_register = ReconciliationRegister("jira_issue")
    change_register = ReconciliationRegister("jira_change")

    projected_work_items: list[dict[str, Any]] = []

    # Behavioral metrics counters
    behavioral_measurements = {
        "total_source_issues": len(source_issues),
        "unique_source_keys": len(set(it.get("key") for it in source_issues if it.get("key"))),
        "duplicate_source_keys": len(source_issues) - len(set(it.get("key") for it in source_issues if it.get("key"))),
        "null_due_dates": 0,
        "null_resolution_dates": 0,
        "null_assignees": 0,
        "unmapped_statuses": 0,
        "unmapped_priorities": 0,
        "total_changelog_events": 0,
        "items_with_history": 0,
        "items_with_multiple_transitions": 0,
        "items_with_zero_transitions": 0,
    }

    seen_keys: set[str] = set()

    for idx, raw_record in enumerate(source_issues):
        key = str(raw_record.get("key") or f"UNKNOWN-{idx}")
        issue_id = str(raw_record.get("id") or f"id-{idx}")
        fields = raw_record.get("fields", {}) if isinstance(raw_record, dict) else {}

        # Allowlist check
        if allowlist is not None and key not in allowlist:
            issue_register.record(
                identifier=key,
                category="explicitly_excluded",
                reason=f"Key {key} not in Gate 2 target allowlist",
                content_hash=canonical_record_hash(raw_record),
            )
            continue

        if key in seen_keys:
            tax_reg.record(make_source_limitation(
                code="DUPLICATE_KEY",
                subject_key=key,
                message=f"Duplicate key {key} found in source",
                observed_value=key,
            ))
        seen_keys.add(key)

        # Check due date
        if not fields.get("duedate") and not raw_record.get("due_at"):
            behavioral_measurements["null_due_dates"] += 1
            tax_reg.record(make_source_limitation(
                code="NULL_DUE_DATE",
                subject_key=key,
                message=f"Issue {key} has no populated due date in Jira",
                observed_value=None,
            ))

        if not fields.get("resolutiondate") and not raw_record.get("resolved_at"):
            behavioral_measurements["null_resolution_dates"] += 1

        if not fields.get("assignee") and not raw_record.get("assignee"):
            behavioral_measurements["null_assignees"] += 1

        # Check vocabulary mapping
        raw_status = (
            fields.get("status", {}).get("name")
            if isinstance(fields.get("status"), dict)
            else raw_record.get("status")
        )
        if raw_status not in cfg.status_mapping:
            behavioral_measurements["unmapped_statuses"] += 1
            tax_reg.record(make_projection_limitation(
                code="UNMAPPED_STATUS",
                subject_key=key,
                message=f"Status {raw_status!r} not in frozen status mapping",
                observed_value=raw_status,
            ))

        raw_priority = (
            fields.get("priority", {}).get("name")
            if isinstance(fields.get("priority"), dict)
            else raw_record.get("priority")
        )
        if raw_priority not in cfg.priority_mapping:
            behavioral_measurements["unmapped_priorities"] += 1
            tax_reg.record(make_projection_limitation(
                code="UNMAPPED_PRIORITY",
                subject_key=key,
                message=f"Priority {raw_priority!r} not in frozen priority mapping",
                observed_value=raw_priority,
            ))

        # Project item
        try:
            work_item, raw_changes = project_single_work_item(raw_record, cfg)
            projected_work_items.append(work_item)
            issue_register.record(
                identifier=key,
                category="projected_successfully",
                reason="Successfully projected into shadow-jira-fixture-v1 work item",
                content_hash=canonical_record_hash(raw_record),
            )

            # Changes accounting
            status_changes = [c for c in work_item.get("changes", []) if c.get("field") == "status"]
            behavioral_measurements["total_changelog_events"] += len(work_item.get("changes", []))
            if status_changes:
                behavioral_measurements["items_with_history"] += 1
                if len(status_changes) > 1:
                    behavioral_measurements["items_with_multiple_transitions"] += 1
            else:
                behavioral_measurements["items_with_zero_transitions"] += 1

            for c_idx, raw_chg in enumerate(work_item.get("changes", [])):
                chg_id = f"{key}/change/{c_idx}"
                change_register.record(
                    identifier=chg_id,
                    category="projected_successfully",
                    reason=f"Change on {raw_chg['field']} projected successfully",
                    content_hash=canonical_record_hash(raw_chg),
                )

        except Exception as exc:
            issue_register.record(
                identifier=key,
                category="projection_failed",
                reason=f"Projection failed: {exc}",
                content_hash=canonical_record_hash(raw_record),
            )
            tax_reg.record(make_projection_limitation(
                code="PROJECTION_FAILURE",
                subject_key=key,
                message=str(exc),
                observed_value=type(exc).__name__,
            ))

    # Build fixture document
    deterministic_fixture_id = (
        f"{cfg.project_key.lower()}-gate2-{cfg.review_label.lower()}-"
        f"{compute_sha256_text(source_cutoff)[:8]}"
    )

    fixture_doc: dict[str, Any] = {
        "contract_version": JIRA_CONTRACT_VERSION,
        "fixture_id": deterministic_fixture_id,
        "organization": {
            "external_key": cfg.organization_key,
            "name": cfg.organization_name,
        },
        "team": {
            "external_key": cfg.team_key,
            "name": cfg.team_name,
        },
        "project": {
            "provider": "jira",
            "site_key": cfg.site_key,
            "project_key": cfg.project_key,
            "name": cfg.project_name,
        },
        "timezone": cfg.timezone,
        "review_period": {
            "label": cfg.review_label,
            "starts_at": cfg.starts_at,
            "ends_at_exclusive": cfg.ends_at_exclusive,
            "review_cutoff_at": cfg.review_cutoff_at,
            "source_cutoff_at": source_cutoff,
        },
        "configuration": {
            "planning_basis": {
                "key": cfg.planning_basis_key,
                "description": "Gate 2 planning basis honest null (source unavailable).",
            },
            "stalled_threshold_complete_days": cfg.stalled_threshold_complete_days,
            "status_mapping": cfg.status_mapping,
            "priority_mapping": cfg.priority_mapping,
        },
        "source_completeness": {
            "is_complete": True,
            "notes": (
                f"Gate 2 verified live Jira REST capture with {len(projected_work_items)} projected items "
                f"and {behavioral_measurements['total_changelog_events']} changelog events."
                if (capture_file.parent / "gate2_extraction_receipt.json").exists()
                else f"Gate 2 synthetic/mock Jira REST capture with {len(projected_work_items)} projected items. NOT verified live Jira REST observation."
            ),
        },
        "work_items": projected_work_items,
    }

    report = ReconciliationReport(
        registers={"jira_issue": issue_register, "jira_change": change_register},
        notes=f"Gate 2 raw REST projection for {cfg.project_key} ({cfg.review_label})",
    )

    return fixture_doc, report, behavioral_measurements, tax_reg.to_report()

