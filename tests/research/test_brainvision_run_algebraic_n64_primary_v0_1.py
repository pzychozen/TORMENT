"""Tests for the algebraic N=64 PRIMARY_V0_1 runner v0.1 (offline; implementation verification only).

These tests NEVER execute the real PRIMARY_V0_1 enumeration. An autouse fixture replaces both generator entry
points with stubs that raise on contact, so any unstubbed call fails loudly rather than silently starting a
3,395,616-tuple traversal. Every test publishes into a pytest temporary directory; the real ignored results
directory research/brainvision/results/ is never read, created, or written. No verifier, freezer, ΨTRS,
descriptor, N64 evaluator, subprocess, or network contact occurs.
"""
import ast
import hashlib
import io
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import algebraic_direct_sum_n64_candidate_generator_v0_1 as generator  # noqa: E402
import run_algebraic_n64_primary_v0_1 as runner  # noqa: E402
import witness_canonical_json_v0_1 as cjson  # noqa: E402

MAX_TUPLES = 3_395_616
MAX_RECORDS = 20_000


# ----------------------------------------------------------------- safety: no real execution, ever
@pytest.fixture(autouse=True)
def _forbid_real_generator_execution(monkeypatch):
    def _replay_guard(*_args, **_kwargs):
        raise AssertionError("real PRIMARY_V0_1 replay execution attempted")

    def _provisional_guard(*_args, **_kwargs):
        raise AssertionError("provisional generate_candidate_stream was called")

    monkeypatch.setattr(generator, "generate_candidate_stream_with_replay", _replay_guard)
    monkeypatch.setattr(generator, "generate_candidate_stream", _provisional_guard)


# ----------------------------------------------------------------- synthetic replay envelopes
def _counters(examined=12, colliding=7, direct=5, duplicates=1, emitted=4):
    return {"parameter_tuples_examined": examined, "colliding_parameter_tuples_rejected": colliding,
            "direct_tuples_found": direct, "exact_duplicate_candidates_skipped": duplicates,
            "candidate_records_emitted": emitted}


def _records(count=3):
    out = []
    for index in range(count):
        out.append({"raw_support_A": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 + index],
                    "raw_support_B": [0, 1, 2, 55, 56, 57, 58, 59, 60, 61, 62, 63 - index],
                    "candidate_generation_index": index,
                    "generator_diagnostics": {"parameter_tuple_index": index * 7, "U": [0, 1, 2],
                                              "V": [0, 3, 6, 9], "sum_directness_count": 12,
                                              "difference_directness_count": 12,
                                              "exact_duplicate_count_before_emission": 0}})
    return out


def _stream_envelope(terminal_status, records):
    payload = {"schema_name": "brainvision_descriptor_blind_candidate_stream", "schema_version": "0.1",
               "verification_mode": "PRIMARY_CANDIDATE_N64", "N": 64,
               "generator_identity_hash": "a" * 64, "generator_configuration_hash": "b" * 64,
               "budget_identity_hash": "c" * 64, "terminal_status": terminal_status,
               "candidate_count": len(records), "records": records}
    return cjson.envelope("candidate_stream", payload)


def _budget_envelope(max_tuples=MAX_TUPLES, max_records=MAX_RECORDS):
    return cjson.envelope("structural_budget",
                          {"schema_name": "brainvision_generator_structural_budget", "schema_version": "0.1",
                           "profile_name": "PRIMARY_V0_1", "max_parameter_tuples_examined": max_tuples,
                           "max_candidate_records_emitted": max_records,
                           "normalized_parameter_domain_size": MAX_TUPLES,
                           "termination_precedence": ["DOMAIN_EXHAUSTED", "MAX_CANDIDATE_RECORDS_EMITTED",
                                                      "MAX_PARAMETER_TUPLES_EXAMINED"]})


def _replay_envelope(terminal_status="stream_completed", records=None, authoritative=True, eligible=True,
                     byte_identical=True, stream=True, failure=None, run1=None, run2=None,
                     budget_envelope=None):
    records = _records() if records is None else records
    stream_envelope = _stream_envelope(terminal_status, records) if stream else None
    stream_hash = stream_envelope["candidate_stream_sha256"] if stream else None
    run1 = _counters() if run1 is None else run1
    payload = {
        "schema_name": "brainvision_generator_replay_result", "schema_version": "0.1",
        "authoritative_operation": authoritative, "downstream_freeze_eligible": eligible,
        "byte_identical": byte_identical,
        "run1_candidate_stream_sha256": stream_hash, "run2_candidate_stream_sha256": stream_hash,
        "generator_identity_envelope": cjson.envelope("generator_identity", {"route_identity": "X"}),
        "generator_configuration_envelope": cjson.envelope("generator_configuration", {"n": 64}),
        "structural_budget_envelope": _budget_envelope() if budget_envelope is None else budget_envelope,
        "source_identity_envelope": cjson.envelope("source_identity", {"paths": ["research/brainvision/x"]}),
        "run1_structural_counters": run1, "run2_structural_counters": run1 if run2 is None else run2,
        "candidate_stream_envelope": stream_envelope, "failure_record": failure,
    }
    return cjson.envelope("generator_replay_result", payload)


def _failure(code, stage):
    return {"failure_code": code, "stage": stage, "ordered_failure_codes": [code]}


def _stub(monkeypatch, envelope, calls=None):
    def _call(profile_name, *args, **kwargs):
        if calls is not None:
            calls.append((profile_name, args, kwargs))
        return envelope
    monkeypatch.setattr(generator, "generate_candidate_stream_with_replay", _call)


def _run(tmp_path, monkeypatch, envelope, calls=None):
    _stub(monkeypatch, envelope, calls)
    out, err = io.StringIO(), io.StringIO()
    code = runner.run_operation(results_root=str(tmp_path), stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def _final(tmp_path):
    return os.path.join(str(tmp_path), runner.FINAL_DIRECTORY_NAME)


def _staging(tmp_path):
    return os.path.join(str(tmp_path), runner.STAGING_DIRECTORY_NAME)


def _published(tmp_path):
    return sorted(os.listdir(_final(tmp_path)))


def _read_bytes(tmp_path, filename):
    with open(os.path.join(_final(tmp_path), filename), "rb") as handle:
        return handle.read()


def _summary(tmp_path):
    return _read_bytes(tmp_path, runner.SUMMARY_FILENAME).decode("utf-8")


TWO_FILE_SET = sorted([runner.REPLAY_RESULT_FILENAME, runner.SUMMARY_FILENAME])
THREE_FILE_SET = sorted([runner.REPLAY_RESULT_FILENAME, runner.CANDIDATE_STREAM_FILENAME,
                         runner.SUMMARY_FILENAME])


# ----------------------------------------------------------------- sole generator call
def test_exactly_one_replay_call_with_primary_profile(tmp_path, monkeypatch):
    calls = []
    code, _out, _err = _run(tmp_path, monkeypatch, _replay_envelope(), calls)
    assert code == runner.EXIT_PUBLISHED
    assert len(calls) == 1
    assert calls[0] == ("PRIMARY_V0_1", (), {})           # no source-path or budget override is passed


def test_provisional_generator_entry_point_is_never_called(tmp_path, monkeypatch):
    code, _out, _err = _run(tmp_path, monkeypatch, _replay_envelope())
    assert code == runner.EXIT_PUBLISHED                   # autouse guard would have raised otherwise


def test_runner_source_has_no_provisional_call_site():
    with open(runner.__file__.replace(".pyc", ".py"), "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    replay_calls, provisional_calls = 0, 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        name = target.attr if isinstance(target, ast.Attribute) else (
            target.id if isinstance(target, ast.Name) else None)
        if name == "generate_candidate_stream_with_replay":
            replay_calls += 1
        elif name == "generate_candidate_stream":
            provisional_calls += 1
    assert replay_calls == 1                               # exactly one call site, not merely at most one
    assert provisional_calls == 0


# ----------------------------------------------------------------- successful publication
def test_stream_completed_publication(tmp_path, monkeypatch):
    code, out, err = _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    assert code == runner.EXIT_PUBLISHED and err == ""
    assert _published(tmp_path) == THREE_FILE_SET
    assert not os.path.exists(_staging(tmp_path))
    summary = _summary(tmp_path)
    assert "terminal_status = stream_completed" in summary
    assert "derived_termination_reason = DOMAIN_EXHAUSTED" in summary
    assert "candidate-stream artifact written = True" in summary
    assert out == summary                                   # stdout mirrors the summary exactly


def test_budget_exhausted_publication_records_ceiling(tmp_path, monkeypatch):
    counters = _counters(examined=999, emitted=MAX_RECORDS)
    envelope = _replay_envelope("budget_exhausted", run1=counters)
    code, _out, _err = _run(tmp_path, monkeypatch, envelope)
    assert code == runner.EXIT_PUBLISHED
    assert _published(tmp_path) == THREE_FILE_SET           # a prefix is retained, not discarded
    assert "derived_termination_reason = MAX_CANDIDATE_RECORDS_EMITTED" in _summary(tmp_path)


def test_budget_exhausted_tuple_ceiling(tmp_path, monkeypatch):
    counters = _counters(examined=MAX_TUPLES, emitted=17)
    code, _out, _err = _run(tmp_path, monkeypatch, _replay_envelope("budget_exhausted", run1=counters))
    assert code == runner.EXIT_PUBLISHED
    assert "derived_termination_reason = MAX_PARAMETER_TUPLES_EXAMINED" in _summary(tmp_path)


def test_record_ceiling_wins_when_both_ceilings_satisfied(tmp_path, monkeypatch):
    counters = _counters(examined=MAX_TUPLES, emitted=MAX_RECORDS)
    code, _out, _err = _run(tmp_path, monkeypatch, _replay_envelope("budget_exhausted", run1=counters))
    assert code == runner.EXIT_PUBLISHED
    assert "derived_termination_reason = MAX_CANDIDATE_RECORDS_EMITTED" in _summary(tmp_path)


def test_candidate_stream_artifact_is_the_verbatim_embedded_envelope(tmp_path, monkeypatch):
    records = _records(5)
    envelope = _replay_envelope("stream_completed", records=records)
    _run(tmp_path, monkeypatch, envelope)
    embedded = envelope["generator_replay_result"]["candidate_stream_envelope"]
    assert _read_bytes(tmp_path, runner.CANDIDATE_STREAM_FILENAME) == cjson.canonical_json_bytes(embedded)
    written = json.loads(_read_bytes(tmp_path, runner.CANDIDATE_STREAM_FILENAME).decode("utf-8"))
    assert written["candidate_stream"]["records"] == records      # not filtered, reordered, or rebuilt
    assert written["candidate_stream"]["candidate_count"] == 5


# ----------------------------------------------------------------- conditional extraction withheld
@pytest.mark.parametrize("kwargs,expected_marker", [
    ({"eligible": False, "terminal_status": "route_incomplete", "records": [],
      "failure": _failure("GENERATOR_COUNTER_INCONSISTENCY", "counters")},
     "derived_termination_reason = GENERATOR_COUNTER_INCONSISTENCY"),
    ({"eligible": False, "terminal_status": "dependency_unavailable", "records": [],
      "failure": _failure("GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE", "dependency_probe")},
     "derived_termination_reason = GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE"),
])
def test_zero_record_route_replays_publish_two_files(tmp_path, monkeypatch, kwargs, expected_marker):
    terminal = kwargs.pop("terminal_status")
    code, _out, _err = _run(tmp_path, monkeypatch, _replay_envelope(terminal, **kwargs))
    assert code == runner.EXIT_PUBLISHED                     # generator failure is not a runner failure
    assert _published(tmp_path) == TWO_FILE_SET
    summary = _summary(tmp_path)
    assert expected_marker in summary
    assert "candidate-stream artifact written = False" in summary


def test_pre_hash_null_stream_replay(tmp_path, monkeypatch):
    envelope = _replay_envelope(stream=False, authoritative=False, eligible=False, byte_identical=False,
                                failure=_failure("GENERATOR_CONFIGURATION_INVALID", "structural_budget"))
    code, _out, _err = _run(tmp_path, monkeypatch, envelope)
    assert code == runner.EXIT_PUBLISHED
    assert _published(tmp_path) == TWO_FILE_SET
    summary = _summary(tmp_path)
    assert "terminal_status = null" in summary
    assert "replay_failure_reason = GENERATOR_CONFIGURATION_INVALID" in summary
    assert "derived_termination_reason" not in summary       # the two labels are never both emitted
    assert "candidate_stream_sha256 = absent" in summary     # null envelope reports absent, not a zero hash


def test_replay_mismatch(tmp_path, monkeypatch):
    envelope = _replay_envelope(stream=False, authoritative=False, eligible=False, byte_identical=False,
                                failure=_failure("REPLAY_MISMATCH", "replay"))
    code, _out, _err = _run(tmp_path, monkeypatch, envelope)
    assert code == runner.EXIT_PUBLISHED
    assert _published(tmp_path) == TWO_FILE_SET
    assert "replay_failure_reason = REPLAY_MISMATCH" in _summary(tmp_path)


def test_embedded_zero_record_stream_is_not_promoted(tmp_path, monkeypatch):
    """A non-null zero-record stream inside a route-incomplete replay stays embedded only."""
    envelope = _replay_envelope("route_incomplete", records=[], eligible=False,
                                failure=_failure("GENERATOR_COUNTER_INCONSISTENCY", "counters"))
    _run(tmp_path, monkeypatch, envelope)
    assert runner.CANDIDATE_STREAM_FILENAME not in _published(tmp_path)
    written = json.loads(_read_bytes(tmp_path, runner.REPLAY_RESULT_FILENAME).decode("utf-8"))
    assert written["generator_replay_result"]["candidate_stream_envelope"] is not None


@pytest.mark.parametrize("field", ["authoritative_operation", "downstream_freeze_eligible", "byte_identical"])
def test_each_extraction_condition_is_checked_independently(tmp_path, monkeypatch, field):
    envelope = _replay_envelope("stream_completed")
    envelope["generator_replay_result"][field] = False        # deliberately inconsistent shape
    code, _out, _err = _run(tmp_path, monkeypatch, envelope)
    assert code == runner.EXIT_PUBLISHED
    assert _published(tmp_path) == TWO_FILE_SET


# ----------------------------------------------------------------- runner-level validation failures
def test_counter_mismatch_prevents_extraction(tmp_path, monkeypatch):
    envelope = _replay_envelope("stream_completed", run1=_counters(), run2=_counters(examined=13))
    code, _out, err = _run(tmp_path, monkeypatch, envelope)
    assert code == runner.EXIT_FAILURE                        # runner validation failed
    assert _published(tmp_path) == TWO_FILE_SET               # evidence is still retained
    summary = _summary(tmp_path)
    assert "runner_validation_failure = RUN1_RUN2_STRUCTURAL_COUNTER_MISMATCH" in summary
    assert "candidate-stream artifact written = False" in summary
    assert "RUN1_RUN2_STRUCTURAL_COUNTER_MISMATCH" in err
    assert "run1_parameter_tuples_examined = 12" in summary   # both runs reported independently
    assert "run2_parameter_tuples_examined = 13" in summary


_MALFORMED_COUNTERS = {
    "run1_missing_required_key": (
        {field: 1 for field in runner.COUNTER_FIELDS if field != "direct_tuples_found"}, None),
    "run2_extra_key": (None, dict({field: 1 for field in runner.COUNTER_FIELDS}, unexpected_field=0)),
    "bool_counter_value": (dict({field: 1 for field in runner.COUNTER_FIELDS},
                                direct_tuples_found=True), None),
    "non_integer_counter_value": (dict({field: 1 for field in runner.COUNTER_FIELDS},
                                       direct_tuples_found=1.0), None),
    "negative_counter_value": (dict({field: 1 for field in runner.COUNTER_FIELDS},
                                    direct_tuples_found=-1), None),
}


@pytest.mark.parametrize("case", sorted(_MALFORMED_COUNTERS))
def test_malformed_counters_block_extraction(tmp_path, monkeypatch, case):
    bad_run1, bad_run2 = _MALFORMED_COUNTERS[case]
    good = {field: 1 for field in runner.COUNTER_FIELDS}
    envelope = _replay_envelope("stream_completed", run1=bad_run1 if bad_run1 else good,
                                run2=bad_run2 if bad_run2 else (bad_run1 if bad_run1 else good))
    expected_bytes = cjson.canonical_json_bytes(envelope)
    code, _out, err = _run(tmp_path, monkeypatch, envelope)

    assert code == runner.EXIT_FAILURE
    assert os.path.isfile(os.path.join(_final(tmp_path), runner.REPLAY_RESULT_FILENAME))
    assert os.path.isfile(os.path.join(_final(tmp_path), runner.SUMMARY_FILENAME))
    assert not os.path.exists(os.path.join(_final(tmp_path), runner.CANDIDATE_STREAM_FILENAME))
    assert _published(tmp_path) == TWO_FILE_SET
    # the canonical replay artifact is retained byte-for-byte and was never mutated
    assert _read_bytes(tmp_path, runner.REPLAY_RESULT_FILENAME) == expected_bytes
    # the diagnostic lives only in human diagnostics, never in the canonical artifact
    assert runner.COUNTER_SHAPE_INVALID in _summary(tmp_path)
    assert runner.COUNTER_SHAPE_INVALID in err
    assert runner.COUNTER_SHAPE_INVALID.encode("ascii") not in expected_bytes
    assert b"runner_validation_failure" not in _read_bytes(tmp_path, runner.REPLAY_RESULT_FILENAME)


@pytest.mark.parametrize("counters,conforms", [
    ({field: 0 for field in runner.COUNTER_FIELDS}, True),
    ({field: 1 for field in runner.COUNTER_FIELDS if field != "direct_tuples_found"}, False),
    (dict({field: 1 for field in runner.COUNTER_FIELDS}, extra=1), False),
    (dict({field: 1 for field in runner.COUNTER_FIELDS}, direct_tuples_found=True), False),
    (dict({field: 1 for field in runner.COUNTER_FIELDS}, direct_tuples_found=1.0), False),
    (dict({field: 1 for field in runner.COUNTER_FIELDS}, direct_tuples_found=-1), False),
    ("not a mapping", False),
    (None, False),
])
def test_counter_mapping_schema(counters, conforms):
    assert runner.counter_mapping_conforms(counters) is conforms


def test_identically_malformed_counters_are_a_shape_failure_not_agreement():
    bad = {"parameter_tuples_examined": 1}
    payload = {"run1_structural_counters": bad, "run2_structural_counters": dict(bad)}
    assert runner.counter_validation_failure(payload) == runner.COUNTER_SHAPE_INVALID
    assert runner.counters_agree(payload) is False


def test_unresolved_derived_reason(tmp_path, monkeypatch):
    counters = _counters(examined=5, emitted=5)               # neither ceiling reached
    code, _out, err = _run(tmp_path, monkeypatch, _replay_envelope("budget_exhausted", run1=counters))
    assert code == runner.EXIT_FAILURE
    assert _published(tmp_path) == TWO_FILE_SET               # replay artifact retained
    summary = _summary(tmp_path)
    assert "derived_termination_reason = DERIVED_TERMINATION_REASON_UNRESOLVED" in summary
    assert "runner_validation_failure = DERIVED_TERMINATION_REASON_UNRESOLVED" in summary
    assert "DERIVED_TERMINATION_REASON_UNRESOLVED" in err


def test_unresolved_marker_never_enters_canonical_artifacts(tmp_path, monkeypatch):
    counters = _counters(examined=5, emitted=5)
    _run(tmp_path, monkeypatch, _replay_envelope("budget_exhausted", run1=counters))
    replay_bytes = _read_bytes(tmp_path, runner.REPLAY_RESULT_FILENAME)
    assert b"DERIVED_TERMINATION_REASON_UNRESOLVED" not in replay_bytes
    assert b"runner_validation_failure" not in replay_bytes
    assert b"exit" not in replay_bytes.lower().replace(b"existing", b"")


def test_missing_budget_envelope_yields_unresolved(tmp_path, monkeypatch):
    envelope = _replay_envelope("budget_exhausted")
    envelope["generator_replay_result"]["structural_budget_envelope"] = None
    code, _out, _err = _run(tmp_path, monkeypatch, envelope)
    assert code == runner.EXIT_FAILURE
    assert "structural_budget_sha256 = absent" in _summary(tmp_path)


# ----------------------------------------------------------------- pre-execution refusal
def test_refusal_when_final_directory_exists(tmp_path, monkeypatch):
    os.makedirs(_final(tmp_path))
    code, out, err = _run(tmp_path, monkeypatch, _replay_envelope())
    assert code == runner.EXIT_REFUSED
    assert out == "" and "final directory already exists" in err
    assert _published(tmp_path) == []                          # nothing was written into it


def test_refusal_when_staging_directory_exists(tmp_path, monkeypatch):
    os.makedirs(_staging(tmp_path))
    code, _out, err = _run(tmp_path, monkeypatch, _replay_envelope())
    assert code == runner.EXIT_REFUSED
    assert "staging directory already exists" in err
    assert os.path.isdir(_staging(tmp_path))                   # leftover staging keeps blocking


def test_refusal_occurs_before_the_replay_call(tmp_path, monkeypatch):
    os.makedirs(_final(tmp_path))
    calls = []
    code, _out, _err = _run(tmp_path, monkeypatch, _replay_envelope(), calls)
    assert code == runner.EXIT_REFUSED
    assert calls == []                                         # generator never contacted


def test_refusal_never_creates_a_staging_directory(tmp_path, monkeypatch):
    os.makedirs(_final(tmp_path))
    _run(tmp_path, monkeypatch, _replay_envelope())
    assert not os.path.exists(_staging(tmp_path))


# ----------------------------------------------------------------- canonical writing and hashes
def test_json_artifacts_are_canonical_with_no_trailing_newline(tmp_path, monkeypatch):
    _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    for filename in (runner.REPLAY_RESULT_FILENAME, runner.CANDIDATE_STREAM_FILENAME):
        raw = _read_bytes(tmp_path, filename)
        assert not raw.endswith(b"\n") and not raw.endswith(b"\r")
        assert b"\r\n" not in raw
        assert b": " not in raw and b", " not in raw          # compact separators, no pretty printing
        assert raw == cjson.canonical_json_bytes(json.loads(raw.decode("utf-8")))
        assert raw.decode("utf-8").isascii()                   # ensure_ascii=True


def test_replay_artifact_is_the_complete_returned_envelope(tmp_path, monkeypatch):
    envelope = _replay_envelope("stream_completed")
    _run(tmp_path, monkeypatch, envelope)
    assert _read_bytes(tmp_path, runner.REPLAY_RESULT_FILENAME) == cjson.canonical_json_bytes(envelope)
    written = json.loads(_read_bytes(tmp_path, runner.REPLAY_RESULT_FILENAME).decode("utf-8"))
    assert sorted(written) == ["generator_replay_result", "generator_replay_result_sha256"]


def test_whole_file_hashes_are_reported_for_written_artifacts(tmp_path, monkeypatch):
    _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    summary = _summary(tmp_path)
    for filename in (runner.REPLAY_RESULT_FILENAME, runner.CANDIDATE_STREAM_FILENAME):
        digest = runner.file_sha256(_read_bytes(tmp_path, filename))
        assert "  %s = %s" % (filename, digest) in summary


def test_absent_artifact_has_no_whole_file_hash_line(tmp_path, monkeypatch):
    envelope = _replay_envelope("route_incomplete", records=[], eligible=False,
                                failure=_failure("GENERATOR_COUNTER_INCONSISTENCY", "counters"))
    _run(tmp_path, monkeypatch, envelope)
    assert runner.CANDIDATE_STREAM_FILENAME not in _summary(tmp_path)


def test_payload_hash_and_file_hash_each_verify_against_their_own_byte_domain(tmp_path, monkeypatch):
    """Each hash is checked against its own defined byte domain. Equality is neither assumed nor excluded."""
    envelope = _replay_envelope("stream_completed")
    _run(tmp_path, monkeypatch, envelope)
    summary = _summary(tmp_path)
    stream_envelope = envelope["generator_replay_result"]["candidate_stream_envelope"]
    reported_payload_hash = stream_envelope["candidate_stream_sha256"]
    envelope_file_bytes = _read_bytes(tmp_path, runner.CANDIDATE_STREAM_FILENAME)

    # payload domain: canonical bytes of the inner candidate_stream payload only
    assert reported_payload_hash == cjson.payload_sha256(stream_envelope["candidate_stream"])
    assert reported_payload_hash == hashlib.sha256(
        cjson.canonical_json_bytes(stream_envelope["candidate_stream"])).hexdigest()

    # file domain: complete canonical envelope file bytes as written
    reported_file_hash = runner.file_sha256(envelope_file_bytes)
    assert reported_file_hash == hashlib.sha256(envelope_file_bytes).hexdigest()
    assert envelope_file_bytes == cjson.canonical_json_bytes(stream_envelope)

    # each value is reported under its own section, and neither is substituted for the other field
    assert "envelope payload hashes (SHA-256 over payload bytes only):" in summary
    assert "artifact file hashes (SHA-256 over complete file bytes; a different byte domain):" in summary
    assert "  candidate_stream_sha256 = %s" % reported_payload_hash in summary
    assert "  %s = %s" % (runner.CANDIDATE_STREAM_FILENAME, reported_file_hash) in summary


def test_replay_envelope_payload_hash_is_reported(tmp_path, monkeypatch):
    envelope = _replay_envelope("stream_completed")
    _run(tmp_path, monkeypatch, envelope)
    expected = envelope["generator_replay_result_sha256"]
    assert "  generator_replay_result_sha256 = %s" % expected in _summary(tmp_path)


# ----------------------------------------------------------------- summary properties
def test_summary_uses_lf_and_exactly_one_trailing_newline(tmp_path, monkeypatch):
    _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    raw = _read_bytes(tmp_path, runner.SUMMARY_FILENAME)
    assert b"\r" not in raw
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")


def test_summary_is_deterministic_across_runs(tmp_path, monkeypatch, tmp_path_factory):
    second_root = tmp_path_factory.mktemp("second")
    _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    _run(second_root, monkeypatch, _replay_envelope("stream_completed"))
    assert _read_bytes(tmp_path, runner.SUMMARY_FILENAME) == _read_bytes(second_root,
                                                                        runner.SUMMARY_FILENAME)


def test_summary_contains_no_nondeterministic_metadata(tmp_path, monkeypatch):
    _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    summary = _summary(tmp_path)
    assert str(tmp_path) not in summary                         # no temporary or absolute path
    assert os.getcwd() not in summary
    assert "\\" not in summary                                  # no Windows absolute path
    lowered = summary.lower()
    for banned in ("timestamp", "elapsed", "duration", "seconds", "hostname", "username", "pid",
                   "process", "memory", "/tmp", "c:/"):
        assert banned not in lowered
    # A numeric PID substring check is deliberately omitted: short PIDs occur by chance inside 64-hex
    # digests and produce false positives. Cross-run byte-identity is the real determinism guarantee and
    # is asserted separately in test_summary_is_deterministic_across_runs.


def test_summary_declares_closed_stages(tmp_path, monkeypatch):
    _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    summary = _summary(tmp_path)
    assert "freezer invoked = False" in summary
    assert "PsiTRS invoked = False" in summary
    assert "scientific interpretation performed = False" in summary
    assert "operator convenience only; not canonical generator evidence" in summary


def test_summary_reports_both_runs_complete_counters(tmp_path, monkeypatch):
    _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    summary = _summary(tmp_path)
    for field in runner.COUNTER_FIELDS:
        assert "run1_%s = " % field in summary
        assert "run2_%s = " % field in summary


# ----------------------------------------------------------------- atomic publication
def test_publication_is_a_single_rename_of_a_complete_staging_set(tmp_path, monkeypatch):
    observed = {}
    real_rename = runner.os.rename

    def _watch(src, dst):
        observed["staging_contents"] = sorted(os.listdir(src))
        observed["final_existed_before"] = os.path.exists(dst)
        return real_rename(src, dst)

    monkeypatch.setattr(runner.os, "rename", _watch)
    code, _out, _err = _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    assert code == runner.EXIT_PUBLISHED
    assert observed["staging_contents"] == THREE_FILE_SET       # complete set before publication
    assert observed["final_existed_before"] is False            # never overwrites


class _RaisingStream:
    def __init__(self, message="stream refused"):
        self.message = message

    def write(self, _text):
        raise OSError(self.message)


def test_stdout_failure_after_publication_preserves_evidence(tmp_path, monkeypatch):
    envelope = _replay_envelope("stream_completed")
    expected_replay = cjson.canonical_json_bytes(envelope)
    expected_stream = cjson.canonical_json_bytes(
        envelope["generator_replay_result"]["candidate_stream_envelope"])
    _stub(monkeypatch, envelope)
    err = io.StringIO()

    code = runner.run_operation(results_root=str(tmp_path), stdout=_RaisingStream(), stderr=err)

    assert code == runner.EXIT_FAILURE                          # no exception escaped
    assert os.path.isdir(_final(tmp_path))
    assert not os.path.exists(_staging(tmp_path))               # never re-staged or restored
    assert _published(tmp_path) == THREE_FILE_SET
    assert _read_bytes(tmp_path, runner.REPLAY_RESULT_FILENAME) == expected_replay
    assert _read_bytes(tmp_path, runner.CANDIDATE_STREAM_FILENAME) == expected_stream
    assert len(_summary(tmp_path)) > 0
    diagnostics = err.getvalue()
    assert "stdout mirroring failed after publication" in diagnostics
    assert "was not rolled back" in diagnostics


def test_stdout_and_stderr_both_failing_still_returns_exit_one(tmp_path, monkeypatch):
    envelope = _replay_envelope("stream_completed")
    _stub(monkeypatch, envelope)

    code = runner.run_operation(results_root=str(tmp_path), stdout=_RaisingStream("stdout refused"),
                                stderr=_RaisingStream("stderr refused"))

    assert code == runner.EXIT_FAILURE                          # a failing stderr never masks the contract
    assert _published(tmp_path) == THREE_FILE_SET               # published evidence survives intact


def test_stdout_is_not_written_before_publication(tmp_path, monkeypatch):
    observed = {}
    real_rename = runner.os.rename
    out = io.StringIO()

    def _watch(src, dst):
        observed["stdout_before_publication"] = out.getvalue()
        return real_rename(src, dst)

    monkeypatch.setattr(runner.os, "rename", _watch)
    _stub(monkeypatch, _replay_envelope("stream_completed"))
    code = runner.run_operation(results_root=str(tmp_path), stdout=out, stderr=io.StringIO())
    assert code == runner.EXIT_PUBLISHED
    assert observed["stdout_before_publication"] == ""
    assert out.getvalue() == _summary(tmp_path)


def test_publication_failure_leaves_no_final_directory(tmp_path, monkeypatch):
    def _fail(_src, _dst):
        raise OSError("rename refused")
    monkeypatch.setattr(runner.os, "rename", _fail)
    code, out, err = _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    assert code == runner.EXIT_FAILURE
    assert not os.path.exists(_final(tmp_path))
    assert not os.path.exists(_staging(tmp_path))               # staging cleaned
    assert "atomic publication failed" in err and out == ""


# ----------------------------------------------------------------- failure handling and cleanup
def test_unserializable_replay_result_fabricates_nothing(tmp_path, monkeypatch):
    code, out, err = _run(tmp_path, monkeypatch, {"generator_replay_result": {"bad": {1, 2}}})
    assert code == runner.EXIT_FAILURE
    assert not os.path.exists(_final(tmp_path)) and not os.path.exists(_staging(tmp_path))
    assert "not canonically serializable" in err and "no artifact fabricated" in err
    assert out == ""


def test_malformed_replay_envelope_fabricates_nothing(tmp_path, monkeypatch):
    code, _out, err = _run(tmp_path, monkeypatch, {"unexpected_key": 1})
    assert code == runner.EXIT_FAILURE
    assert not os.path.exists(_final(tmp_path)) and not os.path.exists(_staging(tmp_path))
    assert "no artifact fabricated" in err


def test_generator_call_raising_is_contained(tmp_path, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("unexpected generator explosion")
    monkeypatch.setattr(generator, "generate_candidate_stream_with_replay", _boom)
    out, err = io.StringIO(), io.StringIO()
    code = runner.run_operation(results_root=str(tmp_path), stdout=out, stderr=err)
    assert code == runner.EXIT_FAILURE
    assert not os.path.exists(_staging(tmp_path)) and not os.path.exists(_final(tmp_path))
    assert "generator replay call failed" in err.getvalue()


def test_cleanup_after_serialization_failure(tmp_path, monkeypatch):
    envelope = _replay_envelope("stream_completed")              # built BEFORE the serializer is patched
    calls = {"n": 0}
    real = runner.cjson.canonical_json_bytes

    def _fail_on_stream(value):
        calls["n"] += 1
        if calls["n"] >= 2:                                      # replay bytes succeed; stream bytes fail
            raise ValueError("stream not serializable")
        return real(value)

    monkeypatch.setattr(runner.cjson, "canonical_json_bytes", _fail_on_stream)
    code, _out, err = _run(tmp_path, monkeypatch, envelope)
    assert code == runner.EXIT_FAILURE
    assert not os.path.exists(_final(tmp_path))
    assert not os.path.exists(_staging(tmp_path))
    assert "artifact serialization failed" in err


def test_cleanup_after_write_failure(tmp_path, monkeypatch):
    def _fail(_path, _data):
        raise OSError("disk refused")
    monkeypatch.setattr(runner, "_write_bytes", _fail)
    code, _out, err = _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    assert code == runner.EXIT_FAILURE
    assert not os.path.exists(_final(tmp_path)) and not os.path.exists(_staging(tmp_path))
    assert "artifact write failed" in err


def test_cleanup_failure_is_reported_honestly(tmp_path, monkeypatch):
    def _fail_write(_path, _data):
        raise OSError("disk refused")

    def _fail_cleanup(_path):
        raise OSError("cleanup refused")

    monkeypatch.setattr(runner, "_write_bytes", _fail_write)
    monkeypatch.setattr(runner.shutil, "rmtree", _fail_cleanup)
    code, _out, err = _run(tmp_path, monkeypatch, _replay_envelope("stream_completed"))
    assert code == runner.EXIT_FAILURE
    assert "staging cleanup failed" in err
    assert "will block future execution" in err
    assert os.path.isdir(_staging(tmp_path))                    # retained, and it blocks the next run
    assert not os.path.exists(_final(tmp_path))


def test_retained_staging_blocks_the_next_run(tmp_path, monkeypatch):
    os.makedirs(_staging(tmp_path))
    calls = []
    code, _out, _err = _run(tmp_path, monkeypatch, _replay_envelope(), calls)
    assert code == runner.EXIT_REFUSED and calls == []


# ----------------------------------------------------------------- CLI surface
def test_main_rejects_any_argument(capsys):
    for argv in (["prog", "--profile", "TEST_TINY_V0_1"], ["prog", "--out", "x"], ["prog", "extra"]):
        assert runner.main(argv) == runner.EXIT_FAILURE         # never reaches run_operation
    assert "takes no arguments" in capsys.readouterr().err


def test_runner_exposes_no_cli_parser():
    assert not hasattr(runner, "argparse")
    with open(runner.__file__.replace(".pyc", ".py"), "r", encoding="utf-8") as handle:
        source = handle.read()
    assert "add_argument" not in source
    assert "os.environ" not in source and "getenv" not in source


def test_exit_code_constants_are_the_documented_contract():
    assert (runner.EXIT_PUBLISHED, runner.EXIT_FAILURE, runner.EXIT_REFUSED) == (0, 1, 2)


# ----------------------------------------------------------------- independence
_FORBIDDEN_ROOTS = {"witness_family_verifier_v0_1", "witness_family_freeze_v0_1", "psi_trs", "descriptors",
                    "symmetry_gain", "real_video", "run_n64_falsifier_v0_1", "n64_falsifier_fixture_v0_1",
                    "run_prerecorded_paired_analysis_v0_1", "run_prerecorded_operational_harness_v0_1",
                    "torment_service", "subprocess", "socket", "urllib", "requests", "http", "numpy",
                    "multiprocessing", "threading", "ctypes"}


def _import_roots(path):
    with open(path, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            roots.add(node.module.split(".")[0])
    return roots


def test_runner_imports_are_bounded():
    roots = _import_roots(runner.__file__.replace(".pyc", ".py"))
    assert roots.isdisjoint(_FORBIDDEN_ROOTS)
    assert roots.issubset({"__future__", "hashlib", "os", "shutil", "sys", "typing",
                           "algebraic_direct_sum_n64_candidate_generator_v0_1",
                           "witness_canonical_json_v0_1"})


def test_runner_makes_no_dynamic_import_or_process_calls():
    with open(runner.__file__.replace(".pyc", ".py"), "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    watched = {"__import__", "import_module", "exec", "eval", "compile", "popen", "system", "Popen",
               "check_output", "urlopen", "socket", "spawn"}
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            name = target.id if isinstance(target, ast.Name) else (
                target.attr if isinstance(target, ast.Attribute) else None)
            if name in watched:
                found.add(name)
    assert found == set()


def test_runner_performs_no_witness_mathematics():
    for banned in ("autocorrelation", "triple_array", "primitive_period", "affine_apply",
                   "member_g_equivalence_key", "transition_multiset", "one_step_table", "verify_candidate",
                   "freeze", "freeze_with_replay"):
        assert not hasattr(runner, banned)


def test_real_results_directory_is_untouched_by_this_suite():
    """The default root resolves inside the repository, and no test ever publishes into it."""
    assert runner.default_results_root().endswith(os.path.join("research", "brainvision", "results"))
    assert not os.path.exists(os.path.join(runner.default_results_root(), runner.FINAL_DIRECTORY_NAME))
    assert not os.path.exists(os.path.join(runner.default_results_root(), runner.STAGING_DIRECTORY_NAME))
