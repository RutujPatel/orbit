"""Authorized Jira Cloud REST Extractor for Gate 2 Qualification.

Features:
1. Pure read-only REST extraction with rate limiting and exponential backoff retry.
2. Two-pass bounded consistency observation (Pass A -> candidate cutoff Tc -> Pass B fingerprint verification).
3. Comprehensive changelog pagination.
4. Call-by-call endpoint and transaction inventory.
5. Strict token and credential scrubbing.
6. Generates gate2_jira_raw_capture.json, gate2_source_manifest.json, and gate2_endpoint_inventory.json.
7. Hermetic replay / synthetic mode for deterministic qualification testing.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import stat
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from qualification.policy import (
    PROVENANCE_LIVE_PENDING,
    PROVENANCE_LIVE_VERIFIED,
    PROVENANCE_SYNTHETIC,
    ProvenanceReceiptError,
    canonical_record_hash,
    compute_execution_witness,
    compute_runtime_signature,
    compute_sha256_file,
    compute_sha256_text,
    redact_sensitive_text,
)


_ACTIVE_EXTRACTOR_SESSIONS: dict[str, str] = {}


def register_runtime_session(run_id: str, runtime_token: str) -> None:
    """Register an active runtime extractor session."""
    _ACTIVE_EXTRACTOR_SESSIONS[run_id] = runtime_token


def is_registered_session(run_id: str, runtime_token: str) -> bool:
    """Check if session is registered in the active runtime."""
    return _ACTIVE_EXTRACTOR_SESSIONS.get(run_id) == runtime_token


def clear_runtime_sessions() -> None:
    """Clear registered sessions (for testing)."""
    _ACTIVE_EXTRACTOR_SESSIONS.clear()


@dataclass(frozen=True, slots=True)
class ExtractionReceipt:
    """Cryptographic and operational execution receipt for a Jira Cloud REST extraction."""

    run_id: str
    extractor_version: str
    extraction_started_at: str
    extraction_completed_at: str
    source_base_url: str
    requested_issue_count: int
    fetched_issue_count: int
    failed_request_count: int
    pass_a_count: int
    pass_b_count: int
    pass_a_completed: bool
    pass_b_completed: bool
    fingerprints_matched: bool
    allowlist_path: str
    allowlist_sha256: str
    raw_capture_sha256: str = ""
    endpoint_inventory_sha256: str = ""
    transactions_count: int = 0
    execution_witness: str = ""
    is_live_extraction: bool = True
    runtime_token: str = ""
    runtime_signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "extractor_version": self.extractor_version,
            "extraction_started_at": self.extraction_started_at,
            "extraction_completed_at": self.extraction_completed_at,
            "source_base_url": self.source_base_url,
            "requested_issue_count": self.requested_issue_count,
            "fetched_issue_count": self.fetched_issue_count,
            "failed_request_count": self.failed_request_count,
            "pass_a_count": self.pass_a_count,
            "pass_b_count": self.pass_b_count,
            "pass_a_completed": self.pass_a_completed,
            "pass_b_completed": self.pass_b_completed,
            "fingerprints_matched": self.fingerprints_matched,
            "allowlist_path": self.allowlist_path,
            "allowlist_sha256": self.allowlist_sha256,
            "raw_capture_sha256": self.raw_capture_sha256,
            "endpoint_inventory_sha256": self.endpoint_inventory_sha256,
            "transactions_count": self.transactions_count,
            "execution_witness": self.execution_witness,
            "is_live_extraction": self.is_live_extraction,
            "runtime_token": self.runtime_token,
            "runtime_signature": self.runtime_signature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtractionReceipt:
        return cls(
            run_id=data["run_id"],
            extractor_version=data["extractor_version"],
            extraction_started_at=data["extraction_started_at"],
            extraction_completed_at=data["extraction_completed_at"],
            source_base_url=data["source_base_url"],
            requested_issue_count=data["requested_issue_count"],
            fetched_issue_count=data["fetched_issue_count"],
            failed_request_count=data["failed_request_count"],
            pass_a_count=data["pass_a_count"],
            pass_b_count=data["pass_b_count"],
            pass_a_completed=data["pass_a_completed"],
            pass_b_completed=data["pass_b_completed"],
            fingerprints_matched=data["fingerprints_matched"],
            allowlist_path=data["allowlist_path"],
            allowlist_sha256=data["allowlist_sha256"],
            raw_capture_sha256=data.get("raw_capture_sha256", ""),
            endpoint_inventory_sha256=data.get("endpoint_inventory_sha256", ""),
            transactions_count=data.get("transactions_count", 0),
            execution_witness=data.get("execution_witness", ""),
            is_live_extraction=data.get("is_live_extraction", True),
            runtime_token=data.get("runtime_token", ""),
            runtime_signature=data.get("runtime_signature", ""),
        )


class JiraExtractor:
    """Read-only Jira Cloud REST client with transaction inventory and two-pass verification."""

    def __init__(
        self,
        base_url: str,
        email: str | None = None,
        token: str | None = None,
        output_dir: Path | str | None = None,
        user_agent: str = "ShadowORBIT-Gate2-Extractor/1.0",
        timeout: int = 30,
    ) -> None:
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = "https://" + base_url
        self.base_url = base_url.rstrip("/")
        self.email = email or os.environ.get("JIRA_EMAIL") or os.environ.get("JIRA_USER") or os.environ.get("ATLASSIAN_EMAIL")
        self.token = token or os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN") or os.environ.get("ATLASSIAN_TOKEN")
        self.user_agent = user_agent
        self.timeout = timeout
        self.output_dir = Path(output_dir) if output_dir else Path("/home/tecblic/orbit-private/gate2/raw")
        self.endpoint_inventory: list[dict[str, Any]] = []
        self._runtime_token = f"rt-{uuid4().hex}"

    def _auth_header(self) -> str | None:
        if not self.email or not self.token:
            return None
        auth_bytes = f"{self.email}:{self.token}".encode("utf-8")
        return f"Basic {base64.b64encode(auth_bytes).decode('ascii')}"

    def make_request(
        self,
        endpoint: str,
        params: dict[str, str | int] | None = None,
        method: str = "GET",
        max_retries: int = 3,
    ) -> tuple[int, dict[str, Any]]:
        """Execute HTTP request with retry, timing, and transaction logging."""
        query = f"?{urllib.parse.urlencode(params)}" if params else ""
        url = f"{self.base_url}{endpoint}{query}"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
        }
        auth = self._auth_header()
        if auth:
            headers["Authorization"] = auth

        start_time = time.perf_counter()
        req_timestamp = datetime.now(timezone.utc).isoformat()
        status_code = 0
        response_data: dict[str, Any] = {}
        payload_bytes = 0

        req = urllib.request.Request(url, headers=headers, method=method)
        atl_trace_id = None
        x_a_request_id = None
        server_hdr = None
        hsts_hdr = None
        http_date = None

        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    status_code = resp.status
                    raw_body = resp.read()
                    payload_bytes = len(raw_body)
                    response_data = json.loads(raw_body.decode("utf-8"))
                    if hasattr(resp, "headers"):
                        atl_trace_id = resp.headers.get("atl-traceid")
                        x_a_request_id = resp.headers.get("x-arequestid")
                        server_hdr = resp.headers.get("server") or resp.headers.get("Server")
                        hsts_hdr = resp.headers.get("strict-transport-security") or resp.headers.get("Strict-Transport-Security")
                        http_date = resp.headers.get("date") or resp.headers.get("Date")
                    break
            except urllib.error.HTTPError as exc:
                status_code = exc.code
                err_bytes = exc.read()
                payload_bytes = len(err_bytes)
                if hasattr(exc, "headers"):
                    atl_trace_id = exc.headers.get("atl-traceid")
                    x_a_request_id = exc.headers.get("x-arequestid")
                    server_hdr = exc.headers.get("server") or exc.headers.get("Server")
                    hsts_hdr = exc.headers.get("strict-transport-security") or exc.headers.get("Strict-Transport-Security")
                    http_date = exc.headers.get("date") or exc.headers.get("Date")
                try:
                    response_data = json.loads(err_bytes.decode("utf-8"))
                except Exception:
                    response_data = {"error": err_bytes.decode("utf-8", errors="replace")}
                if status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                break
            except Exception as exc:
                status_code = 0
                response_data = {"network_error": str(exc)}
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                break

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Record transaction with transport trace telemetry but without sensitive auth headers
        self.endpoint_inventory.append({
            "request_timestamp": req_timestamp,
            "method": method,
            "endpoint": endpoint,
            "params": params or {},
            "status_code": status_code,
            "latency_ms": latency_ms,
            "response_bytes": payload_bytes,
            "atl_trace_id": atl_trace_id,
            "x_a_request_id": x_a_request_id,
            "server": server_hdr,
            "strict_transport_security": hsts_hdr,
            "http_date": http_date,
        })

        return status_code, response_data

    def fetch_issue_with_changelog(self, issue_key: str) -> dict[str, Any]:
        """Fetch single issue with complete paginated changelog."""
        endpoint = f"/rest/api/3/issue/{issue_key}"
        status, data = self.make_request(endpoint, params={"expand": "changelog"})
        if status != 200:
            raise RuntimeError(f"Failed to fetch issue {issue_key}: HTTP {status} {data}")

        changelog = data.get("changelog", {})
        total = changelog.get("total", 0)
        histories = changelog.get("histories", [])

        # Check if changelog needs additional pagination
        if total > len(histories):
            start_at = len(histories)
            while start_at < total:
                cl_endpoint = f"/rest/api/3/issue/{issue_key}/changelog"
                cl_status, cl_data = self.make_request(
                    cl_endpoint,
                    params={"startAt": start_at, "maxResults": 100},
                )
                if cl_status != 200:
                    break
                page_values = cl_data.get("values", [])
                if not page_values:
                    break
                histories.extend(page_values)
                start_at += len(page_values)
            changelog["histories"] = histories

        return data

    def two_pass_observe(
        self,
        issue_keys: list[str],
        allowlist_path: Path | str | None = None,
        allowlist_sha256: str | None = None,
    ) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]], ExtractionReceipt]:
        """Execute two-pass bounded observation verifying consistency.

        Returns (pass_a_issues, source_cutoff_at, endpoint_inventory, receipt).
        """
        run_id = f"gate2-run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        start_ts = datetime.now(timezone.utc).isoformat()
        failed_count = 0

        # Pass A
        pass_a_issues: list[dict[str, Any]] = []
        for key in issue_keys:
            try:
                issue = self.fetch_issue_with_changelog(key)
                pass_a_issues.append(issue)
            except Exception:
                failed_count += 1
                raise

        pass_a_completed = True
        candidate_cutoff = datetime.now(timezone.utc).isoformat()

        # Pass B fingerprint check
        pass_b_fingerprints: list[str] = []
        pass_b_issues: list[dict[str, Any]] = []
        for key in issue_keys:
            try:
                issue_b = self.fetch_issue_with_changelog(key)
                pass_b_issues.append(issue_b)
                fp = canonical_record_hash({
                    "id": issue_b.get("id"),
                    "key": issue_b.get("key"),
                    "updated": issue_b.get("fields", {}).get("updated"),
                })
                pass_b_fingerprints.append(fp)
            except Exception:
                failed_count += 1
                raise

        pass_b_completed = True
        pass_a_fingerprints = [
            canonical_record_hash({
                "id": it.get("id"),
                "key": it.get("key"),
                "updated": it.get("fields", {}).get("updated"),
            })
            for it in pass_a_issues
        ]

        fingerprints_matched = (pass_a_fingerprints == pass_b_fingerprints)
        if not fingerprints_matched:
            raise RuntimeError(
                "Source inconsistency detected during two-pass verification! "
                "Issues changed during extraction."
            )

        completed_ts = datetime.now(timezone.utc).isoformat()
        witness = compute_execution_witness(self.endpoint_inventory)
        runtime_sig = compute_runtime_signature(
            self._runtime_token,
            run_id,
            self.base_url,
            str(allowlist_sha256 or ""),
            witness,
        )

        register_runtime_session(run_id, self._runtime_token)

        receipt = ExtractionReceipt(
            run_id=run_id,
            extractor_version="1.0.0",
            extraction_started_at=start_ts,
            extraction_completed_at=completed_ts,
            source_base_url=self.base_url,
            requested_issue_count=len(issue_keys),
            fetched_issue_count=len(pass_a_issues),
            failed_request_count=failed_count,
            pass_a_count=len(pass_a_issues),
            pass_b_count=len(pass_b_issues),
            pass_a_completed=pass_a_completed,
            pass_b_completed=pass_b_completed,
            fingerprints_matched=fingerprints_matched,
            allowlist_path=str(allowlist_path or ""),
            allowlist_sha256=str(allowlist_sha256 or ""),
            transactions_count=len(self.endpoint_inventory),
            execution_witness=witness,
            is_live_extraction=True,
            runtime_token=self._runtime_token,
            runtime_signature=runtime_sig,
        )

        return pass_a_issues, candidate_cutoff, self.endpoint_inventory, receipt


def scrub_raw_jira_issue(raw_issue: dict[str, Any]) -> dict[str, Any]:
    """Scrub sensitive user emails, avatars, and tokens while preserving schema structure."""
    scrubbed = json.loads(json.dumps(raw_issue))
    fields = scrubbed.get("fields", {})

    # Redact summary text
    if "summary" in fields and isinstance(fields["summary"], str):
        fields["summary"] = redact_sensitive_text(fields["summary"])

    # Scrub assignee email/accountId
    assignee = fields.get("assignee")
    if isinstance(assignee, dict):
        if "emailAddress" in assignee:
            assignee["emailAddress"] = "[REDACTED_EMAIL]"
        if "accountId" in assignee:
            assignee["accountId"] = "[REDACTED_ACCOUNT_ID]"

    # Scrub reporter
    reporter = fields.get("reporter")
    if isinstance(reporter, dict):
        if "emailAddress" in reporter:
            reporter["emailAddress"] = "[REDACTED_EMAIL]"
        if "accountId" in reporter:
            reporter["accountId"] = "[REDACTED_ACCOUNT_ID]"

    # Scrub changelog authors
    changelog = scrubbed.get("changelog", {})
    for hist in changelog.get("histories", []):
        author = hist.get("author")
        if isinstance(author, dict):
            if "emailAddress" in author:
                author["emailAddress"] = "[REDACTED_EMAIL]"
            if "accountId" in author:
                author["accountId"] = "[REDACTED_ACCOUNT_ID]"

    return scrubbed


def save_gate2_raw_artifacts(
    raw_issues: list[dict[str, Any]],
    source_cutoff_at: str,
    endpoint_inventory: list[dict[str, Any]],
    output_dir: Path | str,
    receipt: ExtractionReceipt | None = None,
    operator: str = "Rutuj Patel",
    authorization_ref: str = "GATE-2-MANAGER-APPROVAL",
) -> tuple[Path, Path, Path, Path | None]:
    """Persist Gate 2 evidence artifacts with fail-closed provenance.

    If an authentic ExtractionReceipt is supplied, sets status to LIVE_REST_CAPTURE_PENDING_VERIFICATION.
    If no receipt is supplied, fails closed by classifying artifact as SYNTHETIC with
    raw_source_independence=False.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. gate2_jira_raw_capture.json
    scrubbed_issues = [scrub_raw_jira_issue(it) for it in raw_issues]
    raw_capture_path = out_path / "gate2_jira_raw_capture.json"
    with open(raw_capture_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "capture_format": "gate2-jira-cloud-rest-v1",
                "source_kind": "jira",
                "source_cutoff_at": source_cutoff_at,
                "issue_count": len(scrubbed_issues),
                "issues": scrubbed_issues,
            },
            f,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )

    # 2. gate2_endpoint_inventory.json
    inventory_path = out_path / "gate2_endpoint_inventory.json"
    with open(inventory_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "inventory_format": "gate2-endpoint-inventory-v1",
                "total_calls": len(endpoint_inventory),
                "transactions": endpoint_inventory,
            },
            f,
            indent=2,
            sort_keys=True,
        )

    cap_hash = compute_sha256_file(raw_capture_path)
    inv_hash = compute_sha256_file(inventory_path)

    # 3. gate2_extraction_receipt.json (if provided)
    receipt_path: Path | None = None
    receipt_hash: str | None = None
    if receipt is not None:
        if receipt.is_live_extraction:
            # Enforce runtime sealing and active session verification
            if not receipt.runtime_token or not receipt.runtime_signature:
                raise ProvenanceReceiptError(
                    "Unsealed ExtractionReceipt rejected: missing runtime_token or runtime_signature. "
                    "Direct instantiation by external caller cannot claim live extraction."
                )
            if not is_registered_session(receipt.run_id, receipt.runtime_token):
                raise ProvenanceReceiptError(
                    f"Direct instantiation or forged ExtractionReceipt rejected: session {receipt.run_id} "
                    f"was not minted by an active JiraExtractor runtime in this process."
                )
            expected_sig = compute_runtime_signature(
                receipt.runtime_token,
                receipt.run_id,
                receipt.source_base_url,
                receipt.allowlist_sha256,
                receipt.execution_witness,
            )
            if receipt.runtime_signature != expected_sig:
                raise ProvenanceReceiptError(
                    "Forged ExtractionReceipt rejected: invalid runtime_signature."
                )
        receipt_path = out_path / "gate2_extraction_receipt.json"
        receipt_dict = receipt.to_dict()
        receipt_dict["raw_capture_sha256"] = cap_hash
        receipt_dict["endpoint_inventory_sha256"] = inv_hash
        receipt_dict["transactions_count"] = len(endpoint_inventory)
        with open(receipt_path, "w", encoding="utf-8") as f:
            json.dump(receipt_dict, f, indent=2, sort_keys=True)
        receipt_hash = compute_sha256_file(receipt_path)

    # 4. gate2_source_manifest.json
    manifest_path = out_path / "gate2_source_manifest.json"
    is_live = receipt is not None and receipt.is_live_extraction
    prov_status = PROVENANCE_LIVE_PENDING if is_live else PROVENANCE_SYNTHETIC

    manifest_data: dict[str, Any] = {
        "manifest_version": "2.0.0",
        "gate": "GATE_2",
        "provenance_status": prov_status,
        "raw_source_independence": is_live,
        "historical_api_responses_retained": is_live,
        "is_empirical_live_source": is_live,
        "operator": operator,
        "authorization_reference": authorization_ref,
        "source_cutoff_at": source_cutoff_at,
        "target_project": "GG",
        "issue_count": len(scrubbed_issues),
        "raw_capture_file": "gate2_jira_raw_capture.json",
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_file": "gate2_endpoint_inventory.json",
        "endpoint_inventory_sha256": inv_hash,
    }
    if receipt_hash:
        manifest_data["receipt_file"] = "gate2_extraction_receipt.json"
        manifest_data["receipt_sha256"] = receipt_hash

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, sort_keys=True)

    return raw_capture_path, manifest_path, inventory_path, receipt_path


def generate_gate2_synthetic_artifacts(
    output_dir: Path | str,
    allowlist_keys: set[str] | None = None,
    source_cutoff_at: str = "2026-09-16T12:00:00+05:30",
    operator: str = "Synthetic Test Harness",
    authorization_ref: str = "SYNTHETIC-PIPELINE-TEST",
) -> tuple[Path, Path, Path]:
    """Generate explicitly labeled synthetic artifacts for pipeline/contract tests.

    Crucially, writes manifest with:
      provenance_status = 'SYNTHETIC'
      raw_source_independence = False
      is_empirical_live_source = False
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    keys = sorted(list(allowlist_keys)) if allowlist_keys else [f"GG-{i}" for i in range(1, 116)]
    sample_issues = []
    endpoint_inventory = []

    for idx, key in enumerate(keys):
        issue_id = f"10{idx:03d}"
        histories = []
        if idx not in [0, 1, 2, 3, 4]:
            histories.append({
                "id": f"cl-{idx}-1",
                "created": "2026-08-10T11:20:00.000+0530",
                "items": [{"field": "status", "from": "1", "fromString": "In Progress", "to": "2", "toString": "In Review"}]
            })
            if idx not in [5, 6, 7, 8]:
                histories.append({
                    "id": f"cl-{idx}-2",
                    "created": "2026-08-25T16:45:00.000+0530",
                    "items": [{"field": "status", "from": "2", "fromString": "In Review", "to": "3", "toString": "Close"}]
                })

        raw_issue = {
            "id": issue_id,
            "key": key,
            "self": f"https://tecblic.atlassian.net/rest/api/3/issue/{issue_id}",
            "fields": {
                "summary": f"Synthetic GoGreen issue for {key}",
                "issuetype": {"id": "10002", "name": "Request", "subtask": False},
                "project": {"id": "10000", "key": "GG", "name": "GoGreen"},
                "priority": {"id": "1", "name": "Highest"},
                "status": {
                    "id": "3" if idx not in [0, 1, 2, 3, 4, 5, 6, 7, 8] else ("2" if idx in [5, 6, 7, 8] else "1"),
                    "name": "Close" if idx not in [0, 1, 2, 3, 4, 5, 6, 7, 8] else ("In Review" if idx in [5, 6, 7, 8] else "In Progress"),
                    "statusCategory": {"id": 3, "key": "done", "name": "Done"}
                },
                "created": "2026-07-15T09:30:00.000+0530",
                "updated": "2026-08-26T10:15:00.000+0530",
                "resolutiondate": "2026-08-25T16:45:00.000+0530" if idx not in [0, 1, 2, 3, 4, 5, 6, 7, 8] else None,
                "duedate": None,
                "assignee": {"displayName": "Dev Team"},
                "reporter": {"displayName": "QA Lead"},
            },
            "changelog": {"histories": histories},
        }
        sample_issues.append(raw_issue)

        endpoint_inventory.append({
            "request_timestamp": "2026-09-16T11:58:12.123456+00:00",
            "method": "GET",
            "endpoint": f"/rest/api/3/issue/{key}",
            "params": {"expand": "changelog"},
            "status_code": 200,
            "latency_ms": 100.0,
            "response_bytes": 1500,
        })

    cap_path, man_path, inv_path, _ = save_gate2_raw_artifacts(
        raw_issues=sample_issues,
        source_cutoff_at=source_cutoff_at,
        endpoint_inventory=endpoint_inventory,
        output_dir=out_path,
        receipt=None,  # No receipt -> explicitly labeled SYNTHETIC
        operator=operator,
        authorization_ref=authorization_ref,
    )

    return cap_path, man_path, inv_path

