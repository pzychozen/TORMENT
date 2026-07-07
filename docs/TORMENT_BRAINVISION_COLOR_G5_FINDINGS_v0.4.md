# TORMENT Brainvision Color G5 Findings v0.4

## 1. Status / quarantine

**DOCS-ONLY research findings note. Non-authorizing, non-implementing.** Records the outcome of the offline v0.4
G5 roughness/spectrum diagnostic, built to the committed v0.4 plan (`9800308`). Work stays under
`research/brainvision/` + `tests/research/`; no `torment_service/` imports; no runtime / camera / live-capture /
screen-capture / streaming / prompt / context / memory / action / render-body / autonomy contact; no
object/scene understanding. **No `§0` pointer; no tags.** This makes **no** vision claim, **no** "Brainvision
sees" claim, and **no** temporal-order claim. `temporal_claim_allowed` remains **False**. Constants were frozen
before running and were **not** tuned after outcomes.

## 2. What was run

`research/brainvision/run_color_g5_diagnostic_v0_4.py` +
`tests/research/test_brainvision_color_g5_diagnostic_v0_4.py` (full research suite **111 passed**; was 101, +10
new tests). Layered on the v0.3 bridge, it implements the predeclared null/control fixtures
(`rough_luminance_only_null`, `rough_chroma_null`, `roughness_matched_color_vs_luminance_pair`,
`spectrum_matched_color_null`, plus a reporting-only shared-phase variant), the roughness/spectrum statistics
(`delta_rms`, spectral centroid, response-vs-roughness Spearman, matched-null response ratios reported **per
channel** for RG/BY/CHROMA separately), and the two sub-gates G5a and G5b. Per the v0.4 requirement,
`spectrum_matched_color_null` is generated **in Y′/RG/BY descriptor space** — Y′ held to the intended fixture's
Y′ series, RG and BY **independently phase-randomized** while preserving each channel's amplitude spectrum;
RGB-space phase randomization is out of scope.

## 3. Results

**G5a — cross-channel roughness immunity: PASS.**
- `a1` rough_luminance_only_null → color response 0.0000 ≤ leak_ceil (0.0085); rough luminance cannot fake color.
- `a2` roughness_matched pair → no cross-fire (color→Y′ 0.0000, luminance→color 0.0000); `pair_valid = True`.
- `a3` response-vs-roughness Spearman = 0.000 < 0.30; color response does not track roughness.

**G5b — within-chroma spectrum immunity: FAIL (predeclared).** Per-channel intended-vs-null response ratios:

```
fixture                         RG      BY    CHROMA   fixture_ok
red_green_opponent_change      1.00    1.00   1.020    False
blue_yellow_opponent_change    1.00    1.00   1.014    False
hue_rotation_like              1.00    1.00   0.000    False
color_only_equal_luminance     1.00    1.00   1.249    False
```

RG and BY ratios are **exactly 1.00** on every fixture — the spectrum-matched null preserves each channel's
amplitude spectrum, so its per-channel std equals the intended fixture's. None of RG/BY clears the
`NULL_BEAT_MARGIN` (ratio ≥ 1.20), so no fixture passes (0/4). CHROMA behaves differently under independent RG/BY
phase changes (0.0 for the constant-chroma hue-rotation fixture, up to 1.25 for `color_only`), which is exactly
why CHROMA is reported separately — but it cannot rescue G5b since RG/BY fail.

**Full G5 = G5a AND G5b → HOLD.** `first_pass_descriptor_control_validity_claim_allowed = False`;
`temporal_claim_allowed = False`.

## 4. First-pass interpretation and verdict

**Verdict: HOLD — exactly the predeclared expected outcome.** G5a passes faithfully: the transform and current
descriptors pass the predeclared G5a cross-channel roughness checks (rough luminance produces no chroma, a roughness-matched
color/luminance pair does not cross-fire, and color response does not correlate with roughness). But G5b fails
by construction: because the color response is per-channel temporal std, a spectrum-matched null (RG/BY
independently phase-randomized, amplitude spectrum preserved) has an identical RG/BY response — ratio exactly
1.00. This **confirms the v0.4-predeclared limitation**: the current RG/BY per-channel temporal-std responses are
spectrum-explained; CHROMA behaves differently but cannot rescue G5b because RG/BY fail.

This is the same confound family that produced the SAG and frame-DET negatives, now shown for the current RG/BY
temporal-std color descriptors: a variance-like statistic is invariant to phase, so it cannot certify structure. The G5a-only pass
does **not** license descriptor-control validity; the honest verdict is HOLD. (One construction note: the G5a
roughness-correlation bank uses sub-Nyquist frequencies — `f = T/2` aliases a sinusoid to a constant at these
lengths and was excluded; it is not a legitimate rough-chroma probe.)

## 5. Non-claims

This does **not**: prove vision or "Brainvision sees"; prove object/scene understanding; prove temporal-order
sensitivity; establish first-pass descriptor-control validity (G5b unmet); validate on natural video; authorize
runtime / service / camera / sensor / live-capture / screen-capture; or authorize prompt / context / memory /
action / render-body / autonomy contact. **No `§0` pointer; no tags.** Brainvision remains offline research,
HELD per v0.6, with `temporal_claim_allowed` **False**.

## 6. Recommended next

- **Codex review** of the G5a/G5b implementation, the spectrum-matched null construction, and this findings note.
- G5b is now a *demonstrated* limitation, not merely an absent gate. The two honest paths remain, either/both as
  a **predeclared** future slice: (a) a **structure-sensitive chroma descriptor** (e.g. one sensitive to RG/BY
  joint phase / hue coherence) that could in principle beat a spectrum-matched null — a **new descriptor**,
  explicitly out of scope here; and/or (b) the **offline gitignored clip corpus** so the achievable G5a-style
  separability can be tested where luminance and color actually correlate. Verdict stays HOLD until then. No
  temporal-order work; no vision claim.

*End — TORMENT Brainvision Color G5 Findings v0.4. Docs-only, non-authorizing. Opens no implementation lane; no
`§0` pointer added; no tags.*
