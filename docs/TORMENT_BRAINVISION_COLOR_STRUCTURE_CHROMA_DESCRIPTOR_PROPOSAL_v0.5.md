# TORMENT Brainvision Color Structure-Sensitive Chroma Descriptor Proposal v0.5

## 1. Status / quarantine and non-claims

**DOCS-ONLY proposal. Non-authorizing, non-implementing. Opens no runtime, integration, or implementation
lane.** It defines — but does not build — a future **structure-sensitive chroma descriptor** family that could
detect RG/BY joint structure the current per-channel temporal-std descriptors cannot. It implements no
descriptor, no diagnostic, no code, and no tests, and touches no `torment_service/`, runtime, camera / sensor /
live-capture / screen-capture / streaming, or prompt / context / memory / action / render-body / autonomy
paths. **No `§0` pointer; no tags.** Everything stays offline under `research/brainvision/` + `tests/research/`,
HELD per v0.6. **This proposal makes no vision claim, no "Brainvision sees" claim, and no temporal-order
claim.** `temporal_claim_allowed` remains **False**. **No implementation is authorized.**

## 2. What v0.4 showed

The v0.4 faithful G5 diagnostic established (offline, on constructed synthetic fixtures):

- **G5a — cross-channel roughness immunity: PASS.** Rough luminance produces no chroma; a roughness-matched
  color-vs-luminance pair does not cross-fire; color response does not track roughness.
- **G5b — within-chroma spectrum immunity: FAIL.** Against a spectrum-matched null (Y′ held; RG and BY
  **independently** phase-randomized, each channel's amplitude spectrum preserved), the intended-vs-null response
  ratios for the active RG/BY channels are **exactly 1.00** on every fixture (0/4).
- **Per-channel temporal std is spectrum-explained.** A variance-like statistic equals the amplitude spectrum
  (Parseval) and is invariant to phase, so it cannot separate structured chroma from a spectrum-matched null.
- **Full descriptor-control validity remains HOLD**; `first_pass_descriptor_control_validity_claim_allowed =
  False`; `temporal_claim_allowed = False`.

The gap is precise: the v0.4 null destroys only the **joint RG–BY phase relationship**, leaving each channel's
marginal spectrum intact. Any descriptor that beats it must read that joint relationship, not per-channel
magnitude.

## 3. The missing target

The target is **not** more per-channel variance (the confounded quantity). It is a **chroma-plane joint-trajectory structure descriptor, with hue-angle quantities only as chroma-gated
readouts**: a quantity sensitive to how RG and BY co-vary over time — the path the
point `(RG(t), BY(t))` traces in the chroma plane, and equivalently the coherence of the hue angle `θ(t) =
atan2(BY, RG)` — rather than the marginal magnitudes of RG or BY. The decisive requirement, fixed by the v0.4
null construction, is that the descriptor must **distinguish intended RG/BY structure from an independently
phase-randomized RG/BY null**: independent phase randomization preserves each channel's spectrum but turns a
coherent chroma-plane path (e.g. a circle for a hue rotation) into an incoherent scatter, so a joint-structure
descriptor must be tested to score intended joint trajectories above the independent null; this is not assumed.

## 4. Candidate families (high-level; none specified, none built)

| family | what it reads | beats independent null? | main weakness |
| --- | --- | --- | --- |
| RG/BY joint phase coherence | cross-spectral coherence / phase-locking between RG(t) and BY(t) | yes — directly measures the fixed phase relation the null destroys | assumes frequency-matched/narrowband structure; less interpretable |
| hue-angle trajectory continuity | smoothness / coherent winding of `θ(t) = atan2(BY, RG)` | yes — coherent hue sweep vs erratic angle | **hue undefined/unstable near low chroma** |
| chroma-plane recurrence geometry | geometry of the `(RG,BY)` path (loop closure, enclosed area vs path length, recurrence) | yes — circle vs scatter | geometry estimators noisy at short length |
| circular hue statistics | circular concentration / resultant length of hue or its increments | yes — concentrated vs uniform | circular statistics easy to misuse |
| cross-channel phase-locking (PLV) | phase-locking value of the analytic phases of RG, BY | yes — high vs low PLV | narrowband assumption; analytic phase unstable at low amplitude |

All five are candidates to test against the **independent** null because all read the joint structure it destroys. None
should beat the **shared-phase** null (§6), which preserves the joint phase relationship — that is exactly why
the shared-phase variant is reporting-only.

## 5. Recommended first family (at most one)

**Recommended: a chroma-plane / hue-trajectory structure descriptor**, i.e. a measure of how coherently
`(RG(t), BY(t))` traces a path (with hue-angle continuity as its interpretable readout), **chroma-gated** so the
hue angle is only used where chroma exceeds a predeclared floor. Justification: it is the most directly
interpretable statement of "does the color sweep coherently," it generalizes beyond pure sinusoids (unlike a
narrowband coherence measure), and it targets exactly what the independent null destroys. Because its known
weakness is hue instability near low chroma, RG/BY joint phase coherence may be reported as a robustness companion only if defined as a secondary check on
the same chroma-plane relationship; it must not become a separate pass path or rescue a failed primary descriptor. Only the chroma-plane/hue family is
recommended for a first slice; phase coherence is a within-evaluation cross-check, not a second family to build.

## 6. Controls (predeclared)

- **Existing G5a controls** — rough_luminance_only_null, roughness_matched_color_vs_luminance_pair,
  roughness-correlation bank (carry the cross-channel roughness immunity forward).
- **v0.4 spectrum-matched null = independent RG/BY phase-randomized null** — Y′ held; RG and BY independently
  phase-randomized. This is the **primary null the structure descriptor must beat**.
- **Shared-phase variant — REPORTING-ONLY.** RG and BY share one random phase set, preserving a shared phase relation
  by construction; predeclared *not* to be beaten (it retains structure), so it is reported, never gated.
- **grayscale / saturation_collapse** — must drive the structure score to a baseline (no chroma → no
  structure).
- **hue_rotation_like fixture** — the canonical active structure fixture (coherent circular chroma-plane path).
- **low_saturation_neutral** — must be handled as neutral: chroma below the gate floor yields no structure
  score, not a spurious one.

## 7. Success / failure criteria (proposal level; thresholds to be predeclared before any run)

Named margins (`STRUCTURE_BEAT_MARGIN`, `NEUTRAL_STRUCTURE_CEIL`, `MAGNITUDE_CORR_CEIL`, `CHROMA_GATE_FLOOR`)
would be frozen before running. No pass may rest on a single favorable fixture.

- **Structure over the independent null:** active hue/chroma-trajectory fixtures beat their **independent**
  spectrum-matched nulls by `STRUCTURE_BEAT_MARGIN`, across a predeclared majority of fixtures — never hidden
  behind CHROMA magnitude or per-channel std.
- **No false structure from achromatic/neutral controls:** grayscale, saturation_collapse, and
  low_saturation_neutral yield structure ≤ `NEUTRAL_STRUCTURE_CEIL` (chroma-gated to neutral).
- **Not a magnitude/variance proxy:** the descriptor must NOT merely track CHROMA magnitude or per-channel std —
  a high-CHROMA-magnitude but joint-structureless case (the independent null itself) must score low, and the
  correlation between the structure score and CHROMA magnitude across fixtures must stay below
  `MAGNITUDE_CORR_CEIL`. The descriptor must also beat smooth/spectrum-matched continuity controls and report
  correlation with CHROMA magnitude, RG/BY per-channel std, delta_rms, and spectral centroid; any high
  correlation above the frozen ceiling blocks validity.
- **Shared-phase reporting only:** the shared-phase null is reported, not required to be beaten.
- **No single-fixture pass; no temporal-order claim.** Majority required; temporal controls (if reported at all)
  remain reporting-only and `temporal_claim_allowed` stays False.

Only if all of the above hold across the predeclared fixture set could a future slice make a **first-pass
structure-sensitive descriptor-control validity** statement — still offline, still not a vision claim.

## 8. Risks / reasons to HOLD

- **Hue is unstable near low chroma.** `atan2(BY, RG)` is undefined/noisy as chroma → 0, so the descriptor must
  be chroma-gated; low-chroma fixtures could otherwise manufacture or destroy apparent structure.
- **Circular statistics are easy to misuse.** Wrapping, bias in resultant-length estimates, and non-uniformity
  artifacts can fake concentration; any circular measure must be predeclared with its bias handling.
- **Phase-randomized null construction matters.** Independent vs shared-phase nulls behave oppositely (§6), and
  on short synthetic sequences phase randomization is ill-conditioned (the v0.4 risk carries over); the null
  must genuinely destroy joint structure without introducing artifacts.
- **It may become another spectrum/continuity proxy.** A hue-trajectory "continuity" measure could secretly
  reduce to per-channel smoothness/spectrum and re-inherit the v0.4 failure; the descriptor must be shown to
  beat the independent null *because of joint phase*, not because it re-derived a magnitude/continuity quantity.
  This is the deepest risk and the main reason to HOLD before building.
- **Real clips still required later.** Even a full synthetic pass would be descriptor-control validity on
  constructed fixtures, not natural-video evidence; the offline gitignored clip corpus remains the eventual
  test.

**Recommended posture: HOLD for review.** This is a genuinely new descriptor family; before any code, Codex /
operator should confirm the family choice (§5), the independent-vs-shared-phase null logic (§6), and the
"not a magnitude/continuity proxy" criterion (§7), which is where the whole idea could quietly fail.

## 9. Non-claims and quarantine boundaries

This proposal does **not**: build or select a descriptor; implement any diagnostic; claim vision, "Brainvision
sees", object/scene understanding, temporal-order sensitivity, or classifier superiority; or authorize any
tuning. It adds no runtime integration, no live/screen capture, no service / camera / sensor contact, and no
prompt / context / memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.** Brainvision
remains offline research under `research/brainvision/` + `tests/research/`, HELD per v0.6, with
`temporal_claim_allowed` **False**. **No implementation is authorized.**

## 10. Recommended next

- **Codex review** of this proposal — the recommended chroma-plane/hue-trajectory family, the
  chroma-gating, the independent-vs-shared-phase null distinction, and especially the anti-proxy criterion.
- **If** accepted, a future docs-only **v0.6 plan** may propose and freeze the descriptor definition, the chroma gate, the
  fixtures/controls, and the named margins before any implementation — with the shared-phase null reporting-only
  and the independent null as the gate. **Otherwise HOLD.** No code, math, or tuning until reviewed.

*End — TORMENT Brainvision Color Structure-Sensitive Chroma Descriptor Proposal v0.5. Docs-only, non-authorizing.
Opens no implementation lane; no `§0` pointer added; no tags.*
