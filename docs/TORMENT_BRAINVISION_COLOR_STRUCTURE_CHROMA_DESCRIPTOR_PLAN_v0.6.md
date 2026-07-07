# TORMENT Brainvision Color Structure-Chroma Descriptor Definition Plan v0.6

## 1. Status / quarantine and non-claims

**DOCS-ONLY definition plan. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** It **freezes**, before any code, the definition of the structure-sensitive chroma
descriptor, its chroma gate, its nulls/controls, its anti-proxy checks, and its pass/fail/HOLD logic — so a
later slice is judged against criteria fixed in advance. It implements no descriptor, no diagnostic, no code,
and no tests, and touches no `torment_service/`, runtime, camera / sensor / live-capture / screen-capture /
streaming, or prompt / context / memory / action / render-body / autonomy paths. **No `§0` pointer; no tags.**
Everything stays offline under `research/brainvision/` + `tests/research/`, HELD per v0.6. **This plan makes no
vision claim, no "Brainvision sees" claim, and no temporal-order claim.** `temporal_claim_allowed` remains
**False**. **No implementation is authorized.**

## 2. v0.4 / v0.5 state

- v0.4 showed the current **per-channel temporal-std** RG/BY responses are **spectrum-limited**: they equal the
  amplitude spectrum (Parseval), are phase-invariant, and score **exactly 1.00** against a spectrum-matched null
  that independently phase-randomizes RG and BY. Full descriptor-control validity is **HOLD**.
- v0.5 selected the next candidate: a **chroma-plane joint-trajectory structure** descriptor, with hue-angle
  quantities only as chroma-gated readouts, the **independent RG/BY phase-randomized null as the gate target**,
  the **shared-phase null reporting-only**, and RG/BY joint phase coherence only as a non-rescuing secondary
  check.
- Descriptor-control validity remains **HOLD**; this plan defines (not builds) the descriptor that a future
  slice would test.

## 3. Primary descriptor definition (frozen for later implementation)

**Inputs.** Per-frame spatial-mean series `RG(t)`, `BY(t)`, and `CHROMA(t) = sqrt(RG(t)^2 + BY(t)^2)`, for
`t = 0 .. T-1` (the v0.3 bridge descriptors; no new channel).

**Chroma gate.** A sample `t` is **valid** iff `CHROMA(t) >= CHROMA_GATE_FLOOR`. Below-floor samples are
neutralized: they are excluded from all direction/angle statistics and contribute no structure. If the valid
fraction is below `MIN_VALID_FRACTION`, the descriptor returns **NEUTRAL** (no structure), never a spurious
value. All angle-based quantities are computed only on valid consecutive pairs.

**Primary claim surface — magnitude-normalized chroma-plane joint-trajectory structure `S`.** The claim rests on
the **plane geometry of the trajectory `(RG(t), BY(t))`, normalized to unit chroma direction**
`u(t) = (RG(t), BY(t)) / CHROMA(t)` on valid samples, compared against the nulls/controls of §5 — **not** on any
single raw hue number. Magnitude normalization is deliberate: it reduces direct CHROMA magnitude dependence, but does not by
itself eliminate magnitude, smoothness, sampling, or per-channel spectral proxies; those must be tested by the
anti-proxy gates in §6. `S` is a predeclared
combination of the components in §4 in which **each required component must independently clear its floor** (so a
case passing one component via a proxy does not pass overall).

**Hue-angle quantities are readouts only.** `θ(t) = atan2(BY(t), RG(t))` and its wrapped increments may be
reported as chroma-gated readouts that corroborate `S`, but **no validity claim rests on a hue statistic alone**
(hue is unstable near low chroma — §7).

**No vague "continuity."** The plan does **not** use an unqualified "continuity" score. Any smoothness-flavored
component is admissible only if it is (a) magnitude-normalized, and (b) predeclared to be tested against the
**smooth / spectrum-matched continuity control** (§5) — i.e. it must be shown to beat a smooth-but-jointly-
structureless signal, or it is rejected as a smoothness/spectrum proxy.

## 4. Candidate measurable components (frozen list; exact weights predeclared before running)

The primary `S` is composed from these; the plan freezes which are **required** vs **reported**. This plan
freezes the required component **classes, not the formulas**; a later docs-only formula freeze is required before
code (the "e.g." descriptions below are illustrative candidates, not frozen formulas).

- **Path/scatter contrast (required, primary geometry):** a magnitude-normalized contrast between an ordered
  low-dimensional locus (line or arc) and an isotropic 2-D scatter of the same directions — e.g. confinement of
  `u(t)` to a 1-D locus and/or net directed advance vs total path. This is the primary plane-geometry surface.
- **Angular-increment consistency (required, chroma-gated readout+component):** concentration (mean resultant
  length) of wrapped hue increments `Δθ` over valid consecutive pairs — high for steady winding, low for erratic
  angle. Reported as a readout and used as a required component; never the sole claim. Angular-increment
  consistency is valid only for rotation-like fixtures in the first slice; it must not be used to claim
  collinear phase-locked chroma structure.
- **Loop / trajectory coherence (reported):** signed net winding and/or enclosed-area-to-path ratio, to separate
  a coherently winding path (rotation regime) from a back-and-forth wander.
- **Joint phase / path coherence (reported):** how well `(RG,BY)` is described by a coherent structured phasor
  vs an incoherent one.
- **RG/BY phase-coherence companion (optional, NON-RESCUING secondary):** cross-channel coherence/PLV of RG and
  BY, reported only as a secondary check on the same chroma-plane relationship; **it cannot create a pass path or
  rescue a failed primary** `S`.

The first slice would freeze the **required** set to {path/scatter contrast, angular-increment consistency},
combined so both must clear their floors; the rest are reported. **First-slice claim scope is rotation-like
chroma-plane trajectories only. Collinear RG/BY phase-locked changes are reported as out-of-scope unless a
separate collinear component is predeclared.**

## 5. Nulls and controls (predeclared)

- **Independent RG/BY phase-randomized null — GATE TARGET, must be beaten.** Y′ held; RG and BY independently
  phase-randomized (amplitude spectra preserved). This is the null that destroys joint structure; `S` must beat
  it.
- **Shared-phase null — REPORTING-ONLY.** RG and BY share one random phase set (a shared phase relation by
  construction); predeclared **not** required to be beaten (it retains structure).
- **grayscale** and **saturation_collapse** — chroma removed/collapsed; `S` must fall to baseline (no chroma → no
  structure).
- **low_saturation_neutral** — chroma below the gate floor; must be handled as NEUTRAL, not spurious structure.
- **rough_luminance_only_null** and **roughness_matched_color_vs_luminance_pair** — carry the G5a cross-channel
  roughness immunity forward (rough luminance and matched roughness must not create structure/cross-fire).
- **smooth / spectrum-matched continuity control** — a smooth but **jointly structureless** signal (e.g. two
  independent smooth/low-pass RG,BY, or a spectrum-matched surrogate); `S` must beat it, or `S` is a
  smoothness/spectrum proxy. The exact generator/null construction for this control must be frozen in a separate
  plan or in this plan before implementation; otherwise the anti-smoothness gate is not auditable.
- **high-chroma structureless control** — high CHROMA magnitude but no joint structure (the independent null
  itself is one such case); `S` must NOT fire, proving `S` is not a magnitude proxy.

## 6. Anti-proxy checks (predeclared; high correlation blocks validity)

Across the fixture/control bank, report and gate the correlation between `S` and each of:

- **CHROMA magnitude** (mean/median chroma level);
- **RG std** and **BY std** (per-channel temporal std);
- **delta_rms** (temporal roughness);
- **spectral centroid / spread** (frequency content).

Each `|correlation|` must stay below `MAGNITUDE_CORR_CEIL` (or its per-statistic named ceiling). **Any high
correlation above the frozen ceiling blocks validity**, even if the primary margin is met — because it means `S`
is tracking magnitude/roughness/spectrum rather than joint structure.

## 7. Pass / fail / HOLD logic (predeclared; named margins frozen before running)

Named constants (`CHROMA_GATE_FLOOR`, `MIN_VALID_FRACTION`, `STRUCTURE_BEAT_MARGIN`, `NEUTRAL_STRUCTURE_CEIL`,
`MAGNITUDE_CORR_CEIL`) are fixed before any run and never tuned after.

A future slice may make a **first-pass structure-sensitive descriptor-control validity** statement (still
offline, still not vision) only if **all** hold:

- **Primary over the independent null:** active joint-structure fixtures beat their **independent** null by
  `STRUCTURE_BEAT_MARGIN`, across a predeclared majority of in-scope rotation-like fixtures, with every required
  component clearing its floor; out-of-scope regimes cannot contribute to PASS (no single-fixture pass).
- **Beats the continuity + structureless controls:** `S(intended)` beats the smooth/spectrum-matched continuity
  control and the high-chroma structureless control by the same margin (proves not a smoothness/magnitude proxy).
- **Neutral controls stay low:** grayscale, saturation_collapse, low_saturation_neutral yield `S <=
  NEUTRAL_STRUCTURE_CEIL`.
- **Anti-proxy clean:** all §6 correlations below their ceilings.
- **Secondary is non-rescuing:** the RG/BY phase-coherence companion is reported only; it cannot flip a failed
  primary; the shared-phase null is reporting-only.

Otherwise the verdict is **HOLD** (validity not established) — or **FAIL** if `S(intended)` does not exceed the
independent null at all. In all cases: **no temporal-order claim; no vision claim;** `temporal_claim_allowed`
stays False.

## 8. Expected output tables (predeclared schemas — shapes fixed before implementation)

Placeholders `·`; no results exist yet.

**T1 — per-fixture S vs nulls/controls:**

| fixture | S_intended | S_independent_null | beats_by_margin? | S_shared_phase (report) | S_continuity_ctrl |
| --- | --- | --- | --- | --- | --- |
| (active + control fixtures) | · | · | Y/n | · | · |

**T2 — neutral / gate handling:**

| control | valid_fraction | S | neutral? |
| --- | --- | --- | --- |
| grayscale / saturation_collapse / low_saturation_neutral | · | · | Y/n |

**T3 — anti-proxy correlations:**

| statistic | corr(S, stat) | ceiling | ok? |
| --- | --- | --- | --- |
| CHROMA_mag / RG_std / BY_std / delta_rms / spectral_centroid | · | `MAGNITUDE_CORR_CEIL` | Y/n |

**T4 — gate summary:** primary-beats-null, beats-continuity, beats-structureless, neutral-low, anti-proxy-clean,
secondary-non-rescuing → overall PASS / HOLD / FAIL, plus `first_pass_structure_validity_claim_allowed` and
`temporal_claim_allowed` (always False here).

## 9. Risks / reasons to HOLD

- **Hue instability near low chroma.** `atan2` is undefined/noisy as chroma → 0; the chroma gate and
  `MIN_VALID_FRACTION` mitigate this, but low-chroma fixtures could still distort angle-based components.
- **Circular-statistics misuse.** Resultant-length bias, wrapping, and small-sample non-uniformity can fake
  concentration; every circular measure must be predeclared with its bias handling.
- **Path score becoming a smoothness/spectrum proxy.** The deepest risk: a "path/scatter" or angular component
  could reduce to per-channel smoothness/spectrum and re-inherit the v0.4 failure. The smooth/spectrum-matched
  continuity control and the §6 anti-proxy correlations exist precisely to expose this; if they are not cleanly
  passed, the verdict is HOLD.
- **Phase-randomized null ambiguity.** Independent vs shared-phase nulls behave oppositely; on short synthetic
  sequences phase randomization is ill-conditioned. The null construction must be predeclared and reported.
- **Single-regime scope.** A single scalar may not capture rotation and collinear joint structure at once;
  restricting the first-slice claim to a well-defined regime is preferred over an over-general claim that quietly
  fails a regime.
- **Overfitting synthetic controls / real clips still required.** Passing hand-built synthetic controls is
  necessary but not sufficient; the offline gitignored clip corpus remains the eventual test where luminance and
  color actually correlate.

**Recommended posture: HOLD for review.** This freezes a genuinely new descriptor family's definition; before
any code, Codex / operator should confirm the required-component set (§4), the continuity + structureless
controls (§5), and the anti-proxy ceilings (§6), which are where a real chroma-structure descriptor could still
turn out to be a proxy.

## 10. Non-claims and quarantine boundaries

This plan does **not**: build or select a descriptor; implement any component, null, or diagnostic; claim vision,
"Brainvision sees", object/scene understanding, temporal-order sensitivity, or classifier superiority; or
authorize any tuning. It adds no runtime integration, no live/screen capture, no service / camera / sensor
contact, and no prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no
tags.** Brainvision remains offline research under `research/brainvision/` + `tests/research/`, HELD per v0.6,
with `temporal_claim_allowed` **False**. **No implementation is authorized.**

## 11. Recommended next

- **Codex review** of this definition — the required-component set and its floors, the magnitude-normalized
  primary surface, the continuity/structureless controls, and the anti-proxy ceilings.
- **If** accepted, a single offline research slice may write a final formula-freeze plan or, if formulas are
  added here, implement exactly the frozen formulas under
  `research/brainvision/` + `tests/research/`, with all named constants fixed before running, the independent
  null as the gate, the shared-phase null and the phase-coherence companion reporting-only, and the anti-proxy
  gauntlet enforced. **Otherwise HOLD.** No code, math, or tuning until reviewed.

*End — TORMENT Brainvision Color Structure-Chroma Descriptor Definition Plan v0.6. Docs-only, non-authorizing.
Opens no implementation lane; no `§0` pointer added; no tags.*
