"""K3 behaviour freeze for the TriOctaPhaseLockModel.phase_lock_step stochastic-forcing boundary.

Authority
---------
tests/fixtures/stochastic_forcing_boundary_k3/forcing_fixture.json is the production
bit-exact oracle.  Its ``results`` block is the verbatim BASE_WINDOWS capture of the
UNMODIFIED pre-K3 kernel at commit 7a3c5445 (noise block still inline in
phase_lock_step, no stochastic_forcing.py) taken on the authoritative Windows
`torment` environment, whose fingerprint is stored in ``authority.environment``.
Omega values involve transcendental functions (phase sync, Box-Muller), so they are
compared bit-exactly ONLY when the environment fingerprint matches (Windows drift
fails, other OSes skip).  The legacy MT19937 state (key, pos, has_gauss) is integer
arithmetic and is compared everywhere.  No tolerances.

Frozen
------
  * sigma <= 0 / NaN / None / absent: no RNG draw, global RNG state untouched, Omega exact;
  * sigma > 0 from np.random.seed(7): Omega exact after each of 8 calls, exact global RNG
    state before/after each call, exactly two standard_normal(3) draws per call in order
    (real part first, then imaginary), replicated bit-exactly with plain numpy;
  * g_override None / int 1 / 0.17 (float() coercion) with and without noise;
  * lambda_phase default and 0.0: phase-triad sync precedes the noise draws;
  * state.Omega is rebound on every call; with sigma <= 0 it is bound to the very object
    returned by apply_phase_triad_sync, with sigma > 0 to a new array;
  * failure/read ordering for unusual params objects (absent, None, 0, <0, >0, str, NaN,
    attribute access raising AttributeError -> treated as absent, raising RuntimeError ->
    propagates after lambda_phase was read, before state.Omega is rebound, no RNG draw);
  * full step() with sigma > 0 from np.random.seed(11): Omega, z, Z_vec per step (exact).
The capture encoding is identical to windows_ab/k3_ab.py (the A/B tool that produced the fixture).
"""
from __future__ import annotations

import ast
import hashlib
import json
import platform
import re
import sys
from pathlib import Path
from unittest import mock

import numpy as np
import pytest

from torment_service.kernel import model_core
from torment_service.kernel.model_core import ModelParams, ModelState, TriOctaPhaseLockModel
from torment_service.kernel.phase_triad_sync import apply_phase_triad_sync
from torment_service.kernel.stochastic_forcing import apply_stochastic_forcing

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "stochastic_forcing_boundary_k3"
FIXTURE_PATH = FIXTURE_DIR / "forcing_fixture.json"
FIXTURE_SHA256_PATH = FIXTURE_DIR / "forcing_fixture.sha256"
AUTHORITY_COMMIT = "7a3c5445399e4f613cb615c8a60143361805e115"

OMEGA0 = np.array([0.3 + 0.1j, -0.2 + 0.4j, 0.1 - 0.3j], dtype=np.complex128)
SIGMAS = {"sigma_default0": None, "sigma_pos": 0.01, "sigma_neg": -0.5, "sigma_nan": float("nan")}
G_OVERRIDES = {"g_none": None, "g_int1": 1, "g_017": 0.17}
LAMBDAS = {"lam_default": None, "lam_zero": 0.0}
N_PLS, SEED_PLS = 8, 7
N_STEP, SEED_STEP, SIGMA_STEP = 6, 11, 0.01
NOISY_PREFIX = "sigma_pos"


# ---------------------------------------------------------------- capture (== k3_ab.py)
def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _enc(a) -> dict:
    a = np.asarray(a)
    if a.dtype.kind == "c":
        flat = [[x.real.hex(), x.imag.hex()] for x in a.ravel().tolist()]
    elif a.dtype.kind == "f":
        flat = [float(x).hex() for x in a.ravel().tolist()]
    else:
        flat = [int(x) for x in a.ravel().tolist()]
    return {"dtype": str(a.dtype), "shape": list(a.shape), "data": flat}


def _mt(digest: dict) -> tuple:
    return (digest["algo"], digest["key_sha256"], digest["pos"], digest["has_gauss"])


def rng_digest() -> dict:
    name, keys, pos, has_gauss, cached = np.random.get_state()
    return {"algo": str(name), "key_sha256": _sha256_bytes(np.asarray(keys, dtype=np.uint32).tobytes()),
            "pos": int(pos), "has_gauss": int(has_gauss), "cached_gaussian": float(cached).hex()}


def _params(sigma, lam) -> ModelParams:
    kw = {}
    if sigma is not None:
        kw["omega_noise_sigma"] = sigma
    if lam is not None:
        kw["lambda_phase"] = lam
    return ModelParams(**kw)


def _pls_case(sigma, g_override, lam) -> dict:
    np.random.seed(SEED_PLS)
    state = ModelState(Omega=OMEGA0.copy())
    model = TriOctaPhaseLockModel(_params(sigma, lam))
    rows = []
    for _ in range(N_PLS):
        before = rng_digest()
        prev = state.Omega
        if g_override is None:
            model.phase_lock_step(state)
        else:
            model.phase_lock_step(state, g_override=g_override)
        rows.append({"Omega": _enc(state.Omega), "rng_before": before, "rng_after": rng_digest(),
                     "rebound": state.Omega is not prev})
    return {"rows": rows}


def _step_case() -> dict:
    np.random.seed(SEED_STEP)
    state = ModelState(Omega=OMEGA0.copy())
    model = TriOctaPhaseLockModel(ModelParams(omega_noise_sigma=SIGMA_STEP))
    rows = []
    for _ in range(N_STEP):
        model.step(state, dt=0.1)
        rows.append({"Omega": _enc(state.Omega), "z": float(state.z).hex(), "Z_vec": _enc(state.Z_vec),
                     "t": float(state.t).hex(), "step": int(state.step), "rng_after": rng_digest()})
    return {"rows": rows}


def _draw_order_oracle() -> dict:
    out = {}
    for seed in (0, 7, 12345):
        sigma = 0.01
        np.random.seed(seed)
        state = ModelState(Omega=OMEGA0.copy())
        model = TriOctaPhaseLockModel(ModelParams(omega_noise_sigma=sigma))
        model.phase_lock_step(state)
        kernel_rng = rng_digest()
        quiet = ModelState(Omega=OMEGA0.copy())
        TriOctaPhaseLockModel(ModelParams()).phase_lock_step(quiet)
        np.random.seed(seed)
        n1 = np.random.standard_normal(3)
        n2 = np.random.standard_normal(3)
        replica = quiet.Omega + (sigma * (n1 + 1j * n2).astype(np.complex128))
        out[f"seed_{seed}"] = {"kernel": _enc(state.Omega), "replica": _enc(replica),
                               "equal": bool(np.array_equal(state.Omega, replica)),
                               "kernel_rng_after": kernel_rng, "replica_rng_after": rng_digest()}
    return out


def build_results() -> dict:
    return {
        "omega0": _enc(OMEGA0),
        "phase_lock_step": {f"{s}|{g}|{l}": _pls_case(SIGMAS[s], G_OVERRIDES[g], LAMBDAS[l])
                            for s in SIGMAS for g in G_OVERRIDES for l in LAMBDAS},
        "full_step_sigma_pos": _step_case(),
        "draw_order_oracle": _draw_order_oracle(),
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
        return {"name": d.get("name"), "version": d.get("version"), "openblas configuration": d.get("openblas configuration")}

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
    assert hashlib.sha256(raw).hexdigest() == recorded, "immutable K3 forcing fixture was modified"
    return json.loads(raw.decode("utf-8"))


@pytest.fixture(scope="module")
def results(fixture) -> dict:
    return fixture["results"]


@pytest.fixture(scope="module")
def actual() -> dict:
    saved = np.random.get_state()
    try:
        return build_results()
    finally:
        np.random.set_state(saved)


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
    pytest.skip("bit-exact forcing fixture is bound to the authoritative Windows environment; "
                "structural and RNG-state invariants still run here. Fingerprint mismatch:\n  " + "\n  ".join(diff))


@pytest.fixture
def rng_restore():
    saved = np.random.get_state()
    yield
    np.random.set_state(saved)


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
    assert set(results["phase_lock_step"]) == {f"{s}|{g}|{l}" for s in SIGMAS for g in G_OVERRIDES for l in LAMBDAS}


# ---------------------------------------------------------------- platform-independent: RNG state and draws
@pytest.mark.parametrize("case", [f"{s}|{g}|{l}" for s in SIGMAS for g in G_OVERRIDES for l in LAMBDAS])
def test_rng_state_sequence_is_exact_and_platform_independent(results, actual, case):
    exp_rows, act_rows = results["phase_lock_step"][case]["rows"], actual["phase_lock_step"][case]["rows"]
    assert len(act_rows) == len(exp_rows) == N_PLS
    noisy = case.startswith(NOISY_PREFIX)
    for i, (a, e) in enumerate(zip(act_rows, exp_rows)):
        # MT19937 key/pos/has_gauss are integer state: identical on every platform
        assert _mt(a["rng_before"]) == _mt(e["rng_before"]) and _mt(a["rng_after"]) == _mt(e["rng_after"]), f"{case} row {i}: RNG state"
        assert a["rebound"] is True and e["rebound"] is True
        assert a["Omega"]["dtype"] == e["Omega"]["dtype"] == "complex128" and a["Omega"]["shape"] == [3]
        if not noisy:
            assert a["rng_before"] == a["rng_after"], f"{case} row {i}: RNG consumed although sigma <= 0"
        else:
            assert a["rng_before"] != a["rng_after"], f"{case} row {i}: RNG not consumed although sigma > 0"
            assert a["rng_after"]["has_gauss"] == 0  # six Gaussians = three Box-Muller pairs, nothing cached
    for a, e in zip(actual["full_step_sigma_pos"]["rows"], results["full_step_sigma_pos"]["rows"]):
        assert _mt(a["rng_after"]) == _mt(e["rng_after"]) and (a["t"], a["step"]) == (e["t"], e["step"])


def test_exactly_two_standard_normal_3_draws_per_noisy_call_in_order(rng_restore):
    calls = []
    real = np.random.standard_normal

    def recording(*args, **kwargs):
        calls.append((args, kwargs))
        return real(*args, **kwargs)

    model = TriOctaPhaseLockModel(ModelParams(omega_noise_sigma=0.01))
    state = ModelState(Omega=OMEGA0.copy())
    with mock.patch.object(np.random, "standard_normal", recording):
        for _ in range(3):
            model.phase_lock_step(state)
    assert calls == [((3,), {})] * 6
    calls.clear()
    quiet = TriOctaPhaseLockModel(ModelParams())
    with mock.patch.object(np.random, "standard_normal", recording):
        quiet.phase_lock_step(ModelState(Omega=OMEGA0.copy()))
    assert calls == []


def test_noise_is_replicated_bit_exactly_by_two_ordered_draws(rng_restore, actual):
    for rec in actual["draw_order_oracle"].values():
        assert rec["equal"] is True and rec["kernel"] == rec["replica"]
        assert rec["kernel_rng_after"] == rec["replica_rng_after"]


def test_helper_is_identity_without_draws_when_sigma_not_positive(rng_restore):
    omega = OMEGA0.copy()
    for sigma in (0.0, -0.5, float("nan"), -0.0):
        before = rng_digest()
        out = apply_stochastic_forcing(omega, sigma)
        assert out is omega and rng_digest() == before
    np.random.seed(3)
    out = apply_stochastic_forcing(omega, 0.01)
    assert out is not omega and out.dtype == np.complex128 and not np.shares_memory(out, omega)
    np.random.seed(3)
    n1 = np.random.standard_normal(3)
    n2 = np.random.standard_normal(3)
    assert _enc(out) == _enc(omega + (0.01 * (n1 + 1j * n2).astype(np.complex128)))
    assert np.array_equal(omega, OMEGA0)  # input untouched


def test_phase_sync_precedes_noise_and_omega_is_rebound_to_the_sync_result_when_quiet(rng_restore):
    order = []
    real_sync = model_core.apply_phase_triad_sync
    real_sn = np.random.standard_normal
    returned = {}

    def sync(omega_next, lam):
        order.append("sync")
        out = real_sync(omega_next, lam)
        returned["sync"] = out
        return out

    def sn(*a, **k):
        order.append("draw")
        return real_sn(*a, **k)

    state = ModelState(Omega=OMEGA0.copy())
    with mock.patch.object(model_core, "apply_phase_triad_sync", sync), mock.patch.object(np.random, "standard_normal", sn):
        TriOctaPhaseLockModel(ModelParams(omega_noise_sigma=0.01)).phase_lock_step(state)
    assert order == ["sync", "draw", "draw"]
    assert state.Omega is not returned["sync"]
    order.clear()
    quiet = ModelState(Omega=OMEGA0.copy())
    prev = quiet.Omega
    with mock.patch.object(model_core, "apply_phase_triad_sync", sync), mock.patch.object(np.random, "standard_normal", sn):
        TriOctaPhaseLockModel(ModelParams()).phase_lock_step(quiet)
    assert order == ["sync"]
    assert quiet.Omega is returned["sync"] and quiet.Omega is not prev


def test_g_override_int_coerces_like_float_and_default_g_path_unchanged(rng_restore):
    a, b = ModelState(Omega=OMEGA0.copy()), ModelState(Omega=OMEGA0.copy())
    model = TriOctaPhaseLockModel(ModelParams())
    model.phase_lock_step(a, g_override=1)
    model.phase_lock_step(b, g_override=1.0)
    assert _enc(a.Omega) == _enc(b.Omega)
    c, d = ModelState(Omega=OMEGA0.copy()), ModelState(Omega=OMEGA0.copy())
    model.phase_lock_step(c)
    model.phase_lock_step(d, g_override=model.p.g)
    assert _enc(c.Omega) == _enc(d.Omega)


# ---------------------------------------------------------------- unusual params objects
class _Raise:
    def __init__(self, exc):
        self.exc = exc


class _OddParams:
    """ModelParams' values as a plain object; omega_noise_sigma absent, odd, or raising on access."""

    def __init__(self, sigma_spec, log=None):
        base = ModelParams()
        for name in base.__dataclass_fields__:
            if name != "omega_noise_sigma":
                object.__setattr__(self, name, getattr(base, name))
        if sigma_spec != "ABSENT":
            object.__setattr__(self, "omega_noise_sigma", sigma_spec)
        object.__setattr__(self, "_log", log if log is not None else [])

    def __getattribute__(self, name):
        if name.startswith("_") :
            return object.__getattribute__(self, name)
        object.__getattribute__(self, "_log").append(name)
        value = object.__getattribute__(self, name)
        if isinstance(value, _Raise):
            raise value.exc
        return value


READ_ORDER = ["eps", "g", "k_vals", "delta_vals", "lambda_phase", "omega_noise_sigma"]


@pytest.mark.parametrize("spec", ["ABSENT", None, 0, -0.5, float("nan"), _Raise(AttributeError("no sigma"))],
                         ids=["absent", "none", "zero", "negative", "nan", "raises_AttributeError"])
def test_quiet_sigma_variants_draw_nothing_and_match_default_params(rng_restore, spec):
    log = []
    odd = TriOctaPhaseLockModel(_OddParams(spec, log))
    ref = TriOctaPhaseLockModel(ModelParams())
    s_odd, s_ref = ModelState(Omega=OMEGA0.copy()), ModelState(Omega=OMEGA0.copy())
    before = rng_digest()
    odd.phase_lock_step(s_odd)
    assert rng_digest() == before
    ref.phase_lock_step(s_ref)
    assert _enc(s_odd.Omega) == _enc(s_ref.Omega)
    assert log == READ_ORDER


@pytest.mark.parametrize("spec", [0.01, "0.01", np.float64(0.01)], ids=["float", "str", "np_float64"])
def test_positive_sigma_variants_coerce_identically_and_draw(rng_restore, spec):
    np.random.seed(5)
    s_odd = ModelState(Omega=OMEGA0.copy())
    TriOctaPhaseLockModel(_OddParams(spec)).phase_lock_step(s_odd)
    after_odd = rng_digest()
    np.random.seed(5)
    s_ref = ModelState(Omega=OMEGA0.copy())
    TriOctaPhaseLockModel(ModelParams(omega_noise_sigma=0.01)).phase_lock_step(s_ref)
    assert _enc(s_odd.Omega) == _enc(s_ref.Omega) and after_odd == rng_digest()


def test_sigma_access_raising_runtimeerror_propagates_after_lambda_phase_before_any_write(rng_restore):
    log = []
    model = TriOctaPhaseLockModel(_OddParams(_Raise(RuntimeError("boom")), log))
    state = ModelState(Omega=OMEGA0.copy())
    prev = state.Omega
    before = rng_digest()
    with pytest.raises(RuntimeError) as excinfo:
        model.phase_lock_step(state)
    assert type(excinfo.value) is RuntimeError and str(excinfo.value) == "boom"
    assert log == READ_ORDER                       # failed exactly at the sigma read, after lambda_phase
    assert state.Omega is prev and np.array_equal(state.Omega, OMEGA0)  # never rebound
    assert rng_digest() == before                  # nothing drawn


def test_model_core_import_surface_does_not_eagerly_import_stochastic_forcing():
    tree = ast.parse(Path(model_core.__file__).read_text(encoding="utf-8"))
    module_level = {("." * n.level + (n.module or "")) for n in tree.body if isinstance(n, ast.ImportFrom)}
    assert ".stochastic_forcing" not in module_level  # theta-contract allowlist keeps holding
    pls = next(m for m in ast.walk(tree) if isinstance(m, ast.FunctionDef) and m.name == "phase_lock_step")
    lazy = [n for n in ast.walk(pls) if isinstance(n, ast.ImportFrom) and n.module == "stochastic_forcing"]
    assert len(lazy) == 1 and [a.name for a in lazy[0].names] == ["apply_stochastic_forcing"]


# ---------------------------------------------------------------- bit-exact (authoritative environment only)
@pytest.mark.parametrize("case", [f"{s}|{g}|{l}" for s in SIGMAS for g in G_OVERRIDES for l in LAMBDAS])
def test_phase_lock_step_omega_is_bit_exact_on_the_authoritative_environment(results, actual, exact_env, case):
    assert actual["phase_lock_step"][case] == results["phase_lock_step"][case]


def test_full_step_with_noise_is_bit_exact_on_the_authoritative_environment(results, actual, exact_env):
    assert actual["full_step_sigma_pos"] == results["full_step_sigma_pos"]
    assert actual["draw_order_oracle"] == results["draw_order_oracle"]
