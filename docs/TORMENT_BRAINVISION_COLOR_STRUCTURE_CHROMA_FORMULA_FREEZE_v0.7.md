# TORMENT Brainvision Color Structure-Chroma Formula-Freeze Plan v0.7

## 1. Status / quarantine and non-claims

**DOCS-ONLY formula-freeze plan. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It **freezes the exact formulas and the exact null/control generators** for the first
rotation-like chroma-plane structure slice, so a later slice implements them verbatim with nothing left to
choose. It implements no descriptor, no diagnostic, no code, and no tests, and touches no `torment_service/`,
runtime, camera / sensor / live-capture / screen-capture / streaming, or prompt / context / memory / action /
render-body / autonomy paths. **No `§0` pointer; no tags.** Everything stays offline under `research/brainvision/`
+ `tests/research/`, HELD per v0.6. **This plan makes no vision claim, no "Brainvision sees" claim, and no
temporal-order claim.** `temporal_claim_allowed` remains **False**. **No implementation is authorized.**

## 2. v0.6 status

v0.6 froze the required component **classes** (path/scatter contrast + angular-increment consistency), not the
formulas; scoped the first-slice claim to **rotation-like** chroma-plane trajectories only (collinear RG/BY
phase-locked changes out-of-scope unless separately predeclared); and required a **formula freeze before code**.
Implementation remains unauthorized. This plan supplies that formula freeze.

## 3. Frozen constants (predeclared; fixed before any run; never tuned after)

- `CHROMA_GATE_FLOOR = 1e-3` — sample valid iff `CHROMA(t) >= CHROMA_GATE_FLOOR`.
- `MIN_VALID_FRACTION = 0.5` — minimum fraction of valid consecutive pairs, else NEUTRAL.
- `MIN_VALID_PAIRS = 3` — minimum count of valid consecutive pairs, else NEUTRAL.
- `STRUCTURE_BEAT_MARGIN = 0.20` — beat tests require ratio `>= 1 + margin` (i.e. `>= 1.20`).
- `NEUTRAL_STRUCTURE_CEIL = 0.20` — neutral controls must yield `S <= this`.
- `PSC_FLOOR = 0.30`, `AIC_FLOOR = 0.30` — per-component floors (each required component must clear its own).
- `MAGNITUDE_CORR_CEIL = 0.30` — `|Spearman|` ceiling for every anti-proxy correlation.
- `EPS = 1e-9`.
All scores below lie in `[0, 1]`, so the floors/ceilings are directly interpretable.

## 4. Frozen primary descriptor formulas

**Inputs.** Per-frame spatial-mean series `RG(t)`, `BY(t)`, `CHROMA(t) = sqrt(RG(t)^2 + BY(t)^2)`, `t = 0..T-1`
(v0.3 bridge descriptors; no new channel).

**Chroma gate.** Sample `t` is **valid** iff `CHROMA(t) >= CHROMA_GATE_FLOOR`. A consecutive **pair** `(t, t+1)`
is **valid** iff both samples are valid. Let `Np` = number of valid pairs and `Ppair` = total pairs `= T-1`.
Return **NEUTRAL** (score 0, excluded from any PASS) iff `Np < MIN_VALID_PAIRS` or `Np / Ppair <
MIN_VALID_FRACTION`.

**Unit chroma direction.** For each valid sample, `u(t) = (RG(t), BY(t)) / CHROMA(t)` (a unit vector; magnitude
removed by construction).

**Signed turn per valid pair.** For each valid pair, the plane cross product
`c(t) = u_x(t)·u_y(t+1) - u_y(t)·u_x(t+1)` (equal to `sin(Δθ_t)`, the signed turn between consecutive unit
directions; computed from the unit vectors, **no `atan2`**).

**Component 1 — Path/scatter contrast `PSC` (primary plane geometry, magnitude-normalized).**
`PSC = | Σ c(t) | / ( Σ |c(t)| + EPS )`, sum over valid pairs. `PSC ∈ [0, 1]`. A coherently winding rotation has
same-sign turns so `|Σc| = Σ|c|` → `PSC ≈ 1`; a back-and-forth wander or an incoherent scatter has cancelling
signs → `PSC ≈ 0`. This is the primary claim surface and uses only unit-direction geometry.

**Component 2 — Angular-increment consistency `AIC` (chroma-gated hue readout + required component).**
Hue `θ(t) = atan2(BY(t), RG(t))` on valid samples; wrapped increment `Δθ_t = atan2(sin(θ(t+1)-θ(t)),
cos(θ(t+1)-θ(t))) ∈ (-π, π]` on valid pairs. Raw mean resultant length `R = | (1/Np) Σ exp(i·Δθ_t) | ∈ [0,1]`.
**Bias-corrected** (to remove the small-sample positive bias, so it is comparable to a same-length null):
`AIC = sqrt( max(0, (Np·R^2 - 1) / (Np - 1)) )` for `Np >= 2`, else `0`. `AIC ∈ [0,1]`; steady winding → `≈1`,
random increments → `≈0`. It is a **required component but never the sole claim surface**, and — per v0.6 — is
valid only for rotation-like fixtures (§5); it must not be used to claim collinear phase-locked structure.
`AIC` partly overlaps `PSC` (both read the signed turns between consecutive unit directions); it is a
**consistency companion, not an independent geometry surface, and cannot rescue a failed `PSC`**.

**Primary score `S`.** `S = sqrt( PSC · AIC )` (geometric mean; `∈ [0,1]`). The **component-floor gate** requires
**both** `PSC >= PSC_FLOOR` **and** `AIC >= AIC_FLOOR` (a case passing one via a proxy does not pass). A NEUTRAL
window has `S = 0` and cannot contribute to a PASS.

## 5. Frozen rotation-like fixture scope

**In-scope (rotation family; the only fixtures that may contribute to a PASS).** Each uses
`RG(t) = A·cos(θ(t))`, `BY(t) = A·sin(θ(t))`, `Y' = BASE_Y`, `A = AMP`, over `t = 0..T-1` (gamut-safe as in the
v0.3 bridge). A coherent hue trajectory `θ(t)`:

- `rot_full` — `θ(t) = 2π·t/T` (one turn). **Primary PASS fixture.**
- `rot_multi2` — `θ(t) = 4π·t/T` (two turns). **Primary PASS fixture.**
- `rot_reverse` — `θ(t) = -2π·t/T` (opposite direction). **Primary PASS fixture.**
- `rot_half` — `θ(t) = π·t/(T-1)` (half-turn arc). **Reporting-only arc-sensitivity fixture.**
- `rot_quarter` — `θ(t) = (π/2)·t/(T-1)` (quarter arc). **Reporting-only arc-sensitivity fixture.**

**Primary PASS fixtures: `rot_full`, `rot_multi2`, `rot_reverse`; `rot_half` and `rot_quarter` are reporting-only
arc-sensitivity fixtures.** Finite arcs make `PSC`/`AIC` sensitive to endpoint / window effects (few turns,
boundary bias), so arcs cannot contribute to PASS unless their null behavior is separately validated in a later
plan.

**Out-of-scope / REPORTING-ONLY** (may be reported, cannot contribute to a PASS): `hue_rotation_like` from the
bridge is folded into `rot_full`; `red_green_opponent_change` and `blue_yellow_opponent_change` are degenerate
(one opponent axis fixed at 0 → no winding); `color_only_equal_luminance` is **collinear phase-locked** (RG, BY
proportional) — explicitly **out-of-scope** per v0.6. These are reported for transparency but excluded from the
PASS count.

## 6. Frozen null / control generators

For each in-scope rotation fixture with series `(Y'(t), RG(t), BY(t))`, `phase_randomize_1d(x, rng)` is the v0.4
generator (preserves amplitude spectrum + DC + Nyquist exactly; randomizes intermediate phases). RNG seeds are
predeclared per fixture.

- **Trajectory-order-permuted chroma-plane null — PRIMARY GATE TARGET (must be beaten by `PSC`/`AIC`/`S`).**
  Primary gate null: randomly permute the temporal order of full chroma-plane samples `u(t)` with a predeclared
  seed, preserving the set of unit directions and CHROMA values while destroying coherent winding. This is the
  valid no-joint-structure null: the permuted trajectory has the **same multiset of unit directions and CHROMA
  values** but no coherent winding → `PSC`, `AIC`, `S` low. The independently permuted-BY variant is
  **reporting-only** because it changes chroma-plane occupancy and may alter CHROMA geometry. (Trajectory-order
  permutation here is a structure control only and makes **no temporal-order claim** — see §8/§10.)
- **Independent RG/BY phase-randomized null — REPORTING-ONLY (not the primary gate).** `Y'` held to the intended
  series; `RG_null = phase_randomize_1d(RG, rng_a)`, `BY_null = phase_randomize_1d(BY, rng_b)` with **independent**
  RNGs. Independent RG/BY phase randomization is **NOT assumed to destroy joint structure** for single-frequency
  sinusoidal rotation fixtures; for narrowband fixtures it may produce a coherent ellipse (so `PSC`/`AIC` can stay
  high). Therefore it is reporting-only for `rot_full` / `rot_multi2` (and `rot_reverse`) unless explicitly paired
  with the phase-destroying primary gate null above.
- **Shared-phase null — REPORTING-ONLY.** Same random phase set applied to `RG` and `BY` (relative phase
  preserved) → trajectory stays rotation-like → high `S`; predeclared **not** required to be beaten.
- **Smooth / spectrum-matched continuity control (anti-smoothness).** Two **independent** smooth signals:
  `RG_c = A·norm(movavg(whitenoise(seed_c), k=7))`, `BY_c = A·norm(movavg(whitenoise(seed_d), k=7))`, `Y' =
  BASE_Y`, where `movavg(·, k=7)` is a length-7 moving average, `norm(·)` scales to unit peak, and both series
  are independently generated. Smooth but **jointly structureless** (back-and-forth, not winding) → `PSC` low.
  `S(intended)` must beat this, or `S` is a smoothness proxy.
- **High-chroma structureless control.** `RG_h = clip(A·randn(seed_e), -A, A)`, `BY_h = clip(A·randn(seed_f), -A,
  A)`, `Y' = BASE_Y` — high chroma magnitude, independent, no joint structure → `S` must NOT fire.
- **grayscale** — `RG = BY = 0` (chroma 0) → NEUTRAL.
- **saturation_collapse** — the bridge control (scale toward gray, factor 0) → NEUTRAL.
- **low_saturation_neutral** — bridge fixture, `|RG|,|BY|` below `CHROMA_GATE_FLOOR` → NEUTRAL.
- **rough_luminance_only_null** — v0.4 generator (rough `Y'`, chroma 0) → NEUTRAL.
- **roughness_matched_color_vs_luminance_pair** — v0.4 generator; reported to carry G5a cross-channel roughness
  immunity forward (no structure from luminance roughness, no cross-fire).

## 7. Frozen anti-proxy checks

Over the full bank (in-scope rotations + trajectory-order-permuted nulls + independent nulls + continuity +
structureless + reported fixtures), compute Spearman rank correlation between `S` and each statistic, and require `|Spearman| <
MAGNITUDE_CORR_CEIL`:

- `CHROMA magnitude` — median `CHROMA(t)` over valid samples;
- `RG std` — temporal std of `RG(t)`;
- `BY std` — temporal std of `BY(t)`;
- `delta_rms` — RMS frame-to-frame change of the chroma magnitude series;
- `spectral centroid / spread` — energy-weighted mean temporal frequency (and its spread) of `CHROMA(t)`;
- `directional delta_rms of u(t)` — RMS frame-to-frame change of the unit-direction series;
- `angular increment magnitude` — mean `|Δθ_t|` over valid pairs;
- `RG/BY spectral centroid / spread` — per-channel (not only `CHROMA`) frequency content;
- **null-relative versions** of the above — each statistic's ratio/difference vs the primary-gate null, to check
  `S` is not tracking a proxy the null already shares.

**Any `|Spearman|` above its ceiling blocks validity**, even if all beat-margins are met, because it means `S`
is tracking magnitude / roughness / spectrum rather than joint rotation structure. (Because `S` is
magnitude-normalized, these correlations are expected low; the check verifies rather than assumes it.)

## 8. Frozen pass / HOLD / FAIL logic

Per in-scope rotation fixture `f`, `fixture_ok(f)` iff **all**:

- `S_intended(f) >= (1 + STRUCTURE_BEAT_MARGIN) · S_trajectory_order_permuted_null(f)` (the **primary required
  gate** — the trajectory-order-permuted chroma-plane null of §6);
- `S_intended(f) >= (1 + STRUCTURE_BEAT_MARGIN) · S_continuity_control`;
- `S_intended(f) >= (1 + STRUCTURE_BEAT_MARGIN) · S_high_chroma_structureless`;
- `PSC_intended(f) >= PSC_FLOOR` **and** `AIC_intended(f) >= AIC_FLOOR`.

**PASS** (a first-pass structure-sensitive descriptor-control validity statement — still offline, still not
vision) iff **all**:

- `fixture_ok(f)` holds for a **strict majority (> 0.5)** of the **in-scope** rotation fixtures (no
  single-fixture pass; out-of-scope fixtures cannot contribute);
- every neutral control yields `S <= NEUTRAL_STRUCTURE_CEIL` (or NEUTRAL);
- every anti-proxy `|Spearman| < MAGNITUDE_CORR_CEIL`;
- the shared-phase null, the **independent RG/BY phase-randomized null (reporting-only for narrowband fixtures)**,
  and the RG/BY phase-coherence companion are reported only (none may create a pass path or rescue a failed
  primary).

**FAIL** iff `S_intended <= S_trajectory_order_permuted_null` on a majority of in-scope fixtures, with component
floors unmet or not exceeding the null; **otherwise HOLD** (validity not established — e.g. margin met on the null
but not on the continuity/structureless controls, or an anti-proxy correlation exceeds its ceiling). In every case: **no
temporal-order claim; no vision claim;** `temporal_claim_allowed` and (unless PASS)
`first_pass_descriptor_control_validity_claim_allowed` stay False. This plan predeclares **no** expected verdict
and forbids tuning toward one.

## 9. Risks / reasons to HOLD

- **Formulas may still encode a smoothness/spectrum proxy.** `PSC` and `AIC` are both turn/angle based; a signal
  that is smooth but not winding could still score moderately. The smooth/spectrum-matched continuity control
  (§6) is the explicit guard — if `S` does not beat it, the verdict is HOLD, not PASS.
- **Rotation-only scope may be too narrow.** The in-scope set is a synthetic rotation family; a real chroma
  structure need not be a clean rotation, and collinear phase-locked structure is out-of-scope here. A PASS would
  be narrow by construction.
- **The chroma gate may discard too much data.** At `CHROMA_GATE_FLOOR = 1e-3`, low-chroma fixtures can fall below
  `MIN_VALID_FRACTION` and return NEUTRAL; this is safe but may leave few usable samples on real content.
- **Short synthetic sequences make phase randomization fragile.** At `T = 32` the amplitude spectrum is coarse
  and phase randomization is ill-conditioned; the independent null is reporting-only because for narrowband
  fixtures it can preserve coherent ellipse-like structure (the v0.4 risk carries over).
- **Circular-statistics bias.** `AIC` uses a bias correction, but small `Np` still inflates resultant length; the
  intended-vs-null margin (same `Np`) mitigates but does not eliminate this.
- **Overfitting synthetic controls / real clips still required.** Passing hand-built synthetic controls is
  necessary but not sufficient; the offline gitignored clip corpus remains the eventual test.

**Recommended posture: HOLD for review.** These formulas and generators are now exact enough to implement; before
any code, Codex / operator should confirm the `PSC`/`AIC`/`S` definitions (§4), the rotation family and
out-of-scope list (§5), the continuity and structureless generators (§6), and the anti-proxy ceilings (§7).

## 10. Non-claims and quarantine boundaries

This plan does **not**: build or select a descriptor; implement any formula, null, or diagnostic; claim vision,
"Brainvision sees", object/scene understanding, temporal-order sensitivity, or classifier superiority; or
authorize any tuning. It adds no runtime integration, no live/screen capture, no service / camera / sensor
contact, and no prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no
tags.** Brainvision remains offline research under `research/brainvision/` + `tests/research/`, HELD per v0.6,
with `temporal_claim_allowed` **False**. **No implementation is authorized.**

## 11. Recommended next

- **Codex review** of these frozen formulas and generators.
- **If** accepted, a single offline research slice may implement exactly the frozen formulas (§4), fixtures
  (§5), generators (§6), anti-proxy checks (§7), and pass/HOLD/FAIL logic (§8) under `research/brainvision/` +
  `tests/research/`, with all §3 constants fixed before running and no tuning. **Otherwise HOLD.** No code, math,
  or tuning until reviewed.

*End — TORMENT Brainvision Color Structure-Chroma Formula-Freeze Plan v0.7. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*
