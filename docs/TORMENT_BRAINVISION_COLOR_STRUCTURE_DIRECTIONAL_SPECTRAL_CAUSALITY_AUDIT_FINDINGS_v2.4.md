# TORMENT Brainvision Color Structure Directional / Per-Channel-Spectral Causality Audit Findings v2.4

## 1. Status / quarantine and non-claims

**DOCS-ONLY findings receipt for a REPORTING-ONLY diagnostic. Non-authorizing, non-implementing.** It records
the v2.4 causality-audit result — a decomposition of the surviving directional / per-channel-spectral residual
axis under the **unchanged** frozen §7/§8 machinery. It **changes no formula / §7 anti-proxy logic / §8 verdict
logic / threshold / control**, deletes or cherry-picks nothing, and invents no acceptance criterion. Everything
stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6.

This note makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains **False**.
It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture / streaming, or
prompt / context / memory / action / render-body / autonomy paths, and makes **no real-clip / local-clip move**
and **no memory-system integration**. Brainvision Path B is **not proven vision** and is **not a functioning
vision layer for TORMENT memory**. **No `§0` pointer; no tags.**

## 2. What was implemented

A single reporting-only diagnostic + its test lock, delivered **UNCOMMITTED** over HEAD `882c24d`
(`docs(research): plan brainvision directional spectral audit`):

```text
research/brainvision/run_color_structure_directional_spectral_audit_v2_4.py
tests/research/test_brainvision_color_structure_directional_spectral_audit_v2_4.py
```

The diagnostic reuses, **by identity**, the frozen v0.7/v0.8 machinery (`structure_score` / `_stats` /
`_spearman` / constants), the v1.9 parameterized fixture generators (`_winder` / `_arc_osc` / `_collinear` /
`_outback`), and the **v2.1 consolidated deconfounded bank** (`v21._build_bank` / `v21.run`, bank_size 38). It
emits the six predeclared v2.3 sections and decomposes the residual **per sub-axis** (directional vs
per-channel-spectral). The reporting-only classification **cannot change the verdict**: the verdict is the
frozen §8 result over the consolidated bank (HOLD), and an in-code assertion refuses any HOLD→PASS upgrade.

## 3. Tests run

Validated in the reconstructed committed tree (`git archive HEAD` + the two new files, sandbox):

```text
v2.4 tests:                     10 passed
v2.1 integrated-map regression:  9 passed
full Brainvision suite:         202 passed  (Windows source-of-truth expectation)
```

Sandbox note (transparency): the Linux sandbox reconstruction reports **201 passed + 1 failed**, where the one
failure is `test_brainvision_color_structure_pooled_gate_audit_v1_8.py::test_matched_subset_blockers_are_reported_consistently`.
This is the **documented `spectral_centroid` Linux/Windows knife-edge** (pooled `|rho|` ≈ 0.263 on the Linux
sandbox vs ≥ 0.30 on Windows); it was confirmed **pre-existing** in a pristine `git archive HEAD` tree **without
the v2.4 files**, so it is **not** caused by this slice and **passes on Windows**. Per repo doctrine, Windows
pytest is the source of truth for boundary stats; the operator should re-run the suite on Windows to confirm the
202 count.

## 4. Numeric outputs (sandbox reconstruction; reporting-only)

`verdict HOLD | anti_proxy_ok False | bank_size 38 | classification mixed_or_unresolved`

### 4.1 Pooled Spearman driver table (remaining axis; frozen §7, `|rho| >= 0.30` fails)

```text
#1  nr_u_directional_delta_rms   rho=-0.862  fail   [directional]
#2  u_directional_delta_rms      rho=-0.858  fail   [directional]
#3  angular_increment_mag        rho=-0.850  fail   [directional]
#4  nr_angular_increment_mag     rho=-0.847  fail   [directional]
#5  nr_by_centroid               rho=-0.704  fail   [per_channel_spectral]
#6  by_centroid                  rho=-0.703  fail   [per_channel_spectral]
#7  rg_centroid                  rho=-0.702  fail   [per_channel_spectral]
#8  nr_rg_centroid               rho=-0.702  fail   [per_channel_spectral]
#9  by_spread                    rho=-0.638  fail   [per_channel_spectral]
#10 nr_by_spread                 rho=-0.635  fail   [per_channel_spectral]
#11 rg_spread                    rho=-0.597  fail   [per_channel_spectral]
#12 nr_rg_spread                 rho=-0.584  fail   [per_channel_spectral]
controlled reference: by_std pass (rho=+0.023 sandbox / +0.036 Windows-truth),
                      spectral_centroid pass (rho=+0.009 sandbox / -0.050 Windows-truth)
```

The directional stats lead the wall (`|rho|` 0.847–0.862); the per-channel-spectral stats follow (0.584–0.704).
All remaining rows are **far from the 0.30 ceiling** (robust across platforms). `by_std` / `spectral_centroid`
appear only as controlled reference (pass on both platforms).

### 4.2 Exact-matched pair diagnostics + pairwise deltas

```text
family          nonwinder_pick   mean|Δblk|   ΔS      ΔPSC    matched   S/PSC separates
movement        outback_0.20     0.0036      +0.822  +0.968  True      True
rg_by_centroid  collinear_1      0.0000      +1.000  +1.000  True      True
rg_by_spread    collinear_2      0.0000      +0.999  +1.000  True      True
```

On every family the target blocker is matched to numerical precision (mean `|Δ|` ≤ 0.0036) yet `S` / `PSC` still
separate coherent winding from cancellation (`ΔS` 0.82–1.00). The descriptor is **not** merely reading the
blocker.

### 4.3 Null-relative decomposition (source of the pooled association)

```text
nr_u_directional_delta_rms   full=-0.858  primaries_only=-0.803  -> descriptor_blocker_co_movement
nr_angular_increment_mag     full=-0.850  primaries_only=-0.686  -> descriptor_blocker_co_movement
nr_rg_centroid               full=-0.702  primaries_only=-0.059  -> null_bank_geometry
nr_by_centroid               full=-0.703  primaries_only=-0.076  -> null_bank_geometry
nr_rg_spread                 full=-0.597  primaries_only=+0.137  -> null_bank_geometry
nr_by_spread                 full=-0.638  primaries_only=+0.002  -> null_bank_geometry
```

(The frozen `nr_` baseline is a scalar, so `nr_` and raw Spearman coincide; the informative split is **where**
the association lives.) For the **directional** stats the association survives among the actual winders/nonwinders
(co-movement); for the **per-channel-spectral** stats it **collapses to ~0** among primaries and is reintroduced
by the null / control geometry.

### 4.4 Within-class vs cross-group vs pooled

```text
stat                     pooled   within_winder   within_nonwinder   cross_group
u_directional_delta_rms  -0.858   +0.000          -0.518             -0.928
angular_increment_mag    -0.850   +0.000          +0.070             -0.870
rg_centroid              -0.702   +0.000          +0.886             -0.912
by_centroid              -0.703   +0.000          +0.807             -0.912
rg_spread                -0.597   +0.000          +0.993             -0.928
by_spread                -0.638   +0.000          +0.732             -0.928
```

Within the winder class `S` is pinned at 1.0 (within-winder Spearman 0.000; winders occupy a **tight** blocker
region — e.g. `rg_centroid ∈ [0.0312, 0.0313]`, `rg_spread ≈ 0`), while the pooled failure is carried by the
**cross-group** structure (`|rho|` ≈ 0.87–0.93).

## 5. Classification (reporting-only; v2.3 vocabulary only)

```text
headline: mixed_or_unresolved
  directional          -> B_validity_surface_mismatch   (matched pairs separate at fixed blocker;
                                                          near-definitional co-movement of winding)
  per_channel_spectral -> C_bank_composition_artifact    (primaries-only association collapses;
                                                          failure reintroduced by null/control geometry)
A_descriptor_limitation: NOT supported on either sub-axis
```

**A (descriptor limitation) is not supported:** on every sub-axis `S` / `PSC` still separates winding from
cancellation at matched blocker values. The **directional** axis is a near-definitional co-movement of coherent
winding (B-leaning): winding forces low directional jitter by construction, and the pooled association survives
among primaries but is broken by exact matching. The **per-channel-spectral** axis is a bank-composition effect
(C-leaning): the primaries-only association is ~0 and the pooled failure is reintroduced by the null / control
geometry. Because the two sub-axes support **different** readings, the single headline is
**mixed_or_unresolved**. This is a decomposition of the residual, **not** a descriptor-validity, vision, or
temporal-order claim.

## 6. Verdict and preserved flags

```text
verdict:                                          HOLD   (frozen §8 over the v2.1 consolidated bank, by identity)
classification cannot change verdict:             True   (reporting-only; in-code HOLD->PASS assertion + test lock)
first_pass_structure_validity_claim_allowed:      False
temporal_claim_allowed:                           False
```

The frozen §8 verdict is unchanged at **HOLD**. The reporting-only classification is structurally barred from
upgrading it (regression lock: `test_classification_cannot_upgrade_verdict_regression_lock`).

## 7. Non-claims (unchanged) and recommended next

This receipt makes **no** descriptor-validity claim, **no** temporal-order proof, **no** vision claim, **no**
"Brainvision sees" claim, and **no** functioning-memory-system-vision-layer claim. It authorizes **no** real
clips, **no** memory integration, **no** §7 edit, **no** §8 verdict edit, **no** threshold invention, **no**
replacement acceptance criteria, and **no** control deletion. `first_pass_structure_validity_claim_allowed = False`
and `temporal_claim_allowed = False` are unchanged.

- **Codex review** of this receipt and of the per-axis decomposition (directional → B-leaning, per-channel → C,
  A not supported; headline mixed_or_unresolved), keeping the verdict at HOLD and all disallowed moves disallowed.
- **If accepted,** the next decision is a docs-only fork over the two sub-axes (a directional validity-surface
  review vs a per-channel bank-composition follow-up); **no** implementation, real-clip, or memory move is opened
  here. Otherwise **HOLD**.

Brainvision remains **offline / quarantined**, HELD per v0.6.
**No `§0` pointer; no tags.**

*End — TORMENT Brainvision Color Structure Directional / Per-Channel-Spectral Causality Audit Findings v2.4.
Reporting-only diagnostic; docs-only receipt. Opens no implementation lane; changes no frozen formula, gate, or
verdict; deletes no control; invents no threshold; no descriptor redesign; no `§0` pointer added; no tags.*
