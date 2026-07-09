# TORMENT Brainvision Matched Generative Search Synthesis v0.4e

## 1. Status / non-claims

**DOCS-ONLY synthesis / next-decision note. Non-authorizing, non-implementing. Opens no code, no tests, no
runtime, no integration lane.** It records what the v0.4d sealed matched-generative-search run means and what
research question comes next. It **authorizes no code and no tests**, invents no threshold, changes no formula /
§7 anti-proxy logic / §8 verdict logic, deletes or weakens no control, redesigns no descriptor, and opens **no
classifier (form B) and no neural encoder (form C)**. Everything stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. Brainvision Path B remains **not
proven vision**. A synthesis alone moves nothing: **no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v0.4 / v0.4a / v0.4b / v0.4c / v0.4d

```text
v0.4  (54daf01)  proposed the different construction; accepted Direction B (matched generative search).
v0.4a (80a6242)  planned B as a META-PLAN (rules/shape only).
v0.4b (bae9753)  closed TOL and the protocol rules; deferred the numeric enumeration.
v0.4c (635027e)  sealed the numeric enumeration (families / grid / seeds / split / 283-eval budget).
v0.4d (77ed133)  IMPLEMENTED and ran the sealed search (form A, non-learning); outcome Partial.
v0.4e (this doc) synthesizes v0.4d and recommends the next research question.
```

This note changes nothing v0.4b/v0.4c froze. It only interprets v0.4d and recommends a branch.

## 3. Windows repo truth

Windows pytest is the source of truth (per the boundary-stat lesson). Recorded verbatim:

```text
python -m pytest tests/research/test_brainvision_matched_generative_search_v0_4d.py -q
  15 passed in 1.08s

python research/brainvision/run_matched_generative_search_v0_4d.py
  model A_non_learning_search | learning False
  objective: proxy_match_residual + feasibility(PSC < PSC_FLOOR)
  evaluations dev/held/total: 190 93 283
  held-out per target:
    winder_ph3.14  best_residual=0.045046 matched=True feasible_found=True
    winder_r0.7    best_residual=0.036    matched=True feasible_found=True
    winder_r0.5    best_residual=0.06     matched=True feasible_found=True
  held-out baseline audit:
    movement_channel_energy = 1.0    directional = 1.0    per_channel = 1.0    frame_diff = 0.8333
    all_closed = False   evaluator_ba = 1.0   separates = True
  protocol_ok: True   OUTCOME: Partial   verdict: HOLD   locks: False False False

python -m pytest tests/research -q
  250 passed in 42.03s
```

(The one `spectral_centroid` Linux/Windows knife-edge test that fails in the Linux sandbox passes on Windows,
hence 250 passed here.)

## 4. v0.4d result summary

v0.4d ran the sealed enumeration exactly. It was **protocol-clean**: the sealed **283-evaluation envelope was
preserved** (190 development + 93 held-out, full grid once per target, no restarts / retries / redraws),
`protocol_ok = True`, single-shot held-out. The search objective was only `proxy_match_residual` under the sole
feasibility constraint `PSC < PSC_FLOOR`; the evaluator and baseline audit ran only afterward and were never fed
back.

**Feasible held-out matches were found for all three held-out targets** within the frozen `TOL = 0.0634` (best
residuals 0.045 / 0.036 / 0.060, inside v0.3's reported 0.0404–0.0634 band; the binding matches were the
frozen-grounded `segment_paired_canceller`, PSC ≈ 0.032 versus winder PSC = 1.0). The frozen evaluator still
separated winders from their matched non-winders (`evaluator_ba = 1.0`). But the pooled held-out cheap-baseline
audit did **not** close: all four matched groups still separated the two classes at best-threshold BA 0.833–1.00
(none `<= CHANCE_BAND = 0.60`). Outcome: **Partial**. Verdict **HOLD**; claim locks all False.

## 5. Why the result is Partial, not Match-feasible

Match-feasible requires **three** things together: a strict majority of held-out targets matched **and** all
four matched cheap-baseline groups closed (best-threshold BA `<= 0.60`) **and** the frozen evaluator still
separates. v0.4d met the first and third but **failed the second**:

```text
matched held-out targets   = 3 / 3   (strict majority: yes)
frozen evaluator separates = yes (evaluator_ba 1.0)
all four groups closed      = NO  (movement 1.0, directional 1.0, per_channel 1.0, frame_diff 0.833; none <= 0.60)
=> Partial (not Match-feasible)
```

The crux: **matching the declared per-pair proxy residual is not the same as closing class-level baseline
separability.** `proxy_match_residual` is an L-inf, per-pair quantity — it asks whether *each winder* is within
`TOL` of *its own matched candidate* on the ten matched statistics. The cheap-baseline audit is a *class-level,
best-threshold* quantity — it asks whether *some single feature* can separate the *group of winders* from the
*group of matched candidates*. A per-pair match within `TOL` does not force the two classes to overlap: the
winders as a set and the candidates as a set can still occupy separable ranges on some feature, so an optimistic
best-threshold baseline still achieves high BA. That gap is exactly why v0.4d is Partial.

## 6. What v0.4d newly teaches

```text
v0.3 said:   the hand-built all-shortcuts-closed construction was INFEASIBLE
             (we could not hand-build matched candidates).
v0.4d says:  a sealed matched generative search CAN find feasible residual matches (<= TOL) for all held-out
             targets, yet cheap-baseline SEPARABILITY survives strongly.
```

So the obstruction has **moved**. It is no longer "we could not hand-build candidates" — the sealed search found
feasible, within-`TOL` matches for every held-out target. The deeper obstruction is that **matching the declared
proxy residuals is not sufficient to close adversarial baseline separability.** The proxy wall now sits at the
*separability* level, not the *construction* level. This is a genuinely new, honest research signal — and it
still upgrades **no** claim (see §11): it is an in-vitro synthetic result within one sealed enumeration.

## 7. What remains unresolved

```text
- WHICH features, inside movement_channel_energy / directional / per_channel / frame_diff, still separate the
  classes after the per-pair residual match -- the audit reports group-level BA, not the responsible feature.
- WHETHER the residual survival of separability is a small-N best-threshold artifact (3 winders vs 3 matched
  candidates is a very optimistic separability regime) or a real class-level distributional axis.
- WHETHER the declared match criterion (per-pair L-inf over the ten matched stats within TOL) is the right
  SUFFICIENCY criterion for "matched," or too weak to imply baseline closure.
- (spectral stays audit-note-only and is not implicated here.)
```

None of these is resolved by v0.4d, and none is resolved by this synthesis.

## 8. Recommended next research question

```text
Baseline anatomy:
  what exactly are the adversarial baselines SEEING that the declared proxy-residual match did not close?
```

Concretely (as a future, separately-gated question — not opened here): for each of the four matched groups,
which individual feature and which best-threshold still separates the matched held-out winders from their
matched candidates, and by how much — decomposing the group-level BA into per-feature contributions on the same
matched pairs v0.4d produced.

## 9. Candidate next branches

```text
A. Baseline anatomy diagnostic
   Decompose each matched group's surviving best-threshold BA into per-feature contributions on the v0.4d
   matched held-out pairs; identify exactly which features separate after the residual match. Reporting-only,
   reuses frozen surfaces, invents nothing.
   Pro: directly answers §8; smallest, most informative next step; no new fixtures / thresholds.
   Con: at small N the per-feature picture is coarse (mitigated by reporting, not by weakening controls).

B. Tolerance / residual sufficiency audit
   Ask whether per-pair L-inf <= TOL is the right sufficiency criterion, or whether a stricter / different
   (still frozen-referenced) residual notion is needed for "matched" to imply baseline closure.
   Pro: probes the match definition itself.
   Con: risks drifting toward threshold re-negotiation; must stay reference-only, no invention; premature
        before knowing WHAT separates (A should come first).

C. Candidate-family expansion amendment
   A reviewed docs-only amendment adding non-winder families aimed at the features A identifies as separating.
   Pro: could actually close the surviving separability.
   Con: fixture-chasing risk; must not be opened before A shows what to target; requires a sealed amendment.

D. Pause Brainvision and return to TORMENT memory / kernel work
   Accept the Partial result as a clean stopping point and redirect effort to another TORMENT layer.
   Pro: honest; spends no further effort if the operator judges the question answered enough.
   Con: leaves the "what do the baselines see" question open.
```

## 10. Recommended next step

**Recommend Branch A (baseline anatomy diagnostic) first, after Codex accepts this synthesis.** A is the
smallest, most informative next step: it answers §8 directly, would be reporting-only and reuse frozen surfaces,
and it must precede B (residual sufficiency) and C (family expansion) — both of which need to know *what*
separates before they can be aimed. D (pause) remains a legitimate operator call.

```text
1. Codex review THIS synthesis (docs-only; over committed edge 77ed133).
2. If accepted, commit this synthesis doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first step (a diagnostic plan
   before any code). This synthesis opens no code and authorizes no implementation.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, §0, or tag work is recommended or authorized here.
```

## 11. What would still not be proven

Even a future Branch-A anatomy result would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
```

v0.4d's within-`TOL` matches and the surviving separability are in-vitro synthetic facts within one sealed
enumeration; they say nothing about real clips and do not validate the descriptor as measuring real visual
structure. The claim locks (`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`,
`descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force.

## 12. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_MATCHED_GENERATIVE_SEARCH_SYNTHESIS_v0.4e.md
(new, docs-only, untracked; over committed edge 77ed133, synthesizing the v0.4d matched-search run).

Verify that this synthesis:
- is docs-only and opens no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
- records Windows repo truth faithfully (15 passed; 190/93/283; 3/3 held-out matched within TOL; baseline audit
  movement/directional/per_channel = 1.0, frame_diff = 0.833, all_closed = False, evaluator separates; Partial;
  HOLD; full suite 250 passed on Windows);
- states plainly that v0.4d was protocol-clean, the 283-evaluation envelope was preserved, feasible held-out
  matches were found for all three targets under TOL, and the outcome is Partial (NOT Match-feasible) because
  the adversarial baseline groups still separated strongly (per-pair residual match != class-level baseline
  closure);
- frames the newly-taught point correctly: the obstruction moved from "could not hand-build candidates" (v0.3)
  to "matching the declared proxy residuals does not close adversarial baseline separability" (v0.4d);
- recommends Branch A (baseline anatomy diagnostic) as the next research question -- what the baselines are
  seeing that the residual match did not close -- and lists branches A/B/C/D with A first, WITHOUT opening any
  code or authorizing implementation;
- invents no threshold, redesigns no descriptor, weakens no control; preserves all claim locks
  (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD;
- makes no vision / "Brainvision sees" / temporal-order / descriptor-validity / memory-readiness /
  runtime-readiness / integration-readiness claim; adds no §0 pointer and no tags.

Flag any overclaim of the Partial result, any implicit opening of B/C/runtime/memory/real-clips, any threshold
invention, any claim-lock/verdict movement, or any misrecording of the Windows truth.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Matched Generative Search Synthesis v0.4e. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural work; changes no frozen formula, gate, evaluator, or verdict;
deletes or weakens no control; redesigns no descriptor; invents no threshold; makes no vision /
descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*
