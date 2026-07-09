# TORMENT Brainvision Baseline Anatomy Findings v0.5a

## 1. Status / non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY, NON-LEARNING, EXPLANATORY form-A diagnostic.** It records
what the v0.5a baseline-anatomy diagnostic found when it decomposed the surviving v0.4d cheap-baseline
separability into per-feature anatomy. It is **explanatory, not corrective**: it explains *why* v0.4d remained
Partial and does **not** try to make Brainvision pass or close the baselines. It **changes no formula / §7
anti-proxy logic / §8 verdict logic / threshold / control**, redefines no `TOL`, reruns / replaces no v0.4d
sealed candidate, adds no generator family, trains no weights, opens no classifier (form B) and no neural
encoder (form C).

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. The frozen Brainvision §8 verdict is
**HOLD** and untouched.

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Inputs and delivered files

```text
v0.4d (77ed133)  matched search -> Partial (3/3 held-out matched within TOL; baselines still separate).
v0.4e (3814d44)  synthesis: obstruction moved to "residual match does not close baseline separability".
v0.5  (1255be7)  baseline anatomy PLAN (Branch A).

Delivered UNCOMMITTED over HEAD 1255be7 (form A, non-learning, explanatory-only; reuses frozen surfaces + the
v0.4d matched pairs by identity):
  research/brainvision/run_baseline_anatomy_v0_5a.py
  tests/research/test_brainvision_baseline_anatomy_v0_5a.py
```

## 3. What was implemented

A single reporting-only diagnostic that reuses the **exact** v0.4d sealed held-out search (same seeds / targets
/ grid; deterministic) and verifies it reproduces the committed v0.4d matched pairs, then decomposes the four
matched groups into per-feature anatomy on those 3 winders vs 3 matched `segment_paired_canceller` candidates.
For each feature it reports the frozen best-threshold balanced accuracy, the signed median difference by label,
whether it separates (BA `>` the reused reporting reference `CHANCE_BAND = 0.60`), and the group concentration.
`structure_score` / `_stats` / `GROUPS` / `_best_threshold` and the v0.4d search surfaces are reused by
identity; no threshold is invented and `TOL` is not redefined. Spectral is not inspected as a closure group.
Non-finite / extreme feature values are defensively excluded and can never become evidence.

## 4. Result — distributed_residual_geometry (honest, NOT tuned)

```text
matched targets = 3/3   per-pair residual all <= TOL (0.045 / 0.036 / 0.060)   protocol_ok = True
outcome = distributed_residual_geometry     protocol_metric_mismatch_flag = True

group                     group_max_BA  concentration   per-feature (BA ; signed median diff winder-candidate)
movement_channel_energy   1.000         distributed     by_std 1.000 (+0.0196) ; rg_std 0.833 (-0.0257) ;
                                                         chroma_mag 0.833 (-0.0360) ; delta_rms 0.833 (-0.0000)
directional               1.000         distributed     u_directional_delta_rms 1.000 (-0.0036) ;
                                                         angular_increment_mag 1.000 (-0.0037)
per_channel               1.000         distributed     rg_centroid 1.000 (-0.0001) ; by_centroid 1.000 (-0.0339) ;
                                                         rg_spread 1.000 (-0.0028) ; by_spread 1.000 (-0.0294)
frame_diff                0.833         single-feature  delta_rms 0.833 (-0.0000)

top features by EFFECT SIZE : chroma_mag, by_centroid, by_spread, rg_std, by_std   (BY + amplitude/chroma)
top features by BA          : by_std, u_directional_delta_rms, angular_increment_mag, rg_centroid, by_centroid
```

**Reading (research-only).** The surviving separability is **distributed**: in all three multi-feature groups
more than one feature separates the classes. But two structural facts qualify it:

1. **The BA saturation is largely small-N optimism.** Seven of eleven features reach best-threshold BA = 1.00
   while their signed median differences are tiny (down to 0.0001). At n = 3 vs 3, a feature needs only the
   three winder values to fall on one side of the three candidate values (by any margin) to score 1.00. High BA
   with near-zero median gap is the signature of that optimism, not of a large class-level gap.
2. **The genuine (effect-size) residual is concentrated in BY / amplitude statistics.** Ranking features by
   |signed median difference| puts `chroma_mag`, `by_centroid`, `by_spread`, `rg_std`, `by_std` on top — the
   BY-channel and amplitude/channel-energy statistics. `by_std` alone perfectly carries
   `movement_channel_energy` (winders higher `by_std`, lower `rg_std` = channel-energy imbalance).

## 5. Answers to the specific v0.5 questions

```text
- movement_channel_energy separates by AMPLITUDE + CHANNEL-ENERGY IMBALANCE (by_std up, rg_std / chroma_mag
  down in winders); by_std is the perfect single carrier. Not "coverage".
- directional separation still comes from BOTH angular-increment statistics (u_directional_delta_rms and
  angular_increment_mag), but at negligible effect size (~0.0036) -> essentially small-N best-threshold optimism.
- per_channel separability saturates on all four features, yet the EFFECT SIZE remains concentrated in BY
  statistics (by_centroid -0.034, by_spread -0.029 >> rg_centroid -0.0001, rg_spread -0.0028).
- frame_diff separation is delta_rms only, with a ZERO median difference (constant-chroma family -> delta_rms
  ~ 0 in both classes); its BA 0.833 is a small-N best-threshold artifact, not a magnitude / asymmetry / edge signal.
- YES: the v0.4d group-level per-pair L-inf/TOL summary HID multi-feature class-level separability -- per-pair
  match held within TOL for all three pairs, yet class-level best-threshold BA separates across many features.
```

## 6. Outcome taxonomy (all leave claim locks unchanged)

```text
concentrated_residual_feature   a small set of features carries most separability
distributed_residual_geometry   many features separate; group-level residual closure was insufficient  (THIS RUN)
protocol_metric_mismatch        per-pair residual/TOL does not capture the class-level separability      (FLAG = True)
invalid_diagnostic_breach       tuning / rerun / replacement / non-finite backing a result -> rejected
```

This run is `distributed_residual_geometry` with the `protocol_metric_mismatch` flag also True: separability is
spread across features, and the per-pair L-inf/TOL match did not capture the class-level best-threshold
separability. Neither reading moves any claim.

## 7. Defensive non-finite handling

`_is_clean` (reused from v0.4d) rejects NaN, +/-inf, and `|x| > 1e6`. A feature with any non-clean value is
excluded from its BA / median and flagged `invalid_nonfinite`; a non-finite value can never separate, never
carry a group, and never back a result — if one appears in a matched pair the whole run is
`invalid_diagnostic_breach`. Non-finite values are never treated as infinity or as stronger evidence.

## 8. Tests run

```text
python -m pytest tests/research/test_brainvision_baseline_anatomy_v0_5a.py -q   -> 12 passed
python research/brainvision/run_baseline_anatomy_v0_5a.py                        -> ran clean (outcome above)
python -m pytest tests/research -q                                               -> 261 passed, 1 failed (sandbox)
```

The single full-suite failure is the pre-existing, documented `spectral_centroid` Linux/Windows knife-edge in
`test_brainvision_color_structure_pooled_gate_audit_v1_8.py` (green on Windows; unrelated to v0.5a). The v0.5a
tests assert only platform-independent robust facts: only the four matched groups are inspected (spectral
excluded); the v0.4d sealed pairs are reused and reproduced exactly (no rerun with new params, no replaced
pair, no family/grid/seed/TOL change); per-feature BA and signed median differences are computed; non-finite
values cannot become evidence; claim locks stay False and verdict HOLD. Windows pytest is the source of truth.

## 9. Claim locks and verdict

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
frozen_brainvision_verdict                  = HOLD   (untouched)
vision_claim = False   memory_readiness_claim = False   runtime_readiness_claim = False
integration_readiness_claim = False
```

Naming which features still separate is an in-vitro synthetic description within one sealed enumeration; it
moves no lock and no verdict, and is not descriptor validity or vision evidence.

## 10. Recommended next (not opened here)

- **Codex review** this findings receipt + the harness / tests.
- **If accepted,** the operator runs the Windows suite and commits. The anatomy points two ways, which are a
  **separate, future** docs-first decision (not opened here): the surviving separability is diffuse and largely
  small-N best-threshold optimism (Branch B — tolerance / residual sufficiency, and/or a larger held-out set
  via a reviewed v0.4c amendment), while the genuine effect-size residual is concentrated in BY / amplitude
  statistics (a possible Branch C family-expansion target, only if separately gated). Or **HOLD**. No code,
  classifier (B), neural (C), real clips, runtime, memory, `§0`, or tags are recommended here.

## 11. Codex review prompt

```text
Please review the v0.5a baseline anatomy diagnostic:
  research/brainvision/run_baseline_anatomy_v0_5a.py
  tests/research/test_brainvision_baseline_anatomy_v0_5a.py
  docs/TORMENT_BRAINVISION_BASELINE_ANATOMY_FINDINGS_v0.5a.md
(new, UNCOMMITTED, over committed edge 1255be7; implements the v0.5 Branch-A plan).

Verify that this slice:
- is offline research only (research/brainvision + tests/research + one findings doc); no torment_service, no
  runtime / memory / camera / sensor / streaming, no real clips; NO classifier (form B) / neural encoder (form C);
- is EXPLANATORY not corrective: it explains why v0.4d stayed Partial and does NOT try to close the baselines,
  make Brainvision pass, or tune anything (reporting-only; optimizes no decision/PSC-AIC-BA/classifier/
  S_best_threshold/label/held-out/shortcut objective);
- inspects ONLY the four matched groups (movement_channel_energy, directional, per_channel, frame_diff) with the
  frozen v0.3 GROUPS membership reused by identity, keeps spectral audit-note-only (NOT a closure group), and
  notes frame_diff = delta_rms (single feature shared with movement_channel_energy);
- REUSES / PRESERVES the exact v0.4d sealed matched held-out pairs (reproduces best_cand_id + residual 0.045 /
  0.036 / 0.060), reruns nothing with new params, replaces no pair, adds no generator family, changes no
  family/grid/seed/envelope, invents no threshold, and does NOT redefine TOL (CHANCE_BAND 0.60 reused only as a
  descriptive reference);
- computes per-feature best-threshold BA + signed median difference by label, ranks by BA and by effect size,
  and reports concentration vs distribution and whether the per-pair L-inf/TOL summary hid multi-feature
  class-level separability;
- reports distributed_residual_geometry with the protocol_metric_mismatch flag, and surfaces the small-N
  best-threshold-optimism caveat honestly (BA ~1.0 with tiny median gaps) and the BY/amplitude effect-size
  concentration -- WITHOUT overclaiming;
- defensively excludes NaN / non-finite / extreme values from all outputs and forces invalid_diagnostic_breach
  if one backs a result;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; makes no vision / "Brainvision sees" /
  temporal-order / descriptor-validity / memory / runtime / integration claim; no §0; no tags.

Flag any threshold invention, any TOL redefinition, any rerun/replacement of v0.4d, any new family, any
tuning-toward-closure, any non-finite value that could become evidence, any claim-lock/verdict movement, or any
overclaim of the anatomy (e.g. treating feature separability as descriptor validity or vision evidence).
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Baseline Anatomy Findings v0.5a. Reporting-only, non-learning, explanatory; offline
research. Changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no control; redesigns no
descriptor; invents no threshold; redefines no TOL; reruns / replaces no v0.4d candidate; opens no classifier /
neural / runtime / memory / real-clip work; makes no vision / descriptor-validity / temporal-order / memory /
runtime / integration claim; no `§0` pointer; no tags.*
