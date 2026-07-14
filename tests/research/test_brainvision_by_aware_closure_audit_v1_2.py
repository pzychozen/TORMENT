"""v1.2 tests: BY-aware closure audit (form A, NON-LEARNING; REPORTING-only; offline).

Lock the v1.2 slice to ROBUST facts: it GENERATES the preregistered BY-aware reporting obligations (v1.1 proposal
+ v1.1a plan, panels A-G) as diagnostic output over the reused v0.7b / v0.8a / v0.9b / v1.0b records (via v1.0b,
which reproduces the v0.7b sealed matching by identity) with no sample replacement / new seeds / new families /
new candidate generation; it keeps TOL / thresholds / descriptor / GROUPS unchanged and spectral audit-note-only;
it re-presents panels A-G WITHOUT adopting a closure metric / equation / threshold / pass-fail gate; it adds the
v1.1a obligation guards (no offset-vs-TOL gate, no binding gate, no hidden closure, no family expansion, guard G
all False); the result label is CONSERVATIVE (reporting_generated / gap_visible / invalid_protocol_breach) and
NEVER closure_achieved; non-finite values / a broken guard can never become evidence; and claim locks stay False
with verdict HOLD. Offline; no torment_service.
"""
import ast
import os
import sys

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_by_channel_metric_anatomy_v0_8a as m8a                       # noqa: E402
import run_by_opponent_axis_closure_audit_v0_9b as m9b                  # noqa: E402
import run_by_aware_closure_audit_v1_0b as m10b                         # noqa: E402
import run_by_aware_closure_audit_v1_2 as m12                           # noqa: E402

SRC = os.path.join(BV_DIR, "run_by_aware_closure_audit_v1_2.py")
PANELS = ("A_signed_offset", "B_by_vs_rg_dominance", "C_binding_stat", "D_region_family",
          "E_coupling_leakage_separation", "F_residual_aggregation_warning", "G_non_authorizing_visibility")
V11A_GUARD_FLAGS = ("authorizes_descriptor_validity", "authorizes_temporal_order", "authorizes_pass_fail",
                    "authorizes_closure", "authorizes_runtime", "authorizes_memory", "authorizes_integration",
                    "authorizes_live_or_screen_use", "authorizes_vision")
REQUIRED_FALSE_FLAGS = ("new_closure_metric_adopted", "pass_fail_gate_introduced", "tol_redefined",
                        "descriptor_redesign_authorized", "generator_family_expansion_authorized",
                        "spectral_closure_reopened", "flat_geometry_authorized", "screen_analysis_authorized",
                        "runtime_authorized", "memory_authorized", "vision_claim_allowed", "closure_achieved")


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
    assert set(mods) <= {"__future__", "run_by_channel_metric_anatomy_v0_8a",
                         "run_by_opponent_axis_closure_audit_v0_9b", "run_by_aware_closure_audit_v1_0b"}


def test_reuses_records_by_identity():
    assert m12.BY_FEATURES is m8a.BY_FEATURES
    assert m12.CHANCE_SIGN is m9b.CHANCE_SIGN
    r = m12.run()
    assert r["reuses_v0_7b_v0_8a_v0_9b_records"] is True
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "m10b.run()" in src                                    # goes through v1.0b (which reproduces v0.7b via v0.9b/v0.8a)


def test_reuse_by_identity_core_values_match_v1_0b():
    r = m12.run()
    b = m10b.run()
    Pr, Pb = r["panels"], b["panels"]
    for s in m8a.BY_FEATURES:
        assert Pr["A_signed_offset"][s]["signed_offset"] == Pb["A_signed_offset"][s]["signed_offset"]
        assert Pr["A_signed_offset"][s]["sign_consistency"] == Pb["A_signed_offset"][s]["sign_consistency"]
        assert Pr["A_signed_offset"][s]["dominant_sign"] == Pb["A_signed_offset"][s]["dominant_sign"]
    assert Pr["B_by_vs_rg_dominance"]["by_dominant_over_rg"] == Pb["B_by_vs_rg_dominance"]["by_dominant_over_rg"]
    assert Pr["C_binding_stat"]["by_binds_above_share"] == Pb["C_binding_stat"]["by_binds_above_share"]
    assert (Pr["E_coupling_leakage_separation"]["dominant_mechanism"]
            == Pb["E_coupling_leakage_separation"]["dominant_mechanism"])
    assert (Pr["F_residual_aggregation_warning"]["aggregation_warning"]
            == Pb["F_residual_aggregation_warning"]["aggregation_warning"])


def test_no_sample_replacement_no_new_seeds_families():
    r = m12.run()
    assert r["new_family_or_axis"] is False
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    for tok in ("def _f1_", "def _f2_", "def _f3_", "def _f4_", "def _f5_", "def _winders(", "def _candidates(",
                "REPLICATION_SEEDS", "REPLICATION_WINDER", "DEVELOPMENT_SEEDS"):
        assert tok not in src, tok


def test_tol_thresholds_unchanged_no_new_metric_or_gate():
    r = m12.run()
    assert r["TOL"] == 0.0634 and r["tol_redefined"] is False and r["TOL_redefined"] is False
    assert r["new_threshold_introduced"] is False
    assert r["new_closure_metric_adopted"] is False
    assert r["pass_fail_gate_introduced"] is False
    assert r["frozen_brainvision_verdict"] == "HOLD"


# ---- required output properties (v1.2 task contract) ----
def test_required_output_properties_present_and_correct():
    r = m12.run()
    assert r["protocol_ok"] is True
    assert r["reporting_only"] is True
    assert r["visibility_is_non_authorizing"] is True
    for k in REQUIRED_FALSE_FLAGS:
        assert k in r and r[k] is False, k


# ---- spectral audit-note-only ----
def test_spectral_audit_note_only():
    r = m12.run()
    assert "audit-note-only" in r["spectral_role"]
    assert r["spectral_closure_reopened"] is False
    flat = repr(r["panels"])
    assert "spectral_centroid" not in flat and "spectral_spread" not in flat


# ---- panels A-G present + obligation annotations ----
def test_panels_A_to_G_present():
    r = m12.run()
    assert set(r["panels"].keys()) == set(PANELS)
    for s in m8a.BY_FEATURES:
        d = r["panels"]["A_signed_offset"][s]
        assert "signed_offset" in d and "sign_consistency" in d and "dominant_sign" in d
        assert "magnitude_frac_TOL" in d                              # obligation A: |offset| relative to frozen TOL


def test_obligation_A_magnitude_relative_to_tol_no_gate():
    r = m12.run()
    A = r["panels"]["A_signed_offset"]
    assert A["offset_vs_tol_gate"] is False                           # magnitude is DESCRIPTIVE, not a gate
    for s in m8a.BY_FEATURES:
        m = A[s]["magnitude_frac_TOL"]
        assert isinstance(m, float) and m == m                        # finite (not NaN)


def test_obligation_guards_no_binding_no_family_expansion_no_hidden_closure():
    r = m12.run()
    P = r["panels"]
    assert P["C_binding_stat"]["binding_gate_introduced"] is False
    assert P["D_region_family"]["generator_family_expansion_authorized"] is False
    assert P["F_residual_aggregation_warning"]["hidden_closure_claim"] is False


def test_reporting_obligations_map_A_to_G():
    r = m12.run()
    ob = r["reporting_obligations"]
    for k in ("A_signed_offset_reporting", "B_by_dominance_reporting", "C_binding_reporting",
              "D_aggregation_warning_reporting", "E_coupling_leakage_separation", "F_region_family_caveat",
              "G_non_authorizing_guard"):
        assert k in ob, k
    assert ob["A_signed_offset_reporting"]["offset_vs_tol_gate"] is False
    assert ob["B_by_dominance_reporting"]["visibility_evidence_only"] is True
    assert ob["C_binding_reporting"]["binding_gate"] is False
    assert ob["D_aggregation_warning_reporting"]["hidden_closure_claim"] is False
    assert ob["F_region_family_caveat"]["generator_family_expansion_authorized"] is False


def test_panel_G_guard_all_nine_v11a_flags_false():
    r = m12.run()
    g = r["panels"]["G_non_authorizing_visibility"]
    assert g["visibility_is_diagnostic_only"] is True
    for k in V11A_GUARD_FLAGS:                                        # the NINE v1.1a §7 required flags
        assert k in g and g[k] is False, k
    for k in ("authorizes_flat_geometry", "authorizes_screen_analysis"):   # extras kept, NOT substitutes
        assert g[k] is False, k
    ob_g = r["reporting_obligations"]["G_non_authorizing_guard"]
    assert set(ob_g.keys()) == set(V11A_GUARD_FLAGS)                  # obligations expose exactly the nine
    assert all(v is False for v in ob_g.values())


# ---- outcome labels sealed + conservative (never closure) ----
def test_outcome_label_is_sealed_and_never_closure():
    r = m12.run()
    assert r["outcome_label"] in m12.OUTCOME_LABELS
    assert set(m12.OUTCOME_LABELS) == {"BY_aware_closure_reporting_generated", "BY_aware_closure_gap_visible",
                                       "invalid_protocol_breach"}
    assert r["closure_achieved"] is False
    assert "closure_achieved" not in m12.OUTCOME_LABELS
    for lbl in m12.OUTCOME_LABELS:
        assert "achieved" not in lbl and "closed" not in lbl


# ---- real-run: the BY wall persists under the reporting -> gap_visible (structural) ----
def test_real_run_reports_gap_visible():
    r = m12.run()
    assert r["outcome_label"] == "BY_aware_closure_gap_visible"
    assert r["by_wall_persists"] is True
    assert r["closure_achieved"] is False
    P = r["panels"]
    assert P["A_signed_offset"]["by_std"]["dominant_sign"] == "+"
    assert P["A_signed_offset"]["by_centroid"]["dominant_sign"] == "-"
    assert P["A_signed_offset"]["by_spread"]["dominant_sign"] == "-"
    assert P["B_by_vs_rg_dominance"]["by_dominant_over_rg"] is True
    assert P["C_binding_stat"]["by_binds_above_share"] is True
    assert P["E_coupling_leakage_separation"]["dominant_mechanism"] == "BY_axis_asymmetry"
    assert P["F_residual_aggregation_warning"]["aggregation_warning"] is True
    assert P["D_region_family"]["single_matching_family_caveat"] is True


# ---- non-finite / breach / broken guard cannot become evidence ----
def test_v1_0b_breach_propagates_to_invalid(monkeypatch):
    def stub():
        return {"outcome_label": "invalid_protocol_breach", "protocol_ok": False, "breaches": ["nonfinite"],
                "reuses_v0_7b_v0_8a_v0_9b_records": True, "panels": {}, "TOL": 0.0634}
    monkeypatch.setattr(m10b, "run", stub)
    r = m12.run()
    assert r["outcome_label"] == "invalid_protocol_breach"
    assert r["protocol_ok"] is False
    assert r["by_wall_persists"] is False
    assert r["closure_achieved"] is False


def test_v1_0b_non_reproduction_forces_invalid(monkeypatch):
    real = m10b.run

    def stub():
        v = dict(real())
        v["reuses_v0_7b_v0_8a_v0_9b_records"] = False
        return v
    monkeypatch.setattr(m10b, "run", stub)
    r = m12.run()
    assert r["outcome_label"] == "invalid_protocol_breach"


@pytest.mark.parametrize("flag", ["authorizes_closure", "authorizes_temporal_order",
                                  "authorizes_live_or_screen_use"])
def test_authorizing_guard_forces_invalid(monkeypatch, flag):
    real = m10b.run

    def stub():
        v = dict(real())
        p = dict(v["panels"])
        g = dict(p["G_non_authorizing_visibility"])
        g[flag] = True                                               # ANY authorizing guard flag is inadmissible
        p["G_non_authorizing_visibility"] = g
        v["panels"] = p
        return v
    monkeypatch.setattr(m10b, "run", stub)
    r = m12.run()
    assert r["outcome_label"] == "invalid_protocol_breach"
    assert r["protocol_ok"] is False


# ---- claim locks / verdict ----
def test_claim_locks_and_verdict_hold():
    r = m12.run()
    assert r["frozen_brainvision_verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False
    assert r["descriptor_validity_claim_allowed"] is False
    assert r["vision_claim"] is False and r["memory_readiness_claim"] is False
    assert r["runtime_readiness_claim"] is False and r["integration_readiness_claim"] is False
    assert r["learning"] is False and r["reporting_only"] is True


def test_no_temporal_or_recurrence_features():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    for tok in ("recurrence", "arrow_of_time", "time_reversed", "laminarity", "rqa", "diagonal_length"):
        assert tok not in src, tok
