# TORMENT Brainvision — Stage S3B v0.3 BLOCKER-3 Resource-Admissibility Implementation Specification v0.1

## 1. Document Status

```text
document_class                    = selected-blocker implementation specification (docs-only)
selected_blocker                  = BLOCKER-3
authority_created                 = none
implementation_authorized         = false
execution_authorized              = false
resource_stress_execution_authorized = false
platform_probe_authorized         = false
manifest_contact_authorized       = false
real_publication_authorized       = false
real_recovery_authorized          = false
source_modified                   = false
tests_modified                    = false
prior_docs_modified               = false
```

BLOCKER-3 is selected for specification only.

```text
BLOCKER-3 is not implemented.
BLOCKER-3 is not proven.
BLOCKER-3 is not partially closed.
```

The successor implementation authorization remains separate. This
specification creates no implementation authority and authorizes no resource
stress execution, platform probing, manifest contact, publication, recovery,
descriptor execution, scientific execution, results-tree writes, source change,
test change, or prior-document change.

## 2. Governing Baseline

```text
commit  = 0d52dc0f8945a3be20aabcc33226751a8c8a3e9b
subject = docs(research): select resource bounds as first platform blocker
```

Primary governing selection record:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_PLATFORM_BLOCKER_DECOMPOSITION_AND_FIRST_BOUND_SELECTION_v0.1.md
```

This specification also preserves the architecture review, architecture
decision record, durable-evidence implementation specification, implementation
authorization, and implementation findings record. It does not amend H1-H5 and
does not falsely close BLOCKER-1, BLOCKER-2, or BLOCKER-4.

## 3. Permanent Boundaries

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

The work remains:

```text
offline
quarantined
synthetic-only
non-production
non-service
non-kernel
non-memory-integrated
non-cognitive
non-autonomous
```

This specification concerns resource admissibility only. It does not establish
scientific truth, publication truth, cognitive truth, deployment readiness, or
operational safety.

## 4. Current Committed Controls

Current controls already committed in the durable-evidence substrate include:

```text
MAX_NESTING_DEPTH                 = 32
MAX_CONTAINER_MEMBER_COUNT        = 4096
MAX_STORED_RECORD_OBJECT_BYTES    = 65536
MAX_STORED_BUNDLE_OBJECT_BYTES    = 4194304
```

Also currently committed:

```text
canonical JSON is ASCII
null is prohibited
float is prohibited
bool is distinct from int
duplicate JSON keys are rejected
canonical payload has exactly one terminal LF
BOM and CR are prohibited
publication artifact inventory contains exactly three fixed filenames
```

These are partial controls. They are not a complete publication-artifact,
aggregate-set, staging-capacity, or recovery-read resource contract.

This specification does not reconstruct or estimate historical v0.2 artifact
sizes.

## 5. Binding Resource Policy

These values are contract ceilings selected as powers-of-two or exact sums.
They are not measurements or reconstructions of the historical v0.2 result.

### 5.1 Existing retained limits

```text
MAX_RESOURCE_NESTING_DEPTH                   = 32
MAX_RESOURCE_CONTAINER_MEMBERS_PER_CONTAINER = 4096
MAX_STORED_RECORD_OBJECT_BYTES               = 65536
MAX_STORED_BUNDLE_OBJECT_BYTES               = 4194304
```

### 5.2 New structural preflight limits

```text
MAX_RESOURCE_TOTAL_NODE_COUNT           = 16384
MAX_RESOURCE_SINGLE_STRING_ASCII_BYTES  = 1048576
MAX_RESOURCE_TOTAL_STRING_ASCII_BYTES   = 4194304
MAX_RESOURCE_INTEGER_ABS                = 9223372036854775807
MAX_PUBLICATION_SOURCE_BUNDLE_BYTES     = 4194304
```

### 5.3 New publication artifact limits

```text
MAX_PUBLICATION_ARTIFACT_COUNT           = 3

MAX_PUBLICATION_RESULT_ARTIFACT_BYTES    = 16384
MAX_PUBLICATION_EXECUTION_ENVELOPE_BYTES = 8388608
MAX_PUBLICATION_SUMMARY_BYTES            = 1024

MAX_PUBLICATION_ARTIFACT_SET_BYTES       = 8406016
```

The aggregate value is exactly:

```text
16384 + 8388608 + 1024 = 8406016
```

### 5.4 Staging and recovery limits

```text
MAX_PUBLICATION_STAGING_WRITE_BYTES         = 8406016
MAX_PUBLICATION_RECOVERY_VERIFICATION_BYTES = 8406016
```

The staging-capacity requirement is:

```text
required_staging_bytes = exact sum of the three generated artifact byte lengths

required_staging_bytes <= MAX_PUBLICATION_STAGING_WRITE_BYTES

synthetic_capacity_available_bytes >= required_staging_bytes
```

No invented filesystem-overhead reserve is added. This contract concerns exact
logical bytes, not filesystem block allocation or real free-space guarantees.

### 5.5 Independent source-bundle and stored-bundle limits

```text
At-limit acceptance is local to the validator and object class being tested.

End-to-end acceptance requires every independently applicable limit to pass.

Passing MAX_PUBLICATION_SOURCE_BUNDLE_BYTES does not override
MAX_STORED_BUNDLE_OBJECT_BYTES.

Because a stored bundle object contains wrapper fields in addition to the bundle
payload, a source bundle at 4194304 bytes is not promised to be end-to-end
storable under the 4194304-byte stored-bundle-object ceiling.
```

Roles:

```text
MAX_PUBLICATION_SOURCE_BUNDLE_BYTES
  = independent upper bound for a source bundle presented to the bounded
    publication validator

MAX_STORED_BUNDLE_OBJECT_BYTES
  = independent upper bound for the complete canonical stored-bundle object,
    including its wrapper fields
```

Do not lower either ceiling, invent a wrapper-size subtraction, or introduce a
historical size measurement.

## 6. Limit Rationale

```text
65536 and 4194304 preserve the existing committed stored-object ceilings.

4194304 bounds the accepted canonical source bundle presented to publication.

8388608 provides a bounded envelope ceiling above the bounded source bundle,
without claiming that the envelope always equals or is smaller than the source bundle.

16384 and 1024 are bounded ceilings for the fixed-shape result artifact
and fixed five-line summary.

8406016 is the exact sum of the three per-artifact ceilings.

16384 total JSON nodes and 4194304 total ASCII string bytes prevent a valid
per-container shape from expanding into an unbounded complete object graph.

The symmetric integer-magnitude ceiling prevents arbitrary-length Python
integers from causing unbounded canonicalization work.
```

These limits are not scientifically derived. They are not claimed to be optimal
or permanent. Changing them later requires a new policy identity,
specification, authorization, and review.

## 7. Four Validation Layers

The resource-admissibility contract preserves four separate decisions:

```text
1. semantic schema validity
2. canonical-byte validity
3. resource admissibility
4. storage-capacity admissibility
```

### 7.1 Semantic schema validity

Checks keys, types, field meanings, identities, result-kind vocabulary, and
chain semantics.

### 7.2 Canonical-byte validity

Checks deterministic canonical bytes, ASCII, no BOM, no CR, one terminal LF,
and exact key order.

### 7.3 Resource admissibility

Checks byte ceilings, total node count, depth, per-container count, per-string
bytes, total-string bytes, integer magnitude, artifact count, per-artifact
bytes, and aggregate bytes.

### 7.4 Storage-capacity admissibility

Checks only whether a synthetic capacity adapter reports at least the exact
logical bytes required for pytest-local staging.

A pass in one layer must not imply a pass in another.

## 8. Structural Accounting Rules

A deterministic resource scan must run before JSON serialization.

The scan must count:

```text
total_node_count:
  the root value and every mapping value or list element

mapping keys:
  do not increment total_node_count independently
  but their ASCII bytes count toward total_string_ascii_bytes

string values:
  their ASCII bytes count toward total_string_ascii_bytes

mapping/list members:
  each individual container remains capped at 4096

integer values:
  bool is handled separately and is not an int
  abs(value) must be <= 9223372036854775807
```

Symmetric integer-magnitude contract:

```text
accepted:
-9223372036854775807 through +9223372036854775807

rejected:
-9223372036854775808
+9223372036854775808
```

The scan must reject before `json.dumps` when any structural limit fails. It
must use bounded recursion or an explicit stack and preserve the existing depth
definition. The preflight scan must not change canonical bytes or hashes.

### 8.1 Deterministic failure precedence for structured Python values

Use bounded deterministic depth-first traversal in mapping insertion order and
list order.

For each visited value, apply this order:

```text
1. supported-domain type check
2. semantic/domain validity at the current value
3. current-value resource check
4. current-container member-count check
5. global node/string budget update
6. bounded descent into children
```

Examples:

```text
null, float, unsupported type, non-string mapping key,
or non-ASCII/control string
  = semantic/domain invalidity when encountered

valid ASCII string over its byte limit
  = STRING_SIZE_LIMIT_EXCEEDED

valid int outside the symmetric magnitude limit
  = INTEGER_MAGNITUDE_LIMIT_EXCEEDED

container over 4096 members
  = CANONICAL_STRUCTURE_LIMIT_EXCEEDED
  without scanning all descendants merely to search for another defect
```

The first failure encountered under this fixed traversal and phase order wins.
An implementation must not perform an unbounded full-object scan to find a
potentially higher-priority defect deeper in an already over-limit container.

### 8.2 Deterministic failure precedence for serialized artifacts

For serialized artifact or recovery bytes, apply:

```text
1. file-type and readable-object admission
2. bounded byte read
3. per-artifact and cumulative byte limits
4. canonical-byte validation
5. semantic artifact validation
6. regenerated-byte comparison
7. expected hash comparison
```

An oversized artifact must be rejected before unbounded parsing or canonical
reconstruction.

### 8.3 Resource versus semantic result classes

Semantic/domain failures remain existing semantic or artifact-validation
failures. They must not be relabelled as resource failures.

Resource codes apply only after the relevant input is valid enough to evaluate
that particular resource rule, except for bounded-read admission, which must
protect parsing from oversized input.

### 8.4 Full-memory allocation boundary

Structural preflight bounds the accepted object graph before `json.dumps`.

A post-serialization byte-length check alone does not prevent temporary
serialization amplification.

The first implementation permits full-memory serialization only because the
node, container, single-string, total-string, integer, and source-object limits
jointly bound the admitted object graph.

This does not claim streaming serialization.

## 9. Policy Identity

The future implementation must define an immutable ordered resource-policy
declaration with this distinct schema identity:

```text
durable-evidence-resource-admissibility-policy-v0.3
```

The policy declaration must contain every binding constant from Section 5 in a
fixed key order.

```text
resource_admissibility_policy_sha256 =
SHA-256(canonical_json_bytes(resource_policy_declaration))
```

The implementation must not hardcode an unexplained predicted hash in advance.
The hash must be computed from the fixed declaration.

The carried identity value has this exact fixed object shape:

```text
resource_admissibility_policy_identity = {
  "policy_schema_identity":
    "durable-evidence-resource-admissibility-policy-v0.3",
  "policy_sha256":
    resource_admissibility_policy_sha256
}
```

Required key order:

```text
policy_schema_identity
policy_sha256
```

Required validation:

```text
resource_admissibility_policy_identity must be a mapping

its key order must be exact

policy_schema_identity must equal
durable-evidence-resource-admissibility-policy-v0.3

policy_sha256 must be lowercase 64-hex

policy_sha256 must equal
SHA-256(canonical_json_bytes(resource_policy_declaration))
```

The policy identity must be carried through existing utility-identity inputs
rather than changing the accepted J1/J2 chain grammar.

Required:

```text
publication_utility_identities[
  "resource_admissibility_policy_identity"
]

publication_recovery_utility_identity[
  "resource_admissibility_policy_identity"
]
```

The fixed outer key is:

```text
resource_admissibility_policy_identity
```

The publication projection identity already binds publication utility
identities. The recovery authority record must bind the recovery utility
identity containing the same policy identity.

A mismatch must classify as:

```text
RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH
```

Changing any binding ceiling changes the canonical declaration and therefore
its SHA-256 identity. Two different declarations may share the policy schema
name but must have different policy SHA-256 identities unless their canonical
declaration bytes are identical.

Do not add a new scientific result field. Do not alter scientific truth or
bundle identity semantics.

## 10. Proposed Source Surface

The future implementation is bound to exactly six files.

### 10.1 Modified source files

```text
research/brainvision/durable_evidence_schema_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
```

### 10.2 New test files

```text
research/brainvision/test_durable_evidence_resource_admissibility_v0_3.py
research/brainvision/test_durable_evidence_publication_resource_bounds_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_resource_bounds_v0_3.py
```

No seventh file. No replay-module modification. No Windows adapter
modification. No production, kernel, service, manifest, descriptor,
scientific-runner, or results-tree modification.

If implementation cannot honestly remain within these six files, it must stop
for renewed specification review.

## 11. Schema-Layer Proposed Contract

The shared schema-layer surface should be substantially equivalent to:

```text
ResourceAdmissibilityError
ResourceStructureLimitError
ResourceStringLimitError
ResourceIntegerLimitError
PublicationArtifactSizeLimitError
PublicationArtifactSetSizeLimitError
RecoveryVerificationBudgetError
ResourceAdmissibilityIndeterminateError
```

Shared functions should be substantially equivalent to:

```text
resource_admissibility_policy_declaration()
resource_admissibility_policy_sha256()

validate_resource_domain(value)
canonical_json_bytes_bounded(value, max_bytes)

validate_publication_artifact_resource_map(artifact_bytes_by_name)
read_file_bytes_bounded(path, max_bytes)
```

Names may be refined only if the exact responsibilities remain distinct.

`canonical_json_bytes()` must retain its existing canonical meaning. The future
implementation must not silently change hashes or canonical serialization. The
bounded helper may call existing canonicalization only after structural
preflight succeeds.

## 12. Publication Integration

The future implementation must preserve the existing operation sequence:

```text
durable PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED
durable PUBLICATION_ATTEMPTED
resource preflight
artifact generation
artifact-set resource validation
synthetic staging-capacity validation
staging-directory creation
artifact writes
staging verification
durability adapter
promotion adapter
final verification
durable PUBLICATION_COMPLETED
```

Authority and `PUBLICATION_ATTEMPTED` may already be durable before artifact
resource rejection occurs. A resource failure must never produce
`PUBLICATION_COMPLETED`.

A pre-generation resource failure must create no staging directory and write no
publication artifact. Artifact generation and aggregate validation must complete
in memory before `staging_directory.mkdir()`.

Generation must be sequential and bounded:

```text
result artifact:
  generate with 16384-byte ceiling

execution envelope:
  generate with 8388608-byte ceiling

summary:
  generate with 1024-byte ceiling

aggregate:
  checked incrementally
  must not exceed 8406016
```

Only narrowly relevant resource failures should be caught. `MemoryError` and
`OverflowError` must map fail closed. Do not catch `KeyboardInterrupt`,
`SystemExit`, or arbitrary `BaseException`.

## 13. Synthetic Staging-Capacity Contract

The future implementation must define a platform-neutral injectable adapter
local to the publication/resource layer. It must not live in the Windows
durability adapter.

Required result fields:

```text
status
required_bytes
available_bytes
detail
```

Required statuses:

```text
STAGING_CAPACITY_CONFIRMED
STAGING_CAPACITY_UNAVAILABLE
STAGING_CAPACITY_INDETERMINATE
```

Required validation:

```text
status must be one of the three declared statuses

required_bytes must be a strict non-negative int
bool is rejected

available_bytes:
  strict non-negative int for CONFIRMED or UNAVAILABLE
  null only for INDETERMINATE

returned required_bytes must equal the caller-computed exact required bytes

CONFIRMED requires available_bytes >= required_bytes

UNAVAILABLE requires available_bytes < required_bytes

unknown or internally inconsistent result
  = RESOURCE_ADMISSIBILITY_INDETERMINATE
```

Default behaviour must fail closed. Only pytest-local synthetic positive
adapters may return confirmed.

The adapter does not prove real disk capacity, filesystem allocation,
durability, or promotion safety.

## 14. Recovery Integration

The current recovery path must not use an unbounded `Path.read_bytes()` for
final publication artifacts after this future implementation.

Before opening any final publication artifact, require a fail-closed admission
check:

```text
pre-open lstat or equivalent

reject if the directory entry is a symlink

reject if a reparse-point artifact is detected where the platform exposes that fact

reject if the entry is not a regular file

open in binary read mode

perform post-open fstat or equivalent

reject if the opened object is not a regular file
```

The implementation must reject:

```text
directory in place of artifact
symlink artifact
detectable reparse-point artifact
named pipe
socket
device-like object
non-regular file
read error
size-indeterminate object
type change detected between admission and bounded read
```

Required secondary classifications:

```text
RECOVERY_ARTIFACT_TYPE_INVALID
RECOVERY_ARTIFACT_READ_INDETERMINATE
```

Both map to:

```text
PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE
```

This check must remain fail closed and bounded. It must not claim:

```text
race-free filesystem security
Windows directory durability
post-crash attribution
reparse-point elimination under every platform condition
```

If a type or substitution condition cannot be classified confidently, use the
indeterminate result and write neither recovery success record.

Bounded recovery reading:

```text
verify exact inventory first

for each expected artifact:
  open in binary mode
  read no more than per-artifact limit + 1 byte
  reject if the extra byte is present

maintain cumulative bytes read
reject before cumulative bytes exceed 8406016
```

A pre-read `stat` size may be used as an early rejection signal. `stat` must
not be treated as sufficient proof because a file can change between stat and
read.

The bounded read result must still pass:

```text
semantic artifact validation
canonical-byte validation
exact regenerated-byte comparison
expected SHA-256 comparison
resource-policy validation
```

On any oversized or indeterminate artifact:

```text
PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED must not be written
PUBLICATION_RECOVERY_EVIDENCE_COMPLETED must not be written
final artifacts must not be modified
the original publication chain must not be modified
```

J2 remains evidence-only and incapable of generation, staging, promotion,
repair, replacement, or deletion.

## 15. Failure Representation

Secondary failure-code vocabulary:

```text
RESOURCE_LIMIT_EXCEEDED
ARTIFACT_SIZE_LIMIT_EXCEEDED
ARTIFACT_SET_SIZE_LIMIT_EXCEEDED
SUMMARY_SIZE_LIMIT_EXCEEDED
CANONICAL_STRUCTURE_LIMIT_EXCEEDED
STRING_SIZE_LIMIT_EXCEEDED
INTEGER_MAGNITUDE_LIMIT_EXCEEDED
STAGING_SPACE_BUDGET_UNAVAILABLE
RECOVERY_VERIFICATION_BUDGET_EXCEEDED
RESOURCE_ADMISSIBILITY_INDETERMINATE
RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH
RECOVERY_ARTIFACT_TYPE_INVALID
RECOVERY_ARTIFACT_READ_INDETERMINATE
```

Top-level J1 classifications:

```text
PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED
PUBLICATION_STAGING_SPACE_BUDGET_UNAVAILABLE
PUBLICATION_RESOURCE_ADMISSIBILITY_INDETERMINATE
```

Top-level J2 classifications:

```text
PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED
PUBLICATION_RECOVERY_VERIFICATION_BUDGET_EXCEEDED
PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE
```

Optional result fields:

```text
resource_failure_code
resource_policy_identity
```

Do not create a new scientific result kind. Do not convert a resource failure
into scientific PASS, scientific FAIL, publication success, or normal recovery
completion.

### 15.1 Exact J1 failure mapping

| Secondary code | J1 top-level classification |
|---|---|
| `RESOURCE_LIMIT_EXCEEDED` | `PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED` |
| `ARTIFACT_SIZE_LIMIT_EXCEEDED` | `PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED` |
| `ARTIFACT_SET_SIZE_LIMIT_EXCEEDED` | `PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED` |
| `SUMMARY_SIZE_LIMIT_EXCEEDED` | `PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED` |
| `CANONICAL_STRUCTURE_LIMIT_EXCEEDED` | `PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED` |
| `STRING_SIZE_LIMIT_EXCEEDED` | `PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED` |
| `INTEGER_MAGNITUDE_LIMIT_EXCEEDED` | `PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED` |
| `RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH` | `PUBLICATION_RESOURCE_ADMISSIBILITY_FAILED` |
| `STAGING_SPACE_BUDGET_UNAVAILABLE` | `PUBLICATION_STAGING_SPACE_BUDGET_UNAVAILABLE` |
| `RESOURCE_ADMISSIBILITY_INDETERMINATE` | `PUBLICATION_RESOURCE_ADMISSIBILITY_INDETERMINATE` |

```text
RECOVERY_VERIFICATION_BUDGET_EXCEEDED is not a valid J1 secondary code.
```

### 15.2 Exact J2 failure mapping

| Secondary code | J2 top-level classification |
|---|---|
| `RESOURCE_LIMIT_EXCEEDED` | `PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED` |
| `ARTIFACT_SIZE_LIMIT_EXCEEDED` | `PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED` |
| `SUMMARY_SIZE_LIMIT_EXCEEDED` | `PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED` |
| `CANONICAL_STRUCTURE_LIMIT_EXCEEDED` | `PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED` |
| `STRING_SIZE_LIMIT_EXCEEDED` | `PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED` |
| `INTEGER_MAGNITUDE_LIMIT_EXCEEDED` | `PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED` |
| `RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH` | `PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_FAILED` |
| `ARTIFACT_SET_SIZE_LIMIT_EXCEEDED` | `PUBLICATION_RECOVERY_VERIFICATION_BUDGET_EXCEEDED` |
| `RECOVERY_VERIFICATION_BUDGET_EXCEEDED` | `PUBLICATION_RECOVERY_VERIFICATION_BUDGET_EXCEEDED` |
| `RESOURCE_ADMISSIBILITY_INDETERMINATE` | `PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE` |
| `RECOVERY_ARTIFACT_TYPE_INVALID` | `PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE` |
| `RECOVERY_ARTIFACT_READ_INDETERMINATE` | `PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE` |

```text
STAGING_SPACE_BUDGET_UNAVAILABLE is not a valid J2 secondary code.
```

When multiple resource failures would be possible, the fixed processing order
determines the one reported secondary code. No multiple-code set or
implementation-dependent winner is permitted.

### 15.3 Result-field semantics

```text
On resource failure:
  resource_failure_code = exact non-null secondary code
  resource_policy_identity = exact bound identity object

On resource success that claims policy admission:
  resource_failure_code = null
  resource_policy_identity = exact bound identity object

On results created before resource admission is attempted:
  resource_failure_code = null
  resource_policy_identity = null
```

Use one fixed rule; do not alternate between absent and null.

Any dataclass additions must:

```text
have defaults
preserve existing callers
be added after existing fields
be constructed by keyword
```

Do not change existing positional meaning.

## 16. Required Success Cases

Future tests must bind:

```text
minimum valid resource-domain object
current exact three-artifact synthetic publication
at-limit total node count
at-limit per-container member count
at-limit single ASCII string
at-limit total ASCII string bytes
accepted and rejected symmetric integer-magnitude boundaries
generic source-bundle resource validator accepts exactly
MAX_PUBLICATION_SOURCE_BUNDLE_BYTES when tested independently
end-to-end bundle acceptance succeeds only for a fixture that satisfies both
the source-bundle ceiling and the complete stored-bundle-object ceiling
at-limit result artifact bytes
at-limit execution-envelope bytes
at-limit summary bytes
at-limit aggregate artifact-set bytes
at-limit recovery verification bytes
staging adapter reports exactly required bytes
resource policy identity deterministic across independent construction
```

At-limit means equality is accepted.

### 16.1 Boundary-fixture rules

```text
generic-validator at-limit fixture:
  proves the validator accepts equality at its own local ceiling

real fixed-shape artifact fixture:
  proves the current semantic artifact remains accepted below its ceiling

end-to-end bundle fixture:
  must satisfy source-bundle and stored-bundle-object limits simultaneously
```

```text
generic validator at-limit fixture
  !=
semantically valid end-to-end stored-bundle fixture
```

Do not require artificial padding of fixed-shape production artifacts merely to
hit a ceiling.

For fixed-shape artifacts whose valid schema cannot naturally reach the
ceiling:

```text
use a generic bounded-byte validator for equality and limit-plus-one tests

use the real fixed-shape artifact for ordinary acceptance and regression tests
```

Production constants must remain fixed.

Test-private reduced ceilings remain allowed only through test-private policy
objects or helper parameters that production paths cannot select automatically.

## 17. Required Failure Cases

Future tests must bind limit plus one:

```text
nesting depth + 1
container members + 1
total node count + 1
single string bytes + 1
total string bytes + 1
integer magnitude + 1
source bundle bytes + 1
result artifact bytes + 1
execution-envelope bytes + 1
summary bytes + 1
aggregate artifact-set bytes + 1
recovery verification bytes + 1
staging available bytes = required bytes - 1
```

Also required:

```text
float and null remain semantic/domain failures
bool is not treated as an integer
non-ASCII/control string remains invalid
unexpected allocation failure maps to indeterminate
no completion record after failure
no staging directory after pre-generation resource failure
no ARTIFACTS_VERIFIED recovery record after oversized final artifact
```

## 18. Required Fault Injections

Required fault seams:

```text
object expands beyond a pre-generation estimate
artifact generator returns per-artifact limit + 1 bytes
three individually valid artifacts exceed aggregate limit
summary generator returns over-limit canonical-looking text
staging adapter returns unavailable
staging adapter returns indeterminate
bounded reader observes limit + 1 byte
file grows after stat but before bounded read
cumulative recovery budget exceeds aggregate on final artifact
MemoryError during structural scan
MemoryError during canonicalization
MemoryError during bounded recovery read
interruption after one in-memory artifact but before set acceptance
```

All tests remain within safe host-memory bounds. Do not allocate
attacker-proportional gigabyte fixtures. Use compact synthetic objects and
test-local injected ceilings where necessary to exercise boundary logic safely.
Production binding constants must remain fixed; injectable smaller limits may
exist only in test-private helpers or explicitly test-only policy objects.

## 19. Replay and Evidence Invariants

Future proof must show:

```text
resource-rejected publication has no PUBLICATION_COMPLETED record

resource-rejected recovery has no
PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED or
PUBLICATION_RECOVERY_EVIDENCE_COMPLETED record

valid-prefix replay does not conceal a contradictory or oversized tail

resource failure does not alter the authoritative scientific bundle
or SCIENTIFIC_COMPLETION receipt

resource policy identity is present in the applicable utility identity evidence

same logical bytes still produce the same canonical hash
when accepted under the policy
```

No replay implementation change is expected. If replay changes become
necessary, stop for renewed specification review rather than adding a seventh
file.

Existing replay does not independently execute or revalidate the complete
resource-admissibility policy.

Resource-aware writers guarantee that no publication or recovery completion
record is appended after resource rejection.

Existing replay then truthfully observes the resulting incomplete chain and
continues to reject contradictory tails under its existing grammar.

If independent policy revalidation by replay becomes required, implementation
must stop because replay-module modification is outside this specification.

## 20. Existing-Test Preservation

All existing Stage S3B v0.3 tests must remain green. The future implementation
must preserve at least:

```text
172 existing durable-evidence tests
17 existing boundary tests
```

The future focused resource suite must be additive. This specification does not
predict its final count.

Two complete authoritative Windows runs are required after implementation, and
one independent Linux review run is required where available.

## 21. Explicit Non-Claims

The future implementation would not establish:

```text
Windows directory durability
file-metadata durability
directory-entry durability
same-volume no-replace promotion
atomic promotion
post-crash attribution
real free-space availability
real publication safety
real recovery safety
real-operation authorization
scientific validity
historical v0.2 result size
production readiness
Brainvision readiness
memory integration readiness
```

A synthetic staging-capacity adapter is not evidence of real storage capacity.
A bounded recovery read is not evidence of crash consistency.

## 22. Open Blockers

```text
BLOCKER-1 = open
BLOCKER-2 = open
BLOCKER-3 = selected and specified, not closed
BLOCKER-4 = open
```

Only a later separately authorized implementation, adversarial review,
authoritative Windows validation, commit, and findings record may close
BLOCKER-3.

## 23. Stop Conditions

Implementation must stop if:

```text
an exact limit cannot be implemented without real data contact
historical v0.2 size reconstruction becomes necessary
a test requires real publication or recovery
a proof requires Windows crash semantics
a seventh file becomes necessary
canonical bytes or existing identity semantics would change
replay modules require modification
resource tests risk unbounded host allocation
production/kernel/service contact becomes necessary
```

## 24. Required Successor

```text
SPECIFICATION_STATUS = READY_FOR_INDEPENDENT_REVIEW
SELECTED_BLOCKER = BLOCKER_3
BLOCKER_3_IMPLEMENTED = False
BLOCKER_3_CLOSED = False

NEXT_STEP =
SEPARATE_DOCS_ONLY_BLOCKER_3_IMPLEMENTATION_AUTHORIZATION
```

This specification itself does not authorize implementation.
