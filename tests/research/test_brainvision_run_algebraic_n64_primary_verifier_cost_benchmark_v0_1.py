"""Tests for the algebraic N=64 PRIMARY_V0_1 verifier-cost benchmark v0.1 (implementation verification only).

These tests NEVER call the real verifier, NEVER read the real 20,000-record retained stream, and NEVER write
the real results root. An autouse fixture replaces verify_candidate and verify_family with guards that raise on
contact; tests that need output install a synthetic verify_candidate stub. Every test builds a temporary git
repository (committed real verifier/serializer bytes so their blob identities equal the frozen constants, plus a
committed benchmark-runner stub and a gitignored synthetic candidate-stream fixture whose 20,000 records are
minimal) and publishes into a temporary result root outside that repository. A deterministic injected timer
yields exact durations, so statistics and projections are exactly predictable and no real witness mathematics
runs.
"""
import ast
import hashlib
import io
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import witness_canonical_json_v0_1 as cjson  # noqa: E402
import witness_family_verifier_v0_1 as verifier  # noqa: E402
import run_algebraic_n64_primary_verifier_cost_benchmark_v0_1 as bench  # noqa: E402

SOURCE_MODULE_FILES = {
    "verifier": "witness_family_verifier_v0_1.py",
    "serializer": "witness_canonical_json_v0_1.py",
}
SAMPLE = bench.SAMPLE_INDICES


# --------------------------------------------------------------- synthetic candidate-stream fixture (20000)
def _records(count):
    out = []
    for index in range(count):
        out.append({"raw_support_A": [0, 1, 2], "raw_support_B": [0, 3, 6],
                    "candidate_generation_index": index})
    return out


@pytest.fixture(scope="session")
def stream_fixture():
    payload = {"schema_name": "brainvision_descriptor_blind_candidate_stream", "schema_version": "0.1",
               "verification_mode": "PRIMARY_CANDIDATE_N64", "N": 64,
               "generator_identity_hash": "a" * 64, "generator_configuration_hash": "b" * 64,
               "budget_identity_hash": "c" * 64, "terminal_status": "budget_exhausted",
               "candidate_count": 20000, "records": _records(20000)}
    envelope = cjson.envelope("candidate_stream", payload)
    stream_bytes = cjson.canonical_json_bytes(envelope)
    return {"bytes": stream_bytes, "whole_sha": hashlib.sha256(stream_bytes).hexdigest(),
            "payload_sha": envelope["candidate_stream_sha256"]}


def _run_git(root, *args):
    subprocess.run(["git", "-C", root, *args], check=True, capture_output=True, text=True)


def _build_repo(root, stream_bytes):
    bv = os.path.join(root, "research", "brainvision")
    results = os.path.join(bv, "results", "algebraic_n64_primary_v0_1")
    os.makedirs(results)
    for _role, filename in SOURCE_MODULE_FILES.items():
        with open(os.path.join(BV_DIR, filename), "rb") as handle:
            data = handle.read()
        with open(os.path.join(bv, filename), "wb") as handle:
            handle.write(data)
    with open(os.path.join(bv, "run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py"), "wb") as handle:
        handle.write(b"# stub benchmark runner marker\n")
    with open(os.path.join(root, ".gitignore"), "wb") as handle:
        handle.write(b"research/brainvision/results/\n")
    with open(os.path.join(results, "algebraic_n64_primary_v0_1_candidate_stream.json"), "wb") as handle:
        handle.write(stream_bytes)
    _run_git(root, "init", "-q")
    _run_git(root, "symbolic-ref", "HEAD", "refs/heads/main")
    _run_git(root, "config", "user.email", "t@t.t")
    _run_git(root, "config", "user.name", "t")
    _run_git(root, "add", "-A")
    _run_git(root, "commit", "-q", "-m", "sources")
    _run_git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return root


@pytest.fixture(scope="session")
def clean_repo(tmp_path_factory, stream_fixture):
    root = str(tmp_path_factory.mktemp("benchrepo"))
    return _build_repo(root, stream_fixture["bytes"])


@pytest.fixture(autouse=True)
def _bind_input_constants(monkeypatch, stream_fixture):
    monkeypatch.setattr(bench, "INPUT_EXPECTED_SIZE", len(stream_fixture["bytes"]))
    monkeypatch.setattr(bench, "INPUT_WHOLE_FILE_SHA256", stream_fixture["whole_sha"])
    monkeypatch.setattr(bench, "INPUT_PAYLOAD_SHA256", stream_fixture["payload_sha"])


@pytest.fixture(autouse=True)
def _forbid_real_verifier(monkeypatch):
    def _candidate_guard(*_a, **_k):
        raise AssertionError("real verify_candidate contacted")

    def _family_guard(*_a, **_k):
        raise AssertionError("verify_family contacted")
    monkeypatch.setattr(verifier, "verify_candidate", _candidate_guard)
    monkeypatch.setattr(verifier, "verify_family", _family_guard)


@pytest.fixture
def results_root(tmp_path):
    return os.path.join(str(tmp_path), "external_results")


FIXED_ENV = {"python_version": "3.11.0", "python_implementation": "CPython", "os_name": "TestOS",
             "os_release": "1.0", "machine_architecture": "x86_64", "logical_cpu_count": 8,
             "process_bitness_bits": 64, "perf_counter_resolution": "1e-09",
             "perf_counter_monotonic": True, "perf_counter_adjustable": False}


def _timer(step_by_call):
    """Deterministic timer: each _timed_verify does start() then end(); yields exact durations per call."""
    ticks = []
    now = [0]
    for delta in step_by_call:
        ticks.append(now[0]); now[0] += delta      # start
        ticks.append(now[0]); now[0] += 1          # end (advance past the call)
    iterator = iter(ticks)

    def _clock():
        return next(iterator)
    return _clock


def _good_result(index):
    return {"execution_invalid": False, "execution_code": None,
            "pair_certificate": {"index": index}, "ordered_failure_codes": [],
            "primary_failure_code": None, "pair_valid": True}


def _install_verifier(monkeypatch, fn, calls=None):
    def _stub(record, n):
        if calls is not None:
            calls.append((record.get("candidate_generation_index"), n))
        return fn(record, n)
    monkeypatch.setattr(verifier, "verify_candidate", _stub)


def _run(clean_repo, results_root, monkeypatch, verifier_fn, *, durations=None, calls=None, env=None):
    _install_verifier(monkeypatch, verifier_fn, calls)
    step = durations if durations is not None else [7] * bench.PLANNED_CALL_COUNT
    out, err = io.StringIO(), io.StringIO()
    code = bench.run_operation(repository_root=clean_repo, results_root=results_root,
                               timer_ns=_timer(step), environment=env if env is not None else dict(FIXED_ENV),
                               stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def _final(results_root):
    return os.path.join(results_root, bench.FINAL_DIRECTORY_NAME)


def _staging(results_root):
    return os.path.join(results_root, bench.STAGING_DIRECTORY_NAME)


def _published(results_root):
    return sorted(os.listdir(_final(results_root)))


def _result_payload(results_root):
    with open(os.path.join(_final(results_root), bench.RESULT_FILENAME), "rb") as handle:
        raw = handle.read()
    return raw, json.loads(raw.decode("utf-8"))["verifier_cost_benchmark_result"]


def _summary(results_root):
    with open(os.path.join(_final(results_root), bench.SUMMARY_FILENAME), "rb") as handle:
        return handle.read()


TWO_FILE_SET = sorted([bench.RESULT_FILENAME, bench.SUMMARY_FILENAME])


# ============================================================= complete benchmark
def test_complete_benchmark_publishes_and_exits_zero(clean_repo, results_root, monkeypatch):
    calls = []
    code, out, err = _run(clean_repo, results_root, monkeypatch,
                          lambda record, n: _good_result(record["candidate_generation_index"]), calls=calls)
    assert code == bench.EXIT_PUBLISHED
    assert _published(results_root) == TWO_FILE_SET
    assert not os.path.exists(_staging(results_root))
    assert len(calls) == 32                                       # exactly 32 verify_candidate calls
    assert [c[1] for c in calls] == [64] * 32                     # always N=64
    _raw, payload = _result_payload(results_root)
    assert payload["benchmark_status"] == "BENCHMARK_COMPLETE"
    assert payload["schema_name"] == "brainvision_verifier_cost_benchmark_result"
    assert payload["benchmark_class"] == "NON_AUTHORITATIVE_VERIFIER_COST_BENCHMARK"
    assert payload["benchmark_profile"] == "PRIMARY_V0_1_FIXED_16_TWO_PASS"
    assert payload["authoritative_operation"] is False
    assert payload["completed_call_count"] == 32
    assert payload["planned_call_count"] == 32
    assert payload["linear_projections"] is not None


def test_call_order_and_panels_are_frozen(clean_repo, results_root, monkeypatch):
    calls = []
    _run(clean_repo, results_root, monkeypatch,
         lambda record, n: _good_result(record["candidate_generation_index"]), calls=calls)
    called_indices = [c[0] for c in calls]
    assert called_indices == list(SAMPLE) * 2                     # 16 in frozen order, twice
    _raw, payload = _result_payload(results_root)
    records = payload["call_records"]
    assert [r["candidate_generation_index"] for r in records] == list(SAMPLE) * 2
    assert [r["sample_order_position"] for r in records] == list(range(16)) * 2
    assert [r["pass_number"] for r in records] == [1] * 16 + [2] * 16
    prefix = [r for r in records if r["panel"] == "PREFIX_8"]
    spread = [r for r in records if r["panel"] == "SPREAD_8"]
    assert len(prefix) == 16 and len(spread) == 16
    assert all(r["candidate_generation_index"] in SAMPLE[:8] for r in prefix)
    assert all(r["candidate_generation_index"] in SAMPLE[8:] for r in spread)


def test_result_schema_distinct_from_freeze_result(clean_repo, results_root, monkeypatch):
    _run(clean_repo, results_root, monkeypatch,
         lambda record, n: _good_result(record["candidate_generation_index"]))
    raw, payload = _result_payload(results_root)
    assert b"freeze_result" not in raw
    assert "verifier_cost_benchmark_result" in json.loads(raw.decode("utf-8"))
    for banned in ("family_manifest", "candidate_decision_ledger", "accepted_pair_certificate_envelopes"):
        assert banned not in payload
    assert payload["family_selection_performed"] is False
    assert payload["family_verification_performed"] is False
    assert payload["family_freeze_performed"] is False


def test_no_full_pair_certificate_duplicated_in_artifact(clean_repo, results_root, monkeypatch):
    _run(clean_repo, results_root, monkeypatch,
         lambda record, n: _good_result(record["candidate_generation_index"]))
    _raw, payload = _result_payload(results_root)
    for record in payload["call_records"]:
        assert "pair_certificate" not in record                  # only its hash is retained
        assert bench.cjson.is_lower_hex_64(record["canonical_result_sha256"])


def test_canonical_result_has_no_trailing_newline_and_summary_lf(clean_repo, results_root, monkeypatch):
    _run(clean_repo, results_root, monkeypatch,
         lambda record, n: _good_result(record["candidate_generation_index"]))
    raw, _payload = _result_payload(results_root)
    assert not raw.endswith(b"\n")
    assert raw == cjson.canonical_json_bytes(json.loads(raw.decode("utf-8")))
    summary = _summary(results_root)
    assert b"\r" not in summary and summary.endswith(b"\n") and not summary.endswith(b"\n\n")


# ============================================================= statistics and projections
def test_statistics_are_exact_over_injected_durations(clean_repo, results_root, monkeypatch):
    # 32 durations: pass1 = 1..16, pass2 = 1..16 (same, so replay hashes match by construction)
    durations = list(range(1, 17)) + list(range(1, 17))
    _run(clean_repo, results_root, monkeypatch,
         lambda record, n: _good_result(record["candidate_generation_index"]), durations=durations)
    _raw, payload = _result_payload(results_root)
    combined = payload["statistics"]["combined"]["overall"]
    assert combined["count"] == 32
    assert combined["total_ns"] == 2 * sum(range(1, 17))          # 2 * 136 = 272
    assert combined["minimum_ns"] == 1 and combined["maximum_ns"] == 16
    assert combined["mean_ns"] == {"numerator": 17, "denominator": 2}   # 272/32 = 17/2
    # sorted combined = [1,1,2,2,...,16,16]; median of 32 = (16th,17th) = (8,9) -> 17/2
    assert combined["median_ns"] == {"numerator": 17, "denominator": 2}
    pass1_overall = payload["statistics"]["pass_1"]["overall"]
    assert pass1_overall["count"] == 16 and pass1_overall["total_ns"] == 136
    assert pass1_overall["minimum_ns"] == 1 and pass1_overall["maximum_ns"] == 16
    # nearest-rank p25 rank=ceil(0.25*16)=4 -> sorted[3]=4 ; p75 rank=12 -> sorted[11]=12
    assert pass1_overall["p25_ns"] == 4 and pass1_overall["p75_ns"] == 12


def test_projections_labeled_and_exact(clean_repo, results_root, monkeypatch):
    durations = [10] * 32                                         # every call 10 ns
    _run(clean_repo, results_root, monkeypatch,
         lambda record, n: _good_result(record["candidate_generation_index"]), durations=durations)
    _raw, payload = _result_payload(results_root)
    proj = payload["linear_projections"]
    assert "linear engineering projection" in proj["labels"]
    assert "not a guarantee" in proj["labels"]
    # overall mean = 10 ns exactly; * 40000 = 400000 ns
    assert proj["overall_mean_times_40000_ns"] == {"numerator": 400000, "denominator": 1}
    assert proj["overall_mean_times_20000_ns"] == {"numerator": 200000, "denominator": 1}
    assert proj["overall_mean_times_16_ns"] == {"numerator": 160, "denominator": 1}


def test_even_count_non_integer_median_is_exact_rational(clean_repo, results_root, monkeypatch):
    # pass durations chosen so a panel median is a non-integer (…, giving denominator 2)
    durations = [1, 2, 3, 4, 5, 6, 7, 8, 100, 100, 100, 100, 100, 100, 100, 100] * 2
    _run(clean_repo, results_root, monkeypatch,
         lambda record, n: _good_result(record["candidate_generation_index"]), durations=durations)
    _raw, payload = _result_payload(results_root)
    prefix = payload["statistics"]["pass_1"]["PREFIX_8"]
    # PREFIX_8 pass1 durations sorted = [1..8]; median = (4+5)/2 = 9/2
    assert prefix["median_ns"] == {"numerator": 9, "denominator": 2}
    assert isinstance(prefix["median_ns"]["numerator"], int)


# ============================================================= sampled-index validation
def test_sampled_index_correctness_uses_candidate_generation_index(clean_repo, results_root, monkeypatch):
    _run(clean_repo, results_root, monkeypatch,
         lambda record, n: _good_result(record["candidate_generation_index"]))
    _raw, payload = _result_payload(results_root)
    # every call record's stored index equals its stream candidate_generation_index (== position value)
    for record in payload["call_records"]:
        assert record["candidate_generation_index"] == SAMPLE[record["sample_order_position"]]


def test_corrupted_sample_index_refuses(tmp_path, stream_fixture, results_root, monkeypatch):
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    input_path = os.path.join(root, "research", "brainvision", "results", "algebraic_n64_primary_v0_1",
                              "algebraic_n64_primary_v0_1_candidate_stream.json")
    with open(input_path, "rb") as handle:
        envelope = json.loads(handle.read().decode("utf-8"))
    envelope["candidate_stream"]["records"][2499]["candidate_generation_index"] = 123456
    rebuilt = cjson.envelope("candidate_stream", envelope["candidate_stream"])
    rebuilt_bytes = cjson.canonical_json_bytes(rebuilt)
    with open(input_path, "wb") as handle:
        handle.write(rebuilt_bytes)
    monkeypatch.setattr(bench, "INPUT_EXPECTED_SIZE", len(rebuilt_bytes))
    monkeypatch.setattr(bench, "INPUT_WHOLE_FILE_SHA256", hashlib.sha256(rebuilt_bytes).hexdigest())
    monkeypatch.setattr(bench, "INPUT_PAYLOAD_SHA256", rebuilt["candidate_stream_sha256"])
    calls = []
    code, _out, err = _run(root, results_root, monkeypatch,
                           lambda record, n: _good_result(0), calls=calls)
    assert code == bench.EXIT_REFUSED
    assert calls == []                                           # verifier never contacted
    assert any(marker in err for marker in ("INPUT_STREAM_ENVELOPE_INVALID", "INPUT_STRUCTURE_INVALID",
                                            "SAMPLE_INDEX_MISMATCH", "SAMPLE_INDEX_OUT_OF_RANGE"))


# ============================================================= replay mismatch / execution-invalid / exception
def test_output_replay_mismatch_exits_one(clean_repo, results_root, monkeypatch):
    state = {"n": 0}

    def _fn(record, n):
        state["n"] += 1
        # make pass-2 call for index 0 differ from pass-1
        differ = state["n"] > 16 and record["candidate_generation_index"] == 0
        result = _good_result(record["candidate_generation_index"])
        if differ:
            result["primary_failure_code"] = "DIVERGENT"
        return result
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _fn)
    assert code == bench.EXIT_FAILURE
    assert _published(results_root) == TWO_FILE_SET               # failure result still published
    _raw, payload = _result_payload(results_root)
    assert payload["benchmark_status"] == "OUTPUT_REPLAY_MISMATCH"
    assert payload["pass_to_pass_identity"]["all_match"] is False
    assert 0 in payload["pass_to_pass_identity"]["mismatched_indices"]
    assert payload["linear_projections"] is None


def test_execution_invalid_stops_and_exits_one(clean_repo, results_root, monkeypatch):
    calls = []

    def _fn(record, n):
        result = _good_result(record["candidate_generation_index"])
        if record["candidate_generation_index"] == 4:            # 5th call in pass 1
            result["execution_invalid"] = True
            result["execution_code"] = "VERIFIER_CONFIGURATION_INVALID"
        return result
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _fn, calls=calls)
    assert code == bench.EXIT_FAILURE
    assert len(calls) == 5                                       # stopped immediately, no retry/continue
    _raw, payload = _result_payload(results_root)
    assert payload["benchmark_status"] == "VERIFIER_EXECUTION_INVALID"
    assert payload["completed_call_count"] == 5
    assert payload["failure_record"]["candidate_generation_index"] == 4
    assert payload["linear_projections"] is None


def test_verifier_exception_stops_retains_and_exits_one(clean_repo, results_root, monkeypatch):
    calls = []

    def _fn(record, n):
        if record["candidate_generation_index"] == 2:
            raise RuntimeError("verifier boom")
        return _good_result(record["candidate_generation_index"])
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _fn, calls=calls)
    assert code == bench.EXIT_FAILURE
    assert len(calls) == 3                                       # 0,1,2 -> raised on 2, no retry
    _raw, payload = _result_payload(results_root)
    assert payload["benchmark_status"] == "VERIFIER_CALL_EXCEPTION"
    assert "VERIFIER_CALL_EXCEPTION" in err


def test_malformed_verifier_output_is_result_invalid(clean_repo, results_root, monkeypatch):
    def _fn(record, n):
        result = _good_result(record["candidate_generation_index"])
        if record["candidate_generation_index"] == 1:
            result["pair_valid"] = "yes"                         # not a strict bool
        return result
    code, _out, _err = _run(clean_repo, results_root, monkeypatch, _fn)
    assert code == bench.EXIT_FAILURE
    _raw, payload = _result_payload(results_root)
    assert payload["benchmark_status"] == "BENCHMARK_RESULT_INVALID"
    assert payload["failure_record"]["stage"] == "OUTPUT_PAIR_VALID_NOT_BOOL"


def test_missing_required_verifier_key_is_result_invalid(clean_repo, results_root, monkeypatch):
    def _fn(record, n):
        result = _good_result(record["candidate_generation_index"])
        if record["candidate_generation_index"] == 0:
            del result["primary_failure_code"]
        return result
    code, _out, _err = _run(clean_repo, results_root, monkeypatch, _fn)
    assert code == bench.EXIT_FAILURE
    _raw, payload = _result_payload(results_root)
    assert payload["benchmark_status"] == "BENCHMARK_RESULT_INVALID"


# ============================================================= publication / retention
def test_rename_failure_retains_staging(clean_repo, results_root, monkeypatch):
    def _fail(_src, _dst):
        raise OSError("rename refused")
    monkeypatch.setattr(bench.os, "rename", _fail)
    code, _out, err = _run(clean_repo, results_root, monkeypatch,
                           lambda record, n: _good_result(record["candidate_generation_index"]))
    assert code == bench.EXIT_FAILURE
    assert not os.path.exists(_final(results_root))
    assert os.path.isdir(_staging(results_root))
    assert sorted(os.listdir(_staging(results_root))) == TWO_FILE_SET
    assert "publication rename failed" in err


def test_stdout_failure_after_publication_keeps_final(clean_repo, results_root, monkeypatch):
    class _Raising:
        def write(self, _t):
            raise OSError("stdout refused")
    _install_verifier(monkeypatch, lambda record, n: _good_result(record["candidate_generation_index"]))
    err = io.StringIO()
    code = bench.run_operation(repository_root=clean_repo, results_root=results_root,
                               timer_ns=_timer([7] * 32), environment=dict(FIXED_ENV),
                               stdout=_Raising(), stderr=err)
    assert code == bench.EXIT_FAILURE
    assert _published(results_root) == TWO_FILE_SET
    assert not os.path.exists(_staging(results_root))
    assert "stdout mirroring failed after publication" in err.getvalue()


# ------------------------- publication-boundary: everything published inside staging, no post-rename write ---
def _snapshot_after_rename(monkeypatch, results_root):
    """Wrap os.rename to capture both final artifact hashes at the instant of publication."""
    snapshot = {}
    real_rename = bench.os.rename

    def _watch(src, dst):
        real_rename(src, dst)
        if os.path.basename(dst) == bench.FINAL_DIRECTORY_NAME:
            with open(os.path.join(dst, bench.RESULT_FILENAME), "rb") as handle:
                snapshot["result"] = hashlib.sha256(handle.read()).hexdigest()
            with open(os.path.join(dst, bench.SUMMARY_FILENAME), "rb") as handle:
                snapshot["summary"] = hashlib.sha256(handle.read()).hexdigest()
    monkeypatch.setattr(bench.os, "rename", _watch)
    return snapshot


def test_no_post_rename_artifact_write(clean_repo, results_root, monkeypatch):
    written_paths = []
    real_write = bench._write_exclusive

    def _record(path, data):
        written_paths.append(path)
        real_write(path, data)
    monkeypatch.setattr(bench, "_write_exclusive", _record)
    snapshot = _snapshot_after_rename(monkeypatch, results_root)

    code, _out, _err = _run(clean_repo, results_root, monkeypatch,
                            lambda record, n: _good_result(record["candidate_generation_index"]))
    assert code == bench.EXIT_PUBLISHED
    # every write went directly into the staging directory, never into the final directory
    assert written_paths
    assert all(os.path.dirname(path) == _staging(results_root) for path in written_paths)
    assert all(os.path.dirname(path) != _final(results_root) for path in written_paths)
    # bytes captured at publication equal the bytes present after the run returned (no post-rename rewrite)
    with open(os.path.join(_final(results_root), bench.RESULT_FILENAME), "rb") as handle:
        result_now = hashlib.sha256(handle.read()).hexdigest()
    with open(os.path.join(_final(results_root), bench.SUMMARY_FILENAME), "rb") as handle:
        summary_now = hashlib.sha256(handle.read()).hexdigest()
    assert snapshot["result"] == result_now
    assert snapshot["summary"] == summary_now


def test_result_hash_present_in_summary_without_post_rename_rewrite(clean_repo, results_root, monkeypatch):
    written_paths = []
    real_write = bench._write_exclusive

    def _record(path, data):
        written_paths.append(path)
        real_write(path, data)
    monkeypatch.setattr(bench, "_write_exclusive", _record)
    _run(clean_repo, results_root, monkeypatch,
         lambda record, n: _good_result(record["candidate_generation_index"]))
    raw_result, _payload = _result_payload(results_root)
    expected_hash = hashlib.sha256(raw_result).hexdigest()
    summary = _summary(results_root).decode("utf-8")
    assert ("result_whole_file_sha256 = %s" % expected_hash) in summary   # correct hash, staged once
    assert written_paths.count(os.path.join(_staging(results_root), bench.SUMMARY_FILENAME)) == 1


def test_rename_failure_staging_summary_is_honest(clean_repo, results_root, monkeypatch):
    def _fail(_src, _dst):
        raise OSError("rename refused")
    monkeypatch.setattr(bench.os, "rename", _fail)
    code, _out, err = _run(clean_repo, results_root, monkeypatch,
                           lambda record, n: _good_result(record["candidate_generation_index"]))
    assert code == bench.EXIT_FAILURE
    assert not os.path.exists(_final(results_root))
    assert sorted(os.listdir(_staging(results_root))) == TWO_FILE_SET     # complete staging retained
    with open(os.path.join(_staging(results_root), bench.SUMMARY_FILENAME), "rb") as handle:
        staged_summary = handle.read().decode("utf-8")
    for false_claim in ("exit_code = 0", "publication completed = True",
                        "published_artifact_set = result+summary"):
        assert false_claim not in staged_summary
    assert "publication protocol = staging-to-final atomic rename" in staged_summary
    assert "planned artifact set = result+summary" in staged_summary


def test_stdout_failure_preserves_final_bytes(clean_repo, results_root, monkeypatch):
    class _Raising:
        def write(self, _t):
            raise OSError("stdout refused")
    snapshot = _snapshot_after_rename(monkeypatch, results_root)
    _install_verifier(monkeypatch, lambda record, n: _good_result(record["candidate_generation_index"]))
    err = io.StringIO()
    code = bench.run_operation(repository_root=clean_repo, results_root=results_root,
                               timer_ns=_timer([7] * 32), environment=dict(FIXED_ENV),
                               stdout=_Raising(), stderr=err)
    assert code == bench.EXIT_FAILURE
    assert os.path.isdir(_final(results_root))
    result_now = hashlib.sha256(
        open(os.path.join(_final(results_root), bench.RESULT_FILENAME), "rb").read()).hexdigest()
    summary_now = hashlib.sha256(
        open(os.path.join(_final(results_root), bench.SUMMARY_FILENAME), "rb").read()).hexdigest()
    assert snapshot["result"] == result_now                              # unchanged after stdout failure
    assert snapshot["summary"] == summary_now


def test_negative_injected_duration_never_completes(clean_repo, results_root, monkeypatch):
    _install_verifier(monkeypatch, lambda record, n: _good_result(record["candidate_generation_index"]))
    # timer yields started=10, completed=3 for the first call -> duration -7
    ticks = iter([10, 3])

    def _bad_clock():
        return next(ticks)
    err = io.StringIO()
    code = bench.run_operation(repository_root=clean_repo, results_root=results_root,
                               timer_ns=_bad_clock, environment=dict(FIXED_ENV),
                               stdout=io.StringIO(), stderr=err)
    assert code == bench.EXIT_FAILURE
    _raw, payload = _result_payload(results_root)
    assert payload["benchmark_status"] == "BENCHMARK_RESULT_INVALID"
    assert payload["failure_record"]["stage"] == "negative_duration"
    assert payload["linear_projections"] is None


def test_never_overwrites_existing_final(clean_repo, results_root, monkeypatch):
    os.makedirs(_final(results_root))
    calls = []
    code, _out, err = _run(clean_repo, results_root, monkeypatch,
                           lambda record, n: _good_result(0), calls=calls)
    assert code == bench.EXIT_REFUSED and calls == []
    assert "FINAL_DIRECTORY_EXISTS" in err


def test_preexisting_staging_refusal_not_deleted(clean_repo, results_root, monkeypatch):
    os.makedirs(_staging(results_root))
    marker = os.path.join(_staging(results_root), "keep.txt")
    open(marker, "w").close()
    calls = []
    code, _out, err = _run(clean_repo, results_root, monkeypatch,
                           lambda record, n: _good_result(0), calls=calls)
    assert code == bench.EXIT_REFUSED and calls == []
    assert os.path.exists(marker) and "STAGING_DIRECTORY_EXISTS" in err


# ============================================================= CLI refusal
def test_main_rejects_any_argument(capsys):
    for argv in (["prog", "--x"], ["prog", "extra"]):
        assert bench.main(argv) == bench.EXIT_REFUSED
    assert "takes no arguments" in capsys.readouterr().err


def test_run_operation_rejects_extra_arguments(clean_repo, results_root):
    err = io.StringIO()
    code = bench.run_operation(repository_root=clean_repo, results_root=results_root,
                               extra_arguments=["--x"], stdout=io.StringIO(), stderr=err)
    assert code == bench.EXIT_REFUSED and "takes no arguments" in err.getvalue()


# ============================================================= repository / source refusals
def test_dirty_tree_refuses(tmp_path, stream_fixture, results_root, monkeypatch):
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    with open(os.path.join(root, "research", "brainvision", "witness_family_verifier_v0_1.py"), "ab") as handle:
        handle.write(b"\n# dirty\n")
    calls = []
    code, _out, err = _run(root, results_root, monkeypatch, lambda record, n: _good_result(0), calls=calls)
    assert code == bench.EXIT_REFUSED and calls == []
    assert "WORKING_TREE_NOT_CLEAN" in err


def test_origin_mismatch_refuses(tmp_path, stream_fixture, results_root, monkeypatch):
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    with open(os.path.join(root, "extra.txt"), "w") as handle:
        handle.write("x")
    _run_git(root, "add", "-A")
    _run_git(root, "commit", "-q", "-m", "advance")
    code, _out, err = _run(root, results_root, monkeypatch, lambda record, n: _good_result(0))
    assert code == bench.EXIT_REFUSED and "ORIGIN_MAIN_MISMATCH" in err


def test_verifier_blob_identity_mismatch_refuses(tmp_path, stream_fixture, results_root, monkeypatch):
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    monkeypatch.setattr(bench, "FROZEN_SOURCE_BLOB_IDS",
                        dict(bench.FROZEN_SOURCE_BLOB_IDS, verifier="0" * 40))
    calls = []
    code, _out, err = _run(root, results_root, monkeypatch, lambda record, n: _good_result(0), calls=calls)
    assert code == bench.EXIT_REFUSED and calls == []
    assert "SOURCE_BLOB_IDENTITY_MISMATCH" in err


@pytest.mark.parametrize("role_file,expected_marker", [
    ("run_algebraic_n64_primary_verifier_cost_benchmark_v0_1.py", "RUNNER_PATH_OWNERSHIP_INVALID"),
    ("witness_family_verifier_v0_1.py", "SOURCE_PATH_INVALID"),
    ("witness_canonical_json_v0_1.py", "SOURCE_PATH_INVALID"),
])
def test_source_symlink_or_path_escape_refuses(tmp_path, stream_fixture, results_root, monkeypatch,
                                               role_file, expected_marker):
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    target = os.path.join(root, "research", "brainvision", role_file)
    outside = os.path.join(str(tmp_path), "outside_" + role_file)
    with open(outside, "wb") as handle:
        handle.write(b"# elsewhere\n")
    os.remove(target)
    try:
        os.symlink(outside, target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")
    # commit the symlink so the working tree stays clean; the refusal is about the source being a symlink,
    # not about a dirty tree (clean-tree check precedes source checks in the pre-contact order)
    _run_git(root, "add", "-A")
    _run_git(root, "commit", "-q", "-m", "symlink")
    _run_git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    calls = []
    code, _out, err = _run(root, results_root, monkeypatch, lambda record, n: _good_result(0), calls=calls)
    assert code == bench.EXIT_REFUSED and calls == []
    assert expected_marker in err


def test_source_bytes_differ_from_commit_refuses(tmp_path, stream_fixture, results_root, monkeypatch):
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    original = bench._git_blob_bytes

    def _mutated(repo, blob):
        return (original(repo, blob) or b"") + b"X"
    monkeypatch.setattr(bench, "_git_blob_bytes", _mutated)
    code, _out, err = _run(root, results_root, monkeypatch, lambda record, n: _good_result(0))
    assert code == bench.EXIT_REFUSED and "SOURCE_BYTES_DIFFER_FROM_COMMIT" in err


# ============================================================= input refusals
def test_input_size_mismatch_refuses(clean_repo, results_root, monkeypatch):
    monkeypatch.setattr(bench, "INPUT_EXPECTED_SIZE", 123)
    calls = []
    code, _out, err = _run(clean_repo, results_root, monkeypatch, lambda record, n: _good_result(0),
                           calls=calls)
    assert code == bench.EXIT_REFUSED and calls == []
    assert "INPUT_SIZE_MISMATCH" in err


def test_input_payload_hash_mismatch_refuses(clean_repo, results_root, monkeypatch):
    monkeypatch.setattr(bench, "INPUT_PAYLOAD_SHA256", "8" * 64)
    code, _out, err = _run(clean_repo, results_root, monkeypatch, lambda record, n: _good_result(0))
    assert code == bench.EXIT_REFUSED and "INPUT_PAYLOAD_HASH" in err


def test_duplicate_json_keys_refused(tmp_path, stream_fixture, results_root, monkeypatch):
    dup = b'{"candidate_stream":{},"candidate_stream":{},"candidate_stream_sha256":"' + b"7" * 64 + b'"}'
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    input_path = os.path.join(root, "research", "brainvision", "results", "algebraic_n64_primary_v0_1",
                              "algebraic_n64_primary_v0_1_candidate_stream.json")
    with open(input_path, "wb") as handle:
        handle.write(dup)
    monkeypatch.setattr(bench, "INPUT_EXPECTED_SIZE", len(dup))
    monkeypatch.setattr(bench, "INPUT_WHOLE_FILE_SHA256", hashlib.sha256(dup).hexdigest())
    code, _out, err = _run(root, results_root, monkeypatch, lambda record, n: _good_result(0))
    assert code == bench.EXIT_REFUSED and "INPUT_JSON_INVALID" in err


# ============================================================= environment record
def test_environment_record_has_only_permitted_fields(clean_repo, results_root, monkeypatch):
    _run(clean_repo, results_root, monkeypatch,
         lambda record, n: _good_result(record["candidate_generation_index"]))
    _raw, payload = _result_payload(results_root)
    env = payload["environment"]
    assert set(env) == set(FIXED_ENV)
    raw = _result_payload(results_root)[0]
    for banned in (b"USER", b"HOME", b"ip_address", b"computer_name", b"USERNAME"):
        assert banned not in raw


# ============================================================= AST / import boundary
def _bench_source():
    with open(bench.__file__.replace(".pyc", ".py"), "r", encoding="utf-8") as handle:
        return handle.read()


def _calls_named(tree, name):
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            attr = target.attr if isinstance(target, ast.Attribute) else (
                target.id if isinstance(target, ast.Name) else None)
            if attr == name:
                found.append(node)
    return found


def test_exactly_one_verify_candidate_call_site():
    assert len(_calls_named(ast.parse(_bench_source()), "verify_candidate")) == 1


def test_zero_forbidden_math_and_freezer_call_sites():
    tree = ast.parse(_bench_source())
    for banned in ("verify_family", "incremental_family_eligibility", "freeze", "freeze_with_replay",
                   "validate_local_configuration"):
        assert _calls_named(tree, banned) == [], banned


def test_import_boundary():
    tree = ast.parse(_bench_source())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            roots.add(node.module.split(".")[0])
    assert roots.issubset({"__future__", "hashlib", "json", "os", "platform", "stat", "subprocess", "sys",
                           "time", "typing", "witness_canonical_json_v0_1", "witness_family_verifier_v0_1"})
    for forbidden in ("witness_family_freeze_v0_1", "run_algebraic_n64_primary_freeze_v0_1",
                      "algebraic_direct_sum_n64_candidate_generator_v0_1", "psi_trs", "descriptors",
                      "run_n64_falsifier_v0_1", "torment_service"):
        assert forbidden not in roots


def test_timed_region_contains_only_verify_candidate():
    """The single timed helper brackets exactly one verify_candidate call and nothing else costly."""
    tree = ast.parse(_bench_source())
    timed = [node for node in ast.walk(tree)
             if isinstance(node, ast.FunctionDef) and node.name == "_timed_verify"]
    assert len(timed) == 1
    assert len(_calls_named(timed[0], "verify_candidate")) == 1
    for banned in ("canonical_json_bytes", "payload_sha256", "loads", "rename", "makedirs"):
        assert _calls_named(timed[0], banned) == [], banned


# ============================================================= real-path protection
def test_real_result_paths_never_created_by_this_suite():
    real_results = os.path.join(BV_DIR, "results")
    assert (
        os.path.exists(os.path.join(real_results, bench.FINAL_DIRECTORY_NAME))
        == _BV_REAL_FINAL_EXISTED_AT_IMPORT
    )
    assert (
        os.path.exists(os.path.join(real_results, bench.STAGING_DIRECTORY_NAME))
        == _BV_REAL_STAGING_EXISTED_AT_IMPORT
    )


def test_default_repository_root_points_into_repo():
    root = bench._default_repository_root()
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
    os.path.join(_BV_REAL_RESULTS_ROOT_AT_IMPORT, bench.FINAL_DIRECTORY_NAME)
)
_BV_REAL_STAGING_EXISTED_AT_IMPORT = os.path.exists(
    os.path.join(_BV_REAL_RESULTS_ROOT_AT_IMPORT, bench.STAGING_DIRECTORY_NAME)
)
