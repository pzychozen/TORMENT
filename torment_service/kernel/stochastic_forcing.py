# stochastic_forcing.py
# ============================================================
# Optional stochastic forcing for TriOctaPhaseLockModel.phase_lock_step.
#
# K3 structural split (ownership only, no mathematics or RNG semantics
# changed): the optional complex Gaussian forcing block moved here
# verbatim from phase_lock_step.  phase_lock_step still reads the
# params in the original order, runs the baseline recurrence and the
# phase-triad synchronization locally, resolves
#   sigma = float(getattr(p, "omega_noise_sigma", 0.0) or 0.0)
# at the original point, calls apply_stochastic_forcing(Omega_next,
# sigma), and rebinds state.Omega at the original point.
#
# Draws come from the GLOBAL numpy legacy stream (np.random), in the
# original order: standard_normal(3) for the real part, then
# standard_normal(3) for the imaginary part; nothing is drawn when
# sigma <= 0 (or NaN), and Omega_next is then returned unchanged (the
# same object), so state.Omega rebinding semantics are unchanged.
# ============================================================
import numpy as np


def apply_stochastic_forcing(Omega_next: np.ndarray, sigma: float) -> np.ndarray:
    """Add sigma * (N(0,1) + 1j*N(0,1)) forcing when sigma > 0 (pre-K3 block, verbatim)."""
    if sigma > 0.0:
        noise = (np.random.standard_normal(3) + 1j*np.random.standard_normal(3))
        Omega_next = Omega_next + (sigma * noise.astype(np.complex128))
    return Omega_next
