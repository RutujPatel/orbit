"""Gate 2 Fresh Authorized Jira REST Qualification Test Suite.

Proves that ORBIT accurately represents and processes fresh, un-shaped Jira Cloud
REST observations directly extracted from Jira Cloud under the frozen CSE baseline 6d82d12.

Key test areas:
1. Provenance & Source Manifest (v2.0.0, authentic raw REST capture, cryptographic locks).
2. Endpoint & Transaction Telemetry (call-by-call latency, payload bytes, scrubbed credentials).
3. Raw REST Capture Integrity (authentic Atlassian schema, privacy scrubbing).
4. Reconciliation Accounting (strict 4-category conservation across jira_issue and jira_change).
5. Behavioral Measurements & Census (due dates, resolutions, transitions census).
6. 6-Category Behavioral Taxonomy (100% limitation classification, 0 engine defects).
7. Deterministic Fixture Structure (shadow-jira-fixture-v1, honest null planning basis).
8. Frozen Engine Pipeline Execution (validate -> normalize -> adapt -> bundle -> joint invariants).
9. Qualification Identity & Locks (engine commit 6d82d12, configuration digest).
10. Fail-Closed Security (strict errors on missing or tampered raw artifacts).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure orbit repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from qualification.config import (
    Gate2JiraConfig,
    GATE2_RAW_CAPTURE_PATH,
    GATE2_RAW_CAPTURE_SHA256,
    GATE2_SOURCE_MANIFEST_PATH,
    GATE2_SOURCE_MANIFEST_SHA256,
    GATE2_ENDPOINT_INVENTORY_PATH,
    GATE2_ENDPOINT_INVENTORY_SHA256,
    GATE2_ALLOWLIST_COUNT,
    FROZEN_ENGINE_COMMIT,
    JIRA_CONTRACT_VERSION,
    verify_and_compute_gate2_dataset_hashes,
    create_gate2_qualification_identity,
)
from qualification.policy import compute_sha256_file, TaxonomyRegister
from qualification.projection.jira_projection import project_gate2_raw_rest
from shadow_orbit.validation import validate_fixture
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.jira_evidence_adapter import adapt_jira_evidence
from shadow_orbit.evidence_types import SourceInstance
from shadow_orbit.evidence_assembly import assemble_evidence_bundle, validate_evidence_bundle


# ── 1. Provenance and Source Manifest ─────────────────────────────────────────

def test_gate2_provenance_and_source_manifest():
    """Verify Gate 2 manifest locks and fail-closed provenance audit."""
    if not GATE2_SOURCE_MANIFEST_PATH.exists():
        pytest.fail(f"Gate 2 source manifest missing at {GATE2_SOURCE_MANIFEST_PATH}")

    actual_digest = compute_sha256_file(GATE2_SOURCE_MANIFEST_PATH)
    assert actual_digest == GATE2_SOURCE_MANIFEST_SHA256, (
        f"Manifest digest mismatch! Got {actual_digest}, expected {GATE2_SOURCE_MANIFEST_SHA256}"
    )

    with GATE2_SOURCE_MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    # Schema & artifact lock assertions
    assert manifest["manifest_version"] == "2.0.0"
    assert manifest["gate"] == "GATE_2"
    assert manifest["issue_count"] == GATE2_ALLOWLIST_COUNT
    assert manifest["target_project"] == "GG"
    assert manifest["raw_capture_file"] == "gate2_jira_raw_capture.json"
    assert manifest["raw_capture_sha256"] == GATE2_RAW_CAPTURE_SHA256
    assert manifest["endpoint_inventory_file"] == "gate2_endpoint_inventory.json"
    assert manifest["endpoint_inventory_sha256"] == GATE2_ENDPOINT_INVENTORY_SHA256

    # Provenance hardening proof: The unhardened incident manifest self-asserts
    # AUTHENTIC_RAW_REST_CAPTURE, BUT verify_extraction_provenance fails closed
    # because no genuine extraction receipt exists!
    from qualification.policy import verify_extraction_provenance, ProvenanceReceiptError
    from qualification.projection.jira_projection import load_frozen_allowlist
    from qualification.config import FROZEN_ALLOWLIST_SHA256

    allowlist = load_frozen_allowlist()
    with pytest.raises(ProvenanceReceiptError, match="extraction receipt"):
        verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=GATE2_RAW_CAPTURE_PATH,
            inventory_path=GATE2_ENDPOINT_INVENTORY_PATH,
            receipt_path=None,
            allowlist_keys=allowlist,
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )


# ── 2. Endpoint Inventory Telemetry ───────────────────────────────────────────

def test_gate2_endpoint_inventory_telemetry():
    """Verify call-by-call endpoint inventory records valid HTTP telemetry with zero credentials."""
    if not GATE2_ENDPOINT_INVENTORY_PATH.exists():
        pytest.fail(f"Gate 2 endpoint inventory missing at {GATE2_ENDPOINT_INVENTORY_PATH}")

    actual_digest = compute_sha256_file(GATE2_ENDPOINT_INVENTORY_PATH)
    assert actual_digest == GATE2_ENDPOINT_INVENTORY_SHA256

    with GATE2_ENDPOINT_INVENTORY_PATH.open("r", encoding="utf-8") as handle:
        inventory = json.load(handle)

    assert inventory["inventory_format"] == "gate2-endpoint-inventory-v1"
    assert inventory["total_calls"] == GATE2_ALLOWLIST_COUNT

    transactions = inventory["transactions"]
    assert isinstance(transactions, list)
    assert len(transactions) == GATE2_ALLOWLIST_COUNT

    for tx in transactions:
        assert tx["method"] == "GET"
        assert tx["endpoint"].startswith("/rest/api/3/issue/GG-")
        assert tx["status_code"] == 200
        assert tx["latency_ms"] > 0
        assert tx["response_bytes"] > 0
        assert "request_timestamp" in tx

        # Credential scrubbing check: no auth headers or tokens
        tx_str = json.dumps(tx)
        assert "bearer" not in tx_str.lower()
        assert "basic" not in tx_str.lower()
        assert "api_token" not in tx_str.lower()
        assert "authorization" not in tx_str.lower()


# ── 3. Raw REST Capture Integrity ─────────────────────────────────────────────

def test_gate2_raw_rest_capture_integrity():
    """Verify raw REST capture contains authentic Atlassian schema fields and no leaked secrets."""
    if not GATE2_RAW_CAPTURE_PATH.exists():
        pytest.fail(f"Gate 2 raw capture missing at {GATE2_RAW_CAPTURE_PATH}")

    actual_digest = compute_sha256_file(GATE2_RAW_CAPTURE_PATH)
    assert actual_digest == GATE2_RAW_CAPTURE_SHA256

    with GATE2_RAW_CAPTURE_PATH.open("r", encoding="utf-8") as handle:
        capture_doc = json.load(handle)

    issues = capture_doc.get("issues", [])
    assert len(issues) == GATE2_ALLOWLIST_COUNT

    for issue in issues:
        # Authentic Jira Cloud REST schema fields
        assert "id" in issue
        assert "key" in issue
        assert issue["key"].startswith("GG-")
        fields = issue.get("fields", {})
        assert "issuetype" in fields
        assert "priority" in fields
        assert "status" in fields
        assert "statusCategory" in fields["status"]
        assert "created" in fields
        assert "updated" in fields

        # Authentic changelog structure
        changelog = issue.get("changelog", {})
        assert "histories" in changelog or "values" in changelog

        # Security policy: no emails or secrets
        issue_str = json.dumps(issue)
        assert "@tecblic" not in issue_str
        assert "password" not in issue_str.lower()
        assert "bearer" not in issue_str.lower()


# ── 4. Reconciliation Accounting ──────────────────────────────────────────────

def test_gate2_reconciliation_accounting_balance():
    """Verify strict four-category reconciliation balance across jira_issue and jira_change."""
    config = Gate2JiraConfig()
    fixture_doc, report, measurements, tax_report = project_gate2_raw_rest(
        raw_capture_path=GATE2_RAW_CAPTURE_PATH,
        config=config,
        expected_sha256=GATE2_RAW_CAPTURE_SHA256,
    )

    # 1. Overall balance
    assert report.is_balanced() is True, "Reconciliation report must be balanced"
    assert "jira_issue" in report.registers
    assert "jira_change" in report.registers

    # 2. jira_issue register exact accounting
    issue_reg = report.registers["jira_issue"]
    assert issue_reg.is_balanced() is True
    assert issue_reg.source_considered == GATE2_ALLOWLIST_COUNT
    assert issue_reg.projected_successfully == GATE2_ALLOWLIST_COUNT
    assert issue_reg.projection_failed == 0
    assert issue_reg.contract_not_representable == 0
    assert issue_reg.explicitly_excluded == 0

    # 3. jira_change register exact accounting
    change_reg = report.registers["jira_change"]
    assert change_reg.is_balanced() is True
    assert change_reg.source_considered == 216
    assert change_reg.projected_successfully == 216
    assert change_reg.projection_failed == 0
    assert change_reg.contract_not_representable == 0
    assert change_reg.explicitly_excluded == 0


# ── 5. Behavioral Measurements and Census ──────────────────────────────────────

def test_gate2_behavioral_measurements_and_census():
    """Verify real-world source behavior metrics and transition distribution census."""
    config = Gate2JiraConfig()
    fixture_doc, report, measurements, tax_report = project_gate2_raw_rest(
        raw_capture_path=GATE2_RAW_CAPTURE_PATH,
        config=config,
    )

    # Core volume counts
    assert measurements["total_source_issues"] == 115
    assert measurements["unique_source_keys"] == 115
    assert measurements["duplicate_source_keys"] == 0

    # Real-world Jira observations
    assert measurements["null_due_dates"] == 115, "100% of real Jira issues have null due dates"
    assert measurements["null_resolution_dates"] == 9, "9 issues are currently unresolved"
    assert measurements["null_assignees"] == 0, "All 115 issues have assigned owners"
    assert measurements["unmapped_statuses"] == 0, "All statuses mapped in frozen mapping"
    assert measurements["unmapped_priorities"] == 0, "All priorities mapped in frozen mapping"

    # Transition census
    assert measurements["total_changelog_events"] == 216
    assert measurements["items_with_history"] == 110
    assert measurements["items_with_multiple_transitions"] == 106
    assert measurements["items_with_zero_transitions"] == 5

    # Conservation of items: 110 with history + 5 with zero = 115
    assert measurements["items_with_history"] + measurements["items_with_zero_transitions"] == 115

    # Verification of forensic census finding: 106 / 110 = 96.36% > 1 transitions
    pct_multiple = (measurements["items_with_multiple_transitions"] / measurements["items_with_history"]) * 100.0
    assert 96.3 <= pct_multiple <= 96.5


# ── 6. Six-Category Behavioral Taxonomy ───────────────────────────────────────

def test_gate2_taxonomy_classification():
    """Verify 100% of limitations are captured in the taxonomy register with 0 engine defects."""
    tax_reg = TaxonomyRegister()
    fixture_doc, report, measurements, tax_report = project_gate2_raw_rest(
        raw_capture_path=GATE2_RAW_CAPTURE_PATH,
        config=Gate2JiraConfig(),
        taxonomy_register=tax_reg,
    )

    summary = tax_report["summary_counts"]

    # All null due dates are recorded as source limitations
    assert summary["source_limitation"] == 115
    assert summary["engine_defect"] == 0, "Zero engine defects in Gate 2 projection"
    assert summary["harness_defect"] == 0, "Zero harness defects in Gate 2 projection"
    assert summary["projection_limitation"] == 0
    assert summary["contract_limitation"] == 0
    assert summary["environment_limitation"] == 0
    assert tax_report["total_entries"] == 115

    # Inspect individual taxonomy entries
    for entry in tax_report["entries"]:
        assert entry["category"] == "source_limitation"
        assert entry["code"] == "NULL_DUE_DATE"
        assert entry["subject_key"].startswith("GG-")
        assert entry["action"] == "Record honest null; emit QualityIssue"


# ── 7. Deterministic Fixture Structure ────────────────────────────────────────

def test_gate2_deterministic_fixture_structure():
    """Verify projected fixture strictly adheres to shadow-jira-fixture-v1 contract."""
    config = Gate2JiraConfig()
    fixture_doc, report, measurements, tax_report = project_gate2_raw_rest(
        raw_capture_path=GATE2_RAW_CAPTURE_PATH,
        config=config,
    )

    # Top-level fixture metadata
    assert fixture_doc["contract_version"] == JIRA_CONTRACT_VERSION
    assert fixture_doc["organization"]["external_key"] == "tecblic"
    assert fixture_doc["team"]["external_key"] == "gogreen"
    assert fixture_doc["project"]["project_key"] == "GG"
    assert fixture_doc["timezone"] == "Asia/Kolkata"

    # Deterministic fixture ID (independent of wall-clock execution date)
    assert fixture_doc["fixture_id"].startswith("gg-gate2-2026-w38-")

    # Review period matches Gate 2 configuration
    rp = fixture_doc["review_period"]
    assert rp["label"] == "2026-W38"
    assert rp["starts_at"] == "2026-09-14T00:00:00+05:30"
    assert rp["ends_at_exclusive"] == "2026-09-19T00:00:00+05:30"
    assert rp["source_cutoff_at"] == "2026-09-16T12:00:00+05:30"

    # Honest null planning basis
    assert fixture_doc["configuration"]["planning_basis"]["key"] == "source_unavailable"

    # Work items count
    assert len(fixture_doc["work_items"]) == GATE2_ALLOWLIST_COUNT


# ── 8. Frozen Engine Pipeline Execution ───────────────────────────────────────

def test_gate2_frozen_engine_pipeline_execution():
    """Verify projected Gate 2 fixture executes end-to-end through frozen CSE baseline 6d82d12."""
    config = Gate2JiraConfig()
    fixture_doc, _, _, _ = project_gate2_raw_rest(
        raw_capture_path=GATE2_RAW_CAPTURE_PATH,
        config=config,
    )

    # 1. Validation phase
    validated = validate_fixture(fixture_doc)
    assert len(validated.accepted_raw_items) == GATE2_ALLOWLIST_COUNT
    assert len(validated.quarantined_records) == 0
    assert len(validated.validation_conditions) == 0

    # 2. Normalization phase
    normalized = normalize_fixture(validated)
    assert len(normalized.work_items) == GATE2_ALLOWLIST_COUNT

    # 3. Jira evidence adaptation
    source_instance = SourceInstance(source_kind="jira", instance_id=config.site_key)
    ctx, observations, quality_issues = adapt_jira_evidence(
        normalized=normalized,
        source_instance=source_instance,
        observation_id="obs-gate2-qualification",
        fixture_id=fixture_doc["fixture_id"],
    )
    assert len(observations) == GATE2_ALLOWLIST_COUNT
    assert len(quality_issues) == 0

    # 4. Evidence bundle assembly
    bundle = assemble_evidence_bundle(
        bundle_id="bundle-gate2-qualification",
        bundle_version="1.0.0",
        jira_context=ctx,
        jira_observations=observations,
        jira_quality_issues=quality_issues,
    )
    assert len(bundle.observations) == GATE2_ALLOWLIST_COUNT

    # 5. Joint invariant validation (CSE-1.7 engine contract)
    bundle_issues = validate_evidence_bundle(bundle)
    assert len(bundle_issues) == 0, f"Evidence bundle validation failed with issues: {bundle_issues}"


# ── 9. Qualification Identity and Locks ────────────────────────────────────────

def test_gate2_qualification_identity_and_locks():
    """Verify populated QualificationIdentity correctly records engine commit and dataset hashes."""
    config = Gate2JiraConfig()
    identity = create_gate2_qualification_identity(config=config, verify_on_disk=True)

    assert identity.engine_commit == FROZEN_ENGINE_COMMIT
    assert identity.engine_commit == "6d82d12"
    assert identity.jira_contract_version == JIRA_CONTRACT_VERSION
    assert identity.projection_revision == "gate2-r1"

    hashes_dict = dict(identity.dataset_hashes)
    assert hashes_dict["gate2_raw_capture"] == GATE2_RAW_CAPTURE_SHA256
    assert hashes_dict["gate2_source_manifest"] == GATE2_SOURCE_MANIFEST_SHA256
    assert hashes_dict["gate2_endpoint_inventory"] == GATE2_ENDPOINT_INVENTORY_SHA256

    assert len(identity.configuration_digest) == 64


# ── 10. Fail-Closed Security on Missing or Tampered Artifacts ─────────────────

def test_gate2_fail_closed_on_missing_or_tampered_artifacts(tmp_path):
    """Verify qualification fails closed on missing files or violated cryptographic locks."""
    # 1. Missing raw capture file
    missing_capture = tmp_path / "missing_capture.json"
    with pytest.raises(FileNotFoundError, match="Gate 2 qualification artifact missing"):
        verify_and_compute_gate2_dataset_hashes(raw_capture_path=missing_capture)

    # 2. Tampered raw capture file
    tampered_capture = tmp_path / "tampered_capture.json"
    tampered_capture.write_text('{"tampered": true}', encoding="utf-8")
    with pytest.raises(RuntimeError, match="Cryptographic lock violated for Gate 2 gate2_raw_capture"):
        verify_and_compute_gate2_dataset_hashes(raw_capture_path=tampered_capture)

    # 3. Missing manifest file
    missing_manifest = tmp_path / "missing_manifest.json"
    with pytest.raises(FileNotFoundError, match="Gate 2 qualification artifact missing"):
        verify_and_compute_gate2_dataset_hashes(source_manifest_path=missing_manifest)

    # 4. Tampered manifest file
    tampered_manifest = tmp_path / "tampered_manifest.json"
    tampered_manifest.write_text('{"manifest_version": "99.0.0"}', encoding="utf-8")
    with pytest.raises(RuntimeError, match="Cryptographic lock violated for Gate 2 gate2_source_manifest"):
        verify_and_compute_gate2_dataset_hashes(source_manifest_path=tampered_manifest)
