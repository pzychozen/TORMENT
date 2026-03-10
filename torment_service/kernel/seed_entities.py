# seed_entities.py
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from typing import List, Dict, Any, Optional


def _as3(x) -> np.ndarray:
    return np.asarray(x, dtype=float).reshape(3)


@dataclass
class SeedEntity:
    """
    External emitted object (NOT part of Ω dynamics).
    Has a position/velocity in R^3 and a trail for visualization.
    Carries a payload snapshot (phases/amplitudes/etc) for provenance.

    vel0: initial velocity at spawn time (frozen; used for logging/diagnostics).
    """
    eid: int
    born_step: int
    channel: int  # 0/1/2 (which of the 3 channels emitted)
    pos: np.ndarray
    vel: np.ndarray
    vel0: np.ndarray  # frozen copy of initial velocity
    payload: Dict[str, Any] = field(default_factory=dict)

    trail: List[np.ndarray] = field(default_factory=list)
    alive: bool = True

    # geometry histories
    r_history: List[float] = field(default_factory=list)
    z_history: List[float] = field(default_factory=list)
    x_history: List[float] = field(default_factory=list)
    y_history: List[float] = field(default_factory=list)

    def push_trail(self, maxlen: int = 200) -> None:
        self.trail.append(self.pos.copy())
        if len(self.trail) > maxlen:
            self.trail.pop(0)


@dataclass
class SeedWorld:
    """
    Simple integrator for emitted seeds (ball + tail).
    Physics here is deliberately simple and decoupled from Ω.
    """
    dt: float = 1.0
    drag: float = 0.02  # velocity damping per step
    drift: np.ndarray = field(default_factory=lambda: np.zeros(3))  # constant drift
    trail_len: int = 200

    entities: List[SeedEntity] = field(default_factory=list)
    _next_id: int = 1

    def spawn(
        self,
        born_step: int,
        channel: int,
        pos: np.ndarray,
        vel: np.ndarray,
        payload: Optional[Dict[str, Any]] = None,
    ) -> SeedEntity:
        v = _as3(vel)
        ent = SeedEntity(
            eid=self._next_id,
            born_step=born_step,
            channel=int(channel),
            pos=_as3(pos),
            vel=v.copy(),
            vel0=v.copy(),  # <- frozen at birth (do NOT touch later)
            payload=dict(payload or {}),
        )

        # include starting point in diagnostics
        r0 = float(np.sqrt(ent.pos[0] ** 2 + ent.pos[1] ** 2))
        z0 = float(ent.pos[2])
        ent.r_history.append(r0)
        ent.z_history.append(z0)
        ent.x_history.append(float(ent.pos[0]))
        ent.y_history.append(float(ent.pos[1]))

        ent.push_trail(self.trail_len)
        self.entities.append(ent)
        self._next_id += 1
        return ent

    def step(self) -> None:
        if not self.entities:
            return

        for e in self.entities:
            if not e.alive:
                continue

            # velocity update (keeps full vector)
            e.vel = (1.0 - self.drag) * e.vel + self.drift

            # position update
            e.pos = e.pos + self.dt * e.vel

            # geometry-only diagnostics
            r = float(np.sqrt(e.pos[0] ** 2 + e.pos[1] ** 2))
            z = float(e.pos[2])
            e.r_history.append(r)
            e.z_history.append(z)
            e.x_history.append(float(e.pos[0]))
            e.y_history.append(float(e.pos[1]))

            e.push_trail(self.trail_len)

    def snapshot_trails(self) -> Dict[int, np.ndarray]:
        """
        Returns {eid: (T,3) array} trails for easy plotting.
        """
        out: Dict[int, np.ndarray] = {}
        for e in self.entities:
            if e.trail:
                out[e.eid] = np.stack(e.trail, axis=0)
        return out
