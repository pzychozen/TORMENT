"""v0.8a tests: BY-channel metric anatomy (form A, NON-LEARNING; EXPLANATORY-only; offline).

Lock the v0.8a slice to ROBUST facts: it reproduces the v0.7b sealed replication BY IDENTITY (no sample
replacement, no seed/count/pairing change), uses only the existing v0.7b / frozen generator surfaces, keeps
TOL / thresholds / descriptor / GROUPS unchanged and spectral audit-note-only, inspects the primary BY features
(by_centroid / by_spread / by_std) with rg_* / directional as comparison-only, labels the outcome from the
sealed v0.8 set, never lets non-finite values become evidence, and keeps claim locks False with verdict HOLD.
Offline; no torment_service.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_color_structure_v0_8 as cs                                   # noqa: E402
import run_matched_generative_search_v0_4d as m4d                       # noqa: E402
import run_residual_sufficiency_v0_6a as m6a                            # noqa: E402
import run_larger_n_residual_replication_v0_7b as m7b                   # noqa: E402
import run_by_channel_metric_anatomy_v0_8a as m8a                       # noqa: E402

SRC = os.path.join(BV_DIR, "run_by_channel_metric_anatomy_v0_8a.py")


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
    assert set(mods) <= {"numpy", "__future__", "run_color_structure_v0_8",
                         "run_matched_generative_search_v0_4d", "run_residual_sufficiency_v0_6a",
                         "run_larger_n_residual_replication_v0_7b"}


def test_reuses_frozen_surfaces_by_identity():
    assert m8a._feature_audit is m6a._feature_audit
    assert m8a._is_clean is m4d._is_clean
    assert m8a._spearman is cs.g5._spearman          # frozen rank correlation reused, not re-authored
    assert m8a.MATCHED_STATS is m4d.MATCHED_STATS
    assert m8a.TOL == m7b.TOL == 0.0634


# ---- reproduces v0.7b; no sample replacement / seed / count / pairing change ----
def test_reproduces_v0_7b_no_sample_change():
    r = m8a.run()
    assert r["reproduces_v0_7b"] is True
    assert r["n_matched"] == 19 and r["n_unmatched"] == 5
    assert tuple(r["unmatched_winders"]) == ("w_sp3.00", "w_sp3.50", "w_r0.4", "w_r0.3", "w_r0.2")
    assert r["n_replication_evaluations"] == 1056 and r["protocol_ok"] is True
    # uses the sealed v0.7b enumeration constants (unchanged) and its generator surfaces (no new family)
    assert m7b.REPLICATION_SEEDS == (20260723, 20260724, 20260725)
    assert m7b.SEALED_TOTAL_EVALUATIONS == 1278
    src = open(SRC, encoding="utf-8").read()
    for reused in ("m7b._winders", "m7b._candidates", "m7b.REPLICATION_WINDER_SPEEDS", "m4d._feat",
                   "m4d._safe_feat", "m4d._residual"):
        assert reused in src, reused
    for tok in ("def _f1_", "def _f2_", "def _f3_", "def _f4_", "def _f5_", "def _winders(", "def _candidates("):
        assert tok not in src, tok        # defines no generator / no new family of its own


def test_frozen_thresholds_and_flags():
    r = m8a.run()
    assert r["TOL"] == 0.0634 and r["TOL_redefined"] is False
    assert r["new_threshold_introduced"] is False and r["new_family_or_axis"] is False


# ---- spectral audit-note-only ----
def test_spectral_audit_note_only():
    r = m8a.run()
    assert "audit-note-only" in r["spectral_role"]
    for grp in (m8a.BY_FEATURES, m8a.RG_FEATURES, m8a.DIRECTIONAL_FEATURES, m8a.AMPLITUDE_FEATURES):
        assert "spectral_centroid" not in grp and "spectral_spread" not in grp
    assert "spectral_centroid" not in r["by_vs_rg"] and "spectral_spread" not in r["by_vs_rg"]


# ---- primary BY features inspected; RG / directional comparison-only ----
def test_primary_by_features_and_comparison_roles():
    assert m8a.BY_FEATURES == ("by_centroid", "by_spread", "by_std")
    assert m8a.RG_FEATURES == ("rg_centroid", "rg_spread")
    assert m8a.DIRECTIONAL_FEATURES == ("u_directional_delta_rms", "angular_increment_mag")
    r = m8a.run()
    # BY-only anatomy (signed differences, coupling, amplitude) covers only the primary target
    assert set(r["by_signed_difference"].keys()) == set(m8a.BY_FEATURES)
    # RG / directional appear ONLY as comparison in the BY-vs-RG effect table
    for s in m8a.RG_FEATURES + m8a.DIRECTIONAL_FEATURES:
        assert s in r["by_vs_rg"] and s not in r["by_signed_difference"]


# ---- outcome labels only the sealed set ----
def test_outcome_label_is_sealed():
    r = m8a.run()
    assert r["outcome_label"] in m8a.OUTCOME_LABELS
    assert set(m8a.OUTCOME_LABELS) == {"BY_axis_asymmetry", "BY_centroid_spread_coupling", "BY_amplitude_leakage",
                                       "BY_family_artifact", "BY_metric_compression", "BY_anatomy_inconclusive",
                                       "invalid_protocol_breach"}


# ---- real-run anatomy (structural, platform-stable) ----
def test_real_run_reports_axis_asymmetry():
    r = m8a.run()
    assert r["by_dominant_over_rg"] is True                        # BY effects exceed RG effects
    assert r["mean_by_sign_consistency"] > 0.5                     # BY differences systematically signed
    # by_std winders higher (+), by_centroid / by_spread winders lower (-)
    assert r["by_signed_difference"]["by_std"]["dominant_sign"] == "+"
    assert r["by_signed_difference"]["by_centroid"]["dominant_sign"] == "-"
    assert r["by_signed_difference"]["by_spread"]["dominant_sign"] == "-"
    sc = r["mechanism_scores"]
    assert sc["BY_axis_asymmetry"] == max(sc.values())            # asymmetry is the strongest signal
    assert sc["BY_axis_asymmetry"] > sc["BY_centroid_spread_coupling"]
    assert sc["BY_axis_asymmetry"] > sc["BY_amplitude_leakage"]
    assert r["outcome_label"] == "BY_axis_asymmetry"


# ---- non-finite values can never become evidence ----
def test_nonfinite_forces_invalid_breach(monkeypatch):
    real = m8a._reproduce_replication_pairs

    def stub():
        pairs, unmatched, n_eval = real()
        pairs[0]["win_feat"] = dict(pairs[0]["win_feat"])
        pairs[0]["win_feat"]["by_centroid"] = float("inf")        # non-finite in a required BY feature
        return pairs, unmatched, n_eval
    monkeypatch.setattr(m8a, "_reproduce_replication_pairs", stub)
    r = m8a.run()
    assert r["outcome_label"] == "invalid_protocol_breach"
    assert r["protocol_ok"] is False


# ---- claim locks / verdict ----
def test_claim_locks_and_verdict_hold():
    r = m8a.run()
    assert r["frozen_brainvision_verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False
    assert r["descriptor_validity_claim_allowed"] is False
    assert r["vision_claim"] is False and r["memory_readiness_claim"] is False
    assert r["runtime_readiness_claim"] is False and r["integration_readiness_claim"] is False
    assert r["learning"] is False and r["explanatory_only"] is True and r["reporting_only"] is True


def test_no_temporal_or_recurrence_features():
    src = open(SRC, encoding="utf-8").read().lower()
    for tok in ("recurrence", "arrow_of_time", "time_reversed", "laminarity", "rqa", "diagonal_length"):
        assert tok not in src, tok
