# model_core.py
# K1 structural split: history/offline run machinery (history allocation,
# record-before-step loop, uxy chart sampling, run metadata, optional
# latent-foreclosure post-run hook) lives in model_history.py.
# K2 structural split: the staged Z readout mathematics (rho, theta, z,
# Z_macro, Z_chiral, Z_vec) lives in staged_readouts.py; update_z here
# resolves theta_lock_override and performs the in-place writes.  This module
# keeps the live kernel: parameters, state, recurrence, phase sync, noise,
# clock, update_z (mutation), cycle stage, identity state and the master step().
import numpy as np
from dataclasses import dataclass, field

from .constants_selector import default_k_triplet
from .phase_triad_sync import apply_phase_triad_sync
from .identity_rules import (
    CycleConfig,
    compute_cycle_stage,
    map_identity_state,
)


# -----------------------------
# Diagnostic-only helpers (implementation owned by model_history; these
# names stay here as thin delegators for existing source-shape consumers)
# -----------------------------
def _unit(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    from .model_history import unit
    return unit(v, eps)


def _mirror_z(v: np.ndarray) -> np.ndarray:
    from .model_history import mirror_z
    return mirror_z(v)


@dataclass
class ModelParams:
    # Phase-lock engine
    eps: float = 0.05              # time step / nonlinearity scale
    g: float = 0.2                 # coupling strength for 3-node Laplacian
    k_vals: np.ndarray = field(default_factory=default_k_triplet)
    delta_vals: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=complex))

    # D24 / phase scaffold
    d24_steps: int = 12
    phi_step_per_iter: int = 1     # how many D24 sectors to advance per step

    # Phase-triad synchronization strength
    lambda_phase: float = 0.001    # small positive value to enable triad sync

    # Emergent Z parameters (toy choices)
    lambda_vp: float = 0.618       # vesica compression constant
    gamma: float = 0.577           # damping / drift
    theta_lock: float = 0.244      # preferred angle (rad) ~ 14 deg

    # Optional stochastic forcing (set >0 to break perfect limit cycles in sims)
    omega_noise_sigma: float = 0.0  # complex noise std per step (0 disables)

    # Z manifold blending weights
    z_alpha: float = 1.0          # weight for macro geometry
    z_beta: float = 0.5           # weight for chiral geometry

    # Cycle thresholds for kappa (S0..S6 bands)
    kappa_thresholds: np.ndarray = field(default_factory=lambda: np.array(
        [0.2, 0.5, 0.9, 1.3, 1.8, 2.3]
    ))

    @property
    def cycle_config(self) -> CycleConfig:
        return CycleConfig(kappa_thresholds=self.kappa_thresholds)


@dataclass
class ModelState:
    # tri-octa complex amplitudes
    Omega: np.ndarray              # shape (3,), complex

    # Discrete geometry / identity indices
    phi_index: int = 0             # D24 sector index 0..11
    cycle_stage: int = 0           # S0..S6 -> 0..6
    identity_state: int = 0        # s0..s8

    # Emergent Z diagnostics
    z: float = 0.0                 # scalar Z height

    # Macro geometry orientation vector (corridor angle + scalar z)
    Z_macro: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))

    # Pure chiral orientation vector from internal phases
    Z_chiral: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))

    # Total / blended orientation vector (legacy name: Z_vec)
    Z_vec: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=float))

    # Time / step counters
    t: float = 0.0                 # time (continuous)
    step: int = 0                  # step counter

    # --- keep this method! ---
    def kappa(self) -> float:
        """Return |Omega| as a scalar (used many places)."""
        return float(np.linalg.norm(self.Omega))


def _make_history_meta(seed: int | None = None, version: str | None = None) -> dict:
    from .model_history import make_history_meta
    return make_history_meta(seed=seed, version=version)


class TriOctaPhaseLockModel:
    """Minimal integrated model:
    - 3-node phase-lock engine on Omega_A,B,C
    - D24 phase scaffold via phi_index
    - Emergent Z field from (kappa, phi, t)
    - Recursive cycle stage S0..S6 from kappa thresholds
    """
    def __init__(self, params: ModelParams):
        self.p = params

        # 3-node Laplacian
        self.L = np.array(
            [[-2, 1, 1],
             [ 1,-2, 1],
             [ 1, 1,-2]],
            dtype=float
        )

    # -------- local dynamics --------
    def phase_lock_step(
        self, state: ModelState, *, g_override: float | None = None,
    ) -> None:
        """One discrete step of the 3-node Mexican-hat + coupling."""
        Omega = state.Omega
        eps = self.p.eps
        g = self.p.g if g_override is None else float(g_override)
        k_vals = self.p.k_vals
        delta = self.p.delta_vals

        # --- baseline dynamics (UNCHANGED) ---
        nonlinear = eps * Omega * (k_vals - np.abs(Omega)**2)
        coupling = g * self.L.dot(Omega)
        Omega_next = Omega + nonlinear + delta + coupling

        # --- optional phase-triad synchronization (SEPARATE) ---
        Omega_next = apply_phase_triad_sync(
            Omega_next,
            getattr(self.p, "lambda_phase", 0.0)
        )

        # --- optional tiny stochastic forcing (breaks perfect periodicity when enabled) ---
        sigma = float(getattr(self.p, "omega_noise_sigma", 0.0) or 0.0)
        if sigma > 0.0:
            noise = (np.random.standard_normal(3) + 1j*np.random.standard_normal(3))
            Omega_next = Omega_next + (sigma * noise.astype(np.complex128))
        

        # --- finalize state ---
        state.Omega = Omega_next

    def advance_phi(self, state: ModelState) -> None:
        """Advance D24 phase index."""
        state.phi_index = (state.phi_index + self.p.phi_step_per_iter) % self.p.d24_steps

    # -------- emergent Z / cycle --------
    def update_z(
        self, state: ModelState, *, theta_lock_override: float | None = None,
    ) -> None:
        """
        Emergent Z from triangular phase oscillator idea.

        Redefine Z_vec as a full orientation manifold vector that mixes:
          - macro TriOcta geometry (corridor angle + scalar z)
          - micro chiral geometry from Omega phases.
        """

        # The mathematics (rho, theta, z, Z_macro, Z_chiral, Z_vec) is owned by
        # staged_readouts (K2).  This method keeps the original interleaving
        # of parameter reads, computation and in-place writes, so failure
        # points and the state visible at them are unchanged.  Imported lazily
        # so the module import surface stays within the theta-contract allowlist.
        from .staged_readouts import blend_z, compute_chiral_z, compute_macro_z

        kappa = state.kappa()
        phi_index = state.phi_index
        d24_steps = self.p.d24_steps
        lam = self.p.lambda_vp
        gamma = self.p.gamma
        theta_lock = (
            self.p.theta_lock
            if theta_lock_override is None
            else theta_lock_override
        )

        # --- scalar Z as before (macro vesica/TriOcta Z) + (1) macro geometry ---
        macro = compute_macro_z(
            kappa, phi_index, state.t,
            d24_steps=d24_steps, lambda_vp=lam, gamma=gamma, theta_lock=theta_lock,
        )
        state.z = float(macro.z)
        Z_macro = macro.Z_macro
        state.Z_macro[:] = Z_macro

        # (2) Micro chiral contribution from Omega phases
        Z_chiral = compute_chiral_z(state.Omega)
        state.Z_chiral[:] = Z_chiral

        # (3) Blend them into a single orientation manifold vector
        alpha = self.p.z_alpha
        beta = self.p.z_beta
        Z_vec = blend_z(Z_macro, Z_chiral, alpha, beta)
        state.Z_vec[:] = Z_vec

    def update_cycle_stage(self, state: ModelState) -> None:
        """Cycle stage = how many kappa thresholds are crossed (S0..S6)."""
        kappa = state.kappa()
        state.cycle_stage = compute_cycle_stage(kappa, self.p.cycle_config)

    def update_identity_state(self, state: ModelState) -> None:
        """Use external identity rule mapping from (cycle_stage, z) to s0..s8."""
        state.identity_state = map_identity_state(
            stage=state.cycle_stage,
            z=state.z,
            num_states=9,
        )

    # -------- master step + runner --------
    def step(
        self,
        state: ModelState,
        dt: float = 0.1,
        *,
        g_override: float | None = None,
        theta_lock_override: float | None = None,
    ) -> None:
        """One full model update step."""
        # 1) local phase-lock dynamics on tri-octa modes
        self.phase_lock_step(state, g_override=g_override)
        # 2) D24 phase progression
        self.advance_phi(state)
        # 3) time update
        state.t += dt
        state.step += 1
        # 4) emergent Z update from (kappa, phi, t)
        self.update_z(state, theta_lock_override=theta_lock_override)
        # 5) cycle stage & identity update
        self.update_cycle_stage(state)
        self.update_identity_state(state)

    def run(
        self,
        state: ModelState,
        n_steps: int = 100,
        dt: float = 0.1,
        *,
        seed: int | None = None,
        version: str | None = None
    ):
        """Run the model for n_steps and return history arrays for analysis."""
        # History/offline machinery is owned by model_history (K1).  Imported
        # lazily so that importing model_core keeps its pure kernel import
        # surface (constants_selector, su3_basis, phase_triad_sync,
        # latent_foreclosure, identity_rules are the only allowed siblings).
        from .model_history import run_history
        return run_history(self, state, n_steps=n_steps, dt=dt, seed=seed, version=version)
