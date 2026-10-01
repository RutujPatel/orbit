import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from qualification.config import (
    GoGreenJiraConfig,
    FROZEN_ALLOWLIST_PATH,
    FROZEN_ALLOWLIST_SHA256,
    FROZEN_ALLOWLIST_COUNT,
    RAW_REST_CAPTURE_PATH,
    CSV_SOURCE_PATH,
    CSV_SOURCE_SHA256,
    CSV_SOURCE_CUTOFF,
    WORKSPACE_CSV_PATH,
    REFERENCE_FIXTURE_PATH,
    REFERENCE_FIXTURE_SHA256,
    REST_SNAPSHOT_CUTOFF,
    SOURCE_MANIFEST_PATH,
    SOURCE_MANIFEST_SHA256,
    HISTORICAL_RAW_REST_RETAINED,
    verify_and_compute_dataset_hashes,
    create_populated_qualification_identity,
)
from qualification.policy import compute_sha256_file
from qualification.projection.jira_projection import (
    load_frozen_allowlist,
    load_jira_csv_records,
    project_from_raw_rest_capture,
    project_gogreen_jira,
    verify_historical_reference_fixture,
)
from shadow_orbit.validation import validate_fixture
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.jira_evidence_adapter import adapt_jira_evidence
from shadow_orbit.evidence_types import SourceInstance
from shadow_orbit.evidence_assembly import assemble_evidence_bundle, validate_evidence_bundle


def test_gogreen_source_manifest_path_b_provenance():
    """Verify source manifest explicitly establishes Path B and cryptographic locks for retained artifacts."""
    if not SOURCE_MANIFEST_PATH.exists():
        pytest.fail(f"Source manifest missing at {SOURCE_MANIFEST_PATH}! Qualification Gate Failed.")

    digest = compute_sha256_file(SOURCE_MANIFEST_PATH)
    assert digest == SOURCE_MANIFEST_SHA256, f"Manifest hash mismatch! Got {digest}, expected {SOURCE_MANIFEST_SHA256}"

    with SOURCE_MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    # Verify Path B provenance determination
    prov = manifest["provenance_assessment"]
    assert prov["historical_raw_rest_retained"] is False
    assert prov["raw_source_independence_established_for_historical_cutoff"] is False
    assert prov["historical_cutoff"] == REST_SNAPSHOT_CUTOFF
    assert "Line 79" in prov["governance_basis"] or "line 79" in prov["governance_basis"]
    assert HISTORICAL_RAW_REST_RETAINED is False

    # Verify retained artifact hashes match config locks
    retained = manifest["retained_artifacts"]
    assert retained["frozen_allowlist"]["sha256"] == FROZEN_ALLOWLIST_SHA256
    assert retained["frozen_allowlist"]["issue_count"] == FROZEN_ALLOWLIST_COUNT
    assert retained["retained_jira_csv_export"]["sha256"] == CSV_SOURCE_SHA256
    assert retained["historical_reference_fixture"]["sha256"] == REFERENCE_FIXTURE_SHA256


def test_gogreen_historical_reference_fixture_verification_and_pipeline():
    """Verify historical reference fixture against frozen CSE contracts while labeling it strictly reference evidence."""
    if not REFERENCE_FIXTURE_PATH.exists():
        pytest.fail(f"Historical reference fixture missing at {REFERENCE_FIXTURE_PATH}! Qualification Gate Failed.")

    config = GoGreenJiraConfig()
    fixture_doc, report, history_report = verify_historical_reference_fixture(
        fixture_path=REFERENCE_FIXTURE_PATH,
        expected_sha256=REFERENCE_FIXTURE_SHA256,
    )

    # 1. Multi-collection reconciliation accounting
    assert report.is_balanced() is True
    assert "jira_issue" in report.registers
    assert "jira_change" in report.registers

    issue_reg = report.registers["jira_issue"]
    assert issue_reg.source_considered == 115
    assert issue_reg.projected_successfully == 115
    assert issue_reg.projection_failed == 0
    assert issue_reg.contract_not_representable == 0
    assert issue_reg.explicitly_excluded == 0

    change_reg = report.registers["jira_change"]
    assert change_reg.source_considered == 235
    assert change_reg.projected_successfully == 235
    assert change_reg.projection_failed == 0

    # 2. Honest provenance status and history coverage reporting
    assert history_report["provenance_status"] == "historical_reference_evidence"
    assert history_report["raw_source_independent"] is False
    assert history_report["history_supplied"] is True
    assert history_report["total_projected_items"] == 115
    assert history_report["items_with_history"] == 110
    assert history_report["total_change_events"] == 235
    assert history_report["history_dependent_qualification"] == "exercised"

    # 3. Populated qualification identity with verified on-disk digests
    identity = create_populated_qualification_identity(config, verify_on_disk=True)
    assert identity.engine_commit == "6d82d12"
    assert len(identity.dataset_hashes) == 4
    assert dict(identity.dataset_hashes)["historical_reference_fixture"] == REFERENCE_FIXTURE_SHA256
    assert dict(identity.dataset_hashes)["source_manifest"] == SOURCE_MANIFEST_SHA256
    assert dict(identity.dataset_hashes)["frozen_allowlist"] == FROZEN_ALLOWLIST_SHA256
    assert dict(identity.dataset_hashes)["csv_source_export"] == CSV_SOURCE_SHA256
    assert len(identity.configuration_digest) == 64

    # 4. Frozen engine validation
    validated = validate_fixture(fixture_doc)
    assert len(validated.accepted_raw_items) == 115
    assert len(validated.quarantined_records) == 0
    assert len(validated.validation_conditions) == 0

    # 5. Frozen engine normalization
    normalized = normalize_fixture(validated)
    assert len(normalized.work_items) == 115

    # 6. CSE evidence adaptation
    source_instance = SourceInstance(source_kind="jira", instance_id=config.site_key)
    ctx, observations, quality_issues = adapt_jira_evidence(
        normalized=normalized,
        source_instance=source_instance,
        observation_id="obs-gogreen-historical-ref",
        fixture_id=fixture_doc["fixture_id"],
    )
    assert len(observations) == 115
    assert len(quality_issues) == 0

    # 7. Evidence bundle assembly and joint invariant validation
    bundle = assemble_evidence_bundle(
        bundle_id="bundle-gogreen-historical-ref",
        bundle_version="1.0.0",
        jira_context=ctx,
        jira_observations=observations,
        jira_quality_issues=quality_issues,
    )
    bundle_issues = validate_evidence_bundle(bundle)
    assert len(bundle_issues) == 0
    assert len(bundle.observations) == 115


def test_gogreen_csv_export_projection_and_unsupplied_history():
    """Verify retained Jira CSV export with strict boundary, uniqueness, and unsupplied history assertions."""
    csv_file = CSV_SOURCE_PATH if CSV_SOURCE_PATH.exists() else WORKSPACE_CSV_PATH
    if not csv_file.exists():
        pytest.fail(f"Retained Jira CSV source file missing at {csv_file}! Qualification Gate Failed.")

    # 1. Fail-closed on actual file hash verification
    actual_csv_hash = compute_sha256_file(csv_file)
    assert actual_csv_hash == CSV_SOURCE_SHA256, (
        f"CSV source digest mismatch! Expected {CSV_SOURCE_SHA256}, got actual {actual_csv_hash}"
    )

    records = load_jira_csv_records(csv_file)
    assert len(records) == 317

    # 2. Key uniqueness and completeness in the 317-row source export
    source_keys = [r.get("Issue key") for r in records if r.get("Issue key")]
    assert len(source_keys) == 317, "All 317 records must contain an 'Issue key'"
    assert len(set(source_keys)) == 317, "No duplicate Jira keys must occur in the 317-row source CSV"

    # 3. Allowlist loading and boundary proof
    allowlist = load_frozen_allowlist(FROZEN_ALLOWLIST_PATH)
    assert len(allowlist) == FROZEN_ALLOWLIST_COUNT

    # Boundary proof: all 115 frozen allowlist keys must occur in the source CSV
    assert allowlist.issubset(set(source_keys)), "All 115 frozen allowlist keys must occur in the source CSV"

    config = GoGreenJiraConfig()

    fixture_doc, report, history_report = project_gogreen_jira(
        source_records=records,
        config=config,
        corpus_id="pilot115",
        projection_revision="r2",
        partition_id="dev",
        allowlist=allowlist,
        explicit_source_cutoff=CSV_SOURCE_CUTOFF,  # Explicitly tied to CSV cutoff, NOT REST cutoff
    )

    # 4. Reconciliation accounting
    assert report.is_balanced() is True
    issue_reg = report.registers["jira_issue"]
    assert issue_reg.source_considered == 317
    assert issue_reg.projected_successfully == 115
    assert issue_reg.explicitly_excluded == 202
    assert issue_reg.projection_failed == 0
    assert issue_reg.contract_not_representable == 0

    # 5. Exact projected key set matching
    projected_keys = [it["key"] for it in fixture_doc["work_items"]]
    assert len(projected_keys) == 115, "Exactly 115 items projected"
    assert set(projected_keys) == allowlist, "Projected keys must exactly match frozen allowlist"
    assert len(set(projected_keys)) == 115, "All 115 frozen allowlist keys occur exactly once in projected output"

    # 6. History coverage reporting: prominently unsupplied
    assert history_report["history_supplied"] is False
    assert history_report["total_change_events"] == 0
    assert history_report["history_dependent_qualification"] == "not_exercised"
    assert "Source did not supply changelogs" in history_report["notes"]

    # 7. Source cutoff correctly reflects CSV cutoff
    assert fixture_doc["review_period"]["source_cutoff_at"] == CSV_SOURCE_CUTOFF

    # 8. Frozen engine validation accepts the structure
    validated = validate_fixture(fixture_doc)
    assert len(validated.accepted_raw_items) == 115
    assert len(validated.quarantined_records) == 0


def test_gogreen_raw_rest_capture_fail_closed_when_missing():
    """Verify qualification fails closed with clear Path B diagnostics when raw REST capture is requested but missing."""
    assert not RAW_REST_CAPTURE_PATH.exists()

    with pytest.raises(FileNotFoundError, match="Line 79"):
        project_from_raw_rest_capture(
            raw_capture_path=RAW_REST_CAPTURE_PATH,
            config=GoGreenJiraConfig(),
            allowlist_path=FROZEN_ALLOWLIST_PATH,
        )


def test_qualification_identity_dynamic_verification_fails_closed_on_tampering(tmp_path):
    """Verify that verify_and_compute_dataset_hashes fails closed on missing or tampered artifacts."""
    # 1. Missing file fails closed with FileNotFoundError
    missing_file = tmp_path / "non_existent.csv"
    with pytest.raises(FileNotFoundError, match="Authoritative qualification artifact missing"):
        verify_and_compute_dataset_hashes(csv_path=missing_file)

    # 2. Tampered file fails closed with RuntimeError (lock violated)
    tampered_allowlist = tmp_path / "tampered_allowlist.txt"
    tampered_allowlist.write_text("GG-9999\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Cryptographic lock violated for frozen_allowlist"):
        verify_and_compute_dataset_hashes(allowlist_path=tampered_allowlist)
