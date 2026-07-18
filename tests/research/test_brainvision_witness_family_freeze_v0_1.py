"""Tests for the deterministic descriptor-blind witness freezer + authoritative replay (offline).

No generator, ΨTRS, or descriptor logic is imported or run. No N=64 witness is searched for or generated.
Three-pair selection/assembly is exercised with an explicit verifier TEST DOUBLE (monkeypatched verify_candidate
or _freeze_once), clearly labeled as selection-contract tests; the freezer still invokes "the verifier" and never
trusts stream-supplied certificates. Real successful N=64 family freezing is deferred until an authorized frozen
family fixture exists. Authoritative infrastructure (replay gating, self-checks) is exercised end-to-end with the
real verifier via REFERENCE_REGRESSION_N12, which cannot freeze a primary family.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import witness_canonical_json_v0_1 as cjson  # noqa: E402
import witness_family_verifier_v0_1 as v  # noqa: E402
import witness_family_freeze_v0_1 as fz  # noqa: E402

HEX = "0" * 64
WA = [0, 1, 3, 5, 6]
WB = [0, 1, 2, 4, 7]


def _rec(a, b, index):
    return {"raw_support_A": a, "raw_support_B": b, "candidate_generation_index": index}


def _stream_env(mode, n, records, terminal="stream_completed"):
    payload = {"schema_name": v.STREAM_SCHEMA_NAME, "schema_version": v.STREAM_SCHEMA_VERSION,
               "verification_mode": mode, "N": n, "generator_identity_hash": HEX,
               "generator_configuration_hash": HEX, "budget_identity_hash": HEX, "records": records,
               "candidate_count": len(records), "terminal_status": terminal}
    return cjson.envelope("candidate_stream", payload)


def _member(support, key, autocorr):
    return {"raw_support": support, "weight": len(support), "autocorrelation": autocorr,
            "one_step_table": {"c00": 0, "c01": 0, "c10": 0, "c11": 0},
            "transition_multiset": {"0": 0, "1": 0}, "primitive_period": 64, "member_G_equivalence_key": key}


def _canned_valid(sa, sb, ka, kb, autocorr):
    cert = {"member_certificate_A": _member(sa, ka, autocorr), "member_certificate_B": _member(sb, kb, autocorr),
            "canonical_pair_key": [ka, kb], "autocorrelation_equal": True, "one_step_table_equal": True,
            "transition_multiset_equal": True, "triple_disagreement_count": 1, "affine_inequivalent": True,
            "affine_plus_complement_inequivalent": True, "direct_complement_image": False,
            "triple_G_nonaligned": True, "pair_valid": True, "ordered_failure_codes": [],
            "provenance": {"stream_raw_support_A": sa, "stream_raw_support_B": sb, "raw_roles_swapped": False}}
    return {"execution_invalid": False, "execution_code": None, "pair_certificate": cert,
            "ordered_failure_codes": [], "primary_failure_code": None, "pair_valid": True}


# ----------------------------- stream validation / non-authoritative freeze -----------------------------
def test_freeze_rejects_broken_stream_hash():
    env = _stream_env("PRIMARY_CANDIDATE_N64", 64, [_rec([0, 1, 2], [0, 1, 2, 3], 0)])
    env["candidate_stream_sha256"] = "f" * 64
    result = fz.freeze(env)["freeze_result"]
    assert result["family_frozen"] is False
    assert result["failure_record"]["failure_code"] == v.CANDIDATE_STREAM_HASH_MISMATCH


def test_freeze_family_not_freezable_all_rejected():
    records = [_rec([0, 1, 2], [0, 1, 2, 3], 0), _rec([0, 1, 4], [0, 2, 5, 9], 1),
               _rec([0, 5, 10], [0, 5, 10, 20], 2)]
    result = fz.freeze(_stream_env("PRIMARY_CANDIDATE_N64", 64, records))["freeze_result"]
    assert result["family_frozen"] is False
    assert result["failure_record"]["failure_code"] == v.FAMILY_NOT_FREEZABLE
    assert len(result["candidate_decision_ledger"]) == 3
    assert all(e["primary_failure_code"] == v.CANDIDATE_NOT_HOMOMETRIC for e in result["candidate_decision_ledger"])


def test_plain_single_pass_cannot_claim_authoritative_freeze(monkeypatch):
    canned = {i: _canned_valid([i], [i + 100], [i], [i + 100], [10, i, 0]) for i in range(3)}
    monkeypatch.setattr(v, "verify_candidate", lambda record, n: canned[record["candidate_generation_index"]])
    result = fz.freeze(_stream_env("PRIMARY_CANDIDATE_N64", 64, [_rec([0], [0], i) for i in range(3)]))["freeze_result"]
    assert result["provisional_k3_valid"] is True          # K=3 pairs are provisionally valid
    assert result["family_frozen"] is False                # but single pass is never authoritative
    assert result["authoritative_operation"] is False
    assert result["family_manifest"] is None


# ----------------------------- selection contract (verifier test double; non-authoritative) -----------------------------
def test_selection_first_k_reuse_stop_and_not_evaluated(monkeypatch):
    canned = {
        0: _canned_valid([0, 1], [2, 3], [0, 1], [2, 3], [10, 0, 0]),
        1: _canned_valid([4, 5], [6, 7], [4, 5], [6, 7], [10, 1, 0]),
        2: _canned_valid([0, 1], [8, 9], [0, 1], [8, 9], [10, 2, 0]),      # member reuse
        3: _canned_valid([10, 11], [12, 13], [10, 11], [12, 13], [10, 3, 0]),
        4: _canned_valid([14, 15], [16, 17], [14, 15], [16, 17], [10, 4, 0]),
    }
    monkeypatch.setattr(v, "verify_candidate", lambda record, n: canned[record["candidate_generation_index"]])
    result = fz.freeze(_stream_env("PRIMARY_CANDIDATE_N64", 64, [_rec([0], [0], i) for i in range(5)]))["freeze_result"]
    assert result["accepted_candidate_indices"] == [0, 1, 3]
    ledger = {e["candidate_generation_index"]: e for e in result["candidate_decision_ledger"]}
    assert v.FAMILY_MEMBER_REUSED in ledger[2]["family_reject_reasons"]
    assert ledger[4]["status"] == fz.NOT_EVALUATED_AFTER_K_REACHED           # after K reached
    assert [e["candidate_generation_index"] for e in result["candidate_decision_ledger"]] == [0, 1, 2, 3, 4]


def test_selection_rejects_g_equivalent_and_class_reuse(monkeypatch):
    canned = {
        0: _canned_valid([0, 1], [2, 3], [0, 1], [2, 3], [10, 0, 0]),
        1: _canned_valid([4, 5], [6, 7], [0, 1], [6, 7], [10, 1, 0]),      # key reuse -> G-equivalent
        2: _canned_valid([8, 9], [10, 11], [8, 9], [10, 11], [10, 0, 0]),  # autocorr class reuse
    }
    monkeypatch.setattr(v, "verify_candidate", lambda record, n: canned[record["candidate_generation_index"]])
    result = fz.freeze(_stream_env("PRIMARY_CANDIDATE_N64", 64, [_rec([0], [0], i) for i in range(3)]))["freeze_result"]
    assert result["accepted_candidate_indices"] == [0]
    ledger = {e["candidate_generation_index"]: e for e in result["candidate_decision_ledger"]}
    assert v.FAMILY_MEMBER_G_EQUIVALENT in ledger[1]["family_reject_reasons"]
    assert v.FAMILY_AUTOCORRELATION_CLASS_REUSED in ledger[2]["family_reject_reasons"]


# ----------------------------- authoritative replay -----------------------------
def _canned_provisional_k3():
    envs = [cjson.envelope("pair_verifier_certificate",
                           _canned_valid([2 * i], [2 * i + 1], [2 * i], [2 * i + 1], [10, i, 0])["pair_certificate"])
            for i in range(3)]
    return {"schema_name": fz.FREEZE_RESULT_SCHEMA, "schema_version": "0.1",
            "verification_mode": "PRIMARY_CANDIDATE_N64", "N": 64, "candidate_stream_sha256": "a" * 64,
            "candidate_count": 3, "terminal_stream_status": "stream_completed",
            "generator_identity_hash": HEX, "generator_configuration_hash": HEX, "budget_identity_hash": HEX,
            "candidate_decision_ledger": [], "candidate_decision_ledger_sha256": "b" * 64,
            "accepted_candidate_indices": [0, 1, 2], "accepted_pair_certificate_envelopes": envs,
            "family_certificate": cjson.envelope("family_verifier_certificate", {"family_valid": True}),
            "family_manifest": None, "provisional_k3_valid": True, "family_frozen": False,
            "authoritative_operation": False, "regression_mode_no_primary_manifest": False,
            "resource_policy_status": fz.RESOURCE_POLICY_STATUS, "failure_record": None}


def test_authoritative_replay_success_freezes_family(monkeypatch):
    config = v.validate_local_configuration()
    monkeypatch.setattr(fz, "_run_self_checks", lambda source_paths: {"valid": True, "code": None, "config": config})
    monkeypatch.setattr(fz, "_freeze_once", lambda env: _canned_provisional_k3())
    result = fz.freeze_with_replay(_stream_env("PRIMARY_CANDIDATE_N64", 64, [_rec([0], [0], 0)]))["freeze_result"]
    assert result["family_frozen"] is True
    assert result["replay_record"]["byte_identical"] is True
    manifest = result["family_manifest"]["family_manifest"]
    for field in ("verifier_source_sha256", "serializer_source_sha256", "freeze_source_sha256",
                  "verifier_configuration_sha256", "serializer_configuration_sha256", "freeze_configuration_sha256",
                  "candidate_stream_sha256", "generator_identity_hash", "budget_identity_hash",
                  "repository_commit_identity", "candidate_decision_ledger_sha256"):
        assert field in manifest
    assert fz.verify_manifest_identity(result["family_manifest"]) == (True, None)


def test_authoritative_replay_mismatch(monkeypatch):
    config = v.validate_local_configuration()
    monkeypatch.setattr(fz, "_run_self_checks", lambda source_paths: {"valid": True, "code": None, "config": config})
    counter = {"n": 0}

    def diverging(env):
        counter["n"] += 1
        base = _canned_provisional_k3()
        base["candidate_stream_sha256"] = ("a" if counter["n"] == 1 else "c") * 64   # differ on second pass
        return base
    monkeypatch.setattr(fz, "_freeze_once", diverging)
    result = fz.freeze_with_replay(_stream_env("PRIMARY_CANDIDATE_N64", 64, [_rec([0], [0], 0)]))["freeze_result"]
    assert result["family_frozen"] is False
    assert result["failure_record"]["failure_code"] == v.REPLAY_MISMATCH
    assert result["family_manifest"] is None


def test_manifest_identity_tamper_detected(monkeypatch):
    config = v.validate_local_configuration()
    monkeypatch.setattr(fz, "_run_self_checks", lambda source_paths: {"valid": True, "code": None, "config": config})
    monkeypatch.setattr(fz, "_freeze_once", lambda env: _canned_provisional_k3())
    result = fz.freeze_with_replay(_stream_env("PRIMARY_CANDIDATE_N64", 64, [_rec([0], [0], 0)]))["freeze_result"]
    manifest_env = dict(result["family_manifest"])
    manifest_env["family_manifest"] = dict(manifest_env["family_manifest"])
    manifest_env["family_manifest"]["N"] = 12                                        # tamper
    assert fz.verify_manifest_identity(manifest_env) == (False, v.HASH_IDENTITY_FAILURE)


def test_authoritative_self_check_failure_blocks_freeze(monkeypatch):
    monkeypatch.setattr(fz, "_run_self_checks",
                        lambda source_paths: {"valid": False, "code": v.VERIFIER_REGRESSION_FAILURE,
                                              "stage": "regression", "config": None})
    result = fz.freeze_with_replay(_stream_env("PRIMARY_CANDIDATE_N64", 64, [_rec([0, 1, 2], [0, 1, 2, 3], 0)]))["freeze_result"]
    assert result["family_frozen"] is False
    assert result["failure_record"]["failure_code"] == v.VERIFIER_REGRESSION_FAILURE


# ----------------------------- real N=12 integration (authoritative, no primary family) -----------------------------
def test_real_n12_integration_replay_and_no_primary_manifest():
    env = _stream_env("REFERENCE_REGRESSION_N12", 12, [_rec(WA, WB, 0)])
    result = fz.freeze_with_replay(env)["freeze_result"]              # real verifier + real self-checks + replay
    assert result["authoritative_operation"] is True
    assert result["replay_record"]["byte_identical"] is True
    assert result["regression_mode_no_primary_manifest"] is True
    assert result["family_frozen"] is False and result["family_manifest"] is None
    assert result["candidate_decision_ledger"][0]["candidate_generation_index"] == 0
    assert result["accepted_pair_certificate_envelopes"][0]["pair_verifier_certificate"]["pair_valid"] is True


def test_compare_freeze_results():
    assert fz.compare_freeze_results({"a": 1}, {"a": 2}) is False
    assert fz.compare_freeze_results({"a": 1}, {"a": 1}) is True


def test_freezer_serialization_failure_emit_site(monkeypatch):
    # force the production result-emission wrapper to fail -> canonical SERIALIZATION_FAILURE
    monkeypatch.setattr(v, "envelope_or_failure", lambda name, payload: (None, v.SERIALIZATION_FAILURE))
    result = fz.freeze(_stream_env("PRIMARY_CANDIDATE_N64", 64, [_rec([0, 1, 2], [0, 1, 2, 3], 0)]))["freeze_result"]
    assert result["failure_record"]["failure_code"] == v.SERIALIZATION_FAILURE
    assert result["family_frozen"] is False


def test_freeze_unserializable_stream_diagnostics(monkeypatch):
    # production path: nonfinite generator_diagnostics -> SERIALIZATION_FAILURE, no raw exception escapes
    payload = {"schema_name": v.STREAM_SCHEMA_NAME, "schema_version": v.STREAM_SCHEMA_VERSION,
               "verification_mode": "PRIMARY_CANDIDATE_N64", "N": 64, "generator_identity_hash": HEX,
               "generator_configuration_hash": HEX, "budget_identity_hash": HEX,
               "records": [{"raw_support_A": [0, 1, 2], "raw_support_B": [0, 1, 2, 3],
                            "candidate_generation_index": 0, "generator_diagnostics": float("nan")}],
               "candidate_count": 1, "terminal_status": "stream_completed"}
    env = {"candidate_stream": payload, "candidate_stream_sha256": "0" * 64}
    result = fz.freeze(env)["freeze_result"]
    assert result["failure_record"]["failure_code"] == v.SERIALIZATION_FAILURE
    assert result["family_frozen"] is False


# ----------------------------- freezer forbidden imports -----------------------------
def test_freezer_forbidden_imports_ast():
    with open(os.path.join(BV_DIR, "witness_family_freeze_v0_1.py"), "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    assert roots.isdisjoint({"psi_trs", "run_n64_falsifier_v0_1", "descriptors"})
    assert not any("generator" in r for r in roots)
    assert roots.issubset({"__future__", "os", "typing", "witness_canonical_json_v0_1",
                           "witness_family_verifier_v0_1"})
