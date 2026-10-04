"""P4A relocation contracts, captured from 48fc146 before definitions was edited.

The compact fixture holds exact results and function AST hashes, not source.
Floating-point captures are bound to the recorded Windows/NumPy environment;
a drift on Windows fails rather than silently skipping or rebasing the data.
"""
from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import importlib
import inspect
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import textwrap
import warnings

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/kernel_definitions_p4a.json"
FIXTURE_SHA256 = "fdd17d9eab96c2ae43d2bbbb399a5d112fcf3e03f20552d6f2e72603c562e583"
PREDECESSOR = "48fc146b1e5837e770218494129dcd5d6975dc5e"
GROUPS = {
    "observables.chirality": (
        "compute_jeff_from_omega", "compute_jeff_series", "chirality_sign",
        "count_sign_flips", "estimate_chirality_commit_time", "jeff_radius_stats",
        "estimate_chirality_timescale",
    ),
    "observables.recursive_velocity": (
        "vrec_entropy", "vrec_geom_direction", "_wrap_angle_pi",
        "compute_recursive_velocity_geom", "compute_recursive_velocity",
    ),
    "observables.z_geometry": ("estimate_z_stabilization_time",),
    "offline.rsb_observables": (
        "compute_spectral_energy_series", "compute_dominant_band_series",
        "compute_spectral_entropy_series", "compute_rsb_observables",
    ),
    "offline.rsb_classification": ("classify_run",),
    "offline.rsb_analysis": (
        "analyze_rsb_history", "summarize_rsb_seed", "format_rsb_seed_summary",
    ),
}
OWNERS = {name: module for module, names in GROUPS.items() for name in names}

# Stage A: only these source contracts change; identity/defaults remain frozen.
REPAIR_COVERAGE = {
    "compute_recursive_velocity_geom": ("test_optional_omega_components",),
    "analyze_rsb_history": ("test_rsb_layouts", "test_seed_is_only_a_label"),
    "summarize_rsb_seed": ("test_optional_summary_series", "test_empty_wrapper_composes"),
    "format_rsb_seed_summary": ("test_incomplete_formatter",),
}


def _cases():
    """Small explicit histories; no model execution, random draws or source copies."""
    cases = {}

    def add(function, label, *args, **kwargs):
        cases[function + "/" + label] = (function, args, kwargs)

    omega = np.array([1., 1., 1j])
    for label, value in (("ordinary", omega), ("row", omega.reshape(1, 3)),
                         ("column", omega.reshape(3, 1)), ("bad_size", np.ones(4))):
        add("compute_jeff_from_omega", label, value)
    histories = {
        "preferred_alias": {"J_eff": np.array([.25, -.5]), "Omega": "unused"},
        "fallback_empty": {"J_eff": [], "Omega": np.array([omega, omega.conj()])},
        "fallback_none": {"J_eff": None, "Omega": np.array([omega])},
        "empty": {"Omega": np.empty((0, 3), dtype=complex)},
        "missing": {}, "none": None, "bad_shape": {"Omega": np.ones((2, 2))},
    }
    for label, hist in histories.items():
        add("compute_jeff_series", label, hist)
    for label, value in (("positive", 1.), ("negative", -1.), ("zero", 0.),
                         ("edge", 1e-9), ("nan", np.nan), ("inf", np.inf)):
        add("chirality_sign", label, value)
    add("chirality_sign", "custom_deadband", .01, deadband=.02)
    add("count_sign_flips", "flips", [1., 0., -1., np.nan, -2., 1.])
    add("count_sign_flips", "empty", [])
    for label, signal in {"stable": [0., -.3, .2, .9, 1.], "empty": [],
                          "zeros": [0., 0.], "nan": [1., np.nan],
                          "late_flip": [1., -.9, -1.]}.items():
        add("estimate_chirality_commit_time", label, signal)
    add("estimate_chirality_commit_time", "unreachable", [1., 2.], frac=2.)
    for label, signal in {"ordinary": [-2., 0., 1.], "empty": [], "nan": [np.nan, 1.]}.items():
        add("jeff_radius_stats", label, signal)
    for label, signal in {"growing": [0., .1, .4, .8, 1.], "falling": [1., .8, .4, .1, 0.],
                          "flat": [1., 1.], "empty": [], "nan": [0., np.nan]}.items():
        add("estimate_chirality_timescale", label, np.arange(len(signal), dtype=float), np.array(signal))

    for function in ("vrec_entropy", "compute_recursive_velocity"):
        for label, signal in {"empty": [], "one": [2.], "ordinary": [1., .2, .5],
                              "nan": [1., np.nan, 0.]}.items():
            add(function, label, signal)
    z = np.array([[1., 0., 0.], [0., 1., 0.], [0., 0., 0.], [np.nan, 0., 0.]])
    add("vrec_geom_direction", "undefined", {"Z_total": z, "Z_vec": np.ones_like(z)})
    add("vrec_geom_direction", "fallback", {"Z_vec": z[:2]}, z_key="missing")
    add("vrec_geom_direction", "floor", {"Z_total": z[:2]}, norm_floor=2.)
    for label, arr in (("empty", np.empty((0, 3))), ("one", np.ones((1, 3)))):
        add("vrec_geom_direction", label, {"Z_total": arr})
        add("compute_recursive_velocity_geom", label, {"Z_total": arr}, return_components=True)
    add("vrec_geom_direction", "missing", {})
    add("_wrap_angle_pi", "boundaries", np.array([-3*np.pi, -np.pi, 0., np.pi, 3*np.pi, np.nan, np.inf]))
    geom = {"Z_total": np.array([[0., 0., 0.], [3., 4., 0.], [3., 4., 2.]]),
            "Z_vec": np.ones((3, 3)), "Omega": np.array([omega, 1j*omega, -omega]),
            "phi_index": np.array([1, 1, 4]), "kappa": np.array([.1, .4, .2])}
    add("compute_recursive_velocity_geom", "components", geom, w_z=.5, w_phase=2.,
        w_corridor=1.5, w_kappa=.3, return_components=True)
    add("compute_recursive_velocity_geom", "default", geom)
    add("compute_recursive_velocity_geom", "fallback", {"Z_vec": geom["Z_total"]}, return_components=True)
    add("compute_recursive_velocity_geom", "none", None)
    add("compute_recursive_velocity_geom", "missing", {})
    add("compute_recursive_velocity_geom", "none_omega", {"Z_total": z[:2], "Omega": None})
    add("compute_recursive_velocity_geom", "mismatched", {**geom, "kappa": np.arange(5.)})

    aligned = np.tile([1., 0., 0.], (6, 1))
    z_hist = {"t": np.arange(6.), "Z_total": aligned, "Z_vec": -aligned}
    for label, hist in {
        "ordinary": z_hist, "fallback": {"t": np.arange(6.), "Z_vec": aligned},
        "undefined": {"t": np.arange(6.), "Z_total": np.zeros((6, 3))},
        "nan": {"t": np.arange(6.), "Z_total": np.full((6, 3), np.nan)},
        "short": {"t": np.arange(2.), "Z_total": aligned[:2]},
        "time_mismatch": {"t": np.arange(3.), "Z_total": aligned},
        "none": None, "missing_z": {"t": np.arange(6.)}, "missing_t": {},
    }.items():
        add("estimate_z_stabilization_time", label, hist, tail=5)

    psi = (np.arange(72).reshape(3, 3, 4, 2) / 32 + .125j).astype(complex)
    empty = np.empty((0, 3, 4, 2), dtype=complex)
    energy = np.array([[1., 1., 0.], [0., 2., 2.]])
    for label, value in (("ordinary", psi), ("empty", empty), ("bad_shape", np.ones((2, 2)))):
        add("compute_spectral_energy_series", label, value)
    for function in ("compute_dominant_band_series", "compute_spectral_entropy_series"):
        for label, value in (("ordinary_ties", energy), ("empty", np.empty((0, 3))),
                             ("bad_shape", np.ones(3)), ("zero_bands", np.empty((2, 0)))):
            add(function, label, value)
    add("compute_spectral_entropy_series", "zero_negative_nan", np.array([[0., 0.], [-1., 0.], [np.nan, 1.]]))
    add("compute_spectral_entropy_series", "one_band", np.ones((2, 1)))
    for label, value in (("ordinary", psi), ("empty", empty), ("one_helicity", psi[..., :1])):
        add("compute_rsb_observables", label, value)
    axes = dict(chan_axis=3, phase_axis=0, hel_axis=2)
    alternate = psi.transpose(2, 0, 3, 1)
    add("compute_rsb_observables", "axes_dark", alternate, dark_channels=(2,), **axes)
    add("compute_rsb_observables", "no_dark", psi, dark_channels=())
    add("compute_rsb_observables", "bad_axes", psi, chan_axis=2)
    add("compute_rsb_observables", "bad_dark", psi, dark_channels=(9,))
    add("compute_rsb_observables", "bad_shape", np.ones(3))
    for label, d, spread, hel in (
        ("collapse", [.5]*4, [.05]*4, [1.]*4),
        ("attractor", [.5]*4, [.5]*4, [.2]*4),
        ("oscillatory", [.1, 1., .1, 1.], [.5]*4, [0.]*4),
        ("helicity_oscillatory", [.5]*4, [.5]*4, [-1., 1., -1., 1.]),
        ("ambiguous", [.5]*4, [.95]*4, [1.]*4),
        ("undefined_h", [.5]*4, [.5]*4, [np.nan]*4),
        ("nan_spread", [.5]*4, [np.nan]*4, [0.]*4),
        ("empty", [], [], []),
    ):
        add("classify_run", label, d, spread, hel)
    add("classify_run", "custom", [.5]*4, [.5]*4, [0.]*4, sigma_coll=.6)
    add("analyze_rsb_history", "ordinary_verbose_seed", psi, seed=19)
    add("analyze_rsb_history", "quiet", psi, verbose=False)
    add("analyze_rsb_history", "empty", empty)
    add("analyze_rsb_history", "axes_existing_behavior", alternate, **axes)
    add("analyze_rsb_history", "classifier_options", psi, sigma_coll=100.)
    for label, tail_amp, transition in (
        ("meta_reversible", [1., 1., 1., 1.], 1),
        ("meta_attractor", [1., 1., 0., 0.], 1),
        ("meta_fast", [1., 0., 0., 0.], 1),
        ("meta_slow", [1., 0., 0., 0.], 3),
        ("meta_ambiguous", [1., .2, 0., 0.], 1),
    ):
        history = np.ones((6, 3, 4, 2), dtype=complex)
        history[transition:] = np.array(tail_amp)[None, None, :, None]
        add("analyze_rsb_history", label, history)
    add("analyze_rsb_history", "zero_signal", np.zeros((2, 3, 4, 2), dtype=complex))
    stats = {"label": "Class III_spec", "spectral_entropy_series": np.array([1., .6, .05]),
             "dom_band_series": np.array([2, 1, 2])}
    add("summarize_rsb_seed", "ordinary", stats, t=[0., .5, 1.], seed=7)
    add("summarize_rsb_seed", "defaults", stats)
    add("summarize_rsb_seed", "empty", {})
    add("summarize_rsb_seed", "nan_entropy", {**stats, "spectral_entropy_series": [1., np.nan]})
    add("summarize_rsb_seed", "nan_band_error", {**stats, "dom_band_series": [np.nan]})
    add("summarize_rsb_seed", "short_time_error", stats, t=[0.])
    add("summarize_rsb_seed", "none_series_error", {"spectral_entropy_series": None, "dom_band_series": None})
    add("format_rsb_seed_summary", "empty", {})
    add("format_rsb_seed_summary", "ordinary", {
        "regime": "Class III_spec", "seed": 7, "H0": 1., "HT": .05, "delta_H": .95,
        "t_collapse_10pct": 1., "m0_final": 2, "visited_bands": [1, 2], "n_band_switches": 2,
    })
    add("format_rsb_seed_summary", "incomplete_error", {"H0": 1., "HT": .5})
    return cases


def _encode(value):
    if isinstance(value, np.ndarray):
        return {"array": [value.dtype.str, list(value.shape), value.tobytes(order="C").hex()]}
    if isinstance(value, np.generic):
        return {"numpy_scalar": [value.dtype.str, value.tobytes().hex()]}
    if isinstance(value, dict):
        return {"dict": [[key, _encode(item)] for key, item in value.items()]}
    if isinstance(value, tuple):
        return {"tuple": [_encode(item) for item in value]}
    if isinstance(value, list):
        return [_encode(item) for item in value]
    if isinstance(value, float):
        return {"float": value.hex()}
    if isinstance(value, complex):
        return {"complex": [value.real.hex(), value.imag.hex()]}
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"Uncaptured value type: {type(value)}")


def _arrays(value, path=""):
    if isinstance(value, np.ndarray):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _arrays(item, path + "/" + str(key))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            yield from _arrays(item, path + "/" + str(index))


def _observe(module, case):
    name, args, kwargs = case
    before = _encode((args, kwargs))
    stdout, stderr = io.StringIO(), io.StringIO()
    result = None
    with warnings.catch_warnings(record=True) as caught, contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        warnings.simplefilter("always")
        try:
            result = getattr(module, name)(*args, **kwargs)
            outcome = {"return": _encode(result)}
        except Exception as exc:
            outcome = {"error": [type(exc).__module__ + "." + type(exc).__qualname__, str(exc)]}
    assert _encode((args, kwargs)) == before, name + " mutated its inputs"
    outcome["stdout"] = stdout.getvalue()
    outcome["stderr"] = stderr.getvalue()
    outcome["warnings"] = [[type(w.message).__module__ + "." + type(w.message).__qualname__, str(w.message)] for w in caught]
    outcome["input_aliases"] = [
        [rp, ap, result_array is arg_array, bool(np.shares_memory(result_array, arg_array))]
        for rp, result_array in _arrays(result) for ap, arg_array in _arrays((args, kwargs))
        if result_array is arg_array or np.shares_memory(result_array, arg_array)
    ]
    return outcome


def _environment():
    config = np.show_config(mode="dicts")
    dependencies = config.get("Build Dependencies", {})
    return {
        "system": platform.system(), "machine": platform.machine(), "python": sys.version,
        "numpy": np.__version__,
        "numeric_libraries": {key: {field: dependencies.get(key, {}).get(field)
                                    for field in ("name", "version", "openblas configuration")}
                              for key in ("blas", "lapack")},
        "simd": config.get("SIMD Extensions", {}),
    }


def _function_contract(function):
    node = ast.parse(textwrap.dedent(inspect.getsource(function))).body[0]
    return {"ast_sha256": hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest(),
            "signature": str(inspect.signature(function)),
            "defaults": _encode(function.__defaults__), "kwdefaults": _encode(function.__kwdefaults__)}


@pytest.fixture(scope="module")
def recorded():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_SHA256, "Do not regenerate the predecessor fixture"
    data = json.loads(raw)
    assert data["predecessor"] == PREDECESSOR
    assert set(data["functions"]) == set(OWNERS)
    assert set(data["cases"]) == set(_cases())
    return data


@pytest.fixture(scope="module")
def exact_environment(recorded):
    current = _environment()
    if current != recorded["environment"]:
        if current["system"] == "Windows":
            pytest.fail("Authoritative Windows environment changed: " + repr(current))
        pytest.skip("Exact P4A values require the recorded Windows/NumPy environment")


@pytest.mark.parametrize("case_id", list(_cases()))
def test_predecessor_results(case_id, recorded, exact_environment):
    definitions = importlib.import_module("torment_service.kernel.definitions")
    expected = copy.deepcopy(recorded["cases"][case_id])
    # The immutable fixture retains the five historical defects. Re-admit only
    # their corrected fields, using hand results or unaffected canonical cases.
    if case_id == "compute_recursive_velocity_geom/none_omega":
        del expected["error"]
        expected["return"] = _encode(np.array([np.sqrt(2.)]))
    elif case_id == "analyze_rsb_history/ordinary_verbose_seed":
        summary = dict(expected["return"]["dict"])["seed_summary"]["dict"]
        next(pair for pair in summary if pair[0] == "seed")[1] = 19
    elif case_id == "analyze_rsb_history/axes_existing_behavior":
        canonical = dict(recorded["cases"]["analyze_rsb_history/quiet"]["return"]["dict"])
        for pair in expected["return"]["dict"]:
            if pair[0] in {"E_t_m", "dom_band_series", "spectral_entropy_series", "seed_summary", "meta_label"}:
                pair[1] = canonical[pair[0]]
    elif case_id == "summarize_rsb_seed/none_series_error":
        del expected["error"]
        expected["return"] = recorded["cases"]["summarize_rsb_seed/empty"]["return"]
    elif case_id == "format_rsb_seed_summary/incomplete_error":
        del expected["error"]
        expected["return"] = (
            "RSB seed summary\n  regime: ?\n  H(0)    = 1.000\n  H(T)    = 0.500\n"
            "  ΔH      = 0.500\n  t_collapse_10pct: none (no 10% collapse)\n"
            "  m₀(T)   = None\n  visited bands = []\n  # band switches = 0"
        )
    assert _observe(definitions, _cases()[case_id]) == expected


@pytest.mark.parametrize("name", list(OWNERS))
def test_owner_identity_signature_and_admitted_source_contract(name, recorded):
    definitions = importlib.import_module("torment_service.kernel.definitions")
    module_name = "torment_service.kernel." + OWNERS[name]
    owner = importlib.import_module(module_name)
    function = getattr(owner, name)
    assert getattr(definitions, name) is function
    assert function.__module__ == module_name
    actual = _function_contract(function)
    expected = dict(recorded["functions"][name])
    if name in REPAIR_COVERAGE:
        coverage = ast.parse((ROOT / "tests/test_kernel_analysis_repairs.py").read_bytes())
        tests = {node.name for node in coverage.body if isinstance(node, ast.FunctionDef)}
        assert set(REPAIR_COVERAGE[name]) <= tests
        del actual["ast_sha256"], expected["ast_sha256"]
    assert actual == expected


@pytest.mark.parametrize("module", list(GROUPS))
def test_owner_has_only_assigned_functions_and_explicit_dependencies(module):
    path = ROOT / "torment_service/kernel" / (module.replace(".", "/") + ".py")
    tree = ast.parse(path.read_bytes())
    assert {node.name for node in tree.body if isinstance(node, ast.FunctionDef)} == set(GROUPS[module])
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert [(item.name, item.asname) for item in node.names] == [("numpy", "np")]
        elif isinstance(node, ast.ImportFrom):
            assert module == "offline.rsb_analysis"
            assert node.level == 1 and node.module in ("rsb_observables", "rsb_classification")


def test_compatibility_surface_and_constant(recorded):
    definitions = importlib.import_module("torment_service.kernel.definitions")
    chirality = importlib.import_module("torment_service.kernel.observables.chirality")
    assert definitions.EPS == chirality.EPS == 1e-12
    assert definitions.np is np
    assert "__all__" not in vars(definitions)
    scope = {}
    exec("from torment_service.kernel.definitions import *", scope)
    assert sorted(name for name in scope if name != "__builtins__") == recorded["wildcard"]
    assert "_wrap_angle_pi" not in scope
    tree = ast.parse(Path(definitions.__file__).read_bytes())
    assert not any(isinstance(node, (ast.FunctionDef, ast.ClassDef)) for node in ast.walk(tree))


def test_keep_separate_cognitive_input_contract():
    from torment_service.kernel.definitions import compute_jeff_from_omega
    from torment_service.kernel.model_core import ModelParams, ModelState
    from torment_service.cognitive_core import CognitiveCore, CognitiveCoreState
    row = np.array([[1., 1., 1j]])
    assert compute_jeff_from_omega(row) == 1.
    with pytest.raises(ValueError, match=r"not enough values to unpack \(expected 3, got 1\)"):
        CognitiveCore().update(CognitiveCoreState(), state=ModelState(Omega=row), params=ModelParams())


def _child(tmp_path, code):
    env = os.environ.copy()
    env.update(TORMENT_DATA_DIR=str(tmp_path / "data"), TORMENT_MCP_DATA_DIR=str(tmp_path / "mcp"),
               PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    prefix = f"""
import importlib
import importlib.abc
import sys
sys.path.insert(0, {str(ROOT)!r})
blocked = ('matplotlib', 'scipy', 'pandas', 'sklearn')
attempts = []
assert not any(name.split('.')[0] in blocked for name in sys.modules)
class BlockOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in blocked:
            attempts.append(fullname)
            raise ModuleNotFoundError(fullname, name=fullname)
sys.meta_path.insert(0, BlockOptional())
"""
    suffix = "\nassert not attempts\nassert not any(name.split('.')[0] in blocked for name in sys.modules)\n"
    result = subprocess.run([sys.executable, "-B", "-c", prefix + textwrap.dedent(code) + suffix],
                            cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8", timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("module", ["definitions", *GROUPS])
def test_fresh_owner_imports_and_calls_without_optional_libraries(tmp_path, module):
    _child(tmp_path, f"""
        owner = importlib.import_module('torment_service.kernel.{module}')
        import runpy
        helpers = runpy.run_path({str(Path(__file__).resolve())!r})
        seen = set()
        for case in helpers['_cases']().values():
            name = case[0]
            if name not in seen and hasattr(owner, name):
                outcome = helpers['_observe'](owner, case)
                assert 'error' not in outcome, (name, outcome)
                seen.add(name)
        assert seen
        if {module!r} != 'definitions':
            assert 'torment_service.kernel.definitions' not in sys.modules
        assert 'torment_service.kernel.rsb_model' not in sys.modules
        assert 'torment_service.memory_kernel' not in sys.modules
        assert 'torment_service.fabric' not in sys.modules
    """)


@pytest.mark.parametrize("package", ("observables", "offline"))
def test_package_markers_do_not_aggregate(tmp_path, package):
    _child(tmp_path, f"""
        importlib.import_module('torment_service.kernel.{package}')
        assert not any(name.startswith('torment_service.kernel.{package}.') for name in sys.modules)
        assert 'numpy' not in sys.modules
    """)


def test_live_runtime_does_not_load_new_owners(tmp_path):
    _child(tmp_path, """
        for name in ('kernel', 'kernel.model_core', 'memory_kernel', 'cognitive_core',
                     'checkpoint', 'memory_graph', 'fabric'):
            importlib.import_module('torment_service.' + name)
        for name in sys.modules:
            assert not name.startswith(('torment_service.kernel.observables', 'torment_service.kernel.offline'))
        assert 'torment_service.kernel.definitions' not in sys.modules
    """)
