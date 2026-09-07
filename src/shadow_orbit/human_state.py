"""Validation and normalization of explicit prior human-review state."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from shadow_orbit.types import NormalizedFixture, RuleMatch
from shadow_orbit.validation import parse_aware_datetime


CONTRACT_VERSION = "shadow-prior-review-human-state-v1"

PRODUCT_DISPOSITIONS = frozenset(
    {
        "included",
        "not_for_this_week",
        "deferred",
        "resolved",
    }
)

LEARNING_CLASSIFICATIONS = frozenset(
    {
        "already_known",
        "new",
        "not_relevant",
        "source_wrong",
    }
)

COMMITMENT_STATUSES = frozenset(
    {
        "open",
        "completed",
        "cancelled",
    }
)


@dataclass(frozen=True, slots=True)
class PriorFindingFeedback:
    """Human feedback attached to a prior deterministic finding group."""

    subject_key: str
    related_rule_keys: tuple[str, ...]
    product_disposition: str
    learning_classification: str
    reason: str | None


@dataclass(frozen=True, slots=True)
class Commitment:
    """Human-originated commitment state used for continuity preparation."""

    external_key: str
    origin_review_label: str
    origin_decision_key: str | None
    summary: str
    owner: str
    due_at: datetime
    created_at: datetime
    status_at_prior_review_completion: str
    status_at_current_preparation: str
    normally_lives: str | None


@dataclass(frozen=True, slots=True)
class PriorHumanState:
    """Validated human-state sidecar."""

    contract_version: str
    fixture_id: str
    organization_key: str
    team_key: str
    prior_review_label: str
    current_review_label: str
    finding_feedback: tuple[PriorFindingFeedback, ...]
    commitments: tuple[Commitment, ...]


def _require_non_empty_string(
    value: Any,
    field_path: str,
) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_path} must be a non-empty string.")
    return value


def _prior_finding_index(
    matches: tuple[RuleMatch, ...],
) -> set[tuple[str, str]]:
    return {
        (match.subject_key, match.rule_key)
        for match in matches
    }


def validate_human_state(
    document: dict[str, Any],
    *,
    prior_fixture: NormalizedFixture,
    current_fixture: NormalizedFixture,
    prior_matches: tuple[RuleMatch, ...],
) -> PriorHumanState:
    """
    Validate human-originated continuity input.

    The expected artifact and the Week 2 fixture's embedded
    commitments_at_preparation block are not runtime inputs here.
    """
    value = deepcopy(document)

    required_top_level = {
        "contract_version",
        "fixture_id",
        "organization_key",
        "team_key",
        "prior_review_label",
        "current_review_label",
        "finding_feedback",
        "commitments",
    }
    missing = sorted(required_top_level - value.keys())
    if missing:
        raise ValueError(
            "Human-state document is missing required fields: "
            f"{missing}"
        )

    if value["contract_version"] != CONTRACT_VERSION:
        raise ValueError(
            "Unsupported human-state contract_version: "
            f"{value['contract_version']!r}"
        )

    prior_document = prior_fixture.raw_document
    current_document = current_fixture.raw_document

    organization_key = _require_non_empty_string(
        value["organization_key"],
        "organization_key",
    )
    team_key = _require_non_empty_string(
        value["team_key"],
        "team_key",
    )
    prior_review_label = _require_non_empty_string(
        value["prior_review_label"],
        "prior_review_label",
    )
    current_review_label = _require_non_empty_string(
        value["current_review_label"],
        "current_review_label",
    )

    if organization_key != prior_document["organization"]["external_key"]:
        raise ValueError(
            "Human-state organization does not match the prior fixture."
        )
    if organization_key != current_document["organization"]["external_key"]:
        raise ValueError(
            "Human-state organization does not match the current fixture."
        )

    if team_key != prior_document["team"]["external_key"]:
        raise ValueError(
            "Human-state team does not match the prior fixture."
        )
    if team_key != current_document["team"]["external_key"]:
        raise ValueError(
            "Human-state team does not match the current fixture."
        )

    if prior_review_label != prior_fixture.review_period.label:
        raise ValueError(
            "Human-state prior review label does not match "
            "the prior fixture."
        )
    if current_review_label != current_fixture.review_period.label:
        raise ValueError(
            "Human-state current review label does not match "
            "the current fixture."
        )

    comparison = current_document.get("comparison")
    if not isinstance(comparison, dict):
        raise ValueError(
            "Current fixture must contain explicit comparison metadata."
        )

    if comparison.get("prior_review_label") != prior_review_label:
        raise ValueError(
            "Current fixture predecessor does not match "
            "the human-state input."
        )

    if (
        comparison.get("prior_fixture_id")
        != prior_document["fixture_id"]
    ):
        raise ValueError(
            "Current fixture predecessor identity does not match "
            "the prior fixture."
        )

    feedback_values = value["finding_feedback"]
    if not isinstance(feedback_values, list):
        raise ValueError("finding_feedback must be an array.")

    prior_subjects = {
        item.key
        for item in prior_fixture.work_items
    }
    prior_finding_keys = _prior_finding_index(prior_matches)

    feedback: list[PriorFindingFeedback] = []
    feedback_subjects: set[str] = set()

    for index, entry in enumerate(feedback_values):
        path = f"finding_feedback[{index}]"
        if not isinstance(entry, dict):
            raise ValueError(f"{path} must be an object.")

        required = {
            "subject_key",
            "related_rule_keys",
            "product_disposition",
            "learning_classification",
            "reason",
        }
        missing_entry = sorted(required - entry.keys())
        if missing_entry:
            raise ValueError(
                f"{path} is missing required fields: {missing_entry}"
            )

        subject_key = _require_non_empty_string(
            entry["subject_key"],
            f"{path}.subject_key",
        )

        if subject_key in feedback_subjects:
            raise ValueError(
                f"Duplicate feedback subject: {subject_key}"
            )
        feedback_subjects.add(subject_key)

        if subject_key not in prior_subjects:
            raise ValueError(
                f"{path}.subject_key does not exist in prior source state."
            )

        related = entry["related_rule_keys"]
        if (
            not isinstance(related, list)
            or not related
            or not all(
                isinstance(rule_key, str) and rule_key
                for rule_key in related
            )
        ):
            raise ValueError(
                f"{path}.related_rule_keys must be a non-empty "
                "array of strings."
            )

        related_rule_keys = tuple(related)
        if len(set(related_rule_keys)) != len(related_rule_keys):
            raise ValueError(
                f"{path}.related_rule_keys contains duplicates."
            )

        for rule_key in related_rule_keys:
            if (subject_key, rule_key) not in prior_finding_keys:
                raise ValueError(
                    f"{path} references prior rule {rule_key!r}, "
                    "but that rule did not fire for the subject."
                )

        product_disposition = entry["product_disposition"]
        if product_disposition not in PRODUCT_DISPOSITIONS:
            raise ValueError(
                f"{path}.product_disposition is unsupported."
            )

        learning_classification = entry[
            "learning_classification"
        ]
        if (
            learning_classification
            not in LEARNING_CLASSIFICATIONS
        ):
            raise ValueError(
                f"{path}.learning_classification is unsupported."
            )

        reason = entry["reason"]
        if reason is not None and not isinstance(reason, str):
            raise ValueError(
                f"{path}.reason must be a string or null."
            )

        feedback.append(
            PriorFindingFeedback(
                subject_key=subject_key,
                related_rule_keys=related_rule_keys,
                product_disposition=product_disposition,
                learning_classification=learning_classification,
                reason=reason,
            )
        )

    commitment_values = value["commitments"]
    if not isinstance(commitment_values, list):
        raise ValueError("commitments must be an array.")

    commitments: list[Commitment] = []
    commitment_keys: set[str] = set()

    for index, entry in enumerate(commitment_values):
        path = f"commitments[{index}]"
        if not isinstance(entry, dict):
            raise ValueError(f"{path} must be an object.")

        required = {
            "external_key",
            "origin_review_label",
            "origin_decision_key",
            "summary",
            "owner",
            "due_at",
            "created_at",
            "status_at_prior_review_completion",
            "status_at_current_preparation",
            "normally_lives",
        }
        missing_entry = sorted(required - entry.keys())
        if missing_entry:
            raise ValueError(
                f"{path} is missing required fields: {missing_entry}"
            )

        external_key = _require_non_empty_string(
            entry["external_key"],
            f"{path}.external_key",
        )
        if external_key in commitment_keys:
            raise ValueError(
                f"Duplicate commitment key: {external_key}"
            )
        commitment_keys.add(external_key)

        origin_review_label = _require_non_empty_string(
            entry["origin_review_label"],
            f"{path}.origin_review_label",
        )
        if origin_review_label != prior_review_label:
            raise ValueError(
                f"{path}.origin_review_label must match "
                "the prior review."
            )

        origin_decision_key = entry["origin_decision_key"]
        if origin_decision_key is not None:
            origin_decision_key = _require_non_empty_string(
                origin_decision_key,
                f"{path}.origin_decision_key",
            )

        prior_status = entry[
            "status_at_prior_review_completion"
        ]
        current_status = entry[
            "status_at_current_preparation"
        ]

        if prior_status not in COMMITMENT_STATUSES:
            raise ValueError(
                f"{path}.status_at_prior_review_completion "
                "is unsupported."
            )
        if current_status not in COMMITMENT_STATUSES:
            raise ValueError(
                f"{path}.status_at_current_preparation is unsupported."
            )

        normally_lives = entry["normally_lives"]
        if (
            normally_lives is not None
            and not isinstance(normally_lives, str)
        ):
            raise ValueError(
                f"{path}.normally_lives must be a string or null."
            )

        commitments.append(
            Commitment(
                external_key=external_key,
                origin_review_label=origin_review_label,
                origin_decision_key=origin_decision_key,
                summary=_require_non_empty_string(
                    entry["summary"],
                    f"{path}.summary",
                ),
                owner=_require_non_empty_string(
                    entry["owner"],
                    f"{path}.owner",
                ),
                due_at=parse_aware_datetime(
                    entry["due_at"],
                    f"{path}.due_at",
                ),
                created_at=parse_aware_datetime(
                    entry["created_at"],
                    f"{path}.created_at",
                ),
                status_at_prior_review_completion=prior_status,
                status_at_current_preparation=current_status,
                normally_lives=normally_lives,
            )
        )

    return PriorHumanState(
        contract_version=value["contract_version"],
        fixture_id=_require_non_empty_string(
            value["fixture_id"],
            "fixture_id",
        ),
        organization_key=organization_key,
        team_key=team_key,
        prior_review_label=prior_review_label,
        current_review_label=current_review_label,
        finding_feedback=tuple(
            sorted(
                feedback,
                key=lambda item: item.subject_key,
            )
        ),
        commitments=tuple(
            sorted(
                commitments,
                key=lambda item: item.external_key,
            )
        ),
    )
