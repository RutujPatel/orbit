"""Canonical EvidenceBundle builder for real Apache Jira and GitHub evidence.

Loads verified real artifacts from qualification/wave3/apache_real/,
adapts them into canonical WorkItemState, CodeChangeState, and
CrossSystemStateAlignment structures, and returns an assembled EvidenceBundle
conforming to ORBIT contracts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shadow_orbit.evidence_types import (
    CodeChangeState,
    CrossSystemStateAlignment,
    EntityRef,
    EvidenceBundle,
    EvidenceObservation,
    EvidenceRelationship,
    ObservationContext,
    ProvenanceRef,
    SourceInstance,
    WorkItemState,
)

from .apache_alignment_adapter import build_cross_system_alignment
from .apache_github_adapter import (
    APACHE_GITHUB_SOURCE,
    adapt_apache_github_commit,
    adapt_apache_github_pr,
)
from .apache_jira_adapter import (
    APACHE_JIRA_SOURCE,
    adapt_apache_jira_issue,
    is_valid_apache_jira_key,
)

DEFAULT_CORPUS_DIR = (
    Path(__file__).resolve().parents[1]
)  # qualification/wave3/apache_real


def load_apache_raw_fixtures(
    corpus_dir: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load all 31 verified raw JSON files from the Apache real corpus.

    Returns
    -------
    raw_files:
        Dictionary mapping relative file paths to loaded JSON objects.
    fixtures_by_id:
        Dictionary mapping full fixture_id strings to in-memory collection dictionaries
        structured for deterministic provenance dereferencing.
    """
    base = Path(corpus_dir or DEFAULT_CORPUS_DIR)
    manifest_path = base / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    raw_files: dict[str, Any] = {}
    fixtures_by_id: dict[str, Any] = {}

    # 1. Jira issues
    for item in manifest.get("records", {}).get("jira_issues", []):
        rel_path = item["file"]
        full_path = base / rel_path
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_files[rel_path] = data
        fixture_id = f"qualification/wave3/apache_real/{rel_path}"
        fixtures_by_id[fixture_id] = {"work_items": [data]}

    # 2. GitHub PRs, commits, reviews
    for item in manifest.get("records", {}).get("github_pull_requests", []):
        rel_path = item["file"]
        full_path = base / rel_path
        with open(full_path, "r", encoding="utf-8") as f:
            pr_data = json.load(f)
        raw_files[rel_path] = pr_data
        fixture_id = f"qualification/wave3/apache_real/{rel_path}"
        fixtures_by_id[fixture_id] = {"pull_requests": [pr_data]}

        # Commits
        commits_rel = rel_path.replace(".json", "_commits.json")
        commits_full = base / commits_rel
        if commits_full.exists():
            with open(commits_full, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            raw_files[commits_rel] = c_data
            c_fid = f"qualification/wave3/apache_real/{commits_rel}"
            fixtures_by_id[c_fid] = {"commits": c_data}

        # Reviews
        reviews_rel = rel_path.replace(".json", "_reviews.json")
        reviews_full = base / reviews_rel
        if reviews_full.exists():
            with open(reviews_full, "r", encoding="utf-8") as f:
                r_data = json.load(f)
            raw_files[reviews_rel] = r_data
            r_fid = f"qualification/wave3/apache_real/{reviews_rel}"
            fixtures_by_id[r_fid] = {"reviews": r_data}

    # 3. Negative controls
    for item in manifest.get("records", {}).get("negative_controls", []):
        rel_path = item["file"]
        full_path = base / rel_path
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_files[rel_path] = data
        fixture_id = f"qualification/wave3/apache_real/{rel_path}"
        if "jira" in rel_path:
            fixtures_by_id[fixture_id] = {"work_items": [data]}
        else:
            fixtures_by_id[fixture_id] = {"pull_requests": [data]}

    return raw_files, fixtures_by_id


def build_apache_evidence_bundle(
    corpus_dir: str | Path | None = None,
    bundle_id: str = "orbit_wave3_apache_canonical_bundle",
) -> tuple[EvidenceBundle, dict[str, Any]]:
    """Assemble a canonical EvidenceBundle from the verified Apache real corpus.

    Returns
    -------
    bundle:
        The assembled and sorted EvidenceBundle.
    fixtures_by_id:
        Dictionary of in-memory fixture collections for active provenance dereferencing.
    """
    base = Path(corpus_dir or DEFAULT_CORPUS_DIR)
    raw_files, fixtures_by_id = load_apache_raw_fixtures(base)

    cutoff_dt = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)
    jira_context = ObservationContext(
        observation_id="obs_apache_jira_real_001",
        source_instance=APACHE_JIRA_SOURCE,
        source_cutoff_at=cutoff_dt,
        coverage_note="Verified real Apache Jira target issues",
    )
    github_context = ObservationContext(
        observation_id="obs_apache_github_real_001",
        source_instance=APACHE_GITHUB_SOURCE,
        source_cutoff_at=cutoff_dt,
        coverage_note="Verified real Apache GitHub pull requests, commits, and reviews",
    )

    observations: list[EvidenceObservation] = []
    jira_obs_by_key: dict[str, EvidenceObservation] = {}
    pr_obs_by_key: dict[str, EvidenceObservation] = {}
    commit_obs_by_sha: dict[str, EvidenceObservation] = {}

    # 1. Adapt Target Jira Issues
    jira_keys = [
        "PARQUET-2010",
        "KAFKA-13557",
        "AVRO-3234",
        "FLINK-24409",
        "FLINK-14386",
        "FLINK-14665",
    ]
    for key in jira_keys:
        rel_path = f"jira/{key}.json"
        raw_issue = raw_files[rel_path]
        fixture_id = f"qualification/wave3/apache_real/{rel_path}"
        obs = adapt_apache_jira_issue(raw_issue, jira_context, fixture_id=fixture_id)
        observations.append(obs)
        jira_obs_by_key[key] = obs

    # 2. Adapt Negative Control Jira Issues
    for neg_key in ["PARQUET-1812", "ZOOKEEPER-4348"]:
        rel_path = f"negative_controls/jira/{neg_key}.json"
        raw_issue = raw_files[rel_path]
        fixture_id = f"qualification/wave3/apache_real/{rel_path}"
        obs = adapt_apache_jira_issue(raw_issue, jira_context, fixture_id=fixture_id)
        observations.append(obs)
        jira_obs_by_key[neg_key] = obs

    # 3. Adapt Target GitHub PRs
    pr_specs = [
        ("apache/parquet-java", 885, "github/parquet-java/pull_885.json"),
        ("apache/kafka", 11617, "github/kafka/pull_11617.json"),
        ("apache/avro", 1370, "github/avro/pull_1370.json"),
        ("apache/flink", 17401, "github/flink/pull_17401.json"),
        ("apache/flink", 17773, "github/flink/pull_17773.json"),
        ("apache/flink", 17799, "github/flink/pull_17799.json"),
        ("apache/flink", 10123, "github/flink/pull_10123.json"),
    ]
    for repo, pr_num, rel_path in pr_specs:
        raw_pr = raw_files[rel_path]
        fixture_id = f"qualification/wave3/apache_real/{rel_path}"
        commits_rel = rel_path.replace(".json", "_commits.json")
        reviews_rel = rel_path.replace(".json", "_reviews.json")
        commits = raw_files.get(commits_rel)
        reviews = raw_files.get(reviews_rel)

        obs = adapt_apache_github_pr(
            raw_pr,
            github_context,
            fixture_id=fixture_id,
            repo=repo,
            commits=commits,
            reviews=reviews,
        )
        observations.append(obs)
        pr_key = f"{repo}/{pr_num}"
        pr_obs_by_key[pr_key] = obs

    # 4. Adapt Negative Control GitHub PR
    neg_pr_path = "negative_controls/github/parquet-java/pull_3822.json"
    raw_neg_pr = raw_files[neg_pr_path]
    neg_pr_fid = f"qualification/wave3/apache_real/{neg_pr_path}"
    neg_obs = adapt_apache_github_pr(
        raw_neg_pr,
        github_context,
        fixture_id=neg_pr_fid,
        repo="apache/parquet-java",
    )
    observations.append(neg_obs)
    pr_obs_by_key["apache/parquet-java/3822"] = neg_obs

    # Verify Snyk bot PR #8 rejection: AXIOS-12613773 is rejected and NOT added as Jira work item
    snyk_pr_path = "negative_controls/github/snyk_bot/pull_8.json"
    assert snyk_pr_path in raw_files
    assert not is_valid_apache_jira_key("AXIOS-12613773")

    # 5. Adapt Chain 2 Commits (5 review commits for KAFKA-13557)
    kafka_commits_rel = "github/kafka/pull_11617_commits.json"
    kafka_commits = raw_files[kafka_commits_rel]
    kafka_commits_fid = f"qualification/wave3/apache_real/{kafka_commits_rel}"
    for raw_c in kafka_commits:
        c_obs = adapt_apache_github_commit(
            raw_c,
            repo="apache/kafka",
            context=github_context,
            fixture_id=kafka_commits_fid,
        )
        observations.append(c_obs)
        commit_obs_by_sha[raw_c["sha"]] = c_obs

    # 6. Build Cross-System Relationships & Alignments
    relationships: list[EvidenceRelationship] = []
    alignments: list[CrossSystemStateAlignment] = []

    # ── Chain 1: PARQUET-2010 ↔ PR 885 (DECLARED_MENTION)
    p2010_jira = jira_obs_by_key["PARQUET-2010"]
    p885_pr = pr_obs_by_key["apache/parquet-java/885"]
    p885_prov = p885_pr.provenance_refs
    relationships.append(
        EvidenceRelationship(
            subject_ref=p885_pr.entity_ref,
            object_ref=p2010_jira.entity_ref,
            kind="mentions",
            basis="lexical_match",
            subject_observation_id=github_context.observation_id,
            object_observation_id=jira_context.observation_id,
            provenance_refs=p885_prov,
        )
    )
    alignments.append(
        build_cross_system_alignment(
            subject_obs=p2010_jira,
            corroborating_obs=p885_pr,
            linkage_type="DECLARED_MENTION",
        )
    )

    # ── Chain 2: KAFKA-13557 ↔ PR 11617 (EXPLICIT_LINK, 5 commits)
    k13557_jira = jira_obs_by_key["KAFKA-13557"]
    k11617_pr = pr_obs_by_key["apache/kafka/11617"]
    k11617_prov = k11617_pr.provenance_refs
    relationships.append(
        EvidenceRelationship(
            subject_ref=k11617_pr.entity_ref,
            object_ref=k13557_jira.entity_ref,
            kind="explicit_link",
            basis="explicit_metadata",
            subject_observation_id=github_context.observation_id,
            object_observation_id=jira_context.observation_id,
            provenance_refs=k11617_prov,
        )
    )
    alignments.append(
        build_cross_system_alignment(
            subject_obs=k13557_jira,
            corroborating_obs=k11617_pr,
            linkage_type="EXPLICIT_LINK",
        )
    )
    # Link PR to commits (structural association within GitHub context)
    for sha, c_obs in commit_obs_by_sha.items():
        relationships.append(
            EvidenceRelationship(
                subject_ref=k11617_pr.entity_ref,
                object_ref=c_obs.entity_ref,
                kind="has_head_commit" if sha == k11617_pr.observed_state.head_commit_sha else "has_base_commit",
                basis="structural_association",
                subject_observation_id=github_context.observation_id,
                object_observation_id=github_context.observation_id,
                provenance_refs=k11617_prov,
            )
        )

    # ── Chain 3: AVRO-3234 ↔ PR 1370 (EXPLICIT_LINK)
    a3234_jira = jira_obs_by_key["AVRO-3234"]
    a1370_pr = pr_obs_by_key["apache/avro/1370"]
    a1370_prov = a1370_pr.provenance_refs
    relationships.append(
        EvidenceRelationship(
            subject_ref=a1370_pr.entity_ref,
            object_ref=a3234_jira.entity_ref,
            kind="explicit_link",
            basis="explicit_metadata",
            subject_observation_id=github_context.observation_id,
            object_observation_id=jira_context.observation_id,
            provenance_refs=a1370_prov,
        )
    )
    alignments.append(
        build_cross_system_alignment(
            subject_obs=a3234_jira,
            corroborating_obs=a1370_pr,
            linkage_type="EXPLICIT_LINK",
        )
    )

    # ── Chain 4: FLINK-24409 ↔ PRs 17401, 17773, 17799 (EXPLICIT_LINK)
    f24409_jira = jira_obs_by_key["FLINK-24409"]
    for pr_num in [17401, 17773, 17799]:
        pr_obs = pr_obs_by_key[f"apache/flink/{pr_num}"]
        relationships.append(
            EvidenceRelationship(
                subject_ref=pr_obs.entity_ref,
                object_ref=f24409_jira.entity_ref,
                kind="explicit_link",
                basis="explicit_metadata",
                subject_observation_id=github_context.observation_id,
                object_observation_id=jira_context.observation_id,
                provenance_refs=pr_obs.provenance_refs,
            )
        )
        alignments.append(
            build_cross_system_alignment(
                subject_obs=f24409_jira,
                corroborating_obs=pr_obs,
                linkage_type="EXPLICIT_LINK",
            )
        )

    # ── Chain 5: FLINK-14386 + FLINK-14665 ↔ PR 10123 (EXPLICIT_LINK, many-to-one)
    f10123_pr = pr_obs_by_key["apache/flink/10123"]
    for f_key in ["FLINK-14386", "FLINK-14665"]:
        f_jira = jira_obs_by_key[f_key]
        relationships.append(
            EvidenceRelationship(
                subject_ref=f10123_pr.entity_ref,
                object_ref=f_jira.entity_ref,
                kind="explicit_link",
                basis="explicit_metadata",
                subject_observation_id=github_context.observation_id,
                object_observation_id=jira_context.observation_id,
                provenance_refs=f10123_pr.provenance_refs,
            )
        )
        alignments.append(
            build_cross_system_alignment(
                subject_obs=f_jira,
                corroborating_obs=f10123_pr,
                linkage_type="EXPLICIT_LINK",
            )
        )

    # Deterministic Canonical Sorting
    sorted_contexts = sorted(
        (jira_context, github_context),
        key=lambda c: (c.source_instance.instance_id, c.observation_id),
    )
    sorted_observations = sorted(
        observations,
        key=lambda o: (
            o.entity_ref.source_instance.instance_id,
            o.entity_ref.entity_kind,
            o.entity_ref.entity_id,
        ),
    )
    sorted_relationships = sorted(
        relationships,
        key=lambda r: (
            r.kind,
            r.basis,
            r.subject_ref.entity_id,
            r.object_ref.entity_id,
            r.subject_observation_id,
            r.object_observation_id,
        ),
    )
    sorted_alignments = sorted(
        alignments,
        key=lambda a: (
            a.subject_ref.entity_id,
            a.corroborating_ref.entity_id,
            a.relationship_kind,
            a.state_comparison,
            a.temporal_comparison,
            a.rationale,
        ),
    )

    bundle = EvidenceBundle(
        bundle_id=bundle_id,
        bundle_version="1.0.0",
        observation_contexts=tuple(sorted_contexts),
        observations=tuple(sorted_observations),
        relationships=tuple(sorted_relationships),
        unresolved_references=(),
        quality_issues=(),
        cross_system_alignments=tuple(sorted_alignments),
    )

    return bundle, fixtures_by_id
