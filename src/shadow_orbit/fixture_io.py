"""Filesystem I/O for explicit fixture and expected-artifact paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_document(path: str | Path) -> dict[str, Any]:
    """Load one JSON object from an explicit path without modifying it."""
    resolved = Path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError(f"{resolved} must contain a top-level JSON object.")

    return value


def load_fixture(path: str | Path) -> dict[str, Any]:
    return load_json_document(path)


def load_expected_artifact(path: str | Path) -> dict[str, Any]:
    return load_json_document(path)
