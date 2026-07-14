"""v1.7 tests: BY-aware closure failure anatomy (form A, NON-LEARNING; REPORTING-only; offline).

Lock the v1.7 slice to ROBUST facts: it inspects WHY the A + D + G spine still reports the BY signed-ordering gap,
over the reused v1.5 spine (which reuses v0.7b/v0.8a/v0.9b/v1.0b/v1.2 by identity), and DECIDES bounded-lever vs
pivot WITHOUT adopting a metric / equation / threshold / gate; the guard is completeness-enforced (any missing OR
authorizing flag breaches); anatomy panels A-E are present; bounded_lever_identified is an explicit bool;
recommended_next is present (flat_opponent_plane_spatial_field_proposal when no lever); closure_achieved is always
False; protocol_ok means required panels + guard present, not closure; output is deterministic; and claim locks
stay False with verdict HOLD. Offline; no torment_service.
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
import run_by_aware_closure_audit_v1_5 as m15                           # noqa: E402
import run_by_aware_closure_failure_anatomy_v1_7 as m17                 # noqa: E402

SRC = os.path.join(BV_DIR, "run_by_aware_closure_failure_anatomy_v1_7.py")
ANATOMY_PANELS = ("A_residual_aggregation_hides_ordering", "B_offset_structural_to_family",
                  "C_by_rg_balance_mismatch", "D_by_std_binds_strongest", "E_abstraction_insufficient")
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
    assert set(mods) <= {"__future__", "run_by_channel_metric_anatomy_v0_8a", "run_by_aware_closure_audit_v1_5"}


def test_reuses_v1_5_spine_by_identity():
    assert m17.BY_FEATURES is m8a.BY_FEATURES
    assert m17.V11A_GUARD_FLAGS is m15.V11A_GUARD_FLAGS
    r = m17.run()
    assert r["reuses_v1_5_spine_by_identity"] is True
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    assert "m15.run()" in src


def test_no_sample_replacement_no_new_seeds_families():
    r = m17.run()
    assert r["new_family_or_axis"] is False
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    for tok in ("def _f1_", "def _f2_", "def _f3_", "def _f4_", "def _f5_", "def _winders(", "def _candidates(",
                "REPLICATION_SEEDS", "REPLICATION_WINDER", "DEVELOPMENT_SEEDS"):
        assert tok not in src, tok


# ---- anatomy panels A-E present ----
def test_anatomy_panels_A_to_E_present():
    r = m17.run()
    assert set(r["anatomy_panels"].keys()) == set(ANATOMY_PANELS)
    for k in ANATOMY_PANELS:
        p = r["anatomy_panels"][k]
        assert "question" in p and "evidence" in p and "observed" in p
        assert "would_require_to_close" in p and "is_bounded_lever" in p
        assert isinstance(p["observed"], bool) and isinstance(p["is_bounded_lever"], bool)


# ---- bounded lever decision explicit + conservative ----
def test_bounded_lever_identified_is_bool_and_recommended_next_present():
    r = m17.run()
    assert "bounded_lever_identified" in r and isinstance(r["bounded_lever_identified"], bool)
    assert "recommended_next" in r and r["recommended_next"] is not None
    if r["bounded_lever_identified"]:
        assert r["candidate_lever"] is not None                       # report candidate lever if identified
    else:
        assert r["candidate_lever"] is None
        assert r["recommended_next"] == "flat_opponent_plane_spatial_field_proposal"


def test_real_run_reports_no_bounded_lever_and_pivot():
    r = m17.run()
    assert r["outcome_label"] == "BY_failure_anatomy_no_bounded_lever"
    assert r["bounded_lever_identified"] is False
    assert r["recommended_next"] == "flat_opponent_plane_spatial_field_proposal"
    # every fixture-metric mechanism (A/C/D) requires a forbidden op; B/E are pivot signals
    P = r["anatomy_panels"]
    for k in ("A_residual_aggregation_hides_ordering", "C_by_rg_balance_mismatch", "D_by_std_binds_strongest"):
        assert P[k]["is_bounded_lever"] is False
    assert P["B_offset_structural_to_family"]["is_pivot_signal"] is True
    assert P["E_abstraction_insufficient"]["is_pivot_signal"] is True


def test_outcome_label_sealed_and_never_closure():
    r = m17.run()
    assert r["outcome_label"] in m17.OUTCOME_LABELS
    assert set(m17.OUTCOME_LABELS) == {"BY_failure_anatomy_bounded_lever_visible",
                                       "BY_failure_anatomy_no_bounded_lever", "invalid_protocol_breach"}
    assert r["closure_achieved"] is False
    for lbl in m17.OUTCOME_LABELS:
        assert "closure" not in lbl and "achieved" not in lbl and "closed" not in lbl


# ---- no adoption ----
def test_no_metric_threshold_tol_gate_adoption():
    r = m17.run()
    assert r["TOL"] == 0.0634 and r["tol_redefined"] is False and r["TOL_redefined"] is False
    for k in REQUIRED_FALSE_FLAGS:
        assert k in r and r[k] is False, k
    assert r["frozen_brainvision_verdict"] == "HOLD"
    assert r["reporting_only"] is True and r["visibility_is_non_authorizing"] is True


def test_no_descriptor_family_spectral_reopening():
    r = m17.run()
    assert r["descriptor_redesign_authorized"] is False
    assert r["generator_family_expansion_authorized"] is False
    assert r["spectral_closure_reopened"] is False
    assert "audit-note-only" in r["spectral_role"]


def test_no_flat_or_screen_implementation_authorization():
    r = m17.run()
    assert r["flat_geometry_authorized"] is False and r["screen_analysis_authorized"] is False
    # the pivot RECOMMENDATION is a docs-only proposal target, not an implementation authorization
    assert r["recommended_next"] == "flat_opponent_plane_spatial_field_proposal"


# ---- guard completeness / authorizing -> breach ----
@pytest.mark.parametrize("flag", ["authorizes_closure", "authorizes_temporal_order",
                                  "authorizes_live_or_screen_use", "authorizes_vision"])
def test_authorizing_guard_forces_invalid(monkeypatch, flag):
    real = m15.run

    def stub():
        v = dict(real())
        sp = dict(v["primary_spine"])
        g = dict(sp["G_non_authorizing_visibility"]) if "G_non_authorizing_visibility" in sp else dict(sp["G_non_authorizing_guard"])
        g[flag] = True
        sp["G_non_authorizing_guard"] = g
        v["primary_spine"] = sp
        return v
    monkeypatch.setattr(m15, "run", stub)
    r = m17.run()
    assert r["protocol_ok"] is False
    assert r["outcome_label"] == "invalid_protocol_breach"


@pytest.mark.parametrize("flag", ["authorizes_temporal_order", "authorizes_live_or_screen_use"])
def test_missing_required_guard_flag_forces_invalid(monkeypatch, flag):
    real = m15.run

    def stub():
        v = dict(real())
        sp = dict(v["primary_spine"])
        g = dict(sp["G_non_authorizing_guard"])
        del g[flag]                                                  # a REQUIRED v1.1a flag is ABSENT -> inadmissible
        sp["G_non_authorizing_guard"] = g
        v["primary_spine"] = sp
        return v
    monkeypatch.setattr(m15, "run", stub)
    r = m17.run()
    assert r["protocol_ok"] is False
    assert r["outcome_label"] == "invalid_protocol_breach"


def test_v1_5_breach_propagates_to_invalid(monkeypatch):
    def stub():
        return {"outcome_label": "invalid_protocol_breach", "protocol_ok": False, "breaches": ["nonfinite"],
                "reuses_v0_7b_v0_8a_v0_9b_v1_0b_v1_2_records": True, "primary_spine": {}, "support_reporting": {},
                "TOL": 0.0634, "closure_achieved": False}
    monkeypatch.setattr(m15, "run", stub)
    r = m17.run()
    assert r["outcome_label"] == "invalid_protocol_breach"
    assert r["protocol_ok"] is False
    assert r["closure_achieved"] is False


# ---- determinism ----
def test_output_is_deterministic():
    assert repr(m17.run()) == repr(m17.run())


# ---- claim locks / verdict ----
def test_claim_locks_and_verdict_hold():
    r = m17.run()
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
