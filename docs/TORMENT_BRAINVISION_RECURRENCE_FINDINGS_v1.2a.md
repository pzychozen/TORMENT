# TORMENT Brainvision Recurrence Findings v1.2a

## 1. Status / quarantine

**DOCS-ONLY research findings note. Non-authorizing, non-implementing.** Records the outcome of the offline
v1.2a ordered-recurrence / continuity harness, run against the predeclared v1.2a plan (`b405a49`). Work stays
under `research/brainvision/` + `tests/research/`; no `torment_service/` imports; no service / runtime / camera
/ sensor / live-capture / prompt / context / memory / action / render-body / autonomy contact. **No `§0`
pointer; no tags.** This does **not** prove Brainvision works, does **not** prove temporal-order or
arrow-of-time sensitivity, and does **not** authorize any integration. `temporal_claim_allowed` remains
**False**. Constants were frozen before running and were **not** changed after seeing outcomes.

## 2. What was run

`research/brainvision/run_sag_recurrence_v1_2a.py` + `tests/research/test_brainvision_sag_recurrence_v1_2a.py`
(full research suite **88 passed**; was 79, +9 new tests). The harness builds a recurrence-quantification (RQA)
diagnostic on the per-window normalized descriptor field exactly per the v1.2a plan: frame recurrence **m = 1**,
line of identity + Theiler band excluded, **Theiler w = 0** primary, **RR_target = 0.10** via a per-window
distance-quantile ε rule, diagonal **ℓmin = 3** primary, **DET** primary. Controls: temporal
(true/shuffled/reversed/circular), per-window shuffle surrogates for a DET z-score, an amplitude-spectrum-matched
(phase-randomized) surrogate, and two frozen dissociation probes (`rough_ordered`, `smooth_disordered`).

## 3. Results

**T1 — per-control pooled medians (non-neutral; 24 near-flat `constant` cells excluded):**

```
control            RR      DET      L      LAM     ENTR    DET_z
true             0.100   0.431   6.91   0.656   0.851   22.39
time_shuffled    0.100   0.030   3.00   0.225   0.000    0.07
time_reversed    0.100   0.431   6.91   0.656   0.851   24.82
circular_shift   0.100   0.431   6.67   0.661   0.830   22.18
```

**T2 — per-field Tier-A (median DET; ordered group {true,reversed,circular} vs shuffle):**

```
field               true    rev    circ   ord_min  shuffle  true_z  vote
lowpass             0.485  0.485  0.475   0.475    0.000    28.45    Y
rough_ordered       0.691  0.691  0.691   0.691    0.030    42.36    Y
sine                0.342  0.342  0.342   0.342    0.025    16.44    Y
sine_phase_shift    0.458  0.458  0.463   0.458    0.015    24.14    Y
smooth_disordered   0.619  0.619  0.592   0.592    0.025    31.90    Y
smooth_ramp         0.943  0.943  0.928   0.928    0.022    47.06    Y
spike               0.015  0.015  0.015   0.015    0.030    -0.45    n
tiny_noise          0.015  0.015  0.015   0.015    0.030    -0.60    n
white_noise         0.015  0.015  0.015   0.015    0.030    -0.55    n
```

**T3 — roughness invariance / dissociation:** pooled_ordered_DET = 0.431, pooled_shuffle_DET = 0.030;
rough_ordered_DET = 0.691, smooth_disordered_DET = 0.619, spectrum_matched_DET = 0.413;
**Spearman(DET, delta_rms) = −0.746** (ceiling |ρ| < 0.30) → **invariance_pass = False**. Additionally,
`smooth_disordered_DET = 0.619` and `spectrum_matched_DET = 0.413` are not low relative to the ordered DET
scale, so the dissociation/spectral controls also support the FAIL reading.

**T4 — Tier-B arrow of time:** verdict **NA**. Symmetric DET is time-reversal invariant (T1 shows
`time_reversed` DET equals `true` DET), so it is not used for a Tier-B claim; no directional variant was
designed.

**T5 — gates:** roughness_invariance_prereq = **False**; tier_A_undirected_order = **False**;
tier_B_arrow_of_time = **NA**; field_majority = 0.667; pooled_ordered_beats_shuffle = True;
near_flat_neutral_count = 24.

**Secondary sensitivity (NON-RESCUING; cannot change the primary verdict):** w=1 ρ = −0.740, w=2 ρ = −0.700,
lmin=2 ρ = −0.776 — all still fail the invariance ceiling.

## 4. First-pass interpretation

The RR matching works at the reported per-control median level under the frozen quantile rule (RR = 0.100 for
every control) and, at m = 1, RR is identical across
true/shuffled/reversed/circular — the frame-level permutation-invariance the plan relied on holds. DET separates
the ordered/adjacent group (≈ 0.43) from `time_shuffled` (≈ 0.03) very strongly, and `time_reversed` /
`circular_shift` sit on top of `true`, so the DET separation subcriteria are met at face value
(field_majority 0.667 > 0.5; pooled ordered beats shuffle), but full Tier A is not met because the
roughness-invariance prerequisite fails.

**But the predeclared roughness-invariance pre-requisite fails.** Spearman(DET, delta_rms) = −0.746 shows DET is
strongly (inversely) tied to roughness: at Theiler w = 0, DET substantially rewards local temporal continuity
(smoothness), and `time_shuffle` destroys smoothness, so the `true` ≫ `shuffle` gap is confounded with
roughness rather than being clean temporal order. The gate is designed to catch exactly this, and it does. The
secondary sensitivity (w = 1, w = 2, lmin = 2) confirms the confound is robust (ρ ≈ −0.70 to −0.78), so it is
not merely a near-diagonal artifact of w = 0.

## 5. Verdict and what it does / does not rule out

**Verdict: FAIL under the v1.2a plan.** The recurrence/continuity family, as predeclared (m = 1 frame DET), does
not pass the roughness-invariance pre-requisite, so no order claim of any tier is permitted.
`undirected_order_claim_allowed = False`; `temporal_claim_allowed = False`.

The `rough_ordered` probe scoring DET = 0.691 is consistent with DET detecting the planted periodic recurrence
in that synthetic anchor. But because `smooth_disordered` and spectrum-matched controls also score high, this
cannot be treated as clean order evidence. The safer reading is that DET contains an order-sensitive component,
but the current frame-level diagnostic does not separate it cleanly from continuity/spectral structure.

## 6. Non-claims

This does **not**: prove a mechanism; prove classifier superiority; prove working vision; prove temporal-order or
arrow-of-time sensitivity; authorize runtime / service / camera / sensor / live capture; or authorize prompt /
context / memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.** Brainvision remains
offline research, HELD per v0.6.

## 7. Recommended next

- **Codex reviews** this findings note and the harness, in particular the RR-quantile ε rule, the LOI/Theiler
  exclusion, and the invariance-gate reading.
- The FAIL says frame-level DET is roughness-confounded, so any future direction (a **proposal only**, not built,
  no tuning) would need to isolate the order signal from continuity — e.g. scoring DET *relative to a
  roughness-matched / spectrum-matched surrogate per window* (so the continuity floor is subtracted), or
  restricting to long-range period diagonals where the `rough_ordered` anchor already shows clean order signal.
  Whether to open a v1.2b along those lines is an operator/trio decision; nothing is implemented here.

*End — TORMENT Brainvision Recurrence Findings v1.2a. Docs-only, non-authorizing. Opens no implementation lane;
no `§0` pointer added; no tags.*
