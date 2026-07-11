# TORMENT Brainvision BY/Chroma Synthetic Fixture Design Boundary Plan v2.23

## 1. Status / Scope

**DOCS-ONLY fixture-design BOUNDARY plan.** This is a boundary-setting note only. It opens **no** code, **no** tests,
**no** runtime, and **no** integration lane; it authorizes **no** implementation, **no** fixture generation, **no**
fixture design, **no** validation, **no** readiness claim, and **no** capability claim, and it is not corrective. It
sits over the accepted v2.22 edge (`8e0c2f6`) and changes none of the accepted files.

**v2.23 defines the boundary for future fixture design only.** It specifies what a *future* synthetic fixture-design
document — one that would target the v2.22 BY/chroma residual isolation question — may contain and what it must never
contain. It prepares a safe boundary *before* any future fixture-family proposal exists.

**v2.23 does not design fixtures or authorize implementation.** It introduces and authorizes **no** implementation,
tests, actual fixture generation, concrete fixture definitions, fixture data, descriptor, coordinate system, numeric
geometry, metric, equation, threshold, scoring, pass/fail gate, validation, closure, real clip, screen / camera / live
/ sensor / streaming path, runtime path, memory path, prompt / context / action / render-body / autonomy contact,
classifier (form B), or neural encoder (form C). It makes **no** production vision claim, **no** "Brainvision sees"
claim, **no** temporal-order claim, and **no** descriptor-validity / geometry-validity / screen-readiness /
memory-readiness / runtime-readiness / integration-readiness claim. **Any future fixture-design document must be
separately planned, Codex-reviewed, and operator-approved.** Everything stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6. **HOLD / HELD means held for analysis and claim control — not abandoned.**

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

## 2. v2.22 Question Preserved

```text
PRIMARY QUESTION (Formulation A) -- preserved verbatim in force:
  "Can future synthetic design distinguish BY-axis residual behavior from generic chroma proxy effects without adopting
   metrics or closure claims?"

MANDATORY NON-CLAIM CONSTRAINT (Formulation C) -- preserved verbatim in force:
  "Residual localization must not imply descriptor validity."

FOLDED-IN GUARDRAIL (Formulation B): a future design must hold apart FIXTURE-FAMILY ARTIFACTS -- the fixtures must not
manufacture the apparent residual -- WITHOUT validating the fixture families.

The question remains UNRESOLVED and NON-AUTHORIZING. Nothing about it is answered, and posing it grants nothing.

ALSO PRESERVED:
  - BY/color/chroma evidence remains UNRESOLVED LOCALIZATION EVIDENCE (it says where the difficulty is, not that it is
    closed);
  - prior FIXTURE-METRIC FAILURES are NOT solved;
  - the flat opponent-field SYMBOLIC SCAFFOLD is NON-VALIDATING scaffold only (its identities are names, not geometry
    truth);
  - SYNTHETIC FALSIFICATION remains SAFER than screen / real-clip / runtime / memory / classifier / neural / vision
    work;
  - SYNTHETIC FALSIFICATION still does NOT imply validation.
```

## 3. Future Fixture-Design Boundary

```text
A future synthetic fixture-design document (a possible v2.24, only if separately approved) MAY discuss, at a
CONCEPTUAL level only:

  - WHAT RESIDUAL PRESSURE is being isolated (the BY-axis residual vs generic chroma proxy distinction, conceptually);
  - WHAT PROXY-RISK CLASS is being guarded against (spectrum / per-channel-std / directional-movement / roughness, named
    as confound CLASSES to hold apart -- never as adopted measures);
  - WHAT FIXTURE-FAMILY ROLES might be needed IN PRINCIPLE (e.g. "a role that carries the residual pressure", "a role
    that carries only the proxy character", "a null/control role") -- ROLES, never instances;
  - WHAT CLAIM LOCKS must remain False (all of them; see Section 1);
  - WHAT COUNTS AS REPORTING-ONLY LANGUAGE (per v2.17 wording discipline);
  - WHAT MUST REMAIN unmeasured, unscored, unvalidated, and unimplemented.

It MUST NOT define:

  - ACTUAL FIXTURES (no fixture instances, no fixture bank, no generated content);
  - DATA STRUCTURES (no schemas, arrays, fields, or payloads);
  - FORMULAS or EQUATIONS;
  - METRICS, SCORES, or THRESHOLDS;
  - EXPECTED OUTPUTS or expected measurable outcomes;
  - PASS/FAIL CRITERIA or acceptance rules;
  - descriptors, coordinates, or numeric geometry;
  - any screen / real-clip / camera / live / sensor / streaming / runtime / memory path;
  - classifier (form B) or neural (form C) content;
  - any validation, closure, or vision claim.

A future fixture-design document is a DESCRIPTION OF WHAT WOULD HAVE TO BE TRUE, not a construction of anything.
```

## 4. Boundary Dimension Review

```text
--------------------------------------------------------------------------------------------------------------------
D1. ALLOWED CONCEPTUAL CONTENT
   The future design doc may discuss: the residual pressure being isolated; the proxy-risk class guarded against;
   fixture-family ROLES in principle; the claim locks that stay False; reporting-only language; and what stays
   unmeasured / unscored / unvalidated / unimplemented. All at the level of "what would have to be true", never "here
   is the thing".

D2. FORBIDDEN CONCRETE CONTENT
   It must NOT define: actual fixtures or fixture instances; a fixture bank; data structures / schemas / arrays /
   payloads; formulas or equations; metrics, scores, or thresholds; expected outputs or measurable outcomes; pass/fail
   criteria; descriptors; coordinates; numeric geometry. Concreteness IS the breach.

D3. RESIDUAL ISOLATION BOUNDARY (isolation must not become closure)
   "Isolating" the BY/chroma residual means posing a CONCEPTUAL DISTINCTION, never resolving it. A future doc may say
   what a distinction would have to hold apart; it may NOT say the residual IS distinct, IS real, or IS closed.
   Localization != closure; the BY/color/chroma route stays UNRESOLVED.

D4. PROXY-RISK BOUNDARY (generic proxies must not be treated as solved)
   The proxy classes (spectrum, per-channel std, directional movement, roughness) are named ONLY as confounds to hold
   apart conceptually. A future doc may NOT treat any proxy as measured, controlled, ruled out, or solved, and may NOT
   adopt any of them as a measure. The standing presumption remains: an apparent residual IS a generic proxy effect
   until a reporting-only distinction shows otherwise -- and no such showing exists.

D5. DESCRIPTOR-VALIDITY BOUNDARY (enforcing Formulation C)
   The target stays LOCALIZATION, never descriptor proof. A future doc must carry Formulation C explicitly, must keep
   descriptor_validity_claim_allowed = False, must define NO descriptor, and must never imply that localizing a
   residual makes any descriptor valid, better, or warranted. "Where the difficulty is" is not "the descriptor works".

D6. REPORTING-ONLY BOUNDARY ("distinguish / isolate / separate" must not become scored/validated)
   These verbs are the highest-risk words in this line. In any future doc they mean ONLY: "report whether a distinction
   can even be POSED", never "measure how separated", "score the separation", or "show the separation is real". They
   must always appear with an explicit non-claim ("a reporting-only distinction; not a scored or validated
   separation"). Per v2.17: never "passed", "verified", "proven", "succeeded".

D7. NO-METRIC BOUNDARY
   No metric, threshold, score, equation, ratio, margin, ceiling, floor, acceptance criterion, or pass/fail gate may be
   introduced -- not as a definition, not as an example, not as a "for illustration". If a sentence requires a number
   to be meaningful, it is out of bounds. The question comes before the machinery; no math until the target failure is
   clear and separately approved.

D8. NO-FIXTURE-DEFINITION BOUNDARY (v2.23 must not itself become fixture design)
   THIS document defines boundaries only. It names NO fixture, NO family, NO instance, NO parameter, and NO content. It
   describes what a FUTURE doc may discuss -- and by construction does not do that discussing itself. Any concrete
   fixture content appearing here would be a breach of this plan's own scope.

D9. OPERATOR-GATED CONTINUATION
   Before any future v2.24 fixture-family PROPOSAL: a SEPARATE docs-first plan, a Codex review, and explicit operator
   approval are required, naming the exact scope, what it must never become, and how every claim lock and the
   generated-vs-validated separation are preserved. v2.23 authorizes NO continuation by itself.
--------------------------------------------------------------------------------------------------------------------
```

## 5. Forbidden Drift Register

Drifts that any future fixture-design document (and any reading of this one) must refuse:

```text
- DISTINCTION becoming METRIC: "distinguish/separate" turning into a scored, measured, or thresholded separation.
- ISOLATION becoming CLOSURE: "isolate the residual" turning into "the residual is real / resolved / closed".
- RESIDUAL LOCALIZATION becoming DESCRIPTOR VALIDITY: "we localized it" turning into "the descriptor is valid/works".
- PROXY-RISK DISCUSSION becoming SOLVED PROXY CONTROL: naming the confounds turning into "the proxies are controlled /
  ruled out".
- CONCEPTUAL FIXTURE ROLES becoming CONCRETE FIXTURE DEFINITIONS: a role ("carries the residual pressure") turning into
  an instance, a bank, a schema, or a parameter.
- FUTURE DESIGN becoming IMPLEMENTATION AUTHORIZATION: a design description turning into a licence to write code.
- SYNTHETIC FALSIFICATION becoming VALIDATION: an offline reporting-only probe turning into evidence the field "works".
- REPORTING-ONLY LANGUAGE becoming PASS/FAIL LANGUAGE: "reported" turning into "passed / failed / verified / proven".
```

Additionally, any future fixture-design document must: **remain docs-only** unless separately approved otherwise; use
**conceptual fixture roles only**; avoid **concrete fixture instances**; avoid **numerical parameters**; avoid
**expected measurable outcomes**; avoid **pass/fail language**; avoid **descriptor-validity language**; avoid
**geometry-validity language**; avoid **validation/closure language**; avoid **screen/runtime/memory/vision language**;
**preserve all locks False**; and **keep `verdict = HOLD`**.

## 6. Operator-Gated Next Step

```text
The next ACTUAL slice must be chosen by the OPERATOR. IF approved, it may be a DOCS-ONLY FIXTURE-FAMILY PROPOSAL
(a possible v2.24) -- and even that must be SEPARATELY BOUNDED, Codex-reviewed, and operator-approved before it is
written, and must conform to every boundary in Sections 3-5 (conceptual roles only; no fixtures, data structures,
formulas, metrics, thresholds, expected outputs, or pass/fail criteria; Formulation C carried explicitly; all locks
False; verdict HOLD).

v2.23 is NOT self-authorizing: it starts no work, proposes no fixture family, designs nothing, and commits to nothing.
Until the operator chooses, the flat opponent-field symbolic branch stays PAUSED HELD, the prior BY/color/chroma work
stays FROZEN EVIDENCE, the v2.22 question stays UNRESOLVED, and Brainvision stays offline / quarantined.
```

## 7. Verdict

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

OUTCOME_LABEL: BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_DESIGN_BOUNDARY_PLAN_ONLY
```

v2.23 is a docs-only synthetic fixture design boundary plan. It preserves the v2.22 primary question (Formulation A)
and its mandatory non-claim constraint (Formulation C), plus the folded-in fixture-artifact guardrail (Formulation B);
defines what a future fixture-design document may discuss conceptually (residual pressure, proxy-risk class, fixture
roles in principle, claim locks, reporting-only language, what stays unmeasured) and what it must never define
(fixtures, data structures, formulas, metrics, thresholds, expected outputs, pass/fail criteria, descriptors,
coordinates); reviews nine boundary dimensions; registers the forbidden drifts; and gates any continuation behind
separate operator approval and Codex review. It designs no fixtures, defines no metric / score / threshold, selects no
work, and is not self-authorizing. All claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 8. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_DESIGN_BOUNDARY_PLAN_v2.23.md
(new, docs-only, untracked; over the accepted v2.22 edge 8e0c2f6).

Verify that this plan:
- is docs-only and authorizes NO implementation, NO tests, NO actual fixture generation, NO concrete fixture
  definitions, NO fixture data, NO descriptor / coordinate / numeric geometry / metric / equation / threshold /
  scoring / pass-fail gate / validation / closure, no real clips, no screen / camera / live / sensor / streaming /
  runtime / memory paths, no classifier (form B) / neural (form C), no vision; and DOES NOT DESIGN FIXTURES;
- frames the central question as WHAT a future BY/chroma synthetic fixture-design document would be allowed to describe
  and what it must avoid, so Formulation A stays reporting-only and Formulation C prevents descriptor-validity drift;
- preserves the v2.22 framing verbatim: the PRIMARY question ("Can future synthetic design distinguish BY-axis residual
  behavior from generic chroma proxy effects without adopting metrics or closure claims?") and the MANDATORY non-claim
  constraint ("Residual localization must not imply descriptor validity"), plus that BY/color/chroma evidence remains
  unresolved localization evidence, prior fixture-metric failures are not solved, the flat opponent-field symbolic
  scaffold is non-validating scaffold only, synthetic falsification is safer than screen/runtime/memory/vision work,
  and synthetic falsification still does not imply validation;
- defines the ALLOWED conceptual content for a future design doc (residual pressure being isolated; proxy-risk class
  guarded against; fixture-family ROLES in principle; claim locks that stay False; reporting-only language; what stays
  unmeasured / unscored / unvalidated / unimplemented) and the FORBIDDEN concrete content (actual fixtures, data
  structures, formulas, metrics, thresholds, expected outputs, pass/fail criteria, descriptors, coordinates);
- covers ALL required boundary dimensions (D1 allowed conceptual content; D2 forbidden concrete content; D3 residual
  isolation must not become closure; D4 proxy-risk must not be treated as solved; D5 descriptor-validity boundary
  enforcing Formulation C; D6 reporting-only boundary preventing "distinguish/isolate/separate" from becoming scored or
  validated; D7 no-metric boundary; D8 no-fixture-definition boundary keeping v2.23 itself from becoming fixture design;
  D9 operator-gated continuation);
- registers the forbidden drifts (distinction -> metric; isolation -> closure; residual localization -> descriptor
  validity; proxy-risk discussion -> solved proxy control; conceptual fixture roles -> concrete fixture definitions;
  future design -> implementation authorization; synthetic falsification -> validation; reporting-only language ->
  pass/fail language) and the future-doc guardrails (docs-only; conceptual roles only; no concrete instances; no
  numerical parameters; no expected measurable outcomes; no pass/fail, descriptor-validity, geometry-validity,
  validation/closure, or screen/runtime/memory/vision language; all locks False; verdict HOLD);
- states that the next slice, IF approved, may be a DOCS-ONLY fixture-family proposal that must be separately bounded,
  Codex-reviewed, and operator-approved; and that v2.23 is not self-authorizing;
- preserves the locks and verdict (Section 7): flat_field_validated = False; first_pass_structure_validity_claim_allowed
  = False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_DESIGN_BOUNDARY_PLAN_ONLY; interprets HOLD/HELD as held for analysis, not
  abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any concrete fixture / fixture instance / fixture bank / data structure / schema / formula / metric / score /
threshold / expected output / pass-fail criterion / numerical parameter defined anywhere in this plan (which would
breach its own D8 scope), any "distinguish/isolate/separate" used as a scored or validated term, any proxy treated as
controlled or solved, any residual localization implying descriptor validity, any closure claimed, any scaffold or
fixture family cited as validation or geometry truth, any screen / real-clip / camera / live / runtime / memory
authorization, any classifier (B) / neural (C) opening, any "Brainvision sees" / vision / descriptor-validity /
geometry-validity / temporal-order / readiness / capability claim, any authorization of fixture design or
implementation, or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY/Chroma Synthetic Fixture Design Boundary Plan v2.23. Docs-only boundary plan. Opens no
implementation lane, no tests, no fixture generation, and no fixture design; opens no classifier / neural / screen /
real-clip / runtime / memory work; adopts no descriptor / coordinate system / numeric geometry / metric / equation /
threshold / scoring / pass-fail rule; defines no fixture, data structure, formula, expected output, or acceptance
criterion; preserves the v2.22 primary question (Formulation A) and mandatory non-claim constraint (Formulation C) with
the folded-in fixture-artifact guardrail (Formulation B); specifies what a FUTURE fixture-design document may discuss
conceptually and what it must never define, across nine boundary dimensions, with a forbidden-drift register and
future-doc guardrails; gates any continuation behind separate operator approval and Codex review; keeps the flat
opponent-field symbolic branch PAUSED HELD, prior BY/color/chroma work FROZEN EVIDENCE, and the v2.22 question
UNRESOLVED; is not self-authorizing; preserves all claim locks and the frozen verdict HOLD; makes no vision /
"Brainvision sees" / descriptor-validity / geometry-validity / temporal-order / readiness claim; outcome label
BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_DESIGN_BOUNDARY_PLAN_ONLY; no `§0` pointer added; no tags.*
