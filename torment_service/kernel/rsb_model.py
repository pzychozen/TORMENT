# rsb_model.py
# ============================================================
# Recursive Spectral Banding (RSB) toy engine
# Hilbert space: channels x phases x helicity
#   channels: 0 = vis, 1 = L, 2 = S
#   phases:   m = 0..M-1  (default M = 12)
#   helicity: 0 = +, 1 = -
# ============================================================

from dataclasses import dataclass
import numpy as np


@dataclass
class RSBParams:
    # Hilbert space
    num_channels: int = 3
    num_phases: int = 12
    num_helicity: int = 2

    # Channel recursion (forward–backward)
    theta: float = 0.35
    phi: float = 0.0
    alpha_L: float = 0.20
    beta_S: float = 0.10
    d_vis: float = 0.95

    # RSB Hamiltonian parameters
    kappa_L: float = 0.4
    kappa_S: float = 0.3
    mu: float = 0.25

    # Reinforcement (REFU-like)
    gamma: float = 0.05
    eta: float = 0.02

    # Time step for RSB Hamiltonian
    eps_rsb: float = 0.05

    # Spectral contraction
    alpha: float = 0.0            # base contraction strength
    adaptive_alpha: bool = False  # if True, scale alpha by spectral entropy


class RSBModel:
    """
    Minimal but real RSB engine.

    State:
        psi shape: (C, M, H) = (3, num_phases, 2)

    One step does:
        1) channel mixing via T_chan = D R_- U_+
        2) spectral + helicity mixing via H_RSB (Euler step)
        3) reinforcement / damping (REFU-like)
        4) spectral contraction toward a dominant band
        5) renormalization
    """

    def __init__(self, params: RSBParams):
        self.p = params
        self._validate_params()

        assert self.p.num_channels == 3
        assert self.p.num_helicity == 2

        self.M = self.p.num_phases

        # Precompute channel recursion matrix T_chan = D R_- U_+
        self.T_chan = self._build_channel_matrix()

        # Phase Laplacian Δ_12 and phase mask M_12
        self.L_phase = self._build_phase_laplacian(self.M)
        self.M_phase = self._build_phase_mask(self.M)

        # Optional: precomputed spectral band mask (not used by default)
        self.band_mask = self._build_band_mask(self.M)

    # ------------------------------
    # Validation
    # ------------------------------
    def _validate_params(self) -> None:
        p = self.p
        if p.alpha_L < 0.0 or p.beta_S < 0.0:
            raise ValueError(f"alpha_L and beta_S must be non-negative (got {p.alpha_L}, {p.beta_S}).")
        if p.alpha_L + p.beta_S > 1.0 + 1e-9:
            raise ValueError(
                f"alpha_L + beta_S must be ≤ 1 to keep vis amplitude real "
                f"(got {p.alpha_L + p.beta_S})."
            )
        if not (0.0 <= p.d_vis <= 1.0):
            # Not fatal, but unusual; we just warn via print.
            print(f"[RSBModel] Warning: d_vis={p.d_vis} is outside [0,1].")

    # ------------------------------
    # Operator builders
    # ------------------------------
    def _build_channel_matrix(self) -> np.ndarray:
        p = self.p

        # U_+ on (vis, L), phase on S
        theta = p.theta
        phi = p.phi
        U_plus = np.array(
            [
                [np.cos(theta),  np.sin(theta), 0.0],
                [-np.sin(theta), np.cos(theta), 0.0],
                [0.0,            0.0,           np.exp(1j * phi)],
            ],
            dtype=complex,
        )

        # R_-: branching/leakage from vis → L,S
        alpha_L = p.alpha_L
        beta_S = p.beta_S
        R_minus = np.array(
            [
                [np.sqrt(1.0 - alpha_L - beta_S), 0.0, 0.0],
                [np.sqrt(alpha_L),                1.0, 0.0],
                [np.sqrt(beta_S),                 0.0, 1.0],
            ],
            dtype=complex,
        )

        # D: vis damping
        d_vis = p.d_vis
        D = np.diag([d_vis, 1.0, 1.0]).astype(complex)

        # Composition: T_chan = D R_- U_+
        T_chan = D @ R_minus @ U_plus
        return T_chan

    @staticmethod
    def _build_phase_laplacian(M: int) -> np.ndarray:
        """Discrete Laplacian on a ring of size M."""
        L = np.zeros((M, M), dtype=float)
        for m in range(M):
            L[m, m] = -2.0
            L[m, (m + 1) % M] = 1.0
            L[m, (m - 1) % M] = 1.0
        return L

    @staticmethod
    def _build_phase_mask(M: int) -> np.ndarray:
        """
        M_12 diagonal mask.

        Currently: M_phase[m] = cos(M * phi_m) with phi_m = 2π m / M,
        which evaluates to 1 for all integer m. This keeps the toy model
        simple: the μ-term is global in phase.
        """
        m = np.arange(M)
        phi_m = 2.0 * np.pi * m / float(M)
        return np.cos(float(M) * phi_m).astype(float)

    @staticmethod
    def _build_band_mask(M: int, center: int | None = None, width: float | None = None) -> np.ndarray:
        """
        Build a smooth spectral band mask w[m] in [0,1],
        peaked at 'center' with Gaussian falloff.

        Default:
            center = M // 4   (arbitrary but asymmetric)
            width  = M / 6    (moderately narrow)

        Note: this mask is not used in the core dynamics yet, but is
        available for UI / diagnostics or alternative contraction rules.
        """
        if center is None:
            center = M // 4
        if width is None:
            width = M / 6.0

        m = np.arange(M)
        # wrap distance on the ring
        dist = np.minimum(np.abs(m - center), M - np.abs(m - center))
        w = np.exp(-0.5 * (dist / width) ** 2)

        # normalize to max = 1
        max_w = w.max()
        if max_w > 0.0:
            w /= max_w
        return w.astype(float)

    # ------------------------------
    # Core operators
    # ------------------------------
    def _apply_channel_recursion(self, psi: np.ndarray) -> np.ndarray:
        """
        Apply channel matrix T_chan on channel axis.

        psi shape: (3, M, 2)
        out[c', m, h] = Σ_c T_chan[c', c] * psi[c, m, h]
        """
        return np.einsum("ab,bmh->amh", self.T_chan, psi)

    def _laplacian_on_phase(self, arr: np.ndarray) -> np.ndarray:
        """
        Apply L_phase along the phase axis (axis=1) for a (C, M, H) array.
        """
        # arr[c, m, h], we want out[c, m, h] = Σ_{m'} L[m, m'] arr[c, m', h]
        return np.einsum("mn,cmh->cnh", self.L_phase, arr)

    def _H_RSB_action(self, psi: np.ndarray) -> np.ndarray:
        """
        Compute H_RSB |psi> as a (3, M, 2) array without building
        the full 72×72 matrix explicitly.

        H_RSB =
            κ_L  * P_L ⊗ Δ_phase ⊗ I
          + κ_S  * P_S ⊗ Δ_phase ⊗ σ_z
          + μ    * (P_L + P_S) ⊗ M_phase ⊗ σ_x
        """
        p = self.p
        C, M, H = psi.shape
        assert C == 3 and H == 2

        out = np.zeros_like(psi, dtype=complex)

        # --- Term 1: κ_L * P_L ⊗ Δ_phase ⊗ I ---
        if abs(p.kappa_L) > 0.0:
            lap_L = self._laplacian_on_phase(psi[1:2, :, :])[0]  # (M, 2)
            out[1, :, :] += p.kappa_L * lap_L

        # --- Term 2: κ_S * P_S ⊗ Δ_phase ⊗ σ_z ---
        if abs(p.kappa_S) > 0.0:
            lap_S = self._laplacian_on_phase(psi[2:3, :, :])[0]  # (M, 2)
            # σ_z = diag(+1, -1)
            out[2, :, 0] += p.kappa_S * (+1.0) * lap_S[:, 0]
            out[2, :, 1] += p.kappa_S * (-1.0) * lap_S[:, 1]

        # --- Term 3: μ * (P_L + P_S) ⊗ M_phase ⊗ σ_x ---
        if abs(p.mu) > 0.0:
            # σ_x: swap helicities
            for c in (1, 2):
                v = psi[c, :, :]  # (M, 2)
                swap = np.stack([v[:, 1], v[:, 0]], axis=-1)  # (M, 2)
                out[c, :, :] += p.mu * self.M_phase[:, None] * swap

        return out

    def _apply_spectral_contraction(self, psi: np.ndarray) -> np.ndarray:
        """
        Spectral contraction toward a dominant phase band.

        Steps:
          1. Compute spectral energy per phase m: E_m
          2. Find argmax m0
          3. Build a one-hot mask at m0
          4. Mix psi toward that band with effective strength alpha_eff:

                psi <- (1 - alpha_eff) * psi + alpha_eff * psi_band

        If adaptive_alpha=True, alpha_eff = alpha * S_norm, where S_norm is
        the normalized spectral entropy in [0, 1].
        """
        alpha = float(self.p.alpha)
        if alpha <= 0.0:
            return psi

        # psi: shape (C, M, H)
        _, M, _ = psi.shape

        # 1) spectral energy per phase index
        E_m = np.sum(np.abs(psi) ** 2, axis=(0, 2))  # shape (M,)

        # Optional: adaptive scaling by spectral entropy
        if self.p.adaptive_alpha:
            total_E = E_m.sum()
            if total_E > 0.0:
                p_m = E_m / total_E
                # normalized spectral entropy S_norm ∈ [0,1]
                S = -np.sum(p_m * np.log(p_m + 1e-12))
                S_norm = S / np.log(M + 1e-12)
                alpha_eff = alpha * S_norm
            else:
                alpha_eff = 0.0
        else:
            alpha_eff = alpha

        # Clamp for safety
        alpha_eff = float(np.clip(alpha_eff, 0.0, 1.0))
        if alpha_eff <= 0.0:
            return psi

        # 2) dominant phase index
        m0 = int(np.argmax(E_m))

        # 3) one-hot band mask
        mask = np.zeros(M, dtype=float)
        mask[m0] = 1.0

        # 4) project psi into that band
        psi_band = psi * mask[None, :, None]

        # 5) mix
        psi_new = (1.0 - alpha_eff) * psi + alpha_eff * psi_band
        return psi_new

    def _apply_reinforcement(self, psi: np.ndarray) -> np.ndarray:
        """
        REFU-like gain/loss on channels:
            vis -> amplitude scaled by exp(-eta/2)
            L,S -> amplitude scaled by exp(+gamma/2)
        """
        p = self.p
        amp_vis = np.exp(-0.5 * p.eta)
        amp_dark = np.exp(+0.5 * p.gamma)

        psi_out = psi.copy()
        # channel 0: vis
        psi_out[0, :, :] *= amp_vis
        # channels 1,2: dark
        psi_out[1, :, :] *= amp_dark
        psi_out[2, :, :] *= amp_dark
        return psi_out

    # ------------------------------
    # Public API
    # ------------------------------
    def step(self, psi: np.ndarray, rng: np.random.Generator | None = None) -> np.ndarray:
        """
        Perform a single RSB update step on a given state psi.

        This is the core map used by `run`, and can also be called
        directly by demos / UI code.
        """
        p = self.p

        # 1) channel recursion
        psi = self._apply_channel_recursion(psi)

        # 2) spectral + helicity mixing via H_RSB
        Hpsi = self._H_RSB_action(psi)
        psi = psi - 1j * p.eps_rsb * Hpsi

        # 3) reinforcement (REFU-like)
        psi = self._apply_reinforcement(psi)

        # 4) spectral contraction toward preferred band
        psi = self._apply_spectral_contraction(psi)

        # 5) renormalize
        norm = np.sqrt(np.sum(np.abs(psi) ** 2))
        if norm == 0.0:
            if rng is None:
                raise ValueError("RSBModel.step requires an explicit rng for reproducibility.")
            psi = rng.standard_normal(psi.shape) + 1j * rng.standard_normal(psi.shape)
            psi /= np.sqrt(np.sum(np.abs(psi) ** 2))
        else:
            psi /= norm

        return psi

    def run(
        self,
        n_steps: int = 200,
        seed: int | None = 0,
        rng: np.random.Generator | None = None,
        psi0: np.ndarray | None = None) -> np.ndarray:
        """
        Run the RSB recursion for n_steps.

        Args:
            n_steps: number of steps to simulate.
            seed: RNG seed for random initial state (if psi0 is None).
            psi0: optional initial state array of shape (3, M, 2).
                  If provided, it will be normalized at start.

        Returns:
            psi_hist: np.ndarray with shape (n_steps, 3, M, 2)
        """
        if rng is None:
            if seed is None:
                raise ValueError("Provide either rng or seed for reproducible RSB runs.")
            rng = np.random.default_rng(seed)

        if psi0 is None:
            psi0 = rng.standard_normal((3, self.M, 2)) + 1j * rng.standard_normal((3, self.M, 2))

        # normalize initial state
        norm0 = np.sqrt(np.sum(np.abs(psi0) ** 2))
        if norm0 == 0.0:
            psi = np.zeros_like(psi0, dtype=complex)
            psi[0, 0, 0] = 1.0  # trivial basis state
        else:
            psi = psi0 / norm0

        psi_hist = np.zeros((n_steps, 3, self.M, 2), dtype=complex)

        for n in range(n_steps):
            psi_hist[n] = psi
            psi = self.step(psi, rng=rng)

        return psi_hist