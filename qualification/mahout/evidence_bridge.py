"""Mahout Evidence Bridge and Relationship Extraction Layer.

Adapts normalized Mahout fixtures into canonical EvidenceBundle containers
and extracts comprehensive structural relationship topologies (Subtasks, Epics,
Issue Links).

Preserves:
- Full ObservationContext with temporal interval and source cutoff.
- Individual EvidenceObservation[JiraIssueState] for each work item.
- Lossless QualityIssue mapping from DataQualityConditions.
- Canonical EvidenceBundle validation.
- Complete structural relationship accounting (in-seed, dependency-covered,
  and external unresolved links).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure orbit repo root and src are on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from shadow_orbit.evidence_assembly import (
    assemble_evidence_bundle,
    validate_evidence_bundle,
)
from shadow_orbit.evidence_types import (
    EntityRef,
    EvidenceBundle,
    EvidenceObservation,
    JiraIssueState,
    ObservationContext,
    ProvenanceRef,
    QualityIssue,
    SourceInstance,
)
from shadow_orbit.jira_evidence_adapter import adapt_jira_evidence
from shadow_orbit.types import NormalizedFixture

DEFAULT_SOURCE_INSTANCE = SourceInstance(
    source_kind="jira",
    instance_id="mahout-jira",
)


@dataclass(frozen=True, slots=True)
class MahoutStructuralLink:
    """An explicit relational reference between source entities."""

    source_key: str
    target_key: str
    relationship_type: str  # 'subtask_parent', 'epic_link', 'issuelink'
    link_name: str  # e.g. 'subtask_of', 'belongs_to_epic', 'relates_to', 'blocks', etc.
    classification: str  # 'internal_to_primary_seed', 'covered_by_structural_dependency', 'external_unselected_mahout', 'external_cross_project'
    is_resolved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_key": self.source_key,
            "target_key": self.target_key,
            "relationship_type": self.relationship_type,
            "link_name": self.link_name,
            "classification": self.classification,
            "is_resolved": self.is_resolved,
        }


@dataclass(frozen=True, slots=True)
class EvidenceBridgeResult:
    """Complete assembled evidence container and structural relationship registry."""

    bundle: EvidenceBundle
    observation_context: ObservationContext
    observations_by_key: dict[str, EvidenceObservation[JiraIssueState]]
    relationships: tuple[MahoutStructuralLink, ...]
    relationship_counts_by_type: dict[str, int]
    relationship_counts_by_classification: dict[str, int]
    total_quality_issues: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle.bundle_id,
            "bundle_version": self.bundle.bundle_version,
            "observation_count": len(self.bundle.observations),
            "total_quality_issues": self.total_quality_issues,
            "relationship_counts_by_type": dict(self.relationship_counts_by_type),
            "relationship_counts_by_classification": dict(self.relationship_counts_by_classification),
            "total_relationships_audited": len(self.relationships),
        }


def extract_mahout_structural_relationships(
    raw_docs: list[dict[str, Any]],
    primary_seed_keys: set[str],
    dependency_keys: set[str],
) -> tuple[MahoutStructuralLink, ...]:
    """Extract and classify all relationship-bearing fields from raw Mahout documents.
    
    Inspects:
    1. Subtask -> Parent ('parent')
    2. Epic Link ('customfield_12311120')
    3. Issue Links ('issuelinks')
    """
    links: list[MahoutStructuralLink] = []
    all_selected = primary_seed_keys | dependency_keys

    for doc in raw_docs:
        s_key = str(doc.get("key", "")).strip()
        fields = doc.get("fields", {}) or {}

        # 1. Subtask -> Parent
        parent_obj = fields.get("parent")
        if isinstance(parent_obj, dict) and parent_obj.get("key"):
            p_key = str(parent_obj["key"]).strip()
            if p_key in primary_seed_keys:
                cls = "internal_to_primary_seed"
            elif p_key in dependency_keys:
                cls = "covered_by_structural_dependency"
            else:
                cls = "external_unselected_mahout"

            links.append(
                MahoutStructuralLink(
                    source_key=s_key,
                    target_key=p_key,
                    relationship_type="subtask_parent",
                    link_name="subtask_of",
                    classification=cls,
                    is_resolved=(p_key in all_selected),
                )
            )

        # 2. Epic Link (customfield_12311120)
        epic_link = fields.get("customfield_12311120")
        if epic_link and isinstance(epic_link, str) and epic_link.strip():
            e_key = epic_link.strip()
            if e_key in primary_seed_keys:
                cls = "internal_to_primary_seed"
            elif e_key in dependency_keys:
                cls = "covered_by_structural_dependency"
            else:
                cls = "external_unselected_mahout"

            links.append(
                MahoutStructuralLink(
                    source_key=s_key,
                    target_key=e_key,
                    relationship_type="epic_link",
                    link_name="belongs_to_epic",
                    classification=cls,
                    is_resolved=(e_key in all_selected),
                )
            )

        # 3. Issue Links (issuelinks)
        raw_issue_links = fields.get("issuelinks") or []
        for lk in raw_issue_links:
            if not isinstance(lk, dict):
                continue
            # Directed link: inward or outward
            link_type = (lk.get("type") or {}).get("name") or "Relates"
            target_obj = lk.get("outwardIssue") or lk.get("inwardIssue")
            if not isinstance(target_obj, dict) or not target_obj.get("key"):
                continue
            t_key = str(target_obj["key"]).strip()

            if t_key in primary_seed_keys:
                cls = "internal_to_primary_seed"
            elif t_key in dependency_keys:
                cls = "covered_by_structural_dependency"
            elif t_key.startswith("MAHOUT-"):
                cls = "external_unselected_mahout"
            else:
                cls = "external_cross_project"

            links.append(
                MahoutStructuralLink(
                    source_key=s_key,
                    target_key=t_key,
                    relationship_type="issuelink",
                    link_name=link_type,
                    classification=cls,
                    is_resolved=(t_key in all_selected),
                )
            )

    links.sort(key=lambda l: (l.relationship_type, l.source_key, l.target_key))
    return tuple(links)


def build_mahout_evidence_bridge(
    normalized_fixture: NormalizedFixture,
    raw_docs: list[dict[str, Any]],
    primary_seed_keys: set[str],
    dependency_keys: set[str],
    bundle_id: str = "mahout-evidence-bundle",
    bundle_version: str = "1.0.0",
    source_instance: SourceInstance = DEFAULT_SOURCE_INSTANCE,
    observation_id: str = "obs-mahout-evidence-1",
) -> EvidenceBridgeResult:
    """Build the complete EvidenceBundle and structural relationship registry."""
    # 1. Adapt Jira evidence
    obs_ctx, jira_obs, quality_issues = adapt_jira_evidence(
        normalized_fixture,
        source_instance=source_instance,
        observation_id=observation_id,
    )

    # 2. Assemble and validate canonical EvidenceBundle
    bundle = assemble_evidence_bundle(
        bundle_id=bundle_id,
        bundle_version=bundle_version,
        jira_context=obs_ctx,
        jira_observations=tuple(jira_obs),
        jira_quality_issues=tuple(quality_issues),
    )
    validate_evidence_bundle(bundle)

    # 3. Index observations by issue key
    obs_by_key = {
        obs.entity_ref.entity_id: obs
        for obs in bundle.observations
        if isinstance(obs, EvidenceObservation) and obs.entity_ref.entity_kind == "jira_issue"
    }

    # 4. Extract structural relationships
    relationships = extract_mahout_structural_relationships(
        raw_docs=raw_docs,
        primary_seed_keys=primary_seed_keys,
        dependency_keys=dependency_keys,
    )

    type_counts: dict[str, int] = {}
    class_counts: dict[str, int] = {}
    for rel in relationships:
        type_counts[rel.relationship_type] = type_counts.get(rel.relationship_type, 0) + 1
        class_counts[rel.classification] = class_counts.get(rel.classification, 0) + 1

    total_qi = len(bundle.quality_issues) + sum(len(obs.quality_issues) for obs in bundle.observations)

    return EvidenceBridgeResult(
        bundle=bundle,
        observation_context=obs_ctx,
        observations_by_key=obs_by_key,
        relationships=relationships,
        relationship_counts_by_type=type_counts,
        relationship_counts_by_classification=class_counts,
        total_quality_issues=total_qi,
    )
