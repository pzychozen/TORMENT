# TORMENT Brainvision BY-Aware Closure Failure Anatomy Proposal v1.6

## 1. Status / non-claims

**DOCS-ONLY proposal. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It proposes — for future, separately-gated consideration only — a **final targeted failure-anatomy step**
to inspect *why* the selected A + D + G BY-aware closure spine still reports the closure gap as visible. It is a
**decision-point** proposal: either it points at a plausible bounded **closure lever**, or it recommends
**pivoting** off the current fixture-metric route toward a flat opponent-plane / spatial-field framing. It
**discusses candidate failure mechanisms and adopts none**. It defines **no metric, no equation, no threshold,
no pass/fail validity rule, no offset-vs-`TOL` gate, no binding gate**, and implements nothing. It **authorizes
no code and no tests**, **redefines no `TOL`**, changes no formula / §7 anti-proxy logic / §8 verdict logic,
deletes or weakens no control, redesigns no descriptor, reopens no spectral group as a closure group, expands no
generator family, and opens **no classifier (form B) and no neural encoder (form C)**. It does **not** pivot to
flat / screen geometry itself and opens **no flat-geometry / screen-analysis implementation**. Everything stays
offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. A proposal alone moves nothing: **no
claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v1.5 findings

```text
v1.4  (da946ed)  finite audit PREREGISTRATION of the A + D + G spine (B / C / E report-only).
v1.4a (86cb1f7)  implementation AUTHORIZATION review: exact v1.5 boundary.
v1.5  (cb2c8fd)  A + D + G spine HARNESS: generated the reporting/guard structure (completeness-enforced guard).
v1.5f (559964a)  FINDINGS: BY_aware_closure_gap_still_visible; closure_achieved False; HOLD.
v1.6  (this doc) failure-anatomy PROPOSAL: why does the spine still report the gap? Decision-point; adopting none.
```

v1.5 implemented the preregistered spine and honestly reported the gap PERSISTS. v1.6 asks the narrower,
decision-forcing question: WHY — and does the answer point at a bounded lever or off the fixture-metric route
entirely? It proves nothing, validates nothing, adopts nothing, and changes nothing v1.4 / v1.4a / v1.5 froze.

## 3. Failure-anatomy objective

```text
OBJECTIVE:
  Inspect WHY the selected A + D + G BY-aware closure spine still reports a systematic BY signed ordering AFTER
  the per-pair residual / TOL match passes -- and DECIDE, from that inspection, one of two things:
    (i)  a plausible, BOUNDED closure LEVER exists (something a later finite anatomy could represent WITHOUT a new
         metric / threshold), or
    (ii) no such lever is in view, and the persistent BY-axis failure indicates the current FIXTURE-METRIC route
         is the wrong abstraction -> pivot to a flat opponent-plane / spatial-field proposal.
This is NOT another visibility audit for its own sake; it is a decision point about whether to keep grinding the
fixture-metric route or to pivot.
```

## 4. Current failure statement

```text
Under the v1.5 A + D + G spine (reusing the frozen records by identity), the BY offset SURVIVES residual / TOL
matching: signed and sign-consistent (by_std +0.04505 @0.95, by_centroid -0.03393 @0.90, by_spread -0.02935 @0.84),
BY-dominant over RG and directional features, often-binding (by_std binds 10/19; BY-binding fraction 0.6316 > share
0.30), coexisting with a passing per-pair closure (aggregation coexistence True) -- on a SINGLE matching family
(segment_paired_canceller), coupling and amplitude weak. protocol_ok is presence/guard-completeness only; the
guard is intact; closure_achieved is False.

CORE QUESTION:
  Why does the selected BY-aware closure spine still report systematic BY signed ordering after residual / TOL
  matching -- i.e. what, structurally, lets a signed, BY-dominant, often-binding class-level offset pass the
  per-pair L-inf <= TOL match while the classes stay ordered?
```

## 5. Candidate failure mechanisms

Proposed for DISCUSSION; **NONE adopted, and none turned into a metric / threshold / gate here**. Each is a
candidate explanation of the persistence, with what a later bounded anatomy might look at (§6) and whether it
plausibly offers a lever or points to a pivot (§8 / §9):

```text
A. Residual aggregation hides signed BY ordering
   The per-pair L-inf residual is sign-blind and pair-local; a consistently-signed, class-level BY ordering can be
   below TOL per pair yet systematic across pairs. LEVER? possibly (a representation that reads across-pair sign
   structure) -- but the risk is that any such reading needs a threshold, which is out of scope.

B. BY signed offset is structural to the fixture family
   The signed offset may be an intrinsic property of the single matching family (segment_paired_canceller) rather
   than a separable, closable discrepancy. If so, there is NO fixture-metric lever -- this points toward a PIVOT
   (the abstraction, not the metric, carries the offset).

C. BY/RG opponent balance is mismatched even when residual/TOL passes
   The residual treats BY and RG symmetrically, but the discrepancy is concentrated on the BY axis; the opponent
   BALANCE may be mismatched while the aggregate residual passes. LEVER? possibly (represent the balance) -- but,
   as in A, only if representable without a dominance ratio / cutoff.

D. by_std binds matching more strongly than centroid/spread
   by_std is the binding stat far more often than by_spread / by_centroid; the match may be "held together" by the
   very axis under suspicion. LEVER? possibly (a binding-aware VIEW) -- but must stay annotation-only; a binding
   gate is out of scope.

E. Current trajectory / winder-canceller abstraction may be the wrong geometry for screen-like vision
   The whole fixture family (winder / non-winder trajectory cancellers) may be the wrong ABSTRACTION for the
   opponent-axis structure a screen-like vision task would need. If the persistence is abstraction-level, no
   fixture-metric lever will close it -> PIVOT to flat opponent-plane / spatial-field.
```

## 6. What anatomy may inspect later

If a later, separately-gated v1.6a finite anatomy is opened, it **may inspect** (reporting-only, reuse by
identity, adopting nothing):

```text
- the ACROSS-PAIR structure of the signed BY offset (is the ordering systematic beyond per-pair sign consistency?) (A);
- whether the signed offset is INVARIANT across the single family's members vs separable from them (B);
- the BY-vs-RG / directional balance on the pairs where residual passes yet BY ordering persists (C);
- the binding distribution conditioned on by_std vs centroid / spread (D);
- descriptive contrasts that would DISTINGUISH a fixture-metric lever (A / C / D) from an abstraction-level failure
  (B / E) -- reported, not decided.
All inspection re-presents frozen quantities; it computes no new statistic that is not such a re-presentation and
adopts no metric / threshold / gate.
```

## 7. What anatomy may not inspect

```text
- NO new metric / equation / threshold / ratio / sign-consistency cutoff / pass-fail validity rule.
- NO TOL / floor / CHANCE_BAND change; NO offset-vs-TOL gate; NO binding gate; NO §7 / §8 / control / evaluator change.
- NO descriptor / _stats / GROUPS redesign; NO generator-family expansion; NO spectral reopening as closure.
- NO new data / samples / seeds / families / candidate generation; NO classifier (form B) / neural (form C).
- NO flat-geometry / screen-analysis IMPLEMENTATION; NO camera / live / sensor / screen / streaming.
- NO runtime / memory / integration / real-clip path.
- NO promotion of any report-only view (A / C / D) into a decision input or gate.
Anatomy INSPECTS the existing frozen surface; it does not build, adopt, or authorize.
```

## 8. Decision rule for stopping metric grind

```text
This is the LAST BY fixture-metric anatomy step UNLESS it produces a CLEAR, BOUNDED lever. Concretely:
  - A "clear bounded lever" = a concrete, representable-over-the-frozen-records inspection (from A / C / D) that
    could plausibly DISTINGUISH or ADDRESS the signed ordering WITHOUT adopting a new metric / threshold / gate and
    WITHOUT expanding the family -- specifiable as a docs-first v1.6a finite anatomy plan.
  - If v1.6 (this proposal) or a subsequent v1.6a does NOT surface such a lever -- or if the inspection points to
    mechanism B or E (offset structural to the family / wrong abstraction) -- then the fixture-metric route is
    exhausted and the work PIVOTS (§9). No further BY fixture-metric anatomy is proposed beyond this step absent a
    lever.
This rule exists to prevent metric grind: one more anatomy step, then either a bounded lever or a pivot.
```

## 9. Pivot criteria toward flat opponent-plane / spatial-field proposal

```text
PIVOT to a flat opponent-plane / spatial-field proposal (docs-only) IF ANY of:
  - the persistence is best explained by mechanism B (signed offset structural to the single fixture family) or
    mechanism E (winder / non-winder trajectory-canceller abstraction is the wrong geometry);
  - no A / C / D lever is representable over the frozen records without a new metric / threshold / gate or a family
    expansion;
  - a later v1.6a finite anatomy still shows the SAME wall without surfacing a new lever.
The pivot is a DOCS-ONLY proposal to consider whether a flat opponent-plane / spatial-field framing represents the
opponent-axis structure better than the current fixtures. It authorizes NO flat-geometry / screen-analysis
implementation; it is a conceptual reframing, gated separately.
```

## 10. What remains frozen

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator; the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual (L-inf over the ten matched stats, spectral excluded) and PSC < PSC_FLOOR feasibility.
- the closed F1-F5 family set; the single matching family (segment_paired_canceller); the v0.7b samples;
  spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a / v0.9b / v1.0b / v1.2 / v1.5 records reused by identity; no sample replacement / new seeds / generation.
- claim locks and verdict HOLD.
This proposal changes none of the above; a later anatomy would reuse ALL of it by identity.
```

## 11. What remains unproven

Inspecting the failure — and even choosing to pivot — leaves all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not closure                    (the gap is visible; it is not closed)
```

The proof route remains **HELD / HOLD** because the BY offset is visible but not closed. The claim locks and
`verdict = HOLD` remain in force whether the outcome is a bounded lever or a pivot.

## 12. Candidate next branches

Docs-first candidates only; **none opened or authorized here**:

```text
A. v1.6a FINITE failure-anatomy plan (docs-only)  -- IF this proposal surfaces a clear bounded lever (from A / C / D):
   preregister a single, reporting-only anatomy over the frozen records that inspects that lever, adopting no
   metric / threshold / gate.
B. FLAT OPPONENT-PLANE / SPATIAL-FIELD proposal (docs-only)  -- IF no bounded lever (mechanism B / E, or no
   representable A / C / D lever): pivot to consider whether the fixture abstraction is wrong. Conceptual only;
   NO flat-geometry / screen-analysis implementation.
C. Operator / new-math NOTE (docs-only).
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 13. Recommended next step

**Recommend using this proposal as the decision point: open Branch A (v1.6a finite failure-anatomy plan,
docs-only) ONLY IF a clear bounded lever is surfaced from mechanisms A / C / D; otherwise pivot to Branch B (flat
opponent-plane / spatial-field proposal, docs-only).** This is explicitly the **LAST BY fixture-metric anatomy
step unless it produces a clear bounded lever** — the stop rule in §8 prevents further metric grind. C (operator
new-math) and D (pause) remain legitimate operator calls.

```text
1. Codex review THIS proposal (docs-only; over committed edge 559964a).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed:
   - if a clear bounded lever (A / C / D) is in view -> open Branch A as a SEPARATE, docs-first v1.6a finite
     anatomy plan (reporting-only; no metric / threshold / gate / family / spectral / flat / screen / runtime /
     memory adopted);
   - else (mechanism B / E, or no representable lever) -> pivot to Branch B (flat opponent-plane / spatial-field
     proposal, docs-only; no flat-geometry / screen-analysis implementation).
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 14. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_AWARE_CLOSURE_FAILURE_ANATOMY_PROPOSAL_v1.6.md
(new, docs-only, untracked; over committed edge 559964a, proposing a FINAL targeted failure-anatomy decision point
for the persisting BY-aware closure gap, adopting none).

Verify that this proposal:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED; and
  authorizes NO flat-geometry and NO screen-analysis implementation;
- discusses candidate failure MECHANISMS ONLY and ADOPTS NONE -- it defines no metric, no equation, no threshold,
  no pass/fail validity rule, no offset-vs-TOL gate, no binding gate; redefines no TOL; redesigns no descriptor;
  expands no family; reopens no spectral group;
- states the core question correctly (why the A + D + G spine still reports systematic BY signed ordering after
  residual/TOL matching) and frames the note as a DECISION POINT: bounded lever OR pivot -- NOT another visibility
  audit for its own sake;
- lists candidate mechanisms A-E (residual aggregation hides ordering / offset structural to fixture family / BY-RG
  balance mismatch / by_std binds strongest / winder-canceller abstraction may be wrong geometry) as discussion,
  with what a later anatomy MAY (§6) and MAY NOT (§7) inspect, all reporting-only / reuse-by-identity;
- gives a STOP rule (§8): this is the LAST BY fixture-metric anatomy step unless it produces a clear BOUNDED lever;
  and PIVOT criteria (§9) toward a docs-only flat opponent-plane / spatial-field proposal if mechanism B / E or no
  representable A / C / D lever;
- keeps everything in §10 frozen and §11 unproven (vision / descriptor validity / temporal order / closure remain
  unproven under either outcome);
- recommends Branch A (v1.6a finite anatomy plan) only if a bounded lever is surfaced, else Branch B (pivot), lists
  C/D, and opens none;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted metric / equation / threshold / pass-fail rule, any TOL redefinition, any offset-vs-TOL / binding
gate, any descriptor redesign, any family expansion, any spectral reopening, any flat-geometry / screen-analysis /
runtime / memory / real-clip authorization, any claim that closure is ACHIEVED (vs the gap being visible), any
descriptor-validity / vision / temporal-order claim, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Aware Closure Failure Anatomy Proposal v1.6. Docs-only decision-point proposal,
non-authorizing. Opens no implementation lane; opens no classifier / neural / screen / flat-geometry work; changes
no frozen formula, gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no
threshold; redefines no TOL; adopts no closure metric or equation; creates no offset-vs-TOL or binding gate;
discusses candidate failure mechanisms only, adopting none; is the LAST BY fixture-metric anatomy step unless it
produces a clear bounded lever, else pivot to flat opponent-plane / spatial-field; keeps the gap visible not closed;
makes no vision / descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer
added; no tags.*
