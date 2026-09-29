"""Bounded In-Memory Provenance Dereferencing and Validation (Milestone 2 / P3-05).

Provides deterministic, in-memory dereferencing of ProvenanceRef.record_locator
and ProvenanceRef.source_field_path against validated in-memory fixtures.

Design Rules & Invariants:
1. ZERO external I/O: No network, no filesystem, no database access.
2. Fail-closed semantics: Unknown, out-of-bounds, or malformed locators return
   explicit structured failure states rather than raising unhandled exceptions.
3. Never convert UNAVAILABLE or NOT_FOUND into False.
4. Verify locator grammar, collection authorization, index bounds, entity identity,
   and optional source field presence.
5. Emits canonical QualityIssue instances matching QualityCode vocabulary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from shadow_orbit.evidence_types import (
    EntityRef,
    ProvenanceRef,
    QualityCode,
    QualityIssue,
)


ProvenanceResolutionStatus = Literal[
    "RESOLVED",
    "NOT_FOUND",
    "ACCESS_DENIED",
    "UNAVAILABLE",
    "MALFORMED_LOCATOR",
    "UNSUPPORTED_LOCATOR",
    "STALE",
    "AMBIGUOUS",
    "INVALID",
]
"""Closed set of provenance dereferencing outcomes (Pass 4 / ADR-004)."""

_AUTHORIZED_COLLECTIONS: frozenset[str] = frozenset({
    "work_items",
    "repositories",
    "branches",
    "commits",
    "pull_requests",
    "reviews",
})

_SEGMENT_REGEX = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\[([^\[\]]+)\]$")


@dataclass(frozen=True, slots=True)
class LocatorSegment:
    """A single segment in a dotted locator path (e.g. 'repositories[0]')."""

    collection: str
    selector: int | str
    is_index: bool


@dataclass(frozen=True, slots=True)
class DereferenceResult:
    """The result of dereferencing a provenance locator and source field path."""

    status: ProvenanceResolutionStatus
    record: Any | None = None
    field_value: Any | None = None
    error_message: str | None = None
    quality_issue: QualityIssue | None = None

    @property
    def is_resolved(self) -> bool:
        return self.status == "RESOLVED"


def parse_locator(locator: str | None) -> tuple[tuple[LocatorSegment, ...], str | None]:
    """Parse a record_locator string into a tuple of LocatorSegments.

    Returns (segments, error_message). On parse error, segments is empty and
    error_message describes the grammar violation.
    """
    if locator is None:
        return (), "Locator is None"

    clean = locator.strip()
    if not clean:
        return (), "Locator is empty"

    parts = clean.split(".")
    segments: list[LocatorSegment] = []

    for part in parts:
        if not part:
            return (), f"Empty segment in locator '{locator}'"
        match = _SEGMENT_REGEX.fullmatch(part)
        if not match:
            return (), f"Segment '{part}' violates grammar 'collection[selector]'"

        col, sel = match.group(1), match.group(2)
        if not col or not sel:
            return (), f"Malformed segment '{part}'"

        if col not in _AUTHORIZED_COLLECTIONS:
            return (), f"Collection '{col}' is not an authorized locator collection"

        if sel.isdigit():
            segments.append(LocatorSegment(collection=col, selector=int(sel), is_index=True))
        else:
            segments.append(LocatorSegment(collection=col, selector=sel, is_index=False))

    return tuple(segments), None


def _extract_container_dict(fixture: Any) -> dict[str, Any] | None:
    """Extract a dictionary representation from a fixture or fixture wrapper."""
    if fixture is None:
        return None
    if isinstance(fixture, dict):
        return fixture
    if hasattr(fixture, "raw_document") and isinstance(fixture.raw_document, dict):
        return fixture.raw_document
    return None


def _resolve_selector_in_list(
    collection: str,
    selector: int | str,
    is_index: bool,
    items: list[Any] | tuple[Any, ...],
) -> tuple[Any | None, ProvenanceResolutionStatus, str | None]:
    """Resolve a single segment selector against a list or tuple of items."""
    if is_index:
        idx = int(selector)
        if 0 <= idx < len(items):
            return items[idx], "RESOLVED", None

        # Out-of-bounds index: check if selector was intended as a numeric ID (e.g. PR number or source_id)
        # before failing with NOT_FOUND.
        ident = str(selector)
        matches: list[Any] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            matched = False
            if collection == "pull_requests":
                matched = str(item.get("number")) == ident
            elif collection == "work_items":
                matched = (
                    str(item.get("source_id")) == ident
                    or str(item.get("id")) == ident
                    or item.get("key") == ident
                )
            elif collection == "repositories":
                matched = str(item.get("repo_id")) == ident or item.get("name") == ident
            elif collection == "branches":
                matched = item.get("name") == ident
            elif collection == "commits":
                matched = str(item.get("sha")) == ident
            elif collection == "reviews":
                matched = str(item.get("review_id")) == ident or str(item.get("id")) == ident
            if matched:
                matches.append(item)

        if len(matches) == 1:
            return matches[0], "RESOLVED", None
        if len(matches) > 1:
            return (
                None,
                "AMBIGUOUS",
                f"Numeric selector '{selector}' is ambiguous in collection '{collection}' ({len(matches)} matches found)",
            )

        return (
            None,
            "NOT_FOUND",
            f"Index {idx} out of bounds for collection '{collection}' of size {len(items)}",
        )

    # String identifier matching
    ident = str(selector)
    matches: list[Any] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        matched = False
        if collection == "work_items":
            matched = (
                item.get("key") == ident
                or str(item.get("source_id")) == ident
                or str(item.get("id")) == ident
            )
        elif collection == "repositories":
            matched = (
                str(item.get("repo_id")) == ident
                or item.get("name") == ident
                or f"{item.get('owner')}/{item.get('name')}" == ident
            )
        elif collection == "branches":
            matched = item.get("name") == ident
        elif collection == "commits":
            matched = (
                str(item.get("sha")) == ident
                or (len(ident) >= 7 and str(item.get("sha", "")).startswith(ident))
            )
        elif collection == "pull_requests":
            matched = (
                str(item.get("number")) == ident
                or item.get("title") == ident
            )
        elif collection == "reviews":
            matched = str(item.get("review_id")) == ident or str(item.get("id")) == ident
        else:
            matched = False

        if matched:
            matches.append(item)

    if len(matches) == 1:
        return matches[0], "RESOLVED", None
    if len(matches) == 0:
        return None, "NOT_FOUND", f"Identifier '{ident}' not found in collection '{collection}'"
    return (
        None,
        "AMBIGUOUS",
        f"Identifier '{ident}' is ambiguous in collection '{collection}' ({len(matches)} matches found)",
    )


def _verify_entity_identity(
    resolved_record: dict[str, Any],
    expected_ref: EntityRef,
) -> tuple[bool, str | None]:
    """Verify that resolved record identity matches the expected EntityRef."""
    kind = expected_ref.entity_kind
    expected_id = expected_ref.entity_id

    if kind == "jira_issue":
        key = resolved_record.get("key")
        source_id = str(resolved_record.get("source_id", ""))
        raw_id = str(resolved_record.get("id", ""))
        if expected_id not in (key, source_id, raw_id):
            return (
                False,
                f"Resolved Jira record key '{key}' does not match expected entity_id '{expected_id}'",
            )
        return True, None

    if kind == "github_repository":
        repo_id = str(resolved_record.get("repo_id", ""))
        owner_name = f"{resolved_record.get('owner')}/{resolved_record.get('name')}"
        name = str(resolved_record.get("name", ""))
        if expected_id not in (repo_id, owner_name, name):
            return (
                False,
                f"Resolved GitHub repository '{repo_id}' does not match expected entity_id '{expected_id}'",
            )
        return True, None

    if kind == "github_branch":
        name = str(resolved_record.get("name", ""))
        if expected_id != name and not expected_id.endswith(f"/{name}"):
            return (
                False,
                f"Resolved GitHub branch '{name}' does not match expected entity_id '{expected_id}'",
            )
        return True, None

    if kind == "github_commit":
        sha = str(resolved_record.get("sha", ""))
        if expected_id != sha and not expected_id.endswith(f"/{sha}"):
            return (
                False,
                f"Resolved GitHub commit sha '{sha}' does not match expected entity_id '{expected_id}'",
            )
        return True, None

    if kind == "github_pull_request":
        num = str(resolved_record.get("number", ""))
        if expected_id != num and not expected_id.endswith(f"/{num}"):
            return (
                False,
                f"Resolved GitHub PR number '{num}' does not match expected entity_id '{expected_id}'",
            )
        return True, None

    if kind == "github_review":
        rid = str(resolved_record.get("review_id", ""))
        if expected_id != rid and not expected_id.endswith(f"/{rid}"):
            return (
                False,
                f"Resolved GitHub review id '{rid}' does not match expected entity_id '{expected_id}'",
            )
        return True, None

    return True, None


def _traverse_field_path(
    record: dict[str, Any],
    field_path: str,
) -> tuple[bool, Any | None]:
    """Traverse a dotted field path inside a record."""
    if not field_path:
        return True, record

    parts = field_path.split(".")
    curr: Any = record

    for p in parts:
        if isinstance(curr, dict) and p in curr:
            curr = curr[p]
        elif isinstance(curr, dict) and "fields" in curr and isinstance(curr["fields"], dict) and p in curr["fields"]:
            # Fallback for Jira raw fields sub-dictionary
            curr = curr["fields"][p]
        else:
            return False, None

    return True, curr


def dereference_locator(
    locator: str | None,
    fixture: Any,
    expected_entity_ref: EntityRef | None = None,
    source_field_path: str | None = None,
    source_cutoff_at: datetime | None = None,
) -> DereferenceResult:
    """Deterministically dereference a provenance locator against an in-memory fixture.

    Parameters
    ----------
    locator:
        The record_locator string (e.g. 'work_items[0]', 'repositories[0].branches[main]').
    fixture:
        An in-memory dictionary or fixture dataclass (ValidatedFixture, NormalizedFixture, etc.).
    expected_entity_ref:
        Optional EntityRef to verify identity alignment against the dereferenced record.
    source_field_path:
        Optional field path to verify and extract from the dereferenced record.
    source_cutoff_at:
        Optional cutoff timestamp to check for post-cutoff stale records.

    Returns
    -------
    DereferenceResult containing resolution status, dereferenced record, field value,
    and a structured QualityIssue if resolution failed.
    """
    if fixture is None:
        msg = "Source fixture is unavailable for in-memory dereferencing"
        return DereferenceResult(
            status="UNAVAILABLE",
            error_message=msg,
            quality_issue=QualityIssue(
                code="unresolved",
                message=msg,
                subject_ref=expected_entity_ref,
                subject_scope="provenance:fixture",
            ),
        )

    container = _extract_container_dict(fixture)
    if container is None:
        msg = f"Fixture object of type '{type(fixture).__name__}' has no accessible document dictionary"
        return DereferenceResult(
            status="UNAVAILABLE",
            error_message=msg,
            quality_issue=QualityIssue(
                code="unresolved",
                message=msg,
                subject_ref=expected_entity_ref,
                subject_scope="provenance:fixture",
            ),
        )

    segments, parse_error = parse_locator(locator)
    if parse_error is not None:
        clean_loc = locator or "<None>"
        status: ProvenanceResolutionStatus = (
            "UNSUPPORTED_LOCATOR" if "not an authorized" in parse_error else "MALFORMED_LOCATOR"
        )
        quality_code: QualityCode = "unsupported_value" if status == "UNSUPPORTED_LOCATOR" else "invalid"
        return DereferenceResult(
            status=status,
            error_message=parse_error,
            quality_issue=QualityIssue(
                code=quality_code,
                message=f"Locator '{clean_loc}' error: {parse_error}",
                subject_ref=expected_entity_ref,
                subject_scope="provenance:locator",
            ),
        )

    # Walk through segments
    curr_node: Any = container

    for i, seg in enumerate(segments):
        if not isinstance(curr_node, dict):
            msg = f"Cannot resolve collection '{seg.collection}' in non-object node at segment {i}"
            return DereferenceResult(
                status="NOT_FOUND",
                error_message=msg,
                quality_issue=QualityIssue(
                    code="unresolved",
                    message=msg,
                    subject_ref=expected_entity_ref,
                    subject_scope="provenance:locator",
                ),
            )

        items = curr_node.get(seg.collection)
        if items is None or not isinstance(items, (list, tuple)):
            msg = f"Collection '{seg.collection}' not found or not a list at segment {i}"
            return DereferenceResult(
                status="NOT_FOUND",
                error_message=msg,
                quality_issue=QualityIssue(
                    code="unresolved",
                    message=msg,
                    subject_ref=expected_entity_ref,
                    subject_scope="provenance:locator",
                ),
            )

        resolved_item, res_status, res_err = _resolve_selector_in_list(
            collection=seg.collection,
            selector=seg.selector,
            is_index=seg.is_index,
            items=items,
        )

        if res_status != "RESOLVED":
            code: QualityCode = "invalid" if res_status == "AMBIGUOUS" else "unresolved"
            return DereferenceResult(
                status=res_status,
                error_message=res_err,
                quality_issue=QualityIssue(
                    code=code,
                    message=res_err or f"Failed resolving segment '{seg.collection}[{seg.selector}]'",
                    subject_ref=expected_entity_ref,
                    subject_scope="provenance:locator",
                ),
            )

        curr_node = resolved_item

    # Top-level resolved record
    resolved_record = curr_node
    if not isinstance(resolved_record, dict):
        msg = f"Resolved locator '{locator}' yielded non-dictionary record"
        return DereferenceResult(
            status="INVALID",
            record=resolved_record,
            error_message=msg,
            quality_issue=QualityIssue(
                code="invalid",
                message=msg,
                subject_ref=expected_entity_ref,
                subject_scope="provenance:record",
            ),
        )

    # Check Access Denied flag
    if resolved_record.get("access_denied") is True or resolved_record.get("error") == "access_denied":
        msg = f"Access denied to source record for locator '{locator}'"
        return DereferenceResult(
            status="ACCESS_DENIED",
            record=resolved_record,
            error_message=msg,
            quality_issue=QualityIssue(
                code="unsupported_value",
                message=msg,
                subject_ref=expected_entity_ref,
                subject_scope="provenance:access",
            ),
        )

    # Check Entity Identity if requested
    if expected_entity_ref is not None:
        identity_ok, id_err = _verify_entity_identity(resolved_record, expected_entity_ref)
        if not identity_ok:
            return DereferenceResult(
                status="INVALID",
                record=resolved_record,
                error_message=id_err,
                quality_issue=QualityIssue(
                    code="contradictory",
                    message=id_err or "Entity identity contradiction",
                    subject_ref=expected_entity_ref,
                    subject_scope="provenance:identity",
                ),
            )

    # Check Field Path if requested
    field_value: Any | None = None
    if source_field_path is not None and source_field_path.strip():
        field_exists, extracted_val = _traverse_field_path(resolved_record, source_field_path.strip())
        if not field_exists:
            msg = f"Field '{source_field_path}' does not exist on resolved record for locator '{locator}'"
            return DereferenceResult(
                status="NOT_FOUND",
                record=resolved_record,
                field_value=None,
                error_message=msg,
                quality_issue=QualityIssue(
                    code="missing",
                    message=msg,
                    subject_ref=expected_entity_ref,
                    subject_scope="provenance:field",
                ),
            )
        field_value = extracted_val

    # Check Stale Cutoff if provided
    if source_cutoff_at is not None:
        rec_time_str = resolved_record.get("updated_at") or resolved_record.get("committed_at")
        if isinstance(rec_time_str, str):
            try:
                # Basic ISO parse for temporal bound check
                dt = datetime.fromisoformat(rec_time_str.replace("Z", "+00:00"))
                if dt > source_cutoff_at:
                    msg = f"Resolved record timestamp ({rec_time_str}) postdates source cutoff ({source_cutoff_at.isoformat()})"
                    return DereferenceResult(
                        status="STALE",
                        record=resolved_record,
                        field_value=field_value,
                        error_message=msg,
                        quality_issue=QualityIssue(
                            code="invalid",
                            message=msg,
                            subject_ref=expected_entity_ref,
                            subject_scope="provenance:temporal",
                        ),
                    )
            except (ValueError, TypeError):
                pass

    return DereferenceResult(
        status="RESOLVED",
        record=resolved_record,
        field_value=field_value,
        error_message=None,
        quality_issue=None,
    )


def dereference_provenance_ref(
    prov_ref: ProvenanceRef,
    fixture: Any,
    expected_entity_ref: EntityRef | None = None,
    source_cutoff_at: datetime | None = None,
) -> DereferenceResult:
    """Convenience helper dereferencing a ProvenanceRef dataclass."""
    return dereference_locator(
        locator=prov_ref.record_locator,
        fixture=fixture,
        expected_entity_ref=expected_entity_ref,
        source_field_path=prov_ref.source_field_path,
        source_cutoff_at=source_cutoff_at,
    )
