"""K1 behaviour freeze for the TriOctaPhaseLockModel.run() history boundary.

Authority
---------
tests/fixtures/model_history_boundary_k1/history_fixture.json is the production
bit-exact oracle.  Its ``results`` block is the verbatim BASE_WINDOWS capture of
the UNMODIFIED pre-K1 kernel at commit fa20855a (model_core.py sha256
c9fcc159..., no model_history.py) taken on the authoritative Windows `torment`
environment (Python 3.11.15 / NumPy 2.4.4 / scipy-openblas 0.3.31.188.0 /
AMD64, fingerprint stored in ``authority.environment``).  The K1 candidate
captured on the same environment was byte-identical to it.

The fixture is NOT a portable oracle: the same cases captured on Linux differ in
the last ulp (uxy_coords, Omega, Z_*, dot products, kappa, z).  Therefore:

  * platform-independent invariants (keys, dtypes, shapes, record-before-step
    ordering, phi_index / t / step bookkeeping, Z_total/Z_vec separation,
    aliasing, _meta shape, latent-foreclosure hook presence) run everywhere;
  * every float.hex / complex comparison runs ONLY when the current environment
    fingerprint equals the fixture's.  Elsewhere on Windows a mismatch FAILS
    (the authoritative environment drifted: re-bind deliberately); on any other
    OS the exact comparisons are SKIPPED with the fingerprint in the reason.
  * there are no tolerances anywhere.

The capture encoding below is identical to windows_ab/k1_ab.py (the A/B tool
that produced the fixture): floats/complex via float.hex, ints as ints, run_id
and timestamp_utc excluded as non-deterministic by design.
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

from torment_service.kernel.model_core import ModelParams, ModelState, TriOctaPhaseLockModel

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "model_history_boundary_k1"
FIXTURE_PATH = FIXTURE_DIR / "history_fixture.json"
FIXTURE_SHA256_PATH = FIXTURE_DIR / "history_fixture.sha256"
AUTHORITY_COMMIT = "fa20855ae6b66280b211528b027655755a0dad45"

HISTORY_KEYS = [
    "Omega", "kappa", "phi_index", "z", "Z_macro", "Z_total", "Z_vec", "Z_chiral",
    "dot_vec_macro", "dot_chiral_macro", "dot_vec_chiral", "cycle_stage",
    "identity_state", "t", "uxy_coords",
]
PLATFORM_INDEPENDENT_KEYS = ["phi_index", "t"]  # pure integer counter / pure double accumulation
OMEGA0 = np.array([0.3 + 0.1j, -0.2 + 0.4j, 0.1 - 0.3j], dtype=np.complex128)
CASES = [  # (name, n_steps, dt, seed, version)
    ("n0_default_dt", 0, 0.1, None, None),
    ("n1_default_dt", 1, 0.1, 7, "k1-freeze"),
    ("n5_default_dt", 5, 0.1, 7, "k1-freeze"),
    ("n5_dt005", 5, 0.05, None, "k1-freeze"),
]
LATENT_N_STEPS, LATENT_DT = 3, 0.1


# ---------------------------------------------------------------- encoding (== k1_ab.py)
def _enc(a) -> dict:
    a = np.asarray(a)
    if a.dtype.kind == "c":
        flat = [[x.real.hex(), x.imag.hex()] for x in a.ravel().tolist()]
    elif a.dtype.kind == "f":
        flat = [float(x).hex() for x in a.ravel().tolist()]
    else:
        flat = [int(x) for x in a.ravel().tolist()]
    return {"dtype": str(a.dtype), "shape": list(a.shape), "data": flat}


def _enc_scalar(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return float(v).hex()
    if isinstance(v, (complex, np.complexfloating)):
        return [complex(v).real.hex(), complex(v).imag.hex()]
    if isinstance(v, np.ndarray):
        return _enc(v)
    if isinstance(v, (list, tuple)):
        return [_enc_scalar(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _enc_scalar(x) for k, x in v.items()}
    if v is None or isinstance(v, str):
        return v
    return {"__repr__": repr(v)}


def _state_snapshot(state: ModelState) -> dict:
    return {
        "Omega": _enc(state.Omega), "phi_index": int(state.phi_index),
        "cycle_stage": int(state.cycle_stage), "identity_state": int(state.identity_state),
        "z": float(state.z).hex(), "Z_macro": _enc(state.Z_macro), "Z_chiral": _enc(state.Z_chiral),
        "Z_vec": _enc(state.Z_vec), "t": float(state.t).hex(), "step": int(state.step),
    }


def _run_case(n_steps, dt, seed, version):
    state = ModelState(Omega=OMEGA0.copy())
    model = TriOctaPhaseLockModel(ModelParams())
    initial = _state_snapshot(state)
    hist = model.run(state, n_steps=n_steps, dt=dt, seed=seed, version=version)
    return initial, hist, state


def _case_record(n_steps, dt, seed, version) -> dict:
    initial, hist, state = _run_case(n_steps, dt, seed, version)
    return {
        "keys": sorted(k for k in hist.keys() if k != "_meta"),
        "history": {k: _enc(hist[k]) for k in HISTORY_KEYS},
        "meta_seed": hist["_meta"]["seed"], "meta_version": hist["_meta"]["version"],
        "has_latent_foreclosure": "latent_foreclosure" in hist,
        "initial_state": initial, "terminal_state": _state_snapshot(state),
    }


@dataclass
class _LatentParams(ModelParams):
    """Controlled custom params: the only way the current hook is reachable."""
    latent_foreclosure_enabled: bool = True
    lf_delta: float = 1e-4
    lf_K: int = 3
    lf_N: int = 8
    lf_eps: float = 0.05


def _latent_record() -> dict:
    state = ModelState(Omega=OMEGA0.copy())
    model = TriOctaPhaseLockModel(_LatentParams())
    hist = model.run(state, n_steps=LATENT_N_STEPS, dt=LATENT_DT)
    lf = hist.get("latent_foreclosure")
    return {
        "present": lf is not None,
        "entries": None if lf is None else [_enc_scalar(e) for e in lf],
        "history": {k: _enc(hist[k]) for k in HISTORY_KEYS},
        "terminal_state": _state_snapshot(state),
    }


# ---------------------------------------------------------------- environment binding
def current_environment_fingerprint() -> dict:
    try:
        cfg = np.show_config(mode="dicts")
    except Exception:  # numpy without dict-mode show_config: cannot match the authority
        cfg = {}
    deps = cfg.get("Build Dependencies", {})

    def dep(name):
        d = deps.get(name, {})
        return {"name": d.get("name"), "version": d.get("version"),
                "openblas configuration": d.get("openblas configuration")}

    simd = cfg.get("SIMD Extensions", {})
    # sys.version is parsed directly: platform.python_version()/python_compiler() reject the
    # "| packaged by Anaconda, Inc. |" form of sys.version used by the authoritative environment.
    compiler = re.search(r"\[(.*?)\]", sys.version)
    return {
        "system": platform.system(), "machine": platform.machine(),
        "python_version": "%d.%d.%d" % sys.version_info[:3],
        "python_compiler": compiler.group(1) if compiler else None,
        "numpy_version": np.__version__, "blas": dep("blas"), "lapack": dep("lapack"),
        "simd": {"baseline": simd.get("baseline"), "found": simd.get("found")},
    }


def _fingerprint_diff(expected: dict, actual: dict) -> list[str]:
    out = []
    for k in sorted(set(expected) | set(actual)):
        if expected.get(k) != actual.get(k):
            out.append(f"{k}: fixture={expected.get(k)!r} current={actual.get(k)!r}")
    return out


@pytest.fixture(scope="module")
def fixture() -> dict:
    raw = FIXTURE_PATH.read_bytes()
    recorded = FIXTURE_SHA256_PATH.read_text(encoding="utf-8").split()[0]
    assert hashlib.sha256(raw).hexdigest() == recorded, "immutable K1 history fixture was modified"
    return json.loads(raw.decode("utf-8"))


@pytest.fixture(scope="module")
def results(fixture) -> dict:
    return fixture["results"]


@pytest.fixture(scope="module")
def exact_env(fixture):
    """Gate for every bit-exact comparison against the Windows authority."""
    expected = fixture["authority"]["environment"]
    actual = current_environment_fingerprint()
    diff = _fingerprint_diff(expected, actual)
    if not diff:
        return actual
    if actual["system"] == expected["system"]:
        pytest.fail("authoritative Windows environment changed; the bit-exact fixture must be re-bound "
                    "deliberately, not skipped:\n  " + "\n  ".join(diff))
    pytest.skip("bit-exact history fixture is bound to the authoritative Windows environment; "
                "structural invariants still run here. Fingerprint mismatch:\n  " + "\n  ".join(diff))


# ---------------------------------------------------------------- fixture integrity
def test_fixture_is_immutable_and_bound_to_the_windows_authority(fixture, results):
    auth = fixture["authority"]
    assert auth["captured_from_commit"] == AUTHORITY_COMMIT
    assert auth["environment"]["system"] == "Windows"
    for key in ("machine", "python_version", "python_compiler", "numpy_version", "blas", "lapack", "simd"):
        assert auth["environment"][key] not in (None, {}, [])
    re_serialised = (json.dumps(results, indent=1, sort_keys=True) + "\n").encode("utf-8")
    assert hashlib.sha256(re_serialised).hexdigest() == auth["results_sha256"], \
        "embedded results are not the recorded BASE_WINDOWS capture"
    assert results["omega0"] == _enc(OMEGA0)
    assert set(results["cases"]) == {c[0] for c in CASES}


# ---------------------------------------------------------------- platform-independent invariants
@pytest.mark.parametrize("name,n_steps,dt,seed,version", CASES)
def test_history_structure_is_platform_independent(results, name, n_steps, dt, seed, version):
    expected = results["cases"][name]
    actual = _case_record(n_steps, dt, seed, version)
    assert actual["keys"] == expected["keys"]
    for k in HISTORY_KEYS:
        assert actual["history"][k]["dtype"] == expected["history"][k]["dtype"], f"{name}: dtype of {k}"
        assert actual["history"][k]["shape"] == expected["history"][k]["shape"], f"{name}: shape of {k}"
    for k in PLATFORM_INDEPENDENT_KEYS:
        assert actual["history"][k] == expected["history"][k], f"{name}: history[{k!r}] differs"
    assert actual["meta_seed"] == expected["meta_seed"]
    assert actual["meta_version"] == expected["meta_version"]
    assert actual["has_latent_foreclosure"] is False and expected["has_latent_foreclosure"] is False
    assert actual["initial_state"] == expected["initial_state"]  # no arithmetic involved
    for k in ("phi_index", "step", "t"):
        assert actual["terminal_state"][k] == expected["terminal_state"][k], f"{name}: terminal {k}"


def test_latent_hook_structure_is_platform_independent(results):
    expected = results["latent"]
    actual = _latent_record()
    assert actual["present"] is True and expected["present"] is True
    assert len(actual["entries"]) == len(expected["entries"]) == 1
    assert sorted(actual["entries"][0]) == sorted(expected["entries"][0]) == ["R_opt", "V_opt", "survival_frac"]
    for k in HISTORY_KEYS:
        assert actual["history"][k]["dtype"] == expected["history"][k]["dtype"]
        assert actual["history"][k]["shape"] == expected["history"][k]["shape"]
    for k in PLATFORM_INDEPENDENT_KEYS:
        assert actual["history"][k] == expected["history"][k]
    assert actual["terminal_state"]["step"] == expected["terminal_state"]["step"] == LATENT_N_STEPS


def test_record_before_step_ordering_and_terminal_mutation():
    initial, hist, state = _run_case(5, 0.1, None, None)
    # row 0 is the state BEFORE the first step
    assert _enc(hist["Omega"][0]) == initial["Omega"]
    assert int(hist["phi_index"][0]) == initial["phi_index"]
    assert float(hist["t"][0]).hex() == initial["t"]
    # the terminal state is one step past the last recorded row
    assert state.step == 5 and int(hist["phi_index"][-1]) == 4
    assert float(hist["t"][-1]).hex() == float(0.1 + 0.1 + 0.1 + 0.1).hex()
    assert float(state.t).hex() == float(0.1 + 0.1 + 0.1 + 0.1 + 0.1).hex()


def test_dt_only_advances_time_and_z_envelope():
    _, h1, s1 = _run_case(3, 0.1, None, None)
    _, h2, s2 = _run_case(3, 0.05, None, None)
    assert _enc(h1["Omega"]) == _enc(h2["Omega"])            # Omega path is dt-independent
    assert _enc(h1["phi_index"]) == _enc(h2["phi_index"])
    assert float(s1.t).hex() != float(s2.t).hex()


def test_z_total_and_z_vec_are_equal_contents_but_separate_arrays():
    _, hist, _ = _run_case(4, 0.1, None, None)
    assert np.array_equal(hist["Z_total"], hist["Z_vec"])
    assert hist["Z_total"] is not hist["Z_vec"]
    assert not np.shares_memory(hist["Z_total"], hist["Z_vec"])


def test_meta_shape_seed_and_version():
    _, hist, _ = _run_case(1, 0.1, 11, "v")
    meta = hist["_meta"]
    assert set(meta) == {"run_id", "seed", "version", "timestamp_utc"}
    assert meta["seed"] == 11 and meta["version"] == "v"
    assert re.fullmatch(r"run_[0-9a-f]{10}", meta["run_id"])
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", meta["timestamp_utc"])
    _, hist2, _ = _run_case(1, 0.1, None, None)
    assert hist2["_meta"]["seed"] is None and hist2["_meta"]["version"] == "unknown"


def test_default_params_never_trigger_latent_foreclosure():
    _, hist, _ = _run_case(6, 0.1, None, None)
    assert "latent_foreclosure" not in hist
    assert not hasattr(ModelParams(), "latent_foreclosure_enabled")


def test_history_does_not_alias_state_buffers():
    _, hist, state = _run_case(2, 0.1, None, None)
    for key in ("Z_macro", "Z_chiral", "Z_vec", "Z_total"):
        assert not np.shares_memory(hist[key], getattr(state, "Z_vec" if key == "Z_total" else key))
    assert not np.shares_memory(hist["Omega"], state.Omega)


# ---------------------------------------------------------------- bit-exact (authoritative environment only)
@pytest.mark.parametrize("name,n_steps,dt,seed,version", CASES)
def test_history_values_are_bit_exact_on_the_authoritative_environment(results, exact_env, name, n_steps, dt, seed, version):
    expected = results["cases"][name]
    actual = _case_record(n_steps, dt, seed, version)
    for k in HISTORY_KEYS:
        assert actual["history"][k] == expected["history"][k], f"{name}: history[{k!r}] differs bit-exactly"
    assert actual["terminal_state"] == expected["terminal_state"], f"{name}: terminal state differs"
    assert actual == expected


def test_latent_hook_output_is_bit_exact_on_the_authoritative_environment(results, exact_env):
    assert _latent_record() == results["latent"]
