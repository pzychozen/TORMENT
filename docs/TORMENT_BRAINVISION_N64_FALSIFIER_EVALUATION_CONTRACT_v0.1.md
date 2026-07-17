# TORMENT Brainvision N=64 Falsifier Evaluation Contract v0.1

## 1. Status and authority

Docs-only evaluation specification for the exact independent N=64 homometric falsifier. It declares a future
evaluation contract; it authorizes no implementation, no experiment, and no ΨTRS evaluation. No candidate has
been run through ΨTRS. This document does not redesign the closed boundary-neutral ΨTRS companion arc.

```text
FORMAL_HOLD_active = True
Mode_0_active = True

file_modification_authorized = False
draft_scope = single docs-only untracked evaluation-contract document
implementation_authorized = False
experiment_authorized = False
scientific_claim_authorized = False
temporal_order_claim_authorized = False
perception_or_vision_claim_authorized = False
runtime_integration_authorized = False
production_kernel_modification_authorized = False
```

Prepared against repository `main` at HEAD `753aade`. The tracked working tree was clean before drafting. At
review time the only working-tree entry is this untracked document; an untracked document has no repository
authority merely because it exists. Source inspected read-only: `research/brainvision/psi_trs.py`,
`research/brainvision/run_prerecorded_paired_analysis_v0_1.py`.

Numerical convention: all standard deviations reported under this contract are **population standard
deviation (`ddof = 0`)**; no sample-standard-deviation alternative is used.

## 2. Immutable boundaries

The production TORMENT memory kernel is immutable for this lane. This specification never modifies or
proposes modifying:

```text
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

Brainvision remains offline, prerecorded, quarantined, service-disconnected, non-runtime, non-production,
and descriptive. Any future implementation stays under `research/brainvision/` + `tests/research/`.

## 3. Accepted fixture

```text
N = 64
U = {0,1,3}
V = {0,4,12}
A = U + V     = {0,1,3,4,5,7,12,13,15}
B = U + (−V)  = {0,1,3,52,53,55,60,61,63}
```

Established certificates (from the accepted mathematical prototype; recomputed in the fixture layer per §11):

```text
weight(A) = weight(B) = 9
complete periodic autocorrelation identical at all 64 lags
directed one-step table: c00=50, c01=5, c10=5, c11=4
T_A(4,12)=3 , T_B(4,12)=0
ordered labeled triple-array disagreements = 264
```

Matched under the declared real / scalar / binary / circular scope: value multiset; complete periodic
autocorrelation; absolute transition-magnitude multiset; complete directed one-step transition table. The
complete labeled triple-correlation arrays differ; the complete unlabeled triple-value histograms are
identical. This is an independent N=64 witness, not an N=13 lift.

### 3.1 Equivalence quotient G (F4 = TRANSLATION_ONLY)

```text
G = circular translations of Z64
```

`G` governs fixture equivalence and orbit interpretation only. Not quotiented: reflection, unit
multiplication, full affine action, complement, arbitrary permutation. Reflection is excluded because it
reverses directed temporal orientation and maps labeled lags to their negatives (the demonstrated property
is labeled). **Translation quotienting does not make ΨTRS shift-invariant** (see §10): only an exact
self-pair with identical inputs must produce zero distance within tolerance; nonzero circular shifts of a
member are not required by contract to produce zero ΨTRS distance, consistent with the closed companion
findings that relative circular controls may remain nonzero. Broader fixture-provenance certificates
(reflection-, affine-, affine-plus-complement-inequivalence) are recorded in §11 and do not enlarge `G`.

## 4. Exact encoding contract (F1, F9)

```text
F1 = DIRECT_SCALAR_BINARY_0_1
F9 = RAW_NO_EXTERNAL_NORMALIZATION

D[t,0] = x[t]        x[t] ∈ {0,1}
shape  = (64, 1)
dtype  = finite real
```

Use the raw scalar `0/1` field directly. Do not center to `±1`; do not add a complement channel; do not
duplicate the channel; do not z-score, scale, standardize, or otherwise externally preprocess. Existing
internal ΨTRS operations are unchanged.

## 5. C=1 source status

`psi_trs_features` requires a two-dimensional input and unpacks `T, C = D.shape`. For shape `(64,1)`, the
current implementation is executable because the two-dimensional FFT, warp operations, spectral recursion,
and per-channel loop all accept one channel. Bounded facts only:

```text
C=1 is source-executable
C=1 is newly declared for this fixture
C=1 is not an established repository-wide descriptor convention
C=1 lacks focused existing coverage
```

Every existing Brainvision analyzer and test feeds multi-channel `(T, C)` fields (`C > 1`; the companion
tests use `channels = 4`). C=1 is not described as source-supported beyond the four bounded facts above; a
future implementation must add its own C=1 coverage.

## 6. Feature schema (F10)

```text
F10 = EXPLICIT_SOURCE_DERIVED_11_FEATURE_SCHEMA
feature_count = 11   (for C = 1: 9 fixed features + 2 per channel)
```

Source note: `psi_trs_features` returns a **positional list with no explicit names in source**
(`research/brainvision/psi_trs.py:126-130`). The names below are **derived from the source expressions**
(variable names and operations); they are declared here as a documentation convention, not read from a named
schema in code. The order is the source order and must be preserved.

```text
idx | source expression                    | source-derived name
----|--------------------------------------|-----------------------------
 0  | rho.mean()                           | rho_mean
 1  | rho.std()                            | rho_std
 2  | rho.max() - rho.min()                | rho_range
 3  | desync.mean()                        | desync_mean
 4  | desync.std()                         | desync_std
 5  | np.abs(desync).max()                 | desync_absmax
 6  | psi_traj.mean()                      | psi_traj_mean
 7  | psi_traj.std()                       | psi_traj_std
 8  | float(psi_traj[-1])                  | psi_traj_last
 9  | np.abs(rfft(Dw[:,0]-mean)).mean()    | ch0_rfft_mag_mean
10  | np.abs(rfft(Dw[:,0]-mean)).std()     | ch0_rfft_mag_std
```

`rho` = per-row local `psi_spec` over the causal trailing window (`window = 8`); `desync = kappa *
bounded_warp(rho, ...)` (identically zero at `kappa = 0`, so features 3-5 vanish under the ablation);
`psi_traj` = the 3-step `spectral_recursion` Ψspec trajectory; features 9-10 are the per-channel warped-field
rFFT-magnitude summaries (the `.std()` here is population std, `ddof = 0`, matching NumPy). Every future
output value must be associated with: feature index, source-derived name, descriptor variant (`psi_trs` /
`psi_trs_k0`), member, and start offset.

## 7. Symmetric primary metric (F2 = JOINT_MEAN_NORM_NORMALIZED_L2)

For feature vectors `f_A`, `f_B`:

```text
numerator             = ||f_A − f_B||_2
joint_scale           = (||f_A||_2 + ||f_B||_2) / 2
effective_joint_scale = max(joint_scale, EPSILON)
d_sym(A,B)            = numerator / effective_joint_scale

equivalent: d_sym = 2||f_A − f_B||_2 / max(||f_A||_2 + ||f_B||_2, 2·EPSILON)
```

```text
EPSILON               = 1e-12   (the existing paired-analysis normalization epsilon,
                                 research/brainvision/run_prerecorded_paired_analysis_v0_1.py:46;
                                 distinct from psi_trs.py internal _EPS = 1e-8, NOT reused here)
NEAR_EPSILON_THRESHOLD = 1e-9   (existing diagnostic threshold, ≥ EPSILON)
```

Symmetric denominator diagnostics, for every symmetric comparison:

```text
joint_epsilon_hit      = joint_scale <= EPSILON
joint_near_epsilon_hit = joint_scale <= NEAR_EPSILON_THRESHOLD
```

The future output must retain, per symmetric comparison: `numerator`; raw `joint_scale`;
`effective_joint_scale`; `joint_epsilon_hit`; `joint_near_epsilon_hit`; and finite flags.

Recorded properties: symmetric under role swap; dimensionless; zero for identical finite feature vectors;
privileges neither member; no success threshold selected. Boundedness is **conditional, not asserted
absolutely**: by the triangle inequality `d_sym ∈ [0, 2]` whenever `joint_scale ≥ EPSILON`; in the
degenerate case `joint_scale < EPSILON` (both feature vectors near zero) the clamp permits values above 2, so
no unconditional bound is claimed.

## 8. Directional diagnostics (F6 = RETAIN_BOTH_EXISTING_DIRECTIONAL_NORMALIZATIONS)

For each directional response, defined separately per direction (matching the source response form
`num / max(den, EPSILON)`):

```text
numerator             = ||f_B − f_A||_2                (= ||f_A − f_B||_2, common to both directions)

raw_denominator_A     = ||f_A||_2
effective_denominator_A = max(raw_denominator_A, EPSILON)
q_A_to_B              = numerator / effective_denominator_A

raw_denominator_B     = ||f_B||_2
effective_denominator_B = max(raw_denominator_B, EPSILON)
q_B_to_A              = numerator / effective_denominator_B
```

For each direction, per descriptor variant, report: all 64 per-start responses; arithmetic mean; median;
minimum; maximum; population standard deviation (`ddof = 0`); and, for each per-start directional object,
retain: `numerator`; raw denominator; effective denominator; epsilon-hit flag (`raw_denominator ≤ EPSILON`);
near-epsilon flag (`raw_denominator ≤ NEAR_EPSILON_THRESHOLD = 1e-9`); finite flag.

Role swap must leave the symmetric primary object (§7) unchanged and exchange the two directional objects.
Terminology is neutral only: `member_A`, `member_B`, `pair_direction_A_to_B`, `pair_direction_B_to_A`. Do
not use `true` or `control`.

## 9. Common-start aggregation (F5 = SAME_OFFSET_ALL_64_STARTS_MEAN_SYMMETRIC_DISTANCE)

Rotation convention (the already-established boundary-neutral convention), governing common-start A/B
evaluation, the self-shift controls (§10), the fixed start `s = 0`, and all reported start and shift labels:

```text
rotate(x,s)[t] = x[(t+s) mod 64]      equivalently   rotate(x,s) = np.roll(x,-s)
```

All indices and additions are in `Z64`. For every common start `s ∈ {0,…,63}`, with the **same** start
applied to both members:

```text
A_s = rotate(A, s) ,  B_s = rotate(B, s)
d_s = d_sym( psi(A_s), psi(B_s) )
D_all_starts = arithmetic_mean(d_0, …, d_63)
```

Required diagnostics: fixed-start `d_0`; all 64 per-start `d_s`; minimum; maximum; median; arithmetic mean;
population standard deviation (`ddof = 0`); all argmin starts; all argmax starts. All 64 starts counted with
multiplicity; do not deduplicate repeated rotations by content. This object uses one common start for both
members and is **not** relative-shift minimization, best alignment, quotient distance, or orbit minimization.

## 10. Self-shift orbit controls (F7)

```text
F7 = ALL_64_RELATIVE_SHIFTS_WITH_ALL_64_COMMON_STARTS
```

The complete self-shift orbit is evaluated independently for **both descriptor variants** (`psi_trs` and
`psi_trs_k0`). For each descriptor variant, each member `X`, relative shift `r ∈ {0,…,63}`, and common start
`s ∈ {0,…,63}` (rotation convention per §9):

```text
shift_control_X(r,s) = d_sym( psi(rotate(X,s)), psi(rotate(X,s+r)) )        rotate(X,s+r)[t] = X[(t+s+r) mod 64]
shift_control_X(r)   = arithmetic_mean over all s
```

Retain, for each descriptor variant, the complete symmetric response object and its denominator diagnostics
(§7) for all per-start values and all 64 relative-shift aggregates; count all shifts and starts with
multiplicity. Interpretation:

```text
r = 0 : exact self-pair, expected zero within declared numerical tolerance (applies separately to psi_trs and psi_trs_k0)
r ≠ 0 : not required to be zero
```

Directional self-shift responses are **not** selected as mandatory primary controls; they may be retained as
optional diagnostics only if that does not complicate the v0.1 contract, and are not silently required. Do
not introduce minimum-over-shifts distance, best-alignment distance, or quotient-orbit minimization.

Self-shift comparability is **unresolved**:

```text
self_shift_comparability_policy_selected = False
```

The complete self-shift orbit must be reported descriptively. No exact ratio, ranking rule, tolerance, or
invalidation threshold for "comparable to A/B" is selected in v0.1. Specific attribution to the A/B
higher-order distinction must not be made until a later docs-only decision predeclares how the A/B response
is compared with the self-shift orbit. Classification: **BLOCKS_IMPLEMENTATION_AUTHORIZATION**.

## 11. Fixture certificates

The fixture layer must recompute, from the support sets, before any interpretation.

Lower-order (C4):

```text
value multiset ; weight ; complete periodic autocorrelation ;
absolute transition-magnitude multiset ; complete directed one-step transition table
```

Higher-order (C5, F3 = COMPLETE_LABELED_TRIPLE_ARRAY_AS_FIXTURE_CERTIFICATE). Triple-correlation convention:

```text
For support S ⊆ Z64:
  T_S(k,l) = |{ t ∈ Z64 : t ∈ S, t+k ∈ S, t+l ∈ S }|
           = Σ_{t∈Z64} 1_S(t) · 1_S(t+k) · 1_S(t+l)
All indices and lags are modulo 64.

Complete labeled triple-correlation array: { T_S(k,l) : (k,l) ∈ Z64 × Z64 }
```

```text
T_A(4,12) = 3
T_B(4,12) = 0
ordered labeled disagreement count = 264
```

The complete labeled triple-correlation array is a **pre-run fixture-admissibility certificate**, kept
strictly separate from any ΨTRS evaluation response. The fixed coordinate `(4,12)` remains an existence
certificate only. No scalar triple-array evaluation metric is selected:

```text
H2_scalar_summary_selected = False
```

Equivalence, active quotient vs broader provenance:

```text
Active quotient:
  G = translations only (F4, §3.1)

Broader fixture-provenance certificates:
  not reflection-equivalent
  not affine-equivalent
  not affine-plus-complement-equivalent
```

These broader certificates record the accepted fixture's provenance and distinctness. They do **not** enlarge
the active quotient `G` and do **not** authorize reflection or affine orbit minimization.

## 12. `psi_trs` and `psi_trs_k0` separation

Keep these separate; retain all raw feature vectors by start:

```text
psi_trs(member_A) , psi_trs(member_B)
psi_trs_k0(member_A) , psi_trs_k0(member_B)
```

Member-local kappa difference vector (coordinate-wise difference between two descriptor variants that share
the same feature schema; NOT pair-response differences):

```text
member_local_kappa_difference_A(s) = f_psi_trs_A(s) − f_psi_trs_k0_A(s)
member_local_kappa_difference_B(s) = f_psi_trs_B(s) − f_psi_trs_k0_B(s)
```

These are coordinate-wise differences between two descriptor variants with the same feature schema. They are
**not** a mechanism decomposition and are **not** direct measurements of a recursive contribution.

Pairwise symmetric response (§7) reported separately for `psi_trs` and `psi_trs_k0`. Directional pair
responses (§8) reported both directions separately for `psi_trs` and `psi_trs_k0`. A response-wise kappa
difference may be reported only after the exact response object is named, e.g.:

```text
delta_d_sym(s)     = d_sym_psi_trs(s) − d_sym_psi_trs_k0(s)
delta_q_A_to_B(s) , delta_q_B_to_A(s)   (directional deltas remain directional)
```

No response difference is a direct measurement of a recursive mechanism.

### 12.1 Analytic guard

Under the selected raw scalar `0/1` encoding, equal weight and equal complete periodic autocorrelation
constrain the scalar members to equal Fourier power magnitude. Therefore the source-derived global
per-channel FFT-summary features (`ch0_rfft_mag_mean`, `ch0_rfft_mag_std`) used by ΨTRS at `kappa = 0` are
expected to match, subject to the exact implementation's centering, indexing, and numerical conventions.

Limit: this does **not** predict equality of local-window `rho` features, nonlinear spectral-recursion
features, complete ΨTRS vectors, directional responses, or symmetric pair distances. This is a structural
constraint, not a result claim.

## 13. Replay contract (F11 = CANONICAL_JSON_BYTE_STABLE_REPLAY)

Already-selected requirements for the canonical machine output:

```text
UTF-8
sorted object keys
fixed separators
nonfinite JSON values forbidden
deterministic list order
schema/version identifier
fixture/input hash
source commit/configuration identifiers
output SHA-256
canonical JSON is replay authority
no output file written by default
```

Human-readable output may exist later but is not replay authority. Replay is separated into: exact numerical
equality; canonical JSON byte equality; fixture/input hashes; output hash.

Unresolved (the byte contract is not yet complete):

```text
canonical_json_serialization_details_selected = False
```

Unresolved details: exact `ensure_ascii` behavior; exact separators; trailing-newline policy; float rendering
authority; negative-zero normalization; whether the output hash is external metadata or included in the
serialized object; the exact byte range covered by SHA-256. These details must be resolved in a later
docs-only implementation specification before implementation authorization. A self-referential hash field
must not be introduced without an explicit construction. No JSON schema file is created. Classification:
**BLOCKS_IMPLEMENTATION_AUTHORIZATION**.

## 14. Invalidation rules

A run is invalid if any of the following occurs:

```text
input shape is not (64,1)
input values are not finite real 0/1 values
feature count is not exactly 11
feature order / schema identifier does not match the contract
fixture or certificate hash does not match
source / configuration identity does not match replay metadata
a required descriptor variant is missing
a required start or relative shift is missing
role-swap symmetry fails (symmetric primary changes)
any required denominator diagnostic is absent
nonfinite input, feature, numerator, denominator, directional response, symmetric distance, or aggregate
an invalid start is silently removed (invalid starts must be surfaced, never dropped)
the exact self-pair (r = 0) does not produce zero distance within declared tolerance
replay (numerical or canonical-JSON byte) fails
```

The fixture is invalid if any lower-order (C4) or higher-order (C5) certificate fails to reproduce.

Self-pair tolerance is unresolved:

```text
self_pair_tolerance_selected = False
```

Implementation authorization remains blocked until an exact self-pair numerical tolerance policy is selected.
No tolerance is selected during this correction task. The eventual policy must distinguish: exact
mathematical zero; floating-point feature equality; symmetric metric equality; and absolute versus relative
comparison. No result threshold is selected here.

## 15. Conservative outcome semantics

```text
no observed separation =
  no observed separation under the declared fixture, encoding, metric, starts, and implementation
separation in psi_trs and psi_trs_k0 =
  response to some evaluated A/B difference
separation in psi_trs but not psi_trs_k0 =
  response consistent with dependence on components removed or changed by the kappa-zero ablation
separation only at some starts =
  boundary/start dependence
exact self-pair failure =
  run invalid
role-swap failure of symmetric primary =
  run invalid
certificate failure =
  fixture invalid
nonfinite or denominator failure =
  run invalid
replay failure =
  run invalid or non-reproducible
self-shift controls comparable to A/B =
  reported descriptively only; comparability policy unselected (self_shift_comparability_policy_selected =
  False, §10); specific A/B attribution deferred to a later docs-only decision, not an invalidation rule in v0.1
```

This specification does not claim, and no run under it may claim: perception; production vision;
temporal-order proof; arrow of time; causality; classification; statistical significance;
recursive-mechanism validation; general descriptor insensitivity from a null result; or specificity to
triple correlation from nonzero separation alone.

## 16. Provisional future file boundary (F8 = REUSABLE_QUARANTINED_FIXTURE_CERTIFICATE_MODULE)

Recorded shape of a **not-yet-authorized** future implementation:

```text
research/brainvision/n64_falsifier_fixture_v0_1.py
research/brainvision/run_n64_falsifier_v0_1.py
tests/research/test_brainvision_n64_falsifier_v0_1.py
```

The future fixture module would own: exact fixture construction; S1/S2/S3 certificate recomputation;
complete labeled triple arrays; fixed-lag certificate; ordered disagreement count; declared equivalence
checks. The runner and tests would consume one certificate implementation rather than duplicate mathematical
logic. No `.npz` fixture, JSON schema file, or result artifact is proposed. This file set is provisional;
implementation remains unauthorized.

## 17. Explicit non-authorizations

```text
No runner, fixture code, or test is implemented or authorized by this document.
No ΨTRS evaluation is authorized. No candidate is run. No experiment is run.
No result artifact is generated. No result placeholder is created.
No research implementation file is modified. No production code is modified.
psi_trs.py is not modified (no defect found; the fixture adapts to the stable descriptor).
The production TORMENT memory kernel is immutable. No §0, registry, or orientation pointer is changed.
No staging, commit, or push.
```

## 18. Unresolved items (source-exposed and review-exposed)

1. **Feature names are documentation conventions, not a source-named schema.** `psi_trs_features` returns a
   positional list; the §6 names are derived from source expressions. Any renaming must be recorded.
2. **Two epsilon constants exist.** `EPSILON = 1e-12` (paired-analysis normalization, used for `d_sym` and
   directional denominators) is distinct from `psi_trs.py` internal `_EPS = 1e-8`. This specification uses
   `1e-12` for response normalization only and does not alter the descriptor-internal constant.
3. **C=1 focused coverage** is absent and must be added by a future implementation.

Additional unresolved flags:

```text
self_shift_comparability_policy_selected      = False
self_pair_tolerance_selected                  = False
canonical_json_serialization_details_selected = False
exact_output_schema_fields_selected           = False
```

Classification — these block implementation authorization:

```text
BLOCKS_IMPLEMENTATION_AUTHORIZATION:
  self-shift comparability policy
  self-pair tolerance
  canonical JSON serialization details
  exact output schema fields
  C=1 focused coverage
```

After this v0.1 correction pass, the following are **no longer unresolved**:

```text
rotation sign/indexing convention          (defined, §9/§10)
symmetric epsilon-hit semantics            (defined, §7)
self-shift descriptor-variant coverage     (both psi_trs and psi_trs_k0, §10)
population versus sample standard deviation (population, ddof = 0, §1/§7-§10)
active quotient versus broader provenance wording (separated, §3.1/§11)
```

## 19. Preserved accepted decisions

The following operator selections are unchanged by this correction pass:

```text
F1  = DIRECT_SCALAR_BINARY_0_1
F2  = JOINT_MEAN_NORM_NORMALIZED_L2
F3  = COMPLETE_LABELED_TRIPLE_ARRAY_AS_FIXTURE_CERTIFICATE
F4  = TRANSLATION_ONLY
F5  = SAME_OFFSET_ALL_64_STARTS_MEAN_SYMMETRIC_DISTANCE
F6  = RETAIN_BOTH_EXISTING_DIRECTIONAL_NORMALIZATIONS
F7  = ALL_64_RELATIVE_SHIFTS_WITH_ALL_64_COMMON_STARTS
F8  = REUSABLE_QUARANTINED_FIXTURE_CERTIFICATE_MODULE
F9  = RAW_NO_EXTERNAL_NORMALIZATION
F10 = EXPLICIT_SOURCE_DERIVED_11_FEATURE_SCHEMA
F11 = CANONICAL_JSON_BYTE_STABLE_REPLAY
```

The exact N=64 fixture and all accepted certificate values are unchanged. The closed boundary-neutral ΨTRS
companion arc is not reopened.

*End — TORMENT Brainvision N=64 Falsifier Evaluation Contract v0.1. Docs-only, non-authorizing,
non-implementing. Fixture adapts to the stable descriptor; ΨTRS and the production kernel are unmodified. No
`§0` pointer; no registry or orientation update; no tags.*
