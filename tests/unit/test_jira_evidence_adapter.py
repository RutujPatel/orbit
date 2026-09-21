"""Tests for the additive Jira evidence adapter (CSE-1.4).

Covers all 14 test classes from the approved plan:
  1. SourceInstance enforcement
  2. EntityRef construction
  3. JiraIssueState construction
  4. ObservationContext propagation
  5. Temporal validation
  6. Provenance construction
  7. Approved quality mappings
  8. Unmapped condition preservation
  9. Orphan subject_key handling
 10. Deterministic ordering
 11. WorkItems permutation invariance
 12. Immutability
 13. Adapter does not change existing evaluation
 14. SourceInstance identity
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    SourceInstance,
)
from shadow_orbit.fixture_io import load_fixture
from shadow_orbit.jira_evidence_adapter import adapt_jira_evidence
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.types import (
    DataQualityCondition,
    NormalizedFixture,
    ReviewPeriod,
    WorkItem,
)
from shadow_orbit.validation import validate_fixture


# ── Paths ────────────────────────────────────────────────────────────

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

CLEAN_WEEK_ONE = (
    REPOSITORY_ROOT / "fixtures" / "jira" / "northstar_clean_week_1.json"
)
MESSY_WEEK_ONE = (
    REPOSITORY_ROOT / "fixtures" / "jira" / "northstar_messy_week_1.json"
)


# ── Shared helpers ───────────────────────────────────────────────────

JIRA_SOURCE = SourceInstance(source_kind="jira", instance_id="test-jira")
OBSERVATION_ID = "obs-clean-w1"
FIXTURE_ID = "northstar-clean-week-1"

T0 = datetime(2026, 2, 2, 9, 0, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 2, 9, 0, 0, 0, tzinfo=timezone.utc)
T_CUTOFF = datetime(2026, 2, 9, 9, 0, 0, tzinfo=timezone.utc)


def _clean_normalized() -> NormalizedFixture:
    doc = load_fixture(CLEAN_WEEK_ONE)
    return normalize_fixture(validate_fixture(doc))


def _messy_normalized() -> NormalizedFixture:
    doc = load_fixture(MESSY_WEEK_ONE)
    return normalize_fixture(validate_fixture(doc))


def _adapt_clean(**kwargs):
    """Run the adapter on the clean fixture with default arguments."""
    defaults = dict(
        normalized=_clean_normalized(),
        source_instance=JIRA_SOURCE,
        observation_id=OBSERVATION_ID,
        fixture_id=FIXTURE_ID,
    )
    defaults.update(kwargs)
    return adapt_jira_evidence(**defaults)


def _adapt_messy(**kwargs):
    """Run the adapter on the messy fixture with default arguments."""
    defaults = dict(
        normalized=_messy_normalized(),
        source_instance=JIRA_SOURCE,
        observation_id="obs-messy-w1",
        fixture_id="northstar-messy-week-1",
    )
    defaults.update(kwargs)
    return adapt_jira_evidence(**defaults)


# =====================================================================
# 1. TestSourceInstanceEnforcement
# =====================================================================


class TestSourceInstanceEnforcement:
    """The adapter must reject non-Jira SourceInstances."""

    def test_rejects_github_source_instance(self):
        github_source = SourceInstance(
            source_kind="github", instance_id="gh-org"
        )
        with pytest.raises(ValueError, match="source_kind='jira'"):
            adapt_jira_evidence(
                normalized=_clean_normalized(),
                source_instance=github_source,
                observation_id="obs-1",
            )

    def test_accepts_jira_source_instance(self):
        ctx, observations, _ = _adapt_clean()
        assert ctx.source_instance.source_kind == "jira"
        assert len(observations) > 0


# =====================================================================
# 2. TestEntityRefConstruction
# =====================================================================


class TestEntityRefConstruction:
    """EntityRef must use jira_issue kind and WorkItem.key as entity_id."""

    def test_entity_kind_is_jira_issue(self):
        _, observations, _ = _adapt_clean()
        for obs in observations:
            assert obs.entity_ref.entity_kind == "jira_issue"

    def test_entity_id_is_work_item_key(self):
        normalized = _clean_normalized()
        _, observations, _ = adapt_jira_evidence(
            normalized=normalized,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        expected_keys = {wi.key for wi in normalized.work_items}
        actual_keys = {obs.entity_ref.entity_id for obs in observations}
        assert actual_keys == expected_keys

    def test_source_instance_matches(self):
        _, observations, _ = _adapt_clean()
        for obs in observations:
            assert obs.entity_ref.source_instance is JIRA_SOURCE


# =====================================================================
# 3. TestJiraIssueStateConstruction
# =====================================================================


class TestJiraIssueStateConstruction:
    """All 10 mapped fields must be correctly transferred."""

    def test_all_fields_mapped(self):
        normalized = _clean_normalized()
        _, observations, _ = adapt_jira_evidence(
            normalized=normalized,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        states_by_key = {
            obs.observed_state.key: obs.observed_state
            for obs in observations
        }
        for wi in normalized.work_items:
            state = states_by_key[wi.key]
            assert isinstance(state, JiraIssueState)
            assert state.key == wi.key
            assert state.source_status == wi.source_status
            assert state.source_priority == wi.source_priority
            assert state.status_category == wi.status_category
            assert state.priority_band == wi.priority_band
            assert state.assignee == wi.assignee
            assert state.created_at == wi.created_at
            assert state.updated_at == wi.updated_at
            assert state.resolved_at == wi.resolved_at
            assert state.due_at == wi.due_at

    def test_optional_fields_none(self):
        """WorkItems with None assignee/resolved_at/due_at propagate."""
        normalized = _clean_normalized()
        _, observations, _ = adapt_jira_evidence(
            normalized=normalized,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        states_by_key = {
            obs.observed_state.key: obs.observed_state
            for obs in observations
        }
        # Find items with None optional fields
        for wi in normalized.work_items:
            state = states_by_key[wi.key]
            if wi.assignee is None:
                assert state.assignee is None
            if wi.resolved_at is None:
                assert state.resolved_at is None
            if wi.due_at is None:
                assert state.due_at is None

    def test_unknown_status_preserved_verbatim(self):
        """WorkItems with status_category='unknown' are preserved."""
        _, observations, _ = _adapt_messy()
        states_by_key = {
            obs.observed_state.key: obs.observed_state
            for obs in observations
        }
        # OPS-004 has unmapped status 'Awaiting External Validation'
        assert states_by_key["OPS-004"].status_category == "unknown"
        assert (
            states_by_key["OPS-004"].source_status
            == "Awaiting External Validation"
        )

    def test_unknown_priority_preserved_verbatim(self):
        """WorkItems with priority_band='unknown' are preserved."""
        _, observations, _ = _adapt_messy()
        states_by_key = {
            obs.observed_state.key: obs.observed_state
            for obs in observations
        }
        # OPS-005 has unmapped priority 'Urgent-ish'
        assert states_by_key["OPS-005"].priority_band == "unknown"
        assert states_by_key["OPS-005"].source_priority == "Urgent-ish"


# =====================================================================
# 4. TestObservationContextPropagation
# =====================================================================


class TestObservationContextPropagation:
    """ObservationContext must propagate all supplied arguments."""

    def test_full_temporal_propagation(self):
        ctx, _, _ = _adapt_clean(
            observed_interval_starts_at=T0,
            observed_interval_ends_at_exclusive=T1,
            source_cutoff_at=T_CUTOFF,
            coverage_note="scope_complete: true",
        )
        assert ctx.observation_id == OBSERVATION_ID
        assert ctx.source_instance is JIRA_SOURCE
        assert ctx.observed_interval_starts_at == T0
        assert ctx.observed_interval_ends_at_exclusive == T1
        assert ctx.source_cutoff_at == T_CUTOFF
        assert ctx.coverage_note == "scope_complete: true"

    def test_missing_temporals_remain_none(self):
        ctx, _, _ = _adapt_clean()
        assert ctx.observed_interval_starts_at is None
        assert ctx.observed_interval_ends_at_exclusive is None
        assert ctx.source_cutoff_at is None
        assert ctx.coverage_note is None

    def test_observation_context_shared_across_observations(self):
        ctx, observations, _ = _adapt_clean()
        for obs in observations:
            assert obs.observation_context is ctx


# =====================================================================
# 5. TestTemporalValidation
# =====================================================================


class TestTemporalValidation:
    """Temporal arguments must be timezone-aware with valid ordering."""

    def test_naive_starts_at_raises(self):
        naive = datetime(2026, 2, 2, 9, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            _adapt_clean(
                observed_interval_starts_at=naive,
                observed_interval_ends_at_exclusive=T1,
            )

    def test_naive_ends_at_raises(self):
        naive = datetime(2026, 2, 9, 0, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            _adapt_clean(
                observed_interval_starts_at=T0,
                observed_interval_ends_at_exclusive=naive,
            )

    def test_naive_cutoff_raises(self):
        naive = datetime(2026, 2, 9, 9, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            _adapt_clean(source_cutoff_at=naive)

    def test_reversed_interval_raises(self):
        with pytest.raises(ValueError, match="strictly before"):
            _adapt_clean(
                observed_interval_starts_at=T1,
                observed_interval_ends_at_exclusive=T0,
            )

    def test_equal_interval_raises(self):
        with pytest.raises(ValueError, match="strictly before"):
            _adapt_clean(
                observed_interval_starts_at=T0,
                observed_interval_ends_at_exclusive=T0,
            )

    def test_valid_interval_accepted(self):
        ctx, _, _ = _adapt_clean(
            observed_interval_starts_at=T0,
            observed_interval_ends_at_exclusive=T1,
        )
        assert ctx.observed_interval_starts_at == T0
        assert ctx.observed_interval_ends_at_exclusive == T1

    def test_none_temporals_accepted(self):
        # No error when all temporals are None
        ctx, _, _ = _adapt_clean()
        assert ctx.observed_interval_starts_at is None

    def test_partial_interval_accepted(self):
        """Only starts_at supplied, no ends_at — no interval check."""
        ctx, _, _ = _adapt_clean(
            observed_interval_starts_at=T0,
        )
        assert ctx.observed_interval_starts_at == T0
        assert ctx.observed_interval_ends_at_exclusive is None


# =====================================================================
# 6. TestProvenanceConstruction
# =====================================================================


class TestProvenanceConstruction:
    """Provenance must use pre-quarantine raw indexes."""

    def test_record_locator_uses_raw_index(self):
        """Clean fixture: PLAT-101 is raw index 0, PLAT-112 is index 11."""
        _, observations, _ = _adapt_clean()
        prov_by_key = {
            obs.entity_ref.entity_id: obs.provenance_refs[0]
            for obs in observations
        }
        assert prov_by_key["PLAT-101"].record_locator == "work_items[0]"
        assert prov_by_key["PLAT-112"].record_locator == "work_items[11]"

    def test_fixture_id_propagated(self):
        _, observations, _ = _adapt_clean()
        for obs in observations:
            assert obs.provenance_refs[0].fixture_id == FIXTURE_ID

    def test_fixture_id_none_when_omitted(self):
        _, observations, _ = adapt_jira_evidence(
            normalized=_clean_normalized(),
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        for obs in observations:
            assert obs.provenance_refs[0].fixture_id is None

    def test_provenance_source_instance_matches(self):
        _, observations, _ = _adapt_clean()
        for obs in observations:
            ref = obs.provenance_refs[0]
            assert ref.source_instance is JIRA_SOURCE
            assert ref.observation_id == OBSERVATION_ID

    def test_messy_raw_indexes_are_pre_quarantine(self):
        """Messy fixture: OPS-001 is raw[0], OPS-030 is raw[30].

        OPS-020 is quarantined (duplicate) so won't appear in output,
        but other items' raw indexes must reflect original positions.
        """
        _, observations, _ = _adapt_messy()
        prov_by_key = {
            obs.entity_ref.entity_id: obs.provenance_refs[0]
            for obs in observations
        }
        assert prov_by_key["OPS-001"].record_locator == "work_items[0]"
        assert prov_by_key["OPS-002"].record_locator == "work_items[1]"
        # OPS-030 is at raw index 29 (the duplicate OPS-020 is at 30)
        assert prov_by_key["OPS-030"].record_locator == "work_items[29]"

    def test_zero_raw_matches_raises(self):
        """Provenance resolution must fail for missing raw records."""
        normalized = _clean_normalized()
        # Inject a WorkItem with a key that doesn't exist in raw_document
        phantom = WorkItem(
            source_id="99999",
            key="PLAT-999",
            title="Phantom",
            item_type="Story",
            source_priority="Medium",
            priority_band="ordinary",
            source_status="To Do",
            status_category="todo",
            assignee=None,
            created_at=T0,
            updated_at=T0,
            resolved_at=None,
            due_at=None,
            planned_at_period_start=False,
            history_complete=True,
            source_status_at_period_start=None,
            changes=(),
        )
        modified = NormalizedFixture(
            raw_document=normalized.raw_document,
            review_period=normalized.review_period,
            work_items=normalized.work_items + (phantom,),
            quarantined_records=normalized.quarantined_records,
            data_quality_conditions=normalized.data_quality_conditions,
        )
        with pytest.raises(ValueError, match="No raw record found"):
            adapt_jira_evidence(
                normalized=modified,
                source_instance=JIRA_SOURCE,
                observation_id=OBSERVATION_ID,
            )

    def test_multiple_raw_matches_raises(self):
        """Provenance resolution must fail for duplicated raw records."""
        normalized = _clean_normalized()
        # Inject a duplicate into raw_document
        raw_doc = deepcopy(normalized.raw_document)
        raw_doc["work_items"].append(
            deepcopy(raw_doc["work_items"][0])
        )  # duplicate PLAT-101
        modified = NormalizedFixture(
            raw_document=raw_doc,
            review_period=normalized.review_period,
            work_items=normalized.work_items,
            quarantined_records=normalized.quarantined_records,
            data_quality_conditions=normalized.data_quality_conditions,
        )
        with pytest.raises(ValueError, match="Multiple raw records found"):
            adapt_jira_evidence(
                normalized=modified,
                source_instance=JIRA_SOURCE,
                observation_id=OBSERVATION_ID,
            )


# =====================================================================
# 7. TestApprovedQualityMappings
# =====================================================================


class TestApprovedQualityMappings:
    """All four approved Jira → CSE quality mappings must work."""

    def test_unknown_status_maps_to_unsupported_value(self):
        """OPS-004 has UNKNOWN_STATUS condition."""
        _, observations, _ = _adapt_messy()
        obs_004 = next(
            o for o in observations
            if o.entity_ref.entity_id == "OPS-004"
        )
        status_issues = [
            q for q in obs_004.quality_issues
            if "unmapped status" in q.message
        ]
        assert len(status_issues) == 1
        assert status_issues[0].code == "unsupported_value"

    def test_unknown_priority_maps_to_unsupported_value(self):
        """OPS-005 has UNKNOWN_PRIORITY condition."""
        _, observations, _ = _adapt_messy()
        obs_005 = next(
            o for o in observations
            if o.entity_ref.entity_id == "OPS-005"
        )
        priority_issues = [
            q for q in obs_005.quality_issues
            if "unmapped priority" in q.message
        ]
        assert len(priority_issues) == 1
        assert priority_issues[0].code == "unsupported_value"

    def test_partial_history_maps_to_incomplete(self):
        """OPS-005 has PARTIAL_HISTORY condition."""
        _, observations, _ = _adapt_messy()
        obs_005 = next(
            o for o in observations
            if o.entity_ref.entity_id == "OPS-005"
        )
        history_issues = [
            q for q in obs_005.quality_issues
            if q.code == "incomplete"
        ]
        assert len(history_issues) == 1

    def test_invalid_optional_timestamp_maps_to_invalid(self):
        """OPS-025 has INVALID_OPTIONAL_TIMESTAMP condition."""
        _, observations, _ = _adapt_messy()
        obs_025 = next(
            o for o in observations
            if o.entity_ref.entity_id == "OPS-025"
        )
        timestamp_issues = [
            q for q in obs_025.quality_issues
            if q.code == "invalid"
        ]
        assert len(timestamp_issues) == 1

    def test_quality_issue_subject_ref_set(self):
        """Per-entity quality issues must have subject_ref populated."""
        _, observations, _ = _adapt_messy()
        obs_004 = next(
            o for o in observations
            if o.entity_ref.entity_id == "OPS-004"
        )
        for q in obs_004.quality_issues:
            assert q.subject_ref is not None
            assert q.subject_ref.entity_id == "OPS-004"

    def test_clean_fixture_quality_mapping(self):
        """Clean fixture has PARTIAL_HISTORY and UNKNOWN_STATUS."""
        _, observations, _ = _adapt_clean()
        obs_109 = next(
            o for o in observations
            if o.entity_ref.entity_id == "PLAT-109"
        )
        # PLAT-109 has UNKNOWN_STATUS
        assert any(
            q.code == "unsupported_value" for q in obs_109.quality_issues
        )
        obs_110 = next(
            o for o in observations
            if o.entity_ref.entity_id == "PLAT-110"
        )
        # PLAT-110 has PARTIAL_HISTORY
        assert any(
            q.code == "incomplete" for q in obs_110.quality_issues
        )


# =====================================================================
# 8. TestUnmappedConditionPreservation
# =====================================================================


class TestUnmappedConditionPreservation:
    """Unmapped Jira condition codes must be preserved, not discarded."""

    def test_unknown_code_preserved_as_unsupported_value(self):
        normalized = _clean_normalized()
        # Inject a condition with a code not in the approved map
        injected = DataQualityCondition(
            code="SOME_FUTURE_CODE",
            subject_key="PLAT-101",
            message="This is a future condition.",
        )
        modified = NormalizedFixture(
            raw_document=normalized.raw_document,
            review_period=normalized.review_period,
            work_items=normalized.work_items,
            quarantined_records=normalized.quarantined_records,
            data_quality_conditions=(
                normalized.data_quality_conditions + (injected,)
            ),
        )
        _, observations, _ = adapt_jira_evidence(
            normalized=modified,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        obs_101 = next(
            o for o in observations
            if o.entity_ref.entity_id == "PLAT-101"
        )
        unmapped = [
            q for q in obs_101.quality_issues
            if "SOME_FUTURE_CODE" in q.message
        ]
        assert len(unmapped) == 1
        assert unmapped[0].code == "unsupported_value"
        assert "future condition" in unmapped[0].message.lower()

    def test_unmapped_code_not_silently_discarded(self):
        """Total quality issues out must equal total conditions in."""
        normalized = _clean_normalized()
        injected = DataQualityCondition(
            code="NOVEL_CODE",
            subject_key=None,
            message="Bundle-level novel condition.",
        )
        modified = NormalizedFixture(
            raw_document=normalized.raw_document,
            review_period=normalized.review_period,
            work_items=normalized.work_items,
            quarantined_records=normalized.quarantined_records,
            data_quality_conditions=(
                normalized.data_quality_conditions + (injected,)
            ),
        )
        _, observations, bundle_issues = adapt_jira_evidence(
            normalized=modified,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        # Count all quality issues (per-entity + bundle)
        total_out = sum(
            len(o.quality_issues) for o in observations
        ) + len(bundle_issues)
        total_in = len(modified.data_quality_conditions)
        assert total_out == total_in


# =====================================================================
# 9. TestOrphanSubjectKeyHandling
# =====================================================================


class TestOrphanSubjectKeyHandling:
    """Orphan subject_keys must become bundle-level 'unresolved'."""

    def test_orphan_subject_key_becomes_unresolved(self):
        normalized = _clean_normalized()
        orphan = DataQualityCondition(
            code="UNKNOWN_STATUS",
            subject_key="NONEXISTENT-999",
            message="This references a quarantined/absent item.",
        )
        modified = NormalizedFixture(
            raw_document=normalized.raw_document,
            review_period=normalized.review_period,
            work_items=normalized.work_items,
            quarantined_records=normalized.quarantined_records,
            data_quality_conditions=(
                normalized.data_quality_conditions + (orphan,)
            ),
        )
        _, _, bundle_issues = adapt_jira_evidence(
            normalized=modified,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        unresolved = [
            q for q in bundle_issues if q.code == "unresolved"
        ]
        assert len(unresolved) == 1
        assert "NONEXISTENT-999" in unresolved[0].message
        assert "UNKNOWN_STATUS" in unresolved[0].message

    def test_none_subject_key_is_bundle_level(self):
        normalized = _clean_normalized()
        global_cond = DataQualityCondition(
            code="UNKNOWN_STATUS",
            subject_key=None,
            message="Global quality observation.",
        )
        modified = NormalizedFixture(
            raw_document=normalized.raw_document,
            review_period=normalized.review_period,
            work_items=normalized.work_items,
            quarantined_records=normalized.quarantined_records,
            data_quality_conditions=(
                normalized.data_quality_conditions + (global_cond,)
            ),
        )
        _, observations, bundle_issues = adapt_jira_evidence(
            normalized=modified,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        # The global condition must be in bundle, not per-entity
        global_matches = [
            q for q in bundle_issues
            if "Global quality observation" in q.message
        ]
        assert len(global_matches) == 1
        assert global_matches[0].subject_ref is None

    def test_matched_subject_key_is_per_entity(self):
        """Conditions with subject_key matching an accepted WorkItem
        are attached per-entity, not bundle-level."""
        _, observations, bundle_issues = _adapt_messy()
        # OPS-004 has UNKNOWN_STATUS — must be per-entity, not bundle
        obs_004 = next(
            o for o in observations
            if o.entity_ref.entity_id == "OPS-004"
        )
        assert len(obs_004.quality_issues) > 0
        # Verify none of OPS-004's quality issues leaked to bundle
        bundle_ops004 = [
            q for q in bundle_issues
            if q.subject_ref is not None
            and q.subject_ref.entity_id == "OPS-004"
        ]
        assert len(bundle_ops004) == 0


# =====================================================================
# 10. TestDeterministicOrdering
# =====================================================================


class TestDeterministicOrdering:
    """Output ordering must be deterministic."""

    def test_observations_sorted_by_entity_id(self):
        _, observations, _ = _adapt_clean()
        entity_ids = [o.entity_ref.entity_id for o in observations]
        assert entity_ids == sorted(entity_ids)

    def test_messy_observations_sorted_by_entity_id(self):
        _, observations, _ = _adapt_messy()
        entity_ids = [o.entity_ref.entity_id for o in observations]
        assert entity_ids == sorted(entity_ids)

    def test_per_entity_quality_issues_sorted(self):
        _, observations, _ = _adapt_messy()
        for obs in observations:
            if len(obs.quality_issues) > 1:
                keys = [
                    (q.code, q.message)
                    for q in obs.quality_issues
                ]
                assert keys == sorted(keys)

    def test_bundle_quality_issues_sorted(self):
        """Inject multiple bundle-level conditions and verify sort."""
        normalized = _clean_normalized()
        c1 = DataQualityCondition(
            code="ZZZ_CODE", subject_key=None, message="B message"
        )
        c2 = DataQualityCondition(
            code="AAA_CODE", subject_key=None, message="A message"
        )
        modified = NormalizedFixture(
            raw_document=normalized.raw_document,
            review_period=normalized.review_period,
            work_items=normalized.work_items,
            quarantined_records=normalized.quarantined_records,
            data_quality_conditions=(
                normalized.data_quality_conditions + (c1, c2)
            ),
        )
        _, _, bundle_issues = adapt_jira_evidence(
            normalized=modified,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        keys = [(q.code, q.message) for q in bundle_issues]
        assert keys == sorted(keys)


# =====================================================================
# 11. TestWorkItemsPermutationInvariance
# =====================================================================


class TestWorkItemsPermutationInvariance:
    """Varying NormalizedFixture.work_items order must produce
    identical semantic output (same observations, same content).
    Raw provenance indexes remain stable because raw_document is fixed.
    """

    def test_reversed_work_items_same_output(self):
        normalized = _clean_normalized()
        reversed_items = tuple(reversed(normalized.work_items))
        modified = NormalizedFixture(
            raw_document=normalized.raw_document,
            review_period=normalized.review_period,
            work_items=reversed_items,
            quarantined_records=normalized.quarantined_records,
            data_quality_conditions=normalized.data_quality_conditions,
        )
        ctx1, obs1, bq1 = adapt_jira_evidence(
            normalized=normalized,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
            fixture_id=FIXTURE_ID,
        )
        ctx2, obs2, bq2 = adapt_jira_evidence(
            normalized=modified,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
            fixture_id=FIXTURE_ID,
        )
        # Same observation count
        assert len(obs1) == len(obs2)
        # Same entity IDs in same order
        ids1 = [o.entity_ref.entity_id for o in obs1]
        ids2 = [o.entity_ref.entity_id for o in obs2]
        assert ids1 == ids2
        # Same provenance locators (from fixed raw_document)
        for o1, o2 in zip(obs1, obs2):
            assert (
                o1.provenance_refs[0].record_locator
                == o2.provenance_refs[0].record_locator
            )
        # Same quality issues
        for o1, o2 in zip(obs1, obs2):
            assert o1.quality_issues == o2.quality_issues
        # Same bundle-level quality
        assert bq1 == bq2

    def test_shuffled_work_items_same_output(self):
        """A specific non-trivial permutation."""
        normalized = _clean_normalized()
        items = list(normalized.work_items)
        # Rotate by 5 positions
        rotated = items[5:] + items[:5]
        modified = NormalizedFixture(
            raw_document=normalized.raw_document,
            review_period=normalized.review_period,
            work_items=tuple(rotated),
            quarantined_records=normalized.quarantined_records,
            data_quality_conditions=normalized.data_quality_conditions,
        )
        _, obs1, _ = adapt_jira_evidence(
            normalized=normalized,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
            fixture_id=FIXTURE_ID,
        )
        _, obs2, _ = adapt_jira_evidence(
            normalized=modified,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
            fixture_id=FIXTURE_ID,
        )
        assert obs1 == obs2


# =====================================================================
# 12. TestImmutability
# =====================================================================


class TestImmutability:
    """The adapter must not mutate inputs and outputs must be frozen."""

    def test_normalized_fixture_unchanged(self):
        normalized = _clean_normalized()
        snapshot_items = normalized.work_items
        snapshot_conditions = normalized.data_quality_conditions
        snapshot_quarantined = normalized.quarantined_records
        adapt_jira_evidence(
            normalized=normalized,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        assert normalized.work_items is snapshot_items
        assert normalized.data_quality_conditions is snapshot_conditions
        assert normalized.quarantined_records is snapshot_quarantined

    def test_work_items_unchanged(self):
        normalized = _clean_normalized()
        items_before = deepcopy(normalized.work_items)
        adapt_jira_evidence(
            normalized=normalized,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        assert normalized.work_items == items_before

    def test_raw_document_unchanged(self):
        normalized = _clean_normalized()
        raw_before = deepcopy(normalized.raw_document)
        adapt_jira_evidence(
            normalized=normalized,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )
        assert normalized.raw_document == raw_before

    def test_output_observations_frozen(self):
        _, observations, _ = _adapt_clean()
        for obs in observations:
            with pytest.raises(FrozenInstanceError):
                obs.entity_ref = None  # type: ignore[misc]

    def test_output_states_frozen(self):
        _, observations, _ = _adapt_clean()
        for obs in observations:
            with pytest.raises(FrozenInstanceError):
                obs.observed_state.key = "MUTATED"  # type: ignore[misc]

    def test_output_quality_issues_frozen(self):
        _, observations, _ = _adapt_messy()
        for obs in observations:
            for q in obs.quality_issues:
                with pytest.raises(FrozenInstanceError):
                    q.code = "MUTATED"  # type: ignore[misc]


# =====================================================================
# 13. TestAdapterDoesNotChangeExistingEvaluation
# =====================================================================


class TestAdapterDoesNotChangeExistingEvaluation:
    """Running the adapter must not affect existing evaluation."""

    def test_evaluation_identical_after_adapter(self):
        from shadow_orbit.evaluation import evaluate_week_one_rules

        normalized = _clean_normalized()
        matches_before, suppressed_before = evaluate_week_one_rules(
            normalized
        )

        # Run the adapter
        adapt_jira_evidence(
            normalized=normalized,
            source_instance=JIRA_SOURCE,
            observation_id=OBSERVATION_ID,
        )

        matches_after, suppressed_after = evaluate_week_one_rules(
            normalized
        )
        assert matches_before == matches_after
        assert suppressed_before == suppressed_after


# =====================================================================
# 14. TestSourceInstanceIdentity
# =====================================================================


class TestSourceInstanceIdentity:
    """Different SourceInstances produce distinct EntityRefs."""

    def test_different_instance_ids_distinct_entity_refs(self):
        normalized = _clean_normalized()
        src_a = SourceInstance(
            source_kind="jira", instance_id="jira-site-a"
        )
        src_b = SourceInstance(
            source_kind="jira", instance_id="jira-site-b"
        )
        _, obs_a, _ = adapt_jira_evidence(
            normalized=normalized,
            source_instance=src_a,
            observation_id="obs-a",
        )
        _, obs_b, _ = adapt_jira_evidence(
            normalized=normalized,
            source_instance=src_b,
            observation_id="obs-b",
        )
        # Same entity_id but different source_instance → not equal
        for oa, ob in zip(obs_a, obs_b):
            assert oa.entity_ref.entity_id == ob.entity_ref.entity_id
            assert oa.entity_ref != ob.entity_ref
            assert (
                oa.entity_ref.source_instance.instance_id
                != ob.entity_ref.source_instance.instance_id
            )

    def test_same_instance_id_equal_entity_refs(self):
        normalized = _clean_normalized()
        src1 = SourceInstance(
            source_kind="jira", instance_id="same-site"
        )
        src2 = SourceInstance(
            source_kind="jira", instance_id="same-site"
        )
        _, obs1, _ = adapt_jira_evidence(
            normalized=normalized,
            source_instance=src1,
            observation_id="obs-1",
        )
        _, obs2, _ = adapt_jira_evidence(
            normalized=normalized,
            source_instance=src2,
            observation_id="obs-2",
        )
        for o1, o2 in zip(obs1, obs2):
            assert o1.entity_ref == o2.entity_ref
