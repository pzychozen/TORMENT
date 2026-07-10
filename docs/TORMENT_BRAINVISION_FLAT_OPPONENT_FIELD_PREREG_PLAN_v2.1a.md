# TORMENT Brainvision Flat Opponent-Field Preregistration Plan v2.1a

## 1. Status / non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration lane.**
It turns the accepted v2.1 preregistration proposal into a **finite preregistration plan**: the concrete
preregistration structure that must exist before any future offline-only flat opponent-field implementation or
descriptor design can be considered. It **specifies required preregistration obligations only — it adopts no
descriptor, no coordinate system, no metric, no equation, no threshold, no pass/fail rule**, and implements
nothing. It **authorizes no code and no tests**, **redefines no `TOL`**, changes no formula / §7 anti-proxy logic
/ §8 verdict logic, deletes or weakens no control, redesigns no descriptor, reopens no spectral group, expands no
generator family, and opens **no classifier (form B) and no neural encoder (form C)**. It opens **no
flat-geometry implementation and no screen-analysis implementation**. Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

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

## 2. Relation to v2.1 proposal

```text
v2.0  (5598c28)  flat opponent-field PROPOSAL: candidate research abstraction pivot; conceptual; adopting none.
v2.0a (01d5d9b)  flat opponent-field CONCEPT PLAN: bounded the abstraction's meaning / components / non-goals.
v2.1  (56b344c)  flat opponent-field PREREGISTRATION proposal: what a future prereg must CONTAIN (obligations A-F).
v2.1a (this doc) flat opponent-field PREREGISTRATION plan: the FINITE prereg structure that must exist before any
                 implementation or descriptor design; adopting none; authorizing no code.
```

v2.1 proposed WHAT a flat opponent-field preregistration must contain; v2.1a fixes the finite plan — the concrete
obligations, the deferred design decisions, and what a later implementation may / may not inspect and claim — so a
later docs-first finite-audit design (v2.2) has a narrowed, well-bounded starting point. Where v2.1 said what a
prereg must contain, v2.1a says what the finite prereg STRUCTURE is and what it defers. It proves nothing,
validates nothing, adopts nothing, and changes nothing v0.4b / v0.4c / v0.7a froze or v0.7b … v2.1 produced.

## 3. Preregistration-plan objective

```text
CORE QUESTION:
  What FINITE preregistration structure must exist before any future flat opponent-field implementation or
  descriptor design can be considered?

OBJECTIVE:
  Fix, in finite detail, the preregistration obligations a future offline-only flat opponent-field audit must
  satisfy (A-F), the design decisions that stay DEFERRED, and what a later implementation may / may not inspect and
  claim -- WITHOUT adopting any descriptor / coordinate system / metric / equation / threshold and WITHOUT
  authorizing any code, screen analysis, or vision claim.
This is a bounding plan, not a design, an experiment, or an implementation.
```

## 4. Frozen prior state

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator; the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual; PSC < PSC_FLOOR feasibility; the closed F1-F5 family set; the single matching family;
  the v0.7b samples; spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a … v1.7 records and artifacts, preserved as FROZEN EVIDENCE (not failed / retracted); v2.0 / v2.0a /
  v2.1 as an UNVALIDATED conceptual pivot; no sample replacement / new seeds / generation.
- claim locks and verdict HOLD.
This plan freezes ALL of the above; a flat opponent-field preregistration is a SEPARATE offline research surface.
```

## 5. Finite preregistration scope

```text
- FINITE and BOUNDED: the future preregistration must fix obligations A-F (§6) and nothing more; it may specify
  REQUIRED FUTURE PREREG FIELDS but must NOT design the descriptor, choose coordinates, define equations, create
  thresholds, or authorize implementation.
- CONCEPTUAL: obligations are stated as conceptual requirements over OFFLINE SYNTHETIC content; no coordinate
  system, resolution, patch equation, relation equation, or metric is fixed.
- OFFLINE ONLY: no screen analysis, no screen capture, no camera / live / sensor / streaming, no real clips; the
  offline / no-screen / no-vision boundary is restated as a standing obligation (see F).
- NON-DRIFTING: the plan's job is to keep a later plan / audit from smuggling in a descriptor, coordinate system,
  metric, or screen path; the deferral set (§7) is the guardrail.
- The plan opens NO implementation; §8 lists what a later, separately-gated implementation MAY inspect conceptually.
```

## 6. Required preregistration obligations

The future preregistration MUST state all of A-F. Each is a concrete **preregistration-content requirement**;
none is a descriptor, a coordinate system, a metric, an equation, a threshold, or a decision.

```text
A. Patch-definition obligation
   The prereg MUST define what a local opponent PATCH must conceptually represent (position-indexed local opponent
   content). MUST NOT adopt a coordinate system, a resolution, or a patch equation; MUST NOT adopt a descriptor.
B. Opponent-channel obligation
   The prereg MUST keep the BY / RG opponent relation EXPLICIT (the axes already in play, kept conceptually).
   MUST NOT adopt a channel metric or a descriptor.
C. Spatial-relation obligation
   The prereg MUST name the candidate spatial relations to be represented: ADJACENCY, NEIGHBORHOOD, GRADIENT, EDGE,
   CONTINUITY / DISCONTINUITY. MUST NOT adopt equations for any of them.
D. Region/field obligation
   The prereg MUST distinguish LOCAL patch effects from FIELD-LEVEL organisation (a local patch is not a field
   property). MUST NOT adopt a pass/fail rule.
E. Temporal-layer deferral
   The prereg MUST record that motion / time is a LATER OPTIONAL layer, NOT a first principle; the first pass stays
   spatial.
F. Non-authorizing guard
   The prereg MUST commit that all claim locks remain False and that flat opponent-field reporting authorizes NO
   vision, descriptor-validity, temporal-order, runtime, memory, integration, screen, live, or real-clip claim.
```

Each obligation is a **required future prereg field**. Adopting any as a descriptor, coordinate system, metric, or
implementation is explicitly **out of scope here** and would need a separate, separately-gated decision.

## 7. Deferred design decisions

The following are **explicitly deferred** to a separate, later, gated decision and are **NOT decided, adopted,
invented, or authorized by this plan**:

```text
- The flat-field DESCRIPTOR; any COORDINATE SYSTEM / resolution / patch or relation EQUATION.
- Any METRIC / scoring function / threshold / ratio / cutoff / pass-fail validity rule.
- Any TOL / floor / CHANCE_BAND change; any §7 / §8 / control / evaluator change.
- Any generator-family expansion; any spectral reopening as a closure group; any change to the frozen descriptor.
- Any classifier (form B) / neural encoder (form C).
- Any flat-geometry / screen-analysis IMPLEMENTATION; any camera / live / sensor / screen-capture / streaming; any real clips.
- Any runtime / memory / integration; any torment_service touch.
- Any temporal layer as a first principle (deferred per obligation E).
A future decision to adopt any of the above would be a SEPARATE preregistered gate, not an entailment of this plan.
```

## 8. What a later implementation may inspect

If — and only if — a later, separately-gated decision (after v2.2) authorizes an offline-only flat opponent-field
study, it **may inspect CONCEPTUALLY** (offline synthetic, adopting nothing here):

```text
- what conceptually counts as a local opponent patch (obligation A), WITHOUT a coordinate system / descriptor;
- the explicit BY / RG opponent relation over patches (obligation B), WITHOUT a metric;
- the named candidate spatial relations -- adjacency / neighborhood / gradient / edge / continuity (obligation C),
  WITHOUT equations;
- the distinction between local patch effects and field-level organisation (obligation D), WITHOUT a pass/fail;
- (only later, optionally) a deferred temporal layer (obligation E);
- a claim-lock + verdict summary and the non-authorization guard (obligation F).
All inspection is CONCEPTUAL over offline synthetic content; it adopts no descriptor / coordinate system / metric /
equation / threshold and decides nothing.
```

## 9. What a later implementation may not claim

Even a fully obligation-conformant later study **may not claim** any of:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not live / screen / camera use
not closure                    (the BY gap is visible, not closed, in EITHER abstraction)
not that flat opponent-field is better (still a candidate to bound and explore, not validated)
```

Fixing the preregistration structure is a docs-layer step over an unvalidated abstraction; it says nothing about
real clips or screens and adopts no descriptor or metric. The proof route remains **HELD / HOLD**. The claim locks
and `verdict = HOLD` remain in force.

## 10. Review checklist

A future flat opponent-field preregistration (and any later study) is **consistent with this plan** iff a reviewer
can check all of:

```text
[ ] docs only at THIS stage; any study only after a separate docs-first gate (v2.2 finite audit design first).
[ ] obligations A-F all stated; nothing beyond them; no descriptor / coordinate system / metric / equation / threshold adopted.
[ ] A: patch defined conceptually, no coordinate system / resolution / descriptor.
[ ] B: BY / RG opponent relation explicit, no channel metric / descriptor.
[ ] C: adjacency / neighborhood / gradient / edge / continuity NAMED, no equations.
[ ] D: local-patch vs field-level distinction stated, no pass/fail rule.
[ ] E: temporal layer recorded as later optional, not first principle.
[ ] F: claim locks False; no vision / descriptor-validity / temporal-order / runtime / memory / integration / screen /
    live / real-clip claim.
[ ] deferred set (§7) untouched; v1.x kept as frozen evidence; v2.x kept unvalidated.
[ ] offline only: no screen analysis / capture / camera / live / streaming / real clips; verdict HOLD; no §0; no tags.
```

## 11. Candidate next branches

Docs-first candidates only; **none opened or authorized here**:

```text
A. v2.2 FLAT OPPONENT-FIELD FINITE AUDIT DESIGN (docs-only)
   Turn this finite preregistration into a docs-first finite audit DESIGN: what an offline-only flat-field study
   would conceptually inspect and how it would be bounded -- adopting NO descriptor / coordinate system / metric /
   equation / threshold, opening NO implementation. (Recommended next.)
B. RESUME the BY fixture-metric route (docs-first)
   Only if the flat-field direction stalls or the operator prefers: revisit the frozen fixture route. No lever is
   currently in view.
C. Operator / new-math NOTE (docs-only).
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 12. Recommended next step

**Recommend Branch A (v2.2 flat opponent-field finite audit design, docs-only) next.** v2.1 proposed the
obligations and v2.1a fixes the finite preregistration structure; the clean next move is a docs-first finite audit
DESIGN that says — WITHOUT adopting a descriptor / coordinate system / metric / equation / threshold — what an
offline-only flat-field study would conceptually inspect and how it would be bounded, with the offline / no-screen
/ no-vision boundary restated. **No implementation, screen analysis, descriptor, or coordinate system is
authorized.** B (resume fixtures), C (operator new-math), and D (pause) remain legitimate operator calls.

```text
1. Codex review THIS preregistration plan (docs-only; over committed edge 56b344c).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first v2.2 flat opponent-field
   finite audit design (conceptual; no descriptor / coordinate system / metric / equation / threshold adopted; no
   flat-geometry / screen-analysis / camera / live / real-clip / runtime / memory implementation).
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_PREREG_PLAN_v2.1a.md
(new, docs-only, untracked; over committed edge 56b344c, turning the accepted v2.1 proposal into a FINITE
preregistration plan for a future offline-only flat opponent-field audit, adopting none, authorizing no code).

Verify that this plan:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen-capture/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
  and opens NO flat-geometry and NO screen-analysis implementation;
- specifies REQUIRED PREREGISTRATION OBLIGATIONS ONLY and ADOPTS NONE -- it designs no descriptor, chooses no
  coordinates, defines no equations, creates no thresholds, adopts no metric / coordinate system / pass-fail rule;
  redefines no TOL; expands no family; reopens no spectral group;
- states the core question (what finite preregistration structure must exist before any flat opponent-field
  implementation / descriptor design) and a finite, offline-only, non-drifting scope (§5);
- fixes obligations A-F (patch definition without a coordinate system / descriptor; opponent-channel BY/RG explicit
  without a metric; spatial relations named -- adjacency / neighborhood / gradient / edge / continuity -- without
  equations; local-patch vs field-level distinction without a pass/fail; temporal deferral; non-authorizing guard
  with all claim locks False);
- defers (§7) every descriptor / coordinate system / metric / equation / threshold / TOL / pass-fail / family /
  spectral / classifier / neural / flat / screen / runtime / memory / real-clip decision to a separate later gate;
- frames §8 / §9 correctly (a later study may only inspect CONCEPTUALLY, adopting nothing, and may claim no vision /
  descriptor validity / temporal order / closure / flat-field-superiority / memory / runtime / integration / screen /
  live use), keeps v1.x as FROZEN EVIDENCE and v2.x UNVALIDATED, provides a review checklist (§10), and recommends
  Branch A (v2.2 finite audit design, docs-only), opening no implementation;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted descriptor / coordinate system / metric / equation / threshold / pass-fail rule, any TOL
redefinition, any family expansion, any spectral reopening, any flat-geometry / screen-analysis / camera / live /
real-clip / runtime / memory authorization, any "Brainvision sees" / vision / descriptor-validity / temporal-order
claim, any treatment of v1.x as retracted rather than frozen evidence, any claim that flat opponent-field is
validated, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Preregistration Plan v2.1a. Docs-only plan, non-authorizing. Opens
no implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no frozen formula, gate,
evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no
TOL; adopts no descriptor / coordinate system / metric / equation; specifies the finite flat opponent-field
preregistration obligations only, adopting none; preserves v1.x as frozen evidence and v2.x as an unvalidated
conceptual pivot; makes no vision / "Brainvision sees" / descriptor-validity / temporal-order / memory / runtime /
integration claim; no `§0` pointer added; no tags.*
