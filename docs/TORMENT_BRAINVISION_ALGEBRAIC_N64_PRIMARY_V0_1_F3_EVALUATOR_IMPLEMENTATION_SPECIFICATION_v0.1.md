# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Evaluator Implementation Specification v0.1

## 0. Decision

```text
A. SPECIFY THE FROZEN-FAMILY F3 EVALUATOR IMPLEMENTATION
```

This document specifies, but does not implement or execute, the offline evaluator that will apply the already-frozen F3 contract to the immutable K=3 witness family selected at candidate indices:

```text
[478, 479, 480]
```

This document is:

```text
docs-only
non-implementing
non-executing
offline
quarantined
non-runtime
non-production
```

This document does not authorize:

```text
evaluator implementation
test execution against the real frozen family
PsiTRS evaluation
descriptor execution on the frozen witnesses
freezer rerun
candidate-generator rerun
candidate-stream mutation
witness replacement
threshold tuning
N64 falsifier rerun
scientific inference
production integration
production-kernel modification
live capture
```

---

## 1. Governing evidence and contract

Frozen family evidence and F3 binding:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_FROZEN_K3_FAMILY_EVIDENCE_AND_F3_EVALUATION_BINDING_v0.1.md
```

Binding commit:

```text
0397c8ee203dd31937064938cac963d1951ca5f0
```

Authoritative freezer findings:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_AUTHORITATIVE_FREEZER_FINDINGS_v0.1.md
```

Existing family and F3 contract:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_DESCRIPTOR_BLIND_HIGHER_ORDER_WITNESS_FAMILY_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

Existing N64 response implementation used as a parity reference only:

```text
research/brainvision/run_n64_falsifier_v0_1.py
```

Descriptor source:

```text
research/brainvision/psi_trs.py
```

Independent verifier:

```text
research/brainvision/witness_family_verifier_v0_1.py
```

Canonical serializer:

```text
research/brainvision/witness_canonical_json_v0_1.py
```

The new evaluator must not amend the accepted F3 mathematics.

It must not import the old N64 runner as its production evaluation engine. The old runner owns a different fixture, authorization gate, schema, and transport. The new evaluator must re-express the exact frozen rotation and symmetric-response formulas locally and prove parity against the old runner’s pure functions in tests.

---

## 2. Frozen implementation paths

Implementation must create exactly these production modules:

```text
research/brainvision/algebraic_n64_f3_frozen_identity_v0_1.py

research/brainvision/algebraic_n64_f3_evaluator_v0_1.py

research/brainvision/run_algebraic_n64_f3_evaluation_v0_1.py
```

Tests must be created at:

```text
tests/research/test_brainvision_algebraic_n64_f3_frozen_identity_v0_1.py

tests/research/test_brainvision_algebraic_n64_f3_evaluator_v0_1.py

tests/research/test_brainvision_run_algebraic_n64_f3_evaluation_v0_1.py
```

No production file outside `research/brainvision/` may be changed.

The following remain immutable:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
research/brainvision/witness_family_verifier_v0_1.py
research/brainvision/witness_family_freeze_v0_1.py
research/brainvision/witness_canonical_json_v0_1.py

torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

---

## 3. Frozen identity module

The module:

```text
algebraic_n64_f3_frozen_identity_v0_1.py
```

must contain constants only.

It must not import:

```text
numpy
psi_trs
the old N64 runner
the verifier
the freezer
the generator
torment_service
```

Permitted imports:

```text
__future__
typing
```

It must bind the exact immutable evidence identities:

```text
N = 64
K = 3
accepted_candidate_indices = (478, 479, 480)

freeze_result_payload_sha256 =
35e03a83fee83b7fc13514397e10115b3f6b99f847bf17d20772a0e61376796e

freeze_result_whole_file_sha256 =
97af61ea4debf9d66146f3e33f035c17c60965c1d9fed0ebbf3d09ead58cbca5

family_manifest_sha256 =
352a49bc8d06a35b41b8783f8a869a1645d93c76ddb91df379492b37106d8151

family_verifier_certificate_sha256 =
416d32bba578856b5122402186860643071070c946829020799138da13ee764e

candidate_stream_payload_sha256 =
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5
```

Pair certificate hashes in exact order:

```text
51e72030237da850757979588b4c4107de69a6098ce7c9a3559243b5545edf2b

3b3475fc9bd2264fd17035f62ddbbc03d584a1fa94f5f28db712941f6e683408

d4bbb7d8d8958cca261728721115de21efa154c50930bf787e4153fcb28ddfd9
```

Exact raw supports:

```text
candidate 478:
A = (0,1,2,4,5,6,7,9,11,12,13,15)
B = (0,1,3,4,5,7,9,10,11,60,62,63)

candidate 479:
A = (0,1,2,4,5,6,7,9,12,13,14,16)
B = (0,1,3,4,5,8,10,11,12,60,62,63)

candidate 480:
A = (0,1,2,4,5,6,7,9,13,14,15,17)
B = (0,1,3,4,5,9,11,12,13,60,62,63)
```

The identity module is a compact committed binding, not a replacement for the canonical freezer result.

Production evaluation must require both:

```text
the local canonical freeze result
and
exact agreement with the committed frozen identity module
```

---

## 4. Production evaluator imports and independence

The evaluator module may import only:

```text
__future__
math
typing
numpy
psi_trs
witness_canonical_json_v0_1
witness_family_verifier_v0_1
algebraic_n64_f3_frozen_identity_v0_1
```

It must not import:

```text
run_n64_falsifier_v0_1
witness_family_freeze_v0_1
any candidate generator
any prerecorded harness
SAG or descriptors package
torment_service
```

The runner may additionally import only the standard-library modules required for:

```text
filesystem validation
Git subprocess calls
JSON loading
hashing
exclusive output publication
stdout/stderr transport
```

AST tests must prove no production module imports `torment_service` or a candidate generator.

---

## 5. Evaluation authorization gate

Production descriptor contact must remain closed by default.

Exact gate:

```text
environment variable:
ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED

authorizing value:
1
```

No other value authorizes.

The runner must accept:

```text
zero command-line arguments
no path override
no configuration override
no metric override
no start subset
no worker-count override
no threshold override
```

The later exact execution sequence, not authorized by this document, will be:

```bat
set ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED=1
python research\brainvision\run_algebraic_n64_f3_evaluation_v0_1.py
```

The runner must refuse before descriptor contact when the gate is absent or differs.

Importing any new module must never evaluate PsiTRS.

---

## 6. Canonical freezer-input path and preflight

Exact input path:

```text
research/brainvision/results/algebraic_n64_primary_v0_1_freeze_v0_1/
  algebraic_n64_primary_v0_1_freeze_result.json
```

The runner must perform a pre-descriptor preflight that verifies:

```text
input is a regular file
whole-file SHA-256 exact
strict UTF-8 decoding succeeds
JSON parsing succeeds
top-level key set exact:
  freeze_result
  freeze_result_sha256
freeze-result payload hash exact
family_frozen = True
authoritative_operation = True
accepted_candidate_indices = [478,479,480]
candidate_count = 20000
terminal_stream_status = budget_exhausted
candidate_stream_sha256 exact
family manifest envelope present
family manifest payload hash exact
family certificate envelope present
family certificate payload hash exact
three pair certificate envelopes present
three pair certificate payload hashes exact and in frozen order
raw supports exact and in frozen A/B order
execution commit binding exact:
  6ddd02f9f6fdf74721dc9cd620cbb2a0aa0fecc8
```

Unknown, missing, reordered, transformed, or mismatched evidence must fail preflight.

Preflight may call the integer-exact verifier.

It must not call PsiTRS.

---

## 7. Independent witness reverification

Before descriptor contact, the evaluator must reverify all frozen mathematical evidence.

For each pair, construct an exact verifier record:

```text
raw_support_A
raw_support_B
candidate_generation_index
```

Call:

```python
witness_family_verifier_v0_1.verify_candidate(record, 64)
```

Require:

```text
execution_invalid = False
pair_valid = True
ordered_failure_codes = []
recomputed pair certificate canonical hash equals frozen pair hash
recomputed pair certificate payload equals the embedded frozen payload
```

Then call:

```python
witness_family_verifier_v0_1.verify_family(recomputed_pair_certificates, 64)
```

Require exact equality with the embedded family certificate:

```text
family_valid = True
members_non_reused = True
mutual_G_inequivalent = True
distinct_autocorrelation_classes = True
ordered_failure_codes = []
```

Require its canonical payload hash to equal:

```text
416d32bba578856b5122402186860643071070c946829020799138da13ee764e
```

A witness mismatch is a pre-descriptor refusal, not a failed F3 hypothesis.

---

## 8. Exact input encoding

Each raw support must be converted to a fresh NumPy array:

```text
shape = (64, 1)
dtype = float
value at t = 1.0 iff t belongs to the support
value at t = 0.0 otherwise
```

Required checks:

```text
exactly 64 rows
exactly one channel
all finite
all values exactly 0.0 or 1.0
weight exactly 12
raw support recovered from the field equals the frozen support
```

No mutation of the source support object is permitted.

No centering, scaling, complement channel, padding, embedding, spatial mapping, 3D conversion, or learned preprocessing is permitted.

---

## 9. Exact rotation and response primitives

The evaluator must implement locally:

```python
rotate(field, s) = np.roll(field, -s % 64, axis=0)
```

with declared meaning:

```text
rotate(x,s)[t] = x[(t+s) mod 64]
```

The evaluator must implement locally the exact symmetric response:

```text
numerator = ||f_a - f_b||_2
joint_scale = (||f_a||_2 + ||f_b||_2) / 2
effective_joint_scale = max(joint_scale, 1e-12)
distance = numerator / effective_joint_scale
```

Each response object must contain:

```text
numerator
joint_scale
effective_joint_scale
joint_epsilon_hit
joint_near_epsilon_hit
finite
distance
```

Constants:

```text
EPSILON = 1e-12
NEAR_EPSILON_THRESHOLD = 1e-9
COMPARISON_TOLERANCE = 0.0
```

Parity tests must compare the new pure `rotate` and `symmetric_response` functions against the corresponding committed pure functions in:

```text
run_n64_falsifier_v0_1.py
```

Parity tests must use synthetic arrays and finite synthetic feature vectors only.

They must not invoke PsiTRS.

---

## 10. Exact descriptor binding

Descriptor variants:

```text
psi_trs
psi_trs_k0
```

Exact calls:

```python
psi_trs.psi_trs_features(field, kappa=0.5)

psi_trs.psi_trs_features(field, kappa=0.0)
```

Expected feature count:

```text
11
```

Every returned feature vector must be:

```text
one-dimensional
length 11
finite
float
```

No feature deletion, weighting, rescaling, standardization, clipping, rounding, or postprocessing is permitted before response calculation.

The evaluator must record:

```text
variant
kappa
start
member identity
raw feature vector
feature vector canonical SHA-256
finite status
feature count
```

---

## 11. Feature-cache and call-count contract

For one full evaluation pass:

```text
6 members
2 descriptor variants
64 starts
```

Exact descriptor-call count:

```text
6 * 2 * 64 = 768
```

The evaluator must build the complete feature cache once per pass.

Every cross-pair and self-shift response must be derived from that cache.

The evaluator must not call PsiTRS while constructing:

```text
cross responses
self-shift responses
aggregates
gate objects
verdicts
serialization
summary text
```

Two-pass replay therefore requires exactly:

```text
1536 production descriptor calls
```

unless a declared descriptor validity failure stops a pass early.

The result must record the attempted and completed descriptor-call counts.

---

## 12. Pure cache-evaluation interface

The evaluator must separate descriptor contact from response mathematics.

Required internal structure:

```text
build_production_feature_cache(...)
    the only evaluator path allowed to invoke psi_trs_features

evaluate_from_feature_cache(...)
    pure response, orbit, gate, validity, and verdict calculation
    no descriptor import use inside this function
```

Tests must exercise `evaluate_from_feature_cache(...)` with deterministic synthetic finite feature caches.

Implementation tests must not invoke the production descriptor on the real frozen family.

The production runner must use only the production cache builder.

No test-only feature provider or path override may be exposed through the production CLI.

---

## 13. Member evaluation object

There are exactly six member objects, in frozen order:

```text
candidate_478_A
candidate_478_B
candidate_479_A
candidate_479_B
candidate_480_A
candidate_480_B
```

Each member object must contain:

```text
member_id
candidate_generation_index
pair_order_index
raw_role
raw_support
raw_support_sha256
weight
pair_verifier_certificate_sha256
features_by_variant
self_orbits_by_variant
```

For each variant, `features_by_variant` contains exactly 64 start rows.

For each variant, `self_orbits_by_variant` contains:

```text
identity_controls
nonidentity_shifts
maximum_nonidentity_mean
argmax_nonidentity_shifts
coverage
```

---

## 14. Identity self-pair controls

For each member, variant, and start:

```text
response(features(member,s), features(member,s))
```

must satisfy exactly:

```text
numerator = 0.0
distance = 0.0
finite = True
```

There are exactly:

```text
6 * 2 * 64 = 768 identity controls per pass
```

Any failure makes the evaluation invalid.

Identity controls are not part of the nonidentity reference maximum.

---

## 15. Complete nonidentity self-shift orbit

For each member and variant, evaluate every:

```text
relative shift r = 1..63
matched start s = 0..63
```

using:

```text
left  = features(rotate(member,s), variant)
right = features(rotate(member,(s+r) mod 64), variant)
```

Coverage per member and variant:

```text
63 * 64 = 4032 response objects
```

Total per pass:

```text
6 * 2 * 63 * 64 = 48,384 nonidentity self-shift responses
```

For every shift, emit:

```text
relative_shift
64 per-start response objects
count
minimum
maximum
median
mean
population_standard_deviation
argmin_starts
argmax_starts
```

For every member and variant, emit:

```text
maximum_nonidentity_mean
argmax_nonidentity_shifts
```

Duplicate numerical values retain multiplicity.

No self-shift response may be dropped or deduplicated.

---

## 16. Cross-pair evaluation

For each frozen pair, variant, and matched start:

```text
cross_s =
symmetric_response(
    features(rotate(A,s), variant),
    features(rotate(B,s), variant)
)
```

Coverage per pass:

```text
3 pairs * 2 variants * 64 starts = 384 cross responses
```

For every pair and variant, emit:

```text
64 per-start response objects
count
minimum
maximum
median
mean
population_standard_deviation
argmin_starts
argmax_starts
```

The arithmetic mean across all 64 starts is the authoritative cross aggregate used by the gates.

---

## 17. Recursive-companion object

For each pair and start:

```text
difference_s =
psi_trs_cross_s.distance - psi_trs_k0_cross_s.distance
```

Emit:

```text
64 raw unrounded differences
minimum
maximum
median
mean
population_standard_deviation
positive_count
zero_count
negative_count
all_positive
```

Gate:

```text
recursive_positive_all_starts =
    all 64 differences > 0.0
```

This is only a companion sign condition.

It does not measure or prove a recursive mechanism.

---

## 18. Pair gates

For each pair:

```text
full_cross_mean
k0_cross_mean

full_self_A_max
full_self_B_max

k0_self_A_max
k0_self_B_max
```

Exact gate objects:

```text
full_dual_orbit_extreme =
    full_cross_mean > full_self_A_max
    AND
    full_cross_mean > full_self_B_max

k0_not_extreme_against_either_member =
    k0_cross_mean <= k0_self_A_max
    AND
    k0_cross_mean <= k0_self_B_max

recursive_positive_all_starts =
    every full_cross_s - k0_cross_s > 0.0
```

Primary pair verdict:

```text
PAIR_STRONG_PASS =
    valid_run
    AND full_dual_orbit_extreme
    AND k0_not_extreme_against_either_member
    AND recursive_positive_all_starts
```

Exact comparison tolerance:

```text
0.0
```

Equality fails every strict greater-than requirement.

No rank, quantile, median, trimmed mean, alternate orbit reference, or near-tie rescue may change the Boolean result.

---

## 19. Pair verdict labels

Each pair must emit a Boolean primary pass and all applicable flags from:

```text
PAIR_STRONG_PASS

PAIR_FULL_NOT_DUAL_ORBIT_EXTREME

PAIR_K0_ALSO_DUAL_ORBIT_EXTREME

PAIR_RECURSIVE_SIGN_FAILURE

PAIR_INVALID
```

Multiple failure flags may coexist.

The exact gate inputs and signed margins must be emitted.

Required margins:

```text
full_margin_vs_A =
full_cross_mean - full_self_A_max

full_margin_vs_B =
full_cross_mean - full_self_B_max

k0_margin_vs_A =
k0_cross_mean - k0_self_A_max

k0_margin_vs_B =
k0_cross_mean - k0_self_B_max

minimum_recursive_difference =
min_s(full_cross_s - k0_cross_s)
```

Margins are descriptive and do not alter the gates.

---

## 20. Family verdict

After all three pair results:

```text
3 PAIR_STRONG_PASS
    -> STRONG_FAMILY_FALSIFIER_SUCCESS

1 or 2 PAIR_STRONG_PASS
    -> VALID_MIXED_FAMILY_RESULT

0 PAIR_STRONG_PASS and every pair valid
    -> STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY

any pair or family validity failure
    -> INVALID_FAMILY_EVALUATION
```

Emit:

```text
strong_pass_count
pair_verdicts in frozen order
family_verdict
```

No alternative or secondary family verdict is permitted.

---

## 21. Validity object

The pass payload must emit exact Boolean fields:

```text
freeze_result_identity_valid
family_manifest_identity_valid
family_certificate_identity_valid
pair_certificate_identities_valid
frozen_support_identity_valid
witness_reverification_valid
source_identity_valid
descriptor_identity_valid
input_encoding_valid
feature_schema_valid
feature_coverage_valid
cross_coverage_valid
identity_self_pair_valid
self_orbit_coverage_valid
all_response_values_finite
normalization_valid
gate_inputs_valid
canonical_serialization_valid
```

`valid_run` is the conjunction of all listed pass-local validity fields.

Replay validity is added only at the final result layer.

A validity failure must not be converted into a scientific gate failure.

---

## 22. Declared invalid-result behavior

Declared descriptor or numerical validity failures must produce a canonical result when possible.

Examples:

```text
wrong feature length
nonfinite feature value
descriptor exception with stable exception-class recording
missing coverage
identity self-pair failure
normalization failure
gate input missing
```

Nonfinite values must never be serialized as NaN or Infinity.

Instead, the result must record:

```text
value_status
failure code
stage
member
variant
start when available
```

and omit or set the invalid numeric field to `null`.

The family verdict becomes:

```text
INVALID_FAMILY_EVALUATION
```

Unexpected uncaught exceptions remain runner failures.

---

## 23. Failure-code namespace

Exact namespace:

```text
torment_brainvision_algebraic_n64_f3_evaluation_v0_1
```

Exact version:

```text
0.1
```

Required codes:

```text
EVALUATION_NOT_AUTHORIZED
REPOSITORY_STATE_INVALID
SOURCE_IDENTITY_FAILURE
INPUT_FILE_MISSING
INPUT_WHOLE_FILE_HASH_MISMATCH
INPUT_JSON_INVALID
FREEZE_RESULT_PAYLOAD_HASH_MISMATCH
FAMILY_MANIFEST_HASH_MISMATCH
FAMILY_CERTIFICATE_HASH_MISMATCH
PAIR_CERTIFICATE_HASH_MISMATCH
FROZEN_SUPPORT_MISMATCH
WITNESS_REVERIFICATION_FAILURE
OUTPUT_PATH_EXISTS

DESCRIPTOR_CALL_FAILED
DESCRIPTOR_FEATURE_SCHEMA_INVALID
DESCRIPTOR_FEATURE_NONFINITE
FEATURE_COVERAGE_INCOMPLETE
CROSS_COVERAGE_INCOMPLETE
SELF_PAIR_CONTROL_FAILURE
SELF_ORBIT_COVERAGE_INCOMPLETE
NORMALIZATION_FAILURE
GATE_INPUT_INVALID
CANONICAL_SERIALIZATION_FAILURE
REPLAY_MISMATCH

PUBLICATION_FAILURE
STDOUT_FAILURE
```

The implementation may add narrower subcodes only with adversarial review before execution authorization.

---

## 24. Two-pass replay

The evaluator must perform two complete internal passes within one runner invocation.

Each pass must:

```text
rebuild every production descriptor feature from scratch
perform exactly the same frozen-order calculations
produce a canonical pass payload
exclude timestamps, durations, process IDs, absolute paths, and mutable host state
```

Compute:

```text
run1_sha256 = SHA256(canonical pass-1 bytes)
run2_sha256 = SHA256(canonical pass-2 bytes)
byte_identical = pass1 bytes == pass2 bytes
```

A frozen family may receive an authoritative evaluation verdict only when:

```text
byte_identical = True
```

Replay mismatch yields:

```text
valid_run = False
family_verdict = INVALID_FAMILY_EVALUATION
failure_code = REPLAY_MISMATCH
```

No automatic third pass or retry is permitted.

---

## 25. Environment and source identity

Capture a stable environment fingerprint outside the replay payload.

At minimum:

```text
Python implementation
Python version
Python compiler
NumPy version
platform system/release/machine
byte order
Python executable SHA-256 or stable unavailable sentinel
NumPy build-configuration SHA-256
NumPy runtime-information SHA-256
```

Bind raw-byte SHA-256 and Git blob identities for:

```text
frozen identity module
evaluator module
runner module
psi_trs.py
witness verifier
canonical serializer
```

The later execution authorization must freeze the exact implementation blob identities.

The evaluator must not bind or contact production-kernel sources.

---

## 26. Canonical result schema

Top-level envelope:

```text
{
  "family_evaluation_result": <payload>,
  "family_evaluation_result_sha256":
      SHA256(canonical_json_bytes(<payload>))
}
```

Payload keys:

```text
schema_name
schema_version
authoritative_operation
execution_commit_identity
frozen_evidence_identity
source_identities
environment_fingerprint
evaluation_configuration
evaluation_configuration_sha256
evaluation_pass
evaluation_pass_sha256
replay_record
validity
family_verdict
failure_record
authority
```

Exact schema identity:

```text
schema_name =
torment_brainvision_algebraic_n64_f3_family_evaluation

schema_version =
0.1
```

`evaluation_pass` contains:

```text
members
pairs
family_summary
descriptor_call_record
pass_validity
```

The final envelope hash covers the payload only.

Recursive self-hashing is prohibited.

---

## 27. Canonical serialization

Use:

```text
witness_canonical_json_v0_1
```

Policy:

```text
ensure_ascii = True
sort_keys = True
compact separators
allow_nan = False
UTF-8
no trailing newline in canonical bytes
```

All NumPy objects must be converted to native JSON-safe objects before serialization.

Negative zero must be normalized to positive `0.0` before canonical output.

No timestamps, durations, absolute paths, temporary paths, host names, user names, process IDs, random identifiers, or filesystem ordering may enter canonical evidence.

---

## 28. Output and publication paths

Final directory:

```text
research/brainvision/results/
  algebraic_n64_primary_v0_1_f3_evaluation_v0_1/
```

Staging directory:

```text
research/brainvision/results/
  .algebraic_n64_primary_v0_1_f3_evaluation_v0_1.staging/
```

Exact final files:

```text
algebraic_n64_primary_v0_1_f3_evaluation_result.json

algebraic_n64_primary_v0_1_f3_evaluation_summary.txt
```

Publication rules:

```text
both final and staging directories must be absent before execution
exclusive staging-directory creation
exclusive file creation
exact two-file staging set
single staging-to-final rename
no overwrite
no merge
no resume
no cleanup of evidence-bearing staging after post-contact failure
```

The summary is operator convenience only.

The JSON is canonical evidence.

---

## 29. Runner repository-state gate

Before descriptor contact, the runner must require:

```text
branch = main
HEAD = origin/main
working tree clean, including ordinary untracked files
repository root exact
all production module paths owned by research/brainvision
all bound source bytes match committed Git blobs
input identity exact
final output directory absent
staging output directory absent
authorization gate exact
```

Any failure before descriptor contact exits as a pre-contact refusal.

No output evidence is created for a clean pre-contact refusal.

---

## 30. Authority-consumption boundary

A later execution authorization must define the consumption threshold as:

```text
the first production call to:
psi_trs.psi_trs_features(...)
on any frozen family member
```

Before that call:

```text
no frozen-family descriptor contact occurred
evaluation authority may remain unconsumed after a true pre-contact refusal
```

After that call:

```text
authority is consumed
no retry
no second runner invocation
no witness replacement
preserve final/staging/absence exactly
```

This specification does not itself grant that authority.

---

## 31. Exit-code contract

```text
exit 0:
canonical two-file publication completed
family verdict may be:
  STRONG_FAMILY_FALSIFIER_SUCCESS
  VALID_MIXED_FAMILY_RESULT
  STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
  INVALID_FAMILY_EVALUATION

exit 1:
post-contact unexpected execution failure
replay publication failure
serialization failure preventing canonical result
staging/final publication failure
post-publication stdout failure

exit 2:
pre-contact refusal
```

Exit `0` does not imply scientific success.

The canonical `family_verdict` is authoritative.

---

## 32. Summary contract

The deterministic summary must include:

```text
execution commit
frozen input identities
source identities
descriptor call counts
replay hashes
replay byte-identical status
pair order
per-pair primary pass
per-pair gate Booleans
per-pair margins
strong pass count
family verdict
validity status
failure code/stage
published artifact set
closed-boundary statements
```

It must state:

```text
operator convenience only; not canonical evaluation evidence
```

No scientific interpretation beyond the frozen verdict labels is permitted.

---

## 33. Test requirements

### 33.1 Import and boundary tests

```text
import performs no evaluation
import creates no files
no production module imports torment_service
no production module imports a generator
identity module contains constants only
runner accepts no CLI arguments
authorization gate defaults closed
```

### 33.2 Frozen identity tests

```text
all three candidate indices exact
all six supports exact
each support sorted, unique, in range
each support weight 12
pair hashes exact and ordered
family hash exact
freeze-result hashes exact
```

### 33.3 Pure primitive parity tests

Against the committed old N64 runner’s pure functions:

```text
rotation parity over all 64 starts
symmetric-response parity over representative finite vectors
epsilon and near-epsilon flag parity
negative-zero normalization
```

No descriptor call is permitted.

### 33.4 Feature-cache mathematics tests

Using synthetic finite feature caches only:

```text
complete 64-start cross coverage
complete 63x64 self-orbit coverage
identity exact-zero controls
correct aggregate arithmetic
correct maxima and argmax ties
correct recursive differences
correct pair gates
correct family verdict mapping
zero-tolerance equality behavior
```

### 33.5 Invalidity tests

```text
wrong feature length
nonfinite feature sentinel handling
missing start
missing shift
identity self-pair failure
normalization failure
certificate mismatch
support mismatch
replay mismatch
serialization rejection
```

### 33.6 Publication tests

Using temporary directories and monkeypatched evaluator output only:

```text
no overwrite
staging exclusivity
exact two-file set
atomic rename
staging retention after evidence-bearing failure
empty staging cleanup before contact
stdout failure after publication preserves final evidence
```

### 33.7 No real-family descriptor test

The implementation test suite must prove that it never calls:

```text
psi_trs.psi_trs_features
```

on any of the six frozen family members.

Monkeypatch the descriptor entry point to raise if contacted during ordinary tests.

---

## 34. Implementation review sequence

After this specification is accepted and committed:

```text
1. implement the three production modules and three test modules
2. run focused tests using synthetic feature caches only
3. run the wider Brainvision research test suite
4. inspect source boundaries and direct file contents
5. perform one focused adversarial implementation review
6. correct only genuine blockers
7. commit and push the implementation
8. freeze exact source blob and raw-byte identities
9. prepare a separate docs-only execution authorization
10. execute exactly once only after that authorization
```

No implementation step authorizes evaluation.

---

## 35. Authority state

```text
DOCUMENTATION_AUTHORIZED = True

FROZEN_K3_FAMILY_EVIDENCE_RECORDED = True
FROZEN_K3_FAMILY_BOUND_TO_F3 = True

F3_EVALUATOR_IMPLEMENTATION_SPECIFIED = True
F3_EVALUATOR_IMPLEMENTATION_AUTHORIZED = False
F3_EVALUATOR_TEST_EXECUTION_AUTHORIZED = False

F3_EVALUATION_AUTHORIZED = False
PsiTRS_EVALUATION_AUTHORIZED = False

FREEZER_RERUN_AUTHORIZED = False
GENERATOR_RERUN_AUTHORIZED = False
WITNESS_REPLACEMENT_AUTHORIZED = False
THRESHOLD_TUNING_AUTHORIZED = False

SCIENTIFIC_INFERENCE_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
LIVE_CAPTURE_AUTHORIZED = False
```

`FORMAL_HOLD` and `Mode_0` remain active.

---

## 36. Final disposition

```text
A. FROZEN-FAMILY F3 EVALUATOR IMPLEMENTATION SPECIFIED
```

The implementation must preserve:

```text
the exact six frozen raw supports
the exact pair order
the exact F3 response formula
all 64 matched starts
complete nonidentity self-shift references
strict zero-tolerance gates
the preregistered pair and family verdicts
two-pass byte-identical replay
source and evidence identity binding
one-run later execution semantics
the production-kernel boundary
```

No implementation or PsiTRS evaluation occurred while preparing this specification.

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Evaluator Implementation Specification v0.1.*
