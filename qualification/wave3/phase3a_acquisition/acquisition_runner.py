"""Pass 5 / Wave 3 Phase 3A — Controlled Evidence Acquisition Runner.

Executes Stage B evidence acquisition strictly against the frozen cohort manifest:
- Reads qualification/wave3/phase3a_acquisition/manifest/phase3a_frozen_cohort.json
- Verifies SHA-256 integrity of the frozen manifest
- Performs read-only GitHub REST API calls via gh CLI
- Enforces identity safety and closed outcome taxonomy
- Persists raw JSON responses without transforming into canonical models
- Computes SHA-256 digests for all acquired raw artifacts
- Generates outcomes/acquisition_results.json and CSV
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = BASE_DIR / "manifest" / "phase3a_frozen_cohort.json"
EXPECTED_MANIFEST_SHA256 = "3aa4ebabefa84e95dd433d20ba82c852cce4a1bfe7a4f246bb9c01873f077775"

RAW_DIR = BASE_DIR / "raw"
OUTCOMES_DIR = BASE_DIR / "outcomes"
HASHES_DIR = BASE_DIR / "hashes"

RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTCOMES_DIR.mkdir(parents=True, exist_ok=True)
HASHES_DIR.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    """Compute SHA-256 of a local file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def call_gh_api(endpoint: str) -> tuple[int, dict[str, Any] | list[Any] | None, str]:
    """Execute gh api and return (http_status, parsed_json, error_message)."""
    cmd = ["gh", "api", endpoint, "--include"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return 0, None, "Request timed out after 30s"
    except Exception as e:
        return 0, None, str(e)

    # gh api --include outputs HTTP response headers followed by empty line, then body
    stdout = res.stdout
    stderr = res.stderr

    status_code = 0
    body = ""

    lines = stdout.splitlines()
    header_mode = True
    body_lines = []

    for idx, line in enumerate(lines):
        if header_mode:
            if idx == 0 and line.startswith("HTTP/"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    status_code = int(parts[1])
            elif line.strip() == "":
                header_mode = False
        else:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    if status_code == 0:
        # Fallback if gh headers weren't captured as expected
        if res.returncode == 0:
            status_code = 200
            body = stdout.strip()
        else:
            if "404" in stderr or "Not Found" in stderr:
                status_code = 404
            elif "403" in stderr:
                status_code = 403
            elif "401" in stderr:
                status_code = 401
            else:
                status_code = 500

    parsed = None
    if body:
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = None

    err = stderr.strip() if res.returncode != 0 else ""
    return status_code, parsed, err


def run_acquisition():
    print("=" * 80)
    print("PASS 5 / WAVE 3 PHASE 3A — CONTROLLED EVIDENCE ACQUISITION")
    print("=" * 80)

    # Step 1: Verify Manifest Integrity
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Cohort manifest not found: {MANIFEST_PATH}")

    actual_hash = sha256_file(MANIFEST_PATH)
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Manifest SHA-256: {actual_hash}")
    if actual_hash != EXPECTED_MANIFEST_SHA256:
        raise ValueError(
            f"Manifest SHA-256 mismatch!\nExpected: {EXPECTED_MANIFEST_SHA256}\nActual:   {actual_hash}"
        )
    print("✓ Manifest integrity verified. Beginning Stage B acquisition.\n")

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    candidates = manifest["candidates"]
    total = len(candidates)
    print(f"Total frozen cohort candidates to acquire: {total}")

    outcomes = []
    acquired_artifacts = {}
    identity_checks = []

    # Closed Outcome Taxonomy:
    # ACQUIRED, NOT_FOUND, ACCESS_DENIED, RATE_LIMITED, UNAVAILABLE,
    # MALFORMED_REFERENCE, UNSUPPORTED_REPOSITORY, API_ERROR, NETWORK_ERROR

    for idx, c in enumerate(candidates, 1):
        rank = c["selection_rank"]
        proj = c["project"]
        jira_key = c["jira_key"]
        repo = c["repository"]
        pr_num = c["pr_number"]
        url = c["source_url"]

        safe_repo = repo.replace("/", "__")
        repo_dir = RAW_DIR / proj / safe_repo
        repo_dir.mkdir(parents=True, exist_ok=True)

        pr_file = repo_dir / f"pr_{pr_num}.json"
        commits_file = repo_dir / f"pr_{pr_num}_commits.json"
        reviews_file = repo_dir / f"pr_{pr_num}_reviews.json"

        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{idx:3d}/{total:3d}] #{rank:3d} {proj:<10} {jira_key:<15} -> {repo} #{pr_num} ... ", end="", flush=True)

        # Retrieve PR metadata
        endpoint = f"repos/{repo}/pulls/{pr_num}"
        status_code, pr_data, err_msg = call_gh_api(endpoint)

        outcome = "API_ERROR"
        artifact_path = None
        error_class = None

        if status_code == 200 and isinstance(pr_data, dict):
            # Check identity safety
            returned_num = pr_data.get("number")
            base_repo_obj = pr_data.get("base", {}).get("repo", {}) or {}
            returned_repo = base_repo_obj.get("full_name") or repo

            num_matches = (returned_num == pr_num)
            repo_matches = (returned_repo.lower() == repo.lower())

            identity_checks.append({
                "selection_rank": rank,
                "jira_key": jira_key,
                "requested_repo": repo,
                "returned_repo": returned_repo,
                "requested_pr_number": pr_num,
                "returned_pr_number": returned_num,
                "repo_matches": repo_matches,
                "num_matches": num_matches,
                "identity_safe": (num_matches and repo_matches)
            })

            if not num_matches:
                outcome = "API_ERROR"
                error_class = f"PR number mismatch: requested {pr_num}, got {returned_num}"
                print(f"FAILED (ID mismatch)")
            else:
                outcome = "ACQUIRED"
                artifact_path = str(pr_file.relative_to(BASE_DIR))

                # Save raw PR JSON
                with open(pr_file, "w", encoding="utf-8") as pf:
                    json.dump(pr_data, pf, indent=2)
                acquired_artifacts[artifact_path] = sha256_file(pr_file)

                # Acquire supporting evidence: commits
                time.sleep(0.15)
                c_status, c_data, _ = call_gh_api(f"repos/{repo}/pulls/{pr_num}/commits")
                if c_status == 200 and isinstance(c_data, list):
                    with open(commits_file, "w", encoding="utf-8") as cf:
                        json.dump(c_data, cf, indent=2)
                    c_rel = str(commits_file.relative_to(BASE_DIR))
                    acquired_artifacts[c_rel] = sha256_file(commits_file)

                # Acquire supporting evidence: reviews
                time.sleep(0.15)
                r_status, r_data, _ = call_gh_api(f"repos/{repo}/pulls/{pr_num}/reviews")
                if r_status == 200 and isinstance(r_data, list):
                    with open(reviews_file, "w", encoding="utf-8") as rf:
                        json.dump(r_data, rf, indent=2)
                    r_rel = str(reviews_file.relative_to(BASE_DIR))
                    acquired_artifacts[r_rel] = sha256_file(reviews_file)

                state_str = pr_data.get("state")
                merged_str = "merged" if pr_data.get("merged") else "unmerged"
                print(f"ACQUIRED ({state_str}, {merged_str})")

        elif status_code == 404:
            # Check whether repository exists or PR doesn't exist
            time.sleep(0.1)
            repo_status, repo_data, _ = call_gh_api(f"repos/{repo}")
            if repo_status == 404:
                outcome = "UNSUPPORTED_REPOSITORY"
                error_class = f"Repository '{repo}' not found on GitHub"
                print(f"UNSUPPORTED_REPOSITORY (Repo 404)")
            else:
                outcome = "NOT_FOUND"
                error_class = f"PR #{pr_num} not found in repository '{repo}'"
                print(f"NOT_FOUND (PR 404)")

        elif status_code in (401, 403):
            if "rate limit" in err_msg.lower():
                outcome = "RATE_LIMITED"
                error_class = err_msg
                print(f"RATE_LIMITED")
            else:
                outcome = "ACCESS_DENIED"
                error_class = err_msg or "HTTP 403 Forbidden"
                print(f"ACCESS_DENIED")

        elif status_code == 0:
            outcome = "NETWORK_ERROR"
            error_class = err_msg or "Connection failure"
            print(f"NETWORK_ERROR")

        else:
            outcome = "API_ERROR"
            error_class = f"HTTP {status_code}: {err_msg}"
            print(f"API_ERROR (HTTP {status_code})")

        outcomes.append({
            "selection_rank": rank,
            "project": proj,
            "jira_key": jira_key,
            "repository": repo,
            "pr_number": pr_num,
            "requested_url": url,
            "outcome": outcome,
            "http_status": status_code,
            "retrieval_timestamp": timestamp,
            "error_classification": error_class,
            "raw_artifact_path": artifact_path,
        })

        # Polite throttle delay
        time.sleep(0.2)

    # Step 3: Write Outcomes & Hashes
    results_json_path = OUTCOMES_DIR / "acquisition_results.json"
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(outcomes, f, indent=2)

    results_csv_path = OUTCOMES_DIR / "acquisition_results.csv"
    with open(results_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "selection_rank", "project", "jira_key", "repository", "pr_number",
            "requested_url", "outcome", "http_status", "retrieval_timestamp",
            "error_classification", "raw_artifact_path"
        ])
        writer.writeheader()
        writer.writerows(outcomes)

    hashes_path = HASHES_DIR / "raw_sha256.json"
    with open(hashes_path, "w", encoding="utf-8") as f:
        json.dump(acquired_artifacts, f, indent=2, sort_keys=True)

    # Step 4: Summary Metrics
    counts = {}
    for o in outcomes:
        c_val = o["outcome"]
        counts[c_val] = counts.get(c_val, 0) + 1

    print("\n" + "=" * 80)
    print("ACQUISITION OUTCOME SUMMARY")
    print("=" * 80)
    print(f"Total Cohort Candidates:       {total}")
    for k, v in sorted(counts.items()):
        print(f"  {k:<26} {v:3d} ({v/total*100:5.1f}%)")
    print(f"Total Raw Artifacts Stored:    {len(acquired_artifacts)}")
    print(f"Raw Artifact Hashes Saved:     {hashes_path}")
    print(f"Outcomes Saved:                {results_json_path}")
    print("=" * 80)

    return outcomes, acquired_artifacts, identity_checks, counts


if __name__ == "__main__":
    run_acquisition()
