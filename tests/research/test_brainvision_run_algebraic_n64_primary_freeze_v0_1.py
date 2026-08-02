"""Tests for the algebraic N=64 PRIMARY_V0_1 freezer runner v0.1 (offline; implementation verification only).

These tests NEVER invoke the real freezer and NEVER read the real retained candidate stream or real result
paths. An autouse fixture replaces both freezer entry points with guards that raise on contact; each test that
needs a result explicitly installs a synthetic stub for freeze_with_replay only. Every test operates on a
temporary git repository built from the committed verifier/serializer/freezer source bytes (so their Git blob
identities equal the runner's frozen constants) plus a small synthetic candidate-stream fixture, and publishes
into a temporary result root outside that repository.
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
import witness_family_freeze_v0_1 as freezer  # noqa: E402
import run_algebraic_n64_primary_freeze_v0_1 as runner  # noqa: E402

SOURCE_MODULE_FILES = {
    "verifier": "witness_family_verifier_v0_1.py",
    "serializer": "witness_canonical_json_v0_1.py",
    "freeze": "witness_family_freeze_v0_1.py",
}


# --------------------------------------------------------------- synthetic candidate-stream fixture
def _records(count):
    out = []
    for index in range(count):
        out.append({"raw_support_A": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                    "raw_support_B": [0, 1, 2, 55, 56, 57, 58, 59, 60, 61, 62, 63],
                    "candidate_generation_index": index,
                    "generator_diagnostics": {"parameter_tuple_index": index, "U": [0, 1, 2],
                                              "V": [0, 3, 6, 9], "sum_directness_count": 12,
                                              "difference_directness_count": 12,
                                              "exact_duplicate_count_before_emission": 0}})
    return out


@pytest.fixture(scope="session")
def stream_fixture():
    payload = {"schema_name": "brainvision_descriptor_blind_candidate_stream", "schema_version": "0.1",
               "verification_mode": "PRIMARY_CANDIDATE_N64", "N": 64,
               "generator_identity_hash": "a" * 64, "generator_configuration_hash": "b" * 64,
               "budget_identity_hash": "c" * 64, "terminal_status": "budget_exhausted",
               "candidate_count": 3, "records": _records(3)}
    envelope = cjson.envelope("candidate_stream", payload)
    stream_bytes = cjson.canonical_json_bytes(envelope)
    return {"bytes": stream_bytes, "envelope": envelope, "count": 3,
            "whole_sha": hashlib.sha256(stream_bytes).hexdigest(),
            "payload_sha": envelope["candidate_stream_sha256"]}


# --------------------------------------------------------------- temp repository builder
def _run_git(root, *args):
    subprocess.run(["git", "-C", root, *args], check=True, capture_output=True, text=True)


def _build_repo(root, stream_bytes):
    """Build a clean git repo on branch main with committed sources + runner stub + gitignored input."""
    bv = os.path.join(root, "research", "brainvision")
    results = os.path.join(bv, "results", "algebraic_n64_primary_v0_1")
    os.makedirs(results)
    for role, filename in SOURCE_MODULE_FILES.items():
        with open(os.path.join(BV_DIR, filename), "rb") as handle:
            data = handle.read()
        with open(os.path.join(bv, filename), "wb") as handle:
            handle.write(data)
    # stub runner file at the exact expected runner path (regular file; content irrelevant to source binding)
    with open(os.path.join(bv, "run_algebraic_n64_primary_freeze_v0_1.py"), "wb") as handle:
        handle.write(b"# stub runner marker\n")
    with open(os.path.join(root, ".gitignore"), "wb") as handle:
        handle.write(b"research/brainvision/results/\n")
    # ignored local evidence: the candidate stream lives under results/
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
    root = str(tmp_path_factory.mktemp("freezerepo"))
    return _build_repo(root, stream_fixture["bytes"])


@pytest.fixture(autouse=True)
def _bind_constants(monkeypatch, stream_fixture):
    """Bind the frozen INPUT constants to the synthetic fixture so the real 20000-record stream is never used."""
    monkeypatch.setattr(runner, "INPUT_EXPECTED_SIZE", len(stream_fixture["bytes"]))
    monkeypatch.setattr(runner, "INPUT_WHOLE_FILE_SHA256", stream_fixture["whole_sha"])
    monkeypatch.setattr(runner, "INPUT_PAYLOAD_SHA256", stream_fixture["payload_sha"])
    monkeypatch.setattr(runner, "STREAM_CANDIDATE_COUNT", stream_fixture["count"])


@pytest.fixture(autouse=True)
def _forbid_real_freeze(monkeypatch):
    def _replay_guard(*_a, **_k):
        raise AssertionError("real freeze_with_replay contacted")

    def _freeze_guard(*_a, **_k):
        raise AssertionError("freeze contacted")
    monkeypatch.setattr(freezer, "freeze_with_replay", _replay_guard)
    monkeypatch.setattr(freezer, "freeze", _freeze_guard)


@pytest.fixture
def results_root(tmp_path):
    return os.path.join(str(tmp_path), "external_results")


# --------------------------------------------------------------- freeze-result builders (synthetic)
def _source_identities(source_paths):
    identities = {}
    for role, path in source_paths.items():
        with open(path, "rb") as handle:
            identities[role + "_source_sha256"] = hashlib.sha256(handle.read()).hexdigest()
        identities[role + "_source_path"] = "research/brainvision/" + os.path.basename(path)
    return identities


def _base_freeze_payload(head, source_paths, payload_sha):
    return {
        "schema_name": "brainvision_witness_freeze_result", "schema_version": "0.1",
        "verification_mode": "PRIMARY_CANDIDATE_N64", "N": 64,
        "candidate_stream_sha256": payload_sha, "candidate_count": 3,
        "terminal_stream_status": "budget_exhausted", "authoritative_operation": True,
        "resource_policy_status": "UNBOUNDED_BY_V0_1_SPECIFICATION",
        "replay_record": {"run1_sha256": "d" * 64, "run2_sha256": "d" * 64, "byte_identical": True},
        "local_source_identities": _source_identities(source_paths),
        "verifier_configuration_sha256": "e" * 64,
        "candidate_decision_ledger_sha256": "f" * 64,
        "accepted_candidate_indices": [], "accepted_pair_certificate_envelopes": [],
        "family_certificate": None, "family_manifest": None,
        "family_frozen": False, "failure_record": None,
    }


def _positive(head, source_paths, payload_sha):
    payload = _base_freeze_payload(head, source_paths, payload_sha)
    manifest_payload = {"schema_name": "brainvision_witness_family_manifest", "schema_version": "0.1",
                        "repository_commit_identity": head, "candidate_stream_sha256": payload_sha, "K": 3}
    payload["family_manifest"] = cjson.envelope("family_manifest", manifest_payload)
    payload["family_frozen"] = True
    payload["accepted_candidate_indices"] = [0, 1, 2]
    payload["accepted_pair_certificate_envelopes"] = [{"x": 1}, {"x": 2}, {"x": 3}]
    return cjson.envelope("freeze_result", payload)


def _valid_negative(head, source_paths, payload_sha, code="FAMILY_NOT_FREEZABLE"):
    payload = _base_freeze_payload(head, source_paths, payload_sha)
    payload["failure_record"] = {"failure_code": code, "stage": "family_selection",
                                 "ordered_failure_codes": [code]}
    return cjson.envelope("freeze_result", payload)


def _execution_invalid(head, source_paths, payload_sha, code="REPLAY_MISMATCH"):
    payload = _base_freeze_payload(head, source_paths, payload_sha)
    payload["failure_record"] = {"failure_code": code, "stage": "replay", "ordered_failure_codes": [code]}
    return cjson.envelope("freeze_result", payload)


def _install(monkeypatch, builder, calls=None):
    def _stub(candidate_stream_envelope, repository_commit_identity, source_paths):
        if calls is not None:
            calls.append({"env": candidate_stream_envelope, "head": repository_commit_identity,
                          "source_paths": dict(source_paths)})
        return builder(repository_commit_identity, source_paths)
    monkeypatch.setattr(freezer, "freeze_with_replay", _stub)


def _run(clean_repo, results_root, monkeypatch, builder, calls=None):
    payload_sha = runner.INPUT_PAYLOAD_SHA256
    _install(monkeypatch, lambda head, sp: builder(head, sp, payload_sha), calls)
    out, err = io.StringIO(), io.StringIO()
    code = runner.run_operation(repository_root=clean_repo, results_root=results_root, stdout=out, stderr=err)
    return code, out.getvalue(), err.getvalue()


def _final(results_root):
    return os.path.join(results_root, runner.FINAL_DIRECTORY_NAME)


def _staging(results_root):
    return os.path.join(results_root, runner.STAGING_DIRECTORY_NAME)


def _published(results_root):
    return sorted(os.listdir(_final(results_root)))


TWO_FILE_SET = sorted([runner.RESULT_FILENAME, runner.SUMMARY_FILENAME])


# ============================================================= positive / negative / execution-invalid
def test_positive_publishes_and_exits_zero(clean_repo, results_root, monkeypatch):
    calls = []
    code, out, err = _run(clean_repo, results_root, monkeypatch, _positive, calls)
    assert code == runner.EXIT_PUBLISHED
    assert _published(results_root) == TWO_FILE_SET
    assert not os.path.exists(_staging(results_root))
    assert len(calls) == 1                                          # exactly one freezer call
    assert isinstance(calls[0]["head"], str) and len(calls[0]["head"]) == 40
    assert set(calls[0]["source_paths"]) == {"verifier", "serializer", "freeze"}
    with open(os.path.join(_final(results_root), runner.SUMMARY_FILENAME)) as handle:
        summary = handle.read()
    assert "family_frozen = True" in summary
    assert "freezer invoked = True" in summary
    assert "outer replay performed = False" in summary
    assert out == summary


def test_result_artifact_is_exact_canonical_returned_object(clean_repo, results_root, monkeypatch):
    captured = {}

    def _builder(head, sp, payload_sha):
        env = _positive(head, sp, payload_sha)
        captured["env"] = env
        return env
    _install(monkeypatch, lambda head, sp: _builder(head, sp, runner.INPUT_PAYLOAD_SHA256))
    runner.run_operation(repository_root=clean_repo, results_root=results_root,
                         stdout=io.StringIO(), stderr=io.StringIO())
    with open(os.path.join(_final(results_root), runner.RESULT_FILENAME), "rb") as handle:
        written = handle.read()
    assert written == cjson.canonical_json_bytes(captured["env"])   # exact bytes, no runner fields added
    assert not written.endswith(b"\n")


def test_valid_negative_exits_zero_and_preserves_greedy_language(clean_repo, results_root, monkeypatch):
    code, out, err = _run(clean_repo, results_root, monkeypatch, _valid_negative)
    assert code == runner.EXIT_PUBLISHED
    assert _published(results_root) == TWO_FILE_SET
    with open(os.path.join(_final(results_root), runner.SUMMARY_FILENAME)) as handle:
        summary = handle.read()
    assert "classification = VALID_NEGATIVE" in summary
    assert "greedy non-backtracking first-fit" in summary
    assert "FAMILY_NOT_FREEZABLE" in summary
    assert err == ""                                                # a normal negative writes no stderr


def test_execution_invalid_result_publishes_but_exits_one(clean_repo, results_root, monkeypatch):
    code, out, err = _run(clean_repo, results_root, monkeypatch, _execution_invalid)
    assert code == runner.EXIT_FAILURE
    assert _published(results_root) == TWO_FILE_SET                 # retained and published
    assert "execution-invalid freezer result REPLAY_MISMATCH" in err
    with open(os.path.join(_final(results_root), runner.SUMMARY_FILENAME)) as handle:
        summary = handle.read()
    assert "classification = EXECUTION_INVALID" in summary


@pytest.mark.parametrize("failure_code", sorted(runner.EXECUTION_INVALID_CODES))
def test_all_execution_invalid_codes_exit_one(clean_repo, results_root, monkeypatch, failure_code):
    rc, _out, _err = _run(clean_repo, results_root, monkeypatch,
                          lambda h, sp, ps: _execution_invalid(h, sp, ps, failure_code))
    assert rc == runner.EXIT_FAILURE
    assert _published(results_root) == TWO_FILE_SET                 # exact canonical result published
    with open(os.path.join(_final(results_root), runner.SUMMARY_FILENAME)) as handle:
        summary = handle.read()
    assert "classification = EXECUTION_INVALID" in summary
    assert "failure_code = %s" % failure_code in summary


# ============================================================= runner-invalid canonical results
def test_runner_invalid_result_retained_and_published_exit_one(clean_repo, results_root, monkeypatch):
    def _broken(head, sp, payload_sha):
        env = _positive(head, sp, payload_sha)
        env["freeze_result"]["accepted_candidate_indices"] = [0, 1]   # only 2, not K=3
        return cjson.envelope("freeze_result", env["freeze_result"])
    code, out, err = _run(clean_repo, results_root, monkeypatch, _broken)
    assert code == runner.EXIT_FAILURE
    assert _published(results_root) == TWO_FILE_SET                 # runner-invalid is still published
    assert "RESULT_RUNNER_INVALID" in err
    with open(os.path.join(_final(results_root), runner.SUMMARY_FILENAME)) as handle:
        summary = handle.read()
    assert "classification = RUNNER_INVALID" in summary
    assert "runner_validation_failure = POSITIVE_ACCEPTED_INDEX_COUNT" in summary


def test_unbound_source_hash_is_runner_invalid(clean_repo, results_root, monkeypatch):
    def _tampered(head, sp, payload_sha):
        env = _valid_negative(head, sp, payload_sha)
        env["freeze_result"]["local_source_identities"]["verifier_source_sha256"] = "0" * 64
        return cjson.envelope("freeze_result", env["freeze_result"])
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _tampered)
    assert code == runner.EXIT_FAILURE
    assert "SOURCE_SHA256_UNBOUND:verifier" in err


def test_wrong_stream_hash_binding_is_runner_invalid(clean_repo, results_root, monkeypatch):
    def _tampered(head, sp, payload_sha):
        env = _valid_negative(head, sp, payload_sha)
        env["freeze_result"]["candidate_stream_sha256"] = "1" * 64
        return cjson.envelope("freeze_result", env["freeze_result"])
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _tampered)
    assert code == runner.EXIT_FAILURE
    assert "FIELD_MISMATCH:candidate_stream_sha256" in err


def test_result_payload_hash_mismatch_is_runner_invalid(clean_repo, results_root, monkeypatch):
    def _tampered(head, sp, payload_sha):
        env = _valid_negative(head, sp, payload_sha)
        env["freeze_result"]["family_frozen"] = False               # mutate payload after hash computed
        env["freeze_result"]["extra"] = "drift"
        return env                                                  # hash no longer matches payload
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _tampered)
    assert code == runner.EXIT_FAILURE
    assert "RESULT_PAYLOAD_HASH_MISMATCH" in err


# ------------------------- false-result structural validation (never a valid negative by mere presence) -----
def _negative_with(head, source_paths, payload_sha, *, failure_record, byte_identical=True,
                   family_manifest=None):
    payload = _base_freeze_payload(head, source_paths, payload_sha)
    payload["failure_record"] = failure_record
    payload["family_manifest"] = family_manifest
    payload["replay_record"] = {"run1_sha256": "d" * 64, "run2_sha256": "d" * 64,
                                "byte_identical": byte_identical}
    return cjson.envelope("freeze_result", payload)  # re-wrap so the payload hash stays consistent


_FALSE_RESULT_RUNNER_INVALID_CASES = {
    "empty_failure_record": (dict(failure_record={}), "NEGATIVE_FAILURE_CODE_INVALID"),
    "missing_failure_code": (dict(failure_record={"stage": "s", "ordered_failure_codes": ["X"]}),
                             "NEGATIVE_FAILURE_CODE_INVALID"),
    "missing_stage": (dict(failure_record={"failure_code": "X", "ordered_failure_codes": ["X"]}),
                      "NEGATIVE_STAGE_INVALID"),
    "missing_ordered": (dict(failure_record={"failure_code": "X", "stage": "s"}),
                        "NEGATIVE_ORDERED_CODES_INVALID"),
    "ordered_not_a_list": (dict(failure_record={"failure_code": "X", "stage": "s",
                                                "ordered_failure_codes": "X"}),
                           "NEGATIVE_ORDERED_CODES_INVALID"),
    "ordered_non_string_item": (dict(failure_record={"failure_code": "X", "stage": "s",
                                                     "ordered_failure_codes": [1]}),
                                "NEGATIVE_ORDERED_CODES_INVALID"),
    "code_absent_from_ordered": (dict(failure_record={"failure_code": "X", "stage": "s",
                                                      "ordered_failure_codes": ["Y"]}),
                                 "NEGATIVE_FAILURE_CODE_NOT_IN_ORDERED"),
    "non_execinvalid_but_replay_false": (dict(
        failure_record={"failure_code": "FAMILY_NOT_FREEZABLE", "stage": "family_selection",
                        "ordered_failure_codes": ["FAMILY_NOT_FREEZABLE"]}, byte_identical=False),
        "NEGATIVE_REPLAY_NOT_IDENTICAL"),
}


@pytest.mark.parametrize("case", sorted(_FALSE_RESULT_RUNNER_INVALID_CASES))
def test_false_result_structural_failures_are_runner_invalid(clean_repo, results_root, monkeypatch, case):
    kwargs, marker = _FALSE_RESULT_RUNNER_INVALID_CASES[case]
    code, _out, err = _run(clean_repo, results_root, monkeypatch,
                           lambda h, sp, ps: _negative_with(h, sp, ps, **kwargs))
    assert code == runner.EXIT_FAILURE
    assert _published(results_root) == TWO_FILE_SET                 # exact canonical result still published
    with open(os.path.join(_final(results_root), runner.SUMMARY_FILENAME)) as handle:
        summary = handle.read()
    assert "classification = RUNNER_INVALID" in summary
    assert "runner_validation_failure = %s" % marker in summary


def test_positive_with_non_mapping_manifest_payload_is_runner_invalid(clean_repo, results_root, monkeypatch):
    def _bad_manifest(head, sp, payload_sha):
        payload = _base_freeze_payload(head, sp, payload_sha)
        payload["family_frozen"] = True
        payload["accepted_candidate_indices"] = [0, 1, 2]
        payload["accepted_pair_certificate_envelopes"] = [{"x": 1}, {"x": 2}, {"x": 3}]
        # correctly hashed, but the manifest payload is a string, not a mapping
        payload["family_manifest"] = cjson.envelope("family_manifest", "not a mapping")
        return cjson.envelope("freeze_result", payload)
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _bad_manifest)
    assert code == runner.EXIT_FAILURE
    assert _published(results_root) == TWO_FILE_SET
    with open(os.path.join(_final(results_root), runner.SUMMARY_FILENAME)) as handle:
        summary = handle.read()
    assert "classification = RUNNER_INVALID" in summary
    assert "runner_validation_failure = POSITIVE_MANIFEST_PAYLOAD_NOT_MAPPING" in summary


# ============================================================= unserializable / exception
def test_unserializable_return_is_not_published(clean_repo, results_root, monkeypatch):
    def _bad(head, sp):
        return {"freeze_result": {"unserializable": {1, 2, 3}}, "freeze_result_sha256": "z" * 64}
    monkeypatch.setattr(freezer, "freeze_with_replay",
                        lambda env, repository_commit_identity, source_paths: _bad(repository_commit_identity,
                                                                                   source_paths))
    out, err = io.StringIO(), io.StringIO()
    code = runner.run_operation(repository_root=clean_repo, results_root=results_root, stdout=out, stderr=err)
    assert code == runner.EXIT_FAILURE
    assert not os.path.exists(_final(results_root))
    assert not os.path.exists(_staging(results_root))              # empty staging removed
    assert "RESULT_NOT_SERIALIZABLE" in err.getvalue() and out.getvalue() == ""


def test_freezer_exception_contained_no_retry(clean_repo, results_root, monkeypatch):
    calls = {"n": 0}

    def _boom(env, repository_commit_identity, source_paths):
        calls["n"] += 1
        raise RuntimeError("freezer exploded")
    monkeypatch.setattr(freezer, "freeze_with_replay", _boom)
    out, err = io.StringIO(), io.StringIO()
    code = runner.run_operation(repository_root=clean_repo, results_root=results_root, stdout=out, stderr=err)
    assert code == runner.EXIT_FAILURE
    assert calls["n"] == 1                                          # no automatic retry
    assert not os.path.exists(_final(results_root))
    assert not os.path.exists(_staging(results_root))              # empty staging removed
    assert "FREEZER_CALL_EXCEPTION" in err.getvalue()


# ============================================================= staging / publication failures
def test_rename_failure_retains_staging(clean_repo, results_root, monkeypatch):
    def _fail(_src, _dst):
        raise OSError("rename refused")
    monkeypatch.setattr(runner.os, "rename", _fail)
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _positive)
    assert code == runner.EXIT_FAILURE
    assert not os.path.exists(_final(results_root))
    assert os.path.isdir(_staging(results_root))                   # staging with evidence retained
    assert sorted(os.listdir(_staging(results_root))) == TWO_FILE_SET
    assert "publication rename failed" in err


def test_stdout_failure_after_publication_preserves_final(clean_repo, results_root, monkeypatch):
    class _Raising:
        def write(self, _t):
            raise OSError("stdout refused")
    payload_sha = runner.INPUT_PAYLOAD_SHA256
    _install(monkeypatch, lambda head, sp: _positive(head, sp, payload_sha))
    err = io.StringIO()
    code = runner.run_operation(repository_root=clean_repo, results_root=results_root,
                                stdout=_Raising(), stderr=err)
    assert code == runner.EXIT_FAILURE
    assert _published(results_root) == TWO_FILE_SET                 # final intact, not rolled back
    assert not os.path.exists(_staging(results_root))
    assert "stdout mirroring failed after publication" in err.getvalue()


def test_never_overwrites_existing_final(clean_repo, results_root, monkeypatch):
    os.makedirs(_final(results_root))
    calls = []
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _positive, calls)
    assert code == runner.EXIT_REFUSED                             # final exists -> pre-contact refusal
    assert calls == []                                             # freezer never contacted
    assert "FINAL_DIRECTORY_EXISTS" in err


def test_preexisting_staging_is_refusal_not_deleted(clean_repo, results_root, monkeypatch):
    os.makedirs(_staging(results_root))
    marker = os.path.join(_staging(results_root), "keep.txt")
    open(marker, "w").close()
    calls = []
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _positive, calls)
    assert code == runner.EXIT_REFUSED
    assert calls == []
    assert os.path.exists(marker)                                  # not auto-deleted
    assert "STAGING_DIRECTORY_EXISTS" in err


# ============================================================= CLI refusal
def test_main_rejects_any_argument(capsys):
    for argv in (["prog", "--input", "x"], ["prog", "extra"], ["prog", "--help"]):
        assert runner.main(argv) == runner.EXIT_REFUSED
    assert "takes no arguments" in capsys.readouterr().err


def test_run_operation_rejects_extra_arguments(clean_repo, results_root):
    err = io.StringIO()
    code = runner.run_operation(repository_root=clean_repo, results_root=results_root,
                                extra_arguments=["--x"], stdout=io.StringIO(), stderr=err)
    assert code == runner.EXIT_REFUSED and "takes no arguments" in err.getvalue()


# ============================================================= repository pre-contact refusals
def test_dirty_tree_refuses(tmp_path, stream_fixture, results_root, monkeypatch):
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    with open(os.path.join(root, "research", "brainvision", "witness_family_verifier_v0_1.py"), "ab") as handle:
        handle.write(b"\n# dirty\n")                               # modify a tracked file
    calls = []
    code, _out, err = _run(root, results_root, monkeypatch, _positive, calls)
    assert code == runner.EXIT_REFUSED
    assert calls == []
    assert "WORKING_TREE_NOT_CLEAN" in err


def test_origin_mismatch_refuses(tmp_path, stream_fixture, results_root, monkeypatch):
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    # advance HEAD so origin/main no longer equals HEAD
    with open(os.path.join(root, "extra.txt"), "w") as handle:
        handle.write("x")
    _run_git(root, "add", "-A")
    _run_git(root, "commit", "-q", "-m", "advance")
    code, _out, err = _run(root, results_root, monkeypatch, _positive)
    assert code == runner.EXIT_REFUSED
    assert "ORIGIN_MAIN_MISMATCH" in err


def test_wrong_branch_refuses(tmp_path, stream_fixture, results_root, monkeypatch):
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    _run_git(root, "branch", "-m", "main", "other")
    _run_git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    code, _out, err = _run(root, results_root, monkeypatch, _positive)
    assert code == runner.EXIT_REFUSED
    assert "BRANCH_NOT_MAIN" in err


def test_source_blob_identity_mismatch_refuses(tmp_path, stream_fixture, results_root, monkeypatch):
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    monkeypatch.setattr(runner, "FROZEN_SOURCE_BLOB_IDS",
                        dict(runner.FROZEN_SOURCE_BLOB_IDS, verifier="0" * 40))
    calls = []
    code, _out, err = _run(root, results_root, monkeypatch, _positive, calls)
    assert code == runner.EXIT_REFUSED
    assert calls == []
    assert "SOURCE_BLOB_IDENTITY_MISMATCH" in err


def test_source_bytes_differ_from_commit_refuses(clean_repo, results_root, monkeypatch, tmp_path,
                                                 stream_fixture):
    # a fresh repo whose on-disk source differs from the committed blob (simulated via committed-then-edited)
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    path = os.path.join(root, "research", "brainvision", "witness_canonical_json_v0_1.py")
    with open(path, "rb") as handle:
        data = handle.read()
    # edit working copy only, then restage nothing; but that dirties the tree, so instead swap after add.
    # Simplest deterministic route: leave tree clean but point blob check to a real id while bytes changed
    # is covered by the blob-id test; here assert byte-equality path via a targeted monkeypatch.
    original = runner._git_blob_bytes

    def _mutated(repo, blob):
        return (original(repo, blob) or b"") + b"X"                 # committed bytes appear to differ
    monkeypatch.setattr(runner, "_git_blob_bytes", _mutated)
    code, _out, err = _run(root, results_root, monkeypatch, _positive)
    assert code == runner.EXIT_REFUSED
    assert "SOURCE_BYTES_DIFFER_FROM_COMMIT" in err


# ============================================================= input pre-contact refusals
def test_input_size_mismatch_refuses(clean_repo, results_root, monkeypatch):
    monkeypatch.setattr(runner, "INPUT_EXPECTED_SIZE", 123)
    calls = []
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _positive, calls)
    assert code == runner.EXIT_REFUSED
    assert calls == []
    assert "INPUT_SIZE_MISMATCH" in err


def test_input_whole_file_hash_mismatch_refuses(clean_repo, results_root, monkeypatch):
    monkeypatch.setattr(runner, "INPUT_WHOLE_FILE_SHA256", "9" * 64)
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _positive)
    assert code == runner.EXIT_REFUSED
    assert "INPUT_WHOLE_FILE_HASH_MISMATCH" in err


def test_input_payload_hash_mismatch_refuses(clean_repo, results_root, monkeypatch):
    monkeypatch.setattr(runner, "INPUT_PAYLOAD_SHA256", "8" * 64)
    code, _out, err = _run(clean_repo, results_root, monkeypatch, _positive)
    assert code == runner.EXIT_REFUSED
    assert "INPUT_PAYLOAD_HASH" in err


def test_duplicate_json_keys_rejected(tmp_path, stream_fixture, results_root, monkeypatch):
    # craft an input whose bytes carry a duplicate key while still matching a patched size/hash
    dup = b'{"candidate_stream":{},"candidate_stream":{},"candidate_stream_sha256":"' + b"7" * 64 + b'"}'
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    input_path = os.path.join(root, "research", "brainvision", "results", "algebraic_n64_primary_v0_1",
                              "algebraic_n64_primary_v0_1_candidate_stream.json")
    with open(input_path, "wb") as handle:
        handle.write(dup)
    monkeypatch.setattr(runner, "INPUT_EXPECTED_SIZE", len(dup))
    monkeypatch.setattr(runner, "INPUT_WHOLE_FILE_SHA256", hashlib.sha256(dup).hexdigest())
    code, _out, err = _run(root, results_root, monkeypatch, _positive)
    assert code == runner.EXIT_REFUSED
    assert "INPUT_JSON_INVALID" in err


def test_nonfinite_json_rejected(tmp_path, stream_fixture, results_root, monkeypatch):
    bad = b'{"candidate_stream":{"x":NaN},"candidate_stream_sha256":"' + b"7" * 64 + b'"}'
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    input_path = os.path.join(root, "research", "brainvision", "results", "algebraic_n64_primary_v0_1",
                              "algebraic_n64_primary_v0_1_candidate_stream.json")
    with open(input_path, "wb") as handle:
        handle.write(bad)
    monkeypatch.setattr(runner, "INPUT_EXPECTED_SIZE", len(bad))
    monkeypatch.setattr(runner, "INPUT_WHOLE_FILE_SHA256", hashlib.sha256(bad).hexdigest())
    code, _out, err = _run(root, results_root, monkeypatch, _positive)
    assert code == runner.EXIT_REFUSED
    assert "INPUT_JSON_INVALID" in err


def test_noncanonical_input_refuses(tmp_path, stream_fixture, results_root, monkeypatch):
    # valid JSON, correct size/hash, but not canonical (extra whitespace)
    noncanonical = b'{"candidate_stream": {}, "candidate_stream_sha256": "' + b"7" * 64 + b'"}'
    root = _build_repo(os.path.join(str(tmp_path), "repo"), stream_fixture["bytes"])
    input_path = os.path.join(root, "research", "brainvision", "results", "algebraic_n64_primary_v0_1",
                              "algebraic_n64_primary_v0_1_candidate_stream.json")
    with open(input_path, "wb") as handle:
        handle.write(noncanonical)
    monkeypatch.setattr(runner, "INPUT_EXPECTED_SIZE", len(noncanonical))
    monkeypatch.setattr(runner, "INPUT_WHOLE_FILE_SHA256", hashlib.sha256(noncanonical).hexdigest())
    code, _out, err = _run(root, results_root, monkeypatch, _positive)
    assert code == runner.EXIT_REFUSED
    assert "INPUT_NOT_CANONICAL" in err


# ============================================================= AST structural guarantees
def _runner_source():
    with open(runner.__file__.replace(".pyc", ".py"), "r", encoding="utf-8") as handle:
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


def test_exactly_one_freeze_with_replay_call_site():
    tree = ast.parse(_runner_source())
    calls = _calls_named(tree, "freeze_with_replay")
    assert len(calls) == 1
    keywords = {kw.arg for kw in calls[0].keywords}
    assert "repository_commit_identity" in keywords                # explicit provenance
    assert "source_paths" in keywords


def test_zero_freeze_and_zero_direct_verifier_call_sites():
    tree = ast.parse(_runner_source())
    assert _calls_named(tree, "freeze") == []
    for banned in ("verify_candidate", "verify_family", "member_certificate", "triple_array",
                   "verify_supplied_hash", "verify_manifest_identity"):
        assert _calls_named(tree, banned) == [], banned


def test_no_outer_replay_and_bounded_imports():
    source = _runner_source()
    tree = ast.parse(source)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            roots.add(node.module.split(".")[0])
    assert roots.issubset({"__future__", "hashlib", "json", "os", "stat", "subprocess", "sys", "typing",
                           "witness_canonical_json_v0_1", "witness_family_verifier_v0_1",
                           "witness_family_freeze_v0_1"})
    for forbidden in ("algebraic_direct_sum_n64_candidate_generator_v0_1", "psi_trs",
                      "run_n64_falsifier_v0_1", "torment_service", "numpy", "requests"):
        assert forbidden not in roots
    assert len(_calls_named(tree, "freeze_with_replay")) == 1       # single call -> no outer replay


# ============================================================= real-path protection
def test_real_result_paths_are_never_created_by_this_suite():
    real_results = os.path.join(BV_DIR, "results")
    assert (
        os.path.exists(os.path.join(real_results, runner.FINAL_DIRECTORY_NAME))
        == _BV_REAL_FINAL_EXISTED_AT_IMPORT
    )
    assert (
        os.path.exists(os.path.join(real_results, runner.STAGING_DIRECTORY_NAME))
        == _BV_REAL_STAGING_EXISTED_AT_IMPORT
    )


def test_default_repository_root_points_into_the_repo():
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
