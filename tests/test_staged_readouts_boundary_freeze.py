"""K2 behaviour freeze for the TriOctaPhaseLockModel.update_z staged-readout boundary.

Authority
---------
tests/fixtures/staged_readouts_boundary_k2/readouts_fixture.json is the production
bit-exact oracle.  Its ``results`` block is the verbatim BASE_WINDOWS capture of the
UNMODIFIED pre-K2 kernel at commit afbb1235 (update_z still computing in place, no
staged_readouts.py) taken on the authoritative Windows `torment` environment, whose
fingerprint is stored in ``authority.environment``.  The fixture is not a portable
oracle (Linux differs in the last ulp), so:

  * platform-independent invariants run everywhere: alias identity of the Z arrays,
    state.z being a Python float, in-place write semantics, theta_lock_override
    None == explicit default, idempotent re-call, update_z == compute_staged_z,
    purity of compute_staged_z, phi_index / t / step bookkeeping, shapes/dtypes,
    the model_core import surface (staged_readouts imported lazily only), and the
    pre-K2 failure point for params missing z_alpha/z_beta (AttributeError after
    z, Z_macro and Z_chiral are written, Z_vec untouched);
  * every float.hex comparison runs ONLY when the environment fingerprint matches;
    on Windows a mismatch FAILS (authoritative environment drifted), elsewhere the
    exact comparisons are SKIPPED with the fingerprint difference in the reason;
  * there are no tolerances anywhere.

What is frozen bit-exactly (noise disabled, default params unless stated):
  * 6 steps with and without theta_lock_override (default and custom params:
    lambda_vp, gamma, theta_lock, z_alpha, z_beta, d24_steps, phi_step_per_iter),
    recording z, Z_macro, Z_chiral, Z_vec, kappa, t, phi_index, cycle/identity after
    each step (post-increment state.t semantics);
  * direct update_z() calls on constructed states: 3 Omega vectors x phi_index
    {0, 5, 11} x t {0.0, 0.35, 1.7} x override {None, 0.0, 1.1}, default and custom.
The capture encoding is identical to windows_ab/k2_ab.py (the A/B tool that produced
the fixture).
"""
from __future__ import annotations

import ast
import hashlib
import json
import platform
import re
import sys
from pathlib import Path

import numpy as np
import pytest

from torment_service.kernel import model_core
from torment_service.kernel.model_core import ModelParams, ModelState, TriOctaPhaseLockModel
from torment_service.kernel.staged_readouts import StagedReadouts, compute_staged_z

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "staged_readouts_boundary_k2"
FIXTURE_PATH = FIXTURE_DIR / "readouts_fixture.json"
FIXTURE_SHA256_PATH = FIXTURE_DIR / "readouts_fixture.sha256"
AUTHORITY_COMMIT = "afbb1235c7dfad2867dbe2f23c0a44ca11bfbe31"

OMEGAS = {
    "omega_a": np.array([0.3 + 0.1j, -0.2 + 0.4j, 0.1 - 0.3j], dtype=np.complex128),
    "omega_b": np.array([1.2 - 0.4j, 0.05 + 0.9j, -0.7 - 0.2j], dtype=np.complex128),
    "omega_zero": np.zeros(3, dtype=np.complex128),
}
STEP_CASES = [  # (name, params_kind, n_steps, dt, override)
    ("default_step", "default", 6, 0.1, None),
    ("default_step_override", "default", 6, 0.1, 0.369),
    ("custom_step", "custom", 6, 0.05, None),
    ("custom_step_override", "custom", 6, 0.05, -0.3),
]
DIRECT_PHI = [0, 5, 11]
DIRECT_T = [0.0, 0.35, 1.7]
DIRECT_OVERRIDE = [None, 0.0, 1.1]
CUSTOM_PARAMS = dict(lambda_vp=0.9, gamma=0.1, theta_lock=0.7, z_alpha=0.3, z_beta=1.25,
                     d24_steps=7, phi_step_per_iter=2)
READOUT_ARRAYS = ("Z_macro", "Z_chiral", "Z_vec")


# ---------------------------------------------------------------- capture (== k2_ab.py)
def _enc(a) -> dict:
    a = np.asarray(a)
    if a.dtype.kind == "c":
        flat = [[x.real.hex(), x.imag.hex()] for x in a.ravel().tolist()]
    elif a.dtype.kind == "f":
        flat = [float(x).hex() for x in a.ravel().tolist()]
    else:
        flat = [int(x) for x in a.ravel().tolist()]
    return {"dtype": str(a.dtype), "shape": list(a.shape), "data": flat}


def _params(kind) -> ModelParams:
    return ModelParams() if kind == "default" else ModelParams(**CUSTOM_PARAMS)


def _readout_snapshot(state: ModelState) -> dict:
    return {
        "z": float(state.z).hex(), "z_type": type(state.z).__name__,
        "Z_macro": _enc(state.Z_macro), "Z_chiral": _enc(state.Z_chiral), "Z_vec": _enc(state.Z_vec),
        "t": float(state.t).hex(), "phi_index": int(state.phi_index), "step": int(state.step),
        "kappa": float(state.kappa()).hex(),
        "cycle_stage": int(state.cycle_stage), "identity_state": int(state.identity_state),
    }


def _step_case(kind, n_steps, dt, override) -> dict:
    state = ModelState(Omega=OMEGAS["omega_a"].copy())
    model = TriOctaPhaseLockModel(_params(kind))
    rows = []
    for _ in range(n_steps):
        if override is None:
            model.step(state, dt=dt)
        else:
            model.step(state, dt=dt, theta_lock_override=override)
        rows.append(_readout_snapshot(state))
    return {"rows": rows, "terminal_Omega": _enc(state.Omega)}


def _direct_key(oname, phi, t, ov) -> str:
    return f"{oname}|phi={phi}|t={float(t).hex()}|override={'None' if ov is None else float(ov).hex()}"


def _direct_case(kind) -> dict:
    model = TriOctaPhaseLockModel(_params(kind))
    out = {}
    for oname, omega in OMEGAS.items():
        for phi in DIRECT_PHI:
            for t in DIRECT_T:
                for ov in DIRECT_OVERRIDE:
                    state = ModelState(Omega=omega.copy(), phi_index=phi, t=t)
                    if ov is None:
                        model.update_z(state)
                    else:
                        model.update_z(state, theta_lock_override=ov)
                    out[_direct_key(oname, phi, t, ov)] = {
                        "z": float(state.z).hex(), "Z_macro": _enc(state.Z_macro),
                        "Z_chiral": _enc(state.Z_chiral), "Z_vec": _enc(state.Z_vec),
                        "Omega_unchanged": bool(np.array_equal(state.Omega, omega)),
                    }
    return out


def build_results() -> dict:
    return {
        "omegas": {k: _enc(v) for k, v in OMEGAS.items()},
        "custom_params": {k: (float(v).hex() if isinstance(v, float) else v) for k, v in CUSTOM_PARAMS.items()},
        "step_cases": {name: _step_case(kind, n, dt, ov) for name, kind, n, dt, ov in STEP_CASES},
        "direct_default": _direct_case("default"),
        "direct_custom": _direct_case("custom"),
    }


# ---------------------------------------------------------------- environment binding
def current_environment_fingerprint() -> dict:
    try:
        cfg = np.show_config(mode="dicts")
    except Exception:
        cfg = {}
    deps = cfg.get("Build Dependencies", {})

    def dep(name):
        d = deps.get(name, {})
        return {"name": d.get("name"), "version": d.get("version"),
                "openblas configuration": d.get("openblas configuration")}

    simd = cfg.get("SIMD Extensions", {})
    compiler = re.search(r"\[(.*?)\]", sys.version)  # platform.python_version() rejects Anaconda's sys.version
    return {
        "system": platform.system(), "machine": platform.machine(),
        "python_version": "%d.%d.%d" % sys.version_info[:3],
        "python_compiler": compiler.group(1) if compiler else None,
        "numpy_version": np.__version__, "blas": dep("blas"), "lapack": dep("lapack"),
        "simd": {"baseline": simd.get("baseline"), "found": simd.get("found")},
    }


def _fingerprint_diff(expected: dict, actual: dict) -> list[str]:
    return [f"{k}: fixture={expected.get(k)!r} current={actual.get(k)!r}"
            for k in sorted(set(expected) | set(actual)) if expected.get(k) != actual.get(k)]


@pytest.fixture(scope="module")
def fixture() -> dict:
    raw = FIXTURE_PATH.read_bytes()
    recorded = FIXTURE_SHA256_PATH.read_text(encoding="utf-8").split()[0]
    assert hashlib.sha256(raw).hexdigest() == recorded, "immutable K2 readouts fixture was modified"
    return json.loads(raw.decode("utf-8"))


@pytest.fixture(scope="module")
def results(fixture) -> dict:
    return fixture["results"]


@pytest.fixture(scope="module")
def actual() -> dict:
    return build_results()


@pytest.fixture(scope="module")
def exact_env(fixture):
    expected = fixture["authority"]["environment"]
    current = current_environment_fingerprint()
    diff = _fingerprint_diff(expected, current)
    if not diff:
        return current
    if current["system"] == expected["system"]:
        pytest.fail("authoritative Windows environment changed; the bit-exact fixture must be re-bound "
                    "deliberately, not skipped:\n  " + "\n  ".join(diff))
    pytest.skip("bit-exact readouts fixture is bound to the authoritative Windows environment; "
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
    assert results["omegas"] == {k: _enc(v) for k, v in OMEGAS.items()}
    assert set(results["step_cases"]) == {c[0] for c in STEP_CASES}
    assert len(results["direct_default"]) == len(results["direct_custom"]) == 81


# ---------------------------------------------------------------- platform-independent invariants
@pytest.mark.parametrize("name", [c[0] for c in STEP_CASES])
def test_step_bookkeeping_and_shapes_are_platform_independent(results, actual, name):
    exp_rows, act_rows = results["step_cases"][name]["rows"], actual["step_cases"][name]["rows"]
    assert len(act_rows) == len(exp_rows) == 6
    for i, (a, e) in enumerate(zip(act_rows, exp_rows)):
        assert a["z_type"] == e["z_type"] == "float", f"{name} row {i}: state.z must stay a Python float"
        for key in READOUT_ARRAYS:
            assert (a[key]["dtype"], a[key]["shape"]) == (e[key]["dtype"], e[key]["shape"]) == ("float64", [3])
        for key in ("t", "phi_index", "step"):  # pure += dt / integer modulus / counter
            assert a[key] == e[key], f"{name} row {i}: {key}"


def test_direct_cases_keep_omega_untouched_and_cover_the_grid(results, actual):
    for block in ("direct_default", "direct_custom"):
        assert set(actual[block]) == set(results[block])
        for key, rec in actual[block].items():
            assert rec["Omega_unchanged"] is True and results[block][key]["Omega_unchanged"] is True, key
            for arr in READOUT_ARRAYS:
                assert (rec[arr]["dtype"], rec[arr]["shape"]) == ("float64", [3])


def test_update_z_writes_in_place_and_preserves_array_identity():
    model = TriOctaPhaseLockModel(ModelParams())
    state = ModelState(Omega=OMEGAS["omega_a"].copy())
    before = {k: getattr(state, k) for k in READOUT_ARRAYS}
    external = {k: getattr(state, k) for k in READOUT_ARRAYS}  # an external holder of the buffers
    model.update_z(state)
    for k in READOUT_ARRAYS:
        assert getattr(state, k) is before[k], f"{k} was rebound instead of written in place"
        assert np.shares_memory(getattr(state, k), external[k])
        assert np.any(external[k] != 0.0), f"external holder of {k} did not observe the in-place write"
    assert type(state.z) is float
    model.step(state, dt=0.1)
    for k in READOUT_ARRAYS:
        assert getattr(state, k) is before[k]
        assert np.array_equal(external[k], getattr(state, k))


def test_override_none_equals_explicit_default_theta_lock_bitwise():
    params = ModelParams()
    a = ModelState(Omega=OMEGAS["omega_b"].copy(), phi_index=5, t=0.35)
    b = ModelState(Omega=OMEGAS["omega_b"].copy(), phi_index=5, t=0.35)
    model = TriOctaPhaseLockModel(params)
    model.update_z(a)
    model.update_z(b, theta_lock_override=params.theta_lock)
    assert _readout_snapshot(a) == _readout_snapshot(b)
    c = ModelState(Omega=OMEGAS["omega_b"].copy(), phi_index=5, t=0.35)
    model.update_z(c, theta_lock_override=params.theta_lock + 0.125)
    assert c.z != a.z  # the override is actually threaded into the computation


def test_update_z_is_idempotent_for_a_fixed_state_and_uses_the_given_t():
    model = TriOctaPhaseLockModel(ModelParams())
    state = ModelState(Omega=OMEGAS["omega_a"].copy())
    model.step(state, dt=0.1)
    first = _readout_snapshot(state)
    model.update_z(state)  # recompute on the post-increment state: must be a pure function of it
    assert _readout_snapshot(state) == first
    assert float(state.t).hex() == float(0.1).hex() and state.step == 1
    rewound = ModelState(Omega=state.Omega.copy(), phi_index=state.phi_index, t=0.0)
    model.update_z(rewound)
    assert rewound.z != state.z  # z depends on the (post-increment) state.t it is given


def test_update_z_delegates_bit_exactly_to_compute_staged_z():
    for kind in ("default", "custom"):
        params = _params(kind)
        model = TriOctaPhaseLockModel(params)
        for oname, omega in OMEGAS.items():
            for ov in (None, 1.1):
                state = ModelState(Omega=omega.copy(), phi_index=5, t=0.35)
                if ov is None:
                    model.update_z(state)
                else:
                    model.update_z(state, theta_lock_override=ov)
                r = compute_staged_z(
                    state.Omega, state.kappa(), state.phi_index, state.t,
                    d24_steps=params.d24_steps, lambda_vp=params.lambda_vp, gamma=params.gamma,
                    theta_lock=params.theta_lock if ov is None else ov,
                    z_alpha=params.z_alpha, z_beta=params.z_beta,
                )
                assert isinstance(r, StagedReadouts)
                assert float(r.z).hex() == float(state.z).hex()
                for k in READOUT_ARRAYS:
                    assert _enc(getattr(r, k)) == _enc(getattr(state, k)), (kind, oname, ov, k)
                    assert getattr(r, k) is not getattr(state, k) and not np.shares_memory(getattr(r, k), getattr(state, k))
                assert float(r.rho).hex() == float(state.kappa() / (1.0 + state.kappa())).hex()


def test_compute_staged_z_is_pure():
    omega = OMEGAS["omega_b"].copy()
    snapshot = omega.copy()
    r1 = compute_staged_z(omega, float(np.linalg.norm(omega)), 7, 0.35, d24_steps=12, lambda_vp=0.618,
                          gamma=0.577, theta_lock=0.244, z_alpha=1.0, z_beta=0.5)
    r2 = compute_staged_z(omega, float(np.linalg.norm(omega)), 7, 0.35, d24_steps=12, lambda_vp=0.618,
                          gamma=0.577, theta_lock=0.244, z_alpha=1.0, z_beta=0.5)
    assert np.array_equal(omega, snapshot)
    assert [float(x).hex() for x in (r1.rho, r1.theta, r1.z)] == [float(x).hex() for x in (r2.rho, r2.theta, r2.z)]
    for k in READOUT_ARRAYS:
        assert _enc(getattr(r1, k)) == _enc(getattr(r2, k))
        assert getattr(r1, k) is not getattr(r2, k)
        assert getattr(r1, k).dtype == np.float64 and getattr(r1, k).shape == (3,)
    assert r1.Z_vec.tolist() == (1.0 * r1.Z_macro + 0.5 * r1.Z_chiral).tolist()


def test_model_core_import_surface_does_not_eagerly_import_staged_readouts():
    tree = ast.parse(Path(model_core.__file__).read_text(encoding="utf-8"))
    module_level = {("." * n.level + (n.module or "")) for n in tree.body if isinstance(n, ast.ImportFrom)}
    assert ".staged_readouts" not in module_level  # theta-contract allowlist keeps holding
    update_z = next(m for m in ast.walk(tree) if isinstance(m, ast.FunctionDef) and m.name == "update_z")
    lazy = [n for n in ast.walk(update_z) if isinstance(n, ast.ImportFrom) and n.module == "staged_readouts"]
    assert len(lazy) == 1 and sorted(a.name for a in lazy[0].names) == ["blend_z", "compute_chiral_z", "compute_macro_z"]


# ---------------------------------------------------------------- failure-point characterization
class _IncompleteParams:
    """ModelParams' attribute values as a plain object, with some attributes missing."""

    def __init__(self, *missing: str, **values):
        base = ModelParams(**values)
        for name in base.__dataclass_fields__:
            if name not in missing:
                setattr(self, name, getattr(base, name))


@pytest.mark.parametrize("missing,expected_name", [
    (("z_alpha",), "z_alpha"),
    (("z_beta",), "z_beta"),
    (("z_alpha", "z_beta"), "z_alpha"),
])
def test_params_missing_blend_weights_fail_after_z_macro_chiral_are_written(missing, expected_name):
    """Pre-K2 ordering: z, Z_macro[:], Z_chiral[:] are written, then AttributeError on the blend weight."""
    values = dict(lambda_vp=0.9, gamma=0.1, theta_lock=0.7, d24_steps=7)
    reference = TriOctaPhaseLockModel(ModelParams(**values))
    ref_state = ModelState(Omega=OMEGAS["omega_b"].copy(), phi_index=5, t=0.35)
    reference.update_z(ref_state, theta_lock_override=0.2)

    model = TriOctaPhaseLockModel(_IncompleteParams(*missing, **values))
    state = ModelState(Omega=OMEGAS["omega_b"].copy(), phi_index=5, t=0.35)
    state.Z_vec[:] = [7.0, -7.0, 7.5]  # sentinel: must survive the failure untouched
    z_vec_obj = state.Z_vec
    with pytest.raises(AttributeError) as excinfo:
        model.update_z(state, theta_lock_override=0.2)
    assert type(excinfo.value) is AttributeError
    assert excinfo.value.name == expected_name
    # visible mutation at the point of failure: exactly the first three writes, bit-exact
    assert type(state.z) is float and float(state.z).hex() == float(ref_state.z).hex()
    assert _enc(state.Z_macro) == _enc(ref_state.Z_macro)
    assert _enc(state.Z_chiral) == _enc(ref_state.Z_chiral)
    assert state.Z_vec is z_vec_obj and state.Z_vec.tolist() == [7.0, -7.0, 7.5]
    assert np.array_equal(state.Omega, OMEGAS["omega_b"]) and state.phi_index == 5 and state.t == 0.35


# ---------------------------------------------------------------- bit-exact (authoritative environment only)
@pytest.mark.parametrize("name", [c[0] for c in STEP_CASES])
def test_step_readouts_are_bit_exact_on_the_authoritative_environment(results, actual, exact_env, name):
    assert actual["step_cases"][name] == results["step_cases"][name]


@pytest.mark.parametrize("block", ["direct_default", "direct_custom"])
def test_direct_update_z_is_bit_exact_on_the_authoritative_environment(results, actual, exact_env, block):
    for key in results[block]:
        assert actual[block][key] == results[block][key], key
    assert actual[block] == results[block]
