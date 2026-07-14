"""BV flat opponent-field audit v2.3 (offline research; form A; NON-LEARNING; NOT vision).

REPORTING/GUARD IMPLEMENTATION ONLY. It generates the accepted v2.2 flat opponent-field audit reporting panels
A-F as STRUCTURAL / CONCEPTUAL reporting over OFFLINE SYNTHETIC content. The flat opponent-field is a NEW,
UNVALIDATED abstraction (the v2.0 pivot); v2.3 has NO frozen prior harness to reuse and introduces NO numeric
surface, descriptor, or coordinate system. It reports the v2.1a preregistration OBLIGATIONS themselves as
conceptual conformance, with STRUCTURAL BOOLEANS ONLY, and carries a completeness-enforced non-authorizing guard.

  A patch-definition   : conceptual local opponent-patch requirement; NO coordinate system; NO descriptor.
  B opponent-channel   : BY/RG explicitness requirement; NO metric.
  C spatial-relation   : adjacency / neighborhood / gradient / edge / continuity-discontinuity named; NO equations.
  D region-field       : local patch effects vs field-level organization distinction; NO pass/fail rule.
  E temporal-deferral  : motion/time deferred, NOT a first principle.
  F non-authorizing guard: all required authorization flags present and False; ANY missing OR True -> protocol_ok False.

It IMPLEMENTS NO descriptor, NO coordinate system, NO metric, NO equation, NO threshold, NO pass/fail validity
gate; REDEFINES NO TOL; expands no family; reopens no spectral group; adds NO classifier (form B) / neural encoder
(form C); opens NO flat-geometry implementation beyond conceptual panel reporting and NO screen-analysis
implementation; touches no runtime / memory / integration / real clips.

protocol_ok means ONLY that the required reporting panels and the guard are present -- NOT validation, NOT closure.
flat_field_validated is ALWAYS False. The result label is CONSERVATIVE: FLAT_OPPONENT_FIELD_REPORTING_GENERATED,
or invalid_protocol_breach when a panel is missing or the guard is missing / authorizing. Output is deterministic.
Verdict HOLD; all claim locks False. v1.x remains FROZEN EVIDENCE; v2.x remains an UNVALIDATED conceptual pivot.

stdlib only; no torment_service; no runtime / camera / sensor / live-capture / screen-capture / streaming / prompt
/ context / memory / action / render-body / autonomy contact; no real clips.
"""
from __future__ import annotations

PANELS = ("A_patch_definition", "B_opponent_channel", "C_spatial_relation", "D_region_field",
          "E_temporal_deferral", "F_non_authorizing_guard")

SPATIAL_RELATIONS = ("adjacency", "neighborhood", "gradient", "edge", "continuity_discontinuity")

# v2.2 §8 required non-authorization flags (completeness-enforced; all present and False):
GUARD_FLAGS = ("authorizes_vision", "authorizes_descriptor_validity", "authorizes_temporal_order",
               "authorizes_runtime", "authorizes_memory", "authorizes_integration",
               "authorizes_screen", "authorizes_live", "authorizes_real_clip")

OUTCOME_LABELS = ("FLAT_OPPONENT_FIELD_REPORTING_GENERATED", "invalid_protocol_breach")


def _build_guard():
    g = {k: False for k in GUARD_FLAGS}
    g["guard_present"] = True
    g["statement"] = ("flat opponent-field reporting is diagnostic only; it authorizes no vision, descriptor "
                      "validity, temporal order, runtime, memory, integration, screen, live, or real-clip claim.")
    return g


def _guard_ok(g):
    """Completeness-enforced: guard present, all nine required flags PRESENT and False, and no authorizes_* True.
    A missing OR True required flag -> not ok -> breach."""
    if not isinstance(g, dict) or g.get("guard_present") is not True:
        return False
    if not all(k in g and g[k] is False for k in GUARD_FLAGS):
        return False
    auth_keys = [k for k in g if k.startswith("authorizes_")]
    return bool(auth_keys) and all(g.get(k) is False for k in auth_keys)


def _build_panels():
    panelA = {"obligation": "define what a local opponent patch must conceptually represent (position-indexed "
                            "local opponent content)",
              "reports_conceptual_patch_requirement": True,
              "coordinate_system_adopted": False, "descriptor_adopted": False, "conformant": True}
    panelB = {"obligation": "keep the BY/RG opponent relation explicit (conceptual)",
              "by_rg_relation_explicit": True, "metric_adopted": False, "descriptor_adopted": False,
              "conformant": True}
    panelC = {"obligation": "name the candidate spatial relations to be represented",
              "relations_named": list(SPATIAL_RELATIONS), "equations_adopted": False, "conformant": True}
    panelD = {"obligation": "distinguish local patch effects from field-level organization",
              "local_vs_field_distinguished": True, "pass_fail_rule_adopted": False, "conformant": True}
    panelE = {"obligation": "record that motion/time is deferred and not a first principle",
              "temporal_deferred": True, "temporal_is_first_principle": False, "conformant": True}
    panelF = _build_guard()
    return {"A_patch_definition": panelA, "B_opponent_channel": panelB, "C_spatial_relation": panelC,
            "D_region_field": panelD, "E_temporal_deferral": panelE, "F_non_authorizing_guard": panelF}


def run():
    panels = _build_panels()

    breaches = []
    if set(panels.keys()) != set(PANELS):
        breaches.append("panels_incomplete")
    else:
        if list(panels["C_spatial_relation"].get("relations_named", [])) != list(SPATIAL_RELATIONS):
            breaches.append("spatial_relations_incomplete")
        if panels["A_patch_definition"].get("coordinate_system_adopted") is not False \
                or panels["A_patch_definition"].get("descriptor_adopted") is not False:
            breaches.append("patch_panel_adopted_forbidden")
        if panels["B_opponent_channel"].get("metric_adopted") is not False:
            breaches.append("channel_panel_adopted_metric")
        if panels["C_spatial_relation"].get("equations_adopted") is not False:
            breaches.append("spatial_panel_adopted_equations")
        if panels["D_region_field"].get("pass_fail_rule_adopted") is not False:
            breaches.append("region_panel_adopted_pass_fail")
        if panels["E_temporal_deferral"].get("temporal_is_first_principle") is not False:
            breaches.append("temporal_not_deferred")
        if not _guard_ok(panels["F_non_authorizing_guard"]):
            breaches.append("guard_missing_or_authorizing")

    clean = (len(breaches) == 0)
    obligation_conformance = {}

    if clean:
        obligation_conformance = {k: bool(panels[k].get("conformant", True)) if k != "F_non_authorizing_guard"
                                  else True for k in PANELS}
        outcome_label = "FLAT_OPPONENT_FIELD_REPORTING_GENERATED"
        outcome = ("FLAT_OPPONENT_FIELD_REPORTING_GENERATED: the accepted v2.2 flat opponent-field panels A-F were "
                   "generated as structural/conceptual reporting; nothing is validated, adopted, or closed")
    else:
        outcome_label = "invalid_protocol_breach"
        outcome = "invalid_protocol_breach: " + "; ".join(breaches)

    return {"diagnostic": "v2.3 flat opponent-field audit (form A, NON-LEARNING; REPORTING/guard only; panels A-F "
                          "as structural/conceptual conformance over the v2.2 design; adopts no descriptor/"
                          "coordinate-system/metric/equation/threshold; non-authorizing)",
            "model_form": "A_non_learning_reporting", "learning": False,
            "reporting_only": True, "conceptual_only": True, "offline_only": True,
            "prereg_source": "v2.1a preregistration plan + v2.2 audit design (accepted)",
            "audit_question": "generate the accepted v2.2 flat opponent-field panels A-F as structural reporting",
            "panels": panels, "obligation_conformance": obligation_conformance,
            "flat_field_validated": False,
            "descriptor_adopted": False, "coordinate_system_adopted": False, "metric_adopted": False,
            "equation_adopted": False, "threshold_adopted": False, "pass_fail_validity_rule_adopted": False,
            "tol_redefined": False, "generator_family_expansion_authorized": False,
            "spectral_closure_reopened": False, "flat_geometry_authorized": False,
            "screen_analysis_authorized": False, "runtime_authorized": False, "memory_authorized": False,
            "real_clip_authorized": False, "vision_claim_allowed": False,
            "v1x_status": "frozen_evidence", "v2x_status": "unvalidated_conceptual_pivot",
            "protocol_ok": clean, "breaches": breaches,
            "outcome_label": outcome_label, "outcome": outcome,
            "frozen_brainvision_verdict": "HOLD",
            "first_pass_structure_validity_claim_allowed": False, "temporal_claim_allowed": False,
            "descriptor_validity_claim_allowed": False,
            "vision_claim": False, "memory_readiness_claim": False, "runtime_readiness_claim": False,
            "integration_readiness_claim": False}


if __name__ == "__main__":
    r = run()
    print("model", r["model_form"], "| reporting_only", r["reporting_only"], "| conceptual_only",
          r["conceptual_only"], "| offline_only", r["offline_only"])
    print("audit question:", r["audit_question"])
    print("protocol_ok:", r["protocol_ok"], r["breaches"], "| flat_field_validated:", r["flat_field_validated"])
    print("descriptor_adopted:", r["descriptor_adopted"], "| coordinate_system_adopted:",
          r["coordinate_system_adopted"], "| metric_adopted:", r["metric_adopted"], "| equation_adopted:",
          r["equation_adopted"], "| threshold_adopted:", r["threshold_adopted"],
          "| pass_fail_validity_rule_adopted:", r["pass_fail_validity_rule_adopted"])
    if r["protocol_ok"]:
        print("\nPANELS A-F:")
        for k in PANELS:
            p = r["panels"][k]
            if k == "F_non_authorizing_guard":
                print("  %-24s guard_present=%s  all_flags_False=%s"
                      % (k, p["guard_present"], all(p[f] is False for f in GUARD_FLAGS)))
            else:
                print("  %-24s conformant=%s  obligation=%s..." % (k, p["conformant"], p["obligation"][:48]))
        print("\nobligation_conformance:", r["obligation_conformance"])
    print("\nOUTCOME_LABEL:", r["outcome_label"])
    print("v1x_status:", r["v1x_status"], "| v2x_status:", r["v2x_status"])
    print("verdict:", r["frozen_brainvision_verdict"], "| locks", r["first_pass_structure_validity_claim_allowed"],
          r["temporal_claim_allowed"], r["descriptor_validity_claim_allowed"])
