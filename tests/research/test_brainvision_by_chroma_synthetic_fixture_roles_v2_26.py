"""v2.26 tests: BY/chroma synthetic fixture ROLES (static symbolic; reporting only; offline).

Lock the v2.26 slice to ROBUST facts: it builds a DETERMINISTIC STATIC SYMBOLIC report of exactly the six v2.24
BY/chroma conceptual roles (A BY-dominant chroma residual, B generic chroma proxy, C matched non-BY chroma, D BY/chroma
entangled, E fixture-family artifact, F null / reporting-boundary), carrying symbolic / reporting fields only -- no
fixtures, no fixture data, no arrays / vectors / images / pixels / coordinates, no descriptors, no metrics / scores /
thresholds / formulas, no pass-fail gates, no validation, no expected outputs, no classifier or neural content, and no
screen / runtime / memory / vision paths. Every role has role_generated=True and role_validated=False; all claim locks,
adoption flags, and authorization guards are present and False; flat_field_validated=False; verdict=HOLD; outcome label
BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_REPORTING_ONLY; the conservative CANONICAL protocol checker returns
protocol_ok=True with empty breaches for the clean report and flips to False under every mutation probe -- including
missing / extra / wrong roles, validated roles, a PASS verdict, a moved lock / flag / guard, an EXTRA key added to the
lock / flag / guard groups even when its value is False (an extra False key silently widens the guarded surface),
forbidden concrete fields, and forbidden claiming wording (validation / closure / readiness / screen / runtime /
memory / classifier / neural / vision) inside an allowed string field. Output is deterministic. Offline; no
torment_service.

Protocol greenness here means BOUNDARY COMPLIANCE ONLY. It is not validation, not distinguishability, not descriptor
validity, not closure, and not readiness. The v2.22 primary question stays UNRESOLVED.
"""
import ast
import copy
import os
import sys

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import by_chroma_synthetic_fixture_roles_v2_26 as m226                        # noqa: E402

SRC = os.path.join(BV_DIR, "by_chroma_synthetic_fixture_roles_v2_26.py")

REQUIRED_ROLES = ("A_BY_dominant_chroma_residual_role",
                  "B_generic_chroma_proxy_role",
                  "C_matched_non_BY_chroma_role",
                  "D_BY_chroma_entangled_role",
                  "E_fixture_family_artifact_role",
                  "F_null_reporting_boundary_role")

ROLE_ALLOWED_KEYS = {"role_id", "role_label", "conceptual_purpose", "reporting_focus", "non_claim_constraints",
                     "forbidden_interpretations", "safe_reporting_language", "role_generated", "role_validated"}

REQUIRED_CLAIM_LOCKS = ("flat_field_validated", "first_pass_structure_validity_claim_allowed",
                        "temporal_claim_allowed", "descriptor_validity_claim_allowed",
                        "geometry_validity_claim_allowed", "screen_readiness_claim_allowed",
                        "runtime_readiness_claim_allowed", "memory_readiness_claim_allowed",
                        "integration_readiness_claim_allowed", "vision_claim_allowed",
                        "role_validity_claim_allowed", "residual_localization_claim_allowed",
                        "proxy_resolved_claim_allowed", "metric_separation_claim_allowed",
                        "closure_claim_allowed", "validation_claim_allowed")

REQUIRED_ADOPTION_FLAGS = ("descriptor_adopted", "coordinate_system_adopted", "metric_adopted", "threshold_adopted",
                           "scoring_adopted", "pass_fail_gate_adopted")


def _rep():
    return m226.build_by_chroma_synthetic_fixture_roles_v2_26()


# ---- provenance ----
def test_stdlib_only_imports():
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


def test_no_numeric_or_vision_libs_in_source():
    src = open(SRC, encoding="utf-8").read()
    for tok in ("import numpy", "import cv2", "import torch", "tensorflow", "np.", "cv2.", "torch.",
                "imread(", "VideoCapture", "pygame"):
        assert tok not in src, tok


# ---- exactly the six v2.24 roles ----
def test_exactly_six_roles():
    r = _rep()
    assert set(r["roles"].keys()) == set(REQUIRED_ROLES)
    assert tuple(m226.REQUIRED_ROLES) == REQUIRED_ROLES


def test_role_keys_are_symbolic_allowlist():
    r = _rep()
    for rname, robj in r["roles"].items():
        assert set(robj.keys()) == ROLE_ALLOWED_KEYS, (rname, set(robj.keys()))


def test_reporting_focus_from_closed_label_set():
    r = _rep()
    for rname, robj in r["roles"].items():
        focus = robj["reporting_focus"]
        assert isinstance(focus, str) and focus in m226.ALLOWED_REPORTING_FOCUS, (rname, focus)


def test_reporting_lists_are_nonempty_string_lists():
    r = _rep()
    for rname, robj in r["roles"].items():
        for key in ("non_claim_constraints", "forbidden_interpretations", "safe_reporting_language"):
            val = robj[key]
            assert isinstance(val, list) and len(val) > 0, (rname, key)
            for el in val:
                assert isinstance(el, str), (rname, key, el)


def test_no_numeric_or_container_values_in_roles():
    r = _rep()
    for rname, robj in r["roles"].items():
        for k, v in robj.items():
            assert not isinstance(v, dict), (rname, k, "nested dict")
            if isinstance(v, bool):
                continue
            assert not isinstance(v, (int, float)), (rname, k, "numeric value")
            if isinstance(v, (list, tuple)):
                for el in v:
                    assert isinstance(el, str), (rname, k, "non-string list element")


def test_no_forbidden_concrete_field_keys_in_roles():
    r = _rep()
    for rname, robj in r["roles"].items():
        for k in robj:
            low = k.lower()
            for tok in m226.FORBIDDEN_KEY_TOKENS:
                assert tok not in low, (rname, k, tok)


def test_every_role_generated_true():
    r = _rep()
    for rname, robj in r["roles"].items():
        assert robj["role_generated"] is True, rname


def test_every_role_validated_false():
    r = _rep()
    for rname, robj in r["roles"].items():
        assert robj["role_validated"] is False, rname


# ---- canonical text carries no claiming wording (generation is not validation) ----
def test_canonical_report_free_of_forbidden_wording():
    r = _rep()
    strings = [r["note"]]
    for robj in r["roles"].values():
        for v in robj.values():
            if isinstance(v, str):
                strings.append(v)
            elif isinstance(v, list):
                strings += [el for el in v if isinstance(el, str)]
    for s in strings:
        low = s.lower()
        for phrase in m226.FORBIDDEN_WORDING:
            assert phrase not in low, (phrase, s)


# ---- locks / flags / guards all present and False ----
def test_required_claim_locks_present_and_false():
    r = _rep()
    for k in REQUIRED_CLAIM_LOCKS:
        assert k in r["claim_locks"] and r["claim_locks"][k] is False, k
    assert set(m226.CLAIM_LOCKS) == set(REQUIRED_CLAIM_LOCKS)


def test_required_adoption_flags_present_and_false():
    r = _rep()
    for k in REQUIRED_ADOPTION_FLAGS:
        assert k in r["adoption_flags"] and r["adoption_flags"][k] is False, k
    assert set(m226.ADOPTION_FLAGS) == set(REQUIRED_ADOPTION_FLAGS)


def test_all_authorization_guards_present_and_false():
    r = _rep()
    for k in m226.AUTHORIZATION_GUARDS:
        assert k in r["authorization_guards"] and r["authorization_guards"][k] is False, k


# ---- top-level scalars ----
def test_scalar_report_flags():
    r = _rep()
    assert r["reporting_only"] is True
    assert r["offline_research_only"] is True
    assert r["symbolic_static_only"] is True


def test_flat_field_validated_false():
    assert _rep()["flat_field_validated"] is False


def test_verdict_hold():
    assert _rep()["verdict"] == "HOLD"


def test_outcome_label_and_version():
    r = _rep()
    assert r["outcome_label"] == "BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_REPORTING_ONLY"
    assert r["version"] == "v2.26"
    assert m226.OUTCOME_LABEL == "BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_REPORTING_ONLY"


# ---- protocol checker: clean ----
def test_protocol_ok_clean():
    chk = m226.check_protocol(_rep())
    assert chk["protocol_ok"] is True
    assert chk["breaches"] == []


def test_protocol_ok_when_called_without_argument():
    chk = m226.check_protocol()
    assert chk["protocol_ok"] is True and chk["breaches"] == []


# ---- protocol checker: mutation probes each flip protocol_ok False ----
def _mut_missing_role(r):
    del r["roles"]["C_matched_non_BY_chroma_role"]


def _mut_extra_role(r):
    r["roles"]["G_extra_role"] = copy.deepcopy(r["roles"]["A_BY_dominant_chroma_residual_role"])


def _mut_wrong_role_name(r):
    r["roles"]["Z_bogus_role"] = r["roles"].pop("F_null_reporting_boundary_role")


def _mut_role_validated_true(r):
    r["roles"]["A_BY_dominant_chroma_residual_role"]["role_validated"] = True


def _mut_role_generated_false(r):
    r["roles"]["B_generic_chroma_proxy_role"]["role_generated"] = False


def _mut_flat_field_validated_true(r):
    r["flat_field_validated"] = True


def _mut_verdict_pass(r):
    r["verdict"] = "PASS"


def _mut_claim_lock_true(r):
    r["claim_locks"]["temporal_claim_allowed"] = True


def _mut_role_validity_claim_lock_true(r):
    r["claim_locks"]["role_validity_claim_allowed"] = True


def _mut_closure_claim_lock_true(r):
    r["claim_locks"]["closure_claim_allowed"] = True


def _mut_adoption_flag_true(r):
    r["adoption_flags"]["metric_adopted"] = True


def _mut_pass_fail_gate_adopted_true(r):
    r["adoption_flags"]["pass_fail_gate_adopted"] = True


def _mut_authorization_guard_true(r):
    r["authorization_guards"]["implementation_authorizes_validation"] = True


def _mut_extra_false_claim_lock(r):
    r["claim_locks"]["some_new_claim_allowed"] = False


def _mut_extra_false_adoption_flag(r):
    r["adoption_flags"]["equation_adopted"] = False


def _mut_extra_false_authorization_guard(r):
    r["authorization_guards"]["implementation_authorizes_metric_claim"] = False


def _mut_forbidden_coordinate_field(r):
    r["roles"]["A_BY_dominant_chroma_residual_role"]["x_coordinate"] = "0"


def _mut_forbidden_fixture_data_field(r):
    r["roles"]["A_BY_dominant_chroma_residual_role"]["fixture_data"] = "patch"


def _mut_forbidden_descriptor_field(r):
    r["roles"]["B_generic_chroma_proxy_role"]["descriptor"] = "d"


def _mut_forbidden_metric_field(r):
    r["roles"]["B_generic_chroma_proxy_role"]["metric"] = "rho"


def _mut_forbidden_threshold_field(r):
    r["roles"]["C_matched_non_BY_chroma_role"]["threshold"] = "high"


def _mut_forbidden_score_field(r):
    r["roles"]["C_matched_non_BY_chroma_role"]["score"] = "high"


def _mut_forbidden_vector_field(r):
    r["roles"]["D_BY_chroma_entangled_role"]["vector"] = [1, 2, 3]


def _mut_forbidden_image_field(r):
    r["roles"]["D_BY_chroma_entangled_role"]["image"] = "x"


def _mut_forbidden_classifier_field(r):
    r["roles"]["E_fixture_family_artifact_role"]["classifier"] = "label"


def _mut_forbidden_neural_field(r):
    r["roles"]["E_fixture_family_artifact_role"]["neural_encoding"] = "e"


def _mut_forbidden_screen_field(r):
    r["roles"]["F_null_reporting_boundary_role"]["screen"] = "x"


def _mut_forbidden_pass_fail_field(r):
    r["roles"]["F_null_reporting_boundary_role"]["pass_fail"] = "pass"


def _mut_numeric_value_in_allowed_field(r):
    r["roles"]["E_fixture_family_artifact_role"]["role_id"] = 5


def _mut_forbidden_reporting_focus_label(r):
    r["roles"]["A_BY_dominant_chroma_residual_role"]["reporting_focus"] = "measured_by_axis"


def _mut_extra_top_level_field(r):
    r["threshold"] = "0"


def _mut_bad_outcome_label(r):
    r["outcome_label"] = "BRAINVISION_BY_CHROMA_ROLES_VALIDATED"


def _mut_bad_version(r):
    r["version"] = "v9.9"


def _mut_empty_non_claim_constraints(r):
    r["roles"]["A_BY_dominant_chroma_residual_role"]["non_claim_constraints"] = []


def _mut_empty_forbidden_interpretations(r):
    r["roles"]["B_generic_chroma_proxy_role"]["forbidden_interpretations"] = []


def _mut_delete_safe_reporting_language(r):
    del r["roles"]["C_matched_non_BY_chroma_role"]["safe_reporting_language"]


# --- string-content holes: claiming wording inside ALLOWED string fields ---
def _mut_note_validation_vision_claim(r):
    r["note"] = "brainvision sees and the descriptor is valid"


def _mut_role_label_validation_claim(r):
    r["roles"]["A_BY_dominant_chroma_residual_role"]["role_label"] = "role is valid"


def _mut_purpose_closure_claim(r):
    r["roles"]["D_BY_chroma_entangled_role"]["conceptual_purpose"] = "closure achieved; the residual is separable"


def _mut_purpose_readiness_claim(r):
    r["roles"]["C_matched_non_BY_chroma_role"]["conceptual_purpose"] = "ready for integration; is ready"


def _mut_constraints_proxy_solved_claim(r):
    r["roles"]["B_generic_chroma_proxy_role"]["non_claim_constraints"] = ["the proxy is controlled"]


def _mut_constraints_not_an_artifact_claim(r):
    r["roles"]["E_fixture_family_artifact_role"]["non_claim_constraints"] = ["not an artifact"]


def _mut_constraints_null_passed_claim(r):
    r["roles"]["F_null_reporting_boundary_role"]["non_claim_constraints"] = ["the null control passed"]


def _mut_safe_language_scored_separation_claim(r):
    r["roles"]["A_BY_dominant_chroma_residual_role"]["safe_reporting_language"] = ["a separation score"]


def _mut_interpretations_runtime_memory_claim(r):
    r["roles"]["D_BY_chroma_entangled_role"]["forbidden_interpretations"] = ["opens a runtime path and a memory path"]


def _mut_interpretations_classifier_neural_claim(r):
    r["roles"]["E_fixture_family_artifact_role"]["forbidden_interpretations"] = ["a classifier label and neural target"]


# --- identity / content holes: drift from the canonical A-F role report ---
def _mut_wrong_role_id(r):
    r["roles"]["A_BY_dominant_chroma_residual_role"]["role_id"] = "Z"


def _mut_wrong_role_label(r):
    r["roles"]["C_matched_non_BY_chroma_role"]["role_label"] = "totally different label"


def _mut_allowed_but_wrong_reporting_focus(r):
    r["roles"]["F_null_reporting_boundary_role"]["reporting_focus"] = "artifact_suspicion_focus"


def _mut_dropped_constraint_entry(r):
    r["roles"]["A_BY_dominant_chroma_residual_role"]["non_claim_constraints"] = ["nothing to see here"]


@pytest.mark.parametrize("mut", [
    _mut_missing_role,
    _mut_extra_role,
    _mut_wrong_role_name,
    _mut_role_validated_true,
    _mut_role_generated_false,
    _mut_flat_field_validated_true,
    _mut_verdict_pass,
    _mut_claim_lock_true,
    _mut_role_validity_claim_lock_true,
    _mut_closure_claim_lock_true,
    _mut_adoption_flag_true,
    _mut_pass_fail_gate_adopted_true,
    _mut_authorization_guard_true,
    _mut_extra_false_claim_lock,
    _mut_extra_false_adoption_flag,
    _mut_extra_false_authorization_guard,
    _mut_forbidden_coordinate_field,
    _mut_forbidden_fixture_data_field,
    _mut_forbidden_descriptor_field,
    _mut_forbidden_metric_field,
    _mut_forbidden_threshold_field,
    _mut_forbidden_score_field,
    _mut_forbidden_vector_field,
    _mut_forbidden_image_field,
    _mut_forbidden_classifier_field,
    _mut_forbidden_neural_field,
    _mut_forbidden_screen_field,
    _mut_forbidden_pass_fail_field,
    _mut_numeric_value_in_allowed_field,
    _mut_forbidden_reporting_focus_label,
    _mut_extra_top_level_field,
    _mut_bad_outcome_label,
    _mut_bad_version,
    _mut_empty_non_claim_constraints,
    _mut_empty_forbidden_interpretations,
    _mut_delete_safe_reporting_language,
    _mut_note_validation_vision_claim,
    _mut_role_label_validation_claim,
    _mut_purpose_closure_claim,
    _mut_purpose_readiness_claim,
    _mut_constraints_proxy_solved_claim,
    _mut_constraints_not_an_artifact_claim,
    _mut_constraints_null_passed_claim,
    _mut_safe_language_scored_separation_claim,
    _mut_interpretations_runtime_memory_claim,
    _mut_interpretations_classifier_neural_claim,
    _mut_wrong_role_id,
    _mut_wrong_role_label,
    _mut_allowed_but_wrong_reporting_focus,
    _mut_dropped_constraint_entry,
])
def test_mutation_probe_flips_protocol_ok_false(mut):
    r = _rep()
    mut(r)
    chk = m226.check_protocol(r)
    assert chk["protocol_ok"] is False
    assert len(chk["breaches"]) >= 1


# ---- named breaches: the canonical gate and the wording gate are both live ----
def test_canonical_note_breach_named():
    r = _rep()
    r["note"] = "brainvision sees and the descriptor is valid"
    chk = m226.check_protocol(r)
    assert "noncanonical_note" in chk["breaches"]


def test_canonical_role_field_breach_named():
    r = _rep()
    r["roles"]["A_BY_dominant_chroma_residual_role"]["conceptual_purpose"] = "a measured BY axis"
    chk = m226.check_protocol(r)
    assert "noncanonical_role_field:A_BY_dominant_chroma_residual_role.conceptual_purpose" in chk["breaches"]


def test_forbidden_wording_breach_named_in_note():
    r = _rep()
    r["note"] = "brainvision sees and the descriptor is valid"
    chk = m226.check_protocol(r)
    assert "forbidden_wording:note:brainvision sees" in chk["breaches"]
    assert "forbidden_wording:note:descriptor is valid" in chk["breaches"]


def test_forbidden_wording_breach_named_in_role_list_entry():
    r = _rep()
    r["roles"]["E_fixture_family_artifact_role"]["non_claim_constraints"] = ["not an artifact"]
    chk = m226.check_protocol(r)
    assert "forbidden_wording:E_fixture_family_artifact_role.non_claim_constraints:not an artifact" in chk["breaches"]


def test_role_validated_breach_named():
    r = _rep()
    r["roles"]["A_BY_dominant_chroma_residual_role"]["role_validated"] = True
    chk = m226.check_protocol(r)
    assert "role_validated_true:A_BY_dominant_chroma_residual_role" in chk["breaches"]


def test_verdict_breach_named():
    r = _rep()
    r["verdict"] = "PASS"
    chk = m226.check_protocol(r)
    assert "verdict_not_hold" in chk["breaches"]


def test_extra_false_claim_lock_breach_named():
    r = _rep()
    r["claim_locks"]["some_new_claim_allowed"] = False
    chk = m226.check_protocol(r)
    assert chk["protocol_ok"] is False
    assert "claim_lock_extra:some_new_claim_allowed" in chk["breaches"]


def test_extra_false_adoption_flag_breach_named():
    r = _rep()
    r["adoption_flags"]["equation_adopted"] = False
    chk = m226.check_protocol(r)
    assert chk["protocol_ok"] is False
    assert "adoption_flag_extra:equation_adopted" in chk["breaches"]


def test_extra_false_authorization_guard_breach_named():
    r = _rep()
    r["authorization_guards"]["implementation_authorizes_metric_claim"] = False
    chk = m226.check_protocol(r)
    assert chk["protocol_ok"] is False
    assert "authorization_guard_extra:implementation_authorizes_metric_claim" in chk["breaches"]


def test_forbidden_concrete_field_breach_named():
    r = _rep()
    r["roles"]["A_BY_dominant_chroma_residual_role"]["fixture_data"] = "patch"
    chk = m226.check_protocol(r)
    assert "forbidden_role_field:A_BY_dominant_chroma_residual_role.fixture_data" in chk["breaches"]
    assert "forbidden_token_field:A_BY_dominant_chroma_residual_role.fixture_data" in chk["breaches"]


# ---- determinism ----
def test_output_is_deterministic():
    assert repr(_rep()) == repr(_rep())
    assert repr(m226.check_protocol(_rep())) == repr(m226.check_protocol(_rep()))
