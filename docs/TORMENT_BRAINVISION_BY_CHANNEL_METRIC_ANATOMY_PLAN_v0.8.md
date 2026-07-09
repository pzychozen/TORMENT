# TORMENT Brainvision BY-Channel Metric Anatomy Plan v0.8

## 1. Status / non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It pre-registers a *future* explanatory diagnostic (Branch A of v0.7c) that would inspect **why** the
BY-channel features (`by_centroid`, `by_spread`, `by_std`) persist as substantial residual separability under
the existing residual / `TOL` protocol, even after larger-N replication dissolved the directional / RG / small-N
artifacts. It **authorizes no code and no tests**, invents no threshold, **redefines no `TOL`**, adopts **no new
closure metric**, proposes no pass/fail rule change, changes no formula / §7 anti-proxy logic / §8 verdict
logic, deletes or weakens no control, redesigns no descriptor, reopens no spectral group, expands no generator
family, adds no new axis, and opens **no classifier (form B) and no neural encoder (form C)**. Everything stays
offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

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

## 2. Relation to v0.6a / v0.7b / v0.7c

```text
v0.6a (910ab34)  residual sufficiency audit -> mixed_metric_and_small_n (on n = 3 vs 3 matched pairs).
v0.7b (978bb36)  larger-N replication -> BY_persistence_metric_insufficiency: BY-channel (by_centroid / by_spread
                 / by_std) persists substantial; directional / rg weaken to negligible; perfect BA = 1.0
                 saturation collapsed for all (small-N pervasive).
v0.7c (ca3a95f)  synthesis: v0.7b SHARPENED and LOCALIZED the wall to BY-channel opponent-axis geometry; does NOT
                 prove Brainvision / validate the descriptor / invalidate prior work; recommended Branch A.
v0.8  (this doc) pre-registers that Branch A BY-channel anatomy diagnostic, docs-only, before any code.
```

This diagnostic is **explanatory, not corrective**: it is not trying to make Brainvision pass — it is trying to
explain the localized surviving wall. It changes nothing v0.4b/v0.4c/v0.7a froze or v0.7b produced.

## 3. BY-channel anatomy question

```text
Why do the BY-channel features (by_centroid, by_spread, by_std) persist as substantial residual separability
under the existing residual / TOL protocol -- what property of the blue-yellow opponent axis does a per-pair
L-inf <= TOL match leave systematically unclosed?
```

## 4. Features to inspect

```text
PRIMARY target (BY-channel):
  by_centroid    by_spread    by_std

COMPARISON features (context, NOT the main target):
  rg_centroid    rg_spread    u_directional_delta_rms    angular_increment_mag
```

The comparison features are the ones that **weakened to negligible** at larger n (v0.7b); they anchor a BY-vs-RG
and BY-vs-directional contrast. Spectral stays audit-note-only and is not inspected as a closure group.

## 5. Candidate explanations

```text
A. Opponent-axis asymmetry
   The synthetic matching closes global residuals while leaving a systematic blue-yellow axis offset.
B. Coverage geometry
   Winder / canceller candidates cover the chroma path differently in BY even when residual / TOL is satisfied.
C. Centroid / spread coupling
   by_centroid and by_spread are not independent; the closure metric may match one while allowing coupled
   separability in the other.
D. by_std amplitude / channel-energy leakage
   by_std persistence may indicate residual channel-energy or amplitude imbalance rather than structural geometry.
E. Residual aggregation problem
   The L-inf / group residual compresses feature-level BY separability too much (per-pair match hides BY ordering).
F. Generator-family artifact
   The existing F1-F5 surfaces may make BY-channel closure structurally harder than RG closure.
```

## 6. Allowed diagnostic outputs

The future diagnostic (a separate, later v0.8a code step — **not opened here**) would be **reporting-only** and
would reuse the v0.7b (and v0.4d / v0.5a / v0.6a) records **by identity** — no rerun with new parameters, no
replaced sample, no new family. Allowed outputs:

```text
- per-feature BY vs RG comparison (by_* vs rg_* separability / effect size);
- by_centroid / by_spread / by_std signed-difference distributions;
- effect persistence across matched vs unmatched larger-N targets;
- correlation / coupling between by_centroid and by_spread;
- whether by_std tracks amplitude / channel-energy more than geometry;
- whether BY persistence concentrates in specific winder parameter regions (speed / phase / radius);
- whether BY persistence appears in all F1-F5 candidate families or only some;
- whether the unmatched larger-N targets are BY-dominated failures;
- whether residual aggregation (L-inf / group) hides BY feature-level ordering.
```

## 7. Forbidden interpretations

```text
- NO new thresholds; NO changing TOL; NO new closure metric; NO pass/fail rule change.
- NO descriptor redesign; NO new generator families; NO new axis; NO control weakening.
- NO tuning until BY closes; NO replacing the v0.7b samples; NO rerun with new parameters.
- NO treating BY anatomy as vision / "Brainvision sees" evidence.
- NO treating BY persistence as descriptor validity.
- NO temporal-order reading; spectral stays audit-note-only, not reopened as a closure group.
- NO claim-lock or verdict movement; NO runtime / memory / integration authorization.
```

## 8. What would count as useful evidence

The evidence is the **descriptive pattern** of where the BY persistence lives — **not** a pass, a new threshold,
or a validity statement. Candidate future outcomes:

```text
A. BY_axis_asymmetry
   BY persistence appears as a systematic opponent-axis offset (blue-yellow) the per-pair match leaves unclosed.
B. BY_centroid_spread_coupling
   by_centroid and by_spread are coupled in a way the residual metric does not close.
C. BY_amplitude_leakage
   by_std persistence appears tied to channel-energy / amplitude leakage rather than structural geometry.
D. BY_family_artifact
   BY persistence is concentrated in specific existing F1-F5 candidate families (not uniform across families).
E. BY_metric_compression
   BY feature-level ordering survives because group-level residual aggregation is too compressed.
F. BY_anatomy_inconclusive
   the existing records cannot distinguish these causes without a separately gated plan; no claim movement.
```

All of A / B / C / D / E / F are research-only descriptions and leave the claim locks and verdict unchanged.

## 9. What would still not be proven

Even a completed BY-channel anatomy would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

Explaining where the BY persistence lives is an in-vitro synthetic, metric-level description within the same
family set; it says nothing about real clips and does not validate the descriptor. The proof route remains
**HELD / HOLD**. The claim locks (`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`,
`descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force under every outcome.

## 10. Candidate next branches after anatomy

```text
If E (BY_metric_compression):
   -> a SEPARATE, future docs-first BY-channel closure metric PROPOSAL comparing feature-level BY separability
      against the group residual -- WITHOUT adopting thresholds. (Proposal only; no code, no metric adopted.)
If A / B (BY_axis_asymmetry / BY_centroid_spread_coupling):
   -> a SEPARATE, future operator / new-math intuition step on whether this reflects a deeper chroma-plane /
      opponent-axis geometry issue. (Framing only; no descriptor redesign.)
If C (BY_amplitude_leakage):
   -> a SEPARATE, future reporting-only check of whether by_std is a channel-energy / amplitude proxy rather
      than geometry. No control change.
If D (BY_family_artifact):
   -> a SEPARATE, future reviewed consideration of the F1-F5 family composition -- gated; NOT a family expansion
      opened here.
If F (BY_anatomy_inconclusive):
   -> HOLD, or gather more records first; no claim movement.

Pausing Brainvision and returning to TORMENT memory / kernel work remains a legitimate operator call.
```

## 11. Recommended next step

```text
1. Codex review THIS plan (docs-only; over committed edge ca3a95f).
2. If accepted, commit this plan doc. No §0 pointer; no tags.
3. Only THEN, and only on explicit operator instruction, may a SEPARATE future v0.8a code diagnostic implement
   EXACTLY this reporting-only anatomy on the reused v0.7b (and v0.4d / v0.5a / v0.6a) records -- form A,
   non-learning, frozen surfaces reused by identity, inventing no threshold, redefining no TOL, adopting no
   closure metric, expanding no family, delivered UNCOMMITTED for review, Windows the source of truth. This
   plan authorizes no such code by itself.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 12. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_CHANNEL_METRIC_ANATOMY_PLAN_v0.8.md
(new, docs-only, untracked; over committed edge ca3a95f, pre-registering Branch A from v0.7c).

Verify that this plan:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
- is EXPLANATORY not corrective: it explains WHY by_centroid / by_spread / by_std persist under residual / TOL,
  and does NOT try to make Brainvision pass, close BY, or tune anything;
- inspects the BY-channel features (by_centroid / by_spread / by_std) as the primary target with rg_* and the
  directional pair as comparison context, and keeps spectral audit-note-only (NOT reopened as a closure group);
- reuses the v0.7b (and v0.4d / v0.5a / v0.6a) records BY IDENTITY: reruns nothing with new params, replaces no
  sample, adds no generator family, invents no threshold, changes no descriptor / control, and does NOT redefine
  TOL or adopt any new closure metric;
- lists candidate explanations (opponent-axis asymmetry / coverage geometry / centroid-spread coupling / by_std
  amplitude-channel-energy leakage / residual aggregation compression / generator-family artifact) and limits
  outputs to reporting-only anatomy (BY-vs-RG comparison, signed-difference distributions, matched-vs-unmatched
  persistence, centroid-spread coupling, by_std amplitude tracking, winder-region concentration, per-family
  concentration, unmatched-target analysis, residual-aggregation hiding);
- lists candidate outcomes A BY_axis_asymmetry / B BY_centroid_spread_coupling / C BY_amplitude_leakage /
  D BY_family_artifact / E BY_metric_compression / F BY_anatomy_inconclusive, all leaving claim locks and verdict
  unchanged;
- forbids new thresholds, TOL change, new closure metric, descriptor redesign, new families, tuning-until-BY-
  closes, sample replacement, and treating BY anatomy as descriptor validity or vision evidence;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any threshold invention, any TOL change, any closure-metric adoption, any descriptor redesign, any new
family, any tuning-toward-closure, any sample replacement, any implicit opening of B/C or runtime/memory/real-
clips, any claim-lock/verdict movement, or any overclaim of the future anatomy.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Channel Metric Anatomy Plan v0.8. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, evaluator, or verdict;
deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no TOL; adopts no
closure metric; expands no generator family; makes no vision / descriptor-validity / temporal-order / memory /
runtime / integration claim; no `§0` pointer added; no tags.*
