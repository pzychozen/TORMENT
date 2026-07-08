# TORMENT Brainvision Color Structure Broader Matched-Pair Diagnostic Findings v2.9

## 1. Status / quarantine and non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY diagnostic. Non-authorizing, non-implementing.** It records
the v2.9 broader matched-pair result — an expansion of the matched-pair evidence for the two unresolved v2.7
candidates, under the **unchanged** frozen §7/§8 machinery. It **changes no formula / §7 anti-proxy logic / §8
verdict logic / threshold / control**, deletes or weakens nothing, redesigns no descriptor, and invents no
acceptance criterion. Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains **False**.
It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture / streaming, or
prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip / local-clip move**
and **no memory-system integration**. Brainvision Path B is **not proven vision** and is **not a functioning
vision layer for TORMENT memory**. **No `§0` pointer; no tags.**

## 2. What was implemented

A single reporting-only diagnostic + its test lock, delivered **UNCOMMITTED** over HEAD `d1124df`
(`docs(research): plan brainvision broader matched-pair diagnostic`):

```text
research/brainvision/run_color_structure_broader_matched_pair_diagnostic_v2_9.py
tests/research/test_brainvision_color_structure_broader_matched_pair_diagnostic_v2_9.py
```

It reuses, **by identity**, the frozen v0.7/v0.8 machinery (`structure_score` / `_stats` / `_spearman` /
constants), the v1.9 + v2.0 parameterized generators, the v2.1 consolidated bank, and the **v2.4
decomposition** (`v24.run`). It implements the v2.8 families (directional expansion; non-collinear per-channel
matches; target-preserving vs blocker-preserving), applies the predeclared v2.8 interpretation rules, and
reports the classification. The verdict is taken from the frozen §8 logic over the v2.1 bank (**HOLD**); an
in-code assertion and a regression test bar any HOLD→PASS upgrade.

## 3. Tests run

Validated in the reconstructed committed tree (`git archive HEAD` + the new files, sandbox):

```text
v2.9 tests:                        11 passed
v2.4 decomposition regression:     10 passed
full Brainvision suite:           213 passed   (Windows source-of-truth expectation)
```

Sandbox note (transparency): the Linux sandbox reconstruction reports **212 passed + 1 failed**, the one
failure being the **documented `spectral_centroid` Linux/Windows knife-edge** in
`test_brainvision_color_structure_pooled_gate_audit_v1_8.py` (pooled `|rho|` ≈ 0.263 on Linux vs ≥ 0.30 on
Windows). It was confirmed **pre-existing** without the v2.9 files and **passes on Windows**; it is **not**
caused by this slice. Per repo doctrine, Windows pytest is the source of truth for boundary stats.

## 4. Predeclared criteria and family list

Predeclared as code constants **before** any result was computed (reporting-only; they cannot become §7/§8
thresholds, cannot move the verdict, and were not tuned after seeing results):

```text
MATCH_REPORT_DELTA            = 0.05   (reused from v1.9; "matched" label if |Δblocker| < it)
SEP_MIN_DELTA_S               = 0.5    (S-separation cutoff; v2.4 convention)
LOW_S_MAX                     = 0.5    ("stays low S" if S < it)
PSC_FLOOR / AIC_FLOOR         = 0.30   (reused frozen floors: "low" < floor, "high" >= floor; NOT re-gated)
CEIL                          = 0.30   (reused frozen anti-proxy ceiling: "low" |rho| < it, "high" >= it)
REPEATED_SUPPORT_MIN_FAMILIES = 2      (>= this many matched families must separate = "repeated")
```

Predeclared family list (all reported below, feasible or not):

```text
directional winders:            winder_full, winder_2x_speed, winder_half_speed, winder_radius_0.5, winder_phase_pi
directional nonwinder pool:      outback_0.10/0.20/0.40, arc_1.2_k2, arc_0.8_k3
smoothness-without-winding:      smooth_arc_0.3_k1, smooth_arc_0.4_k1, smooth_outback_0.10
per-channel winders:             winder_full, winder_radius_0.5
per-channel non-collinear pool:  arc_0.3_k1, arc_0.4_k1, arc_0.6_k1, outback_0.10, arc_0.8_k3
per-channel collinear reference: collinear_1, collinear_2
```

## 5. Constructions: successful / imperfect / failed / infeasible

- **Directional matched families:** 5/5 predeclared winders **matched** (feasibility `matched`, mean
  `|Δblocker|` ≤ 0.0072) against a directionally-matched cancellation partner. **None imperfect, none failed,
  none dropped.**
- **Smoothness-without-winding:** 3/3 cases **constructed** (feasibility `constructed`) — low directional
  blockers achieved.
- **Non-collinear per-channel families:** 2/2 predeclared winders **matched** (feasibility `matched`, mean
  `|Δblocker|` = 0.0024) against a **non-collinear** cancellation partner (`arc_0.3_k1`) — non-collinear
  matching of centroid + spread is **feasible** (this addresses the v2.6 caution that the v2.4 matches were
  collinear-only). The collinear reference (`collinear_1`, `|Δ|` = 0.0000) is reported for comparison only.

No construction was infeasible or failed in this run; had any been, it would be reported as
`imperfect_match` / `infeasible_not_low_jitter` rather than dropped or swapped.

## 6. Numeric outputs (sandbox reconstruction; reporting-only)

`verdict HOLD | headline mixed_or_unresolved | directional directional_B_strengthened | per_channel per_channel_C_strengthened`

### 6.1 Directional matched expansion

```text
family              nonwinder_pick   mean|dblk|   dS       matched   separates
winder_full         outback_0.20     0.0036      +0.822    True      True
winder_2x_speed     outback_0.40     0.0072      +0.828    True      True
winder_half_speed   outback_0.10     0.0018      +0.821    True      True
winder_radius_0.5   outback_0.20     0.0036      +0.822    True      True
winder_phase_pi     outback_0.20     0.0036      +0.822    True      True
```

Across multiple angular speeds, a radius variant, and a phase offset, `S` / `PSC` still separates at matched
directional blockers.

### 6.2 Smoothness-without-coherent-winding

```text
case                 S      PSC     AIC     u_ddr   ang     low_dir   stays_low_S/PSC
smooth_arc_0.3_k1    0.226  0.051   0.999   0.041   0.037   True      True
smooth_arc_0.4_k1    0.226  0.051   0.999   0.055   0.049   True      True
smooth_outback_0.10  0.179  0.032   0.995   0.100   0.100   True      True
```

Smooth, low-jitter trajectories that do **not** wind coherently (low `PSC`) all stay **low `S`** — smoothness
alone does not produce a high structure score. No smooth low-jitter case scored high `S`.

### 6.3 Non-collinear per-channel matches

```text
family              pick         non_collinear   mean|dblk|   dS       matched   separates
winder_full         arc_0.3_k1   True            0.0024      +0.774    True      True
winder_radius_0.5   arc_0.3_k1   True            0.0024      +0.774    True      True
collinear reference collinear_1  False           0.0000      +1.000    True      True
```

At matched centroid / spread with a **non-collinear** canceller, `S` / `PSC` still separates.

### 6.4 Target-preserving vs blocker-preserving

Target-preserving (winders only): `S_pinned = True`, `S_range = [1.0, 1.0]`; within-winder Spearman reported as
`0.000` for every blocker (no within-class `S` variation to correlate), while the blockers themselves vary
(e.g. `u_directional_delta_rms` range `[0.098, 0.390]`, `rg_spread` range `[0.0, 0.075]`). Blocker-preserving:
the matched directional pairs above (blocker ~fixed, target class varies) separate. Within/cross/pooled and
null-relative decomposition are carried by identity from v2.4 (primaries-only per-channel ≈ 0; pooled per-channel
fails; source `null_bank_geometry`).

## 7. Classification (reporting-only; v2.8 vocabulary only)

```text
headline:                          mixed_or_unresolved
directional axis:                  directional_B_strengthened
per-channel-spectral axis:         per_channel_C_strengthened
A_descriptor_limitation_supported: False

signals:
  broader_directional_matched_separates      = True
  smoothness_alone_stays_low_S_PSC            = True
  smoothness_alone_high_S_exists              = False
  noncollinear_per_channel_feasible           = True
  noncollinear_matched_separates              = True
  primaries_only_per_channel_low              = True
  pooled_null_control_drives_per_channel      = True
```

Broader (and now **non-collinear**) matched-pair evidence: on both sub-axes `S` / `PSC` still separates winding
from cancellation at matched blockers, and smoothness-without-winding cases stay low `S` / `PSC`. So
**A_descriptor_limitation stays unsupported**. The **directional B** candidate is **strengthened** (per the
predeclared rule: matched pairs still separate across multiple families, and smoothness alone stays low). The
**per-channel C** candidate is **strengthened** (per the predeclared rule: non-collinear matched pairs separate
at fixed centroid / spread, primaries-only association stays low, and the pooled failure is carried by
null / control geometry). Because the two sub-axes support **different** (though each strengthened) readings,
the single-label headline is **mixed_or_unresolved**. This is a re-characterization of the residual, **not** a
descriptor-validity, vision, or temporal-order claim.

## 8. Verdict and preserved flags

```text
verdict:                                      HOLD   (frozen §8 over the v2.1 bank, by identity)
classification cannot change verdict:         True   (reporting-only; in-code HOLD->PASS assertion + test lock)
first_pass_structure_validity_claim_allowed:  False
temporal_claim_allowed:                        False
gate_change_allowed:                           False
control_deletion_allowed:                      False
descriptor_redesign_allowed:                   False
descriptor_validity_claim_allowed:             False
```

The frozen §8 verdict is unchanged at **HOLD**. The reporting-only classification is structurally barred from
upgrading it (regression lock: `test_classification_cannot_upgrade_verdict_regression_lock`).

## 9. Non-claims (unchanged) and recommended next

This receipt makes **no** descriptor-validity claim, **no** temporal-order proof, **no** vision claim, **no**
"Brainvision sees" claim, and **no** functioning-memory-system-vision-layer claim. It authorizes **no** real
clips, **no** memory integration, **no** §7 edit, **no** §8 verdict edit, **no** threshold invention, **no**
replacement acceptance criteria, **no** control deletion, and **no** descriptor redesign.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.

- **Codex review** of this receipt and of the classification (directional B strengthened, per-channel C
  strengthened, A unsupported, headline mixed_or_unresolved), keeping the verdict at HOLD and all disallowed
  moves disallowed.
- **If accepted,** the next decision is a docs-only synthesis of what the strengthened-but-distinct candidates
  imply (both remain unresolved as arc-wide readings); **no** implementation, §7/§8, control, real-clip, or
  memory move is opened here. Otherwise **HOLD**.

Brainvision remains **offline / quarantined**, HELD per v0.6.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Broader Matched-Pair Diagnostic Findings v2.9. Reporting-only
diagnostic; docs-only receipt. Opens no implementation lane; changes no frozen formula, gate, or verdict;
deletes or weakens no control; invents no threshold; redesigns no descriptor; no `§0` pointer added; no tags.*
