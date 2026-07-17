"""Focused tests for the exact N=64 homometric falsifier (fixture v0.1 + runner v0.1).

Offline; no torment_service. Categories 1/3/4/5, the GENERIC (all-zero/all-one) C=1 descriptor checks, the
evaluation-gate/environment/invalid-payload/emission tests, and the AST boundary scan are safe to execute:
none passes member A or member B through the descriptor. The FIXTURE-SPECIFIC A/B ΨTRS test is gated behind
the N64_EVALUATION_AUTHORIZED == "1" flag and is skipped unless a separate evaluation authorization sets it;
it is NOT executed during the implementation phase.
"""
import ast
import json
import math
import os
import sys

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.realpath(__file__))
_BV_DIR = os.path.realpath(os.path.join(_HERE, "..", "..", "research", "brainvision"))
if _BV_DIR not in sys.path:
    sys.path.insert(0, _BV_DIR)

import n64_falsifier_fixture_v0_1 as fx  # noqa: E402
import psi_trs  # noqa: E402
import run_n64_falsifier_v0_1 as runner  # noqa: E402

N = 64
_EVAL_AUTHORIZED = os.environ.get("N64_EVALUATION_AUTHORIZED") == "1"
_candidate_gate = pytest.mark.skipif(
    not _EVAL_AUTHORIZED, reason="N64 candidate A/B evaluation through ΨTRS is not authorized in this phase")

ACCEPTED_A = [0, 1, 3, 4, 5, 7, 12, 13, 15]
ACCEPTED_B = [0, 1, 3, 52, 53, 55, 60, 61, 63]
TOP_LEVEL_OBJECTS = {"schema", "authority", "source", "environment", "configuration", "fixture",
                     "feature_schema", "results", "controls", "validity", "replay"}


# ------- local INDEPENDENT recomputation helpers (must not call the fixture module) -------

def _support_from_uv(low, high):
    return sorted({(a + b) % N for a in low for b in high})


def _autocorr(support):
    ss = set(support)
    return [sum(1 for t in range(N) if t in ss and (t + k) % N in ss) for k in range(N)]


def _one_step(support):
    ss = set(support)
    w = len(support)
    c11 = sum(1 for t in range(N) if t in ss and (t + 1) % N in ss)
    return {"c00": N - 2 * w + c11, "c01": w - c11, "c10": w - c11, "c11": c11}


def _triple(support, k, l):
    ss = set(support)
    return sum(1 for t in range(N) if t in ss and (t + k) % N in ss and (t + l) % N in ss)


def _triple_full(support):
    return [[_triple(support, k, l) for l in range(N)] for k in range(N)]


def _disagreements(ta, tb):
    return sum(1 for k in range(N) for l in range(N) if ta[k][l] != tb[k][l])


def _histogram(ta):
    hist = {}
    for row in ta:
        for v in row:
            hist[str(v)] = hist.get(str(v), 0) + 1
    return hist


def _no_none(obj):
    if obj is None:
        return False
    if isinstance(obj, dict):
        return all(_no_none(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return all(_no_none(v) for v in obj)
    return True


# ============================ Category 1: fixture / certificate ============================

def test_literal_supports_and_uv_reconstruction():
    assert _support_from_uv((0, 1, 3), (0, 4, 12)) == ACCEPTED_A
    assert _support_from_uv((0, 1, 3), tuple((-b) % N for b in (0, 4, 12))) == ACCEPTED_B
    fixture = fx.build_fixture()
    assert fixture["member_A_support"] == ACCEPTED_A
    assert fixture["member_B_support"] == ACCEPTED_B


def test_collision_free_unique_sums():
    a_sums = [(u + v) % N for u in (0, 1, 3) for v in (0, 4, 12)]
    b_sums = [(u + v) % N for u in (0, 1, 3) for v in tuple((-b) % N for b in (0, 4, 12))]
    assert len(set(a_sums)) == len(a_sums) == 9
    assert len(set(b_sums)) == len(b_sums) == 9


def test_encoding_shape_and_binary():
    for support in (ACCEPTED_A, ACCEPTED_B):
        field = fx.encode(support)
        assert field.shape == (N, 1)
        assert np.all(np.isfinite(field))
        assert set(np.unique(field).tolist()).issubset({0.0, 1.0})
        assert int(field.sum()) == 9


def test_lower_order_certificates_independent():
    fixture = fx.build_fixture()
    assert fixture["lower_order"]["weight_A"] == 9 and fixture["lower_order"]["weight_B"] == 9
    assert fixture["lower_order"]["periodic_autocorrelation_A"] == _autocorr(ACCEPTED_A)
    assert fixture["lower_order"]["periodic_autocorrelation_B"] == _autocorr(ACCEPTED_B)
    assert _autocorr(ACCEPTED_A) == _autocorr(ACCEPTED_B)
    assert fixture["lower_order"]["directed_one_step_table_A"] == _one_step(ACCEPTED_A)
    assert _one_step(ACCEPTED_A) == {"c00": 50, "c01": 5, "c10": 5, "c11": 4}
    assert fixture["lower_order"]["absolute_transition_magnitude_multiset_A"] == {"0": 54, "1": 10}
    assert fixture["lower_order"]["lower_order_match"] is True


def test_higher_order_certificates_independent():
    fixture = fx.build_fixture()
    ta, tb = _triple_full(ACCEPTED_A), _triple_full(ACCEPTED_B)
    assert _triple(ACCEPTED_A, 4, 12) == 3 and _triple(ACCEPTED_B, 4, 12) == 0
    assert fixture["higher_order"]["fixed_lag_value_A"] == 3
    assert fixture["higher_order"]["fixed_lag_value_B"] == 0
    assert _disagreements(ta, tb) == 264
    assert fixture["higher_order"]["ordered_disagreement_count"] == 264
    assert _histogram(ta) == _histogram(tb)
    assert fixture["higher_order"]["unlabeled_histogram_match"] is True


def test_provenance_inequivalence():
    fixture = fx.build_fixture()
    for value in fixture["provenance"].values():
        assert value is False


def test_deterministic_fixture_hash():
    a = fx.build_fixture()
    b = fx.build_fixture()
    assert a["fixture_sha256"] == b["fixture_sha256"] and a == b


# ============================ Category 2: descriptor (generic C=1 executes; A/B gated) ============

def test_generic_all_zero_all_one_c1():
    for field in (np.zeros((N, 1), dtype=float), np.ones((N, 1), dtype=float)):
        for variant in runner.DESCRIPTOR_VARIANTS:
            vector = runner.features(field, variant)
            assert vector.shape == (11,) and np.all(np.isfinite(vector))
    v0 = runner.features(np.zeros((N, 1), dtype=float), "psi_trs_k0")
    assert v0[3] == 0.0 and v0[4] == 0.0 and v0[5] == 0.0


def test_generic_deterministic_repeated_calls():
    field = np.ones((N, 1), dtype=float)
    assert np.array_equal(runner.features(field, "psi_trs"), runner.features(field, "psi_trs"))


def test_feature_schema_shape_and_order():
    assert len(runner.FEATURE_SCHEMA) == 11
    assert [e["index"] for e in runner.FEATURE_SCHEMA] == list(range(11))
    assert runner.FEATURE_SCHEMA[0]["name"] == "rho_mean"
    assert runner.FEATURE_SCHEMA[10]["name"] == "ch0_rfft_mag_std"
    for entry in runner.FEATURE_SCHEMA:
        assert entry["descriptor_variants"] == ["psi_trs", "psi_trs_k0"]


@_candidate_gate
def test_candidate_ab_self_pair_exact_zero():  # gated: passes A/B through ΨTRS
    fixture = fx.build_fixture()
    for support in (fixture["member_A_support"], fixture["member_B_support"]):
        for variant in runner.DESCRIPTOR_VARIANTS:
            for s in range(N):
                f = runner.features(runner.rotate(fx.encode(support), s), variant)
                assert runner.symmetric_response(f, f)["distance"] == 0.0


# ============================ Evaluation gate (correction 1) ============================

def test_evaluation_gate_predicate_only_one_authorizes():
    assert runner._evaluation_authorized("1") is True
    for value in (None, "", "0", "true", "True", "yes", "2", "01", " 1", "1 "):
        assert runner._evaluation_authorized(value) is False


def test_build_payload_gated_when_unset(monkeypatch):
    monkeypatch.delenv(runner.EVALUATION_AUTHORIZATION_ENV, raising=False)
    with pytest.raises(runner.EvaluationNotAuthorizedError):
        runner.build_payload()


def test_gate_blocks_descriptor_call(monkeypatch):
    monkeypatch.delenv(runner.EVALUATION_AUTHORIZATION_ENV, raising=False)
    calls = []

    def _stub(field, kappa=0.5, **kwargs):
        calls.append(kappa)
        return np.zeros(11, dtype=float)

    monkeypatch.setattr(psi_trs, "psi_trs_features", _stub)
    with pytest.raises(runner.EvaluationNotAuthorizedError):
        runner.build_payload()
    assert calls == []  # descriptor never reached


def test_main_emits_no_stdout_when_unauthorized(monkeypatch, capsys):
    monkeypatch.delenv(runner.EVALUATION_AUTHORIZATION_ENV, raising=False)
    with pytest.raises(runner.EvaluationNotAuthorizedError):
        runner._main([])
    captured = capsys.readouterr()
    assert captured.out == ""


# ============================ Environment capture (correction 2) ============================

def test_env_capture_print_none_normalized(monkeypatch, capsys):
    monkeypatch.setattr(np, "n64_fake_print_none", lambda: print("alpha\r\nbeta  \tgamma  "), raising=False)
    method, status, digest = runner._tagged_numpy_capture("n64_fake_print_none")
    assert method == "stdout_text" and status == "ok" and len(digest) == 64
    assert capsys.readouterr().out == ""  # no stdout leak


def test_env_capture_structured_no_print(monkeypatch):
    monkeypatch.setattr(np, "n64_fake_structured", lambda: {"blas": "openblas", "n": 1}, raising=False)
    method, status, digest = runner._tagged_numpy_capture("n64_fake_structured")
    assert method == "structured" and status == "ok" and len(digest) == 64


def test_env_capture_print_and_structured_prefers_structured(monkeypatch, capsys):
    def _api():
        print("noise")
        return {"x": 1}
    monkeypatch.setattr(np, "n64_fake_both", _api, raising=False)
    method, status, _ = runner._tagged_numpy_capture("n64_fake_both")
    assert method == "structured" and status == "ok"
    assert capsys.readouterr().out == ""


def test_env_capture_exception_sentinel(monkeypatch):
    def _api():
        raise ValueError("boom")
    monkeypatch.setattr(np, "n64_fake_raise", _api, raising=False)
    method, status, digest = runner._tagged_numpy_capture("n64_fake_raise")
    assert method == "unavailable" and status == "unavailable_call_failed" and len(digest) == 64


def test_env_capture_absent_sentinel():
    method, status, digest = runner._tagged_numpy_capture("definitely_not_a_numpy_api")
    assert method == "unavailable" and status == "unavailable_api_absent" and len(digest) == 64


def test_env_capture_deterministic_hash():
    a = runner.capture_environment()
    b = runner.capture_environment()
    assert runner.canonical_sequence_sha256(a) == runner.canonical_sequence_sha256(b)


def test_capture_environment_no_stdout_leak(capsys):
    runner.capture_environment()
    assert capsys.readouterr().out == ""


# ============================ Input validation (corrections 3) ============================

def test_input_validation_rejections():
    good = np.zeros((N, 1), dtype=float)
    good[0, 0] = 1.0
    runner.validate_input(good)
    for bad in (
        np.zeros((N,), dtype=float), np.zeros((32, 1), dtype=float), np.zeros((N, 2), dtype=float),
        np.zeros((N, 1), dtype=bool), np.full((N, 1), 2, dtype=int), np.array([["0"]] * N),
        np.full((N, 1), np.nan, dtype=float), np.zeros((N, 1), dtype=complex),
    ):
        with pytest.raises(runner.ValidationError):
            runner.validate_input(bad)


def test_input_validation_python_booleans_rejected():
    nested = [[False]] + [[True]] * (N - 1)          # nested Python booleans
    mixed = [[0]] + [[False]] + [[1]] * (N - 2)      # mixed int / bool
    tuple_bool = tuple((bool(i % 2),) for i in range(N))
    object_bool = np.array([[True]] + [[False]] * (N - 1), dtype=object)
    for bad in (nested, mixed, tuple_bool, object_bool):
        with pytest.raises(runner.ValidationError) as info:
            runner.validate_input(bad)
        assert info.value.code == "invalid_input_boolean"


def test_input_validation_numeric_string_rejected():
    with pytest.raises(runner.ValidationError) as info:
        runner.validate_input([["0"]] * N)
    assert info.value.code == "invalid_input_dtype"


def test_input_validation_accepts_int_and_float():
    int_field = [[1 if i in ACCEPTED_A else 0] for i in range(N)]
    float_field = [[1.0 if i in ACCEPTED_B else 0.0] for i in range(N)]
    assert runner.validate_input(int_field).dtype == np.float64
    assert runner.validate_input(float_field).dtype == np.float64
    assert runner.validate_input(np.array(int_field, dtype=np.int64)).shape == (N, 1)


def test_validation_error_codes():
    cases = {
        "invalid_input_shape": np.zeros((N,), dtype=float),
        "invalid_input_dtype": np.zeros((N, 1), dtype=complex),
        "invalid_input_nonfinite": np.full((N, 1), np.inf, dtype=float),
        "invalid_input_nonbinary": np.full((N, 1), 3, dtype=int),
    }
    for code, bad in cases.items():
        with pytest.raises(runner.ValidationError) as info:
            runner.validate_input(bad)
        assert info.value.code == code


# ============================ Invalid canonical payload (correction 4) ============================

@pytest.mark.parametrize("code", [
    "invalid_input_shape", "invalid_input_dtype", "invalid_input_boolean",
    "invalid_input_nonfinite", "invalid_input_nonbinary",
])
def test_invalid_payload_deterministic_and_finite(code):
    payload = runner.build_invalid_payload([code])
    assert set(payload.keys()) == TOP_LEVEL_OBJECTS
    assert payload["validity"]["overall_valid"] is False
    assert payload["validity"]["error_codes"] == [code]
    assert payload["results"] == {"members": {}, "pair": {}, "kappa_differences": {}}
    assert _no_none(payload)
    wrapper = runner.build_wrapper(payload)
    text = runner.canonical_text(wrapper)
    assert "NaN" not in text and "Infinity" not in text and ":null" not in text
    assert runner.canonical_sequence_sha256(payload) == wrapper["payload_sha256"]


def test_invalid_payload_sorted_unique_codes():
    payload = runner.build_invalid_payload(["invalid_input_shape", "invalid_input_shape",
                                            "invalid_input_dtype"])
    assert payload["validity"]["error_codes"] == ["invalid_input_dtype", "invalid_input_shape"]


# ============================ Metric / validity (category 3) ============================

def test_symmetric_identical_vector_exact_zero_and_symmetry():
    f = np.array([1.0, 2.0, -3.0, 0.5, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    assert runner.symmetric_response(f, f)["distance"] == 0.0
    g = f + 1.0
    assert runner.symmetric_response(f, g)["distance"] == runner.symmetric_response(g, f)["distance"]


def test_directional_role_exchange_and_denominators():
    f = np.array([1.0] + [0.0] * 10)
    g = np.array([0.0, 2.0] + [0.0] * 9)
    ab = runner.directional_response(f, g, "member_A_to_member_B")
    ba = runner.directional_response(g, f, "member_B_to_member_A")
    assert ab["numerator"] == ba["numerator"]
    assert ab["raw_denominator"] != ba["raw_denominator"]
    assert ab["effective_denominator"] == max(ab["raw_denominator"], runner.EPSILON)


def test_epsilon_and_conditional_bound():
    zero = np.zeros(11)
    resp = runner.symmetric_response(zero, zero)
    assert resp["joint_epsilon_hit"] is True and resp["distance"] == 0.0
    f = np.array([3.0] + [0.0] * 10)
    g = np.array([-3.0] + [0.0] * 10)
    assert 0.0 <= runner.symmetric_response(f, g)["distance"] <= 2.0


def test_aggregate_population_std_and_sorted_ties():
    agg = runner.aggregate([1.0, 1.0, 3.0, 3.0])
    assert agg["count"] == 4 and agg["argmin_starts"] == [0, 1] and agg["argmax_starts"] == [2, 3]
    assert abs(agg["population_standard_deviation"] - float(np.std([1, 1, 3, 3], ddof=0))) < 1e-12


def test_canonicalize_rejects_nonfinite():
    with pytest.raises(runner.NonFiniteError):
        runner.canonical_bytes({"x": float("nan")})
    with pytest.raises(runner.NonFiniteError):
        runner.canonical_bytes({"x": float("inf")})


# ============================ Rotation / controls (category 4) ============================

def test_rotation_convention_and_s0_identity():
    x = np.arange(N, dtype=float).reshape(N, 1)
    assert np.array_equal(runner.rotate(x, 0), x)
    for s in (1, 5, 63):
        rotated = runner.rotate(x, s)
        assert all(rotated[t, 0] == x[(t + s) % N, 0] for t in range(N))


def test_placement_tie_aware_over_63():
    ref = [0.0] * 30 + [1.0] * 33
    p = runner.placement(0.5, ref)
    assert p["reference_count"] == 63 and p["lower_count"] == 30 and p["higher_count"] == 33
    p_tie = runner.placement(1.0, ref)
    assert p_tie["equal_count"] == 33
    assert p_tie["midrank_fraction"] == (30 + 0.5 * 33) / 63


# ============================ Schema / serialization / hashing / emission / boundary (category 5) ======

def test_canonical_negative_zero_normalization_and_compactness():
    assert runner.canonical_bytes({"a": -0.0}) == b'{"a":0.0}'
    assert runner.canonical_bytes({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def test_canonical_insertion_order_independence():
    one = {"z": 1, "a": {"y": 2, "x": 3}}
    two = {"a": {"x": 3, "y": 2}, "z": 1}
    assert runner.canonical_bytes(one) == runner.canonical_bytes(two)


def test_wrapper_payload_hash_reconstruction():
    payload = {"k": [1, 2, 3], "f": 0.5}
    wrapper = runner.build_wrapper(payload)
    assert "payload_sha256" not in wrapper["payload"]
    assert runner.canonical_sequence_sha256(wrapper["payload"]) == wrapper["payload_sha256"]
    parsed = json.loads(runner.canonical_text(wrapper))
    assert runner.canonical_sequence_sha256(parsed["payload"]) == parsed["payload_sha256"]


def test_sequence_hash_matches_fixture_module():
    seq = [[1, 2], [3, 4]]
    assert runner.canonical_sequence_sha256(seq) == fx.canonical_sequence_sha256(seq)


def test_emit_stdout_only_no_trailing_newline(capsys):
    wrapper = {"payload": {"a": 1, "b": [1, 2]}, "payload_sha256": "deadbeef"}
    runner.emit(wrapper)
    out = capsys.readouterr().out
    assert out == runner.canonical_text(wrapper)
    assert not out.endswith("\n")
    assert json.loads(out) == {"payload": {"a": 1, "b": [1, 2]}, "payload_sha256": "deadbeef"}


def test_emit_stderr_does_not_alter_canonical_bytes(capsys):
    wrapper = {"payload": {"a": 1}, "payload_sha256": "x"}
    sys.stderr.write("diagnostic noise\n")
    runner.emit(wrapper)
    captured = capsys.readouterr()
    assert captured.out == runner.canonical_text(wrapper)
    assert "diagnostic noise" in captured.err


def test_input_validation_valid_int_float_and_string_rejected_dtype():
    # extra guard: numeric string dtype and valid numeric leaves
    assert runner.validate_input(np.array([[0.0]] * N)).shape == (N, 1)


def _dotted(func):
    parts = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
    parts.reverse()
    if len(parts) >= 2:
        return (".".join(parts[:-1]), parts[-1])
    return tuple(parts)


def _scan_forbidden(path):
    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    protected = ("torment_service", "torment_service/kernel", "torment_service/memory_kernel",
                 "torment_service/fabric")
    loaders = {("importlib", "import_module"), ("importlib.util", "spec_from_file_location"),
               ("importlib.machinery", "SourceFileLoader"), ("runpy", "run_module"), ("runpy", "run_path")}
    subproc = {("subprocess", "run"), ("subprocess", "call"), ("subprocess", "check_call"),
               ("subprocess", "check_output"), ("subprocess", "Popen"), ("os", "system"), ("os", "popen")}
    violations = []

    def _refs_protected(node):
        for sub in ast.walk(node):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                if any(p in sub.value for p in protected):
                    return True
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "torment_service" or alias.name.startswith("torment_service."):
                    violations.append("import " + alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "torment_service"
                                or node.module.startswith("torment_service.")):
                violations.append("from " + node.module)
        elif isinstance(node, ast.Call):
            target = _dotted(node.func)
            if isinstance(node.func, ast.Name) and node.func.id == "__import__" and _refs_protected(node):
                violations.append("__import__ protected")
            if target in loaders and _refs_protected(node):
                violations.append("loader " + ".".join(target))
            if target in subproc and _refs_protected(node):
                violations.append("subprocess " + ".".join(target))
    return violations


def test_production_boundary_guards():
    for name in ("n64_falsifier_fixture_v0_1.py", "run_n64_falsifier_v0_1.py"):
        assert _scan_forbidden(os.path.join(_BV_DIR, name)) == []
