"""v1.1 tests: SAG failure-analysis harness (offline).

Lock the MACHINERY and the mechanism-relevant invariants of the v1.1 failure analysis: offline-only, no
service/runtime imports, deterministic stats, finite output, report completes, near-flat cells excluded, and
the rank-correlation helper is correct. Also lock the two facts the harness exists to surface: the v1.0
failure reproduces (pooled shuffled gain > true) and it co-occurs with higher temporal roughness (shuffled
delta_rms > true), while time_reversed preserves frame adjacency (reversed delta_rms == true). These tests do
NOT assert a temporal PASS, do NOT assert H1_SUPPORTED, and assert no diagnostic/vision claim. Offline; no
torment_service.
"""
import ast
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_sag_failure_analysis_v1_1 as fa  # noqa: E402


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


def test_spearman_helper_monotonic_and_ties():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert abs(fa._spearman(x, 2.0 * x + 1.0) - 1.0) < 1e-9      # perfect increasing
    assert abs(fa._spearman(x, -x) + 1.0) < 1e-9                 # perfect decreasing
    # average-tie ranks: [10,10,20,30] -> ranks [1.5,1.5,3,4]
    assert np.allclose(fa._rankdata(np.array([10.0, 10.0, 20.0, 30.0])), [1.5, 1.5, 3.0, 4.0])


def test_stats_deterministic():
    a = fa.run_analysis(n=2)
    b = fa.run_analysis(n=2)
    assert len(a) == len(b)
    for ra, rb in zip(a, b):
        assert ra["field"] == rb["field"] and ra["control"] == rb["control"] and ra["seed"] == rb["seed"]
        assert ra["sag_gain"] == rb["sag_gain"]
        for st in fa.STATS:
            assert (ra[st] == rb[st]) or (np.isnan(ra[st]) and np.isnan(rb[st]))


def test_near_flat_cells_excluded():
    rows = fa.run_analysis(fields=("constant", "white_noise", "sine"), n=2)
    a = fa.analyze(rows)
    assert a["neutral_count"] >= 1                     # constant gated to neutral
    assert not any(r["neutral"] for r in rows if r["field"] in ("white_noise", "sine"))
    # correlations + verdict keys present and finite-or-nan (never crash)
    assert set(fa.STATS) <= set(a["correlations"])
    assert a["verdict"]["verdict"] in ("H1_SUPPORTED", "H1_PARTIAL", "H1_NOT_SUPPORTED")


def test_reversed_preserves_roughness_shuffle_raises_it():
    # mechanism invariants on a temporally-smooth field (sine): time_reversal preserves the multiset of
    # frame-to-frame deltas (adjacency), so delta_rms is unchanged; shuffling decorrelates adjacent frames
    # and MUST raise delta_rms. This is the crux the harness exists to expose. No PASS is asserted.
    rows = fa.run_analysis(fields=("sine",), n=3)
    def med(control, key):
        return float(np.median([r[key] for r in rows if r["control"] == control and not r["neutral"]]))
    true_dr, rev_dr, shuf_dr = med("true", "delta_rms"), med("time_reversed", "delta_rms"), med("time_shuffled", "delta_rms")
    assert np.isclose(rev_dr, true_dr, rtol=1e-6)      # reversal preserves adjacency -> same roughness
    assert shuf_dr > true_dr                            # shuffle raises roughness


def test_pooled_failure_reproduces_and_cooccurs_with_roughness():
    a = fa.analyze(fa.run_analysis(n=4))
    pc = a["per_control"]
    # v1.0 failure reproduced at pooled level: shuffled gain far exceeds true gain
    assert pc["time_shuffled"]["sag_gain"] > pc["true"]["sag_gain"]
    # ...and it co-occurs with higher temporal roughness (the explanation, not a temporal-order rescue)
    assert pc["time_shuffled"]["delta_rms"] > pc["true"]["delta_rms"]
    assert pc["time_shuffled"]["temporal_continuity"] < pc["true"]["temporal_continuity"]
    v = a["verdict"]
    assert v["gain_top_control"] == "time_shuffled" and v["delta_rms_top_control"] == "time_shuffled"


def test_report_completes_and_makes_no_diagnostic_claim():
    s = fa.format_report(n=3)
    assert "FAILURE ANALYSIS" in s and "predeclared verdict" in s
    assert "no new diagnostic proposed or built" in s
    assert "temporal-order" in s  # the reading explicitly frames the non-specificity
