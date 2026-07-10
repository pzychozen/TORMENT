"""BV BY-aware closure audit v1.5 (offline research; form A; NON-LEARNING; NOT vision).

REPORTING/GUARD IMPLEMENTATION ONLY. It GENERATES the v1.4-preregistered BY-aware closure audit reporting
structure -- the selected A + D + G primary spine with B / C / E report-only support -- over the EXISTING v0.7b /
v0.8a / v0.9b / v1.0b / v1.2 records, reusing the accepted v1.2 audit (run_by_aware_closure_audit_v1_2) BY
IDENTITY and re-expressing its panels under the explicit v1.4 spine framing. It ADDS NO new statistic.

  PRIMARY SPINE (v1.3a-selected, v1.4-preregistered):
    A signed BY offset      : per-BY sign direction + sign consistency + |offset| RELATIVE TO the frozen TOL as a
                              DESCRIPTIVE reference (reused |smd|/TOL by identity); NO offset-vs-TOL gate.
    D aggregation anti-hiding: whether group residual/TOL matching COEXISTS with a systematic BY signed ordering;
                              hidden closure impossible in the reporting; NO validity pass/fail gate.
    G non-authorizing guard : all NINE authorization flags present and False; ANY True -> protocol_ok False.
  SUPPORT (report-only; never a gate):
    B BY/RG opponent-balance | C binding-aware residual partition (residual frozen) | E region/family stratified
    (single-family caveat); plus the coupling/leakage mechanism panel as background context.

It ADOPTS NO closure metric, NO equation, introduces NO pass/fail validity gate, invents NO threshold, REDEFINES
NO TOL, creates NO offset-vs-TOL gate and NO binding gate, changes no evaluator / control, redesigns no
descriptor, reopens no spectral group, expands no family, and adds NO classifier (form B) / neural encoder
(form C). It reruns / replaces NO sample and adds NO seed / family / candidate generation. It does NOT pivot to
flat / screen geometry and does NOT touch runtime / memory / integration / real clips.

protocol_ok means ONLY that the required A + D + G reporting panels and the guard are present -- NOT closure.
closure_achieved is ALWAYS False. The result label is CONSERVATIVE: BY_aware_closure_audit_reporting_complete, or
BY_aware_closure_gap_still_visible when the reused reporting shows the systematic BY offset still survives
residual / TOL matching. NaN / non-finite / breach / an authorizing guard force invalid_protocol_breach via the
reused chain and can never produce closure, a pass, a validity claim, or a claim / verdict movement. Verdict HOLD.

stdlib only; reuses only quarantined research surfaces; no torment_service; no runtime / camera / sensor /
live-capture / screen-capture / streaming / prompt / context / memory / action / render-body / autonomy contact;
no real clips.
"""
from __future__ import annotations

import run_by_channel_metric_anatomy_v0_8a as m8a
import run_by_aware_closure_audit_v1_2 as m12

# ---- reused-by-identity surfaces ----
BY_FEATURES = m8a.BY_FEATURES                       # by_centroid, by_spread, by_std
PANELS = m12.PANELS                                 # frozen seven panel keys (reused by identity)
V11A_GUARD_FLAGS = m12.V11A_GUARD_FLAGS             # nine v1.1a authorization flags (reused by identity)

OUTCOME_LABELS = ("BY_aware_closure_audit_reporting_complete", "BY_aware_closure_gap_still_visible",
                  "invalid_protocol_breach")


def _guard_ok(g):
    """Guard admissible iff diagnostic-only AND every authorizes_* it carries is False (m12 generic check) AND all
    nine v1.1a-required flags are PRESENT and False. A missing OR True required flag -> not ok -> breach."""
    if not m12._guard_ok(g):
        return False
    return all(k in g and g[k] is False for k in V11A_GUARD_FLAGS)   # completeness: all nine present and False


def run():
    c = m12.run()                                                    # accepted v1.2 audit; reuse chain to v0.7b by identity

    breaches = list(c.get("breaches", []) or [])
    if c.get("outcome_label") == "invalid_protocol_breach":
        breaches.append("v1_2_breach")
    if not c.get("protocol_ok"):
        breaches.append("v1_2_protocol_not_ok")
    if not c.get("reuses_v0_7b_v0_8a_v0_9b_records"):
        breaches.append("v1_2_does_not_reproduce_v0_7b")
    if c.get("closure_achieved") is not False:
        breaches.append("closure_achieved_not_false")
    src_panels = c.get("panels") or {}
    if set(src_panels.keys()) != set(PANELS):
        breaches.append("v1_2_panels_incomplete")
    elif not _guard_ok(src_panels.get("G_non_authorizing_visibility")):
        breaches.append("guard_missing_or_authorizing")

    clean = (len(breaches) == 0)
    primary_spine, support_reporting, reporting_obligations, panels = {}, {}, {}, {}
    by_wall_persists = False
    outcome_label, outcome = None, None

    if clean:
        A = src_panels["A_signed_offset"]                            # signed BY offset (+ magnitude_frac_TOL, offset_vs_tol_gate False)
        D = src_panels["F_residual_aggregation_warning"]             # aggregation coexistence (+ hidden_closure_claim False)
        G = src_panels["G_non_authorizing_visibility"]               # guard: nine flags all False, diagnostic-only
        B = src_panels["B_by_vs_rg_dominance"]                       # support: BY/RG opponent balance
        Cpanel = src_panels["C_binding_stat"]                        # support: binding-aware (binding_gate_introduced False)
        E = src_panels["D_region_family"]                            # support: region/family (family_expansion_authorized False)
        CL = src_panels["E_coupling_leakage_separation"]            # background: coupling/leakage mechanism context

        panels = dict(src_panels)                                    # keep the frozen seven panels by identity

        primary_spine = {
            "A_signed_offset": A,
            "D_aggregation_anti_hiding": D,
            "G_non_authorizing_guard": G}

        support_reporting = {
            "B_by_rg_opponent_balance": B,
            "C_binding_aware_partition": Cpanel,
            "E_region_family_stratified": E,
            "coupling_leakage_background": CL,
            "support_only": True,
            "promoted_to_gate": False}

        reporting_obligations = {
            "primary": {
                "A_signed_offset": {
                    "frozen_panel": "A_signed_offset", "reports_by_features": list(BY_FEATURES),
                    "reports_sign_direction": True, "reports_sign_consistency": True,
                    "reports_magnitude_frac_TOL": True, "offset_vs_tol_gate": False},
                "D_aggregation_anti_hiding": {
                    "frozen_panel": "F_residual_aggregation_warning",
                    "reports_residual_tol_coexistence_with_by_ordering": True,
                    "hidden_closure_claim": False, "validity_pass_fail_gate": False},
                "G_non_authorizing_guard": {k: False for k in V11A_GUARD_FLAGS}},
            "support_report_only": {
                "B_by_rg_opponent_balance": {"frozen_panel": "B_by_vs_rg_dominance", "report_only": True, "is_gate": False},
                "C_binding_aware_partition": {"frozen_panel": "C_binding_stat", "report_only": True, "is_gate": False,
                                              "residual_redefined": False},
                "E_region_family_stratified": {"frozen_panel": "D_region_family", "report_only": True, "is_gate": False,
                                               "generator_family_expansion_authorized": False},
                "coupling_leakage_background": {"frozen_panel": "E_coupling_leakage_separation", "report_only": True,
                                                "is_gate": False}}}

        by_wall_persists = bool(c.get("by_wall_persists"))           # reused from v1.2 (deterministic; NOT recomputed)

        if by_wall_persists:
            outcome_label = "BY_aware_closure_gap_still_visible"
            outcome = ("BY_aware_closure_gap_still_visible: the preregistered A + D + G reporting was generated and "
                       "shows the systematic BY opponent-axis offset still survives residual/TOL matching (signed, "
                       "sign-consistent, BY-dominant, often-binding, aggregation-warning) -- the wall is VISIBLE, "
                       "NOT CLOSED (single matching family caveat preserved)")
        else:
            outcome_label = "BY_aware_closure_audit_reporting_complete"
            outcome = ("BY_aware_closure_audit_reporting_complete: the preregistered A + D + G reporting was "
                       "generated; it does not assert the BY gap and closes nothing")
    else:
        outcome_label = "invalid_protocol_breach"
        outcome = "invalid_protocol_breach: " + "; ".join(breaches)

    return {"diagnostic": "v1.5 BY-aware closure audit (form A, NON-LEARNING; REPORTING/guard only; v1.4-"
                          "preregistered A + D + G spine, B/C/E report-only; reuses v1.2 by identity; adopts no "
                          "metric/equation/threshold/pass-fail/gate; non-authorizing)",
            "model_form": "A_non_learning_reporting", "learning": False, "reporting_only": True,
            "prereg_source": "v1.4 preregistration (accepted) on the v1.3a-selected A + D + G spine; B/C/E report-only",
            "audit_question": "generate the preregistered A + D + G BY-aware reporting; does the BY wall still persist?",
            "reuses_v0_7b_v0_8a_v0_9b_v1_0b_v1_2_records": bool(c.get("reuses_v0_7b_v0_8a_v0_9b_records")) and clean,
            "reuses_v1_2_by_identity": clean,
            "TOL": c.get("TOL"), "tol_redefined": False, "TOL_redefined": False, "new_threshold_introduced": False,
            "new_closure_metric_adopted": False, "pass_fail_gate_introduced": False,
            "offset_vs_tol_gate": False, "binding_gate": False, "validity_pass_fail_gate": False,
            "closure_achieved": False, "by_wall_persists": by_wall_persists,
            "new_family_or_axis": False, "generator_family_expansion_authorized": False,
            "descriptor_redesign_authorized": False, "spectral_closure_reopened": False,
            "spectral_role": "audit-note-only (NOT reopened)",
            "flat_geometry_authorized": False, "screen_analysis_authorized": False,
            "runtime_authorized": False, "memory_authorized": False, "vision_claim_allowed": False,
            "visibility_is_non_authorizing": True,
            "primary_spine": primary_spine, "support_reporting": support_reporting,
            "reporting_obligations": reporting_obligations, "panels": panels,
            "protocol_ok": clean, "breaches": breaches,
            "outcome_label": outcome_label, "outcome": outcome,
            "frozen_brainvision_verdict": "HOLD",
            "first_pass_structure_validity_claim_allowed": False, "temporal_claim_allowed": False,
            "descriptor_validity_claim_allowed": False,
            "vision_claim": False, "memory_readiness_claim": False, "runtime_readiness_claim": False,
            "integration_readiness_claim": False}


if __name__ == "__main__":
    r = run()
    print("model", r["model_form"], "| reporting_only", r["reporting_only"], "| TOL", r["TOL"],
          "(redefined=%s)" % r["tol_redefined"])
    print("audit question:", r["audit_question"])
    print("reuses v0.7b/v0.8a/v0.9b/v1.0b/v1.2 records:", r["reuses_v0_7b_v0_8a_v0_9b_v1_0b_v1_2_records"],
          "| protocol_ok:", r["protocol_ok"], r["breaches"])
    print("new_closure_metric_adopted:", r["new_closure_metric_adopted"],
          "| pass_fail_gate_introduced:", r["pass_fail_gate_introduced"],
          "| offset_vs_tol_gate:", r["offset_vs_tol_gate"], "| binding_gate:", r["binding_gate"],
          "| closure_achieved:", r["closure_achieved"])
    if r["protocol_ok"]:
        S = r["primary_spine"]
        print("\nPRIMARY SPINE A + D + G:")
        A = S["A_signed_offset"]
        print("  A signed-offset (offset_vs_tol_gate=%s):" % A["offset_vs_tol_gate"])
        for s in BY_FEATURES:
            d = A[s]
            print("     %-12s offset=%+.5f  sign_consistency=%.2f  dominant=%s  |offset|/TOL=%.2f"
                  % (s, d["signed_offset"], d["sign_consistency"], d["dominant_sign"], d["magnitude_frac_TOL"]))
        Dp = S["D_aggregation_anti_hiding"]
        print("  D aggregation coexistence:", Dp["aggregation_warning"], "| hidden_closure_claim:", Dp["hidden_closure_claim"])
        Gp = S["G_non_authorizing_guard"]
        print("  G guard diagnostic-only:", Gp["visibility_is_diagnostic_only"], "| authorizes_closure:", Gp["authorizes_closure"],
              "| all nine False:", all(Gp[k] is False for k in V11A_GUARD_FLAGS))
        sup = r["support_reporting"]
        print("SUPPORT (report-only=%s, gate=%s): B by_dominant=%s | C binding_gate=%s | E single_family_caveat=%s"
              % (sup["support_only"], sup["promoted_to_gate"], sup["B_by_rg_opponent_balance"]["by_dominant_over_rg"],
                 sup["C_binding_aware_partition"]["binding_gate_introduced"],
                 sup["E_region_family_stratified"]["single_matching_family_caveat"]))
        print("by_wall_persists:", r["by_wall_persists"])
    print("\nOUTCOME_LABEL:", r["outcome_label"])
    print("closure_achieved:", r["closure_achieved"], "| verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"],
          r["descriptor_validity_claim_allowed"])
