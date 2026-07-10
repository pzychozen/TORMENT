# TORMENT Brainvision BY-Aware Closure Findings v1.5

## 1. Status / non-claims

**DOCS-ONLY findings synthesis for a REPORTING/GUARD-ONLY, NON-LEARNING form-A implementation.** It records what
the v1.5 BY-aware closure audit established and did **not** establish. It is a synthesis of an already-accepted,
already-committed harness (`cb2c8fd`); it opens **no** code, tests, runtime, or integration lane and is not
corrective. The v1.5 harness implemented the v1.4-preregistered A + D + G reporting/guard structure (B / C / E
report-only) as diagnostic output; it does **not** adopt a closure metric, define an equation, introduce a
pass/fail validity gate, invent a threshold, **redefine `TOL`**, create an offset-vs-`TOL` gate or a binding gate,
change the evaluator / control, redesign the descriptor, reopen spectral as a closure group, expand a generator
family, or open a classifier (form B) / neural encoder (form C). It reran / replaced **no** sample and added
**no** seed / family / candidate generation. It does **not** pivot to flat / screen geometry and opens **no**
flat-geometry / screen-analysis implementation. Everything stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6.

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

## 2. Relation to v1.4 / v1.4a / v1.5

```text
v1.4  (da946ed)  finite audit PREREGISTRATION: A + D + G reporting obligations + structural acceptance checks;
                 B / C / E report-only; adopting none; authorizing no code.
v1.4a (86cb1f7)  implementation AUTHORIZATION review: defined the EXACT v1.5 boundary; recommended authorizing v1.5
                 only on Codex acceptance + explicit operator approval.
v1.5  (cb2c8fd)  A + D + G spine HARNESS: generated the preregistered reporting/guard structure; reuses v1.2 by
                 identity; accepted as-is (after a Codex P1 fix making guard completeness enforced).
v1.5  (this doc) findings synthesis: records what v1.5 established and did NOT establish.
```

v1.4 fixed WHAT a conformant audit must report and what makes its protocol acceptable; v1.4a fixed the exact
implementation boundary; v1.5 implemented that boundary as a reporting/guard-only harness. This synthesis is a
receipt over that implementation. It does not prove Brainvision, validate the descriptor, adopt a metric, or
select flat / screen geometry, and it changes nothing v0.4b / v0.4c / v0.7a froze or v0.7b / v0.8a / v0.9b /
v1.0b / v1.2 produced.

## 3. What v1.5 implemented

The v1.5 harness (`research/brainvision/run_by_aware_closure_audit_v1_5.py`, with
`tests/research/test_brainvision_by_aware_closure_audit_v1_5.py`) is a form-A, non-learning, reporting/guard-only
audit that reuses the accepted v1.2 audit **by identity** (v1.2 reuses v1.0b -> v0.9b -> v0.8a -> the v0.7b sealed
matching) and re-expresses its panels under the explicit v1.4 A + D + G spine framing:

```text
PRIMARY SPINE (v1.3a-selected, v1.4-preregistered):
  A signed BY offset       : per-BY sign direction + sign consistency + |offset| relative to the frozen TOL as a
                             DESCRIPTIVE reference (reused |smd|/TOL by identity); offset_vs_tol_gate = False.
  D aggregation anti-hiding : whether group residual/TOL matching COEXISTS with a systematic BY signed ordering;
                             hidden_closure_claim = False (hidden closure impossible in the reporting).
  G non-authorizing guard  : all NINE authorization flags present and False; ANY missing OR True -> protocol_ok False.
SUPPORT (report-only; never a gate):
  B BY/RG opponent-balance | C binding-aware residual partition (residual frozen) | E region/family stratified
  (single-family caveat); plus the coupling/leakage panel as background context.
```

It adopts no closure metric, no equation, no threshold, no pass/fail validity gate, no offset-vs-`TOL` gate, and
no binding gate; it redefines no `TOL`, redesigns no descriptor, expands no family, and reopens no spectral group.
`protocol_ok` means only that the required A + D + G reporting and the guard are present — **not** closure.
`closure_achieved` is hard-wired False; the output is deterministic; non-finite / breach / non-reproduction / a
missing-or-authorizing guard force `invalid_protocol_breach`.

## 4. Validation summary

```text
targeted v1.5 tests   : 26 passed
v1.5 script           : emits BY_aware_closure_gap_still_visible ; protocol_ok True ; closure_achieved False
guard-probe           : a missing OR authorizing guard flag -> protocol_ok False (guard_missing_or_authorizing)
reuse-chain tests     : v0.8a / v0.9b / v1.0b / v1.2 unchanged (green)
full tests/research    : 372 passed
claim locks / verdict : locks False False False ; verdict HOLD (unchanged)
```

The tests assert only platform-independent robust facts: reuse of the v0.7b / v0.8a / v0.9b / v1.0b / v1.2 records
by identity (no sample replacement / new seeds / families / candidate generation); `TOL` / thresholds / descriptor
/ `GROUPS` unchanged; no new closure metric, no pass/fail gate, no offset-vs-`TOL` or binding gate; spectral
audit-note-only; the A + D + G spine present; the guard exposing all nine v1.1a flags all False, with ANY missing
OR True flag forcing `invalid_protocol_breach`; B / C / E report-only; a deterministic, conservative,
never-closure label; and claim locks staying False with verdict HOLD. Windows pytest is the source of truth.

## 5. Main result

```text
OUTCOME_LABEL: BY_aware_closure_gap_still_visible     closure_achieved = False     verdict = HOLD

PRIMARY SPINE
  A signed-offset (offset_vs_tol_gate = False)
     by_std      +0.04505  sign_consistency 0.95  dominant +  |offset|/TOL 0.71
     by_centroid -0.03393  sign_consistency 0.90  dominant -  |offset|/TOL 0.54
     by_spread   -0.02935  sign_consistency 0.84  dominant -  |offset|/TOL 0.46
  D aggregation coexistence = True   hidden_closure_claim = False
  G guard diagnostic-only = True     all nine authorization flags = False
SUPPORT (report-only; gate = False)
  B by_dominant_over_rg = True   C binding_gate_introduced = False   E single_matching_family_caveat = True

by_wall_persists = True
```

**v1.5 successfully implemented the preregistered A + D + G BY-aware reporting/guard structure with B / C / E
report-only support, but it did not establish closure.** The outcome is **`BY_aware_closure_gap_still_visible`** —
the systematic BY opponent-axis offset still survives the residual / `TOL` match (signed, sign-consistent,
BY-dominant, often-binding, aggregation-warning), so the wall is **visible, not closed**. Implementing the
preregistered structure moves **no** claim lock and **no** verdict.

## 6. Guard completeness result

```text
The G guard is now COMPLETENESS-ENFORCED (Codex P1 fix, accepted): admissibility requires that the guard is
diagnostic-only, that EVERY authorization flag it carries is False, AND that all NINE v1.1a-required flags
(descriptor_validity, temporal_order, pass_fail, closure, runtime, memory, integration, live_or_screen_use, vision)
are PRESENT and False.
  - real run: all nine present and False -> guard admissible -> protocol_ok True (reporting present, NOT closure).
  - probe (any flag True): -> protocol_ok False, invalid_protocol_breach (guard_missing_or_authorizing).
  - probe (any required flag ABSENT, e.g. temporal_order deleted): -> protocol_ok False, invalid_protocol_breach.
This confirms the non-authorizing guard cannot be silently weakened by omission OR by an authorizing flag; a
degraded guard can never produce a reporting result, closure, pass, validity claim, or claim / verdict movement.
```

## 7. Interpretation

```text
- v1.5 is the FIRST implemented, boundary-conformant realisation of the v1.4 preregistration: the A + D + G spine
  named in v1.3a and preregistered in v1.4 is now GENERATED as reporting/guard output that, by construction,
  cannot let BY_axis_asymmetry hide UNREPRESENTED inside residual / TOL matching, and cannot silently drop its
  non-authorization guard.
- The reporting works AS DESIGNED and the honest reading is negative-for-closure: under the A + D + G structure the
  BY wall PERSISTS (by_wall_persists = True). This is evidence about the DESCRIPTOR SURFACE, not about Brainvision,
  vision, or the descriptor's validity. It is an in-vitro, single-matching-family, metric-level observation.
- A + D + G are REPORTING / STRUCTURAL checks, not validity gates: A reports the signed offset (no offset-vs-TOL
  gate), D reports the residual/TOL-vs-ordering coexistence (no validity gate, hidden closure impossible), G is a
  standing non-authorization guard. protocol_ok = presence of required reporting + guards; it is NOT closure.
- B / C / E remain report-only support and were not promoted to gates.
```

## 8. Why this is not closure

```text
- CLOSURE would require a represented DECISION under which the systematic, signed, BY-dominant, often-binding
  offset could NOT pass while the classes stay ordered. v1.5 adopts NO such decision: no metric, no equation, no
  threshold, no pass/fail validity gate, no offset-vs-TOL or binding gate, no TOL change. It only REPORTS + GUARDS.
- protocol_ok = True means only that the required A + D + G reporting and guard are PRESENT; it is explicitly NOT a
  closure, a pass, or a validity statement (closure_achieved is hard-wired False; the label set has no closure-
  positive label).
- The residual / TOL match is unchanged and still passes every matched pair; the offset still coexists with it
  (D aggregation coexistence = True). Reporting that coexistence, and refusing hidden closure, is visibility, not closure.
- The observation rests on a SINGLE matching family (segment_paired_canceller); the caveat is preserved (E), not
  engineered away. A single-family, in-vitro reporting result cannot be closure by construction.
```

## 9. What remains frozen

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator (structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR).
- the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual (L-inf over the ten matched stats, spectral excluded) and PSC < PSC_FLOOR feasibility.
- the closed F1-F5 family set; the single matching family (segment_paired_canceller); the v0.7b samples;
  spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a / v0.9b / v1.0b / v1.2 records reused by identity; no sample replacement / new seeds / candidate generation.
- claim locks and verdict HOLD.
v1.5 changed none of the above; this synthesis changes none of the above.
```

## 10. What remains unproven

Even with the A + D + G structure implemented and the gap shown to persist, all of the following stay
**unproven**:

```text
not vision                     not "Brainvision sees"
not descriptor validity        not temporal order
not real-video understanding   not a unique real-world color-structure advantage
not memory readiness           not runtime readiness           not integration readiness
not closure                    (the gap is visible; it is not closed)
```

The proof route remains **HELD / HOLD** because the BY offset is visible but not closed. The claim locks
(`first_pass_structure_validity_claim_allowed`, `temporal_claim_allowed`, `descriptor_validity_claim_allowed`)
and `verdict = HOLD` remain in force.

## 11. Next branch options

Docs-first / tightly-bounded candidates only; **none opened or authorized here**:

```text
A. v1.6 CLOSURE FAILURE ANATOMY (docs-first or tightly-bounded reporting-only diagnostic)
   Inspect WHY the A + D + G spine still reports the gap as visible -- what, structurally, keeps the offset
   surviving residual / TOL matching -- WITHOUT adopting a metric / equation / threshold / gate. ONE more anatomy
   step only.

B. FLAT OPPONENT-PLANE / SPATIAL-FIELD proposal (docs-only)
   Consider whether the PERSISTENT BY-axis failure indicates the current FIXTURE ABSTRACTION is wrong -- i.e.
   whether a flat opponent-plane / spatial-field framing would represent the opponent-axis structure better.
   Conceptual only; NO flat-geometry / screen-analysis implementation.

C. Operator / new-math NOTE (docs-only), or
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 12. Recommended next step

**Recommend Branch A (v1.6 closure failure anatomy) next — but ONE more anatomy step only.** v1.5 shows the gap
persists under the preregistered structure; the next clean move is a single, tightly-bounded anatomy of WHY the
A + D + G spine still reports the gap as visible — docs-first or reporting-only, adopting nothing. **If v1.6 still
shows the same wall without surfacing a new lever, pivot to Branch B (flat opponent-plane / spatial-field
proposal)** rather than iterate anatomy further or force a metric. C (operator new-math) and D (pause) remain
legitimate operator calls.

```text
1. Codex review THIS findings synthesis (docs-only; over committed edge cb2c8fd).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future v1.6 closure-failure-anatomy step
   (docs-first or tightly-bounded reporting-only; no metric / equation / threshold / gate / descriptor / family /
   spectral / flat / screen / runtime / memory adopted). If v1.6 finds no new lever, pivot to Branch B.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 13. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_AWARE_CLOSURE_FINDINGS_v1.5.md
(new, docs-only, untracked; over committed edge cb2c8fd, synthesizing the accepted v1.5 reporting/guard-only harness).

Verify that this synthesis:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED; and
  authorizes NO flat-geometry and NO screen-analysis implementation;
- records the result correctly: v1.5 IMPLEMENTED the preregistered A + D + G reporting/guard structure (B / C / E
  report-only) but did NOT establish closure; the outcome is BY_aware_closure_gap_still_visible; closure_achieved =
  False; protocol_ok means required reporting + guards present ONLY, not closure;
- records the guard-completeness result (§6): a missing OR authorizing guard flag forces protocol_ok False /
  invalid_protocol_breach (the accepted Codex P1 fix), so the non-authorization guard cannot be weakened by omission;
- states that v1.5 ADOPTS NO closure metric / equation / threshold / pass-fail validity gate / offset-vs-TOL gate /
  binding gate, REDEFINES NO TOL, redesigns no descriptor, expands no family, reopens no spectral group; reuses
  v0.7b/v0.8a/v0.9b/v1.0b/v1.2 by identity; A + D + G are reporting/structural checks not validity gates; B / C / E
  remain report-only;
- reports the validation faithfully (26 targeted passed; full tests/research 372 passed; gap_still_visible;
  closure_achieved False; locks False False False; verdict HOLD; missing-guard probe breaches);
- frames the result as an in-vitro, single-matching-family, descriptor-surface observation that authorizes nothing,
  and leaves vision / descriptor validity / temporal order / real-video / memory / runtime / integration / closure
  UNPROVEN;
- recommends Branch A (v1.6 closure failure anatomy) next but ONE step only, pivoting to Branch B (flat opponent-plane
  / spatial-field) if v1.6 shows the same wall without a new lever; lists C/D;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted metric / equation / threshold / pass-fail rule, any TOL redefinition, any offset-vs-TOL / binding
gate, any descriptor redesign, any family expansion, any spectral reopening as a closure group, any B / C / E
promotion, any flat-geometry / screen-analysis / runtime / memory / real-clip authorization, any claim that closure
is ACHIEVED (vs the gap being visible), any descriptor-validity / vision / temporal-order claim, or any claim-lock/
verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Aware Closure Findings v1.5. Docs-only synthesis of a reporting/guard-only
implementation. Opens no implementation lane; opens no classifier / neural / screen / flat-geometry work; changes
no frozen formula, gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no
threshold; redefines no TOL; adopts no closure metric or equation; creates no offset-vs-TOL or binding gate; records
the preregistered A + D + G structure as IMPLEMENTED but the gap as VISIBLE not CLOSED, with a completeness-enforced
non-authorizing guard; makes no vision / descriptor-validity / temporal-order / memory / runtime / integration
claim; no `§0` pointer added; no tags.*
