# TORMENT Brainvision BY-Channel Metric Anatomy Findings v0.8a

## 1. Status / non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY, NON-LEARNING, EXPLANATORY form-A diagnostic.** It records
what the v0.8a BY-channel metric anatomy found. It is **explanatory, not corrective**: it explains *why*
`by_centroid`, `by_spread`, `by_std` persist and does **not** try to make Brainvision pass or close BY. It
**changes no formula / §7 anti-proxy logic / §8 verdict logic / threshold / control**, **redefines no `TOL`**,
adopts **no new closure metric**, adds no new family / axis, trains no weights, reopens no spectral group, opens
no classifier (form B) and no neural encoder (form C).

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
v0.7b (978bb36)  larger-N replication -> BY_persistence_metric_insufficiency.
v0.7c (ca3a95f)  synthesis: localized the wall to BY-channel opponent-axis geometry; recommended Branch A.
v0.8  (c0c5040)  BY-channel metric anatomy PLAN.

Delivered UNCOMMITTED over HEAD c0c5040 (form A, non-learning, explanatory-only; reuses v0.7b + frozen surfaces
by identity):
  research/brainvision/run_by_channel_metric_anatomy_v0_8a.py
  tests/research/test_brainvision_by_channel_metric_anatomy_v0_8a.py
```

## 3. What was implemented

A single reporting-only diagnostic that **reproduces the v0.7b sealed replication matching by identity** (same
frozen winder + F1-F5 generators, same sealed seeds / counts / pairing, `proxy_match_residual`, `PSC < PSC_FLOOR`
feasibility, `TOL`) and verifies it reproduces the committed v0.7b matched (19) / unmatched (5) sets, then
reports a BY-channel anatomy over those exact pairs. It answers the seven v0.8 diagnostic questions with
reporting-only outputs, using a **parameter-free comparative scoring** of the candidate mechanisms. `TOL`,
thresholds, the descriptor / `GROUPS`, and the evaluator are unchanged; spectral stays audit-note-only; non-
finite / extreme values are excluded and can never become evidence (they force `invalid_protocol_breach`).

## 4. Result — BY_axis_asymmetry (honest, NOT tuned)

```text
reproduces v0.7b: True (19 matched, 5 unmatched: w_sp3.00, w_sp3.50, w_r0.4, w_r0.3, w_r0.2)   protocol_ok = True
outcome = BY_axis_asymmetry

(1) BY vs RG effect size (|smd|/TOL):  BY_dominant_over_rg = True
    by_std 71%   by_centroid 54%   by_spread 46%   >>   rg_centroid 0%   rg_spread 4%   directional 6%
(2) BY signed-difference sign consistency (mean 0.895):
    by_centroid  dominant -  0.90    by_spread  dominant -  0.84    by_std  dominant +  0.95
(3) centroid/spread coupling (Spearman)        = 0.031   (weak)
(4) by_std ~ amplitude (Spearman)              = {chroma_mag: 0.292, rg_std: 0.169}   (weak)
(5) matched family distribution                = {segment_paired_canceller: 19}   (single family matches)
(6) region BY (by_centroid BA)                 = speed 0.75, phase 1.00, radius 1.00   (unmatched: speed 2, radius 3)
(7) binding L-inf stat: by_std 10, chroma_mag 3, rg_spread 2, others 1   -> BY-binding fraction 0.63

mechanism scores: BY_axis_asymmetry 0.789  >  BY_metric_compression 0.332  >  BY_amplitude_leakage 0.292  >
                  BY_centroid_spread_coupling 0.031
```

**Reading (research-only).** The BY persistence is a **systematic opponent-axis (blue-yellow) offset**: winders
are systematically **lower** on `by_centroid` / `by_spread` (dominant-sign 84-90%) and systematically **higher**
on `by_std` (95%) than their matched cancellers, even though every pair matches within `TOL`. The BY effects
(46-71% of `TOL`) dwarf the RG effects (0-4%). The competing explanations are weak: centroid/spread coupling is
near zero (Spearman 0.03), and `by_std` barely tracks amplitude / channel-energy (0.29 / 0.17), so it is not
primarily amplitude leakage. A secondary signal is residual-aggregation compression (`by_std` is the binding
L-inf stat in 10 of 19 pairs, so the per-pair L-inf lets the class-level BY offset through), but the dominant
signal is the systematic signed axis offset. Outcome: **`BY_axis_asymmetry`** (asymmetry score 0.79, well above
the others).

## 5. Answers to the seven v0.8 questions

```text
1. BY vs RG: BY effects (46-71% TOL) are systematically far larger than RG effects (0-4%). BY-dominant = True.
2. BY signed differences: consistently signed (by_centroid/by_spread winders lower ~85-90%; by_std winders
   higher 95%) -> a systematic directional offset, not noise.
3. Centroid/spread coupling: WEAK (Spearman 0.03) -> not a coupled-geometry story.
4. by_std amplitude leakage: WEAK (Spearman 0.29 chroma_mag / 0.17 rg_std) -> by_std is more geometric than
   amplitude; not primarily channel-energy leakage.
5. Family anatomy: all 19 matches are segment_paired_canceller (only that family matches within TOL); BY
   persistence is measured against F3 cancellers -- not distinguishable across families (single matching family).
6. Target-region anatomy: BY persists across phase / radius (BA 1.0) and is weaker in the speed region (BA 0.75);
   the 5 unmatched targets are high-speed and low-radius (low-amplitude) winders, not BY-specific failures.
7. Residual aggregation: by_std is the binding L-inf stat for 10/19 pairs (BY-binding fraction 0.63 vs a 0.30
   share) -> the L-inf per-pair match does let the class-level BY ordering through (a secondary compression signal).
```

## 6. Threshold-free classification and defensive handling

The candidate mechanisms are scored on comparable [0,1] scales and compared: `BY_axis_asymmetry` =
`2*mean_sign_consistency - 1` (0 = chance sign), `BY_centroid_spread_coupling` = |Spearman(by_centroid,
by_spread diffs)|, `BY_amplitude_leakage` = max |Spearman(by_std, amplitude diffs)|, `BY_metric_compression` =
BY-binding-fraction minus the BY share of the ten matched stats. The outcome is the **argmax** — a comparative
selection, **not** a fixed pass/fail cutoff; `BY_family_artifact` requires >= 2 matching families to compare
(here only one matches). Non-finite / extreme values are excluded via the frozen `_is_clean`; if any appears in
a required feature, no evidence is computed and the run is `invalid_protocol_breach`.

## 7. Outcome taxonomy (all leave claim locks unchanged)

```text
BY_axis_asymmetry            systematic opponent-axis offset the per-pair match leaves unclosed   (THIS RUN)
BY_centroid_spread_coupling  by_centroid / by_spread coupled beyond the residual metric
BY_amplitude_leakage         by_std tied to channel-energy / amplitude rather than geometry
BY_family_artifact           BY persistence concentrated in a subset of matching families
BY_metric_compression        BY ordering survives because group-level residual aggregation is too compressed
BY_anatomy_inconclusive      records cannot distinguish the causes
invalid_protocol_breach      budget mismatch / non-finite / non-reproduction -> no evidential weight
```

## 8. Tests run

```text
python -m pytest tests/research/test_brainvision_by_channel_metric_anatomy_v0_8a.py -q  -> 11 passed
python research/brainvision/run_by_channel_metric_anatomy_v0_8a.py                       -> ran clean (result above)
python -m pytest tests/research -q                                                       -> 299 passed, 1 failed (sandbox)
```

The single full-suite failure is the pre-existing, documented `spectral_centroid` Linux/Windows knife-edge in
`test_brainvision_color_structure_pooled_gate_audit_v1_8.py` (green on Windows; unrelated to v0.8a). The v0.8a
tests assert only platform-independent robust facts: reproduction of the v0.7b matched/unmatched sets by
identity (no sample replacement, no seed/count/pairing change); `TOL` / thresholds / descriptor / `GROUPS`
unchanged; spectral audit-note-only; the primary BY features inspected with rg_* / directional comparison-only;
outcome from the sealed labels; non-finite values cannot become evidence; and claim locks stay False with
verdict HOLD. Windows pytest is the source of truth.

## 9. Claim locks and verdict

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
frozen_brainvision_verdict                  = HOLD   (untouched)
vision_claim = False   memory_readiness_claim = False   runtime_readiness_claim = False
integration_readiness_claim = False
```

Naming the BY persistence as a systematic axis offset is an in-vitro synthetic, metric-level description within
the same family set; it moves no lock and no verdict, and is not descriptor validity or vision evidence.

## 10. Recommended next (not opened here)

- **Codex review** this findings receipt + the harness / tests.
- **If accepted,** the operator runs the Windows suite and commits. The anatomy identifies the BY persistence as
  a **systematic blue-yellow opponent-axis offset** (with a secondary residual-aggregation compression signal),
  not coupling or amplitude leakage. The honest follow-ups remain **separate, future, docs-first** steps (not
  opened here): a Branch-B **BY-channel closure metric proposal** that would represent the axis offset the
  per-pair L-inf does not (WITHOUT adopting thresholds), and/or an **operator / new-math** framing of whether
  this reflects a deeper chroma-plane / opponent-axis geometry issue. Or **HOLD**. No code, classifier (B),
  neural (C), real clips, runtime, memory, `§0`, or tags are recommended here.

## 11. Codex review prompt

```text
Please review the v0.8a BY-channel metric anatomy:
  research/brainvision/run_by_channel_metric_anatomy_v0_8a.py
  tests/research/test_brainvision_by_channel_metric_anatomy_v0_8a.py
  docs/TORMENT_BRAINVISION_BY_CHANNEL_METRIC_ANATOMY_FINDINGS_v0.8a.md
(new, UNCOMMITTED, over committed edge c0c5040; implements the v0.8 Branch-A plan).

Verify that this slice:
- is offline research only (research/brainvision + tests/research + one findings doc); no torment_service, no
  runtime / memory / camera / sensor / streaming, no real clips; NO classifier (form B) / neural encoder (form C);
- is EXPLANATORY not corrective: it explains WHY by_centroid / by_spread / by_std persist and does NOT try to
  close BY, make Brainvision pass, or tune anything;
- REPRODUCES the v0.7b sealed replication BY IDENTITY (19 matched / 5 unmatched), replaces no sample, changes no
  seed / count / pairing, adds no generator family, invents no threshold, REDEFINES NO TOL, adopts NO new closure
  metric, changes no descriptor / GROUPS / evaluator / control, keeps spectral audit-note-only;
- inspects the primary BY features (by_centroid / by_spread / by_std) with rg_* and directional as comparison-
  only, and answers the seven v0.8 questions (BY-vs-RG, signed-difference sign consistency, centroid/spread
  coupling, by_std amplitude tracking, family anatomy, target-region anatomy, residual-aggregation binding);
- classifies the mechanism by a THRESHOLD-FREE comparative argmax of [0,1] scores (asymmetry / coupling /
  amplitude / compression), not a fixed cutoff, and reports BY_axis_asymmetry (systematic opponent-axis offset:
  winders lower by_centroid/by_spread, higher by_std; coupling and amplitude weak; compression a secondary signal);
- defensively excludes non-finite / extreme values (forces invalid_protocol_breach; computes no evidence on them);
- does NOT treat BY anatomy as descriptor validity or vision evidence, does NOT move claim locks or authorize
  runtime/memory/integration; preserves all claim locks (first_pass_structure_validity_claim_allowed = False;
  temporal_claim_allowed = False; descriptor_validity_claim_allowed = False) and verdict = HOLD; no §0; no tags.

Flag any threshold invention, any TOL change, any closure-metric adoption, any descriptor redesign, any new
family, any sample replacement / non-reproduction of v0.7b, any non-finite value that could become evidence, any
claim-lock/verdict movement, or any overclaim of the anatomy.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision BY-Channel Metric Anatomy Findings v0.8a. Reporting-only, non-learning, explanatory;
offline research. Changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no control;
redesigns no descriptor; invents no threshold; redefines no TOL; adopts no closure metric; adds no new family or
axis; reopens no spectral group; opens no classifier / neural / runtime / memory / real-clip work; makes no
vision / descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer; no tags.*
