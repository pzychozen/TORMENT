"""Neutral Character drift measurement boundary.

This module retains the legacy CharacterStore and makes no native storage
decision. It separates the existing measurement/state transition from the
later gravity-correction mutation so a qualified native reader cannot acquire
generic memory or motif mutation authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from .character import CharacterSeed, CharacterState, measure_drift


class CharacterDriftMeasurementStatus(str, Enum):
    NOT_DUE = "NOT_DUE"
    SEED_UNAVAILABLE = "SEED_UNAVAILABLE"
    REINFORCED_EFFECTIVE_NOOP = "REINFORCED_EFFECTIVE_NOOP"
    MEASURED = "MEASURED"
    CHARACTER_GRAVITY_CORRECTION_REQUIRED = "CHARACTER_GRAVITY_CORRECTION_REQUIRED"


@dataclass(frozen=True)
class CharacterDriftPostWriteRequest:
    """The narrow existing post-write facts Character measurement consumes."""

    workspace_id: str
    agent_id: str
    current_step: int
    stored: bool
    storage_outcome: str

    def __post_init__(self) -> None:
        if not isinstance(self.workspace_id, str) or not self.workspace_id:
            raise ValueError("workspace_id must be non-empty")
        if not isinstance(self.agent_id, str) or not self.agent_id:
            raise ValueError("agent_id must be non-empty")
        if not isinstance(self.current_step, int) or isinstance(self.current_step, bool):
            raise ValueError("current_step must be an integer")
        if type(self.stored) is not bool:
            raise ValueError("stored must be a boolean")
        if self.storage_outcome not in {"NO_WRITE", "REINFORCED_EXISTING", "CREATED_NEW"}:
            raise ValueError("storage_outcome is invalid")


@dataclass(frozen=True)
class CharacterDriftMeasurementResult:
    """Read/state outcome; it grants neither memory nor motif write authority."""

    status: CharacterDriftMeasurementStatus
    seed: CharacterSeed | None = None
    drift: Mapping[str, Any] | None = None
    high_drift: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.status, CharacterDriftMeasurementStatus):
            raise ValueError("status must be CharacterDriftMeasurementStatus")
        if self.seed is not None and not isinstance(self.seed, CharacterSeed):
            raise ValueError("seed must be CharacterSeed or None")
        if self.drift is not None:
            object.__setattr__(self, "drift", MappingProxyType(dict(self.drift)))
        if type(self.high_drift) is not bool:
            raise ValueError("high_drift must be a boolean")

    @property
    def measured(self) -> bool:
        return self.status in {
            CharacterDriftMeasurementStatus.MEASURED,
            CharacterDriftMeasurementStatus.CHARACTER_GRAVITY_CORRECTION_REQUIRED,
        }


class CharacterDriftRuntimePort(Protocol):
    def measure_for_post_write(
        self, request: CharacterDriftPostWriteRequest,
    ) -> CharacterDriftMeasurementResult:
        """Measure and persist CharacterState through retained external state."""


def persist_character_drift_state(
    *, store: Any, workspace_id: str, agent_id: str, seed_id: str,
    previous_state: CharacterState | None, current_step: int, drift: Mapping[str, Any],
) -> CharacterState:
    """Preserve the legacy CharacterState update, history cap, and save path."""
    state = previous_state
    if state is None:
        state = CharacterState(workspace_id=workspace_id, agent_id=agent_id, seed_id=seed_id)
    state.drift_score = float(drift["drift_score"])
    state.drift_direction = str(drift["drift_direction"])
    state.distance_to_seed = float(drift["distance_to_seed"])
    state.seed_basin_phi = float(drift.get("seed_basin_phi", 0.0))
    state.seed_basin_kappa = float(drift.get("seed_basin_kappa", 0.0))
    state.seed_basin_tension = float(drift.get("seed_basin_tension", 0.0))
    state.seed_basin_role = str(drift.get("seed_basin_role", "plateau"))
    state.core_count = int(drift.get("core_count", 0))
    state.relational_count = int(drift.get("relational_count", 0))
    state.situational_count = int(drift.get("situational_count", 0))
    state.drift_history.append((int(current_step), float(drift["drift_score"])))
    state.drift_history = state.drift_history[-50:]
    store.save_state(workspace_id, state)
    return state


class LegacyCharacterDriftRuntime:
    """Exact Character graph/cache measurement behind the neutral port."""

    def __init__(
        self, *, character_enabled: bool, drift_every: int, seed_id: str,
        store: Any, graph: Any, motif_registry: Any,
    ) -> None:
        self._character_enabled = bool(character_enabled)
        self._drift_every = int(drift_every)
        self._seed_id = str(seed_id or "").strip()
        self._store = store
        self._graph = graph
        self._motif_registry = motif_registry

    def measure_for_post_write(
        self, request: CharacterDriftPostWriteRequest,
    ) -> CharacterDriftMeasurementResult:
        if not _due(self._character_enabled, self._drift_every, request):
            return CharacterDriftMeasurementResult(CharacterDriftMeasurementStatus.NOT_DUE)
        if not self._seed_id:
            return CharacterDriftMeasurementResult(CharacterDriftMeasurementStatus.SEED_UNAVAILABLE)
        seed = self._store.load_seed(request.workspace_id, self._seed_id)
        if seed is None or not seed.seed_motif_id:
            return CharacterDriftMeasurementResult(CharacterDriftMeasurementStatus.SEED_UNAVAILABLE)
        # This order intentionally retains the old reinforcement oddity: it
        # enters the outer gate and resolves seed state but makes no measure.
        if request.storage_outcome != "CREATED_NEW":
            return CharacterDriftMeasurementResult(
                CharacterDriftMeasurementStatus.REINFORCED_EFFECTIVE_NOOP, seed=seed,
            )
        prior = self._store.load_state(request.workspace_id, request.agent_id)
        drift = measure_drift(
            graph=self._graph, motif_registry=self._motif_registry, coherence_field=None,
            seed=seed, agent_id=request.agent_id, current_step=request.current_step,
            previous_state=prior,
        )
        persist_character_drift_state(
            store=self._store, workspace_id=request.workspace_id, agent_id=request.agent_id,
            seed_id=self._seed_id, previous_state=prior, current_step=request.current_step, drift=drift,
        )
        high = _high_drift(seed, drift)
        return CharacterDriftMeasurementResult(
            CharacterDriftMeasurementStatus.CHARACTER_GRAVITY_CORRECTION_REQUIRED if high
            else CharacterDriftMeasurementStatus.MEASURED,
            seed=seed, drift=drift, high_drift=high,
        )


def _due(enabled: bool, drift_every: int, request: CharacterDriftPostWriteRequest) -> bool:
    return bool(enabled and request.stored and request.current_step > 0 and request.current_step % drift_every == 0)


def _high_drift(seed: CharacterSeed, drift: Mapping[str, Any]) -> bool:
    return (
        float(drift["drift_score"]) < -seed.drift_correction_threshold
        and str(drift["drift_direction"]) == "away_seed"
    )


__all__ = [
    "CharacterDriftMeasurementResult", "CharacterDriftMeasurementStatus",
    "CharacterDriftPostWriteRequest", "CharacterDriftRuntimePort",
    "LegacyCharacterDriftRuntime", "persist_character_drift_state",
]
