# TORMENT Brainvision Offline Prototype Model Findings v0.2

## 1. Status / quarantine and non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY, NON-LEARNING offline probe.** It records the v0.2 form-A
scoring-probe result over synthetic fixtures. It **changes no formula / §7 anti-proxy logic / §8 verdict logic /
threshold / control**, deletes or weakens nothing, redesigns no descriptor, and trains no weights. Everything
stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, and **no** runtime-readiness claim. The frozen
Brainvision §8 verdict is **HOLD** and untouched. `first_pass_structure_validity_claim_allowed` remains
**False**, `temporal_claim_allowed` remains **False**, `descriptor_validity_claim_allowed` remains **False**. It
touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture / streaming, or prompt /
context / memory / action / render-body / autonomy paths, and makes **no real-clip / local-clip move** and
**no memory-system integration**. Brainvision Path B is **not proven vision** and is **not a functioning vision
layer for TORMENT memory**. **No `§0` pointer; no tags.**

## 2. Accepted inputs (v0.1 plan + Path B)

```text
v0.1 plan committed:  0611aff  docs(research): plan brainvision offline prototype model
Path B closed:        57a57ab
  directional_B_strengthened but unresolved   (directional_proxy_failure_resolved = False)
  per_channel_C_strengthened but unresolved    (per_channel_proxy_failure_resolved = False)
  A_descriptor_limitation_supported = False
  verdict = HOLD
  first_pass_structure_validity_claim_allowed = False
  temporal_claim_allowed = False
  descriptor_validity_claim_allowed = False
```

Path B is used only as evidence that the color-structure primitive is worth **testing** as one feature family —
not as proof of vision, descriptor validity, or integration readiness.

## 3. What was implemented

A single reporting-only, **NON-LEARNING** probe + its test lock, delivered **UNCOMMITTED** over HEAD `0611aff`:

```text
research/brainvision/run_offline_prototype_model_v0_2.py
tests/research/test_brainvision_offline_prototype_model_v0_2.py
```

Form **A only** (non-learning scoring). Forms B (tiny classical classifier) and C (tiny neural encoder) are
**not** opened. It reuses the frozen v0.7/v0.8 descriptors by identity (`structure_score` / `_stats` /
constants) and the v1.9 + v2.0 synthetic generators. Recurrence / temporal summaries (DET / RR / LAM) are
**excluded** to avoid temporal leakage.

## 4. Task families

Five synthetic binary tasks (label 1 = coherent-winding structure; 0 = cancellation), designed to progressively
close cheap shortcuts:

```text
F1_unmatched            winders vs mixed cancellers (easy; cheap features may separate)
F2_movement_matched     winders vs directionally-matched outbacks
F3_perchannel_matched   winders vs non-collinear centroid/spread-matched arcs
F4_smoothness           winders vs smooth low-jitter cancellers
F5_std_matched          full-amplitude winders vs channel-energy-matched cancellers (movement shortcut CLOSED)
```

## 5. Feature families used

```text
color-structure:        PSC, AIC, S
directional:            u_directional_delta_rms, angular_increment_mag
per-channel-spectral:   rg_centroid, by_centroid, rg_spread, by_spread
recurrence/temporal:    EXCLUDED (no DET/RR/LAM)
cheap-baseline groups:  movement_only (rg_std,by_std,chroma_mag), direction_only, spectral_only,
                        per_channel_only, frame_diff_proxy (delta_rms), random
```

## 6. Fixed scoring rule (non-learning)

```text
color-structure model:  predict "structure" iff PSC >= PSC_FLOOR (0.30) and AIC >= AIC_FLOOR (0.30)
```

The rule reuses the **frozen** PSC/AIC floors; **no weights and no thresholds are tuned from labels**. Cheap
baselines are given an **optimistic** best single-threshold (chosen with label knowledge) — generous to the
baselines so that a frozen-rule win is meaningful.

## 7. Balanced accuracy, confusion, baselines

Per-family balanced accuracy (color frozen rule) and best cheap baseline (within-family, optimistic):

```text
family                  color_BA   best_cheap (within, optimistic)
F1_unmatched            1.000      movement_only 0.875
F2_movement_matched     1.000      movement_only 1.000*
F3_perchannel_matched   1.000      movement_only 1.000*
F4_smoothness           1.000      movement_only 1.000*
F5_std_matched          1.000      direction_only 1.000* (spectral_only also 1.000)
* within-family optimistic best-threshold OVERFITS tiny N (perfect separation on ~1e-3 feature
  differences with 3-vs-3 samples) -- see §10; the reliable comparison is cross-family (§9).
```

Pooled (n = 31; 15 structure / 16 non-structure):

```text
color-structure model BA = 1.000   confusion = {tp:15, fn:0, fp:0, tn:16}
pooled cheap baselines (optimistic): movement_only 0.873, spectral_only 0.7708, per_channel_only 0.806,
                                     frame_diff_proxy 0.6875, direction_only 0.715, random ~0.5
```

## 8. Ablations (color-structure family)

```text
PSC_only  (>= floor)        BA = 1.000   (PSC carries the separation)
AIC_only  (>= floor)        BA = 0.500   (AIC alone FAILS -- cancellers have high AIC; PSC is the discriminator)
S_best_threshold            BA = 1.000
```

The `AIC_only = 0.500` ablation is important: the winding-coherence separation is carried by **PSC**, not by
angular concentration (AIC) alone.

## 9. Held-out / cross-family generalization (reliable comparison)

Baseline threshold chosen on the reference family (F1), applied **unchanged** to held-out families; the
non-learning color rule needs no reference:

```text
held-out family        color_BA   movement_only  direction_only  spectral_only  per_channel_only  frame_diff
F2_movement_matched    1.000      1.000          0.667           0.667          0.667             0.500
F3_perchannel_matched  1.000      1.000          0.500           0.667          0.500             0.833
F4_smoothness          1.000      1.000          0.500           0.667          0.500             0.833
F5_std_matched         1.000      0.500          0.833           1.000          0.667             0.500
```

Summary:

```text
color_single_fixed_rule_generalizes_across_all_families      = True
any_single_cheap_baseline_generalizes_across_all_held_out    = False
each_family_separable_by_some_cheap_baseline                 = True
shuffled_label_control_ba (avg of 500 shuffles)              = 0.4982  (~chance; sanity OK)
```

## 10. Failure cases and shortcut analysis

- **Channel-energy shortcut on generic families.** On F2/F3/F4 a cheap `movement_only` (channel-std / chroma-
  energy) threshold learned on F1 **generalizes perfectly** (BA 1.0) — a real cross-family shortcut. So on these
  families the color-structure rule has **no demonstrated advantage** over a cheap energy proxy.
- **F5 closes the energy shortcut but not the spectral one.** On the channel-energy-matched family F5,
  `movement_only` drops to **0.500** (shortcut closed), but `spectral_only` reaches **1.000** — i.e. F5 exposes
  a *different* cheap proxy. **No single synthetic family here closes all cheap shortcuts at once.**
- **Small-N overfitting of the optimistic within-family baseline.** With 3-vs-3 samples, the optimistic
  best-threshold can perfectly separate ~1e-3 numeric differences, inflating within-family baseline BA to 1.0.
  This is why §9 cross-family generalization — not §7 within-family — is treated as the reliable comparison.
- **AIC-only fails** (§8): the separation is a PSC effect, not angular concentration.
- **The task itself is the Path B winding-vs-cancellation signal.** The color rule's perfect separation is the
  *same* coherent-winding effect Path B already established; it is **not new evidence** of vision or validity.

## 11. Claim locks (unchanged)

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
frozen_brainvision_verdict                  = HOLD  (untouched)
vision_claim = False   memory_readiness_claim = False   runtime_readiness_claim = False
```

Forbidden inference jumps (none taken):

```text
"prototype works"            ->  "Brainvision sees"           : NOT taken
"synthetic scorer works"     ->  "memory integration"          : NOT taken
"beats baseline"             ->  "descriptor validity"         : NOT taken
"descriptor helps"           ->  "temporal order"              : NOT taken
"score separates fixtures"   ->  "runtime readiness"           : NOT taken
```

## 12. Research-only verdict

```text
research_signal:
  color_structure_single_fixed_rule_generalizes_across_all_families;
  no_single_cheap_baseline_does;
  but_each_family_also_separable_by_some_cheap_baseline;
  research_signal_only_no_vision_or_validity_claim
```

Read honestly: a **single, non-learning, interpretable** color-structure rule separates all five synthetic
tasks and generalizes across them without any per-family tuning, and **no single cheap baseline** matches that
cross-family. **But** every individual family is also separable by *some* cheap baseline, so v0.2 does **not**
isolate a color-structure contribution that no cheap proxy can achieve, and the separation is the same
winding-vs-cancellation signal Path B established. This is a **modest research signal only** — it moves no claim
lock and no verdict, and it is not evidence of vision, descriptor validity, temporal order, memory readiness, or
runtime readiness.

## 13. Tests run

```text
python -m pytest tests/research/test_brainvision_offline_prototype_model_v0_2.py -q     -> 10 passed
python -m pytest tests/research/ -q                                                     -> 224 passed (Windows)
```

Sandbox reconstruction: the full suite shows **223 passed + 1 failed**, the failure being the documented
`spectral_centroid` Linux/Windows knife-edge in `test_brainvision_color_structure_pooled_gate_audit_v1_8.py`
(pre-existing, unrelated to v0.2, passes on Windows). Windows pytest is the source of truth for boundary stats.

## 14. Recommended next (not opened here)

Possible next slices, each requiring separate opening + review:

- A synthetic family (or task) that closes **all** cheap shortcuts **simultaneously** (energy + spectral +
  per-channel + frame-diff) with larger N, to test whether any color-structure advantage survives when every
  cheap proxy is neutralized — the honest way to isolate a genuine contribution.
- Only if that holds, consider form **B** (tiny classical classifier) with strict held-out families.

Real clips / local-clip manifest and memory-system integration stay disallowed; no §7/§8/threshold/control/
descriptor change may be made without a fresh freeze and adversarial review.

- **Codex review** of this receipt and of the non-learning, baseline-gated, research-only framing.
- **If accepted,** the next slice may be the all-shortcuts-closed synthetic task (still form A) or a
  strictly-held-out form B; otherwise **HOLD**.

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Offline Prototype Model Findings v0.2. Reporting-only, non-learning; docs-only
receipt. Opens no implementation lane; changes no frozen formula, gate, or verdict; deletes or weakens no
control; redesigns no descriptor; makes no vision / descriptor-validity / temporal-order / memory / runtime
claim; no `§0` pointer added; no tags.*
