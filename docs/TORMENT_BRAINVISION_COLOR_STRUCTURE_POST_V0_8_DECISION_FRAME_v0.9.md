# TORMENT Brainvision Color Structure Post-v0.8 Decision Frame v0.9

## 1. Status / quarantine and non-claims

**DOCS-ONLY decision frame. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** This note reviews the outcome of the v0.8 chroma-structure diagnostic
(implemented from the v0.7 formula-freeze, `dc0ffec`; tested at `c225452`; Codex accepted the patched
version AS-IS) and **recommends only which research slice should be considered next**. It implements no descriptor,
no diagnostic, no code, and no tests, and it changes nothing about the frozen v0.7 formulas. Everything
stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. **No `§0` pointer; no
tags.**

This frame makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths. **No implementation is
authorized by this document.**

## 2. Honest summary of v0.8

v0.8 implemented the frozen v0.7 chroma-structure formula diagnostic verbatim and Codex accepted the
patched version AS-IS. The descriptor read the v0.3-bridge per-frame chroma-plane series and computed,
exactly as frozen:

- **Chroma gate + NEUTRAL handling.** A sample is valid iff `CHROMA(t) >= CHROMA_GATE_FLOOR`; a
  consecutive pair is valid iff both endpoints are valid. If too few pairs are valid
  (`Np < MIN_VALID_PAIRS`, or valid fraction `< MIN_VALID_FRACTION`), the window returns **NEUTRAL**
  (score 0, excluded from any PASS).
- **Unit chroma direction `u(t)`.** For each valid sample, `u(t) = (RG(t), BY(t)) / CHROMA(t)` — a unit
  vector, so chroma magnitude is removed from the unit-direction calculation; magnitude/proxy independence still depends on the anti-proxy gate.
- **Signed turn `c(t)`.** For each valid pair, the plane cross product
  `c(t) = u_x(t)·u_y(t+1) − u_y(t)·u_x(t+1)` (equal to `sin(Δθ_t)`, computed from the unit vectors, no
  `atan2`).
- **Path/scatter contrast `PSC = |Σ c| / (Σ |c| + eps)`.** Coherent, same-sign winding → `PSC ≈ 1`;
  cancelling / back-and-forth turns → `PSC ≈ 0`. This is the primary, magnitude-normalized claim
  surface.
- **Bias-corrected `AIC`.** Circular resultant of the wrapped hue increments, bias-corrected
  (`AIC = sqrt(max(0, (Np·R² − 1)/(Np − 1)))`) so it is comparable to a same-length null. Required
  companion component, valid only for rotation-like fixtures; it cannot rescue a failed `PSC`.
- **Primary score `S = sqrt(PSC · AIC)`** (geometric mean, in `[0, 1]`).
- **Component-floor gate.** A PASS path requires **both** `PSC >= PSC_FLOOR` **and** `AIC >= AIC_FLOOR`;
  clearing one component via a proxy does not pass.

Fixtures and controls exactly as frozen in v0.7:

- **Primary PASS fixtures:** `rot_full` (one turn), `rot_multi2` (two turns), `rot_reverse` (opposite
  direction).
- **Reporting-only arc fixtures:** `rot_half` (half-turn arc), `rot_quarter` (quarter arc) — endpoint /
  window effects keep them off the PASS path.
- **Primary gate null:** the **trajectory-order-permuted** null over the full `u(t)` samples — same
  multiset of unit directions and CHROMA values, temporal order scrambled, coherent winding destroyed.
  This is the only null `S`/`PSC`/`AIC` must beat.
- **Reporting-only nulls:** the independent phase-randomized RG/BY null; the independently permuted-BY
  variant; and the shared-phase null (corrected per Codex to a shared phase *offset* preserving relative
  phase). None of these gates.
- **Smooth continuity control** (two independent length-7-smoothed noise series — smooth but jointly
  structureless).
- **High-chroma structureless control** (independent clipped Gaussian RG/BY — large chroma, no joint
  structure).
- **Neutral controls** (grayscale, saturation collapse, low-saturation neutral, rough-luminance-only,
  roughness-matched color-vs-luminance) — must stay `≤ ceil` / NEUTRAL.
- **Expanded anti-proxy Spearman gauntlet** — after Codex review the anti-proxy bank was completed with
  per-channel spectral spread/centroid and the null-relative (`nr_`) versions, and the zero-chroma
  neutrals were correctly excluded from it (they are covered by the separate neutral-ceiling gate).

Results, exactly as recorded in the v0.8 findings note:

```
fixture       scope     S    PSC   AIC   S_traj  S_indep  S_shared  ok
rot_full      PASS   1.000  1.00  1.00   0.025    0.931    1.000    True
rot_multi2    PASS   1.000  1.00  1.00   0.090    0.995    1.000    True
rot_reverse   PASS   1.000  1.00  1.00   0.000    0.997    1.000    True
rot_half      report 1.000  1.00  1.00   0.230    0.294    0.385     -
rot_quarter   report 1.000  1.00  1.00   0.128    0.331    0.165     -
```

Continuity control `S = 0.303`; structureless control `S = 0.0`. Neutral controls all NEUTRAL / `≤ ceil`.
Anti-proxy failures (|Spearman| ≥ 0.30): `chroma_mag` +0.335, `delta_rms` −0.486, `by_centroid` −0.453,
`rg_spread` −0.427, `by_spread` −0.589, plus the null-relative variants `nr_by_centroid` −0.453,
`nr_rg_spread` −0.423, `nr_by_spread` −0.580. `anti_proxy_ok = False` → **VERDICT: HOLD**, after the full
v0.7-required stats were completed.

## 3. What worked

- **The descriptor is not empty.** It fires cleanly on the intended synthetic rotation fixtures relative to the primary trajectory-order-permuted null.
- **It detects the planted coherent winding** in the synthetic rotation fixtures: in-scope rotations
  scored `S = PSC = AIC = 1.0`.
- **The trajectory-order-permuted null is the correct primary gate for this narrow rotation-scope
  slice** — it preserves the multiset of directions/CHROMA and destroys only coherent winding, which is
  the exact structure the descriptor claims. Under it, `S` dropped to about **0.00–0.09**, so the
  descriptor beats its primary gate null by a large margin; the planted coherent-winding signal is recovered in these fixtures, and this permutation destroys that planted trajectory structure.
- **The independent phase-randomized null stayed high** (`S_indep` ≈ 0.93–0.997), empirically
  confirming v0.7's decision to demote it to reporting-only: for narrowband sinusoidal rotations it
  produces a coherent ellipse rather than scatter, so it is invalid as a gate for this fixture family.
- **The shared-phase null is reporting-only** (relative phase preserved → still rotation-like); it never
  gates and did not.
- **The continuity control was beaten at fixture level** (`S` 1.0 vs 0.303 by margin), so the score is
  not explained by the single smooth continuity control at the fixture level.
- **Neutral controls stayed neutral** — no cross-fire from luminance roughness, chroma collapse, or
  grayscale.

## 4. What blocked validity

- **Final verdict remains `VERDICT: HOLD`.** `first_pass_structure_validity_claim_allowed = False`;
  `temporal_claim_allowed = False`.
- **No descriptor-control validity claim, no vision claim, no temporal-order claim** may be drawn from
  v0.8.
- **The anti-proxy gate failed** across the completed v0.7 §7 bank. Correlations exceeded the 0.30
  ceiling for chroma magnitude, chroma `delta_rms`, BY centroid, RG/BY spectral spread, and the
  null-relative spread/centroid variants.
- **Therefore the current `S` remains entangled with spectral / magnitude proxies.** In these synthetic
  rotations, coherent winding and per-channel spectral narrowness co-vary — a coherent rotation is
  narrowband while its trajectory-permuted null is broadband — so `S` and per-channel spread move
  together across the bank. Under v0.7 §8 any anti-proxy correlation above the ceiling blocks validity
  regardless of the beat-margins.
- **This is a useful HOLD, not a failed arc.** The diagnostic is non-empty, and its primary gate behaved as intended for this narrow synthetic rotation family;
  what is unresolved is whether the *score* can be certified free of a magnitude / roughness / spectrum
  association on a fixture bank that currently over-entangles those axes with winding.

## 5. Three candidate next directions

### A. Fixture-bank redesign — recommended first

Add / redesign synthetic fixtures that intentionally **dissociate winding coherence from directional
smoothness, chroma magnitude, and per-channel spectral spread**, while **preserving the current frozen
v0.7 diagnostic meaning unchanged**. This is the cleanest next slice: it targets the actual v0.8 blocker
(an over-entangled bank) without touching the `PSC`/`AIC`/`S` definitions or the validity logic, so a
future run tests the same descriptor against a bank where low anti-proxy correlations are achievable in
principle. If `S` survives a bank where winding and spectral narrowness are decorrelated, the anti-proxy
gate becomes informative rather than structurally doomed. Lowest risk, highest diagnostic value first.

### B. Null-relative anti-proxy redesign — potentially useful, more dangerous

Rework the anti-proxy target so it is measured relative to the primary-gate null rather than against the
frozen mixed-bank correlation gauntlet. This could in principle remove the shared-narrowband confound.
But it **changes the validity logic away from the v0.7 frozen mixed-bank correlation gauntlet**, which is
the load-bearing anti-proxy contract. Any such change must go through a fresh formula-freeze and careful
Codex / operator review before implementation — it is not a tune, and it risks defining the confound away
rather than dissolving it. Useful to hold in reserve; not the first move.

### C. Descriptor redesign — real option, premature now

Replace or augment `PSC`/`AIC` if they prove **inherently** proxy-bound. This is a genuine option and
should stay on the table, but it is **premature before testing whether the current fixture bank is simply
over-entangled**. Redesigning the descriptor to escape a confound that actually lives in the fixtures
would be solving the wrong problem and would discard a working, correctly-gated diagnostic. Revisit only
if a decorrelated fixture bank (Direction A) still shows `S` tracking magnitude / spectrum.

## 6. Recommendation

**Next slice: docs/planning for a fixture-bank redesign first.** That slice should be a predeclared plan
(no code) that defines candidate synthetic fixtures which intentionally separate:

- winding coherence,
- directional smoothness,
- chroma magnitude,
- RG/BY spectral spread,
- centroid / spread null-relative proxy behavior,
- neutral / chroma-floor behavior.

The goal is a bank on which low anti-proxy correlations are *achievable in principle*, so the v0.7
anti-proxy gate becomes a real test of the descriptor rather than a measurement of the bank's built-in
entanglement — all while keeping the frozen v0.7 `PSC`/`AIC`/`S` definitions and validity logic intact.
**v0.9 itself authorizes no code, no tests, and no change to the frozen formulas.** Directions B and C
remain recorded options, not yet opened.

## 7. Quarantine and non-claims (unchanged)

This decision frame does **not**: prove vision or "Brainvision sees"; prove object / scene understanding;
prove temporal-order sensitivity; establish structure-sensitive descriptor-control validity (anti-proxy
unmet); validate on natural video; or authorize any implementation. Specifically:

- Brainvision remains **offline / quarantined**, HELD per v0.6.
- **No runtime integration.**
- **No `torment_service/` / service-path contact.**
- **No camera / live-capture / sensor / screen-capture / streaming input.**
- **No prompt / context / memory / action / render-body / autonomy contact.**
- **No production vision claim.**
- **No "Brainvision sees" claim.**
- **No temporal-order claim** (`temporal_claim_allowed` stays False).
- **No real-clip / local-clip move yet.** The offline local-clip manifest is a strictly later step and
  should **not** start until the synthetic anti-proxy entanglement is understood.

`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

## 8. Recommended next

- **Codex review** of this decision frame and of the recommendation to open a fixture-bank-redesign
  planning slice next (Direction A), keeping Directions B and C recorded but unopened.
- **If the operator explicitly opens the next docs-only slice,** that slice should only predeclare the candidate decorrelated fixture
  bank (the six separations in §6), with the frozen v0.7 formulas and validity logic untouched and no
  code, math, or tuning until that plan is itself reviewed. **Otherwise HOLD.**

*End — TORMENT Brainvision Color Structure Post-v0.8 Decision Frame v0.9. Docs-only, non-authorizing.
Opens no implementation lane; changes no frozen formula; no `§0` pointer added; no tags.*
