# TORMENT Brainvision Flat Opponent-Field Implementation Review v2.2a

## 1. Status / non-claims

**DOCS-ONLY implementation authorization review. It MAY recommend implementation, but it implements nothing.**
Opens no code, no tests, no runtime, no integration lane here. It reviews whether a future **v2.3** reporting-only
harness of the v2.2 flat opponent-field audit design may be authorized, and defines the **exact boundary** v2.3
would have to respect if the operator later approves it. Recommending authorization is **not** performing it: this
document writes no `.py`, runs nothing, and authorizes nothing by itself — a separate, explicit operator decision
is required to open v2.3.

It adopts **no** descriptor, **no** coordinate system, **no** metric, **no** equation, invents **no** threshold,
**redefines no `TOL`**, adds **no** pass/fail validity rule, changes no formula / §7 anti-proxy logic / §8 verdict
logic, deletes or weakens no control, redesigns no descriptor, reopens no spectral group, expands no generator
family, and opens **no classifier (form B) and no neural encoder (form C)**. It authorizes **no flat-geometry
implementation beyond reporting the accepted conceptual audit panels** and **no screen-analysis implementation**.
Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. A review alone moves nothing: **no claim
lock and no verdict changes here.**

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v2.2 audit design

```text
v2.1a (8625e90)  flat opponent-field PREREGISTRATION plan: finite obligations A-F + deferrals.
v2.2  (8376caa)  flat opponent-field AUDIT DESIGN: reporting panels A-F + output fields + guards + breach conditions;
                 adopting none; authorizing no code.
v2.2a (this doc) implementation AUTHORIZATION review: may a v2.3 reporting-only harness of v2.2 be authorized, and
                 what is its EXACT boundary? Recommends; authorizes nothing by itself.
```

v2.2 fixed WHAT a conformant flat opponent-field audit must report (panels A-F, output fields, guards, breach
conditions). v2.2a asks the narrower question: is that structure ready to be IMPLEMENTED as a reporting-only
harness, and if so, under what precise, bounded scope? It changes nothing v2.2 froze and adopts nothing.

## 3. Implementation-readiness question

```text
QUESTION:
  Is the v2.2-designed flat opponent-field audit (panels A-F + guards) ready to be implemented as a v2.3
  reporting-only harness -- WITHOUT that implementation adopting any descriptor / coordinate system / metric /
  equation / threshold / pass-fail rule, and WITHOUT authorizing screen analysis / real clips / runtime / memory /
  vision?

ASSESSMENT (docs-only):
  - The v2.2 panels A-F are CONCEPTUAL obligation-conformance reports, not measurements: each reports whether a
    v2.1a obligation is stated / respected, with structural conformance booleans only. No panel requires a
    descriptor, a coordinate system, a metric, or an equation, so a reporting-only harness can GENERATE the
    structure without adopting any of them.
  - Precedent exists for reporting-only, non-authorizing, guard-completeness-enforced harnesses in the fixture
    route (v1.2 / v1.5 / v1.7, accepted). v2.3 would apply the SAME discipline to the flat opponent-field panels:
    structural conformance + a non-authorizing guard whose any-True-or-missing flag forces a breach.
  - IMPORTANT DIFFERENCE from the fixture route: v2.3 has NO frozen prior harness to reuse by identity (the flat
    field is a new, unvalidated abstraction). v2.3 would therefore report the DESIGN obligations themselves, not a
    reused numeric surface -- which keeps it purely structural / conceptual and is exactly why it can adopt nothing.
  - Therefore the structure appears READY for a reporting-only implementation, conditional on the exact boundary in
    §4-§9 and on explicit operator + Codex approval. Readiness of the STRUCTURE is not authorization of the CODE.
```

## 4. What v2.3 may implement (if later authorized)

```text
If -- and only if -- the operator explicitly authorizes v2.3 after this review is accepted, v2.3 MAY:
  - generate the A patch-definition reporting panel (conceptual local opponent-patch requirements);
  - generate the B opponent-channel reporting panel (BY / RG explicitness requirements);
  - generate the C spatial-relation reporting panel (adjacency / neighborhood / gradient / edge / continuity-
    discontinuity obligations, named);
  - generate the D region-field reporting panel (local patch effects vs field-level organisation distinction);
  - generate the E temporal-deferral reporting panel (motion / time deferred, not first principle);
  - generate the F non-authorizing guard panel (all flags present and False);
  - include STRUCTURAL CONFORMANCE BOOLEANS ONLY (each obligation stated / respected: True/False), no measurement;
  - define protocol_ok to mean ONLY that the required reporting panels and guards are present (NOT validation, NOT closure);
  - set frozen_brainvision_verdict = HOLD and keep all claim locks False;
  - record v1x_status = frozen_evidence and v2x_status = unvalidated_conceptual_pivot.
v2.3 would be reporting-only, form-A, non-learning, CONCEPTUAL over offline synthetic content, adopting nothing.
```

## 5. What v2.3 may not implement

```text
FORBIDDEN in v2.3 (any of these makes it non-conformant):
  - NO descriptor implementation; NO coordinate-system implementation; NO resolution.
  - NO metric implementation; NO equation implementation; NO threshold implementation.
  - NO pass/fail validity gate; NO TOL redefinition; NO §7 / §8 / control / evaluator change.
  - NO generator-family expansion; NO spectral reopening as closure; NO change to the frozen descriptor.
  - NO classifier (form B); NO neural encoder (form C).
  - NO flat-geometry implementation BEYOND reporting the accepted conceptual audit panels; NO screen-analysis
    implementation; NO camera / live / sensor / screen-capture / streaming; NO real clips.
  - NO torment_service/; NO runtime / memory / integration wiring.
  - NO vision / "Brainvision sees" claim; NO descriptor-validity / temporal-order / closure claim; NO runtime-
    readiness / memory-readiness / integration-readiness claim.
  - NO §0 pointer; NO tags; NO claim-lock or verdict movement.
```

## 6. Required files for v2.3

```text
EXACTLY two files, both offline research surfaces (no others):
  research/brainvision/run_flat_opponent_field_audit_v2_3.py
  tests/research/test_brainvision_flat_opponent_field_audit_v2_3.py
No other file may be created or modified by v2.3 (no torment_service/, no runtime, no docs beyond an optional
findings note gated separately). Imports limited to quarantined research surfaces / stdlib; no torment* / service
imports. Because the flat field is a NEW abstraction with no frozen harness to reuse, v2.3 reports the DESIGN
obligations structurally and introduces no numeric surface, descriptor, or coordinate system.
```

## 7. Required output fields

The v2.3 result object MUST expose (field names indicative; conceptual / structural, adopting nothing):

```text
- panels: A_patch_definition, B_opponent_channel, C_spatial_relation, D_region_field, E_temporal_deferral,
  F_non_authorizing_guard (each a conceptual obligation-conformance report with structural booleans only).
- obligation_conformance: mapping obligation A-F -> conformant (bool); no descriptor / metric attached.
- protocol_ok (bool; required panels + guards present ONLY, NOT validation / closure); breaches (list);
  outcome_label (reporting label, e.g. flat_field_prereg_structure_reported / invalid_protocol_breach).
- non-adoption flags, all False: descriptor_adopted, coordinate_system_adopted, metric_adopted, equation_adopted,
  threshold_introduced, pass_fail_rule_introduced, tol_redefined, generator_family_expansion_authorized,
  spectral_closure_reopened, flat_geometry_authorized, screen_analysis_authorized, runtime_authorized,
  memory_authorized, real_clip_authorized, vision_claim_allowed.
- reporting_only = True; conceptual_only = True; offline_only = True.
- v1x_status = "frozen_evidence"; v2x_status = "unvalidated_conceptual_pivot".
- claim locks (all False) + frozen_brainvision_verdict = HOLD.
These are REQUIRED FIELDS, not equations; no field is a descriptor, a coordinate, a metric, or a threshold.
```

## 8. Required tests

`tests/research/test_brainvision_flat_opponent_field_audit_v2_3.py` MUST lock only platform-independent robust
facts:

```text
[ ] provenance: imports only quarantined research surfaces / stdlib (no torment* / service); no new descriptor /
    coordinate system / metric / equation / threshold in source.
[ ] panels A-F all present; each reports conceptual obligation-conformance with structural booleans only.
[ ] guard (panel F): all authorization flags present and False; ANY authorizing flag True (or a required flag
    absent) -> protocol_ok False / invalid_protocol_breach (completeness-enforced, parametrized over multiple flags).
[ ] no adoption: descriptor_adopted / coordinate_system_adopted / metric_adopted / equation_adopted /
    threshold_introduced / pass_fail_rule_introduced / tol_redefined all False; TOL referenced == 0.0634 unchanged.
[ ] protocol_ok means presence-of-required-panels-and-guards ONLY; no validation / closure / descriptor-validity claim.
[ ] reporting_only / conceptual_only / offline_only True; no flat-geometry-beyond-panels / screen / camera / live /
    real-clip / runtime / memory path in source.
[ ] v1x_status frozen_evidence; v2x_status unvalidated_conceptual_pivot.
[ ] output is deterministic; claim locks False; verdict HOLD.
Windows pytest is the source of truth.
```

## 9. Protocol failure conditions

```text
v2.3 MUST return invalid_protocol_breach (protocol_ok False) on ANY of:
  - a missing or incomplete panel A-F;
  - a guard (panel F) that is absent, or carries ANY authorization flag True, or is missing a required flag;
  - any adopted descriptor / coordinate system / metric / equation / threshold / TOL change / pass-fail gate;
  - any generator-family expansion, spectral reopening, or change to the frozen descriptor;
  - any flat-geometry-beyond-panels / screen-analysis / camera / live / real-clip / runtime / memory path;
  - any treatment of v1.x as retracted rather than frozen evidence, or of v2.x as validated.
A breach can NEVER become a validation, a descriptor, a pass, a closure, or a claim / verdict movement.
```

## 10. Claim-lock preservation

```text
Under EVERY v2.3 outcome (flat_field_prereg_structure_reported / invalid_protocol_breach):
  first_pass_structure_validity_claim_allowed = False
  temporal_claim_allowed                      = False
  descriptor_validity_claim_allowed           = False
  frozen_brainvision_verdict                  = HOLD
  vision_claim = memory_readiness_claim = runtime_readiness_claim = integration_readiness_claim = False
v2.3 moves NO claim lock and NO verdict; it is reporting-only, conceptual, and non-authorizing by construction.
```

## 11. Risks / ambiguity notes

```text
- REPORTING-A-DESIGN, NOT A MEASUREMENT: v2.3 reports the DESIGN obligations structurally; there is NO numeric
  surface. Risk: a reviewer expecting measurements. Mitigation: v2.3 is explicitly conceptual/structural (booleans),
  and the tests assert no descriptor / coordinate / metric / equation appears in source.
- "FLAT GEOMETRY BEYOND PANELS": the one nuance in the boundary. v2.3 MAY report the accepted conceptual panels
  A-F; it MUST NOT implement any flat geometry beyond that (no grid, no coordinates, no patch computation over a
  field). Tests must assert no coordinate system / grid / patch-computation appears.
- SCOPE CREEP TO SCREEN / VISION: a flat field resembles a screen. v2.3 is offline synthetic + conceptual ONLY; it
  authorizes NO screen analysis, real clips, camera / live, or vision claim. The guard (F) and offline_only flag
  enforce this; tests must assert them.
- GUARD COMPLETENESS: as in the fixture route (v1.5 P1), the guard must be COMPLETENESS-ENFORCED -- any required
  flag missing OR True forces a breach -- not merely presence-agnostic. v2.3 tests must cover missing-flag and
  True-flag breaches.
- NO REUSE BY IDENTITY: unlike v1.2 -> v1.7, v2.3 has no frozen prior harness to reuse. This is expected (new
  abstraction) but means v2.3's determinism and non-adoption rest on the source itself; tests must assert both.
- READY IS NOT VALIDATED: recommending v2.3 says the STRUCTURE is implementable reporting-only; it says nothing
  about whether the flat opponent-field abstraction is better, or about vision / descriptor validity.
- AUTHORIZATION IS THE OPERATOR'S: this review recommends; only the operator opens v2.3. No code is authorized here.
```

## 12. Recommendation

**Recommend authorizing the v2.3 reporting-only implementation harness — but ONLY IF Codex accepts this review
as-is, and ONLY on the operator's explicit approval.** The v2.2 panels A-F are conceptual obligation-conformance
reports with structural booleans only; they require no descriptor / coordinate system / metric / equation /
threshold, so a reporting-only harness can generate them while adopting nothing, and the boundary in §4-§10 is
precise enough to keep v2.3 non-authorizing, conceptual, and offline. If Codex requires changes, resolve them here
(docs-only) before any code. v2.3 remains an UNVALIDATED-abstraction reporting exercise: it validates nothing and
keeps v1.x as frozen evidence.

```text
1. Codex review THIS implementation authorization review (docs-only; over committed edge 8376caa).
2. If Codex ACCEPTS AS-IS and the operator explicitly approves, open v2.3 as a SEPARATE reporting-only
   implementation limited to the two files in §6, conforming to §4-§10 exactly (panels A-F; structural conformance
   booleans; non-authorizing completeness-enforced guard; protocol_ok = presence-only; claim locks False; verdict HOLD).
3. If Codex requires changes, revise THIS review (docs-only) and re-review before any code.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry-beyond-panels, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_IMPLEMENTATION_REVIEW_v2.2a.md
(new, docs-only, untracked; over committed edge 8376caa, reviewing whether a v2.3 reporting-only harness of the
v2.2 flat opponent-field audit design may be authorized and defining its exact boundary; recommends, authorizes
nothing itself).

Verify that this review:
- is docs-only and implements nothing (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen-capture/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
  authorizes NO screen-analysis and NO flat-geometry implementation BEYOND reporting the accepted conceptual panels;
- MAY recommend implementation but ADOPTS NOTHING itself -- no descriptor, no coordinate system, no metric, no
  equation, no threshold, no TOL change, no pass/fail validity rule, no family expansion, no spectral reopening;
- defines the EXACT v2.3 boundary: allowed files are exactly research/brainvision/run_flat_opponent_field_audit_v2_3.py
  and tests/research/test_brainvision_flat_opponent_field_audit_v2_3.py; allowed scope = generate panels A-F
  (patch-definition / opponent-channel / spatial-relation / region-field / temporal-deferral / non-authorizing guard)
  with STRUCTURAL CONFORMANCE BOOLEANS ONLY; protocol_ok = required reports + guards present, NOT validation / closure;
  verdict HOLD; claim locks False;
- forbids in v2.3: descriptor / coordinate-system / metric / equation / threshold implementation; pass/fail validity
  gate; TOL redefinition; screen-analysis; real clips; runtime / memory integration; and any vision / descriptor-
  validity / temporal-order / closure / runtime-readiness / memory-readiness / integration-readiness claim;
- specifies required output fields (§7), required tests (§8: provenance / panels-present / guard-completeness-enforced
  breach / no-adoption / presence-not-validation / offline-conceptual / v1x-frozen-v2x-unvalidated / determinism),
  protocol failure conditions (§9), and claim-lock preservation under every outcome (§10);
- lists risks (§11: reporting-a-design not a measurement / flat-geometry-beyond-panels / scope creep to screen-vision /
  guard completeness / no reuse by identity / ready != validated / authorization is the operator's) and recommends
  authorizing v2.3 ONLY IF Codex accepts as-is AND the operator explicitly approves;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; keeps v1.x FROZEN EVIDENCE and v2.x UNVALIDATED;
  adds no §0 pointer and no tags.

Flag any adopted descriptor / coordinate system / metric / equation / threshold / pass-fail rule, any TOL
redefinition, any family expansion, any spectral reopening, any flat-geometry-beyond-panels / screen-analysis /
runtime / memory / real-clip authorization, any file beyond the two allowed v2.3 files, any ACTUAL implementation in
this doc, any claim that flat opponent-field is validated or that closure is achieved, any descriptor-validity /
vision / temporal-order claim, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Implementation Review v2.2a. Docs-only authorization review; may
recommend implementation but implements nothing. Opens no implementation lane by itself; opens no classifier /
neural / screen work and no flat-geometry implementation beyond reporting the accepted conceptual panels; changes no
frozen formula, gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no
threshold; redefines no TOL; adopts no descriptor / coordinate system / metric / equation; defines the exact v2.3
reporting-only boundary (panels A-F, structural conformance booleans, non-authorizing guard, protocol_ok =
presence-only) for SEPARATE operator authorization; preserves v1.x as frozen evidence and v2.x as an unvalidated
conceptual pivot; makes no vision / "Brainvision sees" / descriptor-validity / temporal-order / memory / runtime /
integration claim; no `§0` pointer added; no tags.*
