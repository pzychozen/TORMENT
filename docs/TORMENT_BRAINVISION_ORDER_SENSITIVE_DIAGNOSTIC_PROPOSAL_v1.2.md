# TORMENT Brainvision Order-Sensitive Diagnostic Proposal v1.2

## 1. Status / quarantine

**DOCS-ONLY proposal. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation
lane.** This note **predeclares a future direction and its acceptance/failure criteria before any operator or
math is written**, so a later diagnostic is judged against criteria fixed in advance. It implements no code,
adds no operator, changes no tests, and touches no `torment_service/`, runtime, camera / sensor / live-capture,
or prompt / context / memory / action / render-body / autonomy paths. **No `§0` pointer; no tags.** Everything
stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. Nothing here is an accepted fix,
and **this note itself makes no temporal-order claim** — it only defines what a future diagnostic would have to
prove. `temporal_claim_allowed` remains **False**.

## 2. Why v1.0/v1.1 showed roughness confounding (summary, not new analysis)

The v1.0 normalized-control-gated SAG candidate repaired the numeric-hygiene confounds (κ=0 coherence,
amplitude-scale sensitivity, low-energy blow-up, spike wins) but **failed temporal-order specificity**: after
median/MAD amplitude normalization the `time_shuffled` control still scored far above `true` (pooled medians
~true 8.4 vs shuffled 147.7), while `time_reversed` (~6.4) and `circular_shift` (~8.0) sat near `true`.

The v1.1 failure analysis supports the reading that (offline, characterization not proof): the SAG gain is **more aligned
with temporal roughness / spectral spread than with temporal order**. Shuffling is the only tested control that
broadens or roughens the temporal spectrum in these runs — it raises frame-to-frame delta and spectral centroid and drops lag-1
continuity — and it is the only one whose gain explodes. `time_reversed` and `circular_shift` preserve frame
adjacency (hence roughness) and stay near `true`. Amplitude normalization removed scale but not the
roughness-to-energy ratio, so shuffle keeps an advantage. A candidate mechanistic reading: SAG separates a
mirror-perturbed pair in proportion to the field's temporal gradient, which shuffle inflates. **Net: any
diagnostic that responds to roughness/spread will be inflated by shuffle. That is the obstacle v1.2 must
design around.**

## 3. The design problem: order and roughness are entangled by the current controls

A useful first step is to classify each control by what it *destroys* versus *preserves*. This makes explicit
that "beating shuffle" and "being roughness-blind" are not the same requirement, and that not every control is
one a true-order signal should beat.

| control | temporal order | frame adjacency (→ roughness) | arrow / direction | amplitude spectrum \|FFT\| |
| --- | --- | --- | --- | --- |
| true | preserved | preserved (smooth) | forward | preserved |
| time_shuffled | destroyed | destroyed (rough) | destroyed | broadened/roughened in these runs |
| time_reversed | preserved (backward) | preserved (smooth) | flipped | preserved |
| circular_shift | preserved | preserved (one wrap) | forward | preserved |

Two consequences shape the proposal:

- **Shuffle confounds order with roughness.** It is the only control that both destroys order *and* raises
  roughness, so a raw "true vs shuffled" contrast cannot tell the two apart. v1.2 must break this entanglement
  with dedicated roughness/spectral controls (§6), not with more temporal controls.
- **Circular-shift preserves order; reversed preserves undirected order.** A principled *undirected*
  order-sensitivity claim should treat `{true, reversed, circular}` as the ordered/adjacent group and
  `shuffled` as the disordered one — it should **not** require `true` to beat `circular` (which merely re-phases
  an ordered series). Requiring `true > circular` (as the v1.0 gate did) would penalize a correct order measure.
  Separating `true` from `reversed` is a *different and stronger* claim (arrow of time) and is tiered
  accordingly in §5.

## 4. What a future order-sensitive diagnostic must reward

At a high level, the target is a statistic/operator whose value comes from **ordered predictive / recurrent
structure that survives only when frames are in sequence**, and which is **invariant to marginal roughness /
spectral spread**. The design intent is that destroying order (shuffle) should *lower* the score even though it
*raises* roughness — the inverse of the current failure mode.

The single most important design principle, stated in advance: **per-window surrogate normalization.** For each
window, generate its own order-destroying surrogates that hold the confound fixed (predeclared matched or
measured marginal, roughness, and spectral properties), compute the candidate statistic on the true window and on its
surrogates, and report only the *standardized* difference (e.g. a z-score against the surrogate distribution).
Because the surrogate shares the window's roughness/spectrum but has order destroyed, any residual gap becomes
a candidate order-specific signal only if the surrogate checks show roughness/spread did not explain it. This is the classic surrogate-data hygiene and is what makes an
order claim separable from a roughness claim. It is a design principle here — **no surrogate generator or
statistic is implemented in this note.**

## 5. Candidate statistic / operator families (high-level only — none selected, none built)

Framed as **families to evaluate against §7/§8, not accepted fixes**. Each is named at the level of "what
structure it rewards"; no operator, formula, or pseudocode is specified.

- **Predictability / forecastability family** — an ordered series is more predictable from its own past than
  its shuffle at equal marginal roughness; reward low one-step-ahead prediction error *relative to the
  window's own shuffled surrogate*, so raw roughness cancels.
- **Recurrence-structure family** — reward the topological signature of ordered dynamics (long diagonal
  structure / determinism / laminarity in a delay-embedded recurrence view), which shuffle destroys and which
  is largely blind to amplitude scale.
- **Lagged-dependence family** — reward structured cross-time dependence between `t` and `t+τ` across lags
  (mutual-information- or transfer-entropy-like), which collapses under shuffle while single-frame variance
  (roughness) rises; directional asymmetry across lags is the natural Tier-B (arrow-of-time) probe.
- **Phase-structure family** — order/continuity lives largely in Fourier *phase* relationships rather than the
  amplitude spectrum; a phase-coherence-style measure that is amplitude(=roughness)-blind could separate
  ordered phase from randomized phase. (Noted as a family only; unrelated to any other programme's
  phase-coherence work.)

A future slice would pick **at most one** family, predeclare its surrogate normalization and thresholds, and
evaluate it — offline — against the criteria below before any wording about order is permitted.

## 6. First-class controls (predeclared)

Controls must be part of the score from the start, not an afterthought, and must include roughness/spectral
controls that dissociate the confound:

- **Temporal controls (as before):** `true`, `time_shuffled`, `time_reversed`, `circular_shift`.
- **Roughness / spectral controls (new, the point of v1.2):**
  - **amplitude-spectrum-matched surrogates** (phase-randomized while preserving `|FFT|`), to check the measure
    does not merely read the spectrum;
  - **roughness-matched probes that dissociate order from roughness**, including rough-but-ordered and
    smooth-but-disordered cases, to check the measure does not merely read roughness. A measure that scores the
    rough-but-ordered probe high and the smooth-but-disordered probe low is behaving as an order measure; the
    reverse pattern means it is still a roughness meter.

## 7. Predeclared success criteria (what would count as PASS)

A future diagnostic may make an **offline, undirected** order-sensitivity statement only if, with all
thresholds fixed before seeing outcomes, it:

- **Roughness invariance (mandatory pre-requisite):** does **not** separate the roughness/spectral controls of
  §6 by roughness alone — `shuffled` scores **low, not high**, and the rough-but-ordered probe is not penalized
  for being rough. If the score still rises with roughness/spread, the diagnostic fails here and no further
  tier is considered.
- **Tier A — undirected order:** each ordered/adjacent condition, or a predeclared group statistic with
  per-condition floors, must exceed `shuffled` by a robust median and surrogate z-threshold across
  heterogeneous fields and clips.
- **Tier B — arrow of time (optional, strictly higher claim):** `true` separates from `time_reversed` by a
  robust statistic. If Tier B is not achieved, only the Tier-A undirected-order statement may be made, and only
  offline.
- **Tier scope guard:** Failure to separate `true` from `time_reversed` or `circular_shift` blocks only Tier B,
  not Tier A, unless the proposed statistic explicitly depends on direction or absolute phase.
- **Hygiene carried forward:** deterministic, bounded, low-energy-safe, and spike-robust — inheriting the v1.0
  numeric gates so the redesign does not regress the confounds already fixed.

## 8. Predeclared failure criteria (reject or pause)

Reject or pause any v1.2 candidate if:

- `shuffled` still scores **≥** the ordered group (roughness still wins);
- the score **correlates with the roughness/spectral controls** of §6 (invariance fails);
- success **depends on a single field, seed, or spike**, or on mean/max rather than a robust statistic;
- the control taxonomy is applied **inconsistently** (e.g. demanding `true > circular`, which penalizes a
  correct undirected-order measure);
- **any parameter is tuned after seeing control/clip outcomes** (post-hoc tuning invalidates the result);
- a Tier-B (directional) claim is made **without** clearing Tier A and roughness invariance first.

## 9. Non-claims, forbidden moves, and quarantine boundaries

This note does **not**: prove a mechanism; propose or build an operator; implement any diagnostic; claim
temporal-order sensitivity, directionality, working vision, or classifier superiority; select a family; or
authorize any tuning. It adds no runtime integration, no live capture, no service / camera / sensor contact,
and no prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.** No
theory inflation and no "Brainvision works" claim. Brainvision remains offline research under
`research/brainvision/` + `tests/research/`, HELD per v0.6, with `temporal_claim_allowed` **False**.

## 10. Recommended next

- **Codex reviews this proposal** for over/under-statement, and in particular sanity-checks the control
  taxonomy in §3 (undirected-order grouping vs the v1.0 "beat all controls" rule) and the roughness-invariance
  pre-requisite in §7.
- Only after a PASS should a **single offline research slice** be considered — at most one family from §5,
  under `research/brainvision/` + `tests/research/` only, with surrogate-normalized controls first-class and all
  thresholds fixed before real-clip inspection. Until that review passes, no operator, math, or tuning is
  written.

*End — TORMENT Brainvision Order-Sensitive Diagnostic Proposal v1.2. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*
