"""BV chroma-structure pooled-gate AUDIT v1.8 (offline research; NOT runtime/integration; NOT vision).

Governed by docs: TORMENT_BRAINVISION_COLOR_STRUCTURE_POOLED_GATE_AUDIT_PLAN_v1.7. Its ONLY job is to

    decompose pooled HOLD causes under unchanged §7   (NOT: make the pooled gate pass).

It re-reads the EXISTING frozen §7 anti-proxy result of the accepted v1.4 movement-matched diagnostic
(run_color_structure_movement_matched_v1_4, `mm`) and produces REPORTING-ONLY decomposition tables showing
which pooled components drive the remaining HOLD. It imports and reuses the frozen v0.7/v0.8 machinery by
identity (structure_score / _stats / _spearman / constants) and the v1.1 + v1.4 fixtures/bank assembly; it
changes NO formula, NO §7 anti-proxy logic, NO §8 verdict logic, NO threshold, and NO control. It defines no
replacement acceptance criteria, deletes/cherry-picks nothing into a pass, and cannot move the verdict: the
authoritative verdict is taken verbatim from `mm.run()` and stays HOLD.

Leave-one-out and subset views below are ATTRIBUTION VIEWS ONLY (what the existing pooled Spearman would read
if a component were absent) -- they are NOT proposals to remove anything and NOT a pass path. Classification is
reporting-only, conservative, and defaults to "unresolved / needs adversarial review".

stdlib + numpy only; no service imports; no runtime / camera / live-capture / screen-capture / streaming /
prompt / context / memory / action / render-body / autonomy contact; no torment_service; no memory-system
integration; no object/scene understanding; no temporal-order diagnostic; no new descriptor; no new gate; no
real clips. Brainvision Path B is NOT proven vision and is NOT a functioning vision layer for TORMENT memory.
"""
from __future__ import annotations

import numpy as np

import run_color_structure_v0_8 as cs
import run_color_structure_fixture_bank_v1_1 as fb
import run_color_structure_movement_matched_v1_4 as mm

# frozen surfaces reused verbatim (NOT redefined)
spearman = cs.g5._spearman
CEIL = cs.MAGNITUDE_CORR_CEIL
ANTI_PROXY_STATS = cs.ANTI_PROXY_STATS
NULL_REL_STATS = cs.NULL_REL_STATS

CONTROL_FAMILIES = ("traj_null", "indep_null", "continuity_control", "structureless_control")
SUBSETS = ("full_bank", "matched_pairs", "null_controls", "coherent_winders", "non_winder_cancellation")


def _rebuild_bank():
    """Reconstruct the EXACT v1.4 pooled §7 bank (same order/seeds as mm.run), tagged for decomposition.

    Each entry: {name, S, stats, group, fclass}. `group` in {winder, nonwinder, traj_null, indep_null,
    continuity_control, structureless_control}. Faithfulness is asserted against mm.run()'s reported gate.
    """
    T, BASE_Y = mm.T, mm.BASE_Y
    entries = []
    ct = cs._series(*cs.continuity_control())
    S_cont = cs.structure_score(ct[0], ct[1], ct[2])["S"]
    st = cs._series(*cs.structureless_control())
    S_struct = cs.structure_score(st[0], st[1], st[2])["S"]
    for i, name in enumerate(mm.ALL_FIXTURES):
        rg, by, ch, _clip = mm.fixture_series(name)
        s_int = cs.structure_score(rg, by, ch)
        entries.append({"name": name, "S": s_int["S"], "stats": cs._stats(rg, by, ch),
                        "group": mm.ROLE[name], "fclass": mm.CLASS[name]})
        if (name in mm.IN_SCOPE):
            rgp, byp, chp, _r, null_invalid = fb.traj_null_guarded(rg, by)
            if not null_invalid:
                s_traj = cs.structure_score(rgp, byp, chp)
                entries.append({"name": name + "_traj_null", "S": s_traj["S"],
                                "stats": cs._stats(rgp, byp, chp), "group": "traj_null", "fclass": None})
                irg, iby, ich, _ic = cs._series(np.full(T, BASE_Y), *cs.null_independent_phase(rg, by, 9000 + i))
                entries.append({"name": name + "_indep_null", "S": cs.structure_score(irg, iby, ich)["S"],
                                "stats": cs._stats(irg, iby, ich), "group": "indep_null", "fclass": None})
    entries.append({"name": "continuity_control", "S": S_cont, "stats": cs._stats(ct[0], ct[1], ct[2]),
                    "group": "continuity_control", "fclass": None})
    entries.append({"name": "structureless_control", "S": S_struct, "stats": cs._stats(st[0], st[1], st[2]),
                    "group": "structureless_control", "fclass": None})
    return entries


def _traj_base(entries, stat):
    traj = [e["stats"][stat] for e in entries if e["group"] == "traj_null"]
    return float(np.mean(traj)) if traj else 0.0


def _rho(entries, stat, base=0.0):
    if len(entries) < 3:
        return None
    Svec = np.array([e["S"] for e in entries], float)
    vals = np.array([e["stats"][stat] - base for e in entries], float)
    return float(spearman(Svec, vals))


def _all_stat_keys():
    return list(ANTI_PROXY_STATS) + ["nr_" + s for s in NULL_REL_STATS]


def _base_for(entries_full, key):
    # null-relative stats subtract the FULL-bank trajectory-null mean (as in the frozen §7 computation)
    if key.startswith("nr_"):
        return _traj_base(entries_full, key[3:])
    return 0.0


def _stat_name(key):
    return key[3:] if key.startswith("nr_") else key


def _subset(entries, name):
    if name == "full_bank":
        return list(entries)
    if name == "matched_pairs":
        pair_names = {n for pair in mm.MATCHED_PAIRS for n in pair}
        return [e for e in entries if e["name"] in pair_names]
    if name == "null_controls":
        return [e for e in entries if e["group"] in CONTROL_FAMILIES]
    if name == "coherent_winders":
        return [e for e in entries if e["group"] == "winder"]
    if name == "non_winder_cancellation":
        return [e for e in entries if e["group"] == "nonwinder"]
    raise ValueError(name)


def run():
    mm_res = mm.run()                      # authoritative verdict/gate (UNCHANGED); audit cannot alter it
    entries = _rebuild_bank()
    keys = _all_stat_keys()

    # section 1: failing_stats_ranked (all stats ranked by |rho|; pass/fail per the EXISTING gate)
    full = {}
    for key in keys:
        base = _base_for(entries, key)
        rho = _rho(entries, _stat_name(key), base)
        full[key] = rho
    failing_stats_ranked = []
    for key in sorted(keys, key=lambda k: -abs(full[k] if full[k] is not None else 0.0)):
        rho = full[key]
        failing_stats_ranked.append({"stat": key, "spearman_rho": round(rho, 3),
                                     "abs_rho": round(abs(rho), 3),
                                     "gate": "fail" if abs(rho) >= CEIL else "pass"})
    failing_keys = [d["stat"] for d in failing_stats_ranked if d["gate"] == "fail"]

    # section 2: subset_spearman (over predeclared subsets; reporting-only)
    subset_spearman = []
    for sub in SUBSETS:
        se = _subset(entries, sub)
        for key in failing_keys:
            base = _base_for(entries, key)          # full-bank nr base, kept constant across subsets
            rho = _rho(se, _stat_name(key), base)
            s_std = float(np.std([e["S"] for e in se])) if se else 0.0
            subset_spearman.append({"subset": sub, "n": len(se), "stat": key,
                                    "rho": (None if rho is None else round(rho, 3)),
                                    "abs_rho": (None if rho is None else round(abs(rho), 3)),
                                    "s_std": round(s_std, 4)})

    # section 3: fixture_class_contribution (leave-one-class-out attribution; NOT a removal proposal)
    fixture_class_contribution = []
    classes = sorted({e["fclass"] for e in entries if e["fclass"] is not None})
    for cl in classes:
        without = [e for e in entries if e["fclass"] != cl]
        for key in failing_keys:
            base = _base_for(entries, key)
            rho = _rho(without, _stat_name(key), base)
            fixture_class_contribution.append({
                "fixture_class": cl, "stat": key,
                "rho_without_class": (None if rho is None else round(rho, 3)),
                "delta_from_full": (None if rho is None else round(rho - full[key], 3))})

    # section 4: control_family_contribution (leave-one-family-out attribution; NOT a removal proposal)
    control_family_contribution = []
    for fam in CONTROL_FAMILIES:
        without = [e for e in entries if e["group"] != fam]
        for key in failing_keys:
            base = _base_for(entries, key)
            rho = _rho(without, _stat_name(key), base)
            control_family_contribution.append({
                "control_family": fam, "stat": key,
                "rho_without_family": (None if rho is None else round(rho, 3)),
                "delta_from_full": (None if rho is None else round(rho - full[key], 3))})

    # section 5: classification_reporting_only (conservative; CANNOT move verdict).
    # "primary subset" here = the MOVEMENT-MATCHED primary-pair subset (matched_pairs): the controlled-movement
    # comparison that separates a descriptor-level blocker (S tracks the stat even at matched movement) from
    # null/control-driven covariance. Classify every stat that fails the pooled gate OR persists above ceiling
    # on that matched subset -- this also surfaces matched-subset blockers that may pass the pooled gate
    # (e.g. by_std / rg_spread / nr_rg_spread) alongside stats that fail both views (e.g. spectral_centroid,
    # whose pooled |rho| sits at the 0.30 ceiling). No cherry-picking: the same matched-subset rule is applied
    # to every stat, and the pooled verdict stays HOLD (taken verbatim from mm) regardless.
    matched = _subset(entries, "matched_pairs")
    null_controls = _subset(entries, "null_controls")
    matched_rho = {k: _rho(matched, _stat_name(k), _base_for(entries, k)) for k in keys}
    matched_fail = {k for k in keys if matched_rho[k] is not None and abs(matched_rho[k]) >= CEIL}
    classify_keys = list(failing_keys) + [k for k in keys if k in matched_fail and k not in failing_keys]
    classification = []
    for key in classify_keys:
        base = _base_for(entries, key)
        rho_matched = matched_rho[key]
        rho_nc = _rho(null_controls, _stat_name(key), base)
        persists_on_matched = (rho_matched is not None) and (abs(rho_matched) >= CEIL)
        pooled_fail = key in failing_keys
        driven_by_null_controls = (rho_nc is not None) and (abs(rho_nc) >= CEIL) and not persists_on_matched
        if persists_on_matched:
            # S tracks the stat even at exactly matched movement -> descriptor-level association
            label = "likely legitimate descriptor blocker"
            evidence = ("persists above ceiling on the movement-matched primary-pair subset "
                        "(S tracks it even at matched movement)")
        elif pooled_fail and driven_by_null_controls:
            # A/B ambiguity: composition-artifact vs validity-surface framing -> conservatively UNRESOLVED
            label = "unresolved / needs adversarial review"
            evidence = ("pooled failure driven by the null/control subset, absent on matched pairs; "
                        "composition-artifact vs validity-surface-framing is the A/B ambiguity")
        else:
            label = "unresolved / needs adversarial review"
            evidence = "mixed / no clean attribution"
        classification.append({
            "stat": key, "classification": label, "evidence": evidence,
            "pooled_gate": ("fail" if pooled_fail else "pass"),
            "rho_full": round(full[key], 3),
            "rho_primary_subset": (None if rho_matched is None else round(rho_matched, 3)),
            "rho_null_controls_subset": (None if rho_nc is None else round(rho_nc, 3))})

    # faithfulness: reconstructed full-bank gate MUST reproduce mm's reported §7 result (audit changed nothing)
    faithful = all(abs(full[k] - mm_res["anti_proxy"][k]["spearman"]) < 5e-3 for k in keys)

    return {"audit_of": "v1.4_movement_matched (mm.run) pooled §7 gate",
            "verdict": mm_res["verdict"], "anti_proxy_ok": mm_res["anti_proxy_ok"],
            "bank_size": len(entries), "mm_bank_size": mm_res["bank_size"],
            "faithful_reconstruction": bool(faithful),
            "gate_ceiling": CEIL, "reporting_only": True,
            "failing_stats_ranked": failing_stats_ranked, "subset_spearman": subset_spearman,
            "fixture_class_contribution": fixture_class_contribution,
            "control_family_contribution": control_family_contribution,
            "classification_reporting_only": classification,
            "first_pass_structure_validity_claim_allowed": mm_res["first_pass_structure_validity_claim_allowed"],
            "temporal_claim_allowed": mm_res["temporal_claim_allowed"]}


if __name__ == "__main__":
    r = run()
    print("audit_of:", r["audit_of"])
    print("verdict", r["verdict"], "| anti_proxy_ok", r["anti_proxy_ok"], "| bank_size",
          r["bank_size"], "(mm", r["mm_bank_size"], ") | faithful", r["faithful_reconstruction"],
          "| reporting_only", r["reporting_only"])
    print("\n1. failing_stats_ranked (gate ceiling |rho|<%.2f, UNCHANGED):" % r["gate_ceiling"])
    for d in r["failing_stats_ranked"]:
        print("   %-26s rho=%+.3f |rho|=%.3f  %s" % (d["stat"], d["spearman_rho"], d["abs_rho"], d["gate"]))
    print("\n2. subset_spearman (reporting-only):")
    for d in r["subset_spearman"]:
        print("   %-24s n=%-2d s_std=%-7s %-26s rho=%s"
              % (d["subset"], d["n"], d["s_std"], d["stat"], d["rho"]))
    print("\n3. fixture_class_contribution (leave-one-class-out attribution):")
    for d in r["fixture_class_contribution"]:
        print("   class %-2s %-26s rho_without=%s delta=%s"
              % (d["fixture_class"], d["stat"], d["rho_without_class"], d["delta_from_full"]))
    print("\n4. control_family_contribution (leave-one-family-out attribution):")
    for d in r["control_family_contribution"]:
        print("   %-22s %-26s rho_without=%s delta=%s"
              % (d["control_family"], d["stat"], d["rho_without_family"], d["delta_from_full"]))
    print("\n5. classification_reporting_only (cannot move verdict):")
    for d in r["classification_reporting_only"]:
        print("   %-26s [pooled:%s] -> %s\n      (full %+.3f matched_primary %s null_controls %s) %s"
              % (d["stat"], d["pooled_gate"], d["classification"], d["rho_full"], d["rho_primary_subset"],
                 d["rho_null_controls_subset"], d["evidence"]))
