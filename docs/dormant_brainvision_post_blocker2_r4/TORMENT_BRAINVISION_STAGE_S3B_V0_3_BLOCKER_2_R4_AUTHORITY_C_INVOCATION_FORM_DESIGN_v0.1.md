# TORMENT Brainvision Stage S3B v0.3
# BLOCKER-2 R4 - Authority-C Invocation-Form Design v0.1

```text
DRAFT ONLY
NON-EXECUTING
NOT AUTHORISED FOR IMPLEMENTATION
NOT ISSUED
NOT ACTIVE
NOT COMMITTED
NOT PUSHED
```

## 1. Document Status

This document is a non-executing design draft.

It does not implement an Authority-C invocation form.

It does not execute an Authority-C invocation form.

It does not activate Authority C.

It does not issue the Authority-C non-commit activation declaration.

It does not construct candidate bytes.

It does not contact any governed external path.

It does not read or write the governed canonical-input path.

It does not invoke PREPARE_PATHS, PREFLIGHT_ONLY, EXECUTE_EXACT_SINGLE_RUN, the
A/B orchestrator, or any corrected-lane runner.

It does not create execution authority.

It does not close the corrected commit-free window.

It does not begin BLOCKER-4.

It does not stage, commit, push, fetch, pull, or mutate repository state.

## 2. Design Classification

Classification:

```text
B. AUTHORITY_C_INVOCATION_FORM_DESIGN_COMPLETE_WITH_IMPLEMENTATION_PREREQUISITES
```

Rationale:

This document defines the exact future Authority-C invocation form, argument
contract, authority assertions, one-shot mechanism, validation-mode solution,
injection requirements, result contract, exit-code semantics, failure-state
contract, canonical-input-path contact rule, and required tests.

It does not claim implementation readiness. The exact source entry point and
tests still need to be implemented and reviewed before the Authority-C
declaration can be issued.

## 3. Controlling Identities

Accepted invocation HEAD:

```text
1f915e29119cd58ea39e8cf355f7364118c71043
```

Runner source:

```text
path:
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py

Git blob OID:
79d0c89575919c8506c8b9f1278efd5d63b1e813

byte count:
46788

SHA-256:
c61de2f7829e3eb2bb938701f98bbafe54f09f03dab8abd718d421a81b56e976
```

Retained-control source:

```text
path:
research/brainvision/blocker2_retained_absolute_path_control_v0_1.py

Git blob OID:
1779715ed17fffe3a927d24eb445eec51f3d42d6

byte count:
144698

SHA-256:
dc4a6e3f1169c33a2379c3506d107893cb8a48c977300c22bda14db0bf19e3d5
```

Authority-C declaration draft:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_NON_COMMIT_ACTIVATION_DECLARATION_DRAFT_v0.1.md

byte count:
22726

SHA-256:
2c2500e624d77c70d33a6c5d29db6f5f04442fbc6a75a5930e90b89f0df64750
```

Authority-C governance analysis:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_C_ACTIVATION_AND_CANONICAL_INPUT_PREPARATION_GOVERNANCE_ANALYSIS_v0.1.md

byte count:
25324

SHA-256:
0107bf4cddd905701cb88367959a69284ca77d70df6d214236542371ad84e5b8
```

Accepted A/B evidence record:

```text
path:
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_AUTHORITY_A_B_ACCEPTED_EXECUTION_EVIDENCE_RECORD_v0.1.md

byte count:
10514

SHA-256:
22a3dd6ca89a0a3fe218f5ddd615e8fe61bdcb6b9ea8e6b5c2b1b228ce5e4beb
```

## 4. Existing Reusable Components

The future Authority-C implementation may reuse these existing runner
components as components only:

```text
canonical_json_bytes
computed_authorization_input_identity
with_computed_authorization_input_identity
derived_path_model
expected_runtime_identities
validate_authorization_payload
```

The future implementation may also reuse retained-control helpers that produce
identity declarations and blocks:

```text
execution_authorization_identity_declaration
build_execution_authorization_identity_block
run_identity_declaration
```

These are reusable validation or identity-building components. They are not a
complete Authority-C invocation form.

Existing non-compliant surfaces for Authority C:

```text
run_mode_from_file:
requires an authorization-input file path and can dispatch to runner modes

main:
CLI runner entry point, not an Authority-C in-memory-only entry point

prepare_paths:
performs PREPARE_PATHS path preparation and may create directories

preflight_only:
performs runner preflight checks, not Authority-C candidate construction

execute_exact_single_run:
can invoke retained execution

validate_authorization_payload with repository_state=None:
can call collect_repository_state after activation

validate_authorization_payload with file_identity_provider=None:
can fall back to _file_identity_from_disk and git rev-parse after activation
```

Therefore the complete Authority-C invocation form must be a new seam.

## 5. Future Entry Point

Exact future callable:

```python
def run_authority_c_candidate_construction(
    *,
    accepted_invocation_head: str,
    authority_assertions: AuthorityCAssertions,
    repository_state: retained.RepositoryState,
    file_identity_provider: FileIdentityProvider,
    source_identity_inventory: Mapping[str, object],
    document_identity_inventory: Mapping[str, object],
    runtime_declaration_identities: Mapping[str, object],
    path_model: Mapping[str, object],
    execution_authorization_identity_block: Mapping[str, object],
    retained_authorization: Mapping[str, object],
    source_observations: Mapping[str, object],
    canonical_input_absence_observation: Mapping[str, object],
    one_shot_latch_key: str,
) -> Mapping[str, object]:
    ...
```

Entry-point requirements:

```text
does not require an authorization-input file path
does not accept an execution mode argument
does not accept PREPARE_PATHS
does not accept PREFLIGHT_ONLY
does not accept EXECUTE_EXACT_SINGLE_RUN
does not call run_mode_from_file
does not call main
does not call prepare_paths
does not call preflight_only
does not call execute_exact_single_run
does not call retained.run_retained_single_run
```

The callable must construct the candidate payload object in memory, serialize
the canonical candidate bytes in memory, compute the candidate identity in
memory, validate the candidate in memory, and return an operator-visible result
mapping.

No CLI is authorized by this design. A CLI may be designed later only as a thin
adapter over this callable and only if it preserves the same no-file,
no-runner-mode, no-Git-after-activation contract.

## 6. Argument Contract

`accepted_invocation_head` must equal:

```text
1f915e29119cd58ea39e8cf355f7364118c71043
```

`authority_assertions` must be exact and complete.

`repository_state` is required. `repository_state=None` is prohibited.

`file_identity_provider` is required. `file_identity_provider=None` is
prohibited.

`source_identity_inventory`, `document_identity_inventory`,
`runtime_declaration_identities`, `path_model`,
`execution_authorization_identity_block`, `retained_authorization`, and
`source_observations` must be precomputed before declaration issuance.

`canonical_input_absence_observation` must be precomputed before declaration
issuance and must state that the governed canonical-input path was positively
absent on the `final_child_absent` / `ERROR_FILE_NOT_FOUND` basis. It must not
be refreshed during Authority C.

`one_shot_latch_key` must be the exact process-local key derived from:

```text
accepted invocation HEAD
Authority-C declaration draft SHA-256
Authority-C operation label
```

The initial accepted key preimage must include:

```text
accepted_invocation_head:
1f915e29119cd58ea39e8cf355f7364118c71043

authority_c_declaration_sha256:
2c2500e624d77c70d33a6c5d29db6f5f04442fbc6a75a5930e90b89f0df64750

operation_label:
AUTHORITY_C_CANONICAL_INPUT_CANDIDATE_CONSTRUCTION_AND_VALIDATION
```

The implementation must reject missing, unknown, duplicated, placeholder, or
synthetic argument values before candidate construction.

## 7. Authority Assertions

Required authority assertions:

```text
window_open:
true

authority_c_active:
true

authority_d_active:
false

authority_e_active:
false

formal_hold_active:
true

blocker_2_open:
true

blocker_4_inactive:
true
```

No Authority-C operation may begin unless every assertion is present and exact.

CLI or callable flags assert already-established governance state. They do not
create authority.

Any assertion mismatch is a pre-contact abort:

```text
contact_started:
false

opportunity_consumed:
false

classification:
AUTHORITY_C_PRE_CONTACT_ABORT
```

## 8. Lock-Safe Pre-Issuance Repository-State Injection

The invocation form requires a precomputed `RepositoryState` collected before
declaration issuance using the same lock-safe Git posture as Authority A:

```text
GIT_OPTIONAL_LOCKS=0
git --no-optional-locks
```

During Authority C:

```text
repository_state=None:
PROHIBITED

collect_repository_state:
PROHIBITED
```

The precomputed repository state must bind:

```text
branch:
main

HEAD:
1f915e29119cd58ea39e8cf355f7364118c71043

local refs/remotes/origin/main:
1f915e29119cd58ea39e8cf355f7364118c71043

.git/index.lock:
ABSENT

staged:
NONE

tracked deletions:
NONE

unmerged:
NONE

untracked:
exact pre-issuance inventory injected through RepositoryState
```

The invocation form must not embed a fixed list of untracked document names.
The pre-issuance collector must inject the exact `RepositoryState` observed
immediately before declaration issuance. Authority C must compare only to that
injected object and to the candidate payload form derived from that object.

Pattern-based repository-state policy:

```text
Allowed untracked status pattern:
?? docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_R4_*.md

Allowed untracked file type:
Markdown documentation draft only

Required exclusion:
no source file
no test file
no canonical JSON input file
no governed external path
no staged path
no tracked deletion
no unmerged path
no untracked path outside the allowed R4 Markdown pattern

Inventory authority:
the exact `status_lines`, `dirty_authorized_surfaces`, and
`dirty_unrelated_surfaces` captured in the injected RepositoryState payload
```

`dirty_authorized_surfaces` and `dirty_unrelated_surfaces` are produced by
`classify_working_tree_status` against the frozen `AUTHORIZED_SURFACE_PATHS`
constant in `blocker2_retained_absolute_path_control_v0_1.py`. That constant
contains only six `research/brainvision` `.py` paths and no `docs/` path.

Under the corrected commit-free window, the expected values are:

```text
dirty_authorized_surfaces:
empty unless one of the six authorised .py surfaces is genuinely modified

dirty_unrelated_surfaces:
non-empty; it contains every R4 documentation draft and every known CRLF-view
artefact path
```

These values must be accepted exactly as captured during pre-issuance
verification. Neither list may be asserted empty merely as a policy expectation.
`dirty_authorized_surfaces` must not be asserted to equal the R4 documentation
set.

`AUTHORIZED_SURFACE_PATHS` must not be modified to reclassify the documentation
drafts or CRLF-view artefacts. Such a change would be a repository source
modification prohibited while the corrected commit-free window remains open.

The R4 Markdown pattern policy governs which untracked entries may appear in
`status_lines`. It does not govern the `dirty_authorized_surfaces` /
`dirty_unrelated_surfaces` split, which remains determined by the frozen
retained-control constant.

Pre-contact verification must:

```text
1. apply the R4 Markdown pattern policy to the untracked (`??`) subset of
   status_lines;
2. verify zero staged entries, tracked deletions, and unmerged entries;
3. verify the known tracked CRLF-view artefact set has not changed;
4. require exact equality between the captured RepositoryState and the injected
   RepositoryState payload;
5. accept the dirty_* lists exactly as measured rather than attempting to force
   them into a different classification.
```

The candidate payload's `repository_state` field must be exactly equal to
`repository_state.as_payload()` from the injected `RepositoryState` object,
including list order and every status line. Any mismatch is a pre-contact abort
if detected before `begin_contact()` and a validation terminal failure if
detected inside the validation core after contact.

If repository state cannot be collected safely before issuance, Authority C
must not activate.

After Authority-C activation, the invocation form must not inspect repository
state. It must compare only against the injected `RepositoryState`.

## 9. File-Identity Provider Injection

The invocation form requires an injected `FileIdentityProvider`.

During Authority C:

```text
file_identity_provider=None:
PROHIBITED

_file_identity_from_disk default path:
PROHIBITED

git rev-parse:
PROHIBITED

git status:
PROHIBITED

git show:
PROHIBITED

git cat-file:
PROHIBITED

any subprocess or shell process:
PROHIBITED
```

The provider must be constructed or bound before declaration issuance.

Preferred adapter:

```text
PrecomputedImmutableFileIdentityProvider
```

Adapter contract:

```python
class PrecomputedImmutableFileIdentityProvider:
    def __init__(self, identities: Mapping[str, FileIdentity]) -> None:
        ...

    def __call__(self, path: str) -> FileIdentity:
        ...
```

Adapter requirements:

```text
returns only from a precomputed immutable mapping
lookup keys are repository-relative POSIX paths
lookup keys use `/` separators only
lookup keys do not begin with `/`
lookup keys do not contain drive prefixes
lookup keys do not contain `..`
does not perform case normalization
does not perform case folding
does not perform Unicode normalization
matches keys case-sensitively and exactly
does not read files
does not call Git
does not start subprocesses or shell processes
does not fall back to _file_identity_from_disk
does not return a default identity
does not return None
raises a validation error for unknown paths
```

Exact lookup-key derivation:

```python
absolute_path.relative_to(repo_root).as_posix()
```

The derived key must be used exactly as produced by that expression after the
pre-issuance ordinary-file and repository-containment checks. It must remain a
repository-relative POSIX path with forward slashes, case-sensitive exact
matching, no case or Unicode normalization, no fallback, no default, no `None`,
and unknown-key rejection.

Exact `FileIdentity` return shape:

```text
git_blob_oid:
40-character lowercase hex Git blob identity from accepted HEAD

checked_out_byte_sha256:
64-character lowercase hex SHA-256 over same-capture checked-out bytes

checked_out_byte_length:
non-negative integer byte length over same-capture checked-out bytes
```

The provider mapping must be captured before declaration issuance. For each
repository-relative POSIX key, the capture must verify:

```text
repository containment:
the resolved checked-out path remains inside the repository root

ordinary file:
the checked-out path is a regular file

Git blob identity:
the blob identity is taken from accepted HEAD for exactly that key

same-capture bytes:
checked_out_byte_sha256 and checked_out_byte_length are computed from the same
byte read used for the identity capture

symlink rejection:
symlink paths are rejected

junction rejection:
Windows junction paths are rejected

reparse-point rejection:
Windows reparse-point paths are rejected

case-sensitive path check:
the requested key must match the captured repository path casing exactly
```

If any path is outside the repository, absent, non-ordinary, a symlink, a
junction, a reparse point, unknown to accepted HEAD, or case-mismatched, the
provider must be unavailable and Authority C must not activate.

The existing validator's injected provider contract is sufficient only if a
provider is always supplied. Its fallback behavior is insufficient for
Authority C and must be blocked by wrapper-level prechecks before candidate
construction.

## 10. No Process-Launch Guarantee

After Authority-C activation:

```text
subprocess.Popen:
PROHIBITED

subprocess.run(["git", ...]):
PROHIBITED

subprocess.run:
PROHIBITED

subprocess.call:
PROHIBITED

subprocess.check_call:
PROHIBITED

subprocess.check_output:
PROHIBITED

os.system:
PROHIBITED

os.popen:
PROHIBITED

every available os.spawn* function:
PROHIBITED

any subprocess or shell process:
PROHIBITED

collect_repository_state:
PROHIBITED

_file_identity_from_disk default path:
PROHIBITED

repository_state=None:
PROHIBITED

file_identity_provider=None:
PROHIBITED
```

The implementation must fail before candidate construction if either injection
is absent.

Tests must patch or trap:

```text
subprocess.Popen
subprocess.run
subprocess.call
subprocess.check_call
subprocess.check_output
os.system
os.popen
every available os.spawn* function
```

`subprocess.Popen` is the primary subprocess chokepoint. The other named
surfaces must also be explicitly denied or proven to delegate through the
trapped chokepoint.

The prohibition covers all process execution, not only commands containing the
word Git. No subprocess or shell process may be started after Authority-C
activation.

Any process-launch attempt during the Authority-C operation must classify the
result as:

```text
AUTHORITY_C_VALIDATION_TERMINAL_FAILURE
```

if construction has begun, otherwise:

```text
AUTHORITY_C_PRE_CONTACT_ABORT
```

The result must set:

```text
git_subprocess_attempted:
true

process_launch_attempted:
true
```

when the trap observes the attempt.

## 11. Closed Candidate Field Set

TOP_LEVEL_FIELDS count:

```text
23
```

Exact full set in source order:

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

`authorization_input_identity` is calculated over the payload excluding
`authorization_input_identity` itself.

Wrapper schema:

```text
torment.brainvision.blocker2.operator_wrapper.authorization_input.v0.2
```

Declaration schema:

```text
torment.brainvision.blocker2.operator_wrapper.authorization_input_declaration.v0.2
```

Retained schema:

```text
torment.brainvision.blocker2.retained.authorization_input.v0.1
```

Retained mode:

```text
BLOCKER2_ABSOLUTE_PATH_CONTROL_RETAINED_SINGLE_RUN_V0_1
```

Real executor selector:

```text
REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1
```

`expected_branch` is nested and must not be added as an independent top-level
field.

The top-level selector field is `real_executor_selector`. `selector` must not
be added as an independent top-level field.

## 12. In-Memory-Only Construction

Required construction model:

```text
Python bytecode emission:
suppressed by interpreter launch before Authority-C code import or execution

candidate payload object:
constructed in process memory only

canonical candidate bytes:
constructed in process memory only

candidate identity:
calculated in process memory only

filesystem writes:
zero
```

Prohibited primitives and patterns:

```text
temporary files
sibling files
NamedTemporaryFile
mkstemp
Path.write_bytes
open(..., "w")
open(..., "wb")
authorization-input output path
canonical-input path creation
```

Authority C may create no file of any kind.

Candidate bytes must exist only in process memory during this authority.

Mandatory bytecode suppression:

```text
Authority-C process launch:
must use python -B

PYTHONDONTWRITEBYTECODE:
must be present and set to 1 in the environment before the Python interpreter
starts

startup semantics:
PYTHONDONTWRITEBYTECODE is read at interpreter startup. Setting
os.environ["PYTHONDONTWRITEBYTECODE"] after startup does not activate bytecode
suppression and is not an acceptable substitute.

sys.dont_write_bytecode:
the Authority-C entry module must execute `import sys` and then
`sys.dont_write_bytecode = True` before every other import

import ordering:
No other executable statement may occur between `import sys` and
`sys.dont_write_bytecode = True`. The assignment must occur before importing
run_blocker2_authoritative_retained_single_run_v0_1,
blocker2_retained_absolute_path_control_v0_1, or any other Authority-C
dependency capable of generating repository bytecode

pre-validation assertions:
before argument or injection validation, the entry point must assert
sys.dont_write_bytecode is True, sys.flags.dont_write_bytecode is non-zero, and
PYTHONDONTWRITEBYTECODE was present and truthy in the inherited process
environment

failure:
if any bytecode-launch assertion fails, Authority C must abort pre-contact with
exit 2, contact_started=false, and opportunity_consumed=false

callable limitation:
the callable cannot establish these launch-time protections itself. It may only
verify that they were already active.

PYTHONPYCACHEPREFIX:
may additionally point to a directory outside the repository, but it does not
replace python -B and PYTHONDONTWRITEBYTECODE=1 unless separately approved

__pycache__ creation:
prohibited anywhere inside the repository at import time or during Authority C

.pyc creation:
prohibited anywhere inside the repository at import time or during Authority C
```

Direct filesystem-write protections must trap at least:

```text
builtins.open with mode containing w, a, x, or +
Path.open with mode containing w, a, x, or +
Path.write_bytes
Path.write_text
Path.touch
Path.mkdir
os.open with O_WRONLY, O_RDWR, O_CREAT, O_TRUNC, or O_APPEND
os.mkdir
os.makedirs
os.remove
os.unlink
os.rmdir
os.rename
os.replace
shutil.copy
shutil.copy2
shutil.copyfile
shutil.copytree
shutil.move
tempfile.NamedTemporaryFile
tempfile.TemporaryFile
tempfile.mkstemp
tempfile.mkdtemp
logging.FileHandler
```

Indirect filesystem-write protections must also prohibit:

```text
result-file emission
stdout or stderr emission of candidate payload
stdout or stderr emission of canonical candidate bytes
logging of candidate payload
logging of canonical candidate bytes
serialization of candidate payload outside process memory
serialization of canonical candidate bytes outside process memory
subprocess or shell process launch by any surface
imports or cache creation that produce bytecode during Authority C
pytest cache creation
.pytest_cache creation inside the repository
```

The implementation must include write traps for tests. A trap must fail the test
if any direct or indirect filesystem-writing primitive is called during
Authority C. In production, any such attempt at or after `begin_contact()` must
be classified as `AUTHORITY_C_CONSTRUCTION_TERMINAL_FAILURE` or
`AUTHORITY_C_VALIDATION_TERMINAL_FAILURE` according to phase, with
`opportunity_consumed:true`.

## 13. Candidate Construction Sequence

The invocation form must perform this sequence:

```text
1. Verify that bytecode suppression is already in force.
2. Verify required arguments are present.
3. Verify there are no unknown, duplicated, placeholder, or synthetic
   arguments.
4. Verify authority assertions are exact.
5. Verify repository_state is injected.
6. Verify file_identity_provider is injected.
7. Verify accepted_invocation_head equals the accepted HEAD.
8. Verify injected repository_state equals the accepted HEAD, branch,
   origin/main, zero staged entries, no tracked deletions, no unmerged entries,
   unchanged known CRLF-view artefact set, the exact pattern-admitted
   pre-issuance inventory in status_lines, and the dirty_* lists exactly as
   measured by the frozen retained-control classifier.
9. Verify injected canonical_input_absence_observation has the complete
   final_child_absent / ERROR_FILE_NOT_FOUND positive-absence structure and
   sequence-final freshness.
10. Verify source and document identity inputs are complete.
11. Verify source and document identity providers are immutable, exact,
    precomputed, and fallback-free.
12. Verify result, diagnostic, filesystem-write, cache-creation, and
    process-launch traps are armed for the operation.
13. Acquire process-local one-shot latch in
   AUTHORITY_C_ACTIVE_CONSTRUCTION_NOT_BEGUN state.
14. Immediately before constructing the first candidate payload value, call
    begin_contact on the latch.
15. Construct the first candidate payload value in memory.
16. Complete the 23-field candidate payload in memory.
17. Compute authorization_input_identity with
    with_computed_authorization_input_identity.
18. Serialize canonical candidate bytes with canonical_json_bytes.
19. Compute candidate_byte_count and candidate_sha256 from the in-memory bytes.
20. Validate the candidate with the Authority-C validation core.
21. Return the canonical operator-visible result.
22. Stop.
```

Required evidence for step 1:

```text
python -B active
PYTHONDONTWRITEBYTECODE=1 inherited from interpreter launch
sys.dont_write_bytecode == True
sys.flags.dont_write_bytecode != 0
```

The callable must not claim to establish these conditions after import.

All argument validation, injection validation, and precomputed-observation
validation must be complete before latch acquisition.

Steps 1 through 13 are pre-contact. Failure there must return
`contact_started:false` and `opportunity_consumed:false`.

Step 14 begins Authority-C contact and consumes the opportunity.

Any failure after step 14 must return `opportunity_consumed:true` or
`UNKNOWN` according to exact observables.

## 14. One-Shot Enforcement

Chosen mechanism:

```text
process-local latch
```

The future implementation must define a private process-local latch registry:

```python
_AUTHORITY_C_LATCH_REGISTRY_LOCK = threading.Lock()
_AUTHORITY_C_LATCHES: dict[str, AuthorityCInvocationLatch]
```

Latch key:

```text
one_shot_latch_key
```

Latch states:

```text
AUTHORITY_C_ACTIVE_CONSTRUCTION_NOT_BEGUN
AUTHORITY_C_CONSTRUCTION_BEGUN
AUTHORITY_C_CANDIDATE_CONSTRUCTED_IN_MEMORY
AUTHORITY_C_CANDIDATE_VALIDATION_PASSED
AUTHORITY_C_CANDIDATE_VALIDATION_FAILED
AUTHORITY_C_OPPORTUNITY_CONSUMED
AUTHORITY_C_TERMINATED
```

The latch begins in:

```text
AUTHORITY_C_ACTIVE_CONSTRUCTION_NOT_BEGUN
```

The `begin_contact()` method must atomically transition to:

```text
AUTHORITY_C_CONSTRUCTION_BEGUN
AUTHORITY_C_OPPORTUNITY_CONSUMED
```

The atomic transition must be a locked compare-and-set guarded by the
module-level `threading.Lock`. It must succeed only when the current latch state
is exactly `AUTHORITY_C_ACTIVE_CONSTRUCTION_NOT_BEGUN`.

`begin_contact()` must be called immediately before construction of the first
candidate payload value. No payload field, placeholder payload container, or
candidate byte object may be constructed before `begin_contact()` succeeds.

Contact begins at construction of the first candidate payload value.

`begin_contact()` occurs immediately before construction of the first payload
value. It therefore precedes actual payload contact by one control transition.
This is deliberate. The mechanism may conservatively over-consume the
Authority-C opportunity if the first payload operation fails, but it must never
under-consume an opportunity after payload construction may have begun.

The one-shot Authority-C opportunity is consumed at that same instant,
irrespective of outcome.

The opportunity is not consumed by declaration issuance alone.

Any second construction call in the same process with the same latch key must
return:

```text
classification:
AUTHORITY_C_SECOND_ATTEMPT_GOVERNANCE_VIOLATION

terminal:
true
```

This includes:

```text
re-entrant call:
a call made by the same thread while the first call is in progress

threaded second call:
a simultaneous or later call made by another thread in the same process

post-terminal call:
any later call after success, failure, unknown terminal classification, or
opportunity consumption
```

A re-entrant or threaded second call must not block waiting for the first call
to finish. It must observe the locked latch state and fail closed with
`AUTHORITY_C_SECOND_ATTEMPT_GOVERNANCE_VIOLATION`.

No persistent file may be used for the latch.

The latch is process-local only. It does not enforce cross-process exclusion,
does not use lock files, does not inspect repository state, and does not create
any checkpoint. Cross-process governance is supplied solely by the accepted
single-process no-checkpoint Authority-C sequence. Operators must not launch two
Authority-C processes.

If the process terminates after `begin_contact()` succeeds and before a
canonical result is returned, the terminal classification for that Authority-C
opportunity is:

```text
AUTHORITY_C_UNKNOWN_TERMINAL_FAILURE
```

with:

```text
contact_started:
true

opportunity_consumed:
true
```

If the process terminates and it cannot be established whether
`begin_contact()` succeeded, `contact_started` and `opportunity_consumed` must
remain `UNKNOWN`; they must not be inferred.

Independent governance disposition is required before any further act.

Justification:

A process-local latch is testable, requires no filesystem mutation, prevents a
second construction call in the same process, and can expose exact in-process
`contact_started` and `opportunity_consumed` observables without relying only
on operator discipline.

## 15. Validation-Mode Solution

Selected solution:

```text
Option C - Extract a mode-independent validation core.
```

Reason:

The current `validate_authorization_payload` requires one of the runner mode
names and contains fallback paths that can collect repository state or file
identity after activation. Authority C must not accept PREPARE_PATHS,
PREFLIGHT_ONLY, or EXECUTE_EXACT_SINGLE_RUN as an execution mode, and must not
run Git after activation.

The future implementation must extract:

```python
def validate_authority_c_candidate_payload(
    payload: Mapping[str, object],
    *,
    raw_bytes: bytes,
    accepted_invocation_head: str,
    repository_state: retained.RepositoryState,
    file_identity_provider: FileIdentityProvider,
) -> Mapping[str, object]:
    ...
```

This extracted validation core is the sole source of shared validation truth for
all mode-independent authorization-input validation. Copied validation logic is
not permitted.

The existing runner validator must delegate to this core for shared validation.
`validate_authorization_payload` may remain as a mode-specific adapter, but only
for mode gating and runner-specific execution status checks. It must not retain
or reimplement parallel copies of:

```text
top-level field validation
placeholder rejection
authorization_input_identity validation
runtime identity validation
case lock validation
path model validation
source identity inventory validation
document identity inventory validation
repository_state payload validation
canonical byte validation
```

The implementation change that introduces Authority C must complete this
delegation. A conformance-corpus fallback is allowed only if full delegation
genuinely cannot be completed in one later implementation change; even then,
the fallback may only prove equivalence temporarily and cannot authorize
Authority-C issuance while copied validation logic remains.

This core may reuse pure validation helpers and the injected-provider validation
path from the runner, but it must not call runner execution functions.

Strict loader semantics:

```text
UTF-8 BOM:
reject if raw_bytes begins with EF BB BF

UTF-8 decode:
strict UTF-8 only

duplicate keys:
reject during JSON object parsing

non-finite numbers:
reject NaN, Infinity, and -Infinity during parsing and canonicalization

top-level value:
must be a JSON object / Mapping

canonical byte round-trip:
canonical_json_bytes(parsed_value) must equal raw_bytes exactly

payload equality:
parsed_value must equal the supplied in-memory payload exactly

strict reparse:
canonical_json_bytes(payload) must be reparsed with the same strict loader and
must yield an object exactly equal to payload

candidate repository_state equality:
payload["repository_state"] must equal repository_state.as_payload() exactly
```

The strict loader must use duplicate-key rejection and non-finite-number
rejection explicitly. It must not rely on permissive `json.loads` defaults for
`NaN`, `Infinity`, or duplicate keys.

The core must validate:

```text
wrapper_mode:
PREPARE_PATHS as data value only, not as an execution mode

authorization_status:
PREPARED_NOT_ACTIVE

repository identity:
matches injected RepositoryState and accepted invocation HEAD

repository_state field:
exactly equals injected RepositoryState payload form

source identities:
match injected FileIdentityProvider results

document identities:
match injected FileIdentityProvider results

runtime declaration identities:
match expected_runtime_identities

case set:
A1, A2, A3, A5 only

a6_selected:
false

real_executor_selector:
REAL_EXISTING_ABSOLUTE_PATH_A1_A2_A3_A5_V0_1

authorization_input_identity:
self-excluding identity match

canonical bytes:
exact canonical_json_bytes(payload) equality

generated canonical bytes:
strictly reparsed and identical to payload
```

The core must not call:

```text
run_mode_from_file
main
prepare_paths
preflight_only
execute_exact_single_run
retained.run_retained_single_run
collect_repository_state
_file_identity_from_disk
subprocess.Popen
subprocess.run
subprocess.call
subprocess.check_call
subprocess.check_output
os.system
os.popen
os.spawn*
```

This makes it impossible for Authority C to invoke `prepare_paths()` or any
other runner execution path.

## 16. Canonical-Input-Path Contact Rule

Successful Authority-C result must state:

```text
canonical_input_path_contacted:
false
```

Pre-issuance positive-absence checking of the governed canonical-input path is
permitted only before declaration issuance and outside Authority C.

The invocation form prefers injection of:

```text
canonical_input_absence_observation
```

The retained absence model distinguishes `final_child_absent` from
`ancestor_absent`. Both can report positive absence in general, but only
`final_child_absent` is admissible after Authority A has established the
directory tree.

Exact observation schema:

```text
schema:
torment.brainvision.blocker2.r4.canonical_input_absence_observation.v0.1

accepted_invocation_head:
1f915e29119cd58ea39e8cf355f7364118c71043

authority_c_declaration_sha256:
2c2500e624d77c70d33a6c5d29db6f5f04442fbc6a75a5930e90b89f0df64750

operation_label:
AUTHORITY_C_CANONICAL_INPUT_CANDIDATE_CONSTRUCTION_AND_VALIDATION

path_role:
GOVERNED_CANONICAL_INPUT_PATH

observed_path:
the exact governed canonical-input path string observed before issuance

canonical_input_path:
the exact precomputed governed canonical-input path string

positively_absent:
true

basis:
final_child_absent

native_error_code:
2

native_error_name:
ERROR_FILE_NOT_FOUND

detail:
bounded diagnostic text containing no candidate material

pre_existing_kind:
null

observer_identity:
the precomputed identity of the pre-issuance absence observer

observation_scope:
POSITIVE_ABSENCE_CHECK_ONLY

observation_phase:
PRE_ISSUANCE

pre_issuance_sequence_position:
FINAL_PRE_ISSUANCE_ACT

repository_state_head:
1f915e29119cd58ea39e8cf355f7364118c71043

repository_state_origin_main:
1f915e29119cd58ea39e8cf355f7364118c71043

index_lock_state:
ABSENT

governed_path_contact_after_activation:
PROHIBITED
```

Exact validation rules:

```text
mapping shape:
no missing fields, no unknown fields, and no in-schema whole-observation
identity field

accepted_invocation_head:
must equal the accepted invocation HEAD

authority_c_declaration_sha256:
must equal the injected declaration identity

operation_label:
must equal the Authority-C operation label

observed_path:
must equal the governed canonical-input path exactly

canonical_input_path:
must equal the governed canonical-input path exactly, without touching the
filesystem

positively_absent:
must be true

basis:
must be final_child_absent

native_error_name:
must be ERROR_FILE_NOT_FOUND

native_error_code:
must be 2

native error cross-validation:
native_error_code == 2 and native_error_name == ERROR_FILE_NOT_FOUND must both
hold and must describe the same Windows ERROR_FILE_NOT_FOUND condition

detail:
must contain no candidate payload value and no canonical candidate byte content

pre_existing_kind:
must be null

pre_existing_kind retained-model rule:
The retained absence checker sets pre_existing_kind only when the governed
target already exists, in which case the value is "object".

For an admissible final_child_absent observation, pre_existing_kind is None and
is represented in canonical JSON as null.

Any non-null pre_existing_kind indicates that the target existed or that the
observation does not match the retained absence model.

Any non-null value is a pre-contact rejection requiring independent disposition.

explicitly rejected pre_existing_kind values for basis == final_child_absent:
"object"
"ABSENT_FINAL_CHILD"
any other string
any non-null value

observer_identity:
must be present and exact

observation_scope:
must be POSITIVE_ABSENCE_CHECK_ONLY

observation_phase:
must be PRE_ISSUANCE

pre_issuance_sequence_position:
must be FINAL_PRE_ISSUANCE_ACT

repository_state_head and repository_state_origin_main:
must match injected RepositoryState

index_lock_state:
must be ABSENT

explicitly rejected absence bases:
ancestor_absent
parent_or_ancestor_absent

explicitly rejected native errors:
ERROR_PATH_NOT_FOUND
```

After Authority A, a missing ancestor means the governed directory tree has been
destroyed or changed. It is not an admissible form of canonical-input absence.
It is a pre-contact abort requiring independent disposition.

Freshness is sequence-based, not time-based. The absence observation is valid
only if it was the final pre-issuance act before Authority-C declaration
issuance. The implementation must not introduce a wall-clock age threshold,
timestamp freshness rule, timeout, or grace period. A later repository or path
inspection would be a new act and invalidates the declared sequence.

The result must expose:

```text
canonical_input_absence_observation_identity:
SHA-256 of canonical_json_bytes over the complete validated
canonical_input_absence_observation mapping.
```

The observation mapping itself contains no whole-observation identity field. The
identity is computed externally after the complete observation mapping has
passed strict validation. Because the identity is outside the mapped bytes being
hashed, the definition is non-self-referential.

The result field `canonical_input_absence_observation_identity` must equal that
exact SHA-256.

No whole-observation identity field may appear inside the observation whose
bytes it identifies. Self-referential whole-object identity fields are
prohibited. No conditional self-exclusion rule is permitted.

The later Authority-D handoff must bind only this externally computed,
non-self-referential `canonical_input_absence_observation_identity`.

During Authority C, all of the following are prohibited when targeted at the
governed canonical-input path:

```text
Path.exists
os.stat
open
GetFileAttributesW
directory enumeration targeted at canonical-input path
```

The Authority-C operation may use only the injected pre-issuance absence
observation. It must not refresh or confirm the path state after activation.

## 17. Result Schema

Canonical operator-visible result schema:

```text
schema:
torment.brainvision.blocker2.r4.authority_c.candidate_construction_result.v0.1

version:
v0.1
```

Required fields:

```text
schema
version
classification
classification_kind
detail
terminal
contact_started
opportunity_consumed
accepted_invocation_head
authority_c_declaration_sha256
execution_mode
authority_c_active
authority_d_active
authority_e_active
candidate_constructed_in_memory
candidate_validation_attempted
candidate_validation_passed
candidate_byte_count
candidate_sha256
candidate_identity_scope
candidate_bytes_retained_in_process_memory
candidate_written_to_filesystem
canonical_input_path_contacted
canonical_input_absence_observation_identity
repository_state_injected
file_identity_provider_injected
git_subprocess_attempted
process_launch_attempted
execution_authority_created
execution_authority_consumed
failure_phase
failure_code
```

Result serialization, if needed for stdout or an in-memory test comparison, must
use:

```text
canonical_json_bytes
```

It must not write the result to a file during Authority C.

The result must never include:

```text
candidate payload object
canonical candidate bytes
base64, hex, repr, JSON, or text encoding of canonical candidate bytes
any nested copy of the candidate payload
candidate material in detail
candidate material in failure_code
```

The implementation must explicitly prohibit result output, printing, logging,
or serialization of the candidate payload or canonical candidate bytes. The only
operator-visible candidate identity values are:

```text
candidate_byte_count
candidate_sha256
```

Exception and diagnostic channels are subject to the same secrecy prohibition as
the Authority-C result.

The following channels must contain no candidate payload value and no canonical
candidate byte content:

```text
result.detail
failure_code
validation diagnostics
exception messages
exception arguments
tracebacks
local-variable traceback rendering
__repr__
__str__
stdout
stderr
logs
serialized output
```

Diagnostics may expose only:

```text
field names
field counts
rejection classes
candidate_byte_count
candidate_sha256
```

Candidate-holding objects must define safe `__repr__` and `__str__` behavior
that reveals no payload value and no byte content.

Authority C must not enable:

```text
python -X dev
faulthandler
rich traceback handlers
traceback systems that render local variables
debuggers or diagnostic hooks that inspect candidate-holding frames
```

A generic traceback may be emitted only if it cannot render candidate values,
candidate bytes, or local variables containing them.

Success classification:

```text
AUTHORITY_C_CANONICAL_INPUT_CANDIDATE_VALIDATED_IN_MEMORY
```

Non-success classifications:

```text
AUTHORITY_C_PRE_CONTACT_ABORT
AUTHORITY_C_CONSTRUCTION_TERMINAL_FAILURE
AUTHORITY_C_VALIDATION_TERMINAL_FAILURE
AUTHORITY_C_UNKNOWN_TERMINAL_FAILURE
AUTHORITY_C_SECOND_ATTEMPT_GOVERNANCE_VIOLATION
```

Classification kinds:

```text
SUCCESS_TERMINAL
FAIL_CLOSED_PRE_CONTACT
FAIL_CLOSED_CONSUMED
FAIL_CLOSED_UNKNOWN_CONTACT
GOVERNANCE_VIOLATION
USAGE_FAILURE_PRE_OPERATION
```

`execution_mode` must be:

```text
AUTHORITY_C_IN_MEMORY_CANDIDATE_CONSTRUCTION_AND_VALIDATION
```

It must not be PREPARE_PATHS, PREFLIGHT_ONLY, or EXECUTE_EXACT_SINGLE_RUN.

## 18. Exit-Code Semantics

Exit codes for any future CLI adapter over the callable:

```text
0:
accepted Authority-C in-memory construction and validation success

1:
canonical Authority-C non-success result

2:
argument or invocation-form usage failure before operation begins
```

Exit `2` is permitted only before `begin_contact()`:

```text
contact_started:
false

opportunity_consumed:
false
```

All argument validation and injection validation must happen before latch
acquisition. Missing `repository_state`, missing `file_identity_provider`,
invalid `canonical_input_absence_observation`, malformed authority assertions,
unknown arguments, duplicate arguments, and accepted-HEAD mismatch are therefore
pre-contact failures.

The governing boundary is singular and absolute:

```text
exit 2:
only before begin_contact()
contact_started=false
opportunity_consumed=false

exit 1:
every failure at or after begin_contact()
```

No clause may permit exit `2` at or after `begin_contact()`. Unknown process
termination is governed separately by
`AUTHORITY_C_UNKNOWN_TERMINAL_FAILURE` and must never be converted into exit `2`.

Pre-contact usage failure must always be:

```text
contact_started:
false

opportunity_consumed:
false
```

Every failure at or after `begin_contact()` must return exit `1`. This includes
constructor errors, canonicalization errors, validation errors, write-trap
violations, process-launch trap violations, candidate-byte retention failures,
and unknown exceptions after contact.

Second-attempt governance violations are canonical Authority-C non-success
results and must return exit `1`, not exit `2`.

Automatic retry after exit `2` is not permitted.

## 19. Failure-State Contract

Pre-contact failures:

```text
missing prerequisite
authority assertion mismatch
repository state mismatch
identity mismatch
unsafe injection missing
canonical-input path precondition failure
```

Expected result:

```text
contact_started:
false

opportunity_consumed:
false
```

Consumed failures:

```text
constructor exception after first payload value
canonicalization failure
identity-calculation failure
validation failure
candidate-byte loss
unexpected filesystem-write attempt
candidate payload output attempt
canonical candidate byte output attempt
process-launch attempt
unknown exception after construction may have begun
process termination after contact
```

Expected result:

```text
opportunity_consumed:
true or UNKNOWN according to exact evidence
```

Never infer missing values.

All failures and ambiguities inherit the accepted declaration handling:

```text
STOP.
Do not retry.
Do not clean up.
Do not construct a second candidate.
Do not contact a governed path.
Do not delete, truncate, overwrite, move, replace or repair any accidentally
created artifact.
Do not continue to Authority D.
Require independent governance disposition before any further act.
```

## 20. Success Contract

Successful Authority-C completion requires:

```text
classification:
AUTHORITY_C_CANONICAL_INPUT_CANDIDATE_VALIDATED_IN_MEMORY

terminal:
true

contact_started:
true

opportunity_consumed:
true

candidate_constructed_in_memory:
true

candidate_validation_attempted:
true

candidate_validation_passed:
true

candidate_bytes_retained_in_process_memory:
true

candidate_written_to_filesystem:
false

canonical_input_path_contacted:
false

authority_c_active:
true

authority_d_active:
false

authority_e_active:
false

execution_authority_created:
false

execution_authority_consumed:
false
```

On success:

```text
Authority C:
completed and opportunity consumed

Authority D:
remains inactive

Authority E:
remains inactive

execution authority:
not created
not consumed

canonical input:
not published

corrected commit-free window:
remains open

FORMAL_HOLD:
remains active

BLOCKER-2:
remains open

BLOCKER-4:
remains inactive

STOP
```

Authority D is not activated automatically.

Canonical input is not published by Authority-C success.

## 21. Required Tests

Minimum required test count:

```text
136
```

The implementation PR must include at least:

```text
1. accepted in-memory success
2. no candidate file created
3. canonical-input path not contacted
4. repository_state=None rejected pre-contact
5. file_identity_provider=None rejected pre-contact
6. any process-launch attempt trapped and classified terminally
7. second constructor invocation rejected
8. constructor exception after contact consumes opportunity
9. validation failure consumes opportunity
10. argument failure leaves opportunity unconsumed
11. exact 23-field payload
12. canonical byte rules
13. self-excluding authorization-input identity
14. Authority D/E remain inactive
15. execution authority remains uncreated
16. result-schema canonicalization
17. success exit code 0
18. failure exit code 1
19. usage exit code 2
20. no production or governed external mutation
21. duplicate JSON key rejection in strict validation core
22. UTF-8 BOM rejection in strict validation core
23. NaN rejection in strict validation core
24. Infinity rejection in strict validation core
25. top-level non-object JSON rejection
26. non-canonical whitespace/order byte rejection
27. canonical generated bytes are strictly reparsed
28. generated canonical reparse must equal payload
29. payload repository_state must equal injected RepositoryState.as_payload
30. stale fixed untracked-file list is rejected in favor of injected inventory
31. pattern-admitted R4 documentation inventory accepted when injected exactly
32. dirty_unrelated_surfaces accepts captured R4 documentation drafts and known
    CRLF-view artefact paths exactly as measured
33. dirty_authorized_surfaces is not forced to equal the R4 documentation set
34. AUTHORIZED_SURFACE_PATHS remains frozen and contains no docs/ path
35. unrelated untracked path outside the R4 Markdown pattern rejected pre-contact
36. staged entry rejected pre-contact
37. tracked deletion rejected pre-contact
38. unmerged entry rejected pre-contact
39. index.lock presence rejected pre-contact
40. branch mismatch rejected pre-contact
41. HEAD mismatch rejected pre-contact
42. origin/main mismatch rejected pre-contact
43. known CRLF-view artefact set changed rejected pre-contact
44. immutable identity provider unknown path rejected without fallback
45. immutable identity provider absolute path rejected without fallback
46. immutable identity provider case mismatch rejected without fallback
47. immutable identity provider None/default return rejected
48. FileIdentity shape requires git_blob_oid, checked_out_byte_sha256, and
    checked_out_byte_length only
49. accepted-HEAD Git blob identity mismatch rejected
50. checked-out SHA-256 mismatch rejected
51. checked-out byte length mismatch rejected
52. symlink identity path rejected before Authority-C activation
53. junction identity path rejected before Authority-C activation
54. reparse-point identity path rejected before Authority-C activation
55. repository-containment escape rejected before Authority-C activation
56. identity lookup key is exactly absolute_path.relative_to(repo_root).as_posix()
57. python -B, PYTHONDONTWRITEBYTECODE=1, sys.dont_write_bytecode, and
    sys.flags.dont_write_bytecode success path enforced
58. PYTHONDONTWRITEBYTECODE absent at process launch rejected pre-contact
59. python -B absent / sys.flags.dont_write_bytecode false rejected pre-contact
60. sys.dont_write_bytecode false rejected pre-contact
61. repository __pycache__ or .pyc creation during import detected and rejected
62. repository __pycache__ or .pyc creation during Authority C detected and
    rejected
63. pytest cache creation trapped
64. .pytest_cache creation inside the repository prohibited
65. builtins.open write-capable mode trapped during Authority C
66. Path.write_bytes, Path.write_text, Path.touch, and Path.mkdir trapped
67. os.open write flags, os.mkdir, os.makedirs, os.rename, and os.replace
    trapped
68. tempfile.NamedTemporaryFile, TemporaryFile, mkstemp, and mkdtemp trapped
69. shutil copy/move primitives trapped
70. logging.FileHandler trapped
71. subprocess.Popen attempt trapped
72. subprocess.run attempt trapped
73. subprocess.call attempt trapped
74. subprocess.check_call attempt trapped
75. subprocess.check_output attempt trapped
76. os.system attempt trapped
77. os.popen attempt trapped
78. every available os.spawn* attempt trapped
79. non-Git process launch rejected with the same terminal classification
80. candidate payload is not printed, logged, serialized, or returned
81. canonical candidate bytes are not printed, logged, serialized, or returned
82. result exposes only candidate_byte_count and candidate_sha256 for candidate
    identity
83. result detail contains no candidate value
84. failure_code contains no candidate value
85. validation diagnostics contain no candidate value
86. exception message contains no candidate value
87. exception arguments contain no candidate value
88. candidate-holder repr contains no candidate value
89. candidate-holder str contains no candidate value
90. traceback/local-variable rendering is disabled or sanitized
91. stdout contains no candidate value
92. stderr contains no candidate value
93. logs contain no candidate value
94. serialized output contains no candidate value
95. python -X dev, faulthandler, rich traceback handlers, debuggers, and
    diagnostic hooks that inspect candidate frames are disabled
96. canonical_input_absence_observation complete final_child_absent /
    ERROR_FILE_NOT_FOUND shape accepted
97. canonical_input_absence_observation missing/unknown fields rejected
98. canonical_input_absence_observation positively_absent=false rejected
99. ancestor_absent observation rejected pre-contact
100. parent_or_ancestor_absent observation rejected pre-contact
101. ERROR_PATH_NOT_FOUND observation rejected pre-contact
102. mismatched observed_path rejected pre-contact
103. mismatched canonical_input_path rejected pre-contact
104. native error code mismatch rejected pre-contact
105. canonical_input_absence_observation non-final sequence rejected
106. wall-clock freshness threshold is not used
107. Path.exists/os.stat/open/GetFileAttributesW/path-targeted enumeration
    traps fire for governed canonical-input path
108. begin_contact occurs immediately before first payload value construction
109. deliberate over-consumption on first payload operation failure consumes the
    opportunity
110. re-entrant same-thread second call rejected
111. simultaneous second-thread call rejected without waiting
112. post-terminal second call rejected
113. simulated process termination after contact yields unknown terminal
    classification
114. all argument and injection validation completes before latch acquisition
115. every failure at or after begin_contact maps to CLI exit code 1
116. exit code 2 requires contact_started=false and opportunity_consumed=false
117. unknown process termination is never converted into exit code 2
118. Authority D/E remain inactive
119. execution authority remains uncreated
120. no production or governed external mutation
121. existing runner validator delegates shared checks to the extracted core
122. validation-core conformance corpus covers every defined rejection class
123. each corpus case is passed through the extracted shared validation core and
    the existing runner-facing validator
124. each corpus case asserts identical accept/reject outcome, error
    classification, terminal label, and contact-state classification where
    applicable
125. conformance-corpus fallback, if temporarily present, proves exact equivalence
    and cannot authorize Authority-C issuance
126. absence observation contains no in-schema whole-observation identity field
127. observation with an unexpected whole-observation identity field is rejected
     as an unknown-field shape violation
128. canonical_input_absence_observation_identity equals SHA-256 of
     canonical_json_bytes over the complete validated observation mapping
129. changing any observation field changes the external observation identity
130. external observation identity computation is deterministic
131. no self-excluding or self-referential whole-observation identity computation
     is used
132. final_child_absent with pre_existing_kind null is accepted
133. final_child_absent with pre_existing_kind "object" is rejected
134. final_child_absent with pre_existing_kind "ABSENT_FINAL_CHILD" is rejected
135. final_child_absent with any non-null pre_existing_kind is rejected
136. identity-provider alias rejection covers backslash-separator aliases,
     Unicode-normalization aliases, and confirms no normalization or fallback is
     attempted
```

Test restrictions:

```text
temporary or synthetic roots only
no live governed external paths
no live canonical-input path contact
no live evidence-record path contact
no production TORMENT mutation
all process-launch surfaces patched or trapped after activation
filesystem write primitives patched or trapped during Authority C
pytest cache and repository .pytest_cache creation patched or trapped
```

## 22. Implementation Prerequisites

Required code work before declaration issuance:

```text
1. Add AuthorityCAssertions dataclass or equivalent exact mapping validator.
2. Add AuthorityCInvocationLatch, module-level threading.Lock, and
   process-local latch registry.
3. Add locked compare-and-set begin_contact semantics with re-entrant and
   threaded second-call rejection.
4. Add PrecomputedImmutableFileIdentityProvider with exact repository-relative
   POSIX lookup keys and no fallback behavior.
5. Add pre-issuance identity capture checks for ordinary files, repository
   containment, accepted-HEAD Git blobs, same-capture SHA-256 and byte length,
   symlink rejection, junction rejection, and reparse-point rejection.
6. Add the run_authority_c_candidate_construction callable.
7. Extract validate_authority_c_candidate_payload as the sole shared
   mode-independent validation core.
8. Make the existing runner validator delegate shared validation to the
   extracted core.
9. Ensure validate_authority_c_candidate_payload does not call runner execution
   paths, collect_repository_state, _file_identity_from_disk, or Git.
10. Add strict loader semantics for duplicate keys, UTF-8 BOM, non-finite
    numbers, top-level object, canonical byte round-trip, strict reparse, and
    RepositoryState payload equality.
11. Build candidate payload construction from injected inputs only.
12. Compute authorization_input_identity with the self-excluding helper.
13. Canonicalize in memory only.
14. Require Authority-C process launch with python -B and
    PYTHONDONTWRITEBYTECODE=1 before interpreter startup.
15. Execute import sys and then sys.dont_write_bytecode = True before every
    other import or executable statement, with no executable statement between
    the import and assignment.
16. Verify bytecode launch evidence before argument and injection validation.
17. Trap direct and indirect filesystem writes during Authority C, including
    pytest cache and repository .pytest_cache creation.
18. Trap all process-launch surfaces during Authority C.
19. Trap governed canonical-input path contact during Authority C.
20. Validate canonical_input_absence_observation with sequence-based freshness,
    basis=final_child_absent, and native_error_name=ERROR_FILE_NOT_FOUND.
21. Reject ancestor_absent, parent_or_ancestor_absent, and
    ERROR_PATH_NOT_FOUND absence observations.
22. Return the required Authority-C result schema for success and every
    failure class.
23. Ensure result, detail, failure_code, exceptions, diagnostics, repr, str,
    tracebacks, local-variable rendering, stdout, stderr, logs, and serialized
    output never disclose candidate payload values or canonical candidate bytes.
24. Add optional CLI adapter only if it cannot accept runner mode names and
    cannot read or write an authorization-input file.
25. Enforce exit-code semantics exactly: 0 success, 1 Authority-C non-success,
    2 only pre-contact usage failure.
26. Add the required validation-core conformance corpus covering every defined
    rejection class across both the extracted core and the delegating runner
    validator.
27. Add the required tests listed above.
28. Run tests only against temporary or synthetic roots.
29. Obtain independent review before declaration issuance.
```

No implementation work is performed by this design draft.

## 23. Terminal State Of This Draft

After creation of this design draft:

```text
Authority C:
INACTIVE

Authority D:
INACTIVE

Authority E:
INACTIVE

canonical input:
NOT PREPARED
NOT PUBLISHED

execution authority:
NOT CREATED
NOT CONSUMED

corrected commit-free window:
OPEN

FORMAL_HOLD:
ACTIVE

BLOCKER-2:
OPEN

BLOCKER-4:
INACTIVE
```

This draft is design only and is not authority to implement or execute.
