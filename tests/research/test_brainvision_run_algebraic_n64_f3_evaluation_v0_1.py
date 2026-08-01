"""Tests for the frozen-family F3 evaluation runner (non-contact; monkeypatched preflight and pass provider).

An autouse fixture makes psi_trs.psi_trs_features and evaluator.build_production_feature_cache raise if reached,
so no test contacts the descriptor or begins a production pass. Publication/replay/staging tests inject a
synthetic pass provider and monkeypatch the pre-contact preflight so no temporary git repository is required;
pre-contact refusal tests exercise the real gate/argument/output checks. Every publication test uses a
temporary results root; the real repository results path is never written.
"""
import ast
import io
import os
import sys

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import psi_trs  # noqa: E402
import algebraic_n64_f3_evaluator_v0_1 as ev  # noqa: E402
import run_algebraic_n64_f3_evaluation_v0_1 as runner  # noqa: E402


@pytest.fixture(autouse=True)
def _forbid_contact(monkeypatch):
    def _psi_guard(*_a, **_k):
        raise AssertionError("psi_trs.psi_trs_features contacted during a runner test")

    def _cache_guard(*_a, **_k):
        raise AssertionError("build_production_feature_cache contacted during a runner test")
    monkeypatch.setattr(psi_trs, "psi_trs_features", _psi_guard)
    monkeypatch.setattr(ev, "build_production_feature_cache", _cache_guard)


def _synthetic_pass():
    """A minimal but serializable evaluate_from_feature_cache-shaped result (no descriptor contact)."""
    evaluation_pass = {
        "members": [], "pairs": [
            {"candidate_generation_index": 478, "pair_order_index": 0, "primary_pass": False,
             "gates": {"full_dual_orbit_extreme": False, "k0_not_extreme_against_either_member": True,
                       "recursive_positive_all_starts": False},
             "margins": {"full_margin_vs_A": 0.0, "full_margin_vs_B": 0.0, "k0_margin_vs_A": 0.0,
                         "k0_margin_vs_B": 0.0, "minimum_recursive_difference": 0.0},
             "pair_verdict_flags": ["PAIR_FULL_NOT_DUAL_ORBIT_EXTREME"]}],
        "family_summary": {"strong_pass_count": 0, "family_verdict": ev.STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED,
                           "pair_verdicts": [{"candidate_generation_index": 478, "pair_order_index": 0,
                                              "primary_pass": False,
                                              "pair_verdict_flags": ["PAIR_FULL_NOT_DUAL_ORBIT_EXTREME"]}]},
        "descriptor_call_record": {"completed_descriptor_calls": 768},
        "pass_validity": {"feature_schema_valid": True, "canonical_serialization_valid": True}}
    validity = dict(evaluation_pass["pass_validity"])
    return {"evaluation_pass": evaluation_pass, "valid_run": True,
            "family_verdict": ev.STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED, "strong_pass_count": 0,
            "failure_record": None, "validity": validity}


@pytest.fixture
def patched_preflight(monkeypatch):
    monkeypatch.setattr(runner, "_check_repository", lambda root, is_production: "a" * 40)
    monkeypatch.setattr(runner, "_bind_sources", lambda root: {"runner": {"path": "x", "blob_id": "b" * 40,
                                                                          "raw_byte_sha256": "c" * 64}})
    monkeypatch.setattr(runner, "_load_and_validate_input", lambda root: ({}, "d" * 64, []))
    monkeypatch.setattr(runner, "environment_fingerprint", lambda: {"python_version": "3.11.0"})


@pytest.fixture
def results_root(tmp_path):
    return os.path.join(str(tmp_path), "external_results")


def _final(results_root):
    return os.path.join(results_root, runner.FINAL_DIRECTORY_NAME)


def _staging(results_root):
    return os.path.join(results_root, runner.STAGING_DIRECTORY_NAME)


def _published(results_root):
    return sorted(os.listdir(_final(results_root)))


TWO_FILE_SET = sorted([runner.RESULT_FILENAME, runner.SUMMARY_FILENAME])


def _run(results_root, patched, pass_provider, gate_value="1"):
    out, err = io.StringIO(), io.StringIO()
    code = runner.run_operation(repository_root="/unused", results_root=results_root,
                                gate_value=gate_value, pass_provider=pass_provider,
                                stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


# ----------------------------------------------------------------- CLI / gate refusals
def test_main_rejects_any_argument(capsys):
    for argv in (["prog", "--x"], ["prog", "extra"]):
        assert runner.main(argv) == runner.EXIT_REFUSED
    assert "takes no arguments" in capsys.readouterr().err


def test_run_operation_rejects_extra_arguments(results_root):
    err = io.StringIO()
    code = runner.run_operation(repository_root="/unused", results_root=results_root,
                                extra_arguments=["--x"], gate_value="1", pass_provider=_synthetic_pass,
                                stdout=io.StringIO(), stderr=err)
    assert code == runner.EXIT_REFUSED and "takes no arguments" in err.getvalue()


def test_gate_defaults_closed(monkeypatch, results_root):
    monkeypatch.delenv(runner.EVALUATION_AUTHORIZATION_ENV, raising=False)
    calls = {"n": 0}

    def _provider():
        calls["n"] += 1
        return _synthetic_pass()
    err = io.StringIO()
    code = runner.run_operation(repository_root="/unused", results_root=results_root,
                                gate_value="__ENV__", pass_provider=_provider,
                                stdout=io.StringIO(), stderr=err)
    assert code == runner.EXIT_REFUSED
    assert calls["n"] == 0                                              # no pass, no descriptor contact
    assert ev.EVALUATION_NOT_AUTHORIZED in err.getvalue()
    assert not os.path.exists(_staging(results_root))


def test_wrong_gate_value_refused(results_root):
    calls = {"n": 0}

    def _provider():
        calls["n"] += 1
        return _synthetic_pass()
    code, _out, err = _run(results_root, None, _provider, gate_value="0")
    assert code == runner.EXIT_REFUSED and calls["n"] == 0
    assert ev.EVALUATION_NOT_AUTHORIZED in err


# ----------------------------------------------------------------- publication / replay
def test_successful_two_pass_publication(patched_preflight, results_root):
    code, out, err = _run(results_root, patched_preflight, _synthetic_pass)
    assert code == runner.EXIT_PUBLISHED
    assert _published(results_root) == TWO_FILE_SET
    assert not os.path.exists(_staging(results_root))
    assert out != ""                                                   # summary mirrored to stdout
    import json
    with open(os.path.join(_final(results_root), runner.RESULT_FILENAME), "rb") as handle:
        result = json.loads(handle.read().decode("utf-8"))["family_evaluation_result"]
    assert result["schema_name"] == "torment_brainvision_algebraic_n64_f3_family_evaluation"
    assert result["replay_record"]["byte_identical"] is True
    assert result["family_verdict"] == ev.STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED
    assert result["authoritative_operation"] is True


def test_replay_mismatch_yields_invalid_family_evaluation(patched_preflight, results_root):
    state = {"n": 0}

    def _diverging():
        state["n"] += 1
        result = _synthetic_pass()
        result["evaluation_pass"]["family_summary"]["strong_pass_count"] = state["n"]  # differs pass 1 vs 2
        return result
    code, _out, _err = _run(results_root, patched_preflight, _diverging)
    assert code == runner.EXIT_PUBLISHED                               # a canonical result is still published
    import json
    with open(os.path.join(_final(results_root), runner.RESULT_FILENAME), "rb") as handle:
        result = json.loads(handle.read().decode("utf-8"))["family_evaluation_result"]
    assert result["replay_record"]["byte_identical"] is False
    assert result["family_verdict"] == ev.INVALID_FAMILY_EVALUATION
    assert result["failure_record"]["failure_code"] == ev.REPLAY_MISMATCH
    assert result["authoritative_operation"] is False


def test_never_overwrites_existing_final(patched_preflight, results_root):
    os.makedirs(_final(results_root))
    calls = {"n": 0}

    def _provider():
        calls["n"] += 1
        return _synthetic_pass()
    code, _out, err = _run(results_root, patched_preflight, _provider)
    assert code == runner.EXIT_REFUSED and calls["n"] == 0             # pre-contact refusal, no pass
    assert runner.evaluator.OUTPUT_PATH_EXISTS in err


def test_preexisting_staging_refused(patched_preflight, results_root):
    os.makedirs(_staging(results_root))
    calls = {"n": 0}

    def _provider():
        calls["n"] += 1
        return _synthetic_pass()
    code, _out, err = _run(results_root, patched_preflight, _provider)
    assert code == runner.EXIT_REFUSED and calls["n"] == 0
    assert runner.evaluator.OUTPUT_PATH_EXISTS in err


def test_rename_failure_retains_evidence_bearing_staging(patched_preflight, results_root, monkeypatch):
    def _fail(_src, _dst):
        raise OSError("rename refused")
    monkeypatch.setattr(runner.os, "rename", _fail)
    code, _out, err = _run(results_root, patched_preflight, _synthetic_pass)
    assert code == runner.EXIT_FAILURE
    assert not os.path.exists(_final(results_root))
    assert sorted(os.listdir(_staging(results_root))) == TWO_FILE_SET  # complete staging retained
    assert runner.evaluator.PUBLICATION_FAILURE in err


def test_stdout_failure_after_publication_preserves_final(patched_preflight, results_root):
    class _Raising:
        def write(self, _t):
            raise OSError("stdout refused")
    err = io.StringIO()
    code = runner.run_operation(repository_root="/unused", results_root=results_root, gate_value="1",
                                pass_provider=_synthetic_pass, stdout=_Raising(), stderr=err)
    assert code == runner.EXIT_FAILURE
    assert _published(results_root) == TWO_FILE_SET
    assert runner.evaluator.STDOUT_FAILURE in err.getvalue()


def test_pass_exception_is_contained_and_retains_staging(patched_preflight, results_root):
    def _boom():
        raise RuntimeError("evaluation exploded")
    code, _out, err = _run(results_root, patched_preflight, _boom)
    assert code == runner.EXIT_FAILURE
    assert not os.path.exists(_final(results_root))
    assert runner.evaluator.DESCRIPTOR_CALL_FAILED in err


# ----------------------------------------------------------------- import boundary / real-path protection
def _runner_source():
    with open(os.path.join(BV_DIR, "run_algebraic_n64_f3_evaluation_v0_1.py"), "r",
              encoding="utf-8") as handle:
        return handle.read()


def test_runner_import_boundary_no_forbidden_imports():
    tree = ast.parse(_runner_source())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            roots.add(node.module.split(".")[0])
    for forbidden in ("run_n64_falsifier_v0_1", "witness_family_freeze_v0_1", "torment_service"):
        assert forbidden not in roots
    assert not any("generator" in r for r in roots)
    assert "psi_trs" not in roots                                      # descriptor contact only via evaluator


def test_runner_has_no_direct_psi_call_site():
    tree = ast.parse(_runner_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr != "psi_trs_features"


def test_real_results_paths_absent():
    real_results = os.path.join(BV_DIR, "results")
    assert (
        os.path.exists(os.path.join(real_results, runner.FINAL_DIRECTORY_NAME))
        == _BV_REAL_FINAL_EXISTED_AT_IMPORT
    )
    assert (
        os.path.exists(os.path.join(real_results, runner.STAGING_DIRECTORY_NAME))
        == _BV_REAL_STAGING_EXISTED_AT_IMPORT
    )


def test_default_repository_root_points_into_repo():
    root = runner._default_repository_root()
    assert os.path.isdir(os.path.join(root, "research", "brainvision"))


# --------------------------------------------------------------------------- #
# Canonical result-path snapshot.
#
# The authorized algebraic N=64 runs legitimately created the canonical result
# directories, so the earlier 'must remain absent' assertions are no longer
# true. The protection they provided is preserved by comparing against the
# existence state observed at import time instead: no test may create or
# remove a canonical result directory. FINAL and STAGING are snapshotted
# independently.
# --------------------------------------------------------------------------- #

_BV_REAL_RESULTS_ROOT_AT_IMPORT = os.path.join(BV_DIR, "results")
_BV_REAL_FINAL_EXISTED_AT_IMPORT = os.path.exists(
    os.path.join(_BV_REAL_RESULTS_ROOT_AT_IMPORT, runner.FINAL_DIRECTORY_NAME)
)
_BV_REAL_STAGING_EXISTED_AT_IMPORT = os.path.exists(
    os.path.join(_BV_REAL_RESULTS_ROOT_AT_IMPORT, runner.STAGING_DIRECTORY_NAME)
)
