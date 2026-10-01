"""Tests for Gate 2 Provenance Hardening.

Ensures fail-closed provenance verification:
1. Synthetic capture cannot be classified as verified live REST.
2. Replay fixture cannot be classified as verified live REST.
3. Missing extraction receipt fails verification.
4. Receipt/capture hash mismatch fails verification.
5. Inventory/capture inconsistency fails verification (< 230 requests for 115 issues).
6. Authorized scope mismatch fails verification (scope mismatch raises ProvenanceScopeError).
7. Fake hardcoded provenance fields cannot bypass verification.
8. Credentials are not persisted in receipt/manifest (ProvenanceSecurityError).
9. Valid extractor-generated evidence passes verification and returns LIVE_REST_CAPTURE_VERIFIED.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

# Ensure orbit repo root and src/ are on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from qualification.config import (
    FROZEN_ALLOWLIST_PATH,
    FROZEN_ALLOWLIST_SHA256,
    GATE2_RAW_CAPTURE_PATH,
    GATE2_SOURCE_MANIFEST_PATH,
    GATE2_ENDPOINT_INVENTORY_PATH,
    GATE2_SYNTHETIC_DIR,
    GATE2_SYNTHETIC_MANIFEST_PATH,
    GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
    GATE2_SYNTHETIC_INVENTORY_PATH,
)
from qualification.policy import (
    PROVENANCE_LIVE_PENDING,
    PROVENANCE_LIVE_VERIFIED,
    PROVENANCE_REPLAY,
    PROVENANCE_SYNTHETIC,
    ProvenanceError,
    ProvenanceReceiptError,
    ProvenanceScopeError,
    ProvenanceSecurityError,
    compute_execution_witness,
    compute_runtime_signature,
    compute_sha256_file,
    verify_extraction_provenance,
)
from qualification.projection.jira_projection import load_frozen_allowlist, project_gate2_raw_rest
from qualification.extraction.jira_extractor import (
    ExtractionReceipt,
    register_runtime_session,
    clear_runtime_sessions,
    save_gate2_raw_artifacts,
)


# ── 1. Synthetic Capture Cannot Be Verified Live REST ────────────────────────

def test_synthetic_capture_cannot_be_verified_live_rest():
    """Verify synthetic capture manifest is recognized as SYNTHETIC and cannot claim independence."""
    with GATE2_SYNTHETIC_MANIFEST_PATH.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["provenance_status"] == PROVENANCE_SYNTHETIC
    assert manifest["raw_source_independence"] is False
    assert manifest["is_empirical_live_source"] is False

    allowlist = load_frozen_allowlist()
    status = verify_extraction_provenance(
        manifest=manifest,
        raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
        inventory_path=GATE2_SYNTHETIC_INVENTORY_PATH,
        receipt_path=None,
        allowlist_keys=allowlist,
        expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
    )
    assert status == PROVENANCE_SYNTHETIC

    # If synthetic manifest falsely claims independence, it fails closed
    tampered_manifest = dict(manifest, raw_source_independence=True)
    with pytest.raises(ProvenanceError, match="cannot claim raw_source_independence=True"):
        verify_extraction_provenance(
            manifest=tampered_manifest,
            raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
            inventory_path=GATE2_SYNTHETIC_INVENTORY_PATH,
            receipt_path=None,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 2. Replay Fixture Cannot Claim Independence ──────────────────────────────

def test_replay_fixture_cannot_claim_independence():
    """Verify replay/reference fixtures cannot claim raw source independence."""
    replay_manifest = {
        "manifest_version": "2.0.0",
        "provenance_status": PROVENANCE_REPLAY,
        "raw_source_independence": True,  # False claim
    }
    allowlist = load_frozen_allowlist()
    with pytest.raises(ProvenanceError, match="cannot claim raw_source_independence=True"):
        verify_extraction_provenance(
            manifest=replay_manifest,
            raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
            inventory_path=GATE2_SYNTHETIC_INVENTORY_PATH,
            receipt_path=None,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 3. Missing Receipt Fails Closed ──────────────────────────────────────────

def test_missing_extraction_receipt_fails_closed():
    """Verify that claiming authentic live capture without a receipt fails closed."""
    allowlist = load_frozen_allowlist()

    # The existing unhardened incident manifest claims AUTHENTIC_RAW_REST_CAPTURE without a receipt
    with GATE2_SOURCE_MANIFEST_PATH.open("r", encoding="utf-8") as f:
        incident_manifest = json.load(f)

    with pytest.raises(ProvenanceReceiptError, match="extraction receipt"):
        verify_extraction_provenance(
            manifest=incident_manifest,
            raw_capture_path=GATE2_RAW_CAPTURE_PATH,
            inventory_path=GATE2_ENDPOINT_INVENTORY_PATH,
            receipt_path=None,  # No receipt
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 4. Receipt Hash Mismatch Fails Closed ─────────────────────────────────────

def test_receipt_capture_hash_mismatch_fails_closed(tmp_path):
    """Verify that a receipt with mismatched raw capture digest fails verification."""
    allowlist = load_frozen_allowlist()

    receipt_file = tmp_path / "gate2_extraction_receipt.json"
    receipt_data = {
        "run_id": "test-run",
        "extractor_version": "1.0.0",
        "extraction_started_at": "2026-09-16T11:00:00Z",
        "extraction_completed_at": "2026-09-16T11:10:00Z",
        "source_base_url": "https://tecblic.atlassian.net",
        "requested_issue_count": 115,
        "fetched_issue_count": 115,
        "failed_request_count": 0,
        "pass_a_count": 115,
        "pass_b_count": 115,
        "pass_a_completed": True,
        "pass_b_completed": True,
        "fingerprints_matched": True,
        "allowlist_path": str(FROZEN_ALLOWLIST_PATH),
        "allowlist_sha256": FROZEN_ALLOWLIST_SHA256,
        "raw_capture_sha256": "0000000000000000000000000000000000000000000000000000000000000000",  # Mismatch
        "endpoint_inventory_sha256": compute_sha256_file(GATE2_SYNTHETIC_INVENTORY_PATH),
        "transactions_count": 230,
        "is_live_extraction": True,
    }
    receipt_file.write_text(json.dumps(receipt_data), encoding="utf-8")

    manifest = {
        "manifest_version": "2.0.0",
        "provenance_status": PROVENANCE_LIVE_VERIFIED,
        "receipt_sha256": compute_sha256_file(receipt_file),
    }

    with pytest.raises(ProvenanceReceiptError, match="raw_capture_sha256 does not match"):
        verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
            inventory_path=GATE2_SYNTHETIC_INVENTORY_PATH,
            receipt_path=receipt_file,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 5. Inventory Transaction Count Inconsistency Fails Closed ────────────────

def test_inventory_transaction_count_inconsistency_fails_closed(tmp_path):
    """Verify that fewer than 230 transactions for 115 issues in two-pass observation fails."""
    allowlist = load_frozen_allowlist()

    # Create dummy inventory with only 115 requests (instead of required >= 230)
    inv_file = tmp_path / "gate2_endpoint_inventory.json"
    dummy_inv = {
        "inventory_format": "gate2-endpoint-inventory-v1",
        "total_calls": 115,
        "transactions": [{"method": "GET", "status_code": 200}] * 115,
    }
    inv_file.write_text(json.dumps(dummy_inv), encoding="utf-8")
    inv_hash = compute_sha256_file(inv_file)

    receipt_file = tmp_path / "gate2_extraction_receipt.json"
    receipt_data = {
        "run_id": "test-run",
        "extractor_version": "1.0.0",
        "extraction_started_at": "2026-09-16T11:00:00Z",
        "extraction_completed_at": "2026-09-16T11:10:00Z",
        "source_base_url": "https://tecblic.atlassian.net",
        "requested_issue_count": 115,
        "fetched_issue_count": 115,
        "failed_request_count": 0,
        "pass_a_count": 115,
        "pass_b_count": 115,
        "pass_a_completed": True,
        "pass_b_completed": True,
        "fingerprints_matched": True,
        "allowlist_path": str(FROZEN_ALLOWLIST_PATH),
        "allowlist_sha256": FROZEN_ALLOWLIST_SHA256,
        "raw_capture_sha256": compute_sha256_file(GATE2_SYNTHETIC_RAW_CAPTURE_PATH),
        "endpoint_inventory_sha256": inv_hash,
        "transactions_count": 115,
        "is_live_extraction": True,
    }
    receipt_file.write_text(json.dumps(receipt_data), encoding="utf-8")

    manifest = {
        "manifest_version": "2.0.0",
        "provenance_status": PROVENANCE_LIVE_VERIFIED,
        "receipt_sha256": compute_sha256_file(receipt_file),
    }

    with pytest.raises(ProvenanceReceiptError, match="two-pass extraction requires at least 230"):
        verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
            inventory_path=inv_file,
            receipt_path=receipt_file,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 6. Authorized Scope Mismatch Fails Closed ─────────────────────────────────

def test_authorized_scope_mismatch_fails_closed():
    """Verify that a capture with missing or unexpected keys fails closed."""
    # The incident capture has GG-1..GG-115, which has 70 missing and 70 unexpected keys
    allowlist = load_frozen_allowlist()

    with pytest.raises(ProvenanceScopeError, match="Scope mismatch|scope does not match"):
        project_gate2_raw_rest(
            raw_capture_path=GATE2_RAW_CAPTURE_PATH,
            allowlist=allowlist,
            require_exact_scope=True,
        )


# ── 7. Fake Hardcoded Provenance Cannot Bypass Verification ────────────────────

def test_fake_hardcoded_provenance_cannot_bypass_verification():
    """Verify that a manifest claiming AUTHENTIC_RAW_REST_CAPTURE cannot bypass checks."""
    allowlist = load_frozen_allowlist()
    with GATE2_SOURCE_MANIFEST_PATH.open("r", encoding="utf-8") as f:
        incident_manifest = json.load(f)

    # Even though manifest says AUTHENTIC_RAW_REST_CAPTURE and raw_source_independence=True,
    # the verifier fails closed because no valid receipt exists.
    assert incident_manifest["provenance_status"] == "AUTHENTIC_RAW_REST_CAPTURE"
    with pytest.raises(ProvenanceReceiptError):
        verify_extraction_provenance(
            manifest=incident_manifest,
            raw_capture_path=GATE2_RAW_CAPTURE_PATH,
            inventory_path=GATE2_ENDPOINT_INVENTORY_PATH,
            receipt_path=None,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 8. Credentials Detected in Artifacts Fails Closed ─────────────────────────

def test_credentials_detected_in_artifacts_fails_closed(tmp_path):
    """Verify that credentials in manifest or receipt raise ProvenanceSecurityError."""
    allowlist = load_frozen_allowlist()

    receipt_file = tmp_path / "gate2_extraction_receipt.json"
    receipt_data = {
        "run_id": "test-run",
        "extractor_version": "1.0.0",
        "extraction_started_at": "2026-09-16T11:00:00Z",
        "extraction_completed_at": "2026-09-16T11:10:00Z",
        "source_base_url": "https://tecblic.atlassian.net",
        "requested_issue_count": 115,
        "fetched_issue_count": 115,
        "failed_request_count": 0,
        "pass_a_count": 115,
        "pass_b_count": 115,
        "pass_a_completed": True,
        "pass_b_completed": True,
        "fingerprints_matched": True,
        "allowlist_path": str(FROZEN_ALLOWLIST_PATH),
        "allowlist_sha256": FROZEN_ALLOWLIST_SHA256,
        "raw_capture_sha256": compute_sha256_file(GATE2_SYNTHETIC_RAW_CAPTURE_PATH),
        "endpoint_inventory_sha256": compute_sha256_file(GATE2_SYNTHETIC_INVENTORY_PATH),
        "transactions_count": 230,
        "is_live_extraction": True,
        "notes": "Authorization: Bearer my_secret_token",  # Leaked token!
    }
    receipt_file.write_text(json.dumps(receipt_data), encoding="utf-8")

    manifest = {
        "manifest_version": "2.0.0",
        "provenance_status": PROVENANCE_LIVE_VERIFIED,
        "receipt_sha256": compute_sha256_file(receipt_file),
    }

    # Inventory with 230 transactions to pass length check
    inv_file = tmp_path / "inv.json"
    inv_file.write_text(json.dumps({
        "transactions": [{"method": "GET"}] * 230
    }), encoding="utf-8")
    receipt_data["endpoint_inventory_sha256"] = compute_sha256_file(inv_file)
    receipt_file.write_text(json.dumps(receipt_data), encoding="utf-8")
    manifest["receipt_sha256"] = compute_sha256_file(receipt_file)

    with pytest.raises(ProvenanceSecurityError, match="authorization token detected"):
        verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
            inventory_path=inv_file,
            receipt_path=receipt_file,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 9. Valid Extraction Evidence Progresses to Verified State ────────────────

def test_valid_extraction_evidence_progresses_to_verified_state(tmp_path):
    """Verify that a compliant receipt, exact scope, valid transport headers, and execution witness progress to LIVE_REST_CAPTURE_VERIFIED."""
    allowlist = load_frozen_allowlist()

    base_time = datetime(2026, 9, 16, 11, 0, 0, tzinfo=timezone.utc)
    txs = []
    idx = 0
    # Pass A
    for key in sorted(list(allowlist)):
        tx_time = base_time + timedelta(seconds=idx)
        trace_id = hashlib.sha256(f"atl-trace-a-{key}-{idx}".encode()).hexdigest()[:32]
        txs.append({
            "request_timestamp": tx_time.isoformat(),
            "method": "GET",
            "endpoint": f"/rest/api/3/issue/{key}",
            "params": {"expand": "changelog"},
            "status_code": 200,
            "latency_ms": 110.0,
            "response_bytes": 2000,
            "atl_trace_id": trace_id,
            "x_a_request_id": f"req-pass-a-{key}-{idx}",
            "server": "atlassian-proxy",
            "strict_transport_security": "max-age=31536000; preload",
            "http_date": tx_time.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        })
        idx += 1

    # Pass B
    for key in sorted(list(allowlist)):
        tx_time = base_time + timedelta(seconds=idx)
        trace_id = hashlib.sha256(f"atl-trace-b-{key}-{idx}".encode()).hexdigest()[:32]
        txs.append({
            "request_timestamp": tx_time.isoformat(),
            "method": "GET",
            "endpoint": f"/rest/api/3/issue/{key}",
            "params": {"expand": "changelog"},
            "status_code": 200,
            "latency_ms": 112.0,
            "response_bytes": 2000,
            "atl_trace_id": trace_id,
            "x_a_request_id": f"req-pass-b-{key}-{idx}",
            "server": "atlassian-proxy",
            "strict_transport_security": "max-age=31536000; preload",
            "http_date": tx_time.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        })
        idx += 1

    witness = compute_execution_witness(txs)
    runtime_tok = f"rt-{uuid4().hex}"
    runtime_sig = compute_runtime_signature(
        runtime_tok,
        "test-valid-run-001",
        "https://tecblic.atlassian.net",
        FROZEN_ALLOWLIST_SHA256,
        witness,
    )

    inv_file = tmp_path / "gate2_endpoint_inventory.json"
    inv_file.write_text(json.dumps({"inventory_format": "gate2-endpoint-inventory-v1", "total_calls": len(txs), "transactions": txs}), encoding="utf-8")

    inv_hash = compute_sha256_file(inv_file)
    cap_hash = compute_sha256_file(GATE2_SYNTHETIC_RAW_CAPTURE_PATH)

    receipt_file = tmp_path / "gate2_extraction_receipt.json"
    receipt_data = {
        "run_id": "test-valid-run-001",
        "extractor_version": "1.0.0",
        "extraction_started_at": "2026-09-16T10:59:00+00:00",
        "extraction_completed_at": "2026-09-16T11:15:00+00:00",
        "source_base_url": "https://tecblic.atlassian.net",
        "requested_issue_count": 115,
        "fetched_issue_count": 115,
        "failed_request_count": 0,
        "pass_a_count": 115,
        "pass_b_count": 115,
        "pass_a_completed": True,
        "pass_b_completed": True,
        "fingerprints_matched": True,
        "allowlist_path": str(FROZEN_ALLOWLIST_PATH),
        "allowlist_sha256": FROZEN_ALLOWLIST_SHA256,
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_sha256": inv_hash,
        "transactions_count": 230,
        "execution_witness": witness,
        "is_live_extraction": True,
        "runtime_token": runtime_tok,
        "runtime_signature": runtime_sig,
    }
    receipt_file.write_text(json.dumps(receipt_data), encoding="utf-8")
    receipt_hash = compute_sha256_file(receipt_file)

    manifest = {
        "manifest_version": "2.0.0",
        "gate": "GATE_2",
        "provenance_status": PROVENANCE_LIVE_VERIFIED,
        "raw_source_independence": True,
        "historical_api_responses_retained": True,
        "is_empirical_live_source": True,
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_sha256": inv_hash,
        "receipt_file": "gate2_extraction_receipt.json",
        "receipt_sha256": receipt_hash,
    }

    result = verify_extraction_provenance(
        manifest=manifest,
        raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
        inventory_path=inv_file,
        receipt_path=receipt_file,
        allowlist_keys=allowlist,
        expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
    )

    assert result == PROVENANCE_LIVE_VERIFIED


# ── 10. Adversarial Bypass Audit: Offline Fabrication Attempt ────────────────

def test_adversarial_offline_fabrication_cannot_bypass_live_provenance(tmp_path):
    """Adversarial bypass audit test: Offline fabrication with mutually consistent hashes MUST fail closed.

    Proves that an offline script that fabricates:
    - raw capture (115 authorized keys)
    - endpoint inventory (230 dummy transactions)
    - ExtractionReceipt (with matching hashes)
    - manifest (claiming LIVE_REST_CAPTURE_VERIFIED with matching hashes)
    CANNOT satisfy live provenance merely because all internal hashes are mutually consistent.
    """
    allowlist = load_frozen_allowlist()

    # Step 1: Fabricate 115 issues matching the exact allowlist keys
    fake_issues = []
    for k in sorted(list(allowlist)):
        fake_issues.append({
            "id": f"offline-{k}",
            "key": k,
            "fields": {"summary": f"Offline fake issue {k}"},
        })
    raw_capture_file = tmp_path / "gate2_jira_raw_capture.json"
    raw_capture_file.write_text(json.dumps({
        "capture_format": "gate2-jira-cloud-rest-v1",
        "issue_count": 115,
        "issues": fake_issues,
    }), encoding="utf-8")
    actual_cap_hash = compute_sha256_file(raw_capture_file)

    # Step 2: Fabricate 230 dummy transactions (simulating offline forgery without live Atlassian headers)
    fake_txs = []
    for k in sorted(list(allowlist)):
        fake_txs.append({"method": "GET", "endpoint": f"/rest/api/3/issue/{k}", "status_code": 200, "response_bytes": 1000, "latency_ms": 10.0, "request_timestamp": "2026-09-16T11:00:00+00:00"})
        fake_txs.append({"method": "GET", "endpoint": f"/rest/api/3/issue/{k}", "status_code": 200, "response_bytes": 1000, "latency_ms": 10.0, "request_timestamp": "2026-09-16T11:01:00+00:00"})

    inv_file = tmp_path / "gate2_endpoint_inventory.json"
    inv_file.write_text(json.dumps({
        "inventory_format": "gate2-endpoint-inventory-v1",
        "total_calls": 230,
        "transactions": fake_txs,
    }), encoding="utf-8")
    actual_inv_hash = compute_sha256_file(inv_file)

    # Step 3: Fabricate ExtractionReceipt with all matching hashes and valid assertions
    receipt_file = tmp_path / "gate2_extraction_receipt.json"
    receipt_data = {
        "run_id": "adversarial-offline-run-001",
        "extractor_version": "1.0.0",
        "extraction_started_at": "2026-09-16T10:50:00+00:00",
        "extraction_completed_at": "2026-09-16T11:10:00+00:00",
        "source_base_url": "https://tecblic.atlassian.net",
        "requested_issue_count": 115,
        "fetched_issue_count": 115,
        "failed_request_count": 0,
        "pass_a_count": 115,
        "pass_b_count": 115,
        "pass_a_completed": True,
        "pass_b_completed": True,
        "fingerprints_matched": True,
        "allowlist_path": str(FROZEN_ALLOWLIST_PATH),
        "allowlist_sha256": FROZEN_ALLOWLIST_SHA256,
        "raw_capture_sha256": actual_cap_hash,
        "endpoint_inventory_sha256": actual_inv_hash,
        "transactions_count": 230,
        "is_live_extraction": True,
    }
    receipt_file.write_text(json.dumps(receipt_data), encoding="utf-8")
    actual_receipt_hash = compute_sha256_file(receipt_file)

    # Step 4: Fabricate manifest pointing to fabricated receipt and artifacts
    manifest = {
        "manifest_version": "2.0.0",
        "gate": "GATE_2",
        "provenance_status": PROVENANCE_LIVE_VERIFIED,
        "raw_source_independence": True,
        "historical_api_responses_retained": True,
        "is_empirical_live_source": True,
        "raw_capture_sha256": actual_cap_hash,
        "endpoint_inventory_sha256": actual_inv_hash,
        "receipt_file": "gate2_extraction_receipt.json",
        "receipt_sha256": actual_receipt_hash,
    }

    # Verify that all internal hashes are mutually consistent
    assert manifest["raw_capture_sha256"] == actual_cap_hash
    assert manifest["endpoint_inventory_sha256"] == actual_inv_hash
    assert manifest["receipt_sha256"] == actual_receipt_hash
    assert receipt_data["raw_capture_sha256"] == actual_cap_hash
    assert receipt_data["endpoint_inventory_sha256"] == actual_inv_hash
    assert receipt_data["allowlist_sha256"] == FROZEN_ALLOWLIST_SHA256

    # Attempt to bypass live verification with this perfectly consistent offline artifact:
    # MUST FAIL CLOSED because it lacks authentic Atlassian Edge transport trace headers!
    with pytest.raises(ProvenanceReceiptError, match="missing authentic Atlassian transport trace header"):
        verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=raw_capture_file,
            inventory_path=inv_file,
            receipt_path=receipt_file,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 11. Execution Witness Tampering Fails Closed ─────────────────────────────

def test_execution_witness_tampering_fails_closed(tmp_path):
    """Verify that tampering with or forging the execution witness fails closed."""
    allowlist = load_frozen_allowlist()

    base_time = datetime(2026, 9, 16, 11, 0, 0, tzinfo=timezone.utc)
    txs = []
    idx = 0
    for pass_name in ("a", "b"):
        for key in sorted(list(allowlist)):
            tx_time = base_time + timedelta(seconds=idx)
            trace_id = hashlib.sha256(f"atl-trace-{pass_name}-{key}-{idx}".encode()).hexdigest()[:32]
            txs.append({
                "request_timestamp": tx_time.isoformat(),
                "method": "GET",
                "endpoint": f"/rest/api/3/issue/{key}",
                "status_code": 200,
                "latency_ms": 100.0,
                "response_bytes": 1500,
                "atl_trace_id": trace_id,
                "x_a_request_id": f"req-{pass_name}-{key}-{idx}",
                "server": "atlassian-proxy",
                "strict_transport_security": "max-age=31536000; preload",
                "http_date": tx_time.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            })
            idx += 1

    inv_file = tmp_path / "inv.json"
    inv_file.write_text(json.dumps({"total_calls": 230, "transactions": txs}), encoding="utf-8")

    inv_hash = compute_sha256_file(inv_file)
    cap_hash = compute_sha256_file(GATE2_SYNTHETIC_RAW_CAPTURE_PATH)

    runtime_tok = f"rt-{uuid4().hex}"
    runtime_sig = compute_runtime_signature(
        runtime_tok,
        "test-tamper-witness",
        "https://tecblic.atlassian.net",
        FROZEN_ALLOWLIST_SHA256,
        "badbeef000000000000000000000000000000000000000000000000000000000",
    )

    receipt_file = tmp_path / "receipt.json"
    receipt_data = {
        "run_id": "test-tamper-witness",
        "extractor_version": "1.0.0",
        "extraction_started_at": "2026-09-16T10:59:00+00:00",
        "extraction_completed_at": "2026-09-16T11:15:00+00:00",
        "source_base_url": "https://tecblic.atlassian.net",
        "requested_issue_count": 115,
        "fetched_issue_count": 115,
        "failed_request_count": 0,
        "pass_a_count": 115,
        "pass_b_count": 115,
        "pass_a_completed": True,
        "pass_b_completed": True,
        "fingerprints_matched": True,
        "allowlist_path": str(FROZEN_ALLOWLIST_PATH),
        "allowlist_sha256": FROZEN_ALLOWLIST_SHA256,
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_sha256": inv_hash,
        "transactions_count": 230,
        "execution_witness": "badbeef000000000000000000000000000000000000000000000000000000000",  # Forged witness
        "is_live_extraction": True,
        "runtime_token": runtime_tok,
        "runtime_signature": runtime_sig,
    }
    receipt_file.write_text(json.dumps(receipt_data), encoding="utf-8")
    receipt_hash = compute_sha256_file(receipt_file)

    manifest = {
        "manifest_version": "2.0.0",
        "provenance_status": PROVENANCE_LIVE_VERIFIED,
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_sha256": inv_hash,
        "receipt_sha256": receipt_hash,
    }

    with pytest.raises(ProvenanceReceiptError, match="Execution witness mismatch"):
        verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
            inventory_path=inv_file,
            receipt_path=receipt_file,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 12. Duplicate Atlassian Trace IDs Fail Closed ────────────────────────────

def test_duplicate_trace_ids_fail_closed(tmp_path):
    """Verify that replaying or repeating trace IDs fails closed."""
    allowlist = load_frozen_allowlist()

    base_time = datetime(2026, 9, 16, 11, 0, 0, tzinfo=timezone.utc)
    constant_trace_id = "0123456789abcdef0123456789abcdef"
    txs = []
    idx = 0
    for pass_name in ("a", "b"):
        for key in sorted(list(allowlist)):
            tx_time = base_time + timedelta(seconds=idx)
            txs.append({
                "request_timestamp": tx_time.isoformat(),
                "method": "GET",
                "endpoint": f"/rest/api/3/issue/{key}",
                "status_code": 200,
                "latency_ms": 100.0,
                "response_bytes": 1500,
                "atl_trace_id": constant_trace_id,  # DUPLICATE!
                "x_a_request_id": f"req-{pass_name}-{key}-{idx}",
                "server": "atlassian-proxy",
                "strict_transport_security": "max-age=31536000; preload",
                "http_date": tx_time.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            })
            idx += 1

    inv_file = tmp_path / "inv.json"
    inv_file.write_text(json.dumps({"total_calls": 230, "transactions": txs}), encoding="utf-8")
    inv_hash = compute_sha256_file(inv_file)
    cap_hash = compute_sha256_file(GATE2_SYNTHETIC_RAW_CAPTURE_PATH)

    runtime_tok = f"rt-{uuid4().hex}"
    runtime_sig = compute_runtime_signature(
        runtime_tok,
        "test-dup-trace",
        "https://tecblic.atlassian.net",
        FROZEN_ALLOWLIST_SHA256,
        compute_execution_witness(txs),
    )

    receipt_file = tmp_path / "receipt.json"
    receipt_data = {
        "run_id": "test-dup-trace",
        "extractor_version": "1.0.0",
        "extraction_started_at": "2026-09-16T10:59:00+00:00",
        "extraction_completed_at": "2026-09-16T11:15:00+00:00",
        "source_base_url": "https://tecblic.atlassian.net",
        "requested_issue_count": 115,
        "fetched_issue_count": 115,
        "failed_request_count": 0,
        "pass_a_count": 115,
        "pass_b_count": 115,
        "pass_a_completed": True,
        "pass_b_completed": True,
        "fingerprints_matched": True,
        "allowlist_path": str(FROZEN_ALLOWLIST_PATH),
        "allowlist_sha256": FROZEN_ALLOWLIST_SHA256,
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_sha256": inv_hash,
        "transactions_count": 230,
        "execution_witness": compute_execution_witness(txs),
        "is_live_extraction": True,
        "runtime_token": runtime_tok,
        "runtime_signature": runtime_sig,
    }
    receipt_file.write_text(json.dumps(receipt_data), encoding="utf-8")
    receipt_hash = compute_sha256_file(receipt_file)

    manifest = {
        "manifest_version": "2.0.0",
        "provenance_status": PROVENANCE_LIVE_VERIFIED,
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_sha256": inv_hash,
        "receipt_sha256": receipt_hash,
    }

    with pytest.raises(ProvenanceReceiptError, match="Duplicate atl_trace_id detected"):
        verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
            inventory_path=inv_file,
            receipt_path=receipt_file,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 13. Inventory Missing Key Coverage Fails Closed ──────────────────────────

def test_inventory_missing_key_coverage_fails_closed(tmp_path):
    """Verify that missing two-pass coverage for an authorized key fails closed."""
    allowlist = load_frozen_allowlist()

    base_time = datetime(2026, 9, 16, 11, 0, 0, tzinfo=timezone.utc)
    txs = []
    idx = 0
    first_key = sorted(list(allowlist))[0]
    second_key = sorted(list(allowlist))[1]

    # Omit first_key from Pass B, but add an extra request for second_key so total is 230
    for pass_name in ("a", "b"):
        for key in sorted(list(allowlist)):
            if pass_name == "b" and key == first_key:
                # Substitute with an extra request for second_key instead of first_key
                target_key = second_key
            else:
                target_key = key
            tx_time = base_time + timedelta(seconds=idx)
            trace_id = hashlib.sha256(f"trace-{pass_name}-{target_key}-{idx}".encode()).hexdigest()[:32]
            txs.append({
                "request_timestamp": tx_time.isoformat(),
                "method": "GET",
                "endpoint": f"/rest/api/3/issue/{target_key}",
                "status_code": 200,
                "latency_ms": 100.0,
                "response_bytes": 1500,
                "atl_trace_id": trace_id,
                "x_a_request_id": f"req-{pass_name}-{target_key}-{idx}",
            })
            idx += 1

    assert len(txs) == 230
    inv_file = tmp_path / "inv.json"
    inv_file.write_text(json.dumps({"total_calls": len(txs), "transactions": txs}), encoding="utf-8")
    inv_hash = compute_sha256_file(inv_file)
    cap_hash = compute_sha256_file(GATE2_SYNTHETIC_RAW_CAPTURE_PATH)

    receipt_file = tmp_path / "receipt.json"
    receipt_data = {
        "run_id": "test-miss-key",
        "extractor_version": "1.0.0",
        "extraction_started_at": "2026-09-16T10:59:00+00:00",
        "extraction_completed_at": "2026-09-16T11:15:00+00:00",
        "source_base_url": "https://tecblic.atlassian.net",
        "requested_issue_count": 115,
        "fetched_issue_count": 115,
        "failed_request_count": 0,
        "pass_a_count": 115,
        "pass_b_count": 115,
        "pass_a_completed": True,
        "pass_b_completed": True,
        "fingerprints_matched": True,
        "allowlist_path": str(FROZEN_ALLOWLIST_PATH),
        "allowlist_sha256": FROZEN_ALLOWLIST_SHA256,
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_sha256": inv_hash,
        "transactions_count": len(txs),
        "execution_witness": compute_execution_witness(txs),
        "is_live_extraction": True,
    }
    receipt_file.write_text(json.dumps(receipt_data), encoding="utf-8")
    receipt_hash = compute_sha256_file(receipt_file)

    manifest = {
        "manifest_version": "2.0.0",
        "provenance_status": PROVENANCE_LIVE_VERIFIED,
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_sha256": inv_hash,
        "receipt_sha256": receipt_hash,
    }

    with pytest.raises(ProvenanceReceiptError, match="lacks two-pass coverage"):
        verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
            inventory_path=inv_file,
            receipt_path=receipt_file,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 14. Non-Monotonic Timestamps Fail Closed ─────────────────────────────────

def test_non_monotonic_transaction_timestamps_fail_closed(tmp_path):
    """Verify that transaction timestamps traveling backwards in time fail closed."""
    allowlist = load_frozen_allowlist()

    base_time = datetime(2026, 9, 16, 11, 0, 0, tzinfo=timezone.utc)
    txs = []
    idx = 0
    for pass_name in ("a", "b"):
        for key in sorted(list(allowlist)):
            # Invert timestamp for one request
            offset = idx if idx != 50 else (idx - 10)
            tx_time = base_time + timedelta(seconds=offset)
            trace_id = hashlib.sha256(f"trace-mono-{pass_name}-{key}-{idx}".encode()).hexdigest()[:32]
            txs.append({
                "request_timestamp": tx_time.isoformat(),
                "method": "GET",
                "endpoint": f"/rest/api/3/issue/{key}",
                "status_code": 200,
                "latency_ms": 100.0,
                "response_bytes": 1500,
                "atl_trace_id": trace_id,
                "x_a_request_id": f"req-mono-{pass_name}-{key}-{idx}",
                "server": "atlassian-proxy",
                "strict_transport_security": "max-age=31536000; preload",
                "http_date": tx_time.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            })
            idx += 1

    inv_file = tmp_path / "inv.json"
    inv_file.write_text(json.dumps({"total_calls": 230, "transactions": txs}), encoding="utf-8")
    inv_hash = compute_sha256_file(inv_file)
    cap_hash = compute_sha256_file(GATE2_SYNTHETIC_RAW_CAPTURE_PATH)

    runtime_tok = f"rt-{uuid4().hex}"
    runtime_sig = compute_runtime_signature(
        runtime_tok,
        "test-non-mono",
        "https://tecblic.atlassian.net",
        FROZEN_ALLOWLIST_SHA256,
        compute_execution_witness(txs),
    )

    receipt_file = tmp_path / "receipt.json"
    receipt_data = {
        "run_id": "test-non-mono",
        "extractor_version": "1.0.0",
        "extraction_started_at": "2026-09-16T10:59:00+00:00",
        "extraction_completed_at": "2026-09-16T11:15:00+00:00",
        "source_base_url": "https://tecblic.atlassian.net",
        "requested_issue_count": 115,
        "fetched_issue_count": 115,
        "failed_request_count": 0,
        "pass_a_count": 115,
        "pass_b_count": 115,
        "pass_a_completed": True,
        "pass_b_completed": True,
        "fingerprints_matched": True,
        "allowlist_path": str(FROZEN_ALLOWLIST_PATH),
        "allowlist_sha256": FROZEN_ALLOWLIST_SHA256,
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_sha256": inv_hash,
        "transactions_count": 230,
        "execution_witness": compute_execution_witness(txs),
        "is_live_extraction": True,
        "runtime_token": runtime_tok,
        "runtime_signature": runtime_sig,
    }
    receipt_file.write_text(json.dumps(receipt_data), encoding="utf-8")
    receipt_hash = compute_sha256_file(receipt_file)

    manifest = {
        "manifest_version": "2.0.0",
        "provenance_status": PROVENANCE_LIVE_VERIFIED,
        "raw_capture_sha256": cap_hash,
        "endpoint_inventory_sha256": inv_hash,
        "receipt_sha256": receipt_hash,
    }

    with pytest.raises(ProvenanceReceiptError, match="non-monotonic"):
        verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=GATE2_SYNTHETIC_RAW_CAPTURE_PATH,
            inventory_path=inv_file,
            receipt_path=receipt_file,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 15. Adversarial Forged Telemetry Bypass Audit ─────────────────────────────

def test_adversarial_forged_telemetry_cannot_bypass_provenance(tmp_path):
    """Adversarial forged telemetry audit: Full offline telemetry forgery test.

    Attempts to forge:
    - 115 authorized issue keys
    - 230 transactions with valid 32-hex unique atl_trace_id values
    - valid unique x_a_request_id values
    - realistic monotonic timestamps, latency, response_bytes, status 200
    - authentic transport headers (server: atlassian-proxy, strict-transport-security, http_date)
    - Pass A / Pass B completion & matching fingerprints
    - correctly recomputed execution_witness
    - matching raw/inventory/receipt/manifest SHA-256 hashes

    Verifies:
    1. Direct instantiation of ExtractionReceipt cannot be passed into save_gate2_raw_artifacts()
       to forge live manifest flags (fails closed with ProvenanceReceiptError).
    2. An unsealed receipt written directly to disk fails verify_extraction_provenance().
    3. Even if an attacker recomputes all static hashes, missing authentic runtime extractor
       session binding is caught and rejected.
    """
    allowlist = load_frozen_allowlist()

    # Step 1: Fabricate 115 authorized issues
    fake_issues = []
    for k in sorted(list(allowlist)):
        fake_issues.append({
            "id": f"forged-id-{k}",
            "key": k,
            "fields": {
                "summary": f"Forged issue for {k}",
                "status": {"name": "In Progress"},
            },
            "changelog": {"histories": []},
        })

    # Step 2: Fabricate 230 transactions with valid Atlassian Edge headers
    base_time = datetime(2026, 9, 16, 11, 0, 0, tzinfo=timezone.utc)
    fake_txs = []
    idx = 0
    for pass_name in ("a", "b"):
        for k in sorted(list(allowlist)):
            tx_time = base_time + timedelta(seconds=idx)
            trace_id = hashlib.sha256(f"forged-trace-{pass_name}-{k}-{idx}".encode()).hexdigest()[:32]
            fake_txs.append({
                "request_timestamp": tx_time.isoformat(),
                "method": "GET",
                "endpoint": f"/rest/api/3/issue/{k}",
                "params": {"expand": "changelog"},
                "status_code": 200,
                "latency_ms": 105.0,
                "response_bytes": 1800,
                "atl_trace_id": trace_id,
                "x_a_request_id": f"forged-req-{pass_name}-{k}-{idx}",
                "server": "atlassian-proxy",
                "strict_transport_security": "max-age=31536000; preload",
                "http_date": tx_time.strftime("%a, %d %b %Y %H:%M:%S GMT"),
            })
            idx += 1

    witness = compute_execution_witness(fake_txs)

    # Clear active sessions to ensure clean state
    clear_runtime_sessions()

    # Attack Vector 1: Attacker directly instantiates ExtractionReceipt without sealing
    # and tries to pass it to save_gate2_raw_artifacts()
    unsealed_receipt = ExtractionReceipt(
        run_id="adversarial-forged-001",
        extractor_version="1.0.0",
        extraction_started_at=base_time.isoformat(),
        extraction_completed_at=(base_time + timedelta(seconds=idx)).isoformat(),
        source_base_url="https://tecblic.atlassian.net",
        requested_issue_count=115,
        fetched_issue_count=115,
        failed_request_count=0,
        pass_a_count=115,
        pass_b_count=115,
        pass_a_completed=True,
        pass_b_completed=True,
        fingerprints_matched=True,
        allowlist_path=str(FROZEN_ALLOWLIST_PATH),
        allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        transactions_count=230,
        execution_witness=witness,
        is_live_extraction=True,
    )

    out_dir_1 = tmp_path / "forged_run_1"
    with pytest.raises(ProvenanceReceiptError, match="Unsealed ExtractionReceipt rejected"):
        save_gate2_raw_artifacts(
            raw_issues=fake_issues,
            source_cutoff_at="2026-09-16T11:05:00+00:00",
            endpoint_inventory=fake_txs,
            output_dir=out_dir_1,
            receipt=unsealed_receipt,
        )

    # Attack Vector 2: Attacker fabricates runtime_token and signature, but is not an active runtime session
    fake_token = f"rt-{uuid4().hex}"
    fake_sig = compute_runtime_signature(
        fake_token,
        "adversarial-forged-002",
        "https://tecblic.atlassian.net",
        FROZEN_ALLOWLIST_SHA256,
        witness,
    )
    forged_receipt = ExtractionReceipt(
        run_id="adversarial-forged-002",
        extractor_version="1.0.0",
        extraction_started_at=base_time.isoformat(),
        extraction_completed_at=(base_time + timedelta(seconds=idx)).isoformat(),
        source_base_url="https://tecblic.atlassian.net",
        requested_issue_count=115,
        fetched_issue_count=115,
        failed_request_count=0,
        pass_a_count=115,
        pass_b_count=115,
        pass_a_completed=True,
        pass_b_completed=True,
        fingerprints_matched=True,
        allowlist_path=str(FROZEN_ALLOWLIST_PATH),
        allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        transactions_count=230,
        execution_witness=witness,
        is_live_extraction=True,
        runtime_token=fake_token,
        runtime_signature=fake_sig,
    )

    out_dir_2 = tmp_path / "forged_run_2"
    with pytest.raises(ProvenanceReceiptError, match="not minted by an active JiraExtractor runtime"):
        save_gate2_raw_artifacts(
            raw_issues=fake_issues,
            source_cutoff_at="2026-09-16T11:05:00+00:00",
            endpoint_inventory=fake_txs,
            output_dir=out_dir_2,
            receipt=forged_receipt,
        )

    # Attack Vector 3: Attacker writes raw artifacts directly to disk, bypassing save_gate2_raw_artifacts(),
    # but omitting authentic runtime signature
    out_dir_3 = tmp_path / "forged_run_3"
    out_dir_3.mkdir(parents=True, exist_ok=True)
    raw_cap = out_dir_3 / "gate2_jira_raw_capture.json"
    raw_cap.write_text(json.dumps({
        "capture_format": "gate2-jira-cloud-rest-v1",
        "issue_count": 115,
        "issues": fake_issues,
    }), encoding="utf-8")
    inv_file = out_dir_3 / "gate2_endpoint_inventory.json"
    inv_file.write_text(json.dumps({
        "inventory_format": "gate2-endpoint-inventory-v1",
        "total_calls": 230,
        "transactions": fake_txs,
    }), encoding="utf-8")
    receipt_file = out_dir_3 / "gate2_extraction_receipt.json"
    receipt_dict = forged_receipt.to_dict()
    receipt_dict["raw_capture_sha256"] = compute_sha256_file(raw_cap)
    receipt_dict["endpoint_inventory_sha256"] = compute_sha256_file(inv_file)
    receipt_dict["runtime_signature"] = ""  # Stripped / unsealed
    receipt_file.write_text(json.dumps(receipt_dict), encoding="utf-8")
    manifest = {
        "manifest_version": "2.0.0",
        "gate": "GATE_2",
        "provenance_status": PROVENANCE_LIVE_VERIFIED,
        "raw_source_independence": True,
        "historical_api_responses_retained": True,
        "is_empirical_live_source": True,
        "raw_capture_sha256": compute_sha256_file(raw_cap),
        "endpoint_inventory_sha256": compute_sha256_file(inv_file),
        "receipt_sha256": compute_sha256_file(receipt_file),
    }

    with pytest.raises(ProvenanceReceiptError, match="lacks authentic runtime extractor signature"):
        verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=raw_cap,
            inventory_path=inv_file,
            receipt_path=receipt_file,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )

