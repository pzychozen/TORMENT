"""Extracted cognitive identity layer for the TORMENT memory kernel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .kernel.identity_rules import map_identity_state


COGNITIVE_TAU_META = 0.01


@dataclass
class CognitiveCoreState:
    z_mem: float = 0.0
    z_identity: float = 0.0
    identity_state: int = 0


def _cognitive_z_inst_no_decay(
    state: Any, params: Any, *, theta_lock_override: float | None = None,
):
    # Keep this operation-for-operation aligned with the existing Z scaffold.
    kappa = state.kappa()
    rho = kappa / (1.0 + kappa)  # 0..1 soft saturation

    theta = (2.0 * np.pi * state.phi_index) / float(params.d24_steps)
    lam = float(params.lambda_vp)
    theta_lock = float(
        params.theta_lock
        if theta_lock_override is None
        else theta_lock_override
    )

    z_inst = lam * rho * np.cos(3.0 * (theta - theta_lock))  # bounded in [-lam*rho, +lam*rho]
    return z_inst


class CognitiveCore:
    """Stateless compute object for the extracted cognitive state."""

    def update(
        self,
        cognitive_state: CognitiveCoreState,
        *,
        state: Any,
        params: Any,
        theta_lock_override: float | None = None,
    ) -> CognitiveCoreState:
        z_inst = _cognitive_z_inst_no_decay(
            state,
            params,
            theta_lock_override=theta_lock_override,
        )

        O1, O2, O3 = state.Omega
        J_eff = float(np.imag(O1 * np.conj(O2) * O3))
        jeff_norm = J_eff / (1.0 + abs(J_eff))  # in (-1,1)

        cognitive_state.z_mem = (
            (1.0 - COGNITIVE_TAU_META) * float(cognitive_state.z_mem)
            + COGNITIVE_TAU_META * float(jeff_norm)
        )
        cognitive_state.z_identity = float(z_inst + cognitive_state.z_mem)
        cognitive_state.identity_state = map_identity_state(
            stage=state.cycle_stage,
            z=cognitive_state.z_identity,
            num_states=9,
        )
        return cognitive_state
