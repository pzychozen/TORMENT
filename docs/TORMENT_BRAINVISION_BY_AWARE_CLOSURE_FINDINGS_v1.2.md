# TORMENT Brainvision BY-Aware Closure Findings v1.2

## 1. Status / non-claims

**DOCS-ONLY findings synthesis for a REPORTING-ONLY, NON-LEARNING form-A diagnostic.** It records what the v1.2
BY-aware closure audit established and did **not** establish. It is a synthesis of an already-accepted,
already-committed harness (`b8062c4`); it opens **no** code, tests, runtime, or integration lane and is not
corrective. The v1.2 harness generated the preregistered BY-aware reporting obligations (panels A-G from v1.1 /
v1.1a) as diagnostic output; it does **not** adopt a closure metric, define an equation, introduce a pass/fail
gate, invent a threshold, **redefine `TOL`**, change the evaluator / control, redesign the descriptor, reopen
spectral as a closure group, expand a generator family, or open a classifier (form B) / neural encoder (form C).
It reran / replaced **no** sample and added **no** seed / family / candidate generation. It does **not** pivot to
flat / screen geometry and opens **no** flat-geometry / screen-analysis implementation. Everything stays offline
under `research/brainvision/` + `tests/research/`, HELD per v0.6.

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

## 2. Relation to v1.1 and v1.1a

```text
v1.0b (e083bb4)  BY-aware closure AUDIT FINDINGS -> BY_aware_visibility_confirmed (panels A-G; verdict HOLD).
v1.1  (45be17d)  BY-aware closure PREREGISTRATION proposal: what a future prereg must CONTAIN (components A-G),
                 accepted as-is; docs-only; adopting none.
v1.1a (f6cf3c5)  BY-aware closure PREREGISTRATION plan: what a future reporting-only audit must REPORT, over which
                 frozen records, and what it may never claim; accepted as-is; docs-only; adopting none.
v1.2  (b8062c4)  BY-aware closure audit HARNESS: generates the preregistered obligations A-G as diagnostic output;
                 accepted as-is; reporting-only; adopting none. Result: BY_aware_closure_gap_visible.
v1.2  (this doc) findings synthesis: records what v1.2 established and did NOT establish.
```

v1.1 defined the preregistration components; v1.1a turned them into a concrete, finite reporting plan; v1.2
implemented that plan as a reporting-only harness. This synthesis is a receipt over that implementation. It does
not prove Brainvision, validate the descriptor, adopt a metric, or select flat / screen geometry, and it changes
nothing v0.4b/v0.4c/v0.7a froze or v0.7b/v0.8a/v0.9b/v1.0b produced.

## 3. What v1.2 implemented

The v1.2 harness (`research/brainvision/run_by_aware_closure_audit_v1_2.py`, with
`tests/research/test_brainvision_by_aware_closure_audit_v1_2.py`) is a form-A, non-learning, reporting-only audit
that reuses the v1.0b audit **by identity** (v1.0b reuses v0.9b -> v0.8a -> the v0.7b sealed matching) and
re-presents its panels A-G under the v1.1a obligation framing:

```text
A signed-offset : per-BY sign direction + sign consistency + |offset| relative to the frozen TOL as a
                  DESCRIPTIVE effect-size reference (reused |smd|/TOL, by identity); offset_vs_tol_gate = False.
B BY dominance  : BY effects compared against RG and directional features; visibility evidence only.
C binding       : whether BY stats (esp. by_std) bind the residual match, vs proportional share; no binding gate.
D aggregation   : whether per-pair residual/TOL closure COEXISTS with a systematic BY ordering; no hidden closure.
E coupling/leak : BY_axis_asymmetry kept separate from centroid/spread coupling and amplitude leakage.
F region/family : single-matching-family caveat + per-region BY visibility; no generator-family expansion.
G guard         : all NINE v1.1a authorization flags present and False (diagnostic-only).
```

It adopts no closure metric, no equation, no threshold, no pass/fail gate; it redefines no `TOL`, redesigns no
descriptor, expands no family, and reopens no spectral group. It emits a **conservative** outcome label and
hard-wires `closure_achieved = False`; non-finite / breach / a broken (authorizing) guard force
`invalid_protocol_breach` and can never become evidence.

## 4. Validation summary

```text
targeted v1.2 tests   : 21 passed
v1.2 script           : emits BY_aware_closure_gap_visible ; protocol_ok True ; closure_achieved False
reuse-chain tests     : v0.8a / v0.9b / v1.0b unchanged (green)
full tests/research    : 346 passed
claim locks / verdict : locks False False False ; verdict HOLD (unchanged)
```

The tests assert only platform-independent robust facts: reuse of the v0.7b / v0.8a / v0.9b / v1.0b records by
identity (no sample replacement / new seeds / families / candidate generation); `TOL` / thresholds / descriptor /
`GROUPS` unchanged; no new closure metric and no pass/fail gate; spectral audit-note-only; panels A-G present;
guard G exposing all nine v1.1a flags all False (with any authorizing flag forcing `invalid_protocol_breach`);
the conservative label never being a closure; and claim locks staying False with verdict HOLD. Windows pytest is
the source of truth.

## 5. Main result

```text
OUTCOME_LABEL: BY_aware_closure_gap_visible        closure_achieved = False        verdict = HOLD

Panel A (signed-offset)   by_std +0.04505 (0.95) |offset|/TOL 0.71   by_centroid -0.03393 (0.90) 0.54
                          by_spread -0.02935 (0.84) 0.46             offset_vs_tol_gate = False
Panel B (BY-vs-RG)        by_dominant_over_rg = True (visibility evidence only)
Panel C (binding)         by_binding {by_std 10, by_spread 1, by_centroid 1}  above_share = True  binding_gate = False
Panel D (aggregation)     aggregation_warning = True  hidden_closure_claim = False
Panel E (coupling/leak)   dominant_mechanism = BY_axis_asymmetry (coupling / amplitude weak)
Panel F (region/family)   single_matching_family_caveat = True  generator_family_expansion_authorized = False
Panel G (guard)           visibility_is_diagnostic_only = True ; all nine authorization flags = False

gap_criteria all True -> by_wall_persists = True
```

**The preregistered BY-aware reporting structure was successfully generated, but it did not establish closure.**
The result is **`BY_aware_closure_gap_visible`** — the systematic BY opponent-axis offset still survives the
residual / `TOL` match (signed, sign-consistent, BY-dominant, often-binding, aggregation-warning), so the wall is
**visible, not closed**. Making the gap visible in the preregistered A-G structure moves **no** claim lock and
**no** verdict.

## 6. Interpretation

```text
- v1.2 delivers the FIRST implemented, preregistration-conformant view of the BY offset: the offset that was
  named in v0.8a, made visible in v0.9b, re-presented with a non-authorizing guard in v1.0b, and preregistered
  in v1.1 / v1.1a is now GENERATED as diagnostic output that, by construction, cannot let BY_axis_asymmetry hide
  UNREPRESENTED inside residual / TOL matching.
- The reporting works AS DESIGNED and the honest reading is negative-for-closure: under the preregistered
  structure the BY wall PERSISTS. This is evidence about the DESCRIPTOR SURFACE, not about Brainvision, vision,
  or the descriptor's validity. It is an in-vitro, metric-level, single-family observation.
- The guard (G) records, in the audit itself, that this visibility authorizes nothing: not descriptor validity,
  not temporal order, not pass/fail, not closure, not runtime / memory / integration, not live / screen use, not
  vision. The gap being visible is diagnostic; it is not a step toward any of those.
```

## 7. Why this is not closure

```text
- CLOSURE would require a represented decision under which the systematic, signed, BY-dominant offset could NOT
  pass while the classes stay ordered. v1.2 adopts NO such decision: no metric, no equation, no threshold, no
  pass/fail gate, no TOL change. It only REPORTS.
- The residual / TOL match is unchanged and still passes every matched pair; the offset still coexists with it
  (aggregation_warning = True). Reporting that coexistence is visibility, not closure.
- closure_achieved is hard-wired False and the label set contains no closure-positive label; the conservative
  label BY_aware_closure_gap_visible explicitly names a PERSISTING gap, not a resolved one.
- The observation rests on a SINGLE matching family (segment_paired_canceller); the caveat is preserved, not
  engineered away. A single-family, in-vitro reporting result cannot be closure by construction.
```

## 8. What remains frozen

```text
- TOL = 0.0634; PSC_FLOOR = AIC_FLOOR = 0.30; CHANCE_BAND = 0.60 (referenced frozen; not re-thresholded).
- the frozen evaluator (structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR).
- the frozen descriptor / _stats / GROUPS / best-threshold BA / robustness lens.
- proxy_match_residual (L-inf over the ten matched stats, spectral excluded) and PSC < PSC_FLOOR feasibility.
- the closed F1-F5 family set; the single matching family (segment_paired_canceller); the v0.7b samples;
  spectral audit-note-only (NOT reopened as a closure group).
- the v0.8a / v0.9b / v1.0b records reused by identity; no sample replacement / new seeds / candidate generation.
- claim locks and verdict HOLD.
v1.2 changed none of the above; this synthesis changes none of the above.
```

## 9. What remains unproven

Even with the preregistered BY-aware reporting generated and the gap shown to persist, all of the following stay
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

## 10. Next branch options

Docs-first candidates only; **none opened or authorized here**:

```text
A. v1.3 BY-aware closure CANDIDATE DESIGN (docs-only)
   Now that the gap is visible under the preregistered structure, design possible CLOSURE CANDIDATES against
   A-G -- describe candidate components / decision shapes conceptually, still WITHOUT adopting a metric, an
   equation, a threshold, or a pass/fail rule. Docs-only; opens no code.

B. FLAT OPPONENT-PLANE / SPATIAL-FIELD proposal (docs-only)
   Consider whether the PERSISTENT BY wall means the fixture GEOMETRY itself is the wrong abstraction -- i.e.
   whether a flat opponent-plane / spatial-field framing would represent the opponent-axis structure better than
   the current fixtures. Conceptual only; NO flat-geometry / screen-analysis implementation.

C. Operator / new-math NOTE (docs-only), or
D. Pause Brainvision and return to TORMENT memory / kernel work.
```

## 11. Recommended next step

**Recommend Branch A (v1.3 BY-aware closure candidate design, docs-only) first, then Branch B.** v1.2 shows the
gap persists under the preregistered structure, so the next clean move is to use that structure to DESIGN closure
candidates (A) — conceptual, docs-only, adopting nothing — before questioning the fixture geometry (B). If A's
candidates cannot represent a decision that catches the offset without a new threshold or family, that is exactly
the signal to escalate to B (is the fixture geometry the wrong abstraction?). Taking A first keeps the work
grounded in the preregistered obligations; B is the right escalation only once A has been attempted. C (operator
new-math) and D (pause) remain legitimate operator calls.

```text
1. Codex review THIS findings synthesis (docs-only; over committed edge b8062c4).
2. If accepted, the operator commits this doc. No §0 pointer; no tags.
3. If the operator chooses to proceed, open Branch A as a SEPARATE, future, docs-first v1.3 candidate-design note
   (conceptual; no metric / equation / threshold / pass-fail / descriptor / family / spectral / flat / screen /
   runtime / memory adopted). Escalate to Branch B only if A cannot represent a candidate decision.
4. Otherwise the Brainvision prototype line stays HELD. No code, classifier (B), neural (C), runtime, memory,
   real-clip, screen, flat-geometry, §0, or tag work is recommended or authorized here.
```

Claim locks and verdict are unchanged: `first_pass_structure_validity_claim_allowed = False`,
`temporal_claim_allowed = False`, `descriptor_validity_claim_allowed = False`, `verdict = HOLD`.

## 12. Codex review prompt

```text
Please review docs/TORMENT_BRAINVISION_BY_AWARE_CLOSURE_FINDINGS_v1.2.md
(new, docs-only, untracked; over committed edge b8062c4, synthesizing the accepted v1.2 reporting-only harness).

Verify that this synthesis:
- is docs-only and authorizes no implementation (no code/tests, no torment_service/, no runtime, no memory, no
  camera/live/sensor/screen/streaming, no real clips); keeps form B (classifier) and form C (neural) CLOSED; and
  authorizes NO flat-geometry and NO screen-analysis implementation;
- records the result correctly: the preregistered BY-aware reporting structure was GENERATED but did NOT establish
  closure; the outcome is BY_aware_closure_gap_visible (the BY offset still survives residual/TOL matching), NOT
  closure achieved; closure_achieved = False;
- states that v1.2 ADOPTS NO closure metric / equation / threshold / pass-fail gate, REDEFINES NO TOL, redesigns no
  descriptor, expands no family, reopens no spectral group; reuses v0.7b/v0.8a/v0.9b/v1.0b by identity;
- reports the validation faithfully (21 targeted passed; full tests/research 346 passed; gap_visible;
  closure_achieved False; locks False False False; verdict HOLD);
- frames the result as an in-vitro, single-matching-family, descriptor-surface observation that authorizes nothing
  (guard G, all nine v1.1a flags False), and leaves vision / descriptor validity / temporal order / real-video /
  memory / runtime / integration / closure UNPROVEN;
- recommends Branch A (v1.3 BY-aware closure candidate design, docs-only) first, then Branch B (flat opponent-plane /
  spatial-field proposal, docs-only), opening neither, and lists C/D;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; adds no §0 pointer and no tags.

Flag any adopted metric / equation / threshold / pass-fail rule, any TOL redefinition, any descriptor redesign, any
family expansion, any spectral reopening as a closure group, any flat-geometry / screen-analysis / runtime / memory /
real-clip authorization, any claim that the wall is CLOSED (vs visible), any descriptor-validity / vision /
temporal-order claim, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Aware Closure Findings v1.2. Docs-only synthesis of a reporting-only harness. Opens
no implementation lane; opens no classifier / neural / screen / flat-geometry work; changes no frozen formula,
gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor; invents no threshold;
redefines no TOL; adopts no closure metric; defines no equation; records the preregistered reporting as GENERATED
but the gap as VISIBLE not CLOSED; makes no vision / descriptor-validity / temporal-order / memory / runtime /
integration claim; no `§0` pointer added; no tags.*
