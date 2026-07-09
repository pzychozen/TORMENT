# TORMENT Brainvision Larger-N Residual Replication Enumeration v0.7a

## 1. Status / non-claims

**DOCS-ONLY enumeration. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It seals the exact larger-N replication enumeration that v0.7 deferred, so a *future* v0.7a
implementation, if ever separately gated, is fully specified in advance and cannot be tuned toward a win.
Sealing an enumeration is **not** authorizing implementation: no code is authorized here; any implementation
still requires separate explicit operator instruction (§15). It **authorizes no code and no tests**, invents no
threshold, **redefines no `TOL`**, adopts **no new closure metric**, proposes no pass/fail rule change, changes
no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control, redesigns no descriptor,
adds **no new generator family and no new descriptor axis**, reopens no spectral group, and opens **no
classifier (form B) and no neural encoder (form C)**. Everything stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. An enumeration alone moves nothing:
**no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.7

```text
v0.7  (22c7488)  larger-N replication PLAN: rules/shape only; deferred the exact enumeration to a docs-gated step.
v0.7a (this doc) seals that exact enumeration: sample counts, seeds, generator-instance policy, pairing, budget,
                 reporting rules, no-rerun policy, outcome labels.
```

v0.7a changes nothing v0.7 froze. It only fills in the numeric slots v0.7 left to this step, using ONLY more
instances of the existing F1-F5 families and the frozen winder generator — no new family, no new axis, no new
threshold, no `TOL` change, no new closure metric. The v0.4d sealed 283-evaluation result and the v0.5a / v0.6a
findings are **preserved**; this replication is an **additive** larger-N companion, not a rerun or replacement.

## 3. Frozen anchors

Reused **by identity** from frozen, committed code; v0.7a authors no new descriptor, generator, metric, or
threshold:

```text
run_all_shortcuts_closed_synthetic_v0_3.py  GROUPS, ALL_PROXIES, _feat, best-threshold BA, CHANCE_BAND = 0.60
run_color_structure_v0_8.py                 structure_score, _stats, PSC_FLOOR = 0.30, AIC_FLOOR = 0.30, T
run_color_structure_spectral_std_blocker_v1_9.py / _by_std_residual_v2_0.py   winder + F-family generators
run_matched_generative_search_v0_4d.py      proxy_match_residual (L-inf over 10 matched stats, spectral excluded),
                                            PSC < PSC_FLOOR feasibility, TOL = 0.0634, _is_clean / EXTREME cap,
                                            the CLOSED family set F1-F5
run_baseline_anatomy_v0_5a.py               per-feature anatomy (BA, signed median diff, rank separation)
run_residual_sufficiency_v0_6a.py           parameter-free robustness lens (rank gap vs within-class spread)

Frozen evaluator (UNCHANGED):  structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR
Matched groups (UNCHANGED):    movement_channel_energy, directional, per_channel, frame_diff (spectral audit-note-only)
```

Every numeric value in §5-§9 that is not in the block above (winder parameter points, seeds, pool sizes, budget)
is an **enumeration choice** v0.7 authorized v0.7a to make; none is a descriptor / evaluator / closure threshold.

## 4. Larger-N replication question

```text
Which v0.6a separability effects survive when sample support is larger?

Effects to re-test:
  A. BY-channel substantive:   by_centroid, by_spread
  B. Directional tiny-magnitude: u_directional_delta_rms, angular_increment_mag
  C. Fragile small-N:          by_std, rg_centroid, rg_spread
```

At n = 3 vs 3 (v0.6a) best-threshold BA saturates on mere rank separation; at the larger n sealed below,
rank-separating the two classes is a much stronger (less-by-chance) condition, so BA discriminates and the
robustness lens stabilizes.

## 5. Exact sample counts

Winder targets come from the **frozen winder generator** at more parameter points (same generator, more
instances; NOT a new family or axis):

```text
REPLICATION winders (24) -- single-shot audit set:
  speed  sp in {0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5}        (8; frozen v9 winder(sp * FULL))
  phase  ph in {0, pi/4, pi/2, 3pi/4, pi, 5pi/4, 3pi/2, 7pi/4}  (8; frozen v9 series_theta(ph + FULL * arange))
  radius fr in {0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2}         (8; frozen v20 winder(fr))
  -> 24 replication winders

DEVELOPMENT winders (6) -- construction/debug only; parameter points DISJOINT from replication:
  speed  sp in {0.6, 1.25}     phase ph in {pi/8, 9pi/8}     radius fr in {0.85, 0.35}
  -> 6 development winders
```

Candidate pool (per phase) uses ONLY the existing five families at within-axis instances:

```text
F1 full_circle_incoherent_traversal   sigma in {0.3, 0.6, 1.0}                                  (stochastic; x seeds)
F2 rosette_multilobe_traversal        lobes in {2, 3, 5} x radius_frac in {0.7, 1.0}            (6; deterministic)
F3 segment_paired_canceller           increment_g in {0.10,0.15,0.20,0.25,0.30,0.40,0.50,0.79}  (all 8 FROZEN v0.3
                                        outback increments) x pairs in {1, 2}                    (16; deterministic)
F4 phase_scrambled_full_coverage      sigma in {0.5, 1.0, 1.5}                                   (stochastic; x seeds)
F5 hybrid_coverage_preserving_canceller  comboA (deterministic) + comboB (stochastic; x seeds)

pool size per winder:  development (2 seeds) = 3x2 + 6 + 16 + 3x2 + (1+2) = 37
                       replication  (3 seeds) = 3x3 + 6 + 16 + 3x3 + (1+3) = 44
```

The audit runs on the REPLICATION matched pairs, giving up to **24 winders vs 24 matched candidates** (n up to
24 per class; ~8x the v0.6a n = 3). The actual audit n is the number of replication winders that find a
within-`TOL` feasible match (reported, §10).

## 6. Exact seed policy

Fixed explicit seeds; development and replication pools are **disjoint** and sealed:

```text
development_seeds = [20260721, 20260722]                # |pool| = 2
replication_seeds = [20260723, 20260724, 20260725]      # |pool| = 3
```

Stochastic candidate families (F1 / F4 / hybrid-B) draw one instance per (param-combo, seed) from the pool
active in the current phase. Deterministic families ignore seeds. **No seed outside these lists may be used; no
seed may be added or swapped after seeing results (§12).** These seeds are disjoint from the v0.4c seeds.

## 7. Existing generator instances allowed

```text
- Winder targets: ONLY the frozen winder generator (v9 winder / series_theta, v20 winder) at the §5 parameter
  points. No new winder construction.
- Candidates: ONLY the closed families F1-F5 at the §5 within-axis instances. NO new family, NO new axis.
- F3 increments are drawn from the FROZEN v0.3 outback increment set (all eight) -- within the existing axis.
- Sequence length T, descriptor, GROUPS, evaluator, proxy_match_residual, PSC < PSC_FLOOR feasibility, and the
  robustness lens are reused by identity and unchanged.
```

## 8. Target/candidate pairing policy

```text
- For each winder (in the relevant set), evaluate the ENTIRE candidate pool ONCE (single deterministic pass).
- Keep the min proxy_match_residual FEASIBLE candidate (PSC < PSC_FLOOR); tie-break lowest seed then
  lexicographic family/param order (as in v0.4d).
- A winder is a MATCHED pair iff its best feasible residual <= TOL (0.0634, frozen). Non-matched winders are
  reported as unmatched (not dropped, not retried).
- The larger-N audit (per-feature BA / signed median diff / robustness lens) runs on the REPLICATION matched
  pairs, single-shot. Development pairs are for construction/debug only and do not enter the audit verdict.
- The future implementation must NOT search until it passes: it runs the fixed enumeration once and reports.
```

## 9. Run budget

```text
SEARCH_BUDGET (sealed, finite):
  development phase = 6 winders  x 37 pool = 222 evaluations
  replication phase = 24 winders x 44 pool = 1056 evaluations
  total             = 1278 proxy_match_residual + feasibility evaluations, each the full pool once per winder.

Retry policy:
  - NO restarts, NO retries, NO redraws, NO extra seeds beyond the §6 pools, NO "search until match".
  - a candidate that is infeasible (PSC >= PSC_FLOOR) or non-finite/extreme is recorded invalid and SKIPPED;
    it is NOT redrawn and the budget is NOT topped up.
  - a winder with no within-TOL feasible match is reported UNMATCHED; it is NOT replaced.
```

This is compact (~1.3k descriptor evaluations, order-of-magnitude over v0.4d's 283), not a huge grid.

## 10. Reporting outputs

```text
- n_matched replication winders (audit n per class), and the unmatched count;
- per-feature best-threshold BA at larger n (for the §4 effects);
- per-feature signed median difference by label (and as a fraction of TOL);
- the parameter-free robustness lens (rank gap vs within-class spread) at larger n;
- per-feature PERSISTENCE / COLLAPSE / AMBIGUITY relative to v0.6a (does the robust BY-channel separation
  persist; do the fragile small-N separations collapse; does the directional pair stay rank-separated but
  negligible or collapse);
- whether group-level residual / TOL closure still coexists with feature-level separability at larger n;
- defensive NaN / non-finite / extreme-value handling (reused; non-finite values never become evidence);
- an updated outcome label (§11).
```

All outputs are reporting-only. No pass/fail upgrade; no decision-score / classifier-score / label-accuracy /
held-out-performance / cheap-baseline-BA optimization.

## 11. Outcome labels

```text
BY_persistence_metric_insufficiency   BY-channel (by_centroid / by_spread) stays robust at larger n.
directional_collapse_tiny_magnitude   directional stays rank-separated-but-negligible, or collapses.
small_n_features_collapse             by_std / rg_centroid / rg_spread lose saturated BA at larger n.
mixed_effects_persist                 some robust and some small-N effects both persist.
replication_inconclusive              larger-N design cannot resolve without changing metrics / families.
invalid_protocol_breach               budget mismatch / non-finite backing a result / rerun / replacement /
                                      seed or sample change -> no evidential weight, moves no claim.
```

For **every** outcome: `verdict = HOLD`, claim locks stay False, and no vision / descriptor-validity /
temporal-order / memory / runtime / integration claim follows.

## 12. Forbidden reruns / replacements / amendments

```text
- NO rerun / replacement of the v0.4d sealed candidates or result (preserved; this is an additive companion).
- NO replacing failed / unmatched pairs; NO removing awkward samples after seeing results.
- NO adding seeds, winders, candidate instances, or pool members after seeing results.
- NO new family / new axis / new descriptor / new closure metric / TOL change / threshold invention.
- NO increasing the SEARCH_BUDGET or adding retries / restarts / redraws.
- Any change to the family set, axes, parameter points, seeds, split, or budget requires a NEW docs-only,
  Codex-reviewed amendment reviewed BEFORE any rerun.
```

## 13. What would count as useful evidence

The evidence is the **persistence-vs-collapse pattern** of the §4 effects under larger sample support — **not** a
pass, a new threshold, or a validity statement:

```text
- BY-channel PERSISTS robust while the fragile features COLLAPSE  -> metric-insufficiency component real,
  small-N component artifact (BY_persistence + small_n_features_collapse).
- directional stays rank-separated but negligible, or collapses   -> tiny-magnitude / small-N (directional_collapse).
- both robust and small-N effects persist                         -> mixed characterization holds.
- the design cannot separate them at this n                       -> replication_inconclusive; no claim movement.
```

## 14. What would still not be proven

Even a completed larger-N replication would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

Establishing which synthetic separability effects survive larger n is an in-vitro synthetic, metric-level
observation within the same family set; it says nothing about real clips and does not validate the descriptor.
The proof route remains **HELD / HOLD**. The claim locks (`first_pass_structure_validity_claim_allowed`,
`temporal_claim_allowed`, `descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force under every
outcome.

## 15. Recommended next step

```text
1. Codex review THIS enumeration (docs-only; over committed edge 22c7488).
2. If accepted, commit this enumeration doc. No §0 pointer; no tags.
3. Only THEN, and only on explicit operator instruction, may a SEPARATE future v0.7a code step implement EXACTLY
   this sealed enumeration -- form A, non-learning, reporting-only, frozen descriptor / evaluator / families /
   winder generator / proxy_match_residual / robustness lens / TOL reused by identity, delivered UNCOMMITTED for
   review, Windows the source of truth. This doc authorizes no such code by itself.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 16. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_LARGER_N_RESIDUAL_REPLICATION_ENUMERATION_v0.7a.md
(new, docs-only, untracked; over committed edge 22c7488, sealing the larger-N enumeration v0.7 deferred).

Verify that this enumeration:
- is docs-only and authorizes no implementation (no code/tests/generator, no torment_service/, no runtime, no
  memory, no camera/live/sensor/screen/streaming, no real clips); keeps form B / form C CLOSED;
- keeps ALL frozen: TOL (0.0634), PSC_FLOOR/AIC_FLOOR (0.30), CHANCE_BAND (0.60), the evaluator, the descriptor /
  GROUPS / proxy_match_residual / PSC<PSC_FLOOR feasibility / robustness lens; invents NO threshold, redefines NO
  TOL, adopts NO new closure metric, redesigns NO descriptor, keeps spectral audit-note-only;
- grows ONLY sample support via more instances of the frozen winder generator (more speed/phase/radius points)
  and the existing five families (more seeds / within-axis points; F3 uses the frozen v0.3 outback increment
  set); adds NO new family and NO new axis;
- seals exact sample counts (24 replication + 6 development winders), disjoint fixed seeds (dev [20260721,
  20260722]; replication [20260723,20260724,20260725]), a single-pass pairing (min-residual feasible candidate,
  matched iff <= TOL, no search-until-pass), and a finite compact SEARCH_BUDGET (222 + 1056 = 1278), with no
  restarts/retries/redraws/replacements;
- preserves the v0.4d sealed result and v0.5a/v0.6a findings (additive, not a rerun/replacement);
- limits outputs to reporting-only per-feature BA / signed median diff / robustness lens / persistence-collapse-
  ambiguity / coexistence, with NO pass/fail upgrade and NO decision/classifier/label/held-out/cheap-baseline
  optimization;
- lists outcome labels BY_persistence_metric_insufficiency / directional_collapse_tiny_magnitude /
  small_n_features_collapse / mixed_effects_persist / replication_inconclusive / invalid_protocol_breach, all
  leaving claim locks and verdict unchanged;
- makes no vision / "Brainvision sees" / temporal-order / descriptor-validity / memory / runtime / integration
  claim; adds no §0 pointer and no tags.

Flag any new family / new axis / new closure metric / TOL change / invented threshold, any rerun or replacement
of v0.4d, any non-compact or open-ended budget, any search-until-pass or post-hoc sample/seed edit, any pass/fail
upgrade, any implicit opening of B/C or runtime/memory/real-clips, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Larger-N Residual Replication Enumeration v0.7a. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, evaluator, or verdict;
deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no TOL; adopts no new
closure metric; adds no new generator family or axis; makes no vision / descriptor-validity / temporal-order /
memory / runtime / integration claim; no `§0` pointer added; no tags.*
