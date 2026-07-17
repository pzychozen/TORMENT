# TORMENT Brainvision N=64 Falsifier Implementation Specification v0.1

## 1. Status and authority

Docs-only implementation specification for the exact independent N=64 homometric falsifier. It specifies
what a future quarantined implementation *would* build; it authorizes no implementation, no experiment, and
no ΨTRS evaluation. No candidate has been run through ΨTRS.

```text
FORMAL_HOLD_active = True
Mode_0_active = True

file_modification_authorized = False
draft_scope = single docs-only implementation-specification document
implementation_authorized = False
experiment_authorized = False
scientific_claim_authorized = False
temporal_order_claim_authorized = False
perception_or_vision_claim_authorized = False
runtime_integration_authorized = False
production_kernel_modification_authorized = False
```

Repository state, truthfully: the tracked working tree was clean before drafting; at review time the only
working-tree entry is this untracked document; the untracked draft carries no repository authority until
operator acceptance and commit. Prepared against `main` at HEAD `5323e58` (`origin/main`, `origin/HEAD`
synchronized). Source inspected read-only: the evaluation contract v0.1; `research/brainvision/psi_trs.py`;
`research/brainvision/run_prerecorded_paired_analysis_v0_1.py`;
`research/brainvision/run_engineering_benchmark_v0_1.py`; brainvision test conventions.

## 2. Immutable boundaries

The production TORMENT memory kernel is immutable and out of scope:

```text
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

Brainvision remains offline, prerecorded, quarantined, service-disconnected, non-runtime, non-production,
descriptive. All implementation stays under `research/brainvision/` + `tests/research/`. `psi_trs.py` is not
modified.

## 3. Authoritative evaluation contract

Governing document: `docs/TORMENT_BRAINVISION_N64_FALSIFIER_EVALUATION_CONTRACT_v0.1.md`. Unchanged
selections:

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

Exact fixture (unchanged):

```text
N = 64
member_A = {0,1,3,4,5,7,12,13,15}
member_B = {0,1,3,52,53,55,60,61,63}
```

## 4. Selected B1–B6 decisions

```text
B1 = EXACT_FINITE_IN_PROCESS_SELF_PAIR_EQUALITY
B2 = FIXED_CANONICAL_OUTPUT_SCHEMA_WITH_EXPLICIT_PLACEMENT_OBJECTS
B3 = COMPACT_FINITE_ONLY_CANONICAL_JSON_WITH_WRAPPER_ONLY_PAYLOAD_HASH
B4 = COMPLETE_ORBIT_PLUS_TIE_AWARE_DESCRIPTIVE_PLACEMENT
B5 = SINGLE_FOCUSED_TEST_FILE_WITH_INDEPENDENT_CERTIFICATE_RECOMPUTATION_AND_NO_PRODUCTION_IMPORT_GUARDS
B6 = SAME_ENVIRONMENT_BYTE_REPLAY_USING_EXPLICIT_ENVIRONMENT_FINGERPRINT
```

## 5. Provisional file ownership

Exactly three future files (not created here; implementation unauthorized):

```text
research/brainvision/n64_falsifier_fixture_v0_1.py
research/brainvision/run_n64_falsifier_v0_1.py
tests/research/test_brainvision_n64_falsifier_v0_1.py
```

No JSON schema file, `.npz` fixture, result artifact, lockfile, container file, or sidecar hash file is
proposed. Ownership:

```text
fixture module : exact fixture construction; encoding; lower-order certificates; triple-array certificates;
                 fixture-provenance checks; deterministic fixture hash
runner         : boundary validation; stable ΨTRS invocation; metric computation; start and self-shift
                 orchestration; schema assembly; environment capture; canonicalization; hashing; validity;
                 stdout output
test file      : independent mathematical checks; C=1 descriptor coverage; metric/control validation;
                 schema/replay validation; production-boundary guards
psi_trs.py     : unchanged
```

## 6. Input and validation contract

Validation occurs on the original array representation **before** any floating conversion, in this order:

```text
raw = array-like input inspected WITHOUT dtype=float coercion

required:
  ndim = 2
  shape = (64,1)
  dtype is a real numeric integer or floating dtype
```

Reject before conversion:

```text
boolean dtype or boolean scalar values
object dtype
Unicode/string dtype
byte-string dtype
complex dtype
non-numeric values
```

Accept:

```text
integer values exactly equal to 0 or 1
floating values exactly equal to 0.0 or 1.0
NumPy integer and floating scalar equivalents
```

Then require:

```text
all values finite
all values exactly in {0,1}
```

Only after all boundary checks pass may the runner convert the validated field to the finite floating
representation used by the unchanged descriptor. Explicitly:

```text
Numeric strings such as "0" and "1" are rejected.
Boolean False/True values are rejected rather than silently treated as integer 0/1.
No coercion may turn an invalid boundary value into an accepted value.
```

Rotation convention: `rotate(x,s)[t] = x[(t+s) mod 64]` ≡ `np.roll(x, -s, axis=0)`. Validation lives in the
runner/fixture layer, never inside `psi_trs.py`.

## 7. Fixture-module contract (F3, F8)

The fixture module deterministically constructs `member_A`, `member_B` from `U={0,1,3}`, `V={0,4,12}`
(`A=U+V`, `B=U+(−V)` mod 64):

```text
The nine U×V sums producing member_A must be pairwise distinct.
The nine U×(-V) sums producing member_B must be pairwise distinct.
collision_free_unique_sum_packing = True
```

The module performs literal fixture validation of the accepted supports after construction (asserting the
exact accepted arrays). Canonical support ordering:

```text
member_A_support and member_B_support are ascending integer arrays over representatives 0..63.
```

Certificate-array ordering:

```text
periodic_autocorrelation[lag] uses lag = 0..63 ascending
triple_array[k][l] = T_S(k,l) , outer row index k = 0..63 ascending, inner column l = 0..63 ascending,
  all arithmetic modulo 64
```

The complete triple array is one ordered list of 64 ordered rows, each 64 native integers.

Lower-order certificates:

```text
weight_A, weight_B (= 9, 9); value_multiset_A/_B;
periodic_autocorrelation_A/_B (complete 64-lag, inline);
absolute_transition_magnitude_multiset_A/_B;
directed_one_step_table_A/_B (c00=50, c01=5, c10=5, c11=4); lower_order_match
```

Higher-order certificates (F3):

```text
triple_definition: T_S(k,l) = |{ t ∈ Z64 : t ∈ S, t+k ∈ S, t+l ∈ S }|, lags mod 64
complete 64×64 arrays recomputed but NOT inlined
triple_array_sha256_A, triple_array_sha256_B;
fixed_lag = (4,12); fixed_lag_value_A = 3; fixed_lag_value_B = 0 (existence certificate only);
ordered_disagreement_count = 264;
unlabeled_triple_histogram_A/_B; unlabeled_histogram_match = True
```

Provenance certificates (do not enlarge active quotient G = translation-only):

```text
translation_equivalent = False
dihedral_equivalent = False
affine_equivalent = False
affine_plus_complement_equivalent = False
```

## 8. Runner contract

The runner validates input (§6); rotates by the exact convention; invokes `psi_trs.psi_trs_features`
unchanged for `kappa=0.5` (`psi_trs`) and `kappa=0.0` (`psi_trs_k0`); computes the symmetric and directional
metrics (§9); orchestrates all 64 common starts and the full self-shift orbit (§11); assembles the canonical
schema (§9); captures the environment fingerprint (§14); canonicalizes and hashes (§12–13); evaluates
validity (§17); and writes the canonical wrapper to stdout only. It imports nothing from `torment_service`.

## 9. Feature and response schema (B2)

Canonical payload top-level objects (exactly):

```text
schema, authority, source, environment, configuration, fixture,
feature_schema, results, controls, validity, replay
```

`schema`: `name = torment_brainvision_n64_falsifier_evaluation`, `version = 0.1`.

`authority` (all booleans false): `formal_hold_active, mode_0_active, file_modification_authorized,
implementation_authorized, experiment_authorized, production_kernel_modification_authorized,
scientific_claim_authorized, temporal_order_claim_authorized, perception_or_vision_claim_authorized,
runtime_integration_authorized, non_claims`.

`source`: `source_commit, evaluation_contract_path, evaluation_contract_version,
implementation_specification_path, implementation_specification_version, runner_name, runner_version,
fixture_module_name, fixture_module_version`.

`environment`: the B6 fields (§14).

`configuration`:

```text
N = 64; encoding = direct_scalar_binary_0_1; input_shape = [64,1];
rotation_definition = "rotate(x,s)[t] = x[(t+s) mod 64]";
starts = [0..63]; relative_shifts = [0..63];
descriptor_variants = ["psi_trs","psi_trs_k0"];
descriptor_parameters = { "psi_trs": {"kappa": 0.5}, "psi_trs_k0": {"kappa": 0.0} };
feature_count = 11; epsilon = 1e-12; near_epsilon_threshold = 1e-9;
population_standard_deviation_ddof = 0; external_normalization = none; quotient = translation_only;
self_pair_policy = exact_finite_in_process_equality;
self_shift_comparison_policy = complete_orbit_plus_tie_aware_descriptive_placement;
canonicalization_policy = compact_finite_only_canonical_json
```

`fixture`: §7 fields — `name, version, N, member_A_support, member_B_support, encoding, fixture_sha256,
lower_order, higher_order, provenance`.

`feature_schema`: one authoritative ordered array of exactly 11 entries, each
`{index, name, source_expression, descriptor_variants}`:

```text
0  rho_mean          rho.mean()
1  rho_std           rho.std()                        (population std, ddof=0)
2  rho_range         rho.max() - rho.min()
3  desync_mean       desync.mean()                    (== 0 under kappa=0)
4  desync_std        desync.std()                     (== 0 under kappa=0)
5  desync_absmax     np.abs(desync).max()             (== 0 under kappa=0)
6  psi_traj_mean     psi_traj.mean()
7  psi_traj_std      psi_traj.std()                   (population std, ddof=0)
8  psi_traj_last     float(psi_traj[-1])
9  ch0_rfft_mag_mean np.abs(rfft(Dw[:,0]-mean)).mean()
10 ch0_rfft_mag_std  np.abs(rfft(Dw[:,0]-mean)).std() (population std, ddof=0)
```

The feature-schema names and `source_expression` strings are canonical v0.1 specification constants derived
from source; they are not dynamically regenerated from source text at runtime. Changing any index, name,
`source_expression`, or descriptor-variant association requires a schema-version change. The same identical
11-feature schema applies to both variants. Feature result vectors elsewhere remain ordered arrays (never
re-expressed as named mappings).

`results.members` — for every descriptor variant × member × start:
`start, features (ordered length-11 array), feature_count, finite, feature_vector_sha256`.

`results.pair` — exact nesting:

```text
results.pair = { "psi_trs": <variant_pair_results>, "psi_trs_k0": <variant_pair_results> }

variant_pair_results = {
  "per_start": [ { "start": s,
                   "symmetric": <symmetric_response>,
                   "directional": { "member_A_to_member_B": <directional_response>,
                                    "member_B_to_member_A": <directional_response> } }
                 for s = 0..63 ],   # sorted ascending by start
  "aggregate": { "symmetric": <aggregate>,
                 "directional": { "member_A_to_member_B": <aggregate>,
                                  "member_B_to_member_A": <aggregate> } }
}
```

Symmetric object (parent owns `start`, so no duplicate start field inside):
`numerator, joint_scale, effective_joint_scale, joint_epsilon_hit, joint_near_epsilon_hit, finite,
distance`.

Directional object (its `direction` must agree with the enclosing key):
`direction, numerator, raw_denominator, effective_denominator, epsilon_hit, near_epsilon_hit, finite,
response`.

Aggregate (computed independently for symmetric, A→B, B→A; tie arrays sorted ascending):
`count, minimum, maximum, median, mean, population_standard_deviation, argmin_starts, argmax_starts`.

`results.kappa_differences` — subtraction orientation fixed once:

```text
kappa_difference_orientation = psi_trs_minus_psi_trs_k0

member_local = { "member_A": [ {"start": s, "difference": <ordered length-11 vector>, "finite": <bool>}
                               for s=0..63 ],   # difference = f_psi_trs(member,s) - f_psi_trs_k0(member,s)
                 "member_B": [...] }

pairwise_symmetric = [ {"start": s, "difference": d_sym_psi_trs(s) - d_sym_psi_trs_k0(s), "finite": <bool>}
                       for s=0..63 ]

pairwise_directional = {
  "member_A_to_member_B": [ {"start": s, "difference": q_A_to_B_psi_trs(s) - q_A_to_B_psi_trs_k0(s),
                             "finite": <bool>} for s=0..63 ],
  "member_B_to_member_A": [...] }
```

These are arithmetic differences between aligned descriptor-variant objects. They are not mechanism
decompositions, recursive contributions, causal effects, or validation of recursion. All names use
`difference` (never `contribution`, `effect`, `mechanism`).

Optional non-canonical output (§12) lives on stderr only and never affects payload bytes, hashes, validity,
interpretation, or authorization. Prohibited fields (by name or semantics):

```text
success, failure_as_scientific_outcome, separation_detected, higher_order_detected, recursive_confirmed,
mechanism_confirmed, classification, accuracy, p_value, significance, temporal_order, arrow_of_time,
causality, vision, perception, specificity
```

## 10. Self-pair controls (B1)

Policy `EXACT_FINITE_IN_PROCESS_SELF_PAIR_EQUALITY`. The exact self-pair does not compare member A with
member B; it compares a member's rotation with itself:

```text
left  = rotate(member, s)
right = rotate(member, s+0)
f_left = psi(left) ; f_right = psi(right)
```

Finite validation precedes `np.array_equal(f_left, f_right)`. Required exact invariants:

```text
np.array_equal(f_left, f_right) = True
numerator == 0.0
d_sym == 0.0
q_left_to_right == 0.0
q_right_to_left == 0.0
```

Applies independently to `member_A`, `member_B`, `psi_trs`, `psi_trs_k0`, all starts `0..63`. No tolerance:

```text
self_pair_tolerance_selected = NOT_APPLICABLE_EXACT_EQUALITY_POLICY
```

`EPSILON=1e-12` (denominator clamp), `NEAR_EPSILON_THRESHOLD=1e-9` (diagnostic), `_EPS=1e-8`
(descriptor-internal) retain only their established meanings; none is a self-pair tolerance.
`np.array_equal(-0.0, 0.0)` and numeric `== 0.0` remain valid exact numerical checks; canonical negative-zero
normalization (§12) is a separate serialization rule.

Exact `controls.self_pair` nesting:

```text
controls.self_pair = {
  "member_A": { "psi_trs": [<self_pair_start_object> for s=0..63],
                "psi_trs_k0": [<self_pair_start_object> for s=0..63] },
  "member_B": { "psi_trs": [...], "psi_trs_k0": [...] }
}

self_pair_start_object = { start, feature_vectors_finite, feature_vectors_equal, numerator_exact_zero,
                           symmetric_distance_exact_zero, q_left_to_right_exact_zero,
                           q_right_to_left_exact_zero, valid }
```

The A/B pair-result direction names remain `member_A_to_member_B`, `member_B_to_member_A` (§9).

## 11. Self-shift placement (B4)

Policy `COMPLETE_ORBIT_PLUS_TIE_AWARE_DESCRIPTIVE_PLACEMENT`. Exact `controls.self_shift` nesting:

```text
controls.self_shift = {
  "member_A": { "psi_trs": <member_variant_shift_object>, "psi_trs_k0": <member_variant_shift_object> },
  "member_B": { "psi_trs": <member_variant_shift_object>, "psi_trs_k0": <member_variant_shift_object> }
}

member_variant_shift_object = {
  "per_shift": [ { "relative_shift": r,
                   "per_start": [ {"start": s, "symmetric": <complete symmetric response>} for s=0..63 ],
                   "aggregate": <symmetric aggregate> }
                 for r=0..63 ],           # sorted by relative_shift; per_start sorted by start
  "all_start_placement": <placement object>,
  "fixed_start_placement": <placement object>
}
```

`r=0` is present in the complete orbit and exact-self controls; `r=0` is excluded only from the 63-value
descriptive placement reference distribution. All starts and shifts retain multiplicity; no deduplication or
orbit minimization; directional self-shift responses remain non-mandatory.

Placement formulas (unchanged). For member `X`, variant `v`:

```text
S_X_v = [ self_shift_mean(X, v, r) for r ∈ {1..63} ]   reference_count = 63
P_v   = A/B all-start mean symmetric distance

lower_count  = count(s ∈ S_X_v : s < P_v)
equal_count  = count(s ∈ S_X_v : s == P_v)      # exact finite equality defines ties; no tie tolerance
higher_count = count(s ∈ S_X_v : s > P_v)
strict_empirical_fraction = lower_count / 63
weak_empirical_fraction   = (lower_count + equal_count) / 63
midrank_fraction          = (lower_count + 0.5*equal_count) / 63
```

Placement object: `reference_count, lower_count, equal_count, higher_count, strict_empirical_fraction,
weak_empirical_fraction, midrank_fraction, reference_minimum, reference_maximum, reference_median,
reference_mean, reference_population_standard_deviation`. Counts are native integers; fractions are canonical
finite native floats. The same A/B all-start pair mean for a variant is placed separately against member A's
63 nonzero self-shift aggregates and member B's 63 nonzero self-shift aggregates. Fixed-start placement uses
the A/B distance at common start zero against each member's 63 nonzero self-shift responses at common start
zero. Do not pool `member_A` with `member_B`, `psi_trs` with `psi_trs_k0`, or fixed-start with all-start. No
placement result affects numerical run validity.

`controls.role_swap` per variant × start: `symmetric_response_unchanged, directional_objects_exchanged,
valid`.

## 12. Canonical JSON and output transport (B3)

Canonical payload serialization:

```text
encoding = UTF-8; ensure_ascii = True; sort_keys = True; separators = (",", ":"); indent = None;
allow_nan = False; trailing_newline = False; list_order = contract-defined and preserved;
all dictionary keys are strings
```

Pre-serialization conversion: NumPy int→native int; NumPy finite float→native float; NumPy bool→native bool;
NumPy arrays→ordered lists; every value recursively checked finite; every floating negative zero normalized
to `+0.0` before serialization. Any NaN or Infinity invalidates the run and must never become JSON `null`.
Finite floats use native Python JSON number rendering. Do not round, decimal-stringify, hex-duplicate, or
silently emit nonfinite. (This finite-only converter is a fresh implementation; it must not reuse the
existing `_jsonable` helper, which converts nonfinite to `null` — §21.)

Output transport — smallest unambiguous rule:

```text
Canonical machine output:
  canonical stdout contains only the canonical wrapper bytes; no trailing newline; no prose before or after.
Optional noncanonical text (stderr only):
  human_summary, diagnostic_notes, error_messages
```

The optional stderr channel never enters the canonical payload, the wrapper, hashes, numerical validity,
scientific interpretation, or replay authority. Do not append human text to canonical stdout. No additional
CLI format mode is selected.

Invalid-run payload behavior: a nonfinite or otherwise invalid numerical run must never emit the offending
nonfinite value. When input, fixture, computation, or control validation fails but canonical serialization
remains possible, the runner emits a **finite canonical error payload**: all eleven top-level objects remain
present; non-executed result/control collections use their declared empty array or empty-object forms;
validity fields are false as appropriate; `error_codes` identify the failure; no NaN, Infinity, JSON
nonfinite token, string surrogate, or `null` substitution represents the offending value. Unavailable
numerical results are not fabricated. If canonical serialization itself cannot complete: no
machine-authoritative wrapper exists; canonical stdout is empty; a non-authoritative diagnostic may go to
stderr; the run is invalid — distinct from an ordinary invalid evaluation that still emits a canonical finite
error payload.

## 13. Hashing construction (B3)

Common helper contract (prose):

```text
canonical_sequence_sha256(value) = SHA256(canonical_bytes(value))
```

where `value` is the bare canonical JSON sequence itself, not an enclosing object, unless a separate object
hash explicitly says otherwise. Before hashing a numeric sequence: NumPy scalars→native scalars;
arrays→ordered lists; all floating values finite; floating negative zero→`+0.0`; no rounding.

```text
triple_array_sha256_A = canonical_sequence_sha256(triple_array_A)   # §7 row/column order, native integers
triple_array_sha256_B = canonical_sequence_sha256(triple_array_B)
feature_vector_sha256 = canonical_sequence_sha256(ordered_feature_vector)  # bare ordered list of 11 finite floats, F10 order

fixture_sha256               = SHA256(canonical_bytes(fixture_without_fixture_sha256))
configuration_sha256         = SHA256(canonical_bytes(configuration))
environment_fingerprint_sha256 = SHA256(canonical_bytes(environment))
payload_sha256               = SHA256(canonical_bytes(payload))
```

The `fixture` object contains its certificate-array hashes but contains no `replay` object and no indirect
reference back to `fixture_sha256`. `SHA256` is over UTF-8 canonical bytes, hexdigest (repo convention).
Canonical transport wrapper (machine authority = wrapper serialization, no trailing newline):

```text
{ "payload": payload, "payload_sha256": payload_sha256 }
```

The payload must not contain `payload_sha256`. The payload hash authenticates the payload bytes, not the
wrapper. No separate wrapper hash is required. No result file is written by default. The
`environment_fingerprint_sha256` is stored in `replay` (§15), outside the `environment` object, so it is not
self-referential.

## 14. Environment fingerprint (B6)

The canonical `environment` object:

```text
python_implementation, python_version, python_compiler, python_build, python_executable_sha256,
python_executable_capture_status,
numpy_version, numpy_build_configuration_sha256, numpy_build_configuration_capture_method,
numpy_build_configuration_capture_status, numpy_runtime_information_sha256,
numpy_runtime_information_capture_method, numpy_runtime_information_capture_status,
platform_system, platform_release, platform_version, platform_machine, platform_processor, byteorder,
canonicalization_name, canonicalization_version
```

Python executable hash:

```text
python_executable_sha256 = SHA-256 of the exact file bytes referenced by sys.executable
```

when `sys.executable` is nonempty, names a readable regular file, and reads successfully. Deterministic
status values: `ok, unavailable_empty, unavailable_not_regular_file, unavailable_unreadable`. When status is
not `ok`, the matching exact ASCII sentinel is used as `python_executable_sha256`; no exception messages or
temporary paths appear in the sentinel.

NumPy build/runtime capture — preferred order: (1) structured return value when the installed NumPy API
exposes one; (2) else the API's stdout text; (3) else a deterministic unavailable sentinel. For structured
data: NumPy scalars/arrays→native canonical forms; string dict keys; keys sorted via canonical JSON; declared
list order preserved; all numerical values finite. For captured text: capture/decode as UTF-8; normalize CRLF
and CR to LF; remove one terminal newline; strip trailing horizontal whitespace per line; preserve line
order, internal whitespace, and absolute/installation paths (no redaction). Absolute paths are part of
environment identity. Hash a tagged canonical capture object, not bare text:

```text
{ "capture_method": "structured" | "stdout_text" | "unavailable",
  "capture_status": "ok" | <exact unavailable sentinel>,
  "data": <normalized structured object or normalized text or sentinel> }

numpy_build_configuration_sha256 = SHA256(canonical_bytes(tagged_build_capture))
numpy_runtime_information_sha256 = SHA256(canonical_bytes(tagged_runtime_capture))
```

Unavailable APIs use exact deterministic sentinels including `unavailable_api_absent` and
`unavailable_call_failed`; for `unavailable_call_failed`, record the exception class name only, not its
message. Preserve available BLAS, LAPACK, build/compiler, SIMD, and runtime CPU-feature information.

```text
environment_fingerprint_sha256 = SHA256(canonical_bytes(environment))
```

stored in `replay`, not inside `environment`.

## 15. Replay layers (B6)

The payload's `replay` object:

```text
fixture_sha256, configuration_sha256, environment_fingerprint_sha256,
canonicalization_name, canonicalization_version,
same_environment_byte_replay_authority, cross_environment_byte_replay_authority,
cross_environment_numerical_tolerance_selected, cross_environment_replay_pass_fail_selected,
replay_metadata_valid, payload_hash_valid,
same_environment_replay_compared, same_environment_replay_match
```

There is no `payload_sha256` inside `replay` (it lives only in the wrapper). Authority flags:

```text
same_environment_byte_replay_authority = True
cross_environment_byte_replay_authority = False
cross_environment_numerical_tolerance_selected = False
cross_environment_replay_pass_fail_selected = False
```

For a standalone v0.1 run (no reference-run input):

```text
same_environment_replay_compared = False
same_environment_replay_match = "not_compared"
```

`same_environment_replay_match` is a canonical enum: `not_compared, match, mismatch, ineligible`. External
same-environment replay semantics:

```text
replay eligibility = source commit, evaluation-contract identity, implementation-specification identity,
  runner version, fixture-module version, schema version, canonicalization version, environment fingerprint,
  fixture hash, and configuration hash all match
replay success    = an eligible comparison has identical canonical wrapper bytes AND identical payload SHA-256
replay mismatch   = eligibility holds but wrapper bytes or payload SHA-256 differ
replay ineligible = one or more eligibility identities differ
```

Wrapper equality is not an eligibility prerequisite; it is the result being tested. The v0.1 runner only
emits replay material; external comparison is not a numerical-run invalidator. Cross-environment comparison
may report only structural completeness, certificate agreement, configuration identity, finite feature
vectors, and descriptive numerical differences. A package lock, container, or environment image is not
required for v0.1.

## 16. Test contract (B5)

One focused file `tests/research/test_brainvision_n64_falsifier_v0_1.py`, five categories.

Category 1 — Fixture and certificate. Assert the literal accepted A and B support arrays; independently
reconstruct supports from `U` and `V`; verify collision-free unique sums; exact encoded shape `(64,1)`;
binary values; weights; complete periodic autocorrelation; complete directed one-step table; absolute
transition-magnitude multiset; triple definition; fixed-lag values; ordered disagreement count; unlabeled
triple histogram; translation/dihedral/affine/affine-plus-complement provenance; deterministic fixture hash.
The test file must **independently recompute** — without calling the fixture module's corresponding helper —
at least: support construction; periodic autocorrelation; directed one-step table; `T_A(4,12)`; `T_B(4,12)`;
ordered disagreement count; unlabeled triple histogram. The fixture module must not self-certify via the same
code path its tests use.

Category 2 — C=1 ΨTRS. Input `(64,1)`; feature count 11; exact feature order; finite `psi_trs` and
`psi_trs_k0`; desync features 3–5 exactly zero under `kappa=0`; identical schema and vector length across
variants; deterministic repeated calls; all-zero and all-one scalar fields. Runner/fixture-boundary rejection
tests: one-dimensional input; wrong temporal length; zero channels; nonfinite input; nonbinary input. These
validations remain outside `psi_trs.py`.

Category 3 — Metric and validity. Symmetric role invariance; identical-vector exact zero; directional role
exchange; raw/effective denominator behavior; epsilon-hit and near-epsilon flags; conditional bound;
nonfinite invalidation; population std `ddof=0`; complete sorted argmin/argmax tie arrays; no silently removed
starts.

Category 4 — Rotation and aggregation. Exact rotation convention; `s=0` identity; all 64 common starts;
multiplicity; no deduplication; same-offset A/B pairing; no relative-shift minimization; all 64 relative
shifts; all 64 common starts per relative shift; both members; both descriptor variants; exact `r=0`
self-pair; no requirement that nonzero shifts produce zero.

Category 5 — Schema/serialization/hashing/boundary. Exact canonical schema fields and nesting; stable feature
ordering; canonical serialization settings; deterministic list ordering; finite-only serialization;
negative-zero normalization; deterministic fixture/configuration/environment/payload hashes;
non-self-referential payload hash; no result file by default; byte-identical repeated same-environment stdout
wrapper; source/environment identity; intentional schema/hash/configuration mismatch detection; payload-hash
reconstruction from the parsed payload; alternative dictionary insertion orders producing identical canonical
bytes.

Production-boundary guards (established repo pattern: `import ast; ast.parse(...)` source scan, no service
import) must reject statically identifiable use of `import torment_service` / `from torment_service ...`, and
literal or statically resolvable protected targets through `__import__(...)`, `importlib.import_module(...)`,
`importlib.util.spec_from_file_location(...)`, `importlib.machinery.SourceFileLoader(...)`,
`runpy.run_module(...)`, `runpy.run_path(...)`, referencing `torment_service`, `torment_service/kernel/`,
`torment_service/memory_kernel.py`, or `torment_service/fabric.py`; and statically identifiable
subprocess/service invocations through `subprocess.run`, `subprocess.call`, `subprocess.check_call`,
`subprocess.check_output`, `subprocess.Popen`, `os.system`, `os.popen` when the command names a protected
module/path or a service entry point such as `python -m torment_service`. Tests perform source/AST inspection
without importing the production service; they do not reject arbitrary harmless prose strings — protected-string
checks apply only in import, loading, file-access, or subprocess call contexts.

No test asserts a scientific outcome, separation success, significance, classification, perception, temporal
order, mechanism, or higher-order specificity.

## 17. Invalidation and validity

Canonical `validity` object:

```text
overall_valid, fixture_valid, schema_valid, input_valid, descriptor_valid, self_pair_valid,
role_swap_valid, control_completeness_valid, placement_completeness_valid, environment_capture_valid,
serialization_valid, payload_hash_valid, replay_material_valid,
error_code_namespace, error_code_version, error_codes
```

```text
error_code_namespace = torment_brainvision_n64_falsifier_v0_1
error_code_version    = 0.1
overall_valid = logical AND of every internal validity boolean above, excluding error-code metadata fields
```

An external replay comparison status does not contribute to `overall_valid`. Error-code behavior:
`error_codes` are unique stable ASCII identifiers, sorted ascending by code; independent detectable errors are
accumulated where safe; a fatal stage error prevents dependent stages from running; dependent results are not
fabricated. The exhaustive code list may be finalized during implementation, but namespace, version,
deterministic ordering, and accumulation rules are fixed now.

Internal numerical-run invalidators:

```text
wrong input shape; nonbinary input; nonfinite input; wrong feature count; feature schema/order mismatch;
missing descriptor variant; missing member; missing start; missing relative shift; duplicate or silently
removed start/shift; fixture certificate mismatch; fixture hash mismatch; configuration hash mismatch;
self-pair feature inequality; nonzero self-pair numerator or response; role-swap failure; missing mandatory
denominator diagnostic; environment-capture failure; canonicalization failure; internally inconsistent hashes
(a payload hash that fails reconstruction against its own wrapper); schema mismatch; production-boundary
violation
```

Explicitly **external replay (not internal invalidators)** — classified as ineligible / mismatch / match:

```text
environment fingerprint mismatch against another run
wrapper-byte mismatch against another run
payload-hash mismatch against another run
```

Self-shift placement never invalidates numerical validity.

## 18. Claim boundaries

The specification and any future run prohibit: perception or production-vision claims; temporal-order or
arrow-of-time claims; causality claims; classification or accuracy claims; statistical-significance claims;
recursive-mechanism validation; specificity to triple correlation; general sensitivity or insensitivity
claims; scientific success/failure fields; and implementation or experiment authorization by documentation
alone.

## 19. Implementation authorization gate

This document is a specification only. Implementation authorization requires a separate operator decision and
Codex review of this specification. Even when authorized, the fixture module, runner, and tests are built
under the quarantine boundaries above; `psi_trs.py` and the production kernel are never modified; and no
candidate is run through ΨTRS until a further, separately authorized evaluation step. Same-environment
byte-stable replay is the only replay authority selected; cross-environment byte replay is not authorized.
Unchanged and preserved: all F1–F11 and B1–B6 identifiers; fixture supports; weights; one-step table;
fixed-lag values; disagreement count; triple histogram; quotient; encoding; metric; start policy; placement
formulas; serialization settings; same-environment-only byte-replay authority; the three provisional future
files.

## 20. Explicit non-authorizations

```text
No fixture code, runner, or test is implemented or authorized by this document.
No ΨTRS evaluation is authorized. No candidate is run. No experiment is run.
No result artifact, JSON schema file, .npz, lockfile, container, or sidecar hash file is generated.
No research implementation file is modified. No production code is modified. psi_trs.py is unchanged.
The production TORMENT memory kernel is immutable. No §0, registry, or orientation pointer is changed.
No staging, commit, or push.
```

## 21. Source-behavior notes (deliberate deviations, not contract changes)

1. **Nonfinite serialization.** The existing `_jsonable` helper converts nonfinite floats to `null`. B3
   deliberately deviates: nonfinite **invalidates the run** and must never become `null`; the runner
   implements its own finite-validating converter, not `_jsonable`.
2. **Serialization form.** The repo default is `sort_keys=True, indent=2` (pretty). B3 deliberately selects
   compact `separators=(",",":")`, `indent=None`, `allow_nan=False` for the hashed canonical payload; an
   indented human view, if any, is non-authoritative and goes to stderr.
3. **Environment APIs.** `platform.*` capture is established (`run_engineering_benchmark_v0_1.py:303`). NumPy
   `show_config`/`show_runtime` fingerprint APIs are version-dependent and not currently used in-repo; B6's
   record-unavailability-deterministically clause (`unavailable_api_absent` / `unavailable_call_failed`)
   governs where an API is absent.
4. **Population std.** `population_standard_deviation_ddof=0` matches both NumPy's default `.std()` and the
   descriptor's own internal `rho.std()/psi_traj.std()/Fc.std()` — consistent, no conflict.

None alters a selected B1–B6 decision; they record how the selections map onto existing source.

*End — TORMENT Brainvision N=64 Falsifier Implementation Specification v0.1. Docs-only, non-authorizing,
non-implementing. Quarantined; `psi_trs.py` and the production kernel unmodified; no run performed. No `§0`
pointer; no registry or orientation update; no tags.*
