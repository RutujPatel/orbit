"""Reconciliation accounting layer for Real-Data Qualification.

Implements the four-category accounting model:
source_considered = projected_successfully + projection_failed + contract_not_representable + explicitly_excluded
"""

from qualification.reconciliation.reconciler import (
    ReconciliationCategory,
    ReconciliationItem,
    ReconciliationRegister,
    ReconciliationReport,
)

__all__ = [
    "ReconciliationCategory",
    "ReconciliationItem",
    "ReconciliationRegister",
    "ReconciliationReport",
]
