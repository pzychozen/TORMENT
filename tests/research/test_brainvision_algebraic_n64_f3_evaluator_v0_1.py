"""Tests for the frozen-family F3 evaluator (non-contact; synthetic caches and read-only evidence only).

The production descriptor entry point psi_trs.psi_trs_features is monkeypatched by an autouse fixture to raise
if reached, so no ordinary test can contact PsiTRS. The evaluator's pure path is exercised with synthetic
finite feature caches. Parity tests compare only the old N64 runner's pure rotate / symmetric_response.
"""
import ast
import copy
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import psi_trs  # noqa: E402
import witness_canonical_json_v0_1 as cjson  # noqa: E402
import algebraic_n64_f3_frozen_identity_v0_1 as frozen  # noqa: E402
import algebraic_n64_f3_evaluator_v0_1 as ev  # noqa: E402
import run_n64_falsifier_v0_1 as old  # noqa: E402  (parity reference: rotate / symmetric_response only)

REAL_FREEZE_RESULT = os.path.join(
    BV_DIR, "results", "algebraic_n64_primary_v0_1_freeze_v0_1",
    "algebraic_n64_primary_v0_1_freeze_result.json")


@pytest.fixture(autouse=True)
def _forbid_descriptor(monkeypatch):
    def _guard(*_a, **_k):
        raise AssertionError("psi_trs.psi_trs_features contacted during an evaluator test")
    monkeypatch.setattr(psi_trs, "psi_trs_features", _guard)


# ----------------------------------------------------------------- synthetic caches
def _constant_cache(vectors_by_member_variant):
    """Each member/variant maps to a single constant 11-vector repeated across all 64 starts."""
    features = {}
    for member_id, _c, _o, _r, _s in frozen.frozen_members:
        features[member_id] = {}
        for variant in ev.VARIANTS:
            vec = [float(x) for x in vectors_by_member_variant[member_id][variant]]
            features[member_id][variant] = [list(vec) for _ in range(ev.N)]
    return {"features": features, "descriptor_call_record": {"completed_descriptor_calls": 768}}


def _random_cache(seed=0):
    rng = np.random.default_rng(seed)
    features = {}
    for member_id, _c, _o, _r, _s in frozen.frozen_members:
        features[member_id] = {}
        for variant in ev.VARIANTS:
            features[member_id][variant] = [[float(x) for x in rng.standard_normal(11)] for _ in range(ev.N)]
    return {"features": features, "descriptor_call_record": {"completed_descriptor_calls": 768}}


_E0 = [1.0] + [0.0] * 10
_E1 = [0.0, 1.0] + [0.0] * 9
_ZERO = [0.0] * 11


def _strong_pass_spec(strong_pairs):
    """Build a spec where the listed candidate indices are engineered to PAIR_STRONG_PASS.

    Constant-per-member features: self-shift distances are exactly 0, so self maxima are 0.
    STRONG pair: A_full=e0, B_full=e1 (full cross > 0 > 0 self); A_k0=B_k0=zero (k0 cross 0 <= 0 self);
                 differences = full_cross - 0 > 0 -> recursive positive.
    Non-strong pair: A_full=B_full=e0 (full cross 0, not extreme).
    """
    spec = {}
    for candidate, _order, _a, _b, _c in frozen.frozen_pairs:
        member_a = "candidate_%d_A" % candidate
        member_b = "candidate_%d_B" % candidate
        if candidate in strong_pairs:
            spec[member_a] = {"psi_trs": _E0, "psi_trs_k0": _ZERO}
            spec[member_b] = {"psi_trs": _E1, "psi_trs_k0": _ZERO}
        else:
            spec[member_a] = {"psi_trs": _E0, "psi_trs_k0": _E0}
            spec[member_b] = {"psi_trs": _E0, "psi_trs_k0": _E0}
    return spec


# ----------------------------------------------------------------- coverage
def test_coverage_counts_exact():
    out = ev.evaluate_from_feature_cache(_random_cache())
    ep = out["evaluation_pass"]
    nonid = sum(o["coverage"]["responses"] for m in ep["members"]
                for o in m["self_orbits_by_variant"].values())
    cross = sum(len(cv["per_start"]) for p in ep["pairs"] for cv in p["cross_by_variant"].values())
    identity = sum(m["self_orbits_by_variant"][v]["identity_controls"]["count"]
                   for m in ep["members"] for v in ev.VARIANTS)
    assert nonid == 48384
    assert cross == 384
    assert identity == 768
    assert len(ep["members"]) == 6 and len(ep["pairs"]) == 3


def test_identity_controls_exact_zero():
    out = ev.evaluate_from_feature_cache(_random_cache(3))
    for member in out["evaluation_pass"]["members"]:
        for variant in ev.VARIANTS:
            controls = member["self_orbits_by_variant"][variant]["identity_controls"]
            assert controls["all_distance_zero"] is True
            assert controls["nonzero_starts"] == []
    assert out["validity"]["identity_self_pair_valid"] is True


def test_each_nonidentity_shift_has_64_starts():
    out = ev.evaluate_from_feature_cache(_random_cache(5))
    member = out["evaluation_pass"]["members"][0]
    shifts = member["self_orbits_by_variant"]["psi_trs"]["nonidentity_shifts"]
    assert len(shifts) == 63
    assert all(len(s["per_start"]) == 64 and s["count"] == 64 for s in shifts)
    assert [s["relative_shift"] for s in shifts] == list(range(1, 64))


# ----------------------------------------------------------------- gates and verdicts
def test_family_verdict_mapping_direct():
    assert ev._family_verdict(3, True) == ev.STRONG_FAMILY_FALSIFIER_SUCCESS
    assert ev._family_verdict(2, True) == ev.VALID_MIXED_FAMILY_RESULT
    assert ev._family_verdict(1, True) == ev.VALID_MIXED_FAMILY_RESULT
    assert ev._family_verdict(0, True) == ev.STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED
    assert ev._family_verdict(3, False) == ev.INVALID_FAMILY_EVALUATION


def test_all_three_pairs_strong_pass_family_success():
    out = ev.evaluate_from_feature_cache(_constant_cache(_strong_pass_spec({478, 479, 480})))
    assert out["valid_run"] is True
    assert out["strong_pass_count"] == 3
    assert out["family_verdict"] == ev.STRONG_FAMILY_FALSIFIER_SUCCESS
    for pair in out["evaluation_pass"]["pairs"]:
        assert pair["primary_pass"] is True
        gates = pair["gates"]
        assert gates["full_dual_orbit_extreme"] is True
        assert gates["k0_not_extreme_against_either_member"] is True
        assert gates["recursive_positive_all_starts"] is True
        assert "PAIR_STRONG_PASS" in pair["pair_verdict_flags"]


def test_mixed_family_result():
    out = ev.evaluate_from_feature_cache(_constant_cache(_strong_pass_spec({478, 479})))
    assert out["valid_run"] is True
    assert out["strong_pass_count"] == 2
    assert out["family_verdict"] == ev.VALID_MIXED_FAMILY_RESULT


def test_zero_pairs_pass_but_valid_not_supported():
    # identical features everywhere: full cross 0 (not extreme), differences 0 (recursive fails), all valid
    spec = {}
    for member_id, _c, _o, _r, _s in frozen.frozen_members:
        spec[member_id] = {"psi_trs": _E0, "psi_trs_k0": _E0}
    out = ev.evaluate_from_feature_cache(_constant_cache(spec))
    assert out["valid_run"] is True
    assert out["strong_pass_count"] == 0
    assert out["family_verdict"] == ev.STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED
    for pair in out["evaluation_pass"]["pairs"]:
        assert pair["primary_pass"] is False
        assert pair["gates"]["full_dual_orbit_extreme"] is False        # 0 > 0 is False (zero tolerance)
        assert pair["gates"]["recursive_positive_all_starts"] is False  # difference 0 is not > 0
        assert "PAIR_FULL_NOT_DUAL_ORBIT_EXTREME" in pair["pair_verdict_flags"]
        assert "PAIR_RECURSIVE_SIGN_FAILURE" in pair["pair_verdict_flags"]


def test_k0_also_extreme_blocks_strong_pass():
    # full extreme and recursive positive, but k0 cross > 0 (A_k0 != B_k0) -> k0_not_extreme False
    spec = {}
    for candidate, _order, _a, _b, _c in frozen.frozen_pairs:
        spec["candidate_%d_A" % candidate] = {"psi_trs": _E0, "psi_trs_k0": _E0}
        spec["candidate_%d_B" % candidate] = {"psi_trs": _E1, "psi_trs_k0": _E1}
    out = ev.evaluate_from_feature_cache(_constant_cache(spec))
    for pair in out["evaluation_pass"]["pairs"]:
        assert pair["gates"]["k0_not_extreme_against_either_member"] is False
        assert pair["primary_pass"] is False
        assert "PAIR_K0_ALSO_DUAL_ORBIT_EXTREME" in pair["pair_verdict_flags"]
    assert out["family_verdict"] == ev.STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED


def test_recursive_companion_object():
    out = ev.evaluate_from_feature_cache(_constant_cache(_strong_pass_spec({478, 479, 480})))
    companion = out["evaluation_pass"]["pairs"][0]["recursive_companion"]
    assert len(companion["differences"]) == 64
    assert companion["positive_count"] == 64
    assert companion["zero_count"] == 0 and companion["negative_count"] == 0
    assert companion["all_positive"] is True


def test_margins_present_and_signed():
    out = ev.evaluate_from_feature_cache(_constant_cache(_strong_pass_spec({478, 479, 480})))
    margins = out["evaluation_pass"]["pairs"][0]["margins"]
    assert margins["full_margin_vs_A"] > 0.0                            # full cross - self max (0)
    assert margins["minimum_recursive_difference"] > 0.0


# ----------------------------------------------------------------- primitives and parity
def test_rotation_parity_over_all_starts():
    rng = np.random.default_rng(11)
    field = rng.standard_normal((64, 1))
    for s in range(64):
        assert np.array_equal(ev.rotate(field, s), old.rotate(field, s))


def test_symmetric_response_parity():
    rng = np.random.default_rng(12)
    for _ in range(50):
        a = rng.standard_normal(11)
        b = rng.standard_normal(11)
        mine = ev.symmetric_response(a, b)
        theirs = old.symmetric_response(a, b)
        assert mine["numerator"] == theirs["numerator"]
        assert mine["joint_scale"] == theirs["joint_scale"]
        assert mine["effective_joint_scale"] == theirs["effective_joint_scale"]
        assert mine["distance"] == theirs["distance"]
        assert mine["finite"] == theirs["finite"]


def test_epsilon_and_near_epsilon_flag_parity():
    zero = np.zeros(11)
    tiny = np.full(11, 1e-11)                                           # norm ~ 3.3e-11, below near-epsilon
    for a, b in ((zero, zero), (tiny, tiny)):
        mine = ev.symmetric_response(a, b)
        theirs = old.symmetric_response(a, b)
        assert mine["joint_epsilon_hit"] == theirs["joint_epsilon_hit"]
        assert mine["joint_near_epsilon_hit"] == theirs["joint_near_epsilon_hit"]
    zero_response = ev.symmetric_response(zero, zero)
    assert zero_response["joint_epsilon_hit"] is True
    assert zero_response["distance"] == 0.0


def test_negative_zero_normalization():
    assert ev.canonical_float(-0.0) == 0.0
    assert str(ev.canonical_float(-0.0)) == "0.0"
    with pytest.raises(ValueError):
        ev.canonical_float(float("nan"))
    with pytest.raises(ValueError):
        ev.canonical_float(float("inf"))


def test_field_construction_and_recovery():
    support = frozen.raw_support_478_A
    field = ev.build_field(support)
    assert field.shape == (64, 1)
    assert int(field.sum()) == 12
    assert set(np.unique(field)) == {0.0, 1.0}
    assert ev.support_from_field(field) == support
    assert ev.validate_field(field, support) is None
    assert ev.validate_field(field, frozen.raw_support_478_B) == "support_mismatch"


# ----------------------------------------------------------------- invalidity
def test_wrong_feature_length_is_invalid():
    cache = _random_cache(7)
    cache["features"]["candidate_478_A"]["psi_trs"][0] = [0.0] * 10     # length 10, not 11
    out = ev.evaluate_from_feature_cache(cache)
    assert out["valid_run"] is False
    assert out["family_verdict"] == ev.INVALID_FAMILY_EVALUATION
    assert out["failure_record"]["failure_code"] == ev.DESCRIPTOR_FEATURE_SCHEMA_INVALID


def test_nonfinite_feature_is_invalid():
    cache = _random_cache(8)
    cache["features"]["candidate_479_B"]["psi_trs_k0"][5][2] = float("inf")
    out = ev.evaluate_from_feature_cache(cache)
    assert out["valid_run"] is False
    assert out["failure_record"]["failure_code"] == ev.DESCRIPTOR_FEATURE_NONFINITE


def test_missing_start_is_coverage_incomplete():
    cache = _random_cache(9)
    cache["features"]["candidate_480_A"]["psi_trs"] = cache["features"]["candidate_480_A"]["psi_trs"][:63]
    out = ev.evaluate_from_feature_cache(cache)
    assert out["valid_run"] is False
    assert out["failure_record"]["failure_code"] == ev.FEATURE_COVERAGE_INCOMPLETE


def test_missing_member_is_coverage_incomplete():
    cache = _random_cache(10)
    del cache["features"]["candidate_478_B"]
    out = ev.evaluate_from_feature_cache(cache)
    assert out["valid_run"] is False
    assert out["failure_record"]["failure_code"] == ev.FEATURE_COVERAGE_INCOMPLETE


def test_identity_self_pair_failure_via_patched_response(monkeypatch):
    real = ev.symmetric_response

    def _patched(f_a, f_b):
        result = real(f_a, f_b)
        if np.array_equal(np.asarray(f_a), np.asarray(f_b)):
            result = dict(result, numerator=1.0, distance=1.0)          # break the identity control
        return result
    monkeypatch.setattr(ev, "symmetric_response", _patched)
    out = ev.evaluate_from_feature_cache(_random_cache(13))
    assert out["valid_run"] is False
    assert out["validity"]["identity_self_pair_valid"] is False
    assert any(f["failure_code"] == ev.SELF_PAIR_CONTROL_FAILURE
               for f in [out["failure_record"]] if f)


def test_normalization_failure_via_patched_response(monkeypatch):
    def _patched(f_a, f_b):
        return {"numerator": 0.0, "joint_scale": 0.0, "effective_joint_scale": 0.0,
                "joint_epsilon_hit": True, "joint_near_epsilon_hit": True, "finite": False, "distance": 0.0}
    monkeypatch.setattr(ev, "symmetric_response", _patched)
    out = ev.evaluate_from_feature_cache(_random_cache(14))
    assert out["valid_run"] is False
    assert out["validity"]["normalization_valid"] is False


# ----------------------------------------------------------------- evidence validation (read-only)
def _real_envelope():
    with open(REAL_FREEZE_RESULT, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def test_validate_real_frozen_evidence_and_reverify():
    extracted = ev.validate_frozen_evidence(_real_envelope())
    assert len(extracted["pairs"]) == 3
    assert [p["candidate_generation_index"] for p in extracted["pairs"]] == [478, 479, 480]
    assert extracted["pairs"][0]["raw_support_A"] == frozen.raw_support_478_A
    # integer-exact reverification (authorized; no descriptor contact)
    reverified = ev.reverify_witnesses(extracted["pairs"], extracted["family_certificate_envelope"])
    assert reverified["family"]["family_valid"] is True
    for order in range(3):
        assert cjson.payload_sha256(reverified["recomputed_pair_certificates"][order]) \
            == frozen.pair_certificate_sha256[order]
    # recomputed family certificate exactly equals the embedded frozen payload and hashes to the frozen hash
    embedded = extracted["family_certificate_envelope"]["family_verifier_certificate"]
    assert reverified["recomputed_family_certificate"] == embedded
    assert cjson.payload_sha256(reverified["recomputed_family_certificate"]) == \
        frozen.family_verifier_certificate_sha256


# ---- blocker 2: exact family-certificate reverification ----
def _extracted():
    return ev.validate_frozen_evidence(_real_envelope())


def test_family_boolean_altered_fails():
    extracted = _extracted()
    env = copy.deepcopy(extracted["family_certificate_envelope"])
    env["family_verifier_certificate"]["family_valid"] = False
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.reverify_witnesses(extracted["pairs"], env)
    assert excinfo.value.code == ev.FAMILY_CERTIFICATE_HASH_MISMATCH


def test_family_pair_hash_list_reordered_fails():
    extracted = _extracted()
    env = copy.deepcopy(extracted["family_certificate_envelope"])
    hashes = env["family_verifier_certificate"]["pair_certificate_hashes"]
    env["family_verifier_certificate"]["pair_certificate_hashes"] = [hashes[2], hashes[0], hashes[1]]
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.reverify_witnesses(extracted["pairs"], env)
    assert excinfo.value.code == ev.FAMILY_CERTIFICATE_HASH_MISMATCH


def test_family_ordered_failure_codes_altered_fails():
    extracted = _extracted()
    env = copy.deepcopy(extracted["family_certificate_envelope"])
    env["family_verifier_certificate"]["ordered_failure_codes"] = ["INJECTED"]
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.reverify_witnesses(extracted["pairs"], env)
    assert excinfo.value.code == ev.FAMILY_CERTIFICATE_HASH_MISMATCH


def test_family_supplied_hash_altered_fails():
    extracted = _extracted()
    env = copy.deepcopy(extracted["family_certificate_envelope"])
    env["family_verifier_certificate_sha256"] = "0" * 64
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.reverify_witnesses(extracted["pairs"], env)
    assert excinfo.value.code == ev.FAMILY_CERTIFICATE_HASH_MISMATCH


def test_recomputed_vs_embedded_certificate_mismatch_fails(monkeypatch):
    # tamper the embedded payload AND make supplied==frozen hash consistent, so the failure is caught only
    # by the recomputed-vs-embedded equality check (not by the supplied/embedded hash checks)
    extracted = _extracted()
    env = copy.deepcopy(extracted["family_certificate_envelope"])
    tampered = dict(env["family_verifier_certificate"])
    tampered["ordered_failure_codes"] = ["INJECTED"]                    # differs from recomputed ([])
    new_hash = cjson.payload_sha256(tampered)
    env["family_verifier_certificate"] = tampered
    env["family_verifier_certificate_sha256"] = new_hash
    monkeypatch.setattr(frozen, "family_verifier_certificate_sha256", new_hash)
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.reverify_witnesses(extracted["pairs"], env)
    assert excinfo.value.code == ev.FAMILY_CERTIFICATE_HASH_MISMATCH


def test_wrong_frozen_family_hash_expectation_fails(monkeypatch):
    extracted = _extracted()
    monkeypatch.setattr(frozen, "family_verifier_certificate_sha256", "1" * 64)
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.reverify_witnesses(extracted["pairs"], extracted["family_certificate_envelope"])
    assert excinfo.value.code == ev.FAMILY_CERTIFICATE_HASH_MISMATCH


# ---- blocker 1: descriptor return-shape validation (synthetic monkeypatched returns only) ----
@pytest.mark.parametrize("bad", [np.zeros((1, 11)), np.zeros((11, 1)), np.zeros((1, 1, 11)),
                                 np.zeros(10), np.zeros(12), np.array(5.0)])
def test_descriptor_wrong_shape_rejected(monkeypatch, bad):
    monkeypatch.setattr(psi_trs, "psi_trs_features", lambda field, kappa, _v=bad: _v)
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.build_production_feature_cache()
    assert excinfo.value.code == ev.DESCRIPTOR_FEATURE_SCHEMA_INVALID


def test_descriptor_valid_shape_accepted(monkeypatch):
    monkeypatch.setattr(psi_trs, "psi_trs_features",
                        lambda field, kappa: np.arange(11, dtype=float))
    cache = ev.build_production_feature_cache()
    assert cache["descriptor_call_record"]["completed_descriptor_calls"] == 768
    assert cache["descriptor_call_record"]["attempted_descriptor_calls"] == 768
    for member_id, _c, _o, _r, _s in frozen.frozen_members:
        for variant in ev.VARIANTS:
            rows = cache["features"][member_id][variant]
            assert len(rows) == 64 and all(len(vec) == 11 for vec in rows)


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
def test_descriptor_nonfinite_rejected(monkeypatch, bad_value):
    vector = np.zeros(11, dtype=float)
    vector[3] = bad_value
    monkeypatch.setattr(psi_trs, "psi_trs_features", lambda field, kappa, _v=vector: _v.copy())
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.build_production_feature_cache()
    assert excinfo.value.code == ev.DESCRIPTOR_FEATURE_NONFINITE


def test_build_cache_descriptor_path_does_not_reshape():
    # the descriptor path (build_production_feature_cache) must not reshape/flatten/squeeze/ravel the raw
    # descriptor return; norm helpers elsewhere may legitimately reshape for L2 (parity with the old runner)
    with open(os.path.join(BV_DIR, "algebraic_n64_f3_evaluator_v0_1.py"), "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    target = [n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "build_production_feature_cache"]
    assert len(target) == 1
    banned = {"reshape", "flatten", "squeeze", "ravel"}
    for node in ast.walk(target[0]):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in banned


# ---- blocker 3: structured invalid-evidence failure records ----
def test_structured_failure_wrong_shape_records_member_variant_start():
    cache = _random_cache(20)
    cache["features"]["candidate_478_A"]["psi_trs"][7] = [[0.0]] * 11   # 11 non-numeric elements
    out = ev.evaluate_from_feature_cache(cache)
    record = out["failure_record"]
    assert record["failure_code"] == ev.DESCRIPTOR_FEATURE_SCHEMA_INVALID
    assert record["stage"] == "feature_cache_validation"
    assert record["member"] == "candidate_478_A"
    assert record["variant"] == "psi_trs"
    assert record["start"] == 7
    assert record["value_status"] == "schema_invalid"
    assert out["family_verdict"] == ev.INVALID_FAMILY_EVALUATION
    assert out["evaluation_pass"]["pairs"] == []                        # not a failed pair hypothesis


def test_structured_failure_wrong_length_records_member_variant_start():
    cache = _random_cache(21)
    cache["features"]["candidate_479_A"]["psi_trs_k0"][3] = [0.0] * 10
    record = ev.evaluate_from_feature_cache(cache)["failure_record"]
    assert record["failure_code"] == ev.DESCRIPTOR_FEATURE_SCHEMA_INVALID
    assert (record["member"], record["variant"], record["start"]) == ("candidate_479_A", "psi_trs_k0", 3)
    assert record["value_status"] == "schema_invalid"


def test_structured_failure_nonfinite_records_value_status():
    cache = _random_cache(22)
    cache["features"]["candidate_480_B"]["psi_trs"][31][2] = float("nan")
    out = ev.evaluate_from_feature_cache(cache)
    record = out["failure_record"]
    assert record["failure_code"] == ev.DESCRIPTOR_FEATURE_NONFINITE
    assert (record["member"], record["variant"], record["start"]) == ("candidate_480_B", "psi_trs", 31)
    assert record["value_status"] == "nonfinite"


def test_invalid_result_serializable_with_no_nan_and_record_survives():
    cache = _random_cache(23)
    cache["features"]["candidate_478_B"]["psi_trs_k0"][10][4] = float("inf")
    out = ev.evaluate_from_feature_cache(cache)
    assert out["family_verdict"] == ev.INVALID_FAMILY_EVALUATION
    # structured failure record survives into the pass payload
    assert out["evaluation_pass"]["failure_record"]["failure_code"] == ev.DESCRIPTOR_FEATURE_NONFINITE
    raw = ev.canonical_pass_bytes(out["evaluation_pass"])
    assert b"NaN" not in raw and b"Infinity" not in raw
    assert raw == cjson.canonical_json_bytes(json.loads(raw.decode("utf-8")))


def test_tampered_pair_certificate_hash_refused():
    envelope = _real_envelope()
    envelope["freeze_result"]["accepted_pair_certificate_envelopes"][0][
        "pair_verifier_certificate_sha256"] = "0" * 64
    # top-level freeze_result payload hash now differs -> caught first
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.validate_frozen_evidence(envelope)
    assert excinfo.value.code in (ev.FREEZE_RESULT_PAYLOAD_HASH_MISMATCH, ev.PAIR_CERTIFICATE_HASH_MISMATCH)


def test_support_mismatch_refused_via_frozen_override(monkeypatch):
    envelope = _real_envelope()
    # override the frozen expectation so the real support no longer matches -> FROZEN_SUPPORT_MISMATCH
    bad_pairs = list(frozen.frozen_pairs)
    bad_pairs[0] = (478, 0, (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
                    frozen.raw_support_478_B, frozen.pair_certificate_sha256[0])
    monkeypatch.setattr(frozen, "frozen_pairs", tuple(bad_pairs))
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.validate_frozen_evidence(envelope)
    assert excinfo.value.code == ev.FROZEN_SUPPORT_MISMATCH


def test_wrong_frozen_payload_hash_refused(monkeypatch):
    envelope = _real_envelope()
    monkeypatch.setattr(frozen, "freeze_result_payload_sha256", "1" * 64)
    with pytest.raises(ev.EvidenceError) as excinfo:
        ev.validate_frozen_evidence(envelope)
    assert excinfo.value.code == ev.FREEZE_RESULT_PAYLOAD_HASH_MISMATCH


# ----------------------------------------------------------------- serialization
def test_canonical_pass_serialization_no_trailing_newline():
    out = ev.evaluate_from_feature_cache(_constant_cache(_strong_pass_spec({478})))
    raw = ev.canonical_pass_bytes(out["evaluation_pass"])
    assert not raw.endswith(b"\n")
    assert raw == cjson.canonical_json_bytes(json.loads(raw.decode("utf-8")))
    assert raw.decode("utf-8").isascii()


# ----------------------------------------------------------------- import boundary / AST
def test_import_performs_no_descriptor_call_and_creates_no_file(tmp_path, monkeypatch):
    # importing the evaluator (already imported) must not have contacted psi; guard proves it at call time.
    # confirm module exposes exactly one descriptor call site in build_production_feature_cache.
    with open(os.path.join(BV_DIR, "algebraic_n64_f3_evaluator_v0_1.py"), "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    psi_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "psi_trs_features":
            psi_calls.append(node)
    assert len(psi_calls) == 1                                          # exactly one descriptor call site


def test_evaluator_import_boundary():
    with open(os.path.join(BV_DIR, "algebraic_n64_f3_evaluator_v0_1.py"), "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            roots.add(node.module.split(".")[0])
    assert roots.issubset({"__future__", "math", "typing", "numpy", "psi_trs",
                           "witness_canonical_json_v0_1", "witness_family_verifier_v0_1",
                           "algebraic_n64_f3_frozen_identity_v0_1"})
    for forbidden in ("run_n64_falsifier_v0_1", "witness_family_freeze_v0_1", "torment_service"):
        assert forbidden not in roots
    assert not any("generator" in r for r in roots)
