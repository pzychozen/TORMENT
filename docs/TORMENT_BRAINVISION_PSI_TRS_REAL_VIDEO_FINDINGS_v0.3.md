# TORMENT Brainvision ΨTRS Real-Video Findings v0.3

## 1. Status / quarantine

**DOCS-ONLY research findings update. Non-authorizing, non-implementing. Opens no implementation lane and
no service integration.** Extends `TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_FINDINGS_v0.2.md` with an
adversarial five-clip stress set run through the existing offline v0.5.1 real-video route. Everything
remains quarantined under `research/brainvision/` + `tests/research/`; no `torment_service/` imports; no
service / runtime / camera / sensor / live-capture / prompt / context / memory / action / render-body /
autonomy contact. **No `§0` pointer; no tags.** No math invented, no parameters tuned, no code/tests
edited, no manifests/local-inputs/integration files touched.

## 2. Summary

The v0.2 result (four prerecorded clips, 30/32 windows amplifying) **survived an adversarial stress set**.
Five deliberately hard clips — static/low-motion, chaotic motion, hard-cut/discontinuity, repetitive/
periodic, and degraded/low-structure — amplified in **39/40 windows** (stress survival fraction 0.975),
with the fixed clock `G(k=0)` staying coherent at **1.000** throughout. Across all nine clips the count is
**69/72 windows amplifying** (overall fraction 0.958). This strengthens the supported claim from
"repeatable across four prerecorded clips" to **"repeatable across heterogeneous prerecorded descriptor
fields, including a five-clip adversarial stress set"** — but the claim stays narrow: **offline
recursive-time SAG survival only.**

## 3. Results (multi-window SAG, offline prerecorded clips)

| Clip           | Set    | Windows | G(k=0) | G(k>0) mean | median | min   | max      | Amplifying |
|----------------|--------|:-------:|:------:|:-----------:|:------:|:-----:|:--------:|:----------:|
| clip1          | v0.2   |    8    | 1.000  | 14.887  | 13.999 | 2.394 | 33.318   | 8/8 |
| clip2          | v0.2   |    8    | 1.000  | 22.327  | 21.810 | 4.215 | 51.488   | 8/8 |
| clip3          | v0.2   |    8    | 1.000  | 11.461  |  9.124 | 1.121 | 29.474   | 7/8 |
| clip4          | v0.2   |    8    | 1.000  | 231.530 | 21.965 | 1.000 | 1694.543 | 7/8 |
| clip5_static   | stress |    8    | 1.000  | 50.042  | 11.204 | 1.000 | 295.816  | 7/8 |
| clip6_chaotic  | stress |    8    | 1.000  | 32.928  | 16.963 | 3.452 | 99.875   | 8/8 |
| clip7_hardcut  | stress |    8    | 1.000  | 38.364  | 40.023 | 6.829 | 73.116   | 8/8 |
| clip8_periodic | stress |    8    | 1.000  | 17.546  | 17.040 | 4.425 | 39.506   | 8/8 |
| clip9_degraded | stress |    8    | 1.000  | 558.006 | 37.185 | 2.676 | 1587.801 | 8/8 |

`G(k=0)` mean/median/min/max = 1.000 for every clip. **Stress set: 39/40 (0.975). Overall clip1–clip9:
69/72 (0.958).**

## 4. Stress-set interpretation

- The recursive-time SAG survival **survived across an adversarial stress set**, not just the earlier
  ordinary clips. Every stress category amplified in most or all windows while κ=0 stayed coherent.
- Coverage spanned distinct failure-probing regimes: static/low-motion, chaotic motion,
  hard-cut/discontinuity, repetitive/periodic, and degraded/low-structure regimes.
- The one non-amplifying window each in clip3, clip4, and clip5_static keeps the fraction below 1.0
  (0.958 overall) — the effect is strong and repeatable, **not universal per-window.**

## 5. Classification remains secondary

Classification is **not** the evidence here and must not be cited as ΨTRS superiority. Across clips the
true-order vs time-shuffled task saturates on many descriptors (fixed-clock and recursive-time both max
out), and `random_mapping` can score high on some clips. The recursive-time claim rests on SAG as the
stronger diagnostic signal, not classifier rank.

## 6. Spike / outlier warning

Some clips survive but are **spike-sensitive**: a single window can dominate the mean.

- **clip5_static:** mean 50.042 vs median 11.204, max 295.816.
- **clip9_degraded:** mean 558.006 vs median 37.185, max 1587.801.
- (Also from v0.2: **clip4** mean 231.530 vs median 21.965, max 1694.543.)

Read **medians beside means**; the median is the safer representative statistic for spike-heavy clips. **Do not describe the
huge maxima as stable giant amplification** — a 1000×+ single-window spike is not steady amplification.
Spike-heavy behavior is a **separate instability/fragility question**, to be studied on its own, not folded
into the survival claim.

## 7. Non-claims

This evidence does **not**: prove ΨTRS classifier superiority; prove a working vision system; prove video
understanding; authorize runtime integration; authorize camera / sensor / live capture; authorize prompt /
context / memory / action / render-body / autonomy contact. Brainvision remains offline research on
prerecorded `.npz` under `research/brainvision/` + `tests/research/`.

## 8. Recommended next direction

- **Codex adversarial review of the v0.3 claim boundary** — lock exactly what "repeatable offline
  recursive-time SAG survival across a heterogeneous + stress set" may and may not assert.
- **Then a controls / fragility pass using the existing route only** — characterize the spike-heavy clips
  (clip4, clip5_static, clip9_degraded), the non-amplifying windows, and whether the huge maxima are
  numerical or structural. Report medians and amplifying-window fractions.
- **No new math yet.** The signal is repeatable and now stress-tested, but adding operators would outrun
  the evidence.

*End — TORMENT Brainvision ΨTRS Real-Video Findings v0.3. Docs-only, non-authorizing. no `§0` pointer added; no tags.*
