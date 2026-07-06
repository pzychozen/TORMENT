# TORMENT Brainvision Color / Structure Descriptor Bridge Proposal v0.1

## 1. Status / quarantine

**DOCS-ONLY proposal. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation
lane.** It defines a candidate direction — offline, color-aware **descriptors** for prerecorded frames — and the
control discipline a future plan would predeclare. It implements no code, adds no operator, changes no tests,
and touches no `torment_service/`, runtime, camera / sensor / live-capture, or prompt / context / memory /
action / render-body / autonomy paths. **No `§0` pointer; no tags.** Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6. **This note makes no vision claim, no
temporal-order claim, and no "Brainvision sees" claim.** `temporal_claim_allowed` remains **False**. No
implementation is authorized by this note.

## 2. Why deeper recurrence math is on HOLD

The temporal-diagnostic line reached an honest limit, and each step failed the same way — a confound wearing the
costume of signal:

- **SAG (v0.x–v1.0)** was **roughness / spectral-spread aligned**, not temporal-order-specific: time-shuffle
  scored as high or higher than true, and after normalization the gain tracked spectral spread rather than
  order.
- **Frame-level recurrence DET (v1.2a)** was **continuity / spectrum-confounded**: it separated ordered from
  shuffled at face value, but the roughness-invariance pre-requisite failed on three independent checks
  (`smooth_low`, `spectrum_low`, `corr_ok`) with Spearman(DET, delta_rms) = −0.746 — so the separation was
  local smoothness and power spectrum, not clean order.
- **The recurrence residual (v1.2b)** is principled but may be **too strict**: it measures only order *beyond*
  the amplitude spectrum (nonlinear determinism), so if the near-term target actually accepts controlled,
  spectrum-level visual dynamics, the residual is aimed at the wrong bar and would likely return an honest null.

The through-line: **before more temporal math, the descriptors themselves must demonstrably capture the intended
visual/color structure and be separable from roughness/luminance confounds.** A temporal diagnostic built on
opaque descriptor fields inherits whatever confound those fields carry. So deeper recurrence work is **HELD**
pending descriptor quality — this proposal is the descriptor-quality track (Path B).

## 3. The new target

The target is **not**:

- not "AI sees" / "Brainvision sees";
- not object recognition, detection, or scene understanding;
- not runtime, live, or camera vision;
- not a temporal-order or arrow-of-time claim.

The target **is**: controlled, offline, falsifiable low-level descriptors of visual/color dynamics computed on
prerecorded frame stacks. For the first bridge slice, this means a minimal luminance + color-opponent +
saturation descriptor set; hue continuity, edges, coarse layout, and color×motion remain later candidates, not
part of the initial target.

## 4. Descriptor families (high-level only — none specified, none built)

Named at the level of "what visual property it summarizes"; no color-space formula, transform, or code is
specified here. Each family carries the confound it must later be shown separable from.

- **Luminance dynamics** — per-frame achromatic brightness and its temporal change. The baseline channel; the
  chief confound for every color family (color must be shown to be more than luminance).
- **R–G opponency** — red-vs-green opponent signal dynamics, color information carried orthogonally to
  luminance.
- **B–Y opponency** — blue-vs-yellow opponent signal dynamics, the second chromatic axis.
- **Saturation dynamics** — colorfulness / chroma magnitude and its change over time.
- **Hue-shift continuity** — continuity/smoothness of hue *angle* over time (a circular quantity requiring
  circular handling), distinct from saturation or luminance.
- **Color edge / change summaries** — density and change of chromatic boundaries (spatial and temporal), not
  edges of recognized objects.
- **Spatial contrast / coarse layout** — coarse low-resolution contrast and gross spatial arrangement (e.g. a
  small grid), explicitly *not* object localization.
- **Motion / color interaction summaries** — coarse co-variation of color and motion (e.g. whether chromatic
  regions move or stay static), not tracking or optical-flow of objects.

## 5. First-class controls (predeclared)

Controls are part of the score from the start, grouped by what they probe. The temporal group carries the exact
lesson from SAG/recurrence; the color/channel group is the new dissociation machinery; the roughness/spectrum
group prevents a repeat of the v1.1/v1.2a confounds.

- **Temporal:** `time_shuffle` (destroys order, raises roughness), `time_reversal` (preserves |FFT|, flips
  direction), `circular_shift` (moves phase origin).
- **Channel / color ablations:** `channel_shuffle` (permute descriptor channels); `grayscale` (remove chroma →
  all color families should collapse to a baseline); `hue_rotation` (rotate hue angle → hue/opponent families
  should track predictably, luminance should not); `saturation_collapse` (desaturate → saturation/opponent
  families drop, luminance preserved); `luminance_only` (keep luminance, zero chroma); `color_only /
  luminance_removed` (equalize luminance, keep chroma → color families should survive, luminance family should
  collapse).
- **Roughness / spectrum (where relevant):** amplitude-spectrum-matched (phase-randomized) surrogates and
  roughness-matched probes, so a descriptor response is not merely reading roughness/spectral spread.

## 6. What a future descriptor bridge must prove

Predeclared validation obligations (thresholds fixed in advance, before inspecting any real clip):

- **Respond to color/structure, not just roughness:** color families must move under `hue_rotation` /
  `saturation_collapse` while roughness/spectrum controls do not explain the observed color-family movement —
  a dissociation, not an assumption.
- **Color controls act predictably:** `hue_rotation` shifts hue/opponent descriptors in the expected direction;
  `saturation_collapse` lowers saturation/opponent descriptors; `grayscale` collapses all color families toward
  a baseline. Predicted directions are declared before running. These predicted directions are valid only after
  the color space/opponent transform is predeclared.
- **Luminance cannot fake color:** a `color_only / luminance_removed` clip must still drive the color families,
  and the luminance family must **not** reproduce color-only effects. This is the central separability gate —
  the color/luminance confound is the analogue of the roughness confound from the temporal work.
- **Temporal controls stay first-class, but no order claim without gates:** temporal controls are always run,
  but `temporal_claim_allowed` stays **False** unless a future, separately predeclared temporal gate passes
  (inheriting the SAG/recurrence discipline). Descriptor quality is not a temporal-order result.
- **Hygiene carried forward:** deterministic, robust statistics, neutral handling for degenerate frames, and no
  parameter tuning after seeing outcomes.

## 7. Likely future clip-manifest categories

Predeclared categories for an eventual **offline, local, gitignored** prerecorded corpus (never committed;
consistent with the existing `real_video.py` LOCAL_INPUTS pattern). These fix the test surface before any run:

- **color-rich** — strongly chromatic content;
- **low-color** — near-achromatic content (color families should read low);
- **hardcut** — abrupt scene changes (edge/change and temporal controls);
- **smooth motion** — continuous camera/subject motion;
- **flicker** — rapid luminance oscillation (luminance vs color separability);
- **periodic motion** — repeating motion (temporal controls, spectrum);
- **chaotic motion** — irregular motion (roughness/spectrum controls);
- **object motion vs background motion** — differential motion (color×motion family, no object ID);
- **degraded / noisy clips** — compression/noise stress (robustness, neutral handling).

## 8. Recommended descriptor-bridge target (at most one first slice)

**Recommended: a minimal color-opponent + luminance descriptor set, validated on the static color/channel
controls first — temporal and motion deferred.** Concretely, the first future slice (a *plan*, not built here)
should cover only **luminance dynamics + R–G opponency + B–Y opponency + saturation**, and prove them out
against the **color/channel ablations and roughness/spectrum controls** — i.e. establish that these descriptors
behave predictably under controls and are separable from luminance/roughness confounds — **before** adding hue continuity, edges, coarse
layout, or the color×motion family, and well before any temporal-order gate. Descriptor quality first, temporal
later. The riskiest families (motion/color interaction, coarse layout) are explicitly deferred to avoid drift
toward object/scene understanding.

## 9. Risks / reasons to HOLD before implementation

- **No corpus exists yet.** The manifest categories in §7 are aspirational; without an assembled offline corpus
  the descriptors can only be exercised on synthetic color fields, which — exactly as the SAG/recurrence
  synthetics did — may not generalize. Assembling and predeclaring the corpus is a prerequisite, not a detail.
  No descriptor implementation should begin until the offline manifest schema and minimum clip/fixture set are
  written down, including source, transformation, ablation, and expected-control metadata.
- **Color-space choice is a modeling decision.** Which opponent representation (e.g. a YCbCr-style, CIELAB-style,
  or cone-opponent-style transform) is chosen bakes in a specific luminance/color split; it must be predeclared
  and justified, or it silently reintroduces a confound.
- **Color and luminance are correlated in natural video** (bright regions are often saturated), so the
  "luminance cannot fake color" gate may be *hard to pass* on real clips — a genuine HOLD/null risk, not a
  formality.
- **Scope-creep toward "vision."** "Visual structure" can drift toward object/scene understanding; the
  descriptor-level boundary and the "no Brainvision sees" line are easy to erode and must be actively policed.
- **The temporal lesson still applies.** Even excellent color descriptors will, under any temporal diagnostic,
  re-inherit the roughness/spectrum/continuity confounds; this bridge must not be read as re-opening a
  temporal-order path. It is descriptor quality only.

**Recommended posture: HOLD-gated proceed.** Proceed only to a docs-only *plan* for the minimal color-opponent
set (§8) with static color/channel controls, and only after (a) a predeclared color-space choice, (b) an
assembled offline manifest for at least the color-rich / low-color / grayscale-ablation cases, and (c) the trio
confirming the "descriptor quality, not vision" framing. No operator, math, or tuning until that plan is
reviewed.

## 10. Non-claims, forbidden moves, and quarantine boundaries

This proposal does **not**: prove a mechanism; build or select descriptors; implement any diagnostic; claim
vision, "Brainvision sees", object understanding, temporal-order sensitivity, or classifier superiority; or
authorize any tuning. It adds no runtime integration, no live capture, no service / camera / sensor / live-capture
contact, and no prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no
tags.** Brainvision remains offline research under `research/brainvision/` + `tests/research/`, HELD per v0.6,
with `temporal_claim_allowed` **False**. **No implementation is authorized.**

## 11. Recommended next

- **Codex / operator confirm the framing** (descriptor quality, not vision) and the recommended first target
  (§8), and resolve the color-space choice and corpus questions (§9).
- **If** confirmed, a docs-only **descriptor-bridge plan** may be written next — minimal color-opponent set,
  static color/channel + roughness/spectrum controls, predeclared proof obligations and thresholds, and a small
  predeclared offline manifest — with temporal and motion families deferred. **Otherwise HOLD.** No code, math,
  or tuning until that plan is reviewed.

*End — TORMENT Brainvision Color / Structure Descriptor Bridge Proposal v0.1. Docs-only, non-authorizing. Opens
no implementation lane; no `§0` pointer added; no tags.*
