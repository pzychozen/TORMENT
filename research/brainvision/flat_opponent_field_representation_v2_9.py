"""BV flat opponent-field SYMBOLIC representation v2.9 (offline research; static symbolic; NOT vision).

REPRESENTATION-ONLY IMPLEMENTATION. It builds the SMALLEST possible STATIC SYMBOLIC representation of the existing
v2.6/v2.7 flat opponent-field synthetic fixture families A-F, under the accepted v2.8 boundary. It is authorized as a
strictly static/symbolic, offline, non-authorizing slice outside `torment_service/`.

Representation ONLY. It does NOT validate geometry, and it does NOT define or adopt a descriptor, a coordinate system,
numeric geometry, a metric, an equation, a threshold, a control metric, a pass/fail gate, validation, a screen /
real-clip / camera / live / sensor / streaming path, a runtime path, or a memory path. It carries NO x/y / grid /
pixel coordinates, NO vectors, NO arrays implying image/descriptor data, NO numeric distances / gradients, NO
formulas / equations / thresholds / scores / metrics, NO classifier (form B) features, NO neural (form C) encodings,
NO image / screen / real-clip data, and NO pass/fail evaluation.

Each fixture family is a STATIC SYMBOLIC OBJECT: a family id/label, a set of conceptual COMPONENT labels, a set of
conceptual RELATION labels, boundary notes, and the two boolean markers `fixture_represented = True` /
`representation_validated = False`. Representation existence does NOT imply validation: naming a structure is not
measuring, validating, or seeing it. A conservative protocol checker (`check_protocol`) reports `protocol_ok = True`
with `breaches = []` ONLY when every constraint holds. It is CANONICAL: the top-level note and each family's
`family_id`, `family_label`, `boundary_notes`, `conceptual_components`, and `conceptual_relations` must match the
builder's approved static representation EXACTLY -- so arbitrary text (e.g. a claim that geometry is validated or that
Brainvision sees, or coordinate/score/threshold/descriptor text) inside an allowed string field is rejected, and the
canonical A-F identity/content cannot drift. It also marks a breach whenever anything is missing, extra, True where it
must be False, or a forbidden numeric / coordinate / metric / descriptor / image / screen / clip / vector / array /
pass-fail field appears. If uncertain, it marks a breach.

The outcome label is CONSERVATIVE: FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY. Output is deterministic.
`flat_field_validated = False`; all claim locks False; `verdict = HOLD`. v1.x remains FROZEN EVIDENCE; v2.x remains an
UNVALIDATED conceptual pivot.

stdlib only; no torment_service; no runtime / camera / sensor / live-capture / screen-capture / streaming / prompt /
context / memory / action / render-body / autonomy contact; no real clips; no images; no pixel arrays.
"""
from __future__ import annotations

VERSION = "v2.9"
OUTCOME_LABEL = "FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY"

NOTE_TEXT = ("static symbolic representation of the existing A-F flat opponent-field fixture families; "
             "representation only, not validation; adopts no descriptor / coordinate / metric / equation / "
             "threshold / pass-fail; opens no screen / runtime / memory / vision path")

REQUIRED_FAMILIES = ("A_uniform_opponent_patches", "B_adjacent_opponent_patches", "C_gradient_fields",
                     "D_edge_discontinuity_fields", "E_region_field_separation_fixtures", "F_null_control_fields")

# Closed set of conceptual COMPONENT labels (symbolic names only; never numeric, never a descriptor):
ALLOWED_COMPONENTS = frozenset({"patch", "neighbor", "transition", "boundary", "region", "field",
                                "gradient", "discontinuity", "null_control", "opponent_polarity_label"})

# Closed set of conceptual RELATION labels (symbolic names only; never a distance, direction, or magnitude):
ALLOWED_RELATIONS = frozenset({"adjacent_to", "separates", "transitions_to", "contains", "contrasts_with",
                               "has_boundary", "has_null_control_role"})

# Exactly the keys a static symbolic family object may carry:
FAMILY_ALLOWED_KEYS = frozenset({"family_id", "family_label", "conceptual_components", "conceptual_relations",
                                 "boundary_notes", "fixture_represented", "representation_validated"})

# Family fields whose VALUES must match the canonical builder representation exactly:
CANONICAL_FAMILY_FIELDS = ("family_id", "family_label", "boundary_notes",
                           "conceptual_components", "conceptual_relations")

# Claim locks that must stay False (any True -> breach). flat_field_validated is included per the v2.9 contract.
CLAIM_LOCKS = ("first_pass_structure_validity_claim_allowed", "temporal_claim_allowed",
               "descriptor_validity_claim_allowed", "geometry_validity_claim_allowed",
               "screen_readiness_claim_allowed", "runtime_readiness_claim_allowed",
               "memory_readiness_claim_allowed", "integration_readiness_claim_allowed",
               "vision_claim_allowed", "flat_field_validated")

# Adoption flags that must stay False (any True -> breach):
ADOPTION_FLAGS = ("descriptor_adopted", "coordinate_system_adopted", "numeric_geometry_adopted", "metric_adopted",
                  "equation_adopted", "threshold_adopted", "control_metric_adopted", "pass_fail_gate_adopted",
                  "validation_adopted", "screen_path_adopted", "runtime_path_adopted", "memory_path_adopted")

# Authorization guards that must stay False (any True -> breach):
AUTHORIZATION_GUARDS = ("implementation_authorizes_validation", "implementation_authorizes_screen_analysis",
                        "implementation_authorizes_runtime_contact", "implementation_authorizes_memory_contact",
                        "implementation_authorizes_vision_claim", "implementation_authorizes_descriptor_claim",
                        "implementation_authorizes_geometry_claim")

# Top-level report keys that may appear (anything else -> breach):
REPORT_ALLOWED_KEYS = frozenset({"version", "note", "representation_only", "offline_research_only",
                                 "symbolic_static_only", "flat_field_validated", "verdict", "outcome_label",
                                 "fixture_families", "claim_locks", "adoption_flags", "authorization_guards"})

# Forbidden substrings in any family field key (conservative; belt-and-suspenders with the allow-list):
FORBIDDEN_KEY_TOKENS = ("coord", "pixel", "grid", "vector", "arr", "distance", "formula", "equation", "threshold",
                        "score", "metric", "classifier", "descriptor", "image", "screen", "clip", "pass_fail",
                        "passfail", "numeric", "geometry")

REQUIRED_FAMILY_KEYS = ("family_id", "family_label", "conceptual_components", "conceptual_relations",
                        "boundary_notes", "fixture_represented", "representation_validated")


def _build_families():
    """Static symbolic objects for the six existing fixture families. Symbolic labels only; no numbers, no
    coordinates, no descriptor/metric/threshold/pass-fail content. This IS the canonical representation."""
    return {
        "A_uniform_opponent_patches": {
            "family_id": "A", "family_label": "uniform opponent patches",
            "conceptual_components": ["patch", "region", "opponent_polarity_label"],
            "conceptual_relations": ["contains"],
            "boundary_notes": ("a single uniform opponent patch named as one region and its opponent polarity label; "
                               "no neighbors, no distance, no measurement"),
            "fixture_represented": True, "representation_validated": False},
        "B_adjacent_opponent_patches": {
            "family_id": "B", "family_label": "adjacent opponent patches",
            "conceptual_components": ["patch", "neighbor", "region", "opponent_polarity_label"],
            "conceptual_relations": ["adjacent_to", "contrasts_with"],
            "boundary_notes": ("two or more opponent patches named as neighbors; adjacency is a NAME, not a distance "
                               "or an adjacency equation"),
            "fixture_represented": True, "representation_validated": False},
        "C_gradient_fields": {
            "family_id": "C", "family_label": "gradient fields",
            "conceptual_components": ["field", "gradient", "transition", "region"],
            "conceptual_relations": ["transitions_to", "contains"],
            "boundary_notes": ("a smooth opponent transition field; gradient / transition are NAMES, not slopes, "
                               "rates, or numeric gradients"),
            "fixture_represented": True, "representation_validated": False},
        "D_edge_discontinuity_fields": {
            "family_id": "D", "family_label": "edge / discontinuity fields",
            "conceptual_components": ["field", "boundary", "discontinuity", "region"],
            "conceptual_relations": ["has_boundary", "separates", "contrasts_with"],
            "boundary_notes": ("a sharp opponent boundary named as a discontinuity; no edge detector, no gradient "
                               "magnitude, no threshold"),
            "fixture_represented": True, "representation_validated": False},
        "E_region_field_separation_fixtures": {
            "family_id": "E", "family_label": "region-field separation fixtures",
            "conceptual_components": ["region", "field"],
            "conceptual_relations": ["separates", "contains"],
            "boundary_notes": ("a local region vs a global field named via a separation relation; no measure of "
                               "separation, no field descriptor"),
            "fixture_represented": True, "representation_validated": False},
        "F_null_control_fields": {
            "family_id": "F", "family_label": "null / control fields",
            "conceptual_components": ["null_control", "field"],
            "conceptual_relations": ["has_null_control_role"],
            "boundary_notes": ("a neutral / matched non-opponent control named by role only; NOT a pass/fail control, "
                               "no metric, no threshold"),
            "fixture_represented": True, "representation_validated": False},
    }


def build_flat_opponent_field_representation_v2_9():
    """Deterministic static symbolic representation report for the A-F fixture families. Representation only."""
    return {
        "version": VERSION,
        "note": NOTE_TEXT,
        "representation_only": True,
        "offline_research_only": True,
        "symbolic_static_only": True,
        "flat_field_validated": False,
        "verdict": "HOLD",
        "outcome_label": OUTCOME_LABEL,
        "fixture_families": _build_families(),
        "claim_locks": {k: False for k in CLAIM_LOCKS},
        "adoption_flags": {k: False for k in ADOPTION_FLAGS},
        "authorization_guards": {k: False for k in AUTHORIZATION_GUARDS},
    }


def _scan_value(fname, key, v):
    """Conservative value scan: no numbers, no vectors/arrays, no nested structures. Booleans are allowed."""
    b = []
    if isinstance(v, bool):
        return b
    if isinstance(v, (int, float)):
        b.append("forbidden_numeric:%s.%s" % (fname, key))
    elif isinstance(v, str):
        return b
    elif isinstance(v, (list, tuple)):
        for el in v:
            if isinstance(el, bool):
                b.append("forbidden_nonstring_in_list:%s.%s" % (fname, key))
            elif isinstance(el, (int, float)):
                b.append("forbidden_vector_or_array:%s.%s" % (fname, key))
            elif isinstance(el, str):
                continue
            else:
                b.append("forbidden_nested_in_list:%s.%s" % (fname, key))
    elif isinstance(v, dict):
        b.append("forbidden_nested_structure:%s.%s" % (fname, key))
    elif v is None:
        b.append("forbidden_none_value:%s.%s" % (fname, key))
    else:
        b.append("forbidden_value_type:%s.%s" % (fname, key))
    return b


def _check_family(fname, fobj, canon):
    b = []
    if not isinstance(fobj, dict):
        return ["family_not_dict:%s" % fname]
    # key allow-list + forbidden-token scan
    for k in fobj:
        if k not in FAMILY_ALLOWED_KEYS:
            b.append("forbidden_family_field:%s.%s" % (fname, k))
        low = str(k).lower()
        for tok in FORBIDDEN_KEY_TOKENS:
            if tok in low:
                b.append("forbidden_token_field:%s.%s" % (fname, k))
                break
    # required keys present
    for k in REQUIRED_FAMILY_KEYS:
        if k not in fobj:
            b.append("family_missing_key:%s.%s" % (fname, k))
    # boolean markers
    if fobj.get("fixture_represented") is not True:
        b.append("fixture_not_represented:%s" % fname)
    if fobj.get("representation_validated") is not False:
        b.append("representation_validated_true:%s" % fname)
    # symbolic components / relations well-formedness
    comps = fobj.get("conceptual_components")
    rels = fobj.get("conceptual_relations")
    if not (isinstance(comps, list) and len(comps) > 0):
        b.append("missing_symbolic_representation:%s" % fname)
    if isinstance(comps, list):
        for c in comps:
            if not (isinstance(c, str) and c in ALLOWED_COMPONENTS):
                b.append("forbidden_component:%s.%s" % (fname, str(c)))
    if rels is None or not isinstance(rels, list):
        b.append("relations_not_list:%s" % fname)
    else:
        for r in rels:
            if not (isinstance(r, str) and r in ALLOWED_RELATIONS):
                b.append("forbidden_relation:%s.%s" % (fname, str(r)))
    # CANONICAL enforcement: known string / label / component / relation fields must match the approved builder
    # representation EXACTLY (rejects claiming text, coordinate/score/threshold/descriptor text, and identity drift).
    if isinstance(canon, dict):
        for key in CANONICAL_FAMILY_FIELDS:
            if fobj.get(key) != canon.get(key):
                b.append("noncanonical_family_field:%s.%s" % (fname, key))
    # deep value scan
    for k, v in fobj.items():
        b += _scan_value(fname, k, v)
    return b


def check_protocol(report=None):
    """Conservative CANONICAL protocol checker. Returns {'protocol_ok': bool, 'breaches': [...]}. protocol_ok is True
    with an empty breaches list ONLY when every constraint holds AND the note + per-family canonical fields match the
    builder's approved static representation exactly. If uncertain, it marks a breach."""
    if report is None:
        report = build_flat_opponent_field_representation_v2_9()
    breaches = []
    if not isinstance(report, dict):
        return {"protocol_ok": False, "breaches": ["report_not_dict"]}

    canon_families = _build_families()

    # top-level allow-list
    for k in report:
        if k not in REPORT_ALLOWED_KEYS:
            breaches.append("forbidden_report_field:%s" % k)

    # scalar invariants
    if report.get("version") != VERSION:
        breaches.append("bad_version")
    for k in ("representation_only", "offline_research_only", "symbolic_static_only"):
        if report.get(k) is not True:
            breaches.append("missing_true_flag:%s" % k)
    if report.get("outcome_label") != OUTCOME_LABEL:
        breaches.append("bad_outcome_label")
    if report.get("flat_field_validated") is not False:
        breaches.append("flat_field_validated_true")
    if report.get("verdict") != "HOLD":
        breaches.append("verdict_not_hold")
    # canonical top-level note (rejects vision / validation / any non-approved note text)
    if report.get("note") != NOTE_TEXT:
        breaches.append("noncanonical_note")

    # claim locks / adoption flags / authorization guards: all present and False
    for label, keys in (("claim_lock", CLAIM_LOCKS), ("adoption_flag", ADOPTION_FLAGS),
                        ("authorization_guard", AUTHORIZATION_GUARDS)):
        d = report.get({"claim_lock": "claim_locks", "adoption_flag": "adoption_flags",
                        "authorization_guard": "authorization_guards"}[label])
        if not isinstance(d, dict):
            breaches.append("%s_group_missing" % label)
            continue
        for k in keys:
            if k not in d:
                breaches.append("%s_missing:%s" % (label, k))
            elif d[k] is not False:
                breaches.append("%s_true:%s" % (label, k))
        for k, v in d.items():
            if v is not False:
                breaches.append("%s_true:%s" % (label, k))

    # fixture families
    fam = report.get("fixture_families")
    if not isinstance(fam, dict):
        breaches.append("fixture_families_missing")
    else:
        present = set(fam.keys())
        for f in REQUIRED_FAMILIES:
            if f not in present:
                breaches.append("missing_family:%s" % f)
        for f in present:
            if f not in REQUIRED_FAMILIES:
                breaches.append("extra_family:%s" % f)
        for fname, fobj in fam.items():
            breaches += _check_family(fname, fobj, canon_families.get(fname))

    # de-duplicate while preserving order (a single fault may trip multiple guards)
    seen, ordered = set(), []
    for x in breaches:
        if x not in seen:
            seen.add(x)
            ordered.append(x)
    return {"protocol_ok": len(ordered) == 0, "breaches": ordered}


if __name__ == "__main__":
    rep = build_flat_opponent_field_representation_v2_9()
    chk = check_protocol(rep)
    print("version", rep["version"], "| representation_only", rep["representation_only"],
          "| symbolic_static_only", rep["symbolic_static_only"], "| offline_research_only",
          rep["offline_research_only"])
    print("outcome_label:", rep["outcome_label"])
    print("flat_field_validated:", rep["flat_field_validated"], "| verdict:", rep["verdict"])
    print("protocol_ok:", chk["protocol_ok"], "| breaches:", chk["breaches"])
    print("families:", list(rep["fixture_families"].keys()))
    print("claim_locks all False:", all(v is False for v in rep["claim_locks"].values()))
    print("adoption_flags all False:", all(v is False for v in rep["adoption_flags"].values()))
    print("authorization_guards all False:", all(v is False for v in rep["authorization_guards"].values()))
    print("\nFIXTURE FAMILIES A-F (static symbolic objects):")
    for k in REQUIRED_FAMILIES:
        fx = rep["fixture_families"][k]
        print("  %-34s id=%s label=%-30s components=%s" %
              (k, fx["family_id"], fx["family_label"], fx["conceptual_components"]))
