"""v2.31 tests: BY/chroma entanglement-aware reporting SCHEMA (static symbolic; schema generation only; offline).

Lock the v2.31 slice to ROBUST facts: it builds a DETERMINISTIC STATIC SYMBOLIC schema of exactly the six reporting
outcome STANCES (BY_LEANING_UNRESOLVED, GENERIC_CHROMA_LEANING_UNRESOLVED, MATCHED_NON_BY_UNRESOLVED,
ENTANGLED_INSEPARABLE, FIXTURE_ARTIFACT_SUSPECTED, NULL_REPORTING_BOUNDARY); it TAKES NO INPUT (the builder accepts no
argument); it carries NO related_role_ids and NO role-to-outcome mapping (v2.30 Option A); no input / evidence /
decision / arrival / assignment field; no metric / score / threshold / formula / pass-fail / validation / classifier
field; and no descriptor / coordinate / fixture-instance / screen / runtime / memory / vision field. Every stance is
outcome_generated=True and outcome_validated=False; schema_generated=True and schema_validated=False; all claim locks,
adoption flags, and authorization guards are present, CLOSED, and False; verdict=HOLD; the conservative CANONICAL
protocol checker returns protocol_ok=True with empty breaches for the clean report and flips to False under every
mutation probe. Output is deterministic. Offline; no torment_service.

Protocol greenness means BOUNDARY COMPLIANCE ONLY. It is not schema validity, not correctness, not distinguishability,
and not readiness. The v2.22 question stays UNRESOLVED.
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

import by_chroma_entanglement_reporting_schema_v2_31 as m231                   # noqa: E402

SRC = os.path.join(BV_DIR, "by_chroma_entanglement_reporting_schema_v2_31.py")

REQUIRED_OUTCOMES = ("BY_LEANING_UNRESOLVED", "GENERIC_CHROMA_LEANING_UNRESOLVED", "MATCHED_NON_BY_UNRESOLVED",
                     "ENTANGLED_INSEPARABLE", "FIXTURE_ARTIFACT_SUSPECTED", "NULL_REPORTING_BOUNDARY")

OUTCOME_ALLOWED_KEYS = {"outcome_id", "outcome_label", "reporting_stance", "entanglement_status", "non_claim_status",
                        "allowed_language", "forbidden_language", "outcome_generated", "outcome_validated"}

REQUIRED_TOP_LEVEL = ("version", "reporting_only", "offline_research_only", "symbolic_schema_only", "schema_generated",
                      "schema_validated", "outcome_label", "allowed_outcomes", "claim_locks", "adoption_flags",
                      "authorization_guards", "protocol", "verdict")

REQUIRED_CLAIM_LOCKS = ("flat_field_validated", "role_validated", "schema_validated", "entanglement_resolved",
                        "by_residual_isolated", "generic_chroma_proxy_ruled_out",
                        "first_pass_structure_validity_claim_allowed", "temporal_claim_allowed",
                        "descriptor_validity_claim_allowed", "geometry_validity_claim_allowed",
                        "screen_readiness_claim_allowed", "runtime_readiness_claim_allowed",
                        "memory_readiness_claim_allowed", "integration_readiness_claim_allowed",
                        "vision_claim_allowed")

REQUIRED_ADOPTION_FLAGS = ("descriptor_adopted", "coordinate_system_adopted", "metric_adopted", "threshold_adopted",
                           "scoring_adopted", "formula_adopted", "pass_fail_gate_adopted", "validation_adopted",
                           "classifier_adopted", "neural_path_adopted")

REQUIRED_AUTHORIZATION_GUARDS = ("screen_path_authorized", "runtime_path_authorized", "memory_path_authorized",
                                 "integration_path_authorized", "real_clip_path_authorized", "vision_claim_authorized")

# every field name the artifact must never carry, anywhere
BANNED_FIELD_SUBSTRINGS = ("related_role", "role_to_outcome", "role_id", "mapping", "input", "evidence", "decision",
                           "arrival", "assign", "classif", "confidence", "score", "metric", "threshold", "formula",
                           "pass_fail", "validation_result", "descriptor", "coordinate", "fixture_instance", "screen",
                           "runtime", "memory", "vision", "neural", "clip", "pixel", "array", "image")


def _rep():
    return m231.build_by_chroma_entanglement_reporting_schema_v2_31()


def _all_field_names(report):
    """Every SCHEMA field name: top-level keys, protocol keys, and outcome-stance keys.

    The claim_locks / adoption_flags / authorization_guards MEMBER names are deliberately excluded: those names
    legitimately contain the banned tokens (descriptor_adopted, metric_adopted, memory_path_authorized, ...) because
    they are the LOCKS AGAINST those things, held False. A lock named after a hazard is not the hazard.
    """
    names = [k for k in report.keys()]
    names += list(report.get("protocol", {}).keys())
    for obj in report.get("allowed_outcomes", {}).values():
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
    with open(SRC, encoding="utf-8") as fh:
        src = fh.read()
    for tok in ("import numpy", "import cv2", "import torch", "tensorflow", "np.", "cv2.", "torch.",
                "imread(", "VideoCapture", "pygame"):
        assert tok not in src, tok


# ---- (7) the artifact takes NO input: the builder accepts no argument ----
def test_builder_accepts_no_input():
    sig = inspect.signature(m231.build_by_chroma_entanglement_reporting_schema_v2_31)
    assert len(sig.parameters) == 0


# ---- (1) clean report is green ----
def test_protocol_ok_clean():
    chk = m231.check_protocol(_rep())
    assert chk["protocol_ok"] is True
    assert chk["breaches"] == []


def test_protocol_ok_when_called_without_argument():
    chk = m231.check_protocol()
    assert chk["protocol_ok"] is True and chk["breaches"] == []


# ---- (2) exactly six canonical outcome IDs ----
def test_exactly_six_canonical_outcomes():
    r = _rep()
    assert set(r["allowed_outcomes"].keys()) == set(REQUIRED_OUTCOMES)
    assert tuple(m231.REQUIRED_OUTCOMES) == REQUIRED_OUTCOMES
    for oid, obj in r["allowed_outcomes"].items():
        assert obj["outcome_id"] == oid


def test_outcome_keys_are_symbolic_allowlist():
    r = _rep()
    for oid, obj in r["allowed_outcomes"].items():
        assert set(obj.keys()) == OUTCOME_ALLOWED_KEYS, (oid, set(obj.keys()))


def test_top_level_keys_exact():
    r = _rep()
    assert set(r.keys()) == set(REQUIRED_TOP_LEVEL)


# ---- (3) / (4) generated, not validated ----
def test_every_outcome_generated_true():
    for oid, obj in _rep()["allowed_outcomes"].items():
        assert obj["outcome_generated"] is True, oid


def test_every_outcome_validated_false():
    for oid, obj in _rep()["allowed_outcomes"].items():
        assert obj["outcome_validated"] is False, oid


def test_schema_generated_true_schema_validated_false():
    r = _rep()
    assert r["schema_generated"] is True
    assert r["schema_validated"] is False


# ---- (5) / (6) no related_role_ids, no role-to-outcome mapping ----
def test_no_related_role_ids_anywhere():
    names = _all_field_names(_rep())
    for n in names:
        assert "related_role" not in n.lower(), n
        assert "role_id" not in n.lower(), n


def test_no_role_to_outcome_mapping_fields():
    names = _all_field_names(_rep())
    for n in names:
        low = n.lower()
        assert "role_to_outcome" not in low, n
        assert "mapping" not in low, n


def test_no_role_reference_in_source_schema_fields():
    """Option A: the artifact has no field that could carry a v2.24 role reference at all."""
    r = _rep()
    for obj in r["allowed_outcomes"].values():
        for k in obj:
            assert "role" not in k.lower(), k


# ---- (7) / (8) / (9) forbidden field families absent ----
@pytest.mark.parametrize("banned", BANNED_FIELD_SUBSTRINGS)
def test_no_forbidden_field_names_anywhere(banned):
    for n in _all_field_names(_rep()):
        assert banned not in n.lower(), (banned, n)


def test_no_numeric_or_container_values_in_outcomes():
    for oid, obj in _rep()["allowed_outcomes"].items():
        for k, v in obj.items():
            assert not isinstance(v, dict), (oid, k)
            if isinstance(v, bool):
                continue
            assert not isinstance(v, (int, float)), (oid, k)
            if isinstance(v, (list, tuple)):
                for el in v:
                    assert isinstance(el, str), (oid, k, el)


# ---- canonical text carries no claim wording (forbidden_language cites, never asserts) ----
def test_canonical_stance_text_free_of_forbidden_wording():
    r = _rep()
    strings = []
    for obj in r["allowed_outcomes"].values():
        for k in ("outcome_label", "reporting_stance", "entanglement_status", "non_claim_status"):
            strings.append(obj[k])
        strings += obj["allowed_language"]
    for k, v in r["protocol"].items():
        if isinstance(v, str):
            strings.append(v)
    for s in strings:
        low = s.lower()
        for phrase in m231.FORBIDDEN_WORDING:
            assert phrase not in low, (phrase, s)


def test_forbidden_language_is_exactly_the_canonical_citation_list():
    for oid, obj in _rep()["allowed_outcomes"].items():
        assert list(obj["forbidden_language"]) == list(m231.FORBIDDEN_LANGUAGE), oid
    for required in ("BY residual isolated", "generic chroma proxy ruled out", "entanglement resolved",
                     "descriptor validated", "geometry validated", "visual structure detected", "fixture passed",
                     "screen ready", "runtime ready", "memory ready", "vision achieved", "Brainvision sees"):
        assert required in m231.FORBIDDEN_LANGUAGE, required


# ---- ENTANGLED_INSEPARABLE stays a first-class unresolved endpoint ----
def test_entangled_inseparable_is_first_class_endpoint():
    o = _rep()["allowed_outcomes"]["ENTANGLED_INSEPARABLE"]
    assert o["outcome_generated"] is True
    assert o["outcome_validated"] is False
    assert o["entanglement_status"] == "entanglement is the reported outcome"
    low = o["non_claim_status"].lower()
    for denied in ("not failure", "not success", "not noise", "not an implementation defect", "not an else-branch",
                   "not hidden by evidence", "not validation", "not closure"):
        assert denied in low, denied
    assert _rep()["protocol"]["entangled_endpoint_is_first_class"] is True


def test_outcome_set_is_not_exhaustive_and_not_partitioning():
    p = _rep()["protocol"]
    assert p["outcome_set_is_exhaustive"] is False
    assert p["outcome_set_is_partitioning"] is False
    assert p["unresolved_is_part_of_the_outcome_name"] is True


def test_unresolved_stays_in_the_outcome_names():
    for oid in ("BY_LEANING_UNRESOLVED", "GENERIC_CHROMA_LEANING_UNRESOLVED", "MATCHED_NON_BY_UNRESOLVED"):
        assert oid.endswith("_UNRESOLVED")
        assert "unresolved" in _rep()["allowed_outcomes"][oid]["outcome_label"].lower()


# ---- (10) / (11) / (12) locks, flags, guards present and False ----
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


# ---- (13) verdict / label / version ----
def test_verdict_hold():
    assert _rep()["verdict"] == "HOLD"


def test_outcome_label_and_version():
    r = _rep()
    assert r["outcome_label"] == "BRAINVISION_BY_CHROMA_ENTANGLEMENT_REPORTING_SCHEMA_ONLY"
    assert r["version"] == "v2.31"


# ---- (14) mutation probes: each must flip protocol_ok False ----
def _mut_missing_top_level_key(r):
    del r["protocol"]


def _mut_extra_top_level_key(r):
    r["extra_thing"] = "x"


def _mut_missing_outcome(r):
    del r["allowed_outcomes"]["MATCHED_NON_BY_UNRESOLVED"]


def _mut_extra_outcome(r):
    r["allowed_outcomes"]["BY_CONFIRMED"] = copy.deepcopy(r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"])


def _mut_wrong_outcome_id(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["outcome_id"] = "BY_LEANING"


def _mut_wrong_outcome_label(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["outcome_label"] = "BY-leaning"


def _mut_outcome_validated_true(r):
    r["allowed_outcomes"]["ENTANGLED_INSEPARABLE"]["outcome_validated"] = True


def _mut_outcome_generated_false(r):
    r["allowed_outcomes"]["ENTANGLED_INSEPARABLE"]["outcome_generated"] = False


def _mut_schema_validated_true(r):
    r["schema_validated"] = True


def _mut_claim_lock_true(r):
    r["claim_locks"]["entanglement_resolved"] = True


def _mut_extra_false_claim_lock(r):
    r["claim_locks"]["some_new_claim_allowed"] = False


def _mut_missing_claim_lock(r):
    del r["claim_locks"]["by_residual_isolated"]


def _mut_adoption_flag_true(r):
    r["adoption_flags"]["metric_adopted"] = True


def _mut_extra_false_adoption_flag(r):
    r["adoption_flags"]["equation_adopted"] = False


def _mut_missing_adoption_flag(r):
    del r["adoption_flags"]["classifier_adopted"]


def _mut_authorization_guard_true(r):
    r["authorization_guards"]["vision_claim_authorized"] = True


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


def _mut_related_role_ids_field(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["related_role_ids"] = ["A"]


def _mut_role_to_outcome_mapping_field(r):
    r["role_to_outcome_mapping"] = "A -> BY_LEANING_UNRESOLVED"


def _mut_input_field(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["input"] = "case"


def _mut_evidence_field(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["evidence"] = "e"


def _mut_decision_field(r):
    r["decision_rule"] = "pick the highest"


def _mut_arrival_field(r):
    r["arrival"] = "how we got here"


def _mut_assignment_field(r):
    r["allowed_outcomes"]["ENTANGLED_INSEPARABLE"]["assignment"] = "case_7"


def _mut_metric_field(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["metric"] = "rho"


def _mut_score_field(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["score"] = "high"


def _mut_threshold_field(r):
    r["threshold"] = "0"


def _mut_formula_field(r):
    r["formula"] = "x"


def _mut_pass_fail_field(r):
    r["allowed_outcomes"]["NULL_REPORTING_BOUNDARY"]["pass_fail"] = "pass"


def _mut_validation_result_field(r):
    r["validation_result"] = "ok"


def _mut_classifier_field(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["classifier_label"] = "BY"


def _mut_descriptor_field(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["descriptor"] = "d"


def _mut_coordinate_field(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["coordinate"] = "0,0"


def _mut_fixture_instance_field(r):
    r["fixture_instance"] = "f1"


def _mut_screen_field(r):
    r["screen"] = "x"


def _mut_runtime_field(r):
    r["runtime"] = "x"


def _mut_memory_field(r):
    r["memory"] = "x"


def _mut_vision_field(r):
    r["vision"] = "x"


def _mut_numeric_value_in_outcome(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["outcome_label"] = 5


# --- claiming wording inside allowed string fields ---
def _mut_stance_wording_validation_claim(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["reporting_stance"] = "BY residual isolated; descriptor validated"


def _mut_entanglement_status_resolved_claim(r):
    r["allowed_outcomes"]["ENTANGLED_INSEPARABLE"]["entanglement_status"] = "entanglement resolved"


def _mut_non_claim_status_readiness_claim(r):
    r["allowed_outcomes"]["NULL_REPORTING_BOUNDARY"]["non_claim_status"] = "screen ready; runtime ready; memory ready"


def _mut_allowed_language_vision_claim(r):
    r["allowed_outcomes"]["ENTANGLED_INSEPARABLE"]["allowed_language"] = ["Brainvision sees"]


def _mut_outcome_label_descriptor_coordinate_wording(r):
    r["allowed_outcomes"]["MATCHED_NON_BY_UNRESOLVED"]["outcome_label"] = "descriptor coordinate class"


def _mut_forbidden_language_entry_dropped(r):
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["forbidden_language"] = ["BY residual isolated"]


def _mut_forbidden_language_entry_added(r):
    fl = list(r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["forbidden_language"])
    fl.append("BY residual isolated is now permitted")
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["forbidden_language"] = fl


def _mut_protocol_exhaustive_true(r):
    r["protocol"]["outcome_set_is_exhaustive"] = True


def _mut_protocol_entangled_not_first_class(r):
    r["protocol"]["entangled_endpoint_is_first_class"] = False


def _mut_protocol_extra_field(r):
    r["protocol"]["arrival_rule"] = "x"


@pytest.mark.parametrize("mut", [
    _mut_missing_top_level_key,
    _mut_extra_top_level_key,
    _mut_missing_outcome,
    _mut_extra_outcome,
    _mut_wrong_outcome_id,
    _mut_wrong_outcome_label,
    _mut_outcome_validated_true,
    _mut_outcome_generated_false,
    _mut_schema_validated_true,
    _mut_claim_lock_true,
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
    _mut_related_role_ids_field,
    _mut_role_to_outcome_mapping_field,
    _mut_input_field,
    _mut_evidence_field,
    _mut_decision_field,
    _mut_arrival_field,
    _mut_assignment_field,
    _mut_metric_field,
    _mut_score_field,
    _mut_threshold_field,
    _mut_formula_field,
    _mut_pass_fail_field,
    _mut_validation_result_field,
    _mut_classifier_field,
    _mut_descriptor_field,
    _mut_coordinate_field,
    _mut_fixture_instance_field,
    _mut_screen_field,
    _mut_runtime_field,
    _mut_memory_field,
    _mut_vision_field,
    _mut_numeric_value_in_outcome,
    _mut_stance_wording_validation_claim,
    _mut_entanglement_status_resolved_claim,
    _mut_non_claim_status_readiness_claim,
    _mut_allowed_language_vision_claim,
    _mut_outcome_label_descriptor_coordinate_wording,
    _mut_forbidden_language_entry_dropped,
    _mut_forbidden_language_entry_added,
    _mut_protocol_exhaustive_true,
    _mut_protocol_entangled_not_first_class,
    _mut_protocol_extra_field,
])
def test_mutation_probe_flips_protocol_ok_false(mut):
    r = _rep()
    mut(r)
    chk = m231.check_protocol(r)
    assert chk["protocol_ok"] is False
    assert len(chk["breaches"]) >= 1


# ---- named breaches: each gate is live and specific ----
def test_named_breach_related_role_ids():
    r = _rep()
    r["allowed_outcomes"]["BY_LEANING_UNRESOLVED"]["related_role_ids"] = ["A"]
    b = m231.check_protocol(r)["breaches"]
    assert "forbidden_outcome_field:BY_LEANING_UNRESOLVED.related_role_ids" in b
    assert "forbidden_field_token:BY_LEANING_UNRESOLVED.related_role_ids:related_role" in b


def test_named_breach_role_to_outcome_mapping():
    r = _rep()
    r["role_to_outcome_mapping"] = "A -> BY_LEANING_UNRESOLVED"
    b = m231.check_protocol(r)["breaches"]
    assert "forbidden_top_level_field:role_to_outcome_mapping" in b
    assert "forbidden_field_token:top.role_to_outcome_mapping:role_to_outcome" in b


def test_named_breach_extra_false_locks_flags_guards():
    r = _rep()
    r["claim_locks"]["some_new_claim_allowed"] = False
    r["adoption_flags"]["equation_adopted"] = False
    r["authorization_guards"]["camera_path_authorized"] = False
    b = m231.check_protocol(r)["breaches"]
    assert "claim_lock_extra:some_new_claim_allowed" in b
    assert "adoption_flag_extra:equation_adopted" in b
    assert "authorization_guard_extra:camera_path_authorized" in b


def test_named_breach_schema_validated_and_verdict():
    r = _rep()
    r["schema_validated"] = True
    r["verdict"] = "PASS"
    b = m231.check_protocol(r)["breaches"]
    assert "schema_validated_true" in b
    assert "verdict_not_hold" in b


def test_named_breach_outcome_validated_true():
    r = _rep()
    r["allowed_outcomes"]["ENTANGLED_INSEPARABLE"]["outcome_validated"] = True
    b = m231.check_protocol(r)["breaches"]
    assert "outcome_validated_true:ENTANGLED_INSEPARABLE" in b


def test_named_breach_forbidden_wording_in_stance():
    r = _rep()
    r["allowed_outcomes"]["ENTANGLED_INSEPARABLE"]["entanglement_status"] = "entanglement resolved"
    b = m231.check_protocol(r)["breaches"]
    assert "forbidden_wording:ENTANGLED_INSEPARABLE.entanglement_status:entanglement resolved" in b
    assert "noncanonical_outcome_field:ENTANGLED_INSEPARABLE.entanglement_status" in b


def test_named_breach_missing_and_extra_outcome():
    r = _rep()
    del r["allowed_outcomes"]["ENTANGLED_INSEPARABLE"]
    r["allowed_outcomes"]["BY_CONFIRMED"] = {"outcome_id": "BY_CONFIRMED"}
    b = m231.check_protocol(r)["breaches"]
    assert "missing_outcome:ENTANGLED_INSEPARABLE" in b
    assert "extra_outcome:BY_CONFIRMED" in b


# ---- determinism ----
def test_output_is_deterministic():
    assert repr(_rep()) == repr(_rep())
    assert repr(m231.check_protocol(_rep())) == repr(m231.check_protocol(_rep()))
