# TORMENT Brainvision Flat Opponent-Field Findings v2.3

## 1. Status / non-claims

**DOCS-ONLY findings synthesis for a REPORTING/GUARD-ONLY, NON-LEARNING form-A implementation.** It records what
the v2.3 flat opponent-field audit established and did **not** establish. It is a synthesis of an already-accepted,
already-committed harness (`0d8722e`); it opens **no** code, tests, runtime, or integration lane and is not
corrective. The v2.3 harness generated the accepted v2.2 flat opponent-field reporting panels A-F as
structural/conceptual reporting; it does **not** adopt a descriptor, a coordinate system, a metric, an equation, a
threshold, or a pass/fail validity rule, **redefines no `TOL`**, changes no formula / §7 anti-proxy logic / §8
verdict logic, deletes or weakens no control, redesigns no descriptor, reopens no spectral group, expands no
generator family, and opens **no classifier (form B) and no neural encoder (form C)**. It opens **no
flat-geometry implementation and no screen-analysis implementation**. Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. The frozen Brainvision §8 verdict is
**HOLD** and untouched.

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Relation to v2.0-v2.2a

```text
v2.0  (5598c28)  flat opponent-field PROPOSAL: candidate research abstraction pivot; conceptual; adopting none.
v2.0a (01d5d9b)  flat opponent-field CONCEPT PLAN: bounded the abstraction's meaning / components / non-goals.
v2.1  (56b344c)  flat opponent-field PREREGISTRATION proposal: obligations A-F a future prereg must contain.
v2.1a (8625e90)  flat opponent-field PREREGISTRATION plan: the FINITE prereg structure (obligations A-F) + deferrals.
v2.2  (8376caa)  flat opponent-field AUDIT DESIGN: reporting panels A-F + fields + guards + breach conditions.
v2.2a (a37c93d)  implementation AUTHORIZATION review: exact v2.3 boundary; authorize only on Codex + operator approval.
v2.3  (0d8722e)  flat opponent-field HARNESS: generated panels A-F as structural reporting; accepted as-is.
v2.3  (this doc) findings synthesis: records what v2.3 established and did NOT establish.
```

v2.0-v2.0a named and bounded the abstraction; v2.1/v2.1a preregistered its obligations; v2.2/v2.2a designed and
authorized the audit; v2.3 implemented it as a reporting/guard-only harness. This synthesis is a receipt over that
implementation. It does not validate flat opponent-field geometry, adopt a descriptor, or select any
representation, and it changes nothing v0.4b / v0.4c / v0.7a froze or v0.7b … v2.2a produced.

## 3. What v2.3 implemented

The v2.3 harness (`research/brainvision/run_flat_opponent_field_audit_v2_3.py`, with
`tests/research/test_brainvision_flat_opponent_field_audit_v2_3.py`) is a form-A, non-learning,
reporting/guard-only audit that generates the accepted v2.2 panels A-F as **structural / conceptual**
obligation-conformance. Because the flat opponent-field is a NEW, UNVALIDATED abstraction, v2.3 has **no** frozen
prior harness to reuse and introduces **no** numeric surface, descriptor, or coordinate system:

```text
A patch-definition    : reports the conceptual local opponent-patch requirement; coordinate_system / descriptor NOT adopted.
B opponent-channel    : reports the BY/RG explicitness requirement; metric NOT adopted.
C spatial-relation    : reports adjacency / neighborhood / gradient / edge / continuity-discontinuity named; equations NOT adopted.
D region-field        : reports the local-patch-vs-field-level distinction; pass/fail rule NOT adopted.
E temporal-deferral   : reports motion/time as deferred, NOT a first principle.
F non-authorizing guard: nine required authorization flags present and False; ANY missing OR True -> protocol_ok False.
```

It implements no descriptor, no coordinate system, no metric, no equation, no threshold, and no pass/fail validity
gate; it redefines no `TOL`, redesigns no descriptor, expands no family, and reopens no spectral group.
`protocol_ok` means only that the required panels and the guard are present — **not** validation. `flat_field_validated`
is hard-wired False; the output is deterministic; a missing panel or a missing/authorizing guard forces
`invalid_protocol_breach`.

## 4. Validation summary

```text
targeted v2.3 tests   : 21 passed
v2.3 script           : emits FLAT_OPPONENT_FIELD_REPORTING_GENERATED ; protocol_ok True ; flat_field_validated False
guard-probe           : every missing OR True required authorization flag -> protocol_ok False; missing guard_present -> False
full tests/research    : 413 passed
claim locks / verdict : locks False False False ; verdict HOLD (unchanged)
```

The tests assert only platform-independent robust facts: stdlib-only imports (no `torment*` / service); panels A-F
present with structural booleans; the completeness-enforced guard (all nine flags present and False, ANY missing OR
True forcing `invalid_protocol_breach`); no descriptor / coordinate system / metric / equation / threshold / pass-fail
adoption; `protocol_ok` = presence-only (not validation); the conservative label; deterministic output; `v1x_status`
frozen_evidence and `v2x_status` unvalidated_conceptual_pivot; and claim locks staying False with verdict HOLD.
Windows pytest is the source of truth.

## 5. Main result

```text
OUTCOME_LABEL: FLAT_OPPONENT_FIELD_REPORTING_GENERATED     flat_field_validated = False     verdict = HOLD

PANELS A-F (structural / conceptual, adopting nothing)
  A patch-definition    conformant = True   coordinate_system_adopted = False   descriptor_adopted = False
  B opponent-channel    conformant = True   metric_adopted = False
  C spatial-relation    conformant = True   relations = [adjacency, neighborhood, gradient, edge, continuity-discontinuity]   equations_adopted = False
  D region-field        conformant = True   pass_fail_rule_adopted = False
  E temporal-deferral   conformant = True   temporal_deferred = True   temporal_is_first_principle = False
  F non-authorizing guard  guard_present = True   all nine authorization flags = False

protocol_ok = True (required panels + guard present ONLY)   obligation_conformance A-F = all True
```

**v2.3 successfully generated the accepted flat opponent-field conceptual reporting panels A-F with structural
booleans and completeness-enforced guards, but it did not validate flat opponent-field geometry.** The outcome is
**`FLAT_OPPONENT_FIELD_REPORTING_GENERATED`** with **`flat_field_validated = False`**: the reporting structure
exists and is obligation-conformant, but nothing about the abstraction has been tested or validated. Generating the
structure moves **no** claim lock and **no** verdict.

## 6. Guard completeness result

```text
The F non-authorizing guard is COMPLETENESS-ENFORCED (carrying the fixture-route v1.5 P1 lesson): admissibility
requires the guard to be present AND all NINE required authorization flags to be PRESENT and False:
  authorizes_vision, authorizes_descriptor_validity, authorizes_temporal_order, authorizes_runtime,
  authorizes_memory, authorizes_integration, authorizes_screen, authorizes_live, authorizes_real_clip.
  - real run: all nine present and False -> guard admissible -> protocol_ok True (reporting present, NOT validation).
  - probe (any flag True): -> protocol_ok False, invalid_protocol_breach (guard_missing_or_authorizing).
  - probe (any required flag ABSENT, or guard_present absent): -> protocol_ok False, invalid_protocol_breach.
This confirms the non-authorizing guard cannot be silently weakened by omission OR by an authorizing flag; a
degraded guard can never produce a reporting result, validation, descriptor validity, or claim / verdict movement.
```

## 7. Interpretation

```text
- v2.3 is the FIRST implemented, boundary-conformant realisation of the flat opponent-field audit design: the panels
  A-F preregistered in v2.1a and designed in v2.2 are now GENERATED as structural reporting that, by construction,
  adopts no descriptor / coordinate system / metric and cannot silently drop its non-authorization guard.
- The reporting works AS DESIGNED and reports a DESIGN, not a MEASUREMENT: v2.3 confirms the obligation structure is
  representable as conceptual conformance over offline synthetic content. It says NOTHING about whether the flat
  opponent-field abstraction is better than the fixture route, and NOTHING about vision or the descriptor.
- The A-F panels are STRUCTURAL / REPORTING checks, not validity gates: protocol_ok = presence of required panels +
  guard; it is NOT validation, closure, descriptor validity, or a vision claim.
- The abstraction remains UNVALIDATED: there is no synthetic fixture, no representation, and no test of whether local
  BY/RG patches / adjacency / gradients / region-field separation can actually be represented -- only that the
  obligation structure to describe them exists.
```

## 8. Why this is not validation

```text
- VALIDATION would require testing whether the flat opponent-field abstraction actually REPRESENTS opponent structure
  better -- over some synthetic fixture, with a represented notion of "better". v2.3 has NO fixture, NO descriptor,
  NO metric, NO representation; it only reports that the obligation structure is stated and conformant.
- protocol_ok = True means only that the required panels + guard are PRESENT; it is explicitly NOT validation, NOT
  closure, NOT descriptor validity, NOT vision (flat_field_validated is hard-wired False; the label set has no
  validation-positive label).
- Nothing was measured: the panels carry structural booleans (obligation stated / respected), not values over data.
- The abstraction rests on ZERO fixtures so far; a single reporting run over a design cannot be validation by construction.
```

## 9. What remains frozen

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator; the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual; PSC < PSC_FLOOR feasibility; the closed F1-F5 family set; the single matching family;
  the v0.7b samples; spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a … v1.7 fixture-route records, preserved as FROZEN EVIDENCE (not failed / retracted); v2.0 … v2.3 as an
  UNVALIDATED conceptual pivot; no sample replacement / new seeds / generation.
- claim locks and verdict HOLD.
v2.3 changed none of the above; this synthesis changes none of the above.
```

## 10. What remains unproven

Even with the flat opponent-field reporting structure implemented, all of the following stay **unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not closure                    (the BY gap is visible, not closed, in the fixture route)
not that flat opponent-field is better / valid (the reporting structure exists; the abstraction is UNVALIDATED)
```

The proof route remains **HELD / HOLD**. Generating the reporting structure is a docs/structure-layer step over an
unvalidated abstraction; it validates nothing. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`)
and `verdict = HOLD` remain in force.

## 11. Candidate next branches

Docs-first candidates only; **none opened or authorized here**:

```text
A. v2.4 FLAT OPPONENT-FIELD MINIMAL SYNTHETIC FIXTURE PROPOSAL (docs-only)
   Design the SMALLEST offline synthetic fixture family that could LATER test whether local BY/RG opponent patches,
   adjacency, gradients, and region/field separation can be represented STRUCTURALLY -- adopting NO descriptor /
   coordinate system / metric / equation / threshold / pass-fail rule, and NOT implementing any fixture yet.
   (Recommended next.)
B. RESUME the BY fixture-metric route (docs-first)
   Only if the flat-field direction stalls or the operator prefers: revisit the frozen fixture route. No lever is
   currently in view.
C. Operator / new-math NOTE (docs-only).
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 12. Recommended next step

**Recommend Branch A (v2.4 flat opponent-field minimal synthetic fixture proposal, docs-only) next.** v2.3 shows the
obligation structure is representable as conceptual reporting; the next clean move is to DESIGN — docs-only — the
smallest offline synthetic fixture family that could later test whether local BY/RG opponent patches, adjacency,
gradients, and region/field separation can be represented structurally. **Do not implement fixtures yet, and adopt no
descriptor / coordinate system / metric / equation / threshold / pass-fail rule.** B (resume fixtures), C (operator
new-math), and D (pause) remain legitimate operator calls.

```text
1. Codex review THIS findings synthesis (docs-only; over committed edge 0d8722e).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first v2.4 minimal synthetic fixture
   PROPOSAL (conceptual; no fixture implemented; no descriptor / coordinate system / metric / equation / threshold /
   pass-fail adopted; no flat-geometry / screen-analysis / camera / live / real-clip / runtime / memory implementation).
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_FLAT_OPPONENT_FIELD_FINDINGS_v2.3.md
(new, docs-only, untracked; over committed edge 0d8722e, synthesizing the accepted v2.3 reporting/guard-only harness).

Verify that this synthesis:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen-capture/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED;
  and opens NO flat-geometry and NO screen-analysis implementation;
- records the result correctly: v2.3 GENERATED the accepted flat opponent-field panels A-F with structural booleans
  and completeness-enforced guards but did NOT validate flat opponent-field geometry; outcome
  FLAT_OPPONENT_FIELD_REPORTING_GENERATED; flat_field_validated = False; protocol_ok means required panels + guards
  present ONLY, not validation / closure / descriptor validity / vision;
- records the guard-completeness result (§6): a missing OR True required authorization flag (or absent guard_present)
  forces protocol_ok False / invalid_protocol_breach, so the non-authorization guard cannot be weakened by omission;
- states that v2.3 ADOPTS NO descriptor / coordinate system / metric / equation / threshold / pass-fail rule, redefines
  no TOL, redesigns no descriptor, expands no family, reopens no spectral group; A-F are structural reporting checks,
  not validity gates;
- reports the validation faithfully (21 targeted passed; full tests/research 413 passed; reporting generated;
  flat_field_validated False; locks False False False; verdict HOLD; guard probe rejects missing/True/absent-guard);
- keeps v1.x as FROZEN EVIDENCE and v2.x UNVALIDATED, leaves vision / descriptor validity / temporal order / closure /
  flat-field-superiority UNPROVEN, recommends Branch A (v2.4 minimal synthetic fixture proposal, docs-only; no fixture
  implemented; adopts nothing), and lists B/C/D;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted descriptor / coordinate system / metric / equation / threshold / pass-fail rule, any TOL
redefinition, any family expansion, any spectral reopening, any flat-geometry / screen-analysis / camera / live /
real-clip / runtime / memory authorization, any "Brainvision sees" / vision / descriptor-validity / temporal-order
claim, any claim that flat opponent-field is validated, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Flat Opponent-Field Findings v2.3. Docs-only synthesis of a reporting/guard-only
implementation. Opens no implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no
frozen formula, gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no
threshold; redefines no TOL; adopts no descriptor / coordinate system / metric / equation; records the accepted flat
opponent-field panels A-F as GENERATED (structural, conceptual) but the abstraction as UNVALIDATED and flat_field_
validated False, with a completeness-enforced non-authorizing guard; preserves v1.x as frozen evidence and v2.x as an
unvalidated conceptual pivot; makes no vision / "Brainvision sees" / descriptor-validity / temporal-order / memory /
runtime / integration claim; no `§0` pointer added; no tags.*
