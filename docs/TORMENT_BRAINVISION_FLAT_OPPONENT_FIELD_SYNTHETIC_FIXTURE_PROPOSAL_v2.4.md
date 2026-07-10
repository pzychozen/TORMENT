# TORMENT Brainvision Flat Opponent-Field Synthetic Fixture Proposal v2.4

## 1. Status / non-claims

**DOCS-ONLY proposal. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It proposes — for future, separately-gated consideration only — the **smallest offline synthetic fixture
family** that could later let an offline audit inspect whether flat opponent-field concepts (local BY/RG opponent
patches, adjacency, gradients, edges, continuity/discontinuity, region/field separation) can be represented
*structurally*. It **describes candidate fixture families and implements none**. It defines **no descriptor, no
coordinate system, no metric, no equation, no threshold, no pass/fail validity rule** and implements nothing. It
**authorizes no code and no tests**, **redefines no `TOL`**, changes no formula / §7 anti-proxy logic / §8 verdict
logic, deletes or weakens no control, redesigns no descriptor, reopens no spectral group, expands no *frozen*
generator family, and opens **no classifier (form B) and no neural encoder (form C)**. It opens **no
flat-geometry implementation and no screen-analysis implementation**. Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

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

## 2. Relation to v2.3 findings

```text
v2.2  (8376caa)  flat opponent-field AUDIT DESIGN: reporting panels A-F + fields + guards + breach conditions.
v2.2a (a37c93d)  implementation AUTHORIZATION review: exact v2.3 boundary.
v2.3  (0d8722e)  flat opponent-field HARNESS: generated panels A-F as structural reporting (no fixture, no data).
v2.3f (813c76c)  FINDINGS: FLAT_OPPONENT_FIELD_REPORTING_GENERATED; flat_field_validated False; HOLD.
v2.4  (this doc) minimal synthetic fixture PROPOSAL: the smallest offline fixture family that could LATER test the
                 flat opponent-field concepts structurally; conceptual; implementing none.
```

v2.3 showed the obligation structure is representable as conceptual reporting but rests on **zero fixtures** — the
abstraction is unvalidated because there is nothing to inspect yet. v2.4 proposes the smallest synthetic fixture
family that a future audit could inspect, so the flat opponent-field concepts stop being purely conceptual. It
proves nothing, validates nothing, adopts nothing, implements nothing, and changes nothing v0.4b / v0.4c / v0.7a
froze or v0.7b … v2.3 produced.

## 3. Fixture-proposal objective

```text
CORE QUESTION:
  What MINIMAL synthetic fixture family would let a future offline audit inspect local BY/RG opponent patches,
  adjacency, gradients, edges, continuity/discontinuity, and region/field separation -- WITHOUT adopting
  descriptors, coordinates, metrics, equations, thresholds, or pass/fail validity rules?

OBJECTIVE:
  Propose the SMALLEST candidate fixture families (A-F) that could each conceptually exercise one flat
  opponent-field concept, plus the controls that prevent trivial reporting optimism -- as candidates to bound in a
  later preregistration, NOT as fixtures to build. It proposes families only; it adopts NO descriptor / coordinate
  system / metric / equation / threshold and implements NO fixture.
```

## 4. Why a minimal synthetic fixture is needed

```text
- v2.3 reported a DESIGN, not a MEASUREMENT: the flat opponent-field panels A-F exist as conceptual conformance,
  but there is no synthetic content to inspect, so nothing about the abstraction can be tested.
- To move from "the obligation structure exists" toward "the concepts can be represented structurally", a future
  audit needs the SMALLEST possible synthetic fixtures -- each isolating ONE concept (patch, adjacency, gradient,
  edge, region/field) -- so the inspection is bounded and non-drifting.
- MINIMALITY is the safeguard: the smallest fixture family that exercises each concept keeps a later audit from
  needing a descriptor, a coordinate system, or a metric to say anything, and keeps the offline / no-screen /
  no-vision boundary easy to hold. A large or naturalistic fixture set would invite exactly the drift v2.x guards against.
- Controls (family F + §7) are needed so a future audit cannot report optimism trivially (e.g. "structure present"
  when a neutral field would report the same).
```

## 5. Proposed minimal fixture families

Proposed for DISCUSSION; **NONE implemented, and none turned into a descriptor / coordinate system / metric /
equation / threshold here**. Each is the SMALLEST candidate synthetic family exercising ONE flat opponent-field
concept:

```text
A. Uniform opponent patches
   Isolated BY / RG local regions (a single opponent patch on an otherwise neutral field). Tests PATCH
   EXPLICITNESS only (is a local opponent patch conceptually present?).
B. Adjacent opponent patches
   Two or more neighbouring local opponent regions. Tests ADJACENCY / NEIGHBORHOOD relation conceptually (are two
   patches conceptually next to each other?).
C. Gradient fields
   Smooth BY / RG transition fields (opponent content changing gently across the field). Tests GRADIENT /
   CONTINUITY conceptually.
D. Edge / discontinuity fields
   A sharp opponent boundary (opponent content changing abruptly). Tests EDGE / DISCONTINUITY conceptually.
E. Region-field separation fixtures
   A local patch pattern set against a global field organisation. Tests the LOCAL-vs-FIELD distinction conceptually
   (is a local patch effect distinguishable from field-level organisation?).
F. Null / control fields
   Uniform neutral or matched non-opponent controls (no opponent structure, or opponent-matched-but-unstructured).
   PREVENTS trivial reporting optimism (a concept must be reportable ABOVE what a null / matched control reports).
```

Each family is a candidate CONCEPT-ISOLATING fixture for future discussion. Fixing coordinates, a resolution, a
descriptor, a metric, or an equation for any of them is explicitly **out of scope here** and would need a separate,
separately-gated decision. These are conceptual families, NOT an expansion of the frozen fixture-route F1-F5 family
set (which stays closed) and NOT implemented content.

## 6. What each fixture family would inspect conceptually

Illustrative mapping of families to the flat opponent-field concepts (conceptual; none adopted, none measured
here):

```text
family  isolates concept                         maps to v2.2 panel / obligation
------  --------------------------------------   -------------------------------
A       patch explicitness                       A patch-definition / B opponent-channel
B       adjacency / neighborhood                 C spatial-relation (adjacency, neighborhood)
C       gradient / continuity                    C spatial-relation (gradient, continuity)
D       edge / discontinuity                     C spatial-relation (edge, continuity-discontinuity)
E       local-vs-field separation                D region-field
F       null / control                           (controls ALL of A-E; prevents trivial optimism)
A future audit would ask, conceptually and per family: "is THIS concept reportable structurally, and reportable
ABOVE the null / matched control (F)?" -- WITHOUT a descriptor, coordinate system, metric, equation, or threshold.
```

## 7. Required controls

```text
Any future fixture family MUST be accompanied by controls, so a later audit cannot report optimism trivially:
- NULL control: a uniform neutral field with NO opponent structure (family F). A concept must be reportable ABOVE
  what the null reports.
- MATCHED non-opponent control: content matched in low-level respects but lacking the opponent STRUCTURE, so the
  report cannot be explained by a trivial confound.
- PER-CONCEPT control: each of A-E paired with a minimal variant lacking ITS concept (e.g. adjacency fixture vs a
  non-adjacent variant), so the concept is isolated.
- SYMMETRY / balance: opponent axes (BY vs RG) represented so neither is privileged by construction.
Controls are CONCEPTUAL requirements on a future fixture family; this proposal fixes NO control metric, threshold,
or pass/fail rule -- only that controls MUST exist and what they must guard against.
```

## 8. What must remain frozen

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator; the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual; PSC < PSC_FLOOR feasibility; the closed F1-F5 fixture-route family set (NOT expanded);
  the single matching family; the v0.7b samples; spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a … v1.7 fixture-route records, preserved as FROZEN EVIDENCE; v2.0 … v2.3 as an UNVALIDATED conceptual
  pivot; no sample replacement / new seeds / generation of the FROZEN families.
- claim locks and verdict HOLD.
The proposed flat-field fixture families are a SEPARATE, candidate, offline synthetic surface; they do NOT modify or
expand the frozen fixture-route family set, and nothing here is implemented.
```

## 9. What must not be adopted yet

The proposal adopts nothing forward-looking. Explicitly deferred to a separate, later, gated decision (NOT opened,
NOT authorized here):

```text
- NO descriptor for the flat field; NO coordinate system; NO resolution; NO patch / relation / region EQUATION.
- NO metric / scoring function / threshold / ratio / cutoff / pass-fail validity rule / control metric.
- NO TOL / floor / CHANCE_BAND change; NO §7 / §8 / control / evaluator change; NO change to the frozen descriptor.
- NO expansion of the FROZEN F1-F5 fixture-route family set; NO spectral reopening as a closure group.
- NO classifier (form B); NO neural encoder (form C).
- NO fixture IMPLEMENTATION; NO flat-geometry / screen-analysis implementation; NO camera / live / sensor /
  screen-capture / streaming; NO real clips.
- NO runtime / memory / integration; NO torment_service touch.
- NO temporal / motion content (deferred; the fixtures are spatial-first).
A proposal that implemented a fixture, or adopted any of the above, would stop being a proposal. This one implements
and adopts nothing.
```

## 10. What would count as useful evidence

A docs-only fixture proposal yields **no empirical evidence** about the flat opponent-field. "Useful" here means
the families are an adequate candidate set — **not** a validation, a descriptor, or a metric:

```text
- The families A-E each isolate ONE flat opponent-field concept at the SMALLEST scale, and F + §7 controls prevent
  trivial optimism, so a future audit COULD inspect each concept structurally without a descriptor / metric.
- The families are jointly MINIMAL and CONCEPT-COMPLETE for the v2.2 panels (patch, adjacency, gradient, edge,
  region-field), so a later preregistration could bound them without gaps or bloat.
- The frozen set (§8) and the deferral set (§9) are complete enough that a future fixture study could not quietly
  become a descriptor, a coordinate system, a metric, or a screen path.
- Codex accepts the proposal AS-IS (or with bounded modifications) as docs-only, implementing nothing.
Useful evidence is that the fixture families are MINIMAL, CONCEPT-COMPLETE, and CONTROLLED -- a candidate set -- not
that the flat opponent-field abstraction has been validated or that anything has been built.
```

## 11. What would still not be proven

Even a complete, Codex-accepted fixture proposal would leave all of the following **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not closure                    (the BY gap is visible, not closed, in the fixture route)
not that flat opponent-field is better / valid (the fixtures are a candidate set, not built or validated)
```

The proof route remains **HELD / HOLD**. Proposing fixtures fixes candidate families; it validates nothing and
builds nothing. The claim locks (`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`,
`descriptor_validity_claim_allowed`) and `verdict = HOLD` remain in force.

## 12. Candidate next branches

Docs-first candidates only; **none opened or authorized here**:

```text
A. v2.4a MINIMAL SYNTHETIC FIXTURE PREREGISTRATION PLAN (docs-only)
   Turn these candidate families into a docs-first preregistration plan: which families (A-F) a future offline
   fixture study must include, what controls are required, and what it may never claim -- adopting NO descriptor /
   coordinate system / metric / equation / threshold, implementing NO fixture. (Recommended next.)
B. RESUME the BY fixture-metric route (docs-first)
   Only if the flat-field direction stalls or the operator prefers: revisit the frozen fixture route. No lever is
   currently in view.
C. Operator / new-math NOTE (docs-only).
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 13. Recommended next step

**Recommend Branch A (v2.4a minimal synthetic fixture preregistration plan, docs-only) next.** v2.4 names the
smallest candidate fixture families and controls; the clean next move is a docs-first preregistration plan that
fixes which families a future offline fixture study must include and what controls are required — WITHOUT adopting a
descriptor / coordinate system / metric / equation / threshold and WITHOUT implementing any fixture, with the
offline / no-screen / no-vision boundary restated. **Do not implement fixtures, and claim no validation.** B (resume
fixtures), C (operator new-math), and D (pause) remain legitimate operator calls.

```text
1. Codex review THIS proposal (docs-only; over committed edge 813c76c).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first v2.4a minimal synthetic
   fixture preregistration plan (conceptual; no fixture implemented; no descriptor / coordinate system / metric /
   equation / threshold adopted; no flat-geometry / screen-analysis / camera / live / real-clip / runtime / memory
   implementation).
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 14. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_PROPOSAL_v2.4.md
(new, docs-only, untracked; over committed edge 813c76c, proposing the smallest offline synthetic fixture family
that could LATER test the flat opponent-field concepts structurally, implementing none, adopting none).

Verify that this proposal:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen-capture/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
  and opens NO flat-geometry and NO screen-analysis implementation; implements NO fixture;
- proposes candidate fixture FAMILIES ONLY and ADOPTS / IMPLEMENTS NONE -- it designs no descriptor, chooses no
  coordinates, defines no equations, creates no metrics / thresholds / pass-fail rules; redefines no TOL; does NOT
  expand the frozen F1-F5 family set; reopens no spectral group;
- states the core question (smallest fixture family to inspect patches / adjacency / gradients / edges / continuity-
  discontinuity / region-field separation WITHOUT descriptors / coordinates / metrics / equations / thresholds /
  pass-fail) and argues why MINIMALITY + controls are the safeguard (§4);
- lists candidate families A-F (uniform opponent patches / adjacent patches / gradient fields / edge-discontinuity
  fields / region-field separation / null-control) as discussion, mapped to the v2.2 panels (§6), with REQUIRED
  CONTROLS (§7: null, matched non-opponent, per-concept, symmetry) that prevent trivial reporting optimism -- fixing
  NO control metric / threshold / pass-fail;
- keeps everything in §8 frozen (including the frozen F1-F5 set NOT expanded) and §9 deferred / not adopted; frames
  useful evidence (§10) as fixture-set ADEQUACY (minimal, concept-complete, controlled) NOT validation; and §11 leaves
  vision / descriptor validity / temporal order / closure / flat-field-superiority UNPROVEN;
- keeps v1.x as FROZEN EVIDENCE and v2.x UNVALIDATED; recommends Branch A (v2.4a preregistration plan, docs-only;
  no fixture implemented), opening no implementation;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted descriptor / coordinate system / metric / equation / threshold / control metric / pass-fail rule,
any TOL redefinition, any expansion of the frozen F1-F5 family set, any spectral reopening, any fixture
implementation, any flat-geometry / screen-analysis / camera / live / real-clip / runtime / memory authorization,
any "Brainvision sees" / vision / descriptor-validity / temporal-order claim, any claim that flat opponent-field is
validated, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Synthetic Fixture Proposal v2.4. Docs-only conceptual fixture
proposal, non-authorizing. Opens no implementation lane; implements no fixture; opens no classifier / neural / screen
/ flat-geometry work; changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no control;
redesigns no descriptor; invents no threshold; redefines no TOL; adopts no descriptor / coordinate system / metric /
equation; does not expand the frozen F1-F5 family set; proposes the smallest candidate flat opponent-field fixture
families (A-F) + required controls only, adopting and implementing none; preserves v1.x as frozen evidence and v2.x
as an unvalidated conceptual pivot; makes no vision / "Brainvision sees" / descriptor-validity / temporal-order /
memory / runtime / integration claim; no `§0` pointer added; no tags.*
