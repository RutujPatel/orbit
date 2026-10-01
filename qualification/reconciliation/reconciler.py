"""Four-category reconciliation accounting engine.

Implements exact accounting across:
    source_considered
    = projected_successfully
    + projection_failed
    + contract_not_representable
    + explicitly_excluded

Every recognized entity collection must reconcile before entering the frozen
CSE validation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ReconciliationCategory = Literal[
    "projected_successfully",
    "projection_failed",
    "contract_not_representable",
    "explicitly_excluded",
]

VALID_CATEGORIES: frozenset[str] = frozenset({
    "projected_successfully",
    "projection_failed",
    "contract_not_representable",
    "explicitly_excluded",
})


@dataclass(frozen=True, slots=True)
class ReconciliationItem:
    """An individual source entity accounted for during projection."""

    identifier: str
    category: ReconciliationCategory
    reason: str
    content_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "category": self.category,
            "reason": self.reason,
            "content_hash": self.content_hash,
            "metadata": dict(self.metadata),
        }


@dataclass
class ReconciliationRegister:
    """Accounting register for an entity collection (e.g. jira_issue)."""

    entity_type: str
    items: list[ReconciliationItem] = field(default_factory=list)

    def record(
        self,
        identifier: str,
        category: ReconciliationCategory,
        reason: str,
        content_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ReconciliationItem:
        """Record an entity in this register under one of the 4 categories."""
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category!r}. Must be one of {VALID_CATEGORIES}")

        item = ReconciliationItem(
            identifier=identifier,
            category=category,
            reason=reason,
            content_hash=content_hash,
            metadata=dict(metadata or {}),
        )
        self.items.append(item)
        return item

    @property
    def source_considered(self) -> int:
        return len(self.items)

    @property
    def projected_successfully(self) -> int:
        return sum(1 for item in self.items if item.category == "projected_successfully")

    @property
    def projection_failed(self) -> int:
        return sum(1 for item in self.items if item.category == "projection_failed")

    @property
    def contract_not_representable(self) -> int:
        return sum(1 for item in self.items if item.category == "contract_not_representable")

    @property
    def explicitly_excluded(self) -> int:
        return sum(1 for item in self.items if item.category == "explicitly_excluded")

    def is_balanced(self) -> bool:
        """Verify the fundamental 4-category conservation equation."""
        return self.source_considered == (
            self.projected_successfully
            + self.projection_failed
            + self.contract_not_representable
            + self.explicitly_excluded
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "is_balanced": self.is_balanced(),
            "source_considered": self.source_considered,
            "projected_successfully": self.projected_successfully,
            "projection_failed": self.projection_failed,
            "contract_not_representable": self.contract_not_representable,
            "explicitly_excluded": self.explicitly_excluded,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class ReconciliationReport:
    """Comprehensive multi-collection reconciliation report."""

    registers: dict[str, ReconciliationRegister] = field(default_factory=dict)
    notes: str = ""

    def get_or_create_register(self, entity_type: str) -> ReconciliationRegister:
        if entity_type not in self.registers:
            self.registers[entity_type] = ReconciliationRegister(entity_type=entity_type)
        return self.registers[entity_type]

    def is_balanced(self) -> bool:
        if not self.registers:
            return True
        return all(reg.is_balanced() for reg in self.registers.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "all_balanced": self.is_balanced(),
            "registers": {
                name: reg.to_dict() for name, reg in self.registers.items()
            },
            "notes": self.notes,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Source-to-Projection Reconciliation Report",
            "",
            f"**Overall Status**: {'BALANCED ✅' if self.is_balanced() else 'UNBALANCED ❌'}",
            "",
            "| Entity Collection | Considered | Projected | Projection Failed | Not Representable | Excluded | Balanced? |",
            "|---|---|---|---|---|---|---|",
        ]
        for name, reg in sorted(self.registers.items()):
            lines.append(
                f"| `{name}` | {reg.source_considered} | {reg.projected_successfully} | "
                f"{reg.projection_failed} | {reg.contract_not_representable} | "
                f"{reg.explicitly_excluded} | {'YES' if reg.is_balanced() else 'NO'} |"
            )
        lines.append("")
        return "\n".join(lines)
