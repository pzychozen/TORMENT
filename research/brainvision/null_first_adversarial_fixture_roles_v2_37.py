"""BV NULL-FIRST ADVERSARIAL FAMILY ROLES v2.37 (offline research; static symbolic; reporting-only; NOT vision).

ROLE-GENERATION-ONLY IMPLEMENTATION, under the conditional v2.36 implementation boundary. It builds a DETERMINISTIC
STATIC SYMBOLIC report of the six v2.35 null-first adversarial family ROLES: A null / no-structure, B fixture-artifact,
C proxy-confound, D entangled / unresolved, E control-collapse, F candidate-structure-survival.

IT WRITES DOWN SIX ADVERSARIAL NOUNS. That is the whole artifact.

WHAT THIS ARTIFACT DOES NOT DO -- and structurally CANNOT do:
  - it takes NO INPUT (the builder accepts no argument; there is nothing to feed it);
  - it GENERATES no fixture, no fixture instance, and no fixture data; it defines no generation rule, no schema, and no
    data shape;
  - it EVALUATES no evidence, ASSIGNS no outcome, CHOOSES among no outcomes, and carries no arrival rule, decision
    rule, routing, ranking, ordering, matching, or selection of any kind;
  - it CLASSIFIES nothing, VALIDATES nothing, DETECTS nothing, and RULES NOTHING OUT;
  - it adopts NO descriptor, coordinate system, metric, score, threshold, formula, pass/fail gate, or validation
    criterion; it opens NO screen / real-clip / camera / live / sensor / streaming path, NO runtime path, NO memory
    path, NO classifier (form B) path, and NO neural (form C) path; it makes NO vision or readiness claim.

THE NULL-FIRST FLOOR (v2.34): null / artifact / proxy / confound / unresolved outcomes are the ADVERSARIAL BASELINE --
first in order, first in standing, first in presumption. They are NOT cleanup categories and NOT failure buckets. And
"the nulls behaved" cannot even be asserted here: no null has behaved in any way at all, because no null exists. There
are six nouns.

TWO WARNINGS CARRIED FROM v2.36, HELD STRUCTURALLY:
  W1  E_control_collapse_role is REACHABLE IN LANGUAGE ONLY. The role is reported as GENERATED. Control-collapse is
      NOT tested, NOT detected, NOT ruled out, NOT avoided, and NOT handled. control_collapse_ruled_out = False AND
      control_collapse_detected = False. Naming the way your controls could fail is not checking whether they did.
  W2  F_candidate_structure_survival_role is ONLY A FUTURE QUESTION. Nothing here implies that candidate structure
      survived, was detected, was validated, or is EXPECTED. F names a BURDEN, not an entitlement; its emptiness is a
      legitimate PERMANENT state, not a to-do item. Role F is kept (rather than dropped) because without it roles A-E
      would be exhaustive by construction and survival would be reachable only by elimination -- the NULL SINK.

The six roles are SYMBOLIC and NON-PARTITIONING (W3). They are not fixture classes, measured classes, classifier
labels, validation groups, pass/fail categories, or visual categories. They are not exhaustive, more than one may stand
at once, and NOTHING is ever sorted into them -- because there is nothing to sort and no way to sort it.

A conservative CANONICAL protocol checker (`check_protocol`) reports `protocol_ok = True` with `breaches = []` ONLY for
the clean canonical report. It verifies CANONICAL SYMBOLIC STRUCTURE and FORBIDDEN-SURFACE ABSENCE, and NOTHING ELSE
(W4). Greenness does NOT mean scientific validity, fixture quality, control quality, detection, survival, falsification
success, or "the adversary is in place". There is no adversary yet. `role_validated = False` everywhere, even when
every check is green.

v2.37 advances the binding S3 obligation (a pre-stated, reachable survival path) BY EXACTLY NOTHING beyond symbolic
vocabulary. It is a freezing of language, not a step toward a result.

Deterministic. stdlib only; no torment_service; no runtime / camera / sensor / live-capture / screen-capture /
streaming / prompt / context / memory / action / render-body / autonomy contact; no real clips; no images; no arrays.
"""
from __future__ import annotations

VERSION = "v2.37"
OUTCOME_LABEL = "BRAINVISION_NULL_FIRST_ADVERSARIAL_FIXTURE_ROLES_REPORTING_ONLY"

# ---- the six v2.35 roles, in canonical order. Exactly these; no more, no fewer. ----
REQUIRED_ROLES = ("A_null_no_structure_role",
                  "B_fixture_artifact_role",
                  "C_proxy_confound_role",
                  "D_entangled_unresolved_role",
                  "E_control_collapse_role",
                  "F_candidate_structure_survival_role")

REPORT_ALLOWED_KEYS = ("version", "reporting_only", "offline_research_only", "symbolic_role_reporting_only",
                       "roles_generated", "outcome_label", "roles", "claim_locks", "adoption_flags",
                       "authorization_guards", "protocol", "verdict")

ROLE_ALLOWED_KEYS = ("role_id", "role_label", "conceptual_purpose", "adversarial_focus", "safe_reporting_language",
                     "forbidden_interpretations", "non_claim_constraints", "role_generated", "role_validated")

CANONICAL_ROLE_FIELDS = ("role_id", "role_label", "conceptual_purpose", "adversarial_focus",
                         "safe_reporting_language", "forbidden_interpretations", "non_claim_constraints")

PROTOCOL_ALLOWED_KEYS = ("protocol_note", "greenness_means", "roles_are_exhaustive", "roles_are_partitioning",
                         "control_collapse_reachable_in_language_only", "candidate_role_is_a_future_question_only")

CLAIM_LOCKS = ("flat_field_validated", "role_validated", "schema_validated", "entanglement_resolved",
               "by_residual_isolated", "generic_chroma_proxy_ruled_out", "null_rejected", "artifact_ruled_out",
               "proxy_ruled_out", "confound_controlled", "control_collapse_ruled_out", "control_collapse_detected",
               "candidate_structure_validated", "candidate_structure_survived", "candidate_structure_detected",
               "first_pass_structure_validity_claim_allowed", "temporal_claim_allowed",
               "descriptor_validity_claim_allowed", "geometry_validity_claim_allowed",
               "screen_readiness_claim_allowed", "runtime_readiness_claim_allowed",
               "memory_readiness_claim_allowed", "integration_readiness_claim_allowed", "vision_claim_allowed")

ADOPTION_FLAGS = ("descriptor_adopted", "coordinate_system_adopted", "metric_adopted", "threshold_adopted",
                  "scoring_adopted", "formula_adopted", "generation_rule_adopted", "schema_adopted",
                  "pass_fail_gate_adopted", "validation_adopted", "classifier_adopted", "neural_path_adopted")

AUTHORIZATION_GUARDS = ("screen_path_authorized", "runtime_path_authorized", "memory_path_authorized",
                        "integration_path_authorized", "real_clip_path_authorized", "fixture_generation_authorized",
                        "vision_claim_authorized")

# ---- forbidden FIELD-NAME tokens. Scanned ONLY on keys that are NOT in an allow-list, so the canonical keys can never
# collide with the guard. NOTE: the ROLE IDS are canonical v2.35 names (F_candidate_structure_survival_role contains
# "survival"); the ban applies to FIELD names, never to the role ids themselves. ----
FORBIDDEN_FIELD_TOKENS = ("fixture_instance", "fixture_data", "generation", "schema", "data_shape", "array", "image",
                          "descriptor", "coordinate", "metric", "score", "threshold", "formula", "decision",
                          "arrival", "evidence", "confidence", "classif", "validation", "pass_fail", "passfail",
                          "survival", "positive_structure", "screen", "runtime", "memory", "real_clip", "vision",
                          "neural", "pixel", "input", "assign", "mapping", "weight", "ratio", "geometry", "numeric")

# ---- forbidden CLAIM WORDING. Scanned on every canonical string. These are claim SHAPES and bare surface tokens the
# canonical text must never contain; a test asserts the clean report is free of every one of them. ----
FORBIDDEN_WORDING = (
    # the sixteen forbidden claims
    "structure detected", "candidate survived", "candidate structure survived", "fixture passed", "null rejected",
    "artifact ruled out", "proxy ruled out", "confound controlled", "control passed", "descriptor validated",
    "geometry validated", "metric validated", "screen ready", "runtime ready", "memory ready", "vision achieved",
    "brainvision sees",
    # paraphrases of the same moves
    "collapse detected", "collapse ruled out", "not an artifact", "null passed", "baseline passed",
    "confound is handled", "confound is solved", "proxy is controlled", "artifact is controlled", "controls checked",
    "the nulls behaved", "something real is there", "positive structure", "is validated", "are validated",
    "validation passed", "closure achieved", "is closed", "is ready", "proves", "proven", "is confirmed",
    "is verified", "we can now", "we now know",
    # surface tokens that must never appear in an adversarial role string
    "metric", "score", "threshold", "formula", "classifier", "descriptor", "coordinate", "pixel", "screen",
    "runtime", "memory", "vision", "neural", "real clip", "confidence", "decision rule", "arrival rule",
)

PROTOCOL_NOTE = ("static symbolic report of six null-first adversarial family roles; it takes nothing, builds no case, "
                 "tests nothing, controls nothing, and finds nothing; naming an adversary is not defeating one, and "
                 "the roles are nouns, not an adversary")

GREENNESS_MEANS = ("boundary compliance only; never scientific validity, never fixture quality, never control "
                   "quality, never detection, never survival, never falsification success, and never 'the adversary "
                   "is in place'")


def _build_roles():
    """Static symbolic objects for the six v2.35 null-first adversarial family roles. Names and canonical reporting
    prose only; no fixtures, no data, no generation rule, no numbers, no criteria. This IS the canonical report."""
    return {
        "A_null_no_structure_role": {
            "role_id": "A_null_no_structure_role",
            "role_label": "null / no-structure role",
            "conceptual_purpose": ("represent the possibility that NO MEANINGFUL STRUCTURE IS PRESENT; a VALID "
                                   "ENDPOINT, not a failure bucket, not a control that must be beaten, and not a "
                                   "nuisance to clear away"),
            "adversarial_focus": ("the baseline an apparent structure would have to be told apart from; it is the "
                                  "FLOOR, and the floor is where the design starts, not where it fails"),
            "safe_reporting_language": ["reported as null / no-structure"],
            "forbidden_interpretations": [
                "must not be read as a null that was rejected",
                "must not be read as a control that succeeded",
                "must not be read as a baseline that establishes anything",
                "must not be read as a failed run",
            ],
            "non_claim_constraints": [
                "no-structure is a REPORTING STANCE, never an absence that was measured",
                "nothing here is measured, compared, or ranked; null_rejected stays False",
            ],
            "role_generated": True,
            "role_validated": False,
        },
        "B_fixture_artifact_role": {
            "role_id": "B_fixture_artifact_role",
            "role_label": "fixture-artifact role",
            "conceptual_purpose": ("represent the possibility that any apparent structure was CAUSED BY THE WAY THE "
                                   "CASES WERE BUILT, rather than by anything they were built to show"),
            "adversarial_focus": "the design's suspicion of ITSELF, made first-class and permanent",
            "safe_reporting_language": ["reported as fixture-artifact suspected"],
            "forbidden_interpretations": [
                "must not be read as an artifact that was excluded, controlled, or measured",
                "must not be read as a licence to conclude the ABSENCE of an artifact -- that may never be concluded",
                "must not be read as anything that establishes the case families",
            ],
            "non_claim_constraints": [
                "naming the suspicion establishes NOTHING; artifact_ruled_out stays False",
                "the case family may never be declared free of artifacts",
            ],
            "role_generated": True,
            "role_validated": False,
        },
        "C_proxy_confound_role": {
            "role_id": "C_proxy_confound_role",
            "role_label": "proxy-confound role",
            "conceptual_purpose": ("represent the possibility that any apparent structure was CAUSED BY A PROXY OR A "
                                   "CONFOUND rather than by the intended target"),
            "adversarial_focus": ("the confound classes carried forward as FROZEN UNRESOLVED evidence -- spectrum, "
                                  "per-channel spread, directional movement, roughness / continuity -- named as "
                                  "adversaries, never as solved problems"),
            "safe_reporting_language": ["reported as proxy-confounded"],
            "forbidden_interpretations": [
                "must not be read as a proxy that was excluded",
                "must not be read as a confound that was handled, corrected, or solved",
                "must not be read as a comparison that was run",
            ],
            "non_claim_constraints": [
                "naming a confound neither controls it nor removes it; proxy_ruled_out and confound_controlled stay "
                "False",
                "the presumption that an apparent structure IS a proxy effect stands, and no account exists that "
                "says otherwise",
            ],
            "role_generated": True,
            "role_validated": False,
        },
        "D_entangled_unresolved_role": {
            "role_id": "D_entangled_unresolved_role",
            "role_label": "entangled / unresolved role",
            "conceptual_purpose": ("represent INSEPARABLE or UNRESOLVED behaviour -- the case where the adversarial "
                                   "families and any apparent structure CANNOT BE TOLD APART; a VALID, COMPLETE, "
                                   "TERMINAL ENDPOINT"),
            "adversarial_focus": ("the honest hard case: the possibility that the question is UNANSWERABLE, carried "
                                  "unbroken from the earlier entangled role"),
            "safe_reporting_language": ["reported as entangled / unresolved"],
            "forbidden_interpretations": [
                "must not be read as noise",
                "must not be read as hidden evidence for any candidate structure",
                "must not be read as failure, as success, as a defect, or as an else-branch",
                "must not be read as a quantity, a degree of mixing, or a resolution state",
            ],
            "non_claim_constraints": [
                "entanglement is a conceptual POSSIBILITY, never a measured quantity; entanglement_resolved stays "
                "False",
                "reporting it asserts nothing and supports nothing, and it must never be costlier to report than any "
                "other outcome",
            ],
            "role_generated": True,
            "role_validated": False,
        },
        "E_control_collapse_role": {
            "role_id": "E_control_collapse_role",
            "role_label": "control-collapse role",
            "conceptual_purpose": ("represent the possibility that THE CONTROL DESIGN ITSELF COLLAPSES -- that the "
                                   "adversarial families stop being distinguishable as roles at all, or become unable "
                                   "to be told apart from anything else; REACHABLE IN LANGUAGE ONLY"),
            "adversarial_focus": ("the design turning its suspicion on its OWN ADVERSARY; if the controls collapse, "
                                  "NOTHING the design would report means anything, including its nulls"),
            "safe_reporting_language": ["reported as control-collapse"],
            "forbidden_interpretations": [
                "must not be read as control-collapse that was tested, found, avoided, handled, or excluded",
                "must not be read as a bug to be fixed quietly",
                "must not be read as an impossible or merely theoretical case",
                "must not be read as a reason to weaken, retune, or narrow the adversary",
            ],
            "non_claim_constraints": [
                "this role is a NOUN; naming the way the controls could fail is not checking whether they did",
                "control_collapse_ruled_out and control_collapse_detected both stay False",
                "a design that cannot report the collapse of its own controls is not adversarial, only defended",
            ],
            "role_generated": True,
            "role_validated": False,
        },
        "F_candidate_structure_survival_role": {
            "role_id": "F_candidate_structure_survival_role",
            "role_label": "candidate-structure-survival role",
            "conceptual_purpose": ("represent ONLY THE FUTURE QUESTION of whether some candidate structure would "
                                   "withstand adversarial framing; it holds a place for a QUESTION, never for a "
                                   "finding"),
            "adversarial_focus": ("the burden itself -- that any candidate would have to withstand A-C, and stand "
                                  "apart from D, with the adversary FIXED IN ADVANCE and never weakened afterwards"),
            "safe_reporting_language": ["candidate structure remains only a future question"],
            "forbidden_interpretations": [
                "must not imply detection of any candidate structure",
                "must not imply that any candidate withstood anything",
                "must not imply validation, success, or positive evidence",
                "must not be read as an EXPECTATION, a goal, or a slot that ought to be filled",
                "must not be read as the else-branch of the other roles",
            ],
            "non_claim_constraints": [
                "candidate structure remains ONLY A FUTURE QUESTION; its emptiness is a legitimate permanent state, "
                "not a shortfall",
                "candidate_structure_validated, candidate_structure_survived, and candidate_structure_detected all "
                "stay False",
                "this role is kept so that A-E are not exhaustive by construction; it names a burden, not an "
                "entitlement",
            ],
            "role_generated": True,
            "role_validated": False,
        },
    }


def _build_protocol():
    return {
        "protocol_note": PROTOCOL_NOTE,
        "greenness_means": GREENNESS_MEANS,
        "roles_are_exhaustive": False,
        "roles_are_partitioning": False,
        "control_collapse_reachable_in_language_only": True,
        "candidate_role_is_a_future_question_only": True,
    }


def build_null_first_adversarial_fixture_roles_v2_37():
    """Deterministic static symbolic report of the six null-first adversarial family roles. Takes NO input by
    construction: there is nothing to feed it, so there is nothing it could build, evaluate, assign, decide, detect,
    or validate. It writes down six adversarial NOUNS."""
    return {
        "version": VERSION,
        "reporting_only": True,
        "offline_research_only": True,
        "symbolic_role_reporting_only": True,
        "roles_generated": True,
        "outcome_label": OUTCOME_LABEL,
        "roles": _build_roles(),
        "claim_locks": {k: False for k in CLAIM_LOCKS},
        "adoption_flags": {k: False for k in ADOPTION_FLAGS},
        "authorization_guards": {k: False for k in AUTHORIZATION_GUARDS},
        "protocol": _build_protocol(),
        "verdict": "HOLD",
    }


# ------------------------------------------------------------------------------------------------------------------
# conservative canonical protocol checker (W4: canonical symbolic structure + forbidden-surface absence; NOTHING else)
# ------------------------------------------------------------------------------------------------------------------
def _scan_wording(where, text):
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
        if v is not False:
            b.append("%s_true:%s" % (label, k))
    return b


def _check_role(rid, obj, canon):
    b = []
    if not isinstance(obj, dict):
        return ["role_not_dict:%s" % rid]

    for k in obj:
        if k not in ROLE_ALLOWED_KEYS:
            b.append("forbidden_role_field:%s.%s" % (rid, k))
            b += _scan_key_tokens("%s.%s" % (rid, k), k)
    for k in ROLE_ALLOWED_KEYS:
        if k not in obj:
            b.append("role_missing_key:%s.%s" % (rid, k))

    if obj.get("role_generated") is not True:
        b.append("role_not_generated:%s" % rid)
    if obj.get("role_validated") is not False:
        b.append("role_validated_true:%s" % rid)

    if isinstance(canon, dict):
        for k in CANONICAL_ROLE_FIELDS:
            if obj.get(k) != canon.get(k):
                b.append("noncanonical_role_field:%s.%s" % (rid, k))

    for k, v in obj.items():
        b += _scan_value_shape("%s.%s" % (rid, k), v)
        if isinstance(v, str):
            b += _scan_wording("%s.%s" % (rid, k), v)
        elif isinstance(v, (list, tuple)):
            for el in v:
                if isinstance(el, str):
                    b += _scan_wording("%s.%s" % (rid, k), el)
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

    W4: it verifies CANONICAL SYMBOLIC STRUCTURE and FORBIDDEN-SURFACE ABSENCE, and NOTHING ELSE. Greenness is NOT
    scientific validity, NOT fixture quality, NOT control quality, NOT detection, NOT survival, NOT falsification
    success, and NOT 'the adversary is in place'. There is no adversary here -- there are six nouns."""
    if report is None:
        report = build_null_first_adversarial_fixture_roles_v2_37()
    if not isinstance(report, dict):
        return {"protocol_ok": False, "breaches": ["report_not_dict"]}

    breaches = []

    for k in report:
        if k not in REPORT_ALLOWED_KEYS:
            breaches.append("forbidden_top_level_field:%s" % k)
            breaches += _scan_key_tokens("top.%s" % k, k)
    for k in REPORT_ALLOWED_KEYS:
        if k not in report:
            breaches.append("missing_top_level_key:%s" % k)

    if report.get("version") != VERSION:
        breaches.append("bad_version")
    for k in ("reporting_only", "offline_research_only", "symbolic_role_reporting_only", "roles_generated"):
        if report.get(k) is not True:
            breaches.append("flag_not_true:%s" % k)
    if report.get("outcome_label") != OUTCOME_LABEL:
        breaches.append("bad_outcome_label")
    if report.get("verdict") != "HOLD":
        breaches.append("verdict_not_hold")

    breaches += _check_group("claim_lock", "claim_locks", CLAIM_LOCKS, report)
    breaches += _check_group("adoption_flag", "adoption_flags", ADOPTION_FLAGS, report)
    breaches += _check_group("authorization_guard", "authorization_guards", AUTHORIZATION_GUARDS, report)
    breaches += _check_protocol_block(report)

    roles = report.get("roles")
    if not isinstance(roles, dict):
        breaches.append("roles_missing")
    else:
        canon = _build_roles()
        for rid in REQUIRED_ROLES:
            if rid not in roles:
                breaches.append("missing_role:%s" % rid)
        for rid in roles:
            if rid not in REQUIRED_ROLES:
                breaches.append("extra_role:%s" % rid)
        for rid, obj in roles.items():
            breaches += _check_role(rid, obj, canon.get(rid))

    seen, ordered = set(), []
    for x in breaches:
        if x not in seen:
            seen.add(x)
            ordered.append(x)
    return {"protocol_ok": len(ordered) == 0, "breaches": ordered}


if __name__ == "__main__":
    rep = build_null_first_adversarial_fixture_roles_v2_37()
    chk = check_protocol(rep)
    print("version", rep["version"], "| reporting_only", rep["reporting_only"],
          "| offline_research_only", rep["offline_research_only"],
          "| symbolic_role_reporting_only", rep["symbolic_role_reporting_only"])
    print("outcome_label:", rep["outcome_label"])
    print("roles_generated:", rep["roles_generated"], "| verdict:", rep["verdict"])
    print("protocol_ok:", chk["protocol_ok"], "| breaches:", chk["breaches"])
    print("claim_locks all False:", all(v is False for v in rep["claim_locks"].values()))
    print("adoption_flags all False:", all(v is False for v in rep["adoption_flags"].values()))
    print("authorization_guards all False:", all(v is False for v in rep["authorization_guards"].values()))
    print("control_collapse_detected:", rep["claim_locks"]["control_collapse_detected"],
          "| control_collapse_ruled_out:", rep["claim_locks"]["control_collapse_ruled_out"])
    print("candidate_structure_survived:", rep["claim_locks"]["candidate_structure_survived"],
          "| candidate_structure_detected:", rep["claim_locks"]["candidate_structure_detected"])
    print("\nNULL-FIRST ADVERSARIAL FAMILY ROLES (generated, NOT validated; nothing is sorted into them):")
    print("  (role_id carries the FULL canonical v2.35 role ID -- not a short letter)")
    for rid in REQUIRED_ROLES:
        ro = rep["roles"][rid]
        print("  role_id=%-38s label=%s" % (ro["role_id"], ro["role_label"]))
    print("\nsix adversarial NOUNS: nothing is tested, controlled, detected, ruled out, or survived;")
    print("E is reachable in LANGUAGE ONLY; F remains ONLY A FUTURE QUESTION;")
    print("S3 (a pre-stated, reachable survival path) is advanced by exactly NOTHING.")
