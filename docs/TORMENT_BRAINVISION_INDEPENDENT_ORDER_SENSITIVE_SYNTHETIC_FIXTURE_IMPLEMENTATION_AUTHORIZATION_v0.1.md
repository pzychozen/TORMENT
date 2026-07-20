# TORMENT Brainvision Independent Order-Sensitive Synthetic Fixture Implementation Authorization v0.1

## Document status

```text
document_type = docs-only authorization
authorization_version = v0.1
stage = S1B implementation authorization
implementation_authorized = docs-only authorization of the five listed files
execution_authorized = False
```

Authoritative repository baseline:

```text
HEAD = origin/main = 7c7f21a
working tree = clean
```

Committed governing documents:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md

docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SPECIFICATION_v0.1.md
```

This document authorizes the later S1B implementation of the synthetic-control infrastructure specified by the committed S1A fixture-freeze specification. It does not amend either governing specification, and it does not open any S1C freeze-execution or challenger-execution authority.

## 0. Historical and authority boundary

The completed frozen N64/K=3 F3 result remains permanently:

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Preserve:

```text
FORMAL_HOLD = active
Mode_0 = active
```

This authorization concerns only independent synthetic-control infrastructure. It does not amend, rescue, reinterpret, rerun, or replace F3. A future synthetic freeze produces preregistered controls only; nothing in this branch changes the completed F3 verdict.

## 1. Exact authorization disposition

At acceptance of this document, the authority state is:

```text
SYNTHETIC_FIXTURE_FREEZE_SPECIFIED = True
SYNTHETIC_FIXTURE_IMPLEMENTATION_AUTHORIZATION_SPECIFIED = True

SYNTHETIC_FIXTURE_GENERATOR_IMPLEMENTATION_AUTHORIZED = True
SYNTHETIC_FIXTURE_VERIFIER_IMPLEMENTATION_AUTHORIZED = True
SYNTHETIC_FIXTURE_FREEZER_LIBRARY_IMPLEMENTATION_AUTHORIZED = True
SYNTHETIC_FIXTURE_TEST_IMPLEMENTATION_AUTHORIZED = True
SYNTHETIC_FIXTURE_BOUNDED_UNIT_TEST_EXECUTION_AUTHORIZED = True
```

The following remain closed:

```text
SYNTHETIC_FIXTURE_CANONICAL_SEED_SCAN_AUTHORIZED = False
SYNTHETIC_FIXTURE_GENERATION_AUTHORIZED = False
SYNTHETIC_FIXTURE_EXECUTION_AUTHORIZED = False
SYNTHETIC_FIXTURE_FREEZE_AUTHORIZED = False
SYNTHETIC_FIXTURE_AUTHORITATIVE_REPLAY_AUTHORIZED = False
SYNTHETIC_FIXTURE_FINAL_MANIFEST_WRITE_AUTHORIZED = False
SYNTHETIC_FIXTURE_RESULT_PUBLICATION_AUTHORIZED = False

CHALLENGER_IMPLEMENTATION_AUTHORIZED = False
CHALLENGER_SYNTHETIC_VALIDATION_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_INPUT_ACCESS_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_EVALUATION_AUTHORIZED = False

PSITRS_CONTACT_AUTHORIZED = False
RETAINED_EVIDENCE_MODIFICATION_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

Bounded unit tests are not an authoritative fixture-generation or freeze execution. Executing bounded, injected-input unit tests over the implemented library functions does not scan the canonical seed space, does not discover the actual first eight generated fixtures, does not freeze a synthetic family, and does not publish any authoritative manifest. Those actions remain closed and require the separate later S1C authorization.

## 2. Exact authorized files

Creation or modification is authorized only for exactly these five future implementation files:

```text
research/brainvision/independent_order_sensitive_synthetic_fixture_verifier_v0_1.py

research/brainvision/independent_order_sensitive_synthetic_fixture_generator_v0_1.py

research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py

research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_verifier_v0_1.py

research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

No runner, CLI, generated manifest, retained result, fixture output, or execution-gate file is authorized.

No `if __name__ == "__main__":` execution entry point is authorized.

No file outside the five listed paths may be modified during S1B without a new docs-only amendment.

## 3. Module responsibilities

### 3.1 Verifier module

The verifier module owns only pure exact mathematical operations:

```text
support validation and normalization
support-to-binary conversion
periodic A2
step-one transition table
direct labeled M3 array in fixed L3 order
triple disagreement indices
affine support transformation
support complement
affine equivalence
affine-plus-complement equivalence
member_orbit_key
pair_duplicate_key
fixed-fixture verification
generated-pair eligibility evaluation
ordered first-failure eligibility diagnostics
```

It must not import or call the challenger descriptor.

It must not perform filesystem I/O, environment reads, Git calls, subprocess calls, network access, or production contact.

### 3.2 Generator module

The generator module owns:

```text
canonical seed-tuple iteration
C+D and C-D support construction
collision collapse
canonical eligibility-check sequencing
fixed_pair_duplicate_key seeding
seen_pair_keys handling
eligible duplicate diagnostics
first-eight acceptance order
search diagnostics
seed-space exhaustion handling
pure ordered scan-record reduction
```

The generator module must expose one pure reducer:

```text
reduce_scan_records
```

or an equivalently named function with the exact contract specified in §6.

`scan_seed_stream` must use this reducer for duplicate handling, acceptance ordering, first-eight stopping, and search diagnostics.

The implementation must not maintain a second, behaviorally independent copy of that reduction logic.

It may depend only on the verifier module and permitted Python standard-library modules.

It must not serialize or write authoritative manifests.

### 3.3 Freeze-library module

The freeze-library module owns pure library functions for:

```text
exact manifest-object construction
canonical field and nested-object order
canonical compact JSON bytes
manifest payload projection
manifest_payload_sha256 population
external manifest SHA-256 calculation
candidate-pass comparison
deterministic family_frozen finalization
canonical failure-manifest construction where permitted
source/configuration identity validation
static boundary validation from supplied source paths and source text
```

It must not execute the canonical seed scan on import.

It must not read Git, environment variables, retained evidence, frozen-family inputs, or production paths.

Source identities, configuration identities, Python version, source paths, and source text must be explicit function inputs.

It must return data objects or bytes only. It must not write a manifest to disk.

## 4. Exact dependency boundary

All implementation code must be Python standard-library only.

This standard-library-only requirement applies to all five authorized files, including both test files.

Test source may use `unittest` or plain assertions from the Python standard library.

The test files must not import `pytest` or any other non-standard-library package.

Running the test files through an external `pytest` command is permitted only when the test source itself imports no pytest API and remains standard-library-only.

Permit only modules needed for exact deterministic work, such as:

```text
ast
copy
hashlib
itertools
json
math
typing
collections
dataclasses
```

Not all listed imports are required.

Prohibit:

```text
numpy
scipy
pandas
requests
urllib
http
socket
subprocess
importlib
dynamic __import__
random
secrets
time
datetime
uuid
locale
platform
camera or screen-capture packages
torment_service
PsiTRS modules
historical F3 modules
historical asymmetry-audit modules
independent_order_sensitive_descriptor_v0_1
```

If `os` or `pathlib` is used for type-safe path normalization in test or boundary-validation code, it must not be used for environment reads, directory discovery, unrestricted traversal, or runtime evidence access.

## 5. Public implementation contracts

Require explicit typed functions or equivalent exact interfaces for at least:

```text
normalize_support
support_to_binary
periodic_autocorrelation
step_one_transition_table
direct_triple_array
triple_disagreement_indices
affine_support
complement_support
member_orbit_key
pair_duplicate_key
verify_fixed_fixture
evaluate_pair_eligibility

iter_canonical_seed_tuples
construct_pair_from_seed
scan_seed_stream
reduce_scan_records

build_candidate_manifest
canonical_payload_bytes
populate_manifest_payload_hash
canonical_manifest_bytes
external_manifest_sha256
compare_candidate_passes
finalize_authoritative_manifest
build_fixed_fixture_failure_manifest
build_seed_exhaustion_failure_manifest
validate_source_boundary
```

Equivalent naming is allowed only when the implementation preserves one-to-one responsibility and the exact governing contracts.

Every function must have deterministic input validation.

Boolean values must not be silently accepted where exact integer inputs are required.

No function may accept candidate `[478, 479, 480]` identifiers, F3 outputs, retained responses, or challenger descriptor values.

## 6. Bounded unit-test authority

Bounded implementation tests may execute only:

```text
fixed-fixture reconstruction and certificate checks
the exact 288-of-3906 fixed-fixture disagreement check
hand-authored valid and invalid supports
hand-authored affine and complement cases
bounded prefixes of canonical seed iteration
injected finite seed streams
collision-collapse cases
all eight first-failure diagnostic branches
member-orbit-key checks
pair-key slot-exchange checks
fixed-fixture-key duplicate suppression
generated duplicate suppression
manifest schema and key-order checks
payload and manifest hashing
candidate-pass equality and mismatch
family_frozen finalization
canonical fixed-fixture failure manifest
canonical seed-exhaustion failure manifest
static prohibited-import checks
source-ownership checks
no-challenger-import checks
```

Bounded prefixes of the canonical seed iterator are permitted only for iterator-determinism and ordering checks.

For S1B, a bounded prefix of `iter_canonical_seed_tuples()` means at most the first 16 yielded seed tuples.

No S1B test may request, consume, cache, retain, or inspect more than 16 tuples from the canonical iterator.

A test must stop iteration immediately after obtaining the required prefix and must not continue consuming the iterator for diagnostics or cleanup.

Boundary-transition behavior beyond that prefix must be tested with hand-authored injected finite seed streams, not by consuming a longer canonical prefix.

Acceptance, first-eight, and duplicate-suppression behavior must be exercised through injected finite seed streams, so that the actual first eight generated fixtures are never discovered.

`scan_seed_stream` must accept an explicit iterable containing seed tuples only.

Each seed tuple is exactly:

```text
(c1, c2, d1, d2)
```

with four exact integers.

`scan_seed_stream` must reject a supplied seed deterministically when:

```text
the item is not a tuple
tuple length is not exactly 4
any element is a bool
any element is not an integer
c1, c2, d1, or d2 is outside 1..63
c1 >= c2
d1 >= d2
```

Seed-shape predicates are evaluated in the exact order above using first-failure semantics.

A seed-shape failure is an expected invalid generator input.

It must return a deterministic generator diagnostic/result with:

```text
valid = false
failure_code = SEED_ENUMERATION_FAILURE
failure_stage = seed_validation
```

It must not construct supports, evaluate eligibility, create a scan record, accept a fixture, or raise a freeze-level process failure.

Boolean values must be rejected before the general integer check.

For every supplied tuple, `scan_seed_stream` must invoke the real:

```text
construct_pair_from_seed
evaluate_pair_eligibility
pair_duplicate_key
duplicate-diagnostic logic
acceptance-order logic
```

Tests must not inject into `scan_seed_stream`:

```text
precomputed supports
binary sequences
eligibility booleans
rejection reasons
member-orbit keys
pair-duplicate keys
acceptance outcomes
fixture records
manifest records
```

Lower-level verifier tests may use hand-authored supports directly, but those are not generator scan, duplicate-suppression, acceptance-order, or first-eight tests.

Injected finite seed streams used for acceptance tests must be explicitly listed in test source and must not be generated by consuming more than the authorized 16-tuple canonical prefix.

Successful eight-acceptance stopping behavior must not be tested by searching for or requiring eight real eligible canonical seeds unless those seeds have first been separately authorized in a docs-only test-fixture specification.

During S1B, successful first-eight stopping must instead be tested through the pure:

```text
reduce_scan_records
```

function using hand-authored synthetic scan records.

This reducer test is not a canonical-seed scan, is not a `scan_seed_stream` test, and must not be represented as generated-family discovery.

A synthetic scan record has exactly these fields in this order:

```text
seed_tuple
eligible
eligibility_rejection_reason
pair_duplicate_key
fixture_record
```

For an eligible synthetic record:

```text
eligible = true
eligibility_rejection_reason = null
pair_duplicate_key = a hand-authored key satisfying the exact two-key contract below
fixture_record = a hand-authored ordered mapping satisfying the exact fixture-record contract below
```

For an ineligible synthetic record:

```text
eligible = false
eligibility_rejection_reason = one canonical eligibility-rejection reason
pair_duplicate_key = null
fixture_record = null
```

### Synthetic scan-record validation

The public input form accepted by `reduce_scan_records` is an ordered mapping with exactly these keys in exactly this iteration order:

```text
seed_tuple
eligible
eligibility_rejection_reason
pair_duplicate_key
fixture_record
```

No additional key is permitted.

A typed internal representation may be used only after the public ordered mapping has passed this validation and has been normalized without changing any field value.

Malformed synthetic scan records are programming or test-record defects, not mathematical ineligibility.

`reduce_scan_records` must validate each synthetic scan record completely before applying duplicate, acceptance, seen-key, or diagnostic reduction logic.

A malformed synthetic scan record terminates reduction immediately.

No record after the malformed record may be requested or consumed.

The malformed record must not:

```text
be accepted
be appended to accepted records
increment eligible_duplicate_count
increment an eligibility-rejection count
alter seen_pair_keys
alter accepted-fixture order
produce DUPLICATE_PAIR_KEY
produce DUPLICATE_KEY_FAILURE
produce SEED_ENUMERATION_FAILURE
```

The deterministic reducer result must have:

```text
valid = false
failure_code = GENERATOR_CONFIGURATION_INVALID
failure_stage = scan_record_validation
```

and must retain only the valid reduction state completed before the malformed record.

The malformed record itself is not included in accepted records or ordinary search diagnostics.

Synthetic scan-record predicates are evaluated with first-failure semantics in this exact order:

```text
1. record is not an ordered mapping
2. key set is not exactly:
   seed_tuple,
   eligible,
   eligibility_rejection_reason,
   pair_duplicate_key,
   fixture_record
3. key iteration order is not exactly the declared order
4. seed_tuple does not satisfy the exact seed-tuple contract defined earlier in §6
5. eligible is not exactly the JSON-style boolean true or false
6. eligible = true and eligibility_rejection_reason is not null
7. eligible = true and pair_duplicate_key is malformed
8. eligible = true and fixture_record is malformed
9. eligible = false and eligibility_rejection_reason is not one canonical eligibility-rejection reason
10. eligible = false and pair_duplicate_key is not null
11. eligible = false and fixture_record is not null
```

For this test-only reducer contract, a valid `pair_duplicate_key` is exactly a two-element tuple:

```text
(key_0, key_1)
```

where:

```text
key_0 and key_1 are strings
each string contains exactly 64 ASCII characters
every character is either "0" or "1"
key_0 < key_1 lexicographically
```

Equality is not permitted because eligible pair members must be nuisance-orbit inequivalent.

A valid eligible `fixture_record` is an ordered mapping that:

```text
is nonempty
contains a field named pair_duplicate_key
has fixture_record["pair_duplicate_key"] exactly equal to the enclosing scan record's pair_duplicate_key
```

The reducer treats all other fixture-record fields as opaque carried data.

It must preserve the complete fixture record unchanged when the record is accepted.

This minimum validation permits the same reducer to carry:

```text
hand-authored synthetic test fixture records
real fixture records constructed by scan_seed_stream
```

without duplicating manifest-schema validation inside the reducer.

The canonical eligibility-rejection reason vocabulary is exactly:

```text
A_CARDINALITY_NOT_9
B_CARDINALITY_NOT_9
IDENTICAL_SUPPORTS
A2_MISMATCH
TRANSITION_TABLE_MISMATCH
AFFINE_EQUIVALENT
AFFINE_COMPLEMENT_EQUIVALENT
TRIPLE_ARRAY_EQUAL
```

No other string is accepted.

A malformed synthetic scan record must return the deterministic reducer result described above. It must not raise `SyntheticFixtureProcessFailure`, because scan-record validation is an expected bounded-test and generator-configuration boundary rather than a serialization, hash, source-boundary, replay, or finalization process failure.

`reduce_scan_records` must accept:

```text
an explicit iterable of synthetic scan records
an explicit initial seen-pair-key set
acceptance_limit = 8
```

It must:

```text
process records in supplied order
apply the real duplicate-key diagnostic logic
apply the real acceptance-order logic
stop immediately after eight acceptances
consume no later record after the eighth acceptance
return deterministic accepted records and search diagnostics
```

Tests may use the verified fixed-fixture key as an initial seen key or a hand-authored synthetic stand-in key.

No synthetic reducer record may be published, retained as evidence, or confused with a generated fixture.

`scan_seed_stream` coverage must separately prove that supplied seed tuples invoke the real construction, eligibility, pair-key, duplicate-diagnostic, and acceptance-order pipeline.

For each real seed processed by `scan_seed_stream`, the pipeline must construct the corresponding scan record and pass it through the same `reduce_scan_records` logic used by the synthetic reducer tests.

Unit tests must not:

```text
scan the complete canonical seed space
discover the actual first eight generated fixtures
emit or retain the authoritative synthetic family
produce family_frozen = true as a project artifact
write any manifest outside temporary test storage
contact frozen candidates [478, 479, 480]
import or execute the challenger descriptor
```

Testing finalization with `family_frozen = true` is permitted only for an in-memory or temporary synthetic test object that is not produced from the canonical seed scan and is not retained as evidence.

Tests must use in-memory objects by default.

Operating-system temporary directories may be used only when bytes-on-disk behavior is itself the unit under test.

Temporary outputs must be automatically cleaned up before test completion.

Tests must never write temporary manifests, fixture outputs, replay outputs, or other generated artifacts anywhere under the repository tree.

Temporary outputs must never be treated as project evidence, retained results, frozen fixtures, or publishable artifacts.

Python bytecode caches and ordinary external test-runner caches are not scientific artifacts, but the operator must ensure that no unauthorized tracked, retained, staged, committed, or published project output is introduced.

## 7. Canonical scan protection

The implementation must not accidentally perform full generation through:

```text
module import
test collection
fixture setup
default function arguments
global initialization
object construction
serializer construction
static boundary scan
```

The canonical seed iterator must be lazy.

The function that scans a seed stream must require an explicit iterable input.

No zero-argument convenience function that automatically scans the complete canonical seed space is authorized during S1B.

The actual S1C runner and its one-run or two-pass execution authority require a later docs-only authorization.

## 8. Exact manifest implementation boundary

The code must implement the committed S1A manifest schema exactly.

It must not add fields, reorder fields, collapse A/B evidence, replace exact arrays with hashes, or weaken failure behavior.

Candidate pass manifests must use:

```text
family_frozen = false
```

Only the pure finalization function may return a manifest with:

```text
family_frozen = true
```

The function must change only `family_frozen`, then recompute:

```text
canonical payload bytes
manifest_payload_sha256
canonical complete-manifest bytes
external manifest SHA-256
```

`compare_candidate_passes` must compare the complete S1A-required candidate evidence:

```text
canonical payload bytes
manifest_payload_sha256
canonical manifest bytes
external manifest SHA-256
accepted-fixture order
search diagnostics
```

Complete candidate-manifest byte equality may subsume structural equality, but accepted-fixture order and search-diagnostic comparisons must still be available as explicit deterministic comparison results for stable replay-mismatch classification.

For two structurally valid candidate-pass bundles, `compare_candidate_passes` must return one deterministic comparison result object with exactly these fields in this order:

```text
matches
failure_code
failure_stage
mismatch_reasons
```

For equal candidate passes:

```text
matches = true
failure_code = null
failure_stage = null
mismatch_reasons = []
```

For unequal candidate passes:

```text
matches = false
failure_code = REPLAY_MISMATCH
failure_stage = replay_comparison
```

and `mismatch_reasons` contains every applicable reason in this exact order:

```text
canonical_payload_bytes_mismatch
manifest_payload_sha256_mismatch
canonical_manifest_bytes_mismatch
external_manifest_sha256_mismatch
accepted_fixture_order_mismatch
search_diagnostics_mismatch
```

Reasons that do not apply are omitted without changing the order of retained reasons.

An ordinary, structurally valid candidate mismatch must not raise an exception.

A malformed candidate-pass bundle that prevents deterministic comparison must raise:

```text
SyntheticFixtureProcessFailure
failure_code = MANIFEST_SCHEMA_FAILURE
failure_stage = replay_comparison
```

`finalize_authoritative_manifest` must accept only a comparison result with:

```text
matches = true
```

Otherwise it raises:

```text
failure_code = REPLAY_MISMATCH
failure_stage = finalization
```

During S1B, replay mismatch testing remains in-memory or temporary-test behavior only. It does not authorize creation of an S1C execution envelope or authoritative replay artifact.

No authoritative final manifest may be written or retained during S1B.

## 9. Static boundary implementation

Require AST- or source-structure-based checks for:

```text
forbidden imports
dynamic imports
environment-gate reads
subprocess use
network access
camera or screen-capture imports
challenger descriptor imports
historical F3 imports
historical asymmetry-audit imports
torment_service imports
retained-evidence path literals
frozen K=3 path literals
source paths whose normalized repository-relative path is not exactly one of the five authorized paths in §2
unauthorized __main__ execution blocks
```

The boundary checker must operate from explicitly supplied normalized source paths and source text. It must not discover repository files itself.

Source-path normalization is lexical only.

Lexical normalization must use this exact algorithm:

1. Require the supplied path to be a nonempty string.
2. Replace every backslash character with `/`.
3. Reject the path when:
   - it begins with `/`;
   - it begins with `//`;
   - its first two characters are an ASCII letter followed by `:`.
4. Split the string on `/`.
5. Discard empty segments created by repeated separators.
6. Discard every `.` segment.
7. For each `..` segment:
   - remove the immediately preceding retained segment;
   - reject the path if no preceding retained segment exists.
8. Retain every other segment byte-for-byte.
9. Join retained segments with one `/`.
10. Reject an empty normalized result.
11. Compare the normalized result case-sensitively with the five forward-slash allowlist strings in §2.

The checker must not use `os.path.normpath`, `Path.resolve()`, or another platform-dependent path-normalization result.

The caller-supplied allowlist must itself equal the exact five-element §2 allowlist in the same order.

An omitted, reordered, altered, or expanded allowlist must produce:

```text
SOURCE_OWNERSHIP_FAILURE
```

with:

```text
failure_stage = source_boundary
```

The checker must receive:

```text
repository-relative source path
source text
the exact five-path allowlist from §2
```

as explicit inputs.

It must not:

```text
call Path.resolve()
follow symlinks
stat paths
walk directories
discover files
query Git
read environment variables
read repository files
inspect filesystem ownership
```

A source path is authorized only when its lexically normalized repository-relative path is exactly equal to one of the five §2 allowlist strings.

Membership in the broader `research/brainvision/` directory is not sufficient.

## 10. Failure handling

Implementation defects must use the committed ordered failure-code vocabulary.

Ordinary ineligible seeds and duplicate eligible seeds remain diagnostics, not failures.

No free-form exception text may enter a canonical manifest.

Programming exceptions may be used internally during development, but every exported function listed in §5 must expose deterministic public failure behavior.

Verifier and generator functions must return deterministic value or result objects for valid inputs and deterministic diagnostic or result objects for expected invalid mathematical inputs.

The following are the only S1B functions authorized to construct canonical failure manifests:

```text
build_fixed_fixture_failure_manifest
build_seed_exhaustion_failure_manifest
```

The following functions must never convert serialization, source-boundary, hash, comparison, replay, or finalization failures into canonical failure manifests:

```text
canonical_payload_bytes
populate_manifest_payload_hash
canonical_manifest_bytes
external_manifest_sha256
compare_candidate_passes
finalize_authoritative_manifest
validate_source_boundary
```

Those process-level failures must raise one dedicated deterministic exception type:

```text
SyntheticFixtureProcessFailure
```

or an equivalently named single-purpose type with the same exact contract.

The process-failure exception must expose:

```text
failure_code
```

as one canonical failure-code string from §16 of the committed `TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SPECIFICATION_v0.1.md`.

Every later reference in this authorization to the "§16 vocabulary" or "§16 code" must be understood as referring to §16 of that committed S1A fixture-freeze specification.

The process-failure exception must also expose:

```text
failure_stage
```

as exactly one value from this vocabulary:

```text
serialization
hash_identity
source_boundary
replay_comparison
finalization
```

Both `failure_code` and `failure_stage` are mandatory.

No free-form exception text may be serialized into a manifest or used as scientific evidence.

Tests must verify the exact exception type, exact `failure_code`, and exact `failure_stage`.

Expected invalid support or seed inputs that are already represented by verifier or generator diagnostic objects must not be converted into process-level exceptions.

Public process-failure mapping is fixed as follows.

```text
canonical_payload_bytes
canonical_manifest_bytes
```

must raise:

```text
failure_code = SERIALIZATION_FAILURE
failure_stage = serialization
```

when canonical serialization cannot be completed.

```text
populate_manifest_payload_hash
external_manifest_sha256
```

must raise:

```text
failure_code = HASH_IDENTITY_FAILURE
failure_stage = hash_identity
```

when hashing or hash-identity construction cannot be completed.

`validate_source_boundary` must raise exactly one applicable code:

```text
FORBIDDEN_IMPORT_DETECTED
SOURCE_OWNERSHIP_FAILURE
PROHIBITED_CHALLENGER_CONTACT
PROHIBITED_FROZEN_FAMILY_CONTACT
PRODUCTION_BOUNDARY_VIOLATION
```

with:

```text
failure_stage = source_boundary
```

When more than one source-boundary violation is present, the selected code must be the first applicable code in the committed S1A §16 vocabulary order.

`finalize_authoritative_manifest` may raise only:

```text
HASH_IDENTITY_FAILURE
```

with:

```text
failure_stage = hash_identity
```

when final payload or manifest identities cannot be recomputed, or:

```text
REPLAY_MISMATCH
```

with:

```text
failure_stage = finalization
```

when finalization is attempted without a successful candidate-pass comparison.

Expected invalid mathematical supports, ineligible pairs, malformed seed tuples, and ordinary duplicate seeds remain deterministic verifier or generator result objects and must not use `SyntheticFixtureProcessFailure`.

`finalize_authoritative_manifest` may return an in-memory finalization result bundle containing exactly, or through an equivalent typed structure:

```text
final_manifest_object
canonical_payload_bytes
manifest_payload_sha256
canonical_manifest_bytes
external_manifest_sha256
```

The bundle must not contain additional scientific or execution-envelope fields.

The external manifest SHA-256 must not be inserted into the canonical manifest object.

Returning this bundle does not authorize writing any component to disk.

No S1B function may retain, publish, stage, or write the returned bundle as project evidence.

Serialization failure, source-boundary failure, hash failure, and replay mismatch that prevent canonical artifact creation remain process-level outcomes for later S1C execution-envelope specification.

## 11. Test acceptance criteria

The later S1B implementation is acceptable only when:

```text
all authorized tests pass
the exact fixed fixture reconstructs
the exact 288 disagreement certificate passes
all eight eligibility rejection branches are covered
fixed fixture duplicate exclusion is covered
ordinary duplicate diagnostics are covered
first-eight stopping is covered through reduce_scan_records using hand-authored synthetic scan records
scan_seed_stream is separately covered over bounded explicit seed-tuple streams using the real mathematical pipeline
all malformed synthetic scan-record first-failure branches are covered
malformed scan records terminate reduction without consuming a later record
malformed scan records preserve prior valid reduction state
malformed scan records do not alter seen keys or duplicate/rejection counts
manifest field and nested-key orders are exact
candidate manifest hashing is deterministic
candidate replay comparison is deterministic
finalization changes only family_frozen plus derived hashes/bytes
failure-manifest behavior matches S1A
static boundaries reject every prohibited dependency
no canonical full seed scan occurred
no frozen-family access occurred
no generated family or authoritative manifest was retained
```

No scientific interpretation follows from passing implementation tests.

## 12. Required implementation review evidence

After implementation, require reporting of:

```text
exact files created or modified
direct source rendering or reviewable excerpts
test command
test counts and results
warnings
proof that no complete canonical scan ran
proof that no generated family was retained
proof that no output manifest was written
static-boundary test results
working-tree status
```

The operator retains Git authority. Claude must not run Git. Codex performs adversarial review before commit.

## 13. Future S1C boundary

A later S1C authorization must separately freeze:

```text
implementation commit identity
Git blob identities
Windows raw-file SHA-256 identities
test identities
Python version
configuration payload and SHA-256
authorized runner path
exact output paths
execution-envelope schema
two-pass invocation
authoritative replay comparison
finalization and write policy
rerun authority
```

S1B success does not automatically authorize S1C.

## 14. Final authority ledger

The authorization ledger booleans below use the document's project-style authority spelling. They are authorization-state notation and are not the JSON literals used inside canonical manifests.

```text
SYNTHETIC_FIXTURE_FREEZE_SPECIFIED = True
SYNTHETIC_FIXTURE_IMPLEMENTATION_AUTHORIZATION_SPECIFIED = True

SYNTHETIC_FIXTURE_GENERATOR_IMPLEMENTATION_AUTHORIZED = True
SYNTHETIC_FIXTURE_VERIFIER_IMPLEMENTATION_AUTHORIZED = True
SYNTHETIC_FIXTURE_FREEZER_LIBRARY_IMPLEMENTATION_AUTHORIZED = True
SYNTHETIC_FIXTURE_TEST_IMPLEMENTATION_AUTHORIZED = True
SYNTHETIC_FIXTURE_BOUNDED_UNIT_TEST_EXECUTION_AUTHORIZED = True

SYNTHETIC_FIXTURE_CANONICAL_SEED_SCAN_AUTHORIZED = False
SYNTHETIC_FIXTURE_GENERATION_AUTHORIZED = False
SYNTHETIC_FIXTURE_EXECUTION_AUTHORIZED = False
SYNTHETIC_FIXTURE_FREEZE_AUTHORIZED = False
SYNTHETIC_FIXTURE_AUTHORITATIVE_REPLAY_AUTHORIZED = False
SYNTHETIC_FIXTURE_FINAL_MANIFEST_WRITE_AUTHORIZED = False
SYNTHETIC_FIXTURE_RESULT_PUBLICATION_AUTHORIZED = False

CHALLENGER_IMPLEMENTATION_AUTHORIZED = False
CHALLENGER_SYNTHETIC_VALIDATION_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_INPUT_ACCESS_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_EVALUATION_AUTHORIZED = False

PSITRS_CONTACT_AUTHORIZED = False
RETAINED_EVIDENCE_MODIFICATION_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False

FORMAL_HOLD = active
Mode_0 = active
```

## 15. Final disposition

```text
authorized now =
docs-only S1B authorization

authorized after acceptance of this document =
implementation of the five listed Python files
bounded unit-test execution within the stated limits

not authorized =
complete canonical seed scan
discovery of the actual first eight generated fixtures
synthetic-family generation
authoritative two-pass replay
family freeze
manifest publication
challenger implementation
challenger evaluation
frozen K=3 contact
PsiTRS contact
production or kernel contact
```

The next permitted project action is a docs-only review of this authorization, followed only later, and only under this authorization's stated limits, by the S1B implementation. No S1C freeze execution or challenger action follows automatically from this document.
