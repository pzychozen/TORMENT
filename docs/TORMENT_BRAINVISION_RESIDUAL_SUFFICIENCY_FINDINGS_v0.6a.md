# TORMENT Brainvision Residual Sufficiency Findings v0.6a

## 1. Status / non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY, NON-LEARNING, EXPLANATORY form-A audit.** It records what the
v0.6a residual-sufficiency audit found. It is **explanatory, not corrective**: it explains *why* the v0.4d
per-pair residual match coexisted with feature-level baseline separability and does **not** try to make
Brainvision pass. It **redefines no `TOL`**, invents no threshold, proposes no pass/fail rule change, changes no
formula / §7 anti-proxy logic / §8 verdict logic / control, reruns / replaces no v0.4d sealed candidate, adds no
generator family, reopens no spectral group, trains no weights, and opens no classifier (form B) and no neural
encoder (form C).

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. It touches no `torment_service/`, runtime, camera / sensor / live-capture /
screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy paths, and makes
**no real-clip / local-clip move** and **no memory-system integration**. It does **not** say v0.4d was invalid,
does **not** say Brainvision failed or succeeded, and does **not** say descriptors are valid. The frozen
Brainvision §8 verdict is **HOLD** and untouched.

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
verdict                                      = HOLD
```

**No `§0` pointer; no tags.**

## 2. Inputs and delivered files

```text
v0.4d (77ed133)  Partial: 3/3 held-out matched within TOL (per-pair L-inf), baselines still separate.
v0.5a (37a75f7)  baseline anatomy -> distributed_residual_geometry; protocol_metric_mismatch_flag = True.
v0.5b (b5d6676)  synthesis: wall is a closure-metric sufficiency gap; recommended Branch A.
v0.6  (9c73799)  residual sufficiency audit PLAN.

Delivered UNCOMMITTED over HEAD 9c73799 (form A, non-learning, explanatory-only; reuses v0.4d/v0.5a records +
frozen v0.3 by identity):
  research/brainvision/run_residual_sufficiency_v0_6a.py
  tests/research/test_brainvision_residual_sufficiency_v0_6a.py
```

## 3. What was implemented

A single reporting-only audit that reuses (via `run_baseline_anatomy_v0_5a._matched_pairs`) the exact v0.4d
sealed matched held-out pairs — reproducing the committed residuals — and relates, per feature, the per-pair
residual closeness to class-level separability. For each of the four matched groups' features it reports the
frozen best-threshold BA, the signed median difference by label (and as a fraction of `TOL`), the per-pair
deltas, whether the winder-set is rank-separated from the candidate-set, and a **parameter-free robustness
lens**: the between-class rank-separation gap versus the within-class spread (ratio to the natural boundary 1.0).
`TOL`, `PSC_FLOOR`, `AIC_FLOOR`, `CHANCE_BAND` are untouched; no new threshold is adopted; spectral is not
reopened; non-finite / extreme values are defensively excluded, and an effectively-zero within-class spread is
bounded (never reported as a near-infinite ratio).

## 4. Result — mixed_metric_and_small_n (honest, NOT tuned)

```text
audit question: can group-level residual/TOL closure coexist with feature-level separability?  ANSWER: YES.
per-pair residuals all <= TOL (0.045 / 0.036 / 0.060)   protocol_ok = True   outcome = mixed_metric_and_small_n

group / feature            BA     signed_median_diff (% of TOL)   rank-sep   robustness (gap / within-spread)
movement_channel_energy
  rg_std                   0.833  -0.0257 (40%)                   no         not_rank_separated
  by_std                   1.000  +0.0196 (31%)                   yes        fragile      (0.06)
  chroma_mag               0.833  -0.0360 (57%)                   no         not_rank_separated
  delta_rms                0.833  -0.0000 ( 0%)                   no         not_rank_separated
directional
  u_directional_delta_rms  1.000  -0.0036 ( 6%)                   yes        robust_constant_within_class
  angular_increment_mag    1.000  -0.0037 ( 6%)                   yes        robust_constant_within_class
per_channel
  rg_centroid              1.000  -0.0001 ( 0%)                   yes        fragile      (0.004)
  by_centroid              1.000  -0.0339 (54%)                   yes        robust       (6.60)
  rg_spread                1.000  -0.0028 ( 4%)                   yes        fragile      (0.12)
  by_spread                1.000  -0.0294 (46%)                   yes        robust       (7.31)
frame_diff
  delta_rms                0.833  -0.0000 ( 0%)                   no         not_rank_separated

metric_insufficiency_features = [u_directional_delta_rms, angular_increment_mag, by_centroid, by_spread]
small_n_optimism_features     = [by_std, rg_centroid, rg_spread]
```

**Reading (research-only).** The core audit question is answered **yes**: group-level residual / `TOL` closure
**does** coexist with feature-level class separability. Both mechanisms are present, so the outcome is
**`mixed_metric_and_small_n`**:

1. **Metric insufficiency** — `by_centroid` and `by_spread` are robustly rank-separated (between-class gap 6.6x
   and 7.3x the within-class spread) with signed median differences ~50% of `TOL`. These are genuine class-level
   differences that a per-pair L-inf `<= TOL` match did not close (0.034 / 0.029 both sit under the 0.0634
   tolerance, so a pair can be "matched" while the class ordering separates robustly). The directional pair is
   also robustly separated but at negligible magnitude (~6% of `TOL`; constant within class).
2. **Small-N optimism** — `by_std`, `rg_centroid`, `rg_spread` are only fragilely rank-separated (gap far below
   the within-class spread; 0.06x, 0.004x, 0.12x) yet still reach BA = 1.00, the signature of thin-margin
   ordering at n = 3 vs 3.

So the substantive metric-insufficiency evidence is the **BY-channel** statistics (`by_centroid`, `by_spread`),
consistent with v0.5a's effect-size concentration; the BA saturation elsewhere is largely small-N.

## 5. Answers to the required audit outputs

```text
1. per-target residual vs per-feature BA: all three per-pair residuals <= TOL (0.045/0.036/0.060) while
   class-level BA reaches 1.00 on seven features -> closeness coexists with separability.
2. per-target residual vs signed median differences: matched within TOL, yet class-level signed median gaps
   reach 46-57% of TOL on chroma_mag / by_centroid / by_spread.
3. BA-saturated (rank-separated) features, ordered by |signed median diff| as a fraction of TOL (ascending; NO
   cutoff applied): rg_centroid 0.00, rg_spread 0.04, u_directional_delta_rms 0.06, angular_increment_mag 0.06,
   by_std 0.31, by_spread 0.46, by_centroid 0.54. The smallest fractions (rg_centroid / rg_spread / directional)
   are the small-N signature (near-zero class gap yet BA at its ceiling); the largest (by_spread / by_centroid)
   are the substantive class-level differences the per-pair match did not close. (BA saturates at its ceiling
   iff the feature is rank-separated -- a structural fact -- so no "tiny" threshold is used.)
4. class-separable ordering despite residual closeness: yes -- by_centroid / by_spread stay robustly rank-separated
   despite per-pair deltas <= TOL.
5. metric insufficiency vs small-N: BOTH present (robustness lens: robust BY statistics = metric insufficiency;
   fragile rg / by_std = small-N optimism).
6. supported outcome: mixed_metric_and_small_n.
```

## 6. Robustness lens (parameter-free) and defensive handling

The metric-insufficiency vs small-N distinction uses the between-class rank gap versus the within-class spread,
compared to the **natural boundary 1.0** ("gap equals within-class variation"). This is a **descriptive**
robustness reference derived from the data's own scale — it is **not** an adopted pass/fail threshold and is
applied to **no** closure decision, so no new threshold is introduced and `TOL` is unchanged. Non-finite /
extreme values are excluded via the frozen `_is_clean`; an effectively-zero within-class spread is bounded to
`robust_constant_within_class` rather than reported as a near-infinite ratio; any non-finite value in a required
metric forces `audit_inconclusive` and carries no evidential weight.

## 7. Outcome taxonomy (all leave claim locks unchanged)

```text
residual_metric_insufficient   robust class separation survives per-pair L-inf <= TOL only
small_n_baseline_optimism      rank separations are fragile thin-margin only
mixed_metric_and_small_n       both present  (THIS RUN)
audit_inconclusive             records insufficient / non-finite -> no claim movement
```

## 8. Tests run

```text
python -m pytest tests/research/test_brainvision_residual_sufficiency_v0_6a.py -q   -> 13 passed
python research/brainvision/run_residual_sufficiency_v0_6a.py                        -> ran clean (result above)
python -m pytest tests/research -q                                                   -> 274 passed, 1 failed (sandbox)
```

The single full-suite failure is the pre-existing, documented `spectral_centroid` Linux/Windows knife-edge in
`test_brainvision_color_structure_pooled_gate_audit_v1_8.py` (green on Windows; unrelated to v0.6a). The v0.6a
tests assert only platform-independent robust facts: reuse of the v0.4d/v0.5a records by identity; `TOL`
unchanged and no new threshold; spectral not reopened; the v0.4d pairs preserved; no generator/family/grid/seed
change; the parameter-free robustness lens classifies gap-vs-spread and bounds extreme ratios; non-finite values
cannot become evidence; the outcome is one of the four planned labels; and claim locks stay False with verdict
HOLD. Windows pytest is the source of truth.

## 9. Claim locks and verdict

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
frozen_brainvision_verdict                  = HOLD   (untouched)
vision_claim = False   memory_readiness_claim = False   runtime_readiness_claim = False
integration_readiness_claim = False
```

Describing that the closure metric coexisted with feature-level separability is an in-vitro synthetic,
metric-level observation within one sealed enumeration; it moves no lock and no verdict, and is not descriptor
validity or vision evidence.

## 10. Recommended next (not opened here)

- **Codex review** this findings receipt + the harness / tests.
- **If accepted,** the operator runs the Windows suite and commits. Because the outcome is
  `mixed_metric_and_small_n`, both follow-ups from the v0.6 plan remain **separate, future, docs-first** steps
  (not opened here): a Branch B **multi-feature closure metric proposal** aimed at the robust BY-channel
  separations (`by_centroid` / `by_spread`) that the per-pair L-inf missed — comparing per-feature separability,
  signed median differences, and group residuals **without casually inventing pass thresholds** — and a reviewed
  v0.4c amendment for a **larger held-out set** to test whether the small-N (fragile) separations collapse. Or
  **HOLD**. No code, classifier (B), neural (C), real clips, runtime, memory, `§0`, or tags are recommended here.

## 11. Codex review prompt

```text
Please review the v0.6a residual sufficiency audit:
  research/brainvision/run_residual_sufficiency_v0_6a.py
  tests/research/test_brainvision_residual_sufficiency_v0_6a.py
  docs/TORMENT_BRAINVISION_RESIDUAL_SUFFICIENCY_FINDINGS_v0.6a.md
(new, UNCOMMITTED, over committed edge 9c73799; implements the v0.6 Branch-A plan).

Verify that this slice:
- is offline research only (research/brainvision + tests/research + one findings doc); no torment_service, no
  runtime / memory / camera / sensor / streaming, no real clips; NO classifier (form B) / neural encoder (form C);
- is EXPLANATORY not corrective: it explains whether group-level residual/TOL closure can coexist with
  feature-level separability and does NOT try to close the baselines, make Brainvision pass, or tune anything;
- REDEFINES NO TOL, invents no threshold, adopts no new pass/fail rule: the robustness lens (rank gap vs
  within-class spread, boundary 1.0) is a descriptive reference applied to no closure decision;
- reuses the v0.4d / v0.5a records BY IDENTITY (reproduces the sealed matched pairs + residuals 0.045/0.036/0.060),
  reruns nothing with new params, replaces no pair, adds no generator family, changes no family/grid/seed/envelope,
  and keeps spectral audit-note-only (NOT reopened);
- reports the required outputs (per-target residual vs per-feature BA and signed median diff; a THRESHOLD-FREE
  ordering of BA-saturated / rank-separated features by smd-as-fraction-of-TOL, with NO tiny-smd or BA cutoff;
  class-separable ordering despite residual closeness; a metric-insufficiency vs small-N split) and the outcome
  mixed_metric_and_small_n with the substantive metric insufficiency localized to BY-channel statistics;
- defensively excludes NaN / non-finite / extreme values (bounds effectively-zero within-class spread; forces
  audit_inconclusive on a non-finite required metric) so non-finite values can never become evidence;
- does NOT say v0.4d was invalid, does NOT say Brainvision failed or succeeded, does NOT say descriptors valid or
  vision, and does NOT move claim locks or authorize runtime/memory/integration;
- preserves all claim locks (first_pass_structure_validity_claim_allowed = False; temporal_claim_allowed = False;
  descriptor_validity_claim_allowed = False) and verdict = HOLD; no §0; no tags.

Flag any TOL redefinition, any invented / adopted threshold, any rerun/replacement of v0.4d, any new family, any
non-finite value that could become evidence, any claim-lock/verdict movement, any statement that v0.4d was invalid
or Brainvision failed/succeeded, or any overclaim of the audit.
Return ACCEPT AS-IS or MODIFY with exact required changes.
```

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Residual Sufficiency Findings v0.6a. Reporting-only, non-learning, explanatory;
offline research. Changes no frozen formula, gate, evaluator, or verdict; deletes or weakens no control;
redesigns no descriptor; invents no threshold; redefines no TOL; reruns / replaces no v0.4d candidate; reopens
no spectral group; opens no classifier / neural / runtime / memory / real-clip work; makes no vision /
descriptor-validity / temporal-order / memory / runtime / integration claim; no `§0` pointer; no tags.*
