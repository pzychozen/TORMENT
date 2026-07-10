"""BV flat opponent-field synthetic fixtures v2.6 (offline research; form A; NON-LEARNING; NOT vision).

REPORTING/GUARD IMPLEMENTATION ONLY. It GENERATES and REPORTS the preregistered flat opponent-field synthetic
fixture-FAMILY obligations A-F as STRUCTURAL FIXTURE DESCRIPTIONS ONLY, with controls and completeness-enforced
non-authorizing guards. v2.6 is approved under the accepted v2.5 boundary of the flat opponent-field line (v2.0
pivot; v2.1a preregistration; v2.2 audit design; v2.3 reporting panels; v2.4/v2.5 accepted design boundary). It
introduces NO numeric surface: NO pixels, NO images, NO descriptor, NO coordinate system, NO metric, NO equation,
NO threshold, NO control metric, NO pass/fail validity gate, NO validation, NO screen analysis, NO real clips, NO
runtime / memory / integration, NO vision.

Reported fixture families (STRUCTURAL DESCRIPTIONS ONLY -- what each family is CONCEPTUALLY, never how it is built):
  A uniform_opponent_patches   : isolated BY/RG local regions; patch explicitness only; NO descriptor / coord / metric.
  B adjacent_opponent_patches  : neighboring local regions; adjacency/neighborhood conceptually; NO adjacency eqn / dist.
  C gradient_fields            : smooth BY/RG transition fields; gradient/continuity conceptually; NO gradient eqn / thr.
  D edge_discontinuity_fields  : sharp opponent boundaries; edge/discontinuity conceptually; NO edge detector / rule.
  E region_field_separation    : local patch pattern vs global field organization conceptually; NO field descriptor.
  F null_control_fields        : neutral / matched non-opponent controls preventing trivial reporting optimism; NO metric.

protocol_ok means ONLY that the required fixture-family reports, the controls, the generated-vs-validated boundary,
and the guards are PRESENT and admissible -- NOT validation, NOT closure. fixture_reporting_generated is about
GENERATION of structural descriptions only; flat_field_validated is ALWAYS False. No fixture family claims validation.
The result label is CONSERVATIVE: FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED, or invalid_protocol_breach
when a family / control / boundary / flag is missing, an adoption or authorization flag is True, the boundary is
incomplete, flat_field_validated is True, the verdict is not HOLD, a claim lock moves, or any family claims validation.
Output is deterministic. Verdict HOLD; all claim locks False. v1.x remains FROZEN EVIDENCE; v2.x remains an
UNVALIDATED conceptual pivot.

stdlib only; no torment_service; no runtime / camera / sensor / live-capture / screen-capture / streaming / prompt /
context / memory / action / render-body / autonomy contact; no real clips; no images; no pixel arrays.
"""
from __future__ import annotations

FIXTURE_FAMILIES = ("A_uniform_opponent_patches", "B_adjacent_opponent_patches", "C_gradient_fields",
                    "D_edge_discontinuity_fields", "E_region_field_separation", "F_null_control_fields")

# Families that carry a control / null role (guard against trivial reporting optimism):
CONTROL_FAMILIES = ("F_null_control_fields",)

# Required adoption flags (completeness-enforced; all present and False). Any missing OR True -> breach.
ADOPTION_FLAGS = ("descriptor_adopted", "coordinate_system_adopted", "metric_adopted", "equation_adopted",
                  "threshold_adopted", "control_metric_adopted", "pass_fail_validity_rule_adopted",
                  "tol_redefined", "generator_family_expanded", "spectral_closure_reopened")

# Required authorization flags (completeness-enforced; all present and False). Any missing OR True -> breach.
# Includes v2.5 §7 required flat_geometry_beyond_reporting_authorized.
AUTHORIZATION_FLAGS = ("screen_analysis_authorized", "camera_live_sensor_streaming_authorized",
                       "real_clip_authorized", "runtime_authorized", "memory_authorized",
                       "classifier_form_b_authorized", "neural_form_c_authorized",
                       "flat_geometry_beyond_reporting_authorized", "vision_claim_allowed",
                       "descriptor_validity_claim_allowed", "temporal_claim_allowed",
                       "integration_readiness_claim_allowed")

# Claim locks that must stay False; any moving True -> breach.
CLAIM_LOCK_FLAGS = ("first_pass_structure_validity_claim_allowed", "temporal_claim_allowed",
                    "descriptor_validity_claim_allowed", "vision_claim_allowed",
                    "integration_readiness_claim_allowed")

# Keys the generated-vs-validated boundary MUST carry (explicit text + booleans; v2.5 §11).
BOUNDARY_TEXT_KEYS = ("generated_means", "validated_means")

OUTCOME_LABELS = ("FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED", "invalid_protocol_breach")


def _build_fixture_families():
    """Each family is a STRUCTURAL DESCRIPTION only: what it conceptually is, plus explicit absence markers for
    descriptor / coordinates / metric / equation / threshold and an explicit claims_validation=False."""
    absent = {"descriptor_present": False, "coordinates_present": False, "metric_present": False,
              "equation_present": False, "threshold_present": False, "claims_validation": False}
    fam = {
        "A_uniform_opponent_patches": dict(
            family="A", role="stimulus",
            concept="isolated BY/RG local opponent regions described only by patch explicitness",
            reports_patch_explicitness_only=True, **absent),
        "B_adjacent_opponent_patches": dict(
            family="B", role="stimulus",
            concept="neighboring local opponent regions described only as adjacency / neighborhood conceptually",
            reports_adjacency_conceptual=True, **absent),
        "C_gradient_fields": dict(
            family="C", role="stimulus",
            concept="smooth BY/RG transition fields described only as gradient / continuity conceptually",
            reports_gradient_continuity_conceptual=True, **absent),
        "D_edge_discontinuity_fields": dict(
            family="D", role="stimulus",
            concept="sharp opponent boundaries described only as edge / discontinuity conceptually",
            reports_edge_discontinuity_conceptual=True, **absent),
        "E_region_field_separation": dict(
            family="E", role="stimulus",
            concept="local patch pattern vs global field organization described only as local-vs-field distinction",
            reports_local_vs_field_conceptual=True, **absent),
        "F_null_control_fields": dict(
            family="F", role="control",
            concept="neutral / matched non-opponent controls that prevent trivial reporting optimism",
            reports_control_role_conceptual=True, **absent),
    }
    return fam


def _build_adoption_flags():
    return {k: False for k in ADOPTION_FLAGS}


def _build_authorization_flags():
    return {k: False for k in AUTHORIZATION_FLAGS}


def _build_claim_locks():
    return {k: False for k in CLAIM_LOCK_FLAGS}


def _build_flat_field_validated():
    # ALWAYS False in v2.6; builder-backed so the breach check is live and injectable.
    return False


def _build_verdict():
    # ALWAYS HOLD in v2.6; builder-backed so the breach check is live and injectable.
    return "HOLD"


def _build_generated_vs_validated_boundary():
    return {
        "boundary_present": True,
        "generated_means": ("fixture families A-F are GENERATED as structural / conceptual descriptions only; "
                            "generation reports what each family conceptually is, nothing more"),
        "validated_means": ("validation would require a descriptor / coordinate system / metric / equation / "
                            "threshold / pass-fail rule and evidence -- NONE of which exist here"),
        "generated_is_not_validated": True,
        "fixture_generated": True,
        "flat_field_validated": False,
    }


def _families_ok(fam):
    if not isinstance(fam, dict) or set(fam.keys()) != set(FIXTURE_FAMILIES):
        return False
    for v in fam.values():
        if not isinstance(v, dict) or v.get("claims_validation") is not False:
            return False
        for absent_key in ("descriptor_present", "coordinates_present", "metric_present",
                           "equation_present", "threshold_present"):
            if v.get(absent_key) is not False:
                return False
    return True


def _controls_ok(fam):
    if not isinstance(fam, dict):
        return False
    for c in CONTROL_FAMILIES:
        if c not in fam or fam[c].get("role") != "control":
            return False
    return True


def _boundary_ok(b):
    """Explicit generated-vs-validated boundary required (v2.5 §11): present marker, generated!=validated,
    fixture_generated True, flat_field_validated PRESENT and False, and non-empty explicit text on both sides.
    Any missing key OR flat_field_validated not False -> not ok -> breach."""
    if not isinstance(b, dict):
        return False
    if b.get("boundary_present") is not True:
        return False
    if b.get("generated_is_not_validated") is not True:
        return False
    if b.get("fixture_generated") is not True:
        return False
    if "flat_field_validated" not in b or b["flat_field_validated"] is not False:
        return False
    for k in BOUNDARY_TEXT_KEYS:
        if not (isinstance(b.get(k), str) and b[k].strip()):
            return False
    return True


def _flagset_ok(flags, required):
    """Completeness-enforced: dict present, every required key PRESENT and False, and no key True.
    Any missing OR True -> not ok."""
    if not isinstance(flags, dict):
        return False
    if not all(k in flags and flags[k] is False for k in required):
        return False
    return all(v is False for v in flags.values())


def run():
    families = _build_fixture_families()
    adoption = _build_adoption_flags()
    authorization = _build_authorization_flags()
    claim_locks = _build_claim_locks()
    boundary = _build_generated_vs_validated_boundary()
    flat_field_validated = _build_flat_field_validated()
    verdict = _build_verdict()

    breaches = []
    if not _families_ok(families):
        breaches.append("fixture_family_missing_or_claims_validation")
    if not _controls_ok(families):
        breaches.append("controls_missing")
    if not _boundary_ok(boundary):
        breaches.append("generated_vs_validated_boundary_missing_or_incomplete")
    if not _flagset_ok(adoption, ADOPTION_FLAGS):
        breaches.append("adoption_flag_missing_or_true")
    if not _flagset_ok(authorization, AUTHORIZATION_FLAGS):
        breaches.append("authorization_flag_missing_or_true")
    if not _flagset_ok(claim_locks, CLAIM_LOCK_FLAGS):
        breaches.append("claim_lock_moved")
    if flat_field_validated is not False:
        breaches.append("flat_field_validated_true")
    if verdict != "HOLD":
        breaches.append("verdict_not_hold")

    clean = (len(breaches) == 0)

    family_reporting = {}
    outcome_label, outcome = None, None
    if clean:
        family_reporting = {k: {"reported": True, "claims_validation": False} for k in FIXTURE_FAMILIES}
        outcome_label = "FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED"
        outcome = ("FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED: the preregistered flat opponent-field "
                   "synthetic fixture families A-F were generated as structural descriptions with controls and "
                   "non-authorizing guards; nothing is validated, adopted, or closed")
    else:
        outcome_label = "invalid_protocol_breach"
        outcome = "invalid_protocol_breach: " + "; ".join(breaches)

    result = {
        "diagnostic": ("v2.6 flat opponent-field synthetic fixtures (form A, NON-LEARNING; REPORTING/guard only; "
                       "fixture families A-F as structural descriptions with controls; adopts no descriptor / "
                       "coordinate-system / metric / equation / threshold / control-metric / pass-fail rule; "
                       "non-authorizing)"),
        "model_form": "A_non_learning_reporting", "learning": False,
        "reporting_only": True, "conceptual_only": True, "offline_only": True,
        "boundary_source": "v2.5 accepted boundary (flat opponent-field line)",
        "prereg_source": "v2.1a preregistration plan + v2.2/v2.3 flat opponent-field design (accepted)",
        "report_question": ("generate the preregistered flat opponent-field synthetic fixture families A-F as "
                            "structural fixture descriptions with controls and non-authorizing guards"),
        "fixture_families": families,
        "control_families": list(CONTROL_FAMILIES),
        "family_reporting": family_reporting,
        "generated_vs_validated_boundary": boundary,
        "adoption_flags": adoption,
        "authorization_flags": authorization,
        "claim_locks": claim_locks,
        "reporting_only_flag": True,
        "fixture_reporting_generated": True,
        "flat_field_validated": flat_field_validated,
        "v1x_status": "frozen_evidence", "v2x_status": "unvalidated_conceptual_pivot",
        "protocol_ok": clean, "breaches": breaches,
        "outcome_label": outcome_label, "outcome": outcome,
        "frozen_brainvision_verdict": verdict,
        "first_pass_structure_validity_claim_allowed": False,
        "temporal_claim_allowed": False,
        "descriptor_validity_claim_allowed": False,
        "vision_claim": False, "memory_readiness_claim": False, "runtime_readiness_claim": False,
        "integration_readiness_claim": False,
    }
    # Surface adoption + authorization flags at top level too (single source: the built dicts).
    result.update(adoption)
    result.update(authorization)
    return result


if __name__ == "__main__":
    r = run()
    print("model", r["model_form"], "| reporting_only", r["reporting_only"], "| conceptual_only",
          r["conceptual_only"], "| offline_only", r["offline_only"])
    print("report question:", r["report_question"])
    print("protocol_ok:", r["protocol_ok"], r["breaches"],
          "| fixture_reporting_generated:", r["fixture_reporting_generated"],
          "| flat_field_validated:", r["flat_field_validated"])
    print("fixture families:", list(r["fixture_families"].keys()))
    print("control families:", r["control_families"])
    print("generated_vs_validated_boundary present:", r["generated_vs_validated_boundary"]["boundary_present"],
          "| generated_is_not_validated:", r["generated_vs_validated_boundary"]["generated_is_not_validated"])
    print("adoption_flags:", r["adoption_flags"])
    print("authorization_flags:", r["authorization_flags"])
    if r["protocol_ok"]:
        print("\nFIXTURE FAMILIES A-F (structural descriptions):")
        for k in FIXTURE_FAMILIES:
            fx = r["fixture_families"][k]
            print("  %-30s role=%-8s claims_validation=%s  %s" %
                  (k, fx["role"], fx["claims_validation"], fx["concept"][:52] + "..."))
    print("\nOUTCOME_LABEL:", r["outcome_label"])
    print("v1x_status:", r["v1x_status"], "| v2x_status:", r["v2x_status"])
    print("verdict:", r["frozen_brainvision_verdict"], "| claim locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"],
          r["descriptor_validity_claim_allowed"])
