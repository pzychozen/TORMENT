"""Read-only, backend-neutral motif geometry for domain consumers.

This port intentionally carries no motif, bridge, or routing mutation
authority.  It lets policy consumers compare the same immutable runtime
geometry whether its current truth is legacy ``MotifRegistry`` state or a
qualified native multi-scope recovery object.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

import numpy as np

from .motifs import MotifRegistry


@dataclass(frozen=True)
class RuntimeMotifGeometry:
    domain_id: str
    runtime_motif_id: str
    centroid: tuple[float, ...]
    strength: float
    stability_score: float
    member_count: int
    created_ts: int
    last_active_ts: int

    def centroid_np(self) -> np.ndarray:
        return np.asarray(self.centroid, dtype=np.float32)


@runtime_checkable
class MotifGeometryPort(Protocol):
    """The entire geometry dependency available to domain/bridge readers."""

    def domain_ids(self) -> tuple[str, ...]: ...

    def list_motifs(self, domain_id: str) -> tuple[RuntimeMotifGeometry, ...]: ...

    def domain_centroid(self, domain_id: str, expected_dimension: int) -> np.ndarray: ...


class LegacyMotifGeometryAdapter:
    """Expose existing ``MotifRegistry`` geometry without changing its law."""

    def __init__(self, registries: Mapping[str, MotifRegistry]) -> None:
        if not isinstance(registries, Mapping) or not registries:
            raise ValueError("legacy geometry requires a non-empty registry mapping")
        if any(not isinstance(domain, str) or not domain or not isinstance(registry, MotifRegistry)
               for domain, registry in registries.items()):
            raise ValueError("legacy geometry requires domain-keyed MotifRegistry values")
        self._registries = dict(registries)

    def domain_ids(self) -> tuple[str, ...]:
        return tuple(self._registries)

    def list_motifs(self, domain_id: str) -> tuple[RuntimeMotifGeometry, ...]:
        registry = self._registry(domain_id)
        return tuple(
            RuntimeMotifGeometry(
                domain_id=motif.domain_id,
                runtime_motif_id=motif.motif_id,
                centroid=tuple(float(value) for value in motif.centroid),
                strength=float(motif.strength),
                stability_score=float(motif.stability_score),
                member_count=len(motif.members),
                created_ts=int(motif.created_ts),
                last_active_ts=int(motif.last_active_ts),
            )
            for motif in registry.motifs.values()
        )

    def domain_centroid(self, domain_id: str, expected_dimension: int) -> np.ndarray:
        return self._registry(domain_id).domain_centroid(expected_dimension)

    def _registry(self, domain_id: str) -> MotifRegistry:
        try:
            return self._registries[domain_id]
        except KeyError as exc:
            raise KeyError(f"geometry is not available for legacy domain {domain_id!r}") from exc


class NativeMotifGeometryAdapter:
    """Read-only geometry over explicitly recovered E4C shared lanes.

    ``domain_ids`` is caller-owned ordering evidence.  The adapter never
    guesses an unadmitted domain or derives a motif namespace from its name.
    """

    def __init__(self, recovered_runtime: Any, *, domain_ids: tuple[str, ...], expected_dimension: int) -> None:
        if not isinstance(domain_ids, tuple) or not domain_ids or any(
            not isinstance(domain, str) or not domain for domain in domain_ids
        ) or len(set(domain_ids)) != len(domain_ids):
            raise ValueError("native geometry requires distinct explicit domain IDs")
        if not isinstance(expected_dimension, int) or isinstance(expected_dimension, bool) or expected_dimension < 1:
            raise ValueError("native geometry expected_dimension must be positive")
        if not hasattr(recovered_runtime, "lookup_shared"):
            raise ValueError("native geometry requires a recovered multi-scope runtime")
        for domain_id in domain_ids:
            try:
                recovered_runtime.lookup_shared(domain_id)
            except Exception as exc:
                raise ValueError(f"native geometry domain is not admitted: {domain_id!r}") from exc
        self._runtime = recovered_runtime
        self._domain_ids = domain_ids
        self._expected_dimension = expected_dimension

    def domain_ids(self) -> tuple[str, ...]:
        return self._domain_ids

    def list_motifs(self, domain_id: str) -> tuple[RuntimeMotifGeometry, ...]:
        scope = self._scope(domain_id)
        with scope.open_readers() as readers:
            motifs = readers.motifs.list_runtime_motifs(
                motif_alias_namespace_id=scope.fabric_routing_scope.motif_alias_namespace_id,
                domain_id=domain_id,
                semantic_scope_id=scope.memory_runtime_scope.semantic_scope_id,
            )
        return tuple(
            RuntimeMotifGeometry(
                domain_id=item.read_model.domain_id,
                runtime_motif_id=item.read_model.runtime_motif_id,
                centroid=tuple(float(value) for value in item.read_model.centroid),
                strength=float(item.read_model.strength),
                stability_score=float(item.read_model.stability_score),
                member_count=int(item.read_model.member_count),
                created_ts=int(item.read_model.created_ts),
                last_active_ts=int(item.read_model.last_active_ts),
            )
            for item in motifs
        )

    def domain_centroid(self, domain_id: str, expected_dimension: int) -> np.ndarray:
        if expected_dimension != self._expected_dimension:
            raise ValueError("native geometry dimension differs from its qualified lane")
        scope = self._scope(domain_id)
        with scope.open_readers() as readers:
            return readers.motifs.domain_centroid(
                motif_alias_namespace_id=scope.fabric_routing_scope.motif_alias_namespace_id,
                domain_id=domain_id,
                dimension=expected_dimension,
                semantic_scope_id=scope.memory_runtime_scope.semantic_scope_id,
            )

    def _scope(self, domain_id: str) -> Any:
        if domain_id not in self._domain_ids:
            raise KeyError(f"geometry is not available for unadmitted native domain {domain_id!r}")
        return self._runtime.lookup_shared(domain_id)


__all__ = [
    "LegacyMotifGeometryAdapter",
    "MotifGeometryPort",
    "NativeMotifGeometryAdapter",
    "RuntimeMotifGeometry",
]
