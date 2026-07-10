# TORMENT Brainvision Flat Opponent-Field Vocabulary Drift Audit v2.11

## 1. Status / Scope

**DOCS-ONLY vocabulary drift AUDIT.** This is an audit note only. It opens **no** code, **no** tests, **no** runtime,
and **no** integration lane; it authorizes **no** implementation and **no** expansion, and it is not corrective. It
sits over the accepted v2.10 edge (`d227312`) and changes none of the accepted files.

**v2.11 audits vocabulary drift only.** It examines the canonical symbolic vocabulary introduced by the v2.9
representation artifact and stress-synthesized by v2.10, and asks whether any label creates unacceptable pressure
toward a hidden descriptor, coordinate, geometry-validity, metric, screen-object, real-clip, validation, or vision
claim. It audits terms; it changes none of them, adds none, and removes none.

**v2.11 authorizes no implementation or expansion.** It introduces and authorizes **no** descriptor, coordinate
system, numeric geometry, metric, equation, threshold, control metric, pass/fail gate, validation, closure, screen
analysis, real clip, camera / live / sensor / streaming path, runtime path, memory path, prompt / context / action /
render-body / autonomy contact, classifier (form B), or neural encoder (form C), and it authorizes **no** vocabulary
expansion. It makes **no** production vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, and
**no** descriptor-validity / geometry-validity / screen-readiness / memory-readiness / runtime-readiness /
integration-readiness claim. Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per
v0.6. **HOLD / HELD means held for analysis and claim control — not abandoned.**

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

## 2. Why Vocabulary Drift Matters

A symbolic vocabulary is only as safe as the discipline that keeps each term a **name**. The v2.9 labels — `patch`,
`field`, `gradient`, `boundary`, `adjacent_to`, `contains`, `transitions_to`, and the rest — are ordinary vision /
geometry words used here in a deliberately narrowed, non-measured sense. That narrowing is fragile: the *default*
reading of every one of these words, in an imaging or perception context, is a measured quantity or a detected object.
If a later reader, doc, or artifact quietly restores the default reading, a label that was meant to *name* a family
becomes a hidden claim that the family was *measured*, *detected*, *validated*, or *seen*.

Drift is dangerous precisely because it needs no code change. It happens in interpretation: "`boundary`" starts to
imply an edge was detected; "`gradient`" starts to imply a numeric slope; "`region` + `contains`" starts to imply an
object was recognized. Each such slide silently converts a non-authorizing symbol into a geometry-validity, descriptor,
screen-object, or vision claim. This audit names, for each term, the allowed meaning, the specific drift to refuse, a
safe-use invariant, and a conservative risk level — so the discipline is explicit and reviewable before any future
expansion.

## 3. Audit Method

```text
For every component and relation label the audit records four things:
  1. Allowed meaning : the narrow SYMBOLIC meaning permitted in v2.9 (a name, never a measurement).
  2. Forbidden drift : the specific way the term could become a hidden descriptor / coordinate / metric / equation /
                       threshold / visual object / screen object / real-clip / validation / vision claim.
  3. Safe-use rule   : a short invariant for using the term WITHOUT opening any claim.
  4. Risk level      : Low / Medium / High -- how easily the term can be misread as geometry or validation.
Risk levels are CONSERVATIVE (biased toward the higher rating). A "High" rating is NOT a problem to fix by changing the
term; it is a flag that the term needs the most interpretive discipline. No term is authorized to carry any measured
meaning at any risk level.
```

## 4. Component Vocabulary Audit

```text
patch                                                                                      [risk: HIGH]
  allowed : names a single conceptual local opponent unit as a whole; a symbolic unit.
  drift   : -> a PIXEL PATCH / image tile / cropped segment carrying pixels or extent.
  safe    : "patch" names a symbolic unit only; holds no pixels, no coordinates, no extent, no data.

neighbor                                                                                   [risk: MEDIUM]
  allowed : names a conceptual "another patch beside this one" relation-bearing unit; symbolic.
  drift   : -> a grid/coordinate neighbor with a position or index.
  safe    : "neighbor" names a symbolic companion unit; it has no coordinate, index, or distance.

transition                                                                                 [risk: HIGH]
  allowed : names a conceptual change-of-content between opponent parts; symbolic.
  drift   : -> a MEASURED gradient, a numeric change rate, or a TEMPORAL transition over frames.
  safe    : "transition" names a symbolic change; it is not measured, not numeric, not over time.

boundary                                                                                   [risk: HIGH]
  allowed : names a conceptual limit between opponent parts; symbolic.
  drift   : -> a DETECTED EDGE / edge-map / edge-strength value.
  safe    : "boundary" names a symbolic limit; nothing is detected, located, or scored.

region                                                                                     [risk: HIGH]
  allowed : names a conceptual local scope; symbolic.
  drift   : -> a SEGMENTATION mask / segmented area with pixels or extent.
  safe    : "region" names a symbolic scope; it is not a segment, mask, or measured area.

field                                                                                      [risk: HIGH]
  allowed : names a conceptual global organization scope; symbolic.
  drift   : -> a NUMERIC / spatial field (an array of values over positions).
  safe    : "field" names a symbolic scope; it holds no values, no positions, no array.

gradient                                                                                   [risk: HIGH]
  allowed : names a conceptual smooth change; symbolic.
  drift   : -> a NUMERIC GRADIENT / derivative / slope value.
  safe    : "gradient" names a symbolic smoothness; it is not a number, slope, or derivative.

discontinuity                                                                              [risk: HIGH]
  allowed : names a conceptual abrupt change; symbolic.
  drift   : -> a DETECTED discontinuity / edge evidence / jump magnitude.
  safe    : "discontinuity" names a symbolic abruptness; nothing is detected or measured.

null_control                                                                               [risk: MEDIUM]
  allowed : names a conceptual neutral / matched non-opponent role; symbolic.
  drift   : -> a VALIDATION control / a baseline the representation is scored against.
  safe    : "null_control" names a symbolic role; it adjudicates nothing and is scored against nothing.

opponent_polarity_label                                                                    [risk: HIGH]
  allowed : names a conceptual opponent polarity as a LABEL (the "_label" is load-bearing); symbolic.
  drift   : -> a MEASURED color-channel polarity / a signed opponent-channel value (BY/RG measurement).
  safe    : "opponent_polarity_label" names a symbolic polarity label; no channel is read, computed, or measured.
```

## 5. Relation Vocabulary Audit

```text
adjacent_to                                                                                [risk: HIGH]
  allowed : names a conceptual "beside" relation between symbolic units; symbolic.
  drift   : -> COORDINATE GEOMETRY (positions, a lattice, a distance/adjacency computation).
  safe    : "adjacent_to" names a symbolic relation; it has no coordinate, distance, or lattice.

separates                                                                                  [risk: HIGH]
  allowed : names a conceptual "stands between" relation; symbolic.
  drift   : -> SEGMENTATION TRUTH (a proven split of measured content).
  safe    : "separates" names a symbolic relation; it proves no split and measures no content.

transitions_to                                                                             [risk: HIGH]
  allowed : names a conceptual directed change relation between symbolic parts; symbolic.
  drift   : -> a METRIC / equation / rate, or TEMPORAL dynamics over frames.
  safe    : "transitions_to" names a symbolic relation; it is not a rate, an equation, or over time.

contains                                                                                   [risk: MEDIUM]
  allowed : names a conceptual "scope holds this unit" relation; symbolic.
  drift   : -> OBJECT / region DETECTION (a recognized thing inside a measured area).
  safe    : "contains" names a symbolic relation; nothing is detected, recognized, or bounded in pixels.

contrasts_with                                                                             [risk: MEDIUM]
  allowed : names a conceptual "differs in opponent character" relation; symbolic.
  drift   : -> a MEASURED CONTRAST value / ratio.
  safe    : "contrasts_with" names a symbolic relation; no contrast is computed or scored.

has_boundary                                                                               [risk: HIGH]
  allowed : names a conceptual "has a limit" relation; symbolic.
  drift   : -> EDGE-DETECTION EVIDENCE (a found, located, or scored edge).
  safe    : "has_boundary" names a symbolic relation; no edge is found, located, or scored.

has_null_control_role                                                                      [risk: MEDIUM]
  allowed : names a conceptual "plays the null/control role" relation; symbolic.
  drift   : -> PASS/FAIL CONTROL LOGIC (a decision gate or accept/reject rule).
  safe    : "has_null_control_role" names a symbolic role relation; it drives no decision, gate, or rule.
```

## 6. Cross-Term Drift Risks

Individual terms can stay disciplined yet combine into an implied capability. The dangerous combinations:

```text
- patch + boundary          -> reads as SEGMENTATION (a bounded, measured patch). Refuse: both are symbolic names; a
                               named patch with a named boundary is not a segmented, located, or measured area.
- field + gradient          -> reads as NUMERIC FIELD GEOMETRY (a value array with a computed slope). Refuse: a named
                               field with a named gradient holds no values, positions, or derivatives.
- neighbor + adjacent_to    -> reads as a COORDINATE LATTICE (indexed cells with adjacency). Refuse: both are symbolic;
                               together they still carry no coordinate, index, distance, or lattice.
- null_control + contrasts_with -> reads as a VALIDATION CONTROL (a baseline the object is scored against). Refuse: the
                               null/control role and the contrast relation are symbolic; nothing is scored or adjudicated.
- region + contains         -> reads as OBJECT RECOGNITION (a recognized thing inside a segmented region). Refuse: both
                               are symbolic; a named region that names a contained unit recognizes and measures nothing.
- transition + discontinuity -> reads as EDGE / TEMPORAL EVIDENCE (a detected jump, or change over frames). Refuse: both
                               are symbolic; together they detect nothing, measure nothing, and imply no time axis.
```

## 7. Safe-Use Invariants

Invariant rules for the whole vocabulary. Each is a **non-implication** that must hold regardless of any future step:

```text
V1. symbolic TERM existence does NOT imply measured structure.
V2. RELATION label existence does NOT imply coordinate geometry.
V3. family vocabulary COMPLETENESS does NOT imply visual completeness.
V4. NULL/CONTROL vocabulary does NOT imply validation controls.
V5. CANONICAL vocabulary does NOT imply descriptor validity.
V6. NO term may be treated as a screen, pixel, object, segment, metric, coordinate, edge, or piece of evidence.
```

Any reading, doc, or artifact that violates an invariant above has left the accepted boundary and is inadmissible.

## 8. Expansion Recommendation

```text
Recommendation: REMAIN HELD.

The audit finds NO term that is safe to relax and NO combination that may be treated as measured structure. Several
terms carry HIGH interpretive-drift risk (patch, transition, boundary, region, field, gradient, discontinuity,
opponent_polarity_label, adjacent_to, separates, transitions_to, has_boundary) -- meaning they demand the most
discipline, NOT that the terms should change. Do NOT expand the representation, add vocabulary, or relax any term
until this drift audit has been reviewed by Codex AND the operator separately approves a bounded next plan that names
the exact next step, what it must never become, and how every claim lock and the generated-vs-validated separation are
preserved. No descriptor / coordinate / metric / equation / threshold / screen / real-clip / runtime / memory /
classifier (B) / neural (C) / vision work is recommended or authorized here. Held for analysis and claim control --
not abandoned.
```

## 9. Verdict

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

OUTCOME_LABEL: FLAT_OPPONENT_FIELD_VOCABULARY_DRIFT_AUDIT_ONLY
```

v2.11 is a docs-only vocabulary drift audit. It records, for each v2.9 component and relation label, the allowed
symbolic meaning, the forbidden drift, a safe-use invariant, and a conservative risk level; it addresses the dangerous
cross-term combinations; and it recommends the branch REMAIN HELD until Codex review and a separately approved bounded
plan. It adopts, expands, and relaxes nothing. All claim locks and the frozen verdict **HOLD** are preserved and
unmoved.

## 10. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_VOCABULARY_DRIFT_AUDIT_v2.11.md
(new, docs-only, untracked; over the accepted v2.10 edge d227312).

Verify that this audit:
- is docs-only and authorizes NO implementation, NO expansion, and NO vocabulary change (no code / tests / schema, no
  torment_service/, no runtime, no memory, no camera / live / sensor / screen-capture / streaming, no real clips, no
  pixels / images); keeps form B (classifier) and form C (neural) CLOSED; opens no screen-analysis / numeric-geometry;
- frames the central question as WHETHER the canonical symbolic vocabulary can remain safely non-authorizing, and
  audits EVERY v2.9 component label (patch, neighbor, transition, boundary, region, field, gradient, discontinuity,
  null_control, opponent_polarity_label) and EVERY relation label (adjacent_to, separates, transitions_to, contains,
  contrasts_with, has_boundary, has_null_control_role) with: allowed symbolic meaning, forbidden drift, safe-use rule,
  and a conservative risk level;
- explicitly addresses the required drift risks (patch->pixel/segment, neighbor->grid coordinate, transition->measured
  gradient/temporal, boundary->detected edge, region->segmentation, field->numeric/spatial field, gradient->numeric
  gradient, discontinuity->detected edge evidence, null_control->validation control, opponent_polarity_label->measured
  color-channel polarity, adjacent_to->coordinate geometry, separates->segmentation truth, transitions_to->metric/
  equation/temporal, contains->object/region detection, contrasts_with->measured contrast, has_boundary->edge-detection
  evidence, has_null_control_role->pass/fail control logic) and the cross-term risks (patch+boundary, field+gradient,
  neighbor+adjacent_to, null_control+contrasts_with, region+contains, transition+discontinuity);
- states the safe-use invariants (§7) as non-implications (term existence != measured structure; relation existence !=
  coordinate geometry; vocabulary completeness != visual completeness; null/control vocabulary != validation controls;
  canonical vocabulary != descriptor validity; no term is a screen/pixel/object/segment/metric/coordinate/edge/evidence);
- recommends the branch REMAIN HELD, expanding / relaxing no term until Codex review + a separately approved bounded
  plan; recommends NO descriptor / coordinate / metric / screen / real-clip / runtime / memory / neural / classifier
  work;
- preserves the locks and verdict (§9): flat_field_validated = False; first_pass_structure_validity_claim_allowed =
  False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  FLAT_OPPONENT_FIELD_VOCABULARY_DRIFT_AUDIT_ONLY; interprets HOLD/HELD as held for analysis, not abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any term relaxed or expanded, any adopted descriptor / coordinate / numeric geometry / metric / equation /
threshold / control metric / pass-fail rule, any validation / segmentation / edge-detection / geometry-validity claim,
any screen / real-clip / camera / live / runtime / memory authorization, any classifier (B) / neural (C) opening, any
"Brainvision sees" / vision / descriptor-validity / temporal-order / readiness claim, any recommendation to expand, or
any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Vocabulary Drift Audit v2.11. Docs-only audit. Opens no implementation
lane, no expansion, and no vocabulary change; opens no classifier / neural / screen / real-clip / runtime / memory
work; adopts no descriptor / coordinate system / numeric geometry / metric / equation / threshold / control metric /
pass-fail rule; audits every v2.9 component and relation label for drift toward descriptor / coordinate / metric /
segmentation / edge / screen / validation / vision claims and records allowed meaning, forbidden drift, safe-use rule,
and conservative risk per term plus the cross-term risks; recommends the branch REMAIN HELD absent a separately
approved bounded plan; preserves all claim locks and the frozen verdict HOLD; makes no vision / "Brainvision sees" /
descriptor-validity / geometry-validity / temporal-order / readiness claim; outcome label
FLAT_OPPONENT_FIELD_VOCABULARY_DRIFT_AUDIT_ONLY; no `§0` pointer added; no tags.*
