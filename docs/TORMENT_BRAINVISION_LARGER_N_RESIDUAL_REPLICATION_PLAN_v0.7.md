# TORMENT Brainvision Larger-N Residual Replication Plan v0.7

## 1. Status / non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It pre-registers a *future* larger-N replication (Branch A of v0.6b) that would test which of the v0.6a
separability effects survive when sample support is larger. It **authorizes no code and no tests**, invents no
threshold, **redefines no `TOL`**, adopts **no new closure metric**, proposes no pass/fail rule change, changes
no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control, redesigns no descriptor,
reopens no spectral group, **expands no generator family** (unless separately gated later), and opens **no
classifier (form B) and no neural encoder (form C)**. Everything stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. A plan alone moves nothing: **no claim
lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.4d / v0.5a / v0.6a / v0.6b

```text
v0.4d (77ed133)  Partial: 3/3 held-out matched within TOL (per-pair L-inf), baselines still separate.
v0.5a (37a75f7)  baseline anatomy -> distributed_residual_geometry; protocol_metric_mismatch_flag = True.
v0.6a (910ab34)  residual sufficiency audit -> mixed_metric_and_small_n (on the n = 3 vs 3 matched pairs).
v0.6b (2cf1b14)  synthesis: v0.6a explains (not invalidates) v0.4d; wall better characterized; recommended
                 Branch A (larger-N replication) FIRST -- before any metric change or family expansion.
v0.7  (this doc) pre-registers that Branch A larger-N replication, docs-only, before any code.
```

This replication is **explanatory only** and **additive**: it preserves the v0.4d sealed result and the v0.6a
finding, and asks a companion question at larger sample support. It does not say v0.4d was invalid, does not say
Brainvision failed or succeeded, and changes nothing v0.4b/v0.4c froze.

## 3. Replication question

```text
Which v0.6a separability effects survive when n is larger?
```

At n = 3 vs 3, best-threshold BA saturates to 1.00 whenever two triples are merely rank-separated, so BA alone
is a weak discriminator and the metric-insufficiency vs small-N split rests on the parameter-free robustness
lens. Larger sample support makes rank-separation a stronger (less-by-chance) condition, so BA becomes
discriminating and the robustness lens more stable — directly testing whether the fragile small-N separations
lose their saturated BA while the robust BY-channel separations persist.

## 4. Effects to re-test

```text
A. BY-channel substantive candidates:   by_centroid, by_spread
   (v0.6a: robust; between-class rank gap >> within-class spread; ~46-54% of TOL)
B. Directional tiny-magnitude candidates: u_directional_delta_rms, angular_increment_mag
   (v0.6a: robust-constant within class, but NEGLIGIBLE magnitude ~6% of TOL)
C. Fragile small-N candidates:           by_std, rg_centroid, rg_spread
   (v0.6a: fragile thin-margin rank separation; BA = 1.0 attributed to n = 3 vs 3)
```

Spectral stays audit-note-only and is not re-tested as a closure group.

## 5. Larger-N design constraints

```text
- Synthetic / offline fixtures ONLY; form A, non-learning, reporting-only.
- Larger n is chosen specifically to REDUCE best-threshold BA-saturation sensitivity (so BA discriminates and
  the robustness lens stabilizes).
- The future implementation reports effect PERSISTENCE / COLLAPSE / AMBIGUITY -- NOT a pass/fail upgrade.
- The v0.4d sealed 3-pair result and the v0.6a finding are PRESERVED; the replication is an additive larger-N
  companion, not a rerun/replacement of v0.4d.
- Spectral stays audit-note-only; claim locks and verdict HOLD are preserved under EVERY outcome.
- No runtime / memory / real-clip implication.
```

## 6. What must remain frozen

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (all referenced frozen; not re-thresholded).
- the frozen evaluator: structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR.
- the frozen descriptor / _stats / GROUPS / best-threshold BA / defensive value check (reused by identity).
- proxy_match_residual (L-inf over the ten matched statistics, spectral excluded) and the SOLE non-structure
  feasibility constraint PSC < PSC_FLOOR.
- the CLOSED set of five candidate FAMILIES (F1-F5) and the frozen winder generator -- NO new family.
- the four matched groups; spectral audit-note-only.
- the parameter-free robustness lens (between-class rank gap vs within-class spread, boundary 1.0) --
  descriptive, unchanged; NO new closure metric and NO new threshold adopted.
- claim locks and verdict HOLD.
```

## 7. What may vary

Only the **sample support** may grow — via **more instances of the same frozen generators**, never a new family
or a new descriptor axis:

```text
- MORE winder targets: additional instances from the frozen winder generator at more phase / speed / radius
  parameter points (same generator, more points; NOT a new family).
- MORE candidate instances: additional seeds for the stochastic families (F1 / F4 / hybrid-B) and additional
  parameter points WITHIN the existing families' declared axes (NOT new axes, NOT new families).
- a larger, disjoint development / held-out split; a larger but FINITE and COMPACT search budget.

Compactness: the replication should raise n by roughly an order of magnitude (e.g. from 3 vs 3 toward a few
dozen winders and a few dozen matched candidates), NOT arbitrary huge grids. The exact larger enumeration
(grids / ranges / seeds / split / budget) is fixed in a SEPARATE future docs-gated pre-registration (v0.7a's
own sealed enumeration), decided before any code -- this plan sets only the rules, not the numbers.
```

Any move beyond "more instances of the existing families / winder generator" (a genuinely new candidate family,
a new descriptor axis, a new closure metric, or a `TOL` change) is **out of scope** here and would require a
separate, separately-gated proposal.

## 8. Allowed replication outputs

```text
- per-feature best-threshold BA at larger n (for the effects in §4);
- per-feature signed median difference by label at larger n;
- the parameter-free robustness lens (rank gap vs within-class spread) at larger n;
- an effect PERSISTENCE / COLLAPSE / AMBIGUITY classification per feature (does the robust BY-channel separation
  persist; do the fragile small-N separations collapse; does the directional pair stay rank-separated but
  negligible or collapse);
- whether group-level residual / TOL closure still coexists with feature-level separability at larger n;
- an updated assessment among metric_insufficiency / small_n_optimism / mixed / inconclusive;
- defensive NaN / non-finite / extreme-value handling (reused; non-finite values never become evidence).
```

## 9. Forbidden interpretations

```text
- NO new thresholds; NO TOL redefinition; NO new closure metric; NO pass/fail rule change; NO descriptor redesign.
- NO generator-family expansion (only more instances of the existing families / winder generator).
- NO pass/fail UPGRADE from the replication (report persistence / collapse / ambiguity, not a Brainvision pass).
- NO treating effect persistence as descriptor validity or as vision / "Brainvision sees" evidence.
- NO temporal-order reading; spectral stays audit-note-only, not reopened as a closure group.
- NO claim-lock or verdict movement; NO runtime / memory / integration authorization.
- Does NOT say v0.4d was invalid, and does NOT say Brainvision failed or succeeded.
```

## 10. Candidate outcomes

```text
A. BY_persistence_metric_insufficiency
   BY-channel effects (by_centroid / by_spread) persist under larger n -> supports real residual metric insufficiency.
B. directional_collapse_tiny_magnitude
   directional BA / rank separation collapses or stays negligible with larger n -> supports tiny-magnitude / small-N.
C. small_n_features_collapse
   by_std / rg_centroid / rg_spread lose saturated BA -> supports small-N optimism.
D. mixed_effects_persist
   some robust metric-insufficiency effects AND some small-N effects both persist -> mixed explanation remains.
E. replication_inconclusive
   the larger-N design cannot resolve the issue without changing metrics / families -> no claim movement.
```

All of A / B / C / D / E are research-only descriptions and leave the claim locks and verdict unchanged.

## 11. What would count as useful evidence

The evidence is the **persistence-vs-collapse pattern** of the §4 effects under larger sample support — **not** a
pass, a new threshold, or a validity statement:

```text
- BY-channel PERSISTS robust while the fragile features COLLAPSE  -> the metric-insufficiency component is real
  and the small-N component was an artifact (outcomes A + C).
- directional stays rank-separated but negligible, or collapses    -> the directional evidence was tiny-magnitude
  / small-N (outcome B), and should not be weighted as metric insufficiency.
- both robust and small-N effects persist                          -> the mixed characterization holds (outcome D).
- the design cannot separate them at feasible n                    -> inconclusive (outcome E); no claim movement.
```

The larger-N result would sharpen *which* part of the v0.6a wall is real, without upgrading any claim.

## 12. What would still not be proven

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

## 13. Recommended next step

```text
1. Codex review THIS plan (docs-only; over committed edge 2cf1b14).
2. If accepted, commit this plan doc. No §0 pointer; no tags.
3. Only THEN, and only on explicit operator instruction, may a SEPARATE future v0.7a step (a) pre-register the
   exact larger enumeration (grids / ranges / seeds / split / compact finite budget) as a docs-gated step, then
   (b) implement EXACTLY this reporting-only replication -- form A, non-learning, frozen descriptor / evaluator /
   families / winder generator / robustness lens / TOL reused by identity, delivered UNCOMMITTED for review,
   Windows the source of truth. This plan authorizes no such code by itself.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 14. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_LARGER_N_RESIDUAL_REPLICATION_PLAN_v0.7.md
(new, docs-only, untracked; over committed edge 2cf1b14, pre-registering Branch A from v0.6b).

Verify that this plan:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
- plans a larger-N REPLICATION to test which v0.6a effects survive larger n (BY-channel by_centroid/by_spread;
  directional u_directional_delta_rms/angular_increment_mag; fragile by_std/rg_centroid/rg_spread), motivated by
  reducing best-threshold BA-saturation sensitivity at n = 3 vs 3;
- keeps frozen: TOL (0.0634), PSC_FLOOR/AIC_FLOOR (0.30), CHANCE_BAND (0.60), the evaluator, the descriptor /
  GROUPS / proxy_match_residual / PSC<PSC_FLOOR feasibility / robustness lens -- invents NO threshold, redefines
  NO TOL, adopts NO new closure metric, redesigns NO descriptor;
- lets ONLY sample support grow, via MORE INSTANCES of the existing five families (F1-F5) and the frozen winder
  generator (more seeds / more parameter points), and EXPANDS NO generator family and NO descriptor axis; defers
  the exact larger enumeration to a separate future docs-gated pre-registration with a COMPACT finite budget
  (order-of-magnitude, not arbitrary huge grids);
- preserves the v0.4d sealed result and v0.6a finding (additive, not a rerun/replacement); keeps spectral
  audit-note-only;
- limits outputs to reporting-only per-feature BA / signed median difference / robustness lens / persistence-
  collapse-ambiguity classification / coexistence check, and forbids any pass/fail upgrade;
- lists candidate outcomes A BY_persistence / B directional_collapse / C small_n_collapse / D mixed_persist /
  E inconclusive, all leaving claim locks and verdict unchanged;
- does NOT say v0.4d was invalid, does NOT say Brainvision failed or succeeded, does NOT move claim locks or
  authorize runtime/memory/integration; preserves all claim locks
  (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; no §0; no tags.

Flag any threshold invention, any TOL redefinition, any new closure metric, any descriptor redesign, any
generator-family expansion (vs more instances of existing families), any pass/fail upgrade, any implicit opening
of B/C or runtime/memory/real-clips, any claim-lock/verdict movement, or any statement that v0.4d was invalid or
Brainvision failed/succeeded.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Larger-N Residual Replication Plan v0.7. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, evaluator, or verdict;
deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no TOL; adopts no new
closure metric; expands no generator family; makes no vision / descriptor-validity / temporal-order / memory /
runtime / integration claim; no `§0` pointer added; no tags.*
