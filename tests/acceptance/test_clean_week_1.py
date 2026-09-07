from __future__ import annotations

import hashlib
import json
from typing import Any

from shadow_orbit.artifact import machine_derived_projection


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
                f"{path}: list length mismatch; expected "
                f"{len(expected)}, got {len(actual)}"
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
            f"{path}: value mismatch; expected "
            f"{expected!r}, got {actual!r}"
        )

    return None


def test_clean_week_one_matches_approved_machine_projection(
    clean_week_one_actual,
    clean_week_one_expected,
    clean_week_one_path,
    clean_week_one_expected_path,
):
    """
    Compare only the explicit machine-derived boundary.

    The expected artifact is loaded independently by the test and is never
    passed to domain execution. Human-review state is excluded because it
    cannot be derived from Jira input.
    """
    fixture_before = _digest(clean_week_one_path)
    expected_before = _digest(clean_week_one_expected_path)

    expected_projection = machine_derived_projection(
        clean_week_one_expected
    )

    mismatch = _first_mismatch(
        expected_projection,
        clean_week_one_actual,
    )

    assert mismatch is None, (
        f"Clean Week 1 acceptance mismatch:\n{mismatch}\n\n"
        "Expected machine projection:\n"
        f"{json.dumps(expected_projection, indent=2)}\n\n"
        "Actual machine projection:\n"
        f"{json.dumps(clean_week_one_actual, indent=2)}"
    )

    assert _digest(clean_week_one_path) == fixture_before
    assert _digest(clean_week_one_expected_path) == expected_before
