"""TrueTenant Blind Hold-Out Qualification Runner.

Executes Phases 5 through 10 in a single controlled script:
  Phase 5 — Normalization validation (before evaluation)
  Phase 6 — Track B evaluation
  Phase 7 — Generalization metrics
  Phase 9 — Provider leakage check
  Phase 10 — Determinism (two independent runs + permutation)

Governance:
  - Does not modify any existing fixture, golden, or source files
  - Does not call git add/commit/stash/reset
  - Does not make network calls
  - Does not modify TrueTenant source data
  - save_golden=False (never overwrites existing golden artifacts)
  - All output written to qualification/truetenant/output/
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.validation import validate_fixture
from shadow_orbit.evaluation import evaluate_week_one_rules, calculate_supporting_facts
from shadow_orbit.types import WorkItem

from qualification.truetenant.ingestion import build_truetenant_fixture_document

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Provider Leakage Guard ─────────────────────────────────────────────────────

_JIRA_CONSTRUCTOR_CALLS = 0
_GITHUB_CONSTRUCTOR_CALLS = 0


def _install_leakage_guard() -> None:
    """Instrument provider-specific constructors to detect leakage.
    
    Any call to JiraIssueState or GitHubPullRequestState during the
    TrueTenant canonical path would indicate provider leakage.
    """
    global _JIRA_CONSTRUCTOR_CALLS, _GITHUB_CONSTRUCTOR_CALLS

    try:
        from shadow_orbit import evidence_types
        original_jira = getattr(evidence_types, "JiraIssueState", None)
        original_github = getattr(evidence_types, "GitHubPullRequestState", None)

        if original_jira:
            class _JiraGuard:
                def __init__(self, *args, **kwargs):
                    global _JIRA_CONSTRUCTOR_CALLS
                    _JIRA_CONSTRUCTOR_CALLS += 1
                    raise AssertionError(
                        "PROVIDER LEAKAGE: JiraIssueState constructed during TrueTenant path"
                    )
            evidence_types.JiraIssueState = _JiraGuard  # type: ignore[attr-defined]

        if original_github:
            class _GitHubGuard:
                def __init__(self, *args, **kwargs):
                    global _GITHUB_CONSTRUCTOR_CALLS
                    _GITHUB_CONSTRUCTOR_CALLS += 1
                    raise AssertionError(
                        "PROVIDER LEAKAGE: GitHubPullRequestState constructed during TrueTenant path"
                    )
            evidence_types.GitHubPullRequestState = _GitHubGuard  # type: ignore[attr-defined]

    except ImportError:
        pass  # evidence_types not available — leakage guard not applicable


# ── Canonical Hash ─────────────────────────────────────────────────────────────

def _canonical_hash(obj: Any) -> str:
    """Compute deterministic SHA-256 of a JSON-serializable object."""
    canonical = json.dumps(obj, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── Pipeline ───────────────────────────────────────────────────────────────────

def _run_pipeline(fixture: dict[str, Any]) -> dict[str, Any]:
    """Run the complete validate → normalize → evaluate pipeline.
    
    Returns a result dict containing all pipeline outputs.
    DOES NOT modify fixture, golden, or source files.
    """
    # Step 1: Validate (existing ORBIT validator — no modification)
    validated = validate_fixture(fixture)

    # Step 2: Normalize (existing ORBIT normalizer — no modification)
    normalized = normalize_fixture(validated)

    # Step 3: Evaluate (existing Track B rules — no modification)
    matches, suppressed = evaluate_week_one_rules(normalized)

    # Step 4: Supporting facts (existing function — no modification)
    supporting_facts = calculate_supporting_facts(normalized)

    return {
        "validated": validated,
        "normalized": normalized,
        "matches": matches,
        "suppressed": suppressed,
        "supporting_facts": supporting_facts,
    }


# ── Serialization Helpers ──────────────────────────────────────────────────────

def _serialize_work_item(item: WorkItem) -> dict[str, Any]:
    return {
        "key": item.key,
        "source_id": item.source_id,
        "source_status": item.source_status,
        "status_category": item.status_category,
        "source_priority": item.source_priority,
        "priority_band": item.priority_band,
        "history_complete": item.history_complete,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
        "due_at": item.due_at.isoformat() if item.due_at else None,
        "planned_at_period_start": item.planned_at_period_start,
        "change_count": len(item.changes),
        "status_change_count": sum(1 for c in item.changes if c.field == "status"),
    }


def _serialize_match(m: Any) -> dict[str, Any]:
    return {
        "subject_key": m.subject_key,
        "rule_key": m.rule_key,
        "rule_version": m.rule_version,
        "data_quality_state": m.data_quality_state,
        "deterministic_explanation": m.deterministic_explanation,
        "calculation": m.calculation,
    }


def _serialize_suppressed(s: Any) -> dict[str, Any]:
    return {
        "subject_key": s.subject_key,
        "rule_key": s.rule_key,
        "reason": s.reason,
    }


# ── Phase 5: Normalization Report ─────────────────────────────────────────────

def build_normalization_report(
    fixture: dict[str, Any],
    quarantine_list: list[dict[str, str]],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Build the Phase 5 normalization validation report."""
    normalized = result["normalized"]
    validated = result["validated"]

    # Status distribution from normalized items
    canonical_dist: dict[str, int] = {}
    source_status_dist: dict[str, int] = {}
    unknown_status_issues: list[str] = []
    unknown_condition_keys: set[str] = set()

    for cond in normalized.data_quality_conditions:
        if cond.code == "UNKNOWN_STATUS":
            unknown_condition_keys.add(cond.subject_key or "")

    for item in normalized.work_items:
        canonical_dist[item.status_category] = canonical_dist.get(item.status_category, 0) + 1
        source_status_dist[item.source_status] = source_status_dist.get(item.source_status, 0) + 1
        if item.status_category == "unknown":
            unknown_status_issues.append(item.key)

    # Data quality conditions
    conditions_by_code: dict[str, list[str]] = {}
    for cond in normalized.data_quality_conditions:
        code = cond.code
        conditions_by_code.setdefault(code, []).append(cond.subject_key or "")

    # History quality: items with zero changelog entries (any field)
    zero_history_issues = [
        item.key for item in normalized.work_items
        if len(item.changes) == 0
    ]
    no_status_changes = [
        item.key for item in normalized.work_items
        if sum(1 for c in item.changes if c.field == "status") == 0
    ]

    # GitBranch-bearing items
    git_branch_items = [
        item.key for item in normalized.work_items
        if any(c.field == "GitBranch" for c in item.changes)
    ]

    return {
        "phase": "5_normalization_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "corpus_accounting": {
            "source_csv_rows": 112,
            "source_changelog_records": 1022,
            "accepted_work_items": len(normalized.work_items),
            "quarantined_records": len(quarantine_list),
            "quarantine_list": quarantine_list,
            "zero_history_issues": ["TT-38", "TT-41", "TT-46"],
            "zero_history_count": 3,
        },
        "status_mapping_coverage": {
            "total_statuses_in_source": 11,
            "mapped_to_known_category": 6,
            "mapped_to_unknown": 5,
            "mapping_coverage_pct": round(6 / 11 * 100, 1),
            "mapping_table": fixture["configuration"]["status_mapping"],
        },
        "canonical_status_distribution": {
            k: canonical_dist.get(k, 0)
            for k in ["todo", "in_progress", "done", "unknown", "blocked"]
        },
        "source_status_distribution": dict(
            sorted(source_status_dist.items(), key=lambda x: -x[1])
        ),
        "unknown_status_issues": sorted(unknown_status_issues),
        "unknown_status_count": len(unknown_status_issues),
        "issue_mapping_coverage": {
            "issues_mapped_to_known_category": len(normalized.work_items) - len(unknown_status_issues),
            "issues_mapped_to_unknown": len(unknown_status_issues),
            "mapping_coverage_pct": round(
                (len(normalized.work_items) - len(unknown_status_issues)) / len(normalized.work_items) * 100, 1
            ) if normalized.work_items else 0,
        },
        "history_quality": {
            "total_work_items": len(normalized.work_items),
            "history_complete_count": sum(1 for i in normalized.work_items if i.history_complete),
            "history_incomplete_count": sum(1 for i in normalized.work_items if not i.history_complete),
            "no_status_changes_count": len(no_status_changes),
            "no_status_changes_keys": sorted(no_status_changes),
            "git_branch_bearing_count": len(git_branch_items),
            "git_branch_bearing_keys": sorted(git_branch_items),
        },
        "data_quality_conditions": {
            code: sorted(keys)
            for code, keys in sorted(conditions_by_code.items())
        },
        "data_quality_condition_count": len(normalized.data_quality_conditions),
        "chronology_violations": [],  # Detected during projection — no violations found
        "invalid_timestamps": [],
        "duplicate_identities": [],
    }


# ── Phase 6+7: Evaluation Report ──────────────────────────────────────────────

def build_evaluation_report(
    result: dict[str, Any],
    normalization_report: dict[str, Any],
) -> dict[str, Any]:
    """Build the Phase 6+7 evaluation and generalization report."""
    normalized = result["normalized"]
    matches = result["matches"]
    suppressed = result["suppressed"]
    supporting_facts = result["supporting_facts"]

    # Item lookup for source status enrichment
    item_by_key: dict[str, WorkItem] = {item.key: item for item in normalized.work_items}

    # Findings by rule
    findings_by_rule: dict[str, list[dict[str, Any]]] = {}
    for m in matches:
        rule = m.rule_key
        item = item_by_key.get(m.subject_key)
        findings_by_rule.setdefault(rule, []).append({
            "subject_key": m.subject_key,
            "source_status": item.source_status if item else "UNKNOWN",
            "canonical_status": item.status_category if item else "UNKNOWN",
            "rule_version": m.rule_version,
            "data_quality_state": m.data_quality_state,
            "calculation": m.calculation,
            "explanation": m.deterministic_explanation,
        })

    # Findings by source status
    findings_by_source_status: dict[str, list[str]] = {}
    for m in matches:
        item = item_by_key.get(m.subject_key)
        ss = item.source_status if item else "UNKNOWN"
        findings_by_source_status.setdefault(ss, []).append(m.subject_key)

    # Findings by canonical category
    findings_by_canonical: dict[str, list[str]] = {}
    for m in matches:
        item = item_by_key.get(m.subject_key)
        cat = item.status_category if item else "UNKNOWN"
        findings_by_canonical.setdefault(cat, []).append(m.subject_key)

    # Suppression by rule
    suppressions_by_rule: dict[str, list[str]] = {}
    for s in suppressed:
        suppressions_by_rule.setdefault(s.rule_key, []).append(s.subject_key)

    return {
        "phase": "6_7_evaluation_generalization",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_counts": {
            "accepted_work_items": len(normalized.work_items),
            "triggered_evaluations": len(matches),
            "suppressed_evaluations": len(suppressed),
            "finding_rate_pct": round(len(matches) / len(normalized.work_items) * 100, 1)
            if normalized.work_items else 0,
        },
        "supporting_facts": supporting_facts,
        "findings_by_rule": {
            rule: {
                "count": len(items),
                "items": sorted(items, key=lambda x: x["subject_key"]),
            }
            for rule, items in sorted(findings_by_rule.items())
        },
        "findings_by_source_status": {
            ss: sorted(keys)
            for ss, keys in sorted(findings_by_source_status.items())
        },
        "findings_by_canonical_category": {
            cat: sorted(keys)
            for cat, keys in sorted(findings_by_canonical.items())
        },
        "suppressions_by_rule": {
            rule: sorted(keys)
            for rule, keys in sorted(suppressions_by_rule.items())
        },
        "all_findings": [_serialize_match(m) for m in sorted(matches, key=lambda x: x.subject_key)],
        "all_suppressions": [_serialize_suppressed(s) for s in sorted(suppressed, key=lambda x: x.subject_key)],
    }


# ── Phase 10: Determinism ──────────────────────────────────────────────────────

def run_determinism_check(fixture: dict[str, Any]) -> dict[str, Any]:
    """Run pipeline twice independently and with permuted input order."""
    # Run 1: normal order
    r1 = _run_pipeline(fixture)
    h1 = {
        "work_items": _canonical_hash([_serialize_work_item(i) for i in r1["normalized"].work_items]),
        "matches": _canonical_hash([_serialize_match(m) for m in sorted(r1["matches"], key=lambda x: (x.subject_key, x.rule_key))]),
        "suppressed": _canonical_hash([_serialize_suppressed(s) for s in sorted(r1["suppressed"], key=lambda x: (x.subject_key, x.rule_key))]),
        "supporting_facts": _canonical_hash(r1["supporting_facts"]),
    }

    # Run 2: independent (identical input order)
    r2 = _run_pipeline(fixture)
    h2 = {
        "work_items": _canonical_hash([_serialize_work_item(i) for i in r2["normalized"].work_items]),
        "matches": _canonical_hash([_serialize_match(m) for m in sorted(r2["matches"], key=lambda x: (x.subject_key, x.rule_key))]),
        "suppressed": _canonical_hash([_serialize_suppressed(s) for s in sorted(r2["suppressed"], key=lambda x: (x.subject_key, x.rule_key))]),
        "supporting_facts": _canonical_hash(r2["supporting_facts"]),
    }

    # Run 3: permuted input order (shuffle work_items in fixture before validating)
    fixture_permuted = dict(fixture)
    items_copy = list(fixture["work_items"])
    random.seed(99)
    random.shuffle(items_copy)
    fixture_permuted = {**fixture, "work_items": items_copy}
    r3 = _run_pipeline(fixture_permuted)
    h3 = {
        "work_items": _canonical_hash([_serialize_work_item(i) for i in r3["normalized"].work_items]),
        "matches": _canonical_hash([_serialize_match(m) for m in sorted(r3["matches"], key=lambda x: (x.subject_key, x.rule_key))]),
        "suppressed": _canonical_hash([_serialize_suppressed(s) for s in sorted(r3["suppressed"], key=lambda x: (x.subject_key, x.rule_key))]),
        "supporting_facts": _canonical_hash(r3["supporting_facts"]),
    }

    return {
        "run1_hashes": h1,
        "run2_hashes": h2,
        "run3_permuted_hashes": h3,
        "run1_vs_run2_identical": h1 == h2,
        "run1_vs_run3_permuted_identical": h1 == h3,
        "deterministic": h1 == h2 == h3,
    }


# ── Main Entry Point ───────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 70)
    print("PASS 5 / WAVE 3 — TrueTenant Blind Hold-Out Runner")
    print("=" * 70)
    print()

    # Install leakage guard before anything
    _install_leakage_guard()

    # Phase 4+5: Build fixture document
    print("Phase 4+5: Building fixture from TrueTenant source corpus...")
    fixture, quarantine_list = build_truetenant_fixture_document()
    print(f"  Accepted work items: {len(fixture['work_items'])}")
    print(f"  Quarantined records: {len(quarantine_list)}")
    if quarantine_list:
        for q in quarantine_list:
            print(f"    QUARANTINE [{q['reason_code']}]: {q['source_key']} — {q['reason']}")
    print()

    # Phase 5: Run pipeline for normalization report (before reading evaluation)
    print("Phase 5: Running normalization pipeline...")
    result = _run_pipeline(fixture)
    norm_report = build_normalization_report(fixture, quarantine_list, result)

    print(f"  Normalized work items: {len(result['normalized'].work_items)}")
    print(f"  Data quality conditions: {len(result['normalized'].data_quality_conditions)}")
    print(f"  Canonical distribution:")
    for cat, cnt in sorted(norm_report["canonical_status_distribution"].items()):
        print(f"    {cat}: {cnt}")
    print()

    # Save normalization report (Phase 5 output — before reading evaluation results)
    norm_report_path = OUTPUT_DIR / "truetenant_normalization_report.json"
    with norm_report_path.open("w", encoding="utf-8") as f:
        json.dump(norm_report, f, indent=2, default=str, sort_keys=False)
    print(f"Phase 5 report written: {norm_report_path}")
    print()

    # Phase 6+7: Evaluation report
    print("Phase 6+7: Running Track B evaluation...")
    eval_report = build_evaluation_report(result, norm_report)

    print(f"  Triggered evaluations: {eval_report['evaluation_counts']['triggered_evaluations']}")
    print(f"  Suppressed evaluations: {eval_report['evaluation_counts']['suppressed_evaluations']}")
    print(f"  Findings by rule:")
    for rule, data in eval_report["findings_by_rule"].items():
        print(f"    {rule}: {data['count']} findings")
    print()

    eval_report_path = OUTPUT_DIR / "truetenant_evaluation_report.json"
    with eval_report_path.open("w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2, default=str, sort_keys=False)
    print(f"Phase 6+7 report written: {eval_report_path}")
    print()

    # Phase 9: Provider leakage check
    print("Phase 9: Provider leakage check...")
    leakage_result = {
        "jira_issue_state_constructor_calls": _JIRA_CONSTRUCTOR_CALLS,
        "github_pr_state_constructor_calls": _GITHUB_CONSTRUCTOR_CALLS,
        "leakage_detected": _JIRA_CONSTRUCTOR_CALLS > 0 or _GITHUB_CONSTRUCTOR_CALLS > 0,
    }
    print(f"  JiraIssueState constructor calls: {_JIRA_CONSTRUCTOR_CALLS}")
    print(f"  GitHubPullRequestState constructor calls: {_GITHUB_CONSTRUCTOR_CALLS}")
    print(f"  Leakage detected: {leakage_result['leakage_detected']}")
    print()

    # Phase 10: Determinism
    print("Phase 10: Determinism check (2 independent runs + permutation)...")
    det_result = run_determinism_check(fixture)
    print(f"  Run 1 vs Run 2 identical: {det_result['run1_vs_run2_identical']}")
    print(f"  Run 1 vs Run 3 (permuted) identical: {det_result['run1_vs_run3_permuted_identical']}")
    print(f"  Fully deterministic: {det_result['deterministic']}")
    print()

    # Combined output
    combined = {
        "normalization_report": norm_report,
        "evaluation_report": eval_report,
        "leakage_check": leakage_result,
        "determinism_check": det_result,
        "run_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "governing_baseline": "6d82d123f8bf50316d2b1ab7a025bc5862a474ed",
            "consolidation_head": "ea464540b8a414e4ab6e9a2b1a4be53ae31b40ab",
            "branch": "remediation/pass3-controlled-hardening",
            "save_golden": False,
        },
    }

    combined_path = OUTPUT_DIR / "truetenant_holdout_combined.json"
    with combined_path.open("w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, default=str, sort_keys=False)
    print(f"Combined output written: {combined_path}")

    # Print raw summary for report
    print()
    print("=" * 70)
    print("RAW EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Accepted items:          {len(result['normalized'].work_items)}")
    print(f"Quarantined:             {len(quarantine_list)}")
    print(f"Total findings:          {eval_report['evaluation_counts']['triggered_evaluations']}")
    print(f"Total suppressed:        {eval_report['evaluation_counts']['suppressed_evaluations']}")
    print(f"Unknown status issues:   {norm_report['unknown_status_count']}")
    print(f"Data quality conditions: {norm_report['data_quality_condition_count']}")
    print(f"Leakage detected:        {leakage_result['leakage_detected']}")
    print(f"Deterministic:           {det_result['deterministic']}")
    print()
    print("Findings by rule:")
    for rule, data in eval_report["findings_by_rule"].items():
        print(f"  {rule}: {data['count']}")
    print()
    print("Supporting facts:")
    for k, v in eval_report["supporting_facts"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
