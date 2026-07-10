"""v2.3 tests: flat opponent-field audit (form A, NON-LEARNING; REPORTING/guard only; offline).

Lock the v2.3 slice to ROBUST facts: it GENERATES the accepted v2.2 flat opponent-field panels A-F as structural /
conceptual reporting over offline synthetic content, WITHOUT implementing a descriptor / coordinate system / metric
/ equation / threshold / pass-fail validity gate; the guard (panel F) is completeness-enforced (any required flag
missing OR True forces invalid_protocol_breach); protocol_ok means required panels + guard present only, NOT
validation; flat_field_validated is always False; the label is conservative (FLAT_OPPONENT_FIELD_REPORTING_GENERATED
/ invalid_protocol_breach); output is deterministic; v1.x stays frozen evidence and v2.x unvalidated; and claim
locks stay False with verdict HOLD. Offline; no torment_service.
"""
import ast
import os
import sys

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_flat_opponent_field_audit_v2_3 as m23                        # noqa: E402

SRC = os.path.join(BV_DIR, "run_flat_opponent_field_audit_v2_3.py")
PANELS = ("A_patch_definition", "B_opponent_channel", "C_spatial_relation", "D_region_field",
          "E_temporal_deferral", "F_non_authorizing_guard")
GUARD_FLAGS = ("authorizes_vision", "authorizes_descriptor_validity", "authorizes_temporal_order",
               "authorizes_runtime", "authorizes_memory", "authorizes_integration",
               "authorizes_screen", "authorizes_live", "authorizes_real_clip")
REQUIRED_FALSE_FLAGS = ("flat_field_validated", "descriptor_adopted", "coordinate_system_adopted",
                        "metric_adopted", "equation_adopted", "threshold_adopted",
                        "pass_fail_validity_rule_adopted", "tol_redefined",
                        "generator_family_expansion_authorized", "spectral_closure_reopened",
                        "flat_geometry_authorized", "screen_analysis_authorized", "runtime_authorized",
                        "memory_authorized", "real_clip_authorized", "vision_claim_allowed")


# ---- provenance ----
def test_imports_only_stdlib_no_torment():
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
    assert set(mods) <= {"__future__"}


def test_no_forbidden_implementation_tokens_in_source():
    # code-construct tokens only (the non-claims docstring legitimately mentions camera / screen / etc. in prose)
    src = open(SRC, encoding="utf-8").read()
    for tok in ("import numpy", "import cv2", "import torch", "tensorflow", "np.", "cv2.", "torch.",
                "coordinate_grid", "def _descriptor", "def _patchify", "def _grid("):
        assert tok not in src, tok


# ---- panels A-F present ----
def test_panels_A_to_F_present():
    r = m23.run()
    assert set(r["panels"].keys()) == set(PANELS)
    assert list(r["panels"]["C_spatial_relation"]["relations_named"]) == \
        ["adjacency", "neighborhood", "gradient", "edge", "continuity_discontinuity"]
    assert r["panels"]["A_patch_definition"]["coordinate_system_adopted"] is False
    assert r["panels"]["A_patch_definition"]["descriptor_adopted"] is False
    assert r["panels"]["B_opponent_channel"]["metric_adopted"] is False
    assert r["panels"]["C_spatial_relation"]["equations_adopted"] is False
    assert r["panels"]["D_region_field"]["pass_fail_rule_adopted"] is False
    assert r["panels"]["E_temporal_deferral"]["temporal_deferred"] is True
    assert r["panels"]["E_temporal_deferral"]["temporal_is_first_principle"] is False


# ---- required output booleans ----
def test_required_output_booleans_present_and_false():
    r = m23.run()
    assert r["reporting_only"] is True and r["conceptual_only"] is True and r["offline_only"] is True
    for k in REQUIRED_FALSE_FLAGS:
        assert k in r and r[k] is False, k


def test_v1x_frozen_v2x_unvalidated():
    r = m23.run()
    assert r["v1x_status"] == "frozen_evidence"
    assert r["v2x_status"] == "unvalidated_conceptual_pivot"


# ---- guard: all nine present + False; any missing OR True -> breach ----
def test_guard_all_nine_flags_present_and_false():
    r = m23.run()
    g = r["panels"]["F_non_authorizing_guard"]
    assert g["guard_present"] is True
    for k in GUARD_FLAGS:
        assert k in g and g[k] is False, k


@pytest.mark.parametrize("flag", ["authorizes_vision", "authorizes_temporal_order", "authorizes_screen",
                                  "authorizes_real_clip"])
def test_missing_required_guard_flag_forces_invalid(monkeypatch, flag):
    def stub():
        g = {k: False for k in m23.GUARD_FLAGS}
        g["guard_present"] = True
        del g[flag]                                                  # a REQUIRED flag is ABSENT -> inadmissible
        return g
    monkeypatch.setattr(m23, "_build_guard", stub)
    r = m23.run()
    assert r["protocol_ok"] is False
    assert r["outcome_label"] == "invalid_protocol_breach"


@pytest.mark.parametrize("flag", ["authorizes_vision", "authorizes_screen", "authorizes_real_clip",
                                  "authorizes_runtime"])
def test_true_required_guard_flag_forces_invalid(monkeypatch, flag):
    def stub():
        g = {k: False for k in m23.GUARD_FLAGS}
        g["guard_present"] = True
        g[flag] = True                                              # a required flag set True -> inadmissible
        return g
    monkeypatch.setattr(m23, "_build_guard", stub)
    r = m23.run()
    assert r["protocol_ok"] is False
    assert r["outcome_label"] == "invalid_protocol_breach"


def test_missing_guard_present_marker_forces_invalid(monkeypatch):
    def stub():
        return {k: False for k in m23.GUARD_FLAGS}                   # guard_present absent
    monkeypatch.setattr(m23, "_build_guard", stub)
    r = m23.run()
    assert r["protocol_ok"] is False


# ---- protocol_ok = presence/guard-only, not validation ----
def test_protocol_ok_is_presence_not_validation():
    r = m23.run()
    assert r["protocol_ok"] is True
    assert r["flat_field_validated"] is False
    # protocol_ok True while flat_field_validated False demonstrates presence-not-validation semantics


# ---- outcome label sealed + conservative ----
def test_outcome_label_sealed_and_conservative():
    r = m23.run()
    assert r["outcome_label"] in m23.OUTCOME_LABELS
    assert set(m23.OUTCOME_LABELS) == {"FLAT_OPPONENT_FIELD_REPORTING_GENERATED", "invalid_protocol_breach"}
    for lbl in m23.OUTCOME_LABELS:
        assert "validated" not in lbl and "closed" not in lbl and "achieved" not in lbl


def test_real_run_reports_generated():
    r = m23.run()
    assert r["outcome_label"] == "FLAT_OPPONENT_FIELD_REPORTING_GENERATED"
    assert r["protocol_ok"] is True
    assert all(r["obligation_conformance"][k] is True for k in PANELS)


# ---- determinism ----
def test_output_is_deterministic():
    assert repr(m23.run()) == repr(m23.run())


# ---- claim locks / verdict ----
def test_claim_locks_and_verdict_hold():
    r = m23.run()
    assert r["frozen_brainvision_verdict"] == "HOLD"
    assert r["first_pass_structure_validity_claim_allowed"] is False
    assert r["temporal_claim_allowed"] is False
    assert r["descriptor_validity_claim_allowed"] is False
    assert r["vision_claim"] is False and r["memory_readiness_claim"] is False
    assert r["runtime_readiness_claim"] is False and r["integration_readiness_claim"] is False
    assert r["learning"] is False and r["reporting_only"] is True


def test_no_temporal_or_recurrence_features():
    src = open(SRC, encoding="utf-8").read().lower()
    for tok in ("recurrence", "arrow_of_time", "time_reversed", "laminarity", "rqa", "diagonal_length"):
        assert tok not in src, tok
