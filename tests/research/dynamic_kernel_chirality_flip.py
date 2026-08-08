"""tests/research/dynamic_kernel_chirality_flip.py

Standalone, test-adjacent, DETERMINISTIC reconstruction of ONLY the signed-chirality
transition SURFACE (per the accepted `chirality_flip` contract). It is NOT the lost
flip-hunting simulation.

This is a MODULE, not a runnable script. It exposes pure helpers plus frozen result
types and performs NO I/O: no CLI, no plots, no output files, no randomness, and no
background/runtime behavior. It never STEPS the kernel (it never calls the trajectory
`step` method) -- it only reads the chirality surface and the single-update chirality
memory.

Reconstructed surface (source-supported, per the contract):
  * ``jeff(omega)``            -- signed triad area J_eff = Im(O1*conj(O2)*O3);
  * ``normalized_chirality``   -- J_eff / (1 + |J_eff|), bounded in (-1, 1);
  * ``chirality_sign``         -- sign(J_eff) in {-1, 0, +1};
  * ``is_flip(a, b)``          -- PAIRWISE detection: a "flip" is ONLY an opposite
                                 effective chirality sign between two states;
  * ``z_mem_response``         -- the cognitive ``z_mem`` after ONE
                                 ``CognitiveCore.update`` (single update).

NOT reconstructed (HOLD): the flip-hunting loop, the A-D scenario sweep, seed-force
reversal, flip-count tables, PNG reproduction, kernel trajectory stepping, and the
other lost simulation target. The lost driver scripts are not recreated.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np

from torment_service.cognitive_core import CognitiveCore, CognitiveCoreState
from torment_service.kernel.model_core import (
    ModelParams,
    ModelState,
)


def jeff(omega: Sequence[complex]) -> float:
    """Signed triad area ``Im(O1 * conj(O2) * O3)`` -- the canonical J_eff surface."""
    o1, o2, o3 = np.asarray(omega, dtype=complex).reshape(3)
    return float(np.imag(o1 * np.conj(o2) * o3))


def normalized_chirality(omega: Sequence[complex]) -> float:
    """Bounded normalized effective chirality ``J_eff / (1 + |J_eff|)`` in (-1, 1)."""
    j = jeff(omega)
    return j / (1.0 + abs(j))


def chirality_sign(omega: Sequence[complex]) -> int:
    """Effective chirality sign ``sign(J_eff)`` in {-1, 0, +1}."""
    j = jeff(omega)
    if j > 0.0:
        return 1
    if j < 0.0:
        return -1
    return 0


def is_flip(omega_a: Sequence[complex], omega_b: Sequence[complex]) -> bool:
    """PAIRWISE flip: True iff the two states have OPPOSITE nonzero chirality signs.

    A "flip" is defined ONLY as a signed-J_eff sign change (per the contract). It
    depends on nothing else -- not magnitude, not z_mem, not seeds, not a trajectory.
    """
    sa, sb = chirality_sign(omega_a), chirality_sign(omega_b)
    return sa != 0 and sb != 0 and sa != sb


@dataclass(frozen=True)
class ChiralitySample:
    """Structured in-memory snapshot of the chirality surface at one Omega."""
    omega: Tuple[complex, complex, complex]
    jeff: float
    normalized: float
    sign: int


def chirality_sample(omega: Sequence[complex]) -> ChiralitySample:
    """Return the structured chirality-surface snapshot for ``omega``."""
    o = np.asarray(omega, dtype=complex).reshape(3)
    return ChiralitySample(
        omega=(complex(o[0]), complex(o[1]), complex(o[2])),
        jeff=jeff(o),
        normalized=normalized_chirality(o),
        sign=chirality_sign(o),
    )


@dataclass(frozen=True)
class ZMemResponse:
    """Cognitive ``z_mem`` response to one update (chirality-memory prerequisite)."""
    jeff: float
    normalized: float
    z_mem_before: float
    z_mem_after: float


def z_mem_response(
    omega: Sequence[complex],
    *,
    z_mem0: float = 0.0,
    params: Optional[ModelParams] = None,
) -> ZMemResponse:
    """Return the cognitive ``z_mem`` after ONE update from ``z_mem0``.

    Uses ``CognitiveCore.update`` -- a single deterministic update, NOT a
    trajectory step, no loop, no noise. Characterizes the bounded, sign-following
    chirality memory the flip surface depends on.
    """
    if params is None:
        params = ModelParams()
    state = ModelState(
        Omega=np.asarray(omega, dtype=complex).reshape(3).copy(),
    )
    cog = CognitiveCoreState(z_mem=float(z_mem0))
    CognitiveCore().update(cog, state=state, params=params)
    return ZMemResponse(
        jeff=jeff(omega),
        normalized=normalized_chirality(omega),
        z_mem_before=float(z_mem0),
        z_mem_after=float(cog.z_mem),
    )
