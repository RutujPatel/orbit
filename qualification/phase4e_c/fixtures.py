"""Phase 4E-C adversarial fixture builders.

Constructs the 15 authentic and adversarial integration scenarios specified in
Section 11 of the Phase 4E-C Proving Specification.

All fixtures are synthetic or grounded in authentic Phase 4D empirical cases.
Entirely qualification-only. No live provider access is performed.
No production code is modified or monkey-patched.

Adversarial Matrix (Section 11):
    C-01: Redirect + target PR                          -> No PR ownership transfer
    C-02: Redirect + target Jira issue                  -> No Jira state transfer
    C-03: Predecessor + successor PRs with same PR #    -> Distinct identities
    C-04: External dependency + merged dependency PR    -> No first-party completion
    C-05: Packaging relationship + later package merge  -> No causal inference
    C-06: Evolution + explicit Jira<->PR relationship   -> Explicit linkage remains authoritative
    C-07: Evolution + lexical similarity                -> No linkage upgrade
    C-08: Evolution + temporal proximity                -> No causal inference
    C-09: Evolution + missing provenance                -> Explicit evidence gap / fails validation
    C-10: Same repository name across providers         -> Provider/instance isolation
    C-11: Conflicting duplicate relationship IDs        -> Fail closed
    C-12: Permuted evidence ordering                    -> Byte-identical deterministic result
    C-13: Repository evolution removed                  -> No unrelated evidence mutation
    C-14: Repository evolution added                    -> No unjustified new finding (Path A == Path B)
    C-15: Malformed evolution metadata                  -> Rejected / fail closed, never evaluated
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

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
    compute_relationship_id,
)
from qualification.repository_evolution.cases import (
    GH_SOURCE,
    JIRA_SOURCE,
    ROCKSDB_SOURCE,
    DOCKER_SOURCE,
    STRATOSPHERE_SOURCE,
    make_flink_1359_relationship,
    make_flink_1359_observations,
    make_stratosphere_flink_relationship,
    make_numeric_collision_observations,
    make_kafka_rocksdb_relationship,
    make_kafka_9168_observations,
    make_flink_docker_relationship,
    make_flink_20650_observations,
)

# ── Shared instances & fixtures ──────────────────────────────────────────────

GITLAB_SOURCE = SourceInstance("gitlab", "gitlab.com/apache")

_FLINK_FIXTURE_PATH = (
    "qualification/wave3/phase3a_acquisition/raw/FLINK/apache__flink/pr_254.json"
)
_FLINK_FIXTURE_SHA = (
    "85ea7b74f797099be91424b9c3e793f0f8cdcd8dda61e8f82a1cf8468f17754b"
)

# ── Builders for C-01 .. C-15 ────────────────────────────────────────────────

def build_case_c01() -> dict:
    """C-01: Redirect + target PR.

    Repository incubator-flink redirects to flink. PR #254 belongs to flink.
    Invariant: PR ownership must NOT transfer to incubator-flink.
    """
    rel = make_flink_1359_relationship()
    jira_obs, gh_obs = make_flink_1359_observations()
    return {
        "case_id": "C-01",
        "description": "Redirect + target PR: no PR ownership transfer",
        "gate": "4E-C-02",
        "repo_rel": rel,
        "jira_obs": jira_obs,
        "gh_obs": gh_obs,
        "jira_ctx": jira_obs.observation_context,
        "gh_ctx": gh_obs.observation_context,
    }


def build_case_c02() -> dict:
    """C-02: Redirect + target Jira issue.

    Repository incubator-flink redirects to flink. Issue FLINK-1359 is resolved.
    Invariant: Jira issue state must NOT transfer to incubator-flink.
    """
    rel = make_flink_1359_relationship()
    jira_obs, gh_obs = make_flink_1359_observations()
    return {
        "case_id": "C-02",
        "description": "Redirect + target Jira issue: no Jira state transfer",
        "gate": "4E-C-03",
        "repo_rel": rel,
        "jira_obs": jira_obs,
        "gh_obs": gh_obs,
        "jira_ctx": jira_obs.observation_context,
        "gh_ctx": gh_obs.observation_context,
    }


def build_case_c03() -> dict:
    """C-03: Predecessor + successor PRs with same PR number.

    stratosphere/stratosphere#126 and apache/flink#126 share PR #126.
    Invariant: Entities remain distinct; zero identity collapse.
    """
    rel = make_stratosphere_flink_relationship()
    strat_obs, flink_obs = make_numeric_collision_observations()
    return {
        "case_id": "C-03",
        "description": "Predecessor + successor PRs with same PR number: distinct identities",
        "gate": "4E-C-03",
        "repo_rel": rel,
        "strat_obs": strat_obs,
        "flink_obs": flink_obs,
        "strat_ctx": strat_obs.observation_context,
        "flink_ctx": flink_obs.observation_context,
    }


def build_case_c04() -> dict:
    """C-04: External dependency + merged dependency PR.

    apache/kafka depends on facebook/rocksdb. RocksDB PR #2283 is merged.
    KAFKA-9168 is In Progress.
    Invariant: Merged dependency PR does not complete first-party issue.
    """
    rel = make_kafka_rocksdb_relationship()
    kafka_obs, rocks_obs = make_kafka_9168_observations()
    return {
        "case_id": "C-04",
        "description": "External dependency + merged dependency PR: no first-party completion",
        "gate": "4E-C-03",
        "repo_rel": rel,
        "kafka_obs": kafka_obs,
        "rocks_obs": rocks_obs,
        "jira_ctx": kafka_obs.observation_context,
        "gh_ctx": rocks_obs.observation_context,
    }


def build_case_c05() -> dict:
    """C-05: Packaging relationship + later package merge.

    apache/flink packages into docker-library/official-images.
    Flink issue resolved Jan 10, Docker PR merged Feb 15 (36 days later).
    Invariant: Proximity/later merge does not imply causal defect or blame.
    """
    rel = make_flink_docker_relationship()
    flink_obs, docker_obs = make_flink_20650_observations()
    return {
        "case_id": "C-05",
        "description": "Packaging relationship + later package merge: no causal inference",
        "gate": "4E-C-04",
        "repo_rel": rel,
        "flink_obs": flink_obs,
        "docker_obs": docker_obs,
        "jira_ctx": flink_obs.observation_context,
        "gh_ctx": docker_obs.observation_context,
    }


def build_case_c06() -> dict:
    """C-06: Evolution + explicit Jira<->PR relationship.

    An explicit relationship Jira issue <-> PR exists. Repo evolution also exists.
    Invariant: Explicit linkage remains authoritative and unmodified.
    """
    rel = make_flink_1359_relationship()
    jira_obs, gh_obs = make_flink_1359_observations()
    explicit_rel = EvidenceRelationship(
        subject_ref=jira_obs.entity_ref,
        object_ref=gh_obs.entity_ref,
        kind="explicit_link",
        basis="explicit_metadata",
        subject_observation_id=jira_obs.observation_context.observation_id,
        object_observation_id=gh_obs.observation_context.observation_id,
        provenance_refs=(
            ProvenanceRef(
                source_instance=GH_SOURCE,
                observation_id=gh_obs.observation_context.observation_id,
                fixture_id=_FLINK_FIXTURE_PATH,
                record_locator="pull_request[254].issue_url",
            ),
        ),
    )
    return {
        "case_id": "C-06",
        "description": "Evolution + explicit Jira<->PR relationship: explicit linkage authoritative",
        "gate": "4E-C-02",
        "repo_rel": rel,
        "jira_obs": jira_obs,
        "gh_obs": gh_obs,
        "explicit_rel": explicit_rel,
        "jira_ctx": jira_obs.observation_context,
        "gh_ctx": gh_obs.observation_context,
    }


def build_case_c07() -> dict:
    """C-07: Evolution + lexical similarity.

    Jira issue has a lexical mention of a PR, and repo evolution exists.
    Invariant: Evolution does not upgrade lexical mention to explicit link or PROVEN.
    """
    rel = make_flink_1359_relationship()
    jira_obs, gh_obs = make_flink_1359_observations()
    mention_rel = EvidenceRelationship(
        subject_ref=jira_obs.entity_ref,
        object_ref=gh_obs.entity_ref,
        kind="mentions",
        basis="lexical_match",
        subject_observation_id=jira_obs.observation_context.observation_id,
        object_observation_id=gh_obs.observation_context.observation_id,
        provenance_refs=(
            ProvenanceRef(
                source_instance=GH_SOURCE,
                observation_id=gh_obs.observation_context.observation_id,
                fixture_id=_FLINK_FIXTURE_PATH,
                record_locator="pull_request[254].body",
            ),
        ),
    )
    return {
        "case_id": "C-07",
        "description": "Evolution + lexical similarity: no linkage upgrade",
        "gate": "4E-C-02",
        "repo_rel": rel,
        "jira_obs": jira_obs,
        "gh_obs": gh_obs,
        "mention_rel": mention_rel,
        "jira_ctx": jira_obs.observation_context,
        "gh_ctx": gh_obs.observation_context,
    }


def build_case_c08() -> dict:
    """C-08: Evolution + temporal proximity.

    Two events occur in temporally proximate windows in related repositories.
    Invariant: Proximity does not establish causality.
    """
    rel = make_flink_docker_relationship()
    flink_obs, docker_obs = make_flink_20650_observations()
    return {
        "case_id": "C-08",
        "description": "Evolution + temporal proximity: no causal inference",
        "gate": "4E-C-04",
        "repo_rel": rel,
        "flink_obs": flink_obs,
        "docker_obs": docker_obs,
        "jira_ctx": flink_obs.observation_context,
        "gh_ctx": docker_obs.observation_context,
    }


def build_case_c09() -> dict:
    """C-09: Evolution + missing provenance.

    A repository evolution relationship is constructed with an empty or invalid
    provenance reference.
    Invariant: Fails validation closed; rejected.
    """
    src_repo = EntityRef(GH_SOURCE, "repository", "apache/incubator-flink")
    tgt_repo = EntityRef(GH_SOURCE, "repository", "apache/flink")
    invalid_prov = RepositoryProvenanceRef(
        source_instance=GH_SOURCE,
        fixture_id="",
        record_locator="",
        sha256_digest="0" * 64,
    )
    return {
        "case_id": "C-09",
        "description": "Evolution + missing provenance: explicit evidence gap, fails closed",
        "gate": "4E-C-01",
        "source_repo": src_repo,
        "target_repo": tgt_repo,
        "invalid_prov": invalid_prov,
    }


def build_case_c10() -> dict:
    """C-10: Same repository name across providers.

    github.com/apache/flink vs gitlab.com/apache/flink.
    Invariant: Scoped by composite key; no false cross-provider cycle or collision.
    """
    gh_repo = EntityRef(GH_SOURCE, "repository", "apache/flink")
    gl_repo = EntityRef(GITLAB_SOURCE, "repository", "apache/flink")
    prov_gh = RepositoryProvenanceRef(
        source_instance=GH_SOURCE,
        fixture_id=_FLINK_FIXTURE_PATH,
        record_locator="base.repo.full_name",
        sha256_digest=_FLINK_FIXTURE_SHA,
    )
    prov_gl = RepositoryProvenanceRef(
        source_instance=GITLAB_SOURCE,
        fixture_id=_FLINK_FIXTURE_PATH,
        record_locator="base.repo.full_name",
        sha256_digest=_FLINK_FIXTURE_SHA,
    )
    rel1 = RepositoryEvolutionRelationship.create(
        relationship_family="NAVIGATION_ROUTING",
        relationship_type="REDIRECT",
        source_repository=gh_repo,
        target_repository=gl_repo,
        verification_status="PROVEN",
        observed_at=datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc),
        provenance_refs=(prov_gh,),
        family_payload={"http_status_code": 301, "underlying_vcs_id_matched": True},
    )
    return {
        "case_id": "C-10",
        "description": "Same repository name across providers: provider/instance isolation",
        "gate": "4E-C-02",
        "gh_repo": gh_repo,
        "gl_repo": gl_repo,
        "rel": rel1,
    }


def build_case_c11() -> dict:
    """C-11: Conflicting duplicate relationship IDs.

    Two relationships with identical ID but conflicting semantic fields.
    Invariant: assemble_evidence_bundle fails closed with ValueError.
    """
    rel1 = make_flink_1359_relationship()
    rel2_conflicting = RepositoryEvolutionRelationship.create(
        relationship_family="NAVIGATION_ROUTING",
        relationship_type="REDIRECT",
        source_repository=rel1.source_repository,
        target_repository=rel1.target_repository,
        verification_status="SUPPORTED",  # Conflict: SUPPORTED vs PROVEN
        observed_at=rel1.observed_at,
        provenance_refs=rel1.provenance_refs,
        family_payload={"http_status_code": 302},  # Conflict: 302 vs 301
    )
    return {
        "case_id": "C-11",
        "description": "Conflicting duplicate relationship IDs: fail closed",
        "gate": "4E-C-01",
        "rel1": rel1,
        "rel2_conflicting": rel2_conflicting,
    }


def build_case_c12() -> dict:
    """C-12: Permuted evidence ordering.

    Evidence observations, contexts, and repo-relationships supplied in
    different permutations.
    Invariant: Assembles into byte-identical canonically ordered EvidenceBundle.
    """
    rel = make_flink_1359_relationship()
    jira_obs, gh_obs = make_flink_1359_observations()
    return {
        "case_id": "C-12",
        "description": "Permuted evidence ordering: byte-identical deterministic result",
        "gate": "4E-C-01",
        "repo_rel": rel,
        "jira_obs": jira_obs,
        "gh_obs": gh_obs,
        "jira_ctx": jira_obs.observation_context,
        "gh_ctx": gh_obs.observation_context,
    }


def build_case_c13() -> dict:
    """C-13: Repository evolution removed.

    Bundle A with repo evolution vs Bundle B without repo evolution.
    Invariant: Ordinary observations, relationships, alignments are bit-for-bit identical.
    """
    rel = make_flink_1359_relationship()
    jira_obs, gh_obs = make_flink_1359_observations()
    return {
        "case_id": "C-13",
        "description": "Repository evolution removed: no unrelated evidence mutation",
        "gate": "4E-C-05",
        "repo_rel": rel,
        "jira_obs": jira_obs,
        "gh_obs": gh_obs,
        "jira_ctx": jira_obs.observation_context,
        "gh_ctx": gh_obs.observation_context,
    }


def build_case_c14() -> dict:
    """C-14: Repository evolution added.

    Evaluating bundle without repo-rel (Path A) vs bundle with repo-rel (Path B).
    Invariant: evaluate_evidence_bundle produces identical findings (Path A == Path B).
    """
    rel = make_flink_1359_relationship()
    jira_obs, gh_obs = make_flink_1359_observations()
    # Add a mention relationship so candidate pair is evaluated
    mention_rel = EvidenceRelationship(
        subject_ref=jira_obs.entity_ref,
        object_ref=gh_obs.entity_ref,
        kind="mentions",
        basis="lexical_match",
        subject_observation_id=jira_obs.observation_context.observation_id,
        object_observation_id=gh_obs.observation_context.observation_id,
        provenance_refs=(
            ProvenanceRef(
                source_instance=GH_SOURCE,
                observation_id=gh_obs.observation_context.observation_id,
                fixture_id=_FLINK_FIXTURE_PATH,
                record_locator="pull_request[254].body",
            ),
        ),
    )
    return {
        "case_id": "C-14",
        "description": "Repository evolution added: no unjustified new finding (Path A == Path B)",
        "gate": "4E-C-05",
        "repo_rel": rel,
        "jira_obs": jira_obs,
        "gh_obs": gh_obs,
        "mention_rel": mention_rel,
        "jira_ctx": jira_obs.observation_context,
        "gh_ctx": gh_obs.observation_context,
    }


def build_case_c15() -> dict:
    """C-15: Malformed evolution metadata.

    Attempting to create or validate a relationship with malformed directionality,
    transitivity, or empty payload fields.
    Invariant: Fails validation; rejected, never evaluated.
    """
    return {
        "case_id": "C-15",
        "description": "Malformed evolution metadata: rejected/quarantined, never evaluated",
        "gate": "4E-C-01",
    }


# ── Manifest ─────────────────────────────────────────────────────────────────

ADVERSARIAL_CASES: list[dict] = [
    {
        "case_id": "C-01",
        "gate": "4E-C-02",
        "theme": "Linkage Isolation",
        "condition": "Redirect + target PR",
        "required_behavior": "No PR ownership transfer",
        "builder": "build_case_c01",
    },
    {
        "case_id": "C-02",
        "gate": "4E-C-03",
        "theme": "State Isolation",
        "condition": "Redirect + target Jira issue",
        "required_behavior": "No Jira state transfer",
        "builder": "build_case_c02",
    },
    {
        "case_id": "C-03",
        "gate": "4E-C-03",
        "theme": "State Isolation",
        "condition": "Predecessor + successor PRs with same PR number",
        "required_behavior": "Distinct identities",
        "builder": "build_case_c03",
    },
    {
        "case_id": "C-04",
        "gate": "4E-C-03",
        "theme": "State Isolation",
        "condition": "External dependency + merged dependency PR",
        "required_behavior": "No first-party completion",
        "builder": "build_case_c04",
    },
    {
        "case_id": "C-05",
        "gate": "4E-C-04",
        "theme": "Temporal Isolation",
        "condition": "Packaging relationship + later package merge",
        "required_behavior": "No causal inference",
        "builder": "build_case_c05",
    },
    {
        "case_id": "C-06",
        "gate": "4E-C-02",
        "theme": "Linkage Isolation",
        "condition": "Evolution + explicit Jira<->PR relationship",
        "required_behavior": "Explicit linkage remains authoritative",
        "builder": "build_case_c06",
    },
    {
        "case_id": "C-07",
        "gate": "4E-C-02",
        "theme": "Linkage Isolation",
        "condition": "Evolution + lexical similarity",
        "required_behavior": "No linkage upgrade",
        "builder": "build_case_c07",
    },
    {
        "case_id": "C-08",
        "gate": "4E-C-04",
        "theme": "Temporal Isolation",
        "condition": "Evolution + temporal proximity",
        "required_behavior": "No causal inference",
        "builder": "build_case_c08",
    },
    {
        "case_id": "C-09",
        "gate": "4E-C-01",
        "theme": "Evidence Assembly Integrity",
        "condition": "Evolution + missing provenance",
        "required_behavior": "Explicit evidence gap",
        "builder": "build_case_c09",
    },
    {
        "case_id": "C-10",
        "gate": "4E-C-02",
        "theme": "Linkage Isolation",
        "condition": "Same repository name across providers",
        "required_behavior": "Provider/instance isolation",
        "builder": "build_case_c10",
    },
    {
        "case_id": "C-11",
        "gate": "4E-C-01",
        "theme": "Evidence Assembly Integrity",
        "condition": "Conflicting duplicate relationship IDs",
        "required_behavior": "Fail closed",
        "builder": "build_case_c11",
    },
    {
        "case_id": "C-12",
        "gate": "4E-C-01",
        "theme": "Evidence Assembly Integrity",
        "condition": "Permuted evidence ordering",
        "required_behavior": "Byte-identical deterministic result",
        "builder": "build_case_c12",
    },
    {
        "case_id": "C-13",
        "gate": "4E-C-05",
        "theme": "Evaluation Isolation",
        "condition": "Repository evolution removed",
        "required_behavior": "No unrelated evidence mutation",
        "builder": "build_case_c13",
    },
    {
        "case_id": "C-14",
        "gate": "4E-C-05",
        "theme": "Evaluation Isolation",
        "condition": "Repository evolution added",
        "required_behavior": "No unjustified new finding",
        "builder": "build_case_c14",
    },
    {
        "case_id": "C-15",
        "gate": "4E-C-01",
        "theme": "Evidence Assembly Integrity",
        "condition": "Malformed evolution metadata",
        "required_behavior": "Rejected/quarantined, never evaluated",
        "builder": "build_case_c15",
    },
]
