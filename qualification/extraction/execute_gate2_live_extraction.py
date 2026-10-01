"""Authorized Live Jira REST Extraction Execution Runner for Gate 2.

Target: https://tecblic.atlassian.net
Scope: 115 frozen allowlist keys from FROZEN_ALLOWLIST_PATH
Credentials: Runtime environment only (JIRA_EMAIL / JIRA_API_TOKEN)
Protocol: Two-pass bounded observation with fail-closed failure evidence preservation.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure orbit repo root and src/ are on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from qualification.config import (
    FROZEN_ALLOWLIST_PATH,
    FROZEN_ALLOWLIST_SHA256,
    GATE2_RAW_CAPTURE_PATH,
    GATE2_SOURCE_MANIFEST_PATH,
    GATE2_ENDPOINT_INVENTORY_PATH,
    GATE2_EXTRACTION_RECEIPT_PATH,
)
from qualification.policy import (
    ProvenanceError,
    ProvenanceReceiptError,
    ProvenanceScopeError,
    verify_extraction_provenance,
)
from qualification.projection.jira_projection import load_frozen_allowlist, project_gate2_raw_rest
from qualification.extraction.jira_extractor import JiraExtractor, save_gate2_raw_artifacts


def run_gate2_live_extraction(output_dir: Path | str = "/home/tecblic/orbit-private/gate2/raw") -> dict[str, Any]:
    out_path = Path(output_dir)
    failure_log_path = Path("/home/tecblic/orbit-private/gate2/live_extraction_failure_evidence.json")

    # Step 1: Record extraction start
    start_time = datetime.now(timezone.utc)
    start_iso = start_time.isoformat()
    print(f"=== GATE 2 LIVE EXTRACTION STARTED AT {start_iso} ===")

    # Load frozen allowlist
    allowlist_keys = sorted(list(load_frozen_allowlist()))
    print(f"Authorized Scope: {len(allowlist_keys)} issues loaded from {FROZEN_ALLOWLIST_PATH}")
    assert len(allowlist_keys) == 115, f"Expected 115 keys, got {len(allowlist_keys)}"

    # Credentials from runtime environment only
    email = os.environ.get("JIRA_EMAIL") or os.environ.get("JIRA_USER") or os.environ.get("ATLASSIAN_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN") or os.environ.get("ATLASSIAN_TOKEN")
    base_url = "https://tecblic.atlassian.net"

    print(f"Target: {base_url}")
    print(f"Credentials present in runtime environment: email={'YES' if email else 'NO'}, token={'YES' if token else 'NO'}")

    extractor = JiraExtractor(
        base_url=base_url,
        email=email,
        token=token,
        output_dir=out_path,
        user_agent="ShadowORBIT-Gate2-LiveExtractor/1.0",
        timeout=30,
    )

    try:
        # Step 2: Pass A over exactly the authorized 115 issues
        # Step 3: Establish candidate source cutoff
        # Step 4: Pass B over the same exact 115 issues
        # Step 5: Record actual HTTP transaction telemetry
        # Step 6: Verify fingerprints and two-pass scope
        # Step 7: Seal ExtractionReceipt during active runtime session
        print("Executing two-pass bounded observation...")
        pass_a_issues, candidate_cutoff, inventory, receipt = extractor.two_pass_observe(
            issue_keys=allowlist_keys,
            allowlist_path=FROZEN_ALLOWLIST_PATH,
            allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )
        print(f"Pass A & Pass B completed successfully. Cutoff: {candidate_cutoff}")

        # Step 8: Persist raw capture + inventory + receipt + manifest
        print(f"Persisting artifacts to {out_path}...")
        raw_cap_path, manifest_path, inv_path, r_path = save_gate2_raw_artifacts(
            raw_issues=pass_a_issues,
            source_cutoff_at=candidate_cutoff,
            endpoint_inventory=inventory,
            output_dir=out_path,
            receipt=receipt,
            operator="Rutuj Patel",
            authorization_ref="GATE-2-MANAGER-APPROVAL",
        )

        # Step 9: Run verify_extraction_provenance()
        print("Running verify_extraction_provenance()...")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        prov_status = verify_extraction_provenance(
            manifest=manifest,
            raw_capture_path=raw_cap_path,
            inventory_path=inv_path,
            receipt_path=r_path,
            allowlist_keys=set(allowlist_keys),
            expected_allowlist_sha256=FROZEN_ALLOWLIST_SHA256,
        )
        print(f"Provenance verification succeeded: {prov_status}")

        # Step 10: Project into frozen CSE @ 6d82d12
        print("Projecting into frozen CSE schema...")
        projected = project_gate2_raw_rest(
            raw_capture_path=raw_cap_path,
            allowlist=set(allowlist_keys),
            require_exact_scope=True,
        )
        print(f"Projected {len(projected['work_items'])} work items into frozen CSE.")

        return {
            "status": "SUCCESS",
            "provenance_status": prov_status,
            "issues_count": len(pass_a_issues),
            "transactions_count": len(inventory),
            "cutoff": candidate_cutoff,
        }

    except Exception as exc:
        end_time = datetime.now(timezone.utc)
        print(f"\n[CRITICAL] Extraction failed at {end_time.isoformat()}: {exc}")
        print("Preserving failure evidence and stopping without synthetic fallback.")

        failure_evidence = {
            "failure_timestamp": end_time.isoformat(),
            "extraction_started_at": start_iso,
            "target_base_url": base_url,
            "scope_allowlist_count": len(allowlist_keys),
            "allowlist_path": str(FROZEN_ALLOWLIST_PATH),
            "allowlist_sha256": FROZEN_ALLOWLIST_SHA256,
            "credentials_configured": {
                "email_configured": bool(email),
                "token_configured": bool(token),
            },
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "total_transactions_attempted": len(extractor.endpoint_inventory),
            "transactions": extractor.endpoint_inventory,
        }

        with open(failure_log_path, "w", encoding="utf-8") as f:
            json.dump(failure_evidence, f, indent=2)

        print(f"Failure evidence safely recorded at {failure_log_path}")
        return {
            "status": "FAILED",
            "error": str(exc),
            "failure_evidence_path": str(failure_log_path),
            "transactions_count": len(extractor.endpoint_inventory),
        }


if __name__ == "__main__":
    result = run_gate2_live_extraction()
    print("\nResult summary:", json.dumps(result, indent=2))
    if result["status"] != "SUCCESS":
        sys.exit(1)
