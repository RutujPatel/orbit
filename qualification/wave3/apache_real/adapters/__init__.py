"""Canonical adapter package for real Apache Software Foundation Jira and GitHub evidence."""

from .apache_alignment_adapter import (
    build_cross_system_alignment,
    compute_cross_system_alignment_coherence,
)
from .apache_bundle_builder import (
    build_apache_evidence_bundle,
    load_apache_raw_fixtures,
)
from .apache_github_adapter import (
    APACHE_GITHUB_SOURCE,
    adapt_apache_github_commit,
    adapt_apache_github_commit_to_state,
    adapt_apache_github_pr,
    adapt_apache_github_pr_to_state,
)
from .apache_jira_adapter import (
    APACHE_JIRA_SOURCE,
    SUPPORTED_APACHE_PROJECTS,
    adapt_apache_jira_issue,
    adapt_apache_jira_issue_to_state,
    is_valid_apache_jira_key,
    parse_iso_datetime,
)

__all__ = [
    "APACHE_JIRA_SOURCE",
    "APACHE_GITHUB_SOURCE",
    "SUPPORTED_APACHE_PROJECTS",
    "parse_iso_datetime",
    "is_valid_apache_jira_key",
    "adapt_apache_jira_issue_to_state",
    "adapt_apache_jira_issue",
    "adapt_apache_github_pr_to_state",
    "adapt_apache_github_pr",
    "adapt_apache_github_commit_to_state",
    "adapt_apache_github_commit",
    "compute_cross_system_alignment_coherence",
    "build_cross_system_alignment",
    "load_apache_raw_fixtures",
    "build_apache_evidence_bundle",
]
