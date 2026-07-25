# TORMENT Brainvision Stage S3B v0.3 BLOCKER-1 Windows Directory-Durability Implementation Authorization v0.1

## 1. DOCUMENT STATUS

```text
document_class                    = implementation authorization (docs-only)
selected_blocker                  = BLOCKER-1
source_modified_by_this_document  = false
tests_modified_by_this_document   = false
implementation_performed          = false
test_creation_performed           = false
test_execution_performed          = false
live_test_authorized              = false
publication_authorized            = false
publication_recovery_authorized   = false
filesystem_probe_performed        = false
crash_test_authorized             = false
power_loss_test_authorized        = false
real_data_contact_authorized      = false
git_mutations_by_this_document    = none
```

This document authorizes a future implementation surface only. It does not
implement code, create tests, run Win32 directory handles, perform live
publication or recovery, or close BLOCKER-1.

## 2. AUTHORIZATION PURPOSE

Purpose:

```text
Freeze the smallest complete source and test surface necessary to implement
validated identity-bound Windows directory-entry durability for explicitly
defined directory targets using a fail-closed Win32 adapter with deterministic
policy identity, failure mapping, completion gating, replay binding, and
bounded synthetic plus isolated Windows validation.
```

The future implementer must not invent:

```text
file inventory
adapter location
policy declaration location
status taxonomy location
failure vocabulary location
target sequencing
replay binding
recovery binding
test placement
Windows validation boundaries
```

## 3. AUTHORITATIVE BASELINE

Required implementation-authorization baseline:

```text
branch = main

HEAD =
9ca92f9a18e33113e8b1660cbcda495d07ea52fc

origin/main =
9ca92f9a18e33113e8b1660cbcda495d07ea52fc

latest subject =
docs(research): specify blocker 1 Windows directory durability

working tree =
clean before this document was created

index lock =
absent before this document was created
```

This authorization is valid only for that baseline. If implementation begins
from any other baseline, the implementer must stop for renewed authority.

## 4. GOVERNING LINEAGE

Lineage reviewed and preserved:

```text
0d52dc0 docs(research): select resource bounds as first platform blocker
35d7b6e docs(research): specify blocker 3 resource admissibility
01a720c docs(research): authorize blocker 3 resource admissibility implementation
164680b docs(research): correct blocker 3 implementation surface
c03d5f9 research(brainvision): implement blocker 3 resource admissibility
843f861 docs(research): record blocker 3 resource admissibility findings
4e8bc7c docs(research): assess blocker 3 resource admissibility closure
6897fc8 docs(research): assess blocker 1 Windows directory durability
9ca92f9 docs(research): specify blocker 1 Windows directory durability
```

Primary governing documents:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_ASSESSMENT_v0.1.md

docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_SPECIFICATION_v0.1.md
```

Current project state preserved:

```text
BLOCKER-3 =
CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_STAGE_S3B_V0_3_SCOPE

BLOCKER-1 = open
BLOCKER-2 = open
BLOCKER-4 = open

FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

## 5. AUTHORIZED GUARANTEE

Authorized future guarantee:

```text
validated identity-bound Windows directory-entry durability
for explicitly defined directory targets
under the declared Windows 10/11 local fixed NTFS pytest-temporary profile
```

`DIRECTORY_DURABILITY_CONFIRMED` may mean only:

```text
the selected adapter opened the admitted target directory object,
verified the target identity under the frozen policy,
completed FlushFileBuffers on the intended directory handle,
closed or classified close failure fail-closed,
and returned the active directory-durability policy identity
```

It must not mean:

```text
physical power-loss proof
host crash proof
whole-volume persistence proof
storage-controller persistence proof
network filesystem guarantee
same-volume no-replace promotion proof
production readiness
```

Only explicitly bound policy identity may contribute positively to durable
evidence or replay. No implicit policy identity is permitted.

## 6. POLICY DECLARATION OWNERSHIP

Selected ownership:

```text
POLICY_DECLARATION_IN_SCHEMA_MODULE
```

Justification:

```text
research/brainvision/durable_evidence_schema_v0_3.py already owns canonical
serialization, SHA-256 identity helpers, resource-admissibility policy
declarations, resource policy identity validation, and durable evidence schema
constants. Directory-durability policy material is another deterministic schema
identity and must share the same canonical_json_bytes digest rule.
```

Rejected alternatives:

```text
POLICY_DECLARATION_IN_WINDOWS_ADAPTER_MODULE =
rejected because the adapter must not own the evidence policy identity consumed
by publication, recovery, replay, and schema validation.

SEPARATE_POLICY_MODULE_REQUIRED =
rejected because it would add an unnecessary source file and broaden the
surface beyond the existing schema ownership pattern.
```

The schema module must define the policy declaration, digest, and identity:

```text
DIRECTORY_DURABILITY_POLICY_SCHEMA =
durable-evidence-windows-directory-durability-policy-v0.1

directory_durability_policy_declaration() -> dict
directory_durability_policy_sha256() -> str
directory_durability_policy_identity() -> dict[str, str]
validate_directory_durability_policy_identity(value) -> None
```

The declaration must include at least:

```text
policy schema identity
adapter identity
operation identity
supported Windows profile
supported filesystem profile
target-role declaration
status taxonomy
failure-mapping version
path-normalization policy
reparse-point policy
validation-profile identity
```

Required digest rule:

```text
directory_durability_policy_sha256 =
SHA-256(canonical_json_bytes(directory_durability_policy_declaration()))
```

The policy SHA-256 must be computed from canonical policy material and must not
be hardcoded as an unexplained predicted value.

## 7. WIN32 ADAPTER CONTRACT

Adapter location:

```text
research/brainvision/durable_evidence_windows_adapter_v0_3.py
```

The future adapter remains quarantined behind the existing durability adapter
boundary. It may use Python standard-library `ctypes` only. No external
dependency is authorized.

Exact authorized Win32 function inventory:

```text
CreateFileW
FlushFileBuffers
GetLastError
CloseHandle
GetFileAttributesW
GetDriveTypeW
GetVolumeInformationW
GetFileInformationByHandle
```

Required core `CreateFileW` contract for every directory handle opened by the
adapter:

```text
dwDesiredAccess =
GENERIC_WRITE

dwShareMode =
FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE

dwSecurityAttributes =
NULL

dwCreationDisposition =
OPEN_EXISTING

dwFlagsAndAttributes =
FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT

hTemplateFile =
NULL
```

`FILE_FLAG_OPEN_REPARSE_POINT` is mandatory in v0.1 because the frozen reparse
policy rejects symlinks, junctions, mount points, and unknown reparse
directories rather than following them.

Authorized constants are limited to the constants required for the function
signatures, handle checks, file-attribute checks, drive/filesystem support
checks, identity structure, and Windows error mapping frozen in this document.

Not authorized:

```text
pywin32
external dependencies
MoveFileExW
ReplaceFileW
MOVEFILE_WRITE_THROUGH
volume-handle flushing
GetFinalPathNameByHandleW
GetVolumeInformationByHandleW
DeviceIoControl
production adapters
service integration
kernel integration
```

`GetDriveTypeW` and `GetVolumeInformationW` are authorized only for support
profile detection of the path root. `GetFileAttributesW` and
`GetFileInformationByHandle` are authorized only for target admission, reparse
rejection, and identity binding. No additional Win32 API may be added without a
surface-correction document.

## 8. DIRECTORY IDENTITY AND REPARSE POLICY

The future implementation must freeze all path handling before any positive
claim:

```text
input path must normalize to an absolute Windows path
UNC paths are unsupported in v0.1
mapped/network roots are unsupported in v0.1
Windows extended-length path form is used for Win32 calls
volatile absolute roots are evidence material only, never policy digest material
```

Target admission sequence:

```text
1. Reject non-Windows platforms fail-closed.
2. Reject non-absolute targets as DIRECTORY_DURABILITY_TARGET_INVALID with
   TARGET_NOT_ABSOLUTE.
3. Reject unsupported Windows versions or product profiles before confirmation.
4. Use GetDriveTypeW on the drive root and require DRIVE_FIXED.
5. Use GetVolumeInformationW on the drive root and require NTFS.
6. Use GetFileAttributesW on the normalized target.
7. Reject missing targets, non-directories, and any FILE_ATTRIBUTE_REPARSE_POINT.
```

Reparse policy:

```text
directory symlink =
rejected

junction =
rejected

mount point =
rejected

unknown reparse point =
rejected
```

All reparse rejection maps fail-closed as:

```text
status       = DIRECTORY_DURABILITY_TARGET_INVALID
failure_code = TARGET_REPARSE_POINT
```

Frozen identity strategy:

```text
pre-open identity =
open a preflight identity handle with the same CreateFileW directory contract,
query GetFileInformationByHandle, record volume serial number plus file index,
then close the preflight handle.

opened-handle identity =
open the flush handle with the same CreateFileW directory contract, query
GetFileInformationByHandle on that handle, and require equality with the
pre-open identity before FlushFileBuffers.

post-open identity =
after FlushFileBuffers and handle close classification, reopen the same
normalized target with the same CreateFileW directory contract, query
GetFileInformationByHandle, and require equality with the opened-handle
identity before returning confirmed.
```

If any identity handle cannot be opened, queried, or closed deterministically:

```text
status       = DIRECTORY_DURABILITY_INDETERMINATE
failure_code = TARGET_IDENTITY_UNAVAILABLE
```

If the pre-open, opened-handle, or post-open identities differ:

```text
status       = DIRECTORY_DURABILITY_IDENTITY_CHANGED
failure_code = TARGET_IDENTITY_CHANGED
```

This identity strategy intentionally does not authorize
`GetFinalPathNameByHandleW` or `DeviceIoControl`.

## 9. STATUS AND FAILURE TAXONOMY

Top-level status taxonomy:

```text
DIRECTORY_DURABILITY_CONFIRMED
DIRECTORY_DURABILITY_UNSUPPORTED
DIRECTORY_DURABILITY_DENIED
DIRECTORY_DURABILITY_INDETERMINATE
DIRECTORY_DURABILITY_TARGET_INVALID
DIRECTORY_DURABILITY_IDENTITY_CHANGED
DIRECTORY_DURABILITY_OPERATION_FAILED
```

Frozen secondary failure-code vocabulary:

```text
ADAPTER_ABSENT
NON_WINDOWS_PLATFORM
WINDOWS_VERSION_UNSUPPORTED
DRIVE_TYPE_UNSUPPORTED
FILESYSTEM_UNSUPPORTED
TARGET_NOT_ABSOLUTE
TARGET_INVALID
TARGET_MISSING
TARGET_NOT_DIRECTORY
TARGET_REPARSE_POINT
TARGET_IDENTITY_UNAVAILABLE
TARGET_IDENTITY_CHANGED
DIRECTORY_OPEN_UNSUPPORTED
DIRECTORY_OPEN_DENIED
DIRECTORY_OPEN_FAILED
DIRECTORY_FLUSH_UNSUPPORTED
DIRECTORY_FLUSH_DENIED
DIRECTORY_FLUSH_FAILED
DIRECTORY_CLOSE_INDETERMINATE
UNKNOWN_NATIVE_ERROR
UNEXPECTED_EXCEPTION
POLICY_IDENTITY_MISMATCH
```

`TARGET_INVALID` is intentionally included for synthetic-adapter and focused
test coverage. Production adapter code must prefer the more specific target
code when the cause is known.

Status mapping:

```text
DIRECTORY_DURABILITY_CONFIRMED:
  failure_code = null

DIRECTORY_DURABILITY_UNSUPPORTED:
  ADAPTER_ABSENT, NON_WINDOWS_PLATFORM, WINDOWS_VERSION_UNSUPPORTED,
  DRIVE_TYPE_UNSUPPORTED, FILESYSTEM_UNSUPPORTED, DIRECTORY_OPEN_UNSUPPORTED,
  DIRECTORY_FLUSH_UNSUPPORTED

DIRECTORY_DURABILITY_DENIED:
  DIRECTORY_OPEN_DENIED, DIRECTORY_FLUSH_DENIED

DIRECTORY_DURABILITY_TARGET_INVALID:
  TARGET_NOT_ABSOLUTE, TARGET_INVALID, TARGET_MISSING, TARGET_NOT_DIRECTORY,
  TARGET_REPARSE_POINT

DIRECTORY_DURABILITY_IDENTITY_CHANGED:
  TARGET_IDENTITY_CHANGED

DIRECTORY_DURABILITY_OPERATION_FAILED:
  DIRECTORY_OPEN_FAILED, DIRECTORY_FLUSH_FAILED

DIRECTORY_DURABILITY_INDETERMINATE:
  TARGET_IDENTITY_UNAVAILABLE, DIRECTORY_CLOSE_INDETERMINATE,
  UNKNOWN_NATIVE_ERROR, UNEXPECTED_EXCEPTION, POLICY_IDENTITY_MISMATCH
```

Unknown native errors must preserve their numeric code and must map fail-closed.
No unexpected exception may be treated as confirmed.

## 10. WINDOWS ERROR MAPPING

Known native errors must map deterministically:

| Windows error | Numeric code | Status | Failure code |
|---|---:|---|---|
| `ERROR_ACCESS_DENIED` | 5 | `DIRECTORY_DURABILITY_DENIED` | `DIRECTORY_OPEN_DENIED` or `DIRECTORY_FLUSH_DENIED` by phase |
| `ERROR_INVALID_FUNCTION` | 1 | `DIRECTORY_DURABILITY_UNSUPPORTED` | `DIRECTORY_OPEN_UNSUPPORTED` or `DIRECTORY_FLUSH_UNSUPPORTED` by phase |
| `ERROR_NOT_SUPPORTED` | 50 | `DIRECTORY_DURABILITY_UNSUPPORTED` | `DIRECTORY_OPEN_UNSUPPORTED` or `DIRECTORY_FLUSH_UNSUPPORTED` by phase |
| `ERROR_INVALID_PARAMETER` | 87 | `DIRECTORY_DURABILITY_OPERATION_FAILED` | `DIRECTORY_OPEN_FAILED` or `DIRECTORY_FLUSH_FAILED` by phase |
| `ERROR_FILE_NOT_FOUND` | 2 | `DIRECTORY_DURABILITY_TARGET_INVALID` | `TARGET_MISSING` |
| `ERROR_PATH_NOT_FOUND` | 3 | `DIRECTORY_DURABILITY_TARGET_INVALID` | `TARGET_MISSING` |
| `ERROR_SHARING_VIOLATION` | 32 | `DIRECTORY_DURABILITY_DENIED` | `DIRECTORY_OPEN_DENIED` or `DIRECTORY_FLUSH_DENIED` by phase |
| `ERROR_LOCK_VIOLATION` | 33 | `DIRECTORY_DURABILITY_DENIED` | `DIRECTORY_OPEN_DENIED` or `DIRECTORY_FLUSH_DENIED` by phase |
| `ERROR_PRIVILEGE_NOT_HELD` | 1314 | `DIRECTORY_DURABILITY_DENIED` | `DIRECTORY_OPEN_DENIED` or `DIRECTORY_FLUSH_DENIED` by phase |
| `ERROR_NOT_READY` | 21 | `DIRECTORY_DURABILITY_OPERATION_FAILED` | `DIRECTORY_OPEN_FAILED` or `DIRECTORY_FLUSH_FAILED` by phase |
| `ERROR_DEVICE_NOT_CONNECTED` | 1167 | `DIRECTORY_DURABILITY_OPERATION_FAILED` | `DIRECTORY_OPEN_FAILED` or `DIRECTORY_FLUSH_FAILED` by phase |
| `ERROR_GEN_FAILURE` | 31 | `DIRECTORY_DURABILITY_OPERATION_FAILED` | `DIRECTORY_OPEN_FAILED` or `DIRECTORY_FLUSH_FAILED` by phase |
| unknown native error | preserved integer | `DIRECTORY_DURABILITY_INDETERMINATE` | `UNKNOWN_NATIVE_ERROR` |

`ERROR_INVALID_PARAMETER` is explicitly frozen as:

```text
ERROR_INVALID_PARAMETER =
OPERATION_FAILED
```

It must not be automatically mapped to `UNSUPPORTED`.

For `ERROR_INVALID_FUNCTION`, the implementation remains fail-closed. The
isolated Windows confirmation must distinguish, where possible, unsupported
filesystem behavior from a wrong handle contract or adapter defect. If the
supported Windows 10/11 local fixed NTFS pytest-temporary profile returns
`ERROR_INVALID_FUNCTION`, implementation must stop rather than downgrade the
claim silently.

## 11. SUPPORTED ENVIRONMENT

Initial positive profile:

```text
Windows 10 or Windows 11
local fixed volume
NTFS
ordinary non-reparse directory
pytest temporary-directory material
```

Everything else must fail closed, remain unsupported, or remain indeterminate:

```text
Windows Server
ReFS
FAT
FAT32
exFAT
UNC paths
network shares
mapped drives
removable media
cloud-synchronized folders
virtual filesystems
directory symlinks
junctions
mount points
other reparse points
non-Windows platforms
```

This authorization does not permit broad Windows claims. Positive confirmation
is limited to the isolated pytest temporary-directory profile above.

## 12. TARGET AND SEQUENCING CONTRACT

Target roles:

```text
ARTIFACT_PARENT_DIRECTORY
STAGING_PARENT_DIRECTORY
STAGING_DIRECTORY
FINAL_PARENT_DIRECTORY
```

Recovery-chain and receipt records:

```text
write record
flush
file fsync
close
read-back verify
sync ARTIFACT_PARENT_DIRECTORY
require DIRECTORY_DURABILITY_CONFIRMED
admit durability evidence
```

Publication staging-directory creation:

```text
create staging directory
sync STAGING_PARENT_DIRECTORY
require DIRECTORY_DURABILITY_CONFIRMED
```

Complete staged artifact set:

```text
write and verify every artifact
perform one set-level STAGING_DIRECTORY sync
require DIRECTORY_DURABILITY_CONFIRMED
admit staging durability
```

No per-artifact staging-directory sync is authorized in v0.1. The staged set is
not admitted until all artifact files are written, file-durable, read-back
verified, and followed by the single set-level `STAGING_DIRECTORY` sync.

Post-promotion final-parent sync:

```text
Implementation must not implement promotion.
Implementation may expose only a reusable FINAL_PARENT_DIRECTORY sync operation
for future BLOCKER-2 use.
```

BLOCKER-2 remains responsible for sequencing any final-parent call after
promotion and for promotion completion semantics.

## 13. COMPLETION AND EVIDENCE BINDING

The future implementation must bind directory-durability policy identity into:

```text
publication utility identities
immutable-write durability evidence
publication durability evidence
publication replay
publication recovery replay
recovery-chain record durability
completion gating
```

Only:

```text
DIRECTORY_DURABILITY_CONFIRMED
```

may contribute positively.

All other statuses must:

```text
withhold PUBLICATION_COMPLETED
withhold J2 verified/completed evidence
preserve original J1 evidence
preserve final artifacts
preserve the authoritative scientific result
produce deterministic failure evidence
```

Primary writer completion family:

```text
DURABLE_ACCEPTED =
allowed only when directory status is DIRECTORY_DURABILITY_CONFIRMED and
directory_durability_policy_identity matches the active schema policy identity

BYTE_VALID_DURABILITY_UNCONFIRMED =
used for every non-confirmed directory status or policy mismatch after bytes
are written, file-durable, closed, and read-back verified
```

The implementation must add deterministic directory-durability metadata to
write results and verified durability evidence without changing the meaning of
the existing primary writer status strings.

J1 publication failure families:

```text
PUBLICATION_CHAIN_GENESIS_WRITE_FAILED
PUBLICATION_ATTEMPTED_WRITE_FAILED
PUBLICATION_STAGING_DURABILITY_UNCONFIRMED
PUBLICATION_ARTIFACTS_VERIFIED_PUBLICATION_COMPLETED_RECORD_FAILED
```

J2 recovery failure families:

```text
PUBLICATION_RECOVERY_CHAIN_GENESIS_WRITE_FAILED
PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED
```

Replay failure families:

```text
PUBLICATION_CHAIN_DURABILITY_UNCONFIRMED
PUBLICATION_RECOVERY_CHAIN_DURABILITY_UNCONFIRMED
```

No new J1 or J2 grammar is authorized. Policy mismatch must be carried as
deterministic failure evidence and must resolve through the existing
unconfirmed/failure families above.

## 14. BLOCKER-2 HANDOFF

Selected handoff:

```text
SPLIT_CONTRACT_WITH_EXPLICIT_HANDOFF
```

Boundary:

```text
BLOCKER-1 owns the directory-sync primitive, identity-bound policy, pre-promotion
staging-parent and staging-directory durability, recovery-chain record parent
durability, and a reusable FINAL_PARENT_DIRECTORY sync operation.

BLOCKER-2 owns same-volume no-replace promotion semantics, final destination
absence, same-volume verification, no copy, no merge, no overwrite, no
replacement, promotion ownership, and promotion ambiguity.
```

After BLOCKER-2 establishes that a promotion operation created the final
directory entry it claims, BLOCKER-2 may call the BLOCKER-1 adapter on
`FINAL_PARENT_DIRECTORY`. That call proves only the post-promotion
parent-directory sync result under BLOCKER-1 policy.

This document does not implement or close BLOCKER-2.

## 15. AUTHORIZED SOURCE SURFACE

```text
SOURCE_FILE_COUNT = 8
```

Authorized source files:

| Path | Classification | Required work |
|---|---|---|
| `research/brainvision/durable_evidence_schema_v0_3.py` | `REQUIRED_SOURCE_CHANGE` | Own directory-durability policy declaration, canonical digest, policy identity validation, target-role constants, and failure-code constants. |
| `research/brainvision/durable_evidence_windows_adapter_v0_3.py` | `REQUIRED_SOURCE_CHANGE` | Implement frozen fail-closed Win32 adapter, context/result dataclasses, statuses, native error mapping, target admission, support-profile checks, identity strategy, and default adapter behavior. |
| `research/brainvision/durable_evidence_primary_writer_v0_3.py` | `REQUIRED_SOURCE_CHANGE` | Pass directory target context, require confirmed policy-bound directory sync after read-back verification, and carry directory-durability metadata in immutable write results. |
| `research/brainvision/durable_evidence_durability_v0_3.py` | `REQUIRED_SOURCE_CHANGE` | Validate confirmed policy-bound write results and carry directory policy metadata in `VerifiedDurabilityEvidence`. |
| `research/brainvision/durable_evidence_publication_v0_3.py` | `REQUIRED_SOURCE_CHANGE` | Add policy identity to publication utility identity, enforce `STAGING_PARENT_DIRECTORY` and set-level `STAGING_DIRECTORY` syncs, and preserve J1 failure families. |
| `research/brainvision/durable_evidence_publication_recovery_v0_3.py` | `REQUIRED_SOURCE_CHANGE` | Bind J2 recovery-chain record durability to the active policy without importing publication or promotion surfaces, and preserve J2 failure families. |
| `research/brainvision/durable_evidence_publication_replay_v0_3.py` | `REQUIRED_SOURCE_CHANGE` | Require policy-bound durability evidence during J1 replay and map mismatch/unconfirmed evidence to `PUBLICATION_CHAIN_DURABILITY_UNCONFIRMED`. |
| `research/brainvision/durable_evidence_publication_recovery_replay_v0_3.py` | `REQUIRED_SOURCE_CHANGE` | Require policy-bound durability evidence during J2 replay and map mismatch/unconfirmed evidence to `PUBLICATION_RECOVERY_CHAIN_DURABILITY_UNCONFIRMED`. |

Source candidates evaluated but not authorized:

| Path | Classification | Reason |
|---|---|---|
| `research/brainvision/durable_evidence_replay_v0_3.py` | `READ_ONLY_REFERENCE` | Publication-specific replay files own J1/J2 durability classifications; lower chain replay remains generic. |
| `research/brainvision/durable_evidence_authority_v0_3.py` | `NOT_REQUIRED` | Authority consumes centralized `VerifiedDurabilityEvidence`; no policy-specific authority source change is required. |
| `research/brainvision/durable_evidence_scientific_result_v0_3.py` | `NOT_REQUIRED` | Scientific recognition consumes centralized durability evidence and must preserve existing authoritative-result semantics. |

No additional source file may change without a separate surface-correction
document.

## 16. AUTHORIZED TEST SURFACE

```text
EXISTING_TEST_FILE_COUNT = 7
NEW_TEST_FILE_COUNT = 2
TOTAL_TEST_FILE_COUNT = 9
```

Existing tests authorized for compatibility changes:

| Path | Classification | Scope |
|---|---|---|
| `research/brainvision/test_durable_evidence_core_v0_3.py` | `REQUIRED_COMPATIBILITY_TEST_CHANGE` | Primary writer and default fail-closed adapter expectations; confirmed synthetic adapter helper. |
| `research/brainvision/test_durable_evidence_authority_v0_3.py` | `REQUIRED_COMPATIBILITY_TEST_CHANGE` | Confirmed synthetic adapter helper and centralized durability-evidence construction compatibility. |
| `research/brainvision/test_durable_evidence_scientific_result_v0_3.py` | `REQUIRED_COMPATIBILITY_TEST_CHANGE` | Confirmed synthetic adapter helper and scientific-result preservation under policy-bound evidence. |
| `research/brainvision/test_durable_evidence_publication_v0_3.py` | `REQUIRED_COMPATIBILITY_TEST_CHANGE` | Publication helper, staging-parent sync ordering, staged-set sync ordering, completion withholding, and J1 preservation. |
| `research/brainvision/test_durable_evidence_publication_recovery_v0_3.py` | `REQUIRED_COMPATIBILITY_TEST_CHANGE` | J2 recovery write durability, J2 non-completion on non-confirmed status, and original J1 preservation. |
| `research/brainvision/test_durable_evidence_publication_replay_v0_3.py` | `REQUIRED_COMPATIBILITY_TEST_CHANGE` | J1 replay policy mismatch and unconfirmed durability evidence. |
| `research/brainvision/test_durable_evidence_publication_recovery_replay_v0_3.py` | `REQUIRED_COMPATIBILITY_TEST_CHANGE` | J2 replay policy mismatch and unconfirmed durability evidence. |

New focused tests authorized:

| Path | Classification | Scope |
|---|---|---|
| `research/brainvision/test_durable_evidence_windows_directory_durability_v0_3.py` | `NEW_FOCUSED_TEST_REQUIRED` | Pure unit and synthetic adapter coverage for policy identity, canonical declaration, fail-closed default, non-Windows, all statuses, secondary codes including `TARGET_INVALID`, unknown native error preservation, reparse rejection, missing target, non-directory target, completion withholding, J1 preservation, J2 non-completion, and replay policy mismatch. |
| `research/brainvision/test_durable_evidence_windows_directory_durability_integration_v0_3.py` | `NEW_FOCUSED_TEST_REQUIRED` | Isolated Windows pytest `tmp_path` confirmation for the local fixed NTFS profile, confirmed status, policy identity, supported-profile detection, and no mutation outside pytest temporary root. |

Test candidates evaluated but not authorized:

| Path | Classification | Reason |
|---|---|---|
| `research/brainvision/test_durable_evidence_primary_writer_v0_3.py` | `NOT_REQUIRED` | No existing file; primary writer coverage remains in core plus the focused directory-durability tests. |
| `research/brainvision/test_durable_evidence_durability_v0_3.py` | `NOT_REQUIRED` | No existing file; durability-evidence policy binding is covered by the focused directory-durability tests and existing replay tests. |
| `research/brainvision/test_durable_evidence_windows_adapter_v0_3.py` | `NOT_REQUIRED` | No existing file; the authorized Windows adapter coverage is split into pure/synthetic and isolated-integration directory-durability files above. |
| `research/brainvision/test_durable_evidence_publication_resource_bounds_v0_3.py` | `READ_ONLY_REFERENCE` | Resource-bound behavior should remain covered by existing suite execution; no direct directory-adapter fixture change is required. |
| `research/brainvision/test_durable_evidence_publication_recovery_resource_bounds_v0_3.py` | `READ_ONLY_REFERENCE` | Recovery resource-bound behavior should remain covered by existing suite execution; no direct directory-adapter fixture change is required. |
| `research/brainvision/test_durable_evidence_boundary_v0_3.py` | `READ_ONLY_REFERENCE` | Boundary suite must run; no boundary assertion change is authorized unless a future stop condition returns for surface correction. |
| `research/brainvision/test_durable_evidence_publication_boundary_v0_3.py` | `READ_ONLY_REFERENCE` | Boundary suite must run; no publication-boundary assertion change is authorized. |
| `research/brainvision/test_durable_evidence_publication_recovery_boundary_v0_3.py` | `READ_ONLY_REFERENCE` | Boundary suite must run; no recovery-boundary assertion change is authorized. |

No other test file may change.

## 17. ISOLATED WINDOWS VALIDATION BOUNDARY

Authorized future implementation test:

```text
isolated Windows pytest temporary-directory confirmation
```

The isolated integration test may:

```text
create directories and files only beneath pytest tmp_path
open the selected directory handle
invoke the selected directory flush primitive
verify status classification
verify policy identity
verify supported-profile detection
verify no mutation outside tmp_path
```

It may not:

```text
touch real result trees
touch real manifests
touch user data
perform live publication
perform live recovery
kill processes
simulate crashes
use VMs
simulate power loss
change privileges
test network filesystems
test removable filesystems
```

This is not a general live-test lane.

```text
NO_LIVE_TEST_LANE_OPEN
```

## 18. REQUIRED IMPLEMENTATION WORKFLOW

Future implementation may:

```text
implement only the frozen source files
add or modify only the frozen tests
run focused synthetic tests
run isolated Windows tmp_path tests
run pre-existing durable-evidence suites
run boundary tests
perform forbidden-surface scans
perform replay determinism checks
```

Future implementation must not:

```text
stage
commit
push
reset
restore
checkout
clean
normalize
rebase
merge
tag
modify Git history
```

Hilmir remains the authoritative committer and pusher. Claude remains the
independent reviewer.

## 19. FORBIDDEN SURFACES

This authorization does not permit:

```text
live publication
live recovery
real result trees
production integration
kernel integration
memory-system integration
service integration
subprocess interruption
VM crash tests
physical power-loss tests
network filesystem testing
removable-drive testing
real capacity testing
BLOCKER-2 implementation
BLOCKER-4 implementation
production adapters
volume-handle flushing
external Win32 dependencies
any source file outside SOURCE_FILE_COUNT
any test file outside TOTAL_TEST_FILE_COUNT
```

## 20. STOP CONDITIONS

Stop immediately if:

```text
a source or test path outside the frozen surface becomes necessary
the Win32 primitive fails on the supported Windows profile
GENERIC_WRITE cannot open the target directory
FlushFileBuffers fails on the admitted local NTFS target
identity cannot be established deterministically
reparse-point rejection cannot be implemented safely
the policy digest is unstable
replay binding requires an unlisted file
recovery binding requires an unlisted file
existing J1/J2 grammar must change materially
Linux/POSIX behavior regresses
pre-existing tests regress
boundary tests regress
a real path or production surface is contacted
.git/index.lock appears
```

Do not improvise around a stop condition. Return for surface correction or
architectural decision.

## 21. FORMAL-HOLD AND MODE-0 BOUNDARIES

Preserve:

```text
BLOCKER-3 =
CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_STAGE_S3B_V0_3_SCOPE

BLOCKER-1 = open
BLOCKER-2 = open
BLOCKER-4 = open

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

No live-test lane is opened by this document.

## 22. AUTHORIZATION STATE

Selected state:

```text
State A =
BLOCKER_1_IMPLEMENTATION_AUTHORIZED_WITH_FROZEN_SURFACE
```

Reason:

```text
The source surface, test surface, Win32 contract, identity strategy, status
taxonomy, native error mapping, target sequencing, completion binding,
BLOCKER-2 handoff, and isolated Windows validation boundary are frozen
precisely enough for future implementation after independent review.
```

No implementation occurs during this document phase.

## 23. CONCLUSION

```text
BLOCKER-1 =
OPEN

specification =
COMPLETE_AND_ACCEPTED

implementation authorization =
GRANTED only if State A is selected and this authorization is independently
reviewed and committed

live-test authorization =
NOT GRANTED

NO_LIVE_TEST_LANE_OPEN
```

Primary verdict:

```text
A. BLOCKER_1_IMPLEMENTATION_AUTHORIZATION_READY_FOR_INDEPENDENT_REVIEW
```
