# TORMENT Brainvision Flat Opponent-Field Representation Boundary Review v2.8

## 1. Status / Scope

**DOCS-ONLY implementation-boundary REVIEW.** This is a review note only. It opens **no** code, **no** tests, **no**
runtime, and **no** integration lane; it authorizes **no** implementation by itself, and it is not corrective. It sits
over the accepted v2.7 edge (`220fa46`) and changes none of the accepted files.

Lineage held in view:

```text
v2.6  generated/reporting-only STRUCTURAL FIXTURE DESCRIPTIONS for six families A-F (with controls + guards).
v2.7  docs-only conceptual REPRESENTATION PLAN: planned WHETHER A-F could later be represented as bounded symbolic /
      spatial structures while preserving generated-vs-validated separation; authorized no implementation.
v2.8  (this doc) docs-only BOUNDARY REVIEW: reviews the EXACT boundary a possible FUTURE v2.9 minimal representation
      artifact would have to respect to stay safe; authorizes nothing by itself.
```

v2.7 planned conceptual representation only and built nothing. **v2.8 reviews a possible future implementation
boundary only** — it evaluates what would make a later, minimal, symbolic representation artifact *safe* or *unsafe*,
and under what strict, separately-approved conditions such an artifact could ever be permitted. It does not create
that artifact, does not adopt any representation, and does not move the abstraction out of HOLD.

This review introduces and authorizes **no** validation, closure, descriptor, coordinate system, numeric geometry,
metric, equation, threshold, control metric, pass/fail gate, screen analysis, real clip, camera / live / sensor /
screen-capture / streaming path, runtime path, memory path, prompt / context / action / render-body / autonomy
contact, classifier (form B), or neural encoder (form C). It makes **no** production vision claim, **no** "Brainvision
sees" claim, **no** temporal-order claim, **no** descriptor-validity claim, **no** geometry-validity claim, and **no**
screen-readiness / memory-readiness / runtime-readiness / integration-readiness claim. Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6. **HOLD / HELD means held for analysis and claim control —
not abandoned.**

```text
flat_field_validated                        = False
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Central Boundary Question

```text
What EXACT implementation boundary would be safe if a later v2.9 creates a MINIMAL representation artifact for the
A-F flat opponent-field fixture families -- and what would make such an artifact UNSAFE?
```

The question is about a boundary, not a build. A minimal representation artifact is *safe* only if it is a static,
symbolic naming of the already-accepted A-F families that cannot be read as validation, cannot smuggle in a
descriptor / coordinate / metric, and cannot open a screen / runtime / memory path. It is *unsafe* the moment it holds
a number, a coordinate, a computed feature, a pass/fail rule, or any content that could be mistaken for measuring or
seeing. This review defines that line precisely so a future decision can be made cleanly, and so that any future
artifact can be judged admissible or inadmissible against a fixed contract rather than an ad-hoc reading.

## 3. Allowed Future Shape

If — and only if — separately approved (see §8), a future v2.9 minimal representation artifact (discussed here as a
possible `research/brainvision/flat_opponent_field_representation_v2_9.py`, **not created now**) could be limited to
**static, conceptual, symbolic objects only**:

```text
- Offline research-only, OUTSIDE torment_service/, under research/brainvision/ + tests/research/, HELD per v0.6.
- Represents ONLY the existing six fixture families A-F from v2.6/v2.7; introduces no new family and expands none.
- Static symbolic FIXTURE OBJECTS only, each carrying:
    * fixture family name / letter (A-F) and role (stimulus / control);
    * conceptual COMPONENTS drawn from a closed label set: patch, region, field, boundary, transition, gradient,
      discontinuity, null/control;
    * conceptual RELATION labels drawn from a closed set: adjacent_to, separates, transitions_to, contains,
      contrasts_with (NAMES only -- no direction, distance, or magnitude);
    * GUARD FLAGS that remain False (representation_only, represents_not_validates, and absence markers for
      descriptor / coordinates / metric / equation / threshold), completeness-enforced so any missing or True guard
      forces an invalid/breach outcome, never a validation;
    * a CONSERVATIVE outcome label with no validation-positive form.
- Deterministic, symbolic output; no data, no image, no capture, no measurement.
- Preserves generated-vs-validated separation and every v2.6 false lock and the HOLD verdict.
```

Everything in this shape is a **naming** of existing families. It says what a family conceptually *is* and what its
parts conceptually *relate to*, using labels — and nothing more.

## 4. Forbidden Future Shape

A future v2.9 artifact would be **inadmissible** — and this review does not and cannot authorize it — if it contains
any of the following. This list is exhaustive of the disqualifying openings:

```text
- x/y coordinates, grid coordinates, pixel coordinates, positions, vectors;
- numeric distances, numeric gradients, angles, magnitudes, numeric geometry of any kind;
- formulas, equations, thresholds, scores, metrics, control metrics;
- classifier features, descriptor arrays, any descriptor or descriptor-validity content (form B);
- neural encodings / embeddings (form C);
- image data, pixel arrays, screen data, real-clip data, camera / live / sensor / screen-capture / streaming input;
- pass/fail evaluation, decision gates, "better/worse" or validity language;
- validation, closure, geometry-validity, or temporal-order content;
- runtime path, memory path, prompt / context / action / render-body / autonomy contact;
- any torment_service/ touch, or any move that reads as production vision or "Brainvision sees".
```

If a proposed artifact needs any item above to express a family or a relation, it is out of bounds for the
symbolic-representation direction and is not what this review contemplates.

## 5. Generated-vs-Validated Boundary

The load-bearing safeguard, restated for a possible implementation. Each line is a **non-implication**:

```text
representation artifact EXISTS   ≠  the represented geometry is VALID
symbolic RELATION EXISTS         ≠  geometric truth (adjacency/separation/transition are NAMES, not measurements)
GUARD presence EXISTS            ≠  pass/fail evidence (a guard proves non-authorization, not correctness)
symbolic object EXISTS           ≠  a DESCRIPTOR / METRIC / COORDINATE exists
representation EXISTS            ≠  VALIDATION / CLOSURE
representation EXISTS            ≠  screen / vision / runtime / memory / integration readiness
representation EXISTS            ≠  temporal order
```

Building a symbolic artifact would move the scaffold one notch — from *describing* families (v2.6) to *naming their
structure as objects* — but it would still measure nothing, validate nothing, and see nothing. A future artifact that
lets "we can represent A-F" be read as "the flat opponent-field is valid / better / real" has violated this boundary
and is inadmissible.

## 6. Claim-Lock Preservation

Any future v2.9 artifact — and this review — must preserve, unmoved:

```text
flat_field_validated                        = False
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

None of these may move without a **separate, explicit** operator approval for that specific lock. A representation
artifact, by construction, moves no lock and no verdict.

## 7. Risk Review

```text
R1. Representation becoming a hidden descriptor.
    A "component" list could quietly become a feature/descriptor. Mitigation: components are fixed conceptual LABELS
    from a closed set; descriptor_present stays absent; descriptor_validity_claim_allowed stays False; any component
    needing a computed feature is forbidden (§4).

R2. Symbolic relation labels becoming implicit coordinates.
    adjacent_to / separates / transitions_to could imply positions or distances. Mitigation: relations are NAMES only,
    carry no direction / distance / magnitude / order; no coordinate or numeric geometry admissible (§4).

R3. Guard fields becoming pass/fail metrics.
    A guard could drift into a decision score. Mitigation: guards are boolean non-authorization markers, completeness-
    enforced to force an invalid/breach outcome when missing or True; they never adjudicate validity and carry no
    threshold or score.

R4. Null/control fields becoming validation controls.
    Family F could be misread as a pass/fail control. Mitigation: F stays a control BY NAMING only; no decision rule,
    threshold, or metric attaches; it exists for representational completeness, not adjudication.

R5. A-F objects being mistaken for screen objects.
    A "field"/"region" object could be misread as a captured screen region or live-vision object. Mitigation: all
    objects are offline synthetic and symbolic; no screen / capture / camera / live path is opened; objects hold
    labels, not pixels or captured content.

R6. Future implementation read as vision progress rather than scaffold discipline.
    Shipping any .py could be over-read as "Brainvision is advancing toward sight". Mitigation: the artifact is
    explicitly a static symbolic scaffold, non-authorizing, HOLD-preserving; the receipt/tests and this review frame
    it as claim-control discipline, not a vision or readiness step; no readiness claim is made.
```

## 8. Conditional Recommendation

**This review does not authorize implementation.** It offers a *conditional* judgment only:

```text
A future v2.9 minimal representation artifact COULD be considered safe to pursue IF AND ONLY IF, together:
  (1) it is strictly bounded to STATIC, SYMBOLIC representation of the existing A-F families (the §3 Allowed Shape),
      and contains NONE of the §4 Forbidden Shape;
  (2) it is offline research-only, outside torment_service/, under research/brainvision/ + tests/research/;
  (3) it preserves generated-vs-validated separation and every §6 claim lock and the HOLD verdict, with completeness-
      enforced guards that force an invalid/breach outcome (never a validation) on any violation;
  (4) it is preceded by a SEPARATE, explicit operator approval AND a Codex review of a dedicated v2.9 implementation
      PLAN before any code or test is written.

If any one of (1)-(4) is not met, the direction is NOT recommended and remains HELD. Nothing here starts v2.9; the
decision to open it (or not) is the operator's.
```

The conditionality is the point: the boundary above is a gate, not a green light. Absent all four conditions, the
scaffold stays where v2.7 left it.

## 9. Verdict

```text
verdict                                      = HOLD
flat_field_validated                         = False
first_pass_structure_validity_claim_allowed  = False
temporal_claim_allowed                       = False
descriptor_validity_claim_allowed            = False

OUTCOME_LABEL: FLAT_OPPONENT_FIELD_REPRESENTATION_BOUNDARY_REVIEW_ONLY
```

v2.8 is a docs-only boundary review. It defines the exact line a possible future minimal representation artifact would
have to respect, and conditions any such artifact on strict symbolic/static bounds plus separate operator approval and
Codex review. It builds nothing, validates nothing, and authorizes nothing by itself. The abstraction stays **HELD for
analysis and claim control** — not abandoned. All v2.6/v2.7 false locks and the frozen verdict **HOLD** are preserved
and unmoved.

## 10. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_REPRESENTATION_BOUNDARY_REVIEW_v2.8.md
(new, docs-only, untracked; over the accepted v2.7 edge 220fa46).

Verify that this boundary review:
- is docs-only and authorizes NO implementation by itself (no code / tests / schema, no torment_service/, no runtime,
  no memory, no camera / live / sensor / screen-capture / streaming, no real clips, no pixels / images); keeps form B
  (classifier) and form C (neural) CLOSED; opens no screen-analysis and no numeric-geometry implementation;
- frames the central question as WHAT EXACT BOUNDARY would make a FUTURE v2.9 minimal representation artifact safe or
  unsafe, and does not itself create or authorize that artifact;
- specifies the Allowed Future Shape (§3) as STATIC SYMBOLIC objects only -- A-F family coverage only, conceptual
  components (patch/region/field/boundary/transition/gradient/discontinuity/null-control), conceptual relation labels
  (adjacent_to/separates/transitions_to/contains/contrasts_with) as NAMES only, guard flags that remain False, and a
  conservative outcome label; adopts NO descriptor / coordinate / metric / equation / threshold / control metric /
  pass-fail;
- specifies the Forbidden Future Shape (§4) exhaustively: coordinates (x/y/grid/pixel), vectors, numeric distances /
  gradients / geometry, formulas / equations / thresholds / scores / metrics, classifier features / descriptor arrays,
  neural encodings, image / screen / real-clip data, pass/fail evaluation, validation / closure / geometry-validity /
  temporal-order, runtime / memory / prompt / context / action / render-body / autonomy, and torment_service/;
- states the generated-vs-validated boundary (§5) as explicit NON-implications (artifact exists ≠ valid; relation ≠
  geometric truth; guard presence ≠ pass/fail evidence; representation ≠ descriptor / metric / coordinate / validation
  / closure / screen / vision / runtime / memory / integration / temporal-order readiness);
- preserves the claim locks (§6): flat_field_validated = False; first_pass_structure_validity_claim_allowed = False;
  temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; verdict = HOLD;
- records the risks (§7): representation→hidden-descriptor, relation-labels→implicit-coordinates, guards→pass/fail-
  metrics, null/control→validation-controls, A-F-objects→screen-objects, implementation-read-as-vision-progress;
- gives a CONDITIONAL recommendation only (§8): a future v2.9 could be safe IF AND ONLY IF strictly bounded to
  static/symbolic representation AND separately operator-approved after a Codex review of a dedicated v2.9 plan; it
  authorizes nothing now;
- sets outcome label FLAT_OPPONENT_FIELD_REPRESENTATION_BOUNDARY_REVIEW_ONLY; interprets HOLD/HELD as held for
  analysis, not abandoned; adds NO §0 pointer and NO tags; and makes no vision / "Brainvision sees" / descriptor-
  validity / geometry-validity / temporal-order / readiness claim.

Flag any adopted descriptor / coordinate system / numeric geometry / metric / equation / threshold / control metric /
pass-fail rule, any validation / closure / geometry-validity claim, any screen / real-clip / camera / live / runtime /
memory authorization, any classifier (B) / neural (C) opening, any "Brainvision sees" / vision / descriptor-validity /
temporal-order / readiness claim, any UNCONDITIONAL authorization of v2.9, or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, `flat_field_validated = False`, and the frozen verdict **HOLD** are
unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Representation Boundary Review v2.8. Docs-only boundary review. Opens no
implementation lane; opens no classifier / neural / screen / real-clip / runtime / memory work; adopts no descriptor /
coordinate system / numeric geometry / metric / equation / threshold / control metric / pass-fail rule; reviews the
EXACT boundary a possible future v2.9 minimal symbolic representation artifact would have to respect, and conditions
any such artifact on strict static/symbolic bounds plus separate operator approval and Codex review; authorizes
nothing by itself; preserves all v2.6/v2.7 false locks and the frozen verdict HOLD; makes no vision / "Brainvision
sees" / descriptor-validity / geometry-validity / temporal-order / memory / runtime / integration claim; outcome label
FLAT_OPPONENT_FIELD_REPRESENTATION_BOUNDARY_REVIEW_ONLY; no `§0` pointer added; no tags.*
