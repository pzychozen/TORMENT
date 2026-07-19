# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Read-Only Asymmetry Audit Implementation Authorization v0.1

## 0. Decision

```text
A. AUTHORIZE STANDALONE READ-ONLY ASYMMETRY AUDIT ANALYZER IMPLEMENTATION
```

This document authorizes implementation and bounded non-contact testing of the already-specified standalone read-only F3 asymmetry audit analyzer.

This document is:

```text
docs-only
non-implementing during preparation
non-executing during preparation
offline
quarantined
non-production
```

This authorization authorizes only:

```text
standalone analyzer implementation
non-contact synthetic tests
temporary-directory publication tests
read-only retained-input preflight validation tests
static forbidden-import and forbidden-call tests
determinism tests over synthetic fixtures
```

It does not authorize:

```text
running the audit calculations against the retained canonical F3 result
creating the final audit output directory
publishing derived retained-evidence audit artifacts
PsiTRS contact
descriptor recomputation
F3 reevaluation
scientific inference
production integration
kernel modification
```

This authorization becomes effective only after it passes focused adversarial review, is committed, is pushed, and is the synchronized main-branch HEAD.

---

## 1. Governing specification

Bound specification:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_READ_ONLY_ASYMMETRY_AUDIT_SPECIFICATION_v0.1.md
```

Specification commit:

```text
db82ec06faf398d52a002ba56f976e91045d12a4
```

Specification commit subject:

```text
docs(research): specify frozen N64 F3 asymmetry audit
```

The implementation must conform exactly to the specification, including:

```text
exact retained-input path, size, and whole-file SHA-256
exact canonical envelope validation
exact execution identity and verdict bindings
inverse-shift multiset validation
canonical q=1..32 class convention
all six frozen audit questions
deterministic rank, threshold, top-k, and tie semantics
deterministic narrow/intermediate/broad disposition rules
separate derived-output location
non-gating and non-rescue interpretation boundary
```

The completed F3 verdict remains:

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Implementation must not amend, rerun, reconsider, weaken, or rescue that verdict.

---

## 2. Exact authorized implementation files

Creation is authorized only for exactly these two files:

```text
research/brainvision/analyze_algebraic_n64_f3_asymmetry_v0_1.py

tests/research/test_brainvision_analyze_algebraic_n64_f3_asymmetry_v0_1.py
```

No additional production, fixture, helper, result, or documentation files are authorized during implementation without a later docs-only amendment.

Synthetic fixtures should be constructed within the test module or in temporary directories.

---

## 3. Analyzer boundary

The analyzer must be standalone, offline, and standard-library only.

Allowed standard-library imports may include:

```text
hashlib
json
math
os
pathlib
stat
subprocess
sys
tempfile
typing
statistics
```

Use only the subset actually needed.

The analyzer must not import:

```text
numpy
pandas
scipy

psi_trs
research.brainvision.psi_trs

algebraic_n64_f3_evaluator_v0_1
research.brainvision.algebraic_n64_f3_evaluator_v0_1

algebraic_n64_f3_frozen_identity_v0_1
research.brainvision.algebraic_n64_f3_frozen_identity_v0_1

witness_canonical_json_v0_1
research.brainvision.witness_canonical_json_v0_1

torment_service
```

It must not dynamically import, execute, inspect, or invoke those modules.

It must not call or reference as executable functions:

```text
psi_trs_features
build_production_feature_cache
evaluate_from_feature_cache
```

Importing the analyzer module must:

```text
perform no filesystem read
perform no filesystem write
perform no audit calculation
create no directory
print nothing
contact no descriptor
```

The single allowed use of `subprocess` is invoking read-only Git plumbing for the repository-state and source-identity gate in §8. It must never be used for descriptor contact, evaluator invocation, or any write operation.

---

## 4. Recommended analyzer structure

Authorized pure and testable functions correspond to:

```text
canonical_json_bytes(value)
sha256_bytes(data)
whole_file_sha256(path)

resolve_and_validate_repository_state(...)
validate_analyzer_source_identity(...)

validate_retained_envelope(envelope)
validate_retained_payload(payload)
validate_member_and_pair_coverage(payload)
validate_inverse_shift_classes(payload)

collapse_validated_inverse_shift_classes(...)
summarize_shift_class_distribution(...)
summarize_blocking_classes(...)
summarize_ab_shiftwise_asymmetry(...)
summarize_blocking_per_start(...)
summarize_recursive_companion(...)

select_pair_classification(...)
select_family_disposition(...)

build_audit_payload(...)
build_audit_envelope(...)
render_operator_summary(...)

run_audit(...)
write_derived_artifacts_exclusively(...)
main(...)
```

Names may differ slightly where necessary, but responsibilities must remain cleanly separated.

Audit mathematics must be pure over already-loaded retained JSON objects.

Filesystem operations must be isolated from calculation functions.

---

## 5. Exact retained input binding

Default retained input:

```text
research/brainvision/results/algebraic_n64_primary_v0_1_f3_evaluation_v0_1/
  algebraic_n64_primary_v0_1_f3_evaluation_result.json
```

Expected size:

```text
10,784,993 bytes
```

Expected whole-file SHA-256:

```text
51e7cd8087050428c2559262764044624fcb84e19576b5f682bae3ca5b59fd7b
```

Expected top-level key set exactly:

```text
family_evaluation_result
family_evaluation_result_sha256
```

Expected payload bindings:

```text
schema_name =
torment_brainvision_algebraic_n64_f3_family_evaluation

schema_version =
0.1

execution_commit_identity =
c4f489c439d4190611e8e0c5b3034ead3353c26d

family_verdict =
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY

pair order =
[478, 479, 480]

valid_run =
True

replay byte_identical =
True
```

Canonical payload identity must be recomputed locally with standard-library JSON:

```python
json.dumps(
    payload,
    ensure_ascii=True,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

No trailing newline enters payload hashing.

Any input mismatch must cause a structured refusal before audit calculations.

---

## 6. Retained-file read policy

The implementation may inspect the retained canonical JSON read-only during development only to confirm nested schema paths and validation assumptions.

That permission does not authorize:

```text
executing the complete audit over the retained file
calculating or reporting the final retained-family audit metrics
constructing a final retained-family disposition
writing derived retained-family artifacts
```

Tests may open the retained canonical file only for preflight checks such as:

```text
regular non-symlink file
expected path
expected size
expected whole-file SHA-256
valid JSON
exact envelope keys
payload-hash agreement
bound schema and execution identities
```

A retained-input preflight test must stop before invoking the complete audit calculation function.

The final retained-family audit execution requires a later separate docs-only execution authorization after source review and source-identity freeze.

---

## 7. Audit-specific execution gate

The future command-line execution path must be closed by default.

The new audit-specific environment gate is:

```text
ALGEBRAIC_N64_F3_ASYMMETRY_AUDIT_AUTHORIZED
```

Required future value:

```text
1
```

This is not the F3 evaluation gate and grants no descriptor authority. In particular, it is distinct from and must never be confused with:

```text
ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED
```

During implementation and tests:

```text
the gate may be simulated only in temporary-directory synthetic tests
the real retained audit must not be run
```

Without the exact gate, the zero-argument CLI must refuse before loading the retained input or creating any output.

The later execution authorization will specify the exact one-run command and source identities.

---

## 8. Repository-state and source-identity gate

The future zero-argument execution path must resolve and validate repository state before loading the retained input.

Required repository state:

```text
repository root =
the Git top-level directory containing the committed analyzer path

required branch =
main

required repository agreement =
HEAD == origin/main

required working-tree state =
clean, including ordinary untracked files
```

The implementation must resolve the full 40-character lowercase SHA for:

```text
audit_execution_commit_identity =
git rev-parse HEAD
```

It must verify that the analyzer is committed at:

```text
research/brainvision/analyze_algebraic_n64_f3_asymmetry_v0_1.py
```

and that its local bytes agree with its Git object at `HEAD`.

Any repository, branch, synchronization, cleanliness, committed-path, or local-byte mismatch must refuse before loading the retained input and before creating any output.

`source_implementation_authorization_commit_identity` must be filled with the full commit SHA of this authorization after it is committed and before implementation begins.

The later execution authorization will bind the exact audit execution commit and analyzer source identities.

Do not confuse:

```text
input_execution_commit_identity =
the historical c4f489c F3 evaluation commit

audit_execution_commit_identity =
the synchronized HEAD under which the read-only audit executes
```

---

## 9. Output boundary

Future derived-output directory:

```text
research/brainvision/results/
  algebraic_n64_primary_v0_1_f3_asymmetry_audit_v0_1/
```

Future files:

```text
algebraic_n64_primary_v0_1_f3_asymmetry_audit_result.json

algebraic_n64_primary_v0_1_f3_asymmetry_audit_summary.txt
```

The implementation may include publication code, but it must not create this real directory during implementation or tests.

Publication tests must use temporary directories only.

Future real publication must use:

```text
exclusive creation
staging directory
exact two-file artifact set
atomic staging-to-final rename
refusal if final or staging path already exists
```

No write is permitted inside the retained F3 evaluation directory.

---

## 10. Deterministic machine result

The future result must contain at least:

```text
schema_name
schema_version
input_relative_path
input_size_bytes
input_whole_file_sha256
input_payload_sha256
input_execution_commit_identity
audit_execution_commit_identity
source_findings_commit_identity
source_audit_specification_commit_identity
source_implementation_authorization_commit_identity
analyzer_git_blob_sha
analyzer_raw_file_sha256

audit_configuration
audit_configuration_sha256

pair_order
member_order
variant_order

input_validation
inverse_shift_validation
member_audit_tables
pair_audit_tables
recursive_companion_tables
pair_classifications
family_disposition

authoritative_f3_verdict_preserved
non_claim_boundary
```

Bind:

```text
source_findings_commit_identity =
f0c5fdbc6f75e3749323de9e2b13c77b3710df82

source_audit_specification_commit_identity =
db82ec06faf398d52a002ba56f976e91045d12a4
```

`audit_execution_commit_identity`, `analyzer_git_blob_sha`, and `analyzer_raw_file_sha256` are resolved at execution time under the §8 repository-state and source-identity gate. `source_implementation_authorization_commit_identity` is the full commit SHA of this authorization, filled after it is committed.

The machine result must contain no:

```text
timestamp
duration
hostname
username
absolute path
process ID
random value
environment-dependent ordering
scientific interpretation
new F3 verdict
```

---

## 11. Failure and refusal behavior

The implementation must use a stable audit-specific failure namespace and version.

Recommended namespace:

```text
torment_brainvision_algebraic_n64_f3_asymmetry_audit_v0_1
```

At minimum it must distinguish:

```text
AUDIT_NOT_AUTHORIZED
REPOSITORY_STATE_INVALID
SOURCE_IDENTITY_FAILURE
INPUT_PATH_INVALID
INPUT_FILE_MISSING
INPUT_FILE_NOT_REGULAR
INPUT_FILE_SYMLINK
INPUT_SIZE_MISMATCH
INPUT_WHOLE_FILE_HASH_MISMATCH
INPUT_JSON_INVALID
INPUT_ENVELOPE_INVALID
INPUT_PAYLOAD_HASH_MISMATCH
INPUT_SCHEMA_MISMATCH
INPUT_EXECUTION_IDENTITY_MISMATCH
INPUT_REPLAY_STATUS_INVALID
INPUT_VALIDITY_INVALID
INPUT_PAIR_ORDER_MISMATCH
INPUT_FAMILY_VERDICT_MISMATCH
INPUT_COVERAGE_INVALID
INPUT_VALUE_NONFINITE
INVERSE_SHIFT_VALIDATION_FAILURE
AUDIT_CALCULATION_FAILURE
CANONICAL_SERIALIZATION_FAILURE
OUTPUT_PATH_EXISTS
PUBLICATION_FAILURE
```

Preflight failures must produce no derived output directory.

Synthetic calculation validation failures must return structured failure objects rather than partial disposition claims.

No failure may trigger descriptor contact or F3 rerun.

---

## 12. Refusal, disposition-D, and process-failure classification

### 12.1 Pre-audit refusal

The following are refusals and produce no derived output directory:

```text
wrong or absent audit gate
CLI arguments
repository-state failure
source-identity failure
input path invalid
input missing
input not regular
input symlink
input size mismatch
input whole-file hash mismatch
invalid JSON
invalid envelope key set
input payload-hash mismatch
schema mismatch
historical execution-identity mismatch
replay-status mismatch
validity mismatch
pair-order mismatch
family-verdict mismatch
final path already exists
staging path already exists
```

These conditions do not produce disposition D because no accepted retained-evidence audit begins.

### 12.2 Complete descriptive disposition D

After all identity, envelope, historical-result, repository, and output-path preflight checks pass, the following retained-content validation outcomes produce a complete deterministic audit result with:

```text
family_disposition =
D. RETAINED EVIDENCE IS INSUFFICIENT OR INTERNALLY INCONSISTENT
```

Examples:

```text
required member or pair coverage internally inconsistent
required retained response missing
retained response count invalid
retained response value nonfinite
inverse-shift distance multiset mismatch
q=32 self-inverse structure invalid
other frozen audit-validation inconsistency
```

A disposition-D result must:

```text
set audit_valid = False
record ordered failure codes
retain all available raw diagnostics
omit or null unavailable class-collapsed metrics
make no A/B/C claim
preserve the authoritative F3 negative verdict
```

### 12.3 Process failure

Unexpected implementation exceptions, canonical serialization failure, filesystem failure, publication failure, and stdout failure are process failures. They must not be converted into disposition D.

Synthetic invalid fixtures must test all three categories separately.

---

## 13. Exit, publication, and retention contract

Exit-code contract:

```text
exit 0:
complete exact two-file atomic publication of a deterministic audit result
with family disposition A, B, C, or D

exit 1:
unexpected audit-calculation failure
canonical serialization failure
staging write failure
publication or rename failure
post-publication stdout failure

exit 2:
pre-audit refusal
```

```text
exit 0 does not imply scientific success
A/B/C/D are descriptive audit dispositions only
the authoritative F3 verdict remains unchanged
```

Frozen publication behavior:

```text
all audit calculations complete in memory before staging creation
both canonical result bytes and summary bytes complete in memory before staging creation
exclusive staging-directory creation
exclusive binary file creation
exact two-file staged set
single staging-to-final rename
never overwrite
never merge
never resume automatically
```

Failure retention:

```text
an empty staging directory created before any artifact byte is written may be removed

once any derived artifact byte is written, staging is evidence-bearing and must be retained after failure

complete staging must be retained after rename failure

a published final directory must never be rolled back or deleted

stdout failure after successful publication returns exit 1 but preserves the final directory
```

No implementation path may automatically retry calculation, serialization, writing, or rename.

On successful publication, stdout must mirror the operator summary exactly.

Stderr is reserved for refusals, process failures, retained-staging diagnostics, and post-publication stdout failure.

No progress meter, duration, timestamp, or periodic status output is authorized.

---

## 14. Required implementation tests

The test module must cover at least the following.

### 14.1 Import and source boundary

```text
module import is inert
no forbidden imports
no forbidden function calls
no torment_service import
no PsiTRS contact
standard-library-only source
```

Use AST or source inspection where appropriate.

### 14.2 Canonical serialization

```text
sorted keys
compact separators
ASCII escaping
allow_nan=False behavior
no trailing newline
stable SHA-256
negative zero handling if implemented
```

### 14.3 Envelope and input validation

```text
exact accepted envelope
extra top-level key refusal
missing top-level key refusal
payload-hash mismatch
schema mismatch
execution identity mismatch
replay mismatch
validity mismatch
pair-order mismatch
family-verdict mismatch
nonfinite retained value refusal
```

### 14.4 Inverse-shift validation

```text
q and 64-q exact sorted-distance multiset agreement
different original ordering accepted when sorted multisets agree
missing inverse shift refused
distance count other than 64 refused
nonfinite distance refused
multiset mismatch refused
q=32 handled as self-inverse
canonical representative is q
inverse pairs are never averaged
```

### 14.5 Deterministic metrics

```text
cross insertion rank
strict-greater semantics
equal values not counted as greater
descending-value then ascending-q tie ordering
99/95/90 percent-of-maximum counts
top-2 and top-5 lists are ordered objects, not averages
top-8 and top-16 contribution shares
zero-total contribution behavior
positive and negative aligned-start ordering
fewer-than-eight sign-matching behavior
```

### 14.6 Pair and family classification

```text
blocking_class_count 0, 2 => narrow
blocking_class_count 3, 7 => intermediate
blocking_class_count 8, 32 => broad

all narrow => disposition A
all broad => disposition B
mixed or any intermediate => disposition C
any validation failure => disposition D
```

### 14.7 Pure synthetic end-to-end audit

Construct a complete minimal synthetic retained-result fixture sufficient to exercise:

```text
six members
two variants
three pairs
32 inverse classes represented by raw shifts 1..63
64 per-start distances where required
cross responses
recursive companion
all deterministic output tables
```

The fixture may use highly repetitive values to remain readable.

Run the pure audit twice and require byte-identical canonical output.

### 14.8 Filesystem publication in temporary directories

```text
default-closed gate
wrong gate refusal
correct simulated audit gate
input opened read-only
final-path-exists refusal
staging-path-exists refusal
exclusive file creation
exact two-file staging set
atomic staging-to-final rename
no retained-input mutation
```

Use synthetic fixtures and temporary paths only.

### 14.9 Retained canonical preflight only

Permit one read-only test of the actual retained canonical JSON that verifies only:

```text
path
regular non-symlink status
size
whole-file SHA-256
JSON parse
envelope
payload SHA-256
schema
execution identity
replay status
validity
pair order
family verdict
```

The test must not invoke complete audit calculations or create derived output.

It should skip clearly when the gitignored retained artifact is unavailable in another environment.

---

## 15. Test injection and real-path protection

The analyzer must expose a testable internal execution function whose repository root, input path, final path, staging path, gate value, and output stream objects can be injected directly by tests.

The actual command-line surface remains:

```text
zero arguments only
real repository-relative defaults only
closed by default behind:
ALGEBRAIC_N64_F3_ASYMMETRY_AUDIT_AUTHORIZED=1
```

No test may execute the actual zero-argument retained-family audit path with the real audit gate.

The test module must include an autouse or equivalent test guard that fails immediately on any attempt to:

```text
write to the real audit final directory
write to the real audit staging directory
write anywhere inside the retained F3 evaluation directory
run complete audit calculations using the real retained canonical JSON
invoke the real zero-argument CLI with the audit gate enabled
```

Exactly one clearly marked retained-preflight test may read the real retained JSON.

For that retained-preflight test:

```text
the complete-audit entry point must be patched to raise if invoked
all publication functions must be patched to raise if invoked
the audit gate must remain unset
the real audit final and staging directories must remain absent
```

Repository-state and source-identity tests must use temporary Git repositories.

Publication tests must use temporary input, final, and staging paths only.

Add explicit tests for:

```text
audit_execution_commit_identity capture
wrong branch refusal
HEAD/origin mismatch refusal
dirty tracked refusal
ordinary untracked-file refusal
uncommitted analyzer refusal
local analyzer-byte mismatch refusal
exit 0 / 1 / 2 mapping
disposition D publication
preflight refusal creates no output
evidence-bearing staging retention
rename-failure staging retention
published final survives stdout failure
real-path protection
```

---

## 16. Source and repository boundaries

Implementation must not touch:

```text
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

It must not modify:

```text
the F3 evaluator
the F3 runner
the frozen identity
the freezer
the generator
the verifier
the canonical retained artifacts
the audit specification
the findings record
```

Only the two authorized implementation files may be created.

---

## 17. Required review state after implementation

After implementation and testing, the implementer must return:

```text
created file paths
concise architecture summary
focused test command
focused test result
wider relevant research test result if practical
git status --short
raw-byte SHA-256 of analyzer source
raw-byte SHA-256 of test source
confirmation that no retained audit execution occurred
confirmation that the real audit output directory remains absent
confirmation that retained F3 artifact hashes remain unchanged
```

Implementation must not be committed until GPT and Codex complete focused review.

---

## 18. Authority state

Upon committed and synchronized acceptance of this document:

```text
F3_EVALUATION_COMPLETE = True
F3_RERUN_AUTHORIZED = False

READ_ONLY_ASYMMETRY_AUDIT_SPECIFIED = True
READ_ONLY_ASYMMETRY_AUDIT_IMPLEMENTATION_AUTHORIZED = True
READ_ONLY_ASYMMETRY_AUDIT_TEST_EXECUTION_AUTHORIZED = True
READ_ONLY_ASYMMETRY_AUDIT_RETAINED_PREFLIGHT_AUTHORIZED = True
READ_ONLY_ASYMMETRY_AUDIT_EXECUTION_AUTHORIZED = False

REAL_AUDIT_OUTPUT_CREATION_AUTHORIZED = False
PSITRS_CONTACT_AUTHORIZED = False
DESCRIPTOR_RECOMPUTATION_AUTHORIZED = False
RETAINED_EVIDENCE_MODIFICATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

`FORMAL_HOLD` and `Mode_0` remain active.

---

## 19. Disposition

```text
A. AUTHORIZE STANDALONE READ-ONLY ASYMMETRY AUDIT ANALYZER IMPLEMENTATION
```

A later document must separately authorize the one-run retained-family audit execution, after:

```text
this authorization is accepted, committed, and pushed
the two authorized files are implemented
non-contact and preflight-only tests pass
one focused adversarial implementation review finds no blocker
the analyzer and test source identities are frozen
```

Recommended commit subject after focused review:

```text
docs(research): authorize frozen N64 F3 asymmetry audit implementation
```

No analyzer was implemented while preparing this authorization. No audit calculation was executed. No audit output directory was created. The audit-specific gate and the F3 evaluation gate both remained unset. No descriptor or feature cache was recomputed. No PsiTRS contact occurred. The retained canonical F3 artifacts were not modified. The production TORMENT kernel remained untouched.

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Read-Only Asymmetry Audit Implementation Authorization v0.1. Docs-only during preparation. Authorizes implementation of exactly two standalone files plus non-contact, temporary-directory, and read-only-preflight testing. It does not authorize the retained-family audit execution, real audit output creation, PsiTRS contact, descriptor recomputation, F3 reevaluation, or any rescue of the authoritative negative verdict.*
