# Shadow ORBIT GitHub Fixture Input Contract

## Purpose

This contract defines the bounded input accepted by Shadow ORBIT's GitHub fixture validation and normalization pipeline (`CSE-1.3`).

It does not define a universal GitHub schema or mirror every GitHub REST/GraphQL API field.
It models only the bounded entity types and fields necessary for cross-system evidence observation.

## Contract Version

`shadow-github-fixture-v1`

---

## Top-Level Structure

A GitHub fixture document is a single JSON object containing:

- `contract_version`: string, must equal `"shadow-github-fixture-v1"`
- `fixture_id`: non-empty string identifying the fixture
- `source_instance`: object identifying the GitHub source deployment
  - `source_kind`: string, must equal `"github"`
  - `instance_id`: non-empty string (e.g. `"github.com/northstar"` or organization login)
- `observation_context`: object identifying the observation parameters
  - `observation_id`: non-empty string identifying this observation
  - `observed_interval_starts_at`: optional ISO 8601 aware datetime string (or null)
  - `observed_interval_ends_at_exclusive`: optional ISO 8601 aware datetime string (or null)
  - `source_cutoff_at`: optional ISO 8601 aware datetime string (or null)
  - `coverage_note`: optional string documenting known coverage context (or null)
- `source_completeness`: optional object defining extraction completeness (see below)
- `repositories`: array of repository objects (may be empty)

---

## Source Completeness Schema & Semantics

The `source_completeness` block explicitly captures extraction boundaries so that downstream systems do not confuse unextracted data with absent activity.

### Schema

```json
{
  "repositories_complete": true,
  "branches_complete": true,
  "commits_complete": true,
  "pull_requests_complete": true,
  "reviews_complete": true
}
```

### Allowed Fields & Values

| Field | Type | Required? | Allowed Values | Semantics |
| :--- | :--- | :--- | :--- | :--- |
| `repositories_complete` | boolean | Optional | `true`, `false`, `null` | Whether repository enumeration is complete for the source instance |
| `branches_complete` | boolean | Optional | `true`, `false`, `null` | Whether branch enumeration per repository is complete |
| `commits_complete` | boolean | Optional | `true`, `false`, `null` | Whether commit history within the observation interval is complete |
| `pull_requests_complete`| boolean | Optional | `true`, `false`, `null` | Whether pull requests within the observation interval are complete |
| `reviews_complete` | boolean | Optional | `true`, `false`, `null` | Whether reviews for included pull requests are complete |

### Interpretation Rules

1. **`true`:** The extraction process claims complete enumeration for this category within the observation scope.
2. **`false`:** The extraction process explicitly acknowledges partial observation (e.g., pagination cutoff, API rate-limiting, or filtered query). Partial data must never support absence reasoning (e.g. partial review data must never become "there were no reviews").
3. **`null` or omitted:** Completeness is unspecified. Absence reasoning is prohibited.
4. **Validation:** Non-boolean values (e.g. strings or numbers) or unrecognized keys produce an explicit `QualityIssue(code="unsupported_value")`.

---

## Entity Schemas & Fields

### 1. Repository (`github_repository`)

| Field | Type | Requirement | Nullable? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `repo_id` | string or integer | **Required** | No | Stable repository identifier. Serialized as string for identity. |
| `owner` | string | **Required** | No | Account or organization login. |
| `name` | string | **Required** | No | Repository name. Locator, not canonical identity. |
| `default_branch` | string | Optional | Yes | Name of default branch (e.g. `"main"`). |
| `branches` | array | Optional | No | List of branch objects. Defaults to empty array if omitted. |
| `commits` | array | Optional | No | List of commit objects. Defaults to empty array if omitted. |
| `pull_requests` | array | Optional | No | List of pull request objects. Defaults to empty array if omitted. |

**Identity Scope:** `EntityRef(source_instance, "github_repository", repo_id)`.

---

### 2. Branch (`github_branch`)

| Field | Type | Requirement | Nullable? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `name` | string | **Required** | No | Exact branch name (e.g. `"main"`). |
| `head_commit_id`| string | Optional | Yes | Commit SHA at branch tip. |

**Identity Scope:** Scoped by repository identity: `EntityRef(source_instance, "github_branch", f"{repo_id}/{name}")`.

---

### 3. Commit (`github_commit`)

| Field | Type | Requirement | Nullable? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `sha` | string | **Required** | No | Full commit hash or object ID. |
| `message` | string | **Required** | No | Commit message. Preserved as literal string. |
| `author_login` | string | Optional | Yes | GitHub login of author. Literal string; no person resolution. |
| `committed_at` | ISO 8601 string | Optional | Yes | Aware timestamp. If invalid: nulled + `QualityIssue(code="invalid")`. |

**Identity Scope:** Scoped by repository identity: `EntityRef(source_instance, "github_commit", f"{repo_id}/{sha}")`.

---

### 4. Pull Request (`github_pull_request`)

| Field | Type | Requirement | Nullable? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `number` | integer | **Required** | No | Positive integer PR number. |
| `title` | string | **Required** | No | PR title. Preserved as literal string; no Jira mention extraction. |
| `state` | string | **Required** | No | State string (e.g. `"open"`, `"closed"`, `"merged"`). |
| `author_login` | string | Optional | Yes | GitHub login of author. Literal string; no person resolution. |
| `created_at` | ISO 8601 string | Optional | Yes | Aware timestamp. If invalid: nulled + `QualityIssue(code="invalid")`. |
| `merged_at` | ISO 8601 string | Optional | Yes | Aware timestamp. If invalid: nulled + `QualityIssue(code="invalid")`. |
| `target_branch`| string | Optional | Yes | Target/base branch name. |
| `source_branch`| string | Optional | Yes | Source/head branch name. |
| `reviews` | array | Optional | No | List of review objects. Defaults to empty array if omitted. |

**Identity Scope:** Scoped by repository identity: `EntityRef(source_instance, "github_pull_request", f"{repo_id}/{number}")`.

---

### 5. Review (`github_review`)

| Field | Type | Requirement | Nullable? | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `review_id` | string or integer | **Required** | No | Provider review identifier. Serialized as string for identity. |
| `state` | string | **Required** | No | Review state (e.g. `"APPROVED"`, `"CHANGES_REQUESTED"`, `"COMMENTED"`). |
| `reviewer_login`| string | Optional | Yes | GitHub login of reviewer. Literal string; no person resolution. |
| `submitted_at` | ISO 8601 string | Optional | Yes | Aware timestamp. If invalid: nulled + `QualityIssue(code="invalid")`. |

**Identity Scope:** Scoped by PR identity: `EntityRef(source_instance, "github_review", f"{repo_id}/{pr_number}/{review_id}")`.

---

## Validation and Quarantine Semantics

1. **Duplicate Quarantine (All Occurrences):**
   When an identity key is duplicated within its defined scope, **ALL** occurrences of that identity are quarantined. No duplicate is silently kept, merged, or discarded.
   - Duplicate `repo_id` within fixture -> quarantine all occurrences.
   - Duplicate `name` for branches within a repository -> quarantine all occurrences.
   - Duplicate `sha` for commits within a repository -> quarantine all occurrences.
   - Duplicate `number` for pull requests within a repository -> quarantine all occurrences.
   - Duplicate `review_id` for reviews within a pull request -> quarantine all occurrences.

2. **Missing vs. Optional vs. Null Semantics:**
   - **Missing required field:** The enclosing record is invalid and is quarantined.
   - **Missing optional field:** Accepted; normalized to `None` in the observed payload.
   - **Explicit null for nullable optional field:** Accepted; normalized to `None`.
   - **Invalid optional timestamp:** Normalized to `None` and emits a `QualityIssue(code="invalid", ...)`.
   - **Invalid required timestamp:** If any required timestamp is malformed or naive, the record is quarantined.

3. **Provenance Record Locators:**
   `ProvenanceRef.record_locator` MUST address the **original raw fixture document** using 0-based indexing before any validation or quarantine filtering.
   Example: `repositories[0].pull_requests[1].reviews[0]`.

4. **Source Independence:**
   - GitHub pull requests are NOT Jira WorkItems.
   - No Jira key pattern matching (`[A-Z]+-\d+`) or mention extraction occurs.
   - GitHub usernames are preserved as literal strings without mapping to Jira users.

5. **Deferred Features (Later CSE Stages):**
   - **Explicit PR-to-Commit Associations:** Association objects linking PRs to commit SHAs (`pull_request_commits`) are deferred to CSE-1.5.
   - **Fork Head/Base Repository References:** Cross-repository references for pull requests originating from forks are deferred to later CSE stages. In CSE-1.3, all PRs are scoped strictly to the host repository.
   - **Collection-Scoped Coverage Structure:** Granular collection status, observation coverage counts, and omission reasons are deferred to later CSE stages. In CSE-1.3, document-level `source_completeness` boolean flags declare category-level enumeration claims.

