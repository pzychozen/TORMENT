"""Fabric-facing legacy motif runtime boundary.

This module intentionally delegates to :class:`MotifRegistry`. It provides
the narrow ordinary-ingest seam without making a storage-selection decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

import numpy as np

from .motifs import MotifRegistry


@dataclass(frozen=True)
class MotifMutationOutcome:
    """The observable motif result required by Fabric's ordinary ingest path."""

    affected_runtime_ids: tuple[str, ...]
    created_runtime_id: Optional[str]


class MotifRuntimePort(Protocol):
    """Minimal motif operations consumed by ordinary ``TormentFabric.ingest``."""

    def attach_or_create(
        self,
        embedding: np.ndarray,
        *,
        memory_eid: int,
        agent_id: str,
        summary: str,
        attach_threshold: float,
    ) -> MotifMutationOutcome: ...

    def project_coherence_field_rows(self) -> List[Dict[str, Any]]: ...

    def update_entropy_and_suggest(
        self,
        *,
        target_n: int,
        entropy_high: float,
        sim_threshold: float,
        max_suggestions: int,
        auto_merge: bool,
        auto_merge_trigger: float,
    ) -> Dict[str, Any]: ...


class LegacyMotifRuntimeAdapter:
    """Delegate the Fabric motif boundary to the existing ``MotifRegistry``."""

    def __init__(self, registry: MotifRegistry) -> None:
        self._registry = registry

    def attach_or_create(
        self,
        embedding: np.ndarray,
        *,
        memory_eid: int,
        agent_id: str,
        summary: str,
        attach_threshold: float,
    ) -> MotifMutationOutcome:
        affected_runtime_ids, created_runtime_id = self._registry.attach_or_create(
            embedding,
            memory_eid=memory_eid,
            agent_id=agent_id,
            summary=summary,
            attach_threshold=attach_threshold,
        )
        return MotifMutationOutcome(
            tuple(affected_runtime_ids),
            created_runtime_id,
        )

    def project_coherence_field_rows(self) -> List[Dict[str, Any]]:
        """Return the current whole-domain legacy rows in registry ``items`` order."""
        rows: List[Dict[str, Any]] = []
        for motif_id, motif in self._registry.motifs.items():
            rows.append({
                "motif_id": motif_id,
                "label": getattr(motif, "label", motif_id),
                "centroid": list(getattr(motif, "centroid", []) or []),
                "strength": float(getattr(motif, "strength", 0.0) or 0.0),
                "stability_score": float(getattr(motif, "stability_score", 0.0) or 0.0),
                "members": list(getattr(motif, "members", []) or []),
                "radius": (
                    float(self._registry._motif_radius(motif))
                    if hasattr(self._registry, "_motif_radius")
                    else 0.0
                ),
            })
        return rows

    def update_entropy_and_suggest(
        self,
        *,
        target_n: int,
        entropy_high: float,
        sim_threshold: float,
        max_suggestions: int,
        auto_merge: bool,
        auto_merge_trigger: float,
    ) -> Dict[str, Any]:
        return self._registry.update_entropy_and_suggest(
            target_n=target_n,
            entropy_high=entropy_high,
            sim_threshold=sim_threshold,
            max_suggestions=max_suggestions,
            auto_merge=auto_merge,
            auto_merge_trigger=auto_merge_trigger,
        )
