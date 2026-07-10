"""BV BY-aware closure audit v1.0b (offline research; form A; NON-LEARNING; NOT vision).

REPORTING-ONLY. It implements the v1.0a BY-aware closure audit panels A-G over the EXISTING v0.7b / v0.8a / v0.9b
records, so the systematic blue-yellow opponent-axis offset (BY_axis_asymmetry) is made explicitly visible AND
the audit itself records that this visibility is diagnostic-only (panel G, requirement G of v1.0). It reuses the
v0.9b visibility audit (which reproduces the v0.7b sealed matching BY IDENTITY via v0.8a) and re-presents its
panels A-F plus the new non-authorizing panel G. It ADOPTS NO new closure metric, introduces NO pass/fail gate,
invents NO threshold, REDEFINES NO TOL, changes no evaluator / control, redesigns no descriptor, reopens no
spectral group, expands no family, and adds NO classifier (form B) / neural encoder (form C). It reruns /
replaces NO sample and adds NO seed / family / candidate generation. It does NOT pivot to flat / screen geometry.

The panels PRESENT the offset and record that its visibility is diagnostic-only; they DECIDE nothing. The
visibility outcome (confirmed / partial / inconclusive) is a REPORTING label -- NOT a Brainvision pass, NOT a
closure decision -- and it moves NO claim lock and NO verdict (verdict stays HOLD). NaN / non-finite / extreme
values are not admissible evidence: they force invalid_protocol_breach and can never produce a visibility
confirmation, closure, pass/fail, validity claim, or claim movement.

stdlib only; reuses only quarantined research surfaces; no torment_service; no runtime / camera / sensor /
live-capture / screen-capture / streaming / prompt / context / memory / action / render-body / autonomy contact;
no real clips.
"""
from __future__ import annotations

import run_by_channel_metric_anatomy_v0_8a as m8a
import run_by_opponent_axis_closure_audit_v0_9b as m9b

# ---- reused-by-identity surfaces ----
BY_FEATURES = m8a.BY_FEATURES

AF_PANELS = ("A_signed_offset", "B_by_vs_rg_dominance", "C_binding_stat", "D_region_family",
             "E_coupling_leakage_separation", "F_residual_aggregation_warning")

OUTCOME_LABELS = ("BY_aware_visibility_confirmed", "BY_aware_visibility_partial",
                  "BY_aware_visibility_inconclusive", "invalid_protocol_breach")

# panel G (requirement G): BY visibility is DIAGNOSTIC ONLY and authorizes nothing.
NON_AUTHORIZING_PANEL = {
    "visibility_is_diagnostic_only": True,
    "authorizes_descriptor_validity": False, "authorizes_pass_fail": False, "authorizes_closure": False,
    "authorizes_runtime": False, "authorizes_memory": False, "authorizes_integration": False,
    "authorizes_vision": False, "authorizes_flat_geometry": False, "authorizes_screen_analysis": False,
    "statement": ("BY visibility is diagnostic only; it authorizes no descriptor validity, no pass/fail, no "
                  "closure, no runtime / memory / integration, and no vision claim.")}


def run():
    v = m9b.run()                                                    # v0.9b: panels A-F; reproduces v0.7b by identity

    breaches = list(v.get("breaches", []) or [])
    if v.get("outcome_label") == "invalid_protocol_breach":
        breaches.append("v0_9b_breach")
    if not v.get("protocol_ok"):
        breaches.append("v0_9b_protocol_not_ok")
    if not v.get("reuses_v0_8a_reproduces_v0_7b"):
        breaches.append("v0_9b_does_not_reproduce_v0_7b")
    # the A-F panels must be present and non-empty (reused from v0.9b)
    af = v.get("panels") or {}
    if set(af.keys()) != set(AF_PANELS):
        breaches.append("v0_9b_panels_incomplete")

    clean = (len(breaches) == 0)
    panels, outcome_label, outcome = {}, None, None

    if clean:
        panels = dict(af)                                            # A-F re-presented by identity
        panels["G_non_authorizing_visibility"] = dict(NON_AUTHORIZING_PANEL)

        vis = v["outcome_label"]
        if vis == "BY_visibility_confirmed" and all(v.get("offset_visibility_criteria", {}).values()):
            outcome_label = "BY_aware_visibility_confirmed"
            outcome = ("BY_aware_visibility_confirmed: panels A-G make the systematic BY opponent-axis offset "
                       "explicitly visible and record (G) that the visibility is diagnostic-only "
                       "(single matching family caveat preserved)")
        elif vis == "BY_visibility_partial":
            outcome_label = "BY_aware_visibility_partial"
            outcome = "BY_aware_visibility_partial: some panels surface the BY offset while others are limited"
        else:
            outcome_label = "BY_aware_visibility_inconclusive"
            outcome = "BY_aware_visibility_inconclusive: the panels do not surface the BY offset from these records"
    else:
        outcome_label = "invalid_protocol_breach"
        outcome = "invalid_protocol_breach: " + "; ".join(breaches)

    return {"diagnostic": "v1.0b BY-aware closure audit (form A, NON-LEARNING; REPORTING-only; panels A-G over "
                          "reused v0.7b/v0.8a/v0.9b records; adopts no metric, no pass/fail gate; non-authorizing)",
            "model_form": "A_non_learning_reporting", "learning": False, "reporting_only": True,
            "audit_question": "inspect whether residual/TOL leaves systematic BY_axis_asymmetry visible; diagnostic-only",
            "reuses_v0_7b_v0_8a_v0_9b_records": bool(v.get("reuses_v0_8a_reproduces_v0_7b")),
            "TOL": v.get("TOL"), "TOL_redefined": False, "new_threshold_introduced": False,
            "new_closure_metric_adopted": False, "pass_fail_gate_introduced": False,
            "new_family_or_axis": False, "spectral_role": "audit-note-only (NOT reopened)",
            "visibility_is_non_authorizing": True,
            "panels": panels, "protocol_ok": clean, "breaches": breaches,
            "outcome_label": outcome_label, "outcome": outcome,
            "frozen_brainvision_verdict": "HOLD",
            "first_pass_structure_validity_claim_allowed": False, "temporal_claim_allowed": False,
            "descriptor_validity_claim_allowed": False,
            "vision_claim": False, "memory_readiness_claim": False, "runtime_readiness_claim": False,
            "integration_readiness_claim": False}


if __name__ == "__main__":
    r = run()
    print("model", r["model_form"], "| reporting_only", r["reporting_only"], "| TOL", r["TOL"], "(redefined=%s)" % r["TOL_redefined"])
    print("audit question:", r["audit_question"])
    print("reuses v0.7b/v0.8a/v0.9b records:", r["reuses_v0_7b_v0_8a_v0_9b_records"], "| protocol_ok:", r["protocol_ok"], r["breaches"])
    print("new_closure_metric_adopted:", r["new_closure_metric_adopted"], "| pass_fail_gate_introduced:", r["pass_fail_gate_introduced"],
          "| visibility_is_non_authorizing:", r["visibility_is_non_authorizing"])
    if r["protocol_ok"]:
        P = r["panels"]
        print("\npanels present:", list(P.keys()))
        print("A signed-offset:")
        for s in BY_FEATURES:
            d = P["A_signed_offset"][s]
            print("   %-12s offset=%+.5f  sign_consistency=%.2f  dominant=%s" % (s, d["signed_offset"], d["sign_consistency"], d["dominant_sign"]))
        print("B BY-vs-RG dominance:", P["B_by_vs_rg_dominance"]["by_dominant_over_rg"])
        print("C binding:", P["C_binding_stat"]["by_binding_by_feature"], "| frac:", P["C_binding_stat"]["by_binding_fraction"], "| above_share:", P["C_binding_stat"]["by_binds_above_share"])
        print("D region:", {k: vv["by_centroid_BA"] for k, vv in P["D_region_family"]["region_by_persistence"].items()},
              "| single_family_caveat:", P["D_region_family"]["single_matching_family_caveat"])
        print("E dominant_mechanism:", P["E_coupling_leakage_separation"]["dominant_mechanism"])
        print("F aggregation_warning:", P["F_residual_aggregation_warning"]["aggregation_warning"])
        print("G non-authorizing:", P["G_non_authorizing_visibility"]["visibility_is_diagnostic_only"],
              "| authorizes_descriptor_validity:", P["G_non_authorizing_visibility"]["authorizes_descriptor_validity"])
    print("\nOUTCOME_LABEL:", r["outcome_label"])
    print("verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"], r["descriptor_validity_claim_allowed"])
