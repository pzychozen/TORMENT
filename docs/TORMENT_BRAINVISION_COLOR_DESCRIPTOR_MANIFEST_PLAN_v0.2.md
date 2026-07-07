# TORMENT Brainvision Color Descriptor Manifest / Plan v0.2

## 1. Status / quarantine and non-claims

**DOCS-ONLY plan. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation lane.**
It **freezes**, before any code, the minimum offline manifest schema, the first-pass color/opponent transform,
the synthetic fixture and prerecorded-clip categories, the control metadata, and the pass/fail gates for a
future color-descriptor bridge slice. It implements no descriptors, no diagnostic, no code, and no tests, and
touches no `torment_service/`, runtime, camera / sensor / live-capture, or prompt / context / memory / action /
render-body / autonomy paths. **No `§0` pointer; no tags.** Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6. **This plan makes no vision claim, no "Brainvision
sees" claim, and no temporal-order claim.** `temporal_claim_allowed` remains **False**. **No implementation is
authorized by this plan.**

## 2. Color-space / opponent transform choice (first-pass, frozen)

The first-pass transform is chosen for being **simple, deterministic, and fully auditable** — no whitepoint,
no ICC profile, no learned parameters. It is applied per pixel to sRGB values normalized to `[0, 1]`, on the
gamma-encoded values as delivered by the decoded frame (a declared first-pass choice; linearization is a later
refinement, see §9). Four channels are predeclared:

| channel | name | frozen first-pass definition | meaning |
| --- | --- | --- | --- |
| **Y′** | Rec.709-style luma proxy on gamma-encoded sRGB | `Y′ = 0.2126·R + 0.7152·G + 0.0722·B` (Rec.709 luma weights) | achromatic brightness proxy; the baseline/confound channel |
| **RG** | red–green opponent | `RG = R − G` | first chromatic axis |
| **BY** | blue–yellow opponent | `BY = B − (R + G)/2` | second chromatic axis (yellow ≈ (R+G)/2) |
| **CHROMA** | opponent chroma magnitude proxy | `CHROMA = sqrt(RG² + BY²)` | colorfulness magnitude, separated from the Y′ channel by definition, not perceptually orthogonal. |

Descriptor *families* (per the v0.1 proposal) are computed from these channels and their per-frame / temporal
statistics; this plan freezes only the **channel transform**, not the family formulas. Hue is representable as
`atan2(BY, RG)` but **hue-shift continuity, edges, coarse layout, and color×motion remain deferred** (not in
this slice). The transform is deliberately first-pass: §9 records that CIELAB (`L*, a*, b*`) or a
cone-opponent LMS transform are more perceptually grounded alternatives, held for a later revision.

This is not perceptually uniform and must not be described as true luminance, perceptual saturation, or a
calibrated opponent color space. It is acceptable only as a first-pass auditable bridge because the transform is
frozen, simple, and tested by controls.

## 3. Manifest schema (frozen)

Every fixture or clip entry in the offline manifest carries exactly these fields. (Descriptive schema; not a
code artifact.)

| field | meaning |
| --- | --- |
| `id` | unique stable identifier |
| `source_type` | `synthetic_fixture` or `local_prerecorded_clip` |
| `path_or_generator` | generator name (synthetic) or local gitignored path (clip); clips never committed |
| `category` | fixture/clip category (see §4/§5) |
| `expected_active_descriptors` | descriptors that should respond (predeclared, direction stated) |
| `expected_collapsed_descriptors` | descriptors that should go to baseline / not respond |
| `controls_to_run` | which §6 controls apply to this entry |
| `allowed_use` | `calibration` \| `validation` \| `stress` |
| `luminance_color_confound_notes` | explicit note on how luminance and color could be confounded for this entry, and how the entry guards it |
| `transform_id` | frozen transform/version used, including gamma-encoded vs linearized choice |
| `expected_direction_by_control` | predeclared sign/direction for each applicable control |
| `fixture_tolerances` | allowed Y′ drift / chroma drift / clipping tolerance for synthetic fixtures |

`allowed_use` discipline: **calibration** entries may inform predeclared expectations but are **not** evidence;
**validation** entries are scored against the gates; **stress** entries probe robustness/neutral handling and
cannot, on their own, produce a pass.

## 4. Minimum synthetic fixtures (frozen)

All are deterministic generators (seeded). Expectations are predeclared *before* running.

| fixture | what it varies | expected active | expected collapsed | allowed_use |
| --- | --- | --- | --- | --- |
| `luminance_only_change` | brightness only, chroma held ~0 | Y′ | RG, BY, CHROMA | calibration |
| `red_green_opponent_change` | modulate R–G, Y′ held | RG, CHROMA | (Y′ ~flat) | validation |
| `blue_yellow_opponent_change` | modulate B–Y, Y′ held | BY, CHROMA | (Y′ ~flat) | validation |
| `saturation_collapse` | reduce chroma toward gray, Y′ held | CHROMA↓ (RG, BY↓) | Y′ ~flat | validation |
| `hue_rotation_like` | rotate (RG, BY) angle, CHROMA & Y′ held | RG, BY shift; CHROMA ~flat | Y′ ~flat | validation |
| `color_only_equal_luminance` | chroma varies with Y′ equalized across frames | RG, BY, CHROMA | Y′ ~flat | validation (key) |
| `grayscale_control` | chroma set to 0 | Y′ | RG, BY, CHROMA | validation |
| `roughness_matched_color_change` | color change matched in roughness/spectrum to a null | color families (beyond roughness) | — | validation |
| `low_saturation_neutral` | near-achromatic, tiny chroma near a neutral floor | (neutral handling) | color families → neutral, not spurious | stress |

Synthetic fixtures must assert no unintended gamut clipping and must report measured Y′/RG/BY/CHROMA drift;
"Y′ held" means within a frozen tolerance, not assumed.

## 5. Minimum local prerecorded clip categories (frozen; local/gitignored)

No corpus is committed; clips live under a gitignored local path (the existing `real_video.py` LOCAL_INPUTS
pattern). Categories:

- **color-rich** — strongly chromatic content;
- **low-color** — near-achromatic content (color families should read low);
- **grayscale-like** — effectively achromatic source;
- **flicker / luminance-heavy** — rapid luminance change with little chroma (luminance-vs-color separability);
- **color-motion but stable luminance** — chroma dynamics with luminance roughly constant (the natural analogue
  of `color_only_equal_luminance`);
- **degraded / noisy** — compression/noise stress (robustness, neutral handling).

## 6. First-class controls (frozen)

- **Color / channel controls (primary):** `grayscale`, `saturation_collapse`, `hue_rotation`, `channel_shuffle`,
  `luminance_only`, `color_only / luminance_removed`.
- **Roughness / spectrum controls (where relevant):** amplitude-spectrum-matched (phase-randomized) surrogates
  and roughness-matched probes, so a descriptor response is not merely reading roughness/spectral spread.
- **Temporal controls — REPORTING ONLY:** `time_shuffle`, `time_reversal`, `circular_shift` are run and reported
  for completeness but are **not** claim gates in this plan. **No temporal-order claim is made or permitted
  here**; `temporal_claim_allowed` stays False regardless of temporal-control numbers.

## 7. Pass/fail gates (predeclared; thresholds frozen as named constants before running)

Each gate is directional; the named margins (`COLLAPSE_RATIO`, `SEPARATION_MARGIN`, `NEUTRAL_FLOOR`,
`ROUGHNESS_CEIL`) are fixed before any real clip or fixture is inspected and never tuned after.

- **G1 — luminance cannot fake color:** on `color_only_equal_luminance` (and the color-motion/stable-luminance
  clips), the color families must respond while the **Y′** descriptor must **not** reproduce the effect — the
  color response must exceed the luminance response by `SEPARATION_MARGIN`. This is the central separability
  gate.
- **G2 — color collapses as expected:** under `grayscale` and `saturation_collapse`, color families (RG, BY,
  CHROMA) must fall to ≤ `COLLAPSE_RATIO` of their color-rich baseline; **Y′** stays ~unchanged.
- **G3 — luminance descriptor does not reproduce color-only effects:** the **Y′** descriptor's response on
  color-only fixtures/clips must stay below the same `SEPARATION_MARGIN` threshold (the mirror of G1).
- **G4 — low-saturation neutral handling:** `low_saturation_neutral` must be handled as neutral (no spurious
  large color response); values below `NEUTRAL_FLOOR` report neutral, not amplified.
- **G5 — roughness/spectrum controls do not explain color movement:** color-family response must remain
  attributable to the intended color manipulation after roughness/spectrum controls; roughness/spectrum measures
  must not explain the color movement above `ROUGHNESS_CEIL`.
- **G6 — no temporal-order claim:** temporal controls are reported only; no gate in this plan may be read as a
  temporal-order or arrow-of-time result, and `temporal_claim_allowed` remains False.

A slice may state a **first-pass descriptor-control validity** result only if G1–G5 pass on **validation** entries across a
predeclared majority of categories (not one favorable case); G6 is an invariant, not an achievement.

## 8. Expected output tables (predeclared schemas — shapes fixed before implementation)

Placeholders shown as `·`; no results exist yet.

**T1 — manifest summary:**

| source_type | category | n_entries | allowed_use mix |
| --- | --- | --- | --- |
| · | · | · | · |

**T2 — per-fixture descriptor response (median):**

| fixture | Y′ | RG | BY | CHROMA | matches_expected_active/collapsed? |
| --- | --- | --- | --- | --- | --- |
| (each fixture) | · | · | · | · | Y/n |

**T3 — control response matrix (descriptor × control; Δ vs baseline):**

| descriptor | grayscale | saturation_collapse | hue_rotation | channel_shuffle | luminance_only | color_only | spectrum_matched |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Y′ | · | · | · | · | · | · | · |
| RG | · | · | · | · | · | · | · |
| BY | · | · | · | · | · | · | · |
| CHROMA | · | · | · | · | · | · | · |

**T4 — luminance/color separability gate (G1/G3):**

| entry | color_response | luminance_response | separation | G1_pass | G3_pass |
| --- | --- | --- | --- | --- | --- |
| color_only_equal_luminance | · | · | · | Y/n | Y/n |

**T5 — neutral / stress cases:**

| entry | descriptor | value | neutral_floor | handled_as | verdict |
| --- | --- | --- | --- | --- | --- |
| low_saturation_neutral | CHROMA | · | `NEUTRAL_FLOOR` | neutral/amplified | Y/n |

**T6 — gate summary:** G1…G6 PASS/FAIL/NA with the frozen thresholds used. (Temporal controls appear as
reported columns only, never as a gate.)

## 9. Risks / reasons to HOLD before implementation

- **Color-space choice may encode a confound.** The first-pass Rec.709-luma + linear-opponent transform is
  auditable but not perceptually uniform; `R − G` and `B − (R+G)/2` are not calibrated opponent axes, and using
  gamma-encoded (non-linearized) sRGB mixes luminance nonlinearity into the color channels. A wrong first-pass
  bakes a luminance/color confound into every downstream gate. CIELAB / cone-opponent alternatives are the
  named fallback.
- **Natural videos correlate luminance and color** (bright regions are often saturated), so G1 (luminance
  cannot fake color) may be *hard to pass* on real clips — a genuine HOLD/null risk, not a formality.
- **Synthetic fixtures may not generalize.** The fixtures are linear/constructed; passing G1–G5 on synthetics is
  necessary but not sufficient, and cannot substitute for the local clip categories.
- **Scope drift toward vision / object recognition.** "Structure" can pull toward layout/object understanding;
  hue continuity, edges, coarse layout, and color×motion are deferred precisely to hold the descriptor-level and
  "no Brainvision sees" boundaries.
- **Implementation must not begin without manifest review.** No descriptor code should start until this manifest
  schema, the transform choice, the fixture/clip set, and the frozen gate thresholds are reviewed and accepted.

**Recommended posture: HOLD for review.** Freeze this manifest, transform, fixtures, controls, and gates; obtain
Codex/operator review of the transform choice (§2) and the G1 separability design (§7) before any code. No
operator, math, or tuning until then.

## 10. Non-claims (restated) and quarantine boundaries

This plan does **not**: build or select descriptors; implement any transform or diagnostic; claim vision,
"Brainvision sees", object understanding, temporal-order sensitivity, or classifier superiority; or authorize any
tuning. It adds no runtime integration, no live capture, no service / camera / sensor / live-capture contact, and
no prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.** Brainvision
remains offline research under `research/brainvision/` + `tests/research/`, HELD per v0.6, with
`temporal_claim_allowed` **False**. **No implementation is authorized.**

*End — TORMENT Brainvision Color Descriptor Manifest / Plan v0.2. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*
