# TORMENT Brainvision Flat Opponent-Field Proposal v2.0

## 1. Status / non-claims

**DOCS-ONLY conceptual proposal. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no
integration lane.** It proposes — for future, separately-gated consideration only — a candidate **research
abstraction pivot**: whether offline Brainvision should move away from trajectory / winder-canceller *fixture*
geometry toward a **flat opponent-plane / spatial-field** structure as its next offline research abstraction,
motivated by the persistent BY-axis failure the fixture-metric route could not close (v1.7: no bounded lever). It
**describes a candidate abstraction and adopts none**. It defines **no metric, no equation, no threshold, no
descriptor, no pass/fail rule** and implements nothing. It **authorizes no code and no tests**, **redefines no
`TOL`**, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control, redesigns no
descriptor, reopens no spectral group, expands no generator family, and opens **no classifier (form B) and no
neural encoder (form C)**. It opens **no flat-geometry implementation and no screen-analysis implementation**.
Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

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

## 2. Relation to v1.7 no-bounded-lever result

```text
v1.5f (559964a)  FINDINGS: BY_aware_closure_gap_still_visible; closure_achieved False; HOLD.
v1.6  (e992936)  failure-anatomy PROPOSAL: decision point -- bounded lever OR pivot; LAST fixture-metric step
                 unless a bounded lever.
v1.6a (c9adced)  finite failure-anatomy PLAN: mechanisms A-E; bounded-lever criteria; stop/pivot rule.
v1.7  (9fbb4ef)  failure-anatomy DIAGNOSTIC: BY_failure_anatomy_no_bounded_lever -> recommended_next =
                 flat_opponent_plane_spatial_field_proposal.
v2.0  (this doc) flat opponent-field PROPOSAL: candidate research abstraction pivot; conceptual; adopting none.
```

v1.7 ran the final bounded fixture-metric anatomy and found **no** concrete bounded lever: every fixture-metric
mechanism (A / C / D) would require a forbidden operation (a threshold / offset-vs-`TOL` gate / binding gate) and
B / E are pivot signals (the signed offset is single-family structural; the abstraction is the likely level of the
failure). Per the v1.6 / v1.6a stop/pivot rule, that recommends a **docs-only geometry pivot proposal**. This is
that proposal. It proves nothing, validates nothing, adopts nothing, and changes nothing v0.4b / v0.4c / v0.7a
froze or v0.7b … v1.7 produced.

## 3. Why the BY fixture-metric route should pause

```text
- Across v0.8a -> v1.7 the systematic BY signed ordering SURVIVED residual / TOL matching under every
  reporting/guard structure: named (v0.8a), made visible (v0.9b), preregistered + implemented as the A + D + G
  spine (v1.4 / v1.5), and anatomised (v1.7) -- always visible, never closed, always on a SINGLE matching family
  (segment_paired_canceller).
- v1.7 established that no closure decision is representable over the current fixtures WITHOUT a new threshold /
  gate or a family expansion (all out of scope). The persistence is therefore best read as ABSTRACTION-LEVEL:
  the trajectory / winder-canceller fixture family may simply be the WRONG abstraction for the opponent-axis
  structure a screen-like vision task would need.
- PAUSING the fixture-metric grind (not deleting it) and considering a different abstraction is the disciplined
  move the stop/pivot rule was written for. The frozen fixture artifacts (v0.7b matching, descriptor, TOL, family
  set) remain intact and untouched; the pause is a research-direction choice, not a retraction.
```

## 4. Proposed new abstraction: flat opponent-field geometry

```text
CORE QUESTION:
  Should Brainvision move away from trajectory / winder-canceller FIXTURE geometry toward a 2D OPPONENT-FIELD /
  SPATIAL-FIELD structure as the next OFFLINE research abstraction?

PROPOSAL (conceptual only):
  Consider representing the offline synthetic stimulus as a FLAT 2D FIELD of local opponent-axis (BY / RG) content
  -- a spatial arrangement of opponent patches, gradients, and regions -- rather than as a 1D trajectory of a
  winder / non-winder canceller. The hypothesis to EXPLORE (later, docs-first) is that opponent-axis structure
  which is entangled / single-family / non-closable in the trajectory abstraction may be more naturally
  represented -- and its BY persistence more diagnosable -- in a flat spatial-field abstraction.
This is a candidate ABSTRACTION to explore, NOT an adopted representation, descriptor, or implementation.
```

## 5. What "flat opponent-field" means conceptually

```text
- FLAT: a 2D spatial arrangement (a plane of positions), not a temporal trajectory; time is NOT a first principle
  here (see component G).
- OPPONENT: organised around the same opponent axes already in play (blue-yellow / red-green), kept conceptually,
  NOT redefined as a descriptor.
- FIELD: local, position-indexed opponent content (patches / regions) with spatial relations (adjacency,
  gradients, continuity), rather than a single global trajectory statistic.
- The idea is a REPRESENTATIONAL frame for offline synthetic stimuli: "where is opponent content, and how is it
  spatially organised?" -- a different question than "how does a winder/non-winder trajectory cancel?".
This is a conceptual meaning only; it fixes no coordinates, no resolution, no equation, and no descriptor.
```

## 6. What it does not mean

```text
- It does NOT mean Brainvision now sees, or that any vision / "Brainvision sees" claim is made.
- It does NOT mean screen analysis, screen capture, camera / live / sensor / streaming, or real clips are opened.
- It does NOT implement flat geometry; it opens NO flat-geometry / screen-analysis implementation.
- It does NOT adopt a new descriptor, metric, equation, threshold, or pass/fail rule; it redefines NO TOL.
- It does NOT expand the generator family, reopen spectral as a closure group, or open a classifier / neural encoder.
- It does NOT touch runtime / memory / integration, and makes NO readiness claim of any kind.
- It does NOT retract or invalidate the frozen fixture-route artifacts; it PAUSES that route, it does not delete it.
```

## 7. Candidate field components

Proposed for DISCUSSION; **NONE adopted, and none turned into a descriptor / metric / equation / threshold
here**. Each names a candidate ELEMENT a flat opponent-field abstraction might represent:

```text
A. Local BY/RG opponent patches
   Position-indexed local opponent content (small regions carrying BY / RG values) rather than a global statistic.
B. Spatial gradients and edges
   How opponent content CHANGES across space -- gradients and edges -- as candidate structure.
C. Region-level opponent balance
   Opponent balance (BY vs RG) computed per REGION rather than pooled, so a BY-concentrated region is visible in place.
D. Field continuity / discontinuity
   Whether opponent content is spatially CONTINUOUS or breaks (candidate boundaries / segments) across the field.
E. Patch adjacency / neighborhood relations
   Relations BETWEEN patches (which patches neighbour which) as candidate relational structure.
F. Surface-like organization
   Whether patches / regions group into SURFACE-LIKE arrangements (a candidate higher-order organisation).
G. Temporal motion only as a later optional layer, not a first principle
   Motion / trajectory is explicitly DEFERRED: the flat field is spatial FIRST; any temporal layer is a later,
   optional, separately-gated addition -- NOT part of this proposal's core.
```

Each component is a candidate REPRESENTATIONAL element for future discussion. Adopting any as a descriptor, a
metric, a coordinate system, or an implementation is explicitly **out of scope here** and would need a separate,
separately-gated decision.

## 8. Candidate spatial questions

Illustrative questions a flat opponent-field abstraction MIGHT later let one ask (conceptual; none adopted, none
answered here):

```text
- Is BY-concentrated opponent content LOCALISED to regions rather than global (C / A)?
- Do opponent gradients / edges (B) or continuity breaks (D) organise the BY structure spatially?
- Do adjacency / surface-like groupings (E / F) separate what the trajectory abstraction entangled onto a single family?
- Would a spatial-field view make the BY persistence DIAGNOSABLE in place, rather than only visible-not-closed?
These are candidate DIRECTIONS for a later docs-first concept plan; they are not experiments, metrics, or claims here.
```

## 9. How this differs from trajectory/winder-canceller fixtures

```text
current fixture route (v0.7b … v1.7)          proposed flat opponent-field abstraction (conceptual)
-------------------------------------------   ------------------------------------------------------
1D trajectory of a winder / non-winder        2D spatial field of position-indexed opponent content
canceller
global trajectory statistics (the descriptor  local / regional opponent content + spatial relations
_stats over the whole trajectory)
opponent content read via cancellation        opponent content read via spatial arrangement (patches,
dynamics                                      gradients, regions, adjacency)
single matching family (segment_paired_        (candidate) spatial structure not tied to one trajectory family
canceller); BY offset single-family structural
time / motion intrinsic to the fixture        time / motion DEFERRED to an optional later layer (component G)
```

The difference is a change of ABSTRACTION (what is represented and how it is organised), not a new descriptor or
metric within the same abstraction. Nothing in the current route is redefined; it is paused.

## 10. Risks and ambiguity notes

```text
- SCOPE CREEP TO SCREEN / VISION: a "flat 2D field" is superficially close to a screen. This proposal is OFFLINE
  SYNTHETIC and conceptual ONLY; it authorizes NO screen analysis, NO real clips, NO camera / live capture, and
  makes NO vision claim. The next step (v2.0a) must restate this boundary before any concept work.
- REINVENTING A DESCRIPTOR: components A-F could drift into a new descriptor. They are candidate ELEMENTS for
  discussion; adopting any as a descriptor / metric / coordinate system is out of scope and separately gated.
- UNFALSIFIABLE REFRAME: a new abstraction can look attractive without being testable. A later concept plan must
  state, docs-first, what would count as the flat field REPRESENTING opponent structure better -- WITHOUT adopting
  a metric or threshold -- else this is just relabeling.
- ABANDONING EVIDENCE: the pivot must not discard the frozen fixture-route findings. They remain intact; the flat
  field is an ALTERNATIVE abstraction to explore, and the fixture route can be revisited if the pivot stalls.
- TEMPORAL TEMPTATION: motion is deferred (G). Pulling time back in early would re-entangle the exact structure the
  pivot is trying to spatialise; keep the first pass spatial.
- NON-AUTHORIZATION: none of this authorizes descriptor validity, temporal order, vision, runtime, memory,
  integration, or live / screen use.
```

## 11. What remains frozen

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator; the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual; PSC < PSC_FLOOR feasibility; the closed F1-F5 family set; the single matching family;
  the v0.7b samples; spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a … v1.7 records and artifacts, reused / referenced by identity; no sample replacement / new seeds / generation.
- claim locks and verdict HOLD.
This proposal freezes ALL of the above; a flat opponent-field abstraction, if ever explored, is a SEPARATE offline
research surface and does not modify the frozen fixture route.
```

## 12. What remains unproven

Proposing a new abstraction — and even choosing to pivot — leaves all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not closure                    (the BY gap is visible; it is not closed, in EITHER abstraction)
not that flat opponent-field is better (it is a candidate to explore, not a validated abstraction)
```

The proof route remains **HELD / HOLD**. A pivot changes the research DIRECTION, not the evidentiary status: the
claim locks (`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`,
`descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force.

## 13. Candidate next branches

Docs-first candidates only; **none opened or authorized here**:

```text
A. v2.0a FLAT OPPONENT-FIELD CONCEPT PLAN (docs-only)
   Turn this proposal into a concrete, docs-first concept plan: which candidate components (A-F) to explore first,
   what would count as the flat field representing opponent structure better, and the boundary restated -- adopting
   NO descriptor / metric / equation / threshold, opening NO implementation. (Recommended next.)
B. RESUME the BY fixture-metric route (docs-first)
   Only if the pivot stalls or the operator prefers: revisit the frozen fixture route. No lever is currently in view.
C. Operator / new-math NOTE (docs-only).
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 14. Recommended next step

**Recommend Branch A (v2.0a flat opponent-field concept plan, docs-only) next.** v1.7 exhausted the fixture-metric
route; this proposal names a candidate abstraction; the clean next move is a docs-first concept plan that picks
which candidate components to explore and states — WITHOUT adopting a descriptor / metric / equation / threshold —
what would count as the flat field representing opponent structure better, with the offline / no-screen / no-vision
boundary restated. **No implementation, screen analysis, or descriptor is authorized**; the flat field is a
research abstraction to explore, not adopted machinery. B (resume fixtures), C (operator new-math), and D (pause)
remain legitimate operator calls.

```text
1. Codex review THIS proposal (docs-only; over committed edge 9fbb4ef).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first v2.0a flat opponent-field
   concept plan (conceptual; no descriptor / metric / equation / threshold adopted; no flat-geometry /
   screen-analysis / camera / live / real-clip / runtime / memory implementation).
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 15. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_PROPOSAL_v2.0.md
(new, docs-only, untracked; over committed edge 9fbb4ef, proposing a conceptual research abstraction pivot to flat
opponent-plane / spatial-field geometry after v1.7 found no bounded lever, adopting none).

Verify that this proposal:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen-capture/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
  and opens NO flat-geometry and NO screen-analysis implementation;
- proposes a candidate research ABSTRACTION pivot ONLY and ADOPTS NONE -- it defines no descriptor, no metric, no
  equation, no threshold, no pass/fail rule; redefines no TOL; expands no family; reopens no spectral group;
- motivates the pivot correctly from v1.7 (no bounded lever; BY persistence is single-family structural /
  abstraction-level) and frames pausing the fixture-metric route as a research-direction choice, NOT a retraction
  (frozen fixture artifacts remain intact);
- states clearly what "flat opponent-field" means conceptually (§5) and what it does NOT mean (§6: no vision /
  "Brainvision sees" claim, no screen analysis, no flat-geometry implementation, no new descriptor, no equations /
  thresholds);
- lists candidate field components A-G (local BY/RG patches / gradients-edges / region-level balance / continuity /
  adjacency / surface-like organization / temporal motion deferred as a later optional layer) as discussion only,
  adopting none; keeps everything in §11 frozen and §12 unproven (including that flat opponent-field is NOT proven better);
- lists risks (§10: scope creep to screen/vision, reinventing a descriptor, unfalsifiable reframe, abandoning
  evidence, temporal temptation, non-authorization), recommends Branch A (v2.0a concept plan, docs-only) next, and
  opens no implementation;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted descriptor / metric / equation / threshold / pass-fail rule, any TOL redefinition, any family
expansion, any spectral reopening, any flat-geometry / screen-analysis / camera / live / real-clip / runtime / memory
authorization, any "Brainvision sees" / vision / descriptor-validity / temporal-order claim, any claim that closure
is achieved or that flat opponent-field is validated, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Proposal v2.0. Docs-only conceptual abstraction-pivot proposal,
non-authorizing. Opens no implementation lane; opens no classifier / neural / screen / flat-geometry work; changes
no frozen formula, gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no
threshold; redefines no TOL; adopts no metric or equation; proposes a candidate flat opponent-field research
abstraction only, adopting none; pauses (does not retract) the BY fixture-metric route; makes no vision /
"Brainvision sees" / descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer
added; no tags.*
