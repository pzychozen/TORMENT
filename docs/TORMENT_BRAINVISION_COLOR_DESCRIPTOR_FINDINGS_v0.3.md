# TORMENT Brainvision Color Descriptor Findings v0.3

## 1. Status / quarantine

**DOCS-ONLY research findings note. Non-authorizing, non-implementing.** Records the outcome of the first
offline color-descriptor bridge slice, built to the committed v0.2 manifest/plan (`4d21810`) and corrected after
Codex review. Work stays under `research/brainvision/` + `tests/research/`; no `torment_service/` imports; no
runtime / camera / live-capture / screen-capture / streaming / prompt / context / memory / action / render-body
/ autonomy contact; no object recognition or scene understanding. **No `§0` pointer; no tags.** This does
**not** prove vision, does **not** support a "Brainvision sees" claim, and makes **no** temporal-order claim.
`temporal_claim_allowed` remains **False**. Constants were frozen before running and were **not** changed after
outcomes.

## 2. What was run

`research/brainvision/run_color_descriptor_bridge_v0_3.py` +
`tests/research/test_brainvision_color_descriptor_bridge_v0_3.py` (full research suite **101 passed**; was 89,
+12 new tests). The slice implements the frozen first-pass transform (Y′ = Rec.709 luma proxy on gamma-encoded
sRGB; RG = R−G; BY = B−(R+G)/2; CHROMA = √(RG²+BY²)) with an exact inverse, the synthetic fixtures (generated in
opponent space, gamut-safe), the static color/channel controls, per-channel descriptor summaries, and the G1–G6
gate report. Temporal controls are **reporting-only**; hue continuity, edges, coarse layout, and color×motion are
**not** implemented.

**Two Codex corrections shape the result:** (a) the v0.2 **G5 roughness/spectrum gate** (a spectrum-matched
dissociation showing roughness/spectrum does not explain color-descriptor movement) is **NOT faithfully
implemented** in v0.3 — only a narrow sanity check (S1: rough luminance must not create chroma) is run; and (b)
the v0.2 `roughness_matched_color_change` fixture is **deferred** and its unmatched stand-in is renamed
`rough_color_change` so it makes no matched-behavior claim. G2 was also **strengthened** to test collapse across
all RG/BY/CHROMA-bearing validation fixtures, and `y_held_all` is now a required precondition.

## 3. Results

Per-fixture descriptor response (temporal std of spatial mean; `use`):

```
fixture                              Yp      RG      BY   CHROMA   use
luminance_only_change            0.2121  0.0000  0.0000  0.0000   calibration
red_green_opponent_change        0.0000  0.0849  0.0000  0.0374   validation
blue_yellow_opponent_change      0.0000  0.0000  0.0849  0.0374   validation
saturation_collapse              0.0000  0.0357  0.0214  0.0417   validation
hue_rotation_like                0.0000  0.0849  0.0849  0.0000   validation
color_only_equal_luminance       0.0000  0.0849  0.0509  0.0437   validation
grayscale_control                0.0000  0.0000  0.0000  0.0000   validation
rough_color_change               0.0000  0.0464  0.0579  0.0361   validation
low_saturation_neutral           0.0000  0.0002  0.0002  0.0000   stress
```

Control matrix (red_green base): grayscale / saturation-collapse / luminance-only drive all color channels to 0;
hue-rotation moves RG→BY; channel-shuffle scrambles (and perturbs Y′); color-only/luminance-removed preserves
RG/CHROMA. Separability (`color_only_equal_luminance`): color_response = 0.0849, luminance_response ≈ 3.5e-17,
separation ≈ 8.5e10×. Neutral: `low_saturation_neutral` CHROMA level = 3.0e-4 < NEUTRAL_FLOOR (1e-3). `y_held_all
= True` (all five held fixtures within 1e-3). No synthetic fixture clipped gamut. G2 strengthened: collapse holds
across all four RG/BY/CHROMA-bearing validation fixtures. S1 sanity (rough luminance → no chroma) = True — but S1
is **not** the faithful G5.

Gates (frozen constants COLLAPSE_RATIO=0.10, SEPARATION_MARGIN=5.0, NEUTRAL_FLOOR=1e-3, Y_HOLD_TOL=1e-3):
**G1 True, G2 True (strengthened), G3 True, G4 True, G5 (roughness/spectrum) NOT faithfully implemented (False),
G6 True (invariant)** → **VERDICT HOLD**;
`first_pass_descriptor_control_validity_claim_allowed = False`; `temporal_claim_allowed = False`.

## 4. First-pass interpretation and verdict

**Verdict: HOLD.** The core color/channel gates (G1–G4, with G2 strengthened) pass and `y_held_all` holds, so the
transform, fixtures, and static color/channel controls are internally consistent: each opponent channel responds
to its own manipulation and collapses under grayscale/saturation-collapse; the luminance (Y′) proxy stays flat
when color changes at equal luminance; and the near-neutral fixture is handled as neutral. But because the
faithful v0.2 **G5 roughness/spectrum gate is not implemented**, full first-pass descriptor-control validity is
**not** established, and the honest verdict is HOLD rather than PASS.

This slice is therefore **sanity-checked on constructed synthetic fixtures**, not validated. What it is **not**:
not evidence on natural video, not a color-science validation, not any vision or temporal-order claim. Note the
G1 separation is enormous (≈8.5e10×) only because the synthetic fixtures hold Y′ *by construction* and the
transform is an exact linear inverse; the v0.2 HOLD risk — that on natural clips luminance and color correlate,
so G1 may be genuinely *hard* to pass — remains untested here.

## 5. Non-claims

This does **not**: prove vision or "Brainvision sees"; prove object/scene understanding; prove temporal-order
sensitivity; validate on natural video; establish first-pass descriptor-control validity (G5 absent); authorize
runtime / service / camera / sensor / live-capture; or authorize prompt / context / memory / action / render-body
/ autonomy contact. **No `§0` pointer; no tags.** Brainvision remains offline research, HELD per v0.6, with
`temporal_claim_allowed` **False**.

## 6. Recommended next

- **Codex review** of the corrected transform, fixtures, controls, and gate logic, and of this findings note.
- Two honest paths out of HOLD, either/both as a **predeclared** next slice: (a) implement the **faithful G5**
  (a spectrum-matched dissociation plus the deferred `roughness_matched_color_change` fixture matched to a
  roughness/spectrum null), and/or (b) assemble the **offline, gitignored local clip corpus** (color-rich /
  low-color / grayscale-like) so G1 can be tested where luminance and color actually correlate. Until then the
  verdict stays HOLD. No temporal-order work; no vision claim.

*End — TORMENT Brainvision Color Descriptor Findings v0.3. Docs-only, non-authorizing. Opens no implementation
lane; no `§0` pointer added; no tags.*
