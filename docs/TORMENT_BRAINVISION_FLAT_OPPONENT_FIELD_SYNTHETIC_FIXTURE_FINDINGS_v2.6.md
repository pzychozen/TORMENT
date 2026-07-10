# TORMENT Brainvision Flat Opponent-Field Synthetic Fixture Findings v2.6

## 1. Status / non-claims

**DOCS-ONLY findings receipt for a REPORTING/GUARD-ONLY, NON-LEARNING form-A implementation.** It records what the
v2.6 flat opponent-field synthetic fixture reporting harness established and did **not** establish. It is a synthesis
of an already-accepted, already-committed harness (`54fa8b5`) built under the accepted v2.5 boundary; it opens **no**
code, tests, runtime, or integration lane and is not corrective. The v2.6 harness **generated structural fixture
reporting only** for the preregistered synthetic fixture families A-F; it does **not** adopt a descriptor, a
coordinate system, a metric, an equation, a threshold, a control metric, or a pass/fail validity rule, **redefines no
`TOL`**, changes no formula / §7 anti-proxy logic / §8 verdict logic, deletes or weakens no control, redesigns no
descriptor, reopens no spectral group, expands no generator family, and opens **no classifier (form B) and no neural
encoder (form C)**. It opens **no flat-geometry implementation, no pixel/image, and no screen-analysis
implementation**. Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

**v2.6 did not validate flat opponent-field geometry.** This note makes **no** vision claim, **no** "Brainvision
sees" claim, **no** temporal-order claim, **no** descriptor-validity claim, **no** memory-readiness claim, **no**
runtime-readiness claim, and **no** integration-readiness claim. It touches no `torment_service/`, runtime, camera /
sensor / live-capture / screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy
paths, and makes **no real-clip / local-clip move** and **no memory-system integration**. The frozen Brainvision §8
verdict is **HOLD** and untouched.

```text
flat_field_validated                        = False
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v2.3-v2.5

```text
v2.3  (0d8722e)  flat opponent-field AUDIT HARNESS: generated reporting panels A-F as structural reporting; accepted.
v2.3  (813c76c)  flat opponent-field findings receipt: recorded what v2.3 established and did NOT establish.
v2.4  (8dfd48c)  SYNTHETIC FIXTURE PROPOSAL: named the synthetic fixture-family direction; conceptual; adopting none.
v2.4a (dd97f59)  SYNTHETIC FIXTURE PREREG PLAN: the FINITE fixture-family obligations A-F + controls + deferrals.
v2.5  (7f25ba4)  SYNTHETIC FIXTURE IMPLEMENTATION REVIEW: the exact v2.6 boundary (required fields / tests / breach
                 conditions / claim-lock preservation / generated-vs-validated boundary); authorize reporting only.
v2.6  (54fa8b5)  SYNTHETIC FIXTURE HARNESS: generated fixture families A-F as structural fixture DESCRIPTIONS with
                 controls + non-authorizing guards; accepted under the v2.5 boundary.
v2.6  (this doc) findings receipt: records what v2.6 established and did NOT establish.
```

v2.3 implemented the audit panels as reporting; v2.4/v2.4a proposed and preregistered the synthetic fixture families;
v2.5 reviewed and fixed the exact reporting/guard-only boundary; v2.6 implemented it as a reporting/guard-only
harness. This receipt is a synthesis over that implementation. It does not validate flat opponent-field geometry,
adopt a descriptor, or select any representation, and it changes nothing the fixture route or the v2.x design froze.

## 3. What v2.6 implemented

The v2.6 harness (`research/brainvision/run_flat_opponent_field_synthetic_fixtures_v2_6.py`, with
`tests/research/test_brainvision_flat_opponent_field_synthetic_fixtures_v2_6.py`) is a form-A, non-learning,
reporting/guard-only harness that generates the preregistered synthetic fixture families A-F as **structural fixture
descriptions**. Because the flat opponent-field is a NEW, UNVALIDATED abstraction, v2.6 introduces **no** numeric
surface: no pixels, no images, no descriptor, no coordinate system, no metric, no equation, no threshold, no control
metric, no pass/fail validity gate:

```text
A uniform_opponent_patches  : reports isolated BY/RG local regions as patch explicitness only; no descriptor / coord / metric.
B adjacent_opponent_patches : reports neighboring local regions as adjacency / neighborhood conceptually; no adjacency eqn / distance.
C gradient_fields           : reports smooth BY/RG transition fields as gradient / continuity conceptually; no gradient eqn / threshold.
D edge_discontinuity_fields : reports sharp opponent boundaries as edge / discontinuity conceptually; no edge detector / pass-fail.
E region_field_separation   : reports local-patch-pattern vs global-field-organization as a local-vs-field distinction; no field descriptor.
F null_control_fields       : reports neutral / matched non-opponent CONTROLS that prevent trivial reporting optimism; no control metric.
```

Each family is a structural description only: it carries explicit absence markers
(`descriptor_present`, `coordinates_present`, `metric_present`, `equation_present`, `threshold_present` — all False)
and `claims_validation = False`. **No fixture family claims validation.** `protocol_ok` means only that the required
fixture reports, the controls, the generated-vs-validated boundary, and the guards are PRESENT — **not** validation.
`flat_field_validated` is builder-backed and False; the output is deterministic; a missing family / control /
boundary / guard, an authorizing flag, an incomplete boundary, `flat_field_validated = True`, or a non-HOLD verdict
forces `invalid_protocol_breach`.

## 4. Validation summary

```text
targeted v2.6 tests   : 85 passed
v2.6 script           : emits FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED ; protocol_ok True ;
                        flat_field_validated False ; verdict HOLD
mutation probes       : boundary lies (flat_field_validated True inside the boundary / missing boundary text),
                        top-level flat_field_validated True, and a non-HOLD verdict each flip to invalid_protocol_breach
full tests/research    : 498 passed
claim locks / verdict : locks False False False ; verdict HOLD (unchanged)
```

The tests assert only platform-independent robust facts: stdlib-only imports (no `torment*` / service); no pixel array
/ image / coordinate grid / descriptor / metric in source; fixture families A-F present as structural descriptions;
controls present; the generated-vs-validated boundary present and explicit; the completeness-enforced adoption and
authorization flag sets (all present and False, ANY missing OR True forcing `invalid_protocol_breach`); the boundary,
`flat_field_validated`, and verdict each breach-checked; no fixture family claiming validation; `protocol_ok` =
presence-only (not validation); the conservative label; deterministic output; `v1x_status` frozen_evidence and
`v2x_status` unvalidated_conceptual_pivot; and claim locks staying False with verdict HOLD. Windows pytest is the
source of truth.

## 5. Main result

```text
OUTCOME_LABEL: FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED
               flat_field_validated = False     verdict = HOLD     protocol_ok = True (presence-only)

FIXTURE FAMILIES A-F (structural fixture descriptions, adopting nothing)
  A uniform_opponent_patches   role=stimulus  claims_validation=False  descriptor/coordinates/metric/equation/threshold_present=False
  B adjacent_opponent_patches  role=stimulus  claims_validation=False  (adjacency conceptual only; no equation / distance)
  C gradient_fields            role=stimulus  claims_validation=False  (gradient / continuity conceptual only; no equation / threshold)
  D edge_discontinuity_fields  role=stimulus  claims_validation=False  (edge / discontinuity conceptual only; no detector / rule)
  E region_field_separation    role=stimulus  claims_validation=False  (local-vs-field conceptual only; no field descriptor)
  F null_control_fields        role=control   claims_validation=False  (neutral / matched non-opponent controls; no control metric)

generated_vs_validated_boundary : boundary_present=True  generated_is_not_validated=True  fixture_generated=True  flat_field_validated=False
adoption flags (10)             : all present and False
authorization flags (12)        : all present and False
```

**v2.6 successfully generated structural fixture reporting for the flat opponent-field synthetic fixture families A-F
with controls and completeness-enforced non-authorizing guards, but it did not validate flat opponent-field
geometry.** The outcome is **`FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED`** with
**`flat_field_validated = False`**: the fixture-reporting structure exists and is admissible, but nothing about the
abstraction has been built as data, tested, or validated. Generating the structure moves **no** claim lock and **no**
verdict.

## 6. Breach-contract completeness result

```text
The v2.6 breach contract is COMPLETENESS-ENFORCED across every required surface; protocol_ok is True ONLY when all of
the following are present and admissible, and flips to invalid_protocol_breach otherwise:

  fixture families  : EXACTLY A-F present, each a structural description, none claiming validation
                      (missing family OR any claims_validation True -> invalid_protocol_breach).
  controls          : the null / matched non-opponent control family (F) present with role=control
                      (missing control role -> invalid_protocol_breach).
  boundary          : the generated-vs-validated boundary present and explicit -- boundary_present True,
                      generated_is_not_validated True, fixture_generated True, flat_field_validated present and False,
                      and non-empty generated_means / validated_means text
                      (a boundary LIE -- flat_field_validated True inside the boundary, or a missing/empty boundary
                      field -- forces invalid_protocol_breach).
  adoption flags    : all 10 present and False -- descriptor_adopted, coordinate_system_adopted, metric_adopted,
                      equation_adopted, threshold_adopted, control_metric_adopted, pass_fail_validity_rule_adopted,
                      tol_redefined, generator_family_expanded, spectral_closure_reopened
                      (any missing OR any True -> invalid_protocol_breach).
  authorization     : all 12 present and False -- screen_analysis_authorized, camera_live_sensor_streaming_authorized,
                      real_clip_authorized, runtime_authorized, memory_authorized, classifier_form_b_authorized,
                      neural_form_c_authorized, flat_geometry_beyond_reporting_authorized, vision_claim_allowed,
                      descriptor_validity_claim_allowed, temporal_claim_allowed, integration_readiness_claim_allowed
                      (any missing OR any True -> invalid_protocol_breach).
  claim locks       : first_pass_structure_validity_claim_allowed / temporal_claim_allowed /
                      descriptor_validity_claim_allowed all False (any moving True -> invalid_protocol_breach).
  flat_field_validated : False (True -> invalid_protocol_breach).
  verdict           : HOLD (anything else -> invalid_protocol_breach).

Mutation probes confirmed the contract is live, not decorative: injecting a boundary lie (flat_field_validated True
inside the boundary / a missing boundary field), a top-level flat_field_validated = True, or a non-HOLD verdict each
flips protocol_ok to False with outcome invalid_protocol_breach. A degraded guard, boundary, or flag set can never
produce a reporting result, validation, descriptor validity, or claim / verdict movement.
```

## 7. Interpretation

```text
- v2.6 is the FIRST implemented, boundary-conformant realisation of the flat opponent-field synthetic fixture
  reporting: the families A-F proposed in v2.4, preregistered in v2.4a, and boundary-fixed in v2.5 are now GENERATED
  as structural fixture DESCRIPTIONS that, by construction, adopt no descriptor / coordinate system / metric and
  cannot silently drop a guard, a control, or the generated-vs-validated boundary.
- The reporting works AS DESIGNED and reports a DESIGN, not a MEASUREMENT: v2.6 confirms the fixture-family obligation
  structure is representable as conceptual description over offline synthetic content. It says NOTHING about whether
  the flat opponent-field abstraction is better than the fixture route, and NOTHING about vision or the descriptor.
- The A-F families are STRUCTURAL / REPORTING descriptions, not validity gates: protocol_ok = presence of required
  fixture reports + controls + boundary + guards; it is NOT validation, closure, descriptor validity, or a vision claim.
- The abstraction remains UNVALIDATED: there is no built fixture, no representation, and no test of whether uniform
  patches / adjacency / gradients / edges / region-field separation can actually be represented -- only that the
  structural description of them exists, with controls and a generated-vs-validated boundary.
```

## 8. Why this is not validation

```text
- VALIDATION would require testing whether the flat opponent-field abstraction actually REPRESENTS opponent structure
  better -- over some BUILT synthetic fixture, with a represented notion of "better". v2.6 has NO built fixture, NO
  descriptor, NO metric, NO representation; it only reports that the structural fixture DESCRIPTIONS are stated,
  controlled, and non-authorizing.
- protocol_ok = True means only that the required fixture reports + controls + boundary + guards are PRESENT; it is
  explicitly NOT validation, NOT closure, NOT descriptor validity, NOT vision (flat_field_validated is False; the
  label set carries no validation-positive label).
- Nothing was measured: the families carry structural booleans (description stated / absence markers respected), not
  values over data; there are no pixels or images.
- The generated-vs-validated boundary is itself the safeguard: fixture_generated = True means only that the structural
  DESCRIPTIONS were produced; it explicitly does NOT mean any fixture was built as data or that the field was validated.
```

## 9. What remains frozen

```text
- TOL and the frozen fixture-route evaluator / descriptor / _stats / GROUPS / floors are referenced frozen; not
  re-thresholded, not redefined, not reopened. No spectral closure group reopened; no generator family expanded.
- the v0.8a ... v1.7 fixture-route records, preserved as FROZEN EVIDENCE (not failed / retracted); v2.0 ... v2.6 as an
  UNVALIDATED conceptual pivot; no sample replacement / new seeds / generation of data.
- forms B (classifier) and C (neural) stay CLOSED; no flat-geometry-beyond-reporting, screen-analysis, camera, live,
  real-clip, runtime, or memory path opened.
- claim locks and verdict HOLD.
v2.6 changed none of the above; this receipt changes none of the above.
```

## 10. What remains unproven

Even with the flat opponent-field synthetic fixture reporting implemented, all of the following stay **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not closure                    (the BY gap is visible, not closed, in the fixture route)
not that flat opponent-field is better / valid (the fixture-reporting structure exists; the abstraction is UNVALIDATED)
```

The proof route remains **HELD / HOLD**. Generating the fixture-reporting structure is a docs/structure-layer step
over an unvalidated abstraction; it validates nothing. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`) and
`verdict = HOLD` remain in force.

## 11. Candidate next branches

Docs-first candidates only; **none opened, none authorized, and none recommended here**. In particular, this receipt
makes **no recommendation to proceed into descriptors, coordinates, metrics, equations, thresholds, real clips, screen
analysis, runtime, or memory**:

```text
A. Operator decision NOTE (docs-only): whether the synthetic fixture reporting scaffold is a direction to continue at
   all -- a values / product call for the operator, not a technical recommendation from this receipt.
B. Pause Brainvision and return to TORMENT memory / kernel work.
C. HOLD: leave the Brainvision prototype line HELD as-is.
```

## 12. Recommended next step

**Recommend only: Codex review of this receipt, then operator commit, then HOLD.** v2.6 shows the synthetic fixture
obligation structure is representable as conceptual reporting; this receipt records that and nothing more. **No
implementation branch is recommended or authorized here** — the abstraction stays HELD / HOLD, and any future
direction (including whether to continue the fixture-reporting scaffold at all) is a **separate, operator-gated,
docs-first decision**, not a step this receipt endorses.

```text
1. Codex review THIS findings receipt (docs-only; over committed edge 54fa8b5).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. No descriptor / coordinate system / metric / equation / threshold / control-metric / pass-fail / real-clip /
   screen-analysis / flat-geometry-beyond-reporting / runtime / memory / classifier (B) / neural (C) work is
   recommended or authorized here; the line stays HELD / HOLD pending a separate operator decision.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `flat_field_validated = False`,
`verdict = HOLD`.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_FINDINGS_v2.6.md
(new, docs-only, untracked; over committed edge 54fa8b5, synthesizing the accepted v2.6 reporting/guard-only
synthetic fixture harness built under the accepted v2.5 boundary).

Verify that this receipt:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen-capture/streaming, no real clips, no pixels/images); keeps form B (classifier) and form C
  (neural) CLOSED; and opens NO flat-geometry-beyond-reporting and NO screen-analysis implementation;
- records the result correctly: v2.6 GENERATED structural fixture reporting only for families A-F with controls and
  completeness-enforced non-authorizing guards but did NOT validate flat opponent-field geometry; outcome
  FLAT_OPPONENT_FIELD_SYNTHETIC_FIXTURE_REPORTING_GENERATED; flat_field_validated = False; protocol_ok means required
  fixture reports + controls + boundary + guards present ONLY, not validation / closure / descriptor validity / vision;
- records the breach-contract completeness result (§6): a missing family/control/boundary, a boundary lie
  (flat_field_validated True inside the boundary or a missing boundary field), any adoption or authorization flag
  missing or True, a claim lock moving True, flat_field_validated True, or a non-HOLD verdict each forces protocol_ok
  False / invalid_protocol_breach -- and that mutation probes confirmed this;
- states that v2.6 ADOPTS NO descriptor / coordinate system / metric / equation / threshold / control metric / pass-fail
  rule, redefines no TOL, expands no family, reopens no spectral group; families A-F are structural descriptions, not
  validity gates, and no family claims validation;
- reports the validation faithfully (85 targeted passed; full tests/research 498 passed; reporting generated;
  flat_field_validated False; locks False False False; verdict HOLD; mutation probes reject boundary lies /
  flat_field_validated True / non-HOLD verdict);
- keeps v1.x as FROZEN EVIDENCE and v2.x UNVALIDATED, leaves vision / descriptor validity / temporal order / closure /
  flat-field-superiority UNPROVEN, and makes NO recommendation to proceed into descriptors / coordinates / metrics /
  equations / thresholds / real clips / screen analysis / runtime / memory (recommends only Codex review -> commit ->
  HOLD, with any further direction a separate operator-gated docs-first decision);
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False), flat_field_validated = False, and verdict = HOLD; adds no §0 pointer and
  no tags.

Flag any adopted descriptor / coordinate system / metric / equation / threshold / control metric / pass-fail rule, any
TOL redefinition, any family expansion, any spectral reopening, any flat-geometry / screen-analysis / camera / live /
real-clip / runtime / memory authorization, any "Brainvision sees" / vision / descriptor-validity / temporal-order /
integration-readiness claim, any claim that flat opponent-field is validated, any recommendation to proceed into
descriptors / coordinates / metrics / equations / thresholds / real clips / screen analysis / runtime / memory, or any
claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, `flat_field_validated = False`, and the frozen verdict **HOLD** are
unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Synthetic Fixture Findings v2.6. Docs-only receipt of a
reporting/guard-only implementation. Opens no implementation lane; opens no classifier / neural / screen /
flat-geometry / real-clip / runtime / memory work; changes no frozen formula, gate, evaluator, or verdict; deletes or
weakens no control; redesigns no descriptor; invents no threshold; redefines no TOL; adopts no descriptor / coordinate
system / metric / equation / control metric / pass-fail rule; records the accepted flat opponent-field synthetic
fixture families A-F as GENERATED (structural fixture descriptions with controls and a generated-vs-validated
boundary) but the abstraction as UNVALIDATED and flat_field_validated False, with completeness-enforced adoption /
authorization guards; preserves v1.x as frozen evidence and v2.x as an unvalidated conceptual pivot; makes no vision /
"Brainvision sees" / descriptor-validity / temporal-order / memory / runtime / integration claim; recommends no move
into descriptors / coordinates / metrics / equations / thresholds / real clips / screen analysis / runtime / memory;
no `§0` pointer added; no tags.*
