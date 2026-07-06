# TORMENT Brainvision SAG Failure-Analysis Findings v1.1

## 1. Status / quarantine

**DOCS-ONLY research findings note. Non-authorizing, non-implementing. Opens no implementation lane and no
service integration.** Records an **offline failure analysis** of the v1.0 candidate: it explains *why* the
`time_shuffled` control scored higher than `true` after normalization. It introduces **no new operator and no
new diagnostic**. Work stays quarantined under `research/brainvision/` + `tests/research/`; no
`torment_service/` imports; no service / runtime / camera / sensor / live-capture / prompt / context / memory
/ action / render-body / autonomy contact. **No `§0` pointer; no tags.** This does **not** prove Brainvision
works, does **not** prove classifier superiority, and does **not** prove temporal-order specificity.
`temporal_claim_allowed` remains **False**; nothing here rescues it.

## 2. What was run

Harness `research/brainvision/run_sag_failure_analysis_v1_1.py` +
`tests/research/test_brainvision_sag_failure_analysis_v1_1.py` (full research suite **79 passed**; was 72,
+7 new tests). The harness **replays v1.0's exact iteration** (same field seeds, same per-control RNG, same
window order) so the gains it records **are** the v1.0 gains, and pairs each non-neutral window with
predeclared descriptive properties of the *identical* normalized array SAG sees. No operator, no gate, and no
threshold in v1.0 is changed.

**Predeclared hypothesis H1** (fixed before running): after median/MAD amplitude normalization the SAG κ>0
gain is driven by **temporal roughness** (per-frame change magnitude of the normalized field), not temporal
order. Shuffling maximizes roughness (adjacent frames decorrelate → large frame-to-frame deltas + a broad
temporal spectrum); true-order structured fields are temporally smooth. Normalization removes overall scale
but not the roughness-to-energy ratio, so shuffled > true survives. Mechanistic rationale (not tuned): SAG
separates a mirror-perturbed pair in proportion to (differential clock phase) × (temporal gradient of the
field); a rougher field has a larger temporal gradient, so the same clock desync yields a larger field-space
separation. Prediction: `time_reversed` and `circular_shift` preserve adjacency/|FFT| and thus roughness, so
they stay **near** true; only `time_shuffled` departs.

**Predeclared measures** (on `wn = normalize(transform_window(base, control, rng))`): `raw_robust_scale`,
`delta_rms`, `temporal_continuity` (lag-1 autocorr), `spectral_centroid`, `psi_spec_norm`, target `sag_gain`.
**Predeclared rule**: H1 SUPPORTED iff Spearman(`delta_rms`, log₁₀ gain) ≥ 0.5 **and** `delta_rms` is the top
member of the roughness family {`delta_rms`, `spectral_centroid`, `psi_spec_norm`, −`temporal_continuity`}
**and** the highest-`delta_rms` control is also the highest-gain control; PARTIAL iff some roughness member
clears the threshold (with control-ranking agreement) but not `delta_rms` specifically; else NOT SUPPORTED.

## 3. Results

Per-control pooled medians (non-neutral; 24 near-flat `constant` cells excluded):

```
control            gain   delta_rms  continuity  spec_cent   psi_spec  raw_scale
true              8.425      0.656       0.765      0.094      6.454      0.750
time_shuffled   147.660      1.370      -0.023      0.257     16.332      0.750
time_reversed     6.388      0.656       0.765      0.094      6.454      0.750
circular_shift    8.003      0.668       0.756      0.094      6.454      0.750
```

Per-field, true vs shuffled (median gain / median `delta_rms`):

```
field              true_g    shuf_g  s>t?   true_dr   shuf_dr  s>t?
lowpass             6.829   147.936   Y      0.656     1.416    Y
sine                1.344   153.059   Y      0.362     0.952    Y
sine_phase_shift    4.459    81.285   Y      0.364     0.958    Y
smooth_ramp         8.899    42.853   Y      0.056     1.097    Y
spike               1.000     1.000   n    144.769   144.773    Y
tiny_noise        151.312   149.099   n      1.422     1.411    n
white_noise       151.312   149.099   n      1.422     1.411    n
```

Spearman(property, log₁₀ gain) across all 168 non-neutral cells:

```
raw_robust_scale     -0.037
delta_rms            +0.104
temporal_continuity  -0.269
spectral_centroid    +0.279
psi_spec_norm        +0.545
```

**Predeclared verdict: `H1_PARTIAL`.** Top roughness member and overall top correlate = `psi_spec_norm`
(+0.545). Highest-gain control = highest-`delta_rms` control = `time_shuffled` (ranking agrees). The rule
returns PARTIAL — not SUPPORTED — because the *global* `delta_rms` rank-correlation (+0.104) is below 0.5 even
though `psi_spec_norm` clears it. **This was not tuned toward a win.**

## 4. First-pass interpretation

The pooled-control evidence is decisive and matches H1 exactly. `time_shuffled` is the **only** control that
raises every roughness measure (`delta_rms` 0.656→1.370, `spectral_centroid` 0.094→0.257, `psi_spec_norm`
6.454→16.332) and drops continuity (0.765→−0.023), and it is the **only** control whose gain explodes
(8.4→147.7). `time_reversed` reproduces true's roughness stats **exactly** (reversal preserves the multiset of
adjacent deltas) and its gain sits at 6.4 ≈ true; `circular_shift` preserves adjacency up to one wrap point
and sits at 8.0 ≈ true. So the v1.0 failure is **not** "any temporal scramble beats true" — it is specific to
the one transform (shuffle) that whitens the temporal spectrum. This is the cleanest possible statement that
the gain tracks **roughness, not order**.

The per-field table shows the same mechanism at the field level: the effect is concentrated in the
temporally-**smooth** fields (`lowpass`, `sine`, `sine_phase_shift`, `smooth_ramp`) — exactly where shuffling
*raises* roughness — and is absent in the already-rough fields (`spike`, `tiny_noise`, `white_noise`), where
shuffling barely changes roughness and the gain barely moves. Direction is consistent with H1 everywhere.

**Why PARTIAL, not SUPPORTED (exploratory, not predeclared; does not change the verdict).** The weak *global*
`delta_rms` correlation is an artifact of a single field. `spike` is a saturated-gain roughness outlier:
median `delta_rms` ≈ 144.8 (three +5.0 spikes dominate the frame-to-frame delta even after MAD scaling) but
median gain = 1.000 (the field is so dominated by its spikes that the mirror perturbation cannot separate).
That one point breaks the global `delta_rms`↔gain monotonicity and crushes the Spearman. Removing it:

```
                    delta_rms  spec_cent  psi_spec  continuity
ALL non-neutral       +0.104     +0.279    +0.545     -0.269
smooth fields only    +0.417     +0.403    +0.397     -0.425
rough fields only     -0.701     -0.006    +0.665     +0.088   (spike-dominated)
spike EXCLUDED        +0.684     +0.708    +0.700     -0.700
```

With `spike` excluded, **every** roughness-family member clears 0.5 and continuity flips to −0.70, exactly as
H1 predicts. `psi_spec_norm` is the strongest *global* correlate because it is the operator's own bounded
2-D spectral quantity — the thing the state-dependent clock literally reads — and is far less distorted by the
spike outlier than the raw frame-delta. The mechanism reading is robust; only the single predeclared summary
statistic is dragged down by one pathological field.

## 5. Does this suggest a future v1.2 diagnostic? (direction only — NOT built here)

The analysis says the SAG gain is a **spectral-spread / roughness meter**, and shuffle inflates spread. Any
v1.2 would therefore have to remove that confound *before* it could isolate order. Two hypotheses for the trio
to review (predeclare, do not implement yet):

1. **Roughness/spectral equalization before scoring** — whiten or match the temporal power spectrum of `true`
   and each control so all windows carry equal roughness; any residual `true` > `control` gain would then be
   attributable to order rather than spread. Risk: whitening may destroy the very temporal structure a
   vision claim would need, i.e. it could equalize away the signal along with the confound.
2. **Score ordered recurrence/continuity directly** — replace the max-separation gain with a measure that
   rewards ordered continuity/recurrence and that shuffle **cannot** inflate (shuffle should score low, not
   high). This inverts the current failure mode by construction and is the more promising direction, but it is
   a *new operator* and must clear the same first-class shuffle/reverse/circular gate before any claim.

Both are proposals only. **No implementation until a v1.2 proposal note is reviewed** (same discipline as the
v1.0→v1.1 handoff).

## 6. Non-claims

This does **not**: prove a mechanism; prove classifier superiority; prove working vision or video
understanding; prove temporal-order sensitivity; propose or build a new diagnostic; authorize runtime
integration; authorize service / camera / sensor / live capture; authorize prompt / context / memory / action
/ render-body / autonomy contact. **No `§0` pointer; no tags.** Brainvision remains offline research under
`research/brainvision/` + `tests/research/`, HELD per v0.6. `temporal_claim_allowed` stays **False**.

## 7. Recommended next

- **Codex adversarial wording review** of this note — confirm §4/§5 neither over- nor under-state what the run
  shows, especially the clearly-labeled exploratory `spike`-excluded breakdown.
- **Then** decide between the two v1.2 directions (§5) as a *proposal note* with controls first-class and
  thresholds predeclared. No operator work until reviewed.

*End — TORMENT Brainvision SAG Failure-Analysis Findings v1.1. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*
