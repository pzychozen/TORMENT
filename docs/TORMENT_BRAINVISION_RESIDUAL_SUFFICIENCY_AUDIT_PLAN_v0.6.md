# TORMENT Brainvision Residual Sufficiency Audit Plan v0.6

## 1. Status / non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It pre-registers a *future* explanatory audit (Branch A of v0.5b) that would examine whether the v0.4d
group-level residual / `TOL` closure metric is too compressed or too weak compared to feature-level baseline
separability. It **authorizes no code and no tests**, invents no threshold, **redefines no `TOL`**, proposes no
pass/fail rule change, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no
control, redesigns no descriptor, reruns / replaces no v0.4d sealed candidate, adds no generator family, and
opens **no classifier (form B) and no neural encoder (form C)**. Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. Brainvision Path B remains **not
proven vision**. A plan alone moves nothing: **no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.4d / v0.5a / v0.5b

```text
v0.4d (77ed133)  Partial: 3/3 held-out matched within TOL (per-pair L-inf residual), yet the four matched
                 cheap-baseline groups still separated.
v0.5a (37a75f7)  baseline anatomy -> distributed_residual_geometry; protocol_metric_mismatch_flag = True;
                 group max BA movement/directional/per_channel = 1.0, frame_diff = 0.833; distributed = 3,
                 concentrated = 0; small-N caveat preserved.
v0.5b (b5d6676)  synthesis: v0.5a does NOT invalidate v0.4d -- it EXPLAINS why v0.4d stayed Partial; the wall is
                 now a closure-metric sufficiency gap; recommended Branch A (residual sufficiency audit).
v0.6  (this doc) pre-registers that Branch A audit, docs-only, before any code.
```

This audit is **explanatory only**. It does **not** say v0.4d was invalid, does not say Brainvision failed or
succeeded, and changes nothing v0.4b/v0.4c froze or v0.4d/v0.5a produced.

## 3. Audit question

```text
Is the v0.4d group-level residual / TOL closure metric (per-pair L-inf over the ten matched statistics <= TOL)
too COMPRESSED or too WEAK compared to the feature-level, class-level separability the adversarial baselines
exploit -- and how much of the surviving separability is metric insufficiency versus small-N optimism?
```

## 4. Why residual sufficiency is now suspect

```text
- v0.4d closure is a PER-PAIR, SINGLE-NUMBER L-inf summary: is each winder within TOL of ITS OWN matched
  candidate on the worst of the ten matched statistics?
- The baseline audit is a CLASS-LEVEL, PER-FEATURE best-threshold quantity: can some feature separate the
  GROUP of winders from the GROUP of candidates?
- v0.4d showed all 3 per-pair matches held (<= TOL) while all four groups still separated
  (protocol_metric_mismatch_flag = True). v0.5a showed the separability is DISTRIBUTED across features, with the
  genuine effect-size residual in BY / amplitude statistics and much BA saturation attributable to small N.
- So a per-pair L-inf <= TOL summary can COEXIST with class-level, multi-feature separability: the metric may
  compress multi-feature ordering into one distance and thereby fail to represent what the baselines use.
```

This is a suspicion to *audit*, not a conclusion and not a reason to change any threshold.

## 5. What the audit may inspect

The future audit (a separate, later v0.6a code step — **not opened here**) would be **reporting-only** and would
reuse the v0.4d / v0.5a records **by identity** (the same sealed matched held-out pairs and per-feature anatomy;
no rerun with new parameters, no replaced candidate, no new family):

```text
- compare each group's group-level residual against its per-feature best-threshold BA;
- compare group-level residuals against per-feature signed median differences;
- identify features with SMALL signed median difference but SATURATED BA (the small-N optimism signature);
- identify whether residual closeness is hiding class-separable ORDERING (winder-set vs candidate-set fully
  rank-separated on a feature despite small per-pair residual);
- distinguish metric insufficiency from sample-size optimism (how the picture depends on the n=3 vs 3 regime);
- examine, descriptively, whether TOL is too permissive OR whether the L-inf (worst-stat) residual is simply the
  wrong sufficiency STRUCTURE for representing class-level multi-feature ordering -- WITHOUT choosing a new TOL;
- identify what a stricter FUTURE closure proposal would need to consider (per-feature anatomy, rank-order
  tests, sign-consistency tests, or larger-N evidence) -- as questions to carry forward, not as adopted rules.
```

## 6. What the audit must not change

```text
- NO TOL redefinition; NO replacement threshold; NO new pass/fail rule; NO immediate closure-rule change.
- NO rerunning / replacing the v0.4d sealed candidates; NO changed family / grid / seed / envelope.
- NO new generator family; NO descriptor redesign; NO control weakening.
- NO moving claim locks or the verdict; NO authorizing runtime / memory / integration / real clips.
- The audit reuses v0.4d / v0.5a artifacts by identity and only DESCRIBES the metric-vs-separability
  relationship. Spectral stays audit-note-only and is not reopened as a closure group.
```

## 7. Candidate audit outputs

```text
- group-level residual vs per-feature BA table (per matched group);
- group-level residual vs per-feature signed median difference table;
- a flag per feature for "small signed median difference but saturated BA" (small-N optimism signature);
- a rank-ordering / class-separability description per feature (is the winder-set fully separated from the
  candidate-set despite small per-pair residual);
- a descriptive split of surviving separability into metric-insufficiency vs small-N contributions;
- an explicit descriptive note on whether TOL permissiveness or L-inf STRUCTURE is the more likely gap
  (reporting-only; proposes no new value);
- a carried-forward list of what a future stricter closure proposal would need (NOT an adopted rule).
```

## 8. What would count as useful evidence

The evidence is the **relationship** between the group-level residual metric and feature-level class
separability (and its dependence on N) — **not** a pass, a new threshold, or a validity statement. Candidate
future outcomes:

```text
A. residual_metric_insufficient
   group-level residual / TOL closure can COEXIST with feature-level class separability -> the metric is too
   compressed / too weak to represent what the baselines use.
B. small_n_baseline_optimism
   the baseline BA saturation appears mostly an artifact of n=3 vs 3 (BA ~1.0 at near-zero effect size) rather
   than genuine class separability.
C. mixed_metric_and_small_n
   both metric insufficiency and small-N optimism contribute.
D. audit_inconclusive
   the existing v0.4d / v0.5a records are insufficient to distinguish the above; no claim movement.
```

All of A / B / C / D are research-only descriptions and leave the claim locks and verdict unchanged.

## 9. What would still not be proven

Even a completed residual-sufficiency audit would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

Describing whether a closure metric was sufficient is an in-vitro synthetic, metric-level observation within one
sealed enumeration; it says nothing about real clips and does not validate the descriptor. Audit findings do
**not** move the claim locks and do **not** authorize runtime / memory / integration work. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`)
and `verdict = HOLD` remain in force under every outcome.

## 10. Candidate next branches after audit

```text
If A (residual_metric_insufficient):
   -> a SEPARATE, future docs-first Branch B: multi-feature closure metric PROPOSAL comparing per-feature
      separability, signed median differences, and group-level residuals -- WITHOUT casually inventing pass
      thresholds. (Proposal only; no code, no adopted threshold.)
If B (small_n_baseline_optimism):
   -> a SEPARATE, future reviewed v0.4c amendment for a LARGER held-out set to test whether BA saturation
      collapses; still no TOL change.
If C (mixed):
   -> both of the above, sequenced and separately gated.
If D (audit_inconclusive):
   -> HOLD, or gather more records first; no claim movement.

Candidate-family expansion (targeting BY / amplitude) stays docs-gated and RISKY -- it must not precede fixing
the metric question, or it may just produce more Partials.
Pausing Brainvision and returning to TORMENT memory / kernel work remains a legitimate operator call.
```

## 11. Recommended next step

```text
1. Codex review THIS plan (docs-only; over committed edge b5d6676).
2. If accepted, commit this plan doc. No §0 pointer; no tags.
3. Only THEN, and only on explicit operator instruction, may a SEPARATE future v0.6a code audit implement
   EXACTLY this reporting-only analysis on the reused v0.4d / v0.5a records -- form A, non-learning, frozen
   surfaces reused by identity, inventing no threshold and redefining no TOL, delivered UNCOMMITTED for review,
   Windows the source of truth. This plan authorizes no such code by itself.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 12. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_RESIDUAL_SUFFICIENCY_AUDIT_PLAN_v0.6.md
(new, docs-only, untracked; over committed edge b5d6676, pre-registering Branch A from v0.5b).

Verify that this plan:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
- plans an EXPLANATORY audit of whether the v0.4d group-level residual / TOL closure metric is too compressed /
  too weak vs feature-level baseline separability, and how much of the gap is metric insufficiency vs small-N;
- REDEFINES NO TOL, invents no threshold, proposes no pass/fail rule change, and does not adopt any stricter
  closure rule -- it only DESCRIBES the metric-vs-separability relationship and carries questions forward;
- reuses the v0.4d / v0.5a records BY IDENTITY: reruns nothing with new params, replaces no sealed candidate,
  adds no generator family, changes no descriptor / control, and keeps spectral audit-note-only;
- limits outputs to reporting-only comparisons (group residual vs per-feature BA and signed median difference;
  small-median-but-saturated-BA flags; class-separability ordering; a metric-insufficiency vs small-N split; a
  descriptive TOL-permissiveness-vs-L-inf-structure note; a carried-forward list for a future closure proposal);
- lists candidate outcomes A residual_metric_insufficient / B small_n_baseline_optimism / C mixed / D
  inconclusive, all leaving claim locks and verdict unchanged;
- explicitly does NOT say v0.4d was invalid, does NOT say Brainvision failed or succeeded, does NOT say
  descriptors are valid or vision, and does NOT use audit findings to move claim locks or authorize
  runtime / memory / integration;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any TOL redefinition, any invented threshold, any proposed pass/fail change, any rerun/replacement of
v0.4d, any new family, any implicit opening of B/C or runtime/memory/real-clips, any claim-lock/verdict
movement, or any statement that v0.4d was invalid or that Brainvision failed/succeeded.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Residual Sufficiency Audit Plan v0.6. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, evaluator, or verdict;
deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no TOL; reruns /
replaces no v0.4d candidate; makes no vision / descriptor-validity / temporal-order / memory / runtime /
integration claim; no `§0` pointer added; no tags.*
