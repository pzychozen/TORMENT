# TORMENT Brainvision Flat Opponent-Field Representation Plan v2.7

## 1. Status / Scope

**DOCS-ONLY representation PLAN.** This is a planning note only. It opens **no** code, **no** tests, **no**
runtime, and **no** integration lane; it authorizes **no** implementation and is not corrective. It plans
*whether and how* the v2.6 A-F flat opponent-field fixture families could **later** be represented as bounded
symbolic / spatial structures, and it does nothing else. It sits over the accepted v2.6 edge
(`93c6b09`) and changes none of the accepted v2.6 files.

v2.6 reporting is **generated but UNVALIDATED**. The accepted v2.6 harness
(`research/brainvision/run_flat_opponent_field_synthetic_fixtures_v2_6.py`, with its test and findings receipt)
generated structural fixture DESCRIPTIONS for exactly six families — A uniform opponent patches, B adjacent
opponent patches, C gradient fields, D edge / discontinuity fields, E region-field separation fixtures, F
null / control fields — with controls and completeness-enforced non-authorizing guards. `protocol_ok = True`
in v2.6 meant only that the required fixture reports and guards were **present** — not validation, closure,
descriptor validity, geometry validity, temporal order, screen readiness, runtime readiness, memory readiness,
or vision.

**v2.7 plans representation only and authorizes no implementation.** It introduces and authorizes **no**
descriptor, coordinate system, metric, equation, threshold, control metric, pass/fail gate, validation,
closure, screen analysis, real clip, camera / live / sensor / screen-capture / streaming path, runtime path,
memory path, prompt / context / action / render-body / autonomy contact, classifier (form B), or neural
encoder (form C). It makes **no** production vision claim, **no** "Brainvision sees" claim, **no**
temporal-order claim, **no** descriptor-validity claim, **no** memory-readiness / runtime-readiness /
integration-readiness claim. Everything stays offline under `research/brainvision/` + `tests/research/`, HELD
per v0.6. **HOLD / HELD here means held for analysis and claim control — not abandoned.**

```text
reporting_only                              = True   (v2.6, unchanged)
fixture_reporting_generated                 = True   (v2.6, unchanged)
flat_field_validated                        = False
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Central Question

```text
Can the v2.6 A-F fixture families be represented as bounded symbolic / spatial OBJECTS while still preserving
that REPRESENTATION EXISTENCE DOES NOT IMPLY VALIDATION?
```

The question is deliberately narrow. It asks only whether a **bounded symbolic / spatial** representation of the
six families is *conceivable* as a future structure — a small, closed vocabulary of parts and relations — **without**
adopting any numeric geometry, and **without** the existence of that representation being read as evidence that the
flat opponent-field abstraction is valid, better, or "sees" anything. The generated-vs-validated separation from v2.6
is the load-bearing constraint: v2.6 established that *describing* the families is not *validating* them; v2.7 must
extend the same separation to *representing* them. A representation that could be mistaken for a validation, a
descriptor, or a metric is out of scope for v2.7 by construction.

This note does not answer the question with a build. It plans the shape of a possible answer and the guards a future
answer would have to carry.

## 3. Representation Targets

Conceptual targets only. None of the following is implemented, specified numerically, or authorized here; each is a
**planning placeholder** describing what a future representation would have to contain and what it must never become.

```text
T1. Fixture object schema (CONCEPTUAL ONLY)
    A bounded symbolic object naming WHAT a fixture family conceptually is (its family letter, its role
    stimulus/control, its conceptual parts, and its non-claim boundary). It is NOT a data structure holding pixels,
    coordinates, arrays, values, or a descriptor; it holds conceptual labels and guard fields only.

T2. Region relation vocabulary (CONCEPTUAL ONLY)
    A small, closed set of conceptual RELATION labels between parts (e.g. "is-a-patch", "neighbors", "transitions-to",
    "bounded-by", "separates-region-from-field"). These are NAMES for relations, NOT distances, adjacency equations,
    coordinates, or metrics. No relation carries a number, a direction in a coordinate frame, or a magnitude.

T3. Family coverage for A-F
    The vocabulary and schema must be expressible for all six families A-F (including the F control family) using the
    SAME closed vocabulary, so no family needs a private numeric extension. Coverage is a completeness check on the
    CONCEPTUAL vocabulary, not a validation of any family.

T4. Boundary / guard fields that preserve non-authorization
    Every fixture object must carry explicit guard/boundary fields that keep it non-authorizing and non-validating:
    representation_only, represents_not_validates, descriptor_present=absent, coordinates_present=absent,
    metric_present=absent, equation_present=absent, threshold_present=absent, claims_validation=absent, and the
    generated-vs-validated boundary carried forward. These are the same completeness-enforced guard obligations as
    v2.6, restated for representation. A future object WITHOUT them would be inadmissible.
```

## 4. Allowed Conceptual Vocabulary

A future representation may use **simple conceptual labels only**, drawn from a small closed set:

```text
patch        neighbor       transition     boundary
region       field          gradient       discontinuity
null/control
```

These are **conceptual names**, used to say what a family or a part conceptually *is* or *relates to*. Explicitly
**disallowed** in v2.7 (and in any representation it plans): coordinates, numeric geometry, positions, distances,
angles, magnitudes, metrics, formulas, equations, thresholds, pass/fail language, "better/worse" language, and any
descriptor claim. If a label cannot be expressed without a number, a coordinate, a metric, or a pass/fail rule, it is
out of scope for v2.7. The vocabulary is a **naming** vocabulary, never a **measuring** one.

## 5. A-F Representation Sketch

For each family, a conceptual-only sketch of how it *could later* be represented symbolically **without implying
validity**. Each sketch is a description of parts and named relations from the §4 vocabulary — no coordinates, no
numbers, no descriptor, no metric, no pass/fail.

```text
A. Uniform opponent patch
   A single symbolic "patch" object carrying the conceptual note "uniform opponent content", with the guard fields of
   T4. Representation: one patch, no neighbors, no transition, no boundary relation. Says only "a patch is nameable";
   says NOTHING about whether opponent content is validly present.

B. Adjacent opponent patches
   Two or more "patch" objects joined by the conceptual "neighbors" relation. Adjacency is a NAMED relation, not a
   distance or an adjacency equation. Says only "patches can be named as neighbors"; asserts no metric of nearness.

C. Gradient field
   A "field" object carrying the conceptual "gradient" / "transition" note between conceptual endpoints. "Gradient" is
   a NAME for smooth transition, not a slope, derivative, or numeric rate. Says only "a transition field is nameable".

D. Edge / discontinuity field
   A "field" object carrying a conceptual "boundary" / "discontinuity" note. "Discontinuity" is a NAMED contrast
   between regions, not an edge detector, gradient magnitude, or threshold. Says only "a discontinuity is nameable".

E. Region-field separation fixture
   Two conceptual scopes — a local "region" and a global "field" — joined by the conceptual "separates-region-from-
   field" relation. It names the LOCAL-vs-FIELD distinction only; it computes no separation, defines no field
   descriptor, and asserts no measure of separation.

F. Null / control field
   A "null/control" object marked with role=control, carrying the conceptual note "neutral / matched non-opponent
   control". It is a CONTROL by naming, present to prevent trivial representational optimism. It is explicitly NOT a
   pass/fail control, NOT a decision rule, and carries no metric or threshold.
```

Each sketch is a **naming exercise** over the §4 vocabulary. None builds an object, holds data, or claims that the
named structure is present, correct, or valid in any fixture.

## 6. Generated-vs-Validated Preservation Rule

This is the core safeguard of v2.7 and must be stated bluntly. Every arrow below is a **non-implication**:

```text
generated fixture report EXISTS        ≠  represented geometry is VALID
representation EXISTS                   ≠  a DESCRIPTOR exists
representation EXISTS                   ≠  a METRIC exists
representation EXISTS                   ≠  a COORDINATE SYSTEM / numeric geometry exists
representation EXISTS                   ≠  VALIDATION
representation EXISTS                   ≠  CLOSURE
representation EXISTS                   ≠  screen / vision / runtime / memory / integration readiness
representation EXISTS                   ≠  temporal order
representation EXISTS                   ≠  "Brainvision sees"
```

A representation is a bounded set of conceptual NAMES and NAMED relations. Naming a structure never measures it,
never validates it, never grants it a descriptor or a metric, and never moves a claim lock or the verdict. If any
future artifact reads "we can represent A-F" as "the flat opponent-field is valid / better / real", that artifact has
violated this rule and is inadmissible.

## 7. Guard Obligations for Any Future Implementation

Representation is **not** authorized by this plan. Should the operator ever choose to pursue it, the following
obligations hold — stated here as constraints on a hypothetical future, not as an invitation to build:

```text
- Any future implementation requires a SEPARATE, operator-approved implementation PLAN and a Codex review BEFORE any
  code, test, or schema is written. v2.7 authorizes none of it.
- Any future implementation must PRESERVE all v2.6 false locks unless each is EXPLICITLY and SEPARATELY approved:
      first_pass_structure_validity_claim_allowed = False
      temporal_claim_allowed                      = False
      descriptor_validity_claim_allowed           = False
      flat_field_validated                        = False
      verdict                                      = HOLD
- It must carry the completeness-enforced guard/boundary fields of T4 (representation_only, represents_not_validates,
  the generated-vs-validated boundary, and absence markers for descriptor / coordinates / metric / equation /
  threshold), such that a missing or violated guard forces an invalid/breach outcome, never a validation.
- It must adopt NO descriptor, coordinate system, metric, equation, threshold, control metric, or pass/fail gate; open
  NO screen / real-clip / camera / live / sensor / streaming / runtime / memory / prompt / context / action /
  render-body / autonomy path; and keep forms B (classifier) and C (neural) CLOSED.
- It must stay offline under research/brainvision/ + tests/research/, HELD per v0.6, with no §0 pointer and no tags.
```

## 8. Risks / Ambiguities

```text
R1. Symbolic representation mistaken for validation.
    The central risk. A named A-F structure could be read as "the geometry is valid". Mitigation: the §6
    non-implication rule and the T4 represents_not_validates / generated-vs-validated guard fields, restated on every
    object; no validation-positive label anywhere.

R2. Vocabulary drifting into descriptor semantics.
    "patch/gradient/boundary" could slide from NAMES into implied descriptors (feature extractors). Mitigation: §4
    keeps the vocabulary a naming set only; descriptor_present stays absent; descriptor_validity_claim_allowed stays
    False; any label that needs a computed feature is out of scope.

R3. Relation terms drifting into coordinates or metrics.
    "neighbors / transition / separates" could slide into distances, positions, or magnitudes. Mitigation: relations
    are NAMED only, never numeric; no coordinate frame, distance, angle, or magnitude is admissible.

R4. Fixture objects mistaken for screen objects.
    A "field" / "region" object could be misread as a captured screen region or a live-vision object. Mitigation:
    everything is offline synthetic and conceptual; no screen / capture / camera / live path is opened; objects hold
    conceptual labels, not pixels or captured content.

R5. Null/control fields treated as pass/fail controls.
    Family F could be misread as a decision gate. Mitigation: F is a control BY NAMING only; no pass/fail rule, no
    threshold, no decision is attached; it exists to check representational completeness, not to adjudicate.

R6. "Bounded symbolic/spatial" ambiguity.
    "Spatial" could be over-read as numeric geometry. Mitigation: "spatial" here means CONCEPTUAL spatial relations
    (neighbor, boundary, region, field) named without coordinates; if a spatial notion cannot be named without a
    number, it is deferred and out of scope.
```

## 9. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False

OUTCOME_LABEL: FLAT_OPPONENT_FIELD_REPRESENTATION_PLAN_ONLY
```

v2.7 is a docs-only representation PLAN. It plans *whether* the A-F fixture families could later be represented as
bounded symbolic / spatial objects while preserving the generated-vs-validated separation; it builds nothing,
validates nothing, and authorizes nothing. The abstraction stays **HELD for analysis and claim control** — not
abandoned. All v2.6 false locks and the frozen verdict **HOLD** are preserved and unmoved. Whether to pursue
representation at all is a **separate, operator-gated, docs-first decision**, not a step this plan endorses.

## 10. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_REPRESENTATION_PLAN_v2.7.md
(new, docs-only, untracked; over the accepted v2.6 edge 93c6b09).

Verify that this plan:
- is docs-only and authorizes NO implementation (no code / tests / schema, no torment_service/, no runtime, no memory,
  no camera / live / sensor / screen-capture / streaming, no real clips, no pixels / images); keeps form B (classifier)
  and form C (neural) CLOSED; opens no screen-analysis and no flat-geometry-beyond-representation implementation;
- frames the central question as WHETHER the A-F fixture families could LATER be represented as bounded symbolic /
  spatial objects while preserving that representation existence does NOT imply validation;
- keeps the representation targets (§3) and A-F sketches (§5) CONCEPTUAL ONLY: a fixture object schema and a closed
  region-relation vocabulary of NAMES, with guard/boundary fields that preserve non-authorization; adopts NO
  descriptor / coordinate system / metric / equation / threshold / control metric / pass-fail gate;
- restricts vocabulary (§4) to simple conceptual labels (patch, neighbor, transition, boundary, region, field,
  gradient, discontinuity, null/control) and admits NO coordinates / numeric geometry / metrics / formulas /
  thresholds / pass-fail / descriptor claims;
- states the generated-vs-validated preservation rule (§6) as explicit NON-implications (generated report ≠ valid;
  representation ≠ descriptor / metric / coordinate / validation / closure / screen / vision / runtime / memory /
  integration / temporal-order readiness);
- states the guard obligations (§7): any future implementation needs a SEPARATE operator-approved plan + Codex review
  and must preserve all v2.6 false locks unless each is explicitly and separately approved;
- records the risks (§8): symbolic-representation-mistaken-for-validation, vocabulary→descriptor drift, relation→
  coordinate/metric drift, fixture-object→screen-object confusion, null/control→pass/fail confusion;
- preserves the locks and verdict (§9): flat_field_validated = False; first_pass_structure_validity_claim_allowed =
  False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; verdict = HOLD; outcome label
  FLAT_OPPONENT_FIELD_REPRESENTATION_PLAN_ONLY; interprets HOLD/HELD as held for analysis, not abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / temporal-order /
  memory-readiness / runtime-readiness / integration-readiness claim.

Flag any adopted descriptor / coordinate system / metric / equation / threshold / control metric / pass-fail rule,
any coordinates or numeric geometry, any validation / closure claim, any screen / real-clip / camera / live / runtime
/ memory authorization, any classifier (B) / neural (C) opening, any "Brainvision sees" / vision / descriptor-validity
/ temporal-order / readiness claim, any claim that representation implies validation, or any claim-lock / verdict
movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, `flat_field_validated = False`, and the frozen verdict **HOLD** are
unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Representation Plan v2.7. Docs-only representation plan. Opens no
implementation lane; opens no classifier / neural / screen / real-clip / runtime / memory work; adopts no descriptor
/ coordinate system / metric / equation / threshold / control metric / pass-fail rule; introduces no coordinates or
numeric geometry; plans WHETHER the v2.6 A-F fixture families could later be represented as bounded symbolic / spatial
objects while preserving that representation existence does not imply validation; preserves all v2.6 false locks and
the frozen verdict HOLD; makes no vision / "Brainvision sees" / descriptor-validity / temporal-order / memory /
runtime / integration claim; outcome label FLAT_OPPONENT_FIELD_REPRESENTATION_PLAN_ONLY; no `§0` pointer added; no
tags.*
