"""BV BY opponent-axis closure visibility audit v0.9b (offline research; form A; NON-LEARNING; NOT vision).

REPORTING-ONLY. It implements the v0.9a visibility panels A-F over the EXISTING v0.7b / v0.8a records, so the
systematic blue-yellow opponent-axis offset (BY_axis_asymmetry) is made EXPLICITLY VISIBLE. It is not corrective:
it does NOT try to make Brainvision pass or close BY. It reuses the v0.8a anatomy (which reproduces the v0.7b
sealed matching BY IDENTITY) and only re-presents its quantities as dedicated visibility panels. It ADOPTS NO
new closure metric, introduces NO pass/fail gate, invents NO threshold, REDEFINES NO TOL, changes no evaluator /
control, redesigns no descriptor, reopens no spectral group, expands no family, and adds NO classifier (form B) /
neural encoder (form C). It reruns / replaces NO v0.7b sample, adds NO seed / family / candidate generation.

The visibility panels only PRESENT the offset; they DECIDE nothing with it. The visibility outcome
(confirmed / partial / inconclusive) is a REPORTING label about whether the panels surface the offset -- it is
NOT a Brainvision pass, NOT a closure decision, and it moves NO claim lock and NO verdict (verdict stays HOLD).
Confirmation uses only natural references (sign consistency vs the chance level 0.5; BY binding vs its
proportional share of the ten matched stats) and reused v0.8a booleans -- no new numeric threshold. NaN /
non-finite / extreme values are not admissible evidence: they force invalid_protocol_breach and can never
produce a visibility confirmation, closure, validity claim, or claim movement.

stdlib only; reuses only quarantined research surfaces; no torment_service; no runtime / camera / sensor /
live-capture / screen-capture / streaming / prompt / context / memory / action / render-body / autonomy contact;
no real clips.
"""
from __future__ import annotations

import run_matched_generative_search_v0_4d as m4d
import run_by_channel_metric_anatomy_v0_8a as m8a

# ---- reused-by-identity surfaces ----
BY_FEATURES = m8a.BY_FEATURES                      # by_centroid, by_spread, by_std
RG_FEATURES = m8a.RG_FEATURES
DIRECTIONAL_FEATURES = m8a.DIRECTIONAL_FEATURES
MATCHED_STATS = m4d.MATCHED_STATS
_is_clean = m4d._is_clean

CHANCE_SIGN = 0.5                                  # natural reference: random sign fraction (NOT a new threshold)

OUTCOME_LABELS = ("BY_visibility_confirmed", "BY_visibility_partial", "BY_visibility_inconclusive",
                  "invalid_protocol_breach")


def run():
    a = m8a.run()                                                    # reproduces v0.7b by identity; computes panel quantities

    breaches = []
    if not a.get("reproduces_v0_7b"):
        breaches.append("does_not_reproduce_v0_7b")
    if a.get("outcome_label") == "invalid_protocol_breach":
        breaches.append("v0_8a_breach")
    if not a.get("protocol_ok"):
        breaches.append("v0_8a_protocol_not_ok")

    by_share = round(len([s for s in BY_FEATURES if s in MATCHED_STATS]) / len(MATCHED_STATS), 4)
    panels, offset_criteria = {}, {}

    # required panel values must be finite (non-finite is not admissible evidence)
    if not breaches:
        required = []
        for s in BY_FEATURES:
            required += [a["by_signed_difference"][s]["sign_consistency"], a["by_signed_difference"][s]["median_diff"]]
        required += [a["by_binding_fraction"], a["centroid_spread_coupling_spearman"]]
        required += list(a["by_std_amplitude_spearman"].values())
        if not all(_is_clean(v) for v in required):
            breaches.append("nonfinite_panel_value")

    clean = (len(breaches) == 0)

    if clean:
        mean_sc = a["mean_by_sign_consistency"]

        # --- Panel A: signed-offset ---
        panelA = {s: {"signed_offset": a["by_signed_difference"][s]["median_diff"],
                      "sign_consistency": a["by_signed_difference"][s]["sign_consistency"],
                      "dominant_sign": a["by_signed_difference"][s]["dominant_sign"]} for s in BY_FEATURES}
        panelA["mean_sign_consistency"] = mean_sc

        # --- Panel B: BY-vs-RG dominance ---
        panelB = {"by_effects_frac_TOL": {s: a["by_vs_rg"][s]["abs_effect_frac_TOL"] for s in BY_FEATURES},
                  "rg_effects_frac_TOL": {s: a["by_vs_rg"][s]["abs_effect_frac_TOL"] for s in RG_FEATURES},
                  "directional_effects_frac_TOL": {s: a["by_vs_rg"][s]["abs_effect_frac_TOL"] for s in DIRECTIONAL_FEATURES},
                  "by_dominant_over_rg": a["by_dominant_over_rg"]}

        # --- Panel C: binding-stat (by_std / by_spread / by_centroid separated) ---
        bd = a["binding_stat_distribution"]
        panelC = {"binding_stat_distribution": bd, "by_binding_fraction": a["by_binding_fraction"],
                  "by_share_of_matched_stats": by_share,
                  "by_binding_by_feature": {s: bd.get(s, 0) for s in BY_FEATURES},
                  "by_binds_above_share": bool(a["by_binding_fraction"] > by_share)}

        # --- Panel D: region / family (with single-matching-family caveat) ---
        panelD = {"region_by_persistence": a["region_by_persistence"], "unmatched_regions": a["unmatched_regions"],
                  "family_distribution": a["family_distribution"], "n_matching_families": a["n_matching_families"],
                  "single_matching_family_caveat": bool(a["n_matching_families"] == 1),
                  "family_comparison_assessable": bool(a["n_matching_families"] >= 2)}

        # --- Panel E: coupling / leakage separation ---
        mech = a["mechanism_scores"]
        dominant_mech = max(mech, key=mech.get)
        panelE = {"centroid_spread_coupling_spearman": a["centroid_spread_coupling_spearman"],
                  "by_std_amplitude_spearman": a["by_std_amplitude_spearman"], "mechanism_scores": mech,
                  "dominant_mechanism": dominant_mech,
                  "coupling_weak": bool(mech["BY_centroid_spread_coupling"] < mech["BY_axis_asymmetry"]),
                  "amplitude_weak": bool(mech["BY_amplitude_leakage"] < mech["BY_axis_asymmetry"])}

        # --- Panel F: residual-aggregation warning ---
        # matched pairs are within TOL by the closure definition (matched iff residual <= TOL); the warning flags
        # that this per-pair closure COEXISTS with a systematic, BY-dominant, often-binding class-level BY offset.
        per_pair_all_within_tol = True
        by_sign_systematic = bool(mean_sc > CHANCE_SIGN)
        aggregation_warning = bool(per_pair_all_within_tol and a["by_dominant_over_rg"] and by_sign_systematic
                                   and a["by_binding_fraction"] > by_share)
        panelF = {"per_pair_all_within_tol": per_pair_all_within_tol, "by_dominant": a["by_dominant_over_rg"],
                  "by_sign_systematic_above_chance": by_sign_systematic,
                  "by_binds_above_share": bool(a["by_binding_fraction"] > by_share),
                  "aggregation_warning": aggregation_warning}

        panels = {"A_signed_offset": panelA, "B_by_vs_rg_dominance": panelB, "C_binding_stat": panelC,
                  "D_region_family": panelD, "E_coupling_leakage_separation": panelE,
                  "F_residual_aggregation_warning": panelF}

        # visibility confirmation -- reporting criteria (natural references only; NOT a closure pass/fail gate)
        offset_criteria = {
            "A_signed_and_systematic": all(panelA[s]["sign_consistency"] > CHANCE_SIGN for s in BY_FEATURES),
            "B_by_dominant": bool(panelB["by_dominant_over_rg"]),
            "C_by_binds_above_share": panelC["by_binds_above_share"],
            "E_axis_asymmetry_dominant": bool(dominant_mech == "BY_axis_asymmetry"),
            "F_aggregation_warning": panelF["aggregation_warning"],
            "D_region_reported": bool(len(a["region_by_persistence"]) > 0)}
        fully = all(offset_criteria.values())
        partially = any(offset_criteria.values()) and not fully

    if not clean:
        outcome_label = "invalid_protocol_breach"
        outcome = "invalid_protocol_breach: " + "; ".join(breaches)
    elif fully:
        outcome_label = "BY_visibility_confirmed"
        outcome = ("BY_visibility_confirmed: panels A-F make the systematic BY opponent-axis offset explicitly "
                   "visible (family comparison limited to a single matching family; surfaced as a caveat, not a "
                   "visibility failure)")
    elif partially:
        outcome_label = "BY_visibility_partial"
        outcome = "BY_visibility_partial: some panels surface the BY offset while others are limited"
    else:
        outcome_label = "BY_visibility_inconclusive"
        outcome = "BY_visibility_inconclusive: the panels do not surface the BY offset from these records"

    return {"diagnostic": "v0.9b BY opponent-axis closure visibility audit (form A, NON-LEARNING; REPORTING-only; "
                          "panels A-F over reused v0.7b/v0.8a records; adopts no metric, no pass/fail gate)",
            "model_form": "A_non_learning_reporting", "learning": False, "reporting_only": True,
            "audit_question": "make systematic BY_axis_asymmetry explicitly visible without new metric/TOL/pass-fail",
            "reuses_v0_8a_reproduces_v0_7b": bool(a.get("reproduces_v0_7b")),
            "TOL": a.get("TOL"), "TOL_redefined": False, "new_threshold_introduced": False,
            "new_closure_metric_adopted": False, "pass_fail_gate_introduced": False,
            "new_family_or_axis": False, "spectral_role": "audit-note-only (NOT reopened)",
            "panels": panels, "offset_visibility_criteria": offset_criteria,
            "protocol_ok": clean, "breaches": breaches,
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
    print("reuses v0.8a (reproduces v0.7b):", r["reuses_v0_8a_reproduces_v0_7b"], "| protocol_ok:", r["protocol_ok"], r["breaches"])
    print("new_closure_metric_adopted:", r["new_closure_metric_adopted"], "| pass_fail_gate_introduced:", r["pass_fail_gate_introduced"])
    if r["protocol_ok"]:
        P = r["panels"]
        print("\nPANEL A signed-offset:")
        for s in BY_FEATURES:
            d = P["A_signed_offset"][s]
            print("   %-12s offset=%+.5f  sign_consistency=%.2f  dominant=%s" % (s, d["signed_offset"], d["sign_consistency"], d["dominant_sign"]))
        print("   mean sign consistency:", P["A_signed_offset"]["mean_sign_consistency"])
        print("PANEL B BY-vs-RG dominance:", P["B_by_vs_rg_dominance"]["by_dominant_over_rg"],
              "| BY:", P["B_by_vs_rg_dominance"]["by_effects_frac_TOL"], "| RG:", P["B_by_vs_rg_dominance"]["rg_effects_frac_TOL"])
        print("PANEL C binding:", P["C_binding_stat"]["by_binding_by_feature"], "| by_binding_frac:", P["C_binding_stat"]["by_binding_fraction"],
              "| share:", P["C_binding_stat"]["by_share_of_matched_stats"], "| above_share:", P["C_binding_stat"]["by_binds_above_share"])
        print("PANEL D region:", {k: v["by_centroid_BA"] for k, v in P["D_region_family"]["region_by_persistence"].items()},
              "| family:", P["D_region_family"]["family_distribution"], "| single_family_caveat:", P["D_region_family"]["single_matching_family_caveat"])
        print("PANEL E coupling:", P["E_coupling_leakage_separation"]["centroid_spread_coupling_spearman"],
              "| amplitude:", P["E_coupling_leakage_separation"]["by_std_amplitude_spearman"],
              "| dominant_mechanism:", P["E_coupling_leakage_separation"]["dominant_mechanism"])
        print("PANEL F aggregation_warning:", P["F_residual_aggregation_warning"]["aggregation_warning"])
        print("\noffset visibility criteria:", r["offset_visibility_criteria"])
    print("\nOUTCOME_LABEL:", r["outcome_label"])
    print("verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"], r["descriptor_validity_claim_allowed"])
