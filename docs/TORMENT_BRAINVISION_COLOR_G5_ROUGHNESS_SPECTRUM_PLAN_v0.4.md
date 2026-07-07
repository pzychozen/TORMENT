# TORMENT Brainvision Color G5 Roughness/Spectrum Plan v0.4

## 1. Status / quarantine and non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation lane.**
It defines — but does not build — a **faithful G5 roughness/spectrum gate** for the color descriptor bridge, so
a future descriptor-control validity result cannot be explained by roughness/spectrum artifacts. It implements
no descriptors, no diagnostic, no code, and no tests, and touches no `torment_service/`, runtime, camera /
sensor / live-capture / screen-capture / streaming, or prompt / context / memory / action / render-body /
autonomy paths. **No `§0` pointer; no tags.** Everything stays offline under `research/brainvision/` +
`tests/research/`, HELD per v0.6. **This plan makes no vision claim, no "Brainvision sees" claim, and no
temporal-order claim.** `temporal_claim_allowed` remains **False**. **No implementation is authorized.**

## 2. v0.3 HOLD summary

The v0.3 slice sanity-checked the frozen transform and fixtures: the Y′/RG/BY/CHROMA proxies round-trip, gray
has zero chroma, no synthetic fixture clips gamut, "Y′ held" holds within tolerance, and the core color/channel
gates **G1–G4 pass** (with G2 strengthened across the RG/BY/CHROMA-bearing validation fixtures) while **G6**
holds as an invariant. But the v0.2 **G5 roughness/spectrum gate was not faithfully implemented** — only a
narrow sanity check (rough luminance must not create chroma) was run — so `G5_roughness_spectrum_faithful =
False`, `first_pass_descriptor_control_validity_claim_allowed = False`, and the honest verdict is **HOLD**. No
descriptor-control validity is claimed yet.

## 3. What G5 must prove

A faithful G5 must establish, with predeclared thresholds fixed before running, that:

- **color-family response remains attributable to the intended chroma/opponent manipulation**, not to a generic
  roughness/spectrum property of the sequence;
- **roughness/spectrum measures do not explain color-descriptor movement** (low correlation between color
  response and a roughness/spectrum statistic across a bank that varies roughness independently of chroma);
- **luminance-only roughness cannot fake color** (a rough achromatic sequence produces no RG/BY/CHROMA response);
- **spectrum-matched nulls cannot fake color** (a null that matches the color channel's power spectrum but
  destroys its intended opponent structure is not scored like the intended fixture).

## 4. The core tension, and the G5a / G5b split

**The current color response statistic, per-channel temporal std, is determined by each channel’s variance / power spectrum under the frozen response definition.** A
spectrum-matched (phase-randomized) surrogate of a chroma channel preserves its power spectrum and therefore its
temporal std, so the intended fixture and its spectrum-matched null get the *same* per-channel response. This is
the same confound family that sank SAG (roughness) and frame-DET (continuity/spectrum): a variance-like statistic
cannot, by construction, separate structured chroma from a spectrum-matched chroma null. A faithful G5 must
therefore be split into two clearly-scoped sub-gates rather than one over-claimed check:

- **G5a — cross-channel roughness immunity (achievable now).** Roughness in one channel (especially luminance)
  must not leak into the color channels, and color response must not track a roughness statistic across fixtures
  where roughness varies independently of chroma content. This is faithfully testable with the existing
  per-channel descriptors, because gray has *exactly* zero chroma regardless of luminance roughness.
- **G5b — within-chroma spectrum immunity (likely exposes a descriptor limitation).** Structured chroma must be
  distinguishable from a spectrum-matched chroma null. With a per-channel-std response this is **predeclared to
  likely fail** (intended ≈ null), which would honestly reveal that the current chroma response is
  spectrum-explained. A structure-sensitive chroma descriptor would be needed to pass G5b — that is a **new
  descriptor and is out of scope here**; G5b is run as a diagnostic that will expose the limitation, not to
  manufacture a pass. CHROMA magnitude may behave differently under independent RG/BY phase changes, so G5b must
  report RG, BY, and CHROMA separately rather than hiding them behind max color response.

**Full G5 = G5a AND G5b.** If G5a passes but G5b does not, the honest verdict stays **HOLD** (validity not
established), with the reason recorded as "within-chroma spectrum immunity unmet with per-channel-std
descriptors." This split is the recommended design: it lets the achievable part be proven faithfully while
refusing to overclaim the part the current descriptors cannot support.

## 5. Proposed synthetic null / control fixtures (high-level; none built)

- **`rough_luminance_only_null`** — a rough (high-frequency / noise) achromatic sequence, chroma held at 0.
  Feeds G5a; expected RG/BY/CHROMA response ≈ 0.
- **`rough_chroma_null`** — a rough chroma sequence with **no coherent opponent structure** (independent noise in
  RG and BY at a predeclared roughness). Feeds G5b as the "no-structure but rough" reference.
- **`spectrum_matched_color_null`** — generated in Y′/RG/BY descriptor space, with Y′ held to the intended
  fixture’s Y′ series and RG/BY independently phase-randomized while preserving each channel’s amplitude
  spectrum. A shared-phase variant may be reported separately; RGB-space phase randomization is out of scope
  unless separately predeclared because it can reintroduce gamut/Y′ leakage.
- **`roughness_matched_color_vs_luminance_pair`** — a matched pair: a color change and a luminance change
  constructed to share `delta_rms` and spectral centroid. Feeds G5a; the color descriptor must respond to the
  color member and the luminance descriptor to the luminance member, with no cross-firing.
- **`phase_randomized_per_channel_surrogate`** (optional, only if simple enough at the fixture length) — a
  per-channel phase-randomized surrogate used to generate `spectrum_matched_color_null`; predeclared to be used
  only if it is well-behaved at the short synthetic length (see risks).

## 6. Measured roughness / spectrum statistics (predeclared)

Computed per fixture, per channel, on the descriptor's spatial-mean time series:

- **`delta_rms`** — RMS frame-to-frame change (temporal roughness).
- **`spectral_centroid` / frequency spread** — energy-weighted mean normalized frequency (and its spread) of the
  channel's temporal spectrum.
- **`response_vs_roughness_correlation`** — rank correlation between color response and `delta_rms`
  (and separately `spectral_centroid`) across the fixture bank.
- **`matched_null_response_ratio`** — intended color response divided by its matched-null (spectrum-matched)
  response; ≈ 1 means the descriptor cannot separate structure from spectrum.
- **Per-channel response ratios** — RG, BY, and CHROMA reported separately against their matched-null
  counterparts, not only max color response.

## 7. G5 pass/fail criteria (predeclared; named margins frozen before running)

Named constants (`NULL_BEAT_MARGIN`, `LEAK_CEIL`, `ROUGHNESS_CORR_CEIL`) are fixed in advance and never tuned
after. No pass may rest on a single favorable fixture — each sub-gate requires the condition to hold across a
predeclared majority of its applicable fixtures.

- **G5a passes iff all of:**
  - `rough_luminance_only_null` color response ≤ `LEAK_CEIL` (rough luminance cannot fake color); and
  - in `roughness_matched_color_vs_luminance_pair`, the color member drives color descriptors and the luminance
    member drives Y′, with cross-channel response ≤ `LEAK_CEIL` (no roughness-matched cross-firing); and
  - `|response_vs_roughness_correlation|` < `ROUGHNESS_CORR_CEIL` across the roughness-varied bank (color
    response tracks chroma content, not roughness).
- **G5b passes iff:** intended RG/BY/CHROMA responses, reported per channel, exceed their matched-null
  counterparts by `NULL_BEAT_MARGIN` (per-channel `matched_null_response_ratio ≥ 1 + NULL_BEAT_MARGIN`) across a
  majority of intended color fixtures. **Predeclared expectation:** with a per-channel-std response this is likely NOT met (ratio ≈ 1) →
  G5b FAIL/HOLD, exposing a descriptor limitation rather than granting a pass.
- **Full G5 = G5a AND G5b.** If G5b is unmet, verdict stays HOLD (validity not established); a G5a-only pass is
  reported as partial and does not license a descriptor-control validity claim.

## 8. Expected output tables (predeclared schemas — shapes fixed before implementation)

Placeholders `·`; no results exist yet.

**T1 — per-fixture intended vs null response:**

| fixture | role | color_response | matched_null_response | matched_null_response_ratio | beats_null? |
| --- | --- | --- | --- | --- | --- |
| (intended color fixtures + nulls) | intended/null | · | · | · | Y/n |

**T2 — roughness / spectrum statistics:**

| fixture | channel | delta_rms | spectral_centroid | color_response |
| --- | --- | --- | --- | --- |
| (each fixture) | Yp/RG/BY/CHROMA | · | · | · |

**T3 — G5 gate summary:**

| sub-gate | condition | threshold | result |
| --- | --- | --- | --- |
| G5a_luminance_no_color | rough_luminance_only_null ≤ LEAK_CEIL | `LEAK_CEIL` | PASS/FAIL |
| G5a_no_cross_fire | matched pair cross-response ≤ LEAK_CEIL | `LEAK_CEIL` | PASS/FAIL |
| G5a_roughness_corr | \|corr\| < ROUGHNESS_CORR_CEIL | `ROUGHNESS_CORR_CEIL` | PASS/FAIL |
| G5b_spectrum_immunity | ratio ≥ 1 + NULL_BEAT_MARGIN | `NULL_BEAT_MARGIN` | PASS/FAIL/HOLD |
| G5_full | G5a AND G5b | — | PASS/HOLD |

**T4 — HOLD / FAIL reason table:**

| verdict | driving sub-gate(s) | reason |
| --- | --- | --- |
| HOLD/FAIL | · | e.g. "within-chroma spectrum immunity unmet with per-channel-std descriptors" |

## 9. Risks / reasons to HOLD

- **Matching roughness may be ambiguous.** "Same roughness/spectrum" is not unique; `delta_rms`-matched and
  centroid-matched nulls can differ, and a null matched on one statistic may differ on another, weakening the
  "matched null" claim. The matched-on statistic(s) must be predeclared and reported.
- **Phase-randomization on short synthetic sequences may be misleading.** At the fixture length (tens of
  frames) the power spectrum is poorly estimated and phase randomization is ill-conditioned, so
  `spectrum_matched_color_null` may not faithfully represent "same spectrum, no structure." This is why the
  per-channel surrogate is optional and gated on being well-behaved at length.
- **Overfitting synthetic nulls.** Nulls hand-built to be beatable would make G5 pass vacuously; the nulls must
  be predeclared and adversarial, and G5b's likely-FAIL expectation is recorded precisely to resist this.
- **Real clips still required later.** Even a full synthetic G5 pass would be descriptor-control validity on
  constructed fixtures, not natural-video evidence; the offline gitignored clip corpus remains the eventual
  test where luminance and color actually correlate.

## 10. Non-claims and quarantine boundaries

This plan does **not**: build or select descriptors; implement any gate, null, or diagnostic; claim vision,
"Brainvision sees", object/scene understanding, temporal-order sensitivity, or classifier superiority; or
authorize any tuning. It adds no runtime integration, no live/screen capture, no service / camera / sensor
contact, and no prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no
tags.** Brainvision remains offline research under `research/brainvision/` + `tests/research/`, HELD per v0.6,
with `temporal_claim_allowed` **False**. **No implementation is authorized.**

## 11. Recommended next

- **Codex review** of this G5 design, especially the G5a/G5b split (§4) and the predeclared G5b likely-FAIL
  expectation.
- **If** accepted, a future reviewed offline slice may be proposed to implement **G5a faithfully** (rough-luminance null, roughness-matched
  color-vs-luminance pair, roughness-correlation ceiling) and **run G5b as a diagnostic** that is expected to
  expose the per-channel-std spectrum limitation and keep validity at HOLD — with all fixtures, statistics, and
  named margins predeclared before running. A structure-sensitive chroma descriptor (to actually pass G5b) is a
  separate, later question, not authorized here. No code, math, or tuning until reviewed.

*End — TORMENT Brainvision Color G5 Roughness/Spectrum Plan v0.4. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*
