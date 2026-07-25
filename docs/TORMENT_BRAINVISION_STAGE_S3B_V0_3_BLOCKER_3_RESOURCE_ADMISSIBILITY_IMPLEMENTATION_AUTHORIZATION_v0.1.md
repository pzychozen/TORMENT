# TORMENT Brainvision — Stage S3B v0.3 BLOCKER-3 Resource-Admissibility Implementation Authorization v0.1

## 1. Document Status

```text
document_class                         = separate docs-only implementation authorization
selected_blocker                       = BLOCKER-3
governing_specification_status         = accepted
implementation_authorized              = true, subject to Section 3 effectiveness conditions
authorized_source_files                = exactly 3
authorized_test_files                  = exactly 3
authorized_total_files                 = exactly 6
synthetic_pytest_local_execution       = authorized
bounded_fault_injection                = authorized
resource_stress_execution_authorized   = bounded pytest-local fixtures only
platform_probe_authorized              = false
manifest_contact_authorized            = false
descriptor_execution_authorized        = false
scientific_execution_authorized        = false
real_publication_authorized            = false
real_recovery_authorized               = false
real_results_tree_contact_authorized   = false
Windows_adapter_modification           = false
replay_module_modification             = false
production_modification                = false
kernel_modification                    = false
service_runtime_modification           = false
```

This document creates only the narrow implementation and bounded-test authority
defined below. It does not implement BLOCKER-3 and does not itself prove or close
BLOCKER-3.

## 2. Governing Baseline

```text
authoritative_repository =
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric

branch = main

authorized_input_HEAD =
35d7b6e181473508dbbc85518ef4588f76dd3b94

authorized_input_subject =
docs(research): specify blocker 3 resource admissibility
```

Governing specification:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

Governing specification Git blob:

```text
3fc24c03fd85b530e585e52b0e94d8f92c4002f9
```

The implementation must preserve every binding rule, boundary, precedence rule,
failure mapping, test requirement, stop condition, and non-claim in that
specification.

## 3. Authorization Effectiveness

This authorization is not effective merely because a draft exists.

It becomes effective only when all of the following are true:

```text
1. this authorization has received an independent docs-only review;
2. the final independent verdict is A. ACCEPT;
3. the accepted authorization is committed as a docs-only successor of
   35d7b6e181473508dbbc85518ef4588f76dd3b94;
4. the authorization commit is pushed to origin/main;
5. the authoritative Windows working tree is clean and synchronized at that
   pushed authorization commit.
```

Before those conditions are satisfied:

```text
implementation must not begin
source files must not be modified
test files must not be created
resource tests must not be executed
```

The authorization commit may contain only this authorization document.

## 4. Durable-Evidence Architecture Invariants

The authoritative scientific result remains:

```text
verified IMMUTABLE_SCIENTIFIC_BUNDLE
+
valid linked SCIENTIFIC_COMPLETION receipt
```

Publication remains a projection of that authoritative result. Publication is
not the scientific truth transition.

The observer/evidence boundary occurs only when the bundle and completion
receipt are:

```text
durable
verified
identity-bound
mutually linked
accepted
```

J1 grammar remains:

```text
0 PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED
1 PUBLICATION_ATTEMPTED
2 PUBLICATION_COMPLETED
3 optional terminal
```

J2 grammar remains:

```text
0 PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED
1 PUBLICATION_RECOVERY_ATTEMPTED
2 PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED
3 PUBLICATION_RECOVERY_EVIDENCE_COMPLETED
4 optional terminal
```

J2 writes only to its separate recovery evidence chain and cannot claim original
J1 completion.

## 5. Permanent Boundaries

Preserve exactly:

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

This authorization does not permit integration of the durable-evidence
architecture into:

```text
AI cognition
AI autonomy
AI memory
belief formation
truth-selection behaviour
identity
prompt handling
action selection
production TORMENT kernel
live memory-system functionality
```

## 6. Exact Authorized File Surface

Implementation authority is limited to exactly these six files.

### 6.1 Modified source files

```text
research/brainvision/durable_evidence_schema_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
```

### 6.2 New test files

```text
research/brainvision/test_durable_evidence_resource_admissibility_v0_3.py
research/brainvision/test_durable_evidence_publication_resource_bounds_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_resource_bounds_v0_3.py
```

No seventh file is authorized.

No rename, relocation, generated helper file, fixture file, replay file, adapter
file, documentation amendment, or incidental cleanup outside this exact surface
is authorized.

If implementation cannot honestly remain within these six files, stop for a
renewed specification and authorization.

## 7. Explicitly Prohibited Surfaces and Operations

The authorization does not permit modification of, or operational contact with:

```text
replay modules
Windows durability or promotion adapters
torment_service/
production kernel
service/runtime
live memory-system code
manifest readers
real manifests
descriptor or PsiTRS code
scientific runners
real result trees
real publication paths
real recovery paths
```

The authorization does not permit:

```text
real publication
real recovery
publication artifact generation from real data
publication artifact staging to real destinations
publication promotion
publication repair or replacement
resource-stress contact with real data
historical v0.2 artifact reconstruction
platform probing
filesystem crash testing
directory-durability claims
same-volume promotion claims
```

## 8. Binding Resource Policy

The implementation must preserve these exact values.

### 8.1 Existing retained limits

```text
MAX_RESOURCE_NESTING_DEPTH                    = 32
MAX_RESOURCE_CONTAINER_MEMBERS_PER_CONTAINER  = 4096
MAX_STORED_RECORD_OBJECT_BYTES                = 65536
MAX_STORED_BUNDLE_OBJECT_BYTES                = 4194304
```

### 8.2 Structural limits

```text
MAX_RESOURCE_TOTAL_NODE_COUNT             = 16384
MAX_RESOURCE_SINGLE_STRING_ASCII_BYTES    = 1048576
MAX_RESOURCE_TOTAL_STRING_ASCII_BYTES     = 4194304
MAX_RESOURCE_INTEGER_ABS                  = 9223372036854775807
MAX_PUBLICATION_SOURCE_BUNDLE_BYTES       = 4194304
```

### 8.3 Publication artifact limits

```text
MAX_PUBLICATION_ARTIFACT_COUNT               = 3
MAX_PUBLICATION_RESULT_ARTIFACT_BYTES        = 16384
MAX_PUBLICATION_EXECUTION_ENVELOPE_BYTES     = 8388608
MAX_PUBLICATION_SUMMARY_BYTES                = 1024
MAX_PUBLICATION_ARTIFACT_SET_BYTES           = 8406016
```

Exact aggregate arithmetic:

```text
16384 + 8388608 + 1024 = 8406016
```

### 8.4 Staging and recovery limits

```text
MAX_PUBLICATION_STAGING_WRITE_BYTES          = 8406016
MAX_PUBLICATION_RECOVERY_VERIFICATION_BYTES  = 8406016
```

These are engineering contract ceilings. They are not scientific derivations,
historical measurements, reconstructed v0.2 sizes, or deployment guarantees.

Changing any binding value is outside this authorization and requires:

```text
new policy declaration
new policy identity
new specification
new authorization
new independent review
```

## 9. Independent-Limit Rule

The following equal-valued limits remain independent:

```text
MAX_PUBLICATION_SOURCE_BUNDLE_BYTES = 4194304
MAX_STORED_BUNDLE_OBJECT_BYTES      = 4194304
```

At-limit acceptance is local to the validator and object class under test.

End-to-end acceptance requires all independently applicable limits to pass.

A source bundle accepted at exactly 4194304 bytes is not promised to fit in a
complete stored bundle object whose wrapper-plus-payload ceiling is also
4194304 bytes.

The implementation must not:

```text
lower either ceiling
subtract an invented wrapper reserve
merge the validators
treat one limit as overriding the other
claim a generic at-limit fixture is an end-to-end bundle fixture
```

Tests must distinguish:

```text
generic-validator at-limit fixture
real fixed-shape artifact fixture
end-to-end bundle fixture
```

## 10. Validation-Layer Separation

The implementation must preserve four separate validation layers:

```text
1. semantic schema validity
2. canonical-byte validity
3. resource admissibility
4. storage-capacity admissibility
```

A pass in one layer must not imply a pass in another.

Semantic/domain failures must remain semantic/domain failures. They must not be
relabelled as resource failures.

Canonical serialization and existing canonical hashes must not change.

Storage-capacity admissibility is limited to validation of a synthetic
pytest-local adapter response against exact logical staging bytes. It does not
prove real free space, filesystem allocation, durability, or promotion safety.

## 11. Structural Preflight and Accounting

A deterministic pre-serialization resource scan must run before `json.dumps`.

Accounting is binding:

```text
the root value counts as a node

every mapping value counts as a node

every list element counts as a node

mapping keys do not independently count as nodes

mapping-key ASCII bytes count toward total string bytes

string-value ASCII bytes count toward total string bytes

each individual mapping/list is capped at 4096 members

bool is handled before int

abs(integer) <= 9223372036854775807
```

Symmetric integer contract:

```text
accepted:
-9223372036854775807 through +9223372036854775807

rejected:
-9223372036854775808
+9223372036854775808
```

Traversal must be deterministic depth-first using mapping insertion order and
list order.

For each visited value, the fixed order is:

```text
1. supported-domain type check
2. semantic/domain validity at the current value
3. current-value resource validation
4. current-container member-count validation
5. global node/string accounting
6. bounded child traversal
```

The first failure encountered wins.

An already over-limit container must be rejected without scanning all of its
descendants merely to search for another defect.

The scan must use bounded recursion or an explicit bounded stack and preserve
the existing depth definition.

Full-memory serialization is authorized only after structural preflight has
bounded the accepted object graph. No streaming-serialization claim is
authorized.

## 12. Serialized Artifact and Recovery Precedence

For serialized artifact or recovery bytes, the fixed order is:

```text
1. file-type and readable-object admission
2. bounded byte read
3. per-artifact and cumulative byte limits
4. canonical-byte validation
5. semantic artifact validation
6. regenerated-byte comparison
7. expected hash comparison
```

Oversized input must be rejected before unbounded parsing, canonical
reconstruction, or attacker-proportional allocation.

## 13. Resource-Policy Identity

Policy schema identity:

```text
durable-evidence-resource-admissibility-policy-v0.3
```

The implementation must define an immutable ordered policy declaration
containing every binding constant in Section 8 in fixed key order.

```text
resource_admissibility_policy_sha256 =
SHA-256(canonical_json_bytes(resource_policy_declaration))
```

The hash must be computed from the declaration. No unexplained predicted hash
may be hardcoded.

Exact carried identity object:

```json
{
  "policy_schema_identity": "durable-evidence-resource-admissibility-policy-v0.3",
  "policy_sha256": "<computed lowercase 64-hex SHA-256>"
}
```

Exact key order:

```text
policy_schema_identity
policy_sha256
```

The exact identity must be carried under:

```text
publication_utility_identities[
  "resource_admissibility_policy_identity"
]

publication_recovery_utility_identity[
  "resource_admissibility_policy_identity"
]
```

Mismatch code:

```text
RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_MISMATCH
```

Do not change J1 or J2 grammar.

Do not add a scientific-result field.

Do not alter scientific truth, bundle identity, or completion-receipt
semantics.

## 14. Authorized Schema-Layer Responsibilities

Within the authorized schema file, the implementation may add narrowly scoped
resource exceptions and helpers substantially equivalent to:

```text
ResourceAdmissibilityError
ResourceStructureLimitError
ResourceStringLimitError
ResourceIntegerLimitError
PublicationArtifactSizeLimitError
PublicationArtifactSetSizeLimitError
RecoveryVerificationBudgetError
ResourceAdmissibilityIndeterminateError

resource_admissibility_policy_declaration()
resource_admissibility_policy_sha256()
validate_resource_domain(value)
canonical_json_bytes_bounded(value, max_bytes)
validate_publication_artifact_resource_map(artifact_bytes_by_name)
read_file_bytes_bounded(path, max_bytes)
```

Names may be refined only when responsibilities remain distinct and all
specified semantics remain exact.

Existing `canonical_json_bytes()` semantics and output must remain unchanged.

The bounded canonical helper may call existing canonicalization only after
structural preflight succeeds.

## 15. Publication Sequencing Authority

The exact publication artifact inventory remains:

```text
iososv_v0_3_result.json
iososv_v0_3_execution_envelope.json
iososv_v0_3_summary.txt
```

The count must remain exactly three, and no additional publication artifact is
authorized.

The implementation must preserve this exact sequence:

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

Authority and `PUBLICATION_ATTEMPTED` may already be durable before resource
rejection.

A resource failure must never produce `PUBLICATION_COMPLETED`.

All of the following must complete before staging-directory creation:

```text
pre-generation source validation
complete in-memory artifact generation
per-artifact validation
aggregate artifact-set validation
synthetic staging-capacity validation
```

Failure before staging must leave:

```text
no staging directory
no publication artifact writes
no PUBLICATION_COMPLETED record
```

Generation must be sequential and bounded:

```text
result artifact ceiling             = 16384
execution-envelope ceiling          = 8388608
summary ceiling                     = 1024
aggregate ceiling                   = 8406016
```

The aggregate must be checked incrementally.

## 16. Synthetic Staging-Capacity Contract

The publication/resource layer may define a platform-neutral injectable
capacity adapter. It must not be placed in or modify a Windows adapter.

Required fields:

```text
status
required_bytes
available_bytes
detail
```

Statuses:

```text
STAGING_CAPACITY_CONFIRMED
STAGING_CAPACITY_UNAVAILABLE
STAGING_CAPACITY_INDETERMINATE
```

Validation is exact:

```text
status must be known

required_bytes must be a strict non-negative int
bool is rejected

available_bytes must be a strict non-negative int for
CONFIRMED or UNAVAILABLE

available_bytes must be null only for INDETERMINATE

returned required_bytes must equal the caller-computed exact required bytes

CONFIRMED requires available_bytes >= required_bytes

UNAVAILABLE requires available_bytes < required_bytes

unknown or internally inconsistent response
= RESOURCE_ADMISSIBILITY_INDETERMINATE
```

Default behaviour must fail closed.

Only pytest-local synthetic positive adapters may confirm capacity.

The adapter must not inspect or claim real disk capacity.

## 17. Recovery Sequencing and Bounded-Read Authority

Recovery remains J2 evidence-only.

It must not:

```text
generate publication artifacts
stage publication artifacts
write publication artifacts
repair publication artifacts
copy publication artifacts
rename publication artifacts
promote publication artifacts
replace publication artifacts
overwrite publication artifacts
delete publication artifacts
mutate publication artifacts
run science
read the real manifest
claim original J1 completion
```

Recovery must not use unbounded `Path.read_bytes()` for final publication
artifacts.

Required flow:

```text
verify exact inventory

pre-open lstat or equivalent

reject symlink

reject detectable reparse-point artifact

require regular file

open in binary mode

post-open fstat or equivalent

require opened object to remain a regular file

read no more than the applicable per-artifact limit + 1 byte

reject if the extra byte is present

track cumulative accepted bytes

reject before cumulative accepted bytes exceed 8406016
```

A pre-read `stat` may reject early but is not sufficient proof.

Reject fail closed:

```text
directory
symlink
detectable reparse point
named pipe
socket
device-like object
non-regular file
read error
size-indeterminate object
detected type change
```

Required secondary codes:

```text
RECOVERY_ARTIFACT_TYPE_INVALID
RECOVERY_ARTIFACT_READ_INDETERMINATE
```

Both map to:

```text
PUBLICATION_RECOVERY_RESOURCE_ADMISSIBILITY_INDETERMINATE
```

On resource rejection, recovery must write neither:

```text
PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED
PUBLICATION_RECOVERY_EVIDENCE_COMPLETED
```

Final artifacts and the original publication chain must remain unmodified.

This authorization does not establish race-free filesystem security, directory
durability, crash consistency, or universal reparse-point elimination.

## 18. Exact Failure Vocabulary

Authorized secondary codes:

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

No additional resource code is authorized without renewed specification.

## 19. Exact J1 Failure Mapping

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
RECOVERY_VERIFICATION_BUDGET_EXCEEDED is invalid for J1.
```

## 20. Exact J2 Failure Mapping

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
STAGING_SPACE_BUDGET_UNAVAILABLE is invalid for J2.
```

The fixed processing order determines the single reported secondary code.

No multiple-code result or implementation-defined winner is authorized.

## 21. Result-Field Semantics

Future result dataclasses may add only:

```text
resource_failure_code
resource_policy_identity
```

Exact semantics:

```text
on resource failure:
  resource_failure_code = exact non-null secondary code
  resource_policy_identity = exact policy identity object

on successful policy admission:
  resource_failure_code = null
  resource_policy_identity = exact policy identity object

before policy admission is attempted:
  resource_failure_code = null
  resource_policy_identity = null
```

One fixed null/non-null representation must be used.

Any dataclass additions must:

```text
have defaults
appear after existing fields
preserve existing callers
be constructed by keyword
not change existing positional meaning
```

## 22. Exception Handling

Only narrowly relevant `MemoryError` and `OverflowError` may be converted into:

```text
RESOURCE_ADMISSIBILITY_INDETERMINATE
```

Do not broadly catch or relabel:

```text
KeyError
AssertionError
unexpected TypeError
KeyboardInterrupt
SystemExit
BaseException
```

The resource-failure result path must itself remain minimal and bounded.

## 23. Authorized Test Scope

The three new test files may exercise only synthetic pytest-local behavior.

Required success cases include:

```text
minimum valid resource-domain object
current exact three-artifact synthetic publication
at-limit total node count
at-limit per-container member count
at-limit single ASCII string
at-limit total ASCII string bytes
accepted and rejected symmetric integer boundaries
independent source-bundle equality acceptance
end-to-end bundle satisfying both independent limits
at-limit generic result-artifact validator
at-limit generic execution-envelope validator
at-limit generic summary validator
at-limit aggregate artifact-set validator
at-limit recovery verification budget
staging adapter reporting exactly required bytes
deterministic resource-policy identity
```

Required limit-plus-one cases include:

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

Required semantic and invariant cases include:

```text
float and null remain semantic/domain failures
bool is not treated as an integer
non-ASCII/control string remains invalid
unexpected bounded allocation failure maps to indeterminate
no publication completion after resource failure
no staging directory after pre-staging resource failure
no recovery ARTIFACTS_VERIFIED record after oversized final artifact
no recovery EVIDENCE_COMPLETED record after resource rejection
final artifacts remain unmodified
original publication chain remains unmodified
```

Required fault seams include:

```text
object expands beyond a pre-generation estimate
artifact generator returns per-artifact limit + 1 bytes
three individually valid artifacts exceed aggregate limit
summary generator returns over-limit canonical-looking text
staging adapter returns unavailable
staging adapter returns indeterminate
staging adapter returns unknown or internally inconsistent data
bounded reader observes limit + 1 byte
file grows after stat but before bounded read
cumulative recovery budget exceeds aggregate on final artifact
MemoryError during structural scan
MemoryError during canonicalization
MemoryError during bounded recovery read
interruption after one in-memory artifact but before set acceptance
directory substitution
symlink substitution where supported
detectable reparse-point substitution where supported
non-regular file substitution where safely supported
```

At-limit equality must be tested locally per validator.

Fixed-shape production artifacts must not be artificially padded merely to hit
their ceilings.

Test-private reduced policies or helper parameters are authorized only when:

```text
they are confined to tests or explicitly test-only objects
production paths cannot select them automatically
production constants remain unchanged
the fixture remains safely bounded
```

Do not allocate attacker-proportional gigabyte fixtures.

Do not contact real data, real manifests, real result trees, real publication
destinations, or real recovery destinations.

## 24. Existing-Test Preservation and Required Validation

All existing Stage S3B v0.3 tests must remain green.

Preserve at least:

```text
172 existing durable-evidence tests
17 existing boundary tests
```

Focused resource tests are additive. Their final count must be reported from
actual execution and must not be predicted in advance.

After implementation and focused review, required evidence is:

```text
two complete authoritative Windows runs

one independent Linux review run where available
```

The Windows operator uses Command Prompt:

```bat
conda activate torment
cd /d C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
```

Use `python`, not `py`.

Do not require `python --version` or `where python` unless a specific
interpreter ambiguity or execution problem arises.

Prefer direct file review, focused tests, complete test results, `git status`,
and focused cached-name checks over noisy general diffs.

## 25. Replay and Evidence Boundary

No replay implementation change is authorized.

The bounded claim is only:

```text
resource-aware writers append no publication or recovery completion after
resource rejection

existing replay truthfully observes the resulting incomplete chain
```

Existing replay does not independently execute or revalidate the complete
resource policy.

If independent replay-side resource-policy validation becomes necessary, stop
for renewed specification and authorization.

A resource failure must not alter:

```text
the authoritative scientific bundle
the SCIENTIFIC_COMPLETION receipt
scientific truth semantics
bundle identity semantics
```

## 26. Explicit Non-Claims

Successful implementation under this authorization will not establish:

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

## 27. Mandatory Stop Conditions

Implementation must stop immediately if any of the following becomes necessary:

```text
a seventh file

a replay-module change

a Windows-adapter change

a production, kernel, service, or live-memory change

manifest contact

descriptor or PsiTRS execution

scientific execution

real-data resource stress

real result-tree contact

real publication or real recovery

historical v0.2 size reconstruction

platform probing

Windows crash-semantics proof

unbounded or attacker-proportional allocation

canonical-byte or existing-hash change

scientific-result-kind change

J1 or J2 grammar change

scientific truth or bundle identity change

a binding ceiling change

a new failure code or altered failure mapping

a requirement that cannot be implemented fail closed inside the six files
```

On a stop condition:

```text
do not improvise
do not broaden scope
do not add a helper file
do not weaken the contract
report the exact blocker for renewed architecture review
```

## 28. Required Implementation Review

After Codex implementation and before any commit:

```text
1. inspect exactly the six authorized files;
2. verify no seventh file exists;
3. verify no prohibited surface changed;
4. run focused resource tests;
5. run the complete durable-evidence suite;
6. run the boundary suite;
7. perform adversarial review of precedence, identity, bounded reads,
   staging-before-admission, and failure mappings;
8. run the complete authoritative Windows validation twice;
9. obtain one independent Linux review run where available;
10. record actual test counts and any platform-specific skips;
11. stop rather than commit if any binding invariant is unproven.
```

Implementation success alone does not close BLOCKER-3.

Closure additionally requires:

```text
accepted adversarial review
authoritative Windows evidence
accepted implementation commit
push to origin/main
separate findings record
```

## 29. Blocker State

```text
BLOCKER-1 = open
BLOCKER-2 = open
BLOCKER-3 = selected and specified, not implemented or closed
BLOCKER-4 = open
```

Successful implementation under this authorization will not close BLOCKER-1,
BLOCKER-2, or BLOCKER-4 and will not authorize real publication or recovery.

Only later accepted adversarial review, authoritative Windows validation,
implementation commit and push, and a separate findings record may close
BLOCKER-3.

## 30. Authorization Decision

```text
AUTHORIZATION_STATUS = READY_FOR_INDEPENDENT_DOCS_ONLY_REVIEW

AUTHORIZED_BASELINE =
35d7b6e181473508dbbc85518ef4588f76dd3b94

AUTHORIZED_BLOCKER = BLOCKER_3

AUTHORIZED_FILE_COUNT = 6

IMPLEMENTATION_AUTHORIZED_AFTER_EFFECTIVENESS_CONDITIONS = True

REAL_PUBLICATION_AUTHORIZED = False
REAL_RECOVERY_AUTHORIZED = False
PLATFORM_PROBE_AUTHORIZED = False
MANIFEST_CONTACT_AUTHORIZED = False
PRODUCTION_CONTACT_AUTHORIZED = False

BLOCKER_1_CLOSED = False
BLOCKER_2_CLOSED = False
BLOCKER_3_IMPLEMENTED = False
BLOCKER_3_CLOSED = False
BLOCKER_4_CLOSED = False

NEXT_STEP =
INDEPENDENT_DOCS_ONLY_AUTHORIZATION_REVIEW
```

This authorization must receive an independent `A. ACCEPT` verdict, then be
committed and pushed, before the six-file implementation begins.
