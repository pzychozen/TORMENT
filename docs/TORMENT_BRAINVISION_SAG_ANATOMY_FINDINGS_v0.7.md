# TORMENT Brainvision SAG Anatomy Findings v0.7

## 1. Status / quarantine

**DOCS-ONLY research findings note. Non-authorizing, non-implementing. Opens no implementation lane and no
service integration.** Records what the **current** SAG diagnostic appears sensitive to, using synthetic
controlled descriptor fields, to inform the v0.6 diagnostic-redesign target. Work stays quarantined under
`research/brainvision/` + `tests/research/`; no `torment_service/` imports; no service / runtime / camera /
sensor / live-capture / prompt / context / memory / action / render-body / autonomy contact. **No `§0`
pointer; no tags.** No new math; no theory inflation.

## 2. What was measured

An offline anatomy harness (`research/brainvision/run_sag_anatomy.py`,
`tests/research/test_brainvision_sag_anatomy_v0_7.py`; 57 tests pass, existing SAG evaluator reused
unchanged) generates controlled synthetic descriptor windows and runs the **existing** multi-window SAG
evaluator on them, reporting a per-field energy statistic, `G(k=0)`/`G(k>0)` medians, and amplifying-window
counts. The goal is to let SAG show what its amplification tracks — using *"appears sensitive to" /
"consistent with sensitivity to"* language, never proof.

## 3. Results (synthetic controlled fields)

| Field             | energy | G(k=0) med | G(k>0) med | amplifying |
|-------------------|:------:|:----------:|:----------:|:----------:|
| constant          | 0.000  | 1.000      | 1.000      | 0/8        |
| tiny_noise        | 0.000  | **8.433**  | 1497.163   | 0/8        |
| white_noise       | 0.948  | 1.000      | 73.669     | 8/8        |
| smooth_ramp       | 0.344  | 1.000      | 17.571     | 8/8        |
| sine              | 0.500  | 1.000      | 1.913      | 8/8        |
| sine_phase_shift  | 0.500  | 1.000      | 6.593      | 7/8        |
| spike             | 1.214  | 1.000      | 36.576     | 8/8        |
| lowpass           | 0.175  | 1.000      | 21.866     | 8/8        |
| white_noise x0.1  | 0.009  | 1.000      | 1520.173   | 8/8        |
| white_noise x1    | 0.948  | 1.000      | 73.669     | 8/8        |
| white_noise x10   | 94.792 | 1.000      | 5.731      | 8/8        |
| sine_shuffled     | 0.500  | 1.000      | 103.641    | 8/8        |
| sine_reversed     | 0.500  | 1.000      | 3.456      | 7/8        |
| sine_circular     | 0.500  | 1.000      | 4.738      | 8/8        |

## 4. Interpretation (appears sensitive to; not proof)

- **Flat/constant fields do not amplify** (`constant`: G(k>0) 1.000, 0/8) — consistent with amplification
  requiring some field structure.
- **Most non-flat synthetic fields amplified in this harness** (white_noise, smooth_ramp, sine, spike, lowpass all 7–8/8).
- **Periodic fields and their shuffled / reversed / circular variants still amplify** (sine and
  sine_shuffled/reversed/circular all 7–8/8), so **temporal order is not required** — corroborating the
  v0.4/v0.5 controls at the synthetic-field level.
- **White-noise amplitude scaling shows SAG is not amplitude-scale invariant**: G(k>0) median goes
  1520 → 74 → 5.7 for ×0.1 → ×1 → ×10; the gain is consistent with sensitivity to field-to-perturbation scale as well as field structure.
- **The tiny-noise field breaks κ=0 coherence** (G(k=0) median 8.433 instead of 1.000), showing
  **low-energy numerical instability** of the current diagnostic.
- **Mechanism is not proven.** These are characterizations of the current diagnostic's behavior, consistent
  with sensitivity to field richness/variance/scale — not established causes.

## 5. Conclusion

Current SAG results are best treated as **repeatable descriptor-field amplification under the current
diagnostic, with apparent sensitivity to field richness / variance / scale — not temporal-order-specific
recursive-time evidence.** This is fully consistent with the v0.4/v0.5 controls downgrade and the v0.6
target freeze.

## 6. Future diagnostic / tuning target

Any future diagnostic (or tuning of this one) intended to support a temporal-order claim must, predeclared:

- **beat shuffle / reverse / circular controls by robust statistics** (medians and amplifying-window
  counts, not outlier maxima);
- be **scale-robust, or explicitly normalized** so gain does not depend on field-to-perturbation scale;
- **stay stable at low energy** (κ=0 must not blow up on tiny-amplitude fields);
- **not depend on spike-heavy means** (a few extreme windows must not carry the result);
- **keep κ=0 coherent** at/near 1.000 as an invariant.

## 7. Non-claims

This does **not**: prove a mechanism; prove classifier superiority; prove working vision or video
understanding; prove temporal-order sensitivity; authorize runtime integration; authorize service / camera
/ sensor / live capture; authorize prompt / context / memory / action / render-body / autonomy contact.
**No `§0` pointer; no tags.** Brainvision remains offline research under `research/brainvision/` +
`tests/research/`, HELD per v0.6 pending a predeclared diagnostic redesign.

*End — TORMENT Brainvision SAG Anatomy Findings v0.7. Docs-only, non-authorizing. Opens no implementation
lane; no `§0` pointer added; no tags.*
