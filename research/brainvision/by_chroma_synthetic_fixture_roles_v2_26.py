"""BV BY/chroma synthetic fixture ROLES v2.26 (offline research; static symbolic; reporting-only; NOT vision).

REPORTING-ONLY IMPLEMENTATION. It builds the SMALLEST possible STATIC SYMBOLIC report of the six conceptual BY/chroma
family ROLES proposed in v2.24 (A BY-dominant chroma residual, B generic chroma proxy, C matched non-BY chroma,
D BY/chroma entangled, E fixture-family artifact, F null / reporting-boundary), under the conditional v2.25
implementation boundary. It is authorized as a strictly static / symbolic, deterministic, offline, non-authorizing
slice outside `torment_service/`.

Reporting ONLY. It generates NO fixtures and NO fixture data. It does NOT adopt or define a descriptor, a coordinate
system, numeric geometry, a metric, an equation, a threshold, a score, a pass/fail gate, an acceptance criterion, an
expected output, validation, closure, a classifier (form B) feature, a neural (form C) encoding, a screen / real-clip /
camera / live / sensor / streaming path, a runtime path, or a memory path. It carries NO arrays, NO vectors, NO images,
NO pixel data, NO x/y / grid coordinates, NO numeric parameters, NO distances / magnitudes / gradients, and NO
comparison functions.

Each ROLE is a STATIC SYMBOLIC OBJECT: a role id / role label, a conceptual purpose string, a closed reporting-focus
label, non-claim constraints, forbidden interpretations, safe reporting language, and the two boolean markers
`role_generated = True` / `role_validated = False`. Generation is NOT validation: naming a role is not measuring it,
separating anything, validating anything, or seeing anything. Reporting six roles does not answer the v2.22 primary
question ("can future synthetic design distinguish BY-axis residual behavior from generic chroma proxy effects without
adopting metrics or closure claims?") and must not be read as progress toward answering it. The v2.22 Formulation-C
constraint stays in force: residual localization must not imply descriptor validity.

A conservative protocol checker (`check_protocol`) reports `protocol_ok = True` with `breaches = []` ONLY when every
constraint holds. It is CANONICAL: the top-level note and each role's `role_id`, `role_label`, `conceptual_purpose`,
`reporting_focus`, `non_claim_constraints`, `forbidden_interpretations`, and `safe_reporting_language` must match the
builder's approved static report EXACTLY -- so arbitrary text inside an allowed string field is rejected, and the
canonical A-F role identity / content cannot drift. It also marks a breach whenever a role is missing / extra / wrong,
a role is marked validated, the verdict is not HOLD, a claim-lock / adoption-flag / authorization-guard group carries a
missing, EXTRA, or non-False key (an extra False key silently widens the guarded surface, so it is a breach too), a
forbidden concrete field appears, or forbidden claiming wording (validation / closure / readiness / screen / runtime /
memory / classifier / neural / vision) appears in any string. If uncertain, it marks a breach. A green protocol result
means BOUNDARY COMPLIANCE ONLY (v2.14) -- never correctness, distinguishability, validation, or readiness.

The outcome label is CONSERVATIVE: BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_REPORTING_ONLY. Output is
deterministic. `flat_field_validated = False`; all claim locks False; `verdict = HOLD`. Prior BY / color / chroma work
remains FROZEN UNRESOLVED evidence; the flat opponent-field symbolic branch remains PAUSED HELD.

stdlib only; no torment_service; no runtime / camera / sensor / live-capture / screen-capture / streaming / prompt /
context / memory / action / render-body / autonomy contact; no real clips; no images; no pixel arrays.
"""
from __future__ import annotations

VERSION = "v2.26"
OUTCOME_LABEL = "BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_ROLES_REPORTING_ONLY"

NOTE_TEXT = ("static symbolic report of exactly the six v2.24 BY/chroma conceptual roles; role reporting only, never "
             "role validation; generates no fixtures and no fixture data; adopts no descriptor, no coordinate system, "
             "no metric, no threshold, no scoring, and no pass-fail gate; opens no screen, runtime, memory, "
             "classifier, neural, or vision path; the v2.22 primary question stays unresolved")

# The six v2.24 roles, in canonical order. Exactly these; no more, no fewer.
REQUIRED_ROLES = ("A_BY_dominant_chroma_residual_role",
                  "B_generic_chroma_proxy_role",
                  "C_matched_non_BY_chroma_role",
                  "D_BY_chroma_entangled_role",
                  "E_fixture_family_artifact_role",
                  "F_null_reporting_boundary_role")

# Closed set of reporting-focus LABELS (symbolic names only; never a quantity, never a measured focus):
ALLOWED_REPORTING_FOCUS = frozenset({"by_residual_reporting_focus",
                                     "generic_proxy_confound_focus",
                                     "non_by_chroma_focus",
                                     "entanglement_possibility_focus",
                                     "artifact_suspicion_focus",
                                     "null_reporting_boundary_focus"})

# Exactly the keys a static symbolic role object may carry:
ROLE_ALLOWED_KEYS = frozenset({"role_id", "role_label", "conceptual_purpose", "reporting_focus",
                               "non_claim_constraints", "forbidden_interpretations", "safe_reporting_language",
                               "role_generated", "role_validated"})

REQUIRED_ROLE_KEYS = ("role_id", "role_label", "conceptual_purpose", "reporting_focus", "non_claim_constraints",
                      "forbidden_interpretations", "safe_reporting_language", "role_generated", "role_validated")

# Role fields whose VALUES must match the canonical builder report exactly:
CANONICAL_ROLE_FIELDS = ("role_id", "role_label", "conceptual_purpose", "reporting_focus", "non_claim_constraints",
                         "forbidden_interpretations", "safe_reporting_language")

# Claim locks that must stay False (any True -> breach). The first ten are the standing Brainvision locks; the last six
# are the v2.26 role-specific locks.
CLAIM_LOCKS = ("flat_field_validated",
               "first_pass_structure_validity_claim_allowed",
               "temporal_claim_allowed",
               "descriptor_validity_claim_allowed",
               "geometry_validity_claim_allowed",
               "screen_readiness_claim_allowed",
               "runtime_readiness_claim_allowed",
               "memory_readiness_claim_allowed",
               "integration_readiness_claim_allowed",
               "vision_claim_allowed",
               "role_validity_claim_allowed",
               "residual_localization_claim_allowed",
               "proxy_resolved_claim_allowed",
               "metric_separation_claim_allowed",
               "closure_claim_allowed",
               "validation_claim_allowed")

# Adoption flags that must stay False (any True -> breach):
ADOPTION_FLAGS = ("descriptor_adopted", "coordinate_system_adopted", "metric_adopted", "threshold_adopted",
                  "scoring_adopted", "pass_fail_gate_adopted")

# Authorization guards that must stay False (any True -> breach):
AUTHORIZATION_GUARDS = ("implementation_authorizes_validation", "implementation_authorizes_fixture_generation",
                        "implementation_authorizes_screen_analysis", "implementation_authorizes_runtime_contact",
                        "implementation_authorizes_memory_contact", "implementation_authorizes_vision_claim",
                        "implementation_authorizes_descriptor_claim", "implementation_authorizes_geometry_claim")

# Top-level report keys that may appear (anything else -> breach):
REPORT_ALLOWED_KEYS = frozenset({"version", "note", "reporting_only", "offline_research_only", "symbolic_static_only",
                                 "flat_field_validated", "verdict", "outcome_label", "roles", "claim_locks",
                                 "adoption_flags", "authorization_guards"})

# Forbidden substrings in any ROLE field key (conservative; belt-and-suspenders with the key allow-list). These are
# applied to role-object FIELD keys only -- never to the role ids themselves, which are canonical v2.24 names.
FORBIDDEN_KEY_TOKENS = ("coord", "pixel", "grid", "vector", "arr", "distance", "magnitude", "formula", "equation",
                        "threshold", "score", "metric", "weight", "ratio", "classifier", "neural", "embedding",
                        "descriptor", "image", "screen", "clip", "camera", "runtime", "memory", "pass_fail",
                        "passfail", "numeric", "geometry", "data", "fixture_instance")

# Forbidden CLAIMING wording in any string value (conservative). These are claim-shaped phrases: the canonical report
# DENIES claims and must never ASSERT one. Honest denial language ("must not imply descriptor validity") is allowed;
# assertion language is not. The canonical report is required to be free of every phrase below, and a test asserts it.
FORBIDDEN_WORDING = (
    # validation / closure / readiness
    "is validated", "are validated", "has been validated", "have been validated", "successfully validated",
    "validation succeeded", "validation passed", "validation complete", "closure achieved", "closure is reached",
    "is closed", "question is answered", "question is settled", "is resolved", "now resolved", "is ready",
    "ready for", "readiness achieved", "proves", "proven", "is confirmed", "is verified", "we may conclude",
    "therefore valid",
    # role / proxy / artifact / null claim forms
    "role is valid", "roles are valid", "role is real", "proxy is controlled", "proxy is solved",
    "proxy is ruled out", "proxy ruled out", "confound is solved", "not an artifact", "artifact ruled out",
    "artifact is controlled", "null passed", "null control passed", "control passed", "baseline passed",
    "residual is distinct", "residual is separable", "descriptor is valid", "descriptor works",
    "descriptor validity is established", "geometry is valid",
    # metric / separation / pass-fail claim forms
    "separation is measured", "separation score", "distinguishability score", "scored separation",
    "measured separation", "metric adopted", "threshold adopted", "pass/fail", "pass_fail", "passes the gate",
    "gate passed", "acceptance criterion",
    # screen / runtime / memory / classifier / neural / vision
    "brainvision sees", "the system sees", "we see", "screen path", "screen readiness", "runtime path",
    "runtime readiness", "memory path", "memory readiness", "classifier label", "classifier feature",
    "neural target", "neural encoding", "production vision", "vision is achieved", "vision claim is allowed",
    "real clip", "live capture", "screen capture", "streaming", "pixel data",
)


def _build_roles():
    """Static symbolic objects for the six v2.24 BY/chroma conceptual roles. Symbolic labels and conceptual strings
    only; no fixtures, no data, no numbers, no coordinates, no descriptor / metric / threshold / pass-fail content.
    This IS the canonical report."""
    return {
        "A_BY_dominant_chroma_residual_role": {
            "role_id": "A",
            "role_label": "BY-dominant chroma residual role",
            "conceptual_purpose": ("name a conceptual case in which BY-axis residual pressure would be the intended "
                                   "reporting focus; it names what such a case would be FOR, and computes nothing"),
            "reporting_focus": "by_residual_reporting_focus",
            "non_claim_constraints": [
                "residual localization must not imply descriptor validity",
                "BY-dominant is a role NAME; it carries no axis, no channel, and no number",
                "nothing here is measured, computed, compared, or ranked",
            ],
            "forbidden_interpretations": [
                "must not be read as a measured BY axis",
                "must not be read as a quantified dominance",
                "must not be read as a separation that was scored or measured",
                "must not be read as visual truth",
            ],
            "safe_reporting_language": [
                "a role that conceptually carries BY-axis residual pressure",
                "a reporting focus that can be NAMED",
            ],
            "role_generated": True,
            "role_validated": False,
        },
        "B_generic_chroma_proxy_role": {
            "role_id": "B",
            "role_label": "generic chroma proxy role",
            "conceptual_purpose": ("name the conceptual confound class -- spectrum, per-channel spread, directional "
                                   "movement, roughness -- that any apparent residual must be held apart from; naming "
                                   "a confound neither controls it nor removes it"),
            "reporting_focus": "generic_proxy_confound_focus",
            "non_claim_constraints": [
                "the standing presumption holds: an apparent residual IS a generic chroma proxy effect until a "
                "reporting-only distinction shows otherwise, and no such showing exists",
                "naming a confound is not controlling it, not ruling it out, and not measuring it",
            ],
            "forbidden_interpretations": [
                "must not be read as a solved confound",
                "must not be read as a controlled proxy",
                "must not be read as a comparison that was run",
            ],
            "safe_reporting_language": [
                "a role that conceptually carries generic chroma proxy character",
                "a NAMED confound class, held open",
            ],
            "role_generated": True,
            "role_validated": False,
        },
        "C_matched_non_BY_chroma_role": {
            "role_id": "C",
            "role_label": "matched non-BY chroma role",
            "conceptual_purpose": ("name conceptual non-BY chroma pressure, so that BY language does not silently "
                                   "swallow every colour effect; matched is a conceptual relation, never a computed "
                                   "matching"),
            "reporting_focus": "non_by_chroma_focus",
            "non_claim_constraints": [
                "matched is CONCEPTUAL and is never a match computed over any quantity",
                "no colour space, no channel, and no axis system is adopted anywhere",
            ],
            "forbidden_interpretations": [
                "must not be read as a colour-space axis",
                "must not be read as a channel separation that was measured",
                "must not be read as evidence that any representation works",
            ],
            "safe_reporting_language": [
                "a role that conceptually carries non-BY chroma pressure",
                "conceptually matched, never computed",
            ],
            "role_generated": True,
            "role_validated": False,
        },
        "D_BY_chroma_entangled_role": {
            "role_id": "D",
            "role_label": "BY/chroma entangled role",
            "conceptual_purpose": ("name the honest hard case in which BY residual pressure and generic chroma proxy "
                                   "pressure may be INSEPARABLE; it keeps the design from presupposing that a "
                                   "separation exists at all"),
            "reporting_focus": "entanglement_possibility_focus",
            "non_claim_constraints": [
                "entanglement is a conceptual POSSIBILITY, never a quantity and never a degree",
                "this role is a reason the v2.22 question may be UNANSWERABLE; it is not a finding",
            ],
            "forbidden_interpretations": [
                "must not be read as a quantified degree of mixing",
                "must not be read as a separability that was scored",
                "must not be read as closure from this role alone",
            ],
            "safe_reporting_language": [
                "a role that conceptually carries entangled BY and proxy pressure",
                "an honest statement that separability may not exist",
            ],
            "role_generated": True,
            "role_validated": False,
        },
        "E_fixture_family_artifact_role": {
            "role_id": "E",
            "role_label": "fixture-family artifact role",
            "conceptual_purpose": ("name the self-suspicion case: the possibility that any apparent distinction was "
                                   "PRODUCED BY the way the case family itself was constructed; the suspicion is "
                                   "first-class and permanent"),
            "reporting_focus": "artifact_suspicion_focus",
            "non_claim_constraints": [
                "naming the artifact suspicion establishes nothing about the case family",
                "the case family may never be declared free of artifacts",
            ],
            "forbidden_interpretations": [
                "must not be read as an artifact control that succeeded",
                "must not be read as an artifact that was measured",
                "must not be read as evidence that the case families are sound",
            ],
            "safe_reporting_language": [
                "a role that conceptually carries the suspicion that the cases may manufacture the effect",
                "a permanent self-suspicion, never a settled one",
            ],
            "role_generated": True,
            "role_validated": False,
        },
        "F_null_reporting_boundary_role": {
            "role_id": "F",
            "role_label": "null / reporting-boundary role",
            "conceptual_purpose": ("name the non-authorizing boundary at which reporting stops and validation would "
                                   "impermissibly begin; it isolates the CLAIM BOUNDARY itself and nothing about "
                                   "colour"),
            "reporting_focus": "null_reporting_boundary_focus",
            "non_claim_constraints": [
                "this role is an ANTI-CLAIM SCAFFOLD and is never evidence (v2.12 N1-N6)",
                "a green protocol result would mean BOUNDARY COMPLIANCE ONLY, and never a null that succeeded",
            ],
            "forbidden_interpretations": [
                "must not be read as a validation control",
                "must not be read as a baseline",
                "must not be read as a negative control that succeeded",
                "must not be read as falsification success",
            ],
            "safe_reporting_language": [
                "a non-authorizing reporting-boundary role",
                "a control BY NAMING only",
            ],
            "role_generated": True,
            "role_validated": False,
        },
    }


def build_by_chroma_synthetic_fixture_roles_v2_26():
    """Deterministic static symbolic ROLE report for the six v2.24 BY/chroma roles. Reporting only: it names the six
    roles and nothing more. It generates no fixtures, measures nothing, separates nothing, and validates nothing."""
    return {
        "version": VERSION,
        "note": NOTE_TEXT,
        "reporting_only": True,
        "offline_research_only": True,
        "symbolic_static_only": True,
        "flat_field_validated": False,
        "verdict": "HOLD",
        "outcome_label": OUTCOME_LABEL,
        "roles": _build_roles(),
        "claim_locks": {k: False for k in CLAIM_LOCKS},
        "adoption_flags": {k: False for k in ADOPTION_FLAGS},
        "authorization_guards": {k: False for k in AUTHORIZATION_GUARDS},
    }


def _scan_wording(where, text):
    """Conservative claiming-wording scan over a single string. Any forbidden claim phrase -> breach."""
    low = str(text).lower()
    out = []
    for phrase in FORBIDDEN_WORDING:
        if phrase in low:
            out.append("forbidden_wording:%s:%s" % (where, phrase))
    return out


def _scan_value(rname, key, v):
    """Conservative value scan: no numbers, no vectors/arrays, no nested structures. Booleans are allowed. Strings and
    lists of strings are allowed, but every string is wording-scanned."""
    b = []
    if isinstance(v, bool):
        return b
    if isinstance(v, (int, float)):
        b.append("forbidden_numeric:%s.%s" % (rname, key))
    elif isinstance(v, str):
        b += _scan_wording("%s.%s" % (rname, key), v)
    elif isinstance(v, (list, tuple)):
        for el in v:
            if isinstance(el, bool):
                b.append("forbidden_nonstring_in_list:%s.%s" % (rname, key))
            elif isinstance(el, (int, float)):
                b.append("forbidden_vector_or_array:%s.%s" % (rname, key))
            elif isinstance(el, str):
                b += _scan_wording("%s.%s" % (rname, key), el)
            else:
                b.append("forbidden_nested_in_list:%s.%s" % (rname, key))
    elif isinstance(v, dict):
        b.append("forbidden_nested_structure:%s.%s" % (rname, key))
    elif v is None:
        b.append("forbidden_none_value:%s.%s" % (rname, key))
    else:
        b.append("forbidden_value_type:%s.%s" % (rname, key))
    return b


def _check_role(rname, robj, canon):
    b = []
    if not isinstance(robj, dict):
        return ["role_not_dict:%s" % rname]
    # key allow-list + forbidden-token scan (role FIELD keys only)
    for k in robj:
        if k not in ROLE_ALLOWED_KEYS:
            b.append("forbidden_role_field:%s.%s" % (rname, k))
        low = str(k).lower()
        for tok in FORBIDDEN_KEY_TOKENS:
            if tok in low:
                b.append("forbidden_token_field:%s.%s" % (rname, k))
                break
    # required keys present
    for k in REQUIRED_ROLE_KEYS:
        if k not in robj:
            b.append("role_missing_key:%s.%s" % (rname, k))
    # boolean markers: generated is NOT validated
    if robj.get("role_generated") is not True:
        b.append("role_not_generated:%s" % rname)
    if robj.get("role_validated") is not False:
        b.append("role_validated_true:%s" % rname)
    # reporting focus must come from the closed label set
    focus = robj.get("reporting_focus")
    if not (isinstance(focus, str) and focus in ALLOWED_REPORTING_FOCUS):
        b.append("forbidden_reporting_focus:%s.%s" % (rname, str(focus)))
    # the three reporting lists must be non-empty lists of strings
    for key in ("non_claim_constraints", "forbidden_interpretations", "safe_reporting_language"):
        val = robj.get(key)
        if not (isinstance(val, list) and len(val) > 0):
            b.append("missing_symbolic_reporting:%s.%s" % (rname, key))
        elif not all(isinstance(el, str) for el in val):
            b.append("nonstring_reporting_entry:%s.%s" % (rname, key))
    # CANONICAL enforcement: every canonical field must match the approved builder report EXACTLY (rejects claiming
    # text, fixture / metric / threshold / descriptor text, and role identity drift).
    if isinstance(canon, dict):
        for key in CANONICAL_ROLE_FIELDS:
            if robj.get(key) != canon.get(key):
                b.append("noncanonical_role_field:%s.%s" % (rname, key))
    # deep value scan (numbers / containers / nesting / claiming wording)
    for k, v in robj.items():
        b += _scan_value(rname, k, v)
    return b


def check_protocol(report=None):
    """Conservative CANONICAL protocol checker. Returns {'protocol_ok': bool, 'breaches': [...]}. protocol_ok is True
    with an empty breaches list ONLY when every constraint holds AND the note + per-role canonical fields match the
    builder's approved static report exactly. If uncertain, it marks a breach.

    A green result means BOUNDARY COMPLIANCE ONLY (v2.14). It is NOT validation, NOT correctness, NOT
    distinguishability, NOT descriptor validity, NOT closure, and NOT readiness."""
    if report is None:
        report = build_by_chroma_synthetic_fixture_roles_v2_26()
    breaches = []
    if not isinstance(report, dict):
        return {"protocol_ok": False, "breaches": ["report_not_dict"]}

    canon_roles = _build_roles()

    # top-level allow-list
    for k in report:
        if k not in REPORT_ALLOWED_KEYS:
            breaches.append("forbidden_report_field:%s" % k)

    # scalar invariants
    if report.get("version") != VERSION:
        breaches.append("bad_version")
    for k in ("reporting_only", "offline_research_only", "symbolic_static_only"):
        if report.get(k) is not True:
            breaches.append("missing_true_flag:%s" % k)
    if report.get("outcome_label") != OUTCOME_LABEL:
        breaches.append("bad_outcome_label")
    if report.get("flat_field_validated") is not False:
        breaches.append("flat_field_validated_true")
    if report.get("verdict") != "HOLD":
        breaches.append("verdict_not_hold")
    # canonical top-level note (rejects any non-approved note text, including claiming text)
    if report.get("note") != NOTE_TEXT:
        breaches.append("noncanonical_note")
    if isinstance(report.get("note"), str):
        breaches += _scan_wording("note", report["note"])

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
            # an EXTRA key silently widens the lock / adoption / authorization surface even when it is False:
            # a key that is not in the canonical group is a breach regardless of its value.
            if k not in keys:
                breaches.append("%s_extra:%s" % (label, k))
            if v is not False:
                breaches.append("%s_true:%s" % (label, k))

    # roles
    roles = report.get("roles")
    if not isinstance(roles, dict):
        breaches.append("roles_missing")
    else:
        present = set(roles.keys())
        for r in REQUIRED_ROLES:
            if r not in present:
                breaches.append("missing_role:%s" % r)
        for r in present:
            if r not in REQUIRED_ROLES:
                breaches.append("extra_role:%s" % r)
        for rname, robj in roles.items():
            breaches += _check_role(rname, robj, canon_roles.get(rname))

    # de-duplicate while preserving order (a single fault may trip multiple guards)
    seen, ordered = set(), []
    for x in breaches:
        if x not in seen:
            seen.add(x)
            ordered.append(x)
    return {"protocol_ok": len(ordered) == 0, "breaches": ordered}


if __name__ == "__main__":
    rep = build_by_chroma_synthetic_fixture_roles_v2_26()
    chk = check_protocol(rep)
    print("version", rep["version"], "| reporting_only", rep["reporting_only"],
          "| symbolic_static_only", rep["symbolic_static_only"], "| offline_research_only",
          rep["offline_research_only"])
    print("outcome_label:", rep["outcome_label"])
    print("flat_field_validated:", rep["flat_field_validated"], "| verdict:", rep["verdict"])
    print("protocol_ok:", chk["protocol_ok"], "| breaches:", chk["breaches"])
    print("roles:", list(rep["roles"].keys()))
    print("claim_locks all False:", all(v is False for v in rep["claim_locks"].values()))
    print("adoption_flags all False:", all(v is False for v in rep["adoption_flags"].values()))
    print("authorization_guards all False:", all(v is False for v in rep["authorization_guards"].values()))
    print("\nBY/CHROMA CONCEPTUAL ROLES A-F (static symbolic objects; generated, NOT validated):")
    for k in REQUIRED_ROLES:
        ro = rep["roles"][k]
        print("  %-36s id=%s label=%-36s focus=%s" %
              (k, ro["role_id"], ro["role_label"], ro["reporting_focus"]))
    print("\nreporting six roles measures nothing, separates nothing, and validates nothing;")
    print("the v2.22 primary question remains UNRESOLVED and may be unanswerable (role D).")
