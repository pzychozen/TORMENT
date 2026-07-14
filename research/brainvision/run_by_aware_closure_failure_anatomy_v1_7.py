"""BV BY-aware closure failure anatomy v1.7 (offline research; form A; NON-LEARNING; NOT vision).

REPORTING-ONLY bounded failure-anatomy diagnostic. It implements the v1.6a finite plan: it inspects WHY the
accepted A + D + G BY-aware closure spine (v1.5) still reports the BY signed-ordering gap as visible, and answers
ONE decision question -- does the current fixture-metric route expose a concrete BOUNDED LEVER, or should the
branch PIVOT to a flat opponent-plane / spatial-field proposal? It reuses the v1.5 audit
(run_by_aware_closure_audit_v1_5) BY IDENTITY and only RE-PRESENTS its frozen quantities as five anatomy panels
(mechanisms A-E). It ADDS NO new statistic.

  A residual aggregation hides signed BY ordering
  B BY signed offset appears structural to the current fixture family
  C BY/RG opponent balance mismatched even when residual/TOL passes
  D by_std binds matching more strongly than by_centroid/by_spread
  E current trajectory/winder-canceller abstraction appears insufficient for screen-like vision

For each mechanism the panel records the frozen EVIDENCE, whether the phenomenon is OBSERVED, and the operation
that turning it into a CLOSURE decision WOULD REQUIRE. Per the v1.6a bounded-lever criteria (specific, finite,
inspectable WITHOUT redefining TOL / inventing thresholds / descriptor redesign / generator-family expansion), a
mechanism is a BOUNDED LEVER only if it is observed AND requires NO forbidden operation. Each fixture-metric
mechanism's closure path requires a forbidden operation (a sign-consistency threshold / offset-vs-TOL gate for A,
a BY-RG dominance threshold for C, a binding gate for D) and B / E are pivot signals (single-family structural /
abstraction-level), so bounded_lever_identified is derived, not asserted.

It ADOPTS NO closure metric, NO equation, invents NO threshold, REDEFINES NO TOL, creates NO offset-vs-TOL gate
and NO binding gate and NO pass/fail validity gate, changes no evaluator / control, redesigns no descriptor,
reopens no spectral group, expands no family, and adds NO classifier (form B) / neural encoder (form C). It reruns
/ replaces NO sample and adds NO seed / family / candidate generation. It does NOT pivot to flat / screen geometry
(it only RECOMMENDS a docs-only pivot proposal) and does NOT touch runtime / memory / integration / real clips.

protocol_ok means ONLY that the required anatomy panels and the guard are present -- NOT closure.
closure_achieved is ALWAYS False. The result label is CONSERVATIVE:
BY_failure_anatomy_bounded_lever_visible or BY_failure_anatomy_no_bounded_lever. NaN / breach / non-reproduction /
a missing-or-authorizing guard force invalid_protocol_breach via the reused chain. Verdict HOLD.

stdlib only; reuses only quarantined research surfaces; no torment_service; no runtime / camera / sensor /
live-capture / screen-capture / streaming / prompt / context / memory / action / render-body / autonomy contact;
no real clips.
"""
from __future__ import annotations

import run_by_channel_metric_anatomy_v0_8a as m8a
import run_by_aware_closure_audit_v1_5 as m15

# ---- reused-by-identity surfaces ----
BY_FEATURES = m8a.BY_FEATURES                       # by_centroid, by_spread, by_std
V11A_GUARD_FLAGS = m15.V11A_GUARD_FLAGS             # nine v1.1a authorization flags (reused by identity)

SPINE_KEYS = ("A_signed_offset", "D_aggregation_anti_hiding", "G_non_authorizing_guard")
SUPPORT_KEYS = ("B_by_rg_opponent_balance", "C_binding_aware_partition", "E_region_family_stratified")
ANATOMY_PANELS = ("A_residual_aggregation_hides_ordering", "B_offset_structural_to_family",
                  "C_by_rg_balance_mismatch", "D_by_std_binds_strongest", "E_abstraction_insufficient")

OUTCOME_LABELS = ("BY_failure_anatomy_bounded_lever_visible", "BY_failure_anatomy_no_bounded_lever",
                  "invalid_protocol_breach")

PIVOT_TARGET = "flat_opponent_plane_spatial_field_proposal"


def _guard_ok(g):
    """Guard admissible iff diagnostic-only AND every authorizes_* it carries is False AND all nine v1.1a-required
    flags are PRESENT and False. A missing OR True required flag -> not ok -> breach (completeness-enforced)."""
    if not g or g.get("visibility_is_diagnostic_only") is not True:
        return False
    auth_keys = [k for k in g if k.startswith("authorizes_")]
    if not auth_keys or not all(g.get(k) is False for k in auth_keys):
        return False
    return all(k in g and g[k] is False for k in V11A_GUARD_FLAGS)


def run():
    s = m15.run()                                                    # accepted v1.5 A+D+G spine; reuse chain to v0.7b by identity

    breaches = list(s.get("breaches", []) or [])
    if s.get("outcome_label") == "invalid_protocol_breach":
        breaches.append("v1_5_breach")
    if not s.get("protocol_ok"):
        breaches.append("v1_5_protocol_not_ok")
    if not s.get("reuses_v0_7b_v0_8a_v0_9b_v1_0b_v1_2_records"):
        breaches.append("v1_5_does_not_reproduce_v0_7b")
    if s.get("closure_achieved") is not False:
        breaches.append("closure_achieved_not_false")
    spine = s.get("primary_spine") or {}
    support = s.get("support_reporting") or {}
    if set(spine.keys()) != set(SPINE_KEYS):
        breaches.append("v1_5_spine_incomplete")
    elif not _guard_ok(spine.get("G_non_authorizing_guard")):
        breaches.append("guard_missing_or_authorizing")
    if any(k not in support for k in SUPPORT_KEYS):
        breaches.append("v1_5_support_incomplete")

    clean = (len(breaches) == 0)
    anatomy_panels = {}
    bounded_lever_identified = False
    candidate_lever, recommended_next = None, None

    if clean:
        A = spine["A_signed_offset"]
        Dagg = spine["D_aggregation_anti_hiding"]
        Bbal = support["B_by_rg_opponent_balance"]
        Cbind = support["C_binding_aware_partition"]
        Ereg = support["E_region_family_stratified"]

        # --- Mechanism A: residual aggregation hides systematic signed BY ordering ---
        a_observed = bool(Dagg.get("aggregation_warning") and Dagg.get("by_sign_systematic_above_chance"))
        panel_A = {
            "question": "Does residual aggregation hide systematic signed BY ordering?",
            "evidence": {"mean_sign_consistency": A.get("mean_sign_consistency"),
                         "aggregation_warning": Dagg.get("aggregation_warning"),
                         "by_sign_systematic_above_chance": Dagg.get("by_sign_systematic_above_chance"),
                         "per_by_sign_consistency": {s_: A[s_]["sign_consistency"] for s_ in BY_FEATURES}},
            "observed": a_observed,
            "would_require_to_close": "sign_consistency_threshold_or_offset_vs_tol_gate",  # forbidden
            "forbidden_by_boundary": True, "is_bounded_lever": False}

        # --- Mechanism B: BY signed offset appears structural to the single fixture family ---
        n_fam = Ereg.get("n_matching_families")
        b_observed = bool(Ereg.get("single_matching_family_caveat")) or (n_fam == 1)
        panel_B = {
            "question": "Does the BY signed offset appear structural to the current fixture family?",
            "evidence": {"n_matching_families": n_fam,
                         "single_matching_family_caveat": Ereg.get("single_matching_family_caveat"),
                         "family_distribution": Ereg.get("family_distribution")},
            "observed": b_observed,
            "would_require_to_close": "generator_family_expansion",  # forbidden (needed even to TEST separability)
            "forbidden_by_boundary": True, "is_pivot_signal": b_observed, "is_bounded_lever": False}

        # --- Mechanism C: BY/RG opponent balance mismatched even when residual/TOL passes ---
        c_observed = bool(Bbal.get("by_dominant_over_rg"))
        panel_C = {
            "question": "Does BY/RG opponent balance remain mismatched even when residual/TOL passes?",
            "evidence": {"by_effects_frac_TOL": Bbal.get("by_effects_frac_TOL"),
                         "rg_effects_frac_TOL": Bbal.get("rg_effects_frac_TOL"),
                         "by_dominant_over_rg": Bbal.get("by_dominant_over_rg")},
            "observed": c_observed,
            "would_require_to_close": "by_rg_dominance_threshold",  # forbidden
            "forbidden_by_boundary": True, "is_bounded_lever": False}

        # --- Mechanism D: by_std binds matching more strongly than by_centroid/by_spread ---
        bbf = Cbind.get("by_binding_by_feature", {})
        d_observed = bool(bbf.get("by_std", 0) > max(bbf.get("by_centroid", 0), bbf.get("by_spread", 0)))
        panel_D = {
            "question": "Does by_std bind matching more strongly than by_centroid/by_spread?",
            "evidence": {"by_binding_by_feature": bbf, "by_binds_above_share": Cbind.get("by_binds_above_share")},
            "observed": d_observed,
            "would_require_to_close": "binding_gate",  # forbidden
            "forbidden_by_boundary": True, "is_bounded_lever": False}

        # --- Mechanism E: current trajectory/winder-canceller abstraction appears insufficient ---
        # E is derived: if A/C/D each require a forbidden op AND the evidence sits on a single family (B), then the
        # persistence is abstraction-level, not a fixture-metric lever -> pivot signal.
        no_fixture_lever = not (panel_A["is_bounded_lever"] or panel_C["is_bounded_lever"] or panel_D["is_bounded_lever"])
        e_observed = bool(no_fixture_lever and b_observed)
        panel_E = {
            "question": "Does the trajectory/winder-canceller abstraction appear insufficient for screen-like vision?",
            "evidence": {"no_representable_fixture_lever": no_fixture_lever,
                         "single_matching_family": b_observed,
                         "acd_would_require": {"A": panel_A["would_require_to_close"],
                                               "C": panel_C["would_require_to_close"],
                                               "D": panel_D["would_require_to_close"]}},
            "observed": e_observed,
            "would_require_to_close": "flat_opponent_plane_or_spatial_field_reframe",  # outside fixture-metric route
            "forbidden_by_boundary": False, "is_pivot_signal": e_observed, "is_bounded_lever": False}

        anatomy_panels = {"A_residual_aggregation_hides_ordering": panel_A,
                          "B_offset_structural_to_family": panel_B,
                          "C_by_rg_balance_mismatch": panel_C,
                          "D_by_std_binds_strongest": panel_D,
                          "E_abstraction_insufficient": panel_E}

        # a BOUNDED LEVER = an observed mechanism whose closure path requires NO forbidden operation (v1.6a §9/§10)
        lever_panels = [k for k, v in anatomy_panels.items()
                        if v.get("is_bounded_lever") and v.get("observed")]
        bounded_lever_identified = len(lever_panels) > 0

        if bounded_lever_identified:
            candidate_lever = lever_panels
            recommended_next = "v1_7a_bounded_lever_plan_docs_first"
            outcome_label = "BY_failure_anatomy_bounded_lever_visible"
            outcome = ("BY_failure_anatomy_bounded_lever_visible: a concrete bounded lever was surfaced (%s); "
                       "propose a docs-first lever plan, adopting no metric/threshold/gate" % ", ".join(lever_panels))
        else:
            candidate_lever = None
            recommended_next = PIVOT_TARGET
            outcome_label = "BY_failure_anatomy_no_bounded_lever"
            outcome = ("BY_failure_anatomy_no_bounded_lever: every fixture-metric mechanism (A/C/D) would require a "
                       "forbidden operation (threshold / offset-vs-TOL gate / binding gate) and B/E are pivot "
                       "signals (single-family structural / abstraction-level) -> recommend pivoting to a docs-only "
                       "flat opponent-plane / spatial-field proposal (single matching family caveat preserved)")
    else:
        outcome_label = "invalid_protocol_breach"
        outcome = "invalid_protocol_breach: " + "; ".join(breaches)

    return {"diagnostic": "v1.7 BY-aware closure failure anatomy (form A, NON-LEARNING; REPORTING-only; panels A-E "
                          "over reused v1.5 spine by identity; decides bounded-lever vs pivot; adopts no metric/"
                          "equation/threshold/gate; non-authorizing)",
            "model_form": "A_non_learning_reporting", "learning": False, "reporting_only": True,
            "prereg_source": "v1.6a finite failure-anatomy plan (accepted) on the v1.5 A + D + G spine",
            "audit_question": "does the fixture-metric route expose a concrete BOUNDED LEVER, or should it PIVOT?",
            "reuses_v1_5_spine_by_identity": clean,
            "TOL": s.get("TOL"), "tol_redefined": False, "TOL_redefined": False, "new_threshold_introduced": False,
            "new_closure_metric_adopted": False, "pass_fail_gate_introduced": False,
            "offset_vs_tol_gate": False, "binding_gate": False, "validity_pass_fail_gate": False,
            "closure_achieved": False,
            "new_family_or_axis": False, "generator_family_expansion_authorized": False,
            "descriptor_redesign_authorized": False, "spectral_closure_reopened": False,
            "spectral_role": "audit-note-only (NOT reopened)",
            "flat_geometry_authorized": False, "screen_analysis_authorized": False,
            "runtime_authorized": False, "memory_authorized": False, "vision_claim_allowed": False,
            "visibility_is_non_authorizing": True,
            "anatomy_panels": anatomy_panels,
            "bounded_lever_identified": bounded_lever_identified,
            "candidate_lever": candidate_lever, "recommended_next": recommended_next,
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
    print("reuses v1.5 spine by identity:", r["reuses_v1_5_spine_by_identity"], "| protocol_ok:", r["protocol_ok"], r["breaches"])
    print("new_closure_metric_adopted:", r["new_closure_metric_adopted"], "| offset_vs_tol_gate:", r["offset_vs_tol_gate"],
          "| binding_gate:", r["binding_gate"], "| closure_achieved:", r["closure_achieved"])
    if r["protocol_ok"]:
        print("\nANATOMY PANELS A-E:")
        for k in ANATOMY_PANELS:
            p = r["anatomy_panels"][k]
            print("  %-38s observed=%-5s  would_require=%-45s  bounded_lever=%s"
                  % (k, p["observed"], p["would_require_to_close"], p["is_bounded_lever"]))
        print("\nbounded_lever_identified:", r["bounded_lever_identified"], "| candidate_lever:", r["candidate_lever"])
        print("recommended_next:", r["recommended_next"])
    print("\nOUTCOME_LABEL:", r["outcome_label"])
    print("closure_achieved:", r["closure_achieved"], "| verdict:", r["frozen_brainvision_verdict"], "| locks",
          r["first_pass_structure_validity_claim_allowed"], r["temporal_claim_allowed"],
          r["descriptor_validity_claim_allowed"])
