"""Comprehensive Test Suite for the Mahout Real-Data Proving Boundary.

Covers all 12 mandatory qualification categories:
1. Ingestion contract tests
2. Validation tests
3. Normalization tests
4. Temporal reconstruction tests
5. Evidence assembly tests
6. Metric engine tests
7. Finding engine tests
8. End-to-end Mahout pipeline test
9. Deterministic repeatability test
10. Cross-stage provenance chain test
11. Messy data / quarantine proof tests
12. Regression / golden output test

Safety Invariants:
- Zero Jira mutations (0 created, 0 updated, 0 transitioned, 0 deleted, 0 configured).
- Zero calls to Jira API; no Jira credentials required.
- Zero modifications to frozen CSE engine baseline 6d82d12.
- 100% deterministic repeatability.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

# Ensure orbit repo root and src are on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from qualification.config import FROZEN_ENGINE_COMMIT, JIRA_CONTRACT_VERSION
from qualification.mahout.evidence_bridge import (
    DEFAULT_SOURCE_INSTANCE,
    build_mahout_evidence_bridge,
    extract_mahout_structural_relationships,
)
from qualification.mahout.ingestion import (
    DEFAULT_PRIORITY_MAPPING,
    DEFAULT_RAW_CAPTURE_PATH,
    DEFAULT_STATUS_MAPPING,
    DESTINATION_410_ALLOWLIST_PATH,
    DESTINATION_412_ALLOWLIST_PATH,
    PRIMARY_ALLOWLIST_PATH,
    TOTAL_MAHOUT_SOURCE_CONSIDERED,
    build_mahout_fixture_document,
    load_allowlist,
    load_raw_mahout_issues,
    project_single_mahout_record,
)
from qualification.mahout.provenance import (
    trace_suppressed_finding,
    trace_triggered_finding,
)
from qualification.mahout.runner import (
    DEFAULT_GOLDEN_PATH,
    execute_pipeline_pass,
    run_mahout_qualification,
)
from qualification.policy import canonical_record_hash, compute_sha256_file
from shadow_orbit.evaluation import (
    calculate_supporting_facts,
    evaluate_week_one_rules,
)
from shadow_orbit.evidence_assembly import validate_evidence_bundle
from shadow_orbit.evidence_types import EvidenceObservation
from shadow_orbit.messy_acceptance import build_messy_week_one_artifact
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.temporal import (
    completed_during_period,
    elapsed_complete_days,
    introduced_during_period,
    is_overdue,
    is_within_half_open_period,
    status_at_period_end,
)
from shadow_orbit.types import ReviewPeriod, SuppressedEvaluation
from shadow_orbit.validation import validate_fixture


# ── Shared Test Fixtures ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def mahout_raw_data() -> tuple[list[dict[str, Any]], Any]:
    """Load raw Mahout documents and accounting once for the test module."""
    return load_raw_mahout_issues()


@pytest.fixture(scope="module")
def primary_and_dependency_keys() -> tuple[set[str], set[str]]:
    """Return sets of primary seed keys and structural dependency keys."""
    p_keys = set(load_allowlist(PRIMARY_ALLOWLIST_PATH))
    all_412 = set(load_allowlist(DESTINATION_412_ALLOWLIST_PATH))
    d_keys = all_412 - p_keys
    return p_keys, d_keys


# ── Category 1: Ingestion Contract Tests ──────────────────────────────

def test_ingestion_corpus_accounting_invariants(mahout_raw_data):
    """Prove strict 4-category conservation across source selection boundary."""
    docs, acct = mahout_raw_data
    assert acct.source_considered == TOTAL_MAHOUT_SOURCE_CONSIDERED  # 2,121
    assert acct.primary_selected == 400
    assert acct.structural_dependencies_included == 12
    assert acct.total_selected_for_qualification == 412
    assert acct.not_selected_by_policy == 1709
    assert acct.selection_failures == 0
    assert acct.corpus_flavor == "412_full_closure"
    assert acct.to_dict()["is_balanced"] is True


def test_ingestion_source_identity_and_fidelity(mahout_raw_data):
    """Prove authentic source keys, immutable IDs, and timestamps are preserved."""
    docs, _ = mahout_raw_data
    assert len(docs) == 412

    for doc in docs:
        key = doc.get("key")
        source_id = str(doc.get("id"))
        assert key is not None and key.startswith("MAHOUT-")
        assert source_id.isdigit(), f"Expected numeric source_id for {key}, got {source_id}"

        # Project single record
        item = project_single_mahout_record(doc)
        assert item["key"] == key
        assert item["source_id"] == source_id
        assert item["planned_at_period_start"] is None  # Honest null

        # Timestamps must be valid ISO aware strings
        assert item["created_at"].endswith("+00:00") or item["created_at"].endswith("Z")
        assert item["updated_at"].endswith("+00:00") or item["updated_at"].endswith("Z")

        # Missing optional fields must remain None without synthetic coercion
        if not doc.get("fields", {}).get("duedate"):
            assert "due_at" not in item or item["due_at"] is None
        if not doc.get("fields", {}).get("resolutiondate"):
            assert "resolved_at" not in item or item["resolved_at"] is None


# ── Category 2: Validation Tests ──────────────────────────────────────

def test_validation_clean_corpus_accepts_all_selected(mahout_raw_data):
    """Prove all 412 issues pass schema validation without quarantine."""
    docs, _ = mahout_raw_data
    fixture_doc = build_mahout_fixture_document(docs)
    validated = validate_fixture(fixture_doc)

    assert len(validated.accepted_raw_items) == 412
    assert len(validated.quarantined_records) == 0
    assert len(validated.validation_conditions) == 0


def test_validation_quarantines_malformed_records(mahout_raw_data):
    """Prove non-destructive quarantine on malformed source records."""
    docs, _ = mahout_raw_data
    fixture_doc = build_mahout_fixture_document(docs[:5])

    # 1. Non-dict record
    fixture_doc["work_items"].append("invalid_string_record")  # type: ignore

    # 2. Missing required field
    fixture_doc["work_items"].append({
        "source_id": "999901",
        "key": "MAHOUT-99901",
        # Missing title/summary
        "item_type": "Bug",
        "priority": "Major",
        "status": "Open",
        "created_at": "2021-01-01T00:00:00Z",
        "updated_at": "2021-01-01T00:00:00Z",
        "planned_at_period_start": None,
        "history_complete": True,
        "changes": [],
    })

    # 3. Project key mismatch
    fixture_doc["work_items"].append({
        "source_id": "999902",
        "key": "OTHER-99902",
        "title": "Foreign project issue",
        "item_type": "Bug",
        "priority": "Major",
        "status": "Open",
        "created_at": "2021-01-01T00:00:00Z",
        "updated_at": "2021-01-01T00:00:00Z",
        "planned_at_period_start": None,
        "history_complete": True,
        "changes": [],
    })

    # 4. Duplicate key
    dup_item = copy.deepcopy(fixture_doc["work_items"][0])
    fixture_doc["work_items"].append(dup_item)

    validated = validate_fixture(fixture_doc)

    # The 5 original items minus the one duplicated = 4 accepted
    # Plus 1 (dup copy 1) + 1 (dup copy 2) + 1 (non-dict) + 1 (missing field) + 1 (key mismatch) = 5 quarantined
    quarantine_reasons = {q.reason_code for q in validated.quarantined_records}
    assert "INVALID_RECORD" in quarantine_reasons
    assert "MISSING_REQUIRED_FIELD" in quarantine_reasons
    assert "PROJECT_KEY_MISMATCH" in quarantine_reasons
    assert "DUPLICATE_EXTERNAL_KEY" in quarantine_reasons
    assert len(validated.quarantined_records) >= 5


def test_validation_preserves_invalid_optional_timestamp(mahout_raw_data):
    """Prove invalid optional timestamps generate DataQualityCondition without quarantine."""
    docs, _ = mahout_raw_data
    fixture_doc = build_mahout_fixture_document(docs[:2])
    # Corrupt due_at to unparseable string
    fixture_doc["work_items"][0]["due_at"] = "invalid-not-a-date"

    validated = validate_fixture(fixture_doc)
    assert len(validated.accepted_raw_items) == 2
    assert len(validated.quarantined_records) == 0
    # Must emit INVALID_OPTIONAL_TIMESTAMP condition and reset due_at to None
    conditions = [c for c in validated.validation_conditions if c.code == "INVALID_OPTIONAL_TIMESTAMP"]
    assert len(conditions) == 1
    assert conditions[0].subject_key == fixture_doc["work_items"][0]["key"]
    assert validated.accepted_raw_items[0]["due_at"] is None


# ── Category 3: Normalization Tests ───────────────────────────────────

def test_normalization_status_and_priority_mapping(mahout_raw_data):
    """Prove canonical category mapping for statuses and priorities."""
    docs, _ = mahout_raw_data
    fixture_doc = build_mahout_fixture_document(docs)
    validated = validate_fixture(fixture_doc)
    normalized = normalize_fixture(validated)

    for item in normalized.work_items:
        # Status mappings
        if item.source_status in ("Open", "Reopened"):
            assert item.status_category == "todo"
        elif item.source_status in ("In Progress", "Patch Available"):
            assert item.status_category == "in_progress"
        elif item.source_status in ("Resolved", "Closed"):
            assert item.status_category == "done"

        # Priority mappings
        if item.source_priority in ("Blocker", "Critical"):
            assert item.priority_band == "high"
        elif item.source_priority in ("Major", "Minor", "Trivial"):
            assert item.priority_band == "ordinary"


def test_normalization_unmapped_status_and_priority_conditions(mahout_raw_data):
    """Prove unmapped status and priority emit explicit data quality conditions."""
    docs, _ = mahout_raw_data
    # Use configuration with missing status and priority
    custom_status = {"Open": "todo", "Closed": "done"}  # 'In Progress' omitted
    custom_priority = {"Blocker": "high"}  # 'Major' omitted

    fixture_doc = build_mahout_fixture_document(
        docs,
        status_mapping=custom_status,
        priority_mapping=custom_priority,
    )
    validated = validate_fixture(fixture_doc)
    normalized = normalize_fixture(validated)

    codes = {c.code for c in normalized.data_quality_conditions}
    assert "UNKNOWN_STATUS" in codes
    assert "UNKNOWN_PRIORITY" in codes

    unmapped_status_items = [
        item for item in normalized.work_items
        if item.source_status not in custom_status
    ]
    for item in unmapped_status_items:
        assert item.status_category == "unknown"


# ── Category 4: Temporal Reconstruction Tests ─────────────────────────

def test_temporal_period_boundaries_and_reconstruction(mahout_raw_data):
    """Prove temporal reasoning: half-open intervals, completion, and overdue checks."""
    period = ReviewPeriod(
        label="2015-W15",
        starts_at=datetime.fromisoformat("2015-04-06T00:00:00+00:00"),
        ends_at_exclusive=datetime.fromisoformat("2015-04-13T00:00:00+00:00"),
        review_cutoff_at=datetime.fromisoformat("2015-04-13T09:00:00+00:00"),
        source_cutoff_at=datetime.fromisoformat("2015-04-13T09:00:00+00:00"),
    )

    t_in = datetime.fromisoformat("2015-04-08T12:00:00+00:00")
    t_start = datetime.fromisoformat("2015-04-06T00:00:00+00:00")
    t_end = datetime.fromisoformat("2015-04-13T00:00:00+00:00")

    assert is_within_half_open_period(t_in, period) is True
    assert is_within_half_open_period(t_start, period) is True
    assert is_within_half_open_period(t_end, period) is False  # Half-open exclusive

    # Elapsed complete days
    days = elapsed_complete_days(t_start, t_end)
    assert days == 7

    # Overdue check
    due_past = datetime.fromisoformat("2015-04-10T00:00:00+00:00")
    due_future = datetime.fromisoformat("2015-04-20T00:00:00+00:00")
    assert is_overdue(due_past, period.review_cutoff_at) is True
    assert is_overdue(due_future, period.review_cutoff_at) is False


def test_temporal_status_at_period_end_reconstruction(mahout_raw_data):
    """Prove status rollback for changes occurring after period end."""
    docs, _ = mahout_raw_data
    docs_by_key = {d["key"]: d for d in docs}

    # MAHOUT-1648 transitioned Resolved -> Closed on 2015-04-13T09:57:38
    doc = docs_by_key["MAHOUT-1648"]
    item_dict = project_single_mahout_record(doc)

    period = ReviewPeriod(
        label="2015-W15",
        starts_at=datetime.fromisoformat("2015-04-06T00:00:00+00:00"),
        ends_at_exclusive=datetime.fromisoformat("2015-04-13T00:00:00+00:00"),
        review_cutoff_at=datetime.fromisoformat("2015-04-13T09:00:00+00:00"),
        source_cutoff_at=datetime.fromisoformat("2015-04-13T09:00:00+00:00"),
    )

    fixture_doc = build_mahout_fixture_document([doc])
    validated = validate_fixture(fixture_doc)
    normalized = normalize_fixture(validated)
    wi = normalized.work_items[0]

    # At period end (2015-04-13 00:00), the transition on 09:57 had not yet occurred!
    # It was in Resolved (done), not yet Closed.
    reconstructed_status = status_at_period_end(wi, period, DEFAULT_STATUS_MAPPING)
    assert reconstructed_status == "done"


# ── Category 5: Evidence Assembly Tests ───────────────────────────────

def test_evidence_adapter_and_bundle_validation(mahout_raw_data, primary_and_dependency_keys):
    """Prove canonical EvidenceBundle assembly and validation."""
    docs, _ = mahout_raw_data
    p_keys, d_keys = primary_and_dependency_keys

    fixture_doc = build_mahout_fixture_document(docs)
    validated = validate_fixture(fixture_doc)
    normalized = normalize_fixture(validated)

    bridge = build_mahout_evidence_bridge(
        normalized_fixture=normalized,
        raw_docs=docs,
        primary_seed_keys=p_keys,
        dependency_keys=d_keys,
    )

    assert len(bridge.bundle.observations) == 412
    # Canonical validation must pass without exception
    validate_evidence_bundle(bridge.bundle)

    # Verify each observation structure
    sample_obs = bridge.observations_by_key["MAHOUT-1372"]
    assert sample_obs.entity_ref.source_instance == DEFAULT_SOURCE_INSTANCE
    assert sample_obs.entity_ref.entity_kind == "jira_issue"
    assert sample_obs.entity_ref.entity_id == "MAHOUT-1372"
    assert sample_obs.observed_state.key == "MAHOUT-1372"


def test_structural_relationship_census_and_closure(mahout_raw_data, primary_and_dependency_keys):
    """Prove full relationship census: Subtasks (100% closure in 412), Epics, and Issue Links."""
    docs, _ = mahout_raw_data
    p_keys, d_keys = primary_and_dependency_keys

    relationships = extract_mahout_structural_relationships(
        raw_docs=docs,
        primary_seed_keys=p_keys,
        dependency_keys=d_keys,
    )

    subtask_links = [r for r in relationships if r.relationship_type == "subtask_parent"]
    epic_links = [r for r in relationships if r.relationship_type == "epic_link"]
    issue_links = [r for r in relationships if r.relationship_type == "issuelink"]

    # 1. Subtasks: exactly 31 subtasks
    assert len(subtask_links) == 31
    # 100% resolved under 412 full-closure corpus
    assert all(r.is_resolved for r in subtask_links)

    # 2. Epic Links: all targets in primary seed
    assert len(epic_links) >= 48
    epic_targets = {r.target_key for r in epic_links}
    assert epic_targets.issubset(p_keys)

    # 3. Issue Links: non-blocking associations
    assert len(issue_links) >= 106
    external_links = [r for r in issue_links if "external" in r.classification]
    assert len(external_links) > 0  # Proves unresolved external links are recognized


# ── Category 6: Metric Engine Tests ───────────────────────────────────

def test_metric_supporting_facts_evaluation(mahout_raw_data):
    """Prove deterministic supporting facts calculation and honest nulls."""
    docs, _ = mahout_raw_data
    fixture_doc = build_mahout_fixture_document(docs)
    validated = validate_fixture(fixture_doc)
    normalized = normalize_fixture(validated)

    facts = calculate_supporting_facts(normalized)

    assert facts["accepted_work_item_count"] == 412
    assert facts["planned_at_period_start_count"] == 0
    assert facts["planned_at_period_start_keys"] == []
    # Missing due dates: exactly 370 of 412
    assert facts["missing_due_date_count"] == 370
    assert len(facts["missing_due_date_keys"]) == 370
    # Honest null planning basis
    assert facts["manager_facing_completion_percentage"] is None
    assert "planning basis has not been validated" in facts["manager_facing_completion_percentage_reason"]


# ── Category 7: Finding Engine Tests ──────────────────────────────────

def test_finding_engine_deterministic_evaluation(mahout_raw_data):
    """Prove pure finding evaluation generates explainable rule matches without side effects."""
    docs, _ = mahout_raw_data
    fixture_doc = build_mahout_fixture_document(docs)
    validated = validate_fixture(fixture_doc)
    normalized = normalize_fixture(validated)

    matches, suppressed = evaluate_week_one_rules(normalized)

    assert len(matches) > 0
    for match in matches:
        assert match.rule_key in ("BLOCKED_HIGH_PRIORITY", "OVERDUE_HIGH_PRIORITY", "STALLED_WORK")
        assert match.rule_version == "1"
        assert len(match.deterministic_explanation) > 0
        assert len(match.evidence_references) > 0
        assert match.calculation != ""


# ── Category 8: End-to-End Mahout Pipeline Test ───────────────────────

def test_end_to_end_mahout_pipeline_execution():
    """Prove full end-to-end pipeline carries real data from ingestion to review artifact."""
    result = run_mahout_qualification(save_golden=False)

    assert result.contract_version == JIRA_CONTRACT_VERSION
    assert result.engine_commit == FROZEN_ENGINE_COMMIT
    assert result.ingestion_accounting.is_balanced is True
    assert len(result.validated_fixture.accepted_raw_items) == 412
    assert len(result.normalized_fixture.work_items) == 412
    assert len(result.evidence_bridge.bundle.observations) == 412
    assert len(result.rule_matches) > 0

    # Review artifact has required 11-field shape
    artifact = result.review_artifact
    assert artifact["expected_artifact_version"] == "shadow-review-expected-v1"
    assert "import_result" in artifact
    assert "supporting_facts" in artifact
    assert "what_needs_attention" in artifact
    assert "what_orbit_could_not_determine" in artifact


# ── Category 9: Deterministic Repeatability Test ──────────────────────

def test_pipeline_deterministic_repeatability():
    """Prove identical inputs produce byte-for-byte identical review artifacts and facts."""
    res1 = run_mahout_qualification(save_golden=False)
    res2 = run_mahout_qualification(save_golden=False)

    assert res1.golden_digest == res2.golden_digest
    assert canonical_record_hash(res1.review_artifact) == canonical_record_hash(res2.review_artifact)
    assert canonical_record_hash(res1.supporting_facts) == canonical_record_hash(res2.supporting_facts)
    assert len(res1.rule_matches) == len(res2.rule_matches)


# ── Category 10: Cross-Stage Provenance Chain Test ────────────────────

def test_cross_stage_provenance_tracing(mahout_raw_data, primary_and_dependency_keys):
    """Prove traceable chain from raw observation to review artifact for triggered and suppressed findings."""
    docs, _ = mahout_raw_data
    p_keys, d_keys = primary_and_dependency_keys

    fixture_doc = build_mahout_fixture_document(docs)
    validated = validate_fixture(fixture_doc)
    normalized = normalize_fixture(validated)
    bridge = build_mahout_evidence_bridge(normalized, docs, p_keys, d_keys)

    matches, _ = evaluate_week_one_rules(normalized)
    assert len(matches) > 0
    rep_match = matches[0]
    rep_wi = next(w for w in normalized.work_items if w.key == rep_match.subject_key)
    rep_raw = next(d for d in docs if d["key"] == rep_match.subject_key)
    rep_obs = bridge.observations_by_key.get(rep_match.subject_key)

    # 1. Triggered finding trace
    chain = trace_triggered_finding(
        match=rep_match,
        work_item=rep_wi,
        raw_doc=rep_raw,
        validated=validated,
        normalized=normalized,
        observation=rep_obs,
    )
    assert chain.verdict == "TRIGGERED"
    assert len(chain.steps) == 6
    stage_names = [s.stage_name for s in chain.steps]
    assert stage_names == [
        "raw_mahout_observation",
        "validated_source_record",
        "normalized_evidence",
        "temporal_fact",
        "finding_evaluation",
        "review_artifact",
    ]

    # 2. Suppressed finding trace
    suppressed_eval = SuppressedEvaluation(
        subject_key=rep_match.subject_key,
        rule_key="OVERDUE_HIGH_PRIORITY",
        reason="The due date has passed, but status is unmapped.",
    )
    sup_chain = trace_suppressed_finding(
        suppressed=suppressed_eval,
        work_item=rep_wi,
        raw_doc=rep_raw,
        validated=validated,
        normalized=normalized,
        observation=rep_obs,
    )
    assert sup_chain.verdict == "SUPPRESSED"
    assert len(sup_chain.steps) == 4


# ── Category 11: Messy Data & Quarantine Proof Tests ──────────────────

def test_messy_data_quarantine_and_condition_propagation(mahout_raw_data):
    """Prove pipeline handles missing, unmapped, and malformed data with zero silent coercion."""
    docs, _ = mahout_raw_data
    docs_by_key = {d["key"]: d for d in docs}

    # Select an issue with a due date
    due_key = "MAHOUT-1678"
    assert due_key in docs_by_key

    # Configure status mapping omitting 'Closed'
    unmapped_status_map = {
        "Open": "todo",
        "In Progress": "in_progress",
        "Resolved": "done",
        # 'Closed' is omitted -> unknown status
    }

    fixture_doc = build_mahout_fixture_document(
        [docs_by_key[due_key]],
        status_mapping=unmapped_status_map,
        review_cutoff_at="2021-06-05T00:00:00Z",
    )

    validated = validate_fixture(fixture_doc)
    normalized = normalize_fixture(validated)

    # 1. Must emit UNKNOWN_STATUS condition
    assert any(c.code == "UNKNOWN_STATUS" for c in normalized.data_quality_conditions)

    # 2. OVERDUE_HIGH_PRIORITY must be SUPPRESSED rather than falsely triggered or silently dropped
    _, suppressed = evaluate_week_one_rules(normalized)
    assert any(
        s.rule_key == "OVERDUE_HIGH_PRIORITY" and s.subject_key == due_key
        for s in suppressed
    )

    # 3. Must assemble into review artifact under what_orbit_could_not_determine
    artifact = build_messy_week_one_artifact(validated, normalized)
    assert "what_orbit_could_not_determine" in artifact


# ── Category 12: Regression / Golden Output Test ──────────────────────

def test_golden_regression_artifact_integrity():
    """Verify golden regression artifact is valid, up to date, and respects invariants."""
    assert DEFAULT_GOLDEN_PATH.exists(), f"Golden artifact missing at {DEFAULT_GOLDEN_PATH}"

    with DEFAULT_GOLDEN_PATH.open("r", encoding="utf-8") as handle:
        golden = json.load(handle)

    assert golden["engine_commit"] == FROZEN_ENGINE_COMMIT
    assert golden["jira_contract_version"] == JIRA_CONTRACT_VERSION
    assert golden["ingestion_accounting"]["total_selected_for_qualification"] == 412
    assert golden["validation_summary"]["accepted_count"] == 412
    assert golden["validation_summary"]["quarantined_count"] == 0
    assert golden["evidence_summary"]["observation_count"] == 412
    assert golden["invariants"]["src_shadow_orbit_untouched"] is True
    assert golden["invariants"]["jira_mutations_executed"] == 0
    assert golden["invariants"]["jira_configurations_mutated"] == 0
