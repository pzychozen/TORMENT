"""Tests for the independent higher-order witness verifier + canonical serializer (offline; integer-exact).

Small inputs are UNIT-TEST INPUTS ONLY, not scientific fixtures. No generator, psi_trs, N64 evaluator, ΨTRS, or
descriptor logic is imported or run. No N=64 witness is searched for or generated.
"""
import ast
import os
import shutil
import sys

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import witness_canonical_json_v0_1 as cjson  # noqa: E402
import witness_family_verifier_v0_1 as v  # noqa: E402

N12 = 12
WA = [0, 1, 3, 5, 6]
WB = [0, 1, 2, 4, 7]


def _rec(a, b, index=0):
    return {"raw_support_A": a, "raw_support_B": b, "candidate_generation_index": index}


def _stream_env(mode, n, records, terminal="stream_completed", count=None):
    payload = {"schema_name": v.STREAM_SCHEMA_NAME, "schema_version": v.STREAM_SCHEMA_VERSION,
               "verification_mode": mode, "N": n, "generator_identity_hash": "0" * 64,
               "generator_configuration_hash": "0" * 64, "budget_identity_hash": "0" * 64, "records": records,
               "candidate_count": (len(records) if count is None else count), "terminal_status": terminal}
    return cjson.envelope("candidate_stream", payload)


# ----------------------------- N=12 positive certificates -----------------------------
def test_n12_positive_certificates():
    result = v.verify_candidate(_rec(WA, WB), N12)
    assert result["pair_valid"] is True
    cert = result["pair_certificate"]
    assert cert["member_certificate_A"]["autocorrelation"] == [5, 2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2]
    assert cert["member_certificate_A"]["one_step_table"] == {"c00": 4, "c01": 3, "c10": 3, "c11": 2}
    assert cert["member_certificate_A"]["transition_multiset"] == {"0": 6, "1": 6}
    assert cert["triple_disagreement_count"] == 48
    assert cert["member_certificate_A"]["primitive_period"] == 12 == cert["member_certificate_B"]["primitive_period"]
    assert cert["affine_inequivalent"] and cert["affine_plus_complement_inequivalent"]
    assert cert["direct_complement_image"] is False and cert["triple_G_nonaligned"] is True


# ----------------------------- negative fixtures -----------------------------
@pytest.mark.parametrize("a,b,expected", [
    ([0, 1, 2], [0, 3, 7, 9], v.CANDIDATE_NOT_HOMOMETRIC),
    (WA, WA, v.CANDIDATE_SUPPORT_INVALID),
    (WA, sorted((x + 1) % 12 for x in WA), v.CANDIDATE_AFFINE_EQUIVALENT),
    (WA, sorted((-x) % 12 for x in WA), v.CANDIDATE_AFFINE_EQUIVALENT),
    (WA, sorted((5 * x + 1) % 12 for x in WA), v.CANDIDATE_AFFINE_EQUIVALENT),
    ([0, 1, 2, 3, 4, 7], [5, 6, 8, 9, 10, 11], v.CANDIDATE_COMPLEMENT_IMAGE),
    ([0, 2, 4, 6, 8, 10], [1, 3, 5, 7, 9, 11], v.CANDIDATE_MEMBER_NOT_PRIMITIVE),
])
def test_negative_primary_codes(a, b, expected):
    assert v.verify_candidate(_rec(a, b), N12)["primary_failure_code"] == expected


def test_direct_complement_emits_both_codes_direct_first():
    codes = v.verify_candidate(_rec([0, 1, 2, 3, 4, 7], [5, 6, 8, 9, 10, 11]), N12)["ordered_failure_codes"]
    assert codes.index(v.CANDIDATE_COMPLEMENT_IMAGE) < codes.index(v.CANDIDATE_AFFINE_PLUS_COMPLEMENT_EQUIVALENT)


@pytest.mark.parametrize("bad", [[0, 1, 1], [0, 13], [1, 0], [], "x", [0, 1, 2.0], [0, True, 2]])
def test_malformed_support_rejected(bad):
    assert v.verify_candidate(_rec(bad, WB), N12)["primary_failure_code"] in (
        v.CANDIDATE_SUPPORT_INVALID, v.CANDIDATE_SCHEMA_INVALID)


def test_missing_fields_schema_invalid():
    assert v.verify_candidate({"raw_support_A": WA}, N12)["primary_failure_code"] == v.CANDIDATE_SCHEMA_INVALID


# ----------------------------- strict-int schema fields -----------------------------
def test_is_strict_int():
    assert v.is_strict_int(3) is True
    assert v.is_strict_int(True) is False and v.is_strict_int(False) is False
    assert v.is_strict_int(3.0) is False


def test_bool_rejected_in_stream_integer_fields():
    env = _stream_env("REFERENCE_REGRESSION_N12", 12, [_rec(WA, WB, 0)], count=True)  # candidate_count=True
    assert v.validate_stream_envelope(env)["code"] == v.CANDIDATE_STREAM_INVALID
    # candidate_generation_index=False
    payload = {"schema_name": v.STREAM_SCHEMA_NAME, "schema_version": v.STREAM_SCHEMA_VERSION,
               "verification_mode": "REFERENCE_REGRESSION_N12", "N": 12, "generator_identity_hash": "0" * 64,
               "generator_configuration_hash": "0" * 64, "budget_identity_hash": "0" * 64,
               "records": [{"raw_support_A": WA, "raw_support_B": WB, "candidate_generation_index": False}],
               "candidate_count": 1, "terminal_status": "stream_completed"}
    assert v.validate_stream_envelope(cjson.envelope("candidate_stream", payload))["code"] == v.CANDIDATE_STREAM_INVALID
    # N=True -> N/mode phase
    assert v.validate_stream_envelope(_stream_env("REFERENCE_REGRESSION_N12", True, [_rec(WA, WB, 0)]))["code"] \
        == v.CANDIDATE_N_MODE_INVALID


# ----------------------------- A/B normalization -----------------------------
def test_ab_normalization_reversal_invariance():
    forward = v.verify_candidate(_rec(WA, WB), N12)["pair_certificate"]
    reversed_roles = v.verify_candidate(_rec(WB, WA), N12)["pair_certificate"]
    assert cjson.canonical_json_bytes(v.certificate_core(forward)) == \
        cjson.canonical_json_bytes(v.certificate_core(reversed_roles))               # identical normalized core
    assert forward["provenance"]["raw_roles_swapped"] != reversed_roles["provenance"]["raw_roles_swapped"]
    assert forward["member_certificate_A"]["raw_support"] == reversed_roles["member_certificate_A"]["raw_support"]
    assert forward["pair_valid"] == reversed_roles["pair_valid"]


# ----------------------------- triple detector / cross-check / disagreement -----------------------------
def test_triple_detector_two_classes():
    reflection = sorted((-x) % 12 for x in WA)
    assert v.triple_g_aligned(WA, reflection, N12) is True
    assert v.triple_g_aligned(WA, WB, N12) is False


def test_internal_disagreement_when_implied_equality_fails(monkeypatch):
    monkeypatch.setattr(v, "one_step_table", lambda support, n: {"c": support[-1]})
    result = v.verify_candidate(_rec(WA, WB), N12)
    assert result["execution_invalid"] is True and result["execution_code"] == v.VERIFIER_INTERNAL_DISAGREEMENT


# ----------------------------- stream validation -----------------------------
def test_stream_valid_and_mode_binding():
    out = v.validate_stream_envelope(_stream_env("REFERENCE_REGRESSION_N12", 12, [_rec(WA, WB, 0)]))
    assert out["valid"] is True and out["mode"] == "REFERENCE_REGRESSION_N12" and out["n"] == 12


@pytest.mark.parametrize("mode,n", [("REFERENCE_REGRESSION_N12", 64), ("PRIMARY_CANDIDATE_N64", 12),
                                    ("BOGUS_MODE", 12)])
def test_stream_mode_n_invalid(mode, n):
    assert v.validate_stream_envelope(_stream_env(mode, n, [_rec(WA, WB, 0)]))["code"] == v.CANDIDATE_N_MODE_INVALID


def test_stream_hash_mismatch_and_structural():
    env = _stream_env("REFERENCE_REGRESSION_N12", 12, [_rec(WA, WB, 0)])
    env["candidate_stream_sha256"] = "f" * 64
    assert v.validate_stream_envelope(env)["code"] == v.CANDIDATE_STREAM_HASH_MISMATCH
    assert v.validate_stream_envelope(_stream_env("REFERENCE_REGRESSION_N12", 12, [_rec(WA, WB, 5)]))["code"] \
        == v.CANDIDATE_STREAM_INVALID


def test_family_pair_count_invalid():
    cert = v.verify_candidate(_rec(WA, WB), N12)["pair_certificate"]
    assert v.FAMILY_PAIR_COUNT_INVALID in v.verify_family([cert], N12)["ordered_failure_codes"]


# ----------------------------- canonical serializer -----------------------------
def test_canonical_json_and_envelope():
    text = cjson.canonical_json_text({"b": 2, "a": [3, 1, 2]})
    assert text == '{"a":[3,1,2],"b":2}' and not text.endswith("\n")
    env = cjson.envelope("thing", {"b": 2, "a": [3, 1, 2]})
    assert env["thing_sha256"] == cjson.sha256_hex(cjson.canonical_json_bytes({"b": 2, "a": [3, 1, 2]}))


def test_envelope_rejects_recursive_self_hash():
    with pytest.raises(ValueError):
        cjson.envelope("thing", {"thing_sha256": "x"})


def test_is_lower_hex_64():
    assert cjson.is_lower_hex_64("0" * 64) is True
    assert cjson.is_lower_hex_64("A" * 64) is False and cjson.is_lower_hex_64("0" * 63) is False


# ----------------------------- source/config identities -----------------------------
def test_local_configuration_valid_and_hashes():
    out = v.validate_local_configuration()
    assert out["valid"] is True
    for role in ("verifier", "serializer", "freeze"):
        assert cjson.is_lower_hex_64(out["identities"][role + "_source_sha256"])
        assert out["identities"][role + "_source_path"].startswith("research/brainvision/")
    assert cjson.is_lower_hex_64(out["verifier_configuration_sha256"])
    assert v.verify_supplied_hash(out["verifier_configuration_payload"], out["verifier_configuration_sha256"]) \
        == (True, None)


def test_hash_identity_failure_on_tamper():
    config = v.verifier_configuration()
    good = cjson.payload_sha256(config)
    assert v.verify_supplied_hash(config, good)[0] is True
    assert v.verify_supplied_hash(config, "f" * 64)[1] == v.HASH_IDENTITY_FAILURE      # mismatch
    assert v.verify_supplied_hash(config, "abc")[1] == v.HASH_IDENTITY_FAILURE          # malformed


def test_configuration_invalid_on_missing_source(tmp_path):
    paths = {"verifier": os.path.join(str(tmp_path), "nope.py"),
             "serializer": os.path.join(BV_DIR, "witness_canonical_json_v0_1.py"),
             "freeze": os.path.join(BV_DIR, "witness_family_freeze_v0_1.py")}
    assert v.validate_local_configuration(source_paths=paths)["code"] == v.VERIFIER_CONFIGURATION_INVALID


# ----------------------------- runtime independence self-check -----------------------------
def test_independence_self_check_valid():
    assert v.independence_self_check()["valid"] is True


def test_independence_self_check_detects_forbidden_import(tmp_path):
    bad = os.path.join(str(tmp_path), "witness_family_verifier_v0_1.py")
    with open(bad, "w", encoding="utf-8") as handle:
        handle.write("import psi_trs\n")
    paths = {"verifier": bad, "serializer": os.path.join(BV_DIR, "witness_canonical_json_v0_1.py"),
             "freeze": os.path.join(BV_DIR, "witness_family_freeze_v0_1.py")}
    out = v.independence_self_check(paths)
    assert out["valid"] is False and out["code"] == v.FORBIDDEN_IMPORT_DETECTED


# ----------------------------- runtime regression self-check -----------------------------
def test_regression_self_check_valid():
    assert v.regression_self_check()["valid"] is True


def test_regression_self_check_detects_mismatch(monkeypatch):
    real = v.autocorrelation
    monkeypatch.setattr(v, "autocorrelation", lambda support, n: real(support, n)[:-1] + [999])
    out = v.regression_self_check()
    assert out["valid"] is False and out["code"] == v.VERIFIER_REGRESSION_FAILURE


# ----------------------------- certificate validation -----------------------------
def test_certificate_validation_passes_for_valid_cert():
    cert = v.verify_candidate(_rec(WA, WB), N12)["pair_certificate"]
    assert v.validate_pair_certificate(cert, N12) == (True, None)


def test_certificate_validation_detects_corruption():
    cert = v.verify_candidate(_rec(WA, WB), N12)["pair_certificate"]
    cert["member_certificate_A"]["autocorrelation"] = cert["member_certificate_A"]["autocorrelation"][:-1]
    assert v.validate_pair_certificate(cert, N12) == (False, v.CANDIDATE_CERTIFICATE_INVALID)


def test_verify_candidate_reaches_certificate_invalid(monkeypatch):
    real = v.member_certificate
    monkeypatch.setattr(v, "member_certificate",
                        lambda s, n: {**real(s, n), "autocorrelation": real(s, n)["autocorrelation"][:-1]})
    assert v.verify_candidate(_rec(WA, WB), N12)["primary_failure_code"] == v.CANDIDATE_CERTIFICATE_INVALID


# ----------------------------- serialization failure -----------------------------
def test_safe_serialization_failure():
    assert v.safe_canonical_bytes({"x": float("inf")})[0] is False           # allow_nan=False -> ValueError
    assert v.safe_canonical_bytes({"x": {1, 2}})[0] is False                  # set -> TypeError
    assert v.safe_envelope("t", {"x": float("nan")})[0] is False
    assert v.safe_canonical_bytes({"x": [1, 2, 3]})[0] is True


def test_serialization_failure_emit_site():
    assert v.serialize_or_failure({"x": float("inf")}) == (None, v.SERIALIZATION_FAILURE)
    assert v.envelope_or_failure("t", {"x": {1, 2}}) == (None, v.SERIALIZATION_FAILURE)
    data, code = v.serialize_or_failure({"x": [1, 2, 3]})
    assert code is None and data is not None


# ----------------------------- independence / forbidden imports (AST) -----------------------------
_FORBIDDEN = {"psi_trs", "run_n64_falsifier_v0_1", "descriptors", "run_prerecorded_paired_analysis_v0_1"}


def _roots(filename):
    with open(os.path.join(BV_DIR, filename), "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def test_verifier_and_serializer_imports_bounded():
    vr = _roots("witness_family_verifier_v0_1.py")
    assert vr.isdisjoint(_FORBIDDEN) and not any("generator" in r for r in vr)
    assert vr.issubset({"__future__", "ast", "os", "math", "typing", "witness_canonical_json_v0_1"})
    assert _roots("witness_canonical_json_v0_1.py").issubset({"__future__", "hashlib", "json", "typing"})


# ----------------------------- blocker 1: stream serialization safety -----------------------------
def _manual_env(diagnostics):
    payload = {"schema_name": v.STREAM_SCHEMA_NAME, "schema_version": v.STREAM_SCHEMA_VERSION,
               "verification_mode": "REFERENCE_REGRESSION_N12", "N": 12, "generator_identity_hash": "0" * 64,
               "generator_configuration_hash": "0" * 64, "budget_identity_hash": "0" * 64,
               "records": [{"raw_support_A": WA, "raw_support_B": WB, "candidate_generation_index": 0,
                            "generator_diagnostics": diagnostics}],
               "candidate_count": 1, "terminal_status": "stream_completed"}
    return {"candidate_stream": payload, "candidate_stream_sha256": "0" * 64}   # hash irrelevant; content unhashable


@pytest.mark.parametrize("diag", [float("nan"), float("inf"), float("-inf"), {1, 2}])
def test_stream_unserializable_diagnostics_yield_serialization_failure(diag):
    out = v.validate_stream_envelope(_manual_env(diag))       # must not raise
    assert out["code"] == v.SERIALIZATION_FAILURE


def test_valid_diagnostics_are_included_in_stream_hash():
    def env(value):
        payload = {"schema_name": v.STREAM_SCHEMA_NAME, "schema_version": v.STREAM_SCHEMA_VERSION,
                   "verification_mode": "REFERENCE_REGRESSION_N12", "N": 12, "generator_identity_hash": "0" * 64,
                   "generator_configuration_hash": "0" * 64, "budget_identity_hash": "0" * 64,
                   "records": [{"raw_support_A": WA, "raw_support_B": WB, "candidate_generation_index": 0,
                                "generator_diagnostics": {"note": value}}],
                   "candidate_count": 1, "terminal_status": "stream_completed"}
        return cjson.envelope("candidate_stream", payload)
    a, b = env("alpha"), env("beta")
    assert a["candidate_stream_sha256"] != b["candidate_stream_sha256"]         # diagnostics affect the hash
    assert v.validate_stream_envelope(a)["valid"] is True                       # and valid diagnostics pass


# ----------------------------- blocker 2: certificate corruption classes -----------------------------
def _valid_cert():
    return v.verify_candidate(_rec(WA, WB), N12)["pair_certificate"]


@pytest.mark.parametrize("mutate", [
    lambda c: c.update({"triple_disagreement_count": "not-int"}),
    lambda c: c.update({"triple_disagreement_count": 10 ** 9}),
    lambda c: c.update({"canonical_pair_key": "not-list"}),
    lambda c: c["provenance"].pop("raw_roles_swapped"),
    lambda c: c["provenance"].update({"candidate_generation_index": "not-int"}),
    lambda c: c["member_certificate_A"].update({"autocorrelation": c["member_certificate_A"]["autocorrelation"][:-1]}),
    lambda c: c["member_certificate_A"].update({"weight": 999}),
    lambda c: c.update({"pair_valid": False}),                       # inconsistent with predicate conjunction
    lambda c: c["member_certificate_A"].update({"nonserializable": {1, 2}}),   # serialization / hash structure
])
def test_certificate_corruption_classes(mutate):
    cert = _valid_cert()
    mutate(cert)
    assert v.validate_pair_certificate(cert, N12) == (False, v.CANDIDATE_CERTIFICATE_INVALID)


# ----------------------------- blocker 3: independence includes the freezer -----------------------------
def _real_paths():
    return {role: os.path.join(BV_DIR, name) for role, name in v._EXPECTED_MODULES.items()}


def test_independence_includes_freezer_valid():
    assert v.independence_self_check(_real_paths())["valid"] is True


def _write(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def test_independence_forbidden_freezer_import(tmp_path):
    paths = _real_paths()
    paths["freeze"] = _write(os.path.join(str(tmp_path), "witness_family_freeze_v0_1.py"), "import psi_trs\n")
    assert v.independence_self_check(paths)["code"] == v.FORBIDDEN_IMPORT_DETECTED


def test_independence_transitive_forbidden_via_serializer(tmp_path):
    paths = _real_paths()
    paths["serializer"] = _write(os.path.join(str(tmp_path), "witness_canonical_json_v0_1.py"),
                                 "import run_n64_falsifier_v0_1\n")
    assert v.independence_self_check(paths)["code"] == v.FORBIDDEN_IMPORT_DETECTED


def test_independence_serializer_imports_impl(tmp_path):
    paths = _real_paths()
    paths["serializer"] = _write(os.path.join(str(tmp_path), "witness_canonical_json_v0_1.py"),
                                 "import witness_family_verifier_v0_1\n")
    assert v.independence_self_check(paths)["code"] == v.FORBIDDEN_IMPORT_DETECTED


def test_independence_serializer_witness_math(tmp_path):
    paths = _real_paths()
    paths["serializer"] = _write(os.path.join(str(tmp_path), "witness_canonical_json_v0_1.py"),
                                 "def autocorrelation():\n    return 0\n")
    assert v.independence_self_check(paths)["code"] == v.FORBIDDEN_IMPORT_DETECTED


# ----------------------------- blocker 4: source-path ownership -----------------------------
def _fake_repo(tmp_path):
    root = os.path.join(str(tmp_path), "repo")
    bv = os.path.join(root, "research", "brainvision")
    os.makedirs(bv)
    for name in v._EXPECTED_MODULES.values():
        shutil.copy(os.path.join(BV_DIR, name), os.path.join(bv, name))
    paths = {role: os.path.join(bv, name) for role, name in v._EXPECTED_MODULES.items()}
    return root, bv, paths


def test_source_ownership_real_paths_pass():
    out = v.validate_source_ownership(v.default_repository_root(), v.default_source_paths())
    assert out["valid"] is True
    assert out["identities"]["verifier_source_path"] == "research/brainvision/witness_family_verifier_v0_1.py"


def test_source_ownership_outside_repository(tmp_path):
    root, _bv, paths = _fake_repo(tmp_path)
    paths["verifier"] = _write(os.path.join(str(tmp_path), "witness_family_verifier_v0_1.py"), "x=1\n")
    assert v.validate_source_ownership(root, paths)["code"] == v.VERIFIER_CONFIGURATION_INVALID


def test_source_ownership_wrong_filename(tmp_path):
    root, bv, paths = _fake_repo(tmp_path)
    paths["verifier"] = _write(os.path.join(bv, "wrong_name.py"), "x=1\n")
    assert v.validate_source_ownership(root, paths)["code"] == v.VERIFIER_CONFIGURATION_INVALID


def test_source_ownership_wrong_subdirectory(tmp_path):
    root, _bv, paths = _fake_repo(tmp_path)
    other = os.path.join(root, "research", "other")
    os.makedirs(other)
    paths["verifier"] = _write(os.path.join(other, "witness_family_verifier_v0_1.py"), "x=1\n")
    assert v.validate_source_ownership(root, paths)["code"] == v.VERIFIER_CONFIGURATION_INVALID


def test_source_ownership_path_traversal(tmp_path):
    root, bv, paths = _fake_repo(tmp_path)
    paths["verifier"] = os.path.join(bv, "..", "..", "witness_family_verifier_v0_1.py")
    _write(os.path.join(root, "witness_family_verifier_v0_1.py"), "x=1\n")   # exists but outside bv
    assert v.validate_source_ownership(root, paths)["code"] == v.VERIFIER_CONFIGURATION_INVALID


def test_source_ownership_symlink_escape(tmp_path):
    root, bv, paths = _fake_repo(tmp_path)
    outside = _write(os.path.join(str(tmp_path), "evil.py"), "x=1\n")
    link = os.path.join(bv, "witness_family_verifier_v0_1.py")
    os.remove(link)
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        import pytest as _pytest
        _pytest.skip("symlinks unsupported on this filesystem")
    paths["verifier"] = link
    assert v.validate_source_ownership(root, paths)["code"] == v.VERIFIER_CONFIGURATION_INVALID


def test_source_hash_mismatch_yields_hash_identity_failure(tmp_path):
    root, _bv, paths = _fake_repo(tmp_path)
    out = v.validate_local_configuration(repository_root=root, source_paths=paths,
                                         expected_source_hashes={"verifier": "f" * 64})
    assert out["code"] == v.HASH_IDENTITY_FAILURE


# ----------------------------- final blocker: exact-schema + supplied-envelope hash validation ----------
def _valid_envelope():
    return cjson.envelope("pair_verifier_certificate", _valid_cert())


def test_valid_production_envelope_passes():
    assert v.validate_pair_certificate_envelope(_valid_envelope(), N12) == (True, None)


@pytest.mark.parametrize("mutate", [
    lambda e: e["pair_verifier_certificate"]["member_certificate_A"].update({"unexpected": 1}),
    lambda e: e["pair_verifier_certificate"]["member_certificate_B"].update({"debug": "x"}),
    lambda e: e["pair_verifier_certificate"]["member_certificate_A"].update({"generator_score": 0}),
    lambda e: e["pair_verifier_certificate"].update({"psi_response": 0}),
    lambda e: e["pair_verifier_certificate"].update({"notes": "valid json"}),
    lambda e: e["pair_verifier_certificate"]["provenance"].update({"leak": 1}),
    lambda e: e.update({"extra_envelope_meta": 1}),
    lambda e: e["pair_verifier_certificate"].pop("triple_disagreement_count"),
    lambda e: e["pair_verifier_certificate"]["member_certificate_A"].pop("weight"),
])
def test_envelope_extra_or_missing_keys_rejected(mutate):
    env = _valid_envelope()
    mutate(env)
    assert v.validate_pair_certificate_envelope(env, N12) == (False, v.CANDIDATE_CERTIFICATE_INVALID)


def test_supplied_hash_changed_to_valid_hex_detected():
    env = _valid_envelope()
    env["pair_verifier_certificate_sha256"] = "a" * 64                      # valid hex64 but wrong
    assert v.validate_pair_certificate_envelope(env, N12) == (False, v.CANDIDATE_CERTIFICATE_INVALID)


def test_payload_mutated_after_envelope_creation_detected():
    env = _valid_envelope()
    env["pair_verifier_certificate"]["triple_disagreement_count"] = 47      # schema-valid change; hash now stale
    assert v.validate_pair_certificate_envelope(env, N12) == (False, v.CANDIDATE_CERTIFICATE_INVALID)


def test_malformed_supplied_hash_detected():
    env = _valid_envelope()
    env["pair_verifier_certificate_sha256"] = "not-hex"
    assert v.validate_pair_certificate_envelope(env, N12) == (False, v.CANDIDATE_CERTIFICATE_INVALID)


def test_verify_candidate_uses_envelope_validation_path_for_valid_cert():
    # the production path builds an envelope and validates that exact envelope; the accepted N=12 witness passes
    result = v.verify_candidate(_rec(WA, WB), N12)
    assert result["pair_valid"] is True and result["pair_certificate"] is not None


def _rehashed_envelope_with(field, value):
    cert = _valid_cert()
    cert[field] = value                                              # add exactly one forbidden pair-payload field
    return cjson.envelope("pair_verifier_certificate", cert)         # recompute a correct hash over modified payload


@pytest.mark.parametrize("field,value", [("schema_name", "not-production"), ("schema_version", "wrong"),
                                         ("N", 999)])
def test_forbidden_pair_payload_fields_rejected_by_exact_schema(field, value):
    env = _rehashed_envelope_with(field, value)
    # the supplied hash is correctly recomputed over the modified payload -> rejection is schema, not stale hash
    assert env["pair_verifier_certificate_sha256"] == cjson.payload_sha256(env["pair_verifier_certificate"])
    assert v.validate_pair_certificate_envelope(env, N12) == (False, v.CANDIDATE_CERTIFICATE_INVALID)
