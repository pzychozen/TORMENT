# TORMENT Brainvision Flat Opponent-Field Concept Plan v2.0a

## 1. Status / non-claims

**DOCS-ONLY concept plan. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It turns the accepted v2.0 conceptual pivot into a **bounded concept plan**: what the flat opponent-field
abstraction should MEAN, and what a future offline-only research plan would be allowed to inspect *conceptually*.
It **describes and bounds a candidate abstraction — it adopts none**. It defines **no metric, no equation, no
threshold, no descriptor, no coordinate system, no pass/fail rule** and implements nothing. It **authorizes no
code and no tests**, **redefines no `TOL`**, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes
or weakens no control, redesigns no descriptor, reopens no spectral group, expands no generator family, and opens
**no classifier (form B) and no neural encoder (form C)**. It opens **no flat-geometry implementation and no
screen-analysis implementation**. Everything stays offline under `research/brainvision/` + `tests/research/`,
HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. A concept plan alone moves nothing:
**no claim lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v2.0 proposal

```text
v1.7  (9fbb4ef)  failure-anatomy DIAGNOSTIC: BY_failure_anatomy_no_bounded_lever -> recommend a docs-only pivot.
v2.0  (5598c28)  flat opponent-field PROPOSAL: candidate research abstraction pivot; conceptual; adopting none.
v2.0a (this doc) flat opponent-field CONCEPT PLAN: bounds what the abstraction should MEAN and what a future
                 offline-only plan may inspect CONCEPTUALLY; adopting none; authorizing no code.
```

v2.0 named the candidate abstraction; v2.0a bounds it — the conceptual meaning, the candidate components to
consider, the spatial questions it might later license, and the explicit non-goals — so a later docs-first
preregistration (v2.1) has a narrowed, well-bounded starting point. It proves nothing, validates nothing, adopts
nothing, and changes nothing v0.4b / v0.4c / v0.7a froze or v0.7b … v2.0 produced.

## 3. Concept-plan objective

```text
CORE QUESTION:
  What should the flat opponent-field abstraction MEAN, and what would a future OFFLINE-ONLY research plan be
  allowed to inspect CONCEPTUALLY?

OBJECTIVE:
  Bound the flat opponent-field abstraction for a future docs-first preregistration: fix its conceptual meaning
  (§5), the candidate components to consider (§6), the candidate spatial questions (§7), and the explicit
  non-goals (§8) -- WITHOUT adopting any descriptor / metric / equation / threshold and WITHOUT authorizing any
  code, screen analysis, or vision claim.
This is a bounding exercise, not a design, an experiment, or an implementation.
```

## 4. Why the fixture route is paused

```text
- Across v0.8a -> v1.7 the systematic BY signed ordering SURVIVED residual / TOL matching under every
  reporting/guard structure -- named, made visible, preregistered + implemented as the A + D + G spine, and
  anatomised -- always visible, never closed, always on a SINGLE matching family (segment_paired_canceller).
- v1.7 established that no closure decision is representable over the current fixtures WITHOUT a forbidden
  operation (a new threshold / gate / family expansion), so the persistence is best read as ABSTRACTION-LEVEL.
- The BY fixture-metric route is therefore PAUSED (not retracted): the frozen fixture artifacts remain intact
  evidence; the flat opponent-field is an ALTERNATIVE offline abstraction to bound and (later) explore.
The pause is a research-direction choice; the fixture route can be revisited if the flat-field concept stalls.
```

## 5. Flat opponent-field definition, conceptual only

```text
For this concept plan, a FLAT OPPONENT-FIELD means (conceptually, adopting nothing):
  - FLAT   : a 2D spatial arrangement (a plane of positions) of OFFLINE SYNTHETIC content, not a temporal
             trajectory; time is NOT a first principle (component G).
  - OPPONENT: organised around the opponent axes already in play (blue-yellow / red-green), kept CONCEPTUALLY,
             NOT redefined as a descriptor.
  - FIELD  : local, position-indexed opponent content (patches / regions) with spatial relations (adjacency,
             gradients, continuity), rather than a single global trajectory statistic.
The abstraction poses the QUESTION "where is opponent content, and how is it spatially organised?" over offline
synthetic stimuli. It fixes NO coordinates, NO resolution, NO equation, NO descriptor, and NO metric; it is a
conceptual frame only.
```

## 6. Candidate conceptual components

Proposed for DISCUSSION; **NONE adopted, and none turned into a descriptor / metric / equation / threshold /
coordinate system here**. Each names a candidate ELEMENT a flat opponent-field abstraction might represent:

```text
A. Local BY/RG opponent patches
   Position-indexed local opponent content (small regions carrying BY / RG values), rather than a global statistic.
B. Spatial gradients and edges
   How opponent content CHANGES across space -- gradients and edges -- as candidate structure.
C. Region-level opponent balance
   Opponent balance (BY vs RG) per REGION rather than pooled, so a BY-concentrated region is visible in place.
D. Field continuity / discontinuity
   Whether opponent content is spatially CONTINUOUS or breaks (candidate boundaries / segments) across the field.
E. Patch adjacency and neighborhood relation
   Relations BETWEEN patches (which patches neighbour which) as candidate relational structure.
F. Surface-like organization
   Whether patches / regions group into SURFACE-LIKE arrangements (a candidate higher-order organisation).
G. Temporal motion as a later optional layer, not a first principle
   Motion / trajectory is explicitly DEFERRED: the flat field is spatial FIRST; any temporal layer is a later,
   optional, separately-gated addition -- NOT part of this concept plan's core.
```

Each component is a candidate CONCEPTUAL element for future discussion. Adopting any as a descriptor, a metric, a
coordinate system, or an implementation is explicitly **out of scope here** and would need a separate,
separately-gated decision.

## 7. Candidate spatial questions

Illustrative questions the abstraction MIGHT later license (conceptual; none adopted, none answered here):

```text
- Is BY-concentrated opponent content LOCALISED to regions rather than global (A / C)?
- Do opponent gradients / edges (B) or continuity breaks (D) organise the BY structure spatially?
- Do adjacency / surface-like groupings (E / F) separate what the trajectory abstraction entangled onto one family?
- Conceptually, would a spatial-field view make the BY persistence DIAGNOSABLE IN PLACE rather than only
  visible-not-closed?
These are candidate DIRECTIONS for a later docs-first preregistration; they are not experiments, metrics, or claims here.
```

## 8. Explicit non-goals

```text
This concept plan explicitly does NOT:
  - define final equations, coordinates, resolutions, or a scoring function;
  - create or adopt a descriptor / metric / threshold / pass/fail rule; redefine TOL;
  - authorize implementation of any kind (no code / tests);
  - imply, open, or authorize SCREEN ANALYSIS, screen capture, camera / live / sensor / streaming, or real clips;
  - claim vision or that "Brainvision sees"; make any temporal-order / descriptor-validity / readiness claim;
  - expand the generator family, reopen spectral as a closure group, or open a classifier / neural encoder;
  - touch runtime / memory / integration;
  - retract, delete, or invalidate the v1.x fixture-route artifacts (they remain FROZEN EVIDENCE, see §10).
A flat 2D field is superficially close to a screen; this plan is OFFLINE SYNTHETIC and CONCEPTUAL only, and the
non-goal against screen analysis / vision is a standing boundary a later preregistration must restate.
```

## 9. Difference from trajectory / winder-canceller fixtures

```text
current fixture route (v0.7b … v1.7)          flat opponent-field abstraction (conceptual, v2.0 / v2.0a)
-------------------------------------------   ---------------------------------------------------------
1D trajectory of a winder / non-winder        2D spatial field of position-indexed opponent content
canceller
global trajectory statistics                  local / regional opponent content + spatial relations
opponent content read via cancellation        opponent content read via spatial arrangement (patches, gradients,
dynamics                                      regions, adjacency, surfaces)
single matching family; BY offset single-      (candidate) spatial structure not tied to one trajectory family
family structural
time / motion intrinsic                        time / motion DEFERRED to an optional later layer (component G)
```

The difference is a change of ABSTRACTION (what is represented and how it is organised), not a new descriptor or
metric within the same abstraction. Nothing in the current route is redefined; it is paused.

## 10. What remains frozen

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator; the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual; PSC < PSC_FLOOR feasibility; the closed F1-F5 family set; the single matching family;
  the v0.7b samples; spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a … v1.7 records and artifacts, preserved as FROZEN EVIDENCE (not failed / retracted); reused /
  referenced by identity; no sample replacement / new seeds / generation.
- claim locks and verdict HOLD.
The v1.x fixture-route work is preserved evidence of WHAT the trajectory abstraction could and could not close; the
flat opponent-field, if ever explored, is a SEPARATE offline research surface and does not modify any of the above.
```

## 11. What remains unproven

Bounding a new abstraction leaves all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not closure                    (the BY gap is visible; it is not closed, in EITHER abstraction)
not that flat opponent-field is better (it is a candidate to bound and explore, not a validated abstraction)
```

The proof route remains **HELD / HOLD**. Bounding the abstraction changes the research DIRECTION, not the
evidentiary status: the claim locks (`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`,
`descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force.

## 12. Risks / ambiguity notes

```text
- SCOPE CREEP TO SCREEN / VISION: "flat 2D field" is close to a screen. This plan is OFFLINE SYNTHETIC and
  conceptual ONLY; it authorizes NO screen analysis, NO real clips, NO camera / live capture, and makes NO vision
  claim. v2.1 must restate this boundary before any preregistration.
- REINVENTING A DESCRIPTOR: components A-F could drift into a new descriptor. They are candidate CONCEPTUAL
  elements; adopting any as a descriptor / metric / coordinate system is out of scope and separately gated.
- UNFALSIFIABLE REFRAME: a new abstraction can look attractive without being testable. v2.1 must state, docs-first,
  what would count as the flat field REPRESENTING opponent structure better -- WITHOUT adopting a metric / threshold.
- TREATING v1.x AS GARBAGE: the fixture-route artifacts are FROZEN EVIDENCE, not failure to discard. The pivot must
  preserve them and may revisit the fixture route if the flat-field concept stalls.
- TEMPORAL TEMPTATION: motion is deferred (G). Pulling time in early would re-entangle the structure the pivot is
  trying to spatialise; keep the first pass spatial.
- OVER-SPECIFICATION: a concept plan that fixes coordinates / resolution / equations has already overstepped. This
  plan bounds MEANING and QUESTIONS only; specifics belong to a later, separately-gated preregistration (and only
  its docs-first stage).
- NON-AUTHORIZATION: none of this authorizes descriptor validity, temporal order, vision, runtime, memory,
  integration, or live / screen use.
```

## 13. Candidate next branches

Docs-first candidates only; **none opened or authorized here**:

```text
A. v2.1 FLAT OPPONENT-FIELD PREREGISTRATION PROPOSAL (docs-only)
   Turn this bounded concept into a docs-first preregistration proposal: which candidate components (A-F) a future
   offline-only plan would represent, and what would count as the flat field representing opponent structure better
   -- adopting NO descriptor / metric / equation / threshold, opening NO implementation. (Recommended next.)
B. RESUME the BY fixture-metric route (docs-first)
   Only if the flat-field concept stalls or the operator prefers: revisit the frozen fixture route. No lever is
   currently in view.
C. Operator / new-math NOTE (docs-only).
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 14. Recommended next step

**Recommend Branch A (v2.1 flat opponent-field preregistration proposal, docs-only) next.** v2.0 named the
abstraction and v2.0a bounds it; the clean next move is a docs-first preregistration proposal that fixes which
candidate components a future offline-only plan would represent and — WITHOUT adopting a descriptor / metric /
equation / threshold — what would count as the flat field representing opponent structure better, with the offline
/ no-screen / no-vision boundary restated. **No implementation, screen analysis, or descriptor is authorized**; the
flat field is a research abstraction to bound and (later) explore, not adopted machinery. B (resume fixtures), C
(operator new-math), and D (pause) remain legitimate operator calls.

```text
1. Codex review THIS concept plan (docs-only; over committed edge 5598c28).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first v2.1 flat opponent-field
   preregistration proposal (conceptual; no descriptor / metric / equation / threshold adopted; no flat-geometry /
   screen-analysis / camera / live / real-clip / runtime / memory implementation).
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 15. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_CONCEPT_PLAN_v2.0a.md
(new, docs-only, untracked; over committed edge 5598c28, bounding the flat opponent-field abstraction into a
concept plan after the accepted v2.0 pivot, adopting none).

Verify that this concept plan:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen-capture/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
  and opens NO flat-geometry and NO screen-analysis implementation;
- bounds a candidate research ABSTRACTION ONLY and ADOPTS NONE -- it defines no descriptor, no metric, no equation,
  no threshold, no coordinate system, no pass/fail rule; redefines no TOL; expands no family; reopens no spectral group;
- states the core question (what the flat opponent-field should MEAN and what a future offline-only plan may inspect
  CONCEPTUALLY) and gives a conceptual-only definition (§5) with candidate components A-G (§6) and candidate spatial
  questions (§7) as discussion, adopting none;
- lists explicit NON-GOALS (§8: no equations / descriptor / implementation / screen analysis / vision claim / temporal
  layer as first principle) and preserves the v1.x fixture artifacts as FROZEN EVIDENCE, not failed / retracted work
  (§4 / §10);
- keeps everything in §10 frozen and §11 unproven (including that flat opponent-field is NOT proven better), lists
  risks (§12: scope creep to screen/vision, reinventing a descriptor, unfalsifiable reframe, treating v1.x as garbage,
  temporal temptation, over-specification), recommends Branch A (v2.1 preregistration proposal, docs-only), and opens
  no implementation;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted descriptor / metric / equation / threshold / coordinate system / pass-fail rule, any TOL
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

*End — TORMENT Brainvision Flat Opponent-Field Concept Plan v2.0a. Docs-only concept plan, non-authorizing. Opens
no implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no frozen formula, gate,
evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines no
TOL; adopts no metric or equation; bounds the candidate flat opponent-field abstraction (meaning, components,
questions, non-goals) only, adopting none; preserves the v1.x fixture route as frozen evidence, not retracted; makes
no vision / "Brainvision sees" / descriptor-validity / temporal-order / memory / runtime / integration claim; no
`§0` pointer added; no tags.*
