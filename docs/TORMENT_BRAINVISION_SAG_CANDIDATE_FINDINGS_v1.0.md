# TORMENT Brainvision SAG Candidate Findings v1.0

## 1. Status / quarantine

**DOCS-ONLY research findings note. Non-authorizing, non-implementing. Opens no implementation lane and no
service integration.** Records what the first **offline candidate diagnostic** (the normalized-control-gated
SAG candidate v1.0) fixed and what it failed, judged against the v0.9 predeclared acceptance tests. Work
stays quarantined under `research/brainvision/` + `tests/research/`; no `torment_service/` imports; no
service / runtime / camera / sensor / live-capture / prompt / context / memory / action / render-body /
autonomy contact. **No `§0` pointer; no tags.** This does **not** prove Brainvision works, does **not** prove
classifier superiority, and does **not** prove temporal-order specificity. `temporal_claim_allowed` remains
**False**.

## 2. What was run

The candidate harness (`research/brainvision/run_sag_candidate_v1_0.py`,
`tests/research/test_brainvision_sag_candidate_v1_0.py`; full research suite 72 passed) wraps the existing
SAG with per-window robust (median/MAD) normalization, a predeclared near-flat floor, a relative
perturbation, and a first-class temporal-control gate. The gate is an AND of six predeclared checks (fixed
before seeing outcomes) — pooled true-beats-controls, per-field strict-majority true-beats-controls, κ=0
coherence threshold, scale invariance, spike-probe presence, and spike robustness — so
`temporal_claim_allowed` cannot become True from pooled medians alone. Wording throughout is *"appears" /
"in this candidate run"* — characterization, not mechanism proof.

## 3. Results (candidate run)

```
k0_coherent_rate=1.0  near_flat_neutral_count=24  scale_sensitive=False  spike_sensitive=False
scale medians (white_noise): x0.1=151.312  x1.0=151.312  x10.0=151.312
temporal medians: true=8.425  shuffled=147.66  reversed=6.388  circular=8.003
field_majority(true beats all controls)=0.0
temporal gates: g1_pooled_true_beats_controls=False  g2_field_majority_true_beats_controls=False
                g3_k0_coherent_rate=True  g4_scale_invariant=True
                g5_spike_probe_present=True  g6_spike_robust=True
temporal_claim_allowed=False  (failed gates: g1_pooled_true_beats_controls, g2_field_majority_true_beats_controls)
```

## 4. What v1.0 fixed (appears / consistent-with, not proof)

The candidate appears to repair several numeric confounds recorded in v0.7 (anatomy) and v0.8 (parameter
sensitivity):

- **κ=0 coherence reached 1.0** in this candidate run (v0.8 sweep had `k0_coherent_rate ≈ 0.536`).
- **Scale sensitivity was removed for the tested white-noise amplitude multipliers** — the gain median is
  151.312 at ×0.1, ×1.0, and ×10.0 (v0.7 showed 1520 → 74 → 5.7 across the same multipliers).
- **Near-flat / degenerate fields were neutralized** — 24 windows fell below the predeclared robust-scale
  floor and returned neutral / non-amplifying instead of producing fake giant gain (v0.7's tiny-noise κ=0
  blow-up).
- **The spike-sensitivity flag was False** — the robust (MAD) scale plus median score did not show the
  spike-injected advantage in this candidate run, and the probe was present (`g5_spike_probe_present=True`),
  so the flag is a real comparison, not a vacuous pass.

## 5. What v1.0 still fails

The candidate still fails the temporal-control gate:

- **The shuffled median is much higher than the true median** (147.66 vs 8.425) — time-shuffling *raised*
  amplification rather than lowering it.
- **True does not beat all controls by robust median** — it exceeds reversed (6.388) and circular (8.003)
  only marginally and loses badly to shuffled, so the pooled gate `g1` is False.
- **`field_majority(true beats all controls)=0.0`** — on no non-neutral field did true beat every control,
  so the per-field majority gate `g2` is False.

## 6. Conclusion

v1.0 is useful as a **hygiene / normalization improvement** — it repairs the amplitude-scale, low-energy,
κ=0-coherence, and spike confounds that made earlier SAG readings uninterpretable. It is **not** a
temporal-order diagnostic: after normalization, amplification remains more favorable to shuffled fields in
this candidate run; this is consistent with a field-richness/spectral-broadening confound, but does not
prove that mechanism. True windows do not beat shuffled / reversed / circular controls. `temporal_claim_allowed` correctly stays **False**; the candidate
does not force a PASS.

## 7. Non-claims

This does **not**: prove a mechanism; prove classifier superiority; prove working vision or video
understanding; prove temporal-order sensitivity; authorize runtime integration; authorize service / camera /
sensor / live capture; authorize prompt / context / memory / action / render-body / autonomy contact. **No
`§0` pointer; no tags.** Brainvision remains offline research under `research/brainvision/` +
`tests/research/`, HELD per v0.6.

## 8. Recommended next

- **Codex review of this v1.0 findings wording** — confirm §4/§5 neither over- nor under-state what the
  candidate run shows.
- **Then a v1.1 proposal note** *may predeclare* a diagnostic that targets the remaining failure
  specifically: **why shuffled windows score higher than true windows**, and what predeclared measure could
  reward ordered continuity / recurrence **without being fooled by shuffled spectral richness** — with
  controls first-class and thresholds fixed before real-clip inspection.
- **No implementation until the v1.1 proposal is reviewed.**

*End — TORMENT Brainvision SAG Candidate Findings v1.0. Docs-only, non-authorizing. Opens no implementation
lane; no `§0` pointer added; no tags.*
