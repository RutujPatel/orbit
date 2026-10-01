"""Projection layer for Real-Data Qualification.

Converts real-world source records (Jira, and later GitHub) into frozen
CSE fixture input contracts without modifying core engine behavior.
"""

from qualification.projection.jira_projection import (
    generate_jira_fixture_id,
    load_frozen_allowlist,
    load_jira_csv_records,
    project_from_raw_rest_capture,
    project_gogreen_jira,
    project_single_work_item,
)

__all__ = [
    "generate_jira_fixture_id",
    "load_frozen_allowlist",
    "load_jira_csv_records",
    "project_from_raw_rest_capture",
    "project_gogreen_jira",
    "project_single_work_item",
]
