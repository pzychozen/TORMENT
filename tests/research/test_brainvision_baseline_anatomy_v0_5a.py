"""v0.5a tests: baseline anatomy diagnostic (form A, NON-LEARNING; EXPLANATORY-only; offline).

Lock the v0.5a slice to ROBUST facts: it inspects ONLY the four frozen matched groups (spectral excluded as a
closure group); it REUSES/PRESERVES the exact v0.4d sealed matched held-out pairs (no rerun with new params, no
replaced pair, no changed family/grid/seed, no TOL redefinition); it computes per-feature best-threshold BA and
signed median differences; non-finite / extreme values can never become evidence; and claim locks stay False
with verdict HOLD under every outcome. Offline; no torment_service.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_all_shortcuts_closed_synthetic_v0_3 as v3                    # noqa: E402
import run_matched_generative_search_v0_4d as m4d                       # noqa: E402
import run_baseline_anatomy_v0_5a as m5a                                # noqa: E402

SRC = os.path.join(BV_DIR, "run_baseline_anatomy_v0_5a.py")


# ---- provenance ----
def test_imports_only_quarantined_research_surfaces():
    with open(SRC, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    mods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods.append(node.module or "")
    for mod in mods:
        assert not mod.startswith("torment") and "service" not in mod, mod
    assert set(mods) <= {"numpy", "__future__", "run_all_shortcuts_closed_synthetic_v0_3",
                         "run_matched_generative_search_v0_4d"}


def test_reuses_frozen_surfaces_by_identity():
    assert m5a._best_threshold is v3._best_threshold
    assert m5a._is_clean is m4d._is_clean
    assert m5a.GROUPS is v3.GROUPS
    assert m5a.MATCHED_GROUPS == m4d.MATCHED_GROUPS
    assert m5a.SEP_REFERENCE == m4d.CHANCE_BAND == 0.60
    assert m5a.TOL == m4d.TOL == 0.0634                       # TOL reused, NOT redefined


# ---- only the four matched groups; spectral excluded ----
def test_inspects_only_four_matched_groups_spectral_excluded():
    r = m5a.run()
    assert r["inspected_groups"] == ["movement_channel_energy", "directional", "per_channel", "frame_diff"]
    assert "spectral" not in r["inspected_groups"]
    assert "spectral" not in r["anatomy"]
    assert set(r["anatomy"].keys()) == set(m4d.MATCHED_GROUPS)
    # no spectral feature ever appears in the anatomy
    seen = {f["feature"] for g in r["anatomy"].values() for f in g["features"]}
    assert "spectral_centroid" not in seen and "spectral_spread" not in seen


# ---- reuse / preserve the v0.4d sealed matched pairs ----
def test_reuses_and_preserves_v0_4d_matched_pairs():
    r = m5a.run()
    assert r["matched_targets"] == list(m4d.HELDOUT_TARGETS)
    assert r["n_winders"] == 3 and r["n_candidates"] == 3
    assert r["protocol_ok"] is True and r["breaches"] == []
    # per-pair residuals reproduce committed v0.4d exactly
    assert r["per_pair_residual"] == {"winder_ph3.14": 0.045046, "winder_r0.7": 0.036, "winder_r0.5": 0.06}
    assert r["per_pair_all_within_tol"] is True
    # and the harness's EXPECTED table matches what the v0.4d search actually reproduces
    per, _ = m4d._search_phase(m4d.HELDOUT_TARGETS, m4d.HELDOUT_SEEDS)
    for t, (exp_id, exp_res) in m5a.V0_4D_EXPECTED.items():
        assert per[t]["best_cand_id"] == exp_id and abs(per[t]["best_residual"] - exp_res) < 1e-6


def test_no_generator_family_grid_seed_or_envelope_change():
    # the sealed v0.4d enumeration is untouched (values still exactly as sealed)
    assert m4d.FAMILIES == ("full_circle_incoherent_traversal", "rosette_multilobe_traversal",
                            "segment_paired_canceller", "phase_scrambled_full_coverage",
                            "hybrid_coverage_preserving_canceller")
    assert m4d.F3_G == (0.10, 0.20, 0.30, 0.50, 0.79) and m4d.F3_PAIRS == (1, 2)
    assert m4d.DEVELOPMENT_SEEDS == (20260709, 20260710, 20260711)
    assert m4d.HELDOUT_SEEDS == (20260712, 20260713)
    assert m4d.HELDOUT_TARGETS == ("winder_ph3.14", "winder_r0.7", "winder_r0.5")
    assert m4d.SEALED_TOTAL_EVALUATIONS == 283
    # v0.5a defines NO generator family of its own (reuses m4d): source has no candidate-family factory
    src = open(SRC, encoding="utf-8").read()
    for tok in ("def _f1_", "def _f2_", "def _f3_", "def _f4_", "def _f5_", "def candidates("):
        assert tok not in src, tok
    # v0.5a reuses the sealed held-out search verbatim
    assert "_search_phase(m4d.HELDOUT_TARGETS, m4d.HELDOUT_SEEDS)" in src


# ---- per-feature BA + signed median differences ----
def test_per_feature_ba_and_signed_median_diff_computed():
    r = m5a.run()
    for g in m4d.MATCHED_GROUPS:
        a = r["anatomy"][g]
        assert a["features"], g
        for f in a["features"]:
            assert 0.0 <= f["best_threshold_BA"] <= 1.0
            assert isinstance(f["signed_median_diff"], float)
            assert f["winder_median"] is not None and f["candidate_median"] is not None
        assert a["group_max_BA"] == max(f["best_threshold_BA"] for f in a["features"])
    # reproduces the v0.4d group-level BAs (exact rationals; platform-stable)
    assert abs(r["anatomy"]["movement_channel_energy"]["group_max_BA"] - 1.0) < 1e-6
    assert abs(r["anatomy"]["directional"]["group_max_BA"] - 1.0) < 1e-6
    assert abs(r["anatomy"]["per_channel"]["group_max_BA"] - 1.0) < 1e-6
    assert abs(r["anatomy"]["frame_diff"]["group_max_BA"] - 0.8333) < 1e-3


def test_effect_size_concentration_and_mismatch_flag_reported():
    r = m5a.run()
    assert isinstance(r["top_features_by_effect_size"], list) and len(r["top_features_by_effect_size"]) >= 1
    assert isinstance(r["top_features_by_BA"], list) and len(r["top_features_by_BA"]) >= 1
    assert r["protocol_metric_mismatch_flag"] is True     # per-pair matched within TOL yet groups still separate
    assert "small_n" in r["small_n_caveat"] or "small-N" in r["small_n_caveat"]


# ---- non-finite values can never become evidence ----
def test_feature_anatomy_excludes_nonfinite():
    win = [{s: 0.01 for s in v3.GROUPS["per_channel"]}]
    cand = [{s: 0.01 for s in v3.GROUPS["per_channel"]}]
    cand[0]["by_centroid"] = float("nan")
    a = m5a._feature_anatomy(win, cand, "per_channel")
    bad = [f for f in a["features"] if f["feature"] == "by_centroid"][0]
    assert bad["invalid_nonfinite"] is True and bad["best_threshold_BA"] is None and bad["separates"] is False
    assert "by_centroid" not in a["separating_features"]
    assert a["any_nonfinite"] is True


def test_nonfinite_in_pair_forces_invalid_breach(monkeypatch):
    orig = m4d._target_feat

    def bad(t):
        d = dict(orig(t))
        d["by_std"] = float("inf")
        return d
    monkeypatch.setattr(m4d, "_target_feat", bad)
    r = m5a.run()
    assert r["outcome"].startswith("invalid_diagnostic_breach")
    assert r["protocol_ok"] is False


# ---- claim locks / verdict / outcome ----
def test_claim_locks_and_verdict_hold():
    r = m5a.run()
    assert r["frozen_brainvision_verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False
    assert r["descriptor_validity_claim_allowed"] is False
    assert r["vision_claim"] is False and r["memory_readiness_claim"] is False
    assert r["runtime_readiness_claim"] is False and r["integration_readiness_claim"] is False
    assert r["learning"] is False and r["explanatory_only"] is True and r["reporting_only"] is True


def test_outcome_is_one_of_four():
    r = m5a.run()
    head = r["outcome"].split(":", 1)[0]
    assert head in {"concentrated_residual_feature", "distributed_residual_geometry",
                    "protocol_metric_mismatch", "invalid_diagnostic_breach"}


def test_no_temporal_or_recurrence_features():
    src = open(SRC, encoding="utf-8").read().lower()
    for tok in ("recurrence", "arrow_of_time", "time_reversed", "laminarity", "rqa", "diagonal_length"):
        assert tok not in src, tok
