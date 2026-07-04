# TORMENT Brainvision Descriptor→ψ Falsifier Design v0.1 — HELD Research Design

**Status:** DOCS-ONLY research-design document. **Non-authorizing, non-implementing. Opens no
implementation lane and no service integration.** This is the first *concrete* Brainvision experiment
design: it specifies one falsifiable experiment precisely enough to be implemented offline later, in
`research/brainvision/` or `experiments/brainvision/`, without importing anything from
`torment_service/`. Recording this design does not open it.

**The point is not to add a generic vision model.** The point is to test one sharp thing: whether the
*dynamics* of low-level visual descriptors carry a recursive/spectral structure — recurrence, rupture,
return-after-gap, snap/reset — that magnitude-based baselines (frame-diff, plain FFT, RGB statistics)
cannot express. If they do, Brainvision has a real signal to build on. If they don't, we close cleanly.

## 1. Status / boundary inheritance

This design inherits the hard boundary from
`TORMENT_BRAINVISION_OFFLINE_FALSIFIER_BOUNDARY_FRAME_v0.md` (tag
`brainvision-offline-falsifier-boundary-v0` at `8f9c9d3`) and the corrected surface statuses in
`TORMENT_BRAINVISION_RECOVERY_MAP_v0.5.md` (tag `brainvision-recovery-map-v0.5` at `8d4b8a4`).

Preserved without re-arguing the whole boundary doc:

- Does not open service integration. No imports from `torment_service/`, including
  `torment_service/kernel/`.
- `ψ-like` is an independently **re-derived** offline tensor. It does **not** import or reuse the dormant
  `RSBModel`, `definitions.py`, TriOctaMemoryKernel, or SRG.
- Inputs are fixed inert descriptor fixtures only — no camera/screen/sensor/process/browser/game/VR/OS
  streams.
- Outputs are non-authoritative offline research artifacts only, outside TORMENT memory, canon,
  substrate, or runtime state. No trigger/action/memory/prompt/render-body/identity/final-output contact.
- `PROJECT_ORIENTATION_MAP.md` Section 0 remains the active work-order; this doc adds no Section 0
  pointer. Ceiling remains memory/context floor + Mode 0.

## 2. Hypothesis

**Core research question.** Can simple visual/retinal descriptor sequences produce a ψ-like spectral
diagnostic shape that separates continuity, disruption, recurrence, salience-like contrast, or snap/reset
regimes *better than explicit baselines*?

**First testable claim (narrow).** Visual descriptor *dynamics* contain spectral recurrence/rupture
structure that is not captured by plain frame-diff or RGB/luminance statistics.

**Why this could differ from `visual_bus_v0` (which failed).** `visual_bus_v0` mapped the *spatial* FFT of
single frames (luminance / frame-diff / edge bands) into ψ, and lost to frame-diff. It tested a spatial
magnitude spectrum. This design tests something structurally different: the **temporal** spectral and
**return** structure of descriptor *time-series* — how a descriptor rises, falls, recurs, and returns
after a gap. Frame-diff is memoryless (a one-step magnitude); plain FFT is a phase-blind magnitude
spectrum; both are blind to return/recurrence structure and to rising-vs-falling polarity. The ψ-like
mapping is defined precisely to encode those. That is the falsifiable edge — if descriptor dynamics carry
no such structure beyond magnitude, the ψ-like tensor will not separate regimes better than the
baselines, and the claim is refuted.

## 3. Fixture families

Deterministic, seedable, synthetic **descriptor-sequence** fixtures — no object labels, no scenes, no
semantics. Each family is a generator of descriptor time-series with a known ground-truth regime. Minimum
families:

- **stable field** — descriptors flat within noise floor (continuity control).
- **smooth drift** — slow monotonic descriptor change (low-frequency continuity).
- **edge emergence** — gradual rise in edge-energy descriptor.
- **contrast pulse** — a transient spike in contrast energy then return (salience-like).
- **color-light shift** — a sustained shift in color-channel descriptors.
- **occlusion / interruption** — a sharp descriptor drop-out and partial recovery (disruption).
- **snap/reset** — abrupt collapse followed by reinitialization to a new baseline.
- **recurrence after gap** — a descriptor pattern that reappears after a quiet interval (long-return).
- **shuffled temporal order** — a real fixture with its time steps permuted (destroys temporal structure;
  a built-in control, not a regime).
- **random noise control** — i.i.d. descriptor noise (chance floor).

Fixtures are generated deterministically from fixed seeds; no fixture may be sourced from a live stream.

## 4. Descriptor families

Low-level, label-free descriptors computed per fixture time step (no object recognition, no semantics):

- luminance mean / variance
- contrast energy
- frame-diff magnitude
- edge-energy
- color-channel drift
- local patch variance
- temporal recurrence score (self-similarity of the recent descriptor window)
- phase/time continuity score (smoothness / phase alignment of the descriptor trajectory)

These are the raw channels `c` fed into the ψ-like mapping. They are also, by themselves, the
`descriptor-only classifier` baseline (Section 7) — so the experiment can measure what the ψ-like mapping
*adds* over the raw descriptors.

## 5. ψ-like mapping candidate

An independently re-derived offline tensor, **not** imported from `RSBModel`:

`PsiBV[t, c, m, h]`

- `t` = fixture time step (or sliding-window index).
- `c` = descriptor channel family (Section 4).
- `m` = spectral/temporal band — obtained by decomposing each descriptor's local time-window into
  multi-scale temporal bands (candidate offline decompositions: short/mid/long-lag autocorrelation bands;
  temporal-FFT or wavelet bands of the descriptor series; multi-scale return-time bins). `m` is *temporal*
  structure of the descriptor, not the spatial pixel spectrum `visual_bus_v0` used.
- `h` = a polarity / return split — the ψ-native axis plain FFT lacks. Candidate splits (pick and
  predeclare one per run): `{rising, falling}` (sign of local slope), or `{short-return, long-return}`
  (whether the descriptor re-approaches a prior value within a short vs long horizon), or
  `{stable, disruptive}`.

**Re-derived diagnostic scalars** (offline analogues of the recovery-map vocabulary — re-derived, never
imported): a normalized band entropy `H_bv(t)` over `m`; a dominant band `m0_bv(t) = argmax_m`; a
signed **return imbalance** `J_bv(t)` = short-return energy − long-return energy (a recurrence index); and
a recursive velocity `v_bv(t) = |ΔH_bv|`. These four time-series are the working surface for the
diagnostics in Section 6.

This section is conceptual and offline. It names shapes and candidate constructions, not code.

## 6. Diagnostics

Non-authorizing offline diagnostics, each stated as a *separability* question over the re-derived scalars
and PsiBV structure:

- **continuity/disruption separability** — do stable/drift fixtures vs occlusion/snap fixtures separate on
  `v_bv` spikes + `m0_bv` shifts?
- **recurrence-after-gap detection** — does the long-return channel (`h`) energy / `J_bv` mark a returning
  pattern that magnitude baselines miss?
- **snap/reset separability** — does a snap/reset show its characteristic signature (entropy dip then
  rise, or `J_bv` sign flip) distinct from a plain disruption?
- **descriptor-regime classification** — can a simple offline classifier assign the correct fixture-family
  regime from PsiBV features?
- **stability-vs-noise separation** — does PsiBV distinguish structured stability from random-noise
  control?

**Evaluation protocol (offline).** Generate fixtures from fixed seeds; split into train / held-out sets by
seed; predeclare metrics (e.g. balanced accuracy, AUC, or class-pair separability) before running; report
per-regime and per-fixture-family results; run every control in Section 7. All results are metrics/tables/
plots only.

## 7. Baselines

Every diagnostic is measured against explicit baselines. A "win" only counts as a win over these:

- **frame-diff** — the magnitude baseline that beat `visual_bus_v0`.
- **RGB / luminance statistics** — static appearance baseline.
- **descriptor-only classifier** — raw Section-4 descriptors with no ψ-like mapping (ablation: does the
  tensor add anything?).
- **plain FFT** — a plain temporal magnitude spectrum with no return/polarity split (ablation of the
  ψ-native `h` axis and recurrence structure).
- **random mapping** — random projection sanity check.
- **shuffled labels** — chance floor.
- **phase / time-shuffled controls** — destroy temporal structure; a real PsiBV win must vanish here (if
  it survives shuffling, it was an artifact, not temporal structure).
- **old `visual_bus_v0` fixed mapping** — as a failed / negative baseline reference where available.

## 8. Success criteria (predeclared)

- Beats simple baselines (frame-diff, plain FFT, RGB/luminance stats, descriptor-only) on held-out
  deterministic fixtures.
- Survives shuffled-label and phase/time-shuffled controls (the win disappears under shuffling, confirming
  it rests on real temporal structure).
- Separates **at least two** regime classes better than frame-diff and plain FFT.
- Produces only offline research artifacts.
- Requires no service imports and no live state.

## 9. Failure criteria (any of these closes the experiment)

- Does not beat the baselines. (This is a **valid closure**, not permission to widen scope.)
- Only wins on a single fixture family (no general structure).
- Collapses under shuffled / time-randomized controls (the "win" was an artifact).
- Requires widening input authority (live streams, more capture) to show an effect.
- Requires imports from `torment_service/` or reuse of `RSBModel` / SRG / TriOcta to show an effect.
- Produces trigger-, action-, memory-, or prompt-shaped outputs.

Any failure closes at design/experiment level. Closure does not authorize adding runtime inputs or live
surfaces to "make it work."

## 10. Future implementation sketch (very high-level, no code)

If — and only if — the operator later opens an implementation lane:

- **Location:** `research/brainvision/` or `experiments/brainvision/`, never `torment_service/`.
- **Possible files (names only, no code here):** deterministic `fixtures`, `descriptors`, the ψ-like
  `mappings`, `baselines`, `metrics`, and an offline `report`.
- **First lane:** an offline falsifier harness only — prerecorded/deterministic fixtures in, metrics and
  plots out, explicit baselines, no service imports, no live state.
- No code and no commands are included or authorized by this document.

## Current next-state

- Remain HELD. This is a design record, not an opened experiment.
- No Section 0 pointer yet (a separate later step if requested).
- The next legitimate move is an operator decision to open the offline experiment under trio authority, or
  a fresh-chat handoff — chosen deliberately, not opened by momentum.

The Brainvision Descriptor→ψ falsifier is: **designed / bounded / not opened / not implemented / offline
only / non-authoritative / held.**

*End — TORMENT Brainvision Descriptor→ψ Falsifier Design v0.1. Docs-only, non-authorizing. Opens no
implementation lane.*
