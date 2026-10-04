"""P4B ownership and execution contracts captured from the working P4A checkpoint.

The compact fixture stores source contracts and hashes of exact numerical
results, not another source archive or collection of history arrays. Only
run_once's generated run_id/timestamp_utc metadata is excluded from comparison.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib
import importlib.metadata
import inspect
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import warnings

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "torment_service/kernel"
FIXTURE = ROOT / "tests/fixtures/kernel_offline_p4b.json"
FIXTURE_SHA256 = "87a5f982ef7060b93812c52a2ddfbcd7c8b8e1682b254c28a9907ddc29fd6a59"
PREDECESSOR = "967c129057ad6a5f3ea677a7cc01e5c6edfa2068"
OWNERS = {
    "diagnostics": "experiments",
    "physics_sampler": "samplers",
    "physics_sampler2": "cp_analysis",
    "tangent_corridor_analysis": "corridors",
}
FUNCTIONS = {
    "diagnostics": ("run_once", "run_ic_scan", "strong_delta_sector_histogram", "analyze_Jeff_coupling",
                    "run_corridor_spectroscopy_scan", "run_long_time_stability_test", "run_noise_robustness_test"),
    "physics_sampler": ("compute_flavor_probabilities", "compute_relative_phases", "compute_cp_like_invariant",
                        "sample_physics_observables", "summarize_observables", "plot_phase_and_cp_distributions"),
    "physics_sampler2": ("cp_conditioned_masks", "summarize_cp_conditioned_observables",
                         "detect_chirality_selection_window", "plot_flavor_time_series", "plot_Jeff_vs_time"),
    "tangent_corridor_analysis": ("detect_tangent_corridors", "cluster_delta_kz", "cp_split_big_delta_events"),
}
SCRIPT_PATHS = {
    "trajectories": ("torment_service/kernel/analyze_seed_trajectories.py",
                     "scripts/kernel_offline/analyze_seed_trajectories.py"),
    "health": ("torment_service/kernel/c.py", "scripts/kernel_offline/scan_health_summary.py"),
}
DRIVERS = {
    "run_once": ("run_once", {}),
    "ic": ("run_ic_scan", {"n_inits": 1}),
    "spectroscopy": ("run_corridor_spectroscopy_scan", {"n_inits": 1}),
    "long_short": ("run_long_time_stability_test", {"n_steps": 8}),
    "long_regular": ("run_long_time_stability_test", {"n_steps": 48}),
    "noise": ("run_noise_robustness_test", {"n_steps": 32}),
}
SCRIPT_CASES = {
    "trajectories": ("success", "missing", "headers_only", "missing_column"),
    "health": ("success", "no_vrec", "missing", "missing_flags"),
}


def _encode(value):
    if isinstance(value, np.ndarray):
        return ["array", value.dtype.str, list(value.shape), value.tobytes(order="C").hex()]
    if isinstance(value, np.generic):
        return ["numpy_scalar", value.dtype.str, value.tobytes().hex()]
    if isinstance(value, dict):
        return ["dict", [[key, _encode(item)] for key, item in value.items()]]
    if isinstance(value, tuple):
        return ["tuple", [_encode(item) for item in value]]
    if isinstance(value, list):
        return ["list", [_encode(item) for item in value]]
    if isinstance(value, float):
        return ["float", value.hex()]
    if isinstance(value, complex):
        return ["complex", value.real.hex(), value.imag.hex()]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(type(value))


def _digest(value):
    return hashlib.sha256(json.dumps(_encode(value), ensure_ascii=False).encode("utf-8")).hexdigest()


def _environment():
    config = np.show_config(mode="dicts")
    dependencies = config.get("Build Dependencies", {})
    return {
        "system": platform.system(), "machine": platform.machine(), "python": sys.version,
        "packages": {name: importlib.metadata.version(name) for name in ("numpy", "matplotlib", "scipy", "pandas")},
        "numeric_libraries": {name: {key: dependencies.get(name, {}).get(key)
                                     for key in ("name", "version", "openblas configuration")}
                              for name in ("blas", "lapack")},
        "simd": config.get("SIMD Extensions", {}),
    }


def _contract(function, *, restore_imports=False):
    raw = Path(function.__code__.co_filename).read_bytes()
    node = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == function.__name__)
    body = b"".join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
    if restore_imports:
        replacements = {
            "run_ic_scan": (b"from .samplers import sample_physics_observables",
                            b"from .physics_sampler import sample_physics_observables"),
            "run_noise_robustness_test": (b"from ..model_core import ModelState, TriOctaPhaseLockModel",
                                          b"from .model_core import ModelState, TriOctaPhaseLockModel"),
        }
        if function.__name__ in replacements:
            new, old = replacements[function.__name__]
            assert body.count(new) == 1
            body = body.replace(new, old)
    return {
        "source_sha256": hashlib.sha256(body).hexdigest(),
        "ast_sha256": hashlib.sha256(ast.dump(ast.parse(body), include_attributes=False).encode()).hexdigest(),
        "signature": str(inspect.signature(function)),
        "defaults": _encode(function.__defaults__), "kwdefaults": _encode(function.__kwdefaults__),
    }


def _environment_for_child(cwd):
    env = os.environ.copy()
    env.update(TORMENT_DATA_DIR=str(cwd / "data"), TORMENT_MCP_DATA_DIR=str(cwd / "mcp"),
               MPLBACKEND="Agg", MPLCONFIGDIR=str(cwd / "mpl"),
               PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    return env


def _capture_driver(case_id):
    """Real driver execution; only show() is replaced, and RNG is restored."""
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from unittest.mock import patch
    from torment_service.kernel import diagnostics
    from torment_service.kernel.model_core import ModelParams
    function, kwargs = DRIVERS[case_id]
    saved_rng = np.random.get_state()
    stdout = io.StringIO()
    result = {}
    try:
        np.random.seed(2718)
        with warnings.catch_warnings(record=True) as caught, contextlib.redirect_stdout(stdout), patch.object(plt, "show") as show:
            warnings.simplefilter("always")
            try:
                returned = getattr(diagnostics, function)(ModelParams(), **kwargs)
                if function == "run_once":
                    hist, *tail = returned
                    meta = hist["_meta"]
                    assert set(meta) == {"run_id", "timestamp_utc", "seed", "version"}
                    assert isinstance(meta["run_id"], str) and isinstance(meta["timestamp_utc"], str)
                    # These two generated identifiers are not computational outputs.
                    hist = {**hist, "_meta": {k: v for k, v in meta.items() if k not in ("run_id", "timestamp_utc")}}
                    returned = (hist, *tail)
                result["return_sha256"] = _digest(returned)
            except Exception as exc:
                result["error"] = [type(exc).__module__ + "." + type(exc).__qualname__, str(exc)]
            result["rng_sha256"] = _digest(np.random.get_state())
            result["show_calls"] = show.call_count
            result["png_sha256"] = []
            for number in plt.get_fignums():
                image = io.BytesIO()
                plt.figure(number).savefig(image, format="png")
                result["png_sha256"].append(hashlib.sha256(image.getvalue()).hexdigest())
            result["warnings"] = [[type(w.message).__name__, str(w.message)] for w in caught]
    finally:
        plt.close("all")
        np.random.set_state(saved_rng)
    assert _digest(np.random.get_state()) == _digest(saved_rng)
    result["stdout"] = stdout.getvalue()
    return result


def _driver_process(case_id, cwd):
    cwd.mkdir(parents=True, exist_ok=True)
    code = (
        f"import sys,runpy,json; sys.path.insert(0, {str(ROOT)!r}); "
        f"helpers=runpy.run_path({str(Path(__file__).resolve())!r}); "
        f"print(json.dumps(helpers['_capture_driver']({case_id!r})))"
    )
    result = subprocess.run([sys.executable, "-B", "-c", code], cwd=cwd,
                            env=_environment_for_child(cwd), capture_output=True, text=True, encoding="utf-8", timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr, result.stderr
    return json.loads(result.stdout)


def _script_process(script_path, kind, case, cwd):
    cwd.mkdir(parents=True, exist_ok=True)
    inputs = {}
    if kind == "trajectories":
        header = "lambda_phase,channel,traj_class\n"
        path = "outputs_patch39_unified/lambda_02/seed_trajectories_seed1.csv"
        if case == "success":
            inputs[path] = header + "0.2,vis,locked\n0.2,vis,locked\n0.2,vis,wandering\n0.2,vis,unknown\n0.2,dark,\n"
            inputs["outputs_patch39_unified/lambda_05/seed_trajectories_seed2.csv"] = header + "0.5,dark,locked\n0.5,dark,wandering\n"
        elif case == "headers_only":
            inputs[path] = header
        elif case == "missing_column":
            inputs[path] = "lambda_phase,channel\n0.2,vis\n"
    else:
        path = "outputs/wide_scan_triocta_ultra.csv"
        if case == "success":
            inputs[path] = "vrec_mean,has_nan,omega_blowup,kappa_runaway,z_runaway\n1,0,0,0,0\ninf,1,0,0,0\n,0,0,0,0\n2,0,0,0,1\n"
        elif case == "no_vrec":
            inputs[path] = "has_nan,omega_blowup,kappa_runaway,z_runaway\n0,0,0,0\n1,0,0,0\n"
        elif case == "missing_flags":
            inputs[path] = "vrec_mean\n1\n2\n"
    for name, content in inputs.items():
        destination = cwd / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content.encode("utf-8"))
    completed = subprocess.run([sys.executable, "-B", str(script_path)], cwd=cwd,
                               env=_environment_for_child(cwd), capture_output=True, text=True, encoding="utf-8", timeout=60)
    for name, content in inputs.items():
        assert (cwd / name).read_bytes() == content.encode("utf-8"), "Script changed its input"
    generated = {str(p.relative_to(cwd)).replace("\\", "/"): p.read_bytes().hex()
                 for p in sorted(cwd.rglob("*.csv")) if str(p.relative_to(cwd)).replace("\\", "/") not in inputs}
    # Traceback source paths move; retain the exception type/message and exit code.
    if completed.returncode:
        error = completed.stderr.strip().splitlines()[-1]
        assert "Error:" in error, completed.stderr
    else:
        assert not completed.stderr, completed.stderr
        error = None
    return {"exit_code": completed.returncode, "stdout": completed.stdout,
            "exception": error, "generated_csv_hex": generated}


@pytest.fixture(scope="module")
def recorded():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_SHA256, "Do not recapture from the candidate"
    data = json.loads(raw)
    assert data["predecessor"] == PREDECESSOR
    return data


@pytest.fixture(scope="module")
def exact_environment(recorded):
    for dependency in ("matplotlib", "scipy", "pandas"):
        pytest.importorskip(dependency, reason=f"Real P4B capability requires {dependency}")
    current = _environment()
    if current != recorded["environment"]:
        if current["system"] == "Windows":
            pytest.fail("Authoritative Windows environment changed: " + repr(current))
        pytest.skip("Exact P4B capture requires its recorded Windows/NumPy/plotting/CSV environment")


@pytest.mark.parametrize("old,name", [(module, name) for module, names in FUNCTIONS.items() for name in names])
def test_actual_owner_identity_and_source_contract(old, name, recorded):
    compatibility = importlib.import_module("torment_service.kernel." + old)
    owner_name = "torment_service.kernel.offline." + OWNERS[old]
    owner = importlib.import_module(owner_name)
    function = getattr(owner, name)
    assert getattr(compatibility, name) is function
    assert function.__module__ == owner_name
    assert _contract(function, restore_imports=True) == recorded["modules"][old]["functions"][name]


@pytest.mark.parametrize("old", list(OWNERS))
def test_complete_compatibility_surface(old, recorded):
    compatibility = importlib.import_module("torment_service.kernel." + old)
    owner = importlib.import_module("torment_service.kernel.offline." + OWNERS[old])
    names = [name for name in vars(compatibility) if not name.startswith("__")]
    assert names == recorded["modules"][old]["names"]
    assert "__all__" not in vars(compatibility)
    for name in names:
        assert getattr(compatibility, name) is getattr(owner, name)
    scope = {}
    exec(f"from torment_service.kernel.{old} import *", scope)
    assert [name for name in scope if name != "__builtins__"] == recorded["modules"][old]["wildcard"]
    tree = ast.parse(Path(compatibility.__file__).read_bytes())
    assert all(isinstance(node, ast.ImportFrom) or
               (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str))
               for node in tree.body)


@pytest.mark.parametrize("case_id", list(DRIVERS))
def test_real_experiment_driver_matches_predecessor(case_id, tmp_path, recorded, exact_environment):
    assert _driver_process(case_id, tmp_path) == recorded["drivers"][case_id]


@pytest.mark.parametrize("kind", list(SCRIPT_PATHS))
def test_script_payload_and_intentional_old_path_removal(kind, recorded):
    old, new = SCRIPT_PATHS[kind]
    assert not (ROOT / old).exists()
    assert hashlib.sha256((ROOT / new).read_bytes()).hexdigest() == recorded["script_sha256"][kind]
    raw = (ROOT / new).read_bytes()
    assert raw.count(b"\n") == raw.count(b"\r\n")
    assert importlib.util.find_spec("torment_service.kernel." + Path(old).stem) is None


@pytest.mark.parametrize("kind,case", [(kind, case) for kind, cases in SCRIPT_CASES.items() for case in cases])
def test_script_execution_matches_predecessor(kind, case, tmp_path, recorded, exact_environment):
    result = _script_process(ROOT / SCRIPT_PATHS[kind][1], kind, case, tmp_path)
    assert result == recorded["scripts"][kind + "/" + case]


def _blocked_child(tmp_path, code):
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
    result = subprocess.run([sys.executable, "-B", "-c", prefix + code + suffix], cwd=tmp_path,
                            env=_environment_for_child(tmp_path), capture_output=True, text=True, encoding="utf-8", timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("module", [*OWNERS, *("offline." + owner for owner in OWNERS.values())])
def test_old_and_new_imports_without_optional_dependencies(module, tmp_path):
    code = f"module = importlib.import_module('torment_service.kernel.{module}')\n"
    code += "import numpy as np\nassert module.np is np\n"
    if module.startswith("offline."):
        for old in [*OWNERS, "definitions"]:
            code += f"assert 'torment_service.kernel.{old}' not in sys.modules\n"
    code += "assert 'torment_service.kernel.rsb_model' not in sys.modules\n"
    _blocked_child(tmp_path, code)


def test_live_imports_do_not_load_offline_owners_or_scripts(tmp_path):
    _blocked_child(tmp_path, """
for name in ('kernel', 'kernel.model_core', 'memory_kernel', 'cognitive_core', 'checkpoint', 'memory_graph', 'fabric'):
    importlib.import_module('torment_service.' + name)
assert not any(name.startswith('torment_service.kernel.offline') for name in sys.modules)
for name in ('diagnostics', 'physics_sampler', 'physics_sampler2', 'tangent_corridor_analysis', 'analyze_seed_trajectories', 'c'):
    assert 'torment_service.kernel.' + name not in sys.modules
assert not any(name.startswith('scripts.kernel_offline') for name in sys.modules)
""")


@pytest.mark.parametrize("owner", list(OWNERS.values()))
def test_owner_uses_explicit_allowed_dependencies(owner):
    tree = ast.parse((KERNEL / "offline" / (owner + ".py")).read_bytes())
    allowed = {(1, "samplers"), (1, "cp_analysis"), (1, "corridors"),
               (2, "model_core"), (2, "cp_windows"), (2, "observables.chirality"),
               (0, "scipy.cluster.vq")}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert (node.level, node.module) in allowed
        elif isinstance(node, ast.Import):
            assert all(item.name in ("numpy", "matplotlib.pyplot") for item in node.names)
