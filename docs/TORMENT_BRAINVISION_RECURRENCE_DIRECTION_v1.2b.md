# TORMENT Brainvision Recurrence Direction v1.2b

## 1. Status / quarantine

**DOCS-ONLY direction note. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It uses the v1.2a FAIL to define — but not build — the next candidate direction, and
records the reasons this may instead be a HOLD. It implements no code, adds no operator, changes no tests, and
touches no `torment_service/`, runtime, camera / sensor / live-capture, or prompt / context / memory / action /
render-body / autonomy paths. **No `§0` pointer; no tags.** Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6. **This note makes no temporal-order claim.**
`temporal_claim_allowed` remains **False**. **No v1.2b implementation is authorized by this note.**

## 2. What v1.2a ruled out

The frame-level (m = 1) recurrence-determinism (DET) diagnostic, scored raw, is **continuity/roughness- and
spectrum-confounded** and cannot support an order claim. At the frozen constants (RR_target = 0.10, w = 0,
ℓmin = 3), DET separated the ordered/adjacent group from `time_shuffled` at face value, but the predeclared
roughness-invariance pre-requisite failed on three independent checks:

- `smooth_low = False` — `smooth_disordered` scored DET ≈ 0.619 (high, not low);
- `spectrum_low = False` — the amplitude-spectrum-matched surrogate scored DET ≈ 0.413 (high, not low);
- `corr_ok = False` — Spearman(DET, delta_rms) = **−0.746** (DET is strongly, inversely tied to roughness).

The secondary sensitivity (w = 1, w = 2, ℓmin = 2) confirmed the confound is robust (ρ ≈ −0.70 to −0.78), so
it is not a near-diagonal artifact of w = 0. **Reading: raw frame DET largely measures local temporal
continuity (smoothness) and the power spectrum, which time-shuffle destroys — not temporal order per se.**

## 3. What v1.2a did NOT rule out

The `rough_ordered` probe (a deterministic high-frequency periodic trajectory) scored DET ≈ 0.691 — high DET
despite being rough — so recurrence structure **can** detect a planted periodic recurrence that is not reducible
to smoothness. The limitation is that this signal is not cleanly separable from continuity/spectral structure in
the raw pooled statistic. So the recurrence family is not dead; what failed is the **raw, un-normalized** frame
DET, not the idea that ordered recurrence is measurable.

## 4. What the next direction must satisfy

Because v1.2a failed on **both** `smooth_low` and `spectrum_low`, any next direction must defeat **two** distinct
false-positive classes at once:

- **smooth-continuity false positives** — a smooth-but-disordered window (local continuity, no genuine ordered
  recurrence) must not score as ordered; and
- **spectrum-matched false positives** — a phase-randomized surrogate with the same amplitude spectrum,
  preserving the autocorrelation implied by that spectrum while not guaranteeing identical finite-sample
  roughness, must not score as ordered.

A direction that fixes only one of these would re-fail the other. This is the lens for comparing the two
candidates below.

## 5. Direction 1 — surrogate-normalized DET residual

**Idea (high level, not a spec):** replace raw DET with a residual/standardized score of DET against a
per-window **amplitude-spectrum-matched (phase-randomized) surrogate ensemble** — i.e. score only the DET that
remains after subtracting what a same-spectrum, order-destroyed surrogate already produces.

**How it addresses the two false-positive classes:** The spectrum-matched surrogate preserves the amplitude
spectrum, so it controls for the linear autocorrelation/spectral contribution and approximates the continuity
contribution. A smooth-but-disordered window should be tested against this surrogate rather than assumed solved;
any positive residual is only a candidate beyond-spectrum signal if the surrogate ensemble and dissociation
probes show the spectrum/roughness controls did not explain it.

**What it actually measures:** order **beyond the spectrum** — nonlinear determinism — because linear order
(periodicity/autocorrelation represented in the amplitude spectrum) is largely reproduced or controlled for by
a spectrum-matched surrogate and is therefore subtracted away. This is the classic surrogate-data nonlinearity test.

## 6. Direction 2 — long-range / period-diagonal recurrence scoring

**Idea (high level, not a spec):** restrict DET to **long-range diagonals** (recurrences separated by large
time gaps / period-locked offsets), excluding the short-offset near-diagonal lines where local smoothness lives.

**How it addresses the false-positive classes:** it defeats **smooth-continuity** cleanly — continuity is a
short-offset phenomenon, so a smooth-but-disordered window (which never revisits a past sequence at long range)
scores low on long-range diagonals. But it does **not**, by itself, defeat **spectrum-matched** false positives:
a phase-randomized surrogate of a narrowband/periodic signal preserves the period, so it retains long-range
diagonals too. Direction 2 therefore still needs the spectrum-matched control as a separate gate, and for
purely periodic (spectrum-explained) order it cannot beat that control.

## 7. Comparison and recommendation

| criterion | Direction 1 (surrogate residual) | Direction 2 (long-range diagonals) |
| --- | --- | --- |
| defeats smooth-continuity | tests/controls via surrogate residual | partly, by excluding short offsets |
| defeats spectrum-matched | yes, by construction | **no** (needs a separate spectral gate; fails for periodic order) |
| what it measures | order beyond the spectrum (nonlinear determinism) | long-range recurrence (may still be spectrum-explained) |
| main risk | may be ~0 for linearly-ordered fields (null) | re-fails `spectrum_low` for periodic order |

**Recommended (at most one): Direction 1 — surrogate-normalized DET residual.** It is the only candidate that
structurally addresses **both** confounds v1.2a exposed; Direction 2 fixes only continuity and would re-fail the
spectrum gate for periodic order. Direction 2's long-range restriction is worth keeping as a *possible component
folded into a Direction-1 plan* (strip short-offset continuity before the surrogate comparison), but not as a
standalone direction.

## 8. How the recommended direction avoids the two false-positive classes

- **smooth-continuity:** the per-window spectrum-matched surrogate carries comparable spectrum-implied continuity
  as the true window, so the residual removes it; a smooth-but-disordered window yields residual ≈ 0.
- **spectrum-matched:** the surrogate *is* the spectrum-matched control, so spectrum-explained structure is the
  null model being subtracted; only structure a same-spectrum surrogate cannot reproduce survives as a positive
  residual.

The predeclared gate would then require the ordered group to show a positive residual **beyond** its surrogate
ensemble by a fixed margin/z, with the same first-class shuffle/reverse/circular controls and the same
roughness-invariance and dissociation probes as v1.2a — thresholds fixed before any real-clip inspection.

## 9. Risks / reasons to HOLD

- **Direction 1 may bottom out at "no order beyond spectrum."** If the descriptor fields' temporal order is
  linear (periodic / autocorrelated), spectrum-matched surrogates reproduce it and residuals are ≈ 0 — an
  honest **null**, not a win. Note the `rough_ordered` anchor (a near-pure sine) would itself residual ≈ 0 by
  design, because a sine's order *is* its spectrum. There is a real chance the recurrence family terminates here
  as an honest negative for these fields.
- **Target-definition question (should be resolved before any plan).** The v1.2 framework treats "order beyond
  the spectrum" as the bar. If spectrum-explained temporal order (periodicity, continuity) is actually
  acceptable for Brainvision's purpose, then the spectrum-matched gate is *too strict* and the whole
  direction is mis-aimed. Whether Brainvision needs order-beyond-spectrum or is content with spectrum-level
  temporal structure is a values/product call for the operator, not a code decision.
- **Surrogate-generation is itself a modeling choice.** Simple phase randomization vs iterative
  amplitude-adjusted (IAAFT) surrogates, ensemble size, and how the residual/z is defined are all decisions that
  must be predeclared and reviewed before any run; a careless choice could manufacture or destroy a residual.
- **Real-clip availability.** No claim can rest on synthetic fields alone; the synthetic bank is linear by
  construction, so it cannot, on its own, demonstrate order-beyond-spectrum even if the method is sound.

Given the first two risks, a defensible position is to **HOLD**: resolve the target-definition question first,
then decide whether a v1.2b predeclared plan around Direction 1 is worth writing.

## 10. Non-claims, forbidden moves, and quarantine boundaries

This note does **not**: prove a mechanism; build or select an operator; implement any diagnostic; claim
temporal-order sensitivity, directionality, working vision, or classifier superiority; or authorize any tuning.
It adds no runtime integration, no live capture, no service / camera / sensor contact, and no prompt / context /
memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.** Brainvision remains offline
research under `research/brainvision/` + `tests/research/`, HELD per v0.6, with `temporal_claim_allowed`
**False**. **No v1.2b implementation is authorized.**

## 11. Recommended next

- **Codex / operator resolve the §9 target-definition question** (order-beyond-spectrum vs spectrum-level
  temporal structure) before anything else.
- **If** the answer is order-beyond-spectrum, then a docs-only **v1.2b predeclared plan** around Direction 1 may
  be written next (with surrogate generation, residual/z definition, controls, dissociation probes, and
  thresholds all fixed in advance). **Otherwise HOLD** the recurrence family as an honest negative and revisit
  whether a different family (or a different target) is warranted. No operator, math, or tuning until then.

*End — TORMENT Brainvision Recurrence Direction v1.2b. Docs-only, non-authorizing. Opens no implementation lane;
no `§0` pointer added; no tags.*
