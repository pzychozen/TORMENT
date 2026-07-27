# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Wrapper-Mode-Specific Dual External Input Defect Assessment and Correction Authorization v0.1

## 1. Purpose

This document records the discovered wrapper-mode-specific authorization-input
contract for BLOCKER-2 Stage S3B v0.3 and authorizes a later corrected
dual-external-input preparation sequence.

This is a documentation and implementation-contract assessment artifact only.
It does not modify runtime code, wrapper code, schemas, tests, or any external
canonical JSON. It does not run PREPARE_PATHS, PREFLIGHT_ONLY, or
EXECUTE_EXACT_SINGLE_RUN. It does not consume authority.

## 2. Baseline

The repository baseline for this assessment is:

```text
repository:
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric

branch:
main

HEAD:
e4d3adde7878a0af56e35c9b41529242807e7cd6

origin/main:
e4d3adde7878a0af56e35c9b41529242807e7cd6

working tree before this document:
clean

untracked repository files before this document:
none

.git\index.lock:
absent
```

The current frozen identity is:

```text
H_ACTIVE:
e4d3adde7878a0af56e35c9b41529242807e7cd6
```

## 3. Current External Execution Input

Existing external input:

```text
C:\TORMENT\brainvision_active_authorization\blocker2_s3b_v0_3\EXACT_ACTIVE_EXECUTION_INPUT_v0.2.canonical.json
```

Verified current properties:

```text
byte length:
25736

SHA-256:
e2a1a1848827ab22448a945855228e7cd476c79442f265d2a11f040bfa6366d1

encoding:
UTF-8

BOM:
ABSENT

final newline:
ABSENT

canonical JSON:
true

authorization_input_identity:
8feefc92e251c35333f504e4adccd54f0f8df55f5cd5979909dd3f2265dd7686

canonical authorization declaration identity:
d91d1b3d9825610ea0ed68f3628f45def6f0d71aae4a1530a9e6edb878cfc4d4

wrapper_mode:
EXECUTE_EXACT_SINGLE_RUN

authorization_status:
ACTIVE

authoritative:
true
```

This file remains a valid execution-mode input bound to the historical frozen
baseline `e4d3adde7878a0af56e35c9b41529242807e7cd6`.

It is not valid as a PREFLIGHT_ONLY input under the committed wrapper contract.

It remains unconsumed and unexecuted.

This document does not edit, replace, rename, delete, or overwrite it.

## 4. Discovered Defect

The committed wrapper accepts both:

```text
--authorization-input
--mode
```

The committed validator also requires:

```text
payload["wrapper_mode"] == requested mode
```

The existing external JSON binds:

```text
payload["wrapper_mode"] = EXECUTE_EXACT_SINGLE_RUN
```

Direct side-effect-free validation against:

```text
mode = PREFLIGHT_ONLY
```

rejects with:

```text
WrapperValidationError: wrapper mode mismatch
```

Required classification:

```text
wrapper-mode-specific authorization-input contract:
yes

single external JSON reusable across PREFLIGHT_ONLY and EXECUTE_EXACT_SINGLE_RUN:
no

preflight output-contract ambiguity:
not the primary defect

runtime fail-closed behavior:
correct

runtime/schema implementation defect:
not established

authorization and sequencing architecture defect:
yes
```

This is not a hashing cycle defect.

This is not a fixed-point defect.

The wrapper is correctly fail-closed on a requested-mode mismatch. The defect is
that the prior authorization and sequencing architecture treated one external
EXECUTE_EXACT_SINGLE_RUN input as reusable for PREFLIGHT_ONLY.

## 5. Implementation Trace

Inspected implementation files:

```text
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py

research/brainvision/blocker2_retained_absolute_path_control_v0_1.py

research/brainvision/test_run_blocker2_authoritative_retained_single_run_v0_1.py

research/brainvision/test_run_blocker2_authoritative_retained_single_run_integration_v0_1.py
```

The wrapper top-level field set includes `wrapper_mode`.

`authorization_declaration(payload)` constructs:

```text
declaration_payload = all sorted payload fields except authorization_input_identity
```

`computed_authorization_input_identity(payload)` computes:

```text
authorization_input_sha256 =
SHA-256(canonical_json_bytes(declaration_payload))

canonical_authorization_declaration_identity =
SHA-256(canonical_json_bytes({
  "schema": DECLARATION_SCHEMA,
  "authorization_input": declaration_payload
}))
```

Therefore `wrapper_mode` is included in both the plain authorization-input hash
and the canonical authorization declaration identity.

`validate_authorization_payload(payload, mode=...)` checks:

```text
if payload["wrapper_mode"] != mode:
    raise WrapperValidationError(INVALID_AUTHORIZATION_INPUT, "wrapper mode mismatch")
```

The retained Stage-A execution authorization identity declaration is built in
`execution_authorization_identity_declaration(...)`. Its explicit inputs include
repository identity, controlling document identities, policy/schema identities,
prepared-root identities, host and volume identity, operator identity, process
and attempt declarations, executor selector, fault-injection declaration, case
order, A6 state, and source identities. It does not include `wrapper_mode`.

`build_execution_authorization_identity_block(...)` derives:

```text
execution_authorization_identity
result_directory
result_directory_identity
run_identity
```

downstream from the retained Stage-A declaration and derived result-directory
path. It does not add `wrapper_mode` to Stage A, result-directory identity, or
run identity.

## 6. Mode-Binding Answers

Is `wrapper_mode` a top-level authorization-input field?

```text
YES
```

Is `wrapper_mode` included in authorization_input_identity?

```text
YES
```

Reason: `computed_authorization_input_identity` hashes every top-level payload
field except `authorization_input_identity`.

Is `wrapper_mode` included in execution_authorization_identity?

```text
NO
```

Reason: the retained Stage-A declaration does not take `wrapper_mode` as an
input.

Is `wrapper_mode` included in run_identity?

```text
NO
```

Reason: `run_identity_declaration` takes execution authorization identity,
repository identity, case set/order, prepared-root identities,
result_directory_identity, operator identity, attempt declaration, executor
selector, and A6 state. It does not take `wrapper_mode`.

Is `wrapper_mode` included in result_directory_identity?

```text
NO
```

Reason: `result_directory_identity` is a path identity over the derived result
directory. The derived result directory is downstream of
execution_authorization_identity, which does not include `wrapper_mode`.

Is `wrapper_mode` included in canonical authorization declaration identity?

```text
YES
```

Reason: the canonical declaration wraps the same declaration payload that
contains all top-level fields except `authorization_input_identity`.

## 7. Expected Identity Divergence

For two otherwise identical payloads differing only in:

```text
wrapper_mode = PREFLIGHT_ONLY
```

versus:

```text
wrapper_mode = EXECUTE_EXACT_SINGLE_RUN
```

the expected identity behavior is:

| Item | Status | Reason |
| --- | --- | --- |
| canonical bytes | DIFFERENT | The canonical JSON contains a different `wrapper_mode` string. |
| byte length | DIFFERENT | `PREFLIGHT_ONLY` is shorter than `EXECUTE_EXACT_SINGLE_RUN`; the in-memory mode-only variant was 25726 bytes versus 25736 bytes. |
| plain external SHA-256 | DIFFERENT | SHA-256 is over the exact external bytes. |
| authorization_input_identity | DIFFERENT | `authorization_input_sha256` hashes all top-level fields except its own field, including `wrapper_mode`. |
| canonical authorization declaration identity | DIFFERENT | The declaration wraps the same mode-specific declaration payload. |
| execution_authorization_identity | SAME | Stage A does not include `wrapper_mode`. |
| result directory | SAME | The result directory is derived from the unchanged execution_authorization_identity. |
| result_directory_identity | SAME | The path is unchanged when only `wrapper_mode` changes. |
| run_identity | SAME | Stage C uses execution_authorization_identity, result_directory_identity, repository identity, case profile, root identities, operator, attempt declaration, executor selector, and A6 state; it does not use `wrapper_mode`. |

Read-only in-memory comparison against the existing execution JSON produced:

```text
execution input bytes:
25736

mode-only PREFLIGHT variant bytes:
25726

execution input SHA-256:
e2a1a1848827ab22448a945855228e7cd476c79442f265d2a11f040bfa6366d1

mode-only PREFLIGHT variant SHA-256:
1064a5a7a2cac148be4fc2c63cd633b41119d46e292838897b88c95d92197dab

execution authorization_input_identity:
8feefc92e251c35333f504e4adccd54f0f8df55f5cd5979909dd3f2265dd7686

mode-only PREFLIGHT authorization_input_identity:
35b0604d57e30348bd5325ce28c8a106483bebb94a15289205f638e868f7ca20

execution canonical authorization declaration identity:
d91d1b3d9825610ea0ed68f3628f45def6f0d71aae4a1530a9e6edb878cfc4d4

mode-only PREFLIGHT canonical authorization declaration identity:
36387405cab3aed758130f6c1081a171dd491a56d4b8c8595238c1b6124d489a

execution_authorization_identity:
a0d298c31c50b7632b911aef2eab966b0f4075bb1a5a1f1437a003b6b8f612b3

result directory:
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\a0d298c31c50b7632b911aef2eab966b0f4075bb1a5a1f1437a003b6b8f612b3

result_directory_identity:
ff5c34001b20b07f59031f1629419b001594ab3ccbaf19b1dd9d08a24361a8a7

run_identity:
4cc2a574b4d7925d5a1c7bb196df015f26b174b3aed8ab086e33d762b3a003ef
```

The in-memory PREFLIGHT values above are not authorized as an external JSON in
this task. They are recorded only to classify identity divergence.

## 8. Preflight Payload Requirements

A valid ACTIVE preflight input must use:

```text
authorization_status = ACTIVE
wrapper_mode = PREFLIGHT_ONLY
authoritative = true
```

Implementation basis:

```text
validate_authorization_payload(payload, mode=PREFLIGHT_ONLY)
```

requires the requested mode to match `payload["wrapper_mode"]`.

For PREFLIGHT_ONLY and EXECUTE_EXACT_SINGLE_RUN, the execution authorization
document identity must declare:

```text
authorization_status = ACTIVE
```

The top-level payload must also declare:

```text
authorization_status = ACTIVE
```

The wrapper rejects non-authoritative input:

```text
authoritative must be true
```

Therefore the future preflight JSON and future execution JSON must be separate
canonical inputs, each with a mode-specific `wrapper_mode` and mode-specific
authorization_input_identity.

## 9. Evidence-Side Effects

Committed preflight behavior:

```text
creates result directory:
NO

creates GLOBAL_AUTHORITY_ENTRY:
NO

creates LOCAL_GATE_ENTRY:
NO

creates RUN_RESULT:
NO

creates RETAINED_COMPLETION:
NO

consumes authority:
NO

calls real executor:
NO

calls native promotion helper as an execution action:
NO

writes output to disk:
NO

emits canonical result only to stdout by default:
YES
```

Implementation basis:

`preflight_only(...)` validates the authorization payload, checks that
`result_directory`, `global_authority_entry_path`, `local_gate_path`,
`run_result_path`, and `retained_completion_path` do not already exist, calls
`retained.preflight_retained_authorization(...)`, and returns an in-memory
wrapper result record.

`preflight_retained_authorization(...)` validates repository, source,
authorization, result-directory absence, fixture-root state, policy identity,
schema identity, case selection, and execution-authorization identity. It returns
an in-memory preflight dictionary with schema:

```text
torment.brainvision.blocker2.retained.preflight.v0.1
```

It does not create result directories, authority entries, gate entries,
RUN_RESULT, or RETAINED_COMPLETION artifacts.

The wrapper CLI prints a wrapper result record to stdout. With default
`--format json`, the printed schema is:

```text
torment.brainvision.blocker2.operator_wrapper.result.v0.1
```

Expected wrapper terminal labels:

```text
success:
PREFLIGHT_ACCEPTED_UNCONSUMED

validation/evidence rejection:
PREFLIGHT_REJECTED_UNCONSUMED

invalid authorization input:
INVALID_AUTHORIZATION_INPUT
```

The success record has:

```text
authoritative = false
retained_execution = false
authority_consumed = false
```

The rejection record also has:

```text
authoritative = false
retained_execution = false
authority_consumed = false
```

## 10. Exact Future CLI Shape

The committed parser accepts:

```text
--mode
--authorization-input
--format
```

with `--format` choices:

```text
json
human
both
```

and default:

```text
json
```

A later exact preflight authorization, after a valid mode-specific preflight JSON
exists, should use the committed wrapper syntax:

```bat
python research\brainvision\run_blocker2_authoritative_retained_single_run_v0_1.py ^
  --authorization-input "C:\TORMENT\brainvision_active_authorization\blocker2_s3b_v0_3\<H_ACTIVE_DUAL>\EXACT_ACTIVE_PREFLIGHT_INPUT_v0.2.canonical.json" ^
  --mode PREFLIGHT_ONLY ^
  --format json
```

This document does not authorize running that command.

## 11. Corrected Dual-Input Architecture

Mode-specific inputs are required.

Corrected sequence:

```text
1. Commit this correction documentation.
2. Synchronize repository.
3. Define the new synchronized frozen commit as H_ACTIVE_DUAL.
4. Derive one external ACTIVE PREFLIGHT canonical JSON against H_ACTIVE_DUAL.
5. Derive one external ACTIVE EXECUTION canonical JSON against H_ACTIVE_DUAL.
6. Independently review both external JSON files.
7. Authorize exactly one PREFLIGHT_ONLY invocation using only the preflight JSON.
8. Review the preflight result.
9. Authorize exactly one EXECUTE_EXACT_SINGLE_RUN invocation using only the execution JSON.
```

No current ACTIVE identity may be silently carried forward without
re-verification at H_ACTIVE_DUAL.

No future commit hash is defined by this document.

H_ACTIVE_DUAL is a future synchronized commit identity, not a placeholder hash.

## 12. Non-Overwrite External Layout

The existing execution filename is already occupied:

```text
C:\TORMENT\brainvision_active_authorization\blocker2_s3b_v0_3\EXACT_ACTIVE_EXECUTION_INPUT_v0.2.canonical.json
```

It must be preserved unchanged as historical evidence for the e4d3adde-bound
execution-mode input.

Preferred fail-closed correction strategy:

```text
preserve the existing e4d3adde-bound execution JSON unchanged as historical evidence

use a new baseline-specific directory for regenerated inputs
```

Future procedural directory:

```text
C:\TORMENT\brainvision_active_authorization\blocker2_s3b_v0_3\<H_ACTIVE_DUAL>\
```

Future external files:

```text
EXACT_ACTIVE_PREFLIGHT_INPUT_v0.2.canonical.json

EXACT_ACTIVE_EXECUTION_INPUT_v0.2.canonical.json
```

The directory path is procedural and not identity-bound.

No existing external JSON may be overwritten.

## 13. Repository-Sequencing Consequence

Any committed correction document advances HEAD.

Therefore the current e4d3adde-bound external execution JSON becomes historical
and cannot be used against the new live repository baseline after this correction
document is committed.

Both mode-specific external inputs must be regenerated against the later
synchronized frozen commit.

No current ACTIVE identity may be silently carried forward without
re-verification.

This document does not bind its own future containing commit.

This document does not derive H_ACTIVE_DUAL.

This document does not create either future external JSON.

## 14. Current Historical Identity State

The following values are current historical identities for the e4d3adde baseline:

```text
H_ACTIVE:
e4d3adde7878a0af56e35c9b41529242807e7cd6

execution_authorization_identity:
a0d298c31c50b7632b911aef2eab966b0f4075bb1a5a1f1437a003b6b8f612b3

result directory:
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\a0d298c31c50b7632b911aef2eab966b0f4075bb1a5a1f1437a003b6b8f612b3

result_directory_identity:
ff5c34001b20b07f59031f1629419b001594ab3ccbaf19b1dd9d08a24361a8a7

run_identity:
4cc2a574b4d7925d5a1c7bb196df015f26b174b3aed8ab086e33d762b3a003ef

authorization_input_identity:
8feefc92e251c35333f504e4adccd54f0f8df55f5cd5979909dd3f2265dd7686
```

They are not authority for a future advanced HEAD.

Historical inactive identities remain historical only and must not be
substituted.

## 15. Real Evidence State

Read-only evidence-state verification before this document:

```text
derived result directory:
ABSENT

GLOBAL_AUTHORITY_ENTRY:
ABSENT

LOCAL_GATE_ENTRY:
ABSENT

RUN_RESULT:
ABSENT

RETAINED_COMPLETION:
ABSENT

authority_consumed:
false
```

No preflight was run.

No execution was run.

The current execution JSON remains unconsumed.

No result directory or evidence object was created by this task.

## 16. Security Invariants

Preserve:

```text
one-shot authority
no retry
no resume
no overwrite
no repair
no executor substitution
exact A1,A2,A3,A5 order
A6=false
fault injection disabled
fixed prepared roots
repository/source/document/root/operator binding
single process
single attempt
four-object evidence chain
no authority consumption during preflight
no automatic transition from preflight to execution
separate execution authorization after preflight review
```

The correction must not weaken wrapper-mode binding.

The correction must not allow mode mismatch.

The correction must not edit the existing execution JSON in place.

## 17. Project Boundaries

Preserve:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Brainvision remains:

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

BLOCKER state remains:

```text
BLOCKER-2:
OPEN

BLOCKER-4:
inactive
```

Do not begin BLOCKER-4.

## 18. Authorization

This document authorizes only a later correction sequence:

```text
commit this correction documentation
synchronize repository
define H_ACTIVE_DUAL
prepare one external ACTIVE PREFLIGHT canonical JSON
prepare one external ACTIVE EXECUTION canonical JSON
review both
separately authorize one PREFLIGHT_ONLY invocation
review preflight
separately authorize one EXECUTE_EXACT_SINGLE_RUN invocation
```

This document does not authorize:

```text
PREPARE_PATHS
PREFLIGHT_ONLY
EXECUTE_EXACT_SINGLE_RUN
external JSON creation in this task
external JSON replacement
authority consumption
result-directory creation
evidence-object creation
code changes
schema changes
test changes
```

Runtime or schema changes are not established as required by this assessment.
The committed implementation already enforces a mode-specific input contract and
fails closed on mismatch. The required correction is sequencing and external
artifact architecture.

## 19. Stop Boundary

This task ends after:

```text
the one requested defect-assessment/correction-authorization document is created
its exact bytes are hashed
its implementation claims are validated
the repository contains exactly that one untracked file
```

Do not:

```text
stage
commit
push
derive H_ACTIVE_DUAL
create either new external JSON
run preflight
run execution
consume authority
```
