"""Artifact Retention, Security, and Privacy/Redaction Policy for Qualification.

This module formalizes:
1. Prohibited fields that must never appear in repository artifacts.
2. Redaction and sanitization helpers for audit records.
3. Cryptographic hash helpers for deterministic tracking (canonical JSON hashing).
4. Retention guidelines for raw source material vs. derived qualification artifacts.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ATL_TRACE_ID_REGEX = re.compile(r"^[0-9a-f]{32}$")
X_REQUEST_ID_REGEX = re.compile(r"^[0-9a-zA-Z_-]+$")


PROHIBITED_KEY_PATTERNS: tuple[str, ...] = (
    r"email",
    r"token",
    r"password",
    r"secret",
    r"credential",
    r"cookie",
    r"auth",
    r"bearer",
    r"session",
    r"api[_-]?key",
)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
TOKEN_REGEX = re.compile(r"(?:bearer\s+[a-zA-Z0-9_.-]+|ghp_[a-zA-Z0-9]{36}|atlassian_[a-zA-Z0-9=+/]+)", re.IGNORECASE)


def compute_sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hexadecimal digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_sha256_text(text: str) -> str:
    """Compute SHA-256 hexadecimal digest of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_sha256_file(path: str | Path) -> str:
    """Compute SHA-256 hexadecimal digest of a file on disk."""
    resolved = Path(path)
    hasher = hashlib.sha256()
    with resolved.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def canonical_record_hash(record: Any) -> str:
    """Compute canonical SHA-256 digest of nested records via sorted-key JSON.

    Guarantees consistent hashing across nested dictionaries, lists, Unicode,
    and varying key order.
    """
    canonical_json = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return compute_sha256_text(canonical_json)


def is_prohibited_field_name(key: str) -> bool:
    """Check if a dictionary key matches any prohibited sensitive pattern."""
    key_lower = key.lower()
    for pattern in PROHIBITED_KEY_PATTERNS:
        if re.search(pattern, key_lower):
            return True
    return False


def redact_sensitive_text(text: str) -> str:
    """Scrub emails, bearer tokens, and credentials from free text."""
    if not text:
        return text
    scrubbed = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    scrubbed = TOKEN_REGEX.sub("[REDACTED_TOKEN]", scrubbed)
    return scrubbed


def sanitize_source_excerpt(text: str, max_chars: int = 120) -> str:
    """Produce a bounded, redacted excerpt for human audit records."""
    if not text:
        return ""
    scrubbed = redact_sensitive_text(text)
    if len(scrubbed) > max_chars:
        return scrubbed[: max_chars - 3] + "..."
    return scrubbed


# ── Six-Category Taxonomy for Gate 2 Behavioral Classification ───────────────

@dataclass(frozen=True, slots=True)
class TaxonomyEntry:
    """Base entry for qualification behavioral taxonomy."""
    category: str
    code: str
    subject_key: str
    message: str
    remediation_action: str
    observed_value: Any = None


def make_source_limitation(code: str, subject_key: str, message: str, observed_value: Any = None) -> TaxonomyEntry:
    return TaxonomyEntry(
        category="source_limitation",
        code=code,
        subject_key=subject_key,
        message=message,
        remediation_action="Record honest null; emit QualityIssue",
        observed_value=observed_value,
    )


def make_projection_limitation(code: str, subject_key: str, message: str, observed_value: Any = None) -> TaxonomyEntry:
    return TaxonomyEntry(
        category="projection_limitation",
        code=code,
        subject_key=subject_key,
        message=message,
        remediation_action="Account in contract_not_representable register",
        observed_value=observed_value,
    )


def make_contract_limitation(code: str, subject_key: str, message: str, observed_value: Any = None) -> TaxonomyEntry:
    return TaxonomyEntry(
        category="contract_limitation",
        code=code,
        subject_key=subject_key,
        message=message,
        remediation_action="Document contract limitation; do NOT modify frozen schema",
        observed_value=observed_value,
    )


def make_engine_defect(code: str, subject_key: str, message: str, observed_value: Any = None) -> TaxonomyEntry:
    return TaxonomyEntry(
        category="engine_defect",
        code=code,
        subject_key=subject_key,
        message=message,
        remediation_action="Record reproducible defect; DO NOT patch engine during freeze",
        observed_value=observed_value,
    )


def make_environment_limitation(code: str, subject_key: str, message: str, observed_value: Any = None) -> TaxonomyEntry:
    return TaxonomyEntry(
        category="environment_limitation",
        code=code,
        subject_key=subject_key,
        message=message,
        remediation_action="Document environmental constraint",
        observed_value=observed_value,
    )


def make_harness_defect(code: str, subject_key: str, message: str, observed_value: Any = None) -> TaxonomyEntry:
    return TaxonomyEntry(
        category="harness_defect",
        code=code,
        subject_key=subject_key,
        message=message,
        remediation_action="Fix qualification code outside src/shadow_orbit/",
        observed_value=observed_value,
    )


class TaxonomyRegister:
    """Register for categorizing all behavioral findings and limitations."""

    def __init__(self) -> None:
        self.entries: list[TaxonomyEntry] = []

    def record(self, entry: TaxonomyEntry) -> None:
        self.entries.append(entry)

    def count_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {
            "source_limitation": 0,
            "projection_limitation": 0,
            "contract_limitation": 0,
            "engine_defect": 0,
            "environment_limitation": 0,
            "harness_defect": 0,
        }
        for entry in self.entries:
            counts[entry.category] = counts.get(entry.category, 0) + 1
        return counts

    def to_report(self) -> dict[str, Any]:
        return {
            "summary_counts": self.count_by_category(),
            "total_entries": len(self.entries),
            "entries": [
                {
                    "category": e.category,
                    "code": e.code,
                    "subject_key": e.subject_key,
                    "message": e.message,
                    "action": e.remediation_action,
                    "observed_value": str(e.observed_value) if e.observed_value is not None else None,
                }
                for e in self.entries
            ],
        }


# ── Provenance Lifecycle & Verification States ────────────────────────────────

PROVENANCE_SYNTHETIC: str = "SYNTHETIC"
PROVENANCE_REPLAY: str = "REPLAY"
PROVENANCE_REFERENCE_FIXTURE: str = "REFERENCE_FIXTURE"
PROVENANCE_LIVE_PENDING: str = "LIVE_REST_CAPTURE_PENDING_VERIFICATION"
PROVENANCE_LIVE_VERIFIED: str = "LIVE_REST_CAPTURE_VERIFIED"

VALID_PROVENANCE_STATUSES: frozenset[str] = frozenset({
    PROVENANCE_SYNTHETIC,
    PROVENANCE_REPLAY,
    PROVENANCE_REFERENCE_FIXTURE,
    PROVENANCE_LIVE_PENDING,
    PROVENANCE_LIVE_VERIFIED,
})


class ProvenanceError(Exception):
    """Base exception for qualification provenance failures."""
    pass


class ProvenanceScopeError(ProvenanceError):
    """Raised when captured issues do not exactly match the authorized allowlist."""
    pass


class ProvenanceReceiptError(ProvenanceError):
    """Raised when extraction receipt is missing, tampered, or inconsistent."""
    pass


class ProvenanceSecurityError(ProvenanceError):
    """Raised when sensitive credentials or tokens are detected in artifacts."""
    pass


def compute_execution_witness(transactions: list[dict[str, Any]]) -> str:
    """Compute deterministic cryptographic execution witness across transaction chain.

    Binds the exact chronological sequence of HTTP transactions, including
    transport trace identifiers, response sizes, latencies, endpoints, and status codes.
    """
    hasher = hashlib.sha256()
    for tx in transactions:
        canonical = (
            f"{tx.get('request_timestamp')}|{tx.get('method')}|{tx.get('endpoint')}|"
            f"{tx.get('status_code')}|{tx.get('latency_ms')}|{tx.get('response_bytes')}|"
            f"{tx.get('atl_trace_id')}|{tx.get('x_a_request_id')}"
        )
        hasher.update(canonical.encode("utf-8"))
    return hasher.hexdigest()


def compute_runtime_signature(
    runtime_token: str,
    run_id: str,
    base_url: str,
    allowlist_sha256: str,
    execution_witness: str,
) -> str:
    """Compute HMAC-SHA256 runtime signature binding extractor session to execution witness."""
    key = hashlib.sha256(f"orbit-jira-extractor-runtime:{runtime_token}".encode("utf-8")).digest()
    payload = f"{run_id}|{base_url}|{allowlist_sha256}|{execution_witness}".encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def verify_extraction_provenance(
    manifest: dict[str, Any],
    raw_capture_path: Path | str,
    inventory_path: Path | str,
    receipt_path: Path | str | None,
    allowlist_keys: set[str],
    expected_allowlist_sha256: str,
) -> str:
    """Strictly verify extraction provenance.

    Fails closed if an artifact claims live/authentic status without valid receipts,
    two-pass execution evidence, authentic Atlassian transport trace telemetry,
    cryptographic execution witness, exact scope matching, and security scrubbing.

    Hashes verify artifact integrity; they DO NOT verify provenance on their own.
    """
    prov_status = manifest.get("provenance_status")
    if prov_status not in VALID_PROVENANCE_STATUSES and prov_status != "AUTHENTIC_RAW_REST_CAPTURE":
        raise ProvenanceError(f"Unknown or invalid provenance_status: {prov_status!r}")

    # Synthetic or replay artifacts must never claim raw source independence or be promoted to live
    if prov_status in (PROVENANCE_SYNTHETIC, PROVENANCE_REPLAY, PROVENANCE_REFERENCE_FIXTURE):
        if manifest.get("raw_source_independence") is True:
            raise ProvenanceError(
                f"Provenance violation: {prov_status} artifact cannot claim raw_source_independence=True"
            )
        if manifest.get("historical_api_responses_retained") is True:
            raise ProvenanceError(
                f"Provenance violation: {prov_status} artifact cannot claim historical_api_responses_retained=True"
            )
        if manifest.get("is_empirical_live_source") is True:
            raise ProvenanceError(
                f"Provenance violation: {prov_status} artifact cannot claim is_empirical_live_source=True"
            )
        return prov_status

    # Claiming live / authentic capture requires strict evidence verification
    # 1. Missing receipt fails closed
    if receipt_path is None:
        raise ProvenanceReceiptError("Live REST capture requires an extraction receipt; none was provided")

    r_path = Path(receipt_path)
    if not r_path.exists():
        raise ProvenanceReceiptError(f"Live REST extraction receipt missing at {r_path}")

    # Check manifest receipt hash binding
    actual_receipt_hash = compute_sha256_file(r_path)
    declared_receipt_hash = manifest.get("receipt_sha256")
    if declared_receipt_hash and declared_receipt_hash != actual_receipt_hash:
        raise ProvenanceReceiptError(
            f"Manifest receipt_sha256 mismatch! Declared {declared_receipt_hash}, actual {actual_receipt_hash}"
        )

    with r_path.open("r", encoding="utf-8") as f:
        receipt_data = json.load(f)

    # 2. Check allowlist binding in receipt
    if receipt_data.get("allowlist_sha256") != expected_allowlist_sha256:
        raise ProvenanceScopeError(
            f"Receipt allowlist hash {receipt_data.get('allowlist_sha256')} does not match "
            f"authorized scope lock {expected_allowlist_sha256}"
        )

    # 3. Check raw capture file existence & hash binding
    cap_path = Path(raw_capture_path)
    if not cap_path.exists():
        raise ProvenanceReceiptError(f"Raw capture file missing at {cap_path}")
    actual_cap_hash = compute_sha256_file(cap_path)
    if receipt_data.get("raw_capture_sha256") and receipt_data["raw_capture_sha256"] != actual_cap_hash:
        raise ProvenanceReceiptError("Receipt raw_capture_sha256 does not match actual raw capture file hash")
    if manifest.get("raw_capture_sha256") and manifest["raw_capture_sha256"] != actual_cap_hash:
        raise ProvenanceReceiptError("Manifest raw_capture_sha256 does not match actual raw capture file hash")

    with cap_path.open("r", encoding="utf-8") as f:
        capture_data = json.load(f)

    capture_issues = capture_data.get("issues", [])
    capture_keys = set(it.get("key") for it in capture_issues if isinstance(it, dict) and it.get("key"))

    # 4. Exact Scope Check (Fail closed on missing or unexpected keys)
    missing = allowlist_keys - capture_keys
    unexpected = capture_keys - allowlist_keys
    if missing or unexpected:
        raise ProvenanceScopeError(
            f"Authorized scope mismatch! Missing {len(missing)} keys, Unexpected {len(unexpected)} keys"
        )

    # 5. Check two-pass execution integrity in receipt
    if not (receipt_data.get("pass_a_completed") and receipt_data.get("pass_b_completed")):
        raise ProvenanceReceiptError("Receipt does not confirm two-pass observation completion")
    if not receipt_data.get("fingerprints_matched"):
        raise ProvenanceReceiptError("Receipt records fingerprint mismatch between Pass A and Pass B")
    if receipt_data.get("pass_a_count") != len(allowlist_keys):
        raise ProvenanceReceiptError(
            f"Receipt Pass A count ({receipt_data.get('pass_a_count')}) != allowlist count ({len(allowlist_keys)})"
        )
    if receipt_data.get("pass_b_count") != len(allowlist_keys):
        raise ProvenanceReceiptError(
            f"Receipt Pass B count ({receipt_data.get('pass_b_count')}) != allowlist count ({len(allowlist_keys)})"
        )
    if receipt_data.get("is_live_extraction") is not True:
        raise ProvenanceReceiptError("Extraction receipt does not assert is_live_extraction=True")
    if receipt_data.get("source_base_url") != "https://tecblic.atlassian.net":
        raise ProvenanceReceiptError(
            f"Receipt source_base_url {receipt_data.get('source_base_url')!r} does not match authorized Jira Cloud domain"
        )

    # 6. Check endpoint inventory existence & hash binding
    inv_path = Path(inventory_path)
    if not inv_path.exists():
        raise ProvenanceReceiptError(f"Endpoint inventory missing at {inv_path}")
    actual_inv_hash = compute_sha256_file(inv_path)
    if receipt_data.get("endpoint_inventory_sha256") and receipt_data["endpoint_inventory_sha256"] != actual_inv_hash:
        raise ProvenanceReceiptError("Receipt endpoint_inventory_sha256 does not match actual inventory file hash")
    if manifest.get("endpoint_inventory_sha256") and manifest["endpoint_inventory_sha256"] != actual_inv_hash:
        raise ProvenanceReceiptError("Manifest endpoint_inventory_sha256 does not match actual inventory file hash")

    with inv_path.open("r", encoding="utf-8") as f:
        inv_data = json.load(f)

    # Security scan: immediately fail closed if sensitive credentials or tokens are present
    for doc, name in [(manifest, "manifest"), (receipt_data, "receipt"), (inv_data, "inventory")]:
        doc_str = json.dumps(doc).lower()
        if "bearer" in doc_str or "basic " in doc_str or "api_token" in doc_str or "password" in doc_str:
            raise ProvenanceSecurityError(f"Potential credential or authorization token detected in {name}")

    transactions = inv_data.get("transactions", [])
    min_expected_txs = 2 * len(allowlist_keys)
    if len(transactions) < min_expected_txs:
        raise ProvenanceReceiptError(
            f"Endpoint inventory has only {len(transactions)} transactions; two-pass extraction requires at least {min_expected_txs}"
        )
    if receipt_data.get("transactions_count") and receipt_data["transactions_count"] != len(transactions):
        raise ProvenanceReceiptError(
            f"Receipt transactions_count ({receipt_data['transactions_count']}) != actual ({len(transactions)})"
        )

    # 7. Capture-Inventory Consistency and Key Coverage Binding
    key_pattern = re.compile(r"^/rest/api/3/issue/([A-Z0-9]+-\d+)")
    tx_key_counts: dict[str, int] = {}
    for tx in transactions:
        endpoint = tx.get("endpoint", "")
        match = key_pattern.match(endpoint)
        if match:
            k = match.group(1)
            tx_key_counts[k] = tx_key_counts.get(k, 0) + 1

    missing_coverage = allowlist_keys - set(tx_key_counts.keys())
    if missing_coverage:
        raise ProvenanceScopeError(
            f"Endpoint inventory missing requests for {len(missing_coverage)} authorized keys: {sorted(list(missing_coverage))[:5]}"
        )

    insufficient_coverage = {k: c for k, c in tx_key_counts.items() if k in allowlist_keys and c < 2}
    if insufficient_coverage:
        raise ProvenanceReceiptError(
            f"Endpoint inventory lacks two-pass coverage for {len(insufficient_coverage)} keys (fewer than 2 requests per key)"
        )

    unexpected_tx_keys = set(tx_key_counts.keys()) - allowlist_keys
    if unexpected_tx_keys:
        raise ProvenanceScopeError(
            f"Endpoint inventory contains requests for unauthorized keys: {sorted(list(unexpected_tx_keys))[:5]}"
        )

    # 8. Upstream Atlassian Edge Transport Evidence
    trace_ids: list[str] = []
    request_ids: list[str] = []
    for idx, tx in enumerate(transactions):
        atl_trace = tx.get("atl_trace_id")
        if not atl_trace or not isinstance(atl_trace, str):
            raise ProvenanceReceiptError(
                f"Transaction {idx} missing authentic Atlassian transport trace header (atl_trace_id); "
                f"live provenance cannot be established from synthetic or unverified telemetry"
            )
        if not ATL_TRACE_ID_REGEX.match(atl_trace):
            raise ProvenanceReceiptError(
                f"Transaction {idx} atl_trace_id {atl_trace!r} does not match authentic Atlassian Edge trace ID format (32 hex characters)"
            )
        trace_ids.append(atl_trace)

        req_id = tx.get("x_a_request_id")
        if not req_id or not isinstance(req_id, str):
            raise ProvenanceReceiptError(
                f"Transaction {idx} missing Atlassian request ID (x_a_request_id)"
            )
        if not X_REQUEST_ID_REGEX.match(req_id):
            raise ProvenanceReceiptError(
                f"Transaction {idx} x_a_request_id {req_id!r} has invalid format"
            )
        request_ids.append(req_id)

        # Mandatory Atlassian Edge network transport headers
        server_hdr = tx.get("server")
        if not server_hdr or not isinstance(server_hdr, str) or not any(s in server_hdr.lower() for s in ("atlassian", "envoy", "cloudflare")):
            raise ProvenanceReceiptError(
                f"Transaction {idx} missing mandatory Atlassian Edge server header (e.g. atlassian-proxy, envoy): got {server_hdr!r}"
            )

        hsts_hdr = tx.get("strict_transport_security")
        if not hsts_hdr or not isinstance(hsts_hdr, str) or "max-age" not in hsts_hdr.lower():
            raise ProvenanceReceiptError(
                f"Transaction {idx} missing mandatory Atlassian strict_transport_security header: got {hsts_hdr!r}"
            )

        http_date = tx.get("http_date")
        if not http_date or not isinstance(http_date, str):
            raise ProvenanceReceiptError(
                f"Transaction {idx} missing mandatory Atlassian http_date header"
            )

        if tx.get("status_code") != 200:
            raise ProvenanceReceiptError(
                f"Transaction {idx} has non-200 status code: {tx.get('status_code')}"
            )
        if not tx.get("response_bytes") or tx.get("response_bytes", 0) <= 0:
            raise ProvenanceReceiptError(f"Transaction {idx} has non-positive response_bytes: {tx.get('response_bytes')}")
        if tx.get("latency_ms") is None or tx.get("latency_ms", 0) <= 0:
            raise ProvenanceReceiptError(f"Transaction {idx} has non-positive latency_ms: {tx.get('latency_ms')}")

    if len(set(trace_ids)) != len(transactions):
        raise ProvenanceReceiptError(
            f"Duplicate atl_trace_id detected in endpoint inventory ({len(set(trace_ids))} unique vs {len(transactions)} total); "
            f"transactions must each have a unique transport trace ID"
        )
    if len(set(request_ids)) != len(transactions):
        raise ProvenanceReceiptError(
            f"Duplicate x_a_request_id detected in endpoint inventory ({len(set(request_ids))} unique vs {len(transactions)} total)"
        )

    # 9. Cryptographic Execution Witness Verification
    receipt_witness = receipt_data.get("execution_witness")
    if not receipt_witness:
        raise ProvenanceReceiptError("Extraction receipt missing cryptographic execution_witness attestation")
    computed_witness = compute_execution_witness(transactions)
    if receipt_witness != computed_witness:
        raise ProvenanceReceiptError(
            f"Execution witness mismatch! Receipt declared {receipt_witness}, computed {computed_witness}"
        )

    # 10. Extractor Runtime Attestation Signature Verification
    runtime_sig = receipt_data.get("runtime_signature")
    runtime_tok = receipt_data.get("runtime_token")
    if not runtime_sig or not runtime_tok:
        raise ProvenanceReceiptError(
            "Provenance violation: Extraction receipt lacks authentic runtime extractor signature (runtime_token/runtime_signature)"
        )
    expected_sig = compute_runtime_signature(
        runtime_tok,
        receipt_data.get("run_id", ""),
        receipt_data.get("source_base_url", ""),
        receipt_data.get("allowlist_sha256", ""),
        receipt_data.get("execution_witness", ""),
    )
    if runtime_sig != expected_sig:
        raise ProvenanceReceiptError(
            f"Extraction receipt runtime signature mismatch! Declared {runtime_sig}, expected {expected_sig}"
        )

    # 11. Temporal Window & Monotonicity Verification
    start_ts_str = receipt_data.get("extraction_started_at")
    end_ts_str = receipt_data.get("extraction_completed_at")
    if not start_ts_str or not end_ts_str:
        raise ProvenanceReceiptError("Receipt missing extraction_started_at or extraction_completed_at")
    try:
        start_dt = datetime.fromisoformat(start_ts_str.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_ts_str.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProvenanceReceiptError(f"Invalid timestamp in extraction receipt: {exc}")

    if start_dt >= end_dt:
        raise ProvenanceReceiptError(
            f"Invalid extraction window: started_at ({start_ts_str}) >= completed_at ({end_ts_str})"
        )

    prev_dt = start_dt
    for idx, tx in enumerate(transactions):
        tx_ts_str = tx.get("request_timestamp")
        if not tx_ts_str:
            raise ProvenanceReceiptError(f"Transaction {idx} missing request_timestamp")
        try:
            tx_dt = datetime.fromisoformat(tx_ts_str.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ProvenanceReceiptError(f"Transaction {idx} has invalid request_timestamp: {exc}")

        if tx_dt < prev_dt:
            raise ProvenanceReceiptError(
                f"Transaction {idx} timestamp {tx_ts_str} is non-monotonic (precedes previous {prev_dt.isoformat()})"
            )
        if tx_dt > end_dt:
            raise ProvenanceReceiptError(
                f"Transaction {idx} timestamp {tx_ts_str} exceeds extraction_completed_at {end_ts_str}"
            )
        prev_dt = tx_dt

    return PROVENANCE_LIVE_VERIFIED

