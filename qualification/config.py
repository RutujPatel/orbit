"""Qualification Configuration, Identity Schemas, and Authoritative Artifact Locks.

Defines:
1. Two-layer separation: QualificationIdentity vs RunMetadata.
2. Authoritative GoGreen Jira raw capture artifact paths and SHA-256 locks.
3. Frozen GoGreen Jira configuration (resolving D-4, D-5, D-6).
4. GoGreen GitHub discovery state record.
"""

from __future__ import annotations

import json
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qualification.policy import compute_sha256_file, compute_sha256_text

FROZEN_ENGINE_COMMIT = "6d82d12"
JIRA_CONTRACT_VERSION = "shadow-jira-fixture-v1"
GITHUB_CONTRACT_VERSION = "shadow-github-fixture-v1"
QUALIFICATION_HARNESS_VERSION = "0.1.2"
DEFAULT_SAMPLING_SEED = 42

# ── Frozen Source Artifact Identities ──────────────────────────────────────────

# ── Provenance Assessment (Path B) ───────────────────────────────────────────
# Per Milestone 2A Data Governance Authorization line 79 ("Raw API responses:
# Prohibited; not persisted to disk"), raw REST HTTP bodies were discarded in
# memory on 2026-09-09. Therefore, historical raw REST responses were NOT retained.
HISTORICAL_RAW_REST_RETAINED: bool = False
RAW_SOURCE_INDEPENDENCE_ESTABLISHED_HISTORICAL: bool = False

# Source extraction manifest (Path B authoritative provenance record)
SOURCE_MANIFEST_PATH = Path("/home/tecblic/orbit-private/2a/raw/gogreen_jira_source_manifest.json")
SOURCE_MANIFEST_SHA256 = "8353724817152f21e3313ae0a44bf75e1fd5100c1f5b63c93d74210a7d81c2ad"

# Optional pointer for future raw Jira Cloud REST extractions
RAW_REST_CAPTURE_PATH = Path("/home/tecblic/orbit-private/2a/raw/gogreen_jira_rest_capture.json")

# Frozen 115-issue allowlist artifact approved by GoGreen Engineering Manager
FROZEN_ALLOWLIST_PATH = Path("/home/tecblic/orbit-private/2a/allowlist/gogreen_first_manual_projection.txt")
FROZEN_ALLOWLIST_SHA256 = "0638c9fb79b1c4243a1f898772e1c14e81a92eaef06b158ca10b0ffab6284bb1"
FROZEN_ALLOWLIST_COUNT = 115

# Authoritative observation cutoff
REST_SNAPSHOT_CUTOFF = "2026-09-09T12:40:07.050719+05:30"

# Retained Jira CSV export (exploratory census of 317 issues; lacking changelog history)
CSV_SOURCE_PATH = Path("/home/tecblic/orbit-private/2a/raw/gogreen_2a_issues.csv")
CSV_SOURCE_SHA256 = "1cc8bdc6ab47dc03370713da331bb37a6f17ff6b334a5e35b206bece3e8b520e"
CSV_SOURCE_CUTOFF = "2026-09-08T15:21:00+05:30"

# Reference historical fixture (Milestone 2A previous projection artifact)
REFERENCE_FIXTURE_PATH = Path("/home/tecblic/orbit-private/2a/working/gogreen_first_manual_projection_fixture.json")
REFERENCE_FIXTURE_SHA256 = "22ee227de61022a3dba49f57e3d0b7117c1b9ba5ee93da562519db5b5470c92b"

# ── Gate 2 Fresh Authorized Jira REST Capture Artifacts ──────────────────────
GATE2_RAW_CAPTURE_PATH = Path("/home/tecblic/orbit-private/gate2/raw/gate2_jira_raw_capture.json")
GATE2_RAW_CAPTURE_SHA256 = "4f6c22a816f801912274c9f5086dfb7aca07f0890ff47505af3273205c6b081b"
GATE2_SOURCE_MANIFEST_PATH = Path("/home/tecblic/orbit-private/gate2/raw/gate2_source_manifest.json")
GATE2_SOURCE_MANIFEST_SHA256 = "d6a60688f1efc219316404cee548590e2872a9d99831db37e944144c897df964"
GATE2_ENDPOINT_INVENTORY_PATH = Path("/home/tecblic/orbit-private/gate2/raw/gate2_endpoint_inventory.json")
GATE2_ENDPOINT_INVENTORY_SHA256 = "f5cace65cb4f9727ce47e2f7ba7bf2c900301beb7d723a60b0c206f059ee25a9"
GATE2_EXTRACTION_RECEIPT_PATH = Path("/home/tecblic/orbit-private/gate2/raw/gate2_extraction_receipt.json")
GATE2_ALLOWLIST_COUNT = 115

# Gate 2 Synthetic / Mock Fixture Directory (explicitly separated from empirical raw capture)
GATE2_SYNTHETIC_DIR = Path("/home/tecblic/orbit-private/gate2/synthetic")
GATE2_SYNTHETIC_RAW_CAPTURE_PATH = GATE2_SYNTHETIC_DIR / "gate2_jira_raw_capture.json"
GATE2_SYNTHETIC_MANIFEST_PATH = GATE2_SYNTHETIC_DIR / "gate2_source_manifest.json"
GATE2_SYNTHETIC_INVENTORY_PATH = GATE2_SYNTHETIC_DIR / "gate2_endpoint_inventory.json"

# Workspace fallback for CSV (if orbit-private path differs in test runner)
WORKSPACE_CSV_PATH = Path("/home/tecblic/.gemini/antigravity/brain/8a44eb06-14a2-47a0-9c3c-b117e8938d76/.user_uploaded/media_1789025288207.csv")

# ── GitHub Discovery Record ───────────────────────────────────────────────────
GITHUB_DISCOVERY_RECORD: dict[str, Any] = {
    "discovery_status": "COMPLETED",
    "organization": "TecblicInternal",
    "accessible_repositories": [
        "TecblicInternal/GoGreenDjango",
        "TecblicInternal/GoGreeen-React",
    ],
    "repositories_accessible": 2,
    "repositories_total": 2,
    "api_errors": 0,
    "pagination_complete": True,
    "observed_entities": {
        "pull_requests": 8,
        "pr_commit_associations": 23,
        "reviews": 1,
        "branches": 237,
        "unique_jira_keys_mentioned": 4,
    },
    "storage_location": "/home/tecblic/orbit-private/gogreen/github/raw",
    "qualification_phase": "Phase B (Deferred until Jira pipeline qualification is complete)",
}


@dataclass(frozen=True, slots=True)
class QualificationIdentity:
    """Canonical qualification identity determining semantic equivalence."""

    engine_commit: str = FROZEN_ENGINE_COMMIT
    jira_contract_version: str = JIRA_CONTRACT_VERSION
    github_contract_version: str = GITHUB_CONTRACT_VERSION
    projection_revision: str = "r2"
    dataset_hashes: tuple[tuple[str, str], ...] = ()
    harness_version: str = QUALIFICATION_HARNESS_VERSION
    configuration_digest: str = ""
    sampling_seed: int = DEFAULT_SAMPLING_SEED

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_commit": self.engine_commit,
            "jira_contract_version": self.jira_contract_version,
            "github_contract_version": self.github_contract_version,
            "projection_revision": self.projection_revision,
            "dataset_hashes": dict(self.dataset_hashes),
            "harness_version": self.harness_version,
            "configuration_digest": self.configuration_digest,
            "sampling_seed": self.sampling_seed,
        }


@dataclass(frozen=True, slots=True)
class RunMetadata:
    """Operational telemetry and environment metadata."""

    execution_timestamp: str
    host_machine: str = platform.node()
    os_system: str = platform.system()
    python_version: str = sys.version
    peak_memory_rss_bytes: int = 0
    wall_clock_seconds: float = 0.0
    source_extraction_timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_timestamp": self.execution_timestamp,
            "host_machine": self.host_machine,
            "os_system": self.os_system,
            "python_version": self.python_version,
            "peak_memory_rss_bytes": self.peak_memory_rss_bytes,
            "wall_clock_seconds": self.wall_clock_seconds,
            "source_extraction_timestamp": self.source_extraction_timestamp,
        }


@dataclass(frozen=True, slots=True)
class GoGreenJiraConfig:
    """Configuration for GoGreen Jira source projection.

    Resolves:
    - D-3: planning_basis.key = 'source_unavailable' (honest real-data basis)
    - D-4: project_key = 'GG', site_key = 'tecblic.atlassian.net'
    - D-5: review_period = 2026-W37 (2026-09-07 to 2026-09-12 Asia/Kolkata)
    - D-6: status_mapping table frozen with explicit semantic rationale
    """

    project_key: str = "GG"
    project_name: str = "GoGreen"
    site_key: str = "tecblic.atlassian.net"
    org_external_key: str = "tecblic"
    org_name: str = "Tecblic"
    team_external_key: str = "gogreen"
    team_name: str = "GoGreen"
    timezone: str = "Asia/Kolkata"

    # Review period (D-5)
    review_label: str = "2026-W37"
    starts_at: str = "2026-09-07T00:00:00+05:30"
    ends_at_exclusive: str = "2026-09-12T00:00:00+05:30"
    review_cutoff_at: str = "2026-09-12T00:00:00+05:30"
    source_cutoff_at: str = REST_SNAPSHOT_CUTOFF

    # Planning & thresholds (D-3: honest real-data planning basis)
    planning_basis_key: str = "source_unavailable"
    planning_basis_description: str = (
        "Real-data qualification basis: Jira provides no authoritative field equivalent "
        "for planned_at_period_start; values are honestly null."
    )
    stalled_threshold_complete_days: int = 7

    # Status mapping (D-6: Frozen status mapping with approved semantic rationale)
    status_mapping: dict[str, str] = field(
        default_factory=lambda: {
            "Close": "done",
            "In Progress": "in_progress",
            "In Review": "in_progress",
            "Waiting for Additional Informaiton": "blocked",
            "Re-Open": "in_progress",
            "To Do": "todo",
            "Done": "done",
            "Blocked": "blocked",
        }
    )

    # Priority mapping: Highest/High -> high, Medium/Low -> ordinary
    priority_mapping: dict[str, str] = field(
        default_factory=lambda: {
            "Highest": "high",
            "High": "high",
            "Medium": "ordinary",
            "Low": "ordinary",
        }
    )

    def compute_configuration_digest(self) -> str:
        """Compute canonical SHA-256 digest of active configuration."""
        canonical_dict = {
            "project_key": self.project_key,
            "site_key": self.site_key,
            "timezone": self.timezone,
            "review_period": {
                "label": self.review_label,
                "starts_at": self.starts_at,
                "ends_at_exclusive": self.ends_at_exclusive,
                "review_cutoff_at": self.review_cutoff_at,
                "source_cutoff_at": self.source_cutoff_at,
            },
            "planning_basis_key": self.planning_basis_key,
            "status_mapping": self.status_mapping,
            "priority_mapping": self.priority_mapping,
        }
        canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return compute_sha256_text(canonical_json)


def verify_and_compute_dataset_hashes(
    csv_path: Path | str = CSV_SOURCE_PATH,
    expected_csv_sha256: str = CSV_SOURCE_SHA256,
    allowlist_path: Path | str = FROZEN_ALLOWLIST_PATH,
    expected_allowlist_sha256: str = FROZEN_ALLOWLIST_SHA256,
    manifest_path: Path | str = SOURCE_MANIFEST_PATH,
    expected_manifest_sha256: str = SOURCE_MANIFEST_SHA256,
    reference_fixture_path: Path | str = REFERENCE_FIXTURE_PATH,
    expected_reference_fixture_sha256: str = REFERENCE_FIXTURE_SHA256,
) -> tuple[tuple[str, str], ...]:
    """Verify disk files against declared cryptographic locks and return verified actual hashes.

    Fails closed if any artifact is missing or if actual file bytes do not match declared locks.
    """
    artifacts = (
        ("csv_source_export", Path(csv_path), expected_csv_sha256),
        ("frozen_allowlist", Path(allowlist_path), expected_allowlist_sha256),
        ("source_manifest", Path(manifest_path), expected_manifest_sha256),
        ("historical_reference_fixture", Path(reference_fixture_path), expected_reference_fixture_sha256),
    )

    verified_hashes: list[tuple[str, str]] = []
    for label, path, expected_hash in artifacts:
        if not path.exists():
            raise FileNotFoundError(f"Authoritative qualification artifact missing: {label} at {path}")
        actual_hash = compute_sha256_file(path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"Cryptographic lock violated for {label}! Expected {expected_hash}, got actual {actual_hash}"
            )
        verified_hashes.append((label, actual_hash))

    return tuple(verified_hashes)


def create_populated_qualification_identity(
    config: GoGreenJiraConfig | None = None,
    projection_revision: str = "r2",
    sampling_seed: int = DEFAULT_SAMPLING_SEED,
    verify_on_disk: bool = True,
    dataset_hashes: tuple[tuple[str, str], ...] | None = None,
) -> QualificationIdentity:
    """Create a fully populated QualificationIdentity with verified actual hashes.

    When verify_on_disk is True (the default), recomputes SHA-256 digests from the actual
    files on disk immediately before execution and validates them against declared locks.
    """
    cfg = config or GoGreenJiraConfig()
    if dataset_hashes is not None:
        hashes = dataset_hashes
    elif verify_on_disk:
        hashes = verify_and_compute_dataset_hashes()
    else:
        hashes = (
            ("csv_source_export", CSV_SOURCE_SHA256),
            ("frozen_allowlist", FROZEN_ALLOWLIST_SHA256),
            ("source_manifest", SOURCE_MANIFEST_SHA256),
            ("historical_reference_fixture", REFERENCE_FIXTURE_SHA256),
        )

    return QualificationIdentity(
        engine_commit=FROZEN_ENGINE_COMMIT,
        jira_contract_version=JIRA_CONTRACT_VERSION,
        github_contract_version=GITHUB_CONTRACT_VERSION,
        projection_revision=projection_revision,
        dataset_hashes=hashes,
        harness_version=QUALIFICATION_HARNESS_VERSION,
        configuration_digest=cfg.compute_configuration_digest(),
        sampling_seed=sampling_seed,
    )


# ── Gate 2 Fresh REST Configuration and Identity ──────────────────────────────

@dataclass(frozen=True, slots=True)
class Gate2JiraConfig:
    """Configuration for Gate 2 fresh Jira Cloud REST extraction."""

    organization_key: str = "tecblic"
    organization_name: str = "Tecblic"
    team_key: str = "gogreen"
    team_name: str = "GoGreen"
    site_key: str = "gogreen-jira"
    project_key: str = "GG"
    project_name: str = "GoGreen"
    timezone: str = "Asia/Kolkata"
    review_label: str = "2026-W38"
    starts_at: str = "2026-09-14T00:00:00+05:30"
    ends_at_exclusive: str = "2026-09-19T00:00:00+05:30"
    review_cutoff_at: str = "2026-09-19T00:00:00+05:30"
    source_cutoff_at: str = "2026-09-16T12:00:00+05:30"
    planning_basis_key: str = "source_unavailable"
    stalled_threshold_complete_days: int = 7
    status_mapping: dict[str, str] = field(
        default_factory=lambda: {
            "Close": "done",
            "In Progress": "in_progress",
            "In Review": "in_progress",
            "Waiting for Additional Informaiton": "blocked",
            "Re-Open": "in_progress",
            "To Do": "todo",
            "Done": "done",
            "Blocked": "blocked",
        }
    )
    priority_mapping: dict[str, str] = field(
        default_factory=lambda: {
            "Highest": "high",
            "High": "high",
            "Medium": "ordinary",
            "Low": "ordinary",
        }
    )

    def compute_configuration_digest(self) -> str:
        canonical_dict = {
            "organization_key": self.organization_key,
            "team_key": self.team_key,
            "project_key": self.project_key,
            "site_key": self.site_key,
            "timezone": self.timezone,
            "review_period": {
                "label": self.review_label,
                "starts_at": self.starts_at,
                "ends_at_exclusive": self.ends_at_exclusive,
                "review_cutoff_at": self.review_cutoff_at,
                "source_cutoff_at": self.source_cutoff_at,
            },
            "planning_basis_key": self.planning_basis_key,
            "status_mapping": self.status_mapping,
            "priority_mapping": self.priority_mapping,
        }
        canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return compute_sha256_text(canonical_json)


def verify_and_compute_gate2_dataset_hashes(
    raw_capture_path: Path | str = GATE2_RAW_CAPTURE_PATH,
    source_manifest_path: Path | str = GATE2_SOURCE_MANIFEST_PATH,
    endpoint_inventory_path: Path | str = GATE2_ENDPOINT_INVENTORY_PATH,
    expected_raw_capture_sha256: str = GATE2_RAW_CAPTURE_SHA256,
    expected_manifest_sha256: str = GATE2_SOURCE_MANIFEST_SHA256,
    expected_inventory_sha256: str = GATE2_ENDPOINT_INVENTORY_SHA256,
) -> tuple[tuple[str, str], ...]:
    """Verify Gate 2 disk files exist, validate against cryptographic locks, and return digests.

    Fails closed if any Gate 2 raw artifact is missing or tampered.
    NOTE: Hashes establish artifact identity and cryptographic integrity on disk.
    Hashes DO NOT prove source authenticity, live extraction, temporal freshness, or Jira origin.
    """
    artifacts = (
        ("gate2_raw_capture", Path(raw_capture_path), expected_raw_capture_sha256),
        ("gate2_source_manifest", Path(source_manifest_path), expected_manifest_sha256),
        ("gate2_endpoint_inventory", Path(endpoint_inventory_path), expected_inventory_sha256),
    )

    verified_hashes: list[tuple[str, str]] = []
    for label, path, expected_hash in artifacts:
        if not path.exists():
            raise FileNotFoundError(f"Gate 2 qualification artifact missing: {label} at {path}")
        actual_hash = compute_sha256_file(path)
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"Cryptographic lock violated for Gate 2 {label}! Expected {expected_hash}, got actual {actual_hash}"
            )
        verified_hashes.append((label, actual_hash))

    return tuple(verified_hashes)


def create_gate2_qualification_identity(
    config: Gate2JiraConfig | None = None,
    projection_revision: str = "gate2-r1",
    sampling_seed: int = DEFAULT_SAMPLING_SEED,
    verify_on_disk: bool = True,
    dataset_hashes: tuple[tuple[str, str], ...] | None = None,
) -> QualificationIdentity:
    """Create a populated QualificationIdentity for Gate 2 fresh REST qualification."""
    cfg = config or Gate2JiraConfig()
    if dataset_hashes is not None:
        hashes = dataset_hashes
    elif verify_on_disk:
        hashes = verify_and_compute_gate2_dataset_hashes()
    else:
        hashes = (
            ("gate2_raw_capture", GATE2_RAW_CAPTURE_SHA256),
            ("gate2_source_manifest", GATE2_SOURCE_MANIFEST_SHA256),
            ("gate2_endpoint_inventory", GATE2_ENDPOINT_INVENTORY_SHA256),
        )

    return QualificationIdentity(
        engine_commit=FROZEN_ENGINE_COMMIT,
        jira_contract_version=JIRA_CONTRACT_VERSION,
        github_contract_version=GITHUB_CONTRACT_VERSION,
        projection_revision=projection_revision,
        dataset_hashes=hashes,
        harness_version=QUALIFICATION_HARNESS_VERSION,
        configuration_digest=cfg.compute_configuration_digest(),
        sampling_seed=sampling_seed,
    )

