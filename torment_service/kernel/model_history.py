# model_history.py
# ============================================================
# Offline run / history machinery for TriOctaPhaseLockModel.
#
# K1 structural split (ownership only, no mathematics changed):
# the history allocation, record-before-step loop, chart projection
# sampling (project_to_uxy), the history metadata and the optional
# latent-foreclosure post-run hook moved here verbatim from
# model_core.py.  TriOctaPhaseLockModel.run() keeps its name,
# signature, defaults and return structure and delegates to
# run_history().  Production memory processing never calls run();
# it uses TriOctaPhaseLockModel.step() directly.
#
# Order of operations preserved exactly: history dict allocated,
# _meta attached, then per iteration RECORD the current state, THEN
# model.step(state, dt=dt); the latent-foreclosure block runs after
# the loop and only when the params object carries
# latent_foreclosure_enabled (default ModelParams does not).
# ============================================================
import datetime
import uuid
import numpy as np

from .su3_basis import project_to_uxy
from .latent_foreclosure import compute_option_volume


# -----------------------------
# Diagnostic-only helpers
# -----------------------------
def unit(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    if n < eps:
        return np.zeros_like(v, dtype=float)
    return v / n


def mirror_z(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    return np.array([float(v[0]), float(v[1]), -float(v[2])], dtype=float)


def make_history_meta(seed: int | None = None, version: str | None = None) -> dict:
    return {
        "run_id": f"run_{uuid.uuid4().hex[:10]}",
        "seed": None if seed is None else int(seed),
        "version": version if version is not None else "unknown",
        "timestamp_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
    }


def run_history(
    model,
    state,
    n_steps: int = 100,
    dt: float = 0.1,
    *,
    seed: int | None = None,
    version: str | None = None
):
    """Run the model for n_steps and return history arrays for analysis.

    ``model`` is a TriOctaPhaseLockModel; ``state`` is mutated in place by
    ``model.step``.  Body identical to the pre-K1 TriOctaPhaseLockModel.run.
    """
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
    history["_meta"] = make_history_meta(seed=seed, version=version)

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

        Zm_u = unit(Zm)
        Zv_u = unit(Zv)
        Zc_u = unit(Zc)

        history["dot_vec_macro"][i] = float(np.dot(Zv_u, Zm_u))
        history["dot_chiral_macro"][i] = float(np.dot(Zc_u, Zm_u))
        history["dot_vec_chiral"][i] = float(np.dot(Zv_u, Zc_u))

        history["cycle_stage"][i] = state.cycle_stage
        history["identity_state"][i] = state.identity_state
        history["t"][i] = state.t
        history["uxy_coords"][i] = project_to_uxy(state.Omega)

        # step
        model.step(state, dt=dt)

    if hasattr(model.p, "latent_foreclosure_enabled") and model.p.latent_foreclosure_enabled:
        lf = compute_option_volume(
            model,
            state,
            delta=model.p.lf_delta,
            K=model.p.lf_K,
            N=model.p.lf_N,
            eps_corridor=model.p.lf_eps,
            eps_norm=1.0,
        )
        history.setdefault("latent_foreclosure", []).append(lf)

    return history
