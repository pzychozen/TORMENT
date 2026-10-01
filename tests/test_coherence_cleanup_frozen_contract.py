"""Phase 1B: independent frozen production expectations for coherence only.

No source hashes are acceptance conditions. Only the admitted inert fixture is
hash-pinned; baseline source identity is provenance. See the fixture README for
the safe, plugin-disabled invocation and the frozen numerical environment.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.abc
import inspect
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import warnings

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "torment_service" / "kernel"
FIXTURES = Path(__file__).parent / "fixtures" / "coherence_cleanup_phase1a"
FIXTURE_SHA256 = "fb64ddb6e41f390de5daac6eb2e3d1ede192f115a42a68920eb87ffb6fbbcead"
MANIFEST_SHA256 = "2442282d709dac838f879d0c3b1f5c076084549aaaa0733f220b4f1881ff136e"
BASELINE_COMMIT = "a06edcc5c9df5d3b56405085d9f2942b768dc203"
ENTRYPOINTS = (
    ("phase_triad_sync", "triad_coherence"),
    ("seed_emission", "triad_coherence_from_omega"),
)


def _read_cases():
    raw = (FIXTURES / "G_coherence_closure.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_SHA256, "immutable fixture changed"
    data = json.loads(raw)
    assert data["schema"] == "TORMENT_PHASE1A_EXACT_PRODUCTION_FIXTURES_v1"
    assert len(data["cases"]) == 55
    return data["cases"]


CASES = _read_cases()
BY_ID = {case["id"]: case for case in CASES}


def _cases(operation):
    return [case for case in CASES if case["operation"] == operation]


def _pack(value):
    """Encode actual observations in the original inert fixture vocabulary.

    This is a codec, not a scientific expected-value implementation. Keep bit
    strings, signed zero, scalar types and array layout rather than allclose.
    """
    if isinstance(value, np.ndarray):
        return {
            "type": "ndarray", "dtype": value.dtype.str,
            "shape": list(value.shape), "strides": list(value.strides),
            "writeable": bool(value.flags.writeable),
            "data": [_pack(x) for x in value.reshape(-1)],
            "bytes_c_order_hex": None if value.dtype.hasobject else value.tobytes(order="C").hex(),
        }
    if isinstance(value, np.generic):
        return {"type": type(value).__name__, "dtype": value.dtype.str, "value": _pack(value.item())}
    if type(value) is float:
        return {"type": "float", "hex": value.hex(), "bits_be": struct.pack(">d", value).hex()}
    if type(value) is complex:
        return {"type": "complex", "real": _pack(value.real), "imag": _pack(value.imag)}
    if type(value) in (int, bool, str) or value is None:
        return value
    if isinstance(value, dict):
        return {key: _pack(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return {"type": type(value).__name__, "items": [_pack(item) for item in value]}
    raise TypeError("unsupported fixture value: " + type(value).__name__)


def _input(spec):
    special = spec.get("special")
    if special == "none":
        return None
    if special == "ragged":
        return [[1, 2], [3]]
    if special == "bad_string":
        return ["x", "y", "z"]
    values = [complex(float.fromhex(real), float.fromhex(imag)) for real, imag in spec["omega"]]
    container = spec.get("container", "array")
    if container == "list":
        return values
    if container == "tuple":
        return tuple(values)
    if container == "scalar":
        return values[0]
    dtype = spec.get("dtype", "complex128")
    if dtype in ("float32", "float64", "int64", "bool"):
        values = [z.real for z in values]
    if dtype == "str":
        values = [str(z) for z in values]
    if spec.get("noncontiguous"):
        backing = np.zeros(2 * len(values), dtype=dtype)
        backing[::2] = values
        value = backing[::2]
    else:
        value = np.array(values, dtype=dtype)
    if "shape" in spec:
        value = value.reshape(spec["shape"])
    if spec.get("readonly"):
        value.flags.writeable = False
    return value


def _warning_records(records):
    return [{"type": type(w.message).__name__, "message": str(w.message)} for w in records]


def _outcome(call):
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        try:
            result = {"returned": _pack(call())}
        except BaseException as exc:
            # KeyboardInterrupt is an explicit frozen fallback characterization.
            result = {"exception": {"type": type(exc).__name__, "message": str(exc)}}
        result["warnings"] = _warning_records(observed)
    return result


def _observe(call):
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        result = call()
    return {"result": result, "warnings": _warning_records(observed)}


class _PureImportsOnly(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        forbidden = (
            "sqlite3", "_sqlite3", "sentence_transformers", "transformers",
            "openai", "ollama", "torch", "requests", "httpx",
            "trioctagon_historical_kernel", "kernel_physics", "kernel_TO",
        )
        if any(fullname == p or fullname.startswith(p + ".") for p in forbidden):
            raise AssertionError("out-of-scope dependency: " + fullname)
        if fullname.startswith("torment_service.") and not (
            fullname == "torment_service.kernel" or fullname.startswith("torment_service.kernel.")
        ):
            raise AssertionError("full service dependency is outside this test: " + fullname)
        return None


@pytest.fixture(scope="module")
def pure_modules():
    guard = _PureImportsOnly()
    sys.meta_path.insert(0, guard)
    try:
        with np.errstate(divide="warn", over="warn", under="ignore", invalid="warn"):
            modules = {
                name: importlib.import_module("torment_service.kernel." + name)
                for name, _ in ENTRYPOINTS
            }
            for name, module in modules.items():
                assert Path(module.__file__).resolve() == (KERNEL / (name + ".py")).resolve()
            yield modules
    finally:
        sys.meta_path.remove(guard)


def _direct_observation(case, function):
    def call():
        value = _input(case["inputs"])
        before = _pack(value)
        result = _outcome(lambda: function(value))
        after = _pack(value)
        return {"input_before": before, "outcome": result, "input_after": after, "input_unchanged": before == after}
    return _observe(call)


def _assert_direct(case, name, function):
    # Each entry point is checked against its own frozen record, never its peer.
    expected = case["expected"]
    assert _direct_observation(case, function) == {
        "result": expected["result"][name], "warnings": expected["warnings"],
    }, "frozen production mismatch: " + case["id"] + "/" + name


def _tree(relative):
    return ast.parse((ROOT / relative).read_text(encoding="utf-8-sig"))


def _memory_process():
    tree = _tree("torment_service/memory_kernel.py")
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TriOctaMemoryKernel")
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "process")


def _fallback_block():
    # Execute only the current debug slice, never import memory_kernel. Refuse
    # additional calls or imports rather than invoking an expanded dependency.
    blocks = [n for n in _memory_process().body if isinstance(n, ast.Try)
              and any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                      and x.func.id == "triad_coherence" for x in ast.walk(n))]
    assert len(blocks) == 1, "debug telemetry call must remain identifiable"
    block = blocks[0]
    assert [ast.unparse(n.func) for n in ast.walk(block) if isinstance(n, ast.Call)] == ["triad_coherence"]
    assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(block))
    return block


def _fallback_observation(case, function):
    block = _fallback_block()
    code = compile(ast.Module(body=[block], type_ignores=[]), "<current memory debug slice>", "exec")
    def call():
        spec = case["inputs"]
        state = SimpleNamespace(Omega=_input(spec))
        before = _pack(state.Omega)
        callback = function
        if spec.get("raise"):
            error_type = {"RuntimeError": RuntimeError, "ValueError": ValueError,
                          "TypeError": TypeError, "KeyboardInterrupt": KeyboardInterrupt}[spec["raise"]]
            def callback(_):
                raise error_type("PHASE1A_SENTINEL")
        namespace = {"state": state, "triad_coherence": callback}
        def execute():
            exec(code, namespace)
            return {key: namespace[key] for key in ("S_mag", "Phi_coll", "S")}
        return {"outcome": _outcome(execute), "input_unchanged": before == _pack(state.Omega)}
    return _observe(call)


def _emission_observation(case, module):
    def call():
        spec = case["inputs"]
        state = SimpleNamespace(Omega=_input(spec), phi_index=spec.get("q", 0))
        before = _pack(state.Omega)
        gate = module.GapGate(**spec["gate"])
        return {
            "outcome": _outcome(lambda: module.check_emission(state, gate)),
            "input_unchanged": before == _pack(state.Omega), "q_after": state.phi_index,
        }
    return _observe(call)


def test_immutable_fixture_and_provenance():
    _read_cases()
    provenance = json.loads((FIXTURES / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["production_baseline_commit"] == BASELINE_COMMIT
    assert provenance["external_phase1a_manifest_sha256"] == MANIFEST_SHA256
    assert provenance["fixture_sha256"] == FIXTURE_SHA256
    assert provenance["fixture_case_count"] == 55
    assert provenance["expected_output_policy"] == "IMMUTABLE_PRODUCTION_BEFORE_VALUES"
    assert provenance["source_identity_policy"] == "PROVENANCE_ONLY_NOT_TEST_CONDITION"
    assert len(BY_ID) == 55
    assert {c["operation"] for c in CASES} == {"coherence", "fallback", "emission", "entrypoints"}


@pytest.mark.parametrize("case", _cases("coherence"), ids=lambda c: c["id"])
@pytest.mark.parametrize("module_name,function_name", ENTRYPOINTS)
def test_each_entrypoint_against_immutable_production(case, module_name, function_name, pure_modules):
    _assert_direct(case, module_name + "." + function_name, getattr(pure_modules[module_name], function_name))


@pytest.mark.parametrize("case", _cases("fallback"), ids=lambda c: c["id"])
def test_current_memory_debug_fallback_against_frozen_behavior(case, pure_modules):
    expected = case["expected"]
    # Capture path, line numbers and AST hash are provenance, not behavior. Do
    # not enforce baseline source hashes or source layout on a future refactor.
    behavior = {key: value for key, value in expected["result"].items() if key != "exact_source_slice"}
    assert _fallback_observation(case, pure_modules["phase_triad_sync"].triad_coherence) == {
        "result": behavior, "warnings": expected["warnings"],
    }


@pytest.mark.parametrize("case", _cases("emission"), ids=lambda c: c["id"])
def test_seed_emission_consumer_against_frozen_behavior(case, pure_modules):
    assert _emission_observation(case, pure_modules["seed_emission"]) == case["expected"]


def test_both_public_signatures_remain_supported(pure_modules):
    expected = BY_ID["G_entrypoints"]["expected"]["result"]
    for (module_name, function_name), prefix in zip(ENTRYPOINTS, ("phase", "seed")):
        function = getattr(pure_modules[module_name], function_name)
        assert callable(function) is expected[prefix + "_callable"]
        assert str(inspect.signature(function)) == expected[prefix + "_signature"]
        assert pure_modules[module_name].__name__ == "torment_service.kernel." + module_name


def _has_import(tree, module, name, level=0):
    return any(isinstance(n, ast.ImportFrom) and n.module == module and n.level == level
               and any(alias.name == name and alias.asname in (None, name) for alias in n.names)
               for n in ast.walk(tree))


def test_known_consumer_import_surfaces_and_phase_operator_boundary(pure_modules):
    memory = _tree("torment_service/memory_kernel.py")
    assert _has_import(memory, "kernel.phase_triad_sync", "triad_coherence", level=1)
    block = _fallback_block()
    call = next(n for n in ast.walk(block) if isinstance(n, ast.Call))
    assert len(call.args) == 1 and ast.unparse(call.args[0]) == "state.Omega"
    # Verify the values reach the existing debug dictionary, without executing
    # mechanics, summarization, embeddings, or the complete memory method.
    debug_dicts = [n for n in ast.walk(_memory_process()) if isinstance(n, ast.Dict)]
    debug_entries = {(key.value, ast.unparse(value)) for node in debug_dicts
                     for key, value in zip(node.keys, node.values) if isinstance(key, ast.Constant)}
    assert ("S_mag", "float(S_mag)") in debug_entries
    assert ("phi_coll", "float(Phi_coll)") in debug_entries
    seed = _tree("torment_service/kernel/seed_emission.py")
    check = next(n for n in seed.body if isinstance(n, ast.FunctionDef) and n.name == "check_emission")
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "triad_coherence_from_omega" for n in ast.walk(check))
    oracle = _tree("tests/oracles/model_core_v4_0_original.py")
    assert _has_import(oracle, "phase_triad_sync", "triad_coherence")
    assert _has_import(oracle, "phase_triad_sync", "apply_phase_triad_sync")
    model = _tree("torment_service/kernel/model_core.py")
    assert _has_import(model, "phase_triad_sync", "apply_phase_triad_sync", level=1)
    phase = pure_modules["phase_triad_sync"]
    assert callable(phase.apply_phase_triad_sync)
    assert phase.apply_phase_triad_sync is not phase.triad_coherence


def test_oracle_bare_import_compatibility(monkeypatch, pure_modules):
    # Execute the existing import statement only, not the oracle's model code.
    tree = _tree("tests/oracles/model_core_v4_0_original.py")
    statement = next(n for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == "phase_triad_sync")
    monkeypatch.syspath_prepend(str(KERNEL))
    namespace = {}
    exec(compile(ast.Module(body=[statement], type_ignores=[]), "<oracle bare import>", "exec"), namespace)
    bare = sys.modules["phase_triad_sync"]
    assert Path(bare.__file__).resolve() == (KERNEL / "phase_triad_sync.py").resolve()
    assert namespace["triad_coherence"] is bare.triad_coherence
    assert namespace["apply_phase_triad_sync"] is bare.apply_phase_triad_sync
    assert str(inspect.signature(bare.triad_coherence)) == BY_ID["G_entrypoints"]["expected"]["result"]["phase_signature"]
    _assert_direct(BY_ID["G_complex128"], "phase_triad_sync.triad_coherence", bare.triad_coherence)


def test_zero_coherence_is_one_not_caught_exception_telemetry(pure_modules):
    for module_name, function_name in ENTRYPOINTS:
        function = getattr(pure_modules[module_name], function_name)
        _assert_direct(BY_ID["G_zero"], module_name + "." + function_name, function)
        assert function(np.zeros(3, dtype=np.complex128))[0] == 1.0
    case = BY_ID["G_fallback_RuntimeError"]
    actual = _fallback_observation(case, pure_modules["phase_triad_sync"].triad_coherence)
    telemetry = actual["result"]["outcome"]["returned"]
    assert {key: value["hex"] for key, value in telemetry.items()} == {
        "S_mag": "0x0.0p+0", "Phi_coll": "0x0.0p+0", "S": "0x0.0p+0",
    }


def test_negative_control_both_wrong_helpers_are_rejected(monkeypatch, pure_modules):
    case = BY_ID["G_complex128"]
    def wrong(_):
        return 0.0, 0.0, np.complex128(0j)
    with monkeypatch.context() as patch:
        for module_name, function_name in ENTRYPOINTS:
            patch.setattr(pure_modules[module_name], function_name, wrong)
        left = _direct_observation(case, pure_modules["phase_triad_sync"].triad_coherence)
        right = _direct_observation(case, pure_modules["seed_emission"].triad_coherence_from_omega)
        assert left == right  # Mutual agreement is deliberately insufficient.
        for module_name, function_name in ENTRYPOINTS:
            with pytest.raises(AssertionError, match="frozen production mismatch"):
                _assert_direct(case, module_name + "." + function_name, getattr(pure_modules[module_name], function_name))
    for module_name, function_name in ENTRYPOINTS:
        _assert_direct(case, module_name + "." + function_name, getattr(pure_modules[module_name], function_name))
