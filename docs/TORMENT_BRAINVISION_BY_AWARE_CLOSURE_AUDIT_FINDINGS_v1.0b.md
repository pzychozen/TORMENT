# TORMENT Brainvision BY-Aware Closure Audit Findings v1.0b

## 1. Status / non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY, NON-LEARNING form-A audit.** It records what the v1.0b
BY-aware closure audit produced. It presents the v1.0a panels A-G (A-F from v0.9b plus the new non-authorizing
panel G); it does **not** adopt a closure metric, introduce a pass/fail gate, invent a threshold, **redefine
`TOL`**, change the evaluator / control, redesign the descriptor, reopen spectral, expand a family, or open a
classifier (form B) / neural encoder (form C). It reruns / replaces **no** sample and adds **no** seed / family
/ candidate generation. It does **not** pivot to flat / screen geometry and opens **no** screen-analysis /
flat-geometry implementation. It is not corrective: it does **not** try to make Brainvision pass or close BY.

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

## 2. Inputs and delivered files

```text
v0.9b (11a1997)  BY closure visibility AUDIT -> BY_visibility_confirmed (panels A-F).
v0.9c (c17ec74)  synthesis: visibility CONFIRMED, NOT closure.
v1.0  (3738c73)  BY-aware closure STRUCTURE proposal: requirements A-G, adopting none.
v1.0a (3013f85)  BY-aware closure AUDIT PLAN: reporting-only panels A-G over existing records.

Delivered UNCOMMITTED over HEAD 3013f85 (form A, non-learning, reporting-only; reuses v0.9b -- which reuses
v0.8a, which reproduces v0.7b by identity):
  research/brainvision/run_by_aware_closure_audit_v1_0b.py
  tests/research/test_brainvision_by_aware_closure_audit_v1_0b.py
```

## 3. What was implemented

A single reporting-only audit that reuses the v0.9b visibility audit (which reuses v0.8a, which reproduces the
v0.7b sealed matching by identity) and re-presents its panels A-F, then adds the new **non-authorizing panel G**
(requirement G of v1.0): an explicit, structured statement that the BY visibility is diagnostic-only and
authorizes nothing. It adds no data and computes no new statistic; it introduces no metric, no threshold, and no
pass/fail gate. If the underlying v0.9b run breaches, fails to reproduce v0.7b, or returns incomplete panels
(the routes non-finite / extreme values take), the audit returns `invalid_protocol_breach` and can never produce
a visibility confirmation.

## 4. Result — BY_aware_visibility_confirmed (honest, NOT tuned)

```text
reuses v0.7b/v0.8a/v0.9b records: True   protocol_ok = True   new_closure_metric_adopted = False   pass_fail_gate = False
visibility_is_non_authorizing = True     outcome = BY_aware_visibility_confirmed

Panel A (signed-offset)   by_std +0.04505 (0.95)   by_centroid -0.03393 (0.90)   by_spread -0.02935 (0.84)
Panel B (BY-vs-RG)        by_dominant_over_rg = True
Panel C (binding)         by_binding {by_std 10, by_spread 1, by_centroid 1}   fraction 0.6316 > share 0.30
Panel D (region/family)   region by_centroid BA: speed 0.75, phase 1.00, radius 1.00 ; single_matching_family_caveat True
Panel E (coupling/leakage) dominant_mechanism = BY_axis_asymmetry (coupling / amplitude weak)
Panel F (aggregation warn) aggregation_warning = True
Panel G (non-authorizing)  visibility_is_diagnostic_only = True ; authorizes_descriptor_validity / pass_fail / closure /
                           runtime / memory / integration / vision / flat_geometry / screen_analysis = all False
```

**Reading (research-only).** Panels A-G make the systematic BY opponent-axis offset **explicitly visible** (the
signed, sign-consistent, BY-dominant, often-binding class-level offset that coexists with the passing per-pair
residual / `TOL` closure; coupling and amplitude weak; single-matching-family caveat preserved) **and record, in
the audit itself (G), that this visibility is diagnostic-only** — it authorizes no descriptor validity, pass/fail,
closure, runtime, memory, integration, vision, flat-geometry, or screen-analysis. Outcome:
**`BY_aware_visibility_confirmed`**. This confirms **visibility**, not **closure**: the offset still survives the
residual / `TOL` match exactly as before. It establishes **no** vision, descriptor validity, or real-world
property (§9), and moves no claim lock and no verdict.

## 5. Panel outputs (v1.0a mapping)

```text
A. Signed-offset representation      -> per-BY signed offset + sign consistency + dominant sign.
B. Opponent-axis dominance           -> BY vs RG vs directional magnitudes; BY_dominant flag.
C. Binding-stat representation       -> L-inf binding distribution, by_std/by_spread/by_centroid separated, vs share.
D. Aggregation-warning               -> flags per-pair TOL closure coexisting with a systematic BY signed ordering.
E. Coupling/leakage separation       -> coupling and amplitude vs the mechanism scores (axis-asymmetry dominant).
F. Region/family caveat              -> region concentration + family distribution + single-matching-family caveat.
G. Non-authorizing visibility        -> explicit statement + flags: visibility is diagnostic-only, authorizes nothing.
```

## 6. Non-finite handling and no-decision guarantee

Non-finite / extreme values are not admissible evidence: they are excluded upstream (v0.8a / v0.9b short-circuit
via the frozen `_is_clean`), and if the underlying v0.9b run breaches, fails to reproduce v0.7b, or returns
incomplete panels, v1.0b returns `invalid_protocol_breach` and computes no confirmation. The visibility outcome
(confirmed / partial / inconclusive) is a **reporting label** about whether the panels surface the offset — it
is **not** a Brainvision pass, **not** a closure decision, and it changes **no** verdict (HOLD under every
outcome) and **no** claim lock. Panel G records this non-authorization explicitly.

## 7. Outcome taxonomy (all leave claim locks unchanged)

```text
BY_aware_visibility_confirmed    panels A-G make the offset explicitly visible, with the non-authorizing statement (G)   (THIS RUN)
BY_aware_visibility_partial      some panels surface the offset while others are limited
BY_aware_visibility_inconclusive the panels do not surface the offset from these records
invalid_protocol_breach          non-reproduction / non-finite / incomplete panels -> no evidential weight
```

## 8. Tests run

```text
python -m pytest tests/research/test_brainvision_by_aware_closure_audit_v1_0b.py -q  -> 13 passed
python research/brainvision/run_by_aware_closure_audit_v1_0b.py                       -> ran clean (result above)
python -m pytest tests/research -q                                                    -> 325 passed, 1 failed (sandbox)
```

The single full-suite failure is the pre-existing, documented `spectral_centroid` Linux/Windows knife-edge in
`test_brainvision_color_structure_pooled_gate_audit_v1_8.py` (green on Windows; unrelated to v1.0b). The v1.0b
tests assert only platform-independent robust facts: reuse of the v0.7b / v0.8a / v0.9b records by identity (no
sample replacement / new seeds / families / candidate generation); `TOL` / thresholds / descriptor / `GROUPS`
unchanged; no new closure metric and no pass/fail gate; spectral audit-note-only; panels A-G present; the panel
G non-authorization flags all False; outcome from the sealed labels; non-finite / breach cannot become evidence;
and claim locks stay False with verdict HOLD. Windows pytest is the source of truth.

## 9. Claim locks and verdict

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
frozen_brainvision_verdict                  = HOLD   (untouched)
vision_claim = False   memory_readiness_claim = False   runtime_readiness_claim = False
integration_readiness_claim = False
```

Making the BY-axis offset visible (and recording that the visibility is non-authorizing) is an in-vitro,
metric-level reporting step within the same family set; it moves no lock and no verdict, and is not descriptor
validity or vision evidence. The wall is **visible, not closed**.

## 10. Recommended next (not opened here)

- **Codex review** this findings receipt + the harness / tests.
- **If accepted,** the operator runs the Windows suite and commits. The BY-axis offset is now visible in an
  A-G panel layer that also records its own non-authorization. The remaining forks are **separate, future,
  docs-first** decisions (not opened here): a **BY-aware closure metric pre-registration** (candidate metric
  components before any code, no threshold adopted), a **flat opponent-plane / spatial field geometry** framing,
  or an **operator / new-math** note. Or **HOLD**. No code, classifier (B), neural (C), real clips, runtime,
  memory, screen, flat-geometry, `§0`, or tags are recommended here.

## 11. Codex review prompt

```text
Please review the v1.0b BY-aware closure audit:
  research/brainvision/run_by_aware_closure_audit_v1_0b.py
  tests/research/test_brainvision_by_aware_closure_audit_v1_0b.py
  docs/TORMENT_BRAINVISION_BY_AWARE_CLOSURE_AUDIT_FINDINGS_v1.0b.md
(new, UNCOMMITTED, over committed edge 3013f85; implements the v1.0a plan panels A-G).

Verify that this slice:
- is offline research only (research/brainvision + tests/research + one findings doc); no torment_service, no
  runtime / memory / camera / sensor / streaming, no real clips; NO classifier (form B) / neural encoder (form C);
- is REPORTING-ONLY: it presents panels A-G and DECIDES nothing; the visibility outcome (confirmed/partial/
  inconclusive) is a reporting label, NOT a Brainvision pass, NOT a closure decision, and changes no verdict (HOLD)
  and no claim lock;
- ADOPTS NO new closure metric, introduces NO pass/fail gate, invents NO threshold, REDEFINES NO TOL, redesigns no
  descriptor, expands no family, reopens no spectral group;
- reuses the v0.7b / v0.8a / v0.9b records BY IDENTITY (via v0.9b, which reuses v0.8a, which reproduces the v0.7b
  matching), with NO sample replacement / new seeds / new families / new candidate generation;
- presents panels A-F re-presented from v0.9b and adds the NON-AUTHORIZING panel G whose flags
  (authorizes_descriptor_validity / pass_fail / closure / runtime / memory / integration / vision / flat_geometry /
  screen_analysis) are ALL False, with visibility_is_diagnostic_only True;
- reports BY_aware_visibility_confirmed without forcing it, and confirms VISIBILITY not CLOSURE (the offset still
  survives the residual/TOL match);
- forces invalid_protocol_breach on non-finite / breach / non-reproduction / incomplete panels so they never become
  evidence;
- does NOT pivot to flat / screen geometry, does NOT prove Brainvision / validate the descriptor, does NOT move claim
  locks or authorize runtime/memory/integration; preserves all claim locks
  (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; no §0; no tags.

Flag any adopted metric / threshold / pass-fail gate, any TOL redefinition, any descriptor redesign, any sample
replacement / new family, any flat-geometry / screen-analysis authorization, any panel-G flag set True, any claim
that the wall is CLOSED (vs visible), any non-finite value that could become evidence, or any claim-lock/verdict
movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Aware Closure Audit Findings v1.0b. Reporting-only, non-learning; offline research.
Changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no control; redesigns no descriptor;
invents no threshold; redefines no TOL; adopts no closure metric; introduces no pass/fail gate; reruns / replaces
no sample; keeps the wall visible not closed and records its visibility as non-authorizing; opens no classifier /
neural / screen / flat-geometry / runtime / memory / real-clip work; makes no vision / descriptor-validity /
temporal-order / memory / runtime / integration claim; no `§0` pointer; no tags.*
