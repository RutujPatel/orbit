"""Explicit orchestration of the clean Week 1 acceptance pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shadow_orbit.artifact import build_machine_review_artifact
from shadow_orbit.fixture_io import load_fixture
from shadow_orbit.normalization import normalize_fixture
from shadow_orbit.validation import validate_fixture


def execute_clean_week_one(
    fixture_path: str | Path,
) -> dict[str, Any]:
    """
    Execute deterministic machine-derived processing.

    The approved expected artifact is deliberately not accepted as input.
    Human-review state is not fabricated by this function.
    """
    raw_fixture = load_fixture(fixture_path)
    validated = validate_fixture(raw_fixture)
    normalized = normalize_fixture(validated)
    return build_machine_review_artifact(normalized)
