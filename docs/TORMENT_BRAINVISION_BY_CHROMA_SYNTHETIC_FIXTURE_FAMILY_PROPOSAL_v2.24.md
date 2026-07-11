# TORMENT Brainvision BY/Chroma Synthetic Fixture-Family Proposal v2.24

## 1. Status / Scope

**DOCS-ONLY conceptual fixture-family PROPOSAL.** This is a proposal note only. It opens **no** code, **no** tests,
**no** runtime, and **no** integration lane; it authorizes **no** implementation, **no** concrete fixture definitions,
**no** metrics, **no** validation, **no** readiness claim, and **no** capability claim, and it is not corrective. It
sits over the accepted v2.23 edge (`docs(research): plan by chroma fixture design boundary`) and changes none of the
accepted files.

**v2.24 proposes conceptual fixture-family ROLES only.** It names a finite set of conceptual roles that a *future*
reporting-only synthetic falsification design could consider, so that a later implementation-boundary review can decide
whether any of them may ever be converted into reporting-only code. It is **not** implementation, **not** concrete
fixture generation, and **not** a metric or validation design.

**v2.24 authorizes nothing.** It introduces and authorizes **no** implementation, tests, concrete fixture instances,
fixture data, descriptor, coordinate system, numeric geometry, metric, equation, threshold, scoring, pass/fail gate,
validation, closure, real clip, screen / camera / live / sensor / streaming path, runtime path, memory path, prompt /
context / action / render-body / autonomy contact, classifier (form B), or neural encoder (form C). It makes **no**
production vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, and **no** descriptor-validity /
geometry-validity / screen-readiness / memory-readiness / runtime-readiness / integration-readiness claim. **Any future
implementation must be separately reviewed by Codex and operator-approved.** Everything stays offline under
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

## 2. v2.22 / v2.23 Boundary Preserved

```text
PRIMARY QUESTION (v2.22 Formulation A) -- in force:
  "Can future synthetic design distinguish BY-axis residual behavior from generic chroma proxy effects without adopting
   metrics or closure claims?"

MANDATORY NON-CLAIM CONSTRAINT (v2.22 Formulation C) -- in force:
  "Residual localization must not imply descriptor validity."

v2.23 allowed CONCEPTUAL FAMILY-ROLE PLANNING ONLY: a future fixture-design document may discuss the residual pressure
being isolated, the proxy-risk class guarded against, fixture-family ROLES in principle, the claim locks that stay
False, reporting-only language, and what stays unmeasured -- and must NOT define actual fixtures, data structures,
formulas, metrics, thresholds, expected outputs, or pass/fail criteria. v2.24 stays inside that boundary exactly.

ALSO PRESERVED:
  - REPORTING-ONLY: "distinguish / isolate / separate / contrast / BY-dominant / generic proxy / matched / entangled /
    artifact / null" are CONCEPTUAL / REPORTING language ONLY -- they imply no scoring, measurement, validation,
    pass/fail, or proof. "Distinguish" means "report whether a distinction can even be POSED", never "measure how
    separated".
  - DESCRIPTOR-VALIDITY: residual localization must not imply descriptor validity; no family role may imply a
    descriptor works.
  - NO-METRIC: no metrics, scores, thresholds, equations, weights, ratios, distances, axis values, coordinates, numeric
    gradients, or comparison functions -- anywhere.
  - NO-VALIDATION: no validation, closure, pass/fail, control success, or readiness claim.
  - NO-SCREEN/RUNTIME: no screen, real-clip, camera, live, sensor, streaming, runtime, memory, prompt/context/action/
    render-body/autonomy, classifier, neural, or vision path.
  - PRIOR EVIDENCE: prior BY/color/chroma evidence remains FROZEN UNRESOLVED localization evidence, not solved proof.
  - FLAT-FIELD SCAFFOLD: the paused flat opponent-field symbolic scaffold may inform DISCIPLINE but does NOT validate
    these family roles.
```

## 3. Proposed Conceptual Fixture-Family Roles

A finite set of six conceptual ROLES. These are names for *what a case would conceptually be for*, not fixtures. No
data, arrays, formulas, coordinates, numeric parameters, scores, thresholds, or expected measured outputs are defined.

```text
====================================================================================================================
ROLE A -- BY-DOMINANT CHROMA RESIDUAL ROLE
  purpose      : represent a conceptual case where BY-axis residual pressure is the intended REPORTING FOCUS.
  isolates     : conceptually, the "this is where the BY-axis residual pressure would sit" case -- the thing the
                 primary question is about.
  not measured : does NOT measure a BY axis, a channel, a magnitude, a separation, or anything else; nothing is
                 computed.
  drift risk   : "BY-dominant" read as a MEASURED BY axis / a quantified dominance.
  forbidden    : must NOT imply a measured BY axis, descriptor validity, metric separation, visual truth, or validation.
  safe language: "a role that conceptually carries BY-axis residual pressure"; "reporting focus"; never "BY value",
                 "dominance score", "BY channel measured".
  guardrail    : BY-dominant is a ROLE NAME; it carries no axis, no channel, no number; descriptor_validity stays False.
  future review: MAY be considered in a future implementation-boundary review (reporting-only), pending approval.

====================================================================================================================
ROLE B -- GENERIC CHROMA PROXY ROLE
  purpose      : represent a conceptual case where GENERIC CHROMA PROXY effects are the intended confound / proxy-risk
                 focus.
  isolates     : conceptually, the confound class (spectrum / per-channel-std / directional-movement / roughness) that
                 any apparent residual must be held apart from.
  not measured : does NOT measure any proxy, does not control one, does not rule one out; the proxy classes are NAMED
                 as confounds only.
  drift risk   : the proxy being treated as SOLVED, controlled, or measured because it has a role name.
  forbidden    : must NOT imply the proxy is solved, the proxy is measured, a metric comparison exists, or a control
                 passed.
  safe language: "a role that conceptually carries generic chroma proxy character"; never "proxy controlled",
                 "proxy ruled out", "proxy measured".
  guardrail    : the standing presumption holds -- an apparent residual IS a generic proxy effect until a reporting-only
                 distinction shows otherwise, and NO such showing exists.
  future review: MAY be considered in a future implementation-boundary review (reporting-only), pending approval.

====================================================================================================================
ROLE C -- MATCHED NON-BY CHROMA ROLE
  purpose      : represent conceptual NON-BY chroma pressure, so BY-specific language does not swallow all color/chroma
                 effects.
  isolates     : conceptually, the "chroma pressure that is not BY-axis" case -- preventing "BY" from becoming a
                 synonym for "any color effect".
  not measured : does NOT measure a channel, a colour space, a separation between channels, or a match; "matched" is
                 conceptual, not computed.
  drift risk   : "matched" read as METRIC-MATCHED (matched on a measured quantity); "non-BY" read as a coordinate
                 colour-space axis.
  forbidden    : must NOT imply a coordinate colour space, measured channel separation, or descriptor proof.
  safe language: "a role that conceptually carries non-BY chroma pressure"; "conceptually matched"; never "matched on
                 X", "channel-separated", "colour-space coordinate".
  guardrail    : "matched" is a CONCEPTUAL role relation, never a computed matching; no colour space is adopted.
  future review: MAY be considered in a future implementation-boundary review (reporting-only), pending approval.

====================================================================================================================
ROLE D -- BY/CHROMA ENTANGLED ROLE
  purpose      : represent conceptual cases where BY residual pressure and generic chroma proxy pressure may be
                 ENTANGLED (the historically observed situation).
  isolates     : conceptually, the honest hard case -- that the two may not be separable at all; it keeps the design
                 from presupposing separability.
  not measured : does NOT quantify entanglement, does not score separability, does not measure a degree of mixing.
  drift risk   : "entangled" read as QUANTIFIED ENTANGLEMENT (a measured mixing coefficient).
  forbidden    : must NOT imply entanglement is quantified, separation is scored, or closure is possible from this
                 role alone.
  safe language: "a role that conceptually carries entangled BY/proxy pressure"; never "entanglement of degree X",
                 "separability score".
  guardrail    : entanglement is a CONCEPTUAL possibility, and its presence would be a REASON THE QUESTION MAY BE
                 UNANSWERABLE -- not a quantity.
  future review: MAY be considered in a future implementation-boundary review (reporting-only), pending approval.

====================================================================================================================
ROLE E -- FIXTURE-FAMILY ARTIFACT ROLE
  purpose      : represent the possibility that an apparent residual distinction could be PRODUCED BY THE FIXTURE-FAMILY
                 DESIGN ITSELF (the v2.22 Formulation-B guardrail, made a first-class role).
  isolates     : conceptually, the self-suspicion case -- "did we manufacture the effect?" -- so the design cannot take
                 its own construction for granted.
  not measured : does NOT measure an artifact, does not control for one, does not show one absent; no artifact metric
                 exists.
  drift risk   : "artifact role" read as MEASURED ARTIFACT CONTROL, or its presence read as VALIDATING the families.
  forbidden    : must NOT imply fixture artifacts are measured, fixture families are validated, or artifact control
                 succeeded.
  safe language: "a role that conceptually carries the fixtures-may-manufacture-the-effect suspicion"; never "artifact
                 controlled", "artifact ruled out", "families validated".
  guardrail    : naming the artifact suspicion NEVER validates the families; "not an artifact" may never be concluded.
  future review: MAY be considered in a future implementation-boundary review (reporting-only), pending approval.

====================================================================================================================
ROLE F -- NULL / REPORTING-BOUNDARY ROLE
  purpose      : represent a NON-AUTHORIZING boundary role that keeps reporting language from becoming validation.
  isolates     : conceptually, nothing about colour -- it isolates the CLAIM BOUNDARY itself, marking where reporting
                 stops and validation would (impermissibly) begin.
  not measured : does NOT measure anything, does not baseline anything, does not adjudicate anything.
  drift risk   : "null" read as a VALIDATION CONTROL / negative control / passed null (the v2.12 hazard, recurring).
  forbidden    : must NOT imply a validation control, a baseline, a pass/fail null result, or falsification success.
  safe language: "a non-authorizing reporting-boundary role"; "a control BY NAMING only"; never "null control passed",
                 "baseline", "negative control".
  guardrail    : per v2.12 N1-N6 -- the null/boundary role is an ANTI-CLAIM SCAFFOLD, not evidence; protocol greenness
                 would never mean the null "passed".
  future review: MAY be considered in a future implementation-boundary review (reporting-only), pending approval.
====================================================================================================================
```

## 4. Cross-Family Risk Review

Roles may each stay disciplined yet combine into an implied capability. The dangerous combinations, each to be refused:

```text
- A + B  -> reads as a SCORED SEPARATION (BY-dominant vs generic proxy, with a measured gap between them). Refuse: both
            are role names; "distinguish" is a reporting-only DISTINCTION, never a scored or measured separation.
- A + C  -> reads as HIDDEN CHANNEL / AXIS GEOMETRY (BY vs non-BY as coordinate colour-space axes). Refuse: both are
            conceptual roles; no colour space, channel, axis value, or coordinate is adopted.
- B + E  -> reads as a SOLVED PROXY-CONTROL CLAIM (proxy role + artifact role = "we controlled for both"). Refuse:
            naming confounds and self-suspicion controls NOTHING; no proxy or artifact is measured or ruled out.
- D alone-> reads as QUANTIFIED ENTANGLEMENT (a measured degree of mixing). Refuse: entanglement is a conceptual
            possibility that may make the question unanswerable -- never a quantity.
- E + F  -> reads as VALIDATION-CONTROL LOGIC (artifact check + null control = a passed validation apparatus). Refuse:
            both are anti-claim scaffolds; neither adjudicates, scores, or validates anything (v2.12).
- A-F completeness -> reads as VALIDATION COVERAGE ("six roles cover the space, so the design is sound"). Refuse:
            covering six ROLE NAMES is not coverage of any effect, and not validation of anything.
```

## 5. Forbidden Drift Register

```text
- BY-dominant becoming a MEASURED BY AXIS.
- generic proxy becoming a SOLVED CONFOUND.
- matched becoming METRIC-MATCHED.
- entangled becoming QUANTIFIED ENTANGLEMENT.
- artifact becoming MEASURED ARTIFACT CONTROL.
- null becoming a VALIDATION CONTROL.
- distinction becoming a SCORED SEPARATION.
- isolation becoming CLOSURE.
- residual localization becoming DESCRIPTOR VALIDITY.
- family proposal becoming FIXTURE IMPLEMENTATION.
- conceptual family becoming a CLASSIFIER LABEL.
- conceptual family becoming a NEURAL TARGET.
- conceptual family becoming a SCREEN OBJECT / VISUAL CATEGORY.
- synthetic falsification becoming VALIDATION.
- reporting-only becoming PASS/FAIL.
```

## 6. Non-Claim Interpretation

```text
WHAT THIS PROPOSAL MAY ESTABLISH (and only this):
  - a FINITE CONCEPTUAL FAMILY-ROLE PROPOSAL (six named roles, A-F);
  - a REPORTING-ONLY LANGUAGE BOUNDARY for those roles;
  - a FUTURE-REVIEW CANDIDATE SET (roles that a later implementation-boundary review may consider).

WHAT IT DOES NOT ESTABLISH:
  not fixtures            not implementation      not metric separation
  not descriptor validity not validation          not closure
  not readiness           not vision              not that the residual is distinguishable at all
  not that any role is realizable, useful, or correct

Naming six roles measures nothing, builds nothing, separates nothing, and validates nothing. The primary question
remains UNRESOLVED, and it remains genuinely possible (Role D) that BY residual and generic chroma proxy are not
separable at all.
```

## 7. Recommended Next Step

```text
RECOMMEND: a v2.25 IMPLEMENTATION-BOUNDARY REVIEW (docs-only) -- NOT implementation.

  The v2.25 review would decide -- and only decide -- whether a FUTURE v2.26 could ever implement a REPORTING-ONLY
  fixture-family generator with conservative guards, and under exactly what boundary. It would be strictly bounded to
  reporting-only synthetic fixture-family implementation PLANNING: what may be generated as reporting-only structure,
  what guards would be mandatory, what must remain forever absent (metrics, scores, thresholds, descriptors,
  coordinates, validation, pass/fail), and what claim locks stay False.

  v2.24 does NOT recommend direct implementation, and does NOT recommend descriptors, coordinates, metrics, validation,
  screen / real-clip / runtime / memory / classifier (B) / neural (C) / vision work. It is NOT self-authorizing: the
  operator chooses whether v2.25 opens at all, and any v2.25 must be separately bounded, Codex-reviewed, and
  operator-approved. Until then the flat opponent-field symbolic branch stays PAUSED HELD, prior BY/color/chroma work
  stays FROZEN EVIDENCE, and the v2.22 question stays UNRESOLVED.
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

OUTCOME_LABEL: BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_FAMILY_PROPOSAL_ONLY
```

v2.24 is a docs-only conceptual fixture-family proposal. It preserves the v2.22 primary question and its mandatory
descriptor-validity non-claim constraint and the v2.23 conceptual-only boundary; proposes a finite set of six
conceptual fixture-family ROLES (A BY-dominant residual, B generic chroma proxy, C matched non-BY chroma, D BY/chroma
entangled, E fixture-family artifact, F null/reporting-boundary), each with its purpose, what it conceptually isolates,
what it does not measure, its drift risk, its forbidden interpretation, safe reporting language, required guardrail,
and future-review eligibility; reviews the cross-family risks; registers the forbidden drifts; states the non-claim
interpretation; and recommends a docs-only v2.25 implementation-boundary review rather than implementation. It defines
no fixtures, no data, no metric / score / threshold, and is not self-authorizing. All claim locks and the frozen
verdict **HOLD** are preserved and unmoved.

## 9. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_FAMILY_PROPOSAL_v2.24.md
(new, docs-only, untracked; over the accepted v2.23 edge "docs(research): plan by chroma fixture design boundary").

Verify that this proposal:
- is docs-only and authorizes NO implementation, NO tests, NO concrete fixture instances, NO fixture data, NO
  descriptor / coordinate / numeric geometry / metric / equation / threshold / scoring / pass-fail gate / validation /
  closure, no real clips, no screen / camera / live / sensor / streaming / runtime / memory paths, no classifier (form
  B) / neural (form C), no vision; and DEFINES NO CONCRETE FIXTURE, data structure, formula, numeric parameter, score,
  threshold, or expected measured output ANYWHERE;
- frames the central question as WHICH conceptual fixture-family ROLES would be useful for a future reporting-only
  synthetic falsification design aimed at distinguishing BY-axis residual behavior from generic chroma proxy effects,
  while preserving that residual localization does not imply descriptor validity;
- preserves the v2.22 primary question (Formulation A) and mandatory non-claim constraint (Formulation C), and the
  v2.23 conceptual-family-role-planning-only boundary; and preserves the reporting-only, descriptor-validity,
  no-metric, no-validation, no-screen/runtime, prior-evidence (frozen unresolved), and flat-field-scaffold
  (discipline-not-validation) boundaries;
- proposes a FINITE conceptual family-role set (A BY-dominant chroma residual; B generic chroma proxy; C matched non-BY
  chroma; D BY/chroma entangled; E fixture-family artifact; F null/reporting-boundary) and for EACH role gives:
  conceptual purpose; what it helps isolate conceptually; what it does not measure; primary proxy/drift risk; forbidden
  interpretation; safe reporting language; required guardrail; and whether it may be considered for a future
  implementation-boundary review;
- reviews the cross-family risks (A+B scored separation; A+C hidden channel/axis geometry; B+E solved proxy-control
  claim; D quantified entanglement; E+F validation-control logic; A-F completeness as validation coverage);
- includes the forbidden drift register (BY-dominant -> measured BY axis; generic proxy -> solved confound; matched ->
  metric matched; entangled -> quantified entanglement; artifact -> measured artifact control; null -> validation
  control; distinction -> scored separation; isolation -> closure; residual localization -> descriptor validity; family
  proposal -> fixture implementation; conceptual family -> classifier label / neural target / screen object; synthetic
  falsification -> validation; reporting-only -> pass/fail);
- states the non-claim interpretation (may establish ONLY: a finite conceptual family-role proposal, a reporting-only
  language boundary, a future-review candidate set; does NOT establish fixtures, implementation, metric separation,
  descriptor validity, validation, closure, readiness, or vision);
- recommends a docs-only v2.25 IMPLEMENTATION-BOUNDARY REVIEW (strictly bounded to reporting-only synthetic
  fixture-family implementation planning) and NOT direct implementation, and recommends NO descriptor / coordinate /
  metric / validation / screen / real-clip / runtime / memory / classifier / neural / vision work; is NOT
  self-authorizing;
- preserves the locks and verdict (Section 8): flat_field_validated = False; first_pass_structure_validity_claim_allowed
  = False; temporal_claim_allowed = False; descriptor_validity_claim_allowed = False; geometry_validity_claim_allowed =
  False; screen_readiness_claim_allowed = False; runtime_readiness_claim_allowed = False; memory_readiness_claim_allowed
  = False; integration_readiness_claim_allowed = False; vision_claim_allowed = False; verdict = HOLD; outcome label
  BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_FAMILY_PROPOSAL_ONLY; interprets HOLD/HELD as held for analysis, not
  abandoned;
- adds NO §0 pointer and NO tags, and makes no vision / "Brainvision sees" / descriptor-validity / geometry-validity /
  temporal-order / readiness claim.

Flag any concrete fixture / instance / bank / data structure / schema / formula / metric / score / threshold / weight /
ratio / distance / axis value / coordinate / numeric parameter / expected output / pass-fail criterion defined anywhere;
any role name implying measurement, success, validation, or screen/vision; any "distinguish/isolate/separate/matched/
entangled" used as a scored or measured term; any proxy or artifact treated as controlled, ruled out, or solved; any
"not an artifact" conclusion; any null role treated as a validation control or passed baseline; any residual
localization implying descriptor validity; any closure claimed; any authorization of implementation; or any claim-lock /
verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`flat_field_validated = False`, all claim locks False, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY/Chroma Synthetic Fixture-Family Proposal v2.24. Docs-only conceptual proposal. Opens no
implementation lane, no tests, and no fixture generation; opens no classifier / neural / screen / real-clip / runtime /
memory work; adopts no descriptor / coordinate system / numeric geometry / metric / equation / threshold / scoring /
pass-fail rule; defines no fixture, data structure, formula, numeric parameter, score, threshold, or expected output;
proposes six finite conceptual fixture-family ROLES (BY-dominant residual, generic chroma proxy, matched non-BY chroma,
BY/chroma entangled, fixture-family artifact, null/reporting-boundary) with purpose, conceptual isolation, what is not
measured, drift risk, forbidden interpretation, safe language, guardrail, and future-review eligibility per role;
reviews cross-family risks; registers forbidden drifts; states the non-claim interpretation; recommends a docs-only
v2.25 implementation-boundary review rather than implementation; keeps the flat opponent-field symbolic branch PAUSED
HELD, prior BY/color/chroma work FROZEN EVIDENCE, and the v2.22 question UNRESOLVED; is not self-authorizing; preserves
all claim locks and the frozen verdict HOLD; makes no vision / "Brainvision sees" / descriptor-validity /
geometry-validity / temporal-order / readiness claim; outcome label
BRAINVISION_BY_CHROMA_SYNTHETIC_FIXTURE_FAMILY_PROPOSAL_ONLY; no `§0` pointer added; no tags.*
