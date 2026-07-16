# TORMENT Brainvision ΨTRS Real-Video Boundary-Neutral Dual Reporting Design v0.6

## 1. Status / quarantine

**DOCS-ONLY design note. Non-authorizing, non-implementing. Opens no implementation lane and no service
integration.** It defines the design boundary for a *future* dual-reporting mode for the ΨTRS matched
paired analysis and frames one preferred candidate for later adversarial review. It **implements nothing**:
no boundary-neutral companion is built here. It extends the v0.4/v0.5 controls line
(`TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_CONTROLS_FINDINGS_v0.4.md`,
`TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_CONTROLS_COMPLETENESS_v0.5.md`) and concerns the raw ΨTRS response
and `recursive_delta` emitted by `research/brainvision/run_prerecorded_paired_analysis_v0_1.py`. Work stays
quarantined under `research/brainvision/` + `tests/research/`; no `torment_service/` imports; no service /
runtime / camera / sensor / live-capture / prompt / context / memory / action / render-body / autonomy
contact. **No code, tests, `.npz` inputs, result artifacts, benchmark output, existing historical findings,
or service files are changed. No `§0` pointer added; no tags.** No new math; no parameters tuned.

## 2. Accepted design decision

The accepted direction is **PLAN RAW + BOUNDARY-NEUTRAL DUAL REPORTING**.

The current raw ΨTRS response is **fixed-start, block-local, stateful, path-sensitive, deterministic, and
historically preserved**. It is useful as a bounded engineering diagnostic but is sensitive to arbitrary
block beginnings. The structural audit established (across the 36 analyzed blocks = 9 clips x 4 blocks):

```text
reversal recursive_delta positive on 36/36 blocks
circular recursive_delta positive on 36/36 blocks

circular canonical-start alignment:
  original positive blocks       = 36/36
  canonical-aligned median delta = 0.0
```

The circular response is therefore **strongly influenced by start-state alignment**. **No implementation
defect was demonstrated** — this is a property of a fixed-start, stateful, block-local diagnostic, not a bug.

## 3. Purpose of the note

Define the design boundary for future reporting as **RAW ΨTRS RESPONSE + ONE BOUNDARY-NEUTRAL COMPANION
RESPONSE**. The companion would answer only:

> How much of the matched transform response remains after a predeclared boundary-neutralization operation?

It would **not** answer whether temporal order is detected, whether an arrow of time is detected, whether
perception exists, whether recursive time is validated, whether one descriptor is scientifically superior,
or whether the current clips support inference.

## 4. Preferred candidate to frame (for later adversarial review)

**DETERMINISTIC MULTI-START CIRCULAR ENSEMBLE.** Conceptually:

1. Begin with the same cached 64-row transformed array already used by raw ΨTRS.
2. Select a fixed, predeclared set of circular starting offsets.
3. Evaluate both `psi_trs` and `psi_trs_k0` on exactly the same rotated arrays.
4. Aggregate feature responses over those starts with one predeclared deterministic statistic.
5. Report the companion **beside, never instead of**, the raw fixed-start result.

The offset set, aggregation statistic, and computational budget are **not finalized** here (the existing
methodology does not dictate them); they are recorded as explicit design questions in §6.

## 5. Required invariants for any future companion

The future companion must preserve: **same cached source/control arrays; for each ensemble start, the
identical circular offset applied to the matched true and control arrays; those exact rotated arrays
supplied identically to `psi_trs` and `psi_trs_k0`; same control identity; same block identity; same
response formula; deterministic
operation; finite-output diagnostics; raw ΨTRS result preserved unchanged; no labels; no balanced accuracy;
no folds; no classifier; no parameter fitting against current clips; no selection based on favorable
outcomes.** It must be **clearly named and structurally separate from raw output**, and must never silently
replace **historical raw `psi_trs`**, **historical `recursive_delta`**, or **current prerecorded
paired-analysis outputs**.

## 6. Design questions (unresolved)

**Offset policy.** Possible: all 64 circular starts; fixed evenly spaced starts; fixed offsets derived only
from block length. Rejected: offsets chosen from observed response; offsets chosen to reduce
`recursive_delta`; content-selected starts without explicit tie semantics; clip-specific tuned offsets.

**Aggregation policy.** Possible: median feature vector across starts; mean feature vector across starts;
median normalized response across starts; a distributional summary without collapsing to one vector. These
**measure different objects** (a summary in feature space vs. a summary of scalar responses vs. a
distribution) and **must not be mixed casually**; the choice must be predeclared and reported. Every
aggregation policy must preserve start-wise true/control pairing: true and control arrays may not select
starts independently, be independently canonicalized, or be compared across different circular offsets.

**Computational standing (conceptual only; do not optimize or benchmark now).** Cost multiplier scales
roughly with the number of starts (up to ~64x the raw single-start evaluation for a full ensemble);
determinism is achievable given fixed offsets and stable seed derivation; memory needs stay bounded if
starts are streamed rather than materialized together; a **full 64-start evaluation may or may not be
practical** at scale; a **reduced fixed-start design would introduce approximation error** relative to the
full ensemble and must report that dependence.

**Boundary-neutrality standing.** Circular multi-start aggregation can reduce dependence on a *selected
starting row*, but it does **not** automatically remove finite-window boundary effects, trajectory
initialization effects, trailing-window rho effects, directional path dependence, or control-induced
discontinuities. It is therefore a **boundary-neutral companion only in a bounded engineering sense** — not
a mathematically invariant operator unless later proven.

## 7. Raw-versus-companion reporting contract

Any future report must display, separately and side by side: **raw fixed-start response; companion
aggregated response; raw `recursive_delta`; companion `recursive_delta`; raw-minus-companion difference;
per-start spread or dispersion; number of starts; offset policy; aggregation policy; tie or ambiguity count;
finite/nonfinite count.** A positive or negative raw-minus-companion difference means **only** that start
selection affected the measured transform sensitivity; it does **not** determine which result is better or
more valid.

## 8. Tests that would be required before any implementation (recorded, not added)

1. Raw historical values remain byte-for-byte or numerically unchanged.
2. For every start, the identical circular offset is applied to the matched
   true and control arrays, and both ΨTRS and k0 receive those exact rotated arrays.
3. Offset selection is deterministic and descriptor-order independent.
4. No process-randomized hashing is used.
5. Input and cached arrays are not mutated.
6. Companion results are invariant to a global circular rotation when the full-start ensemble is used.
7. Reduced-start designs report approximation dependence explicitly.
8. Tie and duplicate-start behavior is deterministic.
9. All outputs remain finite for finite valid inputs.
10. Response-normalization diagnostics remain present.
11. No classification or inferential fields appear.
12. Default execution writes nothing.
13. Raw and companion results are clearly separated.
14. All scientific and integration locks remain False.

(No tests are added by this note.)

## 9. Alternatives not currently selected

- **Single canonical start** — content-selected arbitrariness and unresolved tie handling (which start is
  "canonical" is ambiguous).
- **Warm-up discard** — changes the measured object and can erase legitimate statefulness.
- **Forward/reverse symmetric initialization** — changes the measured object and adds new design risk by
  imposing a symmetry absent from the raw diagnostic.
- **Learned initial state** — parameter fitting against current clips; a new leakage/design risk.
- **Cross-block carry-over state** — continuous-stream semantics differing from block-local analysis;
  breaks block identity.
- **Boundary-sensitive coordinate deletion** — can erase legitimate statefulness and changes the measured
  object.
- **Retiring `recursive_delta`** — loss of a useful, historically preserved diagnostic.

Principal reasons across these: content-selected arbitrariness; tie handling; a changed measured object;
possible erasure of legitimate statefulness; new leakage/design risks; continuous-stream semantics differing
from block-local analysis; and loss of useful historical diagnostics.

## 10. Status

```text
design direction               = RAW + BOUNDARY-NEUTRAL DUAL REPORTING
preferred candidate for review = DETERMINISTIC MULTI-START CIRCULAR ENSEMBLE
candidate finalized            = False
implementation authorized      = False
experiment authorized          = False

FORMAL HOLD active
Mode 0 active
verdict = HOLD

bounded_experiment_ready           = False
Brainvision_perceptual_claim_ready = False
runtime_integration_authorized     = False
new_scientific_claim_authorized    = False
```

## 11. Non-claims

This note does **not**: prove classifier superiority; prove working vision; prove video or visual
understanding; prove temporal-order sensitivity, an arrow of time, or validated recursive time; establish
that any descriptor is scientifically superior; establish that the current clips support inference;
authorize runtime integration; authorize service / camera / sensor / live capture; authorize prompt /
context / memory / action / render-body / autonomy contact. It authorizes no implementation and no
experiment. Brainvision remains offline research on prerecorded `.npz` under `research/brainvision/` +
`tests/research/`; historical raw ΨTRS, historical `recursive_delta`, and the current paired-analysis
outputs are preserved unchanged.

*End — TORMENT Brainvision ΨTRS Real-Video Boundary-Neutral Dual Reporting Design v0.6. Docs-only,
non-authorizing, non-implementing. Opens no implementation lane; no `§0` pointer added; no tags.*
