"""v1.2a tests: ordered-recurrence / continuity harness (offline).

Lock the MACHINERY and the mechanism-relevant invariants: offline-only, no service/runtime imports, RR matched
to RR_target, line of identity excluded (Lmax < T), symmetric DET is time-reversal invariant (reversed == true,
which is exactly WHY Tier B stays NA), shuffle lowers DET on a smooth field, near-flat cells neutral/excluded,
the rough-but-ordered probe is a planted recurrence anchor (high DET despite high roughness), and the harness
does NOT force a temporal PASS. These tests do NOT assert a specific PASS/FAIL/HOLD outcome (data-dependent) and
assert no vision/temporal-order claim. Offline; no torment_service.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_sag_recurrence_v1_2a as rec  # noqa: E402


def test_no_forbidden_imports():
    for fn in os.listdir(BV_DIR):
        if not fn.endswith(".py"):
            continue
        with open(os.path.join(BV_DIR, fn), encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=fn)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("torment"), f"{fn}: import {alias.name}"
                    assert "rsb_model" not in alias.name, f"{fn}: import {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("torment"), f"{fn}: from {mod}"
                assert "rsb_model" not in mod, f"{fn}: from {mod}"
                for alias in node.names:
                    assert alias.name != "RSBModel", f"{fn}: imports RSBModel"


def test_rr_matches_target_and_deterministic():
    wn = rec.cand.normalize(rec.generate_field("sine", 0))
    a, b = rec.rqa(wn), rec.rqa(wn)
    assert a == b                                   # deterministic
    assert abs(a["RR"] - rec.RR_TARGET) < 0.03      # RR matched to target by the eps rule


def test_line_of_identity_excluded():
    # the main diagonal (length T) must never be counted; Lmax must be < T for every window kind
    for kind in ("sine", "smooth_ramp", "rough_ordered"):
        wn = rec.cand.normalize(rec.generate_field(kind, 0))
        q = rec.rqa(wn)
        assert q["Lmax"] < wn.shape[0], f"{kind}: Lmax {q['Lmax']} >= T (LOI leaked)"


def test_symmetric_det_time_reversal_invariant():
    # reversing time transposes the recurrence matrix; symmetric DET is unchanged -> this is exactly why the
    # recurrence family cannot claim Tier B (arrow of time) from symmetric DET.
    wn = rec.cand.normalize(rec.generate_field("sine_phase_shift", 1))
    assert abs(rec.rqa(wn)["DET"] - rec.rqa(wn[::-1].copy())["DET"]) < 1e-9


def test_shuffle_lowers_det_on_smooth_field():
    wn = rec.cand.normalize(rec.generate_field("sine", 2))
    shuf = wn[np.random.default_rng(0).permutation(wn.shape[0])]
    assert rec.rqa(wn)["DET"] > rec.rqa(shuf)["DET"]


def test_near_flat_neutral_excluded():
    rows = rec.run_recurrence(fields=("constant", "sine"), n=2)
    assert any(r["neutral"] for r in rows if r["field"] == "constant")
    assert not any(r["neutral"] for r in rows if r["field"] == "sine")


def test_rough_ordered_probe_is_planted_recurrence_anchor():
    # dissociation anchor: the rough-but-ordered probe is ROUGH (high delta_rms) yet is a planted recurrence
    # anchor (high DET, well above a shuffled control) -> DET is not purely an inverse-roughness meter.
    wn = rec.cand.normalize(rec.generate_field("rough_ordered", 0))
    shuf = wn[np.random.default_rng(0).permutation(wn.shape[0])]
    dr_rough = rec.fa.cell_stats(rec.generate_field("rough_ordered", 0))["delta_rms"]
    dr_smooth = rec.fa.cell_stats(rec.generate_field("sine", 0))["delta_rms"]
    assert dr_rough > dr_smooth and dr_rough > 0.5    # genuinely rough (rougher than a smooth periodic field)
    assert rec.rqa(wn)["DET"] > rec.rqa(shuf)["DET"] + 0.2   # yet strongly ordered


def test_tier_b_is_na_and_no_forced_pass():
    res = rec.analyze(n=3)
    assert res["T4_tier_b"]["verdict"] == "NA"                 # no directional variant -> Tier B not claimable
    assert res["temporal_claim_allowed"] is False              # directional claim never set here
    assert res["verdict"] in ("PASS", "FAIL", "HOLD")
    # undirected claim is allowed only if BOTH invariance prereq and Tier A pass
    g = res["T5_gates"]
    assert res["undirected_order_claim_allowed"] == bool(
        g["roughness_invariance_prereq"] and g["tier_A_undirected_order"])


def test_t3_exposes_dissociation_subchecks():
    # the invariance pre-req must expose EACH predeclared dissociation subcheck, and invariance_pass must be the
    # exact AND of them (so a FAIL names its cause). Does not assert a specific pass/fail outcome.
    t3 = rec.analyze(n=3)["T3_roughness_invariance"]
    for k in ("ordered_beats_shuffle", "rough_high", "smooth_low", "spectrum_low", "corr_ok"):
        assert k in t3 and isinstance(t3[k], bool)
    assert t3["invariance_pass"] == bool(
        t3["ordered_beats_shuffle"] and t3["rough_high"] and t3["smooth_low"]
        and t3["spectrum_low"] and t3["corr_ok"])


def test_report_completes():
    s = rec.format_report(n=3)
    assert "v1.2a" in s and "VERDICT" in s and "Tier-B" in s and "NON-RESCUING" in s
