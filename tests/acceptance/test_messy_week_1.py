from __future__ import annotations

import hashlib
import json
from typing import Any

from shadow_orbit.acceptance import execute_messy_week_one
from shadow_orbit.messy_acceptance import messy_machine_derived_projection


def _digest(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_mismatch(
    expected: Any,
    actual: Any,
    path: str = "$",
) -> str | None:
    if type(expected) is not type(actual):
        return (
            f"{path}: type mismatch; expected "
            f"{type(expected).__name__}, got "
            f"{type(actual).__name__}"
        )

    if isinstance(expected, dict):
        expected_keys = set(expected)
        actual_keys = set(actual)

        missing = sorted(expected_keys - actual_keys)
        if missing:
            return f"{path}: missing keys {missing}"

        unexpected = sorted(actual_keys - expected_keys)
        if unexpected:
            return f"{path}: unexpected keys {unexpected}"

        for key in expected:
            mismatch = _first_mismatch(
                expected[key],
                actual[key],
                f"{path}.{key}",
            )
            if mismatch:
                return mismatch

        return None

    if isinstance(expected, list):
        if len(expected) != len(actual):
            return (
                f"{path}: list length mismatch; "
                f"expected {len(expected)}, "
                f"got {len(actual)}"
            )

        for index, (expected_item, actual_item) in enumerate(
            zip(expected, actual, strict=True)
        ):
            mismatch = _first_mismatch(
                expected_item,
                actual_item,
                f"{path}[{index}]",
            )
            if mismatch:
                return mismatch

        return None

    if expected != actual:
        return (
            f"{path}: value mismatch; "
            f"expected {expected!r}, "
            f"got {actual!r}"
        )

    return None


def test_messy_week_one_matches_approved_machine_projection(
    messy_week_one_expected,
    messy_week_one_path,
    messy_week_one_expected_path,
):
    """
    Compare only the explicit eleven-field messy machine-derived projection.

    The expected artifact is independently loaded by the test and is never
    supplied to domain execution. The excluded synthetic_human_review_state
    remains human-authored test context and is not generated at runtime.
    """
    protected_paths = (
        messy_week_one_path,
        messy_week_one_expected_path,
    )

    before = {path: _digest(path) for path in protected_paths}

    actual = execute_messy_week_one(messy_week_one_path)

    expected_projection = messy_machine_derived_projection(
        messy_week_one_expected
    )

    assert "synthetic_human_review_state" not in expected_projection
    assert "synthetic_human_review_state" not in actual

    mismatch = _first_mismatch(
        expected_projection,
        actual,
    )

    assert mismatch is None, (
        f"Messy Week 1 acceptance mismatch:\n"
        f"{mismatch}\n\n"
        "Expected machine projection:\n"
        f"{json.dumps(expected_projection, indent=2)}\n\n"
        "Actual machine projection:\n"
        f"{json.dumps(actual, indent=2)}"
    )

    after = {path: _digest(path) for path in protected_paths}
    assert after == before
