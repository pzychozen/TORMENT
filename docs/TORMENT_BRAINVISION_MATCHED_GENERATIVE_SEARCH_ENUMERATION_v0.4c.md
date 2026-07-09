# TORMENT Brainvision Matched Generative Search Enumeration v0.4c

## 1. Status / non-claims

**DOCS-ONLY enumeration. Non-authorizing, non-implementing. Opens no code, no tests, no generator, no runtime,
no integration lane.** It seals the concrete grid / ranges / seeds / splits that the v0.4b protocol deferred, so
a *future* Direction-B matched-generative-search slice, if ever separately gated, is fully specified in advance
and cannot be tuned toward a win. Sealing an enumeration is **not** authorizing implementation: no code is
authorized here; any implementation still requires separate explicit operator instruction (§15). It
**authorizes no code and no tests**, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or
weakens no control, redesigns no descriptor, invents no threshold **outside** the choices v0.4b already
authorized v0.4c to make (§3, §5–§10), and opens **no classifier (form B) and no neural encoder (form C)**.
Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. Brainvision Path B remains **not
proven vision** and **not a functioning vision layer for TORMENT memory**. An enumeration alone moves nothing:
**no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.4 / v0.4a / v0.4b

```text
v0.4  (54daf01)  proposed the different construction; accepted Direction B, no implementation.
v0.4a (80a6242)  planned matched generative search as a META-PLAN (rules/shape only).
v0.4b (bae9753)  closed TOL and the protocol rules; deferred the numeric enumeration.
v0.4c (this doc) seals the numeric enumeration: family list, grid/ranges, seeds, dev/held-out split, budget.
```

v0.4c changes **no** frozen protocol threshold (TOL, PSC_FLOOR, AIC_FLOOR, CHANCE_BAND stay exactly as v0.4b
froze / referenced them). It only fills in the enumeration slots v0.4b explicitly left to a later reviewed
appendix/amendment. Once sealed here, the enumeration is immutable except via a future docs-only, Codex-reviewed
amendment reviewed **before** any rerun (§12). Where v0.4c is more specific than v0.4b, it only tightens.

## 3. Frozen anchors

Reused **by identity** from frozen, committed code / prior committed docs; v0.4c authors no new descriptor,
generator, or protocol threshold:

```text
run_all_shortcuts_closed_synthetic_v0_3.py  GROUPS (proxy mapping), ALL_PROXIES, _linf_residual (raw-delta
                                            L-inf), _feat, CHANCE_BAND = 0.60
run_color_structure_v0_8.py                 structure_score, _stats, PSC_FLOOR = 0.30, AIC_FLOOR = 0.30, T
run_color_structure_spectral_std_blocker_v1_9.py   _winder / _series_theta / _outback / _arc_osc / _collinear
run_color_structure_by_std_residual_v2_0.py        _winder(radius fraction)

Frozen evaluator (UNCHANGED):     structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR
Sole feasibility constraint:      PSC < PSC_FLOOR      (non-structure; NO AIC constraint added -- v0.4b §5)
Frozen match target (v0.4b §6/§7): proxy_match_residual = L-inf over MATCHED_STATS (spectral excluded);
                                   MATCH iff residual <= TOL, TOL = 0.0634 (frozen v0.3 residual ceiling)
MATCHED groups (v0.4b §4):         movement_channel_energy, directional, per_channel, frame_diff
                                   (spectral audit-note-only)
```

Every numeric value in §5–§10 that is **not** in the block above (family parameter values, seeds, split,
budget) is an **enumeration choice** v0.4b authorized v0.4c to make; none is a descriptor decision threshold.

## 4. Closed candidate family list

The candidate non-winder generator families are a **closed, finite set of five**. The future search may
instantiate candidates **only** from these families:

```text
F1  full_circle_incoherent_traversal        full angular coverage, per-step phase incoherent -> PSC low
F2  rosette_multilobe_traversal             multi-lobe coverage without net winding
F3  segment_paired_canceller                paired out/back segments; net turn cancels (cf. frozen v0.3 outback)
F4  phase_scrambled_full_coverage           coverage preserved, per-step phase scrambled
F5  hybrid_coverage_preserving_canceller    declared finite combinations of F1-F4
```

The set is SEALED. No family may be added, removed, or substituted after seeing implementation results without
a future docs-only amendment reviewed by Codex **before** any rerun (§12).

## 5. Exact search grid / parameter ranges

All grids are compact and finite. Deterministic families consume no seed; stochastic families (F1, F4, and the
F1-based hybrid combo) draw one instance per (param-combo, seed) from the §6 pools.

```text
F1 full_circle_incoherent_traversal        (stochastic)
   base_angular_travel = 1.0 (one full circle)            # fixed
   incoherence_sigma   in {0.3, 0.6, 1.0}                 # per-step phase-noise stdev (rad)
   -> 3 param-combos x |seed pool|

F2 rosette_multilobe_traversal             (deterministic)
   lobes       in {2, 3, 5}
   radius_frac in {0.7, 1.0}
   -> 6 combos

F3 segment_paired_canceller                (deterministic; increments reused from frozen v0.3 outback set)
   increment_g in {0.10, 0.20, 0.30, 0.50, 0.79}          # subset of frozen v0.3 _cancellers() outback g
   pairs       in {1, 2}
   -> 10 combos

F4 phase_scrambled_full_coverage           (stochastic)
   scramble_sigma in {0.5, 1.0, 1.5}                      # per-step phase-scramble stdev (rad)
   -> 3 param-combos x |seed pool|

F5 hybrid_coverage_preserving_canceller    (2 declared combos; combo B uses an F1 component -> stochastic)
   comboA = F2(lobes=3, radius_frac=1.0) + F3(increment_g=0.30, pairs=1)   mix=0.5   (deterministic)
   comboB = F1(incoherence_sigma=0.6)    + F3(increment_g=0.50, pairs=2)   mix=0.5   (stochastic: F1 seed)
   -> comboA: 1 instance ; comboB: 1 param-combo x |seed pool|
```

**Target winders** (the STRUCTURE class the candidates are matched against) are the frozen v0.3 `_winders()`
set, reused by identity — not re-authored:

```text
{ winder_sp0.5, winder_sp1.0, winder_sp2.0, winder_ph0.00, winder_ph1.57, winder_ph3.14, winder_r0.7, winder_r0.5 }
```

Sequence length `T` is the frozen `cs.T`; it is not chosen here.

## 6. Exact seed policy

Fixed explicit seeds (preferred over vague randomness). Development and held-out pools are **disjoint** and
sealed:

```text
development_seeds = [20260709, 20260710, 20260711]     # |pool| = 3
heldout_seeds     = [20260712, 20260713]               # |pool| = 2
```

A stochastic candidate instance is produced by exactly one (param-combo, seed) pair from the pool active in the
current phase (development seeds during construction; held-out seeds during the single-shot held-out
evaluation). Deterministic families ignore seeds. **No seed outside these lists may be used; no seed may be
added or swapped after seeing results (§12).**

## 7. Development family set

Used for search construction / debugging (may be inspected and iterated on **before** the held-out phase):

```text
development_targets = [ winder_sp0.5, winder_sp1.0, winder_sp2.0, winder_ph0.00, winder_ph1.57 ]   # 5 targets
development_seeds   = [ 20260709, 20260710, 20260711 ]                                              # 3 seeds

Candidates per development target (full grid, one pass):
   F1 3x3 = 9 | F2 6 | F3 10 | F4 3x3 = 9 | F5 (comboA 1 + comboB 3) = 4     -> 38 candidates / target
Development evaluations = 5 targets x 38 = 190
```

## 8. Held-out family set

Evaluated **once** (§9). Disjoint from development in both target winders and seeds:

```text
heldout_targets = [ winder_ph3.14, winder_r0.7, winder_r0.5 ]     # 3 targets
heldout_seeds   = [ 20260712, 20260713 ]                          # 2 seeds

Candidates per held-out target (full grid, one pass):
   F1 3x2 = 6 | F2 6 | F3 10 | F4 3x2 = 6 | F5 (comboA 1 + comboB 2) = 3     -> 31 candidates / target
Held-out evaluations = 3 targets x 31 = 93
```

The same closed family set (§4) and grid (§5) apply in both phases; only the target-winder subset and the seed
pool differ, so held-out instances are never those inspected during construction.

## 9. Single-shot held-out rule

```text
- development targets/seeds are for search construction and debugging;
- held-out targets/seeds are evaluated EXACTLY ONCE;
- NO tuning, re-selection, grid edit, seed change, TOL change, or family change after held-out results;
- held-out failure is reported as failure or partial (§11); NO invisible reruns;
- held-out targets/seeds are NEVER replaced or reassigned after seeing results.
```

If any of these is violated the run is Invalid / protocol breach (§11) and carries no evidential weight.

## 10. Run-count and retry policy

A **finite** search budget; the future code must not keep searching until it passes.

```text
SEARCH_BUDGET (sealed):
   development phase = 190 candidate-target proxy_match evaluations (§7)
   held-out phase    =  93 candidate-target proxy_match evaluations (§8)
   total             = 283 evaluations, each the full enumerated grid evaluated EXACTLY ONCE per target.

Retry policy:
   - NO random restarts, NO extra seeds beyond the §6 pools, NO "search until match."
   - a candidate that is infeasible (PSC >= PSC_FLOOR, i.e. it winds) or degenerate is recorded as
     invalid-candidate and SKIPPED; it is NOT redrawn and the budget is NOT topped up (cf. v0.3 bounded
     guard: mark-invalid, no redraw-until-desired).
   - per target the search keeps only the min-residual FEASIBLE candidate; ties broken by lowest seed then
     lexicographic family/param order (deterministic, declared).
```

## 11. Outcome classification rules

Evaluated on the held-out set (§8) after the single-shot pass. The per-target and per-group numbers are always
reported in full; the outcome label follows v0.4b §11. "Strict majority of held-out targets" means >= 2 of the
3 held-out targets — a sealed **reporting aggregation** (reused Brainvision field-majority convention), not a
descriptor threshold.

```text
Match-feasible
   feasible matched candidates (PSC < PSC_FLOOR AND proxy_match_residual <= TOL) exist for a STRICT MAJORITY
   (>= 2/3) of held-out targets, AND the pooled held-out cheap-baseline audit closes ALL FOUR matched groups
   (each best-threshold BA <= CHANCE_BAND = 0.60), AND the frozen evaluator still separates winders from the
   matched non-winders on held-out.

Match-infeasible
   across the sealed held-out budget, NO admissible candidate reaches residual <= TOL for ANY held-out target
   (all residuals > TOL; enumerated space exhausted). Residuals reported; stable residual floor noted (e.g. BY
   statistics, per v0.3).

Partial
   anything strictly between the two above -- some held-out targets match and/or some but not all four matched
   groups close. Reported per-target and per-group; never rounded up to "closed."

Invalid / protocol breach
   any §12 forbidden objective/tuning/amendment occurred; or an infeasible candidate was counted as a match;
   or the budget was exceeded; or the held-out single-shot rule (§9) was violated. The run is INVALID, carries
   NO evidential weight, and moves NO claim.
```

Under **every** outcome the claim locks and verdict are unchanged.

## 12. Forbidden tuning / forbidden amendments

The generator's **only** objective is `proxy_match_residual` under the §3 feasibility constraint. Forbidden
objectives (never optimized, targeted, or used as a stopping criterion):

```text
- the final fixed-rule decision score
- PSC/AIC balanced accuracy
- any classifier score
- S_best_threshold
- label accuracy
- held-out performance
- any post-hoc shortcut metric chosen after seeing results
- the cheap-baseline BA as a direct optimizer
- "tuning until cheap baselines look chance-like"
```

Forbidden amendments (all require a future docs-only, Codex-reviewed amendment BEFORE any rerun):

```text
- adding / removing / substituting a candidate family (§4);
- editing any grid value, range, or the family parameter set (§5);
- changing, adding, or swapping any seed (§6) or the dev/held-out split (§7, §8);
- loosening TOL, narrowing the space, dropping an adversarial baseline, or re-selecting proxies to force a pass;
- increasing the SEARCH_BUDGET or adding retries/restarts (§10);
- iterating on held-out families/seeds, or replacing them after seeing results (§9).
```

The generator is **blind** to the frozen evaluator's decision and to the baselines' accuracy while it searches;
those are measured only afterward, on held-out.

## 13. What would count as useful evidence

The evidence is the search's **matching success/failure** plus the **held-out cheap-baseline behaviour** —
**not** any decision score, classifier accuracy, or label accuracy.

```text
Match-feasible reading (research-only):
   the proxy wall is NOT fundamental to the winder/canceller family -- within the sealed enumeration a matched
   family is constructible and the frozen evaluator retains separation the closed cheap proxies lack.
   Establishes NO vision / validity / real-world property (§14).

Match-infeasible reading (research-only):
   Outcome-4-style evidence that the obstruction is structural for this fixture family -- the proxy wall is a
   property of the construction, not fixable by search within the sealed enumeration.
```

A partial result is itself informative and reported as partial (§11). An invalid run is evidence of nothing.

## 14. What would still not be proven

Even a fully successful matched search would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

A matched family plus retained separation would be an **in-vitro synthetic** result about constructible
fixtures within one sealed enumeration; it says nothing about real clips and does not validate the descriptor
as measuring real visual structure. Symmetrically, an infeasibility result would **not** prove the descriptor
invalid — only that this construction route cannot close the shortcuts within the sealed enumeration. The claim
locks (`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`,
`descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force under every §11 outcome.

## 15. Recommended next step

```text
1. Codex review THIS enumeration (docs-only; over committed edge bae9753).
2. If accepted, commit this enumeration doc. No §0 pointer; no tags.
3. Only THEN, and only on explicit operator instruction, may a SINGLE offline implementation slice implement
   EXACTLY the v0.4b protocol + this sealed v0.4c enumeration -- form A, non-learning, frozen descriptor /
   generators / constants reused by identity, delivered UNCOMMITTED for review, Windows the source of truth.
   Neither this doc nor v0.4b authorizes code by itself.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 16. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_MATCHED_GENERATIVE_SEARCH_ENUMERATION_v0.4c.md
(new, docs-only, untracked; over committed edge bae9753, sealing the numeric enumeration v0.4b deferred).

Verify that this enumeration:
- is docs-only and authorizes no implementation (no code/tests/generator, no torment_service/, no runtime,
  no memory, no camera/live/sensor/screen/streaming, no real clips); sealing is NOT authorization;
- keeps form B (classifier) and form C (neural encoder) CLOSED; describes only a form-A, non-learning,
  baseline-gated, offline generator/probe over fixture PARAMETERS;
- changes NO frozen protocol threshold: TOL = 0.0634, PSC_FLOOR/AIC_FLOOR = 0.30, CHANCE_BAND = 0.60 are all
  referenced frozen; the SOLE feasibility constraint stays PSC < PSC_FLOOR (no AIC constraint); the frozen
  evaluator (structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR) is unchanged; MATCHED groups and spectral-
  audit-note-only are unchanged from v0.4b;
- seals a CLOSED finite 5-family list (F1-F5), a compact finite grid (§5, F3 increments reused from frozen v0.3
  outback), explicit disjoint development/held-out seed lists and target-winder split (§6-§8), and a finite
  SEARCH_BUDGET (283 evaluations, full grid once per target, no restarts/retries/redraws);
- makes held-out single-shot (§9) and defines outcome rules (§11) using only frozen quantities (TOL, PSC_FLOOR,
  CHANCE_BAND) plus a declared reporting aggregation (>= 2/3 held-out targets); the >= 2/3 majority is an
  outcome-reporting aggregation, NOT a new descriptor threshold;
- FORBIDS optimizing the decision score, PSC/AIC BA, any classifier score, S_best_threshold, label accuracy,
  held-out performance, any post-hoc shortcut metric, the cheap-baseline BA as a direct optimizer, or
  tuning-until-baselines-look-chance; and forbids post-hoc family/grid/seed/split/budget amendments without a
  reviewed docs-only amendment before rerun;
- reports match-feasible / match-infeasible / partial / invalid honestly, preserves all claim locks
  (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD under every outcome;
- makes no vision / "Brainvision sees" / temporal-order / descriptor-validity / memory-readiness /
  runtime-readiness / integration-readiness claim; adds no §0 pointer and no tags.

Flag any changed protocol threshold, any AIC feasibility constraint, any objective that would let the generator
optimize a decision/baseline/label score, any unbounded/expensive grid, any non-sealed or reassignable seed/
split, any budget that permits search-until-pass, any implicit opening of B/C or runtime/memory/real-clips, or
any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Matched Generative Search Enumeration v0.4c. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, evaluator, or verdict;
deletes or weakens no control; redesigns no descriptor; invents no threshold outside the v0.4b-authorized
enumeration; makes no vision / descriptor-validity / temporal-order / memory / runtime / integration claim; no
`§0` pointer added; no tags.*
