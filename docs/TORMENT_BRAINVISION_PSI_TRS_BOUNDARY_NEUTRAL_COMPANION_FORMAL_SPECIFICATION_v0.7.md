# TORMENT Brainvision ΨTRS Boundary-Neutral Companion Formal Specification v0.7

## 1. Status / quarantine

**DOCS-ONLY formal specification. Non-authorizing, non-implementing.** This note formalizes the
boundary-neutral companion candidate already selected in
`TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_BOUNDARY_NEUTRAL_DUAL_REPORTING_DESIGN_v0.6.md`. It is an
**engineering contract** describing exactly what a future companion *would* compute and report; it builds
nothing. The subject is the raw ΨTRS matched paired response and `recursive_delta` emitted by
`research/brainvision/run_prerecorded_paired_analysis_v0_1.py`.

Implementation remains explicitly **unauthorized**. Work stays quarantined under `research/brainvision/` +
`tests/research/`. No `torment_service` change; no live capture; no camera or sensor route; no provider or
live-model route; no prompt / context / memory / action contact; no MCP, movement, autonomy, or
render-body route; no database, substrate, carrier, or Stage-B route; no classifier claim; no
temporal-order claim; no perception claim. **No `§0` pointer update; no tags.** No code, tests, analyzer,
`.npz` inputs, result artifacts, or generated outputs are changed by this note.

Governing standing (preserved exactly):

```text
FORMAL HOLD active
Mode 0 active
verdict = HOLD

bounded_experiment_ready = False
Brainvision_perceptual_claim_ready = False
runtime_integration_authorized = False
new_scientific_claim_authorized = False

candidate implemented = False
implementation authorized = False
experiment authorized = False
```

## 2. Formalized candidate

The selected candidate is the **deterministic multi-start circular ensemble** with:

```text
offset policy      = O1 — all 64 starts
aggregation policy = A3 — mean normalized response across matched starts
block length       = 64
offsets            = 0, 1, ..., 63   (canonical numeric order)
EPSILON            = 1e-12
```

`EPSILON` is the same fixed value already used by the analyzer (`run_prerecorded_paired_analysis_v0_1.py`,
`EPSILON = 1e-12`) and is not re-tuned here.

**Rotation operator.** For a cached 64-row array `X` and start `s`, define the circular row-rotation that
brings row `s` to row `0`:

```text
R_s(X)[i, :] = X[(i + s) mod 64, :]     equivalently     R_s(X) = np.roll(X, -s, axis=0)
```

This is a mathematical definition of the operation. It does **not** mandate any particular implementation.

**Multiplicity and enumeration.** Every offset receives **equal weight** `1/64`. Offsets are enumerated
canonically as `0, 1, ..., 63`. Duplicate rotations (rotations that happen to produce equal arrays, e.g.
for periodic or constant blocks) **retain their multiplicity**: they must not be deduplicated, collapsed,
or content-weighted. Multiplicity applies to the scalar mean **and to every distribution statistic** in §9.

## 3. Matched-pair invariant

**Companion descriptor domain.**

```text
D_companion = {psi_trs, psi_trs_k0}
```

Throughout this specification, descriptor `d` ranges **only** over `D_companion`. Companion evaluation for
any other prerecorded-analyzer descriptor (`frame_diff`, `plain_fft`, `descriptor_only`, `random_mapping`,
or any other analyzer descriptor) is **outside this specification** and requires a separate scope decision
and authorization.

For a fixed descriptor `d ∈ D_companion`, block, and control, let `X_true` and `X_control` be the block's cached true and
control arrays (the exact arrays already produced by the analyzer's shared transform cache). For each start
`s ∈ {0, ..., 63}` define:

```text
T_s = R_s(X_true)
C_s = R_s(X_control)
```

The **same `s`** is applied to the matched true and control arrays. For both `psi_trs` and `psi_trs_k0`,
the **exact same** `T_s` and `C_s` arrays are supplied to both descriptors.

The specification **prohibits** (any of these makes an implementation non-conforming — see §15):

- independent true/control start selection;
- independent true/control canonicalization;
- comparison of different offsets (a `T_s` compared against a `C_{s'}` with `s ≠ s'`);
- descriptor-specific re-rotation;
- descriptor-specific recanonicalization;
- regeneration that changes values or ordering;
- deduplication of repeated rotations.

## 4. Per-start normalized response

For descriptor `d` and start `s`:

```text
n_d(s) = || f_d(T_s) ||₂                                    (per-start true-feature norm; the raw denominator)

q_d(s) = || f_d(C_s) - f_d(T_s) ||₂ / max( n_d(s), EPSILON )
```

This is the **same response formula** the analyzer already uses (`num = L2(f_c - f_true)`,
`den = max(L2(f_true), EPSILON)`, `response = num/den`), applied per rotated start. `max(n_d(s), EPSILON)`
is the **effective denominator** at start `s`.

Aggregation is **response-space only**. The specification prohibits averaging descriptor features, feature
centroids, embeddings, internal states, or transformed arrays. Only the scalar responses `q_d(s)` are
aggregated.

## 5. Companion scalar

When `valid_d(s)` is true for all 64 starts, as defined in §6, and the computed arithmetic mean is finite:

```text
Q_d = (1 / 64) * Σ_{s=0}^{63} q_d(s)      ≡      companion_response_d
```

The arithmetic **mean** is chosen deliberately (aggregation policy A3). The mean can be moved by a single
extreme start; therefore the **full per-start distribution is mandatory** in every report (§9), so that one
extreme start can never disappear behind the scalar.

## 6. Nonfinite policy

All 64 starts **must be evaluated**.

**Per-start validity predicate.** `valid_d(s)` is true if and only if:

1. every element of `f_d(T_s)` is finite;
2. every element of `f_d(C_s)` is finite;
3. `n_d(s)` is finite;
4. `max(n_d(s), EPSILON)` is finite; and
5. `q_d(s)` is finite.

Then:

```text
finite_count                = |{ s ∈ {0,...,63} : valid_d(s) }|
nonfinite_count             = 64 - finite_count
offending_nonfinite_offsets = sorted { s ∈ {0,...,63} : not valid_d(s) }
```

Per-start serialization:

```text
per_start_responses[s] = q_d(s)   when valid_d(s) is true;
per_start_responses[s] = null     otherwise.
```

`null` represents **semantic unavailability** for that offset. It is never a numerical value and is never
included in any aggregation.

**All-64 requirement.** If any start is invalid:

```text
if nonfinite_count > 0:
    companion_response_d = unavailable
```

The specification **prohibits**: finite-only averaging; silent omission of failing starts; silent
imputation; replacement by zero; clipping solely to obtain a scalar; and partial-start renormalization.
Every offending offset must be reported (`offending_nonfinite_offsets`, §9). The all-64-start requirement
is not weakened.

**Derived-scalar finiteness rule.** Every derived scalar is available only when the value produced by its
specified floating-point computation is finite. This applies to:

```text
companion_response_d    mean                   median
IQR                     minimum                maximum
mean_median_ratio       companion_recursive_delta
raw_minus_companion_d   raw_minus_companion_recursive_delta
minimum_denominator     maximum_denominator
```

If a computed derived value is `NaN`, `+Infinity`, or `-Infinity`, that individual field is semantically
unavailable and is serialized as JSON `null`. `NaN` and infinity must never be emitted. JSON `null` is a
serialization of unavailability only; it must never be treated as zero, substituted into arithmetic, or
included as an aggregation value.

The **stronger** response-distribution rule of §9 is preserved: when any start is invalid, **all**
response-distribution fields are unavailable rather than computed over only the finite subset. This is
distinct from derived overflow — **if all 64 starts are valid but one aggregate calculation itself becomes
nonfinite, only the affected derived field and any field that depends upon it become unavailable; the starts
remain classified as valid, and `finite_count`/`nonfinite_count` are not altered by aggregate overflow.**

**Unavailability / dependency propagation (explicit, hardened):**

```text
companion_recursive_delta           is unavailable unless BOTH companion response operands are available
                                    AND the computed subtraction is finite.

raw_minus_companion_d               is unavailable unless BOTH operands are available AND the computed
                                    subtraction is finite.

raw_minus_companion_recursive_delta is unavailable unless BOTH operands are available AND the computed
                                    subtraction is finite.
```

"Unavailable" is emitted as JSON `null`, consistent with the analyzer's existing convention that non-finite
floats serialize to `null`.

## 7. Companion recursive delta

```text
companion_recursive_delta = companion_response_psi_trs - companion_response_psi_trs_k0
```

Its meaning is limited to: **the difference in mean normalized matched-start transform sensitivity between
`psi_trs` and `psi_trs_k0`**. It must **not** be described as descriptor superiority, temporal-order
sensitivity, arrow-of-time sensitivity, perception, validated recursive-time contribution, mechanism
evidence, or classifier evidence.

## 8. Raw preservation and dual reporting

Raw ΨTRS remains **fixed-start, block-local, stateful, path-sensitive, deterministic, and historically
preserved**. The companion is reported **beside** raw results, **never instead of** them. Historical raw
`psi_trs`, historical `recursive_delta`, and current prerecorded paired-analysis outputs are preserved
unchanged; the companion adds fields, it never overwrites or replaces them.

```text
raw_minus_companion_d                = raw_response_d - companion_response_d
raw_minus_companion_recursive_delta  = raw_recursive_delta - companion_recursive_delta
```

Interpretation is limited to: **the selected fixed start affected the measured transform sensitivity.**
Neither sign of either difference may be presented as scientifically better, more valid, more perceptual,
or more temporally meaningful. The output structure must keep raw and companion fields **visibly and
structurally separate** (distinct, clearly named keys; no interleaving that could be mistaken for a single
number).

## 9. Required per-start diagnostics

For each `d ∈ D_companion`, block, and control companion evaluation the report requires:

```text
per_start_responses          offset_policy
finite_count                 aggregation_policy
nonfinite_count              number_of_starts
offending_nonfinite_offsets  mean
median                       minimum
IQR                          maximum
mean_median_ratio            minimum_denominator
epsilon_hit_count            maximum_denominator
near_epsilon_hit_count
```

**Deterministic conventions** (chosen explicitly; where the repository already fixes a convention it is
reused and named):

- `number_of_starts = 64`; `offset_policy = "O1 — all 64 starts"`;
  `aggregation_policy = "A3 — mean normalized response across matched starts"`.
- **Ordering.** `per_start_responses` is a length-64 list in **canonical numeric offset order** `0..63`;
  index `s` holds `q_d(s)` if and only if `valid_d(s)` is true; otherwise index `s` stores `null`.
- **Offset representation.** Offsets are the integers `0..63`. O1 enumerates exactly this set, so there is
  no out-of-range "invalid offset"; an *offending* start is exactly one for which `valid_d(s)` is false and is
  listed by its integer offset in `offending_nonfinite_offsets` (sorted ascending). `finite_count +
  nonfinite_count = 64`.
- **Response distribution fields** (`mean`, `median`, `IQR`, `minimum`, `maximum`, `mean_median_ratio`) are
  computed over the **complete multiset of all 64** `q_d(s)` **only when `nonfinite_count = 0`**; when
  `nonfinite_count > 0` they are all `unavailable` (`null`). This is **stricter than** the analyzer's raw
  response-normalization helpers (`_median`/`_iqr`/`_mean`, which reduce over the finite subset); the
  companion deliberately refuses finite-only summarization so a partial distribution can never masquerade
  as complete. `mean` equals `companion_response_d` (§5).
- **Quantile / IQR convention.** `median` is computed using numpy median, equivalently the 50th percentile
  under the linear convention; for the fixed even sample size of 64 this is the arithmetic mean of the two
  middle values after sorting the complete 64-value multiset. `IQR = Q3 - Q1` with `Q1` the 25th percentile
  and `Q3` the 75th percentile under **linear interpolation** (numpy `method='linear'`), matching the
  analyzer's `np.percentile(values, [75.0, 25.0])`. `minimum`/`maximum` are the min/max of the 64 `q_d(s)`.
  The median and IQR use all 64 values **only when all 64 starts are valid**.
- **`mean_median_ratio`.** `= mean / median` when `median` is finite and `median ≠ 0`; otherwise
  `unavailable` (`null`). When any input is nonfinite (`nonfinite_count > 0`) it is `unavailable` (both
  `mean` and `median` are already unavailable in that case). This matches the analyzer convention
  (`float(mean/med)` guarded by finite `mean`, finite `med`, `med != 0`, else `nan`→`null`).
- **Denominator fields.** `minimum_denominator` and `maximum_denominator` summarize the **finite raw
  denominators** `n_d(s) = ||f_d(T_s)||₂`. They do **not** summarize the epsilon-floored effective
  denominator `max(n_d(s), EPSILON)`. `epsilon_hit_count` = number of starts with finite `n_d(s)` and
  `n_d(s) <= EPSILON`. `near_epsilon_hit_count` = number of starts with finite `n_d(s)` and
  `n_d(s) <= 1e-9` (`NEAR_EPSILON_THRESHOLD = 1e-9`, the analyzer's value); per the repository convention it
  **includes** every epsilon hit (since `NEAR_EPSILON_THRESHOLD >= EPSILON`). `minimum_denominator`/
  `maximum_denominator` are the min/max over the **finite raw** `n_d(s)`; both are `unavailable` (`null`)
  only when **no finite raw `n_d(s)` exists**, or when their own computed result is nonfinite. Denominator
  diagnostics are computed over the finite raw denominators even when the response scalar is unavailable,
  because their purpose is to expose *why* a start failed.

Multiplicity (§2) applies to all of the above statistics, not only the scalar mean.

## 10. Circular-rotation invariance

Let both matched arrays be globally circularly rotated by `k`:

```text
X'_true    = R_k(X_true)
X'_control = R_k(X_control)
```

Because `R_s(R_k(X)) = R_{(s+k) mod 64}(X)`, for every descriptor `d`:

```text
q'_d(s) = q_d((s + k) mod 64)
```

(the equivalent permutation under this document's sign convention). Therefore the following are
**invariant** under a global rotation:

```text
companion scalar Q_d
the multiset of per-start responses
mean, median, IQR, minimum, maximum
finite_count, nonfinite_count
epsilon_hit_count, near_epsilon_hit_count
minimum_denominator, maximum_denominator
```

The literal response attached to a given offset **label** `s` is generally **permuted**, not individually
unchanged. The specification must **not** claim that the original and rotated inputs produce identical
values at each unchanged literal offset label.

**Canonical reporting.** Offsets are emitted in canonical numeric order `0..63` for each evaluated input. A
global rotation permutes *which* original start-state response appears under each offset label. Inverse
reindexing (`s → (s − k) mod 64`) may be used to demonstrate the per-start correspondence, but it is **not
required** for the scalar / multiset invariants above.

## 11. Edge-case expectations

```text
constant arrays:          scalar remains rotation invariant; the per-start distribution may collapse
                          (all q_d(s) equal). Multiplicity retained.

periodic / repeated arrays: duplicate rotations retain multiplicity; repeated values remain separate
                          per-start observations (never deduplicated).

one extreme finite start: the mean may move; the distribution fields (min/max/median/IQR/per_start_responses)
                          expose the extreme.

one near-zero denominator: normalization uses max(n_d(s), EPSILON); epsilon_hit_count /
                          near_epsilon_hit_count / minimum_denominator expose the denominator condition.

one nonfinite start:      companion_response_d (and the response distribution fields) are unavailable;
                          the offset is listed in offending_nonfinite_offsets.

descriptor evaluation order: no effect on any value.

SAG enabled or disabled:  no effect on companion descriptor semantics.

supplied offset iteration order: no effect after canonical output ordering (0..63).

input / cache mutation:   prohibited (inputs and cached arrays are read-only throughout).

different block length:   outside this specification; requires a new decision (see §15).
```

## 12. Required future tests (specified, not implemented)

A conforming future implementation would require tests proving:

1. Exact global circular-rotation invariance of the scalar with all 64 starts.
2. Correct permutation correspondence of per-start responses under a global rotation (`q'_d(s) = q_d((s+k) mod 64)`).
3. Identical start-wise true/control pairing (same `s` on `T_s` and `C_s`).
4. Identical rotated arrays supplied to ΨTRS and ΨTRS-k0.
5. Offset-iteration-order independence.
6. Descriptor-order independence.
7. Raw historical result preservation:
   - existing raw numerical values remain unchanged;
   - existing raw field names and semantics remain unchanged;
   - companion fields are additive and structurally separate; and
   - whole serialized-output byte identity is **not** required because the output gains new companion fields.
8. Input-array immutability.
9. Cached-array immutability.
10. Duplicate-rotation multiplicity (no deduplication).
11. Constant-array behavior.
12. Periodic-array behavior.
13. Per-start denominator diagnostics (`minimum_denominator`/`maximum_denominator` summarize the finite raw `n_d(s)`, not the effective denominator `max(n_d(s), EPSILON)`).
14. Epsilon handling (`n_d(s) <= EPSILON`).
15. Near-epsilon handling (`n_d(s) <= NEAR_EPSILON_THRESHOLD`, including epsilon hits).
16. Nonfinite-start invalidation governed by the exact `valid_d(s)` predicate (which alone determines `finite_count`, `nonfinite_count`, `offending_nonfinite_offsets`, and the `null` entries of `per_start_responses`).
17. Unavailability / dependency propagation: `companion_recursive_delta`, `raw_minus_companion_d`, and `raw_minus_companion_recursive_delta` are unavailable unless both operands are available **and** the computed subtraction is finite.
18. Per-start distribution reproducibility (deterministic across runs).
19. Deterministic IQR and `mean_median_ratio` edge-case conventions (median = 0, nonfinite inputs).
20. Default no-write behavior.
21. Absence of classifier, labels, folds, balanced-accuracy, inference, or significance fields.
22. Structural separation of raw and companion reporting.
23. Preservation of every scientific and integration lock.
24. Rejection of block lengths other than 64 under this specification.
25. Descriptor domain restricted to `D_companion = {psi_trs, psi_trs_k0}`; no other analyzer descriptor (`frame_diff`, `plain_fft`, `descriptor_only`, `random_mapping`) is companion-evaluated.
26. All 64 starts valid but a single aggregate calculation overflows to nonfinite: only the affected derived field and its dependents become unavailable, while `finite_count`/`nonfinite_count` are unchanged (all starts remain valid).
27. `NaN`/`Infinity` are never serialized (unavailable fields are JSON `null`), and `null` is never used as an aggregation value or substituted into arithmetic.

(No tests are added by this note.)

## 13. Computational standing

```text
expected descriptor-evaluation multiplier ≈ 64x relative to one raw fixed-start evaluation
```

Evaluation may be **streamed one start at a time**; all 64 rotations need not be materialized
simultaneously. **No optimization, caching redesign, vectorization requirement, reduced-offset
approximation, or performance-driven semantic change is authorized.** A reduced-offset design is a
different candidate and is out of scope here.

## 14. Non-claims

This specification is an **engineering contract only**. It does not establish temporal-order sensitivity,
arrow of time, perception, vision, descriptor superiority, recursive-mechanism validity, classifier
validity, inferential validity, statistical significance, production readiness, runtime suitability, or
integration readiness. The companion measures only the **mean normalized matched transform sensitivity
across all 64 circular starts**.

## 15. Stop conditions (specification invalidity)

This specification is **invalid**, and any implementation claiming to follow it is non-conforming, if it
permits any of the following:

```text
mismatched true/control offsets
independent canonicalization
different arrays supplied to psi_trs and psi_trs_k0
duplicate-rotation deduplication
finite-only averaging
feature-space aggregation
silent replacement of raw results
reduced offset sets
block length other than 64
claim expansion
implementation authorization
```

## 16. Status

```text
offset_policy_resolved         = True
aggregation_policy_resolved    = True
formal_specification_recorded  = True

candidate_implemented          = False
implementation_authorized      = False
experiment_authorized          = False

FORMAL_HOLD_active             = True
Mode_0_active                  = True
verdict                        = HOLD
```

*End — TORMENT Brainvision ΨTRS Boundary-Neutral Companion Formal Specification v0.7. Docs-only,
non-authorizing, non-implementing. Opens no implementation lane; no `§0` pointer added; no tags.*
