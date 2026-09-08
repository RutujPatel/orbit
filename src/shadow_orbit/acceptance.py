"""Explicit orchestration of Shadow ORBIT acceptance pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shadow_orbit.artifact import build_machine_review_artifact
from shadow_orbit.continuity import (
    build_week_two_continuity_artifact,
)
from shadow_orbit.evaluation import evaluate_week_one_rules
from shadow_orbit.fixture_io import load_fixture
from shadow_orbit.human_state import validate_human_state
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.validation import validate_fixture


def _load_normalized_fixture(
    fixture_path: str | Path,
):
    raw_fixture = load_fixture(fixture_path)
    validated = validate_fixture(raw_fixture)
    return normalize_fixture(validated)


def execute_clean_week_one(
    fixture_path: str | Path,
) -> dict[str, Any]:
    """
    Execute deterministic Week 1 machine-derived processing.

    The approved expected artifact is not accepted as input.
    Human-review state is not fabricated.
    """
    normalized = _load_normalized_fixture(fixture_path)
    return build_machine_review_artifact(normalized)


def execute_clean_week_two(
    *,
    prior_fixture_path: str | Path,
    current_fixture_path: str | Path,
    human_state_path: str | Path,
) -> dict[str, Any]:
    """
    Execute explicit two-period continuity preparation.

    Expected artifacts are not runtime inputs. The Week 2 fixture's
    embedded commitments_at_preparation block is not passed to
    commitment evaluation. Human commitment state comes only from
    the explicit sidecar.
    """
    prior = _load_normalized_fixture(prior_fixture_path)
    current = _load_normalized_fixture(current_fixture_path)

    prior_machine_artifact = build_machine_review_artifact(
        prior
    )
    prior_matches, _ = evaluate_week_one_rules(prior)

    human_document = load_fixture(human_state_path)
    human_state = validate_human_state(
        human_document,
        prior_fixture=prior,
        current_fixture=current,
        prior_matches=prior_matches,
    )

    return build_week_two_continuity_artifact(
        prior=prior,
        current=current,
        prior_machine_artifact=prior_machine_artifact,
        human_state=human_state,
    )

def execute_messy_week_one(
    fixture_path: str | Path,
) -> dict[str, Any]:
    """
    Execute deterministic messy Week 1 machine-derived processing.

    The approved expected artifact is not accepted as input.
    Human-review state is not fabricated.
    Quarantine, data-quality conditions, and honest limitations
    are derived from runtime source state.
    """
    from shadow_orbit.messy_acceptance import (
        build_messy_week_one_artifact,
    )

    raw_fixture = load_fixture(fixture_path)
    validated = validate_fixture(raw_fixture)
    normalized = normalize_fixture(validated)
    return build_messy_week_one_artifact(validated, normalized)
