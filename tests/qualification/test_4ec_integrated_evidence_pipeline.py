"""Phase 4E-C — Integrated Evidence-Pipeline Qualification Tests.

Organized by the five gates defined in the Phase 4E-C Proving Specification:
    Gate 4E-C-01 — Evidence Assembly Integrity
    Gate 4E-C-02 — Linkage Isolation
    Gate 4E-C-03 — State Isolation
    Gate 4E-C-04 — Temporal Isolation
    Gate 4E-C-05 — Evaluation Isolation

Every adversarial case from Section 11 (C-01 through C-15) is explicitly tested.

Invariants verified:
    - INV-ID-01 .. INV-ID-04 (Identity isolation & deterministic IDs)
    - INV-EV-01 .. INV-EV-03 (Provenance grounding & verification)
    - INV-LK-01 .. INV-LK-02 (Linkage neutrality)
    - INV-ST-01 .. INV-ST-02 (State isolation & no transfer)
    - INV-TM-01 .. INV-TM-02 (Temporal independence & proximity != causality)
    - INV-GR-01 .. INV-GR-03 (Graph constraints & provider scoping)
    - INV-FW-01 .. INV-FW-04 (Semantic firewall integrity)

Baseline reference: 873 passed / 12 skipped / 0 failed (Phase 4E-B HEAD).
Zero production-code changes authorized. All tests are purely additive qualification.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shadow_orbit.evidence_assembly import (
    assemble_evidence_bundle,
    validate_evidence_bundle,
)
from shadow_orbit.evidence_evaluation import (
    evaluate_evidence_bundle,
    serialize_evaluation_result,
)
from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceBundle,
    EvidenceObservation,
    EvidenceRelationship,
    GitHubPullRequestState,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    RepositoryEvolutionRelationship,
    RepositoryProvenanceRef,
    SemanticFirewall,
    SourceInstance,
    UnresolvedReference,
    compute_relationship_id,
    serialize_evidence_bundle,
    validate_repository_evolution_graph,
    validate_repository_evolution_relationship,
    verify_provenance_file_digest,
)
from qualification.phase4e_c.fixtures import (
    ADVERSARIAL_CASES,
    GH_SOURCE,
    JIRA_SOURCE,
    ROCKSDB_SOURCE,
    DOCKER_SOURCE,
    STRATOSPHERE_SOURCE,
    GITLAB_SOURCE,
    build_case_c01,
    build_case_c02,
    build_case_c03,
    build_case_c04,
    build_case_c05,
    build_case_c06,
    build_case_c07,
    build_case_c08,
    build_case_c09,
    build_case_c10,
    build_case_c11,
    build_case_c12,
    build_case_c13,
    build_case_c14,
    build_case_c15,
)


# ── Gate 4E-C-01: Evidence Assembly Integrity ────────────────────────────────

class TestGate4EC01EvidenceAssemblyIntegrity:
    """Gate 4E-C-01: Demonstrate that repository-evolution relationships enter a normal
    EvidenceBundle alongside existing observations, relationships, and alignments
    without altering their semantics, deduplicating safely, and failing closed on defects.

    Covers Adversarial Cases: C-09, C-11, C-12, C-15.
    """

    def test_c09_missing_or_invalid_provenance_fails_validation(self):
        """C-09: Repository evolution with missing or invalid provenance fails validation closed."""
        case = build_case_c09()
        src_repo = case["source_repo"]
        tgt_repo = case["target_repo"]
        invalid_prov = case["invalid_prov"]

        with pytest.raises(ValueError, match="INV-EV-01 violated: provenance_refs.*fixture_id"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=src_repo,
                target_repository=tgt_repo,
                verification_status="PROVEN",
                observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
                provenance_refs=(invalid_prov,),
                family_payload={"http_status_code": 301},
            )

    def test_c11_conflicting_duplicate_relationship_ids_fail_closed(self):
        """C-11: Conflicting duplicate relationship IDs fail closed.

        - assemble_evidence_bundle raises ValueError on semantic conflict.
        - validate_evidence_bundle emits QualityIssue(code="contradictory").
        """
        case = build_case_c11()
        rel1 = case["rel1"]
        rel2 = case["rel2_conflicting"]

        # 1. Assembly fails closed with ValueError
        with pytest.raises(ValueError, match="Semantic conflict detected for relationship_id"):
            assemble_evidence_bundle(
                bundle_id="b-c11-fail",
                bundle_version="1.0.0",
                repository_relationships=(rel1, rel2),
            )

        # 2. Validation flags contradictory quality issue
        bundle_conflict = EvidenceBundle(
            bundle_id="b-c11-validate",
            bundle_version="1.0.0",
            observation_contexts=(),
            repository_relationships=(rel1, rel2),
        )
        issues = validate_evidence_bundle(bundle_conflict)
        assert any(
            i.code == "contradictory" and "Conflicting repository evolution relationships" in i.message
            for i in issues
        ), f"Expected contradictory quality issue, got: {issues}"

    def test_c12_permuted_evidence_ordering_produces_identical_bundle(self):
        """C-12: Permuted evidence ordering produces byte-identical serialized results."""
        case = build_case_c12()
        rel = case["repo_rel"]
        jira_obs = case["jira_obs"]
        gh_obs = case["gh_obs"]

        # Order 1: Jira first, then GitHub, repo_rel
        bundle1 = EvidenceBundle(
            bundle_id="b-c12",
            bundle_version="1.0.0",
            observation_contexts=(jira_obs.observation_context, gh_obs.observation_context),
            observations=(jira_obs, gh_obs),
            repository_relationships=(rel,),
        )

        # Order 2: GitHub first, then Jira, repo_rel
        bundle2 = EvidenceBundle(
            bundle_id="b-c12",
            bundle_version="1.0.0",
            observation_contexts=(gh_obs.observation_context, jira_obs.observation_context),
            observations=(gh_obs, jira_obs),
            repository_relationships=(rel,),
        )

        ser1 = json.dumps(serialize_evidence_bundle(bundle1), sort_keys=True)
        ser2 = json.dumps(serialize_evidence_bundle(bundle2), sort_keys=True)

        assert ser1 == ser2, "Serialized bundle differs under observation permutation"

    def test_c15_malformed_evolution_metadata_rejected(self):
        """C-15: Malformed evolution metadata is rejected and never enters a valid bundle."""
        src_repo = EntityRef(GH_SOURCE, "repository", "apache/incubator-flink")
        tgt_repo = EntityRef(GH_SOURCE, "repository", "apache/flink")
        prov = RepositoryProvenanceRef(
            source_instance=GH_SOURCE,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="base.repo.full_name",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )

        # 1. Invalid directionality
        with pytest.raises(ValueError, match="REDIRECT must have directionality"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=src_repo,
                target_repository=tgt_repo,
                directionality="BIDIRECTIONAL",  # REDIRECT must be DIRECTED
                verification_status="PROVEN",
                observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
                provenance_refs=(prov,),
                family_payload={"http_status_code": 301},
            )

        # 2. Incompatible family and type
        with pytest.raises(ValueError, match="is not a member of family"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="EXTERNAL_DEPENDENCY",  # Invalid type for NAVIGATION_ROUTING
                source_repository=src_repo,
                target_repository=tgt_repo,
                verification_status="PROVEN",
                observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
                provenance_refs=(prov,),
                family_payload={},
            )


# ── Gate 4E-C-02: Linkage Isolation ─────────────────────────────────────────

class TestGate4EC02LinkageIsolation:
    """Gate 4E-C-02: Demonstrate that repository evolution coexists with explicit
    Jira<->GitHub relationships without causing implicit linkage upgrades, ownership
    transfers, or cross-system inference.

    Covers Adversarial Cases: C-01, C-06, C-07, C-10.
    """

    def test_c01_redirect_does_not_transfer_pr_ownership(self):
        """C-01: Redirect + target PR does not transfer PR ownership to predecessor repository."""
        case = build_case_c01()
        rel = case["repo_rel"]
        jira_obs = case["jira_obs"]
        gh_obs = case["gh_obs"]

        bundle = EvidenceBundle(
            bundle_id="b-c01",
            bundle_version="1.0.0",
            observation_contexts=(jira_obs.observation_context, gh_obs.observation_context),
            observations=(jira_obs, gh_obs),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # PR entity ref must point to apache/flink/254, NOT apache/incubator-flink/254
        assert gh_obs.entity_ref.entity_id == "apache/flink/254"
        assert gh_obs.entity_ref.source_instance == GH_SOURCE
        # Predecessor repository is distinct
        assert rel.source_repository.entity_id == "apache/incubator-flink"
        assert rel.source_repository.entity_id != gh_obs.entity_ref.entity_id
        # No cross-system link created between Jira and PR by repository evolution
        assert len(bundle.relationships) == 0

    def test_c06_explicit_linkage_remains_authoritative(self):
        """C-06: Explicit Jira<->PR linkage remains authoritative alongside repository evolution."""
        case = build_case_c06()
        rel = case["repo_rel"]
        jira_obs = case["jira_obs"]
        gh_obs = case["gh_obs"]
        explicit_rel = case["explicit_rel"]

        bundle = EvidenceBundle(
            bundle_id="b-c06",
            bundle_version="1.0.0",
            observation_contexts=(jira_obs.observation_context, gh_obs.observation_context),
            observations=(jira_obs, gh_obs),
            relationships=(explicit_rel,),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # Explicit relationship preserved exactly
        assert len(bundle.relationships) == 1
        r = bundle.relationships[0]
        assert r.kind == "explicit_link"
        assert r.basis == "explicit_metadata"
        assert r.subject_ref == jira_obs.entity_ref
        assert r.object_ref == gh_obs.entity_ref
        # Evaluation evaluates explicit link as PROVEN sufficiency
        res = evaluate_evidence_bundle(bundle)
        # Jira is Resolved, PR #254 is closed/merged
        assert len(res.findings) == 0 or all(f.sufficiency in ("PROVEN", "SUPPORTED") for f in res.findings)

    def test_c07_evolution_does_not_upgrade_lexical_similarity(self):
        """C-07: Evolution does not upgrade lexical/mention relationships to explicit/proven."""
        case = build_case_c07()
        rel = case["repo_rel"]
        jira_obs = case["jira_obs"]
        gh_obs = case["gh_obs"]
        mention_rel = case["mention_rel"]

        bundle = EvidenceBundle(
            bundle_id="b-c07",
            bundle_version="1.0.0",
            observation_contexts=(jira_obs.observation_context, gh_obs.observation_context),
            observations=(jira_obs, gh_obs),
            relationships=(mention_rel,),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # Mention relationship remains mentions / lexical_match
        assert len(bundle.relationships) == 1
        r = bundle.relationships[0]
        assert r.kind == "mentions"
        assert r.basis == "lexical_match"

    def test_c10_cross_provider_isolation_prevents_false_collision(self):
        """C-10: Same repository name across different providers maintains strict instance isolation."""
        case = build_case_c10()
        gh_repo = case["gh_repo"]
        gl_repo = case["gl_repo"]
        rel1 = case["rel"]

        # Validate graph with cross-provider relationship
        validate_repository_evolution_graph((rel1,))

        # Verify that entity_ids match but source_instances differ
        assert gh_repo.entity_id == gl_repo.entity_id == "apache/flink"
        assert gh_repo.source_instance.source_kind == "github"
        assert gl_repo.source_instance.source_kind == "gitlab"
        assert gh_repo != gl_repo


# ── Gate 4E-C-03: State Isolation ───────────────────────────────────────────

class TestGate4EC03StateIsolation:
    """Gate 4E-C-03: Demonstrate that repository evolution never transfers lifecycle state,
    completion, blockage, or ownership across entity boundaries.

    Covers Adversarial Cases: C-02, C-03, C-04.
    """

    def test_c02_redirect_does_not_transfer_jira_state(self):
        """C-02: Redirect + target Jira issue does not transfer Jira state to predecessor."""
        case = build_case_c02()
        rel = case["repo_rel"]
        jira_obs = case["jira_obs"]
        gh_obs = case["gh_obs"]

        bundle = EvidenceBundle(
            bundle_id="b-c02",
            bundle_version="1.0.0",
            observation_contexts=(jira_obs.observation_context, gh_obs.observation_context),
            observations=(jira_obs, gh_obs),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # Jira issue state remains purely on Jira issue ref
        assert jira_obs.observed_state.key == "FLINK-1359"
        assert jira_obs.observed_state.status_category == "done"
        # Predecessor repository has no observed_state
        assert rel.source_repository.entity_kind == "repository"
        assert rel.source_repository.entity_id == "apache/incubator-flink"

    def test_c03_predecessor_successor_distinct_identities_and_state(self):
        """C-03: Predecessor and successor PRs sharing numeric PR #126 have distinct states."""
        case = build_case_c03()
        rel = case["repo_rel"]
        strat_obs = case["strat_obs"]
        flink_obs = case["flink_obs"]

        bundle = EvidenceBundle(
            bundle_id="b-c03",
            bundle_version="1.0.0",
            observation_contexts=(strat_obs.observation_context, flink_obs.observation_context),
            observations=(strat_obs, flink_obs),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # Both have number=126 but distinct entity_id, timestamps, and repo scope
        assert strat_obs.entity_ref.entity_id == "stratosphere/stratosphere/126"
        assert flink_obs.entity_ref.entity_id == "apache/flink/126"
        assert strat_obs.observed_state.merged_at != flink_obs.observed_state.merged_at
        assert strat_obs.entity_ref != flink_obs.entity_ref

    def test_c04_external_dependency_merged_pr_does_not_complete_issue(self):
        """C-04: External dependency merged PR does not complete first-party Jira issue."""
        case = build_case_c04()
        rel = case["repo_rel"]
        kafka_obs = case["kafka_obs"]
        rocks_obs = case["rocks_obs"]

        bundle = EvidenceBundle(
            bundle_id="b-c04",
            bundle_version="1.0.0",
            observation_contexts=(kafka_obs.observation_context, rocks_obs.observation_context),
            observations=(kafka_obs, rocks_obs),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # RocksDB PR #2283 is merged
        assert rocks_obs.observed_state.state == "closed"
        assert rocks_obs.observed_state.merged_at is not None
        # KAFKA-9168 remains In Progress / in_progress; no completion manufactured
        assert kafka_obs.observed_state.source_status == "In Progress"
        assert kafka_obs.observed_state.status_category == "in_progress"
        assert kafka_obs.observed_state.resolved_at is None


# ── Gate 4E-C-04: Temporal Isolation ─────────────────────────────────────────

class TestGate4EC04TemporalIsolation:
    """Gate 4E-C-04: Demonstrate that temporal ordering remains distinct from causality.
    Temporal proximity or sequence across repositories must not infer causal links or fault.

    Covers Adversarial Cases: C-05, C-08.
    """

    def test_c05_packaging_relationship_temporal_independence(self):
        """C-05: Docker packaging PR merged 36 days post-resolution does not infer causal defect."""
        case = build_case_c05()
        rel = case["repo_rel"]
        flink_obs = case["flink_obs"]
        docker_obs = case["docker_obs"]

        bundle = EvidenceBundle(
            bundle_id="b-c05",
            bundle_version="1.0.0",
            observation_contexts=(flink_obs.observation_context, docker_obs.observation_context),
            observations=(flink_obs, docker_obs),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # Timestamps preserved faithfully
        assert flink_obs.observed_state.resolved_at == datetime(2021, 1, 10, 15, 0, 0, tzinfo=timezone.utc)
        assert docker_obs.observed_state.merged_at == datetime(2021, 2, 15, 16, 0, 0, tzinfo=timezone.utc)

        # Evaluate bundle: zero cross-system relationships -> zero findings (no defect inferred)
        res = evaluate_evidence_bundle(bundle)
        assert len(res.findings) == 0
        assert len(res.suppressed_evaluations) == 0

    def test_c08_temporal_proximity_does_not_infer_causality(self):
        """C-08: Temporal proximity across related repositories does not create causal links."""
        case = build_case_c08()
        rel = case["repo_rel"]
        flink_obs = case["flink_obs"]
        docker_obs = case["docker_obs"]

        bundle = EvidenceBundle(
            bundle_id="b-c08",
            bundle_version="1.0.0",
            observation_contexts=(flink_obs.observation_context, docker_obs.observation_context),
            observations=(flink_obs, docker_obs),
            repository_relationships=(rel,),
        )
        # Evaluator produces zero findings because proximity alone is never a candidate pair
        res = evaluate_evidence_bundle(bundle)
        assert res.summary["total_findings"] == 0
        assert res.summary["total_suppressed"] == 0


# ── Gate 4E-C-05: Evaluation Isolation ───────────────────────────────────────

class TestGate4EC05EvaluationIsolation:
    """Gate 4E-C-05: Compare equivalent evidence with and without repository-evolution metadata.
    Path A (without repo evolution) == Path B (with repo evolution). Zero new findings.

    Covers Adversarial Cases: C-13, C-14.
    """

    def test_c13_repository_evolution_removed_leaves_ordinary_evidence_intact(self):
        """C-13: Removing repository evolution from a bundle causes zero mutation to ordinary evidence."""
        case = build_case_c13()
        rel = case["repo_rel"]
        jira_obs = case["jira_obs"]
        gh_obs = case["gh_obs"]

        # Bundle with repo evolution
        bundle_with = EvidenceBundle(
            bundle_id="b-c13-with",
            bundle_version="1.0.0",
            observation_contexts=(jira_obs.observation_context, gh_obs.observation_context),
            observations=(jira_obs, gh_obs),
            repository_relationships=(rel,),
        )

        # Bundle without repo evolution
        bundle_without = EvidenceBundle(
            bundle_id="b-c13-without",
            bundle_version="1.0.0",
            observation_contexts=(jira_obs.observation_context, gh_obs.observation_context),
            observations=(jira_obs, gh_obs),
            repository_relationships=(),
        )

        assert bundle_with.observations == bundle_without.observations
        assert bundle_with.observation_contexts == bundle_without.observation_contexts
        assert bundle_with.relationships == bundle_without.relationships
        assert bundle_with.cross_system_alignments == bundle_without.cross_system_alignments
        assert bundle_with.quality_issues == bundle_without.quality_issues

    def test_c14_evaluation_findings_identical_path_a_vs_path_b(self):
        """C-14: evaluate_evidence_bundle produces bit-identical findings across Path A and Path B.

        Path A: ordinary evidence only (baseline).
        Path B: ordinary evidence + repository evolution relationship.
        """
        case = build_case_c14()
        rel = case["repo_rel"]
        jira_obs = case["jira_obs"]
        gh_obs = case["gh_obs"]
        mention_rel = case["mention_rel"]

        # Path A: without repo evolution
        bundle_a = EvidenceBundle(
            bundle_id="b-c14-path-a",
            bundle_version="1.0.0",
            observation_contexts=(jira_obs.observation_context, gh_obs.observation_context),
            observations=(jira_obs, gh_obs),
            relationships=(mention_rel,),
            repository_relationships=(),
        )

        # Path B: with repo evolution
        bundle_b = EvidenceBundle(
            bundle_id="b-c14-path-b",
            bundle_version="1.0.0",
            observation_contexts=(jira_obs.observation_context, gh_obs.observation_context),
            observations=(jira_obs, gh_obs),
            relationships=(mention_rel,),
            repository_relationships=(rel,),
        )

        res_a = evaluate_evidence_bundle(bundle_a)
        res_b = evaluate_evidence_bundle(bundle_b)

        # Total findings and total suppressed must be identical
        assert len(res_a.findings) == len(res_b.findings)
        assert len(res_a.suppressed_evaluations) == len(res_b.suppressed_evaluations)

        # Finding IDs and dispositions must be identical
        a_findings = [f.finding_id for f in res_a.findings]
        b_findings = [f.finding_id for f in res_b.findings]
        assert a_findings == b_findings

        # Summaries must be identical
        assert res_a.summary["findings_by_rule"] == res_b.summary["findings_by_rule"]
        assert res_a.summary["dispositions"] == res_b.summary["dispositions"]


# ── Manifest & Specification Coverage Tests ──────────────────────────────────

class TestPhase4ECManifestAndSpecificationCoverage:
    """Verifies that all 15 adversarial cases from Section 11 of the specification
    are registered and covered across the five qualification gates.
    """

    def test_adversarial_cases_manifest_contains_exact_15_cases(self):
        """ADVERSARIAL_CASES manifest must contain exactly 15 cases (C-01 to C-15)."""
        assert len(ADVERSARIAL_CASES) == 15
        expected_ids = [f"C-{i:02d}" for i in range(1, 16)]
        manifest_ids = [c["case_id"] for c in ADVERSARIAL_CASES]
        assert manifest_ids == expected_ids

    def test_all_five_gates_represented(self):
        """All five gates (4E-C-01 to 4E-C-05) must be represented in the manifest."""
        gates = {c["gate"] for c in ADVERSARIAL_CASES}
        expected_gates = {"4E-C-01", "4E-C-02", "4E-C-03", "4E-C-04", "4E-C-05"}
        assert gates == expected_gates

    def test_every_case_has_builder_and_required_behavior(self):
        """Every adversarial case definition has required behavior and valid builder."""
        for case in ADVERSARIAL_CASES:
            assert "case_id" in case
            assert "gate" in case
            assert "theme" in case
            assert "condition" in case
            assert "required_behavior" in case
            assert "builder" in case
            assert len(case["required_behavior"]) > 0
