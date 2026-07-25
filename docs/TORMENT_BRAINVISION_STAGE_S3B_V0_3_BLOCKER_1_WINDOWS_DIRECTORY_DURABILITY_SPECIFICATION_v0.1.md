# TORMENT Brainvision Stage S3B v0.3 BLOCKER-1 Windows Directory-Durability Specification v0.1

## 1. DOCUMENT STATUS

```text
document_class                    = blocker specification (docs-only)
selected_blocker                  = BLOCKER-1
authority_created                 = none
implementation_authorized         = false
test_creation_authorized          = false
execution_authorized              = false
live_test_authorized              = false
publication_authorized            = false
publication_recovery_authorized   = false
filesystem_probe_authorized       = false
crash_test_authorized             = false
power_loss_test_authorized        = false
manifest_contact_authorized       = false
real_data_contact_authorized      = false
source_modified_by_this_document  = false
tests_modified_by_this_document   = false
git_mutations_by_this_document    = none
```

This specification defines a future BLOCKER-1 implementation contract. It does
not implement code, create tests, authorize live tests, or close BLOCKER-1.

## 2. SPECIFICATION PURPOSE

This document specifies the Windows directory-entry durability obligation
identified by the accepted BLOCKER-1 assessment.

It answers:

```text
After an immutable artifact file has been written, flushed, file-fsynced,
closed, and byte-verified, what exact synthetic Windows directory durability
operation and evidence are required before the artifact may count as durably
staged or durably finalized?
```

The answer is bounded:

```text
current guarantee =
file-level durability and fail-closed directory-durability seam only

required guarantee =
validated identity-bound Windows directory-entry durability for the explicitly
defined directory targets
```

This specification distinguishes file-content durability, file-handle flush,
directory-entry durability, staging-directory durability, parent-directory
durability, promotion durability, rename durability, final-path visibility,
logical verification, crash consistency, and power-loss persistence. No two are
treated as equivalent unless this document defines the relationship explicitly.

## 3. AUTHORITATIVE BASELINE

Baseline required by this specification order:

```text
branch = main

HEAD =
6897fc8e4cbeaceb4d243418bd7251d470e1635a

origin/main =
6897fc8e4cbeaceb4d243418bd7251d470e1635a

latest subject =
docs(research): assess blocker 1 Windows directory durability

working tree =
clean

index lock =
absent
```

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
```

Primary governing assessment:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_ASSESSMENT_v0.1.md
```

Other governing sources include:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_PLATFORM_BLOCKER_DECOMPOSITION_AND_FIRST_BOUND_SELECTION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_ARCHITECTURE_REVIEW_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_IMPLEMENTATION_FINDINGS_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_CLOSURE_ASSESSMENT_v0.1.md
```

The specification follows the assessment's bounded conclusion and does not
redefine BLOCKER-1.

## 5. BLOCKER-1 SCOPE

BLOCKER-1 owns only the directory-entry durability obligation around
already-written immutable files and explicitly defined directory targets.

In scope:

```text
directory containing a newly created immutable artifact
directory entry linking the artifact name to the written file
staging-directory entry durability before staging is declared durable
final parent-directory durability where required by the publication sequence
Windows support detection
Windows directory-handle operation
directory-flush result classification
fail-closed handling
evidence identity
synthetic adapter and isolated temporary-directory validation
```

Outside BLOCKER-1:

```text
same-volume no-replace promotion implementation - BLOCKER-2
promotion rename durability - BLOCKER-2 unless a narrow post-promotion
parent-directory sync is explicitly handed to BLOCKER-1
crash consistency - BLOCKER-4 or out of scope according to governing documents
resource admissibility - BLOCKER-3, already closed
real filesystem capacity
concurrent hostile mutation
network filesystem guarantees
removable-drive guarantees
production privilege handling
real result trees
real publication or recovery
physical power-loss proof
```

## 6. CURRENT GUARANTEE

The committed Stage S3B v0.3 machinery already provides:

```text
exclusive immutable file creation
bounded canonical bytes
file write
language/runtime buffer flush
file-level fsync or equivalent as exposed by os.fsync
handle close through scoped file context
read-back byte comparison
read-back SHA-256 comparison
fail-closed directory-durability adapter seam
fail-closed promotion adapter seam
durable-completion gating
replay durability-evidence gating
synthetic pytest-local positive adapters
```

The current default directory-durability adapter returns:

```text
DIRECTORY_DURABILITY_UNCONFIRMED
```

Therefore the current positive guarantee is:

```text
file-level durability and fail-closed directory-durability seam only
```

It does not establish:

```text
validated Windows directory-entry durability
directory-handle flush implementation
parent-directory synchronization
filesystem support matrix
native Windows error taxonomy
post-promotion directory persistence
crash consistency
power-loss persistence
```

## 7. REQUIRED DIRECTORY-DURABILITY GUARANTEE

Required guarantee:

```text
For each explicitly required directory target, the future implementation must
open the intended Windows directory object through the selected adapter,
verify that the opened object is the expected non-reparse directory under the
supported platform profile, issue the selected directory flush operation,
close the handle, and bind a confirmed result and policy identity before any
caller treats the associated immutable file or directory entry as durably
accepted.
```

`DIRECTORY_DURABILITY_CONFIRMED` means only:

```text
the selected adapter successfully completed the specified directory-handle
operation for the specified target under the declared validation profile
```

It does not mean:

```text
physical power-loss proof
whole-volume persistence proof
host crash proof
storage-controller persistence proof
network filesystem guarantee
same-volume no-replace promotion proof
production readiness
```

The guarantee is identity-bound. A result produced under one
directory-durability policy cannot silently satisfy replay or completion under
a different policy.

## 8. WINDOWS PRIMITIVE CONTRACT

Selected future implementation approach:

```text
small isolated Win32 adapter
implemented with Python standard library ctypes
no external dependency
no production/kernel/service/memory integration
```

Rationale:

```text
The Python standard library already covers file creation, file flushing,
file fsync, close, and read-back. It does not expose a documented
Windows directory-handle flush primitive at the level required here.
The smallest quarantined surface is therefore a Win32 adapter isolated behind
the existing durability adapter boundary.
```

Informative API sources for the selected boundary are Microsoft Win32
documentation for `CreateFileW`, `FlushFileBuffers`,
`GetDriveTypeW`, `GetVolumeInformationW` or
`GetVolumeInformationByHandleW`, and `GetFinalPathNameByHandleW`.

Selected primitive:

```text
open target directory handle with CreateFileW
use FILE_FLAG_BACKUP_SEMANTICS to obtain a directory handle
use FILE_FLAG_OPEN_REPARSE_POINT or equivalent pre-open policy to avoid
following reparse-point directories
request GENERIC_WRITE because FlushFileBuffers requires a write-capable handle
use OPEN_EXISTING
use FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE unless a later
authorization narrows sharing
call FlushFileBuffers on the directory handle
capture GetLastError on failure
close the handle with CloseHandle
```

Selected target object:

```text
the directory whose entry set must be synchronized for the event being admitted
```

Required access rights:

```text
GENERIC_WRITE
```

Share mode:

```text
FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE
```

Creation disposition:

```text
OPEN_EXISTING
```

Flags and attributes:

```text
FILE_FLAG_BACKUP_SEMANTICS
FILE_FLAG_OPEN_REPARSE_POINT where needed to avoid following a reparse point
```

`FILE_FLAG_WRITE_THROUGH` is not required for the directory-handle contract in
this first specification. If later review finds that it is necessary for a
confirmed directory-handle claim, the implementation must stop for renewed
specification rather than silently broadening this contract.

`MoveFileExW`, `ReplaceFileW`, and `MOVEFILE_WRITE_THROUGH` are not part of
BLOCKER-1's implementation primitive. They belong to BLOCKER-2 promotion
semantics unless a future BLOCKER-2 handoff explicitly delegates a
post-promotion parent sync to this adapter.

Volume handles are not required for the initial BLOCKER-1 contract. Volume
flush requires administrative privilege and would broaden the claim beyond the
directory-entry operation selected here. A need for volume-handle flushing is a
stop condition for renewed architecture review.

Success criterion:

```text
target admitted as supported
target exists
target is a directory
target is not a symlink, junction, or other reparse point
opened handle identity matches the expected target identity
FlushFileBuffers returns nonzero
CloseHandle succeeds or, if CloseHandle failure is observable, maps
fail-closed as indeterminate
```

Unsupported criterion:

```text
platform is not Windows
filesystem or drive class is outside the supported profile
selected directory-handle operation returns an error mapped to unsupported
```

Denied criterion:

```text
the target exists and is otherwise in scope, but access rights, sharing,
privilege, or policy prevent the operation
```

Indeterminate criterion:

```text
the adapter cannot determine whether the intended directory object was opened,
whether the platform is supported, whether the flush was applied to the intended
target, or whether the failure should be classified more specifically
```

No unexpected exception may be treated as confirmed.

## 9. DIRECTORY TARGET MODEL

Directory sync targets:

| Event | Required target | Rationale |
|---|---|---|
| Creation of a stored record file in its chain directory | `ARTIFACT_PARENT_DIRECTORY` | The durable entry is the new immutable record filename in the chain directory. |
| Creation of a stored bundle file in its bundle directory | `ARTIFACT_PARENT_DIRECTORY` | The durable entry is the new immutable bundle filename in the bundle directory. |
| Creation of publication chain record files | `ARTIFACT_PARENT_DIRECTORY` | Publication records are immutable files inside the publication chain directory. |
| Creation of recovery chain record files | `ARTIFACT_PARENT_DIRECTORY` | Recovery records are immutable files inside the recovery chain directory. |
| Creation of staging directory inside its parent | `STAGING_PARENT_DIRECTORY` | The staging directory entry itself must be visible and durable before a staged-set claim can depend on it. |
| Artifact creation inside staging directory | `STAGING_DIRECTORY` | The three artifact names must be durably linked to their written bytes. |
| Each immutable artifact entry after file durability | `STAGING_DIRECTORY` | Per-file file durability is insufficient without the containing directory entry. |
| Completion of the full staged artifact set | `STAGING_DIRECTORY` | One set-level flush after all three artifact writes is the minimum required directory evidence for the staged artifact set. |
| Creation of final publication directory | `NOT_BLOCKER_1` before promotion | The creation/rename of final directory is BLOCKER-2 until the handoff defined in Section 17. |
| Post-promotion parent-directory state | `FINAL_PARENT_DIRECTORY` under split handoff | BLOCKER-2 owns promotion; BLOCKER-1 may provide a reusable parent-directory sync result after BLOCKER-2 establishes ownership. |
| Recovery final-directory reads | `NOT_BLOCKER_1` | Recovery visibility is read-only and evidence-only; it does not prove original J1 directory durability. |

Minimum sequence for staged artifacts:

```text
flush STAGING_PARENT_DIRECTORY after creating staging_directory
write, file-fsync, close, and read-back all three artifacts
flush STAGING_DIRECTORY once after all three artifact entries are present
verify exact inventory and hashes
admit staging durability only after both required directory results are confirmed
```

Per-artifact directory flushing is not required in the initial contract because
the staged-set evidence is not admitted until all artifacts are written and the
staging directory is flushed as a complete set. If a later implementation wants
per-artifact directory evidence, it may add it only through separate
authorization and without weakening the set-level requirement.

## 10. ADAPTER CONTRACT

The future adapter interface must be equivalent in responsibility to:

```text
sync_directory_entry(path, context) -> DirectoryDurabilityResult
```

The exact symbol may evolve only if the existing architecture remains
compatible and the implementation authorization freezes the surface.

Input contract:

```text
path:
  str or Path-like value accepted by the adapter boundary

path form:
  absolute path required after normalization

normalization:
  Windows extended-length normalization is required before CreateFileW

directory existence:
  target must exist before the operation

symlink/reparse-point policy:
  symlinked directories, junctions, mount-point reparse directories, and
  unknown reparse tags are not confirmed; they map fail closed

expected platform:
  Windows only for a confirming adapter

operation context:
  target_role, chain_identity where applicable, event kind, and caller phase

expected directory identity:
  when available, bind volume serial/file index or final handle path identity;
  if identity cannot be acquired, map to indeterminate rather than confirmed
```

Output fields:

```text
status
failure_code
platform
operation
target_path_identity
native_error_code
native_error_name
message
adapter_identity
adapter_policy_identity
```

Field rules:

```text
status:
  one finite taxonomy value from Section 11

failure_code:
  null only for DIRECTORY_DURABILITY_CONFIRMED
  non-null deterministic code otherwise

platform:
  "windows" for a confirming adapter

operation:
  stable operation identity, not free prose

target_path_identity:
  canonical normalized target identity, with volatile absolute roots excluded
  from policy identity material unless intentionally included in evidence only

native_error_code:
  integer Windows error code when available, otherwise null

native_error_name:
  deterministic symbolic name when known, otherwise null

message:
  bounded diagnostic text; not identity-critical

adapter_identity:
  stable adapter implementation identity

adapter_policy_identity:
  computed policy identity from Section 14
```

Default and absent adapters remain fail closed and must not synthesize
`DIRECTORY_DURABILITY_CONFIRMED`.

## 11. STATUS AND FAILURE TAXONOMY

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

`DIRECTORY_DURABILITY_OPERATION_FAILED` is retained as a separate class for
known native failures that are neither unsupported, denied, target-invalid, nor
identity-changing. It must not become a catch-all that hides unknown errors.

Failure-code vocabulary:

```text
DIRECTORY_DURABILITY_ADAPTER_ABSENT
DIRECTORY_DURABILITY_PLATFORM_UNSUPPORTED
DIRECTORY_DURABILITY_FILESYSTEM_UNSUPPORTED
DIRECTORY_DURABILITY_DRIVE_TYPE_UNSUPPORTED
DIRECTORY_DURABILITY_TARGET_MISSING
DIRECTORY_DURABILITY_TARGET_NOT_DIRECTORY
DIRECTORY_DURABILITY_TARGET_REPARSE_POINT
DIRECTORY_DURABILITY_TARGET_IDENTITY_CHANGED
DIRECTORY_DURABILITY_ACCESS_DENIED
DIRECTORY_DURABILITY_SHARING_DENIED
DIRECTORY_DURABILITY_PRIVILEGE_NOT_HELD
DIRECTORY_DURABILITY_DIRECTORY_OPEN_FAILED
DIRECTORY_DURABILITY_DIRECTORY_FLUSH_FAILED
DIRECTORY_DURABILITY_DIRECTORY_CLOSE_INDETERMINATE
DIRECTORY_DURABILITY_NATIVE_ERROR_UNKNOWN
DIRECTORY_DURABILITY_ADAPTER_EXCEPTION
DIRECTORY_DURABILITY_POLICY_IDENTITY_MISMATCH
```

Mapping rules:

```text
DIRECTORY_DURABILITY_CONFIRMED:
  failure_code = null

DIRECTORY_DURABILITY_UNSUPPORTED:
  platform, filesystem, or drive type is outside the supported contract

DIRECTORY_DURABILITY_DENIED:
  access, sharing, lock, or privilege prevents the selected operation

DIRECTORY_DURABILITY_TARGET_INVALID:
  target is missing, not a directory, or a reparse-point directory

DIRECTORY_DURABILITY_IDENTITY_CHANGED:
  pre-open, handle, or post-open identity does not match

DIRECTORY_DURABILITY_OPERATION_FAILED:
  selected operation failed with a known non-denied, non-unsupported native
  failure

DIRECTORY_DURABILITY_INDETERMINATE:
  unknown native error, adapter exception, incomplete identity evidence, close
  uncertainty, or classification ambiguity
```

## 12. WINDOWS ERROR MAPPING

Native errors must be captured by numeric code. Known symbolic names are
diagnostic, not sufficient by themselves.

Deterministic mapping:

| Windows error | Mapping | Failure code |
|---|---|---|
| `ERROR_ACCESS_DENIED` | `DIRECTORY_DURABILITY_DENIED` | `DIRECTORY_DURABILITY_ACCESS_DENIED` |
| `ERROR_INVALID_FUNCTION` | `DIRECTORY_DURABILITY_UNSUPPORTED` | `DIRECTORY_DURABILITY_FILESYSTEM_UNSUPPORTED` |
| `ERROR_NOT_SUPPORTED` | `DIRECTORY_DURABILITY_UNSUPPORTED` | `DIRECTORY_DURABILITY_FILESYSTEM_UNSUPPORTED` |
| `ERROR_INVALID_PARAMETER` | `DIRECTORY_DURABILITY_OPERATION_FAILED` | `DIRECTORY_DURABILITY_DIRECTORY_OPEN_FAILED` or `DIRECTORY_DURABILITY_DIRECTORY_FLUSH_FAILED` according to phase |
| `ERROR_FILE_NOT_FOUND` | `DIRECTORY_DURABILITY_TARGET_INVALID` | `DIRECTORY_DURABILITY_TARGET_MISSING` |
| `ERROR_PATH_NOT_FOUND` | `DIRECTORY_DURABILITY_TARGET_INVALID` | `DIRECTORY_DURABILITY_TARGET_MISSING` |
| `ERROR_SHARING_VIOLATION` | `DIRECTORY_DURABILITY_DENIED` | `DIRECTORY_DURABILITY_SHARING_DENIED` |
| `ERROR_LOCK_VIOLATION` | `DIRECTORY_DURABILITY_DENIED` | `DIRECTORY_DURABILITY_SHARING_DENIED` |
| `ERROR_PRIVILEGE_NOT_HELD` | `DIRECTORY_DURABILITY_DENIED` | `DIRECTORY_DURABILITY_PRIVILEGE_NOT_HELD` |
| `ERROR_NOT_READY` | `DIRECTORY_DURABILITY_OPERATION_FAILED` | `DIRECTORY_DURABILITY_DIRECTORY_FLUSH_FAILED` |
| `ERROR_DEVICE_NOT_CONNECTED` | `DIRECTORY_DURABILITY_OPERATION_FAILED` | `DIRECTORY_DURABILITY_DIRECTORY_FLUSH_FAILED` |
| `ERROR_GEN_FAILURE` | `DIRECTORY_DURABILITY_OPERATION_FAILED` | `DIRECTORY_DURABILITY_DIRECTORY_FLUSH_FAILED` |
| unknown native error | `DIRECTORY_DURABILITY_INDETERMINATE` | `DIRECTORY_DURABILITY_NATIVE_ERROR_UNKNOWN` |

If an error is produced in a phase where the table's failure code is
ambiguous, the implementation must choose the phase-specific code named in the
table and preserve the native numeric code.

No unknown native error may map to confirmed.

## 13. PLATFORM AND FILESYSTEM SUPPORT MATRIX

Initial claimed environment:

```text
Windows 10 or later desktop/server family
local fixed volume
NTFS filesystem
pytest-local or explicitly authorized synthetic path
non-reparse directory target
non-production, non-service, non-kernel execution
```

Support matrix:

| Environment | Classification | Requirement |
|---|---|---|
| Windows 10/11 local fixed NTFS | `SUPPORTED` after isolated confirmation | May produce `DIRECTORY_DURABILITY_CONFIRMED` only after the future implementation's non-destructive Windows temporary-directory test passes. |
| Windows Server local fixed NTFS | `SUPPORTED_WITH_LIMITED_CLAIM` | May be included if the implementation authorization explicitly covers it and tests it. |
| ReFS local fixed volume | `INDETERMINATE` | Do not claim support without explicit future evidence. |
| FAT/FAT32 | `UNSUPPORTED` | Map fail closed. |
| exFAT | `UNSUPPORTED` | Map fail closed. |
| network paths | `UNSUPPORTED` | Map fail closed. |
| UNC paths | `UNSUPPORTED` for initial contract | Do not confirm under this v0.1 policy. |
| mapped drives | `UNSUPPORTED` for initial contract | Do not confirm under this v0.1 policy because backing filesystem and network mapping can be ambiguous. |
| removable media | `UNSUPPORTED` | Map fail closed. |
| virtual filesystems | `UNSUPPORTED` | Map fail closed unless separately specified later. |
| cloud-synchronized folders | `UNSUPPORTED` | Map fail closed for durable publication semantics. |
| symlinked directories | `UNSUPPORTED` / target invalid | Reject before confirmation. |
| junctions | `UNSUPPORTED` / target invalid | Reject before confirmation. |
| mount-point reparse directories | `UNSUPPORTED` / target invalid | Reject before confirmation. |
| unknown reparse points | `UNSUPPORTED` / target invalid | Reject before confirmation. |
| non-Windows | `UNSUPPORTED` | Adapter must fail closed and preserve Linux/POSIX behavior. |

The initial contract deliberately prefers a narrow supported profile over a
general Windows claim.

## 14. POLICY IDENTITY AND EVIDENCE BINDING

The future implementation must define an identity-bound
directory-durability policy declaration containing at least:

```text
policy_schema_identity
adapter_identity
operation_identity
supported_platform_declaration
supported_filesystem_declaration
target_role_declaration
status_taxonomy
failure_mapping_version
path_normalization_policy
reparse_point_policy
validation_profile_identity
```

Required schema identity:

```text
durable-evidence-windows-directory-durability-policy-v0.1
```

Required digest rule:

```text
directory_durability_policy_sha256 =
SHA-256(canonical_json_bytes(directory_durability_policy_declaration))
```

The digest must be computed from canonical policy material and not hardcoded as
an unexplained predicted value.

Required carried identity shape:

```text
directory_durability_policy_identity = {
  "policy_schema_identity":
    "durable-evidence-windows-directory-durability-policy-v0.1",
  "policy_sha256":
    directory_durability_policy_sha256
}
```

Binding locations:

```text
publication utility identities
durability evidence
replay evidence
completion gating
recovery verification where recovery writes J2 durability evidence
```

Replay rule:

```text
A replay under a different directory-durability policy must not silently
validate the original result. Policy mismatch must fail closed with a
deterministic policy-identity mismatch classification or failure code.
```

Policy identity material must not include volatile absolute temporary paths,
timestamps, host names, native error prose, or environment-sensitive messages.
Those may appear in individual evidence records only.

## 15. PUBLICATION SEQUENCING

Required order for each immutable stored record or bundle file:

```text
1. create immutable file in admitted parent directory
2. write bounded bytes
3. flush language/runtime buffer
4. perform file-level durability operation
5. close file handle
6. read back and verify exact bytes/hash
7. synchronize required directory entry
8. verify confirmed directory-durability result
9. admit immutable-write result into verified durability evidence
```

Required order for publication staging:

```text
1. durable PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED record
2. durable PUBLICATION_ATTEMPTED record
3. resource preflight and complete in-memory artifact generation
4. explicit synthetic capacity admission
5. create staging directory
6. synchronize STAGING_PARENT_DIRECTORY for the staging directory entry
7. write all three artifact files with file-level durability and read-back
8. synchronize STAGING_DIRECTORY once for the complete artifact set
9. verify exact staging inventory and hashes
10. admit staged artifact set as durably staged only if all required directory
    results are DIRECTORY_DURABILITY_CONFIRMED
```

Directory synchronization occurs:

```text
once after staging directory creation for the staging directory entry
once after all artifact files are written and read-back verified for the
complete staged artifact set
```

It does not occur before all required file-level writes and read-backs are
complete. No staging durability evidence may be accepted before all required
directory operations are confirmed.

## 16. COMPLETION AND FAILURE GATING

Only:

```text
DIRECTORY_DURABILITY_CONFIRMED
```

may contribute positively to durable publication or recovery-chain evidence.

All other statuses must:

```text
fail closed
withhold PUBLICATION_COMPLETED
produce deterministic failure evidence
preserve the authoritative scientific result
preserve the original J1 evidence chain
avoid creating J2 verified/completed claims caused by a failed J1 publication
```

Existing failure families should be preserved where they already fit:

```text
BYTE_VALID_DURABILITY_UNCONFIRMED
PUBLICATION_CHAIN_GENESIS_WRITE_FAILED
PUBLICATION_ATTEMPTED_WRITE_FAILED
PUBLICATION_STAGING_DURABILITY_UNCONFIRMED
PUBLICATION_ARTIFACTS_VERIFIED_PUBLICATION_COMPLETED_RECORD_FAILED
PUBLICATION_RECOVERY_CHAIN_GENESIS_WRITE_FAILED
PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED
PUBLICATION_CHAIN_DURABILITY_UNCONFIRMED
PUBLICATION_RECOVERY_CHAIN_DURABILITY_UNCONFIRMED
```

Future implementation may add a narrow directory-durability failure family only
if the implementation authorization freezes it. It must not change J1 or J2
grammar, scientific result semantics, bundle identity semantics, or recovery's
evidence-only boundary.

## 17. BLOCKER-2 HANDOFF

Selected handoff:

```text
SPLIT_CONTRACT_WITH_EXPLICIT_HANDOFF
```

Boundary:

```text
BLOCKER-1 proves admitted directory-entry durability for pre-promotion
staging targets and provides a reusable parent-directory synchronization
operation.

BLOCKER-2 owns same-volume no-replace promotion semantics, including final
destination absence, same-volume verification, no copy, no merge, no overwrite,
no replacement, promotion ownership, and promotion ambiguity.

After BLOCKER-2 has established that a promotion operation created the final
directory entry it claims, BLOCKER-2 may call or require the BLOCKER-1
directory-sync adapter on FINAL_PARENT_DIRECTORY. That call proves only the
post-promotion parent-directory sync result under BLOCKER-1's policy; it does
not prove BLOCKER-2 ownership or no-replace semantics.
```

Justification:

```text
The governing decomposition states that promotion involves directory state but
has additional no-replace and attribution concerns separated under BLOCKER-2.
Therefore BLOCKER-1 should supply the directory-sync primitive and evidence
contract, while BLOCKER-2 owns the promotion operation and final ownership
claim.
```

This specification does not implement or close BLOCKER-2.

## 18. VALIDATION PLAN

This section defines future validation layers. It does not authorize execution.

Pure unit tests:

```text
status mapping
unknown-error fail-closed behavior
policy identity determinism
canonical serialization
adapter absence
non-Windows invocation
invalid target
reparse-point rejection
identity mismatch
completion gating
replay policy mismatch
```

Synthetic adapter tests:

```text
confirmed
unsupported
denied
indeterminate
identity changed
operation failed
unexpected exception
policy mismatch
```

Isolated Windows temporary-directory tests:

```text
opening a directory handle with CreateFileW
flushing the selected directory target with FlushFileBuffers
confirmed local fixed NTFS path under pytest tmp
access-denied mapping where safely constructible
missing-target mapping
unsupported filesystem classification where safely detectable
reparse-point rejection where host permissions permit
no mutation outside pytest temporary directories
no live publication
no live recovery
```

Explicitly excluded validation:

```text
live publication
live recovery
real result trees
subprocess-kill validation unless separately authorized
VM crash testing
physical power-loss testing
production privilege escalation
```

The future implementation must not be accepted based only on mocks. It must
eventually include an isolated, non-destructive Windows temporary-directory
confirmation of the chosen primitive, after specification acceptance and
implementation authorization.

## 19. FUTURE IMPLEMENTATION ACCEPTANCE CRITERIA

Future implementation acceptance requires:

```text
authorized source surface frozen by a separate implementation authorization
authorized test surface frozen by a separate implementation authorization
no production/kernel/service/memory changes
no manifest or real-result-tree contact
no real publication or recovery
directory-durability policy digest deterministic
directory target explicit for every event
supported environment explicit and narrow
default adapter fail closed
confirmed path independently tested on supported Windows
all non-confirmed paths withhold completion
replay policy mismatch rejected
no mutation on failure beyond admitted synthetic temporary material
pre-existing durable-evidence and boundary tests preserved
Linux/POSIX behavior preserved or explicitly separated
BLOCKER-2 remains open unless separately assessed and closed
BLOCKER-4 remains open
```

Stop conditions for future implementation:

```text
need for volume-handle flushing
need for administrative privileges
need for crash or power-loss proof
need for real publication or recovery
need for production/kernel/service/memory integration
need for network filesystem support in v0.1
need for external dependency
need to change scientific result semantics
need to change J1 or J2 grammar
need to weaken fail-closed default behavior
```

## 20. RECOMMENDED IMPLEMENTATION SURFACE

Likely future candidate source files:

```text
research/brainvision/durable_evidence_windows_adapter_v0_3.py
research/brainvision/durable_evidence_primary_writer_v0_3.py
research/brainvision/durable_evidence_durability_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
research/brainvision/durable_evidence_publication_replay_v0_3.py
research/brainvision/durable_evidence_publication_recovery_replay_v0_3.py
```

Likely future candidate tests:

```text
relevant existing durable-evidence tests that exercise durability evidence,
publication gating, recovery gating, and replay

one new focused Windows directory-durability test file if implementation
authorization finds it necessary
```

This document does not finalize the authorized file inventory. A separate
implementation-authorization document must freeze the exact source and test
surface before any implementation begins.

No production, kernel, service, memory, descriptor, PsiTRS, scientific-runner,
manifest, real-results, publication artifact, or recovery artifact path may be
proposed.

## 21. LIVE-TEST BOUNDARY

Preserved live-test posture:

```text
NO_LIVE_TEST_LANE_OPEN
```

Validation classifications:

```text
pure unit tests =
FUTURE_AFTER_IMPLEMENTATION_AUTHORIZATION

synthetic adapter tests =
FUTURE_AFTER_IMPLEMENTATION_AUTHORIZATION

isolated Windows temporary-directory tests =
FUTURE_AFTER_IMPLEMENTATION_AUTHORIZATION

subprocess interruption tests =
NOT_AUTHORIZED

VM crash tests =
NOT_AUTHORIZED

physical power-loss tests =
OUT_OF_SCOPE

real publication or recovery =
NOT_AUTHORIZED
```

No filesystem durability probe, live publication, live recovery, process
interruption, crash test, power-loss test, or real-data contact is authorized by
this specification.

## 22. FORMAL-HOLD AND MODE-0 BOUNDARIES

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

This specification does not authorize:

```text
implementation
test creation
live tests
real publication
real recovery
production integration
kernel integration
memory-system integration
crash testing
power-loss testing
```

## 23. SPECIFICATION STATE

Selected state:

```text
State A =
BLOCKER_1_SPECIFICATION_COMPLETE_READY_FOR_IMPLEMENTATION_AUTHORIZATION_REVIEW
```

Reason:

```text
The contract, primitive boundary, taxonomy, sequencing, evidence binding,
support matrix, validation plan, and BLOCKER-2 handoff are precise enough for a
separate implementation-authorization review.
```

This state does not authorize implementation.

## 24. CONCLUSION

```text
current guarantee =
file-level durability and fail-closed directory-durability seam only

required guarantee =
validated identity-bound Windows directory-entry durability for the explicitly
defined directory targets

BLOCKER-1 =
OPEN

implementation authorization =
NOT GRANTED

live-test authorization =
NOT GRANTED
```

Primary verdict:

```text
A. BLOCKER_1_SPECIFICATION_READY_FOR_INDEPENDENT_REVIEW
```
