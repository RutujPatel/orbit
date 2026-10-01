import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from qualification.reconciliation.reconciler import (
    ReconciliationItem,
    ReconciliationRegister,
    ReconciliationReport,
)


def test_reconciliation_register_four_category_balance():
    reg = ReconciliationRegister(entity_type="jira_issue")
    reg.record("GG-1", "projected_successfully", "Valid")
    reg.record("GG-2", "projected_successfully", "Valid")
    reg.record("GG-3", "projection_failed", "Syntax error in date")
    reg.record("GG-4", "contract_not_representable", "Issue link")
    reg.record("GG-5", "explicitly_excluded", "Outside allowlist")

    assert reg.source_considered == 5
    assert reg.projected_successfully == 2
    assert reg.projection_failed == 1
    assert reg.contract_not_representable == 1
    assert reg.explicitly_excluded == 1
    assert reg.is_balanced() is True


def test_reconciliation_register_invalid_category_raises():
    reg = ReconciliationRegister(entity_type="jira_issue")
    with pytest.raises(ValueError, match="Invalid category"):
        reg.record("GG-1", "unknown_category", "Bad")  # type: ignore[arg-type]


def test_reconciliation_report_serialization_and_markdown():
    report = ReconciliationReport()
    jira_reg = report.get_or_create_register("jira_issue")
    jira_reg.record("GG-10", "projected_successfully", "Valid")
    jira_reg.record("GG-11", "explicitly_excluded", "Excluded")

    assert report.is_balanced() is True
    data = report.to_dict()
    assert data["all_balanced"] is True
    assert "jira_issue" in data["registers"]
    assert data["registers"]["jira_issue"]["source_considered"] == 2

    md = report.to_markdown()
    assert "Source-to-Projection Reconciliation Report" in md
    assert "BALANCED ✅" in md
    assert "`jira_issue`" in md
