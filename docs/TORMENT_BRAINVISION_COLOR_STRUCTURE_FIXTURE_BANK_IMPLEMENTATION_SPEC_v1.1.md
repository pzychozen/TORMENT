# TORMENT Brainvision Color Structure Fixture-Bank Implementation Spec v1.1

## 1. Status / quarantine and non-claims

**DOCS-ONLY planning slice. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** This note follows the v1.0 fixture-bank redirection plan (`cdb405c`) and
**predeclares concrete implementation requirements** for the future synthetic fixture bank so the later
implementation slice is **reviewable before any code exists**. It **authorizes no code, writes no tests,
changes no formula, and modifies no existing diagnostic.** The frozen v0.7 descriptor (`dc0ffec`) — chroma
gate + NEUTRAL, unit direction `u(t)`, signed turn `c(t)`, `PSC`, bias-corrected `AIC`,
`S = sqrt(PSC·AIC)`, the component-floor gate, and the §7/§8 anti-proxy gauntlet and pass/HOLD/FAIL logic —
stays **untouched**, along with its constants (`CHROMA_GATE_FLOOR`, `MIN_VALID_PAIRS`,
`MIN_VALID_FRACTION`, `STRUCTURE_BEAT_MARGIN`, `NEUTRAL_STRUCTURE_CEIL`, `PSC_FLOOR`, `AIC_FLOOR`,
`MAGNITUDE_CORR_CEIL`). Everything remains offline under `research/brainvision/` + `tests/research/`, HELD
per v0.6.

- **Current edge:** `cdb405c`.
- v0.8 / v0.9 / v1.0 remain **HOLD**.
- `first_pass_structure_validity_claim_allowed = False`; `temporal_claim_allowed = False`.
- **No descriptor-control validity claim; no vision claim; no "Brainvision sees" claim.**
- **No real-clip / local-clip move.**
- **No implementation is authorized by v1.1.** **No `§0` pointer; no tags.**

## 2. Scope of v1.1

v1.0 defined the fixture classes conceptually. v1.1 turns each class into a **reviewable requirements
contract**: role, invariants, variation axes, the proxy it must decorrelate, what it must **not** imply,
and what would **invalidate** it — plus bank-level balance, null construction, reporting, and honest
invalid-outcome rules. It fixes **no** generator code, seeds, counts, or numeric ranges; those are the
deliverable of a **separately authorized** later implementation slice, which must conform to this
contract. Nothing here changes the descriptor or invents a threshold; the only acceptance surface remains
the unchanged v0.7 §8 logic and its frozen constants.

## 3. Per-class implementation requirements (A–H)

Each class states: **role · hold fixed · must vary · proxy axis decorrelated · must not imply · what
invalidates it.**

### A. Coherent winding with varied chroma magnitude
- **Role.** Supply high-`S` points across a wide chroma-magnitude range so magnitude cannot predict `S`.
- **Hold fixed.** The planted winding trajectory — the `u(t)` direction sequence and its coherent
  same-sign signed-turn structure `c(t)` (so intended `PSC` / `AIC` stay high).
- **Must vary.** The amplitude envelope `A(t)`: median `CHROMA(t)` and its `delta_rms` (constant-high,
  constant-low, ramped, amplitude-modulated).
- **Decorrelates.** `CHROMA magnitude` and `delta_rms` vs `S`.
- **Must not imply.** That magnitude drives structure; that amplitude modulation is temporal-order
  structure.
- **Invalidates if.** Changing `A(t)` alters the signed-turn sign pattern (i.e. changes winding), or the
  envelope silently drops samples below `CHROMA_GATE_FLOOR` (turning valid pairs NEUTRAL and confounding
  the magnitude axis with the gate).

### B. Coherent winding with varied spectral spread
- **Role.** Supply high-`S` points across a wide per-channel spectral-spread range so narrowbandness
  cannot predict `S`.
- **Hold fixed.** Coherent signed-turn winding (net winding; sign-consistency of `c(t)`).
- **Must vary.** Temporal frequency content — angular-velocity jitter, multi-harmonic modulation,
  non-uniform winding rate — so per-channel spectral spread / centroid span a wide range.
- **Decorrelates.** `RG/BY spectral spread` (and centroid) vs `S`.
- **Must not imply.** That a broadband winder is "more real"; any temporal-order reading of frequency
  content.
- **Invalidates if.** The broadening actually breaks winding coherence (net winding becomes
  back-and-forth) — then reclassify to C/E; or jitter is large enough to collapse `PSC`, so it is no
  longer a coherent-winding fixture.

### C. Non-winding smooth chroma trajectories
- **Role.** Supply low-`S` points that are directionally smooth, separating smoothness from winding.
- **Hold fixed.** Smoothness — low directional `delta_rms of u(t)`.
- **Must vary.** The smooth non-winding path shape (back-and-forth arcs, zero-net-winding oscillation),
  across magnitude / spread where feasible.
- **Decorrelates.** `directional delta_rms of u(t)` vs `S` (smooth yet low-`S`).
- **Must not imply.** That smoothness is neutral (it is a distinct live control, not a floor case); any
  temporal claim.
- **Invalidates if.** The path accrues net coherent winding (consistent nonzero `Σc`) — then it is not
  non-winding; or it collapses below the chroma floor — then it is a neutral case, not a smooth
  non-winder.

### D. High-chroma structureless trajectories
- **Role.** Supply low-`S` points at high chroma magnitude (a **family across magnitudes**), from the
  structureless side, paired against A.
- **Hold fixed.** Absence of coherent winding (independent, broadband RG/BY; no joint structure).
- **Must vary.** Chroma magnitude across a wide range that **overlaps class A's** magnitude span.
- **Decorrelates.** `CHROMA magnitude` vs `S` (the low-`S` counterpart to A over the same range).
- **Must not imply.** Anything about winding; it is a **live control, not a null**.
- **Invalidates if.** The independence generator produces spurious coherent-winding runs (nonzero
  consistent `Σc`) — a structural leak; or its magnitude range fails to overlap A's, so magnitude cannot
  be decorrelated.

### E. Spectrally narrow non-winding trajectories
- **Role.** The pivotal decorrelator — low-`S` points at low spectral spread (narrowband), breaking the
  v0.8 "narrowband ⇒ winding" confound; paired against B.
- **Hold fixed.** Spectral narrowness (low per-channel spectral spread).
- **Must vary.** The narrowband non-winding construction — one-dimensional / collinear oscillation along
  a fixed chroma axis, or another **predeclared** narrowband construction — each **verified non-winding by
  its signed-turn structure before inclusion**.
- **Decorrelates.** `RG/BY spectral spread` / centroid vs `S` (narrowband yet low-`S`).
- **Must not imply.** That narrowbandness is winding. **Independent same-frequency phase offsets must not
  be assumed non-winding — they can form coherent ellipses;** every E fixture must be confirmed
  non-winding by its `c(t)` signed-turn structure.
- **Invalidates if.** The fixture actually winds (nonzero coherent `Σc`) — invalid, or reclassify to A/B;
  or it is not actually narrowband — then it does not serve the axis.

### F. Winding with centroid / spread perturbations
- **Role.** Test whether centroid / spread — and their null-relative (`nr_`) variants — can be moved
  **without** changing planted winding.
- **Hold fixed.** Planted winding coherence (signed-turn sign pattern / net winding).
- **Must vary.** BY/RG per-channel **spectral centroid** and per-channel **spread** perturbations.
- **Decorrelates.** `by_centroid`, `rg_centroid`, `rg_spread`, `by_spread` and their `nr_` versions vs
  `S`.
- **Must not imply.** Any mean-hue or semantic color-axis claim (per v1.0: **centroid / spread only**);
  any temporal claim.
- **Invalidates if.** The perturbation changes winding coherence (re-coupling the axis to `S`), so the
  confound is not separated; or it pushes samples below the chroma floor (gate confound).

### G. Null-pair fixtures
- **Role.** The paired baseline for the primary gate **and** the null-relative anti-proxy statistics; not
  a live fixture family.
- **Hold fixed.** For **each** planted fixture: the multiset of `u(t)` directions and `CHROMA(t)` values,
  and each per-sample marginal.
- **Must vary.** **Only the temporal order** (a pure reordering / permutation), destroying adjacency and
  order of signed turns, hence coherent winding.
- **Decorrelates.** Provides the `nr_` baseline for every statistic — the check that `S` is not tracking
  a proxy the null already shares.
- **Must not imply.** It introduces **no new null type**; the trajectory-order permutation is a
  **structure** control, **not** temporal-order evidence.
- **Invalidates if.** The permutation changes the multiset or any marginal (not a pure reordering); or a
  draw accidentally reconstructs coherent winding — then the predeclared implementation spec must either mark that null draw invalid or use a predeclared fallback seed sequence with a fixed retry limit, reporting the retry; it must not redraw until a desired `S` outcome is obtained.

### H. Neutral / chroma-floor fixtures
- **Role.** Floor / neutral confirmation; must stay **NEUTRAL or `S <= NEUTRAL_STRUCTURE_CEIL`**;
  **excluded** from the anti-proxy correlation bank (handled by the separate neutral-ceiling gate).
- **Hold fixed.** Sub-structure / sub-floor character: grayscale, saturation collapse (→ 0),
  low-saturation neutral (below `CHROMA_GATE_FLOOR`), luminance-only roughness, roughness-matched
  color-vs-luminance.
- **Must vary.** The enumerated neutral regimes only — carried forward unchanged from v0.7 / v0.8.
- **Decorrelates.** None directly; confirms the neutral-ceiling gate and that luminance roughness does not
  cross-fire.
- **Must not imply.** Anything about winding or structure; it is **not** part of the anti-proxy
  correlation bank.
- **Invalidates if.** A neutral fixture scores above `NEUTRAL_STRUCTURE_CEIL` (a real leak to investigate,
  or a mis-specified fixture); or it is accidentally included in the anti-proxy correlation bank (the v0.8
  error, which spuriously inflates magnitude/std correlations).

## 4. Balance and anti-cherry-picking rules

- **No selecting fixtures after seeing `S`.** All fixtures and their generator parameters must be
  predeclared and frozen **before** any run. Adding, dropping, or reclassifying a fixture conditioned on
  its observed `S` is forbidden (the only allowed reclassification is the predeclared structural check —
  e.g. an E fixture found to wind — decided by its `c(t)` structure, not by `S`).
- **No deleting hard cases.** The continuity control, high-chroma structureless family (D), and
  narrowband non-winding family (E) must be **retained and expanded**, never removed to clean the gate.
- **No shrinking proxy ranges.** Each proxy axis (magnitude, `delta_rms`, spectral spread / centroid)
  must be **spanned widely**; narrowing a range to reduce a correlation is defining the confound away and
  is forbidden. Decorrelation must come from variation, never from omission.
- **No class-size imbalance.** Predeclare class counts so no single family dominates the pooled Spearman;
  composition must be balanced and stated up front.
- **Matched high-`S` / low-`S` families over shared ranges.** Where possible each high-`S` family has a
  matching low-`S` family across a similar proxy range — A ↔ D over chroma magnitude, B ↔ E over spectral
  spread — so each proxy range contains **both** high-`S` and low-`S` points.
- **Predeclared generator parameters.** Seeds, lengths, amplitude / frequency ranges, perturbation sizes,
  and per-class counts must be predeclared in the implementation slice's spec before execution; no
  post-hoc tuning.

## 5. Null construction requirements

For **every** planted fixture, its trajectory-order-permuted null must:

- **preserve** the multiset of `u(t)` samples and `CHROMA(t)` values (and each per-sample marginal);
- **destroy** the temporal adjacency / order of the signed turns (a pure reordering, so coherent winding
  is removed);
- **introduce no new null type** (a new null *design* is Direction B and is out of scope here);
- **not rely on the independent phase-randomized null as a gate** (for narrowband fixtures it can stay
  high — a coherent ellipse — as v0.8 confirmed);
- **keep the shared-phase and independent phase-randomized nulls reporting-only** unless separately
  re-frozen in a later, explicitly authorized slice.

## 6. Reporting requirements (for the future implementation)

The later implementation slice must report, without tuning toward any verdict:

- per-fixture `S`, `PSC`, `AIC`;
- the primary **trajectory-order-permuted null** score per fixture;
- reporting-only independent phase-randomized, independently permuted-BY, and shared-phase null scores,
  explicitly marked non-gating and non-rescuing;
- the continuity, high-chroma structureless, and neutral controls;
- the anti-proxy Spearman statistics using the **frozen v0.7 §7 names** (`CHROMA magnitude`, `RG std`,
  `BY std`, `delta_rms`, `spectral centroid / spread`, `directional delta_rms of u(t)`, `angular
  increment magnitude`, per-channel `RG/BY spectral centroid / spread`, and their `nr_` null-relative
  versions);
- class-level and **pooled** summaries;
- an **explicit HOLD / PASS / FAIL** per the **unchanged v0.7 §8 logic** (no new threshold, no reweighting).

## 7. Honest invalid / null outcomes

The implementation slice must state these outcomes plainly rather than engineer around them:

- **If high `S` only appears in narrowband rotations** (classes A/B degenerate back to the v0.8 regime),
  the result is **HOLD** — the bank did not decorrelate.
- **If low anti-proxy correlations are achieved by deleting hard cases** (dropping D, E, or the
  continuity / structureless controls), the run is **invalid** — decorrelation-by-omission, not a result.
- **If spectrally narrow non-winding fixtures (E) accidentally wind**, they are **invalid or reclassified**
  (by their `c(t)` structure, not by `S`); a bank whose decorrelation depends on mislabeled winders is
  invalid.
- **If the descriptor still tracks magnitude / spectrum on a genuinely decorrelated bank**, that
  **escalates to Direction C** (descriptor redesign) in a later slice — **not** threshold weakening or
  gate loosening.
- **If implementation requires changing `PSC / AIC / S`** (or any frozen constant), **stop and return to
  docs / review** — that is a formula-freeze change, out of scope for a fixture-bank slice.

## 8. Quarantine and non-claims (unchanged)

This planning slice does not authorize, and no future slice it describes may do without separate authorization:

- authorize any **code** (no fixtures implemented, no generators written);
- authorize any **tests**;
- make any **formula change** (descriptor, constants, or §7/§8 logic all frozen);
- perform any **runtime integration**;
- make any **`torment_service/` / service-path** contact;
- make any **memory / prompt / context / action / render-body / autonomy** contact;
- use any **real clips** (the offline local-clip manifest is a strictly later step, not started until the
  synthetic anti-proxy entanglement is understood);
- make any **temporal-order** claim (`temporal_claim_allowed` stays False);
- make any **vision** claim;
- make any **"Brainvision sees"** claim.

Brainvision remains **offline / quarantined**, HELD per v0.6.
`first_pass_structure_validity_claim_allowed = False` and `temporal_claim_allowed = False` are unchanged.
**No `§0` pointer; no tags.**

## 9. Recommended next

- **Codex review** of this implementation spec — whether the A–H contracts (roles, invariants, variation
  axes, decorrelation targets, invalidation conditions) plus the §4 balance rules, §5 null requirements,
  §6 reporting, and §7 invalid-outcome rules are sufficient to make a later implementation reviewable and
  to prevent decorrelation-by-omission or covert descriptor change.
- **If the operator explicitly opens a later implementation slice,** that slice may specify concrete
  generators, seeds, counts, ranges, and balance conforming to this contract, and run them through the
  **unchanged** frozen v0.7 descriptor and §7/§8 gauntlet — no formula change, no threshold invention, no
  tuning toward a verdict. **Otherwise HOLD.** Directions B (null-relative anti-proxy redesign) and C
  (descriptor redesign) remain recorded but unopened.

*End — TORMENT Brainvision Color Structure Fixture-Bank Implementation Spec v1.1. Docs-only,
non-authorizing. Opens no implementation lane; implements no fixture; writes no test; changes no frozen
formula; no `§0` pointer added; no tags.*
