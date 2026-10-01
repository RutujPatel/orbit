"""Deterministic source description projection for Jira Cloud REST API v3.

Strict Invariants:
- Zero qualification metadata or provenance headers injected.
- Zero Apache author usernames or synthetic identities injected.
- Preserves raw source text exactly without discarding content.
- Generates valid Atlassian Document Format (ADF) document structure.
"""

from __future__ import annotations

from typing import Any


def project_source_description_to_adf(source_description: str | None) -> dict[str, Any] | None:
    """Deterministically project source description into Atlassian Document Format (ADF).
    
    If source_description is None or empty, returns None.
    Contains source text ONLY. Strict invariant: never injects provenance headers or metadata.
    """
    if source_description is None:
        return None
    if not source_description.strip():
        return None

    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": source_description,
                    }
                ],
            }
        ],
    }
