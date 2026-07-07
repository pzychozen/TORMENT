# TORMENT Brainvision Color Structure Fixture-Bank Redirection Plan v1.0

## 1. Status / quarantine and non-claims

**DOCS-ONLY planning slice. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** This note is the next slice recommended by the v0.9 post-v0.8 decision frame
(`7337c79`): it **predeclares** a synthetic fixture-bank redesign whose intent is to dissociate winding
coherence from directional smoothness, chroma magnitude, and per-channel spectral / spread proxies. It
**implements no fixtures, writes no tests, changes no formula, and modifies no existing diagnostic.** The
frozen v0.7 descriptor (`dc0ffec`) — chroma gate + NEUTRAL, unit direction `u(t)`, signed turn `c(t)`,
`PSC`, bias-corrected `AIC`, `S = sqrt(PSC·AIC)`, the component-floor gate, and the v0.7 §7/§8 anti-proxy
gauntlet and pass/HOLD/FAIL logic — stays **untouched**. Everything remains offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6. **No `§0` pointer; no tags.**

This plan makes **no** vision claim, **no** "Brainvision sees" claim, and **no** temporal-order claim.
`first_pass_structure_validity_claim_allowed` remains **False** and `temporal_claim_allowed` remains
**False**. It touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths. **No implementation is
authorized by this document.**

## 2. The v0.8 / v0.9 blocker being addressed

- The v0.8 chroma-structure descriptor was **non-empty**. It **recovered the planted coherent-winding
  signal** in the synthetic rotation fixtures relative to the primary **trajectory-order-permuted** null
  (in-scope rotations `S = PSC = AIC = 1.0`; primary null `S ≈ 0.00–0.09`).
- Nonetheless the final verdict was **HOLD**: `first_pass_structure_validity_claim_allowed = False` and
  `temporal_claim_allowed = False`.
- The **anti-proxy gate failed**. Across the frozen v0.7 §7 bank, `S` stayed correlated beyond the
  ceiling with **chroma magnitude** (`+0.335`), **chroma `delta_rms`** (`−0.486`), **BY centroid**
  (`−0.453`), **RG/BY spectral spread** (`rg_spread −0.427`, `by_spread −0.589`), and the **null-relative
  spread / centroid variants** (`nr_by_centroid −0.453`, `nr_rg_spread −0.423`, `nr_by_spread −0.580`).
  So `S` remained entangled with magnitude / roughness / per-channel spectrum rather than being certified
  as reading joint winding structure alone.
- The diagnosed cause is a **bank-level entanglement**, not (yet) a descriptor defect: in these
  single-frequency synthetic rotations, coherent winding and per-channel spectral narrowness co-vary — a
  coherent rotation is narrowband while its trajectory-permuted null is broadband — so `S` and
  per-channel spread move together across the bank *by construction of the bank*.
- v0.9 therefore recommended **fixture-bank redesign first**, ahead of a null-relative anti-proxy
  redesign (Direction B, changes the frozen validity logic — more dangerous) or a descriptor redesign
  (Direction C, premature before the bank is shown not to be the cause). This plan is that first slice.

## 3. v1.0 planning goal

Predeclare a fixture bank on which the **unchanged** frozen `PSC / AIC / S` descriptor can be tested for
whether it survives when the bank **intentionally separates** the axes that were entangled in v0.8:

- **winding coherence** (sign-consistency of the signed turns `c(t)`),
- **directional smoothness** (frame-to-frame change of `u(t)`),
- **chroma magnitude** (median `CHROMA(t)` and its `delta_rms`),
- **RG/BY spectral spread** (per-channel frequency content),
- **BY / RG centroid behavior** (per-channel spectral centroid/spread only; not a mean-hue or semantic color-axis claim),
- **null-relative spread / centroid proxy behavior** (each statistic vs its trajectory-order-permuted
  null),
- **neutral / chroma-floor behavior** (grayscale, saturation collapse, sub-`CHROMA_GATE_FLOOR`).

The goal is a bank on which a **low** anti-proxy correlation is *achievable in principle*, so that a
future (separately authorized) run turns the v0.7 §7 gauntlet into a real test of the descriptor rather
than a measurement of the bank's built-in entanglement — **while keeping the frozen v0.7 descriptor and
validity logic intact.** This plan predeclares **no** expected verdict and forbids tuning toward one.

## 4. Candidate fixture classes (conceptual only)

Each class is described by **what it holds fixed** and **what it varies**, and by **which entanglement
axis it is meant to break**. No generator code, parameters, counts, or numeric ranges are fixed here;
those belong to a later, separately authorized implementation slice.

- **A. Coherent winding with varied chroma magnitude.** Same planted winding trajectory (same `u(t)`
  direction sequence and signed-turn structure), different amplitude envelopes `A(t)` (e.g. constant-high,
  constant-low, ramped, amplitude-modulated). Because `S` is magnitude-normalized, `S` should stay high
  across the envelope while `CHROMA magnitude` and `delta_rms` vary widely — driving `Spearman(S,
  chroma_mag)` and `Spearman(S, delta_rms)` toward zero. **Breaks: magnitude ↔ winding.**
- **B. Coherent winding with varied spectral spread.** Preserve coherent signed-turn winding while
  changing the temporal frequency mixture — angular-velocity jitter, multi-harmonic modulation,
  non-uniform winding rate — so the trajectory is **not** identical to a single narrowband sinusoid. The
  aim is a family where winding coherence is held roughly constant while per-channel spectral spread spans
  a wide range. **Breaks: spectral-narrowness ↔ winding.**
- **C. Non-winding smooth chroma trajectories.** Smooth RG/BY paths (low directional `delta_rms` of
  `u(t)`) that do **not** complete coherent signed turns (back-and-forth arcs, oscillation with zero net
  winding). Smooth-but-non-winding should score **low** `S` despite smoothness. **Breaks: smoothness ↔
  winding.**
- **D. High-chroma structureless trajectories.** High chroma magnitude without coherent winding
  (independent, broadband RG/BY). Generalizes the existing single high-chroma structureless control into
  a **family across magnitudes**, so magnitude alone never predicts `S`. **Breaks: magnitude ↔ winding
  (from the structureless side).**
- **E. Spectrally narrow non-winding trajectories.** Narrowband RG/BY movement (low per-channel spectral
  spread) **without** coherent rotation — e.g. one-dimensional / collinear oscillation along a fixed chroma axis, or another predeclared narrowband construction that is first verified as non-winding by its signed-turn structure. Independent same-frequency phase offsets must not be assumed non-winding, because they can form coherent ellipses. This is the pivotal decorrelator for the v0.8 confound: it
  supplies "narrowband **and** low-`S`" points, so spectral narrowness stops predicting `S`. **Breaks:
  spectral-narrowness ↔ winding (from the non-winding side).**
- **F. Winding with centroid / spread perturbations.** Planted winding held fixed while BY/RG **centroid**
  (mean hue axis, per-channel spectral centroid) and per-channel **spread** are perturbed, to test whether
  centroid / spread variants — including their null-relative (`nr_`) forms — can be moved **without**
  changing planted winding coherence. **Breaks: centroid / spread ↔ winding.**
- **G. Null-pair fixtures.** For **each** planted fixture, predeclare what its **trajectory-order-permuted
  null** must **preserve** (the multiset of `u(t)` directions and `CHROMA(t)` values; each per-sample
  marginal) and **destroy** (temporal ordering, hence coherent signed-turn winding). These paired nulls
  are the baseline for both the primary gate and the **null-relative** anti-proxy statistics. This class
  introduces **no new null *type*** (a new null design is Direction B and out of scope here); it only makes
  the existing per-fixture null construction explicit.
- **H. Neutral / chroma-floor fixtures.** Grayscale, chroma collapse (saturation → 0), low-saturation
  neutral (below `CHROMA_GATE_FLOOR`), luminance-only roughness, roughness-matched color-vs-luminance, and
  near-floor cases. These must remain **NEUTRAL or `≤ NEUTRAL_STRUCTURE_CEIL`**. Carried forward unchanged
  from v0.7 / v0.8 and, as corrected in v0.8, kept **out** of the anti-proxy correlation bank (they are
  covered by the separate neutral-ceiling gate). **Confirms: floor/neutral handling is undisturbed.**

Intended pooled effect: A + B populate "high-`S`" across wide magnitude and spectral ranges; C + D + E
populate "low-`S`" across smooth, high-chroma, and narrowband regimes respectively; F stresses the
centroid / spread axis directly; G fixes the paired baselines; H holds the floor. Together they are meant
to make each entanglement axis vary **independently of winding** across the bank.

## 5. Acceptance intent (not thresholds)

This plan **invents no new numeric thresholds** and freezes none. The frozen v0.7 constants
(`STRUCTURE_BEAT_MARGIN`, `MAGNITUDE_CORR_CEIL`, `PSC_FLOOR`, `AIC_FLOOR`, `NEUTRAL_STRUCTURE_CEIL`) and
the §8 pass/HOLD/FAIL logic remain the only acceptance surface, unchanged.

The **intent** to be tested by a later, separately authorized implementation slice is: *on a bank
containing classes A–H, can the frozen v0.7 anti-proxy Spearman correlations be brought below the frozen
`MAGNITUDE_CORR_CEIL` for `chroma magnitude`, `delta_rms`, per-channel `spectral spread / centroid`, and
their null-relative versions — **without any change to `PSC / AIC / S`** — while the in-scope rotations
still beat their trajectory-order-permuted, continuity, and structureless controls?* If yes, the
anti-proxy gate becomes informative and the descriptor's structure-sensitivity can be re-examined under
the existing rules. If the descriptor still tracks magnitude / spectrum on a **genuinely decorrelated**
bank, that is the evidence v0.9 said would escalate to Direction C (descriptor redesign), not a reason to
weaken the gate. No verdict is predeclared and no tuning toward one is permitted.

## 6. Risks and how the later plan must guard against them

- **Fixtures too artificial.** A bank so synthetic it resembles no plausible chroma trajectory can pass
  while telling us nothing transferable; natural / local-clip evaluation is a strictly later step. The
  implementation slice must document each fixture's construction and keep it physically plausible.
- **Hiding the proxy rather than separating it.** Numerically shrinking a correlation by compressing an
  axis's range (e.g. narrowing the magnitude span) is *defining the confound away*. The bank must **widen
  and independently span** each axis, not compress it — decorrelation by variation, never by omission.
- **Changing the descriptor by fixture design.** Selecting or tuning fixtures by watching `S` outcomes is
  covert descriptor change. The descriptor and its constants stay frozen; fixtures must be specified from
  their generative definition, **not** chosen because they make `S` behave.
- **Making anti-proxy "easier" by deleting hard cases.** Dropping the high-chroma structureless,
  continuity, or narrowband controls to obtain a clean gate is forbidden. Hard cases must be **retained
  and expanded** (classes C, D, E exist precisely to make the gate harder, not easier).
- **Accidentally implying temporal-order validity.** The trajectory-order-permuted null is a **structure**
  control; winding coherence is **not** temporal-order sensitivity. No fixture, null, or result in this
  arc may be read as evidence the descriptor is order-specific. `temporal_claim_allowed` stays **False**.
- **Bank imbalance / correlation-by-construction.** Unequal class sizes let one class dominate the pooled
  Spearman. The implementation slice must predeclare class balance and composition so a low correlation
  reflects decorrelation, not sampling.

## 7. Strict non-claims (unchanged)

This planning slice does **not**, and no future slice it describes may without separate authorization:

- establish any **descriptor-control validity** claim (anti-proxy remains unmet; verdict stays HOLD),
- make any **temporal-order** claim (`temporal_claim_allowed` stays False),
- make any **vision** claim,
- make any **"Brainvision sees"** claim,
- perform any **real-clip / local-clip** move (the offline local-clip manifest is a strictly later step
  and must not start until the synthetic anti-proxy entanglement is understood),
- perform any **runtime integration**,
- make any **`torment_service/` / service-path** contact,
- make any **memory / prompt / context / action / render-body / autonomy** contact,
- authorize any **code** (no fixtures implemented, no tests written, no formulas changed, no existing
  diagnostic modified).

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

## 8. Recommended next

- **Codex review** of this predeclaration — specifically whether classes A–H cover the v0.8 entanglement
  axes (magnitude, `delta_rms`, per-channel spectral spread / centroid, null-relative variants) and
  whether the §6 guardrails are sufficient to prevent decorrelation-by-omission or covert descriptor
  change.
- **If the operator explicitly opens a later implementation slice,** that slice may specify concrete
  generators, parameters, counts, and balance for classes A–H and run them through the **unchanged**
  frozen v0.7 descriptor and §7/§8 gauntlet — no formula change, no threshold invention, no tuning toward
  a verdict. **Otherwise HOLD.** Directions B (null-relative anti-proxy redesign) and C (descriptor
  redesign) remain recorded but unopened.

*End — TORMENT Brainvision Color Structure Fixture-Bank Redirection Plan v1.0. Docs-only, non-authorizing.
Opens no implementation lane; implements no fixture; writes no test; changes no frozen formula; no `§0`
pointer added; no tags.*
