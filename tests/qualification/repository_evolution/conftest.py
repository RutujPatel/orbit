"""Pytest configuration and shared fixtures for repository evolution qualification."""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from shadow_orbit.evidence_types import EntityRef, ProvenanceRef, SourceInstance
from qualification.repository_evolution.schema import (
    RepositoryEvolutionRelationship,
    RepositoryProvenanceRef,
    SemanticFirewall,
)


@pytest.fixture
def gh_source() -> SourceInstance:
    return SourceInstance("github", "github.com/apache")


@pytest.fixture
def jira_source() -> SourceInstance:
    return SourceInstance("jira", "issues.apache.org")


@pytest.fixture
def flink_repo_ref(gh_source: SourceInstance) -> EntityRef:
    return EntityRef(gh_source, "repository", "apache/flink")


@pytest.fixture
def incubator_flink_repo_ref(gh_source: SourceInstance) -> EntityRef:
    return EntityRef(gh_source, "repository", "apache/incubator-flink")


@pytest.fixture
def stratosphere_repo_ref() -> EntityRef:
    strat_source = SourceInstance("github", "github.com/stratosphere")
    return EntityRef(strat_source, "repository", "stratosphere/stratosphere")


@pytest.fixture
def kafka_repo_ref(gh_source: SourceInstance) -> EntityRef:
    return EntityRef(gh_source, "repository", "apache/kafka")


@pytest.fixture
def rocksdb_repo_ref() -> EntityRef:
    rocks_source = SourceInstance("github", "github.com/facebook")
    return EntityRef(rocks_source, "repository", "facebook/rocksdb")


@pytest.fixture
def sample_provenance(gh_source: SourceInstance) -> RepositoryProvenanceRef:
    return RepositoryProvenanceRef(
        source_instance=gh_source,
        fixture_id="qualification/wave3/sample_fixture.json",
        record_locator="base.repo.full_name",
        sha256_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )


@pytest.fixture
def sample_observed_at() -> datetime:
    return datetime(2026, 9, 30, 16, 0, 0, tzinfo=timezone.utc)
