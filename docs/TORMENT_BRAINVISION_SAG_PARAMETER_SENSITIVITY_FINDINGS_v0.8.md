# TORMENT Brainvision SAG Parameter Sensitivity Findings v0.8

## 1. Status / quarantine

**DOCS-ONLY research findings note. Non-authorizing, non-implementing. Opens no implementation lane and no
service integration.** Records what an offline parameter sweep revealed about the **current** SAG
diagnostic, before any redesign or tuning. Work stays quarantined under `research/brainvision/` +
`tests/research/`; no `torment_service/` imports; no service / runtime / camera / sensor / live-capture /
prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.** No new
math; no proposed implementation; no theory inflation.

## 2. What was measured

An offline sweep (`research/brainvision/run_sag_parameter_sensitivity.py`,
`tests/research/test_brainvision_sag_param_sensitivity_v0_8.py`; 62 tests pass, existing `symmetry_gain`
reused via its eps/kappa parameters) ran the current SAG over a grid of synthetic fields × amplitude
scales × eps × kappa, reporting `G(k=0)`/`G(k>0)` medians, amplifying counts, and diagnostic flags. Wording
throughout is *"appears" / "consistent with" / "in this sweep"* — characterization, not mechanism proof.

## 3. Results

```
cells=840  fields=7  scales=4  eps=5  kappa=6
flags: k0_coherent_rate=0.536  unstable_low_energy=True  scale_sensitive=True  spike_sensitive=True  temporal_claim_allowed=False
kappa=0 coherence fraction by eps: 1e-06=0.54  1e-05=0.54  1e-04=0.54  1e-03=0.54  1e-02=0.54
eps keeping low-energy (scale 0.01) kappa=0 coherent: NONE
kappa profile white_noise(scale1, eps1e-3): k0=1.00  k0.5=6.37  k1=12.76  k2=26.08  k3=43.70  k4=127.02
corr(log10(eps/energy), log10 gain) @ kappa=3: 0.443
```

## 4. Interpretation (appears / consistent-with, not proof)

- **κ=0 coherence is not universal** — only ~0.54 of grid cells have a coherent κ=0 baseline.
- **κ=0 coherence appears amplitude-dependent in this sweep, not eps-driven:** the coherence fraction stays about 0.54
  across every eps, and **no eps rescues low-amplitude (scale 0.01) fields.**
- **Gain only partly tracks the eps-to-field-energy ratio:** the correlation of 0.443 is moderate, not
  strong — so eps/energy does **not** fully explain gain.
- **The diagnostic is scale-sensitive**, but **field type matters too** (not a pure scale artifact).
- **No smooth/bounded κ regime was observed in this sweep:** gain rose sharply across the tested κ range
  (white_noise: 1.00 → 6.37 → 12.76 → 26.08 → 43.70 → 127.02 for κ 0 → 4).
- **Spike-injected fields amplify more than smooth fields** (`spike_sensitive=True`).
- **`temporal_claim_allowed` remains False** — no temporal-order claim is made or supported here (no
  shuffle/reverse control pass is part of this sweep).
- These are **characterization findings, not mechanism proof.**

## 5. Conclusion

The current SAG diagnostic is **under-specified for temporal claims**, because its verdicts depend on
amplitude scale, low-energy baseline stability, spike sensitivity, and an unbounded-looking κ response across the tested range. Any future redesign proposal would need to predeclare and justify candidates for:

1. **amplitude normalization or eps-to-field scaling** (so gain does not move with raw amplitude);
2. **κ=0 coherence across the intended operating range** (including low energy);
3. a **bounded / regularized κ response** (so gain does not explode with κ);
4. and only then, **direct shuffle / reverse / circular controls where true beats controls by robust
   statistics** (medians and amplifying-window counts, not outlier maxima).

Until those hold, "amplification" is best read as strongly confounded by amplitude scale and κ response, not as temporal structure.

## 6. Non-claims

This does **not**: prove a mechanism; prove classifier superiority; prove working vision or video
understanding; prove temporal-order sensitivity; authorize runtime integration; authorize service / camera
/ sensor / live capture; authorize prompt / context / memory / action / render-body / autonomy contact.
**No `§0` pointer; no tags.** Brainvision remains offline research under `research/brainvision/` +
`tests/research/`, HELD per v0.6.

## 7. Recommended next

- **Codex adversarial review of this v0.8 wording** — confirm §4/§5 neither over- nor under-state what the
  sweep shows.
- **Then commit** the v0.8 harness, test, and this findings doc.
- **After that**, a v0.9 redesign-proposal note *may predeclare* candidate fixes and acceptance tests — but
  **no tuning/math implementation before that proposal is reviewed.**

*End — TORMENT Brainvision SAG Parameter Sensitivity Findings v0.8. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*
