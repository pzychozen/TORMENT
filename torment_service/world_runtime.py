"""Backend-neutral boundary for process-local legacy world dynamics.

This module deliberately has no persistence, substrate, or routing imports.
The port names the one post-write semantic event that consumers need while
keeping world entities and storage implementation details private to adapters.
"""
from __future__ import annotations

from typing import Any, Mapping, Protocol

import numpy as np


class WorldRuntimePort(Protocol):
    """Advance process-local world state for one completed post-write step."""

    def advance_for_post_write(self, *, step: int) -> None:
        """Advance the world without publishing durable memory truth."""


class LegacyWorldRuntime(WorldRuntimePort):
    """Thin adapter over the one ``MemoryGraph`` selected by legacy Fabric."""

    def __init__(self, graph: Any) -> None:
        self._graph = graph

    def advance_for_post_write(self, *, step: int) -> None:
        self._graph.step_world(step=int(step), classify_every=50, log_every=1)


def legacy_world_vec3(value: Any, default: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> np.ndarray:
    """Return the exact legacy ``MemoryGraph._vec3`` genesis transformation."""
    if value is None:
        return np.asarray(default, dtype=float)
    vector = np.asarray(value, dtype=float).reshape(-1)
    if vector.size == 0:
        return np.asarray(default, dtype=float)
    if vector.size == 1:
        return np.asarray([float(vector[0]), 0.0, 0.0], dtype=float)
    if vector.size == 2:
        return np.asarray([float(vector[0]), float(vector[1]), 0.0], dtype=float)
    return np.asarray([float(vector[0]), float(vector[1]), float(vector[2])], dtype=float)


def legacy_world_genesis_payload(payload: Mapping[str, Any]) -> dict[str, list[float]]:
    """Derive only the durable genesis kinematic fields legacy writes.

    ``born_step`` and ``channel`` remain structural facts, just as they do in
    ``MemoryGraph``; this helper deliberately does not create a broader world
    mutation surface.
    """
    pos = legacy_world_vec3(payload.get("seed_pos0"))
    vel = legacy_world_vec3(payload.get("seed_v0"))
    return {"pos": pos.tolist(), "vel": vel.tolist(), "vel0": vel.tolist()}


__all__ = [
    "LegacyWorldRuntime",
    "WorldRuntimePort",
    "legacy_world_genesis_payload",
    "legacy_world_vec3",
]
