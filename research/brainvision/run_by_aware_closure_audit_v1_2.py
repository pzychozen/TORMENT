"""BV BY-aware closure audit v1.2 (offline research; form A; NON-LEARNING; NOT vision).

REPORTING-ONLY. It GENERATES the preregistered BY-aware reporting obligations (v1.1 proposal, accepted; v1.1a
plan, accepted; panels A-G) as DIAGNOSTIC OUTPUT ONLY over the EXISTING v0.7b / v0.8a / v0.9b / v1.0b records. It
reuses the v1.0b audit (which reuses v0.9b -> v0.8a -> the v0.7b sealed matching BY IDENTITY) and re-presents its
panels A-G under the v1.1a obligation framing, adding only the obligation-guard annotations the plan requires:
  A signed-offset : per-BY sign direction + sign consistency + |offset| RELATIVE TO the frozen TOL as a
                    DESCRIPTIVE effect-size reference (reused |smd|/TOL, BY IDENTITY), with NO offset-vs-TOL gate;
  B BY dominance  : BY effects compared against RG and directional features, as VISIBILITY EVIDENCE ONLY;
  C binding       : whether BY stats (esp. by_std) bind the residual match, vs proportional share; NO binding gate;
  D aggregation   : whether per-pair residual/TOL closure COEXISTS with a systematic BY ordering; NO hidden closure;
  E coupling/leak : BY_axis_asymmetry kept SEPARATE from centroid/spread coupling and amplitude leakage;
  F region/family : single-matching-family caveat + per-region BY visibility; NO generator-family expansion;
  G guard         : all authorization flags present and False (diagnostic-only).
(NB: panel KEYS keep the frozen v0.9b/v1.0b names -- D_region_family, F_residual_aggregation_warning -- while the
v1.1a obligation LETTERS use D=aggregation, F=region/family. The mapping is spelled out in reporting_obligations.)

It ADOPTS NO new closure metric, NO equation, introduces NO pass/fail gate, invents NO threshold, REDEFINES NO
TOL, changes no evaluator / control, redesigns no descriptor, reopens no spectral group, expands no family, and
adds NO classifier (form B) / neural encoder (form C). It reruns / replaces NO sample and adds NO seed / family /
candidate generation. It does NOT pivot to flat / screen geometry and does NOT touch runtime / memory /
integration / real clips.

The panels PRESENT the offset and record that its visibility is diagnostic-only; they DECIDE nothing. The result
label is CONSERVATIVE: BY_aware_closure_reporting_generated (panels + guards generated) or, when the reporting
reveals the systematic BY offset still survives residual / TOL matching, BY_aware_closure_gap_visible. NEITHER is
a closure -- closure_achieved is ALWAYS False. NaN / non-finite / extreme values are inadmissible: they force
invalid_protocol_breach via the reused chain and can never produce a confirmation, closure, pass/fail, validity
claim, or claim movement. Verdict stays HOLD.

stdlib only; reuses only quarantined research surfaces; no torment_service; no runtime / camera / sensor /
live-capture / screen-capture / streaming / prompt / context / memory / action / render-body / autonomy contact;
no real clips.
"""
from __future__ import annotations

import run_by_channel_metric_anatomy_v0_8a as m8a
import run_by_opponent_axis_closure_audit_v0_9b as m9b
import run_by_aware_closure_audit_v1_0b as m10b

# ---- reused-by-identity surfaces ----
BY_FEATURES = m8a.BY_FEATURES                       # by_centroid, by_spread, by_std
CHANCE_SIGN = m9b.CHANCE_SIGN                        # 0.5 natural reference (REUSED; NOT a new threshold)

PANELS = ("A_signed_offset", "B_by_vs_rg_dominance", "C_binding_stat", "D_region_family",
          "E_coupling_leakage_separation", "F_residual_aggregation_warning", "G_non_authorizing_visibility")

# v1.1a §7 requires these NINE authorization flags on guard G (all False):
V11A_GUARD_FLAGS = ("authorizes_descriptor_validity", "authorizes_temporal_order", "authorizes_pass_fail",
                    "authorizes_closure", "authorizes_runtime", "authorizes_memory", "authorizes_integration",
                    "authorizes_live_or_screen_use", "authorizes_vision")
# extras carried from the upstream v1.0b guard -- KEPT, but NOT substitutes for the nine v1.1a-required flags:
EXTRA_GUARD_FLAGS = ("authorizes_flat_geometry", "authorizes_screen_analysis")

OUTCOME_LABELS = ("BY_aware_closure_reporting_generated", "BY_aware_closure_gap_visible",
                  "invalid_protocol_breach")


def _guard_ok(g):
    """Upstream guard is admissible iff it is diagnostic-only and EVERY authorizes_* flag it carries is False.
    Generic over the flag name, so ANY authorizing flag (incl. temporal_order / live_or_screen_use) breaches."""
    if not g or g.get("visibility_is_diagnostic_only") is not True:
        return False
    auth_keys = [k for k in g if k.startswith("authorizes_")]
    return bool(auth_keys) and all(g.get(k) is False for k in auth_keys)


def run():
    b = m10b.run()                                                   # v1.0b: panels A-G; reuse chain to v0.7b by identity

    breaches = list(b.get("breaches", []) or [])
    if b.get("outcome_label") == "invalid_protocol_breach":
        breaches.append("v1_0b_breach")
    if not b.get("protocol_ok"):
        breaches.append("v1_0b_protocol_not_ok")
    if not b.get("reuses_v0_7b_v0_8a_v0_9b_records"):
        breaches.append("v1_0b_does_not_reproduce_v0_7b")
    src_panels = b.get("panels") or {}
    if set(src_panels.keys()) != set(PANELS):
        breaches.append("v1_0b_panels_incomplete")
    elif not _guard_ok(src_panels.get("G_non_authorizing_visibility")):
        breaches.append("guard_missing_or_authorizing")

    clean = (len(breaches) == 0)
    panels, obligations, gap_criteria = {}, {}, {}
    by_wall_persists = False

    if clean:
        A = src_panels["A_signed_offset"]
        B = src_panels["B_by_vs_rg_dominance"]
        C = src_panels["C_binding_stat"]
        D = src_panels["D_region_family"]
        E = src_panels["E_coupling_leakage_separation"]
        F = src_panels["F_residual_aggregation_warning"]
        # rebuild guard G so v1.2 EXPOSES all nine v1.1a-required flags (+ the two v1.0b extras), all False
        # (admissibility already checked above via _guard_ok: construction is reached only when upstream is clean)
        G = {k: False for k in V11A_GUARD_FLAGS + EXTRA_GUARD_FLAGS}
        G["visibility_is_diagnostic_only"] = True
        G["statement"] = ("BY-aware reporting is diagnostic only; it authorizes no descriptor validity, no "
                          "temporal order, no pass/fail, no closure, no runtime / memory / integration, no "
                          "live / screen use, and no vision claim.")

        # --- Obligation A: signed-offset + |offset| RELATIVE TO frozen TOL (DESCRIPTIVE), NO offset-vs-TOL gate ---
        mag_frac_TOL = B["by_effects_frac_TOL"]                      # |smd|/TOL for BY features, reused BY IDENTITY
        panelA = {s: {"signed_offset": A[s]["signed_offset"], "sign_consistency": A[s]["sign_consistency"],
                      "dominant_sign": A[s]["dominant_sign"], "magnitude_frac_TOL": mag_frac_TOL[s]}
                  for s in BY_FEATURES}
        panelA["mean_sign_consistency"] = A["mean_sign_consistency"]
        panelA["offset_vs_tol_gate"] = False                         # magnitude is DESCRIPTIVE; NOT a pass/fail

        # --- Obligation C: binding esp. by_std, reported vs share; NO binding gate ---
        panelC = dict(C)
        panelC["binding_gate_introduced"] = False

        # --- Obligation F (frozen key D_region_family): single-family caveat + region visibility; NO family expansion ---
        panelD = dict(D)
        panelD["generator_family_expansion_authorized"] = False

        # --- Obligation D (frozen key F_residual_aggregation_warning): coexistence reported; NO hidden closure ---
        panelF = dict(F)
        panelF["hidden_closure_claim"] = False

        panels = {"A_signed_offset": panelA, "B_by_vs_rg_dominance": B, "C_binding_stat": panelC,
                  "D_region_family": panelD, "E_coupling_leakage_separation": E,
                  "F_residual_aggregation_warning": panelF, "G_non_authorizing_visibility": G}

        # explicit v1.1a obligation -> reporting mapping (letters follow the plan; keys note the frozen panel)
        obligations = {
            "A_signed_offset_reporting": {
                "frozen_panel": "A_signed_offset", "by_features": list(BY_FEATURES),
                "reports_sign_direction": True, "reports_sign_consistency": True,
                "reports_magnitude_frac_TOL": True, "offset_vs_tol_gate": False},
            "B_by_dominance_reporting": {
                "frozen_panel": "B_by_vs_rg_dominance",
                "compared_against_rg": True, "compared_against_directional": True,
                "visibility_evidence_only": True},
            "C_binding_reporting": {
                "frozen_panel": "C_binding_stat",
                "reports_by_binding": True, "by_std_separated": True, "binding_gate": False},
            "D_aggregation_warning_reporting": {
                "frozen_panel": "F_residual_aggregation_warning",
                "reports_residual_tol_coexistence_with_by_ordering": True, "hidden_closure_claim": False},
            "E_coupling_leakage_separation": {
                "frozen_panel": "E_coupling_leakage_separation",
                "axis_asymmetry_separated_from_coupling": True,
                "axis_asymmetry_separated_from_amplitude": True},
            "F_region_family_caveat": {
                "frozen_panel": "D_region_family",
                "single_matching_family_caveat": bool(panelD.get("single_matching_family_caveat")),
                "target_region_visibility": bool(len(D.get("region_by_persistence", {})) > 0),
                "generator_family_expansion_authorized": False},
            "G_non_authorizing_guard": {k: False for k in V11A_GUARD_FLAGS}}

        # conservative gap criteria: is the BY wall STILL VISIBLE under the reporting? (reused booleans; NOT a gate)
        gap_criteria = {
            "A_signed_and_systematic": all(panelA[s]["sign_consistency"] > CHANCE_SIGN for s in BY_FEATURES),
            "B_by_dominant": bool(B["by_dominant_over_rg"]),
            "C_by_binds_above_share": bool(panelC["by_binds_above_share"]),
            "E_axis_asymmetry_dominant": bool(E["dominant_mechanism"] == "BY_axis_asymmetry"),
            "F_aggregation_warning": bool(panelF["aggregation_warning"]),
            "D_region_reported": bool(len(D.get("region_by_persistence", {})) > 0)}
        by_wall_persists = all(gap_criteria.values())

        if by_wall_persists:
            outcome_label = "BY_aware_closure_gap_visible"
            outcome = ("BY_aware_closure_gap_visible: the preregistered A-G reporting reveals the systematic BY "
                       "opponent-axis offset still survives residual/TOL matching (signed, sign-consistent, "
                       "BY-dominant, often-binding, aggregation-warning) -- the wall is VISIBLE, NOT CLOSED "
                       "(single matching family caveat preserved)")
        else:
            outcome_label = "BY_aware_closure_reporting_generated"
            outcome = ("BY_aware_closure_reporting_generated: the preregistered A-G reporting was produced; it "
                       "does not assert the BY gap and closes nothing")
    else:
        outcome_label = "invalid_protocol_breach"
        outcome = "invalid_protocol_breach: " + "; ".join(breaches)

    return {"diagnostic": "v1.2 BY-aware closure audit (form A, NON-LEARNING; REPORTING-only; preregistered "
                          "panels A-G over reused v0.7b/v0.8a/v0.9b/v1.0b records; adopts no metric/equation/"
                          "threshold/pass-fail; non-authorizing)",
            "model_form": "A_non_learning_reporting", "learning": False, "reporting_only": True,
            "prereg_source": "v1.1 proposal (accepted) + v1.1a plan (accepted)",
            "audit_question": "generate the preregistered BY-aware A-G reporting; does the BY wall persist under it?",
            "reuses_v0_7b_v0_8a_v0_9b_records": bool(b.get("reuses_v0_7b_v0_8a_v0_9b_records")),
            "reuses_v1_0b_panels": clean,
            "TOL": b.get("TOL"), "tol_redefined": False, "TOL_redefined": False, "new_threshold_introduced": False,
            "new_closure_metric_adopted": False, "pass_fail_gate_introduced": False,
            "closure_achieved": False, "by_wall_persists": by_wall_persists,
            "new_family_or_axis": False, "generator_family_expansion_authorized": False,
            "descriptor_redesign_authorized": False, "spectral_closure_reopened": False,
            "spectral_role": "audit-note-only (NOT reopened)",
            "flat_geometry_authorized": False, "screen_analysis_authorized": False,
            "runtime_authorized": False, "memory_authorized": False, "vision_claim_allowed": False,
            "visibility_is_non_authorizing": True,
            "panels": panels, "reporting_obligations": obligations, "gap_criteria": gap_criteria,
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
    print("reuses v0.7b/v0.8a/v0.9b/v1.0b records:", r["reuses_v0_7b_v0_8a_v0_9b_records"],
          "| protocol_ok:", r["protocol_ok"], r["breaches"])
    print("new_closure_metric_adopted:", r["new_closure_metric_adopted"],
          "| pass_fail_gate_introduced:", r["pass_fail_gate_introduced"],
          "| closure_achieved:", r["closure_achieved"],
          "| visibility_is_non_authorizing:", r["visibility_is_non_authorizing"])
    if r["protocol_ok"]:
        P = r["panels"]
        print("\npanels present:", list(P.keys()))
        print("A signed-offset (with |offset|/TOL, DESCRIPTIVE; offset_vs_tol_gate=%s):" % P["A_signed_offset"]["offset_vs_tol_gate"])
        for s in BY_FEATURES:
            d = P["A_signed_offset"][s]
            print("   %-12s offset=%+.5f  sign_consistency=%.2f  dominant=%s  |offset|/TOL=%.2f"
                  % (s, d["signed_offset"], d["sign_consistency"], d["dominant_sign"], d["magnitude_frac_TOL"]))
        print("B BY-vs-RG dominance:", P["B_by_vs_rg_dominance"]["by_dominant_over_rg"], "(visibility evidence only)")
        print("C binding:", P["C_binding_stat"]["by_binding_by_feature"], "| above_share:",
              P["C_binding_stat"]["by_binds_above_share"], "| binding_gate_introduced:",
              P["C_binding_stat"]["binding_gate_introduced"])
        print("D(aggregation) warning:", P["F_residual_aggregation_warning"]["aggregation_warning"],
              "| hidden_closure_claim:", P["F_residual_aggregation_warning"]["hidden_closure_claim"])
        print("E dominant_mechanism:", P["E_coupling_leakage_separation"]["dominant_mechanism"])
        print("F(region/family) single_family_caveat:", P["D_region_family"]["single_matching_family_caveat"],
              "| generator_family_expansion_authorized:", P["D_region_family"]["generator_family_expansion_authorized"])
        print("G non-authorizing:", P["G_non_authorizing_visibility"]["visibility_is_diagnostic_only"],
              "| authorizes_closure:", P["G_non_authorizing_visibility"]["authorizes_closure"])
        print("\ngap_criteria:", r["gap_criteria"], "| by_wall_persists:", r["by_wall_persists"])
    print("\nOUTCOME_LABEL:", r["outcome_label"])
    print("closure_achieved:", r["closure_achieved"], "| verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"],
          r["descriptor_validity_claim_allowed"])
