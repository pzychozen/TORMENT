"""v1.0b tests: BY-aware closure audit (form A, NON-LEARNING; REPORTING-only; offline).

Lock the v1.0b slice to ROBUST facts: it reuses the v0.7b / v0.8a / v0.9b records (via v0.9b, which reproduces
the v0.7b sealed matching by identity) with no sample replacement / new seeds / new families / new candidate
generation; it keeps TOL / thresholds / descriptor / GROUPS unchanged and spectral audit-note-only; it presents
panels A-G (including the non-authorizing panel G) WITHOUT adopting a closure metric or introducing a pass/fail
gate; non-finite values can never become evidence; the outcome is one of the sealed v1.0a labels; and claim
locks stay False with verdict HOLD. Offline; no torment_service.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_by_channel_metric_anatomy_v0_8a as m8a                       # noqa: E402
import run_by_opponent_axis_closure_audit_v0_9b as m9b                  # noqa: E402
import run_by_aware_closure_audit_v1_0b as m10b                         # noqa: E402

SRC = os.path.join(BV_DIR, "run_by_aware_closure_audit_v1_0b.py")
PANELS = ("A_signed_offset", "B_by_vs_rg_dominance", "C_binding_stat", "D_region_family",
          "E_coupling_leakage_separation", "F_residual_aggregation_warning", "G_non_authorizing_visibility")


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
                         "run_by_opponent_axis_closure_audit_v0_9b"}


def test_reuses_records_by_identity():
    assert m10b.BY_FEATURES is m8a.BY_FEATURES
    r = m10b.run()
    assert r["reuses_v0_7b_v0_8a_v0_9b_records"] is True
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "m9b.run()" in src                                     # goes through v0.9b (which reproduces v0.7b via v0.8a)


def test_no_sample_replacement_no_new_seeds_families():
    r = m10b.run()
    assert r["new_family_or_axis"] is False
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    for tok in ("def _f1_", "def _f2_", "def _f3_", "def _f4_", "def _f5_", "def _winders(", "def _candidates(",
                "REPLICATION_SEEDS", "REPLICATION_WINDER", "DEVELOPMENT_SEEDS"):
        assert tok not in src, tok


def test_tol_thresholds_unchanged_no_new_metric_or_gate():
    r = m10b.run()
    assert r["TOL"] == 0.0634 and r["TOL_redefined"] is False
    assert r["new_threshold_introduced"] is False
    assert r["new_closure_metric_adopted"] is False
    assert r["pass_fail_gate_introduced"] is False
    assert r["frozen_brainvision_verdict"] == "HOLD"


# ---- spectral audit-note-only ----
def test_spectral_audit_note_only():
    r = m10b.run()
    assert "audit-note-only" in r["spectral_role"]
    flat = repr(r["panels"])
    assert "spectral_centroid" not in flat and "spectral_spread" not in flat


# ---- panels A-G present ----
def test_panels_A_to_G_present():
    r = m10b.run()
    assert set(r["panels"].keys()) == set(PANELS)
    for s in m8a.BY_FEATURES:
        d = r["panels"]["A_signed_offset"][s]
        assert "signed_offset" in d and "sign_consistency" in d and "dominant_sign" in d


def test_panel_G_is_non_authorizing():
    r = m10b.run()
    g = r["panels"]["G_non_authorizing_visibility"]
    assert g["visibility_is_diagnostic_only"] is True
    for k in ("authorizes_descriptor_validity", "authorizes_pass_fail", "authorizes_closure", "authorizes_runtime",
              "authorizes_memory", "authorizes_integration", "authorizes_vision", "authorizes_flat_geometry",
              "authorizes_screen_analysis"):
        assert g[k] is False, k
    assert r["visibility_is_non_authorizing"] is True


# ---- outcome labels sealed ----
def test_outcome_label_is_sealed():
    r = m10b.run()
    assert r["outcome_label"] in m10b.OUTCOME_LABELS
    assert set(m10b.OUTCOME_LABELS) == {"BY_aware_visibility_confirmed", "BY_aware_visibility_partial",
                                        "BY_aware_visibility_inconclusive", "invalid_protocol_breach"}


# ---- real-run visibility (structural) ----
def test_real_run_confirms_by_aware_visibility():
    r = m10b.run()
    assert r["outcome_label"] == "BY_aware_visibility_confirmed"
    P = r["panels"]
    assert P["A_signed_offset"]["by_std"]["dominant_sign"] == "+"
    assert P["A_signed_offset"]["by_centroid"]["dominant_sign"] == "-"
    assert P["A_signed_offset"]["by_spread"]["dominant_sign"] == "-"
    assert P["B_by_vs_rg_dominance"]["by_dominant_over_rg"] is True
    assert P["C_binding_stat"]["by_binds_above_share"] is True
    assert P["E_coupling_leakage_separation"]["dominant_mechanism"] == "BY_axis_asymmetry"
    assert P["F_residual_aggregation_warning"]["aggregation_warning"] is True
    assert P["D_region_family"]["single_matching_family_caveat"] is True


# ---- non-finite / breach cannot become evidence ----
def test_v0_9b_breach_propagates_to_invalid(monkeypatch):
    def stub():
        return {"outcome_label": "invalid_protocol_breach", "protocol_ok": False, "breaches": ["nonfinite"],
                "reuses_v0_8a_reproduces_v0_7b": True, "panels": {}, "TOL": 0.0634,
                "offset_visibility_criteria": {}}
    monkeypatch.setattr(m9b, "run", stub)
    r = m10b.run()
    assert r["outcome_label"] == "invalid_protocol_breach"
    assert r["protocol_ok"] is False


def test_v0_9b_non_reproduction_forces_invalid(monkeypatch):
    real = m9b.run

    def stub():
        v = dict(real())
        v["reuses_v0_8a_reproduces_v0_7b"] = False
        return v
    monkeypatch.setattr(m9b, "run", stub)
    r = m10b.run()
    assert r["outcome_label"] == "invalid_protocol_breach"


# ---- claim locks / verdict ----
def test_claim_locks_and_verdict_hold():
    r = m10b.run()
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
