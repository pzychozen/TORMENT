# TORMENT Brainvision Color Structure Findings v0.8

## 1. Status / quarantine

**DOCS-ONLY research findings note. Non-authorizing, non-implementing.** Records the outcome of the offline v0.8
chroma-structure diagnostic, implemented exactly from the committed v0.7 formula-freeze plan (`dc0ffec`) and
corrected after Codex review. Work stays under `research/brainvision/` + `tests/research/`; no `torment_service/`
imports; no runtime / camera / live-capture / screen-capture / streaming / prompt / context / memory / action /
render-body / autonomy contact; no object/scene understanding. **No `§0` pointer; no tags.** This makes **no**
vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim (the trajectory-order permutation
is a structure control only). `temporal_claim_allowed` remains **False**. Constants were frozen in v0.7 and were
**not** tuned.

## 2. What was run

`research/brainvision/run_color_structure_v0_8.py` +
`tests/research/test_brainvision_color_structure_v0_8.py` (full research suite **124 passed**; was 113, +11 new
tests). Layered on the v0.3 bridge and v0.4 g5 module, it implements the frozen v0.7 formulas verbatim: the
chroma gate + NEUTRAL handling, unit direction `u(t)`, signed turn `c(t)`, `PSC = |Σc|/(Σ|c|+eps)`,
bias-corrected `AIC`, `S = sqrt(PSC·AIC)`, the component-floor gate, the in-scope rotation family
(`rot_full`/`rot_multi2`/`rot_reverse`) with reporting-only arcs (`rot_half`/`rot_quarter`), the primary
**trajectory-order-permuted** gate null, the reporting-only nulls (independent phase-rand, permuted-BY,
shared-phase), the smooth continuity control, the high-chroma structureless control, the neutral controls, the
out-of-scope reporting-only fixtures (`red_green` / `blue_yellow` / `color_only`), and the anti-proxy correlation
gauntlet. Per Codex review the shared-phase null was corrected to add a shared phase **offset** (so it preserves
relative phase, reporting-only), the anti-proxy stats were completed with spectral spread + per-channel
spread + null-relative versions, and the zero-chroma neutrals are kept out of the anti-proxy bank (they are
handled by the neutral-ceiling gate).

## 3. Results

Per-fixture (S / PSC / AIC; primary trajectory null S_traj; reporting-only S_indep and S_shared):

```
fixture       scope     S    PSC   AIC   S_traj  S_indep  S_shared  ok
rot_full      PASS   1.000  1.00  1.00   0.025    0.931    1.000    True
rot_multi2    PASS   1.000  1.00  1.00   0.090    0.995    1.000    True
rot_reverse   PASS   1.000  1.00  1.00   0.000    0.997    1.000    True
rot_half      report 1.000  1.00  1.00   0.230    0.294    0.385     -
rot_quarter   report 1.000  1.00  1.00   0.128    0.331    0.165     -
```

Continuity control S = 0.303; structureless control S = 0.0 (margin ×1.2). Neutral controls (grayscale,
saturation_collapse, low_saturation_neutral, rough_luminance_only, roughness_matched_color) all NEUTRAL / ≤ ceil
→ neutral_ok. Out-of-scope reporting-only fixtures (`red_green`, `blue_yellow`, `color_only`) score S ≈ 0
(degenerate / collinear) and cannot contribute to PASS. All three in-scope rotations clear every fixture-level
gate (`in_scope_ok = 3/3`).

Anti-proxy Spearman(S, stat) over the v0.7 §7 bank (|ρ| < 0.30 required); `nr_` = null-relative to the
trajectory-order-permuted-null baseline:

```
chroma_mag                +0.335  FAIL      by_centroid               -0.453  FAIL
rg_std                    +0.001  ok        rg_spread                 -0.427  FAIL
by_std                    +0.288  ok        by_spread                 -0.589  FAIL
delta_rms                 -0.486  FAIL      nr_u_directional_delta_rms -0.245 ok
spectral_centroid         +0.027  ok        nr_angular_increment_mag  -0.210  ok
spectral_spread           +0.107  ok        nr_rg_centroid            -0.284  ok
u_directional_delta_rms   -0.245  ok        nr_by_centroid            -0.453  FAIL
angular_increment_mag     -0.210  ok        nr_rg_spread              -0.423  FAIL
rg_centroid               -0.284  ok        nr_by_spread              -0.580  FAIL
```

`anti_proxy_ok = False`. **VERDICT: HOLD.** `first_pass_structure_validity_claim_allowed = False`;
`temporal_claim_allowed = False`.

## 4. First-pass interpretation and verdict

Two genuine positives, then the blocker:

1. **The descriptor detects the planted coherent winding in these synthetic rotation fixtures relative to the
   trajectory-order-permuted null.** A perfect rotation scores `S = PSC = AIC = 1.0`; the trajectory-order-permuted
   primary null (same multiset of directions/CHROMA, order scrambled) drops it to ~0.00–0.09. So `S` beats the
   primary gate null by a huge margin — the winding is real and the permutation destroys it.
2. **Codex's null-design corrections are confirmed empirically.** The independent RG/BY phase-randomized null
   stays **high** (`S_indep` = 0.93–0.997) for these narrowband rotations — a coherent ellipse, not scatter —
   which is exactly why v0.7 demoted it to reporting-only. The corrected **shared-phase** null (shared phase
   *offset*, relative phase preserved) now also stays rotation-like (`S_shared` = 1.0 for the full rotations),
   a meaningful reporting-only null; it does not gate. `S` also beats the smooth continuity control (1.0 vs 0.30)
   by margin, so it is not explained by the single smooth continuity control at the fixture level.
3. **But the anti-proxy gate blocks validity.** Across the frozen §7 bank (now completed with spectral spread,
   per-channel spread, and null-relative versions), `S` still correlates beyond the 0.30 ceiling with CHROMA
   magnitude (+0.34), CHROMA `delta_rms` (−0.49), and per-channel spectral spread/centroid (`by_centroid` −0.45,
   `rg_spread` −0.43, `by_spread` −0.59), including their **null-relative** versions (`nr_by_centroid` −0.45,
   `nr_rg_spread` −0.42, `nr_by_spread` −0.58). Coherent winding and per-channel spectral narrowness are
   entangled in these synthetic rotations — a coherent rotation is narrowband (low spectral spread) while its
   trajectory-permuted null is broadband — so `S` and per-channel spread move together across the bank. Per v0.7
   §8 this **blocks validity regardless of the beat-margins**, so the honest verdict is HOLD.

This is the v0.7-§9 "deepest risk" realized: `PSC`/`AIC` cannot yet be certified free of a per-channel-spectrum /
magnitude / roughness association on these fixtures. No tuning was applied to change this.

**Transparency note (spec fidelity, not tuning):** the first run wrongly included the four zero-chroma neutral
controls in the anti-proxy correlation bank, which spuriously inflated the magnitude/std correlations (each
zero-chroma control contributes an `(S=0, chroma=0)` point). v0.7 §7 lists the bank as in-scope rotations +
trajectory-order-permuted nulls + independent nulls + continuity + structureless + reported fixtures — the
zero-chroma neutrals are covered by the separate neutral-ceiling gate — so the bank was corrected to match the
frozen spec (and the omitted independent nulls, spread stats, null-relative versions, and out-of-scope reported
fixtures added). The verdict is HOLD in every configuration.

## 5. Non-claims

This does **not**: prove vision or "Brainvision sees"; prove object/scene understanding; prove temporal-order
sensitivity; establish structure-sensitive descriptor-control validity (anti-proxy unmet); validate on natural
video; authorize runtime / service / camera / sensor / live-capture / screen-capture; or authorize prompt /
context / memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.** Brainvision remains
offline research, HELD per v0.6, with `temporal_claim_allowed` **False**.

## 6. Recommended next

- **Codex review** of the corrected v0.8 implementation (shared-phase fix, completed anti-proxy stats,
  out-of-scope reporting-only fixtures) and this findings note.
- The blocker is the per-channel-spectrum / magnitude / roughness entanglement of `S`. Any next step (a
  **predeclared** future plan, not built here) would need to either add a fixture family that dissociates winding
  from per-channel spectral narrowness (so the anti-proxy correlations can be low), or move to a null-relative
  anti-proxy target that does not conflate coherent winding with narrowband spectra — a change to the frozen v0.7
  definition that must go through a fresh formula-freeze, not a tune. Until then the verdict stays HOLD. No
  temporal-order work; no vision claim.

*End — TORMENT Brainvision Color Structure Findings v0.8. Docs-only, non-authorizing. Opens no implementation
lane; no `§0` pointer added; no tags.*
