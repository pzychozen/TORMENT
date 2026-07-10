# TORMENT Brainvision Flat Opponent-Field Synthetic Fixture Preregistration Plan v2.4a

## 1. Status / non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration lane.**
It turns the accepted v2.4 minimal synthetic fixture proposal into a **finite preregistration plan**: the finite
synthetic fixture obligations that must be preregistered before any future flat opponent-field fixture
implementation can be considered. It **specifies required preregistration obligations only — it adopts no
descriptor, no coordinate system, no metric, no equation, no threshold, no pass/fail validity rule**, and
implements nothing. It **authorizes no code and no tests**, **redefines no `TOL`**, changes no formula / §7
anti-proxy logic / §8 verdict logic, deletes or weakens no control, redesigns no descriptor, reopens no spectral
group, expands no *frozen* generator family, and opens **no classifier (form B) and no neural encoder (form C)**.
It opens **no flat-geometry implementation and no screen-analysis implementation**. Everything stays offline under
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

## 2. Relation to v2.4 proposal

```text
v2.3f (813c76c)  flat opponent-field FINDINGS: FLAT_OPPONENT_FIELD_REPORTING_GENERATED; flat_field_validated False.
v2.4  (8dfd48c)  minimal synthetic fixture PROPOSAL: candidate families A-F + controls; implementing none.
v2.4a (this doc) minimal synthetic fixture PREREGISTRATION plan: the FINITE fixture obligations + controls +
                 reporting obligations + deferrals that must be preregistered before any fixture implementation;
                 adopting none; authorizing no code.
```

v2.4 named the smallest candidate fixture families and controls; v2.4a fixes the finite preregistration plan — the
fixture-family obligations (A-F), the required controls, the required reporting obligations, and the deferred
design decisions — so a later docs-first authorization review (v2.5) has a narrowed, well-bounded starting point.
Where v2.4 proposed WHAT families could be, v2.4a says what a preregistration of them must FIX and DEFER. It proves
nothing, validates nothing, adopts nothing, implements nothing, and changes nothing v0.4b / v0.4c / v0.7a froze or
v0.7b … v2.4 produced.

## 3. Preregistration-plan objective

```text
CORE QUESTION:
  What FINITE synthetic fixture obligations must be preregistered before any future flat opponent-field fixture
  implementation can be considered?

OBJECTIVE:
  Fix, in finite detail, the fixture-family obligations a future offline synthetic fixture audit must satisfy
  (A-F), the required controls, the required reporting obligations, and the design decisions that stay DEFERRED --
  WITHOUT adopting any descriptor / coordinate system / metric / equation / threshold and WITHOUT implementing any
  fixture or authorizing any code.
This is a bounding plan, not a fixture, an experiment, or an implementation.
```

## 4. Frozen prior state

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator; the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual; PSC < PSC_FLOOR feasibility; the closed F1-F5 fixture-route family set (NOT expanded);
  the single matching family; the v0.7b samples; spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a … v1.7 fixture-route records, preserved as FROZEN EVIDENCE; v2.0 … v2.3 as an UNVALIDATED conceptual
  pivot; no sample replacement / new seeds / generation of the FROZEN families.
- claim locks and verdict HOLD.
This plan freezes ALL of the above; the proposed flat-field fixtures are a SEPARATE candidate offline surface.
```

## 5. Finite synthetic fixture scope

```text
- FINITE and BOUNDED: the future preregistration must fix fixture-family obligations A-F (§6), required controls
  (§7), and required reporting obligations (§8) and nothing more; it may specify REQUIRED FUTURE OBLIGATIONS but
  must NOT design the descriptor, choose coordinates, define equations, create metrics / thresholds, implement a
  fixture, or authorize implementation.
- CONCEPTUAL + OFFLINE ONLY: obligations are stated as conceptual requirements over OFFLINE SYNTHETIC content; no
  coordinate system, resolution, patch / relation / field equation, or metric is fixed; no screen analysis /
  capture, camera / live / sensor / streaming, or real clips.
- CONTROL-GATED: controls (§7) are REQUIRED before any later implementation; a fixture family without its controls
  is out of scope.
- NON-DRIFTING: the plan's job is to keep a later study from smuggling in a descriptor / coordinate system / metric
  / screen path; the deferral set (§9) is the guardrail.
- The plan opens NO implementation; §10 lists what a later, separately-gated study MAY inspect conceptually.
```

## 6. Required fixture families

The future preregistration MUST state all of A-F. Each is a concrete **fixture-family obligation**; none is a
descriptor, a coordinate system, a metric, an equation, a threshold, or a decision.

```text
A. Uniform opponent patches
   The prereg MUST require that isolated BY / RG local regions be represented CONCEPTUALLY, to inspect PATCH
   EXPLICITNESS only. NO descriptor; NO coordinates; NO metric.
B. Adjacent opponent patches
   The prereg MUST require neighbouring local regions, to inspect ADJACENCY / NEIGHBORHOOD conceptually. NO
   adjacency equation; NO distance metric.
C. Gradient fields
   The prereg MUST require smooth BY / RG transition fields, to inspect GRADIENT / CONTINUITY conceptually. NO
   gradient equation; NO threshold.
D. Edge / discontinuity fields
   The prereg MUST require sharp opponent boundaries, to inspect EDGE / DISCONTINUITY conceptually. NO edge
   detector; NO pass/fail rule.
E. Region-field separation fixtures
   The prereg MUST require a local patch pattern versus global field organisation, to inspect the LOCAL-vs-FIELD
   distinction conceptually. NO field descriptor.
F. Null / control fields
   The prereg MUST require neutral or matched non-opponent controls, to PREVENT trivial reporting optimism. NO
   control metric; NO threshold.
```

Each obligation is a **required future preregistration field**. Adopting any as a descriptor, coordinate system,
metric, or implementation is explicitly **out of scope here** and would need a separate, separately-gated
decision. These families are NOT an expansion of the frozen F1-F5 fixture-route family set (which stays closed).

## 7. Required controls

```text
The preregistration MUST require, before any later implementation:
- NULL control: a uniform neutral field with NO opponent structure. A concept must be reportable ABOVE the null.
- MATCHED non-opponent control: content matched in low-level respects but lacking the opponent STRUCTURE, so a
  report cannot be explained by a trivial confound.
- PER-CONCEPT control: each of A-E paired with a minimal variant lacking ITS concept (e.g. adjacency vs non-adjacent).
- SYMMETRY / balance: BY and RG opponent axes both represented, so neither is privileged by construction.
Controls are CONCEPTUAL requirements; the prereg fixes NO control metric, threshold, or pass/fail rule -- only that
controls MUST exist and what they must guard against. Controls are REQUIRED before any implementation is considered.
```

## 8. Required reporting obligations

```text
The future preregistration MUST require that any later fixture study:
- keeps each fixture family CONCEPTUAL / PREREGISTERED only (until a separate implementation gate);
- attaches an EXPLICIT NON-CLAIM boundary to each fixture family (what the family does NOT establish);
- REQUIRES the controls (§7) before any later implementation;
- distinguishes "fixture GENERATED / REPORTED" from "field VALIDATED" in its output vocabulary;
- defines protocol_ok to mean ONLY that the required fixture reports and guards are present (NOT validation);
- keeps flat_field_validated = False UNLESS a later, SEPARATELY preregistered validation protocol exists;
- keeps ALL claim locks False and verdict HOLD under every outcome.
These are REPORTING OBLIGATIONS on a future study, not equations; none is a metric, a threshold, or a decision.
```

## 9. Deferred design decisions

The following are **explicitly deferred** to a separate, later, gated decision and are **NOT decided, adopted,
invented, or authorized by this plan**:

```text
- descriptor design; coordinate system; field representation.
- equations; metrics; thresholds; pass/fail validity rules.
- implementation files; fixture counts; synthetic data format.
- any TOL / floor / CHANCE_BAND change; any change to the frozen descriptor; any expansion of the frozen F1-F5 set.
- any spectral reopening as a closure group; any classifier (form B) / neural encoder (form C).
- any flat-geometry / screen-analysis IMPLEMENTATION; any camera / live / sensor / screen-capture / streaming; any real clips.
- any runtime / memory / integration; any torment_service touch.
- any temporal / motion content (deferred; fixtures are spatial-first).
A future decision to adopt any of the above would be a SEPARATE preregistered gate, not an entailment of this plan.
```

## 10. What a later implementation may inspect

If — and only if — a later, separately-gated decision (after v2.5) authorizes an offline-only fixture study, it
**may inspect CONCEPTUALLY** (offline synthetic, adopting nothing here):

```text
- whether isolated BY / RG local regions are conceptually present (family A), WITHOUT a descriptor / coordinate / metric;
- whether neighbouring regions are conceptually adjacent (family B), WITHOUT an adjacency equation / distance metric;
- whether a smooth transition is conceptually a gradient / continuous (family C), WITHOUT a gradient equation / threshold;
- whether a sharp boundary is conceptually an edge / discontinuity (family D), WITHOUT an edge detector / pass-fail;
- whether a local patch pattern is conceptually distinct from field-level organisation (family E), WITHOUT a field descriptor;
- whether each concept is reportable ABOVE the null / matched controls (family F + §7);
- a "fixture generated/reported" vs "field validated" distinction, a non-authorization guard, and a claim-lock / verdict summary.
All inspection is CONCEPTUAL over offline synthetic content; it adopts no descriptor / coordinate system / metric /
equation / threshold and decides nothing.
```

## 11. What a later implementation may not claim

Even a fully obligation-conformant later study **may not claim** any of:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not live / screen / camera use
not closure                    (the BY gap is visible, not closed, in the fixture route)
not that flat opponent-field is validated / better (fixtures GENERATED != field VALIDATED; flat_field_validated stays False)
```

Fixing the preregistration structure is a docs-layer step over an unvalidated abstraction; it says nothing about
real clips or screens and adopts no descriptor or metric. The proof route remains **HELD / HOLD**. The claim locks
and `verdict = HOLD` remain in force.

## 12. Review checklist

A future flat opponent-field fixture preregistration (and any later study) is **consistent with this plan** iff a
reviewer can check all of:

```text
[ ] docs only at THIS stage; any study only after a separate v2.5 authorization review.
[ ] fixture-family obligations A-F all stated; nothing beyond them; frozen F1-F5 set NOT expanded.
[ ] A: isolated BY/RG regions conceptual, no descriptor / coordinates / metric.
[ ] B: neighbouring regions conceptual, no adjacency equation / distance metric.
[ ] C: smooth transition conceptual, no gradient equation / threshold.
[ ] D: sharp boundary conceptual, no edge detector / pass-fail.
[ ] E: local-vs-field distinction conceptual, no field descriptor.
[ ] F: null + matched non-opponent + per-concept + symmetry controls REQUIRED; no control metric / threshold.
[ ] reporting obligations (§8): conceptual-only, explicit non-claim per family, controls required, "generated" vs
    "validated" distinguished, protocol_ok = presence-only, flat_field_validated False (absent separate validation prereg).
[ ] deferred set (§9) untouched; v1.x frozen evidence; v2.x unvalidated; claim locks False; verdict HOLD; no §0; no tags.
```

## 13. Candidate next branches

Docs-first candidates only; **none opened or authorized here**:

```text
A. v2.5 SYNTHETIC FIXTURE IMPLEMENTATION AUTHORIZATION review (docs-only)
   Decide whether a reporting-only synthetic fixture harness may be implemented, and define its exact boundary. (Recommended next.)
B. v2.4b FIXTURE-RISK review (docs-only)
   Inspect whether the proposed fixture families accidentally smuggle in descriptors, coordinates, or metrics.
C. Pause for fresh-chat handoff
   Consolidate the full v1.x BY closure arc and the v2.x flat opponent-field pivot before proceeding.
```

## 14. Recommended next step

**Recommend Branch A (v2.5 synthetic fixture implementation authorization review, docs-only) next, if Codex
accepts THIS plan as-is.** v2.4a fixes the finite fixture obligations, controls, and reporting obligations; the
clean next move is an authorization review that decides whether — and under exactly what boundary — a reporting-
only synthetic fixture harness may be implemented, WITHOUT adopting a descriptor / coordinate system / metric /
equation / threshold and WITHOUT authorizing validation. **Do not implement fixtures, do not choose coordinates, do
not define equations or metrics, do not authorize validation, and claim no flat opponent-field success and no
Brainvision-sees.** Branch B (fixture-risk review) is a sensible sibling if drift is a concern; Branch C (pause for
fresh-chat handoff) is a legitimate operator call to consolidate the arc.

```text
1. Codex review THIS preregistration plan (docs-only; over committed edge 8dfd48c).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first v2.5 synthetic fixture
   implementation authorization review (conceptual; no fixture implemented; no descriptor / coordinate system /
   metric / equation / threshold adopted; no flat-geometry / screen-analysis / camera / live / real-clip / runtime /
   memory implementation authorized there). Branch B (v2.4b fixture-risk review) or Branch C (pause) remain open.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 15. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_PREREG_PLAN_v2.4a.md
(new, docs-only, untracked; over committed edge 8dfd48c, turning the accepted v2.4 minimal synthetic fixture
proposal into a FINITE preregistration plan, adopting none, implementing no fixture, authorizing no code).

Verify that this plan:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen-capture/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
  and opens NO flat-geometry and NO screen-analysis implementation; implements NO fixture;
- specifies REQUIRED PREREGISTRATION OBLIGATIONS ONLY and ADOPTS NONE -- it designs no descriptor, chooses no
  coordinates, defines no equations, creates no metrics / thresholds / pass-fail rules; redefines no TOL; does NOT
  expand the frozen F1-F5 family set; reopens no spectral group;
- states the core question (what finite synthetic fixture obligations must be preregistered before any flat
  opponent-field fixture implementation) and a finite, conceptual, offline-only, control-gated, non-drifting scope (§5);
- fixes fixture-family obligations A-F (uniform patches / adjacent patches / gradient fields / edge-discontinuity /
  region-field separation / null-control) each with its NO-descriptor / NO-coordinate / NO-metric / NO-equation /
  NO-threshold / NO-pass-fail constraint; requires controls (§7: null, matched non-opponent, per-concept, symmetry);
  and sets reporting obligations (§8: conceptual-only, explicit non-claim per family, controls required, "generated"
  vs "validated" distinction, protocol_ok = presence-only, flat_field_validated False absent a separate validation
  prereg, claim locks False, verdict HOLD);
- defers (§9) descriptor / coordinate system / field representation / equations / metrics / thresholds / pass-fail /
  implementation files / fixture counts / synthetic data format / any screen-real-clip-live-runtime-memory path;
- frames §10 / §11 correctly (a later study may only inspect CONCEPTUALLY, adopting nothing, and may claim no vision /
  descriptor validity / temporal order / closure / flat-field-validation / memory / runtime / integration / screen /
  live use; fixtures GENERATED != field VALIDATED), keeps v1.x FROZEN EVIDENCE and v2.x UNVALIDATED, provides a review
  checklist (§12), and recommends Branch A (v2.5 authorization review, docs-only) with B (fixture-risk review) / C
  (pause) as siblings;
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

*End — TORMENT Brainvision Flat Opponent-Field Synthetic Fixture Preregistration Plan v2.4a. Docs-only plan,
non-authorizing. Opens no implementation lane; implements no fixture; opens no classifier / neural / screen /
flat-geometry work; changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no control; redesigns
no descriptor; invents no threshold; redefines no TOL; adopts no descriptor / coordinate system / metric / equation;
does not expand the frozen F1-F5 family set; fixes the finite flat opponent-field synthetic fixture obligations
(families A-F + required controls + reporting obligations) only, adopting none; preserves v1.x as frozen evidence and
v2.x as an unvalidated conceptual pivot; keeps fixtures GENERATED distinct from field VALIDATED with
flat_field_validated False; makes no vision / "Brainvision sees" / descriptor-validity / temporal-order / memory /
runtime / integration claim; no `§0` pointer added; no tags.*
