# TORMENT Brainvision Flat Opponent-Field Symbolic Mutation Review v2.13

## 1. Status / Scope

**DOCS-ONLY adversarial mutation REVIEW.** This is a review note only. It opens **no** code, **no** tests, **no**
runtime, and **no** integration lane; it authorizes **no** implementation, **no** test, **no** expansion, **no**
validation, and **no** readiness claim, and it is not corrective. It sits over the accepted v2.12 edge (`811f603`) and
changes none of the accepted files.

**v2.13 reviews adversarial mutation classes only.** It examines the v2.9 symbolic representation guard surface
through an adversarial lens — incorporating the semantic boundaries fixed by v2.10 (stress synthesis), v2.11
(vocabulary drift audit), and v2.12 (null/control boundary review) — and asks which *semantic* mutations could pass as
"symbolic" while smuggling a descriptor, coordinate, metric, validation, screen-object, readiness, or vision claim.
It identifies the mutation classes that must remain blocked; it changes nothing and builds nothing.

**v2.13 authorizes no implementation, tests, expansion, or readiness claim.** It introduces and authorizes **no**
descriptor, coordinate system, numeric geometry, metric, null/control metric, equation, threshold, control metric,
pass/fail gate, validation, closure, screen analysis, real clip, camera / live / sensor / streaming path, runtime
path, memory path, prompt / context / action / render-body / autonomy contact, classifier (form B), or neural encoder
(form C), and it authorizes **no** vocabulary expansion. It makes **no** production vision claim, **no** "Brainvision
sees" claim, **no** temporal-order claim, and **no** descriptor-validity / geometry-validity / screen-readiness /
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

## 2. Why Mutation Review Matters

The v2.9 artifact is safe today because it is static, symbolic, canonically enforced, and conservatively guarded. But
safety is a property of *edits over time*, not just of the current file. A symbolic scaffold is an attractive place to
hide a claim precisely because it *looks* harmless: a new key here, a reworded boundary note there, one label swapped
for a more "descriptive" one, and the object still reads as "just symbols" while quietly carrying a coordinate, a
metric, or a validation result. Small edits are how a non-authorizing scaffold becomes a hidden claim carrier.

This review is therefore adversarial: it assumes a future editor (well-meaning or not) who wants the representation to
"say a little more," and asks what the smallest such changes would be and which must be rejected. For each mutation
class it records the risk, why it is dangerous, the rejection rule, and where the rejection must live — as a **protocol
breach** enforced by `check_protocol` (a code-level guard the current v2.9 checker already enforces or a future checker
must continue to enforce) or as a **docs-level rejection** (a boundary/interpretation that no checker can fully police
and that this review family must keep refusing). Naming both layers keeps the discipline explicit before any future
expansion.

## 3. Mutation Class Review

```text
Legend:  [PROTOCOL] = must be rejected by check_protocol as a breach (protocol_ok -> False).
         [DOCS]     = interpretation-level; no checker fully polices it; this review family must keep refusing it.
         [BOTH]     = the concrete form is a protocol breach AND the reading must also be refused at docs level.

--------------------------------------------------------------------------------------------------------------------
1. IDENTITY DRIFT                                                                                          [PROTOCOL]
   risk      : wrong A-F family_id; wrong family_label; extra family; missing family; label reworded to imply
               validation or a screen object.
   danger    : breaks "represents EXACTLY the six A-F families"; a reworded label can smuggle a claim into an
               allowed field.
   rejection : exactly the six canonical family keys; each family's family_id / family_label must equal the builder's
               canonical value; no extra, no missing.
   layer     : PROTOCOL -- v2.9 check_protocol enforces exact family set + canonical family_id/family_label; any future
               checker MUST keep this. (A reworded label is caught as noncanonical_family_field.)

2. VOCABULARY DRIFT                                                                                            [BOTH]
   risk      : canonical component/relation terms replaced with descriptor-like / geometry-like / visual-object-like /
               metric-like terms; or patch/field/gradient/boundary/region/contains/adjacent_to used to imply measured
               geometry.
   danger    : converts a naming vocabulary into an implied measurement (see v2.11 drift audit).
   rejection : component labels only from the closed ALLOWED_COMPONENTS set; relation labels only from the closed
               ALLOWED_RELATIONS set; canonical per-family component/relation lists must match the builder exactly.
   layer     : BOTH -- an out-of-set or non-canonical label is a PROTOCOL breach (forbidden_component/relation,
               noncanonical_family_field); the READING of an in-set term as measured geometry is a DOCS refusal (v2.11).

3. CLAIMING TEXT DRIFT                                                                                         [BOTH]
   risk      : boundary_notes / labels / note containing words implying validation, vision, screen analysis, object
               detection, segmentation, metric success, proof, pass/fail, readiness, learned category, or descriptor
               validity.
   danger    : an allowed STRING field is the easiest place to hide a claim in free text.
   rejection : the top-level note and each family's boundary_notes/label must equal the builder's canonical text
               (exact-equality, not substring-scanning) -- any claiming text differs from canonical and is rejected.
   layer     : BOTH -- canonical enforcement makes it a PROTOCOL breach (noncanonical_note / noncanonical_family_field);
               the general principle "no claiming text in a symbolic field" is also a DOCS invariant.

4. HIDDEN NUMERIC GEOMETRY                                                                                 [PROTOCOL]
   risk      : coordinates, grids, vectors, arrays, distances, angles, magnitudes, numeric gradients, topology scores,
               or numeric spatial fields anywhere in the object.
   danger    : any number is a measurement; numeric geometry is the core forbidden surface.
   rejection : no numeric value, no list-of-numbers, no nested structure; forbidden coordinate/vector/array/grid keys.
   layer     : PROTOCOL -- v2.9 value scan rejects int/float, numeric lists, and nested structures; key allow-list +
               forbidden-token scan reject coordinate/vector/array/grid keys; any future checker MUST keep this.

5. HIDDEN DESCRIPTOR / DATA PATH                                                                           [PROTOCOL]
   risk      : descriptor arrays, feature vectors, image data, screen data, real-clip data, pixel data, or
               camera/live/sensor/streaming references embedded in the object.
   danger    : smuggles form-B/descriptor content or a capture path into a "symbolic" object.
   rejection : family key allow-list (only the seven symbolic keys) + forbidden-token scan (descriptor/image/screen/
               clip/...) + value scan (no arrays); no data payloads of any kind.
   layer     : PROTOCOL -- v2.9 rejects such keys/values; any future checker MUST keep this. (Source-level: stdlib-only,
               no vision/data libraries.)

6. METRIC / PASS-FAIL DRIFT                                                                                [PROTOCOL]
   risk      : scores, thresholds, baselines, equations, control metrics, pass/fail gates, accuracy-like terms, or
               validation criteria added to the object.
   danger    : turns a representation into an evaluator; a metric or gate implies a measured, judged result.
   rejection : adoption flags (metric/threshold/control_metric/pass_fail_gate/... adopted) must stay present and False;
               forbidden metric/score/threshold keys rejected; no numeric values.
   layer     : PROTOCOL -- v2.9 enforces all adoption flags False + forbidden-token/value scans; any future checker MUST
               keep this.

7. NULL/CONTROL DRIFT                                                                                          [BOTH]
   risk      : null_control / has_null_control_role becoming a validation control, baseline, negative result,
               falsification, proof, or evidence that A-E are meaningful.
   danger    : "control" defaults to "evidence"; F silently validates A-E (see v2.12).
   rejection : F stays a symbolic role (canonical family_id/label/components/relations for F); no metric/baseline/score
               attaches; no comparison of A-E against F.
   layer     : BOTH -- concrete additions (a score/baseline on F, an extra key) are PROTOCOL breaches; the READING of F
               as a validation control / negative result / proof is a DOCS refusal (v2.12 N1-N6).

8. PROTOCOL INTERPRETATION DRIFT                                                                               [DOCS]
   risk      : protocol_ok = True misread as validation, correctness, visual completeness, readiness, or capability
               evidence.
   danger    : a green guard is treated as a passed test of the world.
   rejection : protocol_ok means BOUNDARY COMPLIANCE ONLY (see Section 4); it is never validation/correctness/readiness.
   layer     : DOCS -- no checker can police its own over-reading; this review family must keep refusing it. (v2.9 has
               no validation-positive label, which helps, but the reading is a docs invariant.)

9. OFFLINE BOUNDARY DRIFT                                                                                      [BOTH]
   risk      : any path toward torment_service/, runtime, memory, prompt/context/action/render-body/autonomy,
               screen/camera/live/sensor/streaming, real clips, classifier (form B), or neural (form C).
   danger    : leaves the offline research quarantine; the deepest boundary of the whole arc.
   rejection : stdlib-only, outside torment_service/, no such imports/paths; authorization guards
               (implementation_authorizes_* ) stay present and False.
   layer     : BOTH -- an import/path/authorized-True is a PROTOCOL/provenance breach (import test + authorization
               guards False); the intent to leave quarantine is also a DOCS refusal.

10. OUTCOME / VERDICT DRIFT                                                                                    [BOTH]
   risk      : outcome_label or verdict drifting toward PASS / validated / ready / complete / closed / any
               claim-opening language.
   danger    : re-labels a non-result as a result; moves the verdict off HOLD.
   rejection : outcome_label is sealed to FLAT_OPPONENT_FIELD_SYMBOLIC_REPRESENTATION_ONLY; verdict must equal HOLD;
               the label set carries no validation-positive form.
   layer     : BOTH -- a bad label/verdict is a PROTOCOL breach (bad_outcome_label / verdict_not_hold); introducing a
               claim-opening label is also a DOCS refusal.
--------------------------------------------------------------------------------------------------------------------
```

## 4. Protocol Semantics

```text
protocol_ok = True means BOUNDARY COMPLIANCE ONLY: the object is exactly the six canonical A-F symbolic families with
canonical labels/notes/components/relations, all locks/flags/guards present and False, no numeric/coordinate/vector/
array/descriptor/image/screen/clip/pass-fail/metric field, verdict HOLD, and the sealed outcome label.

protocol_ok = True does NOT mean:
  - validation, or geometry truth;
  - descriptor validity, or coordinate/metric validity;
  - visual structure validity, or visual completeness;
  - screen readiness, runtime readiness, memory readiness, or integration readiness;
  - vision, or "Brainvision sees";
  - that the null/control family "passed", or that A-E are meaningful.
A green guard proves what the object is NOT allowed to carry -- not that anything about the world is true.
```

## 5. Guard Surface Sufficiency

```text
Assessment: the v2.9 hardening DIRECTION is conceptually SUFFICIENT FOR NOW.

The current guard surface already enforces, at the protocol layer, the concrete forms of mutation classes 1, 2 (label
set), 3 (canonical text), 4, 5, 6, 9 (provenance/authorization), and 10 -- via: exact six-family set + canonical
family_id/label/notes/components/relations enforcement; closed component/relation label sets; a key allow-list +
forbidden-token scan; a value scan rejecting numbers, numeric lists, and nested structures; all claim locks / adoption
flags / authorization guards required present and False; a sealed outcome label; a required HOLD verdict; and
stdlib-only provenance. Classes 7 (null/control READING) and 8 (protocol_ok READING), and the interpretive halves of
2/3/9/10, are DOCS-level and are held by the v2.10-v2.12 review family plus Section 3 above.

This review proposes NO implementation change. If a future editor believes an additional guard is warranted (e.g. an
explicit deny-list refinement), that is a SEPARATELY APPROVED future possibility only -- it would require a docs-first
plan, a Codex review, and operator approval that names the exact change, what it must never become, and how every
claim lock and the generated-vs-validated separation are preserved. Nothing is authorized here; the branch stays HELD.
```

## 6. Future Pressure-Test Candidates

Docs-first candidates only; **none opened, none authorized, and none recommended for implementation here**. This
review recommends **no** direct descriptor, coordinate, metric, validation, screen, real-clip, runtime, memory,
neural, classifier, or vision work. Up to three possible docs-first directions the operator could choose from:

```text
A. v2.14 PROTOCOL GUARD SEMANTICS REVIEW (docs-only)
   Review, on paper, precisely what protocol_ok does and does not mean (boundary compliance vs correctness/evidence),
   and the invariants that keep a green guard from being read as a passed test. Adopts nothing; defines no metric.

B. v2.14 A-F FAMILY IDENTITY PRESERVATION AUDIT (docs-only)
   Audit, on paper, how the canonical A-F identity/content enforcement keeps the six families exactly six and exactly
   themselves, and where identity drift could still slip in. Adopts nothing; changes no code.

C. v2.14 SYMBOLIC REPRESENTATION NON-CLAIM INVARIANTS REVIEW (docs-only)
   Consolidate, on paper, the full set of non-claim invariants across v2.10-v2.13 into one reviewable list, so the
   "representation != validation/descriptor/coordinate/metric/screen/vision" discipline is stated in one place.
   Adopts nothing; builds nothing.
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

OUTCOME_LABEL: FLAT_OPPONENT_FIELD_SYMBOLIC_MUTATION_REVIEW_ONLY
```

v2.13 is a docs-only adversarial mutation review. It enumerates ten semantic mutation classes that could compromise
the v2.9 symbolic representation boundary — identity, vocabulary, claiming-text, numeric-geometry, descriptor/data,
metric/pass-fail, null/control, protocol-interpretation, offline-boundary, and outcome/verdict drift — and records for
each the risk, the danger, the rejection rule, and whether it must be rejected at the protocol layer or the docs
layer. It reaffirms that `protocol_ok = True` means boundary compliance only, assesses the current guard direction as
conceptually sufficient for now, and recommends the branch REMAIN HELD. It adopts, expands, and relaxes nothing. All
claim locks and the frozen verdict **HOLD** are preserved and unmoved.

## 8. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_SYMBOLIC_MUTATION_REVIEW_v2.13.md
(new, docs-only, untracked; over the accepted v2.12 edge 811f603).

Verify that this review:
- is docs-only and authorizes NO implementation, NO tests, NO expansion, NO validation, and NO readiness claim (no
  code / tests / schema, no torment_service/, no runtime, no memory, no camera / live / sensor / screen-capture /
  streaming, no real clips, no pixels / images); keeps form B (classifier) and form C (neural) CLOSED; opens no
  screen-analysis / numeric-geometry;
- frames the central question as WHICH semantic mutation classes could compromise the v2.9 symbolic representation
  boundary and what a future checker/review must continue to reject;
- reviews at least the ten required mutation classes (identity drift; vocabulary drift; claiming-text drift; hidden
  numeric geometry; hidden descriptor/data path; metric/pass-fail drift; null/control drift; protocol-interpretation
  drift; offline-boundary drift; outcome/verdict drift) and for EACH records: the mutation risk, why it is dangerous,
  the required rejection rule, and whether it must be a PROTOCOL breach (check_protocol) or a DOCS-level rejection;
- reaffirms (Section 4) that protocol_ok = True means BOUNDARY COMPLIANCE ONLY and NOT validation / geometry truth /
  descriptor validity / visual completeness / screen / runtime / memory / integration readiness / vision / null "pass"
  / A-E meaningfulness;
- assesses guard-surface sufficiency (Section 5) as conceptually sufficient for now and proposes NO implementation
  change except as a separately approved future possibility (docs-first plan + Codex review + operator approval);
- lists up to three docs-first next slices (v2.14 protocol guard semantics review / A-F family identity preservation
  audit / symbolic representation non-claim invariants review) and recommends NO descriptor / coordinate / metric /
  validation / screen / real-clip / runtime / memory / neural / classifier / vision work;
- preserves the locks and verdict (Section 7): flat_field_validated = False; first_pass_structure_validity_claim_allowed
  = False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  FLAT_OPPONENT_FIELD_SYMBOLIC_MUTATION_REVIEW_ONLY; interprets HOLD/HELD as held for analysis, not abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any authorized implementation / test / expansion, any adopted descriptor / coordinate / numeric geometry / metric
/ equation / threshold / control metric / pass-fail rule, any validation / segmentation / falsification / geometry-
validity claim, any screen / real-clip / camera / live / runtime / memory authorization, any classifier (B) / neural
(C) opening, any "Brainvision sees" / vision / descriptor-validity / temporal-order / readiness claim, any claim that
protocol_ok implies validation, any recommendation to expand, or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Symbolic Mutation Review v2.13. Docs-only adversarial mutation review.
Opens no implementation lane, no tests, and no expansion; opens no classifier / neural / screen / real-clip / runtime
/ memory work; adopts no descriptor / coordinate system / numeric geometry / metric / equation / threshold / control
metric / pass-fail rule; enumerates ten semantic mutation classes (identity / vocabulary / claiming-text / numeric-
geometry / descriptor-data / metric-pass-fail / null-control / protocol-interpretation / offline-boundary / outcome-
verdict drift) with risk, danger, rejection rule, and protocol-vs-docs layer per class; reaffirms protocol_ok = True as
boundary compliance only; assesses the current guard direction as conceptually sufficient for now; recommends the
branch REMAIN HELD; preserves all claim locks and the frozen verdict HOLD; makes no vision / "Brainvision sees" /
descriptor-validity / geometry-validity / temporal-order / readiness claim; outcome label
FLAT_OPPONENT_FIELD_SYMBOLIC_MUTATION_REVIEW_ONLY; no `§0` pointer added; no tags.*
