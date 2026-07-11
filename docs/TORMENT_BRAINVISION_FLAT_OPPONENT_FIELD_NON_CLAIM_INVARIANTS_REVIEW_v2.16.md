# TORMENT Brainvision Flat Opponent-Field Non-Claim Invariants Review v2.16

## 1. Status / Scope

**DOCS-ONLY non-claim invariants REVIEW.** This is a consolidation and review note only. It opens **no** code, **no**
tests, **no** runtime, and **no** integration lane; it authorizes **no** implementation, **no** test expansion, **no**
validation, **no** readiness claim, and **no** capability claim, and it is not corrective. It sits over the accepted
v2.15 edge (`234cd93`) and changes none of the accepted files.

**v2.16 reviews non-claim invariants only.** After the v2.10 stress synthesis, v2.11 vocabulary drift audit, v2.12
null/control boundary review, v2.13 mutation review, v2.14 protocol guard semantics review, and v2.15 family identity
audit, this note collects the core non-claim invariants governing the v2.9 symbolic representation artifact into one
reviewable place and hardens them. It reviews invariants; it changes no field, term, family, or behavior.

**v2.16 authorizes no implementation, expansion, validation, readiness, or capability claim.** It introduces and
authorizes **no** descriptor, coordinate system, numeric geometry, metric, null/control metric, equation, threshold,
control metric, pass/fail gate, validation, closure, screen analysis, real clip, camera / live / sensor / streaming
path, runtime path, memory path, prompt / context / action / render-body / autonomy contact, classifier (form B), or
neural encoder (form C), and it authorizes **no** family or vocabulary expansion. It makes **no** production vision
claim, **no** "Brainvision sees" claim, **no** temporal-order claim, and **no** descriptor-validity /
geometry-validity / screen-readiness / memory-readiness / runtime-readiness / integration-readiness claim. Everything
stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. **HOLD / HELD means held for analysis
and claim control — not abandoned.**

```text
flat_field_validated                        = False
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

## 2. Why Non-Claim Invariants Matter

The v2.10-v2.15 arc built six local boundaries — around vocabulary, null/control, mutation, protocol, and family
identity. Each is correct in its own lane, but a reader rarely encounters one lane at a time. The residual risk is
*aggregate*: even with every local boundary in place, the representation as a whole can be rhetorically or procedurally
misread as "progress toward validation / geometry / descriptors / screen / runtime / memory / classifier-neural /
vision." A guarded scaffold, described often enough, starts to sound like a result; a green checker, cited often
enough, starts to sound like proof; six families, listed often enough, start to sound like a visual ontology.

Non-claim invariants are the defense against that aggregate drift. They are the small set of **non-implications** that
must remain true for the artifact to stay a non-authorizing scaffold rather than a hidden claim, stated once and in one
place so no single lane's discipline has to carry the whole load. This review lists each invariant, the drift it
refuses, its safe-use rule, and the consequence if it is violated — so the entire non-claim posture is explicit and
reviewable before any future step.

## 3. Invariant Review

```text
For each invariant: the invariant statement, the drift risk it refuses, the safe-use rule, and the consequence if it
is violated. Sources in the review family are noted where relevant (v2.11 vocabulary, v2.12 null/control, v2.13
mutation, v2.14 protocol, v2.15 family).

--------------------------------------------------------------------------------------------------------------------
I1. REPRESENTATION NON-VALIDATION
   invariant : symbolic representation EXISTENCE does NOT imply validation.
   drift     : "we can represent A-F" read as "the flat opponent-field is validated / works".
   safe-use  : representation names structure; it validates nothing (flat_field_validated stays False).
   violated  : the artifact becomes a hidden validation claim; HOLD collapses. INADMISSIBLE.

I2. FIXTURE NON-EVIDENCE
   invariant : fixture family EXISTENCE does NOT imply evidence of visual structure.
   drift     : a named family read as evidence that the visual structure is present / real.
   safe-use  : a family is a named symbolic scaffold; it evidences nothing about vision.
   violated  : naming becomes measuring; a vision/structure claim leaks in. INADMISSIBLE.

I3. A-F NON-COMPLETENESS
   invariant : EXACT A-F coverage does NOT imply visual completeness. (v2.15)
   drift     : "we cover the six families" read as "we cover all the visual cases".
   safe-use  : coverage of six NAMES is not coverage of any visual space.
   violated  : a completeness/validation-coverage claim leaks in. INADMISSIBLE.

I4. VOCABULARY NON-DESCRIPTOR
   invariant : canonical symbolic VOCABULARY does NOT imply descriptor validity. (v2.11)
   drift     : component labels read as feature/descriptor definitions.
   safe-use  : the vocabulary is a naming set; descriptor_validity_claim_allowed stays False.
   violated  : a descriptor / form-B claim leaks in. INADMISSIBLE.

I5. RELATION NON-GEOMETRY
   invariant : RELATION labels do NOT imply coordinate geometry, measured adjacency, segmentation, or topology. (v2.11)
   drift     : adjacent_to / separates / transitions_to / contains read as positions / distances / splits / topology.
   safe-use  : relations are NAMES; no coordinate, distance, split, or topology exists.
   violated  : a coordinate/segmentation/topology claim leaks in. INADMISSIBLE.

I6. GRADIENT/BOUNDARY NON-MEASUREMENT
   invariant : gradient / boundary / discontinuity labels do NOT imply measured gradients, detected edges, or visual
               discontinuity evidence. (v2.11)
   drift     : these labels read as slopes / edge-maps / jump magnitudes / detected evidence.
   safe-use  : each is a NAME; nothing is measured, detected, located, or scored.
   violated  : a measured-geometry / edge-detection claim leaks in. INADMISSIBLE.

I7. NULL/CONTROL NON-VALIDATION
   invariant : null_control / has_null_control_role do NOT imply control metrics, baselines, negative controls,
               pass/fail gates, falsification success, or validation evidence. (v2.12)
   drift     : F read as the control that validates A-E / a scored baseline / a passed null.
   safe-use  : F is a symbolic role; it adjudicates, scores, and validates nothing (v2.12 N1-N6).
   violated  : A-E are silently treated as a positive result; validation leaks in. INADMISSIBLE.

I8. PROTOCOL NON-PROOF
   invariant : protocol_ok = True and breaches = [] do NOT imply proof, correctness, completeness, validation, or
               capability. (v2.14)
   drift     : a green checker read as a passed test of the world; empty breaches read as "no risk".
   safe-use  : protocol_ok = boundary compliance among KNOWN checks; it proves what is NOT carried, not that it works.
   violated  : the checker becomes a hidden validation system. INADMISSIBLE.

I9. HOLD NON-FAILURE / NON-PASS
   invariant : verdict = HOLD means held for analysis and claim control -- NOT abandoned, failed permanently, passed,
               validated, or ready. (v2.14)
   drift     : HOLD read as a pass, a fail, a validation, or abandonment.
   safe-use  : HOLD is a claim-control state; it stays HOLD until separately re-decided.
   violated  : a pass/fail/validation/abandonment claim leaks in. INADMISSIBLE.

I10. OUTCOME-LABEL NON-CAPABILITY
   invariant : outcome_label is BOUNDARY classification only -- NOT a performance / capability / readiness
               classification. (v2.14)
   drift     : the label read as a capability grade or a readiness result.
   safe-use  : the label names WHERE the artifact sits on the boundary, not HOW WELL it does anything.
   violated  : a capability/readiness claim leaks in. INADMISSIBLE.

I11. OFFLINE NON-RUNTIME
   invariant : offline research artifact EXISTENCE does NOT imply runtime readiness or an integration path.
   drift     : "the artifact exists" read as "it is ready to run / integrate".
   safe-use  : the artifact is offline research-only; runtime/integration guards stay False; no path exists.
   violated  : a runtime/integration-readiness claim leaks in; quarantine breached. INADMISSIBLE.

I12. SYMBOLIC NON-SCREEN
   invariant : symbolic fixture objects are NOT screen objects, pixel objects, image segments, detected regions, or
               visual classes. (v2.13, v2.15)
   drift     : a symbolic object read as captured screen content / a segment / a detected class.
   safe-use  : the objects hold labels, not pixels or captured content; no screen/capture path exists.
   violated  : a screen-object / segmentation / visual-class claim leaks in. INADMISSIBLE.

I13. STATIC NON-TEMPORAL
   invariant : static symbolic representation does NOT imply temporal-order evidence.
   drift     : the static object read as evidence about sequence / arrow-of-time / dynamics.
   safe-use  : the representation is static and symbolic; temporal_claim_allowed stays False; nothing is over time.
   violated  : a temporal-order claim leaks in. INADMISSIBLE.

I14. ANTI-CLAIM FLAGS NON-EVIDENCE
   invariant : false locks, adoption flags, and authorization guards are ANTI-CLAIM constraints -- NOT evidence that
               absence was empirically tested. (v2.14)
   drift     : a False flag read as "we tested and it isn't there" rather than "we do not claim it".
   safe-use  : a False flag withholds a claim / an adoption / an authorization; it tests and evidences nothing.
   violated  : anti-claim discipline is inverted into false evidence. INADMISSIBLE.

I15. NO VISION IMPLICATION
   invariant : NO part of v2.6-v2.16 supports "Brainvision sees" or production vision.
   drift     : the accumulated arc read as incremental progress toward vision.
   safe-use  : every step is reporting / representation / boundary review only; vision_claim_allowed stays False.
   violated  : the whole quarantine is defeated; a vision claim leaks in. INADMISSIBLE.
--------------------------------------------------------------------------------------------------------------------
```

## 4. Cross-Invariant Pressure Points

Invariants can each hold locally yet be defeated in combination. The dangerous combinations, each to be refused:

```text
- A-F coverage + protocol_ok        -> reads as VALIDATION COVERAGE ("all six families pass"). Refuse via I3 + I8:
                                       coverage of six names + a compliant checker is not a validated test matrix.
- vocabulary + relations            -> reads as HIDDEN DESCRIPTOR GEOMETRY (labels + relations as features + positions).
                                       Refuse via I4 + I5: naming vocabulary and named relations carry no feature or
                                       coordinate.
- null/control + breaches=[]        -> reads as PASS/FAIL CONTROL SUCCESS ("the null control passed, no breaches").
                                       Refuse via I7 + I8: F adjudicates nothing and an empty breach list is not a pass.
- HOLD + outcome_label              -> reads as a CAPABILITY STATUS ("held at capability level X"). Refuse via I9 + I10:
                                       HOLD is claim control and the label is a boundary classification, not a grade.
- offline artifact + static rep     -> reads as SCREEN / RUNTIME READINESS ("a working static component ready to run").
                                       Refuse via I11 + I12 + I13: offline + static + symbolic implies no runtime,
                                       screen, or dynamics.
- symbolic representation + family identity -> reads as a VISUAL ONTOLOGY (six extensible visual classes). Refuse via
                                       I2 + I3 + I12 + I15 (and v2.15): the six are fixed symbolic scaffold names, not a
                                       visual class system.
```

## 5. Non-Claim Summary

```text
ESTABLISHED (by v2.6-v2.16), and only this:
  - a STATIC SYMBOLIC SCAFFOLD only;
  - FIXED A-F family coverage only (exactly six, closed, canonical);
  - CANONICAL VOCABULARY only (fixed component / relation label sets + canonical per-family values);
  - BOUNDARY COMPLIANCE CHECKING only (a conservative, canonical check_protocol);
  - ANTI-CLAIM LOCKS only (claim locks / adoption flags / authorization guards, all False).

NOT ESTABLISHED (unproven):
  not validation                 not geometry truth             not descriptor validity
  not metric validity            not visual completeness        not screen readiness
  not real-clip readiness        not runtime readiness          not memory readiness
  not integration readiness      not classifier / neural readiness   not temporal-order evidence
  not production vision          not "Brainvision sees"
```

## 6. Expansion Recommendation

```text
Recommendation: REMAIN HELD.

Do NOT expand into descriptors, coordinates, metrics, validation, screen / real-clip / runtime / memory / neural /
classifier work, or vision. The artifact stays a static symbolic scaffold under conservative, canonical, anti-claim
guards, and the fifteen invariants above must remain true. Any future hardening pass -- or any step that would give any
field, family, term, or guard an evidentiary / measured / capability meaning -- must be SEPARATELY planned (docs-first),
reviewed by Codex, and operator-approved, naming the exact change, what it must never become, and how every claim lock
and the generated-vs-validated separation are preserved. Nothing is authorized here. Held for analysis and claim
control -- not abandoned.
```

## 7. Possible Next Slices

Docs-first candidates only; **none opened, none authorized, and none recommended for implementation here**. This review
recommends **no** direct descriptor, coordinate, metric, validation, screen, real-clip, runtime, memory, neural,
classifier, or vision work. Up to three possible docs-first directions the operator could choose from:

```text
A. v2.17 PROTOCOL WORDING HARDENING REVIEW (docs-only)
   Review, on paper, the exact wording of the protocol outputs and docstrings for any phrasing that could be read as
   validation / capability, and define wording invariants -- WITHOUT changing any field, value, or behavior. Adopts
   nothing; changes no code.

B. v2.17 REPRESENTATION EXPANSION READINESS HOLD REVIEW (docs-only)
   Review, on paper, whether the boundary-review family (v2.10-v2.16) is now SATURATED and the branch should stay HELD
   as-is, and what a FUTURE bounded expansion plan would minimally have to contain before it could even be considered.
   Adopts nothing; authorizes no expansion.

C. v2.17 SYMBOLIC ARTIFACT IMPLEMENTATION HARDENING PLAN (docs-only)
   Plan, on paper only, whether any additional check_protocol guard is warranted (e.g. a deny-list refinement) given
   the v2.13 mutation classes -- as a PROPOSAL requiring separate operator approval and Codex review before any code.
   Adopts nothing; writes no code; authorizes no implementation.
```

## 8. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False
geometry_validity_claim_allowed              = False
screen_readiness_claim_allowed               = False
runtime_readiness_claim_allowed              = False
memory_readiness_claim_allowed               = False
integration_readiness_claim_allowed          = False
vision_claim_allowed                         = False

OUTCOME_LABEL: FLAT_OPPONENT_FIELD_NON_CLAIM_INVARIANTS_REVIEW_ONLY
```

v2.16 is a docs-only non-claim invariants review. It consolidates the fifteen core non-claim invariants governing the
v2.9 symbolic representation artifact — recording for each the invariant statement, the drift risk, the safe-use rule,
and the consequence if violated — addresses the cross-invariant pressure points, summarizes what is established (a
static symbolic scaffold, fixed A-F coverage, canonical vocabulary, boundary-compliance checking, anti-claim locks) and
what is not (validation, geometry, descriptors, metrics, visual completeness, any readiness, temporal order, vision),
and recommends the branch REMAIN HELD. It adopts, expands, and relaxes nothing. All claim locks and the frozen verdict
**HOLD** are preserved and unmoved.

## 9. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_NON_CLAIM_INVARIANTS_REVIEW_v2.16.md
(new, docs-only, untracked; over the accepted v2.15 edge 234cd93).

Verify that this review:
- is docs-only and authorizes NO implementation, NO test expansion, NO family / vocabulary expansion, NO validation,
  NO readiness claim, and NO capability claim (no code / tests / schema, no torment_service/, no runtime, no memory, no
  camera / live / sensor / screen-capture / streaming, no real clips, no pixels / images); keeps form B (classifier)
  and form C (neural) CLOSED; opens no screen-analysis / numeric-geometry;
- frames the central question as WHICH invariants must remain true so the symbolic representation artifact stays a
  non-authorizing scaffold rather than a hidden validation / descriptor / geometry / readiness / vision claim;
- reviews all fifteen required invariants (I1 representation non-validation; I2 fixture non-evidence; I3 A-F
  non-completeness; I4 vocabulary non-descriptor; I5 relation non-geometry; I6 gradient/boundary non-measurement; I7
  null/control non-validation; I8 protocol non-proof; I9 HOLD non-failure/non-pass; I10 outcome-label non-capability;
  I11 offline non-runtime; I12 symbolic non-screen; I13 static non-temporal; I14 anti-claim-flags non-evidence; I15 no
  vision implication) with: invariant statement, drift risk, safe-use rule, and consequence if violated;
- addresses the cross-invariant pressure points (A-F coverage + protocol_ok -> validation coverage; vocabulary +
  relations -> hidden descriptor geometry; null/control + breaches=[] -> pass/fail control success; HOLD + outcome_label
  -> capability status; offline + static -> screen/runtime readiness; symbolic representation + family identity ->
  visual ontology);
- summarizes what IS established (static symbolic scaffold only; fixed A-F coverage only; canonical vocabulary only;
  boundary-compliance checking only; anti-claim locks only) and what is NOT established (validation; geometry truth;
  descriptor validity; metric validity; visual completeness; screen / real-clip / runtime / memory / integration
  readiness; classifier / neural readiness; temporal-order evidence; production vision; "Brainvision sees");
- recommends the branch REMAIN HELD; requires any future hardening pass to be separately planned + Codex-reviewed +
  operator-approved; lists up to three docs-first next slices (v2.17 protocol wording hardening review / representation
  expansion readiness HOLD review / symbolic artifact implementation hardening plan); recommends NO descriptor /
  coordinate / metric / validation / screen / real-clip / runtime / memory / neural / classifier / vision work;
- preserves the locks and verdict (Section 8): flat_field_validated = False; first_pass_structure_validity_claim_allowed
  = False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  FLAT_OPPONENT_FIELD_NON_CLAIM_INVARIANTS_REVIEW_ONLY; interprets HOLD/HELD as held for analysis, not abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any invariant weakened or dropped, any adopted descriptor / coordinate / numeric geometry / metric / equation /
threshold / control metric / pass-fail rule, any validation / segmentation / falsification / geometry-validity claim,
any screen / real-clip / camera / live / runtime / memory authorization, any classifier (B) / neural (C) opening, any
"Brainvision sees" / vision / descriptor-validity / temporal-order / readiness / capability claim, any recommendation
to expand, or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Non-Claim Invariants Review v2.16. Docs-only review. Opens no
implementation lane, no test expansion, and no family / vocabulary expansion; opens no classifier / neural / screen /
real-clip / runtime / memory work; adopts no descriptor / coordinate system / numeric geometry / metric / equation /
threshold / control metric / pass-fail rule; consolidates the fifteen non-claim invariants (representation
non-validation, fixture non-evidence, A-F non-completeness, vocabulary non-descriptor, relation non-geometry,
gradient/boundary non-measurement, null/control non-validation, protocol non-proof, HOLD non-failure/non-pass,
outcome-label non-capability, offline non-runtime, symbolic non-screen, static non-temporal, anti-claim-flags
non-evidence, no vision implication) with statement, drift risk, safe-use rule, and consequence per invariant plus the
cross-invariant pressure points; summarizes established vs not-established; recommends the branch REMAIN HELD; preserves
all claim locks and the frozen verdict HOLD; makes no vision / "Brainvision sees" / descriptor-validity /
geometry-validity / temporal-order / readiness claim; outcome label FLAT_OPPONENT_FIELD_NON_CLAIM_INVARIANTS_REVIEW_ONLY;
no `§0` pointer added; no tags.*
