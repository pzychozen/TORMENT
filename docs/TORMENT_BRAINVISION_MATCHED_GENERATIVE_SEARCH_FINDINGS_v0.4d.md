# TORMENT Brainvision Matched Generative Search Findings v0.4d

## 1. Status / non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY, NON-LEARNING form-A search.** It records the result of
running the sealed v0.4c enumeration under the v0.4b protocol. It **changes no formula / §7 anti-proxy logic /
§8 verdict logic / threshold / control**, trains no weights, uses no label-fitted threshold, opens no
classifier (form B) and no neural encoder (form C), and excludes recurrence / temporal features. Everything
stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. Brainvision Path B remains **not
proven vision**. The frozen Brainvision §8 verdict is **HOLD** and untouched.

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Inputs and delivered files

```text
v0.4  proposal (54daf01)   v0.4a meta-plan (80a6242)   v0.4b prereg (bae9753)   v0.4c enumeration (635027e)

Delivered UNCOMMITTED over HEAD 635027e (form A, non-learning; reuses frozen surfaces by identity):
  research/brainvision/run_matched_generative_search_v0_4d.py
  tests/research/test_brainvision_matched_generative_search_v0_4d.py
```

## 3. What was implemented

A single offline search harness that runs the sealed v0.4c enumeration verbatim: the five closed non-winder
families (F1 full-circle-incoherent, F2 rosette/multi-lobe, F3 segment-paired-canceller [increments reused from
the frozen v0.3 outback set], F4 phase-scrambled-full-coverage, F5 hybrid), the exact grid, the disjoint
development/held-out seed lists and target-winder split, and the finite 283-evaluation budget (190 dev + 93
held-out, full grid once per target, no restarts / retries / redraws). The search objective is **only**
`proxy_match_residual` (L-inf over the ten `MATCHED_STATS`, spectral excluded) under the **sole** feasibility
constraint `PSC < PSC_FLOOR`. `structure_score` / `_stats` / `GROUPS` / `_feat` / the winder generators are
reused by identity from frozen v0.3 / v0.8 / v1.9 / v2.0. `TOL = 0.0634`, `PSC_FLOOR = AIC_FLOOR = 0.30`,
`CHANCE_BAND = 0.60` are referenced frozen. The frozen evaluator and the cheap-baseline audit run only AFTER the
search, on the single-shot held-out set, and are never fed back.

## 4. Result — Partial (honest, NOT tuned)

```text
evaluations: dev 190 + held-out 93 = 283 (sealed)   protocol_ok = True
outcome    = Partial

held-out (best feasible non-winder, matched iff residual <= TOL = 0.0634):
  winder_ph3.14  best_residual = 0.0450  matched = True   (segment_paired_canceller g=0.20 pairs=1; PSC 0.032)
  winder_r0.7    best_residual = 0.0360  matched = True   (segment_paired_canceller g=0.20 pairs=1; PSC 0.032)
  winder_r0.5    best_residual = 0.0600  matched = True   (segment_paired_canceller g=0.20 pairs=2; PSC 0.032)
  n_matched_heldout_targets = 3 / 3   strict_majority = True

held-out cheap-baseline audit on the matched pairs (closed iff best-threshold BA <= CHANCE_BAND = 0.60):
  movement_channel_energy = 1.000   directional = 1.000   per_channel = 1.000   frame_diff = 0.833
  all_matched_groups_closed = False   evaluator_ba = 1.000 (still separates)
```

**Reading (research-only).** Feasible non-winders that match the winders within the frozen `TOL` on all ten
matched statistics **do** exist inside the sealed enumeration (all three held-out targets matched; matched
residuals 0.036–0.060 fall inside v0.3's reported 0.0404–0.0634 band). But matching the L-inf residual is **not
sufficient to close the cheap baselines**: on the pooled matched held-out set the four matched groups still
separate winders from their matched non-winders at best-threshold BA 0.83–1.00 (none `<= 0.60`). So the outcome
is **Partial** — the proxy wall stands even where per-pair residual matching succeeds. This is consistent with
the whole arc (Outcome-4-style proxy wall) and required no tuning; the binding matched families are the
frozen-grounded segment-paired cancellers.

## 5. Defensive NaN / non-finite / extreme-value handling

`_is_clean(x)` rejects NaN, +/-inf, and any `|x| > EXTREME_VALUE_CAP` (1e6, a reporting/hygiene bound, **not** a
descriptor threshold). Non-finite / extreme values can never satisfy feasibility (`PSC` or any matched stat
non-clean -> infeasible), can never satisfy matching (non-clean either side -> residual `+inf`), and can never
back a match (a matched pair with a non-clean matched stat is flagged Invalid / protocol breach). Extreme
quantized artifacts are excluded, never treated as infinity or as stronger evidence. Diagnostic records are
preserved but values are bounded/sanitized before summaries.

## 6. Outcome taxonomy (all leave claim locks unchanged)

```text
Match-feasible          strict majority of held-out targets matched AND all four groups closed AND evaluator separates
Match-infeasible        no admissible candidate reached residual <= TOL for any held-out target
Partial                 anything strictly between (THIS RUN)
Invalid / protocol breach   budget mismatch / non-finite backing a match / single-shot violation -> no evidential weight
```

## 7. Tests run

```text
python -m pytest tests/research/test_brainvision_matched_generative_search_v0_4d.py -q   -> 15 passed
python -m pytest tests/research/test_brainvision_all_shortcuts_closed_synthetic_v0_3.py  -> 11 passed (frozen-surface regression)
python -m pytest tests/research/ -q                                                      -> 249 passed, 1 failed
```

The single full-suite failure is the pre-existing, documented `spectral_centroid` Linux/Windows knife-edge in
`test_brainvision_color_structure_pooled_gate_audit_v1_8.py` (green on Windows; unrelated to v0.4d). The v0.4d
tests assert only platform-independent robust facts: sealed evaluation count 283; families / seeds / grid /
split match v0.4c; `PSC < PSC_FLOOR` is the sole feasibility constraint (AIC plays no role); selection is
argmin-residual over feasible candidates only (no decision / baseline / label / `S_best_threshold` objective);
held-out is single-shot; non-finite / extreme values cannot produce a pass; frozen surfaces reused by identity;
claim locks stay False and verdict HOLD. Windows pytest is the source of truth for boundary stats.

## 8. Claim locks and verdict

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
frozen_brainvision_verdict                  = HOLD   (untouched)
vision_claim = False   memory_readiness_claim = False   runtime_readiness_claim = False
integration_readiness_claim = False
```

The Partial result moves no lock and no verdict. Matching within `TOL` does not establish vision, descriptor
validity, temporal order, or any real-world property; it is an in-vitro synthetic result within one sealed
enumeration and says nothing about real clips.

## 9. Recommended next (not opened here)

- **Codex review** this findings receipt + the harness/tests.
- **If accepted,** the operator runs the Windows suite and commits. Because the outcome is Partial (matched
  within `TOL` but cheap baselines still separate), the honest options are a **separate, future** docs-only
  decision frame — e.g. whether the small-N best-threshold separability is itself the residual to attack, or
  whether to widen the sealed held-out set via a reviewed amendment — or **HOLD**. No code, classifier (B),
  neural (C), real clips, runtime, memory, `§0`, or tags are recommended here.

## 10. Codex review prompt

```text
Please review the v0.4d matched generative search:
  research/brainvision/run_matched_generative_search_v0_4d.py
  tests/research/test_brainvision_matched_generative_search_v0_4d.py
  docs/TORMENT_BRAINVISION_MATCHED_GENERATIVE_SEARCH_FINDINGS_v0.4d.md
(new, UNCOMMITTED, over committed edge 635027e; implements the sealed v0.4c enumeration under the v0.4b protocol).

Verify that this slice:
- is offline research only (research/brainvision + tests/research + one findings doc); no torment_service, no
  runtime / memory / camera / sensor / streaming, no real clips; NO classifier (form B) / neural encoder (form C);
- reuses frozen v0.3/v0.8/v1.9/v2.0 surfaces BY IDENTITY (structure_score/_stats/GROUPS/_feat/winder generators);
  invents no formula, no descriptor, no protocol threshold; TOL=0.0634, PSC_FLOOR/AIC_FLOOR=0.30, CHANCE_BAND=0.60
  referenced frozen; frozen evaluator unchanged; matched groups = 4 (spectral audit-note-only, excluded from match);
- runs EXACTLY the sealed enumeration: 5 families, exact grid, disjoint dev/held-out seeds+targets, finite
  283-evaluation budget (190+93), full grid once per target, no restarts/retries/redraws, single-shot held-out;
- uses the SOLE non-structure feasibility constraint PSC < PSC_FLOOR (no AIC constraint); search objective is
  ONLY proxy_match_residual + feasibility; does NOT optimize the decision score, PSC/AIC BA, any classifier score,
  S_best_threshold, label accuracy, held-out performance, cheap-baseline BA, or any post-hoc metric (baseline
  audit + evaluator are computed only after the search and never fed back);
- defensively excludes NaN / non-finite / extreme-quantized values from feasibility, matching, baseline closure,
  and any claim (clearly reported rule; not treated as infinity or stronger evidence);
- reports Partial honestly (matched within TOL for 3/3 held-out targets, but cheap baselines still separate at
  BA 0.83-1.00 so shortcut closure fails) without tuning toward a win, and classifies match-feasible / infeasible
  / partial / invalid;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD under every outcome; makes no vision /
  "Brainvision sees" / temporal-order / descriptor-validity / memory / runtime / integration claim; no §0; no tags.

Flag any invented threshold, any AIC feasibility constraint, any objective that would let the search optimize a
decision/baseline/label score, any non-finite/extreme value that could produce a pass, any deviation from the
sealed enumeration, any claim-lock/verdict movement, or any overclaim of the Partial result.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Matched Generative Search Findings v0.4d. Reporting-only, non-learning; offline
research. Changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no control; redesigns no
descriptor; invents no threshold; opens no classifier / neural / runtime / memory / real-clip work; makes no
vision / descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer; no tags.*
