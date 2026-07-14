"""v2.6 tests: flat opponent-field synthetic fixtures (form A, NON-LEARNING; REPORTING/guard only; offline).

Lock the v2.6 slice to ROBUST facts: it GENERATES the preregistered flat opponent-field synthetic fixture families
A-F as STRUCTURAL DESCRIPTIONS ONLY (no pixels / images / descriptor / coordinate system / metric / equation /
threshold / control metric / pass-fail validity gate / validation); controls (family F) are present; the
generated-vs-validated boundary is present and explicit; the adoption and authorization flag sets are
completeness-enforced (any required flag missing OR True forces invalid_protocol_breach), as are the claim locks; the
boundary, flat_field_validated, and verdict are each breach-checked; no fixture family claims validation; protocol_ok
means required family reports + controls + boundary + guards present only, NOT validation; fixture_reporting_generated
is True while flat_field_validated is always False; the label is conservative
(FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED / invalid_protocol_breach); output is deterministic; v1.x
stays frozen evidence and v2.x unvalidated; and claim locks stay False with verdict HOLD. Offline; no torment_service.
"""
import ast
import os
import sys

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_flat_opponent_field_synthetic_fixtures_v2_6 as m26              # noqa: E402

SRC = os.path.join(BV_DIR, "run_flat_opponent_field_synthetic_fixtures_v2_6.py")

FIXTURE_FAMILIES = ("A_uniform_opponent_patches", "B_adjacent_opponent_patches", "C_gradient_fields",
                    "D_edge_discontinuity_fields", "E_region_field_separation", "F_null_control_fields")
ADOPTION_FLAGS = ("descriptor_adopted", "coordinate_system_adopted", "metric_adopted", "equation_adopted",
                  "threshold_adopted", "control_metric_adopted", "pass_fail_validity_rule_adopted",
                  "tol_redefined", "generator_family_expanded", "spectral_closure_reopened")
AUTHORIZATION_FLAGS = ("screen_analysis_authorized", "camera_live_sensor_streaming_authorized",
                       "real_clip_authorized", "runtime_authorized", "memory_authorized",
                       "classifier_form_b_authorized", "neural_form_c_authorized",
                       "flat_geometry_beyond_reporting_authorized", "vision_claim_allowed",
                       "descriptor_validity_claim_allowed", "temporal_claim_allowed",
                       "integration_readiness_claim_allowed")
CLAIM_LOCK_FLAGS = ("first_pass_structure_validity_claim_allowed", "temporal_claim_allowed",
                    "descriptor_validity_claim_allowed", "vision_claim_allowed",
                    "integration_readiness_claim_allowed")


def _good_boundary():
    return {
        "boundary_present": True,
        "generated_means": "families A-F are generated as structural descriptions only",
        "validated_means": "validation would require descriptor/metric/evidence -- none exist",
        "generated_is_not_validated": True,
        "fixture_generated": True,
        "flat_field_validated": False,
    }


# ---- constant-set parity with the module (guards against silent flag-list drift) ----
def test_flag_sets_match_module():
    assert tuple(m26.ADOPTION_FLAGS) == ADOPTION_FLAGS
    assert tuple(m26.AUTHORIZATION_FLAGS) == AUTHORIZATION_FLAGS
    assert tuple(m26.CLAIM_LOCK_FLAGS) == CLAIM_LOCK_FLAGS
    assert "flat_geometry_beyond_reporting_authorized" in m26.AUTHORIZATION_FLAGS


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
    # code-construct tokens only (the non-claims docstring legitimately mentions camera / screen / pixels in prose)
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    for tok in ("import numpy", "import cv2", "import torch", "tensorflow", "np.", "cv2.", "torch.",
                "coordinate_grid", "def _descriptor", "def _patchify", "def _grid(", "np.array", "PIL",
                "imread", "VideoCapture"):
        assert tok not in src, tok


# ---- families A-F present as structural descriptions only ----
def test_fixture_families_A_to_F_present():
    r = m26.run()
    assert set(r["fixture_families"].keys()) == set(FIXTURE_FAMILIES)
    assert set(m26.FIXTURE_FAMILIES) == set(FIXTURE_FAMILIES)


def test_no_family_claims_validation_or_carries_numeric_surface():
    r = m26.run()
    for k, fx in r["fixture_families"].items():
        assert fx["claims_validation"] is False, k
        for absent_key in ("descriptor_present", "coordinates_present", "metric_present",
                           "equation_present", "threshold_present"):
            assert fx[absent_key] is False, (k, absent_key)


def test_controls_present():
    r = m26.run()
    assert "F_null_control_fields" in r["fixture_families"]
    assert r["fixture_families"]["F_null_control_fields"]["role"] == "control"
    assert "F_null_control_fields" in r["control_families"]


# ---- generated vs validated boundary present + explicit ----
def test_generated_vs_validated_boundary_present_and_explicit():
    r = m26.run()
    b = r["generated_vs_validated_boundary"]
    assert b["boundary_present"] is True
    assert b["generated_is_not_validated"] is True
    assert b["fixture_generated"] is True
    assert b["flat_field_validated"] is False
    assert isinstance(b["generated_means"], str) and b["generated_means"].strip()
    assert isinstance(b["validated_means"], str) and b["validated_means"].strip()


# ---- adoption flags: all present + False (nested and top-level) ----
def test_adoption_flags_present_and_false():
    r = m26.run()
    for k in ADOPTION_FLAGS:
        assert k in r["adoption_flags"] and r["adoption_flags"][k] is False, k
        assert k in r and r[k] is False, k


# ---- authorization flags: all present + False (nested and top-level) ----
def test_authorization_flags_present_and_false():
    r = m26.run()
    for k in AUTHORIZATION_FLAGS:
        assert k in r["authorization_flags"] and r["authorization_flags"][k] is False, k
        assert k in r and r[k] is False, k


# ---- required output booleans ----
def test_required_output_booleans():
    r = m26.run()
    assert r["reporting_only"] is True and r["conceptual_only"] is True and r["offline_only"] is True
    assert r["fixture_reporting_generated"] is True
    assert r["flat_field_validated"] is False


def test_v1x_frozen_v2x_unvalidated():
    r = m26.run()
    assert r["v1x_status"] == "frozen_evidence"
    assert r["v2x_status"] == "unvalidated_conceptual_pivot"


# ---- protocol failure conditions: each independently flips protocol_ok False ----
def test_missing_fixture_family_forces_invalid(monkeypatch):
    def stub(_orig=m26._build_fixture_families):                    # bind real builder before monkeypatch
        fam = _orig()
        del fam["C_gradient_fields"]
        return fam
    monkeypatch.setattr(m26, "_build_fixture_families", stub)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"


def test_family_claiming_validation_forces_invalid(monkeypatch):
    def stub(_orig=m26._build_fixture_families):                    # bind real builder before monkeypatch
        fam = _orig()
        fam["A_uniform_opponent_patches"]["claims_validation"] = True
        return fam
    monkeypatch.setattr(m26, "_build_fixture_families", stub)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"


def test_missing_controls_forces_invalid(monkeypatch):
    def stub(_orig=m26._build_fixture_families):                    # bind real builder before monkeypatch
        fam = _orig()
        fam["F_null_control_fields"]["role"] = "stimulus"          # no control role left -> controls missing
        return fam
    monkeypatch.setattr(m26, "_build_fixture_families", stub)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"


# boundary: every incompleteness / flat_field_validated-True mutation must breach
@pytest.mark.parametrize("mutate", [
    ("set", "flat_field_validated", True),
    ("del", "flat_field_validated", None),
    ("del", "generated_means", None),
    ("del", "validated_means", None),
    ("del", "generated_is_not_validated", None),
    ("del", "fixture_generated", None),
    ("del", "boundary_present", None),
    ("set", "boundary_present", False),
    ("set", "generated_means", ""),                                # empty text is not explicit
])
def test_boundary_incomplete_or_validated_forces_invalid(monkeypatch, mutate):
    op, key, val = mutate

    def stub():
        b = _good_boundary()
        if op == "del":
            del b[key]
        else:
            b[key] = val
        return b
    monkeypatch.setattr(m26, "_build_generated_vs_validated_boundary", stub)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"


def test_good_boundary_stub_still_valid(monkeypatch):
    # sanity: the test's _good_boundary is accepted, so the breach tests isolate the mutation, not the stub
    monkeypatch.setattr(m26, "_build_generated_vs_validated_boundary", _good_boundary)
    r = m26.run()
    assert r["protocol_ok"] is True


@pytest.mark.parametrize("flag", list(ADOPTION_FLAGS))
def test_missing_adoption_flag_forces_invalid(monkeypatch, flag):
    def stub():
        d = {k: False for k in m26.ADOPTION_FLAGS}
        del d[flag]
        return d
    monkeypatch.setattr(m26, "_build_adoption_flags", stub)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"


@pytest.mark.parametrize("flag", list(ADOPTION_FLAGS))
def test_true_adoption_flag_forces_invalid(monkeypatch, flag):
    def stub():
        d = {k: False for k in m26.ADOPTION_FLAGS}
        d[flag] = True
        return d
    monkeypatch.setattr(m26, "_build_adoption_flags", stub)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"


@pytest.mark.parametrize("flag", list(AUTHORIZATION_FLAGS))
def test_missing_authorization_flag_forces_invalid(monkeypatch, flag):
    def stub():
        d = {k: False for k in m26.AUTHORIZATION_FLAGS}
        del d[flag]
        return d
    monkeypatch.setattr(m26, "_build_authorization_flags", stub)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"


@pytest.mark.parametrize("flag", list(AUTHORIZATION_FLAGS))
def test_true_authorization_flag_forces_invalid(monkeypatch, flag):
    def stub():
        d = {k: False for k in m26.AUTHORIZATION_FLAGS}
        d[flag] = True
        return d
    monkeypatch.setattr(m26, "_build_authorization_flags", stub)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"


@pytest.mark.parametrize("flag", list(CLAIM_LOCK_FLAGS))
def test_claim_lock_moving_true_forces_invalid(monkeypatch, flag):
    def stub():
        d = {k: False for k in m26.CLAIM_LOCK_FLAGS}
        d[flag] = True
        return d
    monkeypatch.setattr(m26, "_build_claim_locks", stub)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"


def test_flat_field_validated_true_forces_invalid(monkeypatch):
    monkeypatch.setattr(m26, "_build_flat_field_validated", lambda: True)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"
    assert "flat_field_validated_true" in r["breaches"]


@pytest.mark.parametrize("bad_verdict", ["PASS", "CLOSED", "hold", "VALIDATED", ""])
def test_verdict_not_hold_forces_invalid(monkeypatch, bad_verdict):
    monkeypatch.setattr(m26, "_build_verdict", lambda: bad_verdict)
    r = m26.run()
    assert r["protocol_ok"] is False and r["outcome_label"] == "invalid_protocol_breach"
    assert "verdict_not_hold" in r["breaches"]


# ---- protocol_ok = presence/guard-only, not validation ----
def test_protocol_ok_is_presence_not_validation():
    r = m26.run()
    assert r["protocol_ok"] is True
    assert r["flat_field_validated"] is False
    # protocol_ok True while flat_field_validated False demonstrates presence-not-validation semantics


# ---- outcome label sealed + conservative ----
def test_outcome_label_sealed_and_conservative():
    r = m26.run()
    assert r["outcome_label"] in m26.OUTCOME_LABELS
    assert set(m26.OUTCOME_LABELS) == {"FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED",
                                       "invalid_protocol_breach"}
    for lbl in m26.OUTCOME_LABELS:
        assert "validated" not in lbl and "closed" not in lbl and "achieved" not in lbl


def test_real_run_reports_generated():
    r = m26.run()
    assert r["outcome_label"] == "FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED"
    assert r["protocol_ok"] is True
    assert r["breaches"] == []
    assert all(r["family_reporting"][k]["reported"] is True for k in FIXTURE_FAMILIES)


# ---- determinism ----
def test_output_is_deterministic():
    assert repr(m26.run()) == repr(m26.run())


# ---- claim locks / verdict ----
def test_claim_locks_and_verdict_hold():
    r = m26.run()
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
