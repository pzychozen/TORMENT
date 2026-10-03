# staged_readouts.py
# ============================================================
# Staged Z readouts for TriOctaPhaseLockModel.
#
# K2 structural split (ownership only, no mathematics changed): the
# mathematical computation of rho, theta, the scalar z, Z_macro,
# Z_chiral and Z_vec moved here verbatim from
# TriOctaPhaseLockModel.update_z.  This module is pure: it reads no
# ModelState and writes nothing.  model_core.update_z owns every
# mutation (state.z, state.Z_macro[:], state.Z_chiral[:],
# state.Z_vec[:]) and keeps the ORIGINAL interleaving of parameter
# reads, computation and writes:
#
#   read d24_steps, lambda_vp, gamma, theta_lock(/override)
#     -> compute_macro_z            -> write state.z, state.Z_macro[:]
#   read state.Omega
#     -> compute_chiral_z           -> write state.Z_chiral[:]
#   read z_alpha, z_beta
#     -> blend_z                    -> write state.Z_vec[:]
#
# so a params object missing z_alpha/z_beta still fails at the same
# point, with z, Z_macro and Z_chiral already written and Z_vec
# untouched, exactly as before the split.
#
# Expression text, float() wrapping, np.array([...], dtype=float)
# construction and the alpha*Z_macro + beta*Z_chiral association are
# unchanged; the arguments are the very objects update_z used to read
# from state / params (ints, floats, the Omega array).
# ============================================================
from typing import NamedTuple

import numpy as np


class MacroZ(NamedTuple):
    rho: float
    theta: float
    z: float            # numpy float64 scalar as computed; the caller wraps float()
    Z_macro: np.ndarray


class StagedReadouts(NamedTuple):
    rho: float
    theta: float
    z: float
    Z_macro: np.ndarray
    Z_chiral: np.ndarray
    Z_vec: np.ndarray


def compute_macro_z(
    kappa: float,
    phi_index: int,
    t: float,
    *,
    d24_steps: int,
    lambda_vp: float,
    gamma: float,
    theta_lock: float,
) -> MacroZ:
    """Scalar z and the macro geometry vector (pre-K2 update_z, part 1).

    ``theta_lock`` is the already-resolved lock angle (override or params).
    """
    # normalize rho with soft saturation
    rho = kappa / (1.0 + kappa)

    theta = (2.0 * np.pi * phi_index) / d24_steps
    lam = lambda_vp

    # --- scalar Z as before (macro vesica/TriOcta Z) ---
    z = lam * rho * np.cos(3.0 * (theta - theta_lock)) * np.exp(-gamma * t)

    # (1) Macro geometry contribution (corridor angle in x-y plane)
    phi = theta

    Z_macro = np.array(
        [float(z * np.cos(phi)),
         float(z * np.sin(phi)),
         float(z)],
        dtype=float
    )
    return MacroZ(rho, theta, z, Z_macro)


def compute_chiral_z(Omega: np.ndarray) -> np.ndarray:
    """Micro chiral contribution from the Omega phases (pre-K2 update_z, part 2)."""
    # (2) Micro chiral contribution from Omega phases
    O1, O2, O3 = Omega
    Z_chiral = np.array(
        [float(np.imag(np.conj(O2) * O3)),
         float(np.imag(np.conj(O3) * O1)),
         float(np.imag(np.conj(O1) * O2))],
        dtype=float
    )
    return Z_chiral


def blend_z(Z_macro: np.ndarray, Z_chiral: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    """Blend macro and chiral geometry into the orientation manifold vector (part 3)."""
    # (3) Blend them into a single orientation manifold vector
    Z_vec = alpha * Z_macro + beta * Z_chiral
    return Z_vec


def compute_staged_z(
    Omega: np.ndarray,
    kappa: float,
    phi_index: int,
    t: float,
    *,
    d24_steps: int,
    lambda_vp: float,
    gamma: float,
    theta_lock: float,
    z_alpha: float,
    z_beta: float,
) -> StagedReadouts:
    """All staged readouts at once (pure composition of the three parts above)."""
    macro = compute_macro_z(kappa, phi_index, t, d24_steps=d24_steps, lambda_vp=lambda_vp,
                            gamma=gamma, theta_lock=theta_lock)
    Z_chiral = compute_chiral_z(Omega)
    Z_vec = blend_z(macro.Z_macro, Z_chiral, z_alpha, z_beta)
    return StagedReadouts(macro.rho, macro.theta, macro.z, macro.Z_macro, Z_chiral, Z_vec)
