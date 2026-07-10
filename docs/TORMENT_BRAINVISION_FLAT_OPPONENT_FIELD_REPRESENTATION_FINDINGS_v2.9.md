# TORMENT Brainvision Flat Opponent-Field Representation Findings v2.9

## 1. Status / non-claims

**Findings for a STATIC SYMBOLIC, REPRESENTATION-ONLY implementation slice.** v2.9 is **offline research-only**. It
implements the smallest possible static symbolic representation of the existing v2.6/v2.7 flat opponent-field
synthetic fixture families A-F, under the accepted v2.8 boundary, and does nothing else. It sits over the accepted
v2.8 edge (`3701dc5`), stays outside `torment_service/`, and opens **no** runtime, memory, screen, camera, live,
sensor, streaming, real-clip, prompt / context / action / render-body / autonomy path.

**v2.9 is symbolic / static representation only. It does not validate geometry.** It does **not** adopt or define a
descriptor, a coordinate system, numeric geometry, a metric, an equation, a threshold, a control metric, a pass/fail
gate, validation, a screen path, a runtime path, a memory path, a classifier (form B), a neural encoder (form C), a
real-clip path, or vision. It carries **no** x/y / grid / pixel coordinates, **no** vectors, **no** arrays implying
image / descriptor data, **no** numeric distances / gradients, **no** formulas / equations / thresholds / scores /
metrics, **no** classifier features, **no** descriptor arrays, **no** image / screen / real-clip data, and **no**
pass/fail evaluation. It makes **no** production vision claim, **no** "Brainvision sees" claim, **no** temporal-order
claim, **no** descriptor-validity claim, **no** geometry-validity claim, and **no** screen-readiness /
memory-readiness / runtime-readiness / integration-readiness claim. Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6. **HOLD / HELD means held for analysis and claim control —
not abandoned.**

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

## 2. Relation to v2.6-v2.8

```text
v2.6  generated/reporting-only STRUCTURAL FIXTURE DESCRIPTIONS for six families A-F (with controls + guards).
v2.7  docs-only conceptual REPRESENTATION PLAN: planned whether A-F could later be represented as bounded symbolic /
      spatial structures while preserving generated-vs-validated separation.
v2.8  docs-only BOUNDARY REVIEW: fixed the exact boundary a future minimal representation artifact must respect;
      conditionally allowed a strictly static / symbolic / offline / non-authorizing slice, separately approved.
v2.9  (3701dc5 boundary) SYMBOLIC REPRESENTATION IMPLEMENTATION: the smallest static symbolic representation of A-F,
      built and tested under exactly the v2.8 boundary.
v2.9  (this doc) findings: records what v2.9 implemented and did NOT establish.
```

v2.9 is the first *implemented* step past reporting: it names the A-F fixture families as static symbolic objects. It
does not validate flat opponent-field geometry, adopt a descriptor, or select any representation over data, and it
changes nothing v1.x froze or v2.0-v2.8 produced.

## 3. What v2.9 implemented

`research/brainvision/flat_opponent_field_representation_v2_9.py` exposes a deterministic
`build_flat_opponent_field_representation_v2_9()` returning a static symbolic report, plus a conservative, CANONICAL
`check_protocol()` (it enforces the note and each family's identity/label/notes/components/relations against the
builder's approved static values, so claiming or forbidden text in an allowed string field and any A-F identity drift
are rejected). The report carries `version = "v2.9"`, `representation_only = True`, `offline_research_only =
True`, `symbolic_static_only = True`, `flat_field_validated = False`, `verdict = "HOLD"`, and `outcome_label =
FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY`, and represents **exactly** the six families:

```text
A_uniform_opponent_patches         id A   components [patch, region, opponent_polarity_label]           relations [contains]
B_adjacent_opponent_patches        id B   components [patch, neighbor, region, opponent_polarity_label] relations [adjacent_to, contrasts_with]
C_gradient_fields                  id C   components [field, gradient, transition, region]              relations [transitions_to, contains]
D_edge_discontinuity_fields        id D   components [field, boundary, discontinuity, region]           relations [has_boundary, separates, contrasts_with]
E_region_field_separation_fixtures id E   components [region, field]                                    relations [separates, contains]
F_null_control_fields              id F   components [null_control, field]                              relations [has_null_control_role]
```

Each family is a static symbolic object with only the symbolic keys `family_id / family_label /
conceptual_components / conceptual_relations / boundary_notes / fixture_represented = True /
representation_validated = False`. Component labels are drawn only from {patch, neighbor, transition, boundary,
region, field, gradient, discontinuity, null_control, opponent_polarity_label}; relation labels only from
{adjacent_to, separates, transitions_to, contains, contrasts_with, has_boundary, has_null_control_role}. The report
also carries the claim-lock, adoption-flag, and authorization-guard groups, all present and False. There are **no**
numbers, coordinates, vectors, arrays, descriptors, metrics, thresholds, or pass/fail fields anywhere in the object.

## 4. Validation summary

```text
focused v2.9 tests    : 48 passed
v2.9 script           : version v2.9 ; representation_only/offline/symbolic_static True ;
                        outcome_label FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY ;
                        flat_field_validated False ; verdict HOLD ; protocol_ok True ; breaches []
mutation probes       : 28 probes each flip protocol_ok -> False (see §6)
full tests/research    : 546 passed
```

The tests assert only platform-independent robust facts: stdlib-only imports (no `torment*` / service, no numeric /
vision libraries); exactly six families A-F; every family symbolic/static (component/relation labels from the allowed
closed sets; no numeric, vector, array, nested, coordinate, metric, descriptor, image, screen, real-clip, or pass/fail
fields); every family `fixture_represented = True` and `representation_validated = False`; all claim locks, adoption
flags, and authorization guards present and False; `flat_field_validated = False`; `verdict = HOLD`; the conservative
label; canonical enforcement (the top-level note and each family's identity/label/notes/components/relations must
match the builder's approved static values, so claiming or forbidden text in an allowed string field, or any A-F
identity/content drift, is rejected); `protocol_ok = True` with empty breaches for the clean report; each of the 28
mutation probes flipping `protocol_ok = False`; and deterministic output. Windows pytest is the source of truth (the
one Linux-sandbox
`spectral_centroid` knife-edge in the unrelated v1.8 audit is Windows-green and independent of this slice).

## 5. Main result

```text
OUTCOME_LABEL: FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY
               flat_field_validated = False     verdict = HOLD     protocol_ok = True (presence/symbolic-only)

fixture families A-F : represented as STATIC SYMBOLIC objects; each fixture_represented=True, representation_validated=False
claim locks (10)     : all present and False
adoption flags (12)  : all present and False
authorization guards : all present and False
```

**v2.9 successfully built a static symbolic representation of the A-F fixture families and its conservative protocol
checker admits it, but it did not validate flat opponent-field geometry.** The outcome is
**`FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY`** with **`flat_field_validated = False`**: the symbolic
representation exists and is admissible, but nothing about the abstraction has been measured, tested, or validated.
Naming the structure moves **no** claim lock and **no** verdict.

## 6. Protocol / breach completeness

```text
check_protocol() returns protocol_ok = True with breaches = [] ONLY when every constraint holds; it is conservative
(if uncertain, it marks a breach). It flips to protocol_ok = False on ANY of the probed conditions:
  - missing required fixture family / extra fixture family;
  - a family missing its symbolic representation (empty components);
  - representation_validated set True (any family);
  - flat_field_validated set True; verdict != HOLD;
  - any claim lock True; any adoption flag True; any authorization guard True;
  - forbidden numeric-geometry / coordinate / vector / array fields;
  - forbidden descriptor / image / screen / real-clip fields;
  - forbidden pass/fail / score / metric / threshold / equation fields (by key allow-list, forbidden-token scan, and
    a value scan that rejects any number, vector, array, or nested structure);
  - CANONICAL drift: the top-level note, or any family's family_id / family_label / boundary_notes /
    conceptual_components / conceptual_relations, differing from the builder's approved static values -- this rejects
    claiming/forbidden TEXT inside an allowed string field (e.g. "validates geometry", "Brainvision sees", or
    coordinate/score/threshold/descriptor text) and any A-F identity/content drift (wrong id/label, allowed-but-wrong
    components, empty/reordered relations), which a substring scan of negated "no metric" notes could not do safely;
  - any extra top-level field, bad version, or bad outcome label.
All 28 mutation probes were exercised in tests and each forced invalid protocol (protocol_ok False, >=1 breach).
```

## 7. Interpretation

```text
- v2.9 is the FIRST implemented step past reporting: the A-F families designed (v2.4/v2.4a), boundary-fixed (v2.5),
  reported (v2.6), planned (v2.7), and boundary-reviewed (v2.8) are now NAMED as static symbolic objects that, by
  construction, carry no number / coordinate / descriptor / metric and cannot silently smuggle one in.
- The representation names a DESIGN, not a MEASUREMENT: v2.9 confirms the A-F families are expressible as bounded
  symbolic objects. It says NOTHING about whether the flat opponent-field abstraction is valid, better, or "sees".
- The symbolic objects are REPRESENTATIONS, not validity evidence: protocol_ok = presence of the required symbolic
  families + guards; it is NOT validation, closure, descriptor validity, geometry validity, or a vision claim.
- The abstraction remains UNVALIDATED: there is no measured fixture, no descriptor, no metric, and no test of whether
  the named structure is actually present or correct -- only that the symbolic naming of it exists.
```

## 8. Why this is not validation

```text
- VALIDATION would require testing whether the abstraction actually REPRESENTS opponent structure better -- over
  measured content, with a represented notion of "better". v2.9 has NO measurement, NO descriptor, NO metric, NO
  coordinate; it only names families and relations as symbols.
- Symbolic RELATION existence (adjacent_to / separates / transitions_to) is NAMING, not geometric truth; guard
  presence proves non-authorization, not correctness; representation existence is not a descriptor / metric /
  coordinate / validation.
- Nothing was measured or evaluated: the objects carry symbolic labels and two boolean markers, no values over data,
  no pass/fail. flat_field_validated is False and the label set carries no validation-positive form.
```

## 9. What remains frozen / unproven

```text
- v1.x remains FROZEN EVIDENCE; v2.0-v2.9 remain an UNVALIDATED conceptual pivot; forms B (classifier) and C (neural)
  stay CLOSED; no TOL redefinition, no descriptor / coordinate / metric / equation / threshold adoption, no spectral
  reopening, no generator-family expansion, no screen / real-clip / camera / live / runtime / memory path.
- Still UNPROVEN: vision; "Brainvision sees"; descriptor validity; geometry validity; temporal order; real-video
  understanding; a unique real-world color-structure advantage; memory / runtime / integration / screen readiness;
  closure (the BY gap is visible, not closed, in the fixture route); that flat opponent-field is better / valid (the
  symbolic representation exists; the abstraction is UNVALIDATED).
- Claim locks and verdict HOLD remain in force. v2.9 changed none of the above; this findings note changes none of it.
```

## 10. Recommended next step

**Recommend only: Codex review of this slice, then operator commit, then HOLD.** v2.9 shows the A-F families are
expressible as static symbolic objects with a conservative non-authorizing checker; this findings note records that
and nothing more. **No further implementation branch is recommended or authorized here** — the abstraction stays
HELD / HOLD, and any future direction (a richer representation, or anything touching descriptors / coordinates /
metrics / validation / screen / runtime / memory / vision) is a **separate, operator-gated, docs-first decision**, not
a step this note endorses.

```text
1. Codex review THIS findings note + the v2.9 implementation and tests (over committed edge 3701dc5).
2. If accepted, the operator commits the three v2.9 files. No §0 pointer; no tags.
3. No descriptor / coordinate / numeric-geometry / metric / equation / threshold / control-metric / pass-fail /
   validation / screen / real-clip / runtime / memory / classifier (B) / neural (C) / vision work is recommended or
   authorized here; the line stays HELD / HOLD pending a separate operator decision.
```

Claim locks and verdict are unchanged: `flat_field_validated = False`;
`first_pass_structure_validity_claim_allowed = False`; `temporal_claim_allowed = False`;
`descriptor_validity_claim_allowed = False`; `verdict = HOLD`.

## 11. Codex review prompt

```text
Please review the v2.9 flat opponent-field SYMBOLIC REPRESENTATION slice (new, over committed edge 3701dc5):
  research/brainvision/flat_opponent_field_representation_v2_9.py
  tests/research/test_brainvision_flat_opponent_field_representation_v2_9.py
  docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_REPRESENTATION_FINDINGS_v2.9.md

Verify that this slice:
- is offline research-only, OUTSIDE torment_service/, stdlib-only (no torment* / service, no numeric / vision
  libraries); opens no runtime / memory / screen / camera / live / sensor / streaming / real-clip / prompt / context /
  action / render-body / autonomy path; keeps form B (classifier) and form C (neural) CLOSED;
- is REPRESENTATION ONLY and does NOT validate geometry: represents EXACTLY the six A-F families as STATIC SYMBOLIC
  objects (family_id / family_label / conceptual_components / conceptual_relations / boundary_notes /
  fixture_represented=True / representation_validated=False), with component labels only from {patch, neighbor,
  transition, boundary, region, field, gradient, discontinuity, null_control, opponent_polarity_label} and relation
  labels only from {adjacent_to, separates, transitions_to, contains, contrasts_with, has_boundary,
  has_null_control_role};
- adopts / defines NO descriptor, coordinate system, numeric geometry, metric, equation, threshold, control metric,
  pass/fail gate, or validation; carries NO x/y / grid / pixel coordinates, vectors, arrays, numeric distances /
  gradients, formulas, scores, classifier features, descriptor arrays, image / screen / real-clip data, or pass/fail
  evaluation anywhere in the object;
- preserves outcome_label = FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY; flat_field_validated = False;
  verdict = HOLD; and all claim locks / adoption flags / authorization guards present and False;
- has a CONSERVATIVE, CANONICAL check_protocol() that returns protocol_ok=True with empty breaches ONLY when every
  constraint holds and flips to False on: missing / extra family, missing symbolic representation,
  representation_validated True, flat_field_validated True, verdict != HOLD, any claim lock / adoption flag /
  authorization guard True, any forbidden coordinate / metric / score / threshold / descriptor / image / screen /
  real-clip / vector / array / numeric field, AND any canonical drift (the top-level note or any family's
  family_id / family_label / boundary_notes / conceptual_components / conceptual_relations differing from the
  builder's approved static values -- rejecting claiming/forbidden TEXT in an allowed string field and any A-F
  identity/content drift) -- and that the tests exercise all of these (48 focused passed incl. 28 mutation probes;
  full tests/research 546 passed; deterministic output);
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim; recommends no move into descriptors / coordinates / metrics / validation / screen
  / runtime / memory / vision (only Codex review -> commit -> HOLD, any further direction a separate operator-gated
  decision).

Flag any adopted descriptor / coordinate / numeric geometry / metric / equation / threshold / control metric /
pass-fail rule, any coordinates / vectors / arrays / numbers in the representation, any validation / closure /
geometry-validity claim, any screen / real-clip / camera / live / runtime / memory authorization, any classifier (B) /
neural (C) opening, any "Brainvision sees" / vision / descriptor-validity / temporal-order / readiness claim, any
claim that representation implies validation, or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Representation Findings v2.9. Findings for a static symbolic,
representation-only implementation slice. Opens no runtime / memory / screen / real-clip / classifier / neural work;
adopts no descriptor / coordinate system / numeric geometry / metric / equation / threshold / control metric /
pass-fail rule; represents EXACTLY the A-F fixture families as static symbolic objects with a conservative
non-authorizing protocol checker; does not validate geometry; preserves flat_field_validated False, all claim locks
False, and the frozen verdict HOLD; makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
temporal-order / memory / runtime / integration claim; outcome label FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY;
no `§0` pointer added; no tags.*
