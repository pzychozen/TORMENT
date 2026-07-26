# TORMENT Brainvision Stage S3B v0.3
# BLOCKER-2 Operator Wrapper and Path Preparation Authorization v0.1

## 0. Document Status

document_class = BLOCKER-2 operator wrapper and path preparation authorization
document_version = v0.1
document_mode = docs-only implementation authorization

Machine-readable status block:

```text
authorization_status = "IMPLEMENTATION_AUTHORIZED"
authorized_task = "OPERATOR_WRAPPER_AND_PATH_PREPARATION"
authoritative_retained_run_authorized = false
authoritative_retained_run_executed = false
authority_consumed = false
blocker_2_state = "OPEN"
blocker_4_started = false
```

This document authorizes only the smallest future implementation surface needed
to make the already accepted BLOCKER-2 retained runtime operable by Hilmir
through one exact, auditable Windows Command Prompt wrapper. It does not modify
code, does not modify tests, does not execute native cases, does not execute
the authoritative retained run, does not create retained evidence, does not
consume authority, does not close BLOCKER-2, and does not start BLOCKER-4.

## 1. Authorization Question

Question:

```text
Should a later implementation phase be authorized to add a narrow operator
wrapper and path-preparation surface for the committed BLOCKER-2 retained
runtime?
```

Answer:

```text
Yes. The exact retained-run authorization assessment identified only wrapper,
path-preparation, and authorization-self-identity activation gaps after the
runtime correction. This document authorizes a narrow wrapper implementation
that resolves those operator gaps without authorizing execution.
```

## 2. Authoritative Baseline

Read-only baseline verified before this document was written:

| Field | Value |
| --- | --- |
| branch | `main` |
| HEAD | `e9608c56762cce3eb5840a7ca07592af7ce8235f` |
| origin/main | `e9608c56762cce3eb5840a7ca07592af7ce8235f` |
| HEAD == origin/main | `true` |
| working tree | `clean` |
| `.git/index.lock` | `absent` |

Reviewed lineage:

```text
e9608c5 docs(research): assess blocker 2 exact retained run authorization
0e8e8d1 research(brainvision): complete blocker 2 retained runtime
b647814 docs(research): authorize blocker 2 retained runtime correction
0503f1c docs(research): assess blocker 2 retained runtime readiness
e144752 research(brainvision): implement blocker 2 retained-run preparation
4a9d58a docs(research): authorize blocker 2 retained-run preparation
23504da docs(research): assess blocker 2 retained single-run readiness
82d6fce docs(research): record blocker 2 absolute-path control findings
03727e7 research(brainvision): implement blocker 2 absolute-path control
e34d3d4 docs(research): authorize blocker 2 absolute-path control
```

## 3. Preserved Boundaries

Preserved:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Brainvision remains offline, quarantined, synthetic-only, non-production,
non-service, non-kernel, non-memory-integrated, non-cognitive, and
non-autonomous.

This authorization does not modify or authorize modification of
`torment_service/kernel/`, production TORMENT memory functionality, live
service behavior, prompt or action surfaces, autonomy, identity, truth
selection, or memory cognition.

This authorization does not support claims of rename atomicity, rename
durability, power-loss persistence, general Windows support, production
readiness, or BLOCKER-2 closure. BLOCKER-4 remains separate and not started.

## 4. Controlling Assessment

Controlling assessment:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_EXACT_AUTHORITATIVE_RETAINED_SINGLE_RUN_AUTHORIZATION_v0.1.md
```

Its final verdict is:

```text
C. REQUIRE_NARROW_RUNTIME_CORRECTION
```

Its controlling readiness decisions are:

```text
FINAL_IDENTITY_BINDING_INCOMPLETE
OPERATOR_PATH_PREPARATION_REQUIRED
NARROW_OPERATOR_WRAPPER_REQUIRED
RUNTIME_REQUIRES_NARROW_CORRECTION
REQUIRE_RUNTIME_CORRECTION_BEFORE_AUTHORIZATION
```

Additional controlling document reviewed:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_POST_COMMIT_RUNTIME_CORRECTION_AUTHORIZATION_v0.1.md
```

Source review confirmed that the retained runtime exposes callable seams such
as `run_retained_single_run`,
`build_execution_authorization_identity_block`, and
`execute_existing_absolute_path_retained_case_set`, while the committed
retained files do not expose a dedicated operator CLI for the complete
identity block. Repository convention supports dedicated `run_*_v0_1.py`
modules with `argparse`, `main(argv)`, and an `if __name__ == "__main__"`
entrypoint.

## 5. Remaining Operator Gaps

The remaining operator gaps are exactly:

```text
no committed operator CLI accepts the complete identity block
no canonical operator input format is committed
exact authority/fixture/result roots need preparation and admission
post-commit authorization self-identities cannot yet be supplied through a
stable operator surface
```

This document does not reopen runtime evidence-chain design, case evaluation,
authority consumption, gate persistence, canonical hashing, or durability
ownership. Those remain owned by
`research/brainvision/blocker2_retained_absolute_path_control_v0_1.py`.

## 6. Authorization Decision

This document authorizes a later narrow implementation phase to add:

```text
one dedicated BLOCKER-2 operator wrapper
one canonical authorization-input format
one exact path-preparation mode
one non-consuming preflight-only mode
one locked authoritative execute mode
focused wrapper tests
focused path/preflight integration tests
```

This document does not authorize executing the retained run during
implementation or tests.

## 7. Authorized Architecture

Authorized architecture:

```text
one new operator-wrapper module
+
one focused unit-test module
+
one focused Windows integration-test module
+
minimal public invocation of the existing retained runtime
```

Wrapper responsibilities are limited to:

```text
parse
validate
admit
bind
display
invoke
return exact terminal status
```

The wrapper must not reimplement authority consumption, gate persistence, case
execution, `RUN_RESULT`, `RETAINED_COMPLETION`, canonical hashing, durable
file writes, directory durability, or retained evidence validation.

## 8. Authorized File Surface

Authorized future implementation files:

| Surface | Path | Authority |
| --- | --- | --- |
| NEW | `research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py` | Dedicated operator wrapper and CLI. |
| NEW | `research/brainvision/test_run_blocker2_authoritative_retained_single_run_v0_1.py` | Focused unit tests for input, modes, locks, and exit/status mapping. |
| NEW | `research/brainvision/test_run_blocker2_authoritative_retained_single_run_integration_v0_1.py` | Focused Windows path-preparation and preflight-only integration tests. |
| MODIFIED ONLY IF UNAVOIDABLE | `research/brainvision/blocker2_retained_absolute_path_control_v0_1.py` | Minimal public seam only if the wrapper cannot invoke the existing retained runtime safely. |

Prefer no modification to the retained runtime. No legacy ephemeral runner,
durable-evidence module, production file, or wildcard file surface is
authorized.

## 9. Canonical Authorization Input

Authorize one canonical JSON input format:

```text
schema = "torment.brainvision.blocker2.operator_wrapper.authorization_input.v0.1"
encoding = "UTF-8 without BOM"
canonical_json = true
duplicate_keys_rejected = true
unknown_fields_rejected = true
```

Required top-level fields:

```text
schema
authorization_status
wrapper_mode
operator_identity
single_process_declaration
single_attempt_declaration
real_executor_selector
retained_mode
authoritative
repository_identity
source_identity_inventory
document_identity_inventory
runtime_declaration_identities
path_model
execution_authorization_identity_block
retained_authorization
repository_state
source_observations
case_set
a6_selected
authorization_input_identity
execution_authorization_document_identity
fault_injection_disabled
```

The input must contain or reference every field needed for:

```text
ExecutionAuthorizationIdentityBlock
RetainedAuthorization
RepositoryState
SourceIdentity
fixture/result/authority paths
real executor selection
case set
A6 selection
operator declaration
```

The input must bind:

```text
execution authorization identity
run identity
assessment identity
implementation-preparation authorization identity
runtime-correction authorization identity
exact-run assessment/authorization identity
repository commit
branch
origin/main
six Git blob identities
six checked-out-byte SHA-256 identities
retained policy identity
native helper policy identity
schema identity
case-set identity
fixture-profile identity
authority-registry-profile identity
evidence-chain identity
retained-mode identity
authority-registry root
fixture root
result parent
result directory
operator identity
single-process declaration
single-attempt declaration
real executor selector
A6 = false
```

Reject:

```text
unknown fields
missing fields
duplicate keys
non-canonical JSON
relative paths
placeholders
UNAVAILABLE_UNTIL_COMMIT
test identities
fault-injection controls
synthetic executor selectors
```

The input file itself must have:

```text
canonical declaration identity
exact-byte SHA-256
```

The future run authorization must bind those bytes before execute mode can be
active.

## 10. Wrapper Modes

Authorize exactly three modes:

```text
PREPARE_PATHS
PREFLIGHT_ONLY
EXECUTE_EXACT_SINGLE_RUN
```

Exact future command shape:

```bat
python research\brainvision\run_blocker2_authoritative_retained_single_run_v0_1.py PREPARE_PATHS

python research\brainvision\run_blocker2_authoritative_retained_single_run_v0_1.py PREFLIGHT_ONLY --authorization-input <absolute-canonical-json-path>

python research\brainvision\run_blocker2_authoritative_retained_single_run_v0_1.py EXECUTE_EXACT_SINGLE_RUN --authorization-input <absolute-canonical-json-path>
```

The wrapper must reject any other mode.

## 11. Exact Path Model

Authorized roots:

| Role | Exact path |
| --- | --- |
| authority registry root | `C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3` |
| fixture root | `C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3` |
| result parent | `C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3` |

The future immutable result directory must be derived from the execution
authorization identity:

```text
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\<execution_authorization_identity>
```

The wrapper must derive, and must not accept arbitrary caller values for:

```text
global authority entry path
local gate path
RUN_RESULT path
RETAINED_COMPLETION path
```

All paths must be absolute, drive-qualified, canonical Win32 DOS paths outside
the repository, ordinary, non-reparse, local fixed NTFS, and
component-aware admitted. The result directory must remain absent before
authority entry.

## 12. Path Preparation Contract

`PREPARE_PATHS` may create only:

```text
C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3
C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3
```

It must not create:

```text
global authority entry
result directory
local gate
RUN_RESULT
RETAINED_COMPLETION
native fixtures that execute a transition
```

After creation it must reject reparse paths, verify local fixed NTFS, verify
ordinary directories, canonicalize paths, record path identities, record volume
evidence, and record directory identities.

The preparation record must be non-authoritative and must include:

```text
canonical paths
path identities
drive type
filesystem name
volume serial
directory identities
reparse status
repository-containment rejection
result-directory absence
authority-entry absence
preparation timestamp
retained_execution = false
authority_consumed = false
```

By default the wrapper should print this record as canonical JSON to stdout.
If later persistence is authorized, it must remain outside the future immutable
result directory and must never be interpreted as retained evidence.

## 13. Preflight-Only Contract

`PREFLIGHT_ONLY` validates the complete future authorization input without
consuming authority.

It must verify:

```text
repository state
source identities
document identities
runtime identities
authorization input bytes
execution authorization document identities
path admission
result directory absence
authority entry absence
real executor selector
case set
A6 false
fault injection disabled
```

It must not create a global authority entry, local gate, result directory,
`RUN_RESULT`, or `RETAINED_COMPLETION`. It must not call native helpers.

Accepted status:

```text
PREFLIGHT_ACCEPTED_UNCONSUMED
```

Rejected status:

```text
PREFLIGHT_REJECTED_UNCONSUMED
```

## 14. Execute-Mode Contract

`EXECUTE_EXACT_SINGLE_RUN` invokes the existing retained runtime once using
the complete validated identity block and real executor.

This mode must not be usable until a later committed execution authorization
activates the exact input bytes. It must reject:

```text
authorization_status != "ACTIVE"
uncommitted authorization document
wrong authorization Git blob
wrong authorization checked-out bytes
wrong canonical authorization declaration identity
synthetic executor selector
fault injection controls
A6 selected
wrong case order
```

Authoritative execution must internally bind:

```text
execute_existing_absolute_path_retained_case_set
```

The wrapper must expose no generic callable, module-function selector, lambda,
test executor, mock executor, or fault executor in authoritative mode.

## 15. Authorization Self-Identity Activation

The wrapper must accept and verify exact post-commit identities for the future
execution authorization document:

```text
Git blob ID
checked-out-byte SHA-256
canonical authorization declaration identity
```

Lifecycle:

```text
1. PREPARED_NOT_ACTIVE document created
2. document committed and synchronized
3. post-commit identities collected
4. exact canonical input generated
5. PREFLIGHT_ONLY succeeds
6. independent review accepts activation
7. EXECUTE_EXACT_SINGLE_RUN invoked once
```

No implementation change may be required between steps 4 and 7.

## 16. Real Executor Binding

Accepted real executor selector:

```text
REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1
```

The selector must map internally and only to:

```text
blocker2_retained_absolute_path_control_v0_1.execute_existing_absolute_path_retained_case_set
```

Rejected selectors include:

```text
synthetic
mock
lambda
callable path
module:function
test executor
fault executor
```

## 17. Case and Order Lock

Selected cases:

```text
A1
A2
A3
A5
```

Execution order:

```text
A1
A2
A3
A5
```

Machine-readable lock:

```text
a6_selected = false
case_order = "A1,A2,A3,A5"
case_set_identity = "b24057bb7ec233414d670a3e1e2aabb90f8a2728ff590b0ed4e811faf8e5f1b1"
```

Reject A4, A6, A7, A8, unknown cases, duplicate cases, and any caller-selected
case order.

## 18. Failure and Exit Contract

The wrapper must print or persist the exact runtime terminal classification.
Process exit code alone must not determine scientific status.

Required wrapper statuses:

```text
PREPARATION_COMPLETE
PREFLIGHT_ACCEPTED_UNCONSUMED
PREFLIGHT_REJECTED_UNCONSUMED
AUTHORITATIVE_RUN_COMPLETE
AUTHORITATIVE_RUN_FAILED_CONSUMED
AUTHORITATIVE_RUN_INTERRUPTED_CONSUMED
AUTHORITY_ALREADY_CONSUMED
INVALID_AUTHORIZATION_INPUT
```

No automatic rerun, retry, resume, repair, release, reset, overwrite, or
force behavior is authorized.

## 19. Test and Fault-Isolation Requirements

Input parsing tests must prove:

```text
non-canonical JSON rejected
duplicate keys rejected
unknown fields rejected
missing fields rejected
placeholder identities rejected
wrong authorization bytes rejected
```

Path preparation tests must prove:

```text
exact roots created
repository-contained paths rejected
relative/UNC/device/reparse paths rejected
non-fixed/non-NTFS profile rejected
result directory not created
authority entry not created
native executor not called
```

Preflight-only tests must prove:

```text
complete valid synthetic input accepted
authority remains unconsumed
no global entry
no local gate
no result directory
no native call
wrong source/document/path identity rejected
```

Execute-mode isolation tests must prove:

```text
execute mode requires ACTIVE committed authorization
synthetic executor cannot be selected
fault injection rejected
A6 rejected
wrong case order rejected
wrong real-executor selector rejected
```

Tests may use synthetic authorization identities, temporary roots, synthetic
executor seams, and `authoritative = false` where needed. They must not execute
a real authoritative run. Windows integration may validate path preparation,
NTFS/fixed-drive admission, BLOCKER-1 public durability interfaces, and
preflight-only behavior, but must not call real A1/A2/A3/A5 under
authoritative mode.

## 20. Claims Supported

This authorization supports:

```text
a narrow operator-wrapper implementation is justified
the wrapper can be bounded to parse/validate/admit/bind/display/invoke/status
the exact path model is fixed
the exact case order is fixed
the real executor selector is locked
authoritative execution remains unauthorized during implementation and tests
```

## 21. Claims Not Supported

This authorization does not support:

```text
authoritative retained execution has occurred
authority has been consumed
retained evidence has been created
native rename behavior has been established for closure
rename atomicity
rename durability
power-loss persistence
general Windows support
production readiness
BLOCKER-2 closure
BLOCKER-4 progress
```

The retained result remains bounded platform evidence only. It is not an
`IMMUTABLE_SCIENTIFIC_BUNDLE`, `SCIENTIFIC_COMPLETION`, publication, or
scientific truth transition.

## 22. Prohibited Actions

The future implementation phase must not:

```text
execute the authoritative retained run
run native retained rename cases in authoritative mode
create authoritative retained evidence
create or consume authoritative authority
close BLOCKER-2
start BLOCKER-4
modify production code
modify torment_service/kernel/
modify durable-evidence shared modules
broaden the file surface
add generic executor selection
add retry/release/resume/repair/force paths
commit
push
tag
stash
reset
clean
checkout another branch
delete files
delete .git/index.lock
```

## 23. Required Implementation Report

The later implementation report must include:

```text
BASELINE
AUTHORIZED FILES
WRAPPER MODES
INPUT SCHEMA
PATH MODEL
PATH PREPARATION
PREFLIGHT-ONLY SEMANTICS
EXECUTE-MODE LOCKS
REAL EXECUTOR BINDING
AUTHORIZATION SELF-IDENTITY
CASE/ORDER LOCK
FAILURE/EXIT CONTRACT
TESTS
BOUNDARY CONFIRMATION
GIT STATE
LIMITATIONS
```

It must confirm:

```text
no authoritative run executed
no authority consumed
no real evidence objects created
BLOCKER-2 remains open
BLOCKER-4 not started
```

## 24. Authorization Verdict

```text
A. AUTHORIZE_OPERATOR_WRAPPER_AND_PATH_PREPARATION
```

This verdict is selected because the document defines one exact wrapper, one
canonical input schema, one exact path model, one preparation mode, one
non-consuming preflight mode, one locked execute mode, one real executor, one
case order, and no execution authority during implementation.

## 25. Exact Next Step

Exact next step:

```text
Implement the narrow operator wrapper and path-preparation surface within only
the authorized file surface, then report implementation and tests without
executing the authoritative retained run.
```

Return control to Hilmir for review.

A. AUTHORIZE_OPERATOR_WRAPPER_AND_PATH_PREPARATION
