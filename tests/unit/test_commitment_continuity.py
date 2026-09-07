from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest

from shadow_orbit.artifact import (
    build_machine_review_artifact,
    serialize_deterministically,
)
from shadow_orbit.continuity import (
    build_week_two_continuity_artifact,
)
from shadow_orbit.evaluation import evaluate_week_one_rules
from shadow_orbit.human_state import validate_human_state
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.validation import validate_fixture


@dataclass(frozen=True, slots=True)
class _PostPreparationCompletion:
    commitment_key: str
    occurred_at: datetime
    completion_note: str


@dataclass(frozen=True, slots=True)
class _LaterCommitmentState:
    commitment_key: str
    current_status: str
    completed_at: datetime
    completion_note: str
    origin_review_label: str
    created_at: datetime


def _represent_later_completion(
    *,
    prepared_artifact,
    prior_human_state,
    event: _PostPreparationCompletion,
) -> _LaterCommitmentState:
    """
    Represent completion after preparation without mutating prepared state.

    This is a focused test-only operation. It is not a production
    post-review workflow or a generalized event model.
    """
    prepared_commitment = next(
        (
            item
            for item in prepared_artifact[
                "open_and_carried_commitments"
            ]["items"]
            if (
                item["external_key"]
                == event.commitment_key
            )
        ),
        None,
    )

    if prepared_commitment is None:
        raise ValueError(
            "The later event references a commitment that "
            "was not present in the prepared artifact."
        )

    if (
        prepared_commitment["status_at_preparation"]
        != "open"
    ):
        raise ValueError(
            "The later completion requires an open "
            "preparation-time state."
        )

    source_commitment = next(
        (
            commitment
            for commitment
            in prior_human_state.commitments
            if (
                commitment.external_key
                == event.commitment_key
            )
        ),
        None,
    )

    if source_commitment is None:
        raise ValueError(
            "The later event references a commitment that "
            "was not present in the human-state sidecar."
        )

    if event.occurred_at <= source_commitment.created_at:
        raise ValueError(
            "The completion event must occur after "
            "commitment creation."
        )

    return _LaterCommitmentState(
        commitment_key=source_commitment.external_key,
        current_status="completed",
        completed_at=event.occurred_at,
        completion_note=event.completion_note,
        origin_review_label=(
            source_commitment.origin_review_label
        ),
        created_at=source_commitment.created_at,
    )


def test_commitment_is_carried_once_as_open_and_overdue(
    clean_week_two_actual,
):
    section = clean_week_two_actual[
        "open_and_carried_commitments"
    ]

    assert section["count"] == 1
    assert len(section["items"]) == 1

    commitment = section["items"][0]

    assert commitment["external_key"] == "COMMITMENT-001"
    assert commitment["origin_review_label"] == "2026-W06"
    assert commitment["status_at_preparation"] == "open"
    assert (
        commitment["due_state_at_preparation"]
        == "overdue"
    )
    assert (
        commitment["due_at"]
        == "2026-02-12T17:00:00Z"
    )
    assert commitment["underlying_matches"] == [
        {
            "rule_key": "OVERDUE_COMMITMENT",
            "rule_version": "1",
            "calculation": (
                "status == open AND "
                "due_at < review_cutoff_at"
            ),
        }
    ]


def test_commitment_remains_separate_from_work_item_findings(
    clean_week_two_actual,
):
    work_item_subjects = {
        item["subject_key"]
        for item in clean_week_two_actual[
            "what_needs_attention"
        ]["items"]
    }

    assert "COMMITMENT-001" not in work_item_subjects


def _assert_embedded_consistency(
    sidecar_document,
    week_two_document,
):
    embedded = {
        value["external_key"]: value
        for value in week_two_document[
            "commitments_at_preparation"
        ]
    }

    for sidecar in sidecar_document["commitments"]:
        matching = embedded[sidecar["external_key"]]

        expected_pairs = {
            "origin_review_label": sidecar[
                "origin_review_label"
            ],
            "summary": sidecar["summary"],
            "owner": sidecar["owner"],
            "due_at": sidecar["due_at"],
            "created_at": sidecar["created_at"],
            "status": sidecar[
                "status_at_current_preparation"
            ],
            "normally_lives": sidecar["normally_lives"],
        }

        for field, expected_value in expected_pairs.items():
            assert matching[field] == expected_value, (
                "Embedded commitment mismatch at "
                f"{sidecar['external_key']}.{field}: "
                f"expected {expected_value!r}, "
                f"got {matching[field]!r}"
            )


def test_embedded_commitment_matches_sidecar_for_test_consistency(
    clean_week_one_human_document,
    clean_week_two_document,
):
    _assert_embedded_consistency(
        clean_week_one_human_document,
        clean_week_two_document,
    )


def test_embedded_commitment_mismatch_fails_explicitly(
    clean_week_one_human_document,
    clean_week_two_document,
):
    altered = deepcopy(
        clean_week_two_document
    )
    altered["commitments_at_preparation"][0][
        "owner"
    ] = "Other"

    with pytest.raises(
        AssertionError,
        match=r"COMMITMENT-001\.owner",
    ):
        _assert_embedded_consistency(
            clean_week_one_human_document,
            altered,
        )


def test_runtime_commitment_output_uses_sidecar_not_embedded_block(
    clean_week_one_document,
    clean_week_two_document,
    clean_week_one_human_document,
):
    altered_current_document = deepcopy(
        clean_week_two_document
    )
    altered_current_document[
        "commitments_at_preparation"
    ][0]["owner"] = (
        "Embedded value that runtime must ignore"
    )

    prior = normalize_fixture(
        validate_fixture(clean_week_one_document)
    )
    current = normalize_fixture(
        validate_fixture(altered_current_document)
    )

    prior_matches, _ = evaluate_week_one_rules(prior)

    human_state = validate_human_state(
        clean_week_one_human_document,
        prior_fixture=prior,
        current_fixture=current,
        prior_matches=prior_matches,
    )

    prior_artifact = build_machine_review_artifact(
        prior
    )

    artifact = build_week_two_continuity_artifact(
        prior=prior,
        current=current,
        prior_machine_artifact=prior_artifact,
        human_state=human_state,
    )

    commitment = artifact[
        "open_and_carried_commitments"
    ]["items"][0]

    assert commitment["owner"] == "Maya"
    assert commitment["owner"] != (
        "Embedded value that runtime must ignore"
    )


def test_later_completion_does_not_mutate_prepared_state(
    clean_week_two_actual,
    clean_week_one_human_state,
    clean_week_two_normalized,
):
    prepared_before = deepcopy(
        clean_week_two_actual
    )
    serialized_before = serialize_deterministically(
        clean_week_two_actual
    )
    sidecar_before = deepcopy(
        clean_week_one_human_state
    )

    prepared_commitment_before = deepcopy(
        clean_week_two_actual[
            "open_and_carried_commitments"
        ]["items"][0]
    )
    source_commitment_before = deepcopy(
        clean_week_one_human_state.commitments[0]
    )

    completion_event = _PostPreparationCompletion(
        commitment_key="COMMITMENT-001",
        occurred_at=(
            clean_week_two_normalized
            .review_period
            .review_cutoff_at
            + timedelta(minutes=1)
        ),
        completion_note=(
            "External security team confirmed approval "
            "for 18 February."
        ),
    )

    later_state = _represent_later_completion(
        prepared_artifact=clean_week_two_actual,
        prior_human_state=clean_week_one_human_state,
        event=completion_event,
    )

    assert later_state.commitment_key == "COMMITMENT-001"
    assert later_state.current_status == "completed"
    assert (
        later_state.completed_at
        == completion_event.occurred_at
    )
    assert later_state.completion_note == (
        "External security team confirmed approval "
        "for 18 February."
    )
    assert later_state.origin_review_label == "2026-W06"
    assert (
        later_state.created_at.isoformat()
        == "2026-02-09T10:15:00+00:00"
    )

    assert clean_week_two_actual == prepared_before
    assert (
        serialize_deterministically(clean_week_two_actual)
        == serialized_before
    )

    assert clean_week_one_human_state == sidecar_before
    assert (
        clean_week_one_human_state.commitments[0]
        == source_commitment_before
    )
    assert (
        clean_week_one_human_state.commitments[0]
        .status_at_current_preparation
        == "open"
    )

    prepared_commitment_after = clean_week_two_actual[
        "open_and_carried_commitments"
    ]["items"][0]

    assert (
        prepared_commitment_after
        == prepared_commitment_before
    )
    assert (
        prepared_commitment_after[
            "origin_review_label"
        ]
        == "2026-W06"
    )
    assert (
        prepared_commitment_after[
            "status_at_preparation"
        ]
        == "open"
    )
    assert (
        prepared_commitment_after[
            "due_state_at_preparation"
        ]
        == "overdue"
    )
