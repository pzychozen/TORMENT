# TORMENT Brainvision Flat Opponent-Field Audit Design v2.2

## 1. Status / non-claims

**DOCS-ONLY design. Non-authorizing, non-implementing. Opens no code, no tests, no runtime, no integration
lane.** It designs — for future, separately-gated consideration only — the *structure* of a future finite
offline-only flat opponent-field audit: what such an audit would have to report (panels A-F), the required output
fields, the non-authorizing guards, and the breach conditions, all built on the accepted v2.1a preregistration
plan. It **designs a reporting structure only — it adopts no descriptor, no coordinate system, no metric, no
equation, no threshold, no pass/fail rule**, and implements nothing. It **authorizes no code and no tests**,
**redefines no `TOL`**, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no
control, redesigns no descriptor, reopens no spectral group, expands no generator family, and opens **no
classifier (form B) and no neural encoder (form C)**. It opens **no flat-geometry implementation and no
screen-analysis implementation**. Everything stays offline under `research/brainvision/` + `tests/research/`,
HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. A design alone moves nothing: **no claim
lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v2.1a preregistration plan

```text
v2.0a (01d5d9b)  flat opponent-field CONCEPT PLAN: bounded the abstraction's meaning / components / non-goals.
v2.1  (56b344c)  flat opponent-field PREREGISTRATION proposal: obligations A-F a future prereg must contain.
v2.1a (8625e90)  flat opponent-field PREREGISTRATION plan: the FINITE prereg structure (obligations A-F) + deferrals.
v2.2  (this doc) flat opponent-field finite AUDIT DESIGN: what a future finite audit must REPORT (panels A-F built
                 on obligations A-F), its output fields, guards, and breach conditions; adopting none; authorizing no code.
```

v2.1a fixed the finite preregistration obligations; v2.2 designs the audit that would report against them — its
panels, output fields, guards, and breach conditions — still without adopting a descriptor / coordinate system /
metric / equation / threshold and without authorizing any implementation. It proves nothing, validates nothing,
adopts nothing, and changes nothing v0.4b / v0.4c / v0.7a froze or v0.7b … v2.1a produced.

## 3. Audit-design objective

```text
CORE QUESTION:
  What would a future finite flat opponent-field audit need to REPORT before any implementation or descriptor
  design can be considered?

OBJECTIVE:
  Design the finite reporting STRUCTURE of a future offline-only flat opponent-field audit -- panels A-F mapped to
  the v2.1a obligations, the required output fields, the non-authorizing guards, and the breach conditions -- so a
  later, separately-gated study has a fixed, non-drifting structure to conform to. It designs the structure only;
  it adopts NO descriptor / coordinate system / metric / equation / threshold and authorizes NO code.
```

## 4. Frozen prior state

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator; the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual; PSC < PSC_FLOOR feasibility; the closed F1-F5 family set; the single matching family;
  the v0.7b samples; spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a … v1.7 records and artifacts, preserved as FROZEN EVIDENCE (not failed / retracted); v2.0 … v2.1a as an
  UNVALIDATED conceptual pivot; no sample replacement / new seeds / generation.
- claim locks and verdict HOLD.
This design freezes ALL of the above; a flat opponent-field audit is a SEPARATE offline research surface.
```

## 5. Finite audit scope

```text
- FINITE and BOUNDED: the future audit must report panels A-F (§6) mapped to the v2.1a obligations and nothing
  more; it may specify REQUIRED FUTURE PANELS AND FIELDS but must NOT design the descriptor, choose coordinates,
  define equations, create thresholds, or authorize implementation.
- CONCEPTUAL + OFFLINE ONLY: panels report CONCEPTUAL obligation-conformance over OFFLINE SYNTHETIC content; no
  coordinate system, resolution, patch / relation equation, or metric is fixed; no screen analysis / capture,
  camera / live / sensor / streaming, or real clips.
- REPORTING-ONLY: the audit would REPORT obligation-conformance and DECIDE nothing; any outcome vocabulary is a
  reporting label, never a Brainvision pass, a closure, a descriptor-validity claim, or a claim / verdict movement.
- NON-DRIFTING: the design's job is to keep a later study from smuggling in a descriptor / coordinate system /
  metric / screen path; the deferral set (§9) and guards (§8) are the guardrails.
- The design opens NO implementation; §10 lists what a later, separately-gated study MAY inspect conceptually.
```

## 6. Proposed audit panels

The future audit MUST report panels A-F, each mapped to a v2.1a obligation. Each panel REPORTS
obligation-conformance conceptually; none adopts a descriptor, a coordinate system, a metric, an equation, a
threshold, or a decision.

```text
A. Patch-definition panel (obligation A)
   Reports the CONCEPTUAL local opponent-patch requirements (what a patch must represent: position-indexed local
   opponent content). NO coordinate system; NO resolution; NO descriptor.
B. Opponent-channel panel (obligation B)
   Reports the BY / RG explicitness requirements (the opponent relation kept explicit and conceptual). NO metric;
   NO descriptor.
C. Spatial-relation panel (obligation C)
   Reports the named spatial-relation obligations: ADJACENCY / NEIGHBORHOOD / GRADIENT / EDGE /
   CONTINUITY-DISCONTINUITY. NO equations.
D. Region-field panel (obligation D)
   Reports the distinction between LOCAL patch effects and FIELD-LEVEL organisation. NO pass/fail rule.
E. Temporal-deferral panel (obligation E)
   Reports that motion / time is DEFERRED and NOT a first principle (the first pass stays spatial).
F. Non-authorizing guard panel (obligation F)
   Reports that all claim locks remain False and that the audit authorizes NO vision, descriptor-validity,
   temporal-order, runtime, memory, integration, screen, live, or real-clip claim.
```

Each panel is a REQUIRED FUTURE PANEL. Turning any panel into a descriptor, coordinate system, metric, or
implementation is explicitly **out of scope here** and would need a separate, separately-gated decision.

## 7. Required output fields

The future audit's result object MUST expose (field names indicative; conceptual, adopting nothing):

```text
- panels: A_patch_definition, B_opponent_channel, C_spatial_relation, D_region_field, E_temporal_deferral,
  F_non_authorizing_guard (each reporting obligation-conformance conceptually).
- obligation_conformance: a mapping obligation A-F -> conformant (bool), with no descriptor / metric attached.
- protocol_ok (bool; present required panels + guards only, NOT validation); breaches (list);
  outcome_label (a reporting label, e.g. flat_field_prereg_structure_reported / invalid_protocol_breach).
- freeze / non-adoption flags, all as specified: descriptor_adopted = False; coordinate_system_adopted = False;
  metric_adopted = False; equation_adopted = False; threshold_introduced = False; pass_fail_rule_introduced = False;
  tol_redefined = False; generator_family_expansion_authorized = False; spectral_closure_reopened = False;
  flat_geometry_authorized = False; screen_analysis_authorized = False; runtime_authorized = False;
  memory_authorized = False; real_clip_authorized = False; vision_claim_allowed = False;
  reporting_only = True; conceptual_only = True; offline_only = True.
- v1x_status = "frozen_evidence"; v2x_status = "unvalidated_conceptual_pivot".
- claim locks (all False) + frozen_brainvision_verdict = HOLD.
These are REQUIRED FIELDS, not equations; no field is a descriptor, a coordinate, a metric, or a threshold.
```

## 8. Required non-authorizing guards

```text
The future audit MUST carry an explicit non-authorization guard (panel F) whose flags are all present and False:
  authorizes_vision = False          authorizes_descriptor_validity = False   authorizes_temporal_order = False
  authorizes_runtime = False         authorizes_memory = False                authorizes_integration = False
  authorizes_screen = False          authorizes_live = False                  authorizes_real_clip = False
ANY guard flag set True (or absent) MUST make protocol_ok False (invalid_protocol_breach). The guard is a STANDING
property: no reporting result, under any outcome label, moves a claim lock or the verdict (HOLD under every
outcome). All claim locks remain False.
```

## 9. Deferred design decisions

The following are **explicitly deferred** to a separate, later, gated decision and are **NOT decided, adopted,
invented, or authorized by this design**:

```text
- The flat-field DESCRIPTOR; any COORDINATE SYSTEM / resolution / patch or relation EQUATION.
- Any METRIC / scoring function / threshold / ratio / cutoff / pass-fail validity rule.
- Any TOL / floor / CHANCE_BAND change; any §7 / §8 / control / evaluator change.
- Any generator-family expansion; any spectral reopening as a closure group; any change to the frozen descriptor.
- Any classifier (form B) / neural encoder (form C).
- Any flat-geometry / screen-analysis IMPLEMENTATION; any camera / live / sensor / screen-capture / streaming; any real clips.
- Any runtime / memory / integration; any torment_service touch.
- Any temporal layer as a first principle (deferred per obligation / panel E).
A future decision to adopt any of the above would be a SEPARATE preregistered gate, not an entailment of this design.
```

## 10. What a later implementation may inspect

If — and only if — a later, separately-gated decision (after v2.2a) authorizes an offline-only flat opponent-field
study, it **may inspect CONCEPTUALLY** (offline synthetic, adopting nothing here):

```text
- the conceptual local opponent-patch requirements (panel A), WITHOUT a coordinate system / descriptor;
- the BY / RG explicitness requirements (panel B), WITHOUT a metric;
- the named spatial-relation obligations -- adjacency / neighborhood / gradient / edge / continuity (panel C),
  WITHOUT equations;
- the local-patch vs field-level distinction (panel D), WITHOUT a pass/fail;
- the temporal-deferral record (panel E);
- the non-authorization guard + claim-lock / verdict summary (panel F).
All inspection is CONCEPTUAL over offline synthetic content; it adopts no descriptor / coordinate system / metric /
equation / threshold and decides nothing.
```

## 11. What a later implementation may not claim

Even a fully panel-conformant later study **may not claim** any of:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not live / screen / camera use
not closure                    (the BY gap is visible, not closed, in EITHER abstraction)
not that flat opponent-field is better (still a candidate to bound and explore, not validated)
```

Designing the audit structure is a docs-layer step over an unvalidated abstraction; it says nothing about real
clips or screens and adopts no descriptor or metric. The proof route remains **HELD / HOLD**. The claim locks and
`verdict = HOLD` remain in force.

## 12. Failure / breach conditions

```text
A future audit built to this design MUST return invalid_protocol_breach (protocol_ok False) on ANY of:
  - a missing or incomplete panel A-F;
  - a non-authorization guard (panel F) that is absent or carries ANY authorization flag True;
  - any adopted descriptor / coordinate system / metric / equation / threshold / pass-fail rule / TOL change;
  - any generator-family expansion, spectral reopening, or change to the frozen descriptor;
  - any flat-geometry / screen-analysis / camera / live / real-clip / runtime / memory path;
  - any treatment of v1.x as retracted rather than frozen evidence, or of v2.x as validated.
A breach can NEVER become a validation, a descriptor, a pass, a closure, or a claim / verdict movement.
```

## 13. Review checklist

A future flat opponent-field audit is **consistent with this design** iff a reviewer can check all of:

```text
[ ] docs only at THIS stage; any study only after a separate v2.2a authorization review.
[ ] panels A-F all present, each mapped to a v2.1a obligation; nothing beyond them.
[ ] A: conceptual patch requirements, no coordinate system / resolution / descriptor.
[ ] B: BY / RG explicitness, no metric / descriptor.
[ ] C: adjacency / neighborhood / gradient / edge / continuity reported, no equations.
[ ] D: local-patch vs field-level distinction, no pass/fail rule.
[ ] E: temporal layer reported as deferred, not first principle.
[ ] F: guard flags all present and False; ANY True -> protocol_ok False; all claim locks False.
[ ] required output fields (§7) present; all non-adoption flags False/as specified; reporting/conceptual/offline only.
[ ] deferred set (§9) untouched; v1.x = frozen evidence; v2.x = unvalidated; verdict HOLD; no §0; no tags.
```

## 14. Candidate next branches

Docs-first / gate candidates only; **none opened or authorized here**:

```text
A. v2.2a IMPLEMENTATION AUTHORIZATION review (docs-only)
   Decide whether to authorize a future offline-only flat opponent-field reporting study of THIS design, and define
   its exact boundary. (Recommended next.)
B. RESUME the BY fixture-metric route (docs-first)
   Only if the flat-field direction stalls or the operator prefers: revisit the frozen fixture route. No lever is
   currently in view.
C. Operator / new-math NOTE (docs-only).
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 15. Recommended next step

**Recommend Branch A (v2.2a implementation authorization review, docs-only) next.** v2.2 designs the finite audit
reporting structure; the clean next move is an authorization review that decides whether — and under exactly what
boundary — a future offline-only flat opponent-field reporting study may be implemented, WITHOUT adopting a
descriptor / coordinate system / metric / equation / threshold and with the offline / no-screen / no-vision
boundary restated. **No implementation, screen analysis, descriptor, or coordinate system is authorized here.** B
(resume fixtures), C (operator new-math), and D (pause) remain legitimate operator calls.

```text
1. Codex review THIS audit design (docs-only; over committed edge 8625e90).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first v2.2a implementation
   authorization review (conceptual; no descriptor / coordinate system / metric / equation / threshold adopted; no
   flat-geometry / screen-analysis / camera / live / real-clip / runtime / memory implementation authorized there).
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 16. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_AUDIT_DESIGN_v2.2.md
(new, docs-only, untracked; over committed edge 8625e90, designing the finite offline-only flat opponent-field
audit reporting structure on the accepted v2.1a preregistration plan, adopting none, authorizing no code).

Verify that this design:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen-capture/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
  and opens NO flat-geometry and NO screen-analysis implementation;
- designs a REPORTING STRUCTURE ONLY and ADOPTS NONE -- it designs no descriptor, chooses no coordinates, defines no
  equations, creates no thresholds, adopts no metric / coordinate system / pass-fail rule; redefines no TOL; expands
  no family; reopens no spectral group;
- states the core question (what a future finite flat opponent-field audit must REPORT before any implementation /
  descriptor design) and a finite, conceptual, offline-only, reporting-only, non-drifting scope (§5);
- designs panels A-F mapped to the v2.1a obligations (patch definition without a coordinate system / descriptor;
  opponent-channel BY/RG explicit without a metric; spatial relations -- adjacency / neighborhood / gradient / edge /
  continuity -- without equations; local-patch vs field-level distinction without a pass/fail; temporal deferral;
  non-authorizing guard), with required output fields (§7) and non-authorizing guards (§8: flags present and False,
  ANY True -> protocol_ok False);
- defers (§9) every descriptor / coordinate system / metric / equation / threshold / TOL / pass-fail / family /
  spectral / classifier / neural / flat / screen / runtime / memory / real-clip decision to a separate later gate;
- frames §10 / §11 correctly (a later study may only inspect CONCEPTUALLY, adopting nothing, and may claim no vision /
  descriptor validity / temporal order / closure / flat-field-superiority / memory / runtime / integration / screen /
  live use), specifies breach conditions (§12), keeps v1.x as FROZEN EVIDENCE and v2.x UNVALIDATED, provides a review
  checklist (§13), and recommends Branch A (v2.2a authorization review, docs-only), opening no implementation;
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

*End — TORMENT Brainvision Flat Opponent-Field Audit Design v2.2. Docs-only finite audit design, non-authorizing.
Opens no implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no frozen formula,
gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no threshold; redefines
no TOL; adopts no descriptor / coordinate system / metric / equation; designs the finite flat opponent-field audit
reporting structure (panels A-F, output fields, guards, breach conditions) only, adopting none; preserves v1.x as
frozen evidence and v2.x as an unvalidated conceptual pivot; makes no vision / "Brainvision sees" /
descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*
