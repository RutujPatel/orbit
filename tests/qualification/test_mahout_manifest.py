"""Qualification Tests for Mahout Source Manifest & Reproducibility.

Tests:
1. Balanced selection-stage accounting (selected_for_qualification vs not_selected_by_policy).
2. Explicit absence of projection-stage terminology (projected_successfully) in selection manifest.
3. Authoritative source census recomputation and internal reconciliation (4,940 status changes).
4. Full transition census accounting for In Progress -> Patch Available (25 occurrences, 24 issues).
5. Strict separation of QualificationIdentity (deterministic) and RunMetadata (telemetry).
6. Exact 400 count in manifest and allowlist.
7. Cryptographic hash integrity across manifest, report, and allowlist.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from qualification.mahout.manifest import (
    compute_authoritative_source_census,
    compute_dataset_content_hash,
    generate_mahout_manifest,
    write_mahout_artifacts,
)
from qualification.mahout.selector import load_mahout_issues_from_mongo
from qualification.policy import compute_sha256_file


@pytest.fixture(scope="module")
def mahout_docs() -> list[dict[str, Any]]:
    try:
        docs = load_mahout_issues_from_mongo()
        if not docs:
            pytest.skip("No Mahout issues found in MongoDB")
        return docs
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")


def test_manifest_selection_accounting_semantics(mahout_docs: list[dict[str, Any]]) -> None:
    manifest, _ = generate_mahout_manifest(mahout_docs, target_size=400)

    # Must contain selection_accounting, NOT projection reconciliation
    assert "selection_accounting" in manifest
    sa = manifest["selection_accounting"]

    assert sa["is_balanced"] is True
    assert sa["source_considered"] == len(mahout_docs)
    assert sa["selected_for_qualification"] == 400
    assert sa["not_selected_by_policy"] == len(mahout_docs) - 400
    assert sa["selection_failed"] == 0

    # Projection-stage terminology MUST NOT leak into source selection accounting
    assert "projected_successfully" not in sa
    assert "projection_failed" not in sa
    assert "contract_not_representable" not in sa
    assert "explicitly_excluded" not in sa


def test_manifest_authoritative_source_census_reconciled(mahout_docs: list[dict[str, Any]]) -> None:
    manifest, _ = generate_mahout_manifest(mahout_docs, target_size=400)

    src_meta = manifest["source_dataset"]
    census = src_meta["authoritative_source_census"]

    assert census["total_source_issues"] == len(mahout_docs)
    assert census["total_status_changes"] == 4940
    assert census["distinct_transition_pairs_count"] == 15

    pairs = census["transition_pairs"]
    sum_occurrences = sum(p["occurrences_in_source"] for p in pairs.values())
    assert sum_occurrences == 4940

    # Check In Progress -> Patch Available census: 25 occurrences across 24 distinct issues
    ipa = pairs["In Progress->Patch Available"]
    assert ipa["occurrences_in_source"] == 25
    assert ipa["distinct_issues_in_source"] == 24
    assert ipa["multi_occurrence_in_single_issue"] is True

    # Check that seed transition breakdown captures 100% of both occurrences and distinct issues
    seed_breakdown = manifest["seed_transition_breakdown"]
    seed_ipa = seed_breakdown["In Progress->Patch Available"]
    assert seed_ipa["occurrences_in_seed"] == 25
    assert seed_ipa["distinct_issues_in_seed"] == 24


def test_manifest_identity_metadata_separation(mahout_docs: list[dict[str, Any]]) -> None:
    manifest, _ = generate_mahout_manifest(mahout_docs, target_size=400)

    ident = manifest["qualification_identity"]
    meta = manifest["run_metadata"]

    # Semantic identity must NOT contain volatile run timestamps or host
    assert "execution_timestamp" not in ident
    assert "host_machine" not in ident
    assert "wall_clock_seconds" not in ident

    # Semantic identity must contain reproducible contracts and hashes
    assert ident["engine_commit"] == "6d82d12"
    assert ident["jira_contract_version"] == "shadow-jira-fixture-v1"
    assert ident["dataset_hashes"]["seed_selection_sha256"]
    assert ident["dataset_hashes"]["source_dataset_content_sha256"]
    assert ident["configuration_digest"]

    # Run metadata must contain operational telemetry
    assert "execution_timestamp" in meta
    assert "host_machine" in meta
    assert meta["wall_clock_seconds"] > 0


def test_write_mahout_artifacts(tmp_path: Path, mahout_docs: list[dict[str, Any]]) -> None:
    manifest_p = tmp_path / "mahout_manifest.json"
    report_p = tmp_path / "mahout_report.md"
    allowlist_p = tmp_path / "mahout_allowlist.txt"

    res = write_mahout_artifacts(
        manifest_path=manifest_p,
        report_path=report_p,
        allowlist_path=allowlist_p,
        target_size=400,
    )

    assert manifest_p.exists()
    assert report_p.exists()
    assert allowlist_p.exists()

    assert compute_sha256_file(manifest_p) == res["manifest_sha256"]
    assert compute_sha256_file(report_p) == res["report_sha256"]
    assert compute_sha256_file(allowlist_p) == res["allowlist_sha256"]

    # Allowlist must have exactly 400 non-empty lines
    lines = [line.strip() for line in allowlist_p.read_text().splitlines() if line.strip()]
    assert len(lines) == 400
    assert len(set(lines)) == 400
