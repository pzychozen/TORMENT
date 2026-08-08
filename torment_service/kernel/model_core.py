# model_core.py
import datetime
import uuid
import numpy as np
from dataclasses import dataclass, field

from .constants_selector import default_k_triplet
from .su3_basis import project_to_uxy
from .phase_triad_sync import apply_phase_triad_sync
from .latent_foreclosure import compute_option_volume
from .identity_rules import (
    CycleConfig,
    compute_cycle_stage,
    map_identity_state,
)


# -----------------------------
# Diagnostic-only helpers
# -----------------------------
def _unit(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    if n < eps:
        return np.zeros_like(v, dtype=float)
    return v / n


def _mirror_z(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    return np.array([float(v[0]), float(v[1]), -float(v[2])], dtype=float)


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
    return {
        "run_id": f"run_{uuid.uuid4().hex[:10]}",
        "seed": None if seed is None else int(seed),
        "version": version if version is not None else "unknown",
        "timestamp_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    }


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

        kappa = state.kappa()
        # normalize rho with soft saturation
        rho = kappa / (1.0 + kappa)

        theta = (2.0 * np.pi * state.phi_index) / self.p.d24_steps
        lam = self.p.lambda_vp
        gamma = self.p.gamma
        theta_lock = (
            self.p.theta_lock
            if theta_lock_override is None
            else theta_lock_override
        )

        # --- scalar Z as before (macro vesica/TriOcta Z) ---
        z = lam * rho * np.cos(3.0 * (theta - theta_lock)) * np.exp(-gamma * state.t)
        state.z = float(z)

        # (1) Macro geometry contribution (corridor angle in x-y plane)
        phi = theta

        Z_macro = np.array(
            [float(z * np.cos(phi)),
             float(z * np.sin(phi)),
             float(z)],
            dtype=float
        )
        state.Z_macro[:] = Z_macro

        # (2) Micro chiral contribution from Omega phases
        O1, O2, O3 = state.Omega
        Z_chiral = np.array(
            [float(np.imag(np.conj(O2) * O3)),
             float(np.imag(np.conj(O3) * O1)),
             float(np.imag(np.conj(O1) * O2))],
            dtype=float
        )
        state.Z_chiral[:] = Z_chiral

        # (3) Blend them into a single orientation manifold vector
        alpha = self.p.z_alpha
        beta = self.p.z_beta
        Z_vec = alpha * Z_macro + beta * Z_chiral
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
        history = {
            "Omega": np.zeros((n_steps, 3), dtype=complex),
            "kappa": np.zeros(n_steps),
            "phi_index": np.zeros(n_steps, dtype=int),
            "z": np.zeros(n_steps),

            "Z_macro": np.zeros((n_steps, 3)),         # macro geometry contribution
            "Z_total": np.zeros((n_steps, 3)),         # blended total (alpha*macro + beta*chiral)
            "Z_vec": np.zeros((n_steps, 3)),           # legacy alias for Z_total
            "Z_chiral": np.zeros((n_steps, 3)),        # pure chirality embedding
            "dot_vec_macro": np.zeros(n_steps),
            "dot_chiral_macro": np.zeros(n_steps),
            "dot_vec_chiral": np.zeros(n_steps),

            "cycle_stage": np.zeros(n_steps, dtype=int),
            "identity_state": np.zeros(n_steps, dtype=int),
            "t": np.zeros(n_steps),
            "uxy_coords": np.zeros((n_steps, 3)),
        }
        history["_meta"] = _make_history_meta(seed=seed, version=version)

        for i in range(n_steps):
            # record
            history["Omega"][i] = state.Omega
            history["kappa"][i] = state.kappa()
            history["phi_index"][i] = state.phi_index
            history["z"][i] = state.z

            history["Z_macro"][i] = state.Z_macro
            history["Z_chiral"][i] = state.Z_chiral
            history["Z_total"][i] = state.Z_vec
            history["Z_vec"][i] = state.Z_vec

            Zm = np.asarray(state.Z_macro, dtype=float)
            Zv = np.asarray(state.Z_vec, dtype=float)
            Zc = np.asarray(state.Z_chiral, dtype=float)

            Zm_u = _unit(Zm)
            Zv_u = _unit(Zv)
            Zc_u = _unit(Zc)

            history["dot_vec_macro"][i] = float(np.dot(Zv_u, Zm_u))
            history["dot_chiral_macro"][i] = float(np.dot(Zc_u, Zm_u))
            history["dot_vec_chiral"][i] = float(np.dot(Zv_u, Zc_u))

            history["cycle_stage"][i] = state.cycle_stage
            history["identity_state"][i] = state.identity_state
            history["t"][i] = state.t
            history["uxy_coords"][i] = project_to_uxy(state.Omega)

            # step
            self.step(state, dt=dt)

        if hasattr(self.p, "latent_foreclosure_enabled") and self.p.latent_foreclosure_enabled:
            lf = compute_option_volume(
                self,
                state,
                delta=self.p.lf_delta,
                K=self.p.lf_K,
                N=self.p.lf_N,
                eps_corridor=self.p.lf_eps,
                eps_norm=1.0,
            )
            history.setdefault("latent_foreclosure", []).append(lf)

        return history
