"""Authentic empirical cases and adversarial scenarios for Phase 4D qualification.

Authoritative references:
    qualification/wave3/phase4b_repository_identity/repository_identity_cases.json
    qualification/wave3/phase4c_repository_evolution_schema/phase4c_adversarial_tests.md
"""

from __future__ import annotations

from datetime import datetime, timezone

from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceObservation,
    EvidenceRelationship,
    GitHubPullRequestState,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    SourceInstance,
)
from qualification.repository_evolution.schema import (
    RepositoryEvolutionRelationship,
    RepositoryProvenanceRef,
    SemanticFirewall,
)

# ── Shared Source Instances ──────────────────────────────────────────────────

GH_SOURCE = SourceInstance("github", "github.com/apache")
JIRA_SOURCE = SourceInstance("jira", "issues.apache.org")
ROCKSDB_SOURCE = SourceInstance("github", "github.com/facebook")
DOCKER_SOURCE = SourceInstance("github", "github.com/docker-library")
STRATOSPHERE_SOURCE = SourceInstance("github", "github.com/stratosphere")


# ── Case A: FLINK-1359 (Navigation Routing / Redirect) ───────────────────────

def make_flink_1359_relationship() -> RepositoryEvolutionRelationship:
    """Authentic redirect relationship from incubator-flink to flink."""
    src_repo = EntityRef(GH_SOURCE, "repository", "apache/incubator-flink")
    tgt_repo = EntityRef(GH_SOURCE, "repository", "apache/flink")
    prov = RepositoryProvenanceRef(
        source_instance=GH_SOURCE,
        fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
        record_locator="base.repo.full_name",
        sha256_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    return RepositoryEvolutionRelationship.create(
        relationship_family="NAVIGATION_ROUTING",
        relationship_type="REDIRECT",
        source_repository=src_repo,
        target_repository=tgt_repo,
        verification_status="PROVEN",
        observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
        provenance_refs=(prov,),
        family_payload={"http_status_code": 301, "underlying_vcs_id_matched": True},
    )


def make_flink_1359_observations() -> tuple[EvidenceObservation, EvidenceObservation]:
    """Observations for FLINK-1359 Jira issue and redirected GitHub PR #254."""
    jira_ref = EntityRef(JIRA_SOURCE, "work_item", "FLINK-1359")
    gh_ref = EntityRef(GH_SOURCE, "code_change", "apache/flink/254")

    jira_obs = EvidenceObservation(
        entity_ref=jira_ref,
        observation_context=ObservationContext(
            observation_id="obs-jira-flink-1359",
            source_instance=JIRA_SOURCE,
        ),
        observed_state=JiraIssueState(
            key="FLINK-1359",
            source_status="Resolved",
            source_priority="Major",
            status_category="done",
            priority_band="medium",
            assignee=None,
            created_at=datetime(2014, 12, 10, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2014, 12, 15, 14, 0, 0, tzinfo=timezone.utc),
            resolved_at=datetime(2014, 12, 15, 14, 0, 0, tzinfo=timezone.utc),
        ),
        provenance_refs=(
            ProvenanceRef(
                source_instance=JIRA_SOURCE,
                observation_id="obs-jira-flink-1359",
                fixture_id="fixtures/jira/clean/flink_issues.json",
                record_locator="issues[FLINK-1359]",
            ),
        ),
    )

    gh_obs = EvidenceObservation(
        entity_ref=gh_ref,
        observation_context=ObservationContext(
            observation_id="obs-gh-flink-pr-254",
            source_instance=GH_SOURCE,
        ),
        observed_state=GitHubPullRequestState(
            number=254,
            title="FLINK-1359 Pull Request",
            state="closed",
            created_at=datetime(2014, 12, 11, 8, 0, 0, tzinfo=timezone.utc),
            merged_at=datetime(2014, 12, 15, 12, 0, 0, tzinfo=timezone.utc),
        ),
        provenance_refs=(
            ProvenanceRef(
                source_instance=GH_SOURCE,
                observation_id="obs-gh-flink-pr-254",
                fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json",
                record_locator="pull_request[254]",
            ),
        ),
    )
    return jira_obs, gh_obs


# ── Case B: stratosphere#126 (Predecessor/Lineage Isolation) ─────────────────

def make_stratosphere_flink_relationship() -> RepositoryEvolutionRelationship:
    """Authentic project lineage relationship: stratosphere/stratosphere -> apache/flink."""
    src_repo = EntityRef(STRATOSPHERE_SOURCE, "repository", "stratosphere/stratosphere")
    tgt_repo = EntityRef(GH_SOURCE, "repository", "apache/flink")
    prov = RepositoryProvenanceRef(
        source_instance=GH_SOURCE,
        fixture_id="qualification/wave3/phase4b_repository_identity/governance_donation.json",
        record_locator="asf_donation_resolution",
        sha256_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    return RepositoryEvolutionRelationship.create(
        relationship_family="PROJECT_LINEAGE",
        relationship_type="PREDECESSOR_SUCCESSOR",
        source_repository=src_repo,
        target_repository=tgt_repo,
        verification_status="PROVEN",
        observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
        provenance_refs=(prov,),
        family_payload={"governance_event": "ASF_INCUBATOR_DONATION"},
    )


def make_numeric_collision_observations() -> tuple[EvidenceObservation, EvidenceObservation]:
    """Two completely distinct PRs sharing the identical numeric PR# 126 in distinct repos."""
    strat_ref = EntityRef(STRATOSPHERE_SOURCE, "code_change", "stratosphere/stratosphere/126")
    flink_ref = EntityRef(GH_SOURCE, "code_change", "apache/flink/126")

    strat_obs = EvidenceObservation(
        entity_ref=strat_ref,
        observation_context=ObservationContext(
            observation_id="obs-gh-stratosphere-pr-126",
            source_instance=STRATOSPHERE_SOURCE,
        ),
        observed_state=GitHubPullRequestState(
            number=126,
            title="Predecessor PR 126 in Stratosphere",
            state="closed",
            created_at=datetime(2014, 3, 1, 10, 0, 0, tzinfo=timezone.utc),
            merged_at=datetime(2014, 3, 5, 12, 0, 0, tzinfo=timezone.utc),
        ),
        provenance_refs=(
            ProvenanceRef(
                source_instance=STRATOSPHERE_SOURCE,
                observation_id="obs-gh-stratosphere-pr-126",
                fixture_id="fixtures/github/stratosphere/pr_126.json",
                record_locator="pull_request[126]",
            ),
        ),
    )

    flink_obs = EvidenceObservation(
        entity_ref=flink_ref,
        observation_context=ObservationContext(
            observation_id="obs-gh-flink-pr-126",
            source_instance=GH_SOURCE,
        ),
        observed_state=GitHubPullRequestState(
            number=126,
            title="Successor PR 126 in Apache Flink",
            state="closed",
            created_at=datetime(2014, 11, 20, 10, 0, 0, tzinfo=timezone.utc),
            merged_at=datetime(2014, 11, 22, 15, 0, 0, tzinfo=timezone.utc),
        ),
        provenance_refs=(
            ProvenanceRef(
                source_instance=GH_SOURCE,
                observation_id="obs-gh-flink-pr-126",
                fixture_id="qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_126.json",
                record_locator="pull_request[126]",
            ),
        ),
    )
    return strat_obs, flink_obs


# ── Case C: KAFKA-9168 (External Dependency Isolation) ───────────────────────

def make_kafka_rocksdb_relationship() -> RepositoryEvolutionRelationship:
    """Authentic external dependency relationship: apache/kafka -> facebook/rocksdb."""
    src_repo = EntityRef(GH_SOURCE, "repository", "apache/kafka")
    tgt_repo = EntityRef(ROCKSDB_SOURCE, "repository", "facebook/rocksdb")
    prov = RepositoryProvenanceRef(
        source_instance=GH_SOURCE,
        fixture_id="qualification/wave3/phase3a_acquisition/raw/KAFKA/facebook__rocksdb/pr_2283.json",
        record_locator="pom.xml:dependencies",
        sha256_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    return RepositoryEvolutionRelationship.create(
        relationship_family="ECOSYSTEM_DEPENDENCY",
        relationship_type="EXTERNAL_DEPENDENCY",
        source_repository=src_repo,
        target_repository=tgt_repo,
        verification_status="PROVEN",
        observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
        provenance_refs=(prov,),
        family_payload={"dependency_scope": "runtime"},
    )


def make_kafka_9168_observations() -> tuple[EvidenceObservation, EvidenceObservation]:
    """Kafka issue (In Progress) and merged external RocksDB PR #2283."""
    kafka_ref = EntityRef(JIRA_SOURCE, "work_item", "KAFKA-9168")
    rocks_ref = EntityRef(ROCKSDB_SOURCE, "code_change", "facebook/rocksdb/2283")

    kafka_obs = EvidenceObservation(
        entity_ref=kafka_ref,
        observation_context=ObservationContext(
            observation_id="obs-jira-kafka-9168",
            source_instance=JIRA_SOURCE,
        ),
        observed_state=JiraIssueState(
            key="KAFKA-9168",
            source_status="In Progress",
            source_priority="Major",
            status_category="in_progress",
            priority_band="medium",
            assignee=None,
            created_at=datetime(2019, 11, 10, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2019, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
            resolved_at=None,
        ),
        provenance_refs=(
            ProvenanceRef(
                source_instance=JIRA_SOURCE,
                observation_id="obs-jira-kafka-9168",
                fixture_id="fixtures/jira/clean/kafka_issues.json",
                record_locator="issues[KAFKA-9168]",
            ),
        ),
    )

    rocks_obs = EvidenceObservation(
        entity_ref=rocks_ref,
        observation_context=ObservationContext(
            observation_id="obs-gh-rocksdb-pr-2283",
            source_instance=ROCKSDB_SOURCE,
        ),
        observed_state=GitHubPullRequestState(
            number=2283,
            title="RocksDB bugfix PR 2283",
            state="closed",
            created_at=datetime(2017, 5, 10, 8, 0, 0, tzinfo=timezone.utc),
            merged_at=datetime(2017, 5, 12, 14, 0, 0, tzinfo=timezone.utc),
        ),
        provenance_refs=(
            ProvenanceRef(
                source_instance=ROCKSDB_SOURCE,
                observation_id="obs-gh-rocksdb-pr-2283",
                fixture_id="qualification/wave3/phase3a_acquisition/raw/KAFKA/facebook__rocksdb/pr_2283.json",
                record_locator="pull_request[2283]",
            ),
        ),
    )
    return kafka_obs, rocks_obs


# ── Case D: FLINK-20650 (Ecosystem Packaging / Temporal Independence) ────────

def make_flink_docker_relationship() -> RepositoryEvolutionRelationship:
    """Authentic ecosystem packaging relationship: apache/flink -> docker-library/official-images."""
    src_repo = EntityRef(GH_SOURCE, "repository", "apache/flink")
    tgt_repo = EntityRef(DOCKER_SOURCE, "repository", "docker-library/official-images")
    prov = RepositoryProvenanceRef(
        source_instance=GH_SOURCE,
        fixture_id="qualification/wave3/phase4b_repository_identity/docker_ecosystem.json",
        record_locator="dockerhub:official_images:flink",
        sha256_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    return RepositoryEvolutionRelationship.create(
        relationship_family="ECOSYSTEM_DEPENDENCY",
        relationship_type="ECOSYSTEM_PACKAGING",
        source_repository=src_repo,
        target_repository=tgt_repo,
        verification_status="SUPPORTED",
        observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
        provenance_refs=(prov,),
        family_payload={"dependency_scope": "docker_image"},
    )


def make_flink_20650_observations() -> tuple[EvidenceObservation, EvidenceObservation]:
    """Flink issue resolved on Jan 10; packaging PR merged 36 days later on Feb 15."""
    flink_ref = EntityRef(JIRA_SOURCE, "work_item", "FLINK-20650")
    docker_ref = EntityRef(DOCKER_SOURCE, "code_change", "docker-library/official-images/9249")

    flink_obs = EvidenceObservation(
        entity_ref=flink_ref,
        observation_context=ObservationContext(
            observation_id="obs-jira-flink-20650",
            source_instance=JIRA_SOURCE,
        ),
        observed_state=JiraIssueState(
            key="FLINK-20650",
            source_status="Resolved",
            source_priority="Major",
            status_category="done",
            priority_band="medium",
            assignee=None,
            created_at=datetime(2020, 12, 17, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2021, 1, 10, 15, 0, 0, tzinfo=timezone.utc),
            resolved_at=datetime(2021, 1, 10, 15, 0, 0, tzinfo=timezone.utc),
        ),
        provenance_refs=(
            ProvenanceRef(
                source_instance=JIRA_SOURCE,
                observation_id="obs-jira-flink-20650",
                fixture_id="fixtures/jira/clean/flink_issues.json",
                record_locator="issues[FLINK-20650]",
            ),
        ),
    )

    docker_obs = EvidenceObservation(
        entity_ref=docker_ref,
        observation_context=ObservationContext(
            observation_id="obs-gh-docker-pr-9249",
            source_instance=DOCKER_SOURCE,
        ),
        observed_state=GitHubPullRequestState(
            number=9249,
            title="Update Flink 1.12 Docker image",
            state="closed",
            created_at=datetime(2021, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            merged_at=datetime(2021, 2, 15, 16, 0, 0, tzinfo=timezone.utc),  # 36 days post-resolution
        ),
        provenance_refs=(
            ProvenanceRef(
                source_instance=DOCKER_SOURCE,
                observation_id="obs-gh-docker-pr-9249",
                fixture_id="fixtures/github/docker/official_images_9249.json",
                record_locator="pull_request[9249]",
            ),
        ),
    )
    return flink_obs, docker_obs
