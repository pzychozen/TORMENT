"""v2.9 tests: flat opponent-field SYMBOLIC representation (static symbolic; representation only; offline).

Lock the v2.9 slice to ROBUST facts: it builds a STATIC SYMBOLIC representation of exactly the six existing A-F
fixture families, with symbolic component/relation labels only (no pixels / images / coordinates / vectors / arrays /
numeric geometry / descriptors / metrics / equations / thresholds / scores / pass-fail); every family has
fixture_represented=True and representation_validated=False; all claim locks, adoption flags, and authorization guards
are present and False; flat_field_validated=False; verdict=HOLD; outcome label
FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY; the conservative CANONICAL protocol checker returns protocol_ok=True
with empty breaches for the clean report and flips to False under every mutation probe -- including claiming/forbidden
text in allowed string fields and any drift from the canonical A-F identity/content; output is deterministic. Offline;
no torment_service.
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

import flat_opponent_field_representation_v2_9 as m29                       # noqa: E402

SRC = os.path.join(BV_DIR, "flat_opponent_field_representation_v2_9.py")

REQUIRED_FAMILIES = ("A_uniform_opponent_patches", "B_adjacent_opponent_patches", "C_gradient_fields",
                     "D_edge_discontinuity_fields", "E_region_field_separation_fixtures", "F_null_control_fields")
FAMILY_ALLOWED_KEYS = {"family_id", "family_label", "conceptual_components", "conceptual_relations",
                       "boundary_notes", "fixture_represented", "representation_validated"}


def _rep():
    return m29.build_flat_opponent_field_representation_v2_9()


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


# ---- families A-F present, symbolic/static ----
def test_exactly_six_families():
    r = _rep()
    assert set(r["fixture_families"].keys()) == set(REQUIRED_FAMILIES)
    assert tuple(m29.REQUIRED_FAMILIES) == REQUIRED_FAMILIES


def test_family_keys_are_symbolic_allowlist():
    r = _rep()
    for fname, fobj in r["fixture_families"].items():
        assert set(fobj.keys()) <= FAMILY_ALLOWED_KEYS, (fname, set(fobj.keys()))
        for req in FAMILY_ALLOWED_KEYS:
            assert req in fobj, (fname, req)


def test_components_and_relations_from_allowed_sets():
    r = _rep()
    for fname, fobj in r["fixture_families"].items():
        comps = fobj["conceptual_components"]
        rels = fobj["conceptual_relations"]
        assert isinstance(comps, list) and len(comps) > 0, fname
        assert isinstance(rels, list), fname
        for c in comps:
            assert isinstance(c, str) and c in m29.ALLOWED_COMPONENTS, (fname, c)
        for rel in rels:
            assert isinstance(rel, str) and rel in m29.ALLOWED_RELATIONS, (fname, rel)


def test_no_numeric_or_container_values_in_families():
    r = _rep()
    for fname, fobj in r["fixture_families"].items():
        for k, v in fobj.items():
            assert not isinstance(v, dict), (fname, k, "nested dict")
            if isinstance(v, bool):
                continue
            assert not isinstance(v, (int, float)), (fname, k, "numeric value")
            if isinstance(v, (list, tuple)):
                for el in v:
                    assert isinstance(el, str), (fname, k, "non-string list element")


def test_every_family_fixture_represented_true():
    r = _rep()
    for fname, fobj in r["fixture_families"].items():
        assert fobj["fixture_represented"] is True, fname


def test_every_family_representation_validated_false():
    r = _rep()
    for fname, fobj in r["fixture_families"].items():
        assert fobj["representation_validated"] is False, fname


# ---- locks / flags / guards all False ----
def test_all_claim_locks_present_and_false():
    r = _rep()
    for k in m29.CLAIM_LOCKS:
        assert k in r["claim_locks"] and r["claim_locks"][k] is False, k


def test_all_adoption_flags_present_and_false():
    r = _rep()
    for k in m29.ADOPTION_FLAGS:
        assert k in r["adoption_flags"] and r["adoption_flags"][k] is False, k


def test_all_authorization_guards_present_and_false():
    r = _rep()
    for k in m29.AUTHORIZATION_GUARDS:
        assert k in r["authorization_guards"] and r["authorization_guards"][k] is False, k


# ---- top-level scalars ----
def test_scalar_report_flags():
    r = _rep()
    assert r["representation_only"] is True
    assert r["offline_research_only"] is True
    assert r["symbolic_static_only"] is True


def test_flat_field_validated_false():
    assert _rep()["flat_field_validated"] is False


def test_verdict_hold():
    assert _rep()["verdict"] == "HOLD"


def test_outcome_label_and_version():
    r = _rep()
    assert r["outcome_label"] == "FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY"
    assert r["version"] == "v2.9"
    assert m29.OUTCOME_LABEL == "FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY"


# ---- protocol checker: clean ----
def test_protocol_ok_clean():
    chk = m29.check_protocol(_rep())
    assert chk["protocol_ok"] is True
    assert chk["breaches"] == []


def test_protocol_ok_when_called_without_argument():
    chk = m29.check_protocol()
    assert chk["protocol_ok"] is True and chk["breaches"] == []


# ---- protocol checker: mutation probes each flip protocol_ok False ----
def _mut_missing_family(r):
    del r["fixture_families"]["C_gradient_fields"]


def _mut_extra_family(r):
    r["fixture_families"]["G_extra_family"] = copy.deepcopy(r["fixture_families"]["A_uniform_opponent_patches"])


def _mut_representation_validated_true(r):
    r["fixture_families"]["A_uniform_opponent_patches"]["representation_validated"] = True


def _mut_flat_field_validated_true(r):
    r["flat_field_validated"] = True


def _mut_verdict_pass(r):
    r["verdict"] = "PASS"


def _mut_claim_lock_true(r):
    r["claim_locks"]["temporal_claim_allowed"] = True


def _mut_adoption_flag_true(r):
    r["adoption_flags"]["metric_adopted"] = True


def _mut_authorization_guard_true(r):
    r["authorization_guards"]["implementation_authorizes_validation"] = True


def _mut_forbidden_coordinate_field(r):
    r["fixture_families"]["A_uniform_opponent_patches"]["x_coordinate"] = "0"


def _mut_forbidden_metric_field(r):
    r["fixture_families"]["B_adjacent_opponent_patches"]["score"] = "high"


def _mut_forbidden_descriptor_field(r):
    r["fixture_families"]["C_gradient_fields"]["descriptor_array"] = "d"


def _mut_forbidden_vector_field(r):
    r["fixture_families"]["D_edge_discontinuity_fields"]["vector"] = [1, 2, 3]


def _mut_numeric_value_in_allowed_field(r):
    r["fixture_families"]["E_region_field_separation_fixtures"]["family_id"] = 5


def _mut_forbidden_component_label(r):
    r["fixture_families"]["F_null_control_fields"]["conceptual_components"] = ["pixel_grid"]


def _mut_forbidden_image_field(r):
    r["fixture_families"]["A_uniform_opponent_patches"]["image_data"] = "x"


def _mut_forbidden_real_clip_field(r):
    r["fixture_families"]["B_adjacent_opponent_patches"]["real_clip_data"] = "x"


def _mut_forbidden_pass_fail_field(r):
    r["fixture_families"]["C_gradient_fields"]["pass_fail"] = "pass"


def _mut_extra_top_level_field(r):
    r["threshold"] = "0"


# --- string-content holes: claiming / forbidden text inside ALLOWED string fields (canonical enforcement) ---
def _mut_boundary_note_validation_vision_claim(r):
    r["fixture_families"]["A_uniform_opponent_patches"]["boundary_notes"] = \
        "this validates geometry and proves Brainvision sees"


def _mut_boundary_note_coordinate_score_threshold_text(r):
    r["fixture_families"]["D_edge_discontinuity_fields"]["boundary_notes"] = \
        "x/y coordinate 5 score 0.7 threshold pass"


def _mut_family_label_descriptor_metric_claim(r):
    r["fixture_families"]["B_adjacent_opponent_patches"]["family_label"] = "descriptor array with metric"


def _mut_top_level_note_vision_validation_claim(r):
    r["note"] = "Brainvision sees and validates geometry"


# --- identity / content holes: drift from the canonical A-F representation ---
def _mut_wrong_family_id(r):
    r["fixture_families"]["A_uniform_opponent_patches"]["family_id"] = "Z"


def _mut_wrong_family_label(r):
    r["fixture_families"]["C_gradient_fields"]["family_label"] = "totally different label"


def _mut_allowed_but_wrong_components(r):
    r["fixture_families"]["F_null_control_fields"]["conceptual_components"] = ["patch"]


def _mut_empty_relations(r):
    r["fixture_families"]["A_uniform_opponent_patches"]["conceptual_relations"] = []


def _mut_empty_components(r):
    r["fixture_families"]["D_edge_discontinuity_fields"]["conceptual_components"] = []


def _mut_delete_components(r):
    del r["fixture_families"]["E_region_field_separation_fixtures"]["conceptual_components"]


@pytest.mark.parametrize("mut", [
    _mut_missing_family,
    _mut_extra_family,
    _mut_representation_validated_true,
    _mut_flat_field_validated_true,
    _mut_verdict_pass,
    _mut_claim_lock_true,
    _mut_adoption_flag_true,
    _mut_authorization_guard_true,
    _mut_forbidden_coordinate_field,
    _mut_forbidden_metric_field,
    _mut_forbidden_descriptor_field,
    _mut_forbidden_vector_field,
    _mut_numeric_value_in_allowed_field,
    _mut_forbidden_component_label,
    _mut_forbidden_image_field,
    _mut_forbidden_real_clip_field,
    _mut_forbidden_pass_fail_field,
    _mut_extra_top_level_field,
    _mut_boundary_note_validation_vision_claim,
    _mut_boundary_note_coordinate_score_threshold_text,
    _mut_family_label_descriptor_metric_claim,
    _mut_top_level_note_vision_validation_claim,
    _mut_wrong_family_id,
    _mut_wrong_family_label,
    _mut_allowed_but_wrong_components,
    _mut_empty_relations,
    _mut_empty_components,
    _mut_delete_components,
])
def test_mutation_probe_flips_protocol_ok_false(mut):
    r = _rep()
    mut(r)
    chk = m29.check_protocol(r)
    assert chk["protocol_ok"] is False
    assert len(chk["breaches"]) >= 1


# ---- canonical enforcement surfaces a descriptive breach (not just a generic fail) ----
def test_canonical_note_breach_named():
    r = _rep()
    r["note"] = "Brainvision sees and validates geometry"
    chk = m29.check_protocol(r)
    assert "noncanonical_note" in chk["breaches"]


def test_canonical_family_field_breach_named():
    r = _rep()
    r["fixture_families"]["A_uniform_opponent_patches"]["boundary_notes"] = "validates geometry; Brainvision sees"
    chk = m29.check_protocol(r)
    assert "noncanonical_family_field:A_uniform_opponent_patches.boundary_notes" in chk["breaches"]


# ---- determinism ----
def test_output_is_deterministic():
    assert repr(_rep()) == repr(_rep())
    assert repr(m29.check_protocol(_rep())) == repr(m29.check_protocol(_rep()))
