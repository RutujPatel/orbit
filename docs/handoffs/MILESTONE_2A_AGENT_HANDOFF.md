# Project ORBIT / Shadow ORBIT — Milestone 2A Agent Handoff

## Restricted Real Jira Data Inspection and Mapping

## 0. Authority and precedence

You are acting as the senior inspection engineer for:

> **Milestone 2A — Restricted Real Jira Data Inspection and Mapping**

Milestone 2A is not a software implementation milestone. It is a controlled data-inspection and design-decision milestone.

The precedence order is:

1. Checked-in canonical Project ORBIT decisions
2. Checked-in Milestone 0 contracts and artifacts
3. Published Milestones 1A, 1B, and 1C
4. Current Git state
5. Explicit authorization for the real dataset
6. This handoff

If this handoff conflicts with the repository or data authorization, stop and report the conflict.

Do not silently resolve discrepancies.

---

# 1. Published baseline

Expected project checkpoint:

```text
Repository: /home/tecblic/orbit
Branch: develop
HEAD: 37a38b0c8c2928433ff5cba8201132dceea58a6f
Short SHA: 37a38b0
origin/develop: same commit
Working tree: clean
Published test suite: 97 tests
```

Published milestones:

```text
Milestone 0:
  PASS / CLOSED
  commit e104810

Milestone 1A:
  PASS / CLOSED / PUBLISHED
  commit 0476df7

Milestone 1B:
  PASS / CLOSED / PUBLISHED
  commit 500c442

Milestone 1C:
  PASS / CLOSED / PUBLISHED
  commit 37a38b0
```

Milestone 1C established deterministic honesty for the approved synthetic messy scenario.

---

# 2. Milestone statement

Milestone 2A determines whether one authorized, narrowly bounded slice of real Jira data can be represented honestly by the existing Shadow ORBIT input contract without inventing state or weakening Milestones 1A–1C.

The secondary engineering observation is:

> Does the projected real dataset contain enough trustworthy evidence to exercise part of the existing deterministic review logic?

Do not interpret machine output as proof of customer usefulness.

---

# 3. Milestone status and authority

```text
Milestone 2A design:         APPROVED
Milestone 2A inspection:     AUTHORIZED after authorization gate
Repository modifications:   NOT AUTHORIZED
Importer implementation:    NOT AUTHORIZED
Milestone 2B:                NOT AUTHORIZED / NOT PREDETERMINED
Commit or push:              NOT AUTHORIZED
```

Milestone 2A must end with exactly one of:

```text
PROCEED TO 2B
PROCEED WITH MANUAL PROJECTION — NO IMPORTER YET
NARROW / CHANGE THE EXPERIMENT
STOP — CONTRACT REVIEW REQUIRED
```

Do not default to `PROCEED TO 2B`.

---

# 4. Strict prohibitions

Do not:

- Modify any repository file
- Add inspection scripts to the repository
- Add customer data to Git
- Stage, commit, or push
- Run `git init`
- Pull, merge, reset, rebase, or switch branches
- Build a Jira connector
- Add OAuth or API infrastructure
- Add a database, UI, worker, network service, or framework
- Add or change condition rules
- Change rule thresholds
- Change status or priority semantics
- Change Milestone 1B attention selection
- Change Milestone 1C honesty behavior
- Infer unknown values
- Convert missing history into complete history
- Convert absent due dates into “not overdue”
- Treat current sprint membership as historical planning intent
- Copy raw customer data into chat, issue trackers, screenshots, or logs
- Claim the inspected dataset is representative
- Claim machine output proves usefulness
- Create a production importer

All inspection artifacts must remain outside Git unless a later, explicit authorization permits a sanitized derivative.

---

# 5. Core honesty invariant

Preserve:

```text
unknown != false
missing != complete
unmapped != normal
invalid != absent
ambiguous != deterministically derived
some history != complete history
current sprint membership != historical planning intent
source extraction time != automatically reliable source cutoff
```

When evidence is insufficient, use:

```text
UNKNOWN
UNAVAILABLE
MANUAL
```

Do not fabricate compatibility.

---

# 6. Phase 0 — Verify the repository checkpoint

Run from the real Git clone:

```bash
cd /home/tecblic/orbit

git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/develop
git log --oneline --decorate -5
```

Required:

```text
branch = develop
HEAD = 37a38b0c8c2928433ff5cba8201132dceea58a6f
origin/develop = same SHA
working tree = clean
```

If any result differs:

1. Do not edit anything.
2. Report exact output.
3. Stop.

Do not automatically repair the repository.

---

# 7. Phase 0A — Build a controlled verification image

Repository execution must use Python 3.13 and pytest 8.x.

Build a disposable local image while network access is available:

```bash
cat > /tmp/orbit-2a-verification.Dockerfile <<'EOF'
FROM python:3.13
RUN python -m pip install --no-cache-dir "pytest>=8.3,<9"
WORKDIR /workspace
EOF

docker build \
  -f /tmp/orbit-2a-verification.Dockerfile \
  -t orbit-2a-verification:py313 \
  /tmp
```

Verify:

```bash
docker run --rm \
  orbit-2a-verification:py313 \
  sh -c '
    python --version &&
    python -m pytest --version
  '
```

Required:

```text
Python 3.13.x
pytest 8.x
```

The temporary Dockerfile is outside the repository.

---

# 8. Phase 0B — Verify the published test baseline

Run with the repository mounted read-only and network disabled:

```bash
docker run --rm \
  --network none \
  -v "/home/tecblic/orbit:/workspace:ro" \
  -w /workspace \
  orbit-2a-verification:py313 \
  sh -c '
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=src \
    python -m pytest -q -p no:cacheprovider
  '
```

Required:

```text
97 passed
```

If the suite fails:

1. Do not handle customer data.
2. Do not modify code.
3. Report the failure.
4. Stop.

---

# 9. Phase 1 — Authorization gate

Do not obtain, open, parse, inspect, or summarize real customer data until the user supplies a complete authorization record.

## Required authorization record

```text
Authorization owner:
Authorization owner’s role:
Organization:
Engineering Manager / team:
Jira project:
Purpose: Shadow ORBIT Milestone 2A restricted real-data inspection

Issue boundary:
Review period starts_at:
Review period ends_at_exclusive:
Review cutoff_at:
Proposed source_cutoff_at:

Permitted source fields:
Prohibited source fields:

Authorized operators:
Raw-data storage location:
Retention deadline:
Deletion procedure:

Sanitized derivative permitted outside private workspace: yes/no
Sanitized derivative permitted in Git: yes/no
Authorization evidence/reference:
Approval date:
```

## Authorization validation checklist

Confirm:

- The authorization owner can approve this use.
- Exactly one organization is included.
- Exactly one team is included.
- Exactly one Jira project is included.
- The issue boundary is explicit.
- The review period is explicit.
- The permitted fields are explicit.
- The prohibited fields are explicit.
- The storage location is explicit.
- The retention deadline is explicit.
- The deletion procedure is explicit.
- Authorized operators are named.
- Permission concerning sanitized derivatives is explicit.

If any field is absent or ambiguous:

```text
MILESTONE 2A STOPPED — AUTHORIZATION INCOMPLETE
```

Do not proceed.

---

# 10. Default field boundary

Unless the authorization is more restrictive, retain only fields needed to inspect the existing contract.

## Potentially permitted fields

```text
immutable Jira issue ID
issue key
summary/title, only if authorized
issue type
priority
status
provider status category
created timestamp
updated timestamp
resolved timestamp
due date
explicit planning evidence
status changes
due-date changes
timestamps associated with relevant changes
```

## Default prohibited fields

```text
comments
attachments
worklogs
user emails
user account IDs
reporter identity
assignee identity
watchers
customer names
customer identifiers
unnecessary descriptions
credentials
tokens
cookies
session values
webhook secrets
unnecessary URLs
unnecessary custom fields
```

Do not retain a prohibited field merely because it was included in the export.

If credentials or tokens are discovered:

1. Stop inspection.
2. Do not print or copy the value.
3. Notify the authorized owner.
4. Follow the approved deletion and incident procedure.

---

# 11. Phase 2 — Create the private workspace

Only after authorization is complete:

```bash
install -d -m 700 /home/tecblic/orbit-private
install -d -m 700 /home/tecblic/orbit-private/2a
install -d -m 700 /home/tecblic/orbit-private/2a/raw
install -d -m 700 /home/tecblic/orbit-private/2a/sanitized
install -d -m 700 /home/tecblic/orbit-private/2a/reports
install -d -m 700 /home/tecblic/orbit-private/2a/working
```

Verify boundaries:

```bash
git -C /home/tecblic/orbit rev-parse --show-toplevel
realpath /home/tecblic/orbit-private/2a
```

Required:

```text
repository root = /home/tecblic/orbit
private root = /home/tecblic/orbit-private/2a
```

The private root must not be inside the repository.

Verify permissions:

```bash
find /home/tecblic/orbit-private/2a \
  -maxdepth 1 \
  -printf '%M %u:%g %p\n'
```

Directories should not be world-readable.

---

# 12. Phase 3 — Obtain one bounded export

Use one manually produced, authorized export or equivalent restricted extraction.

Boundary:

```text
one organization
one Engineering Manager/team
one Jira project
one issue boundary
one review period
one proposed source cutoff
```

Do not curate the dataset to make Shadow ORBIT look effective.

An ordinary and imperfect dataset is acceptable.

Store the export only under:

```text
/home/tecblic/orbit-private/2a/raw/
```

Then:

```bash
chmod 600 /home/tecblic/orbit-private/2a/raw/*
```

Record without printing the data:

```bash
stat /home/tecblic/orbit-private/2a/raw/<export-file>
sha256sum /home/tecblic/orbit-private/2a/raw/<export-file>
```

Record:

```text
export filename:
export format:
export operator:
export start:
export end:
source-reported issue count:
pagination status:
history included:
authorization reference:
SHA-256:
```

A checksum identifies the inspected file. It does not prove authorization or semantic correctness.

---

# 13. Phase 4 — Structural privacy inspection

Before mapping data, verify the export does not contain unauthorized fields.

Perform this locally in the private workspace.

Do not paste raw values into chat.

## JSON field-path inventory

If the export is JSON and `jq` is available:

```bash
jq -r '
  paths
  | map(
      if type == "number"
      then "[]"
      else tostring
      end
    )
  | join(".")
' /home/tecblic/orbit-private/2a/raw/<export-file> \
  | sort -u \
  > /home/tecblic/orbit-private/2a/reports/source-field-paths.txt
```

Review:

```bash
less /home/tecblic/orbit-private/2a/reports/source-field-paths.txt
```

Field names may themselves be sensitive. Keep this report outside Git.

## Privacy review result

Produce:

| Source path | Permitted | Required | Treatment |
|---|---|---|---|
|  | yes/no | yes/no | retain/remove/review |

If unauthorized values are present, create a redacted working copy outside Git. Do not alter the original raw export.

---

# 14. Phase 5 — Inventory real source semantics

Record exact aggregate vocabularies and coverage without exposing unnecessary content.

Inspect:

```text
project keys
issue types
statuses
provider status categories
priorities
timestamp shapes
due-date shapes
history event types
planning-related fields
missing-value behavior
pagination/truncation indicators
```

## Source vocabulary table

| Category | Exact source value | Count | Sensitive | Notes |
|---|---|---:|---|---|
| Project key |  |  | no/yes | |
| Issue type |  |  | no/yes | |
| Status |  |  | no/yes | |
| Status category |  |  | no/yes | |
| Priority |  |  | no/yes | |
| Timestamp format |  |  | no/yes | |
| History field |  |  | no/yes | |
| Planning field |  |  | no/yes | |

Do not infer mappings during inventory. First record what exists.

---

# 15. Phase 6 — Complete the contract mapping

For every required Shadow ORBIT field, choose exactly one classification:

```text
DIRECT
DETERMINISTICALLY DERIVED
MANUAL
UNKNOWN
UNAVAILABLE
OUT OF SCOPE
```

Do not add another category.

## Definitions

### `DIRECT`

The source explicitly provides a value with equivalent semantics.

### `DETERMINISTICALLY DERIVED`

One unambiguous transformation exists and evidence is recorded.

### `MANUAL`

An authorized operator must make an explicit bounded judgment.

Record:

- Operator
- Evidence
- Time spent
- Ambiguity
- Whether another reasonable operator could disagree

### `UNKNOWN`

The contract supports unknown and evidence is insufficient.

### `UNAVAILABLE`

The export does not provide the required information and it cannot be recovered honestly.

### `OUT OF SCOPE`

The source field is irrelevant to the existing contract.

## Required mapping table

| Source path | Source value class/example | Shadow field | Classification | Transformation | Evidence | Ambiguity | Treatment |
|---|---|---|---|---|---|---|---|
|  |  | `source_id` |  |  |  |  | |
|  |  | `key` |  |  |  |  | |
|  |  | `title` |  |  |  |  | |
|  |  | `item_type` |  |  |  |  | |
|  |  | `priority` |  |  |  |  | |
|  |  | `status` |  |  |  |  | |
|  |  | `provider_status_category` |  |  |  |  | |
|  |  | `created_at` |  |  |  |  | |
|  |  | `updated_at` |  |  |  |  | |
|  |  | `resolved_at` |  |  |  |  | |
|  |  | `due_at` |  |  |  |  | |
|  |  | `planned_at_period_start` |  |  |  |  | |
|  |  | `history_complete` |  |  |  |  | |
|  |  | `changes[].field` |  |  |  |  | |
|  |  | `changes[].from_value` |  |  |  |  | |
|  |  | `changes[].to_value` |  |  |  |  | |
|  |  | `changes[].changed_at` |  |  |  |  | |

---

# 16. Field interpretation rules

## `source_id`

Use `DIRECT` only if this is Jira’s stable immutable issue ID.

Do not substitute array position, title, URL, or another convenience value.

## `key`

Confirm every issue is in the authorized project.

Cross-project records must be recorded and excluded—not silently ignored.

## `title`

Classify as:

```text
permitted unchanged
permitted after deterministic redaction
prohibited
```

Do not interpret or rewrite issue meaning.

## `priority`

Map only through explicit, defensible mappings.

Do not infer priority from labels, titles, age, due date, status, or assignee.

Unknown priority remains unknown.

## `status`

Map only through explicit, defensible mappings.

Do not infer status from title or updated timestamp.

Contradictions with provider status category must be recorded.

## Timestamps

Measure:

```text
present
missing
valid timezone-aware
valid timezone-naive
invalid
after source cutoff
after review cutoff
internally contradictory
```

Never attach an assumed timezone to a naive timestamp.

## Due dates

Distinguish:

```text
valid timestamp
date-only value
timezone-naive value
invalid value
missing value
```

Do not automatically interpret a Jira date-only field as midnight in a timezone unless an existing governed rule supports that conversion.

## `history_complete`

Use `true` only if extraction evidence establishes:

- Pagination completion
- No known truncation
- Required event types included
- Relevant history through source cutoff
- No permission-based omissions
- Reliable earliest and latest event coverage

Otherwise use:

```text
history_complete = false
```

## `planned_at_period_start`

Do not use current sprint membership as automatic historical planning evidence.

Use only:

```text
true
false
null
```

If historical planning evidence is unavailable:

```text
null
```

---

# 17. Phase 7 — Per-issue reconciliation

Create one private row for each issue.

| Row | Source ID | Key/pseudonym | In scope | Required timestamps | Status mapping | Priority mapping | Due state | History complete | Planning | Contradiction | Projection result | Notes |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 |  |  | yes/no | valid/invalid | known/unknown | known/unknown | valid/missing/invalid | true/false | true/false/null | yes/no |  | |

Projection result must be one of:

```text
ACCEPTED
QUARANTINED
EXCLUDED_OUT_OF_SCOPE
PENDING_AUTHORIZATION
```

Do not invent new production quarantine reason codes during 2A.

---

# 18. Phase 8 — History-completeness assessment

Complete this evidence table:

| Evidence | Result | Consequence |
|---|---|---|
| Pagination complete | yes/no/unknown | |
| Changelog included | yes/no | |
| Relevant status events included | yes/no/unknown | |
| Relevant due-date events included | yes/no/unknown | |
| Earliest retained event known | yes/no | |
| Latest event through cutoff known | yes/no | |
| Permission omissions possible | yes/no/unknown | |
| Export truncation possible | yes/no/unknown | |
| `history_complete=true` justified | yes/no | |

If completeness is not demonstrated, set it to false in the temporary projection.

Do not replace missing history with `updated_at`.

---

# 19. Phase 9 — Planning assessment

Complete:

| Planning evidence | Available | Historical at period start | Deterministic | Treatment |
|---|---|---|---|---|
| Current sprint membership |  | usually no |  | |
| Sprint changelog |  |  |  | |
| Planning meeting record |  |  |  | |
| Explicit custom field |  |  |  | |
| Manual manager confirmation |  |  |  | |
| Other |  |  |  | |

Record:

```text
known planned count
known unplanned count
unknown planning count
manual planning decisions
time spent
ambiguities
```

Do not calculate a manager-facing completion percentage if planning classification remains incomplete.

---

# 20. Phase 10 — Create a temporary sanitized projection

Only after authorization, privacy inspection, and mapping are complete, create:

```text
/home/tecblic/orbit-private/2a/sanitized/real_projection.json
```

This file must stay outside Git.

It must:

- Use the existing input contract
- Include only authorized fields
- Preserve unknown values
- Preserve missing values
- Preserve contradictions
- Preserve incomplete history
- Preserve original rule-relevant meaning
- Avoid improving data merely to pass validation

## Redaction log

| Source field class | Sanitized treatment | Semantic impact | Authorization |
|---|---|---|---|
|  | remove/pseudonymize/retain | none/describe | |

If redaction alters rule-relevant meaning, the projection is invalid.

---

# 21. Phase 11 — Validate and normalize with Docker

Run with:

```text
network disabled
repository read-only
private workspace read-only
Python 3.13
bytecode disabled
aggregate output only
```

```bash
docker run --rm \
  --network none \
  -v "/home/tecblic/orbit:/workspace:ro" \
  -v "/home/tecblic/orbit-private/2a:/private:ro" \
  -w /workspace \
  orbit-2a-verification:py313 \
  sh -c '
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python - <<'"'"'PY'"'"'
from pathlib import Path

from shadow_orbit.fixture_io import load_fixture
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.validation import validate_fixture

path = Path("/private/sanitized/real_projection.json")
document = load_fixture(path)
validated = validate_fixture(document)
normalized = normalize_fixture(validated)

print("raw_record_count", len(document["work_items"]))
print("accepted_record_count", len(validated.accepted_raw_items))
print(
    "quarantined_record_count",
    len(validated.quarantined_records),
)

quarantine_counts = {}
for record in validated.quarantined_records:
    quarantine_counts[record.reason_code] = (
        quarantine_counts.get(record.reason_code, 0) + 1
    )

condition_counts = {}
for condition in normalized.data_quality_conditions:
    condition_counts[condition.code] = (
        condition_counts.get(condition.code, 0) + 1
    )

print(
    "quarantine_reason_counts",
    sorted(quarantine_counts.items()),
)
print(
    "data_quality_condition_counts",
    sorted(condition_counts.items()),
)
PY
  '
```

Do not print titles, user identities, descriptions, or raw values into shared output.

---

# 22. Phase 12 — Run deterministic evaluation

```bash
docker run --rm \
  --network none \
  -v "/home/tecblic/orbit:/workspace:ro" \
  -v "/home/tecblic/orbit-private/2a:/private:ro" \
  -w /workspace \
  orbit-2a-verification:py313 \
  sh -c '
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python - <<'"'"'PY'"'"'
from pathlib import Path

from shadow_orbit.evaluation import evaluate_week_one_rules
from shadow_orbit.fixture_io import load_fixture
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.validation import validate_fixture

path = Path("/private/sanitized/real_projection.json")
document = load_fixture(path)
validated = validate_fixture(document)
normalized = normalize_fixture(validated)
matches, suppressed = evaluate_week_one_rules(normalized)

match_counts = {}
for match in matches:
    match_counts[match.rule_key] = (
        match_counts.get(match.rule_key, 0) + 1
    )

suppression_counts = {}
for result in suppressed:
    suppression_counts[result.rule_key] = (
        suppression_counts.get(result.rule_key, 0) + 1
    )

print("raw_match_count", len(matches))
print(
    "raw_match_counts_by_rule",
    sorted(match_counts.items()),
)
print("suppressed_evaluation_count", len(suppressed))
print(
    "suppression_counts_by_rule",
    sorted(suppression_counts.items()),
)
PY
  '
```

Do not use the clean or messy synthetic artifact assembler as an automatically approved real-customer presentation contract.

This phase observes evaluator behavior only.

---

# 23. Phase 13 — Collect quantitative evidence

Complete:

| Metric | Result | Denominator | Notes |
|---|---:|---:|---|
| Raw issues |  | — | |
| In-scope issues |  | raw | |
| Excluded out of scope |  | raw | |
| Accepted issues |  | in scope | |
| Quarantined issues |  | in scope | |
| Unknown statuses |  | accepted | |
| Unknown priorities |  | accepted | |
| Unknown planning classifications |  | accepted | |
| Valid due dates |  | accepted | |
| Missing due dates |  | accepted | |
| Invalid due dates |  | accepted | |
| Invalid required timestamps |  | in scope | |
| Incomplete histories |  | accepted | |
| Status/category contradictions |  | accepted | |
| Raw rule matches |  | accepted | |
| Suppressed evaluations |  | eligible evaluations | |
| Candidate findings |  | accepted | |
| Limitation categories |  | — | |
| Issues with limitations |  | accepted | |

Calculate:

```text
acceptance coverage
status mapping coverage
priority mapping coverage
due-date coverage
history coverage
planning coverage
finding density
limitation density
```

These are engineering observations, not confidence, health, severity, or product-success scores.

---

# 24. Phase 14 — Record manual effort

Maintain contemporaneously:

| Activity | Start | End | Minutes | Operator | Decisions | Ambiguous decisions | Notes |
|---|---|---|---:|---|---:|---:|---|
| Authorization |  |  |  |  |  |  | |
| Export |  |  |  |  |  |  | |
| Privacy inspection |  |  |  |  |  |  | |
| Redaction |  |  |  |  |  |  | |
| Status mapping |  |  |  |  |  |  | |
| Priority mapping |  |  |  |  |  |  | |
| Timestamp mapping |  |  |  |  |  |  | |
| History assessment |  |  |  |  |  |  | |
| Planning assessment |  |  |  |  |  |  | |
| Projection construction |  |  |  |  |  |  | |
| Validation review |  |  |  |  |  |  | |
| Founder review |  |  |  |  |  |  | |

Required totals:

```text
authorization/setup time
preprocessing/redaction time
mapping time
projection preparation time
founder/operator total time
manual decision count
ambiguous decision count
```

---

# 25. Phase 15 — Record information outside Jira

Do not ingest additional systems during 2A.

Record only where missing management context lives.

| Information | In Jira | Elsewhere | Location class | Needed by current rules | Needed for review | Treatment |
|---|---|---|---|---|---|---|
| Planning intent |  |  | meeting/Slack/email/etc. |  |  | |
| Blocker context |  |  |  |  |  | |
| Due-date meaning |  |  |  |  |  | |
| Commitment owner |  |  |  |  |  | |
| Decision rationale |  |  |  |  |  | |
| External dependency |  |  |  |  |  | |
| Work state |  |  |  |  |  | |
| Historical transitions |  |  |  |  |  | |

Do not silently add this information to the Jira-derived projection.

---

# 26. Phase 16 — Gap classification

For every mismatch, use:

```text
MAPPING GAP
EXPORT GAP
HISTORY GAP
PLANNING GAP
RULE / CONTRACT GAP
PRIVACY GAP
OUT OF SCOPE
```

## Gap table

| Gap ID | Classification | Source observation | Existing contract/rule | Impact | Temporary treatment | Recommendation |
|---|---|---|---|---|---|---|
| GAP-001 |  |  |  |  | unknown/unavailable/stop | |

If a `RULE / CONTRACT GAP` is found:

1. Do not modify rules.
2. Do not alter source values.
3. Do not implement an importer.
4. Select `STOP — CONTRACT REVIEW REQUIRED` unless the gap can be excluded by narrowing the experiment.

---

# 27. Phase 17 — Produce the 2A report

Create outside Git:

```text
/home/tecblic/orbit-private/2a/reports/milestone_2a_inspection.md
```

Use:

```markdown
# Shadow ORBIT — Milestone 2A Inspection Report

## 1. Boundary and authorization

## 2. Export and data-handling design

## 3. Actual source fields and vocabularies

## 4. Complete mapping table

## 5. Unknown, unavailable, and ambiguous fields

## 6. History-completeness assessment

## 7. Planning-classification assessment

## 8. Validation and quarantine impact

## 9. Deterministic evaluation impact

## 10. Findings, suppressions, and limitations

## 11. Manual founder/operator effort

## 12. Information outside Jira

## 13. Whether Jira alone is sufficient for this review

## 14. Contract and rule gaps

## 15. Recommended sanitized projection

## 16. Decision on Milestone 2B
```

The report must not include:

- Raw customer data
- Unredacted titles unless explicitly authorized
- Comments
- Attachments
- Emails
- Tokens
- Unnecessary identities

---

# 28. Phase 18 — Select exactly one outcome

## `PROCEED TO 2B`

Select only when:

- Existing contract semantics fit without fabrication.
- Cutoffs are defensible.
- Relevant history can be extracted reliably.
- Mappings are deterministic and repeatable.
- Manual judgment is small and bounded.
- Automation would remove repeated mechanical effort.
- Privacy controls permit repeated projection.
- No rule or contract change is required.

This recommends designing 2B. It does not automatically authorize implementation.

## `PROCEED WITH MANUAL PROJECTION — NO IMPORTER YET`

Select when:

- The contract works.
- Manual projection is safe and manageable.
- Mapping semantics are not stable enough to automate.
- One dataset does not justify importer infrastructure.
- Concierge operation can support a real review.

This is a successful result.

## `NARROW / CHANGE THE EXPERIMENT`

Select when:

- Real Jira evidence is too sparse.
- Existing rules can only be exercised for a smaller subset.
- Most output would be limitations.
- Important review context primarily lives outside Jira.
- A narrower experiment can proceed without fabricating state.

This does not authorize changing the product or rules.

## `STOP — CONTRACT REVIEW REQUIRED`

Select when:

- Honest projection requires a schema change.
- Source semantics conflict with the contract.
- A necessary timestamp cannot be represented honestly.
- Required rule evidence is unavailable by design.
- A new source or rule is necessary.
- Privacy constraints prohibit the projection.

---

# 29. Stop conditions

Stop immediately if:

- Authorization is missing or unclear.
- Project/team/issue scope is ambiguous.
- Prohibited data cannot be removed safely.
- Tokens or credentials are found.
- Source cutoff cannot be defended.
- A required mapping needs fabricated meaning.
- A date-only value needs an unauthorized timezone assumption.
- History completeness cannot be assessed.
- Planning state would need to be inferred.
- Customer-sensitive data would need to enter Git.
- A rule change appears necessary.
- A contract change appears necessary.
- A new source is required.
- The repository changes unexpectedly.

Report the stop reason without trying to solve it through implementation.

---

# 30. Milestone 2A PASS criteria

Milestone 2A passes only when:

- One authorized bounded dataset was inspected.
- Data handling and retention were explicit.
- Raw customer data remained outside Git.
- Required fields were fully reconciled.
- Unsupported values remained unknown.
- History completeness was assessed honestly.
- Planning evidence was assessed honestly.
- Quarantine and limitation impacts were measured.
- Deterministic matches and suppressions were measured.
- Manual effort was measured.
- Information outside Jira was documented.
- Contract/rule gaps were recorded.
- A sanitized projection was reviewed, if authorized.
- Exactly one evidence-based outcome was selected.
- The repository remained unchanged.

A PASS does not require selecting `PROCEED TO 2B`.

---

# 31. Final repository integrity verification

After inspection:

```bash
cd /home/tecblic/orbit

git status --short
git rev-parse HEAD
git rev-parse origin/develop
git diff --check
```

Required:

```text
HEAD = 37a38b0c8c2928433ff5cba8201132dceea58a6f
origin/develop = same
no tracked or untracked repository changes created by 2A
```

Check for possible customer exports inside the repository:

```bash
find /home/tecblic/orbit \
  -type f \
  \( \
    -iname '*export*' \
    -o -iname '*real*jira*' \
    -o -iname '*customer*data*' \
  \) \
  -print
```

Review results manually. Do not print file contents.

Do not remove any pre-existing file without user approval.

---

# 32. Retention and deletion

At the authorized retention deadline:

1. Verify which aggregate reports may be retained.
2. Verify whether the sanitized projection must be deleted.
3. Resolve the private path.
4. Obtain operator confirmation.
5. Delete only the approved private workspace.

Verify:

```bash
realpath /home/tecblic/orbit-private/2a
```

Example deletion command, requiring explicit confirmation:

```bash
rm -rf -- /home/tecblic/orbit-private/2a
```

Record:

```text
operator
timestamp
paths deleted
artifacts retained
authorization/reference
```

Do not claim secure physical erasure unless the storage system guarantees it.

---

# 33. Required agent output

## Before inspecting customer data

Return:

1. Git checkpoint
2. Baseline 97-test result
3. Completed authorization record
4. Private workspace verification
5. Confirmation that raw data has not yet been inspected

## After export acquisition

Return only sanitized metadata:

1. Authorization reference
2. Export format
3. Export checksum
4. Aggregate source issue count
5. Permitted/prohibited field verification
6. Confirmation raw data remains outside Git

## After full inspection

Return a sanitized summary:

1. Boundary and authorization result
2. Field inventory summary
3. Mapping classification totals
4. Unknown/unavailable fields
5. History assessment
6. Planning assessment
7. Validation/quarantine aggregates
8. Match/suppression aggregates
9. Limitation aggregates
10. Manual effort
11. Information outside Jira
12. Gap log
13. Repository-integrity result
14. Exactly one outcome:
    - `PROCEED TO 2B`
    - `PROCEED WITH MANUAL PROJECTION — NO IMPORTER YET`
    - `NARROW / CHANGE THE EXPERIMENT`
    - `STOP — CONTRACT REVIEW REQUIRED`

Do not expose customer-sensitive values in chat.

---

# 34. Final instruction

Start with repository verification and the supported Docker baseline.

Then stop and request the completed authorization record if it has not already been supplied.

Do not obtain or inspect customer data until authorization is complete.

Do not modify the repository.

Do not implement Milestone 2B.

Do not commit or push.