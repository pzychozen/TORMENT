# TORMENT Brainvision Order-Sensitive Recurrence Plan v1.2a

## 1. Status / quarantine

**DOCS-ONLY predeclared test plan. Non-authorizing, non-implementing. Opens no runtime, integration, or
implementation lane.** This note turns **one** family from the v1.2 proposal into a concrete plan whose
controls, thresholds, and expected output-table shapes are **fixed in advance, before any code is written and
before any real-clip inspection**. It implements no code, adds no operator, changes no tests, and touches no
`torment_service/`, runtime, camera / sensor / live-capture, or prompt / context / memory / action /
render-body / autonomy paths. **No `§0` pointer; no tags.** Everything stays offline under
`research/brainvision/` + `tests/research/`, HELD per v0.6. **This note makes no temporal-order claim**; it
defines what a *future* offline slice would have to show. `temporal_claim_allowed` remains **False**.

## 2. Scope: exactly one family

Of the four families surveyed in the v1.2 proposal, this plan selects **only the recurrence-structure /
continuity family** (recurrence-quantification-style diagonal and continuity statistics). The predictability,
lagged-dependence, and phase-structure families are **out of scope** for v1.2a and are not planned here. The
plan concerns a single future slice that would build at most this one family, offline, judged against the
criteria below.

## 3. What the statistic family should reward

The family reads the **temporal-sequence topology** of the descriptor field, not its amplitude. Conceptually,
a recurrence is registered when two time points' descriptor states fall within a predeclared closeness
threshold; the collection of recurrences forms a recurrence structure whose **diagonal** runs correspond to
the trajectory revisiting a *sequence* of states in the same order, and whose **vertical/continuity** runs
correspond to the trajectory dwelling in a region.

The statistic family should therefore reward:

- **Determinism (DET)** — the fraction of recurrent points that lie on diagonal lines of length ≥ a
  predeclared minimum. High DET means recurrences come in ordered sequences (continuity/recurrence of order);
  a shuffled series scatters recurrences into isolated points, collapsing DET. **DET is the primary statistic.**
- **Mean / max diagonal line length (L, Lmax)** and **diagonal-length entropy (ENTR)** — secondary,
  reported-but-not-gating descriptors of how long ordered sequences persist.
- **Laminarity (LAM) / trapping time (TT)** — secondary continuity descriptors (vertical structure).

The **recurrence rate (RR)** — the overall density of recurrences — is explicitly **not** an order statistic:
it reflects how the states populate space and is the quantity most exposed to roughness/spread. RR is held
fixed by construction (§4) and reported only as a control, never as evidence of order.

## 4. How it avoids roughness / spectral-spread confounding

Three predeclared layers, strongest first:

1. **Frame-level recurrence bounds RR against point-set changes (primary design choice).** For m = 1, with the
   same off-diagonal eligibility mask and threshold rule, a time shuffle only permutes rows/columns of the
   recurrence matrix; the off-diagonal recurrent-pair count and RR are permutation-invariant. Roughness cannot
   inflate RR through point-set changes, so any `true`-vs-`time_shuffled` difference must be tested in the
   diagonal/order structure (DET, L) rather than in recurrence density. This is a definitional defence against
   the v1.1 confound, not a tuned one. Delay embedding (m > 1) is an **optional secondary** probe only, because
   it reintroduces roughness sensitivity (delay vectors mix adjacent frames); it is not part of the primary
   Tier-A test.
2. **Recurrence-rate matching via a target-RR threshold rule.** The closeness threshold ε is **not** a free
   knob: it is set **per window** to achieve a predeclared target recurrence rate (RR_target), so all
   conditions and controls are compared at equal RR. This removes any residual density/roughness advantage even
   where m > 1 is used. The rule (target RR) is fixed before real-clip inspection; ε values are its output, not
   a tuned input.
3. **Surrogate normalization and dissociation probes (per v1.2 §4/§6).** DET is also reported as a standardized
   score against each window's own order-destroyed surrogates, and evaluated on predeclared **rough-but-ordered**
   and **smooth-but-disordered** probes that break the roughness↔order correlation directly. A measure that
   scores rough-but-ordered high and smooth-but-disordered low — and whose DET does not track a roughness
   statistic — is behaving as an order measure.

## 5. Predeclared design constants (fixed before any implementation or real-clip inspection)

- **Embedding:** primary **m = 1** (frame recurrence), delay τ = 1. Optional secondary m ∈ {2, 3} with τ = 1,
  reported separately and never used to make a Tier-A claim on its own.
- **Distance metric:** Euclidean distance in the per-window normalized descriptor state space (inheriting the
  v1.0 median/MAD normalization and near-flat neutral floor; near-flat windows are neutral and excluded, as in
  v1.0).
- **Threshold rule:** ε chosen per window to hit **RR_target = 0.10** (fixed rule; ε is its output).
- **RR_target caution:** `RR_target = 0.10` is a frozen exploratory constant, not evidence of optimality. Any
  alternate RR_target must be a separately predeclared sensitivity table and cannot rescue a failed primary
  result.
- **Line minimums:** primary diagonal minimum `ℓmin = 3`; `ℓmin = 2` may be reported only as a sensitivity
  check. Vertical `vmin = 2` remains secondary.
- **Line of identity exclusion:** all RR, DET, L, Lmax, ENTR, LAM, and TT calculations exclude the main
  diagonal (`i = j`). RR_target is applied only over eligible off-diagonal pairs. The trivial line of identity
  must never count as a diagonal line.
- **Theiler window:** primary Tier-A uses `w = 0` except for the excluded main diagonal, because near-diagonal
  continuity is part of the target signal. A secondary sensitivity table may report `w = 1` or `w = 2`, but
  Theiler exclusion must not be changed after outcomes.
- **Primary statistic:** **DET**. Secondary reported: L, Lmax, ENTR, LAM, TT, RR (RR as control only).
- **Robust aggregation:** medians across windows/seeds; no mean/max as a gating statistic.
- **Sample size:** a predeclared number of windows per field and seeds per condition (fixed before running),
  large enough that DET medians are stable at T = 64; L/ENTR treated as secondary because diagonal-length
  support is limited at T = 64.
- **Margins/thresholds** (fixed in advance): Tier-A beat margin **M = 0.20** (ordered-group DET must exceed
  shuffle DET by a factor > 1 + M); surrogate z-threshold **Z = 2.0**; roughness-invariance correlation ceiling
  **|Spearman(DET, delta_rms)| < 0.30** across the dissociation set.

All of the above are frozen before the future slice inspects any real clip. Changing any of them after seeing
outcomes invalidates the result (see §11).

## 6. Controls (first-class, predeclared)

- **Temporal:** `true`, `time_shuffled`, `time_reversed`, `circular_shift`.
- **Roughness / spectral:** amplitude-spectrum-matched (phase-randomized) surrogates; per-window shuffle
  surrogates for z-scoring.
- **Dissociation probes** (predeclared by *property*, frozen before running): **rough-but-ordered** — a
  deterministic high-frequency oscillation or fast periodic trajectory with known recurrence order;
  **smooth-but-disordered** — a smoothed random/permuted trajectory with matched marginal scale but destroyed
  sequence order. Exact generators must be frozen before running. These exist to make the roughness↔order
  dissociation testable directly rather than assumed.

## 7. Fields / windows

Reuse the existing synthetic field bank (`constant`, `tiny_noise`, `white_noise`, `smooth_ramp`, `sine`,
`sine_phase_shift`, `spike`, `lowpass`) plus the two dissociation probes (§6), and — if available offline —
prerecorded real-clip descriptor windows. `constant` and other near-flat windows are neutral and excluded (v1.0
floor). `spike` is retained specifically as a watch case (§14).

## 8. Tier A success — undirected order (mandatory target)

With all §5 constants fixed in advance, Tier A **passes** only if, on a **strict majority** (> 0.5) of
non-neutral fields:

- the **minimum median DET over the ordered/adjacent group** `{true, time_reversed, circular_shift}` exceeds
  the **median DET of `time_shuffled`** by the predeclared margin (ordered-group-min DET > shuffle DET ×
  (1 + M)); **and**
- the **DET z-score of `true` against its own shuffle surrogates ≥ Z**;

and, at the pooled level, each ordered-group condition's median DET exceeds shuffle's by the margin. Consistent
with v1.2 §3, Tier A does **not** require `true` to beat `circular_shift` (circular preserves order); the test
is the ordered group versus the disordered control.

## 9. Tier B success — arrow of time (optional, strictly higher; expected-hard)

Tier B **passes** only if a predeclared **directional** variant separates `true` from `time_reversed` by a
robust margin and z-score. **Predeclared expectation / caveat:** standard symmetric recurrence structure is
time-reversal-invariant (reversing time transposes the recurrence structure and preserves diagonal statistics),
so the primary symmetric DET is **expected to NOT** separate `true` from `time_reversed`. Tier B is therefore a
genuine test of whether a directional add-on is required, and **failing Tier B does not weaken a Tier-A pass**
(see the v1.2 §7 Tier-scope guard). No directional operator is designed here; Tier B is only scoped.

## 10. Roughness-invariance pre-requisite (mandatory, checked first)

Before any Tier is credited:

- `time_shuffled` DET must be **low** (below the ordered group), **not** high;
- the **rough-but-ordered** probe must score **high** DET and the **smooth-but-disordered** probe **low** DET;
- **|Spearman(DET, delta_rms)| < 0.30** across the dissociation set (DET must not track roughness).

If this pre-requisite fails, the family is behaving as another roughness meter and **no order claim of any tier
is permitted**, regardless of the temporal-control numbers.

## 11. Failure criteria (reject or pause)

Reject or pause the v1.2a slice if:

- `time_shuffled` DET **≥** the ordered group (order not captured);
- DET **tracks roughness** (invariance pre-req fails: |Spearman(DET, delta_rms)| ≥ 0.30, or rough-but-ordered
  scores low / smooth-but-disordered scores high);
- Tier A holds only on a **single field, seed, or clip**, or depends on mean/max rather than a robust median;
- **RR is not equalized** across conditions (density/roughness confound leaks in);
- **ε (or RR_target, m, ℓmin, Z, M) is changed after seeing outcomes** — post-hoc tuning invalidates the result;
- a **Tier-B (directional)** claim is made from the symmetric statistic without a genuine directional variant.

## 12. Expected output tables (predeclared schemas — shapes fixed before implementation)

The future slice must emit these tables (illustrative placeholders shown as `·`; no results exist yet):

**T1 — per-control pooled medians (non-neutral):**

| control | RR | DET | L | LAM | ENTR | DET_z(vs shuffle surrogate) |
| --- | --- | --- | --- | --- | --- | --- |
| true | · | · | · | · | · | · |
| time_shuffled | · | · | · | · | · | · |
| time_reversed | · | · | · | · | · | · |
| circular_shift | · | · | · | · | · | · |

**T2 — per-field Tier A (median DET):**

| field | DET_true | DET_reversed | DET_circular | ordered_group_min | DET_shuffled | beats_shuffle_by_M? |
| --- | --- | --- | --- | --- | --- | --- |
| (each non-neutral field) | · | · | · | · | · | Y/n |

**T3 — roughness invariance / dissociation:**

| condition | delta_rms | DET | expected | verdict |
| --- | --- | --- | --- | --- |
| rough-but-ordered | · | · | high DET | Y/n |
| smooth-but-disordered | · | · | low DET | Y/n |
| spectrum-matched surrogate | · | · | low DET | Y/n |
| Spearman(DET, delta_rms) | — | · | \|·\| < 0.30 | Y/n |

**T4 — Tier B directionality (optional):**

| field | DET_true | DET_reversed | directional_stat | separates_by_M+Z? |
| --- | --- | --- | --- | --- |
| (each non-neutral field) | · | · | · | Y/n |

**T5 — gate summary:**

| gate | result | thresholds used |
| --- | --- | --- |
| roughness_invariance_pre_req | PASS/FAIL | RR_target, \|corr\|<0.30 |
| tier_A_undirected_order | PASS/FAIL | m=1, M=0.20, Z=2.0 |
| tier_B_arrow_of_time | PASS/FAIL/NA | directional variant |
| hygiene (deterministic/bounded/low-energy/spike) | PASS/FAIL | v1.0 floor inherited |

## 13. Non-claims, forbidden moves, and quarantine boundaries

This plan does **not**: prove a mechanism; build or select an operator; implement any diagnostic; claim
temporal-order sensitivity, directionality, working vision, or classifier superiority; or authorize any tuning.
It adds no runtime integration, no live capture, no service / camera / sensor contact, and no prompt / context
/ memory / action / render-body / autonomy contact. **No `§0` pointer; no tags.** Brainvision remains offline
research under `research/brainvision/` + `tests/research/`, HELD per v0.6, with `temporal_claim_allowed`
**False**.

## 14. Concerns before implementation

- **Directionality is inherently hard for this family.** Symmetric recurrence is time-reversal-invariant, so
  Tier B will very likely fail without a separate directional statistic. This must not be papered over; a
  Tier-A-only pass is the honest expected ceiling for recurrence/continuity.
- **ε / RR_target is the tuning-risk hotspot.** It must remain a fixed rule (target RR); adjusting it after
  seeing clip outcomes is the most likely way to accidentally manufacture a pass.
- **`spike` is the known outlier.** A few dominant spike frames can mutually recur and inflate DET even under
  shuffle (they are order-agnostic recurrences). The invariance pre-req and the spike watch case exist to catch
  this; if spike breaks invariance, the frame-level design may need a predeclared spike-robust closeness rule —
  decided *before* running, not after.
- **m = 1 vs m > 1 trade-off.** m = 1 gives the exact RR permutation-invariance that makes the roughness defence
  clean, at the cost of dynamical richness; m > 1 is richer but reintroduces the confound. The plan keeps m = 1
  primary deliberately; any m > 1 result is secondary and separately reported.
- **Multi-channel state space.** Descriptor fields have C > 1 channels; the Euclidean metric assumes comparable
  channel scaling (inherited normalization). If channels differ in informativeness, recurrence could be
  dominated by a few channels — a predeclared metric choice to confirm in review.
- **Short windows (T = 64).** Diagonal-line statistics (L, Lmax, ENTR) have limited support at T = 64; keep DET
  primary and treat length/entropy measures as secondary, with enough windows/seeds for stable medians.

## 15. Recommended next

- **Codex reviews this plan**, focusing on: the frame-level RR-invariance argument (§4.1), the ε/RR_target rule
  (§4.2, §5), the Tier-B caveat (§9/§14), and the dissociation-probe definitions (§6).
- Only after a PASS should a **single offline research slice** implement exactly this one family under
  `research/brainvision/` + `tests/research/`, with all §5 constants frozen and controls first-class. Until
  that review passes, no operator, math, or tuning is written.

*End — TORMENT Brainvision Order-Sensitive Recurrence Plan v1.2a. Docs-only, non-authorizing. Opens no
implementation lane; no `§0` pointer added; no tags.*
