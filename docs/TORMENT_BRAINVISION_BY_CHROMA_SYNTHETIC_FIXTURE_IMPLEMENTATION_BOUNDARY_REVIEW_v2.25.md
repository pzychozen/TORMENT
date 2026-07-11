# TORMENT Brainvision BY/Chroma Synthetic Fixture Implementation Boundary Review v2.25

## 1. Status / Scope

**DOCS-ONLY implementation-boundary REVIEW.** This is a review note only. It opens **no** code, **no** tests, **no**
runtime, and **no** integration lane; it authorizes **no** implementation by itself, and it is not corrective. It sits
over the accepted v2.24 edge (`docs(research): propose by chroma fixture families`) and changes none of the accepted
files.

**v2.25 reviews whether a FUTURE v2.26 may safely create a reporting-only synthetic fixture-family artifact** for the
six v2.24 BY/chroma conceptual family roles (A BY-dominant residual, B generic chroma proxy, C matched non-BY chroma,
D BY/chroma entangled, E fixture-family artifact, F null/reporting-boundary). It **conditionally** allows a future
v2.26 **only if** that artifact stays strictly within reporting-only, finite-family, non-metric, non-validating
boundaries — and even then only after separate Codex review and operator approval. It reviews a boundary; it
implements nothing.

**v2.25 authorizes nothing by itself.** It introduces and authorizes **no** descriptor adoption, coordinate adoption,
numeric geometry, metric, equation, threshold, scoring, pass/fail gate, validation, closure, real clip, screen /
camera / live / sensor / streaming path, runtime path, memory path, prompt / context / action / render-body / autonomy
contact, classifier (form B), or neural encoder (form C). It makes **no** production vision claim, **no** "Brainvision
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

## 2. v2.22 / v2.23 / v2.24 Boundary Preserved

```text
PRIMARY QUESTION (v2.22 Formulation A) -- in force:
  "Can future synthetic design distinguish BY-axis residual behavior from generic chroma proxy effects without adopting
   metrics or closure claims?"
MANDATORY NON-CLAIM CONSTRAINT (v2.22 Formulation C) -- in force:
  "Residual localization must not imply descriptor validity."

v2.23 fixed what a future fixture-design document may/may not contain (conceptual roles only; no fixtures, data
structures, formulas, metrics, thresholds, expected outputs, or pass/fail criteria).
v2.24 proposed SIX finite conceptual family ROLES (A-F), reporting-only, with Role D encoding that the residual may NOT
be separable at all, Role E making the fixtures-may-manufacture-the-effect suspicion first-class, and Role F carrying
the v2.12 anti-claim scaffold. v2.24 defined NO concrete fixtures / data / metrics / scores / thresholds.

STILL PRESERVED: reporting-only language (distinguish/isolate/separate = "report whether a distinction can be POSED",
never scored); descriptor-validity boundary (localization != descriptor works); no-metric boundary; no-validation
boundary; no-screen/runtime boundary; prior BY/color/chroma evidence FROZEN unresolved; the flat opponent-field
symbolic scaffold as DISCIPLINE not validation. v2.25 stays inside all of it.
```

## 3. Central Boundary Question

```text
Can v2.26 safely implement a DETERMINISTIC, REPORTING-ONLY artifact for the six v2.24 family roles WITHOUT introducing
concrete fixture data, descriptors, coordinates, metrics, scores, thresholds, validation, screen/runtime/memory paths,
classifier/neural paths, or vision claims?

Answer posture: CONDITIONALLY YES -- a v2.26 could be safe IF AND ONLY IF it is a static symbolic role-reporting
artifact of exactly the six roles, guarded by a conservative canonical checker, carrying every claim lock False, with
no numeric / data / metric surface -- and only after separate Codex review and operator approval. Absent every
condition (Section 6), the answer is NO and the branch stays HELD.
```

## 4. Allowed Future v2.26 Shape

If — and only if — separately approved (Section 6), a future v2.26 could be limited to a **static, symbolic,
reporting-only role artifact**, modeled on the accepted v2.9 pattern (a deterministic builder + a conservative
canonical `check_protocol`), but over the six BY/chroma ROLES instead of the flat-field families:

```text
- OFFLINE research-only, OUTSIDE torment_service/, under research/brainvision/ + tests/research/, HELD per v0.6.
- A deterministic build function returning a static symbolic report for EXACTLY the six roles A-F (no more, no fewer).
- Each role object carries SYMBOLIC LABELS ONLY: a role id / role label; a conceptual purpose STRING (canonical, from
  v2.24); a small closed set of conceptual DESCRIPTION labels (e.g. "reporting_focus", "proxy_confound",
  "non_by_chroma", "entangled", "artifact_suspicion", "null_boundary"); an explicit reporting-only marker; and the two
  booleans role_reported = True / role_validated = False.
- A conservative, CANONICAL check_protocol that returns protocol_ok = True / breaches = [] ONLY when: exactly the six
  roles are present; each role's id / label / purpose / description-labels match the builder's canonical values; all
  claim locks / adoption flags / authorization guards are present and False; no forbidden numeric / coordinate /
  vector / array / descriptor / metric / score / threshold / data field appears; role_validated is False everywhere;
  verdict is HOLD; and the outcome label is the sealed conservative label.
- A CONSERVATIVE outcome label with NO validation-positive form (e.g. BY_CHROMA_ROLE_REPORTING_ONLY).
- DETERMINISTIC, symbolic output; NO data, NO image, NO capture, NO measurement.
- Preserves generated-vs-validated separation and every claim lock and the HOLD verdict.
```

This shape REPORTS the six roles as static symbolic objects — it names what each role is for, and nothing more. It is
the role analogue of the v2.9 flat-field symbolic artifact: a naming, not a measurement.

## 5. Forbidden Future v2.26 Shape

A future v2.26 would be **inadmissible** if it contains any of the following. This list is exhaustive of the
disqualifying openings:

```text
- concrete FIXTURE DATA / fixture instances / a fixture bank / generated content; any actual BY/chroma stimulus;
- DATA STRUCTURES carrying values: arrays, vectors, matrices, tensors, images, pixel data;
- coordinates (x/y/grid/pixel), positions, distances, angles, magnitudes, numeric gradients, numeric geometry;
- DESCRIPTORS / feature vectors / descriptor arrays; any descriptor-validity content (form B);
- neural encodings / embeddings (form C);
- METRICS, scores, thresholds, weights, ratios, margins, ceilings, floors, equations, comparison functions;
- PASS/FAIL gates, acceptance criteria, "separation" scores, "distinguishability" scores;
- VALIDATION, closure, "the residual is distinct", "the proxy is controlled", "not an artifact", "the null passed";
- role_validated = True (any role); flat_field_validated = True; any claim lock / adoption flag / authorization guard
  True; a non-HOLD verdict; a non-conservative / validation-positive outcome label;
- any screen / real-clip / camera / live / sensor / streaming / runtime / memory / prompt / context / action /
  render-body / autonomy path; any torment_service/ touch; anything read as production vision or "Brainvision sees".
```

If a proposed v2.26 needs any item above to express a role, it is out of bounds and this review does not contemplate
it.

## 6. Guard Requirements for v2.26 (mandatory conditions)

```text
A future v2.26 is CONDITIONALLY safe to pursue IF AND ONLY IF, together:
  (1) it is strictly the Section-4 ALLOWED shape (static symbolic role reporting of exactly six roles) and contains
      NONE of the Section-5 FORBIDDEN shape;
  (2) it is offline research-only, outside torment_service/, stdlib-only, deterministic;
  (3) it carries a CONSERVATIVE, CANONICAL check_protocol whose green result means BOUNDARY COMPLIANCE ONLY (per
      v2.14) -- exactly six roles; canonical role id/label/purpose/description-labels; all claim locks / adoption flags
      / authorization guards present and False; no forbidden numeric/data/metric/descriptor field; role_validated
      False; verdict HOLD; sealed conservative label -- and that flips protocol_ok False (breach) on ANY violation,
      including canonical drift, claiming text in a role string, a numeric/data/metric field, an extra/missing role,
      role_validated True, a moved lock, or a bad label/verdict;
  (4) it preserves the v2.22 primary question and the Formulation-C descriptor-validity constraint, and encodes Role D
      (the residual may be inseparable) and Role E (artifact suspicion; "not an artifact" may never be concluded) and
      Role F (anti-claim boundary) HONESTLY -- none may be softened into a positive result;
  (5) it is preceded by a SEPARATE, explicit operator approval AND a Codex review of a dedicated v2.26 implementation
      PLAN before any code or test is written.

If any one of (1)-(5) is not met, v2.26 is NOT recommended and the branch stays HELD. This review starts no v2.26.
```

## 7. Conditional Recommendation

```text
RECOMMEND (conditional): a future v2.26 MAY implement a reporting-only BY/chroma role artifact -- IF AND ONLY IF it
meets every Section-6 condition and is separately Codex-reviewed and operator-approved. This is a GATE, not a green
light: absent all five conditions, v2.26 is not recommended and the branch stays HELD.

The recommendation is deliberately narrow. A v2.26 role artifact would advance the line one honest notch -- from
PROPOSING six roles (v2.24) to REPORTING them as guarded static symbolic objects -- while still measuring nothing,
separating nothing, and validating nothing. It would NOT answer the v2.22 question (it cannot: naming roles is not
distinguishing residual from proxy), and it must not be read as progress toward doing so.

v2.25 does NOT recommend, and does NOT authorize: descriptor / coordinate / numeric-geometry / metric / equation /
threshold / scoring / pass-fail / validation / closure / real-clip / screen / runtime / memory / classifier (B) /
neural (C) / vision work. It is NOT self-authorizing: the operator decides whether v2.26 opens at all.
```

## 8. Forbidden Drift Register

Drifts that any future v2.26 (and any reading of this review) must refuse:

```text
- role REPORTING becoming role VALIDATION (role_reported=True read as "the role is real/valid").
- static symbolic role becoming CONCRETE FIXTURE / data / stimulus.
- description LABEL becoming a DESCRIPTOR / feature / measured quantity.
- "distinguish / separate / matched / entangled" becoming a SCORED or MEASURED term.
- generic proxy role becoming a SOLVED / CONTROLLED proxy; artifact role becoming "not an artifact".
- null/boundary role becoming a VALIDATION CONTROL / passed baseline.
- protocol_ok=True becoming VALIDATION / correctness / distinguishability / readiness (v2.14).
- six-role completeness becoming VALIDATION COVERAGE or a VISUAL / classifier / neural ontology.
- reporting-only artifact becoming an IMPLEMENTATION LICENCE beyond exactly the Section-4 shape.
- residual localization becoming DESCRIPTOR VALIDITY; isolation becoming CLOSURE; falsification becoming VALIDATION.
```

## 9. Non-Claim Interpretation

```text
WHAT v2.25 MAY ESTABLISH (and only this):
  - a CONDITIONAL boundary under which a future v2.26 reporting-only role artifact could be pursued;
  - the ALLOWED / FORBIDDEN shape and the mandatory guard conditions for that artifact;
  - a gated, operator-decided candidate for the next slice.

WHAT IT DOES NOT ESTABLISH:
  not an implementation      not a fixture / data / metric        not a descriptor / coordinate
  not validation             not closure                          not that the residual is distinguishable
  not readiness              not vision                           not authorization of anything by itself

Even a fully-approved, fully-guarded v2.26 would REPORT six roles as static symbolic objects -- never measure,
separate, validate, or see anything.
```

## 10. Verdict

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

OUTCOME_LABEL: BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_IMPLEMENTATION_BOUNDARY_REVIEW_ONLY
```

v2.25 is a docs-only implementation-boundary review. It preserves the v2.22 primary question and Formulation-C
constraint and the v2.23/v2.24 boundaries; defines the allowed shape of a future v2.26 reporting-only role artifact (a
deterministic static symbolic report of exactly the six roles + a conservative canonical check_protocol + a sealed
conservative label), the forbidden shape, and the five mandatory guard conditions; conditionally recommends v2.26 only
if every condition is met and it is separately Codex-reviewed and operator-approved; registers the forbidden drifts;
and states the non-claim interpretation. It authorizes nothing by itself and is not self-authorizing. All claim locks
and the frozen verdict **HOLD** are preserved and unmoved.

## 11. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_IMPLEMENTATION_BOUNDARY_REVIEW_v2.25.md
(new, docs-only, untracked; over the accepted v2.24 edge "docs(research): propose by chroma fixture families").

Verify that this review:
- is docs-only and authorizes NOTHING by itself (no code / tests / schema, no torment_service/, no runtime, no memory,
  no camera / live / sensor / screen-capture / streaming, no real clips, no pixels / images); keeps form B (classifier)
  and form C (neural) CLOSED; opens no screen-analysis / numeric-geometry; implements nothing;
- frames the central question as WHETHER a future v2.26 may safely implement a DETERMINISTIC, REPORTING-ONLY artifact
  for the six v2.24 roles WITHOUT concrete fixture data / descriptors / coordinates / metrics / scores / thresholds /
  validation / screen-runtime-memory / classifier-neural / vision;
- preserves the v2.22 primary question (Formulation A) and mandatory non-claim constraint (Formulation C), and the
  v2.23 (conceptual-only) and v2.24 (six reporting-only roles; Role D inseparability, Role E artifact-suspicion, Role F
  anti-claim boundary) boundaries;
- specifies the ALLOWED future v2.26 shape as a STATIC SYMBOLIC, reporting-only role artifact modeled on v2.9 (a
  deterministic builder + a conservative canonical check_protocol) over EXACTLY the six roles, with symbolic labels
  only (role id/label, canonical purpose string, closed description labels, reporting-only marker, role_reported=True /
  role_validated=False), a sealed CONSERVATIVE outcome label, deterministic symbolic output, and preserved locks;
- specifies the FORBIDDEN future v2.26 shape exhaustively (concrete fixture data / instances / bank; arrays / vectors /
  images / pixels; coordinates / numeric geometry; descriptors / feature vectors; neural encodings; metrics / scores /
  thresholds / equations / comparison functions; pass-fail / acceptance / separation scores; validation / closure /
  "residual is distinct" / "proxy controlled" / "not an artifact" / "null passed"; role_validated True / any lock True
  / non-HOLD verdict / non-conservative label; screen / real-clip / camera / live / runtime / memory / torment_service);
- states the five MANDATORY guard conditions (allowed-shape-only + none-forbidden; offline/outside-service/stdlib/
  deterministic; conservative canonical check_protocol = boundary-compliance-only that breaches on ANY violation
  including canonical drift / claiming text / numeric-data-metric field / extra-missing role / role_validated True /
  moved lock / bad label-verdict; honest Role D/E/F; SEPARATE operator approval + Codex review of a dedicated v2.26
  plan before any code) and makes v2.26 CONDITIONAL on all five;
- conditionally recommends v2.26 ONLY under all conditions, as a GATE not a green light, explicitly noting a v2.26
  would NOT answer the v2.22 question and must not be read as progress toward it; recommends NO descriptor / coordinate
  / metric / validation / screen / real-clip / runtime / memory / classifier / neural / vision work; is NOT
  self-authorizing;
- registers the forbidden drifts and states the non-claim interpretation (may establish ONLY a conditional boundary +
  allowed/forbidden shape + mandatory conditions + a gated candidate; does NOT establish implementation / fixture /
  data / metric / descriptor / validation / closure / distinguishability / readiness / vision / authorization);
- preserves the locks and verdict (Section 10): flat_field_validated = False; first_pass_structure_validity_claim_allowed
  = False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_IMPLEMENTATION_BOUNDARY_REVIEW_ONLY; interprets HOLD/HELD as held for
  analysis, not abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any concrete fixture / data / array / image / coordinate / descriptor / metric / score / threshold / equation
defined anywhere; any UNCONDITIONAL authorization of v2.26; any allowed-shape element that carries a number, a datum, a
measurement, or a validation-positive label; any softening of Role D / E / F into a positive result; any
"distinguish/separate/matched/entangled" used as a scored term; any proxy/artifact treated as controlled or ruled out;
any "not an artifact" / "null passed" conclusion; any residual localization implying descriptor validity; any screen /
real-clip / runtime / memory authorization; any classifier (B) / neural (C) opening; any "Brainvision sees" / vision /
readiness / capability claim; or any claim-lock / verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY/Chroma Synthetic Fixture Implementation Boundary Review v2.25. Docs-only boundary review.
Opens no implementation lane, no tests, and no fixture generation; opens no classifier / neural / screen / real-clip /
runtime / memory work; adopts no descriptor / coordinate system / numeric geometry / metric / equation / threshold /
scoring / pass-fail rule; defines no fixture, data structure, formula, numeric parameter, score, threshold, or expected
output; reviews whether a future v2.26 may implement a deterministic reporting-only static symbolic artifact for the
six v2.24 BY/chroma roles, specifying the allowed shape, the forbidden shape, and the five mandatory guard conditions;
conditionally recommends v2.26 only if every condition is met and it is separately Codex-reviewed and operator-approved
(a gate, not a green light); notes a v2.26 would not answer the v2.22 question; registers forbidden drifts; states the
non-claim interpretation; keeps the flat opponent-field symbolic branch PAUSED HELD, prior BY/color/chroma work FROZEN
EVIDENCE, and the v2.22 question UNRESOLVED; authorizes nothing by itself; preserves all claim locks and the frozen
verdict HOLD; makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity / temporal-order /
readiness claim; outcome label BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_IMPLEMENTATION_BOUNDARY_REVIEW_ONLY; no `§0`
pointer added; no tags.*
