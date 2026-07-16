"""Focused tests for the prerecorded paired analyzer v0.1 (offline; unit-only).

Small deterministic in-memory structural arrays are UNIT-TEST INPUTS ONLY -- not scientific fixtures and
not evidence. These tests do not run the full benchmark, assert no scientific correctness, require no
local .npz, and hard-code no machine-specific absolute paths. Offline; no torment_service.
"""
import json
import math
import os
import re
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_prerecorded_paired_analysis_v0_1 as ppa  # noqa: E402


def _structural_field(rows, channels=6, seed=0):
    """Deterministic, non-degenerate (rows, channels) structural array. UNIT-TEST INPUT ONLY."""
    rng = np.random.default_rng(seed)
    t = np.arange(rows, dtype=float)
    cols = []
    for c in range(channels):
        cols.append(np.sin(2 * np.pi * (1 + c) * t / 37.0 + 0.3 * c)
                    + 0.15 * rng.standard_normal(rows)
                    + 0.05 * t / max(rows, 1))
    return np.stack(cols, axis=1)


# ----------------------------- 1-2: block extraction -----------------------------
def test_non_overlapping_64_row_block_extraction():
    field = _structural_field(192, 6)
    raw, info = ppa.non_overlapping_blocks(field)
    assert info["complete_block_count"] == 3
    assert info["block_index_ranges"] == [[0, 64], [64, 128], [128, 192]]
    assert info["descriptor_row_count"] == 192
    assert all(block.shape == (64, 6) for block in raw)
    # non-overlapping: consecutive ranges abut, never overlap
    assert all(raw_next_start == prev_end
               for (_, prev_end), (raw_next_start, _) in zip(info["block_index_ranges"],
                                                             info["block_index_ranges"][1:]))


def test_incomplete_trailing_rows_discarded_and_counted():
    field = _structural_field(200, 6)
    raw, info = ppa.non_overlapping_blocks(field)
    assert info["complete_block_count"] == 3
    assert info["discarded_trailing_rows"] == 8
    assert info["block_index_ranges"][-1] == [128, 192]
    assert len(raw) == 3


# ----------------------------- 3: shared cached array for every descriptor -----------------------------
def test_every_descriptor_receives_the_same_cached_array():
    field = _structural_field(128, 6)
    block_caches, _info = ppa.compute_block_caches(field, clip_ordinal=0)
    seen = {}

    def make_spy(name):
        def spy(arr):
            seen.setdefault(name, []).append(id(arr))
            return np.asarray(arr, dtype=float).mean(axis=0)  # trivial deterministic feature
        return spy

    names = ["alpha", "beta", "gamma"]
    ppa.descriptor_responses(block_caches, extractors={n: make_spy(n) for n in names})

    expected_ids = []
    for blk in block_caches:
        expected_ids.append(id(blk["cache"]["true"]["array"]))       # f_true call
        for control in ppa.CONTROLS:                                  # per-control calls
            expected_ids.append(id(blk["cache"][control]["array"]))
    for name in names:
        assert seen[name] == expected_ids  # identical objects, identical call sequence, for every descriptor


# ----------------------------- 4: determinism across two runs -----------------------------
def test_transform_generation_deterministic_two_runs():
    field = _structural_field(128, 6)
    bc1, _ = ppa.compute_block_caches(field, 0)
    bc2, _ = ppa.compute_block_caches(field, 0)
    for a, b in zip(bc1, bc2):
        for c in ppa.CONTROLS:
            assert a["cache"][c]["array_sha256"] == b["cache"][c]["array_sha256"]
            np.testing.assert_array_equal(a["cache"][c]["array"], b["cache"][c]["array"])


def test_full_analysis_deterministic_and_json_safe():
    field = _structural_field(192, 6)
    r1 = ppa._jsonable(ppa.build_result([ppa.analyze_descriptor_field(field, 0, "unit_a")]))
    r2 = ppa._jsonable(ppa.build_result([ppa.analyze_descriptor_field(field, 0, "unit_a")]))
    s1 = json.dumps(r1, sort_keys=True)
    s2 = json.dumps(r2, sort_keys=True)
    assert s1 == s2  # deterministic + JSON-serializable (JSON-safe)


# ----------------------------- 5: independent of descriptor evaluation order -----------------------------
def test_transform_generation_independent_of_descriptor_order():
    field = _structural_field(128, 6)
    bc, _ = ppa.compute_block_caches(field, 0)
    hashes_before = [{c: bc[i]["cache"][c]["array_sha256"] for c in ppa.CONTROLS} for i in range(len(bc))]
    ex = ppa.default_extractors()
    forward = dict(ex)
    reverse = {k: ex[k] for k in reversed(list(ex.keys()))}
    _s_fwd, per_fwd, _raw_fwd = ppa.descriptor_responses(bc, extractors=forward)
    _s_rev, per_rev, _raw_rev = ppa.descriptor_responses(bc, extractors=reverse)
    hashes_after = [{c: bc[i]["cache"][c]["array_sha256"] for c in ppa.CONTROLS} for i in range(len(bc))]
    assert hashes_before == hashes_after                 # descriptors never mutate/advance the cache
    for name in ex:
        assert per_fwd[name] == per_rev[name]            # responses identical regardless of order


# ----------------------------- 6: no builtin hash() for seed derivation -----------------------------
def test_no_builtin_hash_for_seed_derivation():
    with open(ppa.__file__, encoding="utf-8") as fh:
        src = fh.read()
    assert "hash(" not in src            # builtin hash() (process-randomized) never used
    assert "SeedSequence" in src         # stable integer seed construction is used


# ----------------------------- 7: inputs not mutated -----------------------------
def test_input_arrays_not_mutated():
    field = _structural_field(128, 6)
    snapshot = field.copy()
    ppa.analyze_descriptor_field(field, 0, "unit_a")
    np.testing.assert_array_equal(field, snapshot)


# ----------------------------- 8: true response is zero -----------------------------
def test_true_normalized_response_is_zero():
    field = _structural_field(128, 6)
    clip = ppa.analyze_descriptor_field(field, 0, "unit_a")
    for name in clip["descriptors"]:
        for v in clip["descriptor_responses"][name]["true"]["per_block"]:
            assert abs(v) < 1e-12


# ----------------------------- 9: finite for valid finite input -----------------------------
def test_all_numeric_values_finite_for_finite_input():
    field = _structural_field(192, 6)
    result = ppa._jsonable(ppa.build_result([ppa.analyze_descriptor_field(field, 0, "unit_a")]))

    def walk(o):
        if isinstance(o, float):
            assert math.isfinite(o)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(result)
    # the core paired responses specifically must be fully finite (no None) for valid finite input
    for clip in result["clips"]:
        for name in clip["descriptors"]:
            for control in ppa.CONTROLS:
                pb = clip["descriptor_responses"][name][control]["per_block"]
                assert all(isinstance(x, float) and math.isfinite(x) for x in pb)


# ----------------------------- 10: recursive_delta uses matched responses -----------------------------
def test_recursive_delta_uses_matched_paired_responses():
    field = _structural_field(192, 6)
    clip = ppa.analyze_descriptor_field(field, 0, "unit_a")
    resp = clip["descriptor_responses"]
    rd = clip["recursive_delta"]["per_control"]
    for control in ppa.CONTROLS:
        psi = resp["psi_trs"][control]["per_block"]
        k0 = resp["psi_trs_k0"][control]["per_block"]
        expected = [p - q for p, q in zip(psi, k0)]
        assert rd[control]["per_block"] == pytest.approx(expected, rel=0, abs=0)


# ----------------------------- 11: no inferential mechanisms emitted -----------------------------
def test_no_inferential_tokens_outside_non_claim():
    field = _structural_field(128, 6)
    result = ppa._jsonable(ppa.build_result([ppa.analyze_descriptor_field(field, 0, "unit_a")]))
    non_claim = result.pop("non_claims")
    blob = json.dumps(result, sort_keys=True)
    for tok in ("balanced_accuracy", "classifier", "cross_validation", "prediction"):
        assert tok not in blob, tok
    for tok in ("train", "test", "fold", "label"):
        assert re.search(r"\b" + tok + r"\b", blob) is None, tok
    # the inferential vocabulary is present ONLY in the explicit non-claim
    for tok in ("classifier", "balanced_accuracy", "cross_validation", "ABSENT"):
        assert tok in non_claim


# ----------------------------- 12: default execution writes no files -----------------------------
def test_default_execution_writes_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    canned = ppa._jsonable(ppa.build_result([]))
    monkeypatch.setattr(ppa, "analyze_paths", lambda paths, include_sag=True: canned)
    before = set(os.listdir(tmp_path))
    rc = ppa.main(["fake_clip.npz"])          # printing only; analyze_paths mocked (no real .npz needed)
    after = set(os.listdir(tmp_path))
    assert rc == 0
    assert before == after                    # no result files created implicitly


# ----------------------------- 13: standing + lock fields present -----------------------------
def test_standing_and_lock_fields_present():
    result = ppa.build_result([])
    assert result["analysis_type"] == "DESCRIPTIVE_PAIRED_ENGINEERING_ANALYSIS"
    for key in ("independent_inference_authorized", "temporal_order_claim_authorized",
                "recursive_time_claim_authorized", "perception_claim_authorized",
                "scientific_evidence_generated"):
        assert result[key] is False
    locks = result["locks"]
    assert locks["FORMAL_HOLD_active"] is True
    assert locks["Mode_0_active"] is True
    assert locks["verdict"] == "HOLD"
    for key in ("bounded_experiment_ready", "Brainvision_perceptual_claim_ready",
                "runtime_integration_authorized", "new_scientific_claim_authorized"):
        assert locks[key] is False
    assert isinstance(result["non_claims"], str) and "ABSENT" in result["non_claims"]


# ----------------------------- 14: formatter deterministic + UTF-8 safe -----------------------------
def test_format_report_deterministic_and_utf8_safe():
    field = _structural_field(192, 6)
    result = ppa._jsonable(ppa.build_result([ppa.analyze_descriptor_field(field, 0, "unit_a")]))
    a = ppa.format_report(result)
    b = ppa.format_report(result)
    assert a == b                                  # deterministic
    assert a.encode("utf-8").decode("utf-8") == a  # UTF-8 safe round trip
    assert isinstance(a, str) and len(a) > 0


# ----------------------------- SAG: same cached arrays + metadata matching -----------------------------
def test_sag_variants_receive_the_same_cached_control_arrays(monkeypatch):
    field = _structural_field(128, 6)
    block_caches, _ = ppa.compute_block_caches(field, 0)
    captured = []
    real_eval = ppa._rvd.evaluate_sag_real

    def spy_eval(arrays, *a, **k):
        captured.append([id(x) for x in arrays])
        return real_eval(arrays, *a, **k)

    monkeypatch.setattr(ppa._rvd, "evaluate_sag_real", spy_eval)
    ppa.sag_control_analysis(block_caches)
    assert len(captured) == len(ppa.CONTROLS)          # one SAG call per control
    for control, ids in zip(ppa.CONTROLS, captured):
        assert ids == [id(blk["cache"][control]["array"]) for blk in block_caches]


def test_transform_metadata_matches_cached_arrays():
    field = _structural_field(128, 6)
    block_caches, _ = ppa.compute_block_caches(field, 0)
    for blk in block_caches:
        for control in ppa.CONTROLS:
            assert blk["cache"][control]["metadata_consistent"] is True


# ----------------------------- response-normalization diagnostics -----------------------------
def test_near_zero_denominator_diagnostics():
    # Injected extractor: ZERO true feature vector, NONZERO control feature vector. Does not rely on the
    # real Brainvision descriptors ever producing a zero norm.
    field = _structural_field(64, 6)                       # exactly one 64-row block
    bc, _info = ppa.compute_block_caches(field, 0)
    true_obj = bc[0]["cache"]["true"]["array"]

    def degenerate(arr):
        if arr is true_obj:                                # the cached TRUE array -> zero true feature
            return np.zeros(3)
        return np.array([1.0, 2.0, 3.0])                   # any control array -> nonzero feature

    extractors = {"degenerate": degenerate}
    summary, per, raw = ppa.descriptor_responses(bc, extractors=extractors)
    diag = ppa.build_normalization_diagnostics(
        "unit_clip", list(extractors.keys()), ppa.CONTROLS, len(bc),
        raw["true_feature_norms"], raw["raw_numerators"], per)

    pd = diag["per_descriptor"]["degenerate"]
    assert pd["epsilon_hit_count"] == 1                     # the single block's raw denominator is 0 <= eps
    assert pd["near_epsilon_count"] == 1                    # includes the epsilon hit (threshold >= eps)
    assert pd["min_true_feature_norm"] == pytest.approx(0.0, abs=0.0)

    lr = diag["largest_response"]
    assert lr["descriptor"] == "degenerate"
    assert lr["control"] == "time_shuffled"                # first non-true control under block/control order
    assert lr["block"] == 0
    assert lr["raw_numerator"] == pytest.approx(math.sqrt(14.0))      # L2([1,2,3] - [0,0,0])
    assert lr["raw_denominator"] == pytest.approx(0.0, abs=0.0)
    assert lr["effective_denominator"] == pytest.approx(ppa.EPSILON)
    assert lr["normalized_response"] == pytest.approx(lr["raw_numerator"] / lr["effective_denominator"])
    assert diag["epsilon_hit_total"] == 1 and diag["near_epsilon_total"] == 1


def test_non_degenerate_normalization_diagnostics():
    field = _structural_field(192, 6)
    clip = ppa.analyze_descriptor_field(field, 0, "unit_a")
    diag = clip["response_normalization_diagnostics"]
    assert diag["epsilon"] == ppa.EPSILON
    assert diag["near_epsilon_threshold"] == ppa.NEAR_EPSILON_THRESHOLD == 1e-9
    for _name, pd in diag["per_descriptor"].items():
        assert pd["epsilon_hit_count"] == 0
        assert pd["near_epsilon_count"] == 0
        assert math.isfinite(pd["min_true_feature_norm"])
        assert pd["min_true_feature_norm"] > ppa.NEAR_EPSILON_THRESHOLD
    lr = diag["largest_response"]
    for key in ("normalized_response", "raw_numerator", "raw_denominator", "effective_denominator"):
        assert math.isfinite(lr[key])
    assert lr["effective_denominator"] == max(lr["raw_denominator"], ppa.EPSILON)
    assert lr["normalized_response"] == pytest.approx(
        lr["raw_numerator"] / lr["effective_denominator"], rel=1e-12, abs=1e-15)
    assert diag["epsilon_hit_total"] == 0 and diag["near_epsilon_total"] == 0


def test_normalization_diagnostics_deterministic_and_formatted():
    field = _structural_field(192, 6)
    r1 = ppa._jsonable(ppa.build_result([ppa.analyze_descriptor_field(field, 0, "unit_a")]))
    r2 = ppa._jsonable(ppa.build_result([ppa.analyze_descriptor_field(field, 0, "unit_a")]))
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)          # deterministic + JSON-safe
    assert "response_normalization_diagnostics" in r1                                 # top-level aggregate
    assert "response_normalization_diagnostics" in r1["clips"][0]                     # per-clip auditability
    # numeric diagnostic fields remain numbers (not formatted strings) in the structured dict
    lr = r1["response_normalization_diagnostics"]["largest_response"]
    for key in ("normalized_response", "raw_numerator", "raw_denominator", "effective_denominator"):
        assert isinstance(lr[key], float)
    a = ppa.format_report(r1)
    b = ppa.format_report(r1)
    assert a == b                                                                     # deterministic formatting
    assert "NORMALIZATION SAFETY" in a and "near_epsilon_threshold" in a
    assert "largest normalized response" in a and "raw_numerator" in a
    assert a.encode("utf-8").decode("utf-8") == a                                     # UTF-8 safe
