# TORMENT Brainvision BY-Aware Closure Preregistration Plan v1.1a

## 1. Status / non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It turns the accepted v1.1 preregistration proposal into a **concrete, finite plan** for a future
BY-aware closure audit: it states, in advance, exactly what a later reporting-only audit would be **required to
report** so that a systematic blue-yellow opponent-axis offset (`BY_axis_asymmetry`) cannot hide inside residual
/ `TOL` matching. It specifies **required reporting obligations only — it adopts no metric, no equation, no
threshold, and no decision rule**. It **authorizes no code and no tests**, invents no threshold, **redefines no
`TOL`**, adopts no new closure metric, defines no final equation, proposes no pass/fail rule change, changes no
formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control, redesigns no descriptor, reopens
no spectral group as a closure group, expands no generator family, and opens **no classifier (form B) and no
neural encoder (form C)**. It does **not** pivot to flat / screen geometry and opens **no flat-geometry
implementation and no screen-analysis implementation**. Everything stays offline under `research/brainvision/` +
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

## 2. Relation to accepted v1.1 proposal

```text
v0.8a (8977248)  BY-channel metric anatomy -> BY_axis_asymmetry (signed, sign-consistent, BY-dominant,
                 often-binding class-level opponent-axis offset that survives the residual/TOL match).
v0.9b (11a1997)  BY closure visibility AUDIT -> BY_visibility_confirmed (panels A-F make the offset visible).
v1.0  (3738c73)  BY-aware closure STRUCTURE proposal: requirements A-G a future closure must REPRESENT.
v1.0a (3013f85)  BY-aware closure AUDIT PLAN: reporting-only panels A-G over existing records.
v1.0b (e083bb4)  BY-aware closure AUDIT FINDINGS -> BY_aware_visibility_confirmed (panels A-G; verdict HOLD).
v1.1  (45be17d)  BY-aware closure PREREGISTRATION proposal: what a future prereg must CONTAIN (components A-G),
                 ACCEPTED AS-IS by Codex, docs-only, adopting none.
v1.1a (this doc) turns the accepted v1.1 components A-G into a CONCRETE, FINITE preregistration PLAN: exactly what
                 a later reporting-only audit would be required to report, and what it may not claim; adopting none.
```

Where v1.1 said **what a preregistration must contain**, v1.1a says **what the audit that plan governs must
report, over which frozen records, and what it may never claim** — still without adopting a metric, an equation,
a threshold, or a decision rule. This plan changes nothing v0.4b/v0.4c/v0.7a froze or v0.7b/v0.8a/v0.9b/v1.0b
produced, and does not prove Brainvision, validate the descriptor, adopt a metric, or select flat / screen
geometry.

## 3. Preregistration objective

```text
OBJECTIVE:
  Pre-commit, in advance and in finite detail, the reporting a future BY-aware closure audit MUST produce over
  the frozen records, so that a systematic BY opponent-axis offset is REPRESENTED as a first-class element and
  cannot hide inside residual / TOL matching -- WITHOUT this plan choosing any metric, equation, threshold, or
  decision rule.

The plan fixes, in advance:
  (i)   the FINITE scope (which frozen records, which pairs, which stats)                -> §5
  (ii)  the REQUIRED BY-aware reporting obligations (A-F, concrete)                       -> §6
  (iii) the REQUIRED non-authorizing guards (G)                                           -> §7
  (iv)  the decisions that stay DEFERRED to a separate later gate (metric/equation/thr.)  -> §8
  (v)   what a later implementation MAY inspect / MAY NOT claim                            -> §9 / §10
It authorizes no implementation; §12 lists implementation as a SEPARATE, later, gated branch.
```

## 4. Frozen prior inputs

All inputs are reused **by identity**; none are recomputed, replaced, reseeded, or expanded by this plan.

```text
- Frozen thresholds/constants (referenced, NOT re-thresholded): TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30;
  CHANCE_BAND = 0.60. The frozen evaluator (structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR).
- Frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens; proxy_match_residual = L-inf over
  the ten matched stats (spectral excluded); PSC < PSC_FLOOR feasibility.
- Frozen sealed matching (v0.7b, reproduced by v0.8a): 19 matched / 5 unmatched pairs
  (unmatched: w_sp3.00, w_sp3.50, w_r0.4, w_r0.3, w_r0.2); single matching family segment_paired_canceller.
- Closed F1-F5 generator family set; spectral audit-note-only (NOT a closure group).
- Reused BY-aware quantities (v0.8a/v0.9b/v1.0b panels A-G, reused by identity; reference values, NOT new gates):
    signed offsets   by_std +0.04505 (0.95), by_centroid -0.03393 (0.90), by_spread -0.02935 (0.84); mean 0.895
    BY vs RG/dir     BY {by_std 0.71, by_centroid 0.54, by_spread 0.46}  >>  RG {0.00, 0.04}, directional 0.06
    binding          by_std 10, by_spread 1, by_centroid 1; BY-binding fraction 0.6316 vs proportional share 0.30
    region           by_centroid BA speed 0.75, phase 1.00, radius 1.00
    coupling/leakage coupling 0.031; amplitude {chroma_mag 0.29, rg_std 0.17}; dominant mechanism BY_axis_asymmetry
    aggregation      aggregation_warning = True
- Claim locks and verdict HOLD.
This plan freezes ALL of the above and only pre-commits reporting obligations over these exact records.
```

## 5. Finite audit scope

```text
- The audit is FINITE and BOUNDED: it reuses the v0.7b / v0.8a / v0.9b / v1.0b records BY IDENTITY and reports
  over exactly the 19 matched pairs (and the 5 unmatched, for context), the ten matched stats, the three BY
  stats (by_centroid, by_spread, by_std), the RG and directional comparison features, and the frozen regions.
- NO new data, samples, seeds, families, axes, or candidate generation; NO sample rerun / replacement; NO
  spectral reopening as a closure group (spectral stays audit-note-only).
- The audit is REPORTING-ONLY (form A, non-learning): it re-organizes and re-presents frozen quantities; it
  computes no new statistic that is not a re-presentation of an existing frozen quantity, and it makes NO decision.
- Non-finite / extreme values are inadmissible: they are excluded upstream by the frozen _is_clean and, if the
  underlying records breach / fail to reproduce / return incomplete panels, the audit must return an
  invalid_protocol_breach outcome and can never produce a confirmation.
- Outcome vocabulary is a REPORTING LABEL only (e.g. confirmed / partial / inconclusive / invalid_protocol_breach)
  and never a Brainvision pass, a closure decision, or a claim-lock / verdict movement.
```

## 6. Required BY-aware reporting obligations

The future audit MUST report all of A-F below. Each is a concrete **reporting requirement** over the frozen
records; none is a metric, an equation, a threshold, or a decision. "Report" means surface and separate the
quantity; it never means gate, pass, or close.

```text
A. Signed-offset reporting
   MUST report, per BY stat (by_centroid, by_spread, by_std):
     - the SIGN DIRECTION of the across-pair mean signed offset (dominant + / -),
     - the SIGN CONSISTENCY (fraction of pairs sharing the dominant sign; natural reference is chance 0.5),
     - the MAGNITUDE expressed RELATIVE TO the frozen TOL as a descriptive effect-size reference
       (the existing v0.8a |smd|/TOL reporting, reused by identity).
   MUST NOT introduce any new offset-vs-TOL pass/fail: TOL stays the frozen residual-match tolerance, used here
   only as a descriptive unit. Reporting the offset is not closing it.

B. BY dominance reporting
   MUST report BY effect magnitudes COMPARED AGAINST the RG comparison features and the directional comparison
   feature (opponent-axis dominance), so BY dominance is explicit rather than assumed.
   MUST keep BY dominance as VISIBILITY EVIDENCE ONLY -- never a dominance threshold, ratio rule, or pass.

C. Binding-stat reporting
   MUST report whether BY stats BIND the residual match -- how often each of by_std / by_spread / by_centroid is
   the L-inf-binding stat (especially by_std) -- reported against the proportional share of the ten matched stats.
   MUST NOT let binding become closure: high BY-binding is reported as visibility, never converted into a
   binding-fraction gate or a pass/fail rule.

D. Aggregation-warning reporting
   MUST explicitly report WHEN group-level residual / TOL matching COEXISTS with a systematic BY signed ordering
   (the aggregation / compression warning), so the coexistence is visible in one place.
   MUST prevent hidden closure claims: the warning surfaces the coexistence and decides nothing; a passing
   per-pair residual/TOL match is never re-described as closure of the BY offset.

E. Coupling / leakage separation
   MUST keep BY_axis_asymmetry SEPARATE from centroid/spread coupling and from amplitude / channel-energy leakage,
   reporting the separated mechanism scores so BY dominance is not confounded with coupling or amplitude.

F. Region / family caveat
   MUST preserve and report the SINGLE-MATCHING-FAMILY caveat (all matches are segment_paired_canceller) and the
   TARGET-REGION visibility (per-region BY).
   MUST NOT authorize generator-family expansion to "fix" the single-family limitation: the caveat is reported,
   not engineered away.
```

## 7. Required non-authorizing guards

```text
G. Non-authorizing guard (MANDATORY, mirrors v1.0/v1.0b panel G, all False)
   The audit MUST carry an explicit, structured statement that BY-aware reporting is DIAGNOSTIC-ONLY and
   authorizes NOTHING. Specifically, the following authorization flags MUST all be present and MUST all be False:
     authorizes_descriptor_validity = False   authorizes_temporal_order      = False
     authorizes_pass_fail           = False   authorizes_closure             = False
     authorizes_runtime             = False   authorizes_memory              = False
     authorizes_integration         = False   authorizes_live_or_screen_use  = False
     authorizes_vision              = False
   If any guard flag were set True, or absent, the reporting would be non-conformant to this preregistration.
   The guard is a STANDING property of any audit built to this plan: no reporting result, under any outcome
   label, moves a claim lock or the verdict (HOLD under every outcome).
```

## 8. Deferred metric / equation / threshold decisions

The following are **explicitly deferred** to a separate, later, gated decision and are **NOT decided, adopted,
invented, or authorized by this plan**:

```text
- The closure METRIC / scoring function itself (A-F are reporting obligations, not a metric).
- Any EQUATION, formula, or aggregation that would combine A-F into a single closure quantity.
- Any THRESHOLD, cutoff, ratio, dominance rule, binding-fraction gate, sign-consistency cutoff, or offset-vs-TOL rule.
- Any TOL redefinition; any CHANCE_BAND / PSC_FLOOR / AIC_FLOOR change; any pass/fail rule change.
- Any §7 anti-proxy or §8 verdict-logic change; any control change.
- Any descriptor / _stats / GROUPS redesign; any generator-family expansion; any spectral reopening as a closure group.
- Any classifier (form B) or neural encoder (form C).
- Any flat-geometry / screen-analysis / camera / live / sensor / streaming / runtime / memory / integration path.
- Any real / local clip.
A future decision to adopt any of the above would be a SEPARATE preregistered gate, not an entailment of this plan.
```

## 9. What a later implementation may inspect

If — and only if — a later, separately-gated decision authorizes a reporting-only implementation of this plan, it
**may inspect / re-present** the following over the frozen records (reporting-only, form A, non-learning):

```text
- per-BY signed offsets, sign direction, sign consistency, and |offset| in frozen-TOL units (A);
- BY-vs-RG and BY-vs-directional magnitude comparisons (B);
- the L-inf binding distribution across the ten matched stats, BY stats separated, vs proportional share (C);
- the coexistence of per-pair residual/TOL closure with a systematic BY signed ordering (D);
- separated coupling / amplitude / axis-asymmetry mechanism scores (E);
- per-region BY visibility and the single-matching-family caveat (F);
- the explicit non-authorization guard flags, all False (G);
- protocol_ok, the reporting-label outcome, and a claim-lock / verdict summary (locks False; HOLD).
All inspection is re-presentation of frozen quantities; it computes no new statistic that is not such a
re-presentation, and it decides nothing.
```

## 10. What a later implementation may not claim

Even a fully conformant later audit **may not claim** any of:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not closure                    not a pass / a met threshold / an adopted metric
not real-video understanding   not a unique real-world color-structure advantage
not generator-family generalization (single-family caveat stands)
not memory readiness           not runtime readiness           not integration readiness
not live / screen / camera use
```

Reporting the BY-axis offset (and recording that the reporting is non-authorizing) is an in-vitro, design-layer
step within the same frozen family set; it says nothing about real clips or screens and does not validate the
descriptor or adopt a metric. The proof route remains **HELD / HOLD** because the offset is visible but not
closed. The claim locks and `verdict = HOLD` remain in force.

## 11. Review checklist

A future audit is **conformant to this preregistration** iff a reviewer can check all of:

```text
[ ] docs/records only; reuses v0.7b/v0.8a/v0.9b/v1.0b BY IDENTITY; no new data/seeds/families/candidate generation.
[ ] finite scope: 19 matched (+5 unmatched context), ten matched stats, three BY stats, RG + directional, frozen regions.
[ ] A signed-offset: per-BY sign direction + sign consistency + |offset| in frozen-TOL units; no offset-vs-TOL pass/fail.
[ ] B BY-dominance: BY vs RG and directional reported; dominance kept as visibility evidence only.
[ ] C binding: BY-binding distribution (esp. by_std) vs proportional share; binding never becomes a gate/closure.
[ ] D aggregation-warning: coexistence of residual/TOL closure with systematic BY ordering explicitly reported; no hidden closure.
[ ] E coupling/leakage: BY_axis_asymmetry separated from centroid/spread coupling and amplitude leakage.
[ ] F region/family: single-matching-family caveat + per-region BY reported; NO family expansion authorized.
[ ] G guard: all authorization flags present and False (descriptor/temporal/pass_fail/closure/runtime/memory/
    integration/live_or_screen/vision).
[ ] deferred set (§8) untouched: no metric/equation/threshold/TOL change/pass-fail/descriptor/family/spectral/
    classifier/neural/flat/screen/runtime/memory/real-clip.
[ ] non-finite / breach / non-reproduction -> invalid_protocol_breach; never evidence.
[ ] claim locks False; verdict HOLD; no §0 pointer; no tags.
```

## 12. Candidate next branches

Docs-first candidates only; **none opened or authorized here**:

```text
A. Reporting-only BY-aware closure audit IMPLEMENTATION (SEPARATE, later, gated)
   ONLY if the operator authorizes it: a form-A, non-learning audit that reports A-G over the frozen records
   exactly as pre-committed here (the future v1.1b findings step). This plan specifies WHAT to report; it does
   NOT authorize the code. Authorization is a separate operator decision.
B. Candidate closure-metric COMPONENT enumeration (docs-first)
   Enumerate candidate metric COMPONENTS constrained by A-G, still WITHOUT adopting a metric, equation, or threshold.
C. Flat opponent-plane / spatial FIELD framing (docs-first, conceptual)
   Only AFTER the preregistration path is settled; conceptual only; NO screen / flat-geometry implementation.
D. Operator / new-math NOTE (docs-first)
   Ask the operator for intuition / math only after the reporting obligations are agreed.
E. Pause Brainvision and return to TORMENT memory / kernel work.
```

**Recommended next:** Codex review THIS plan; if accepted, the operator commits it (docs-only; no §0 pointer, no
tags). Whether to then authorize Branch A (the reporting-only implementation) is a **separate operator decision**
— this plan authorizes no code. Do NOT pivot to flat opponent-plane geometry (C) until the preregistration path
is settled. Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_AWARE_CLOSURE_PREREG_PLAN_v1.1a.md
(new, docs-only, untracked; over committed edge 45be17d, turning the accepted v1.1 preregistration proposal into
a concrete finite plan for a future BY-aware closure audit).

Verify that this plan:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED; and
  authorizes NO flat-geometry and NO screen-analysis implementation;
- specifies REQUIRED REPORTING OBLIGATIONS ONLY and ADOPTS NONE -- it defines no metric, no equation, no final
  pass/fail rule, invents no threshold, redefines no TOL, redesigns no descriptor, expands no family, and reopens
  no spectral group (incl. not as a closure group);
- states a finite, bounded scope (§5): reuses v0.7b/v0.8a/v0.9b/v1.0b BY IDENTITY over the 19 matched (+5 unmatched
  context) pairs, ten matched stats, three BY stats, RG + directional, frozen regions; reporting-only; no new
  data/seeds/families/candidate generation; non-finite/breach -> invalid_protocol_breach;
- makes obligations A-F concrete (signed-offset with sign direction / consistency / |offset| in frozen-TOL units
  as descriptive effect-size, NO offset-vs-TOL pass/fail; BY dominance vs RG + directional as visibility only;
  binding esp. by_std vs share, never a gate; aggregation-warning coexistence, no hidden closure; coupling/leakage
  separation; single-family caveat + per-region BY, NO family expansion) and mandates guard G with all
  authorization flags present and False;
- defers (§8) every metric / equation / threshold / TOL / pass-fail / descriptor / family / spectral / classifier /
  neural / flat / screen / runtime / memory / real-clip decision to a separate later gate;
- frames §9/§10 correctly: a later implementation MAY only re-present frozen quantities and MAY NOT claim vision /
  descriptor validity / temporal order / closure / a pass / family generalization / memory / runtime / integration /
  live-screen use;
- lists next branches A-E docs-first, opening none, and notes that Branch A (the reporting-only implementation) is
  a SEPARATE operator-gated decision this plan does NOT authorize;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted metric / equation / threshold / pass-fail rule, any TOL redefinition, any descriptor redesign, any
family expansion, any spectral reopening as a closure group, any control weakening, any offset-vs-TOL or binding gate,
any flat-geometry / screen-analysis / runtime / memory / real-clip authorization, any guard flag set True or absent,
any claim that the wall is CLOSED (vs visible), any descriptor-validity / vision / temporal-order claim, or any
claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Aware Closure Preregistration Plan v1.1a. Docs-only, non-authorizing. Opens no
implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no frozen formula, gate,
evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no
TOL; adopts no closure metric; defines no equation; specifies required reporting obligations only, adopting none;
keeps the wall visible not closed; makes no vision / descriptor-validity / temporal-order / memory / runtime /
integration claim; no `§0` pointer added; no tags.*
