# TORMENT Brainvision BY/Chroma Entanglement Schema Synthesis & Closure Decision v2.32

## 1. Status / Scope

**DOCS-ONLY synthesis and CLOSURE DECISION.** This is a synthesis note only. It opens **no** code, **no** tests, **no**
reporting instance artifact, **no** runtime, and **no** integration lane. It sits over the accepted v2.31 edge
(`83e97ad research(brainvision): add by chroma entanglement reporting schema`) and changes none of the accepted files.

**This document is a STOPPING POINT, not a link in a chain.** Every slice from v2.22 to v2.31 ended by recommending the
next slice, and the operator approved each one. That is a legitimate way to work, and it produced a real result — but
it is also a ratchet, and a ratchet does not know how to stop. v2.32 exists to hand the decision back. It recommends a
direction; it does **not** open one, and it deliberately does not schedule a v2.33.

**Explicitly authorized: nothing.**

```text
NO §0 POINTER IS AUTHORIZED.
NO IMPLEMENTATION IS AUTHORIZED.
NO VALIDATION IS AUTHORIZED.
NO VISION CLAIM AND NO READINESS CLAIM IS AUTHORIZED.
ANY FUTURE CONTINUATION REQUIRES SEPARATE OPERATOR APPROVAL AND SEPARATE CODEX REVIEW.
```

No descriptors, coordinates, numeric geometry, metrics, scores, thresholds, formulas, pass/fail gates, validation,
closure, fixture data, arrays, images, real clips, screen / camera / live / sensor / streaming paths, runtime paths,
memory paths, classifier (form B) or neural (form C) work are introduced, opened, or brought nearer by this note.
Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

```text
flat_field_validated                        = False
role_validated                              = False
schema_validated                            = False
entanglement_resolved                       = False
by_residual_isolated                        = False
generic_chroma_proxy_ruled_out              = False
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
geometry_validity_claim_allowed             = False
screen_readiness_claim_allowed              = False
runtime_readiness_claim_allowed             = False
memory_readiness_claim_allowed              = False
integration_readiness_claim_allowed         = False
vision_claim_allowed                        = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. The Arc, v2.22 → v2.31

```text
v2.22  Framed the question and kept it NON-CLAIM and UNRESOLVED: "can future synthetic design distinguish BY-axis
       residual behavior from generic chroma proxy effects without adopting metrics or closure claims?" -- plus:
       "residual localization must not imply descriptor validity."
v2.24  Proposed SIX symbolic role families (A BY-dominant residual; B generic chroma proxy; C matched non-BY chroma;
       D BY/CHROMA ENTANGLED; E fixture-family artifact; F null / reporting-boundary).
v2.26  Implemented a STATIC SYMBOLIC ROLE-REPORTING ARTIFACT (35d3707). Roles GENERATED, not VALIDATED.
v2.27  Treated Role D as a CENTRAL WARNING and the exposed DECISION POINT (f0e8177).
v2.28  Fixed the ENTANGLEMENT-AWARE REPORTING BOUNDARY (7165cd1): "entangled / inseparable" is a FIRST-CLASS
       UNRESOLVED ENDPOINT; no rule for deciding which outcome applies -- that absence load-bearing.
v2.29  Proposed a STATIC SYMBOLIC SCHEMA SHAPE (0af727e), field names only; schema_validated = False.
v2.30  Reviewed the IMPLEMENTATION BOUNDARY (d47bc56): related_role_ids FORBIDDEN in the first implementation
       artifact (Option A); nine mandatory guard conditions.
v2.31  Implemented the STATIC SYMBOLIC REPORTING SCHEMA ARTIFACT (83e97ad): no inputs (zero-parameter builder), no
       mapping, no assignment, no decision path, no validation; six reporting stances; 115 tests green;
       schema_validated = False; verdict HOLD.
```

## 3. Conclusions

```text
C1. v2.31 SUCCEEDED at what it set out to do. It created a SAFE SYMBOLIC CONTAINER for future reporting stances: a
    deterministic, static, offline artifact with no input, no arrival rule, no assignment, no role-to-outcome
    relation, no metric surface, and a conservative canonical guard. Dropping related_role_ids cost nothing, which
    suggests the field was never load-bearing -- only tempting. The container is real, and it is sound.

C2. v2.31 DID NOT ANSWER THE v2.22 QUESTION. It did not isolate BY residuals. It did not rule out generic chroma proxy
    effects. It did not resolve entanglement. It did not validate descriptors. It did not validate geometry. It did
    not detect visual structure. It could not have: a container with no input cannot learn anything, and that was the
    point of building it that way. NO CLOSURE, NO VALIDATION, AND NO READINESS FOLLOWS FROM IT.

C3. ENTANGLED_INSEPARABLE REMAINS AN HONEST UNRESOLVED ENDPOINT. It must not be collapsed into failure, success,
    noise, an implementation defect, an else-branch, hidden BY evidence, a resolved confound, validation, or closure.
    It survived implementation with all its denials intact, and it stays exactly as it is.

C4. THE BY/CHROMA SCHEMA BRANCH IS COMPLETE AS A NON-AUTHORIZING SCAFFOLD LAYER -- unless the operator explicitly
    chooses a new next target inside it. The scaffold layer was: name the roles, bound the language, decide how
    entanglement gets reported, and write that down under a guard. All four are done. There is no fifth scaffold step
    that would add anything.
```

## 4. What The Arc Actually Bought — And What It Did Not

Stated plainly, because the distinction is easy to lose after ten slices:

```text
BOUGHT:  a vocabulary in which "we could not tell" is a first-class, structured, terminal thing to say;
         a boundary that refuses to manufacture a BY-vs-proxy separation out of reporting language;
         a guarded container that cannot silently acquire a metric, a mapping, or a decision rule;
         a claim-control discipline that has now survived two Codex MODIFYs and one self-caught wording collision.

NOT BOUGHT:  one single fact about colour.
             one step toward distinguishing BY-axis residual behavior from generic chroma proxy effects.
             any reason to think that distinction is possible, or impossible.

The arc improved WHAT THE PROJECT CAN HONESTLY SAY. It did not improve WHAT THE PROJECT KNOWS. Both of those are
worth having, and they are not the same thing, and the second one is the one the v2.22 question asked about.
```

## 5. The Self-Referential Risk

This is the finding that matters most, and it is about the programme rather than about colour:

```text
The last six slices were about the language used to describe a result that does not exist yet.

That was justified -- v2.27 showed the alternative (jumping to fixtures) would have manufactured a separation out of
the reporting vocabulary. Doing the language first was the right call, and it is now DONE.

But the same logic does not license a seventh slice. Each further scaffold layer would be about the previous scaffold
layer, and the distance to any falsifiable claim would grow, not shrink. A schema for reporting instances, then a
review of that schema, then a synthesis of that review -- each one green, each one guarded, each one boundary-clean,
and NONE of them able to be WRONG about anything. Work that cannot be wrong cannot be evidence.

THE TEST TO APPLY TO ANY PROPOSED NEXT SLICE: what could it FAIL at? If the honest answer is "nothing -- it would
either be boundary-clean or be fixed until it was", the slice is scaffolding, not research.
```

## 6. Recommended Branch State

```text
PAUSE / HELD as completed non-authorizing BY/chroma entanglement-aware reporting scaffold.

HELD in the ANALYSIS sense: held for boundary control and future reference -- NOT abandoned, NOT failed, NOT
deprecated. The artifacts stand. The v2.28 language boundary and the v2.31 container remain the governing reference
for any future BY/chroma reporting, whenever and if ever that happens. Nothing here is thrown away; the branch is
simply not the place where the next real question gets asked.
```

## 7. Allowed Future Continuations (all separately gated; none opened here)

```text
====================================================================================================================
OPTION A -- STATIC REPORTING INSTANCE BOUNDARY REVIEW  (docs-only)
  Would review whether future symbolic reporting INSTANCES may exist at all without accepting inputs, assigning
  outcomes, or mapping evidence.
  Honest assessment: this is the narrowest option, and also the one most exposed to the Section-5 risk. An "instance"
  that takes no input and is assigned to nothing is close to a tautology -- it is hard to say what such an instance
  would BE, other than a stance re-stated. If the operator wants A, the review should first answer: what does an
  instance carry that the schema does not already carry? If there is no answer, A is scaffolding.

====================================================================================================================
OPTION B -- RETURN TO BROADER SYNTHETIC FALSIFICATION DESIGN  (RECOMMENDED)
  Step back from BY/chroma schema work entirely. Look for a falsification direction that can eventually TEST
  STRUCTURE without forcing a BY-vs-generic-chroma separation -- i.e. a target where a result could come out WRONG.
  This is the only option that reintroduces the possibility of being wrong, which is the only thing that makes a slice
  research rather than scaffolding.
  It does NOT abandon the BY/chroma work: the v2.28 boundary and the v2.31 container are exactly what a new direction
  would report through, if it ever needed to report an entangled result.

====================================================================================================================
OPTION C -- REOPEN FIXTURE DESIGN AFTER A STRICTER NON-MAPPING INSTANCE BOUNDARY
  Only if the operator explicitly wants to move toward fixture scaffolds, and only after ANOTHER boundary review.
  Honest assessment: the v2.27 hazard has not gone away. A fixture bank still has to decide what its cases are FOR,
  and the moment cases are built "for BY-leaning" and "for generic-proxy", the separation is back in the setup. The
  v2.31 container does NOT solve this -- it only guarantees that if the result is entangled, that can be said. Being
  able to SAY "entangled" is not the same as being safe from MANUFACTURING "separated". C is possible, but it is the
  option most likely to produce a confident wrong answer.
====================================================================================================================
```

## 8. Recommendation

```text
RECOMMEND OPTION B -- return to broader synthetic falsification design -- unless the operator explicitly wants to
continue schema scaffolding.

REASON: the current BY/chroma path has produced useful boundary language and safe symbolic containers, but it still
cannot answer whether BY-axis residual behavior is distinguishable from generic chroma proxy effects. More schema
scaffolding risks becoming SELF-REFERENTIAL unless a new falsification target is chosen. The branch has run out of
things it can be wrong about, and a branch that cannot be wrong cannot make progress on an empirical question.

This recommendation is NOT self-executing. v2.32 opens no v2.33, drafts no plan for Option B, and schedules nothing.
If the operator chooses B, the next step is the operator's to name -- and it should begin with a source-first
orientation survey (formal docs, scratch, tests, code, branches), not with another docs slice.

If the operator instead wants A or C, both remain available, each requires separate operator approval AND separate
Codex review, and each should be held to the Section-5 test: WHAT COULD THIS SLICE FAIL AT?
```

## 9. Forbidden Drift Register

```text
- v2.31's protocol greenness becoming SCHEMA VALIDITY, correctness, distinguishability, or readiness (v2.14).
- the safe container becoming EVIDENCE ("we built the reporting layer, so we are close to a result").
- ENTANGLED_INSEPARABLE becoming failure, success, noise, defect, else-branch, hidden BY evidence, proxy-resolved,
  validation, or closure.
- "the scaffold is complete" becoming "the question is closed". The question is UNRESOLVED, not closed.
- PAUSE / HELD becoming ABANDONED, FAILED, or DEPRECATED.
- scaffolding momentum becoming an implicit authorization ("the last nine slices were approved, so the tenth is
  routine"). Each slice requires its own approval, and this one recommends stopping.
- a synthesis becoming an AUTHORIZATION; a recommendation becoming a licence; a direction becoming a schedule.
- residual localization becoming DESCRIPTOR VALIDITY; isolation becoming CLOSURE; falsification becoming VALIDATION.
```

## 10. Non-Claim Interpretation

```text
WHAT v2.32 MAY ESTABLISH (and only this):
  - a SYNTHESIS of what v2.22-v2.31 did and did not establish;
  - a BRANCH STATE: PAUSE / HELD as a completed non-authorizing scaffold layer;
  - three separately gated continuation options, with an honest assessment of each;
  - a RECOMMENDATION (Option B), which is a recommendation and nothing more.

WHAT IT DOES NOT ESTABLISH:
  not an implementation     not an artifact         not an instance      not fixtures / data
  not a descriptor          not a coordinate        not a metric         not a decision rule
  not validation            not closure             not readiness        not vision
  not that the residual IS distinguishable          not that it IS indistinguishable
  not that entanglement IS the answer               not authorization of anything

The v2.22 question REMAINS UNRESOLVED, and remains possibly unanswerable (v2.24 Role D). Ten slices of careful
boundary work have not moved it one step, and this document says so plainly rather than presenting the scaffold as
progress toward it.
```

## 11. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
role_validated                               = False
schema_validated                             = False
entanglement_resolved                        = False
by_residual_isolated                         = False
generic_chroma_proxy_ruled_out               = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

BRANCH STATE: PAUSE / HELD as completed non-authorizing BY/chroma entanglement-aware reporting scaffold
OUTCOME_LABEL: BRAINVISION_BY_CHROMA_ENTANGLEMENT_SCHEMA_SYNTHESIS_ONLY
```

v2.32 is a docs-only synthesis and closure decision. It states that v2.31 successfully created a safe symbolic
container for future reporting stances; that v2.31 did **not** answer the v2.22 question, isolate BY residuals, rule
out generic chroma proxy effects, resolve entanglement, validate descriptors, validate geometry, or detect visual
structure; that ENTANGLED_INSEPARABLE remains an honest unresolved endpoint which must not be collapsed into failure,
success, noise, hidden BY evidence, validation, or closure; and that the BY/chroma schema branch is complete as a
non-authorizing scaffold layer unless the operator explicitly chooses a new next target. It sets the branch state to
**PAUSE / HELD** (analysis sense — held for boundary control and future reference, not abandoned); lists three
separately gated continuations (A static reporting instance boundary review; B return to broader synthetic
falsification design; C reopen fixture design after a stricter non-mapping instance boundary); and recommends **B**,
because more schema scaffolding risks becoming self-referential unless a new falsification target is chosen. It
authorizes no §0 pointer, no implementation, no validation, and no vision or readiness claim; any continuation requires
separate operator approval and separate review. All claim locks and the frozen verdict **HOLD** are preserved and
unmoved.

## 12. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_CHROMA_ENTANGLEMENT_SCHEMA_SYNTHESIS_v2.32.md
(new, docs-only, untracked; over the accepted v2.31 edge
 "83e97ad research(brainvision): add by chroma entanglement reporting schema").

Verify that this synthesis:
- is docs-only and authorizes NOTHING: no §0 pointer, no implementation, no tests, no reporting instance artifact, no
  validation, no vision / readiness claim; no torment_service/; no fixture data; no arrays / images; no descriptors /
  coordinates / metrics / scores / thresholds / formulas / pass-fail gates; no screen / runtime / memory paths; no
  classifier / neural work; no real clips; adds no tags; and states explicitly that any future continuation requires
  separate operator approval and separate review;
- grounds itself in v2.22 (question non-claim and unresolved), v2.24 (six symbolic role families), v2.26 (roles
  generated, not validated), v2.27 (Role D as central warning / decision point), v2.28 (entangled / inseparable as a
  first-class unresolved endpoint), v2.29 (schema-shape proposal), v2.30 (related_role_ids forbidden in the first
  implementation artifact), and v2.31 (no inputs, no mapping, no assignment, no decision path, no validation);
- states the four required conclusions: (1) v2.31 successfully created a safe symbolic container for future reporting
  stances; (2) v2.31 did NOT answer the v2.22 question, did not isolate BY residuals, did not rule out generic chroma
  proxy effects, did not resolve entanglement, did not validate descriptors, did not validate geometry, and did not
  detect visual structure; (3) ENTANGLED_INSEPARABLE remains an honest unresolved endpoint and must not be collapsed
  into failure, success, noise, hidden BY evidence, validation, or closure; (4) the BY/chroma schema branch is
  complete as a non-authorizing scaffold layer unless the operator explicitly chooses a new next target;
- sets the branch state to PAUSE / HELD as a completed non-authorizing BY/chroma entanglement-aware reporting
  scaffold, and uses HELD in the ANALYSIS sense (held for boundary control and future reference, not abandoned);
- lists the three separately gated continuations (A static reporting instance boundary review; B return to broader
  synthetic falsification design; C reopen fixture design only after a stricter non-mapping instance boundary), opens
  none of them, and RECOMMENDS B unless the operator explicitly wants to continue schema scaffolding -- on the ground
  that the BY/chroma path has produced useful boundary language and safe symbolic containers but still cannot answer
  whether BY-axis residual behavior is distinguishable from generic chroma proxy effects, and that more schema
  scaffolding risks becoming self-referential;
- preserves the locks and verdict (Section 11): flat_field_validated = False; role_validated = False;
  schema_validated = False; entanglement_resolved = False; by_residual_isolated = False;
  generic_chroma_proxy_ruled_out = False; first_pass_structure_validity_claim_allowed = False;
  temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed = False;
  screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False;
  memory_readiness_claim_allowed = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False;
  verdict = HOLD; interprets HOLD/HELD as held for analysis, not abandoned.

Flag any implementation / artifact / instance / code / test; any authorization of a next slice; any automatic
continuation of the docs chain; any treatment of the scaffold as evidence or as progress toward the v2.22 question; any
treatment of "scaffold complete" as "question closed"; any collapse of ENTANGLED_INSEPARABLE into failure, success,
noise, evidence, validation, or closure; any claim that anything was isolated, ruled out, resolved, validated,
detected, or seen; any §0 pointer; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, `role_validated = False`, `schema_validated = False`, `entanglement_resolved = False`,
`by_residual_isolated = False`, `generic_chroma_proxy_ruled_out = False`, all claim locks False, and the frozen verdict
**HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY/Chroma Entanglement Schema Synthesis & Closure Decision v2.32. Docs-only synthesis and
closure decision over the accepted v2.31 edge. Opens no implementation lane, no tests, no reporting instance artifact,
and no fixture generation; opens no classifier / neural / screen / real-clip / runtime / memory work; adopts no
descriptor / coordinate system / numeric geometry / metric / equation / threshold / scoring / formula / pass-fail rule;
authorizes no §0 pointer, no implementation, no validation, and no vision or readiness claim; synthesizes v2.22 through
v2.31; concludes that v2.31 built a safe symbolic container and answered nothing about colour; keeps
ENTANGLED_INSEPARABLE an honest unresolved endpoint; declares the BY/chroma schema branch complete as a non-authorizing
scaffold layer and sets the branch state to PAUSE / HELD (analysis sense — held for boundary control and future
reference, not abandoned); names the self-referential risk of further scaffolding and the test to apply to any proposed
next slice (what could it fail at?); lists three separately gated continuations (A instance boundary review; B return
to broader synthetic falsification design; C fixture design after a stricter non-mapping instance boundary) and
recommends B; opens none of them and schedules no v2.33; requires separate operator approval and separate review for
any continuation; keeps prior BY / color / chroma work FROZEN EVIDENCE, the flat opponent-field symbolic branch PAUSED
HELD, and the v2.22 question UNRESOLVED and possibly unanswerable; is not self-authorizing; preserves all claim locks
and the frozen verdict HOLD; makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
temporal-order / readiness claim; outcome label BRAINVISION_BY_CHROMA_ENTANGLEMENT_SCHEMA_SYNTHESIS_ONLY; no `§0`
pointer added; no tags.*
