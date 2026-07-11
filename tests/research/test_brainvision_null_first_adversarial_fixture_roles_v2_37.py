"""v2.37 tests: null-first adversarial family ROLES (static symbolic; role generation only; offline).

Lock the v2.37 slice to ROBUST facts: it builds a DETERMINISTIC STATIC SYMBOLIC report of exactly the six v2.35
null-first adversarial family roles (A null / no-structure, B fixture-artifact, C proxy-confound, D entangled /
unresolved, E control-collapse, F candidate-structure-survival); it TAKES NO INPUT (the builder accepts no argument);
it carries NO fixture / fixture-data / generation-rule / schema / data-shape field, NO descriptor / coordinate / metric
/ score / threshold / formula field, NO decision / arrival / evidence / confidence / classification field, NO
validation / pass-fail / survival / positive-structure field, and NO screen / runtime / memory / real-clip / vision
field. Every role is role_generated=True and role_validated=False; roles_generated=True; all claim locks, adoption
flags, and authorization guards are present, CLOSED, and False; verdict=HOLD; the conservative CANONICAL protocol
checker returns protocol_ok=True with empty breaches for the clean report and flips to False under every mutation
probe. Output is deterministic. Offline; no torment_service.

W1: E_control_collapse_role is reachable in LANGUAGE ONLY -- control_collapse_detected and control_collapse_ruled_out
both stay False, and no string may claim collapse was tested, detected, ruled out, avoided, or handled.
W2: F_candidate_structure_survival_role is ONLY a future question -- candidate_structure_survived /
_detected / _validated all stay False, and no string may imply survival, detection, validation, or expectation.
W4: protocol greenness means canonical symbolic structure + forbidden-surface absence. It is NOT scientific validity,
fixture quality, control quality, detection, survival, or falsification success. There is no adversary here; there are
six nouns.
"""
import ast
import copy
import inspect
import os
import sys

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import null_first_adversarial_fixture_roles_v2_37 as m237                      # noqa: E402

SRC = os.path.join(BV_DIR, "null_first_adversarial_fixture_roles_v2_37.py")

REQUIRED_ROLES = ("A_null_no_structure_role", "B_fixture_artifact_role", "C_proxy_confound_role",
                  "D_entangled_unresolved_role", "E_control_collapse_role", "F_candidate_structure_survival_role")

# role_id carries the FULL canonical v2.35 role ID (not a short letter): the nested id must equal the key it is filed
# under, so the artifact cannot drift away from the accepted v2.35 names.
CANONICAL_LABELS = {
    "A_null_no_structure_role": ("A_null_no_structure_role", "null / no-structure role"),
    "B_fixture_artifact_role": ("B_fixture_artifact_role", "fixture-artifact role"),
    "C_proxy_confound_role": ("C_proxy_confound_role", "proxy-confound role"),
    "D_entangled_unresolved_role": ("D_entangled_unresolved_role", "entangled / unresolved role"),
    "E_control_collapse_role": ("E_control_collapse_role", "control-collapse role"),
    "F_candidate_structure_survival_role": ("F_candidate_structure_survival_role",
                                            "candidate-structure-survival role"),
}

ROLE_ALLOWED_KEYS = {"role_id", "role_label", "conceptual_purpose", "adversarial_focus", "safe_reporting_language",
                     "forbidden_interpretations", "non_claim_constraints", "role_generated", "role_validated"}

REQUIRED_TOP_LEVEL = ("version", "reporting_only", "offline_research_only", "symbolic_role_reporting_only",
                      "roles_generated", "outcome_label", "roles", "claim_locks", "adoption_flags",
                      "authorization_guards", "protocol", "verdict")

REQUIRED_CLAIM_LOCKS = ("flat_field_validated", "role_validated", "schema_validated", "entanglement_resolved",
                        "by_residual_isolated", "generic_chroma_proxy_ruled_out", "null_rejected",
                        "artifact_ruled_out", "proxy_ruled_out", "confound_controlled", "control_collapse_ruled_out",
                        "control_collapse_detected", "candidate_structure_validated", "candidate_structure_survived",
                        "candidate_structure_detected", "first_pass_structure_validity_claim_allowed",
                        "temporal_claim_allowed", "descriptor_validity_claim_allowed",
                        "geometry_validity_claim_allowed", "screen_readiness_claim_allowed",
                        "runtime_readiness_claim_allowed", "memory_readiness_claim_allowed",
                        "integration_readiness_claim_allowed", "vision_claim_allowed")

REQUIRED_ADOPTION_FLAGS = ("descriptor_adopted", "coordinate_system_adopted", "metric_adopted", "threshold_adopted",
                           "scoring_adopted", "formula_adopted", "generation_rule_adopted", "schema_adopted",
                           "pass_fail_gate_adopted", "validation_adopted", "classifier_adopted", "neural_path_adopted")

REQUIRED_AUTHORIZATION_GUARDS = ("screen_path_authorized", "runtime_path_authorized", "memory_path_authorized",
                                 "integration_path_authorized", "real_clip_path_authorized",
                                 "fixture_generation_authorized", "vision_claim_authorized")

# field-name substrings the artifact must never carry. (Role IDs are canonical v2.35 names and are NOT field names --
# F_candidate_structure_survival_role legitimately contains "survival". The ban is on FIELDS.)
BANNED_FIELD_SUBSTRINGS = ("fixture_instance", "fixture_data", "generation", "schema", "data_shape", "array", "image",
                           "descriptor", "coordinate", "metric", "score", "threshold", "formula", "decision",
                           "arrival", "evidence", "confidence", "classif", "validation", "pass_fail", "survival",
                           "positive_structure", "screen", "runtime", "memory", "real_clip", "vision", "neural",
                           "input", "assign")


def _rep():
    return m237.build_null_first_adversarial_fixture_roles_v2_37()


def _schema_field_names(report):
    """Every SCHEMA FIELD name: top-level keys, protocol keys, and role-object keys.

    Excluded on purpose: the ROLE IDS (canonical v2.35 names) and the claim_lock / adoption_flag /
    authorization_guard MEMBER names -- those names contain the banned tokens BECAUSE they are the locks against
    those things, held False. A lock named after a hazard is not the hazard.
    """
    names = [k for k in report.keys()]
    names += list(report.get("protocol", {}).keys())
    for obj in report.get("roles", {}).values():
        if isinstance(obj, dict):
            names += list(obj.keys())
    return names


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


def test_builder_accepts_no_input():
    sig = inspect.signature(m237.build_null_first_adversarial_fixture_roles_v2_37)
    assert len(sig.parameters) == 0


# ---- (1) clean report is green ----
def test_protocol_ok_clean():
    chk = m237.check_protocol(_rep())
    assert chk["protocol_ok"] is True
    assert chk["breaches"] == []


def test_protocol_ok_when_called_without_argument():
    chk = m237.check_protocol()
    assert chk["protocol_ok"] is True and chk["breaches"] == []


# ---- (2) / (3) exactly six canonical roles, canonical ids and labels ----
def test_exactly_six_canonical_roles():
    r = _rep()
    assert set(r["roles"].keys()) == set(REQUIRED_ROLES)
    assert tuple(m237.REQUIRED_ROLES) == REQUIRED_ROLES


def test_canonical_role_ids_and_labels():
    r = _rep()
    for rid, (cid, clabel) in CANONICAL_LABELS.items():
        assert r["roles"][rid]["role_id"] == cid, rid
        assert r["roles"][rid]["role_label"] == clabel, rid


def test_nested_role_id_is_the_full_canonical_v2_35_id():
    """The nested role_id must be the FULL v2.35 canonical ID and must equal the key it is filed under -- never a
    short letter. Guards against silent drift away from the accepted v2.35 role names."""
    r = _rep()
    for rid, obj in r["roles"].items():
        assert obj["role_id"] == rid, (rid, obj["role_id"])
        assert obj["role_id"] in REQUIRED_ROLES, rid
        assert len(obj["role_id"]) > 1, rid


def test_role_keys_are_symbolic_allowlist():
    for rid, obj in _rep()["roles"].items():
        assert set(obj.keys()) == ROLE_ALLOWED_KEYS, (rid, set(obj.keys()))


def test_top_level_keys_exact():
    assert set(_rep().keys()) == set(REQUIRED_TOP_LEVEL)


# ---- (4) / (5) generated, not validated ----
def test_every_role_generated_true():
    for rid, obj in _rep()["roles"].items():
        assert obj["role_generated"] is True, rid


def test_every_role_validated_false():
    for rid, obj in _rep()["roles"].items():
        assert obj["role_validated"] is False, rid


def test_roles_generated_flag_true():
    assert _rep()["roles_generated"] is True


# ---- (6)-(12) forbidden field families absent ----
@pytest.mark.parametrize("banned", BANNED_FIELD_SUBSTRINGS)
def test_no_forbidden_field_names_anywhere(banned):
    for n in _schema_field_names(_rep()):
        assert banned not in n.lower(), (banned, n)


def test_no_numeric_or_container_values_in_roles():
    for rid, obj in _rep()["roles"].items():
        for k, v in obj.items():
            assert not isinstance(v, dict), (rid, k)
            if isinstance(v, bool):
                continue
            assert not isinstance(v, (int, float)), (rid, k)
            if isinstance(v, (list, tuple)):
                for el in v:
                    assert isinstance(el, str), (rid, k, el)


# ---- canonical text carries no claim wording ----
def test_canonical_text_free_of_forbidden_wording():
    r = _rep()
    strings = []
    for obj in r["roles"].values():
        for v in obj.values():
            if isinstance(v, str):
                strings.append(v)
            elif isinstance(v, list):
                strings += [el for el in v if isinstance(el, str)]
    for v in r["protocol"].values():
        if isinstance(v, str):
            strings.append(v)
    for s in strings:
        low = s.lower()
        for phrase in m237.FORBIDDEN_WORDING:
            assert phrase not in low, (phrase, s)


# ---- W1 / W2 / W3 held in the artifact itself ----
def test_w1_control_collapse_reachable_in_language_only():
    r = _rep()
    e = r["roles"]["E_control_collapse_role"]
    assert e["role_generated"] is True
    assert e["role_validated"] is False
    assert r["claim_locks"]["control_collapse_detected"] is False
    assert r["claim_locks"]["control_collapse_ruled_out"] is False
    assert r["protocol"]["control_collapse_reachable_in_language_only"] is True
    joined = " ".join(e["forbidden_interpretations"]).lower()
    for denied in ("tested", "found", "avoided", "handled", "excluded"):
        assert denied in joined, denied


def test_w2_candidate_survival_is_only_a_future_question():
    r = _rep()
    f = r["roles"]["F_candidate_structure_survival_role"]
    assert f["safe_reporting_language"] == ["candidate structure remains only a future question"]
    assert r["claim_locks"]["candidate_structure_survived"] is False
    assert r["claim_locks"]["candidate_structure_detected"] is False
    assert r["claim_locks"]["candidate_structure_validated"] is False
    assert r["protocol"]["candidate_role_is_a_future_question_only"] is True
    joined = " ".join(f["forbidden_interpretations"]).lower()
    for denied in ("detection", "validation", "expectation", "else-branch"):
        assert denied in joined, denied


def test_w3_roles_non_exhaustive_and_non_partitioning():
    p = _rep()["protocol"]
    assert p["roles_are_exhaustive"] is False
    assert p["roles_are_partitioning"] is False


def test_null_role_is_a_valid_endpoint_not_a_failure():
    a = _rep()["roles"]["A_null_no_structure_role"]
    joined = (" ".join(a["forbidden_interpretations"]) + " " + " ".join(a["non_claim_constraints"])).lower()
    assert "rejected" in joined
    assert "failed run" in joined


def test_entangled_role_is_not_noise_or_hidden_evidence():
    d = _rep()["roles"]["D_entangled_unresolved_role"]
    joined = " ".join(d["forbidden_interpretations"]).lower()
    for denied in ("noise", "hidden evidence", "failure", "success", "else-branch"):
        assert denied in joined, denied


# ---- (13) / (14) / (15) locks, flags, guards present and False ----
def test_all_claim_locks_present_and_false():
    r = _rep()
    assert set(r["claim_locks"].keys()) == set(REQUIRED_CLAIM_LOCKS)
    for k in REQUIRED_CLAIM_LOCKS:
        assert r["claim_locks"][k] is False, k


def test_all_adoption_flags_present_and_false():
    r = _rep()
    assert set(r["adoption_flags"].keys()) == set(REQUIRED_ADOPTION_FLAGS)
    for k in REQUIRED_ADOPTION_FLAGS:
        assert r["adoption_flags"][k] is False, k


def test_all_authorization_guards_present_and_false():
    r = _rep()
    assert set(r["authorization_guards"].keys()) == set(REQUIRED_AUTHORIZATION_GUARDS)
    for k in REQUIRED_AUTHORIZATION_GUARDS:
        assert r["authorization_guards"][k] is False, k


# ---- (16) verdict / label / version ----
def test_verdict_hold():
    assert _rep()["verdict"] == "HOLD"


def test_outcome_label_and_version():
    r = _rep()
    assert r["outcome_label"] == "BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_ROLES_REPORTING_ONLY"
    assert r["version"] == "v2.37"


# ---- (17) mutation probes ----
def _mut_missing_top_level_key(r):
    del r["protocol"]


def _mut_extra_top_level_key(r):
    r["extra_thing"] = "x"


def _mut_missing_role(r):
    del r["roles"]["C_proxy_confound_role"]


def _mut_extra_role(r):
    r["roles"]["G_structure_confirmed_role"] = copy.deepcopy(r["roles"]["A_null_no_structure_role"])


def _mut_wrong_role_id(r):
    r["roles"]["A_null_no_structure_role"]["role_id"] = "Z"


def _mut_wrong_role_label(r):
    r["roles"]["E_control_collapse_role"]["role_label"] = "control-collapse check"


def _mut_role_validated_true(r):
    r["roles"]["F_candidate_structure_survival_role"]["role_validated"] = True


def _mut_role_generated_false(r):
    r["roles"]["A_null_no_structure_role"]["role_generated"] = False


def _mut_roles_generated_false(r):
    r["roles_generated"] = False


def _mut_claim_lock_true(r):
    r["claim_locks"]["control_collapse_detected"] = True


def _mut_candidate_survived_lock_true(r):
    r["claim_locks"]["candidate_structure_survived"] = True


def _mut_extra_false_claim_lock(r):
    r["claim_locks"]["some_new_claim_allowed"] = False


def _mut_missing_claim_lock(r):
    del r["claim_locks"]["null_rejected"]


def _mut_adoption_flag_true(r):
    r["adoption_flags"]["generation_rule_adopted"] = True


def _mut_extra_false_adoption_flag(r):
    r["adoption_flags"]["equation_adopted"] = False


def _mut_missing_adoption_flag(r):
    del r["adoption_flags"]["schema_adopted"]


def _mut_authorization_guard_true(r):
    r["authorization_guards"]["fixture_generation_authorized"] = True


def _mut_extra_false_authorization_guard(r):
    r["authorization_guards"]["camera_path_authorized"] = False


def _mut_missing_authorization_guard(r):
    del r["authorization_guards"]["memory_path_authorized"]


def _mut_verdict_pass(r):
    r["verdict"] = "PASS"


def _mut_bad_version(r):
    r["version"] = "v9.9"


def _mut_reporting_only_false(r):
    r["reporting_only"] = False


# --- forbidden field families ---
def _mut_fixture_instances_field(r):
    r["fixture_instances"] = "f1"


def _mut_fixture_data_field(r):
    r["roles"]["B_fixture_artifact_role"]["fixture_data"] = "patch"


def _mut_generation_rule_field(r):
    r["generation_rules"] = "make cases"


def _mut_schema_field(r):
    r["schema"] = "s"


def _mut_data_shape_field(r):
    r["roles"]["A_null_no_structure_role"]["data_shape"] = "n"


def _mut_descriptor_field(r):
    r["roles"]["A_null_no_structure_role"]["descriptor"] = "d"


def _mut_coordinate_field(r):
    r["roles"]["A_null_no_structure_role"]["coordinate"] = "0,0"


def _mut_metric_field(r):
    r["roles"]["C_proxy_confound_role"]["metric"] = "rho"


def _mut_score_field(r):
    r["roles"]["C_proxy_confound_role"]["score"] = "high"


def _mut_threshold_field(r):
    r["threshold"] = "0"


def _mut_formula_field(r):
    r["formula"] = "x"


def _mut_decision_field(r):
    r["decision_rule"] = "pick one"


def _mut_arrival_field(r):
    r["arrival"] = "how we got here"


def _mut_evidence_field(r):
    r["roles"]["D_entangled_unresolved_role"]["evidence"] = "e"


def _mut_confidence_field(r):
    r["roles"]["D_entangled_unresolved_role"]["confidence"] = "high"


def _mut_classification_field(r):
    r["roles"]["D_entangled_unresolved_role"]["classification"] = "class"


def _mut_validation_field(r):
    r["validation"] = "ok"


def _mut_pass_fail_field(r):
    r["roles"]["E_control_collapse_role"]["pass_fail"] = "pass"


def _mut_survival_field(r):
    r["roles"]["F_candidate_structure_survival_role"]["survival"] = "yes"


def _mut_positive_structure_field(r):
    r["positive_structure"] = "found"


def _mut_screen_field(r):
    r["screen"] = "x"


def _mut_runtime_field(r):
    r["runtime"] = "x"


def _mut_memory_field(r):
    r["memory"] = "x"


def _mut_real_clip_field(r):
    r["real_clip"] = "x"


def _mut_vision_field(r):
    r["vision"] = "x"


def _mut_numeric_value_in_role(r):
    r["roles"]["A_null_no_structure_role"]["role_id"] = 1


# --- forbidden claim wording in allowed string fields ---
def _mut_wording_structure_detected(r):
    r["roles"]["F_candidate_structure_survival_role"]["conceptual_purpose"] = "structure detected"


def _mut_wording_candidate_survived(r):
    r["roles"]["F_candidate_structure_survival_role"]["safe_reporting_language"] = ["candidate survived"]


def _mut_wording_null_rejected(r):
    r["roles"]["A_null_no_structure_role"]["non_claim_constraints"] = ["null rejected"]


def _mut_wording_artifact_ruled_out(r):
    r["roles"]["B_fixture_artifact_role"]["non_claim_constraints"] = ["artifact ruled out"]


def _mut_wording_proxy_ruled_out_confound_controlled(r):
    r["roles"]["C_proxy_confound_role"]["adversarial_focus"] = "proxy ruled out and confound controlled"


def _mut_wording_control_passed(r):
    r["roles"]["E_control_collapse_role"]["adversarial_focus"] = "control passed"


def _mut_wording_fixture_passed(r):
    r["roles"]["B_fixture_artifact_role"]["role_label"] = "fixture passed"


def _mut_wording_descriptor_geometry_metric_validated(r):
    r["roles"]["D_entangled_unresolved_role"]["conceptual_purpose"] = \
        "descriptor validated; geometry validated; metric validated"


def _mut_wording_readiness_claims(r):
    r["roles"]["D_entangled_unresolved_role"]["adversarial_focus"] = "screen ready; runtime ready; memory ready"


def _mut_wording_vision_achieved_brainvision_sees(r):
    r["roles"]["A_null_no_structure_role"]["safe_reporting_language"] = ["vision achieved", "Brainvision sees"]


def _mut_protocol_roles_exhaustive_true(r):
    r["protocol"]["roles_are_exhaustive"] = True


def _mut_protocol_extra_field(r):
    r["protocol"]["arrival_rule"] = "x"


@pytest.mark.parametrize("mut", [
    _mut_missing_top_level_key,
    _mut_extra_top_level_key,
    _mut_missing_role,
    _mut_extra_role,
    _mut_wrong_role_id,
    _mut_wrong_role_label,
    _mut_role_validated_true,
    _mut_role_generated_false,
    _mut_roles_generated_false,
    _mut_claim_lock_true,
    _mut_candidate_survived_lock_true,
    _mut_extra_false_claim_lock,
    _mut_missing_claim_lock,
    _mut_adoption_flag_true,
    _mut_extra_false_adoption_flag,
    _mut_missing_adoption_flag,
    _mut_authorization_guard_true,
    _mut_extra_false_authorization_guard,
    _mut_missing_authorization_guard,
    _mut_verdict_pass,
    _mut_bad_version,
    _mut_reporting_only_false,
    _mut_fixture_instances_field,
    _mut_fixture_data_field,
    _mut_generation_rule_field,
    _mut_schema_field,
    _mut_data_shape_field,
    _mut_descriptor_field,
    _mut_coordinate_field,
    _mut_metric_field,
    _mut_score_field,
    _mut_threshold_field,
    _mut_formula_field,
    _mut_decision_field,
    _mut_arrival_field,
    _mut_evidence_field,
    _mut_confidence_field,
    _mut_classification_field,
    _mut_validation_field,
    _mut_pass_fail_field,
    _mut_survival_field,
    _mut_positive_structure_field,
    _mut_screen_field,
    _mut_runtime_field,
    _mut_memory_field,
    _mut_real_clip_field,
    _mut_vision_field,
    _mut_numeric_value_in_role,
    _mut_wording_structure_detected,
    _mut_wording_candidate_survived,
    _mut_wording_null_rejected,
    _mut_wording_artifact_ruled_out,
    _mut_wording_proxy_ruled_out_confound_controlled,
    _mut_wording_control_passed,
    _mut_wording_fixture_passed,
    _mut_wording_descriptor_geometry_metric_validated,
    _mut_wording_readiness_claims,
    _mut_wording_vision_achieved_brainvision_sees,
    _mut_protocol_roles_exhaustive_true,
    _mut_protocol_extra_field,
])
def test_mutation_probe_flips_protocol_ok_false(mut):
    r = _rep()
    mut(r)
    chk = m237.check_protocol(r)
    assert chk["protocol_ok"] is False
    assert len(chk["breaches"]) >= 1


# ---- named breaches ----
def test_named_breach_survival_field():
    r = _rep()
    r["roles"]["F_candidate_structure_survival_role"]["survival"] = "yes"
    b = m237.check_protocol(r)["breaches"]
    assert "forbidden_role_field:F_candidate_structure_survival_role.survival" in b
    assert "forbidden_field_token:F_candidate_structure_survival_role.survival:survival" in b


def test_named_breach_fixture_generation_field():
    r = _rep()
    r["generation_rules"] = "make cases"
    b = m237.check_protocol(r)["breaches"]
    assert "forbidden_top_level_field:generation_rules" in b
    assert "forbidden_field_token:top.generation_rules:generation" in b


def test_named_breach_extra_false_locks_flags_guards():
    r = _rep()
    r["claim_locks"]["some_new_claim_allowed"] = False
    r["adoption_flags"]["equation_adopted"] = False
    r["authorization_guards"]["camera_path_authorized"] = False
    b = m237.check_protocol(r)["breaches"]
    assert "claim_lock_extra:some_new_claim_allowed" in b
    assert "adoption_flag_extra:equation_adopted" in b
    assert "authorization_guard_extra:camera_path_authorized" in b


def test_named_breach_role_validated_and_verdict():
    r = _rep()
    r["roles"]["E_control_collapse_role"]["role_validated"] = True
    r["verdict"] = "PASS"
    b = m237.check_protocol(r)["breaches"]
    assert "role_validated_true:E_control_collapse_role" in b
    assert "verdict_not_hold" in b


def test_named_breach_forbidden_wording():
    r = _rep()
    r["roles"]["F_candidate_structure_survival_role"]["conceptual_purpose"] = "structure detected"
    b = m237.check_protocol(r)["breaches"]
    assert "forbidden_wording:F_candidate_structure_survival_role.conceptual_purpose:structure detected" in b
    assert "noncanonical_role_field:F_candidate_structure_survival_role.conceptual_purpose" in b


def test_named_breach_missing_and_extra_role():
    r = _rep()
    r["roles"].pop("E_control_collapse_role")
    r["roles"]["G_structure_confirmed_role"] = {"role_id": "G"}
    b = m237.check_protocol(r)["breaches"]
    assert "missing_role:E_control_collapse_role" in b
    assert "extra_role:G_structure_confirmed_role" in b


# ---- determinism ----
def test_output_is_deterministic():
    assert repr(_rep()) == repr(_rep())
    assert repr(m237.check_protocol(_rep())) == repr(m237.check_protocol(_rep()))
