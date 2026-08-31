"""Qualified native Character drift measurement, without Character mutation.

The implementation receives already-qualified read ports. It never accepts a
SQLite connection, semantic writer, MemoryGraph, or MotifRegistry, and it
persists only the retained external CharacterStore state.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import numpy as np

from torment_service.character import (
    CharacterDriftMemoryObservation,
    CharacterSeed,
    measure_drift_from_observations,
)
from torment_service.character_drift_runtime import (
    CharacterDriftMeasurementResult,
    CharacterDriftMeasurementStatus,
    CharacterDriftPostWriteRequest,
    _due,
    _high_drift,
    persist_character_drift_state,
)
from torment_service.memory_runtime_access import (
    PostWriteMemoryEnumerationPort,
    PostWriteMemoryReadPort,
)

from .errors import SubstrateConfigurationError
from .motif_runtime_reader import NativeMotifRuntimeReader


@dataclass(frozen=True)
class NativeCharacterDriftRuntimeConfiguration:
    workspace_id: str
    agent_id: str
    seed_id: str
    domain_id: str
    motif_alias_namespace_id: UUID
    semantic_scope_id: UUID
    expected_dimension: int
    character_enabled: bool
    drift_every: int
    embedding_cache_enabled: bool = True

    def __post_init__(self) -> None:
        for name in ("workspace_id", "agent_id", "domain_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.seed_id, str):
            raise ValueError("seed_id must be text")
        if not isinstance(self.motif_alias_namespace_id, UUID):
            raise ValueError("motif_alias_namespace_id must be a UUID")
        if not isinstance(self.semantic_scope_id, UUID):
            raise ValueError("semantic_scope_id must be a UUID")
        if not isinstance(self.expected_dimension, int) or isinstance(self.expected_dimension, bool) or self.expected_dimension < 1:
            raise ValueError("expected_dimension must be positive")
        if type(self.character_enabled) is not bool:
            raise ValueError("character_enabled must be a boolean")
        if not isinstance(self.drift_every, int) or isinstance(self.drift_every, bool):
            raise ValueError("drift_every must be an integer")
        if type(self.embedding_cache_enabled) is not bool:
            raise ValueError("embedding_cache_enabled must be a boolean")


class NativeCharacterDriftRuntime:
    """C1A native read/state projection over qualified native boundaries."""

    def __init__(
        self, *, configuration: NativeCharacterDriftRuntimeConfiguration,
        store: Any, memory_read: PostWriteMemoryReadPort,
        memory_enumeration: PostWriteMemoryEnumerationPort,
        motif_reader: NativeMotifRuntimeReader,
    ) -> None:
        if not isinstance(configuration, NativeCharacterDriftRuntimeConfiguration):
            raise ValueError("configuration must be NativeCharacterDriftRuntimeConfiguration")
        if not configuration.embedding_cache_enabled:
            raise SubstrateConfigurationError(
                "C1A refuses native Character measurement when TORMENT_GRAPH_EMB_CACHE is disabled"
            )
        if not isinstance(motif_reader, NativeMotifRuntimeReader):
            raise ValueError("motif_reader must be NativeMotifRuntimeReader")
        self._configuration = configuration
        self._store = store
        self._memory_read = memory_read
        self._memory_enumeration = memory_enumeration
        self._motif_reader = motif_reader

    def measure_for_post_write(
        self, request: CharacterDriftPostWriteRequest,
    ) -> CharacterDriftMeasurementResult:
        config = self._configuration
        if request.workspace_id != config.workspace_id or request.agent_id != config.agent_id:
            raise SubstrateConfigurationError("Character request does not match the qualified native scope")
        if not _due(config.character_enabled, config.drift_every, request):
            return CharacterDriftMeasurementResult(CharacterDriftMeasurementStatus.NOT_DUE)
        seed_id = config.seed_id.strip()
        if not seed_id:
            return CharacterDriftMeasurementResult(CharacterDriftMeasurementStatus.SEED_UNAVAILABLE)
        seed = self._store.load_seed(request.workspace_id, seed_id)
        if seed is None or not seed.seed_motif_id:
            return CharacterDriftMeasurementResult(CharacterDriftMeasurementStatus.SEED_UNAVAILABLE)
        if request.storage_outcome != "CREATED_NEW":
            return CharacterDriftMeasurementResult(
                CharacterDriftMeasurementStatus.REINFORCED_EFFECTIVE_NOOP, seed=seed,
            )

        observations = [
            CharacterDriftMemoryObservation(view.eid, view.payload)
            for view in self._memory_enumeration.list_current()
        ]
        prior = self._store.load_state(request.workspace_id, request.agent_id)
        drift = measure_drift_from_observations(
            observations=observations,
            cached_embedding=self._cached_embedding,
            seed_centroid=lambda average: self._seed_centroid(seed, average),
            coherence_field=None,
            seed=seed,
            agent_id=request.agent_id,
            current_step=request.current_step,
            previous_state=prior,
        )
        persist_character_drift_state(
            store=self._store, workspace_id=request.workspace_id, agent_id=request.agent_id,
            seed_id=seed_id, previous_state=prior, current_step=request.current_step, drift=drift,
        )
        high = _high_drift(seed, drift)
        return CharacterDriftMeasurementResult(
            CharacterDriftMeasurementStatus.CHARACTER_GRAVITY_CORRECTION_REQUIRED if high
            else CharacterDriftMeasurementStatus.MEASURED,
            seed=seed, drift=drift, high_drift=high,
        )

    def _cached_embedding(self, eid: int) -> np.ndarray | None:
        qualified = self._memory_read.read_current_embedding(
            eid, expected_dimension=self._configuration.expected_dimension,
        )
        if qualified is None:
            return None
        return _legacy_cache_normalize(
            qualified.as_float32(), expected_dimension=self._configuration.expected_dimension,
        )

    def _seed_centroid(self, seed: CharacterSeed, average: np.ndarray) -> np.ndarray:
        # Current qualified native seed motif is the first geometry branch.
        motifs = self._motif_reader.list_runtime_motifs(
            motif_alias_namespace_id=self._configuration.motif_alias_namespace_id,
            domain_id=self._configuration.domain_id,
            semantic_scope_id=self._configuration.semantic_scope_id,
        )
        for motif in motifs:
            if motif.read_model.runtime_motif_id == seed.seed_motif_id:
                return np.asarray(motif.read_model.centroid, dtype=np.float32)

        # The second branch resolves *only* source-namespace-bound EIDs through
        # the qualified memory port. No global or bare EID lookup exists here.
        seed_embeddings: list[np.ndarray] = []
        for seed_eid in seed.seed_eids:
            if not isinstance(seed_eid, int) or isinstance(seed_eid, bool) or seed_eid < 0:
                raise SubstrateConfigurationError("Character seed contains an invalid namespaced EID")
            vector = self._cached_embedding(seed_eid)
            if vector is not None:
                seed_embeddings.append(vector)
        return np.mean(seed_embeddings, axis=0) if seed_embeddings else average


def _legacy_cache_normalize(vector: Any, *, expected_dimension: int) -> np.ndarray:
    """Exact ``MemoryGraph._normalize`` semantics for C1A's cache projection."""
    value = np.asarray(vector, dtype=np.float32).reshape(-1)
    if value.size == 0:
        return np.zeros(expected_dimension, dtype=np.float32)
    if int(value.shape[0]) != int(expected_dimension):
        if value.size < int(expected_dimension):
            value = np.pad(value, (0, int(expected_dimension) - int(value.size)))
        else:
            value = value[:int(expected_dimension)]
    norm = float(np.linalg.norm(value) + 1e-12)
    return (value / norm).astype(np.float32)


__all__ = [
    "NativeCharacterDriftRuntime", "NativeCharacterDriftRuntimeConfiguration",
]
