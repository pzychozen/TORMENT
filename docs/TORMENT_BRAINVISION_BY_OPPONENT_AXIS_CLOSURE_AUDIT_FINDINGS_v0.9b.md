# TORMENT Brainvision BY Opponent-Axis Closure Audit Findings v0.9b

## 1. Status / non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY, NON-LEARNING form-A visibility audit.** It records what the
v0.9b BY opponent-axis closure visibility audit produced. It presents the v0.9a panels A-F; it does **not**
adopt a closure metric, introduce a pass/fail gate, invent a threshold, **redefine `TOL`**, change the evaluator
/ control, redesign the descriptor, reopen spectral, expand a family, or open a classifier (form B) / neural
encoder (form C). It reruns / replaces **no** v0.7b sample and adds **no** seed / family / candidate generation.
It does **not** pivot to flat / screen geometry and opens **no** screen-analysis / flat-geometry implementation.
It is not corrective: it does **not** try to make Brainvision pass or close BY.

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
v0.8a (8977248)  BY-channel metric anatomy -> BY_axis_asymmetry (systematic opponent-axis offset).
v0.8b (ea20804)  synthesis: sharpened the wall; flat geometry only a future framing.
v0.9  (6485e55)  BY opponent-axis closure PROPOSAL (candidate requirements A-F, adopting none).
v0.9a (3aba63d)  BY opponent-axis closure AUDIT PLAN (reporting-only panels A-F).

Delivered UNCOMMITTED over HEAD 3aba63d (form A, non-learning, reporting-only; reuses v0.8a -- which reproduces
v0.7b by identity):
  research/brainvision/run_by_opponent_axis_closure_audit_v0_9b.py
  tests/research/test_brainvision_by_opponent_axis_closure_audit_v0_9b.py
```

## 3. What was implemented

A single reporting-only audit that reuses the v0.8a anatomy (which reproduces the v0.7b sealed matching by
identity) and re-presents its quantities as the six dedicated v0.9a visibility panels. It adds no data and
computes no new statistic beyond re-organizing the v0.8a outputs; the visibility confirmation uses only natural
references (sign consistency vs the chance level 0.5; BY binding vs its proportional share of the ten matched
stats) and reused v0.8a booleans — no new numeric threshold, no closure metric, no pass/fail gate. Non-finite /
extreme values in a required panel value force `invalid_protocol_breach` and can never become evidence.

## 4. Result — BY_visibility_confirmed (honest, NOT tuned)

```text
reuses v0.8a (reproduces v0.7b): True   protocol_ok = True   new_closure_metric_adopted = False   pass_fail_gate = False
outcome = BY_visibility_confirmed

Panel A (signed-offset)   by_std +0.04505 (consistency 0.95)   by_centroid -0.03393 (0.90)   by_spread -0.02935 (0.84)
                          mean sign consistency 0.895
Panel B (BY-vs-RG)        BY_dominant = True   BY {by_std 0.71, by_centroid 0.54, by_spread 0.46}  >>  RG {0.00, 0.04}
Panel C (binding)         by_binding {by_std 10, by_spread 1, by_centroid 1}   fraction 0.6316 > share 0.30   (above_share)
Panel D (region/family)   region by_centroid BA: speed 0.75, phase 1.00, radius 1.00 ; family {segment_paired_canceller: 19}
                          single_matching_family_caveat = True (family comparison not assessable)
Panel E (coupling/leakage) coupling 0.031 ; amplitude {chroma_mag 0.29, rg_std 0.17} ; dominant_mechanism BY_axis_asymmetry
Panel F (aggregation warn) aggregation_warning = True (per-pair TOL closure coexists with systematic BY signed ordering)

offset visibility criteria: A_signed_and_systematic, B_by_dominant, C_by_binds_above_share,
                            E_axis_asymmetry_dominant, F_aggregation_warning, D_region_reported = all True
```

**Reading (research-only).** The panels make the systematic BY opponent-axis offset **explicitly visible in one
place**: the signed, sign-consistent, BY-dominant, often-binding class-level BY offset (A + B + C) coexists with
a per-pair residual / `TOL` closure that passes every matched pair (F flags this compression), while coupling and
amplitude leakage stay weak (E) — so `BY_axis_asymmetry` remains the best description. The single-matching-family
limitation (all 19 matches are `segment_paired_canceller`) is **surfaced as a caveat** in Panel D, not treated as
a visibility failure, because the offset itself is fully visible via A / B / C / E / F and the region panel.
Outcome: **`BY_visibility_confirmed`**. This is a reporting-layer result; it establishes **no** vision, descriptor
validity, closure, or real-world property (§9), and it moves no claim lock and no verdict.

## 5. Panel outputs (v0.9a mapping)

```text
A. Signed-offset panel           -> per-BY signed offset + sign consistency + dominant sign, plus the mean.
B. BY-vs-RG dominance panel       -> BY vs RG vs directional effect magnitudes; BY_dominant flag.
C. Binding-stat panel             -> L-inf binding distribution, by_std/by_spread/by_centroid separated, vs share.
D. Region/family panel            -> region concentration + family distribution + the single-family caveat.
E. Coupling/leakage separation    -> coupling and amplitude Spearman vs the mechanism scores (axis-asymmetry dominant).
F. Residual-aggregation warning   -> flags per-pair TOL closure coexisting with a systematic BY signed ordering.
```

## 6. Non-finite handling and no-decision guarantee

Non-finite / extreme values are not admissible evidence: if any required panel value is non-finite (checked via
the frozen `_is_clean`, or if the underlying v0.8a run breaches / fails to reproduce v0.7b), the audit returns
`invalid_protocol_breach` and computes no visibility confirmation. The visibility outcome
(confirmed / partial / inconclusive) is a **reporting label** about whether the panels surface the offset — it
is **not** a Brainvision pass, **not** a closure decision, and it changes **no** verdict (HOLD under every
outcome) and **no** claim lock.

## 7. Outcome taxonomy (all leave claim locks unchanged)

```text
BY_visibility_confirmed     panels A-F make the systematic BY offset explicitly visible   (THIS RUN)
BY_visibility_partial       some panels surface the offset while others are limited
BY_visibility_inconclusive  the panels do not surface the offset from these records
invalid_protocol_breach     non-reproduction / non-finite in a required panel -> no evidential weight
```

## 8. Tests run

```text
python -m pytest tests/research/test_brainvision_by_opponent_axis_closure_audit_v0_9b.py -q  -> 12 passed
python research/brainvision/run_by_opponent_axis_closure_audit_v0_9b.py                       -> ran clean (result above)
python -m pytest tests/research -q                                                            -> 311 passed, 1 failed (sandbox)
```

The single full-suite failure is the pre-existing, documented `spectral_centroid` Linux/Windows knife-edge in
`test_brainvision_color_structure_pooled_gate_audit_v1_8.py` (green on Windows; unrelated to v0.9b). The v0.9b
tests assert only platform-independent robust facts: reuse of the v0.7b / v0.8a records by identity (no sample
replacement / new seeds / families / candidate generation); `TOL` / thresholds / descriptor / `GROUPS`
unchanged; no new closure metric and no pass/fail gate; spectral audit-note-only; panels A-F present; outcome
from the sealed labels; non-finite values cannot become evidence; and claim locks stay False with verdict HOLD.
Windows pytest is the source of truth.

## 9. Claim locks and verdict

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
frozen_brainvision_verdict                  = HOLD   (untouched)
vision_claim = False   memory_readiness_claim = False   runtime_readiness_claim = False
integration_readiness_claim = False
```

Making the BY-axis offset visible in the audit layer is an in-vitro, metric-level reporting improvement within
the same family set; it moves no lock and no verdict, and is not descriptor validity or vision evidence.

## 10. Recommended next (not opened here)

- **Codex review** this findings receipt + the harness / tests.
- **If accepted,** the operator runs the Windows suite and commits. The BY-axis offset is now explicitly visible
  in a dedicated panel layer. The remaining forks are **separate, future, docs-first** decisions (not opened
  here): a **BY-channel closure metric proposal** that would represent the axis offset the per-pair L-inf misses
  (WITHOUT adopting thresholds), a **flat opponent-plane / spatial field geometry** framing, or an **operator /
  new-math** note on the intended screen-analysis geometry. Or **HOLD**. No code, classifier (B), neural (C),
  real clips, runtime, memory, screen, flat-geometry, `§0`, or tags are recommended here.

## 11. Codex review prompt

```text
Please review the v0.9b BY opponent-axis closure visibility audit:
  research/brainvision/run_by_opponent_axis_closure_audit_v0_9b.py
  tests/research/test_brainvision_by_opponent_axis_closure_audit_v0_9b.py
  docs/TORMENT_BRAINVISION_BY_OPPONENT_AXIS_CLOSURE_AUDIT_FINDINGS_v0.9b.md
(new, UNCOMMITTED, over committed edge 3aba63d; implements the v0.9a plan panels A-F).

Verify that this slice:
- is offline research only (research/brainvision + tests/research + one findings doc); no torment_service, no
  runtime / memory / camera / sensor / streaming, no real clips; NO classifier (form B) / neural encoder (form C);
- is REPORTING-ONLY: it presents visibility panels A-F and DECIDES nothing with them; the visibility outcome
  (confirmed/partial/inconclusive) is a reporting label, NOT a Brainvision pass, NOT a closure decision, and it
  changes no verdict (HOLD) and no claim lock;
- ADOPTS NO new closure metric, introduces NO pass/fail gate, invents NO threshold (confirmation uses only the
  chance sign level 0.5 and the BY proportional share, plus reused v0.8a booleans), REDEFINES NO TOL, redesigns
  no descriptor, expands no family, reopens no spectral group;
- reuses the v0.7b / v0.8a records BY IDENTITY (via v0.8a, which reproduces the v0.7b matching), with NO sample
  replacement / new seeds / new families / new candidate generation;
- implements all six panels (A signed-offset, B BY-vs-RG dominance, C binding-stat with by_std/by_spread/
  by_centroid separated, D region/family with the single-matching-family caveat, E coupling/leakage separation,
  F residual-aggregation warning) and reports BY_visibility_confirmed without forcing it;
- defensively excludes non-finite / extreme values (forces invalid_protocol_breach) so they never become evidence;
- does NOT pivot to flat / screen geometry, does NOT prove Brainvision / validate the descriptor / prove screen
  analysis, does NOT move claim locks or authorize runtime/memory/integration; preserves all claim locks
  (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; no §0; no tags.

Flag any adopted metric / threshold / pass-fail gate, any TOL redefinition, any descriptor redesign, any sample
replacement / new family, any flat-geometry / screen-analysis authorization, any non-finite value that could
become evidence, any descriptor-validity / vision claim, or any claim-lock/verdict movement.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY Opponent-Axis Closure Audit Findings v0.9b. Reporting-only, non-learning; offline
research. Changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no control; redesigns no
descriptor; invents no threshold; redefines no TOL; adopts no closure metric; introduces no pass/fail gate;
reruns / replaces no v0.7b sample; opens no classifier / neural / screen / flat-geometry / runtime / memory /
real-clip work; makes no vision / descriptor-validity / temporal-order / memory / runtime / integration claim;
no `§0` pointer; no tags.*
