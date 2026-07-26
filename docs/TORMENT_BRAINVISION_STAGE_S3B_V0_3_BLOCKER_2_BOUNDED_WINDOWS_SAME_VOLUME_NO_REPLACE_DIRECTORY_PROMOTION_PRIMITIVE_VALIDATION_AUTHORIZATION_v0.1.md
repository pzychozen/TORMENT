# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Bounded Windows Same-Volume No-Replace Directory Promotion Primitive Validation Authorization v0.1

## 1. Authorization Identity and Scope

document_class = BLOCKER-2 bounded Windows primitive-validation implementation authorization

document_version = v0.1

authorization_scope =
future implementation of an isolated research-only validation harness for the
recommended BLOCKER-2 Windows primitive:

```text
SetFileInformationByHandle
+
FileRenameInfo
+
FILE_RENAME_INFO
+
ReplaceIfExists = FALSE
```

baseline_commit = 559364000c5786e801883354390d47c0cee1c034

baseline_branch = main

baseline_origin = origin/main

derived_authorization_outcome =
A. AUTHORIZE_BOUNDED_WINDOWS_PROMOTION_PRIMITIVE_VALIDATION_IMPLEMENTATION

This document authorizes a future Codex implementation task to create a narrow,
isolated, research-only validation harness and focused tests. It does not
implement that harness, does not run the primitive, does not create validation
evidence, does not authorize an authoritative Windows execution, and does not
prepare the formal BLOCKER-2 specification.

Authorized future implementation purpose:

```text
empirically characterize whether the recommended primitive can perform bounded
same-volume no-replace non-empty-directory rename validation on the authorized
Windows 10/11 local-fixed-NTFS pytest tmp_path profile
```

Not authorized:

```text
BLOCKER-2 production implementation
existing publication-adapter modification
formal BLOCKER-2 specification
publication completion changes
publication recovery changes
publication replay changes
live publication
production integration
kernel, service, memory, cognition, autonomy, or truth-selection integration
authoritative Windows validation execution
```

## 2. Authoritative Baseline

Required synchronized baseline:

```text
branch      = main
HEAD        = 559364000c5786e801883354390d47c0cee1c034
origin/main = 559364000c5786e801883354390d47c0cee1c034
latest      = 5593640 docs(research): research blocker 2 Windows promotion primitive
working tree = clean before this docs-only authorization
.git/index.lock = absent
```

Baseline verification must be repeated by any future implementation or
execution order before it modifies or runs anything. If the baseline or working
tree is unexpected, the future task must stop rather than adapting the
authorization.

## 3. Current Blocker State

Preserved formal state:

```text
BLOCKER-1:
BLOCKER_1_CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_WINDOWS_LOCAL_FIXED_NTFS_TMP_PATH_SCOPE

BLOCKER-2:
OPEN

recommended research primitive:
SetFileInformationByHandle + FileRenameInfo

current procedural state:
REQUIRES_BOUNDED_WINDOWS_PRIMITIVE_VALIDATION_BEFORE_SPECIFICATION

BLOCKER-3:
CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_STAGE_S3B_V0_3_SCOPE

BLOCKER-4:
OPEN
```

This authorization does not reopen BLOCKER-1 or BLOCKER-3. BLOCKER-4 remains
separate. BLOCKER-2 remains open after this authorization.

## 4. Research Basis

Primary research basis:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_WINDOWS_SAME_VOLUME_NO_REPLACE_DIRECTORY_PROMOTION_PRIMARY_SOURCE_PRIMITIVE_RESEARCH_v0.1.md
```

Research record commit:

```text
559364000c5786e801883354390d47c0cee1c034
```

The research derived:

```text
C. SETFILEINFORMATIONBYHANDLE_FILERENAMEINFO_RECOMMENDED_FOR_BLOCKER_2_SPECIFICATION
```

and the next procedural result:

```text
REQUIRES_BOUNDED_WINDOWS_PRIMITIVE_VALIDATION_BEFORE_SPECIFICATION
```

The authorization preserves the research distinctions:

```text
DOCUMENTED
INFERRED
REQUIRES_EMPIRICAL_VALIDATION
UNRESOLVED
```

The research recommendation is not converted into an established production
implementation contract. This document authorizes only validation of the
candidate.

Additional read basis:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SAME_VOLUME_NO_REPLACE_PROMOTION_AND_FINAL_OWNERSHIP_ASSESSMENT_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_CLOSURE_ASSESSMENT_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_IMPLEMENTATION_FINDINGS_v0.1.md
```

Repository seam inspection confirms that the current promotion adapter is an
abstract/fail-closed seam and that `FINAL_PARENT_DIRECTORY` is a reusable
BLOCKER-1 directory-durability role, not a promotion implementation.

## 5. Exact Authorised Implementation Surface

Future implementation may modify or create only these research-only paths:

```text
research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
```

No separate shared validation schema module is authorized by this v0.1
authorization. If implementation proves a fourth shared module technically
necessary, the future task must stop and request renewed authorization.

The future harness may define internal validation schema, taxonomy, policy
identity, result-record builders, and canonical JSON helpers inside the
authorized validation module only.

The future implementation may include constants for a later result path, but it
must not produce authoritative result artifacts unless a separate one-run
execution authorization later permits that run.

## 6. Forbidden Surfaces

The future implementation must not modify:

```text
research/brainvision/durable_evidence_windows_adapter_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_schema_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
research/brainvision/durable_evidence_publication_replay_v0_3.py
research/brainvision/durable_evidence_publication_recovery_replay_v0_3.py
```

The future implementation must also not modify:

```text
source files outside the exact authorized validation surface
existing tests
fixtures outside pytest-created temporary material
registries
indexes
pointers
prior documents
production files
torment_service/kernel/
production TORMENT memory functionality
live service behavior
prompt or action surfaces
autonomy
identity
truth selection
memory cognition
```

No existing promotion seam may be wired to the validation primitive.

No existing publication grammar may change.

No production adapter may be created.

## 7. Candidate Native API Contract

The candidate contract is frozen for validation only.

Source directory handle candidate:

```text
API:
  CreateFileW

dwDesiredAccess:
  DELETE
  plus only any additional access demonstrated necessary by implementation

dwShareMode:
  FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE

dwSecurityAttributes:
  NULL

dwCreationDisposition:
  OPEN_EXISTING

dwFlagsAndAttributes:
  FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT

hTemplateFile:
  NULL
```

Required interpretation:

```text
DELETE access is part of the documented rename requirement.

FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE is a conservative
project candidate and remains subject to empirical validation. It is not stated
as a Microsoft requirement by this document.

FILE_FLAG_BACKUP_SEMANTICS is required to open a directory handle.

FILE_FLAG_OPEN_REPARSE_POINT supports fail-closed inspection of the directory
object rather than implicit target traversal.
```

Destination parent contract:

```text
open destination parent directory separately
use admitted Windows profile
reject reparse destination parent
pass destination parent handle as FILE_RENAME_INFO.RootDirectory
pass only a simple final directory name relative to that handle
```

Forbidden destination name forms:

```text
absolute destination path in FILE_RENAME_INFO.FileName
path traversal components
"."
".."
directory separators
alternate data stream syntax
empty final name
wildcards
drive-qualified syntax
UNC syntax
device namespace syntax
embedded NUL
```

Rename call under validation:

```text
SetFileInformationByHandle(
    source_directory_handle,
    FileRenameInfo,
    pointer_to_FILE_RENAME_INFO,
    buffer_size
)

FILE_RENAME_INFO.ReplaceIfExists = FALSE
```

Forbidden as the operation under validation:

```text
FileRenameInfoEx
FILE_RENAME_REPLACE_IF_EXISTS
FILE_RENAME_POSIX_SEMANTICS
MoveFileW
MoveFileExW
ReplaceFileW
MoveFileTransactedW
Path.rename
os.rename
shutil.move
copy/delete fallback
```

Tests may use ordinary filesystem APIs only to construct or inspect isolated
fixtures. They must never use them as the operation under validation.

The future implementation must explicitly validate:

```text
ctypes structure layout
union treatment of ReplaceIfExists versus Flags
RootDirectory handle width
DWORD FileNameLength in bytes
UTF-16LE final-name encoding
variable-length trailing FileName buffer
total buffer size
pointer lifetime
alignment
SetFileInformationByHandle argtypes and restype
GetLastError timing
CloseHandle behavior
```

The implementation must deterministically construct the variable-length
rename-information buffer. It must not assume that a fixed Python
`ctypes.Structure` containing `WCHAR[1]` is sufficient without verifying
allocation and offsets.

Unsafe malformed native buffers must not be sent to Windows. Malformed-buffer
cases must be tested at the builder/validation layer before any native call.

## 8. Fixture and Path-Safety Boundary

All ordinary validation effects must remain inside pytest-managed isolated
temporary directories.

The harness must refuse:

```text
repository-root paths
paths containing .git
paths outside the supplied authorized fixture root
existing production directories
existing publication directories
system directories
user-profile directories
arbitrary command-line paths
```

The implementation must not expose a general-purpose rename CLI. The runner may
accept only an internally created or explicitly test-injected fixture root.

The future authoritative run, if separately authorized later, must create fresh
isolated fixture material and must not touch repository material except for the
dedicated result-artifact path authorized by that later run.

## 9. Positive Support Profile

Only the following may qualify for positive validation:

```text
Windows 10 or Windows 11 workstation
local fixed volume
NTFS
absolute source and parent fixture paths
ordinary existing source directory
ordinary existing destination parent
source and destination parent non-reparse
isolated pytest tmp_path fixture
source and destination on the same volume
simple absent destination name
bounded non-empty source directory
```

Everything outside the profile must be rejected before the native operation,
skipped with explicit evidence when the fixture cannot exist, or classified
fail closed after native failure.

No positive claim may be made for:

```text
network volumes
removable volumes
non-NTFS filesystems
ReFS
FAT/exFAT
UNC paths
mapped drives
reparse targets
mount points
junctions
symlinks
production paths
repository paths
user document paths
```

## 10. Required Validation Matrix

V1 - positive non-empty same-volume rename:

```text
create source parent, destination parent, non-empty source directory,
bounded nested file content, and absent destination name
capture source object identity, source-parent identity, destination-parent
identity, volume identity, source tree manifest, destination absence, and
validation-policy identity
perform the selected native operation
capture native return, native error code, source-path absence, final-path
existence, final object identity, source/final identity equality, final tree
manifest, parent identity stability, same-volume evidence, and no replacement
```

V2 - existing destination directory:

```text
native operation must fail
existing destination identity and contents remain unchanged
source identity and contents remain unchanged
no merge
no replacement
no partial population
numeric native error retained
```

V3 - existing destination file:

```text
same fail-closed invariants as V2
```

V4 - concurrent destination creation:

```text
bounded deterministic coordination between one promotion attempt and one
competing destination creation
exactly one actor acquires the destination name
the other fails
no existing object is replaced
no merge occurs
no partial directory appears
source/final ownership remains unambiguous
record exact bounded iteration count
```

V5 - source reparse rejection:

```text
reject before promotion for source directory symlink, junction, mount point, or
other available reparse fixture
record SKIPPED_FIXTURE_UNAVAILABLE when the fixture cannot be created safely
```

V6 - destination-parent reparse rejection:

```text
same policy as V5 for destination parent
```

V7 - source mutation/open-handle behavior:

```text
characterize another file handle open within source tree
characterize another directory handle open
characterize file add/modify after preflight but before native call
record native success/failure, native code, pre/post verification result, and
whether stronger quiescence is required
no mutation-contaminated case may count as positive
```

V8 - identity continuity:

```text
retain source directory handle where possible
compare retained source-handle identity, pre-operation source-path identity,
and post-operation final-path identity
require exact equality for positive validation
record limitations precisely when Windows behavior prevents one comparison
```

V9 - invalid final names:

```text
reject before native call:
empty name, ".", "..", slash, backslash, absolute path, drive-qualified path,
UNC form, device form, embedded NUL, alternate-stream syntax
```

V10 - unsupported profile rejection:

```text
deterministically reject safely synthesizable unsupported cases
do not create dangerous or machine-wide fixtures
```

V11 - cross-volume attempt:

```text
requires separately available second local fixed NTFS volume
if unavailable, record SKIPPED_SECOND_VOLUME_UNAVAILABLE
do not use network drive, removable drive, RAM disk, virtual disk creation,
mount manipulation, partition manipulation, or administrator-only fixture
creation without separate future authorization
if executed, require native failure, source intact, destination absent,
numeric error captured, and no copy/delete fallback
```

V12 - native error characterization:

```text
for every failed native case capture operation phase, raw numeric GetLastError
value, symbolic name when known, source identity, destination-parent identity,
fixture classification, source existence, destination existence, and content
integrity
unknown errors remain numeric and fail closed
do not freeze final BLOCKER-2 taxonomy in the validation implementation
```

## 11. Identity and Content Evidence

The validation evidence must capture:

```text
source object identity
source-parent object identity
destination-parent object identity
source volume identity
destination-parent volume identity
pre-operation source-path identity
retained source-handle identity where possible
post-operation final-path identity
source/final identity equality
source tree manifest and SHA-256 hashes
final tree manifest and SHA-256 hashes
destination absence evidence
destination collision object identity when present
parent identity stability before and after operation
```

Identity fields must include volume serial number and file index high/low where
available. Unavailable identity is not positive evidence and must fail closed or
be reported as skipped/indeterminate according to case type.

Content evidence must be bounded, canonical, and deterministic. It must not
retain unnecessary absolute user paths when fixture-relative paths suffice.

## 12. Reparse and Race Handling

The validation harness must reject source and destination-parent reparse points
before native promotion validation.

Available reparse fixtures may include:

```text
directory symlink
junction
mount point
unknown reparse fixture when safely constructible
```

If the host cannot create a fixture without elevation or unsafe setup, the case
must report:

```text
SKIPPED_FIXTURE_UNAVAILABLE
```

and the rejection rule must remain intact.

Race handling is limited to bounded deterministic validation. It must not become
a stress benchmark. The concurrent destination creation case must record the
iteration count and must accept only unambiguous no-replace outcomes.

## 13. Native Error Characterization

The future implementation must capture native error details without converting
unknowns into success.

For each native call phase:

```text
CreateFileW source
CreateFileW source parent
CreateFileW destination parent
SetFileInformationByHandle
GetFileInformationByHandle
FlushFileBuffers for durability investigation
CloseHandle where observable
```

record:

```text
operation phase
raw numeric GetLastError value
symbolic name when known
status classification
fixture classification
source identity
destination-parent identity
source existence
destination existence
content-integrity result
```

The validation implementation may define research-only native error categories,
but it must not freeze the final BLOCKER-2 production taxonomy.

## 14. Parent-Directory Durability Investigation

The validation must distinguish primitive namespace behavior from
post-transition durability characterization.

The existing BLOCKER-1 adapter may be imported and invoked only as a research
dependency for isolated validation. It must not be modified.

D1 - final-parent sync:

```text
after successful rename and post-operation verification, sync
FINAL_PARENT_DIRECTORY through the closed BLOCKER-1 adapter
record DIRECTORY_DURABILITY_CONFIRMED or fail closed
record active directory-durability policy identity and durability evidence
positive full-chain validation requires confirmation
```

This validates the project's executable chain. It is not a Microsoft-documented
power-loss guarantee and must not be described that way.

D2 - former source-parent sync:

```text
after rename, characterize sync of the former source parent
record whether it succeeds under the admitted profile
do not pre-judge whether it is required in the final BLOCKER-2 specification
```

D3 - both-parent ordering:

```text
evaluate rename, post-verify final object, sync former source parent, sync
final parent
evaluate rename, post-verify final object, sync final parent, sync former
source parent
record executability, stable object identities, error behavior, and evidence
shape
do not claim ordering equivalence unless supported
```

D4 - renamed-directory handle flush:

```text
characterize FlushFileBuffers on the retained renamed-directory handle
record native result
do not treat success as proof that this flush is required or sufficient
do not add it to the final contract in this authorization
```

## 15. Fault-Injection Requirements

Only synthetic in-process fault injection is authorized for the future
implementation.

Not authorized:

```text
power loss
reboot
process termination
filesystem corruption
machine crash
VM crash testing
physical power-loss testing
```

Required fail points:

```text
F1 before native rename
F2 after native success but before final-path verification
F3 after final verification but before any parent sync
F4 after first parent sync but before second parent sync
F5 after parent syncs but before validation evidence serialization
F6 after evidence serialization but before evidence-file durability
```

Each point must verify:

```text
no false positive status
no publication completion
no BLOCKER-2 closure claim
deterministic partial-state evidence
source/final namespace observations retained
authoritative scientific result unchanged
```

The validation harness must not attempt J2 recovery or reconstruct publication
completion.

## 16. Validation Taxonomy

The future implementation may define a research-only taxonomy equivalent to:

```text
PRIMITIVE_VALIDATION_CONFIRMED
PRIMITIVE_VALIDATION_FAILED
PRIMITIVE_VALIDATION_UNSUPPORTED
PRIMITIVE_VALIDATION_SKIPPED
PRIMITIVE_VALIDATION_INDETERMINATE
PRIMITIVE_VALIDATION_FIXTURE_INVALID
PRIMITIVE_VALIDATION_IDENTITY_MISMATCH
PRIMITIVE_VALIDATION_CONTENT_MISMATCH
PRIMITIVE_VALIDATION_DESTINATION_REPLACED
PRIMITIVE_VALIDATION_CROSS_VOLUME_COPY_DETECTED
PRIMITIVE_VALIDATION_DURABILITY_UNCONFIRMED
```

Exact names may be refined during implementation review, but the taxonomy must
remain isolated from current production/publication grammar.

Do not introduce these as validation-run outcome statuses:

```text
PROMOTION_CONFIRMED
PUBLICATION_COMPLETED
SCIENTIFIC_COMPLETION
DURABLE_ACCEPTED
```

Only a fully satisfied positive case may contribute to
`PRIMITIVE_VALIDATION_CONFIRMED`.

## 17. Validation-Policy Identity

The future implementation must define a new research-only validation-policy
declaration.

It must bind at minimum:

```text
validation version
selected API
information class
ReplaceIfExists setting
source handle contract
destination-parent handle contract
name restrictions
support profile
reparse rejection
same-volume admission
identity fields
content-manifest rules
native error capture
positive-case requirements
race iteration count
durability investigation sequence
fault-injection points
fixture boundary
skipped-fixture semantics
```

Digest rule:

```text
validation_policy_sha256 =
SHA256(canonical_json_bytes(validation_policy_declaration))
```

The validation-policy identity must not reuse:

```text
directory-durability policy identity
future promotion policy identity
```

It is a validation-policy identity only and must not automatically become the
future BLOCKER-2 production policy identity.

## 18. Utility and Source Identity

Validation evidence must bind:

```text
validation runner source SHA-256
validation module source SHA-256
test-fixture/version identity
Python module identities where already supported by project conventions
active validation-policy identity
selected Microsoft research-record identity
BLOCKER-2 assessment identity
primitive-research document identity
repository HEAD
platform profile
```

If no separate schema module exists, `validation schema source SHA-256` is the
same authorized validation module source SHA-256 with the schema section
identified by stable internal name.

Mutable timestamps must not be logical identity. Wall-clock timestamps may
appear only as non-authoritative metadata.

## 19. Result Schema and Output Path

Future result artifacts, when a separate one-run authorization later permits
the authoritative execution, must be retained under a unique repository result
path:

```text
research/brainvision/results/windows_same_volume_no_replace_promotion_validation_v0_1/<unique_run_identity>/
```

The future run must create a new path and must fail if the path already exists.
No uncontrolled output locations are permitted.

Expected bounded result set:

```text
validation_result.json
validation_manifest.json
validation_summary.txt
```

The future implementation may include dry-run or test-local temporary result
builders under pytest `tmp_path`, but it must not write an authoritative result
under `research/brainvision/results/` unless a separate one-run execution order
authorizes that specific run.

Canonical logical result schema must record at minimum:

```text
schema version
runner identity
validation-policy identity
research-source identity
repository baseline
platform profile
Windows version
filesystem name
drive type
fixture root classification
case identifier
case status
native return
native error code
pre-operation identities
post-operation identities
same-volume evidence
source/final identity comparison
content manifests and hashes
source/destination existence state
parent-sync results
active directory-durability policy identity
fault point when applicable
skip reason when applicable
overall derived result
```

Paths must be represented safely. Prefer fixture-relative representations for
logical evidence and keep absolute paths only as non-authoritative diagnostic
metadata where needed.

## 20. Testing Requirements

Future implementation must include:

```text
pure unit tests for name validation
pure unit tests for buffer construction
pure unit tests for policy identity
synthetic adapter tests
Windows-only focused integration tests
positive-profile test
destination-collision tests
identity-continuity tests
content-integrity tests
reparse rejection tests where fixtures are available
fault-injection tests
result-canonicalization tests
no-output-on-invalid-fixture tests
```

Non-Windows environments must:

```text
skip native positive integration tests explicitly
continue running pure unit and synthetic tests
never return a false positive
```

The future implementation order may authorize only:

```text
new focused validation tests
the existing Stage S3B v0.3 durable-evidence family when regression review
demonstrates relevance
```

Broad all-research execution is not required. Any broader exploratory run must
be labelled non-authoritative.

## 21. Stop Conditions

The future implementation or run must stop fail closed on:

```text
unexpected repository baseline
dirty authoritative Windows working tree
.git/index.lock present
policy identity mismatch
source identity unavailable
destination-parent identity unavailable
unsupported filesystem profile
reparse target
source/destination volume mismatch
destination already existing in a positive case
native API setup ambiguity
ctypes layout ambiguity
unexpected native success after a prohibited fixture
source/final identity mismatch
content mismatch
destination replacement
partial population
cross-volume copy behavior
parent-directory durability unconfirmed
uncontrolled output path
existing result path
unexpected mutation outside fixture root
need to alter existing publication adapter
need to alter existing publication, recovery, or replay grammar
need for production, kernel, service, memory, cognition, autonomy, or live
surface
```

No stop condition may be weakened merely to obtain a positive result.

## 22. Implementation Acceptance Criteria

The future implementation candidate may be accepted only if:

```text
1. exact authorized file surface is respected
2. selected API is SetFileInformationByHandle + FileRenameInfo
3. ReplaceIfExists is FALSE
4. source is opened by handle
5. destination parent is bound through RootDirectory
6. only a simple final name is permitted
7. support profile is enforced
8. source and destination-parent reparses fail closed
9. same-volume proof is handle/object based
10. native no-replace behavior is exercised
11. destination collision preserves both objects
12. source/final identity continuity is measured
13. content equality is measured
14. parent identities are measured
15. native errors remain numeric
16. final-parent durability is exercised through the closed BLOCKER-1 adapter
17. former source-parent durability is characterized
18. renamed-directory flush behavior is characterized without overclaim
19. fault points cannot produce false positive status
20. result evidence is canonical and identity-bound
21. validation policy identity is separate from production policies
22. no publication or recovery grammar changes
23. no existing promotion adapter changes
24. no production, kernel, service, memory, cognitive, autonomy, or live surface changes
25. no authoritative run is consumed during implementation unless separately authorized
```

## 23. Authoritative-Run Separation

This document does not authorize the authoritative Windows validation execution.

Authorized now:

```text
future implementation of isolated research validation harness
future focused tests for that harness
future implementation review inputs
```

Not authorized now:

```text
authoritative Windows validation execution
durable authoritative validation-result retention
copying authoritative run results into the repository
BLOCKER-2 specification
BLOCKER-2 production implementation
```

Preferred workflow:

```text
authorization document
independent review
operator commit and push
exact Codex implementation order
implementation and focused testing only
independent implementation review
operator commit and push
separate exact one-run Windows execution authorization
authoritative Windows execution
findings document
```

Do not combine implementation and authoritative execution unless a later order
explicitly documents the reason and grants that authority.

## 24. Boundary Preservation

Preserved:

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

Required boundary conclusions:

```text
BLOCKER-1 remains closed and is not reopened.
BLOCKER-2 remains open.
BLOCKER-3 remains closed within its authorised scope.
BLOCKER-4 remains open and separate.
The selected primitive remains a research recommendation pending validation.
No promotion implementation has been integrated into publication orchestration.
No publication completion or recovery semantics have changed.
No authoritative validation run is authorized by this document.
No live or production lane is opened.
```

Preserved scientific boundary:

```text
publication is a projection of the authoritative scientific result

authoritative durable result =
verified IMMUTABLE_SCIENTIFIC_BUNDLE
+
linked valid SCIENTIFIC_COMPLETION
```

The validation evidence remains research/platform evidence and cannot become
scientific completion evidence.

## 25. Derived Authorization Outcome

Derived outcome:

```text
A. AUTHORIZE_BOUNDED_WINDOWS_PROMOTION_PRIMITIVE_VALIDATION_IMPLEMENTATION
```

Reason:

The committed primary-source research record supplies enough detail to authorize
a narrow, safe, fail-closed implementation of an isolated research validation
harness. The selected candidate is precise; unresolved properties are exactly
the properties that the validation harness is meant to characterize.

This outcome authorizes implementation and focused tests only.

This outcome does not authorize:

```text
authoritative Windows validation execution
formal BLOCKER-2 specification
BLOCKER-2 production implementation
publication adapter modification
publication completion
recovery or replay changes
live or production operation
```

Rejected alternative:

```text
B. REQUIRE_VALIDATION_DESIGN_REVISION_BEFORE_AUTHORIZATION
```

Rejected because the research record and this authorization define a bounded
file surface, candidate API contract, fixture boundary, validation cases,
durability investigation, result schema, stop conditions, and implementation
review criteria precise enough for a future implementation order.

## 26. Next Procedural Step

Next procedural step:

```text
independent review of this authorization
operator commit and push if accepted
then prepare an exact Codex implementation order
implementation and focused testing only
independent implementation review
operator commit and push if accepted
then prepare a separate exact one-run Windows execution authorization
```

Do not prepare the implementation order in this task.

Do not authorize the authoritative run implicitly.

Do not prepare the one-run execution authorization in this task.

Do not implement or execute the primitive in this task.
