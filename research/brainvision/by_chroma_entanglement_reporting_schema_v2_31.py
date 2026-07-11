"""BV BY/chroma ENTANGLEMENT-AWARE REPORTING SCHEMA v2.31 (offline research; static symbolic; NOT vision).

SCHEMA-GENERATION-ONLY IMPLEMENTATION, under the conditional v2.30 implementation boundary (Option A: related_role_ids
DROPPED). It builds a DETERMINISTIC STATIC SYMBOLIC schema for BY/chroma entanglement-aware reporting: the six v2.28 /
v2.29 reporting-outcome STANCES, written down under a conservative guard.

WHAT THIS ARTIFACT DOES NOT DO -- and structurally CANNOT do:
  - it takes NO INPUT (the builder accepts no argument; there is nothing to feed it);
  - it EVALUATES no evidence, ASSIGNS no outcome to anything, CHOOSES among no outcomes, and provides no arrival rule,
    decision rule, routing, ranking, ordering, matching, or selection of any kind;
  - it MAPS no v2.24 role to any outcome (there is no related_role_ids field and no role-to-outcome relation anywhere:
    a field that can only be made safe by rules about how to read it is not safe, so it is absent, per v2.30 Option A);
  - it CLASSIFIES nothing (the outcome ids are REPORTING STANCES, never labels applied to anything);
  - it VALIDATES nothing (schema_validated = False; outcome_validated = False everywhere);
  - it adopts NO descriptor, coordinate system, numeric geometry, metric, score, threshold, formula, equation,
    comparison, pass/fail gate, acceptance criterion, or expected output;
  - it opens NO screen / real-clip / camera / live / sensor / streaming path, NO runtime path, NO memory path, NO
    classifier (form B) path, and NO neural (form C) path; it makes NO vision claim.

The six outcome ids -- BY_LEANING_UNRESOLVED, GENERIC_CHROMA_LEANING_UNRESOLVED, MATCHED_NON_BY_UNRESOLVED,
ENTANGLED_INSEPARABLE, FIXTURE_ARTIFACT_SUSPECTED, NULL_REPORTING_BOUNDARY -- are REPORTING STANCES ONLY. They are not
classifier labels, not measured classes, not fixture classes, not validation groups, not pass/fail results, and not
visual categories. They are conceptual, NON-EXHAUSTIVE and NON-PARTITIONING: they are not a taxonomy of how the world
can be, and nothing is ever sorted into them.

ENTANGLED_INSEPARABLE is a FIRST-CLASS, TERMINAL, NON-DEFICIENT unresolved endpoint. It is NOT failure, NOT success,
NOT noise, NOT an implementation defect, NOT an else-branch, NOT hidden BY evidence, NOT a confound that was resolved,
NOT validation, and NOT closure. If the honest answer is that BY residual pressure and generic chroma proxy pressure
cannot be told apart, this schema exists so the project can SAY SO AND STOP.

A conservative CANONICAL protocol checker (`check_protocol`) reports `protocol_ok = True` with `breaches = []` ONLY for
the clean canonical report. Greenness means BOUNDARY COMPLIANCE ONLY (v2.14) -- never schema validity, correctness,
distinguishability, or readiness. `schema_validated` stays False even when every check is green.

ONE DESIGN NOTE, stated plainly: the `forbidden_language` field is the single place where the banned claim phrases
legitimately appear -- as CITATIONS of what may never be said. It is therefore guarded by EXACT-SET membership against
the canonical list, not by the assertion scan that guards every other string field (which would otherwise reject the
artifact for naming the very claims it forbids). Citing a claim is not making it; the exact-set gate is what keeps that
distinction honest.

Deterministic. stdlib only; no torment_service; no runtime / camera / sensor / live-capture / screen-capture /
streaming / prompt / context / memory / action / render-body / autonomy contact; no real clips; no images; no arrays.
"""
from __future__ import annotations

VERSION = "v2.31"
OUTCOME_LABEL = "BRAINVISION_BY_CHROMA_ENTANGLEMENT_REPORTING_SCHEMA_ONLY"

# ---- the six reporting-outcome stances, in canonical order. Exactly these; no more, no fewer. ----
REQUIRED_OUTCOMES = ("BY_LEANING_UNRESOLVED",
                     "GENERIC_CHROMA_LEANING_UNRESOLVED",
                     "MATCHED_NON_BY_UNRESOLVED",
                     "ENTANGLED_INSEPARABLE",
                     "FIXTURE_ARTIFACT_SUSPECTED",
                     "NULL_REPORTING_BOUNDARY")

# ---- top-level keys the report may carry (anything else -> breach) ----
REPORT_ALLOWED_KEYS = ("version", "reporting_only", "offline_research_only", "symbolic_schema_only",
                       "schema_generated", "schema_validated", "outcome_label", "allowed_outcomes",
                       "claim_locks", "adoption_flags", "authorization_guards", "protocol", "verdict")

# ---- keys an outcome stance may carry (anything else -> breach) ----
OUTCOME_ALLOWED_KEYS = ("outcome_id", "outcome_label", "reporting_stance", "entanglement_status", "non_claim_status",
                        "allowed_language", "forbidden_language", "outcome_generated", "outcome_validated")

# outcome fields whose VALUES must match the canonical builder report exactly:
CANONICAL_OUTCOME_FIELDS = ("outcome_id", "outcome_label", "reporting_stance", "entanglement_status",
                            "non_claim_status", "allowed_language", "forbidden_language")

PROTOCOL_ALLOWED_KEYS = ("protocol_note", "greenness_means", "outcome_set_is_exhaustive",
                         "outcome_set_is_partitioning", "unresolved_is_part_of_the_outcome_name",
                         "entangled_endpoint_is_first_class")

CLAIM_LOCKS = ("flat_field_validated", "role_validated", "schema_validated", "entanglement_resolved",
               "by_residual_isolated", "generic_chroma_proxy_ruled_out",
               "first_pass_structure_validity_claim_allowed", "temporal_claim_allowed",
               "descriptor_validity_claim_allowed", "geometry_validity_claim_allowed",
               "screen_readiness_claim_allowed", "runtime_readiness_claim_allowed",
               "memory_readiness_claim_allowed", "integration_readiness_claim_allowed", "vision_claim_allowed")

ADOPTION_FLAGS = ("descriptor_adopted", "coordinate_system_adopted", "metric_adopted", "threshold_adopted",
                  "scoring_adopted", "formula_adopted", "pass_fail_gate_adopted", "validation_adopted",
                  "classifier_adopted", "neural_path_adopted")

AUTHORIZATION_GUARDS = ("screen_path_authorized", "runtime_path_authorized", "memory_path_authorized",
                        "integration_path_authorized", "real_clip_path_authorized", "vision_claim_authorized")

# ---- forbidden field-name tokens. Scanned ONLY on keys that are NOT in an allow-list, so the canonical keys
# (schema_validated, outcome_validated, ...) can never collide with the guard. ----
FORBIDDEN_FIELD_TOKENS = ("related_role", "role_to_outcome", "role_id", "mapping", "map_", "input", "evidence",
                          "decision", "arrival", "assign", "classif", "confidence", "score", "metric", "threshold",
                          "formula", "pass_fail", "passfail", "validation_result", "descriptor", "coordinate",
                          "fixture_instance", "screen", "runtime", "memory", "vision", "neural", "clip", "pixel",
                          "array", "image", "weight", "ratio", "distance", "geometry", "numeric")

# ---- forbidden claim wording. Scanned on every canonical string EXCEPT forbidden_language (see module docstring).
# These are claim SHAPES and bare surface tokens the canonical text must never contain. A test asserts the clean
# report is free of every one of them. ----
FORBIDDEN_WORDING = (
    # the twelve required forbidden claims, plus their nearest paraphrases
    "by residual isolated", "residual isolated", "generic chroma proxy ruled out", "proxy ruled out",
    "proxy is controlled", "proxy resolved", "confound resolved", "entanglement resolved", "descriptor validated",
    "geometry validated", "visual structure detected", "structure detected", "fixture passed", "screen ready",
    "runtime ready", "memory ready", "vision achieved", "brainvision sees",
    # other claim shapes
    "not an artifact", "null passed", "control passed", "baseline passed", "residual is distinct",
    "residual is separable", "is validated", "are validated", "validation passed", "closure achieved", "is closed",
    "is ready", "we can now", "we now know", "proves", "proven", "is confirmed", "is verified", "evidence that",
    # surface tokens that must never appear in a reporting stance
    "metric", "score", "threshold", "formula", "classifier", "classification", "descriptor", "coordinate", "pixel",
    "screen", "runtime", "memory", "vision", "neural", "real clip", "confidence", "arrival rule", "decision rule",
)

PROTOCOL_NOTE = ("static symbolic schema of the six reporting-outcome stances; it takes nothing, reaches nothing, "
                 "chooses nothing, attaches nothing to anything, and asserts nothing about colour; naming a stance is "
                 "not measuring, separating, validating, or seeing")

GREENNESS_MEANS = ("boundary compliance only; never schema validity, never correctness, never distinguishability, "
                   "never readiness")

# The canonical citations of what a future report may NEVER say. Cited here, never asserted.
FORBIDDEN_LANGUAGE = (
    "BY residual isolated",
    "generic chroma proxy ruled out",
    "entanglement resolved",
    "descriptor validated",
    "geometry validated",
    "visual structure detected",
    "fixture passed",
    "screen ready",
    "runtime ready",
    "memory ready",
    "vision achieved",
    "Brainvision sees",
)


def _forbidden_language():
    return list(FORBIDDEN_LANGUAGE)


def _build_outcomes():
    """Static symbolic objects for the six reporting-outcome stances. Names and canonical reporting prose only; no
    data, no numbers, no roles, no assignment, no arrival. This IS the canonical schema."""
    return {
        "BY_LEANING_UNRESOLVED": {
            "outcome_id": "BY_LEANING_UNRESOLVED",
            "outcome_label": "BY-leaning unresolved",
            "reporting_stance": ("names a BY-leaning reading as one that could not be excluded, and does not assert "
                                 "it; leaning is a STANCE, not a degree, not a weight, not a strength, and not a "
                                 "direction of any measured quantity"),
            "entanglement_status": "entanglement not excluded",
            "non_claim_status": ("claims nothing about BY-axis behaviour, nothing about representation validity, "
                                 "nothing about geometry, and nothing about seeing; UNRESOLVED is part of the name "
                                 "and may never be dropped"),
            "allowed_language": ["reported as BY-leaning unresolved"],
            "forbidden_language": _forbidden_language(),
            "outcome_generated": True,
            "outcome_validated": False,
        },
        "GENERIC_CHROMA_LEANING_UNRESOLVED": {
            "outcome_id": "GENERIC_CHROMA_LEANING_UNRESOLVED",
            "outcome_label": "generic-chroma-leaning unresolved",
            "reporting_stance": ("names a generic-chroma-proxy reading as one that could not be excluded, and does "
                                 "not assert it; it does not weaken the standing presumption that an apparent "
                                 "residual IS a generic chroma proxy effect until a reporting-only distinction shows "
                                 "otherwise, and no such showing exists"),
            "entanglement_status": "entanglement not excluded",
            "non_claim_status": ("claims nothing about the confound being controlled, ruled out, or measured; "
                                 "UNRESOLVED is part of the name and may never be dropped"),
            "allowed_language": ["reported as generic-chroma-leaning unresolved"],
            "forbidden_language": _forbidden_language(),
            "outcome_generated": True,
            "outcome_validated": False,
        },
        "MATCHED_NON_BY_UNRESOLVED": {
            "outcome_id": "MATCHED_NON_BY_UNRESOLVED",
            "outcome_label": "matched-non-BY unresolved",
            "reporting_stance": ("names a non-BY chroma reading as one that could not be excluded, so that BY does "
                                 "not silently become a synonym for any colour effect; matched is CONCEPTUAL, never a "
                                 "match computed over any quantity"),
            "entanglement_status": "entanglement not excluded",
            "non_claim_status": ("claims no colour space, no channel, and no axis system; UNRESOLVED is part of the "
                                 "name and may never be dropped"),
            "allowed_language": ["reported as matched-non-BY unresolved"],
            "forbidden_language": _forbidden_language(),
            "outcome_generated": True,
            "outcome_validated": False,
        },
        "ENTANGLED_INSEPARABLE": {
            "outcome_id": "ENTANGLED_INSEPARABLE",
            "outcome_label": "entangled / inseparable",
            "reporting_stance": ("states that BY residual pressure and generic chroma proxy pressure could not be "
                                 "told apart here, and stops; a COMPLETE, TERMINAL, NON-DEFICIENT endpoint, reachable "
                                 "on its own terms and never only by elimination"),
            "entanglement_status": "entanglement is the reported outcome",
            "non_claim_status": ("NOT failure, NOT success, NOT noise, NOT an implementation defect, NOT an "
                                 "else-branch, NOT hidden BY evidence, NOT a confound that was resolved, NOT "
                                 "validation, and NOT closure; it asserts nothing about colour and supports nothing"),
            "allowed_language": ["reported as entangled / inseparable"],
            "forbidden_language": _forbidden_language(),
            "outcome_generated": True,
            "outcome_validated": False,
        },
        "FIXTURE_ARTIFACT_SUSPECTED": {
            "outcome_id": "FIXTURE_ARTIFACT_SUSPECTED",
            "outcome_label": "fixture-artifact suspected",
            "reporting_stance": ("states that any apparent distinction may have been PRODUCED BY the way the cases "
                                 "were constructed; it suspects, and it never concludes the absence of an artifact"),
            "entanglement_status": "entanglement not addressed",
            "non_claim_status": ("claims no artifact was measured, none was controlled for, and none was shown "
                                 "absent; the case family may never be declared free of artifacts"),
            "allowed_language": ["reported as fixture-artifact suspected"],
            "forbidden_language": _forbidden_language(),
            "outcome_generated": True,
            "outcome_validated": False,
        },
        "NULL_REPORTING_BOUNDARY": {
            "outcome_id": "NULL_REPORTING_BOUNDARY",
            "outcome_label": "null / reporting-boundary",
            "reporting_stance": ("marks where reporting stops and validation would impermissibly begin; an ANTI-CLAIM "
                                 "SCAFFOLD (v2.12 N1-N6), never a baseline and never a control that succeeded"),
            "entanglement_status": "entanglement not addressed",
            "non_claim_status": ("never evidence, never a baseline, never a negative control that succeeded, and "
                                 "never falsification success"),
            "allowed_language": ["reported as null / reporting-boundary"],
            "forbidden_language": _forbidden_language(),
            "outcome_generated": True,
            "outcome_validated": False,
        },
    }


def _build_protocol():
    return {
        "protocol_note": PROTOCOL_NOTE,
        "greenness_means": GREENNESS_MEANS,
        "outcome_set_is_exhaustive": False,
        "outcome_set_is_partitioning": False,
        "unresolved_is_part_of_the_outcome_name": True,
        "entangled_endpoint_is_first_class": True,
    }


def build_by_chroma_entanglement_reporting_schema_v2_31():
    """Deterministic static symbolic schema report. Takes NO input by construction: there is nothing to feed it, so
    there is nothing it could evaluate, assign, choose, map, or classify. It writes down six ways of saying
    'we do not know', and nothing else."""
    return {
        "version": VERSION,
        "reporting_only": True,
        "offline_research_only": True,
        "symbolic_schema_only": True,
        "schema_generated": True,
        "schema_validated": False,
        "outcome_label": OUTCOME_LABEL,
        "allowed_outcomes": _build_outcomes(),
        "claim_locks": {k: False for k in CLAIM_LOCKS},
        "adoption_flags": {k: False for k in ADOPTION_FLAGS},
        "authorization_guards": {k: False for k in AUTHORIZATION_GUARDS},
        "protocol": _build_protocol(),
        "verdict": "HOLD",
    }


# ------------------------------------------------------------------------------------------------------------------
# conservative canonical protocol checker
# ------------------------------------------------------------------------------------------------------------------
def _scan_wording(where, text):
    """Assertion / surface-token scan over one string. Any forbidden claim shape or surface token -> breach."""
    low = str(text).lower()
    return ["forbidden_wording:%s:%s" % (where, p) for p in FORBIDDEN_WORDING if p in low]


def _scan_key_tokens(where, key):
    low = str(key).lower()
    for tok in FORBIDDEN_FIELD_TOKENS:
        if tok in low:
            return ["forbidden_field_token:%s:%s" % (where, tok)]
    return []


def _scan_value_shape(where, v):
    """No numbers, no nested containers, no None. Booleans, strings, and lists of strings only."""
    if isinstance(v, bool):
        return []
    if isinstance(v, (int, float)):
        return ["forbidden_numeric:%s" % where]
    if isinstance(v, str):
        return []
    if isinstance(v, (list, tuple)):
        out = []
        for el in v:
            if isinstance(el, bool) or isinstance(el, (int, float)):
                out.append("forbidden_numeric_in_list:%s" % where)
            elif not isinstance(el, str):
                out.append("forbidden_nested_in_list:%s" % where)
        return out
    if isinstance(v, dict):
        return ["forbidden_nested_structure:%s" % where]
    if v is None:
        return ["forbidden_none_value:%s" % where]
    return ["forbidden_value_type:%s" % where]


def _check_group(label, group_key, keys, report):
    """Closed-set group check: every canonical key present and False; NO extra key, even one set False (an extra False
    key silently widens the guarded surface -- v2.26 Codex MODIFY)."""
    b = []
    d = report.get(group_key)
    if not isinstance(d, dict):
        return ["%s_group_missing" % label]
    for k in keys:
        if k not in d:
            b.append("%s_missing:%s" % (label, k))
        elif d[k] is not False:
            b.append("%s_true:%s" % (label, k))
    for k, v in d.items():
        if k not in keys:
            b.append("%s_extra:%s" % (label, k))
            b += _scan_key_tokens("%s.%s" % (group_key, k), k)
        if v is not False:
            b.append("%s_true:%s" % (label, k))
    return b


def _check_outcome(oid, obj, canon):
    b = []
    if not isinstance(obj, dict):
        return ["outcome_not_dict:%s" % oid]

    for k in obj:
        if k not in OUTCOME_ALLOWED_KEYS:
            b.append("forbidden_outcome_field:%s.%s" % (oid, k))
            b += _scan_key_tokens("%s.%s" % (oid, k), k)
    for k in OUTCOME_ALLOWED_KEYS:
        if k not in obj:
            b.append("outcome_missing_key:%s.%s" % (oid, k))

    if obj.get("outcome_generated") is not True:
        b.append("outcome_not_generated:%s" % oid)
    if obj.get("outcome_validated") is not False:
        b.append("outcome_validated_true:%s" % oid)

    # the stance id must be the key it is filed under (no renamed / wrong outcome id)
    if obj.get("outcome_id") != oid:
        b.append("outcome_id_mismatch:%s" % oid)

    # canonical enforcement: every canonical field must match the approved builder schema EXACTLY
    if isinstance(canon, dict):
        for k in CANONICAL_OUTCOME_FIELDS:
            if obj.get(k) != canon.get(k):
                b.append("noncanonical_outcome_field:%s.%s" % (oid, k))

    # value shapes
    for k, v in obj.items():
        b += _scan_value_shape("%s.%s" % (oid, k), v)

    # assertion / surface-token wording scan on every string field EXCEPT forbidden_language, which legitimately
    # CITES the banned claims and is instead guarded by exact-set membership below.
    for k in ("outcome_label", "reporting_stance", "entanglement_status", "non_claim_status"):
        v = obj.get(k)
        if isinstance(v, str):
            b += _scan_wording("%s.%s" % (oid, k), v)
    al = obj.get("allowed_language")
    if isinstance(al, list):
        for el in al:
            if isinstance(el, str):
                b += _scan_wording("%s.allowed_language" % oid, el)

    # forbidden_language: exact-set membership. Citing a banned claim is allowed HERE and nowhere else; any entry that
    # is not a canonical citation, and any missing citation, is a breach.
    fl = obj.get("forbidden_language")
    if not isinstance(fl, list):
        b.append("forbidden_language_not_list:%s" % oid)
    else:
        for el in fl:
            if not isinstance(el, str) or el not in FORBIDDEN_LANGUAGE:
                b.append("forbidden_wording:%s.forbidden_language:%s" % (oid, str(el)))
        for req in FORBIDDEN_LANGUAGE:
            if req not in fl:
                b.append("forbidden_language_missing:%s.%s" % (oid, req))
    return b


def _check_protocol_block(report):
    b = []
    p = report.get("protocol")
    if not isinstance(p, dict):
        return ["protocol_block_missing"]
    canon = _build_protocol()
    for k in p:
        if k not in PROTOCOL_ALLOWED_KEYS:
            b.append("forbidden_protocol_field:%s" % k)
            b += _scan_key_tokens("protocol.%s" % k, k)
    for k in PROTOCOL_ALLOWED_KEYS:
        if k not in p:
            b.append("protocol_missing_key:%s" % k)
        elif p.get(k) != canon.get(k):
            b.append("noncanonical_protocol_field:%s" % k)
    for k, v in p.items():
        b += _scan_value_shape("protocol.%s" % k, v)
        if isinstance(v, str):
            b += _scan_wording("protocol.%s" % k, v)
    return b


def check_protocol(report=None):
    """Conservative CANONICAL protocol checker. Returns {'protocol_ok': bool, 'breaches': [...]}. protocol_ok is True
    with an empty breaches list ONLY for the clean canonical report. If uncertain, it marks a breach.

    Greenness means BOUNDARY COMPLIANCE ONLY (v2.14). It is NOT schema validity, NOT correctness, NOT
    distinguishability, NOT descriptor validity, NOT closure, and NOT readiness. schema_validated stays False."""
    if report is None:
        report = build_by_chroma_entanglement_reporting_schema_v2_31()
    if not isinstance(report, dict):
        return {"protocol_ok": False, "breaches": ["report_not_dict"]}

    breaches = []

    # top-level keys: closed allow-list, both directions
    for k in report:
        if k not in REPORT_ALLOWED_KEYS:
            breaches.append("forbidden_top_level_field:%s" % k)
            breaches += _scan_key_tokens("top.%s" % k, k)
    for k in REPORT_ALLOWED_KEYS:
        if k not in report:
            breaches.append("missing_top_level_key:%s" % k)

    # scalar invariants
    if report.get("version") != VERSION:
        breaches.append("bad_version")
    for k in ("reporting_only", "offline_research_only", "symbolic_schema_only", "schema_generated"):
        if report.get(k) is not True:
            breaches.append("flag_not_true:%s" % k)
    if report.get("schema_validated") is not False:
        breaches.append("schema_validated_true")
    if report.get("outcome_label") != OUTCOME_LABEL:
        breaches.append("bad_outcome_label")
    if report.get("verdict") != "HOLD":
        breaches.append("verdict_not_hold")

    # closed groups: missing / extra (even False) / True are all breaches
    breaches += _check_group("claim_lock", "claim_locks", CLAIM_LOCKS, report)
    breaches += _check_group("adoption_flag", "adoption_flags", ADOPTION_FLAGS, report)
    breaches += _check_group("authorization_guard", "authorization_guards", AUTHORIZATION_GUARDS, report)

    # protocol block
    breaches += _check_protocol_block(report)

    # the six stances
    outcomes = report.get("allowed_outcomes")
    if not isinstance(outcomes, dict):
        breaches.append("allowed_outcomes_missing")
    else:
        canon = _build_outcomes()
        for oid in REQUIRED_OUTCOMES:
            if oid not in outcomes:
                breaches.append("missing_outcome:%s" % oid)
        for oid in outcomes:
            if oid not in REQUIRED_OUTCOMES:
                breaches.append("extra_outcome:%s" % oid)
        for oid, obj in outcomes.items():
            breaches += _check_outcome(oid, obj, canon.get(oid))

    seen, ordered = set(), []
    for x in breaches:
        if x not in seen:
            seen.add(x)
            ordered.append(x)
    return {"protocol_ok": len(ordered) == 0, "breaches": ordered}


if __name__ == "__main__":
    rep = build_by_chroma_entanglement_reporting_schema_v2_31()
    chk = check_protocol(rep)
    print("version", rep["version"], "| reporting_only", rep["reporting_only"],
          "| offline_research_only", rep["offline_research_only"],
          "| symbolic_schema_only", rep["symbolic_schema_only"])
    print("outcome_label:", rep["outcome_label"])
    print("schema_generated:", rep["schema_generated"], "| schema_validated:", rep["schema_validated"],
          "| verdict:", rep["verdict"])
    print("protocol_ok:", chk["protocol_ok"], "| breaches:", chk["breaches"])
    print("claim_locks all False:", all(v is False for v in rep["claim_locks"].values()))
    print("adoption_flags all False:", all(v is False for v in rep["adoption_flags"].values()))
    print("authorization_guards all False:", all(v is False for v in rep["authorization_guards"].values()))
    print("related_role_ids present:", any("related_role" in k for k in rep) or
          any("related_role" in k for o in rep["allowed_outcomes"].values() for k in o))
    print("\nREPORTING-OUTCOME STANCES (generated, NOT validated; assigned to nothing):")
    for oid in REQUIRED_OUTCOMES:
        o = rep["allowed_outcomes"][oid]
        print("  %-34s label=%-34s entanglement_status=%s" %
              (oid, o["outcome_label"], o["entanglement_status"]))
    print("\nthe schema takes no input, reaches no outcome, and assigns nothing to anything;")
    print("ENTANGLED_INSEPARABLE is a first-class terminal endpoint; the v2.22 question remains UNRESOLVED.")
