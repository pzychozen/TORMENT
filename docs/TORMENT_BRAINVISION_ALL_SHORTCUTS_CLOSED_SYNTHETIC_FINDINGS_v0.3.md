# TORMENT Brainvision All-Shortcuts-Closed Synthetic Findings v0.3

## 1. Status / quarantine and non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY, NON-LEARNING form-A falsifier.** It records the v0.3
all-shortcuts-closed synthetic result. It **changes no formula / §7 anti-proxy logic / §8 verdict logic /
threshold / control**, trains no weights, uses no label-fitted color threshold, opens no classifier (form B)
and no neural encoder (form C), and excludes recurrence / temporal features. Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, **no** temporal-order claim, **no**
descriptor-validity claim, **no** memory-readiness claim, **no** runtime-readiness claim, and **no**
integration-readiness claim. The frozen Brainvision §8 verdict is **HOLD** and untouched.
`first_pass_structure_validity_claim_allowed` remains **False**, `temporal_claim_allowed` remains **False**,
`descriptor_validity_claim_allowed` remains **False**. It touches no `torment_service/`, runtime, camera /
sensor / live-capture / screen-capture / streaming, or prompt / context / memory / action / render-body /
autonomy paths, and makes **no real-clip / local-clip move** and **no memory-system integration**. Brainvision
Path B is **not proven vision** and is **not a functioning vision layer for TORMENT memory**. **No `§0` pointer;
no tags.**

## 2. Inputs

```text
Path B closed:            57a57ab  docs(research): close brainvision color structure path b
v0.1 plan:                0611aff  docs(research): plan brainvision offline prototype model
v0.2 scoring prototype:   06b36ce  research(brainvision): add offline prototype scoring model
v0.2 synthesis:           07752c8  docs(research): synthesize brainvision offline prototype model
```

v0.2 result carried forward: the fixed color rule generalized across all five synthetic families; no single
cheap baseline generalized across all held-out families; **but every family was still separable by some cheap
baseline** — so v0.2 did not isolate a unique color-structure advantage.

## 3. What was implemented

A single reporting-only, **non-learning** form-A falsifier + its test lock, delivered **UNCOMMITTED** over HEAD
`07752c8`:

```text
research/brainvision/run_all_shortcuts_closed_synthetic_v0_3.py
tests/research/test_brainvision_all_shortcuts_closed_synthetic_v0_3.py
```

It reuses the frozen v0.7/v0.8 descriptors by identity and the v1.9/v2.0 generators. It builds a larger-N
family (structure = coherent winders across angular speeds / phases / radii; non-structure = cancellation
trajectories), matches each winder to the canceller minimizing the L-inf cheap-proxy residual, then applies the
SAME fixed rule (`structure iff PSC >= PSC_FLOOR and AIC >= AIC_FLOOR`) and audits shortcut closure.

## 4. New research question

```text
Can the fixed frozen PSC/AIC color-structure rule still separate synthetic structure when movement/channel-
energy, directional, spectral, per-channel, and frame-diff shortcuts are all matched or neutralized together?
```

## 5. Result — construction infeasible (Outcome 4)

```text
n_structure = 8   n_nonstructure = 5
fixed color rule: balanced accuracy = 1.000   confusion = {tp:8, fn:0, fp:0, tn:5}
all_shortcuts_closed = False
all_shortcuts_closed_construction_feasible = False
outcome = Outcome_4  (all-shortcuts-closed construction INFEASIBLE; residual shortcuts remain)
research_signal = unresolved_proxy_wall_remains
```

The best-effort matched family (winder → best-matched canceller, L-inf proxy residual **0.0404–0.0634**) could
**not** close all five shortcut groups simultaneously. There is a genuine geometric obstruction: matching the
directional per-step increment (`u_directional_delta_rms` / `angular_increment_mag`) conflicts with matching
full symmetric channel coverage (`rg_std` = `by_std`, per-channel centroids / spreads), because a coherent
winder traverses the full circle uniformly while a winding-cancelling out-and-back that matches the per-step
increment covers only a partial arc — leaving residual per-channel-BY differences.

## 6. Shortcut audit (per group)

A group is "closed" only if its best cheap baseline cannot separate the classes (best-threshold BA ≤ 0.60).
`CHANCE_BAND = 0.60` is a **reporting-only** shortcut-audit closure band — not a §7/§8 threshold, not a
replacement acceptance criterion, and not a verdict-moving gate:

```text
group                     cheap_baseline_separates_BA   closed
movement_channel_energy   0.812                         False  (OPEN residual shortcut)
directional               0.738                         False  (OPEN residual shortcut)
spectral                  0.700                         True*  (ill-defined; see note)
per_channel               0.938                         False  (OPEN residual shortcut)
frame_diff                0.675                         False  (OPEN residual shortcut)

open_residual_shortcut_groups = [movement_channel_energy, directional, per_channel, frame_diff]
* spectral: the family has constant chroma (chroma_constant_family = True), so spectral_centroid / spectral_spread
  of CHROMA are FFT-of-a-constant numerical noise -> NOT meaningfully matchable; reported but treated as
  not-a-usable-shortcut rather than claimed "closed" on merit.
```

Matched-stat residuals (per matched pair) are reported in the diagnostic's `matched_pairs[*].per_stat_abs_delta`;
the class-centroid residuals are concentrated in BY statistics (`by_std`, `by_centroid`, `by_spread`), consistent
with the §5 obstruction (per-pair residuals also include other stats). **No residual shortcut difference is
hidden.**

## 7. Baselines, ablations, controls

Cheap-baseline separability over the pooled family (optimistic best-threshold):

```text
per_channel 0.938 (best cheap)   movement_channel_energy 0.812   directional 0.738
spectral 0.700   frame_diff 0.675   random 0.350
best_cheap_baseline = per_channel (0.938)   cheap_baseline_still_separates = True
```

Ablations:

```text
PSC_only_frozen_ba                              = 1.000   (PSC carries the separation)
AIC_only_frozen_ba                              = 0.500   (AIC alone fails)
S_best_threshold_ba_OPTIMISTIC_DIAGNOSTIC_ONLY  = 1.000   (label-fit; NOT the fixed model; diagnostic only)
```

Shuffled-label control (avg of 500 shuffles): `0.5011` (~chance; the fixed rule carries no signal on scrambled
labels).

## 8. Interpretation (research-only)

The fixed color rule separates the family (BA 1.000), but so does a cheap **per-channel** baseline (BA 0.938),
along with movement / directional / frame-diff baselines. Because the all-shortcuts-closed construction is
**infeasible** with the available generators, the **proxy wall remains** and v0.2's signal is **not upgraded**.
This is **Outcome 4**: report infeasibility honestly; do not force a result. It is not evidence of vision,
descriptor validity, temporal order, real-video understanding, memory readiness, runtime readiness, or
integration readiness, and it isolates no unique color-structure advantage.

Allowed reading: *shortcut closure failed (partial); a cheap baseline still separates; research signal
unresolved; the fixed color rule neither gained nor lost support*. Forbidden readings (vision / "Brainvision
sees" / descriptor validity / temporal order / memory or runtime readiness / integration readiness) are **not**
taken.

## 9. Failure cases, infeasibility, and limitations

- **Infeasibility (primary result):** no non-winder in the pool matches a winder on all five shortcut groups
  simultaneously (best L-inf proxy residual ≈ 0.0404–0.0634); four groups remain open.
- **Geometric obstruction:** directional-increment matching vs full symmetric channel coverage are in tension
  (§5); class-centroid residuals are concentrated in BY statistics; per-pair residuals also include other stats.
- **Spectral ill-definedness:** constant-chroma fixtures make `spectral_centroid` / `spectral_spread` FFT-of-
  constant noise; reported transparently, not claimed as a genuine closure.
- **Small N / imbalance:** 8 structure vs 5 unique non-structure (multiple winders matched to the same best
  canceller); balanced accuracy handles imbalance, but the per-group separability BAs are coarse at this N and
  the optimistic best-threshold can overfit small samples. The infeasibility conclusion rests on the
  geometric per-stat residuals, which are not small-N artifacts.

## 10. Claim locks and verdict

```text
first_pass_structure_validity_claim_allowed = False
temporal_claim_allowed                      = False
descriptor_validity_claim_allowed           = False
frozen_brainvision_verdict                  = HOLD   (untouched)
vision_claim = False   memory_readiness_claim = False   runtime_readiness_claim = False
integration_readiness_claim = False
```

Forbidden inference jumps (none taken): prototype-works → sees; scorer-works → memory; beats-baseline →
validity; descriptor-helps → temporal order; separates-fixtures → runtime / integration readiness.

## 11. Tests run

```text
python -m pytest tests/research/test_brainvision_all_shortcuts_closed_synthetic_v0_3.py -q  -> 11 passed
python research/brainvision/run_all_shortcuts_closed_synthetic_v0_3.py                      -> ran clean (exit 0)
python -m pytest tests/research/ -q                                                         -> 235 passed (Windows)
```

Sandbox reconstruction: the full suite shows **234 passed + 1 failed**, the failure being the documented
`spectral_centroid` Linux/Windows knife-edge in `test_brainvision_color_structure_pooled_gate_audit_v1_8.py`
(pre-existing, unrelated to v0.3, passes on Windows). Windows pytest is the source of truth for boundary stats;
the v0.3 tests assert only platform-independent robust facts.

## 12. Recommended next (not opened here)

- Because all-shortcuts-closed construction is **infeasible** with the current generators, the honest options
  are: (a) accept that the synthetic-fixture route cannot isolate a unique color-structure advantage and
  **HOLD** the prototype line; or (b) a **separate, future** docs-only proposal for a fundamentally different
  synthetic construction that could break the directional-increment / channel-coverage tension — still form A,
  still non-learning, still baseline-gated, and only if honestly constructible.
- Forms B / C (classifier / neural), real clips, and memory-system integration stay disallowed until a
  separate future gate.

- **Codex review** of this receipt and of the Outcome-4 infeasibility framing.
- **If accepted,** the next step is either HOLD or a separate docs-only construction proposal; **otherwise
  HOLD.**

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False`, `temporal_claim_allowed = False`,
`descriptor_validity_claim_allowed = False`, and the frozen verdict **HOLD** are unchanged.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision All-Shortcuts-Closed Synthetic Findings v0.3. Reporting-only, non-learning; docs-only
receipt. Opens no implementation lane; opens no classifier / neural work; changes no frozen formula, gate, or
verdict; deletes or weakens no control; redesigns no descriptor; makes no vision / descriptor-validity /
temporal-order / memory / runtime / integration claim; no `§0` pointer added; no tags.*
