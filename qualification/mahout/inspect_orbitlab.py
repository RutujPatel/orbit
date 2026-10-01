"""ORBITLAB Project Capabilities & Vocabulary Compatibility Inspector.

Target: https://tecblic.atlassian.net
Project: ORBITLAB ('Shadow ORBIT Qualification Lab')

Executes:
- Step 1: GET /rest/api/3/project/ORBITLAB (project metadata, style, type, simplified)
- Step 2: GET /rest/api/3/issue/createmeta?projectKeys=ORBITLAB&expand=projects.issuetypes.fields (creation vocabulary)
- Step 3: GET /rest/api/3/project/ORBITLAB/statuses (statuses and workflow transitions)
- Step 4: GET /rest/api/3/priority (priorities)
- Step 5: Vocabulary compatibility evaluation and Import Readiness Gate (READY, BLOCKED, BLOCKED_REQUIRES_CONFIGURATION_REVIEW)

Zero credentials written to disk or logged.
Zero Jira issues created or mutated.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qualification.mahout.compatibility import (
    DEFAULT_COMPATIBILITY_JSON_PATH,
    DEFAULT_COMPATIBILITY_MD_PATH,
    CompatibilityClassification,
    CompatibilityMatrix,
    FieldCompatibility,
    ImportReadinessGate,
    ItemCompatibility,
    MAHOUT_SOURCE_PRIORITIES,
    MAHOUT_SOURCE_STATUSES,
    MAHOUT_SOURCE_TRANSITIONS,
    MAHOUT_SOURCE_TYPES,
    TransitionCompatibility,
    evaluate_compatibility,
    write_compatibility_reports,
)
from qualification.policy import compute_sha256_file, compute_sha256_text

DEFAULT_INSPECTION_EVIDENCE_PATH = Path("/home/tecblic/orbit-private/mahout/orbitlab_inspection_evidence.json")


def _make_jira_request(
    url: str,
    email: str | None,
    token: str | None,
    timeout: int = 30,
) -> tuple[int, dict[str, Any], dict[str, str], float]:
    """Execute authenticated or probe HTTP GET request to Jira Cloud, preserving transport telemetry."""
    headers = {
        "Accept": "application/json",
        "User-Agent": "Shadow-ORBIT-Qualification-Harness/1.0",
    }
    if email and token:
        auth_bytes = f"{email}:{token}".encode("utf-8")
        headers["Authorization"] = f"Basic {base64.b64encode(auth_bytes).decode('ascii')}"

    req = urllib.request.Request(url, headers=headers, method="GET")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency_ms = (time.time() - t0) * 1000
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body) if resp_body.strip() else {}
            return resp.status, data, dict(resp.headers), round(latency_ms, 2)
    except urllib.error.HTTPError as exc:
        latency_ms = (time.time() - t0) * 1000
        err_body = exc.read().decode("utf-8", errors="replace")
        data = {"error": err_body.strip(), "code": exc.code}
        return exc.code, data, dict(exc.headers), round(latency_ms, 2)


def execute_orbitlab_inspection(
    base_url: str | None = None,
    evidence_path: Path | str = DEFAULT_INSPECTION_EVIDENCE_PATH,
    compatibility_json_path: Path | str = DEFAULT_COMPATIBILITY_JSON_PATH,
    compatibility_md_path: Path | str = DEFAULT_COMPATIBILITY_MD_PATH,
    email: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    """Execute live 4-step inspection against ORBITLAB project on Jira Cloud.
    
    Reads credentials strictly from runtime environment variables (JIRA_EMAIL, JIRA_API_TOKEN)
    or explicitly supplied arguments. Zero plaintext credential files used or persisted.
    """
    out_evidence = Path(evidence_path)
    out_evidence.parent.mkdir(parents=True, exist_ok=True)

    if email is None:
        email = os.environ.get("JIRA_EMAIL") or os.environ.get("JIRA_USER") or os.environ.get("ATLASSIAN_EMAIL")
    if token is None:
        token = os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN") or os.environ.get("ATLASSIAN_TOKEN")

    if base_url is None:
        base_url = os.environ.get("JIRA_BASE_URL") or "https://tecblic.atlassian.net"
    base_url = base_url.rstrip("/")

    t_start = datetime.now(timezone.utc).isoformat()
    credentials_present = bool(email and token)

    telemetry_records: list[dict[str, Any]] = []

    if credentials_present:
        # Step 1: Project Metadata
        status1, proj_data, headers1, lat1 = _make_jira_request(
            f"{base_url}/rest/api/3/project/ORBITLAB", email, token
        )
        telemetry_records.append({
            "endpoint": "/rest/api/3/project/ORBITLAB",
            "status": status1,
            "latency_ms": lat1,
            "transport_headers": {
                "server": headers1.get("Server") or headers1.get("server"),
                "atl_trace_id": headers1.get("Atl-Traceid") or headers1.get("atl-traceid"),
                "x_a_request_id": headers1.get("X-Arequestid") or headers1.get("x-arequestid"),
            },
        })

        # Step 2: Createmeta
        createmeta_url = (
            f"{base_url}/rest/api/3/issue/createmeta?projectKeys=ORBITLAB&expand=projects.issuetypes.fields"
        )
        status2, createmeta_data, headers2, lat2 = _make_jira_request(createmeta_url, email, token)
        telemetry_records.append({
            "endpoint": "/rest/api/3/issue/createmeta",
            "status": status2,
            "latency_ms": lat2,
            "transport_headers": {
                "server": headers2.get("Server") or headers2.get("server"),
                "atl_trace_id": headers2.get("Atl-Traceid") or headers2.get("atl-traceid"),
                "x_a_request_id": headers2.get("X-Arequestid") or headers2.get("x-arequestid"),
            },
        })

        # Step 3: Statuses
        status3, statuses_data, headers3, lat3 = _make_jira_request(
            f"{base_url}/rest/api/3/project/ORBITLAB/statuses", email, token
        )
        telemetry_records.append({
            "endpoint": "/rest/api/3/project/ORBITLAB/statuses",
            "status": status3,
            "latency_ms": lat3,
            "transport_headers": {
                "server": headers3.get("Server") or headers3.get("server"),
                "atl_trace_id": headers3.get("Atl-Traceid") or headers3.get("atl-traceid"),
                "x_a_request_id": headers3.get("X-Arequestid") or headers3.get("x-arequestid"),
            },
        })

        # Step 4: Priorities
        status4, priorities_data, headers4, lat4 = _make_jira_request(
            f"{base_url}/rest/api/3/priority", email, token
        )
        telemetry_records.append({
            "endpoint": "/rest/api/3/priority",
            "status": status4,
            "latency_ms": lat4,
            "transport_headers": {
                "server": headers4.get("Server") or headers4.get("server"),
                "atl_trace_id": headers4.get("Atl-Traceid") or headers4.get("atl-traceid"),
                "x_a_request_id": headers4.get("X-Arequestid") or headers4.get("x-arequestid"),
            },
        })

        if status1 == 200 and status2 == 200:
            matrix = evaluate_compatibility(
                project_meta=proj_data,
                createmeta=createmeta_data,
                statuses_meta=statuses_data if isinstance(statuses_data, list) else [],
                priorities_meta=priorities_data if isinstance(priorities_data, list) else [],
            )
            inspection_status = "AUTHENTICATED_INSPECTION_COMPLETED"
        else:
            # Authenticated request returned error (e.g. 403 Forbidden or 404 Project Not Found)
            matrix = CompatibilityMatrix(
                project_identity={"key": "ORBITLAB", "status": f"HTTP {status1}"},
                issue_types=(),
                priorities=(),
                statuses=(),
                transitions=(),
                fields=(),
                readiness_gate=ImportReadinessGate.BLOCKED,
                readiness_reasons=(f"Authenticated query failed with HTTP {status1}: {proj_data.get('error', '')}",),
            )
            inspection_status = "AUTHENTICATED_QUERY_FAILED"

    else:
        # Unauthenticated probe
        status_probe, probe_data, headers_probe, lat_probe = _make_jira_request(
            f"{base_url}/rest/api/3/project/ORBITLAB", None, None
        )
        telemetry_records.append({
            "endpoint": "/rest/api/3/project/ORBITLAB",
            "status": status_probe,
            "latency_ms": lat_probe,
            "transport_headers": {
                "server": headers_probe.get("Server") or headers_probe.get("server"),
                "atl_trace_id": headers_probe.get("Atl-Traceid") or headers_probe.get("atl-traceid"),
                "x_a_request_id": headers_probe.get("X-Arequestid") or headers_probe.get("x-arequestid"),
                "strict_transport_security": headers_probe.get("Strict-Transport-Security"),
                "http_date": headers_probe.get("Date"),
            },
            "error_response": probe_data,
        })

        unauth_types = tuple(
            ItemCompatibility(
                source_value=t,
                destination_value=None,
                classification=CompatibilityClassification.UNAVAILABLE,
                rationale="Uninspected: destination createmeta blocked by missing authentication",
                requires_review=True,
            )
            for t in MAHOUT_SOURCE_TYPES
        )
        unauth_prios = tuple(
            ItemCompatibility(
                source_value=p,
                destination_value=None,
                classification=CompatibilityClassification.UNAVAILABLE,
                rationale="Uninspected: destination priority endpoint blocked by missing authentication",
                requires_review=True,
            )
            for p in MAHOUT_SOURCE_PRIORITIES
        )
        unauth_statuses = tuple(
            ItemCompatibility(
                source_value=s,
                destination_value=None,
                classification=CompatibilityClassification.UNAVAILABLE,
                rationale="Uninspected: destination project statuses blocked by missing authentication",
                requires_review=True,
            )
            for s in MAHOUT_SOURCE_STATUSES
        )
        unauth_transitions = tuple(
            TransitionCompatibility(
                source_from=t_from,
                source_to=t_to,
                destination_path=[],
                classification=CompatibilityClassification.UNAVAILABLE,
                rationale="Uninspected: workflow transition graph blocked by missing authentication",
            )
            for t_from, t_to in MAHOUT_SOURCE_TRANSITIONS
        )
        unauth_fields = tuple(
            FieldCompatibility(
                field_key=fk,
                field_name=fk.capitalize(),
                supported=False,
                required=False,
                schema_type="unknown",
                notes="Uninspected: field schema blocked by missing authentication",
            )
            for fk in ("summary", "description", "duedate", "priority", "issuetype")
        )

        matrix = CompatibilityMatrix(
            project_identity={"key": "ORBITLAB", "base_url": base_url, "status": f"HTTP {status_probe} Unauthenticated"},
            issue_types=unauth_types,
            priorities=unauth_prios,
            statuses=unauth_statuses,
            transitions=unauth_transitions,
            fields=unauth_fields,
            readiness_gate=ImportReadinessGate.BLOCKED,
            readiness_reasons=(
                "ORBITLAB inspection blocked: valid Jira Cloud runtime credentials "
                "(runtime email / API token) are not set in the execution environment. "
                f"Unauthenticated live probe returned HTTP {status_probe} with AtlassianEdge transport headers.",
            ),
        )
        inspection_status = "BLOCKED_BY_AUTHENTICATION_OR_PERMISSIONS"

    # Write compatibility reports
    rep_files = write_compatibility_reports(
        matrix=matrix,
        json_path=compatibility_json_path,
        md_path=compatibility_md_path,
    )

    # Save evidence file
    evidence = {
        "inspection_timestamp": t_start,
        "base_url": base_url,
        "project_key": "ORBITLAB",
        "credentials_present": credentials_present,
        "inspection_status": inspection_status,
        "readiness_gate": matrix.readiness_gate.value,
        "telemetry_records": telemetry_records,
        "zero_mutations_asserted": True,
    }

    with out_evidence.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    evidence_sha = compute_sha256_file(out_evidence)

    return {
        "inspection_status": inspection_status,
        "credentials_present": credentials_present,
        "readiness_gate": matrix.readiness_gate.value,
        "readiness_reasons": list(matrix.readiness_reasons),
        "evidence_path": str(out_evidence),
        "evidence_sha256": evidence_sha,
        "compatibility_json_path": rep_files["json_path"],
        "compatibility_json_sha256": rep_files["json_sha256"],
        "compatibility_md_path": rep_files["md_path"],
        "compatibility_md_sha256": rep_files["md_sha256"],
        "telemetry_records": telemetry_records,
    }


if __name__ == "__main__":
    res = execute_orbitlab_inspection()
    print("ORBITLAB Inspection probe executed:")
    safe_summary = {k: v for k, v in res.items() if k != "telemetry_records"}
    print(json.dumps(safe_summary, indent=2))
    print(f"Readiness Gate: {res['readiness_gate']}")
    for r in res.get("readiness_reasons", []):
        print(f"- {r}")

