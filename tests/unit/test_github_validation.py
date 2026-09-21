"""Unit tests for GitHub fixture validation (CSE-1.3)."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from shadow_orbit.evidence_types import EntityRef, QualityIssue, SourceInstance
from shadow_orbit.fixture_io import load_fixture
from shadow_orbit.github_validation import (
    CONTRACT_VERSION,
    GitHubQuarantinedRecord,
    ValidatedGitHubFixture,
    validate_github_fixture,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "github"
CLEAN_FIXTURE_PATH = FIXTURES_DIR / "clean_github_week_1.json"
MESSY_FIXTURE_PATH = FIXTURES_DIR / "messy_github_week_1.json"


def _make_minimal_document() -> dict:
    return {
        "contract_version": CONTRACT_VERSION,
        "fixture_id": "test_gh_1",
        "source_instance": {
            "source_kind": "github",
            "instance_id": "github.com/test-org",
        },
        "observation_context": {
            "observation_id": "obs-1",
            "observed_interval_starts_at": "2026-02-02T00:00:00Z",
            "observed_interval_ends_at_exclusive": "2026-02-09T00:00:00Z",
            "source_cutoff_at": "2026-02-09T00:00:00Z",
        },
        "source_completeness": {
            "repositories_complete": True,
            "branches_complete": True,
            "commits_complete": True,
            "pull_requests_complete": True,
            "reviews_complete": True,
        },
        "repositories": [
            {
                "repo_id": "repo-1",
                "owner": "test-org",
                "name": "repo-one",
                "default_branch": "main",
                "branches": [{"name": "main", "head_commit_id": "sha1"}],
                "commits": [
                    {
                        "sha": "sha1",
                        "message": "init",
                        "author_login": "alice",
                        "committed_at": "2026-02-03T10:00:00Z",
                    }
                ],
                "pull_requests": [
                    {
                        "number": 1,
                        "title": "Initial PR",
                        "state": "open",
                        "author_login": "alice",
                        "created_at": "2026-02-03T11:00:00Z",
                        "reviews": [
                            {
                                "review_id": "rev-1",
                                "state": "APPROVED",
                                "reviewer_login": "bob",
                                "submitted_at": "2026-02-04T12:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ],
    }


class TestGitHubDocumentValidation:
    """Document-level structural validation."""

    def test_valid_minimal_document_passes(self):
        doc = _make_minimal_document()
        validated = validate_github_fixture(doc)
        assert isinstance(validated, ValidatedGitHubFixture)
        assert validated.source_instance.instance_id == "github.com/test-org"
        assert validated.observation_context.observation_id == "obs-1"
        assert len(validated.accepted_repositories) == 1
        assert len(validated.quarantined_records) == 0

    def test_unsupported_contract_version_raises(self):
        doc = _make_minimal_document()
        doc["contract_version"] = "shadow-github-fixture-v999"
        with pytest.raises(ValueError, match="Unsupported contract_version"):
            validate_github_fixture(doc)

    def test_missing_required_top_level_raises(self):
        doc = _make_minimal_document()
        del doc["repositories"]
        with pytest.raises(ValueError, match="Missing required top-level fields"):
            validate_github_fixture(doc)

    def test_invalid_source_kind_raises(self):
        doc = _make_minimal_document()
        doc["source_instance"]["source_kind"] = "gitlab"
        with pytest.raises(ValueError, match="source_kind must equal 'github'"):
            validate_github_fixture(doc)

    def test_missing_observation_id_raises(self):
        doc = _make_minimal_document()
        del doc["observation_context"]["observation_id"]
        with pytest.raises(ValueError, match="Missing required observation_context fields"):
            validate_github_fixture(doc)

    def test_invalid_observation_interval_emits_quality_issue(self):
        doc = _make_minimal_document()
        doc["observation_context"]["observed_interval_starts_at"] = "invalid-date"
        validated = validate_github_fixture(doc)
        assert any(
            q.code == "invalid" and q.subject_scope == "observation_context:observed_interval_starts_at"
            for q in validated.quality_issues
        )

    def test_contradictory_observation_interval_emits_quality_issue(self):
        doc = _make_minimal_document()
        doc["observation_context"]["observed_interval_starts_at"] = "2026-02-10T00:00:00Z"
        doc["observation_context"]["observed_interval_ends_at_exclusive"] = "2026-02-05T00:00:00Z"
        validated = validate_github_fixture(doc)
        assert any(
            q.code == "contradictory" and q.subject_scope == "observation_context:interval"
            for q in validated.quality_issues
        )

    def test_source_completeness_unsupported_field_emits_quality_issue(self):
        doc = _make_minimal_document()
        doc["source_completeness"]["issues_complete"] = True  # Jira concept in GitHub fixture
        validated = validate_github_fixture(doc)
        assert any(
            q.code == "unsupported_value" and "issues_complete" in q.message
            for q in validated.quality_issues
        )

    def test_source_completeness_non_boolean_emits_quality_issue(self):
        doc = _make_minimal_document()
        doc["source_completeness"]["reviews_complete"] = "yes"
        validated = validate_github_fixture(doc)
        assert any(
            q.code == "unsupported_value" and "reviews_complete" in q.subject_scope
            for q in validated.quality_issues
        )


class TestGitHubQuarantine:
    """Quarantine mechanics for invalid/duplicate GitHub records."""

    def test_duplicate_repo_ids_quarantine_all_occurrences(self):
        doc = _make_minimal_document()
        dup_repo = _make_minimal_document()["repositories"][0]
        dup_repo["name"] = "repo-one-clone"
        doc["repositories"].append(dup_repo)

        validated = validate_github_fixture(doc)
        assert len(validated.accepted_repositories) == 0
        assert len(validated.quarantined_records) == 2
        assert all(
            r.reason_code == "DUPLICATE_REPOSITORY_ID"
            for r in validated.quarantined_records
        )

    def test_missing_repo_fields_quarantined(self):
        doc = _make_minimal_document()
        del doc["repositories"][0]["owner"]
        validated = validate_github_fixture(doc)
        assert len(validated.accepted_repositories) == 0
        assert len(validated.quarantined_records) == 1
        assert validated.quarantined_records[0].reason_code == "MISSING_REQUIRED_FIELD"

    def test_duplicate_branch_names_quarantine_all_occurrences(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["branches"] = [
            {"name": "feature", "head_commit_id": "sha1"},
            {"name": "feature", "head_commit_id": "sha2"},
        ]
        validated = validate_github_fixture(doc)
        assert len(validated.accepted_repositories) == 1
        repo = validated.accepted_repositories[0]
        assert len(repo["branches"]) == 0
        branch_quarantines = [
            r for r in validated.quarantined_records
            if r.reason_code == "DUPLICATE_BRANCH_NAME"
        ]
        assert len(branch_quarantines) == 2

    def test_duplicate_commit_shas_quarantine_all_occurrences(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["commits"] = [
            {"sha": "c1", "message": "msg 1"},
            {"sha": "c1", "message": "msg 2"},
        ]
        validated = validate_github_fixture(doc)
        assert len(validated.accepted_repositories) == 1
        repo = validated.accepted_repositories[0]
        assert len(repo["commits"]) == 0
        commit_quarantines = [
            r for r in validated.quarantined_records
            if r.reason_code == "DUPLICATE_COMMIT_SHA"
        ]
        assert len(commit_quarantines) == 2

    def test_duplicate_pr_numbers_quarantine_all_occurrences(self):
        doc = _make_minimal_document()
        pr1 = {"number": 42, "title": "PR 42 first", "state": "open"}
        pr2 = {"number": 42, "title": "PR 42 second", "state": "closed"}
        doc["repositories"][0]["pull_requests"] = [pr1, pr2]

        validated = validate_github_fixture(doc)
        assert len(validated.accepted_repositories) == 1
        repo = validated.accepted_repositories[0]
        assert len(repo["pull_requests"]) == 0
        pr_quarantines = [
            r for r in validated.quarantined_records
            if r.reason_code == "DUPLICATE_PR_NUMBER"
        ]
        assert len(pr_quarantines) == 2

    def test_duplicate_review_ids_quarantine_all_occurrences(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["pull_requests"][0]["reviews"] = [
            {"review_id": "rev-dup", "state": "APPROVED"},
            {"review_id": "rev-dup", "state": "CHANGES_REQUESTED"},
        ]
        validated = validate_github_fixture(doc)
        repo = validated.accepted_repositories[0]
        pr = repo["pull_requests"][0]
        assert len(pr["reviews"]) == 0
        rev_quarantines = [
            r for r in validated.quarantined_records
            if r.reason_code == "DUPLICATE_REVIEW_ID"
        ]
        assert len(rev_quarantines) == 2

    def test_invalid_optional_timestamp_nulled_with_quality_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["pull_requests"][0]["merged_at"] = "invalid-date"
        validated = validate_github_fixture(doc)
        repo = validated.accepted_repositories[0]
        pr = repo["pull_requests"][0]
        assert pr["merged_at"] is None
        assert any(
            q.code == "invalid" and q.subject_scope == "field:merged_at"
            for q in validated.quality_issues
        )

    def test_pre_quarantine_raw_locators_are_preserved(self):
        """Accepted items retain raw locators addressing the original pre-quarantine indexes."""
        doc = _make_minimal_document()
        # Insert a bad PR at index 0 (missing title) and a good PR at index 1
        bad_pr = {"number": 10, "state": "open"}  # missing title
        good_pr = {"number": 20, "title": "Good PR", "state": "open"}
        doc["repositories"][0]["pull_requests"] = [bad_pr, good_pr]

        validated = validate_github_fixture(doc)
        repo = validated.accepted_repositories[0]
        assert len(repo["pull_requests"]) == 1
        accepted_pr = repo["pull_requests"][0]
        assert accepted_pr["number"] == 20
        # The accepted PR must have the locator repositories[0].pull_requests[1]
        assert accepted_pr["_raw_locator"] == "repositories[0].pull_requests[1]"


class TestGitHubFixturesFromDisk:
    """Tests executing against the JSON fixtures on disk."""

    def test_clean_github_fixture_passes_validation(self):
        raw = load_fixture(CLEAN_FIXTURE_PATH)
        validated = validate_github_fixture(raw)
        assert validated.raw_document["fixture_id"] == "clean_github_week_1"
        assert len(validated.accepted_repositories) == 1
        repo = validated.accepted_repositories[0]
        assert len(repo["branches"]) == 2
        assert len(repo["commits"]) == 2
        assert len(repo["pull_requests"]) == 2
        assert len(validated.quarantined_records) == 0
        assert len(validated.quality_issues) == 0

    def test_messy_github_fixture_quarantines_and_emits_quality_issues(self):
        raw = load_fixture(MESSY_FIXTURE_PATH)
        validated = validate_github_fixture(raw)
        assert validated.raw_document["fixture_id"] == "messy_github_week_1"
        assert len(validated.accepted_repositories) == 1

        reasons = {r.reason_code for r in validated.quarantined_records}
        assert "DUPLICATE_BRANCH_NAME" in reasons
        assert "DUPLICATE_COMMIT_SHA" in reasons
        assert "DUPLICATE_PR_NUMBER" in reasons
        assert "DUPLICATE_REVIEW_ID" in reasons

        invalid_scopes = {q.subject_scope for q in validated.quality_issues if q.code == "invalid"}
        assert "field:committed_at" in invalid_scopes
        assert "field:merged_at" in invalid_scopes


class TestNestedCollectionValidation:
    """Non-array nested collections must emit QualityIssue(code='invalid') and never become []."""

    def test_invalid_branches_collection_type_emits_quality_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["branches"] = "not-an-array"
        validated = validate_github_fixture(doc)
        assert len(validated.accepted_repositories) == 1
        repo = validated.accepted_repositories[0]
        assert repo["branches"] is None
        assert repo["branches"] != []
        assert any(
            q.code == "invalid" and q.subject_scope == "collection:branches"
            for q in validated.quality_issues
        )

    def test_invalid_commits_collection_type_emits_quality_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["commits"] = 12345
        validated = validate_github_fixture(doc)
        assert len(validated.accepted_repositories) == 1
        repo = validated.accepted_repositories[0]
        assert repo["commits"] is None
        assert repo["commits"] != []
        assert any(
            q.code == "invalid" and q.subject_scope == "collection:commits"
            for q in validated.quality_issues
        )

    def test_invalid_pull_requests_collection_type_emits_quality_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["pull_requests"] = {"number": 1}
        validated = validate_github_fixture(doc)
        assert len(validated.accepted_repositories) == 1
        repo = validated.accepted_repositories[0]
        assert repo["pull_requests"] is None
        assert repo["pull_requests"] != []
        assert any(
            q.code == "invalid" and q.subject_scope == "collection:pull_requests"
            for q in validated.quality_issues
        )

    def test_invalid_reviews_collection_type_emits_quality_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["pull_requests"][0]["reviews"] = "invalid-review-array"
        validated = validate_github_fixture(doc)
        assert len(validated.accepted_repositories) == 1
        repo = validated.accepted_repositories[0]
        pr = repo["pull_requests"][0]
        assert pr["reviews"] is None
        assert pr["reviews"] != []
        assert any(
            q.code == "invalid" and q.subject_scope == "collection:reviews"
            for q in validated.quality_issues
        )


class TestScalarFieldTypeValidation:
    """Enforce declared scalar types and reject invalid types and JSON booleans."""

    def test_repo_owner_non_string_quarantined(self):
        for bad_val in (123, True, False, ["owner"], {"k": "v"}):
            doc = _make_minimal_document()
            doc["repositories"][0]["owner"] = bad_val
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories) == 0
            assert any(r.reason_code == "INVALID_FIELD_TYPE" for r in validated.quarantined_records)

    def test_repo_name_non_string_quarantined(self):
        for bad_val in (123, True, False, ["name"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["name"] = bad_val
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories) == 0
            assert any(r.reason_code == "INVALID_FIELD_TYPE" for r in validated.quarantined_records)

    def test_repo_id_boolean_quarantined(self):
        for bad_val in (True, False):
            doc = _make_minimal_document()
            doc["repositories"][0]["repo_id"] = bad_val
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories) == 0
            assert any(r.reason_code == "INVALID_FIELD_TYPE" for r in validated.quarantined_records)

    def test_repo_default_branch_non_string_nulled_with_issue(self):
        for bad_val in (123, True, ["main"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["default_branch"] = bad_val
            validated = validate_github_fixture(doc)
            assert validated.accepted_repositories[0]["default_branch"] is None
            assert any(
                q.code == "invalid" and q.subject_scope == "field:default_branch"
                for q in validated.quality_issues
            )

    def test_branch_name_non_string_or_boolean_quarantined(self):
        for bad_val in (123, True, False, ["branch"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["branches"] = [{"name": bad_val}]
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories[0]["branches"]) == 0
            assert any(r.reason_code == "INVALID_FIELD_TYPE" for r in validated.quarantined_records)

    def test_branch_head_commit_id_non_string_nulled_with_issue(self):
        for bad_val in (123, True, ["sha"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["branches"][0]["head_commit_id"] = bad_val
            validated = validate_github_fixture(doc)
            assert validated.accepted_repositories[0]["branches"][0]["head_commit_id"] is None
            assert any(
                q.code == "invalid" and q.subject_scope == "field:head_commit_id"
                for q in validated.quality_issues
            )

    def test_commit_sha_non_string_or_boolean_quarantined(self):
        for bad_val in (123, True, False, ["sha"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["commits"] = [{"sha": bad_val, "message": "msg"}]
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories[0]["commits"]) == 0
            assert any(r.reason_code == "INVALID_FIELD_TYPE" for r in validated.quarantined_records)

    def test_commit_message_non_string_quarantined(self):
        for bad_val in (123, True, False, ["msg"], {"m": "x"}):
            doc = _make_minimal_document()
            doc["repositories"][0]["commits"][0]["message"] = bad_val
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories[0]["commits"]) == 0
            assert any(r.reason_code == "INVALID_FIELD_TYPE" for r in validated.quarantined_records)

    def test_commit_author_login_non_string_nulled_with_issue(self):
        for bad_val in (123, True, ["alice"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["commits"][0]["author_login"] = bad_val
            validated = validate_github_fixture(doc)
            assert validated.accepted_repositories[0]["commits"][0]["author_login"] is None
            assert any(
                q.code == "invalid" and q.subject_scope == "field:author_login"
                for q in validated.quality_issues
            )

    def test_pr_number_boolean_quarantined_not_treated_as_int(self):
        """Python's bool is a subclass of int; True must not become PR number 1."""
        for bad_val in (True, False):
            doc = _make_minimal_document()
            doc["repositories"][0]["pull_requests"][0]["number"] = bad_val
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories[0]["pull_requests"]) == 0
            assert any(r.reason_code == "INVALID_PR_NUMBER" for r in validated.quarantined_records)

    def test_pr_number_non_positive_or_non_int_quarantined(self):
        for bad_val in (0, -1, "1", 1.5, [1]):
            doc = _make_minimal_document()
            doc["repositories"][0]["pull_requests"][0]["number"] = bad_val
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories[0]["pull_requests"]) == 0
            assert any(r.reason_code == "INVALID_PR_NUMBER" for r in validated.quarantined_records)

    def test_pr_title_non_string_quarantined(self):
        for bad_val in (123, True, False, ["title"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["pull_requests"][0]["title"] = bad_val
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories[0]["pull_requests"]) == 0
            assert any(r.reason_code == "INVALID_FIELD_TYPE" for r in validated.quarantined_records)

    def test_pr_state_non_string_quarantined(self):
        for bad_val in (123, True, False, ["open"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["pull_requests"][0]["state"] = bad_val
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories[0]["pull_requests"]) == 0
            assert any(r.reason_code == "INVALID_FIELD_TYPE" for r in validated.quarantined_records)

    def test_pr_author_login_non_string_nulled_with_issue(self):
        for bad_val in (123, True, ["author"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["pull_requests"][0]["author_login"] = bad_val
            validated = validate_github_fixture(doc)
            assert validated.accepted_repositories[0]["pull_requests"][0]["author_login"] is None
            assert any(
                q.code == "invalid" and q.subject_scope == "field:author_login"
                for q in validated.quality_issues
            )

    def test_pr_target_and_source_branch_non_string_nulled_with_issue(self):
        for branch_field in ("target_branch", "source_branch"):
            for bad_val in (123, True, ["branch"]):
                doc = _make_minimal_document()
                doc["repositories"][0]["pull_requests"][0][branch_field] = bad_val
                validated = validate_github_fixture(doc)
                assert validated.accepted_repositories[0]["pull_requests"][0][branch_field] is None
                assert any(
                    q.code == "invalid" and q.subject_scope == f"field:{branch_field}"
                    for q in validated.quality_issues
                )

    def test_review_id_boolean_quarantined(self):
        for bad_val in (True, False):
            doc = _make_minimal_document()
            doc["repositories"][0]["pull_requests"][0]["reviews"][0]["review_id"] = bad_val
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories[0]["pull_requests"][0]["reviews"]) == 0
            assert any(r.reason_code == "INVALID_FIELD_TYPE" for r in validated.quarantined_records)

    def test_review_state_non_string_quarantined(self):
        for bad_val in (123, True, False, ["APPROVED"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["pull_requests"][0]["reviews"][0]["state"] = bad_val
            validated = validate_github_fixture(doc)
            assert len(validated.accepted_repositories[0]["pull_requests"][0]["reviews"]) == 0
            assert any(r.reason_code == "INVALID_FIELD_TYPE" for r in validated.quarantined_records)

    def test_review_reviewer_login_non_string_nulled_with_issue(self):
        for bad_val in (123, True, ["reviewer"]):
            doc = _make_minimal_document()
            doc["repositories"][0]["pull_requests"][0]["reviews"][0]["reviewer_login"] = bad_val
            validated = validate_github_fixture(doc)
            assert validated.accepted_repositories[0]["pull_requests"][0]["reviews"][0]["reviewer_login"] is None
            assert any(
                q.code == "invalid" and q.subject_scope == "field:reviewer_login"
                for q in validated.quality_issues
            )


class TestGitHubValidationIsolation:
    """Verify github_validation has no dependencies on Jira modules."""

    def test_github_validation_does_not_import_jira(self):
        import shadow_orbit.github_validation as gv
        source = inspect.getsource(gv)
        for forbidden in (
            "shadow_orbit.types",
            "shadow_orbit.validation",
            "shadow_orbit.normalization",
            "shadow_orbit.temporal",
            "shadow_orbit.evaluation",
            "shadow_orbit.artifact",
            "shadow_orbit.human_state",
            "shadow_orbit.deltas",
            "shadow_orbit.continuity",
            "shadow_orbit.messy_acceptance",
            "shadow_orbit.acceptance",
        ):
            assert forbidden not in source, f"github_validation must not import {forbidden}"


class TestCSE15PRValidation:
    """Validation of additive CSE-1.5 PR structural fields."""

    def test_valid_cse15_fields_accepted(self):
        doc = _make_minimal_document()
        pr = doc["repositories"][0]["pull_requests"][0]
        pr["head_commit_sha"] = "sha_head_1"
        pr["base_commit_sha"] = "sha_base_1"
        pr["head_repository_id"] = "fork-repo"
        pr["is_fork"] = True
        pr["pull_request_commits"] = [{"sha": "sha1"}, {"sha": "sha2"}]

        validated = validate_github_fixture(doc)
        v_pr = validated.accepted_repositories[0]["pull_requests"][0]
        assert v_pr["head_commit_sha"] == "sha_head_1"
        assert v_pr["base_commit_sha"] == "sha_base_1"
        assert v_pr["head_repository_id"] == "fork-repo"
        assert v_pr["is_fork"] is True
        assert len(v_pr["pull_request_commits"]) == 2

    def test_invalid_head_commit_sha_nulled_with_quality_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["pull_requests"][0]["head_commit_sha"] = 12345
        validated = validate_github_fixture(doc)
        v_pr = validated.accepted_repositories[0]["pull_requests"][0]
        assert v_pr["head_commit_sha"] is None
        assert any(
            q.code == "invalid" and q.subject_scope == "field:head_commit_sha"
            for q in validated.quality_issues
        )

    def test_invalid_base_commit_sha_nulled_with_quality_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["pull_requests"][0]["base_commit_sha"] = ""
        validated = validate_github_fixture(doc)
        v_pr = validated.accepted_repositories[0]["pull_requests"][0]
        assert v_pr["base_commit_sha"] is None
        assert any(
            q.code == "invalid" and q.subject_scope == "field:base_commit_sha"
            for q in validated.quality_issues
        )

    def test_invalid_head_repository_id_nulled_with_quality_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["pull_requests"][0]["head_repository_id"] = True
        validated = validate_github_fixture(doc)
        v_pr = validated.accepted_repositories[0]["pull_requests"][0]
        assert v_pr["head_repository_id"] is None
        assert any(
            q.code == "invalid" and q.subject_scope == "field:head_repository_id"
            for q in validated.quality_issues
        )

    def test_invalid_is_fork_nulled_with_quality_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["pull_requests"][0]["is_fork"] = "true"  # string, not bool
        validated = validate_github_fixture(doc)
        v_pr = validated.accepted_repositories[0]["pull_requests"][0]
        assert v_pr["is_fork"] is None
        assert any(
            q.code == "invalid" and q.subject_scope == "field:is_fork"
            for q in validated.quality_issues
        )

    def test_invalid_pull_request_commits_not_array_nulled_with_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["pull_requests"][0]["pull_request_commits"] = "not_an_array"
        validated = validate_github_fixture(doc)
        v_pr = validated.accepted_repositories[0]["pull_requests"][0]
        assert v_pr["pull_request_commits"] is None
        assert any(
            q.code == "invalid" and q.subject_scope == "collection:pull_request_commits"
            for q in validated.quality_issues
        )

    def test_pull_request_commits_invalid_entry_skipped_with_issue(self):
        doc = _make_minimal_document()
        doc["repositories"][0]["pull_requests"][0]["pull_request_commits"] = [
            {"sha": "valid_sha"},
            "not_a_dict",
            {"sha": ""},  # empty sha
        ]
        validated = validate_github_fixture(doc)
        v_pr = validated.accepted_repositories[0]["pull_requests"][0]
        assert len(v_pr["pull_request_commits"]) == 1
        assert v_pr["pull_request_commits"][0]["sha"] == "valid_sha"
        assert len([
            q for q in validated.quality_issues
            if q.subject_scope == "collection:pull_request_commits"
        ]) == 2
