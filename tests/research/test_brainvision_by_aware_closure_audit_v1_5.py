"""v1.5 tests: BY-aware closure audit (form A, NON-LEARNING; REPORTING/guard only; offline).

Lock the v1.5 slice to ROBUST facts: it GENERATES the v1.4-preregistered A + D + G spine (B / C / E report-only)
over the reused v0.7b / v0.8a / v0.9b / v1.0b / v1.2 records (via v1.2, which reproduces the v0.7b sealed matching
by identity) with no sample replacement / new seeds / new families / new candidate generation; it keeps TOL /
thresholds / descriptor / GROUPS unchanged and spectral audit-note-only; it re-presents the spine WITHOUT adopting
a closure metric / equation / threshold / pass-fail gate / offset-vs-TOL gate / binding gate; the guard carries all
nine authorization flags False and ANY True forces invalid_protocol_breach; B / C / E are report-only (never gates);
closure_achieved is always False; protocol_ok means only that required reporting + guards are present, not closure;
the conservative label is reporting_complete / gap_still_visible / invalid_protocol_breach; output is deterministic;
and claim locks stay False with verdict HOLD. Offline; no torment_service.
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
import run_by_aware_closure_audit_v1_2 as m12                           # noqa: E402
import run_by_aware_closure_audit_v1_5 as m15                           # noqa: E402

SRC = os.path.join(BV_DIR, "run_by_aware_closure_audit_v1_5.py")
V11A_GUARD_FLAGS = ("authorizes_descriptor_validity", "authorizes_temporal_order", "authorizes_pass_fail",
                    "authorizes_closure", "authorizes_runtime", "authorizes_memory", "authorizes_integration",
                    "authorizes_live_or_screen_use", "authorizes_vision")
REQUIRED_FALSE_FLAGS = ("new_closure_metric_adopted", "pass_fail_gate_introduced", "tol_redefined",
                        "new_threshold_introduced", "offset_vs_tol_gate", "binding_gate", "validity_pass_fail_gate",
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
    assert set(mods) <= {"__future__", "run_by_channel_metric_anatomy_v0_8a", "run_by_aware_closure_audit_v1_2"}


def test_reuses_records_by_identity():
    assert m15.BY_FEATURES is m8a.BY_FEATURES
    assert m15.PANELS is m12.PANELS
    assert m15.V11A_GUARD_FLAGS is m12.V11A_GUARD_FLAGS
    r = m15.run()
    assert r["reuses_v0_7b_v0_8a_v0_9b_v1_0b_v1_2_records"] is True
    assert r["reuses_v1_2_by_identity"] is True
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "m12.run()" in src


def test_spine_values_match_v1_2_by_identity():
    r = m15.run()
    c = m12.run()
    Pc = c["panels"]
    A = r["primary_spine"]["A_signed_offset"]
    for s in m8a.BY_FEATURES:
        assert A[s]["signed_offset"] == Pc["A_signed_offset"][s]["signed_offset"]
        assert A[s]["sign_consistency"] == Pc["A_signed_offset"][s]["sign_consistency"]
        assert A[s]["magnitude_frac_TOL"] == Pc["A_signed_offset"][s]["magnitude_frac_TOL"]
    assert (r["primary_spine"]["D_aggregation_anti_hiding"]["aggregation_warning"]
            == Pc["F_residual_aggregation_warning"]["aggregation_warning"])
    assert r["by_wall_persists"] == c["by_wall_persists"]


def test_no_sample_replacement_no_new_seeds_families():
    r = m15.run()
    assert r["new_family_or_axis"] is False
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    for tok in ("def _f1_", "def _f2_", "def _f3_", "def _f4_", "def _f5_", "def _winders(", "def _candidates(",
                "REPLICATION_SEEDS", "REPLICATION_WINDER", "DEVELOPMENT_SEEDS"):
        assert tok not in src, tok


# ---- no adoption: TOL / metric / thresholds / gates ----
def test_tol_thresholds_unchanged_no_metric_no_gate():
    r = m15.run()
    assert r["TOL"] == 0.0634 and r["tol_redefined"] is False and r["TOL_redefined"] is False
    for k in REQUIRED_FALSE_FLAGS:
        assert k in r and r[k] is False, k
    assert r["frozen_brainvision_verdict"] == "HOLD"


def test_reporting_only_and_non_authorizing():
    r = m15.run()
    assert r["reporting_only"] is True
    assert r["visibility_is_non_authorizing"] is True


# ---- primary spine A + D + G present ----
def test_primary_spine_A_D_G_present():
    r = m15.run()
    S = r["primary_spine"]
    assert set(S.keys()) == {"A_signed_offset", "D_aggregation_anti_hiding", "G_non_authorizing_guard"}
    A = S["A_signed_offset"]
    for s in m8a.BY_FEATURES:
        d = A[s]
        assert "signed_offset" in d and "sign_consistency" in d and "dominant_sign" in d
        assert "magnitude_frac_TOL" in d                              # magnitude relative to frozen TOL
    assert A["offset_vs_tol_gate"] is False                           # NO offset-vs-TOL gate
    D = S["D_aggregation_anti_hiding"]
    assert "aggregation_warning" in D and D["hidden_closure_claim"] is False


def test_no_offset_vs_tol_gate_and_no_binding_gate():
    r = m15.run()
    assert r["offset_vs_tol_gate"] is False and r["binding_gate"] is False and r["validity_pass_fail_gate"] is False
    assert r["primary_spine"]["A_signed_offset"]["offset_vs_tol_gate"] is False
    # binding stays report-only in support C
    assert r["support_reporting"]["C_binding_aware_partition"]["binding_gate_introduced"] is False


# ---- guard: nine flags present + False; any True -> protocol_ok False ----
def test_guard_all_nine_flags_present_and_false():
    r = m15.run()
    g = r["primary_spine"]["G_non_authorizing_guard"]
    assert g["visibility_is_diagnostic_only"] is True
    for k in V11A_GUARD_FLAGS:
        assert k in g and g[k] is False, k
    ob_g = r["reporting_obligations"]["primary"]["G_non_authorizing_guard"]
    assert set(ob_g.keys()) == set(V11A_GUARD_FLAGS)
    assert all(v is False for v in ob_g.values())


@pytest.mark.parametrize("flag", ["authorizes_closure", "authorizes_temporal_order",
                                  "authorizes_live_or_screen_use", "authorizes_vision"])
def test_authorizing_guard_forces_invalid(monkeypatch, flag):
    real = m12.run

    def stub():
        v = dict(real())
        p = dict(v["panels"])
        g = dict(p["G_non_authorizing_visibility"])
        g[flag] = True                                               # ANY authorizing guard flag is inadmissible
        p["G_non_authorizing_visibility"] = g
        v["panels"] = p
        return v
    monkeypatch.setattr(m12, "run", stub)
    r = m15.run()
    assert r["outcome_label"] == "invalid_protocol_breach"
    assert r["protocol_ok"] is False
    assert r["closure_achieved"] is False


@pytest.mark.parametrize("flag", ["authorizes_temporal_order", "authorizes_live_or_screen_use",
                                  "authorizes_descriptor_validity"])
def test_missing_required_guard_flag_forces_invalid(monkeypatch, flag):
    real = m12.run

    def stub():
        v = dict(real())
        p = dict(v["panels"])
        g = dict(p["G_non_authorizing_visibility"])
        del g[flag]                                                  # a REQUIRED v1.1a flag is ABSENT -> inadmissible
        p["G_non_authorizing_visibility"] = g
        v["panels"] = p
        return v
    monkeypatch.setattr(m12, "run", stub)
    r = m15.run()
    assert r["protocol_ok"] is False
    assert r["outcome_label"] == "invalid_protocol_breach"


# ---- B / C / E report-only support (never gates) ----
def test_support_B_C_E_report_only():
    r = m15.run()
    sup = r["support_reporting"]
    assert sup["support_only"] is True and sup["promoted_to_gate"] is False
    for k in ("B_by_rg_opponent_balance", "C_binding_aware_partition", "E_region_family_stratified"):
        assert k in sup, k
    ob = r["reporting_obligations"]["support_report_only"]
    for k in ("B_by_rg_opponent_balance", "C_binding_aware_partition", "E_region_family_stratified"):
        assert ob[k]["report_only"] is True and ob[k]["is_gate"] is False, k
    assert ob["C_binding_aware_partition"]["residual_redefined"] is False
    assert ob["E_region_family_stratified"]["generator_family_expansion_authorized"] is False


# ---- protocol_ok = presence only, NOT closure ----
def test_protocol_ok_is_presence_not_closure():
    r = m15.run()
    assert r["protocol_ok"] is True
    assert r["closure_achieved"] is False
    # protocol_ok True while closure_achieved False demonstrates presence-not-closure semantics


# ---- outcome labels sealed + conservative (never closure) ----
def test_outcome_label_sealed_and_never_closure():
    r = m15.run()
    assert r["outcome_label"] in m15.OUTCOME_LABELS
    assert set(m15.OUTCOME_LABELS) == {"BY_aware_closure_audit_reporting_complete",
                                       "BY_aware_closure_gap_still_visible", "invalid_protocol_breach"}
    assert r["closure_achieved"] is False
    for lbl in m15.OUTCOME_LABELS:
        assert "achieved" not in lbl and "closed" not in lbl


def test_real_run_reports_gap_still_visible():
    r = m15.run()
    assert r["outcome_label"] == "BY_aware_closure_gap_still_visible"
    assert r["by_wall_persists"] is True
    assert r["closure_achieved"] is False
    A = r["primary_spine"]["A_signed_offset"]
    assert A["by_std"]["dominant_sign"] == "+"
    assert A["by_centroid"]["dominant_sign"] == "-"
    assert A["by_spread"]["dominant_sign"] == "-"
    assert r["primary_spine"]["D_aggregation_anti_hiding"]["aggregation_warning"] is True
    assert r["support_reporting"]["E_region_family_stratified"]["single_matching_family_caveat"] is True


# ---- breach / non-reproduction cannot become evidence ----
def test_v1_2_breach_propagates_to_invalid(monkeypatch):
    def stub():
        return {"outcome_label": "invalid_protocol_breach", "protocol_ok": False, "breaches": ["nonfinite"],
                "reuses_v0_7b_v0_8a_v0_9b_records": True, "panels": {}, "TOL": 0.0634, "closure_achieved": False,
                "by_wall_persists": False}
    monkeypatch.setattr(m12, "run", stub)
    r = m15.run()
    assert r["outcome_label"] == "invalid_protocol_breach"
    assert r["protocol_ok"] is False
    assert r["closure_achieved"] is False


def test_v1_2_non_reproduction_forces_invalid(monkeypatch):
    real = m12.run

    def stub():
        v = dict(real())
        v["reuses_v0_7b_v0_8a_v0_9b_records"] = False
        return v
    monkeypatch.setattr(m12, "run", stub)
    r = m15.run()
    assert r["outcome_label"] == "invalid_protocol_breach"


# ---- determinism ----
def test_output_is_deterministic():
    assert repr(m15.run()) == repr(m15.run())


# ---- claim locks / verdict ----
def test_claim_locks_and_verdict_hold():
    r = m15.run()
    assert r["frozen_brainvision_verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False
    assert r["descriptor_validity_claim_allowed"] is False
    assert r["vision_claim"] is False and r["memory_readiness_claim"] is False
    assert r["runtime_readiness_claim"] is False and r["integration_readiness_claim"] is False
    assert r["learning"] is False and r["reporting_only"] is True


def test_spectral_audit_note_only():
    r = m15.run()
    assert "audit-note-only" in r["spectral_role"]
    assert r["spectral_closure_reopened"] is False
    flat = repr(r["primary_spine"]) + repr(r["support_reporting"])
    assert "spectral_centroid" not in flat and "spectral_spread" not in flat


def test_no_temporal_or_recurrence_features():
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read().lower()
    for tok in ("recurrence", "arrow_of_time", "time_reversed", "laminarity", "rqa", "diagonal_length"):
        assert tok not in src, tok
