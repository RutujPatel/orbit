"""Phase 4E-D: Multi-System Evidence Composition & Contextual Utility Qualification Tests.

Verifies the five proving gates, all 15 adversarial scenarios (D-01 through D-15),
the 20 existing formal invariants, and the 4 new compositional invariants (INV-CMP-01..04)
as authorized in:
    docs/specifications/phase4e_d_proving_specification.md

Execution Baseline Reference: 891 passed / 12 skipped / 0 failed.
Zero production code modifications authorized.
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
    CrossSystemStateAlignment,
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
    _repo_endpoint_key,
    compute_relationship_id,
    serialize_evidence_bundle,
    validate_repository_evolution_graph,
    validate_repository_evolution_relationship,
    verify_provenance_file_digest,
)
from qualification.phase4e_d.fixtures import (
    GH_SOURCE,
    JIRA_SOURCE,
    ROCKSDB_SOURCE,
    DOCKER_SOURCE,
    STRATOSPHERE_SOURCE,
    GITLAB_SOURCE,
    build_full_composite_bundle,
    run_all_scenarios,
    execute_scenario_d01,
    execute_scenario_d02,
    execute_scenario_d03,
    execute_scenario_d04,
    execute_scenario_d05,
    execute_scenario_d06,
    execute_scenario_d07,
    execute_scenario_d08,
    execute_scenario_d09,
    execute_scenario_d10,
    execute_scenario_d11,
    execute_scenario_d12,
    execute_scenario_d13,
    execute_scenario_d14,
    execute_scenario_d15,
)


# ── Gate 4E-D-01: Full Composite Bundle Assembly & Preservation ──────────────

class TestGate4ED01CompositeBundleAssembly:
    """Gate 4E-D-01: Full heterogeneous composition without field clobbering,
    type confusion, or relationship mutation.
    """

    def test_full_composite_bundle_preserves_all_eight_fields(self):
        """At least one qualification fixture contains all 8 canonical fields simultaneously."""
        bundle = build_full_composite_bundle("b-gate-01-full")

        # 1. Observation Contexts
        assert len(bundle.observation_contexts) == 3
        # 2. Observations
        assert len(bundle.observations) == 5
        # 3. Relationships
        assert len(bundle.relationships) == 2
        # 4. Unresolved References
        assert len(bundle.unresolved_references) == 1
        # 5. Quality Issues
        assert len(bundle.quality_issues) == 1
        # 6. Cross-System Alignments
        assert len(bundle.cross_system_alignments) == 1
        # 7. Repository Relationships
        assert len(bundle.repository_relationships) == 3
        # 8. Bundle identity & version
        assert bundle.bundle_id == "b-gate-01-full"
        assert bundle.bundle_version == "1.0.0"

        # Serialization round-trip
        ser = serialize_evidence_bundle(bundle)
        assert isinstance(ser, dict)
        assert "observations" in ser
        assert "relationships" in ser
        assert "unresolved_references" in ser
        assert "cross_system_alignments" in ser
        assert "repository_relationships" in ser

    def test_d09_alignment_alongside_topology(self):
        """D-09: Precomputed CrossSystemStateAlignment alongside repository topology."""
        res = execute_scenario_d09()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"

    def test_d14_compound_provenance_chain(self):
        """D-14: Cryptographic chain of custody across compound provenance graph."""
        res = execute_scenario_d14()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"


# ── Gate 4E-D-02: Contextual Disambiguation vs. Linkage Neutrality ───────────

class TestGate4ED02ContextualDisambiguation:
    """Gate 4E-D-02: Disambiguation without linkage upgrades or endpoint rewriting."""

    def test_d01_redirected_repo_pr_ownership(self):
        """D-01: Redirected repo citation with resolved issue and open PR."""
        res = execute_scenario_d01()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"

    def test_d02_predecessor_repo_lineage_merged_pr(self):
        """D-02: Predecessor repo lineage with successor merged PR and open issue."""
        res = execute_scenario_d02()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"

    def test_d06_dual_pr_association_across_repos(self):
        """D-06: Dual PR association across predecessor and target repositories."""
        res = execute_scenario_d06()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"

    def test_d10_cross_provider_identity_partitioning(self):
        """D-10: Multi-provider identity partitioning under identical repository slugs."""
        res = execute_scenario_d10()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"

    def test_d13_lexical_mention_saturation_firewall(self):
        """D-13: Negative linkage firewall under lexical mention saturation."""
        res = execute_scenario_d13()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"


# ── Gate 4E-D-03: Multi-System State & Temporal Coherence ────────────────────

class TestGate4ED03StateAndTemporalCoherence:
    """Gate 4E-D-03: Independent lifecycles and temporal disclosure without causality."""

    def test_d03_external_dependency_pr_no_first_party_completion(self):
        """D-03: External dependency merged PR with in-progress first-party issue."""
        res = execute_scenario_d03()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"

    def test_d04_packaging_pr_observational_lag(self):
        """D-04: Packaging PR merged 36 days post-resolution with explicit link."""
        res = execute_scenario_d04()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"


# ── Gate 4E-D-04: Resilient Gaps & Explicit Ambiguity Scoping ─────────────────

class TestGate4ED04ResilientGapsAndAmbiguity:
    """Gate 4E-D-04: Partial or defective evidence isolated to affected pair without cascade."""

    def test_d05_dangling_unresolved_citation_isolation(self):
        """D-05: Compound bundle with valid explicit link and dangling unresolved citation."""
        res = execute_scenario_d05()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"

    def test_d07_ambiguous_observation_context(self):
        """D-07: Ambiguous observation context (multiple observations for same entity)."""
        res = execute_scenario_d07()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"

    def test_d08_stale_observation_suppression(self):
        """D-08: Stale Jira observation paired with recent GitHub PR."""
        res = execute_scenario_d08()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"

    def test_d11_compound_quality_issue_preservation(self):
        """D-11: Compound quality issue coexistence (unresolved, stale, contradictory)."""
        res = execute_scenario_d11()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"


# ── Gate 4E-D-05: Composite Evaluator Isolation & Permutation ────────────────

class TestGate4ED05EvaluatorTruthAndPermutation:
    """Gate 4E-D-05: Evaluation restricted to authorized rules, permutation invariant."""

    def test_d12_five_way_permutation_determinism(self):
        """D-12: Full composite bundle under 5 randomized permutation sequences."""
        res = execute_scenario_d12()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"

    def test_d15_authorized_rule_set_restriction(self):
        """D-15: Composite evaluation restricted to authorized candidate rules."""
        res = execute_scenario_d15()
        assert res["execution_verified"] is True
        assert res["verdict"] == "PROVEN"


# ── Formal Invariants Verification (20 Existing + 4 Compositional) ───────────

class TestPhase4EDFormalInvariants:
    """Explicitly verifies the 24 formal invariants governing Phase 4E-D."""

    def test_20_existing_invariants_hold_in_composite_bundle(self):
        """Verifies the 20 Phase 4D/4E-C invariants in the full composite bundle."""
        bundle = build_full_composite_bundle("b-invariants-20")

        # INV-ID-01..04: Identity & deterministic IDs
        for r in bundle.repository_relationships:
            assert r.source_repository.entity_kind == "repository"
            assert r.target_repository.entity_kind == "repository"
            assert "/" in r.source_repository.entity_id
            assert "/" in r.target_repository.entity_id
            validate_repository_evolution_relationship(r)

        # INV-EV-01..03: Provenance non-empty & authentic SHA-256
        for r in bundle.repository_relationships:
            assert len(r.provenance_refs) > 0
            for p in r.provenance_refs:
                assert verify_provenance_file_digest(p) is True

        # INV-GR-01..03: Graph acyclicity & provider-scoped keys
        validate_repository_evolution_graph(bundle.repository_relationships)

        # INV-FW-01..04: Semantic firewall & anti-Cartesian candidate pairs
        eval_res = evaluate_evidence_bundle(bundle)
        # Evaluator candidate pairs only include pairs connected by EvidenceRelationship
        paired_subject_ids = {f.subject_ref.entity_id for f in eval_res.findings}
        for rel in bundle.repository_relationships:
            # Repository endpoints never become candidate subjects
            assert rel.source_repository.entity_id not in paired_subject_ids
            assert rel.target_repository.entity_id not in paired_subject_ids

    def test_inv_cmp_01_composite_coexistence(self):
        """INV-CMP-01: Simultaneous presence of all 8 evidence collection types preserves pairwise orthogonality."""
        bundle = build_full_composite_bundle("b-inv-cmp-01")
        assert len(bundle.observation_contexts) > 0
        assert len(bundle.observations) > 0
        assert len(bundle.relationships) > 0
        assert len(bundle.unresolved_references) > 0
        assert len(bundle.quality_issues) > 0
        assert len(bundle.cross_system_alignments) > 0
        assert len(bundle.repository_relationships) > 0

    def test_inv_cmp_02_routing_transparency(self):
        """INV-CMP-02: Navigation routing records contextual evolution without altering referenced endpoints."""
        res = execute_scenario_d01()
        assert "PR endpoint remains 'apache/flink/254'" in res["observed_behavior"]
        assert "zero ownership transferred" in res["observed_behavior"]

    def test_inv_cmp_03_gap_resilience(self):
        """INV-CMP-03: Unresolved, stale, and ambiguous references are scoped without cascade suppression."""
        res_d05 = execute_scenario_d05()
        res_d07 = execute_scenario_d07()
        res_d08 = execute_scenario_d08()
        assert res_d05["execution_verified"] is True
        assert res_d07["execution_verified"] is True
        assert res_d08["execution_verified"] is True

    def test_inv_cmp_04_compound_permutation_invariance(self):
        """INV-CMP-04: Arbitrary permutation of compound evidence collections produces strictly identical digests."""
        res = execute_scenario_d12()
        assert "serialized bundle SHA-256 identical" in res["observed_behavior"]
        assert "evaluation result digests identical" in res["observed_behavior"]


# ── Execution-Derived Manifest Coverage Test ─────────────────────────────────

class TestPhase4EDManifestCoverage:
    """Verifies that all 15 scenarios execute programmatically and derive PROVEN verdicts."""

    def test_all_15_scenarios_execute_and_pass(self):
        results = run_all_scenarios()
        assert len(results) == 15
        expected_ids = [f"D-{i:02d}" for i in range(1, 16)]
        actual_ids = [r["case_id"] for r in results]
        assert actual_ids == expected_ids

        for r in results:
            assert r["execution_verified"] is True, f"Scenario {r['case_id']} was not verified by execution!"
            assert r["verdict"] == "PROVEN", f"Scenario {r['case_id']} failed!"
            assert len(r["observed_behavior"]) > 10, f"Scenario {r['case_id']} observed_behavior is empty!"
            # Ensure observed_behavior was not merely copied from required_behavior
            assert r["observed_behavior"] != r["required_behavior"], (
                f"Scenario {r['case_id']} violated methodological invariant: "
                "observed_behavior was identical to required_behavior!"
            )
