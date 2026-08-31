"""Neutral Character gravity-correction boundary.

Measurement and the additive correction are intentionally distinct Character
operations.  The legacy implementation remains a very small adapter over the
existing :func:`character.gravity_correction`; native implementations can use
the same post-write orchestration without inheriting ``MemoryGraph`` authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from .character import CharacterSeed, gravity_correction


class CharacterGravityCorrectionStatus(str, Enum):
    """The bounded result of one attempted Character correction."""

    NOT_REQUIRED = "NOT_REQUIRED"
    APPLIED = "APPLIED"
    CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED = "CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED"


@dataclass(frozen=True)
class CharacterGravityCorrectionRequest:
    """Facts consumed by the legacy and native additive correction paths."""

    workspace_id: str
    agent_id: str
    step: int
    seed: CharacterSeed
    drift: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name in ("workspace_id", "agent_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.step, int) or isinstance(self.step, bool) or self.step < 0:
            raise ValueError("step must be a non-negative integer")
        if not isinstance(self.seed, CharacterSeed):
            raise ValueError("seed must be CharacterSeed")
        object.__setattr__(self, "drift", MappingProxyType(dict(self.drift)))


@dataclass(frozen=True)
class CharacterGravityCorrectionResult:
    """A correction result with no graph or native mutation authority."""

    status: CharacterGravityCorrectionStatus
    correction_applied: bool
    correction_identity: Any | None = None
    selected_concept: str | None = None
    correction_text: str | None = None
    motif_status: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, CharacterGravityCorrectionStatus):
            raise ValueError("status must be CharacterGravityCorrectionStatus")
        if type(self.correction_applied) is not bool:
            raise ValueError("correction_applied must be a boolean")


class CharacterGravityCorrectionRuntimePort(Protocol):
    def correct_for_post_write(
        self, request: CharacterGravityCorrectionRequest,
    ) -> CharacterGravityCorrectionResult:
        """Perform only the additive Character correction boundary."""


class LegacyCharacterGravityCorrectionRuntime:
    """Delegate exactly to legacy ``gravity_correction`` without translation."""

    def __init__(self, *, graph: Any, motif_registry: Any, embedder: Any) -> None:
        self._graph = graph
        self._motif_registry = motif_registry
        self._embedder = embedder

    def correct_for_post_write(
        self, request: CharacterGravityCorrectionRequest,
    ) -> CharacterGravityCorrectionResult:
        result = gravity_correction(
            graph=self._graph,
            motif_registry=self._motif_registry,
            embedder=self._embedder,
            seed=request.seed,
            agent_id=request.agent_id,
            step=request.step,
            drift_info=dict(request.drift),
        )
        if not bool(result.get("correction_applied", False)):
            return CharacterGravityCorrectionResult(
                CharacterGravityCorrectionStatus.NOT_REQUIRED,
                False,
            )
        return CharacterGravityCorrectionResult(
            CharacterGravityCorrectionStatus.APPLIED,
            True,
            correction_identity=result.get("correction_eid"),
            selected_concept=result.get("concept_reinforced"),
            correction_text=(
                f"[identity reinforcement] {result['concept_reinforced']}"
                if isinstance(result.get("concept_reinforced"), str)
                else None
            ),
        )


__all__ = [
    "CharacterGravityCorrectionResult",
    "CharacterGravityCorrectionRuntimePort",
    "CharacterGravityCorrectionStatus",
    "CharacterGravityCorrectionRequest",
    "LegacyCharacterGravityCorrectionRuntime",
]
