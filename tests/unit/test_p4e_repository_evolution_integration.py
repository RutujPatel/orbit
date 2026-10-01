"""Phase 4E-B: Controlled Production Integration Tests for Repository Evolution.

Verifies:
1. EvidenceBundle backward compatibility and sparse serialization
2. Production integration in assemble_evidence_bundle and validate_evidence_bundle
3. Immutable tuple collections and canonical sorting
4. Deduplication of repository relationships by relationship_id with merged provenance
5. Graph acyclicity validation across lineage and routing families
6. Serialization round-trip and permutation invariance
7. Authentic Apache cases (FLINK-1359, stratosphere#126, KAFKA-9168, FLINK-20650)
8. All 16 Phase 4D invariants preserved in production assembly
9. Evaluator isolation: zero inference, zero mutation, zero state transfer
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
    RelationshipFamily,
    RelationshipType,
    RepositoryEvolutionRelationship,
    RepositoryProvenanceRef,
    SemanticFirewall,
    SourceInstance,
    UnresolvedReference,
    compute_relationship_id,
    deserialize_repository_evolution_relationship,
    serialize_evidence_bundle,
    serialize_repository_evolution_relationship,
    validate_repository_evolution_graph,
    validate_repository_evolution_relationship,
    verify_provenance_file_digest,
)
from qualification.repository_evolution.cases import (
    GH_SOURCE,
    JIRA_SOURCE,
    STRATOSPHERE_SOURCE,
    make_flink_1359_observations,
    make_flink_1359_relationship,
    make_flink_20650_observations,
    make_flink_docker_relationship,
    make_kafka_9168_observations,
    make_kafka_rocksdb_relationship,
    make_numeric_collision_observations,
    make_stratosphere_flink_relationship,
)


@pytest.fixture
def gh_source() -> SourceInstance:
    return SourceInstance("github", "github.com/apache")


@pytest.fixture
def jira_source() -> SourceInstance:
    return SourceInstance("jira", "issues.apache.org/jira")


@pytest.fixture
def sample_obs_context(jira_source: SourceInstance) -> ObservationContext:
    return ObservationContext(
        observation_id="ctx-jira-1",
        source_instance=jira_source,
    )


@pytest.fixture
def sample_gh_context(gh_source: SourceInstance) -> ObservationContext:
    return ObservationContext(
        observation_id="ctx-gh-1",
        source_instance=gh_source,
    )


class TestEvidenceBundleBackwardCompatibility:
    """Verifies that existing EvidenceBundle contracts remain unchanged."""

    def test_default_repository_relationships_is_empty_tuple(
        self, sample_obs_context: ObservationContext
    ):
        bundle = EvidenceBundle(
            bundle_id="b-compat-1",
            bundle_version="1.0.0",
            observation_contexts=(sample_obs_context,),
        )
        assert bundle.repository_relationships == ()
        assert isinstance(bundle.repository_relationships, tuple)

    def test_assemble_evidence_bundle_without_repo_relationships(
        self, sample_obs_context: ObservationContext
    ):
        bundle = assemble_evidence_bundle(
            bundle_id="b-compat-2",
            bundle_version="1.0.0",
            jira_context=sample_obs_context,
        )
        assert bundle.repository_relationships == ()
        assert isinstance(bundle.repository_relationships, tuple)

    def test_serialize_bundle_omits_repository_relationships_when_empty(
        self, sample_obs_context: ObservationContext
    ):
        bundle = EvidenceBundle(
            bundle_id="b-compat-3",
            bundle_version="1.0.0",
            observation_contexts=(sample_obs_context,),
        )
        serialized = serialize_evidence_bundle(bundle)
        assert "repository_relationships" not in serialized

    def test_evaluator_unaffected_by_empty_or_absent_repo_relationships(
        self, sample_obs_context: ObservationContext, sample_gh_context: ObservationContext
    ):
        jira_obs = EvidenceObservation(
            entity_ref=EntityRef(sample_obs_context.source_instance, "jira_issue", "PROJ-1"),
            observation_context=sample_obs_context,
            observed_state=JiraIssueState(
                key="PROJ-1",
                source_status="Resolved",
                source_priority="Major",
                status_category="done",
                priority_band="medium",
                assignee="alice",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                updated_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
                resolved_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
            ),
        )
        gh_obs = EvidenceObservation(
            entity_ref=EntityRef(sample_gh_context.source_instance, "github_pull_request", "apache/flink/1"),
            observation_context=sample_gh_context,
            observed_state=GitHubPullRequestState(
                number=1,
                state="open",
                title="WIP commit",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            ),
        )
        mention_rel = EvidenceRelationship(
            subject_ref=jira_obs.entity_ref,
            object_ref=gh_obs.entity_ref,
            kind="mentions",
            basis="lexical_match",
            subject_observation_id=sample_obs_context.observation_id,
            object_observation_id=sample_gh_context.observation_id,
            provenance_refs=(
                ProvenanceRef(
                    source_instance=sample_obs_context.source_instance,
                    observation_id=sample_obs_context.observation_id,
                    fixture_id="fix.json",
                    record_locator="issues[0]",
                ),
            ),
        )
        bundle1 = EvidenceBundle(
            bundle_id="b-eval-1",
            bundle_version="1.0.0",
            observation_contexts=(sample_obs_context, sample_gh_context),
            observations=(jira_obs, gh_obs),
            relationships=(mention_rel,),
            repository_relationships=(),
        )
        res1 = evaluate_evidence_bundle(bundle1)
        assert len(res1.findings) == 1
        assert res1.findings[0].rule_id == "ORBIT-XB-01"

        # Now with repository evolution relationship present
        repo_rel = make_flink_1359_relationship()
        bundle2 = EvidenceBundle(
            bundle_id="b-eval-2",
            bundle_version="1.0.0",
            observation_contexts=(sample_obs_context, sample_gh_context),
            observations=(jira_obs, gh_obs),
            relationships=(mention_rel,),
            repository_relationships=(repo_rel,),
        )
        res2 = evaluate_evidence_bundle(bundle2)
        # Evaluator findings must be identical
        assert len(res2.findings) == len(res1.findings)
        assert res2.findings[0].rule_id == res1.findings[0].rule_id
        assert res2.findings[0].finding_id == res1.findings[0].finding_id


class TestEvidenceBundleProductionIntegration:
    """Verifies assemble_evidence_bundle and EvidenceBundle handling of repository evolution."""

    def test_assemble_evidence_bundle_with_repository_relationships(
        self, sample_obs_context: ObservationContext
    ):
        rel = make_flink_1359_relationship()
        bundle = assemble_evidence_bundle(
            bundle_id="b-prod-1",
            bundle_version="1.0.0",
            jira_context=sample_obs_context,
            repository_relationships=(rel,),
        )
        assert len(bundle.repository_relationships) == 1
        assert bundle.repository_relationships[0].relationship_id == rel.relationship_id

    def test_repository_relationships_is_frozen_tuple(
        self, sample_obs_context: ObservationContext
    ):
        rel = make_flink_1359_relationship()
        bundle = assemble_evidence_bundle(
            bundle_id="b-prod-2",
            bundle_version="1.0.0",
            jira_context=sample_obs_context,
            repository_relationships=(rel,),
        )
        assert isinstance(bundle.repository_relationships, tuple)
        with pytest.raises(AttributeError):
            bundle.repository_relationships.append(rel)  # type: ignore

    def test_deduplicate_repository_relationships_by_id_and_merge_provenance(
        self, sample_obs_context: ObservationContext, gh_source: SourceInstance
    ):
        p1 = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="locator-1",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        p2 = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="locator-2",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        rel1 = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
            target_repository=EntityRef(gh_source, "repository", "apache/flink"),
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(p1,),
        )
        rel2 = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
            target_repository=EntityRef(gh_source, "repository", "apache/flink"),
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(p2,),
        )
        assert rel1.relationship_id == rel2.relationship_id

        bundle = assemble_evidence_bundle(
            bundle_id="b-prod-3",
            bundle_version="1.0.0",
            jira_context=sample_obs_context,
            repository_relationships=(rel1, rel2),
        )
        assert len(bundle.repository_relationships) == 1
        deduped = bundle.repository_relationships[0]
        # Both provenance refs merged
        assert len(deduped.provenance_refs) == 2
        locators = {p.record_locator for p in deduped.provenance_refs}
        assert locators == {"locator-1", "locator-2"}

    def test_canonical_sorting_of_repository_relationships(
        self, sample_obs_context: ObservationContext
    ):
        rel_a = make_flink_1359_relationship()
        rel_b = make_stratosphere_flink_relationship()
        rel_c = make_kafka_rocksdb_relationship()
        rel_d = make_flink_docker_relationship()

        bundle = assemble_evidence_bundle(
            bundle_id="b-prod-4",
            bundle_version="1.0.0",
            jira_context=sample_obs_context,
            repository_relationships=(rel_d, rel_c, rel_b, rel_a),
        )
        expected_keys = [
            (
                r.relationship_family,
                r.relationship_type,
                r.source_repository.entity_id,
                r.target_repository.entity_id,
                r.relationship_id,
            )
            for r in (rel_d, rel_c, rel_b, rel_a)
        ]
        expected_keys.sort()

        actual_keys = [
            (
                r.relationship_family,
                r.relationship_type,
                r.source_repository.entity_id,
                r.target_repository.entity_id,
                r.relationship_id,
            )
            for r in bundle.repository_relationships
        ]
        assert actual_keys == expected_keys


class TestRepositoryEvolutionValidationIntegration:
    """Verifies that validate_evidence_bundle checks repository evolution relationships and graphs."""

    def test_validate_evidence_bundle_passes_for_valid_relationships(
        self, sample_obs_context: ObservationContext
    ):
        rel = make_flink_1359_relationship()
        bundle = assemble_evidence_bundle(
            bundle_id="b-val-1",
            bundle_version="1.0.0",
            jira_context=sample_obs_context,
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

    def test_validate_evidence_bundle_detects_lineage_graph_cycle(
        self, sample_obs_context: ObservationContext, gh_source: SourceInstance
    ):
        prov = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="base.repo.full_name",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        # Cycle: A -> B and B -> A
        rel1 = RepositoryEvolutionRelationship.create(
            relationship_family="PROJECT_LINEAGE",
            relationship_type="PREDECESSOR_SUCCESSOR",
            source_repository=EntityRef(gh_source, "repository", "org/repo-a"),
            target_repository=EntityRef(gh_source, "repository", "org/repo-b"),
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(prov,),
        )
        rel2 = RepositoryEvolutionRelationship.create(
            relationship_family="PROJECT_LINEAGE",
            relationship_type="PREDECESSOR_SUCCESSOR",
            source_repository=EntityRef(gh_source, "repository", "org/repo-b"),
            target_repository=EntityRef(gh_source, "repository", "org/repo-a"),
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(prov,),
        )
        bundle = assemble_evidence_bundle(
            bundle_id="b-val-cycle",
            bundle_version="1.0.0",
            jira_context=sample_obs_context,
            repository_relationships=(rel1, rel2),
        )
        issues = validate_evidence_bundle(bundle)
        graph_issues = [i for i in issues if i.subject_scope == "repository_evolution:graph"]
        assert len(graph_issues) >= 1
        assert "INV-GR-01" in graph_issues[0].message


class TestSerializationDeterminism:
    """Verifies JSON serialization determinism and round-trip fidelity."""

    def test_serialize_repository_evolution_relationship_roundtrip(self):
        rel = make_flink_1359_relationship()
        d = serialize_repository_evolution_relationship(rel)
        assert isinstance(d, dict)
        assert d["relationship_id"] == rel.relationship_id
        assert d["relationship_family"] == "NAVIGATION_ROUTING"
        assert d["relationship_type"] == "REDIRECT"

        deserialized = deserialize_repository_evolution_relationship(d)
        assert deserialized == rel
        assert deserialized.relationship_id == rel.relationship_id

    def test_serialize_evidence_bundle_includes_repository_relationships_when_present(
        self, sample_obs_context: ObservationContext
    ):
        rel = make_flink_1359_relationship()
        bundle = assemble_evidence_bundle(
            bundle_id="b-ser-1",
            bundle_version="1.0.0",
            jira_context=sample_obs_context,
            repository_relationships=(rel,),
        )
        serialized = serialize_evidence_bundle(bundle)
        assert "repository_relationships" in serialized
        assert len(serialized["repository_relationships"]) == 1
        assert serialized["repository_relationships"][0]["relationship_id"] == rel.relationship_id

    def test_permutation_invariance_on_bundle_serialization(
        self, sample_obs_context: ObservationContext
    ):
        rel_a = make_flink_1359_relationship()
        rel_b = make_stratosphere_flink_relationship()
        rel_c = make_kafka_rocksdb_relationship()
        rel_d = make_flink_docker_relationship()

        bundle1 = assemble_evidence_bundle(
            bundle_id="b-perm-1",
            bundle_version="1.0.0",
            jira_context=sample_obs_context,
            repository_relationships=(rel_a, rel_b, rel_c, rel_d),
        )
        bundle2 = assemble_evidence_bundle(
            bundle_id="b-perm-1",
            bundle_version="1.0.0",
            jira_context=sample_obs_context,
            repository_relationships=(rel_d, rel_c, rel_b, rel_a),
        )
        json1 = json.dumps(serialize_evidence_bundle(bundle1), sort_keys=True)
        json2 = json.dumps(serialize_evidence_bundle(bundle2), sort_keys=True)
        assert json1 == json2


class TestAuthenticApacheProductionPath:
    """Verifies all four authentic empirical cases in assembled production bundles."""

    def test_case_a_flink_1359_production_path(self):
        rel = make_flink_1359_relationship()
        jira_obs, gh_obs = make_flink_1359_observations()
        contexts = (jira_obs.observation_context, gh_obs.observation_context)

        bundle = EvidenceBundle(
            bundle_id="b-apache-a",
            bundle_version="1.0.0",
            observation_contexts=contexts,
            observations=(jira_obs, gh_obs),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # Invariants:
        assert jira_obs.entity_ref.entity_id == "FLINK-1359"
        assert gh_obs.entity_ref.entity_id == "apache/flink/254"
        assert rel.source_repository.entity_id == "apache/incubator-flink"
        assert rel.target_repository.entity_id == "apache/flink"
        assert jira_obs.observed_state.status_category == "done"

    def test_case_b_stratosphere_126_production_path(self):
        rel = make_stratosphere_flink_relationship()
        strat_obs, flink_obs = make_numeric_collision_observations()
        contexts = (strat_obs.observation_context, flink_obs.observation_context)

        bundle = EvidenceBundle(
            bundle_id="b-apache-b",
            bundle_version="1.0.0",
            observation_contexts=contexts,
            observations=(strat_obs, flink_obs),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # Invariant INV-ID-03: Lineage isolation
        assert strat_obs.entity_ref.entity_id == "stratosphere/stratosphere/126"
        assert flink_obs.entity_ref.entity_id == "apache/flink/126"
        assert strat_obs.entity_ref != flink_obs.entity_ref

    def test_case_c_kafka_9168_production_path(self):
        rel = make_kafka_rocksdb_relationship()
        kafka_obs, rocks_obs = make_kafka_9168_observations()
        contexts = (kafka_obs.observation_context, rocks_obs.observation_context)

        bundle = EvidenceBundle(
            bundle_id="b-apache-c",
            bundle_version="1.0.0",
            observation_contexts=contexts,
            observations=(kafka_obs, rocks_obs),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # Invariant INV-ST-02: External dependency state isolation
        assert kafka_obs.observed_state.status_category == "in_progress"
        assert kafka_obs.observed_state.resolved_at is None
        assert rocks_obs.observed_state.merged_at is not None

    def test_case_d_flink_20650_production_path(self):
        rel = make_flink_docker_relationship()
        flink_obs, docker_obs = make_flink_20650_observations()
        contexts = (flink_obs.observation_context, docker_obs.observation_context)

        bundle = EvidenceBundle(
            bundle_id="b-apache-d",
            bundle_version="1.0.0",
            observation_contexts=contexts,
            observations=(flink_obs, docker_obs),
            repository_relationships=(rel,),
        )
        issues = validate_evidence_bundle(bundle)
        assert len(issues) == 0

        # Invariant INV-TM-02: Ecosystem packaging temporal independence
        assert flink_obs.observed_state.resolved_at == datetime(2021, 1, 10, 15, 0, 0, tzinfo=timezone.utc)
        assert docker_obs.observed_state.merged_at == datetime(2021, 2, 15, 16, 0, 0, tzinfo=timezone.utc)

    def test_all_16_phase4d_invariants_hold_in_production_bundle(self):
        rel_a = make_flink_1359_relationship()
        rel_b = make_stratosphere_flink_relationship()
        rel_c = make_kafka_rocksdb_relationship()
        rel_d = make_flink_docker_relationship()

        bundle = EvidenceBundle(
            bundle_id="b-apache-all",
            bundle_version="1.0.0",
            observation_contexts=(),
            repository_relationships=(rel_a, rel_b, rel_c, rel_d),
        )
        # All 16 invariants verified:
        # INV-ID-01, 02, 03, 04
        for r in bundle.repository_relationships:
            assert r.source_repository.entity_kind == "repository"
            assert r.target_repository.entity_kind == "repository"
            validate_repository_evolution_relationship(r)
        # INV-EV-01, 02, 03:
        for r in bundle.repository_relationships:
            assert len(r.provenance_refs) > 0
            for p in r.provenance_refs:
                assert verify_provenance_file_digest(p)
        # INV-GR-01, 02, 03:
        validate_repository_evolution_graph(bundle.repository_relationships)
        # INV-FW-01 to 04:
        for r in bundle.repository_relationships:
            r.semantic_firewall.validate()


class TestPhase4EBHardeningGate:
    """Verifies all Phase 4E-B Hardening Gate findings:
    - Finding 1: Provenance type safety and cryptographic SHA-256 validation
    - Finding 2: Lossless provenance serialization roundtrip (observation_id & source_field_path)
    - Finding 3: Semantic conflict detection during deduplication and contradictory quality issue
    - Finding 4: Cross-provider endpoint identity isolation in graph cycle detection
    """

    def test_h1_provenance_type_safety_rejects_plain_provenance_ref(
        self, gh_source: SourceInstance
    ):
        plain_prov = ProvenanceRef(
            source_instance=gh_source,
            observation_id="obs-1",
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="issues[0]",
        )
        with pytest.raises(TypeError, match="must be an instance of RepositoryProvenanceRef"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
                target_repository=EntityRef(gh_source, "repository", "apache/flink"),
                verification_status="PROVEN",
                observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
                provenance_refs=(plain_prov,),  # type: ignore
            )

    def test_h1_provenance_rejects_empty_locator_and_empty_fixture(
        self, gh_source: SourceInstance
    ):
        # Empty fixture_id
        p_bad_fix = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="",
            record_locator="locator-1",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        with pytest.raises(ValueError, match="fixture_id must be a non-empty string"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
                target_repository=EntityRef(gh_source, "repository", "apache/flink"),
                verification_status="PROVEN",
                observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
                provenance_refs=(p_bad_fix,),
            )

        # Empty record_locator
        p_bad_loc = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        with pytest.raises(ValueError, match="record_locator must be a non-empty string"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
                target_repository=EntityRef(gh_source, "repository", "apache/flink"),
                verification_status="PROVEN",
                observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
                provenance_refs=(p_bad_loc,),
            )

    def test_h1_provenance_rejects_malformed_and_empty_string_sha256(
        self, gh_source: SourceInstance
    ):
        # Malformed SHA (non-hex, wrong length)
        for bad_sha in ["short", "G" * 64, "85EA7B74F797099BE91424B9C3E793F0F8CDCD8DDA61E8F82A1CF8468F17754B", ""]:
            p_malformed = RepositoryProvenanceRef(
                source_instance=gh_source,
                fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
                record_locator="locator-1",
                sha256_digest=bad_sha,
            )
            with pytest.raises(ValueError, match="sha256_digest must be a 64-character lowercase hex string"):
                RepositoryEvolutionRelationship.create(
                    relationship_family="NAVIGATION_ROUTING",
                    relationship_type="REDIRECT",
                    source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
                    target_repository=EntityRef(gh_source, "repository", "apache/flink"),
                    verification_status="PROVEN",
                    observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
                    provenance_refs=(p_malformed,),
                )

        # Empty-string SHA digest
        p_empty_sha = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="locator-1",
            sha256_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        with pytest.raises(ValueError, match="invalid empty-string SHA-256 digest"):
            RepositoryEvolutionRelationship.create(
                relationship_family="NAVIGATION_ROUTING",
                relationship_type="REDIRECT",
                source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
                target_repository=EntityRef(gh_source, "repository", "apache/flink"),
                verification_status="PROVEN",
                observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
                provenance_refs=(p_empty_sha,),
            )

    def test_h1_verify_provenance_file_digest_guards(self, gh_source: SourceInstance):
        # Wrong type returns False safely
        assert verify_provenance_file_digest("not-a-prov") is False  # type: ignore

        # Empty fixture_id returns False safely
        p_empty = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="",
            record_locator="loc",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        assert verify_provenance_file_digest(p_empty) is False

        # Non-existent file returns False safely
        p_missing = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="nonexistent/file.json",
            record_locator="loc",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        assert verify_provenance_file_digest(p_missing) is False

    def test_h2_lossless_provenance_roundtrip_with_optional_fields(
        self, gh_source: SourceInstance
    ):
        prov = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="base.repo.full_name",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
            observation_id="custom-obs-123",
            source_field_path="commits[0].author.name",
        )
        rel = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
            target_repository=EntityRef(gh_source, "repository", "apache/flink"),
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(prov,),
        )
        d = serialize_repository_evolution_relationship(rel)
        assert d["provenance_refs"][0]["observation_id"] == "custom-obs-123"
        assert d["provenance_refs"][0]["source_field_path"] == "commits[0].author.name"

        deserialized = deserialize_repository_evolution_relationship(d)
        assert deserialized == rel
        assert deserialized.provenance_refs[0].observation_id == "custom-obs-123"
        assert deserialized.provenance_refs[0].source_field_path == "commits[0].author.name"

    def test_h3_semantic_conflict_during_deduplication_raises_value_error(
        self, sample_obs_context: ObservationContext, gh_source: SourceInstance
    ):
        p1 = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="locator-1",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        p2 = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="locator-2",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        # Identical ID but conflicting verification_status: PROVEN vs UNVERIFIED
        rel1 = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
            target_repository=EntityRef(gh_source, "repository", "apache/flink"),
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(p1,),
        )
        rel2 = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
            target_repository=EntityRef(gh_source, "repository", "apache/flink"),
            verification_status="UNVERIFIED",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(p2,),
        )
        assert rel1.relationship_id == rel2.relationship_id

        with pytest.raises(ValueError, match="Semantic conflict detected for relationship_id"):
            assemble_evidence_bundle(
                bundle_id="b-conflict-test",
                bundle_version="1.0.0",
                jira_context=sample_obs_context,
                repository_relationships=(rel1, rel2),
            )

    def test_h3_validate_evidence_bundle_flags_conflicting_duplicates_as_contradictory(
        self, gh_source: SourceInstance
    ):
        p1 = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="locator-1",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        p2 = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="locator-2",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        # Construct directly without assemble to test validate_evidence_bundle
        rel1 = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
            target_repository=EntityRef(gh_source, "repository", "apache/flink"),
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(p1,),
        )
        rel2 = RepositoryEvolutionRelationship.create(
            relationship_family="NAVIGATION_ROUTING",
            relationship_type="REDIRECT",
            source_repository=EntityRef(gh_source, "repository", "apache/incubator-flink"),
            target_repository=EntityRef(gh_source, "repository", "apache/flink"),
            verification_status="SUPPORTED",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(p2,),
        )
        bundle = EvidenceBundle(
            bundle_id="b-contradictory-test",
            bundle_version="1.0.0",
            observation_contexts=(),
            repository_relationships=(rel1, rel2),
        )
        issues = validate_evidence_bundle(bundle)
        contradictory_issues = [i for i in issues if i.code == "contradictory"]
        assert len(contradictory_issues) == 1
        assert "Conflicting repository evolution relationships recorded" in contradictory_issues[0].message

    def test_h4_graph_identity_isolation_prevents_false_cross_provider_cycle(self):
        gh_source = SourceInstance("github", "github.com/org")
        gl_source = SourceInstance("gitlab", "gitlab.com/org")
        prov_gh = RepositoryProvenanceRef(
            source_instance=gh_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="gh",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        prov_gl = RepositoryProvenanceRef(
            source_instance=gl_source,
            fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
            record_locator="gl",
            sha256_digest="85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b",
        )
        # GitHub: repo-a -> repo-b
        rel_gh = RepositoryEvolutionRelationship.create(
            relationship_family="PROJECT_LINEAGE",
            relationship_type="PREDECESSOR_SUCCESSOR",
            source_repository=EntityRef(gh_source, "repository", "org/repo-a"),
            target_repository=EntityRef(gh_source, "repository", "org/repo-b"),
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(prov_gh,),
        )
        # GitLab: repo-b -> repo-a (same entity_ids, but DIFFERENT provider)
        rel_gl = RepositoryEvolutionRelationship.create(
            relationship_family="PROJECT_LINEAGE",
            relationship_type="PREDECESSOR_SUCCESSOR",
            source_repository=EntityRef(gl_source, "repository", "org/repo-b"),
            target_repository=EntityRef(gl_source, "repository", "org/repo-a"),
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(prov_gl,),
        )
        # This MUST NOT raise a cycle error because endpoints are distinct (github vs gitlab)
        validate_repository_evolution_graph((rel_gh, rel_gl))

        # But within the same provider, it MUST raise a cycle error
        rel_gh_cycle = RepositoryEvolutionRelationship.create(
            relationship_family="PROJECT_LINEAGE",
            relationship_type="PREDECESSOR_SUCCESSOR",
            source_repository=EntityRef(gh_source, "repository", "org/repo-b"),
            target_repository=EntityRef(gh_source, "repository", "org/repo-a"),
            verification_status="PROVEN",
            observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
            provenance_refs=(prov_gh,),
        )
        with pytest.raises(ValueError, match="INV-GR-01: Cycle detected"):
            validate_repository_evolution_graph((rel_gh, rel_gh_cycle))
