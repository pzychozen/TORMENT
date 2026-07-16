"""Focused tests for the boundary-neutral companion (v0.7 O1+A3 contract; v0.8 opt-in).

Small deterministic in-memory structural arrays are UNIT-TEST INPUTS ONLY -- not scientific fixtures and
not evidence. No experiment is run and no prerecorded .npz fixture is analyzed. Offline; no torment_service.
The suite proves the v0.7/v0.8 companion contract: matched-pair rotation, all-64-start O1 aggregation (A3
mean), the exact valid_d(s) predicate and unavailability propagation, raw denominator diagnostics, raw
preservation, block-scoped output with no cross-block aggregation, CLI opt-in orthogonality, and s=0
independent recomputation.

Cost note: O1 evaluates all 64 starts per block x control x descriptor, so the full-companion result is
computed ONCE in a module-scoped fixture and reused; helper-level behaviours use single 64-row blocks.
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

CD = ("psi_trs", "psi_trs_k0")


def _structural_field(rows, channels=4, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(rows, dtype=float)
    cols = []
    for c in range(channels):
        cols.append(np.sin(2 * np.pi * (1 + c) * t / 37.0 + 0.3 * c)
                    + 0.15 * rng.standard_normal(rows) + 0.05 * t / max(rows, 1))
    return np.stack(cols, axis=1)


def _eval_one(fn, x_true, x_control):
    """Mirror the companion per-start loop for a single descriptor: returns (per_start, denoms, valids)."""
    per_start, denoms, valids = [], [], []
    for s in range(64):
        t_s = np.roll(x_true, -s, axis=0)
        c_s = np.roll(x_control, -s, axis=0)
        f_true = np.asarray(fn(t_s), float)
        f_ctrl = np.asarray(fn(c_s), float)
        n = float(np.linalg.norm(f_true.reshape(-1)))
        eff = max(n, ppa.EPSILON)
        num = float(np.linalg.norm((f_ctrl - f_true).reshape(-1)))
        q = num / eff
        valid = bool(np.all(np.isfinite(f_true)) and np.all(np.isfinite(f_ctrl))
                     and math.isfinite(n) and math.isfinite(eff) and math.isfinite(q))
        per_start.append(float(q) if valid else None)
        denoms.append(n)
        valids.append(valid)
    return per_start, denoms, valids


# ---- heavy full-companion results computed ONCE and reused ----
@pytest.fixture(scope="module")
def field2():
    return _structural_field(128, 4)                                   # 128 rows -> 2 complete 64-row blocks


@pytest.fixture(scope="module")
def raw_clip(field2):
    return ppa.analyze_descriptor_field(field2, 0, "unit_a", with_companion=False)


@pytest.fixture(scope="module")
def comp_clip(field2):
    return ppa.analyze_descriptor_field(field2, 0, "unit_a", with_companion=True)


@pytest.fixture(scope="module")
def comp_json(comp_clip):
    return ppa._jsonable(ppa.build_result([comp_clip]))


# ----------------------------- CLI opt-in + default preservation -----------------------------
def test_cli_flag_defaults_off_and_parses():
    assert ppa._build_parser().parse_args([]).with_boundary_neutral_companion is False
    assert ppa._build_parser().parse_args(
        ["--with-boundary-neutral-companion"]).with_boundary_neutral_companion is True


def test_default_result_has_no_companion(raw_clip):
    assert "boundary_neutral_companion" not in raw_clip
    result = ppa._jsonable(ppa.build_result([raw_clip]))
    assert "boundary_neutral_companion" not in json.dumps(result)
    assert "BOUNDARY-NEUTRAL COMPANION" not in ppa.format_report(result)


def test_main_threads_flag_and_no_write(tmp_path, monkeypatch):
    captured = {}

    def fake_analyze_paths(paths, include_sag=True, with_companion=False):
        captured.update(include_sag=include_sag, with_companion=with_companion)
        return ppa._jsonable(ppa.build_result([]))

    monkeypatch.setattr(ppa, "analyze_paths", fake_analyze_paths)
    monkeypatch.chdir(tmp_path)
    before = set(os.listdir(tmp_path))
    rc = ppa.main(["--with-boundary-neutral-companion", "--no-sag", "clip.npz"])
    assert rc == 0
    assert captured == {"include_sag": False, "with_companion": True}   # orthogonal to --no-sag
    assert set(os.listdir(tmp_path)) == before                          # no file writing


def test_raw_subtrees_unchanged_when_enabled(raw_clip, comp_clip):
    for key in ("descriptor_responses", "recursive_delta", "response_normalization_diagnostics",
                "control_ranks", "sag", "transform_cache", "finite_summary", "blocks"):
        assert comp_clip[key] == raw_clip[key]                          # additive only; raw untouched
    assert "boundary_neutral_companion" in comp_clip


# ----------------------------- structure, domain, block identity, no cross-block -----------------------------
def test_structure_domain_and_block_identity(comp_clip):
    comp = comp_clip["boundary_neutral_companion"]
    assert comp["included"] is True
    assert comp["descriptor_domain"] == ["psi_trs", "psi_trs_k0"]
    assert comp["offset_policy"] == "O1 — all 64 starts"
    assert comp["aggregation_policy"] == "A3 — mean normalized response across matched starts"
    for control in ppa.CONTROLS:
        per_block = comp["per_control"][control]["per_block"]
        assert [e["block"] for e in per_block] == [0, 1]                # explicit ascending block identity
        for e in per_block:
            assert set(e.keys()) >= {
                "block", "psi_trs", "psi_trs_k0", "companion_response_psi_trs",
                "companion_response_psi_trs_k0", "companion_recursive_delta",
                "raw_minus_companion_psi_trs", "raw_minus_companion_psi_trs_k0",
                "raw_minus_companion_recursive_delta"}
            assert "frame_diff" not in e and "plain_fft" not in e and "descriptor_only" not in e
            for d in CD:
                assert e[d]["number_of_starts"] == 64
                assert len(e[d]["per_start_responses"]) == 64          # all 64 in canonical index order


def test_no_cross_block_or_clip_level_aggregation(comp_clip):
    comp = comp_clip["boundary_neutral_companion"]
    for control in ppa.CONTROLS:
        assert set(comp["per_control"][control].keys()) == {"per_block"}   # only per_block, no control scalar
    assert not (set(comp.keys()) & {"companion_response_psi_trs", "companion_recursive_delta",
                                    "mean", "median"})


def test_block_length_is_64_only(comp_clip):
    assert ppa.BLOCK_LEN == 64
    comp = comp_clip["boundary_neutral_companion"]
    for control in ppa.CONTROLS:
        for entry in comp["per_control"][control]["per_block"]:
            for d in CD:
                assert entry[d]["number_of_starts"] == 64


# ----------------------------- matched pairing + s=0 independent recompute -----------------------------
def test_same_rotated_arrays_supplied_to_both_descriptors():
    x_true = _structural_field(64, 4)
    x_ctrl = np.roll(x_true, 5, axis=0)
    # store the actual array OBJECTS (references kept for the whole test so object ids cannot be reused)
    seen = {"psi_trs": [], "psi_trs_k0": []}

    def spy(name):
        def fn(arr):
            seen[name].append(arr)
            return np.asarray(arr, float).mean(axis=0)
        return fn

    ppa._companion_evaluate_block_control({"psi_trs": spy("psi_trs"), "psi_trs_k0": spy("psi_trs_k0")},
                                          x_true, x_ctrl)
    assert len(seen["psi_trs"]) == 64 * 2 and len(seen["psi_trs_k0"]) == 64 * 2   # all 64 offsets x (T_s, C_s)
    # for every paired offset evaluation the SAME object (identity) went to both descriptors, in order
    for psi_arr, k0_arr in zip(seen["psi_trs"], seen["psi_trs_k0"]):
        assert psi_arr is k0_arr                                        # T_s / C_s object identity, not just id()


def test_s0_independently_recomputed_not_reused():
    x_true = _structural_field(64, 4)
    x_ctrl = np.roll(x_true, 5, axis=0)
    seen = []

    def fn(arr):
        seen.append(arr)
        return np.asarray(arr, float).mean(axis=0)

    ppa._companion_evaluate_block_control({"psi_trs": fn, "psi_trs_k0": fn}, x_true, x_ctrl)
    assert len(seen) == 64 * 2 * 2                                     # 2 descriptors x 64 starts x 2 arrays
    assert any(np.array_equal(a, x_true) and a is not x_true for a in seen)   # s=0: fresh roll, not reuse
    assert any(np.array_equal(a, x_ctrl) and a is not x_ctrl for a in seen)


def test_offset_and_descriptor_order_independence():
    x_true = _structural_field(64, 4)
    x_ctrl = np.roll(x_true, 3, axis=0)
    ex = ppa.default_extractors()
    forward = {"psi_trs": ex["psi_trs"], "psi_trs_k0": ex["psi_trs_k0"]}
    reverse = {"psi_trs_k0": ex["psi_trs_k0"], "psi_trs": ex["psi_trs"]}
    a = ppa._companion_evaluate_block_control(forward, x_true, x_ctrl)
    b = ppa._companion_evaluate_block_control(reverse, x_true, x_ctrl)
    for name in CD:
        assert a[name][0] == b[name][0]                                # identical records regardless of order


# ----------------------------- rotation invariance -----------------------------
def test_global_rotation_invariance_scalar_and_permutation():
    x_true = _structural_field(64, 4)
    x_ctrl = np.roll(x_true, 9, axis=0)
    fn = ppa.default_extractors()["psi_trs"]
    k = 7
    rec0, resp0 = ppa._companion_summarize(*_eval_one(fn, x_true, x_ctrl))
    reck, respk = ppa._companion_summarize(
        *_eval_one(fn, np.roll(x_true, -k, axis=0), np.roll(x_ctrl, -k, axis=0)))
    assert resp0 == pytest.approx(respk, rel=1e-9, abs=1e-12)                     # scalar invariant
    assert sorted(rec0["per_start_responses"]) == pytest.approx(sorted(reck["per_start_responses"]))
    for s in range(64):                                                          # q'(s) = q((s+k) mod 64)
        assert reck["per_start_responses"][s] == pytest.approx(
            rec0["per_start_responses"][(s + k) % 64], rel=1e-9, abs=1e-12)


# ----------------------------- immutability -----------------------------
def test_inputs_and_cache_not_mutated():
    field = _structural_field(128, 4)
    field_snapshot = field.copy()
    bc, _ = ppa.compute_block_caches(field, 0)
    _s, per, _raw = ppa.descriptor_responses(bc)
    rec = ppa.recursive_delta(per)
    true_snaps = [blk["cache"]["true"]["array"].copy() for blk in bc]
    ctrl_snaps = [{c: blk["cache"][c]["array"].copy() for c in ppa.CONTROLS} for blk in bc]
    ppa.boundary_neutral_companion(bc, per, rec)
    np.testing.assert_array_equal(field, field_snapshot)
    for i, blk in enumerate(bc):
        np.testing.assert_array_equal(blk["cache"]["true"]["array"], true_snaps[i])
        for c in ppa.CONTROLS:
            np.testing.assert_array_equal(blk["cache"][c]["array"], ctrl_snaps[i][c])


# ----------------------------- multiplicity / constant / periodic -----------------------------
def test_constant_array_scalar_invariant_multiplicity_retained():
    x = np.ones((64, 4), dtype=float)                                  # every rotation identical
    fn = ppa.default_extractors()["psi_trs"]
    rec, resp = ppa._companion_summarize(*_eval_one(fn, x, x))
    assert len(rec["per_start_responses"]) == 64                       # 64 kept (no dedup)
    assert all(v == pytest.approx(0.0) for v in rec["per_start_responses"])
    assert resp == pytest.approx(0.0)


def test_periodic_array_retains_multiplicity():
    t = np.arange(64)
    x = np.stack([np.sin(2 * np.pi * (t % 8) / 8.0) for _ in range(4)], axis=1)   # period 8 | 64
    fn = ppa.default_extractors()["psi_trs"]
    rec, _resp = ppa._companion_summarize(*_eval_one(fn, x, np.roll(x, 3, axis=0)))
    assert len(rec["per_start_responses"]) == 64                       # duplicates remain separate observations
    assert rec["finite_count"] + rec["nonfinite_count"] == 64


# ----------------------------- validity predicate + unavailability -----------------------------
def test_one_invalid_start_invalidates_distribution_and_scalar():
    x = _structural_field(64, 4)
    call = {"n": 0}

    def bad(arr):
        call["n"] += 1
        v = np.asarray(arr, float).mean(axis=0)
        if call["n"] == 5:                                             # make one descriptor call nonfinite
            v = v.copy(); v[0] = np.inf
        return v

    rec, resp = ppa._companion_summarize(*_eval_one(bad, x, np.roll(x, 2, axis=0)))
    assert rec["nonfinite_count"] >= 1 and rec["offending_nonfinite_offsets"]
    for f in ("mean", "median", "IQR", "minimum", "maximum", "mean_median_ratio"):
        assert rec[f] is None                                         # distribution unavailable, not finite-filtered
    assert resp is None
    for s in rec["offending_nonfinite_offsets"]:
        assert rec["per_start_responses"][s] is None


def test_all_valid_but_aggregate_overflow_keeps_counts():
    # Every start valid (finite q), but the arithmetic mean overflows to +inf: the affected derived scalar
    # (mean == companion_response) is unavailable while finite_count/nonfinite_count are untouched.
    per_start = [1e307] * 64
    with pytest.warns(RuntimeWarning, match="overflow encountered"):  # the overflow is intentional and expected
        rec, resp = ppa._companion_summarize(per_start, [1.0] * 64, [True] * 64)
    assert rec["finite_count"] == 64 and rec["nonfinite_count"] == 0  # counts unchanged by aggregate overflow
    assert rec["mean"] is None and resp is None                       # mean overflowed -> unavailable
    assert rec["minimum"] == pytest.approx(1e307) and rec["maximum"] == pytest.approx(1e307)  # min/max finite


def test_zero_median_ratio_unavailable():
    x = np.ones((64, 4), dtype=float)
    fn = ppa.default_extractors()["psi_trs"]
    rec, _r = ppa._companion_summarize(*_eval_one(fn, x, x))          # all q=0 -> median 0
    assert rec["median"] == pytest.approx(0.0)
    assert rec["mean_median_ratio"] is None                           # median == 0 -> ratio unavailable


def test_delta_and_raw_minus_propagate_unavailability():
    assert ppa._sub_if_available(1.0, None) is None
    assert ppa._sub_if_available(None, 1.0) is None
    assert ppa._sub_if_available(float("inf"), 1.0) is None
    assert ppa._sub_if_available(2.0, 0.5) == pytest.approx(1.5)      # null never used in arithmetic


# ----------------------------- denominator diagnostics (raw, not effective) -----------------------------
def test_denominator_diagnostics_use_raw_not_effective():
    zero_true = np.zeros((64, 4), dtype=float)                        # f_true norm 0 for every start
    fn = lambda arr: np.asarray(arr, float).mean(axis=0)             # noqa: E731
    rec, _r = ppa._companion_summarize(*_eval_one(fn, zero_true, np.ones((64, 4))))
    assert rec["epsilon_hit_count"] == 64                             # raw n_d(s) == 0 <= EPSILON
    assert rec["near_epsilon_hit_count"] == 64                        # near-epsilon includes epsilon hits
    assert rec["minimum_denominator"] == pytest.approx(0.0)          # raw 0, NOT the EPSILON floor
    assert rec["maximum_denominator"] == pytest.approx(0.0)


# ----------------------------- JSON safety / no forbidden fields / locks -----------------------------
def test_json_safe_all_64_and_no_nan_infinity(comp_clip):
    clip = ppa._jsonable(comp_clip)
    json.dumps(clip, allow_nan=False)                                # raises if any NaN/Infinity present
    comp = clip["boundary_neutral_companion"]
    for control in ppa.CONTROLS:
        for entry in comp["per_control"][control]["per_block"]:
            for d in CD:
                pr = entry[d]["per_start_responses"]
                assert len(pr) == 64
                assert all((x is None) or (isinstance(x, float) and math.isfinite(x)) for x in pr)


def test_no_inferential_tokens_in_companion(comp_clip):
    # scope the check to the companion subtree itself (the surrounding result legitimately carries the
    # standing/lock fields that DISCLAIM inference, e.g. independent_inference_authorized=False).
    blob = json.dumps(ppa._jsonable(comp_clip["boundary_neutral_companion"]))
    for tok in ("balanced_accuracy", "classifier", "cross_validation", "prediction", "significance",
                "inference"):
        assert tok not in blob, tok
    for tok in ("train", "test", "fold", "label"):
        assert re.search(r"\b" + tok + r"\b", blob) is None, tok


def test_locks_unchanged_with_companion(comp_json):
    assert comp_json["locks"] == {
        "FORMAL_HOLD_active": True, "Mode_0_active": True, "verdict": "HOLD",
        "bounded_experiment_ready": False, "Brainvision_perceptual_claim_ready": False,
        "runtime_integration_authorized": False, "new_scientific_claim_authorized": False}
    for k in ("independent_inference_authorized", "temporal_order_claim_authorized",
              "recursive_time_claim_authorized", "perception_claim_authorized",
              "scientific_evidence_generated"):
        assert comp_json[k] is False


# ----------------------------- human reporting -----------------------------
def test_human_reports_each_block_control_and_points_to_json(comp_json):
    text = ppa.format_report(comp_json)
    assert "BOUNDARY-NEUTRAL COMPANION" in text
    assert "block=0 control=true" in text and "block=1 control=time_shuffled" in text
    assert "Rerun with --format json" in text
    assert "per_start_responses" not in text                          # 64 values not dumped in human output
    # interpretation check scoped to the companion section (the report's pre-existing NON-CLAIM disclaimer
    # legitimately mentions "scientific superiority").
    clip = comp_json["clips"][0]
    comp_text = "\n".join(ppa._format_companion_lines(
        clip, clip["boundary_neutral_companion"], comp_json["controls"]))
    for banned in ("superiority", "arrow of time", "perception", "temporal-order", "significance"):
        assert banned not in comp_text
    assert text.encode("utf-8").decode("utf-8") == text               # UTF-8 safe
