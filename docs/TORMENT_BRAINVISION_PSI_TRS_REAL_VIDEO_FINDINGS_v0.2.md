# TORMENT Brainvision ΨTRS Real-Video Findings v0.2

**Status:** DOCS-ONLY research findings update. **Non-authorizing, non-implementing. Opens no
implementation lane and no service integration.** Extends
`TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_FINDINGS_v0.1.md` with three additional prerecorded clips run
through the existing offline v0.5.1 real-video route. Everything remains quarantined under
`research/brainvision/` + `tests/research/`; no `torment_service/` imports; no service / runtime / camera /
sensor / prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.**
No math was invented, no parameters tuned, no code/tests/manifests/local-inputs touched.

## 1. Summary

The clip1 result reported in v0.1 **repeated across three more real prerecorded clips**. Across clips 1–4
(8 descriptor windows each, 32 total), the fixed-clock baseline `G(k=0)` stayed coherent at **1.000** in
every reported summary, while the state-dependent clock `G(k>0)` amplified in **30 / 32 windows**. This
supports **repeatable offline ΨTRS symmetry-amplification survival across real descriptor fields** — the
strongest replicated offline evidence in this Brainvision research arc so far — while classification remains secondary (it saturated on
true-order vs time-shuffled and does not discriminate ΨTRS from fixed-clock or simple baselines).

## 2. Results (multi-window SAG, offline prerecorded clips)

| Clip  | Windows | G(k=0) mean/med/min/max | G(k>0) mean | G(k>0) median | G(k>0) min | G(k>0) max | Amplifying |
|-------|:-------:|:-----------------------:|:-----------:|:-------------:|:----------:|:----------:|:----------:|
| clip1 |    8    | 1.000 / 1.000 / 1.000 / 1.000 | 14.887 | 13.999 | 2.394 | 33.318   | 8/8 |
| clip2 |    8    | 1.000 / 1.000 / 1.000 / 1.000 | 22.327 | 21.810 | 4.215 | 51.488   | 8/8 |
| clip3 |    8    | 1.000 / 1.000 / 1.000 / 1.000 | 11.461 |  9.124 | 1.121 | 29.474   | 7/8 |
| clip4 |    8    | 1.000 / 1.000 / 1.000 / 1.000 | 231.530| 21.965 | 1.000 | 1694.543 | 7/8 |

**Total: 30 / 32 windows amplified. `G(k=0)` stayed coherent at 1.000 in all reported summaries.**

## 3. Interpretation

- **Repeatable survival across four prerecorded clips.** In every clip the fixed clock (κ=0) preserved
  coherence (G=1.000) while the state-dependent clock (κ>0) amplified in most or all windows. The v0.1
  single-clip signal is now replicated, not a one-off.
- **clip3 is weaker but still survives.** Its `G(k>0)` is the lowest (mean 11.461, median 9.124, min
  1.121 — one window barely above the coherent baseline), and 7/8 windows amplify. Weaker magnitude, same
  qualitative outcome.
- **clip4 survives but has an extreme outlier.** One window produced a very large gain (max 1694.543),
  inflating the mean to 231.530 while the median is 21.965. **The median is the more representative
  statistic here**; the mean should not be read as a typical per-window gain. 7/8 windows amplify.

## 4. Explicit non-claims

This evidence does **not**:

- prove ΨTRS is a superior classifier — true-order vs time-shuffled classification **saturated** across
  many descriptors (fixed-clock and recursive-time both max out), so it does not discriminate;
- prove a working vision system;
- authorize any runtime, camera, sensor, or service integration;
- establish that the amplification generalizes beyond these four clips.

Brainvision remains quarantined under `research/brainvision/` + `tests/research/`; simple/random baselines
remain part of every comparison; the recursive-time claim rests on SAG as the stronger diagnostic signal, not classifier rank.

## 5. Recommended next step

- **Do not add math yet.** The signal is repeatable but still narrow; new operators would outrun the
  evidence.
- **Either** run a **harder stress set later** (more varied real prerecorded clips — different content,
  motion, cuts, lengths, and deliberately adversarial/low-structure clips to probe where amplification
  fails) **or** ask **Codex for a claim-boundary review first**, to lock exactly what "repeatable offline
  ΨTRS SAG survival" is and is not allowed to assert before any further work.
- Continue evaluating **κ=0 vs κ>0 SAG across all windows** (per-window + summary + amplifying-window
  count), reporting the median alongside the mean given clip4's outlier behavior.

*End — TORMENT Brainvision ΨTRS Real-Video Findings v0.2. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added.*
