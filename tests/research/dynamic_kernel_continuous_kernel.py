"""tests/research/dynamic_kernel_continuous_kernel.py

Standalone, test-adjacent, DETERMINISTIC in-memory reconstruction of the baseline
continuous-kernel dynamics (the recovered "continuous_kernel" target / Sim 1).

This is a MODULE, not a runnable script. It exposes a pure function and frozen
result dataclasses and performs NO I/O: no plotting, no CLI, no file output, no
randomness, no external Z-force seed coupling, and no background / runtime tick.
There is intentionally no ``__main__`` entry point.

It reconstructs ONLY baseline continuous kernel stepping using the CANONICAL
``torment_service/kernel`` primitives already locked by
``tests/test_dynamic_kernel_continuous_kernel_reconstruction_contract.py``:
``TriOctaPhaseLockModel`` / ``ModelParams`` / ``ModelState`` (and, optionally, a
DECOUPLED ``SeedWorld``). Per step it records canonical ``Omega`` / ``z`` plus
extracted cognitive ``z_mem`` / the J_eff-like signed coupling /
``cycle_stage`` / ``identity_state``, plus optional decoupled seed position/velocity state.

HOLD (NOT reconstructed here): the external Z-force seed-coupling loop, the
``chirality_flip`` and ``conversation_shock`` targets, plots, data/output files,
and any runtime motion. The three lost driver scripts are NOT recreated.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np

from torment_service.cognitive_core import CognitiveCore, CognitiveCoreState
from torment_service.kernel.model_core import (
    ModelParams,
    ModelState,
    TriOctaPhaseLockModel,
)
from torment_service.kernel.seed_entities import SeedWorld


def jeff_of(omega: Sequence[complex]) -> float:
    """Signed triad area ``Im(O1 * conj(O2) * O3)`` -- the J_eff chirality surface.

    Same formula ``model_core.update_z`` uses internally; recomputed read-only
    from the current ``Omega`` so it can be surfaced per sample.
    """
    o1, o2, o3 = omega
    return float(np.imag(o1 * np.conj(o2) * o3))


@dataclass(frozen=True)
class KernelSample:
    """One per-step kernel snapshot (deterministic, primitive scalars only)."""
    step: int
    t: float
    omega: Tuple[complex, complex, complex]
    kappa: float
    z: float
    z_mem: float
    jeff: float
    cycle_stage: int
    identity_state: int


@dataclass(frozen=True)
class SeedSample:
    """One per-step DECOUPLED seed snapshot (no kernel coupling)."""
    step: int
    positions: Tuple[Tuple[float, float, float], ...]
    velocities: Tuple[Tuple[float, float, float], ...]


@dataclass(frozen=True)
class ContinuousKernelResult:
    """Structured, in-memory result of a continuous-kernel reconstruction run."""
    n_steps: int
    dt: float
    samples: Tuple[KernelSample, ...]
    seed_samples: Tuple[SeedSample, ...] = ()


def run_continuous_kernel_reconstruction(
    *,
    omega0: Sequence[complex] = (0.5 + 0.3j, 0.2 - 0.4j, 0.6 + 0.1j),
    n_steps: int = 200,
    dt: float = 0.1,
    params: Optional[ModelParams] = None,
    seeds: Optional[Sequence[Tuple[int, Sequence[float], Sequence[float]]]] = None,
) -> ContinuousKernelResult:
    """Pure deterministic in-memory continuous-kernel stepping.

    Steps a ``TriOctaPhaseLockModel`` ``n_steps`` times from ``omega0`` and records
    a :class:`KernelSample` after each step. With the default (noiseless)
    ``ModelParams`` (``omega_noise_sigma == 0``) the run is fully reproducible.

    If ``seeds`` (an iterable of ``(channel, pos3, vel3)``) is supplied, a DECOUPLED
    :class:`SeedWorld` is stepped in lockstep and its state recorded. There is NO
    coupling from the kernel ``Z`` field into the seeds -- ``SeedWorld.step()``
    receives no kernel state; the external Z-force loop is HOLD / not reconstructed.

    Returns structured samples only. Performs no I/O, plotting, or file output.
    """
    if params is None:
        params = ModelParams()
    model = TriOctaPhaseLockModel(params)
    state = ModelState(Omega=np.asarray(omega0, dtype=complex).reshape(3).copy())
    cognitive_core = CognitiveCore()
    cognitive_state = CognitiveCoreState()

    world: Optional[SeedWorld] = None
    if seeds:
        world = SeedWorld()  # decoupled integrator; default drag/drift
        for channel, pos, vel in seeds:
            world.spawn(
                born_step=0,
                channel=int(channel),
                pos=np.asarray(pos, dtype=float),
                vel=np.asarray(vel, dtype=float),
            )

    samples: List[KernelSample] = []
    seed_samples: List[SeedSample] = []
    for _ in range(int(n_steps)):
        model.step(state, dt=dt)            # baseline continuous step (no external input)
        cognitive_core.update(cognitive_state, state=state, params=params)
        if world is not None:
            world.step()                    # DECOUPLED -- no kernel state passed in
        o = state.Omega
        samples.append(KernelSample(
            step=int(state.step),
            t=float(state.t),
            omega=(complex(o[0]), complex(o[1]), complex(o[2])),
            kappa=float(state.kappa()),
            z=float(state.z),
            z_mem=float(cognitive_state.z_mem),
            jeff=jeff_of(o),
            cycle_stage=int(state.cycle_stage),
            identity_state=int(cognitive_state.identity_state),
        ))
        if world is not None:
            seed_samples.append(SeedSample(
                step=int(state.step),
                positions=tuple(tuple(float(x) for x in e.pos) for e in world.entities),
                velocities=tuple(tuple(float(x) for x in e.vel) for e in world.entities),
            ))

    return ContinuousKernelResult(
        n_steps=int(n_steps),
        dt=float(dt),
        samples=tuple(samples),
        seed_samples=tuple(seed_samples),
    )
