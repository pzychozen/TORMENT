# TORMENT Brainvision Stage S3B v0.3 BLOCKER-1 Windows Directory-Durability Implementation Findings v0.1

## 1. Status and Scope

```text
BLOCKER-1 implementation =
COMMITTED_AND_INDEPENDENTLY_ACCEPTED

real isolated Windows primitive =
CONFIRMED_WITHIN_AUTHORIZED_PYTEST_TMP_PATH_PROFILE

binding defects =
NONE_PRESENTLY_IDENTIFIED

BLOCKER-1 closure =
NOT YET ENACTED
```

This findings record is bounded to:

```text
Stage S3B v0.3
synthetic offline durable-evidence architecture
Windows 10 or Windows 11 workstation
local fixed NTFS volume
absolute ordinary existing directory
non-reparse target
isolated pytest tmp_path material
```

This document is descriptive only. It records committed implementation findings
and evidence for later review. It does not enact BLOCKER-1 closure, authorize a
live-test lane, modify implementation authority, or change the Brainvision
boundary.

Preserved boundaries:

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

This record does not claim true temporal vision, strong order sensitivity,
production vision, general visual cognition, real-world readiness, scientific
closure beyond the bounded frozen result, or formal BLOCKER-1 closure.

## 2. Authoritative Baseline and Lineage

Authoritative baseline:

```text
branch: main
HEAD: 82b78fc1e8be6b0ce64bb9473d5ada0ebf0db079
origin/main: 82b78fc1e8be6b0ce64bb9473d5ada0ebf0db079
```

Committed implementation:

```text
82b78fc1e8be6b0ce64bb9473d5ada0ebf0db079
research(brainvision): implement blocker 1 Windows directory durability
```

Relevant lineage:

```text
ac5dd26 docs(research): record durable evidence implementation findings v0.3
0d52dc0 docs(research): select resource bounds as first platform blocker
35d7b6e docs(research): specify blocker 3 resource admissibility
01a720c docs(research): authorize blocker 3 resource admissibility implementation
164680b docs(research): correct blocker 3 implementation surface
c03d5f9 research(brainvision): implement blocker 3 resource admissibility
843f861 docs(research): record blocker 3 resource admissibility findings
4e8bc7c docs(research): assess blocker 3 resource admissibility closure
6897fc8 docs(research): assess blocker 1 Windows directory durability
9ca92f9 docs(research): specify blocker 1 Windows directory durability
6ed2613 docs(research): authorize blocker 1 Windows directory durability
82b78fc research(brainvision): implement blocker 1 Windows directory durability
```

The assessment, specification, authorization, and implementation lineage remains
separate from this findings record. Formal closure remains pending a separate
future assessment.

## 3. Exact Implementation Surface

The committed implementation surface contains:

```text
8 source files
7 modified existing test files
2 new focused test files
17 committed paths total
```

Source files:

```text
research/brainvision/durable_evidence_schema_v0_3.py
research/brainvision/durable_evidence_windows_adapter_v0_3.py
research/brainvision/durable_evidence_primary_writer_v0_3.py
research/brainvision/durable_evidence_durability_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
research/brainvision/durable_evidence_publication_replay_v0_3.py
research/brainvision/durable_evidence_publication_recovery_replay_v0_3.py
```

Modified existing tests:

```text
research/brainvision/test_durable_evidence_core_v0_3.py
research/brainvision/test_durable_evidence_authority_v0_3.py
research/brainvision/test_durable_evidence_scientific_result_v0_3.py
research/brainvision/test_durable_evidence_publication_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_v0_3.py
research/brainvision/test_durable_evidence_publication_replay_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_replay_v0_3.py
```

New focused tests:

```text
research/brainvision/test_durable_evidence_windows_directory_durability_v0_3.py
research/brainvision/test_durable_evidence_windows_directory_durability_integration_v0_3.py
```

No production-kernel, live-service, memory-system, autonomous, cognitive, or
production-adapter surface was changed. No `torment_service/kernel/`, production
TORMENT memory functionality, live service behavior, prompt/action surface,
autonomy, identity, truth-selection, or memory-cognition surface was modified.

## 4. Implemented Win32 Primitive

The implementation records and uses the following Win32 APIs in the directory
durability adapter:

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

Frozen `CreateFileW` contract:

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

Explicit exclusions:

```text
no pywin32
no external dependency
no MoveFileExW
no ReplaceFileW
no MOVEFILE_WRITE_THROUGH
no volume-handle flushing
no DeviceIoControl
no GetFinalPathNameByHandleW
no production adapter
no promotion implementation
```

The primitive is a directory-entry durability operation for admitted directory
targets. It is not a promotion operation and does not close BLOCKER-2.

## 5. Support-Profile Enforcement

Only the admitted Windows local-fixed-NTFS profile can return positive
confirmation:

```text
Windows 10 or Windows 11 workstation
local fixed volume
NTFS filesystem
absolute ordinary existing directory
non-reparse directory target
isolated pytest tmp_path material for positive-profile validation
```

Everything outside the admitted profile remains fail-closed as appropriate:

```text
unsupported
denied
indeterminate
invalid
identity-changed
operation-failed
```

A failure within the admitted positive profile is a stop condition. Such a
failure does not justify weakening the profile, broadening support claims, or
changing the durability grammar.

## 6. Identity and Reparse Guarantees

The implementation uses a three-stage object-identity sequence:

```text
1. preflight handle identity
2. actual flush-handle identity
3. post-flush reopened-handle identity
```

Identity fields:

```text
volume serial number
file index high
file index low
```

Identity mappings:

```text
identity unavailable:
DIRECTORY_DURABILITY_INDETERMINATE
TARGET_IDENTITY_UNAVAILABLE

identity changed:
DIRECTORY_DURABILITY_IDENTITY_CHANGED
TARGET_IDENTITY_CHANGED
```

Path-string equality is not treated as filesystem-object identity.

The implementation rejects:

```text
directory symlinks
junctions
mount points
unknown reparse tags
```

with:

```text
DIRECTORY_DURABILITY_TARGET_INVALID
TARGET_REPARSE_POINT
```

## 7. Policy Identity

Policy ownership:

```text
POLICY_DECLARATION_IN_SCHEMA_MODULE
```

Computed directory-durability policy digest:

```text
491ec6dc5704d26f97b58f155434e8f81fe424ee3f9bba997f6ed800298cbba4
```

The digest rule is:

```text
SHA256(canonical_json_bytes(directory_durability_policy_declaration()))
```

The digest is computed from canonical policy material and is not hardcoded.

The policy identity is bound into:

```text
publication utility identities
immutable-write durability evidence
publication durability evidence
publication replay
publication recovery replay
recovery-chain record durability
completion gating
```

Foreign, absent, malformed, or mismatched policy identity fails closed.

## 8. Sequencing Findings

Recovery-chain and receipt sequencing:

```text
write
flush
file fsync
close
read-back verification
sync ARTIFACT_PARENT_DIRECTORY
require DIRECTORY_DURABILITY_CONFIRMED
admit durability evidence
```

Publication staging creation:

```text
create staging directory
sync STAGING_PARENT_DIRECTORY
require DIRECTORY_DURABILITY_CONFIRMED
```

Complete staged-artifact-set sequencing:

```text
write and verify all staged artifacts
perform one set-level STAGING_DIRECTORY sync
require DIRECTORY_DURABILITY_CONFIRMED
admit staging durability
```

No per-artifact staging-directory sync is required.

```text
FINAL_PARENT_DIRECTORY
```

is present only as a reusable BLOCKER-1 operation for future BLOCKER-2 use. It
is not promotion and does not establish promotion ownership or no-replace
semantics.

## 9. Status and Error Taxonomy

Top-level directory durability statuses:

```text
DIRECTORY_DURABILITY_CONFIRMED
DIRECTORY_DURABILITY_UNSUPPORTED
DIRECTORY_DURABILITY_DENIED
DIRECTORY_DURABILITY_INDETERMINATE
DIRECTORY_DURABILITY_TARGET_INVALID
DIRECTORY_DURABILITY_IDENTITY_CHANGED
DIRECTORY_DURABILITY_OPERATION_FAILED
```

Only:

```text
DIRECTORY_DURABILITY_CONFIRMED
```

may contribute positive durability evidence.

Unknown native errors retain their numeric code and map fail-closed to
indeterminate status.

```text
ERROR_INVALID_PARAMETER
```

is treated as operation failure, not unsupported.

## 10. Completion, Publication, Recovery, and Replay Effects

`DURABLE_ACCEPTED` requires both:

```text
DIRECTORY_DURABILITY_CONFIRMED
matching active directory-durability policy identity
```

All non-confirmed outcomes:

```text
withhold PUBLICATION_COMPLETED
withhold J2 verified/completed evidence
preserve original J1 evidence
preserve final artifacts
preserve the authoritative scientific result
produce deterministic failure evidence
```

The implementation preserves the existing J1/J2 grammar and introduces no new
scientific-completion family.

Publication replay and recovery replay reject foreign or malformed
directory-durability policy identity.

Publication is a projection of the authoritative scientific result.

The authoritative durable result remains:

```text
verified IMMUTABLE_SCIENTIFIC_BUNDLE
+
linked valid SCIENTIFIC_COMPLETION
```

The observer/evidence boundary occurs only when that pair is durable, verified,
identity-bound, and linked.

J2 recovery evidence remains separate and cannot reconstruct or claim original
J1 completion.

## 11. Authoritative Windows Test Evidence

Focused Windows directory-durability pair:

```text
23 passed in 0.34s
23 passed in 0.33s
```

Nine authorized test files:

```text
172 passed in 4.48s
172 passed in 5.15s
```

Complete required Stage S3B v0.3 durable-evidence family:

```text
261 passed, 1 skipped in 6.75s
261 passed, 1 skipped in 8.13s
```

The positive-profile integration test:

```text
executed on Windows
did not skip
used pytest tmp_path
detected local fixed NTFS
opened the directory with the frozen CreateFileW contract
called FlushFileBuffers successfully
retained stable identity
returned DIRECTORY_DURABILITY_CONFIRMED
matched the active policy identity
```

No additional executions or measurements are claimed by this findings record.

## 12. Independent-Review Findings

Claude's verdict:

```text
A. ACCEPT_BLOCKER_1_IMPLEMENTATION_CANDIDATE
```

The independent review verified:

```text
exact 17-path surface
policy digest
Win32 ABI
CreateFileW handle contract
GetLastError timing
three-stage identity
reparse rejection
support detection
status and error mappings
target sequencing
durability admission
publication/recovery binding
replay policy binding
synthetic adapter isolation
forbidden-surface absence
line-ending safety
```

Claude's review environment was Linux and therefore did not independently
execute the Windows-only positive-profile integration test or reproduce the
authoritative Windows pytest counts.

Those executions are grounded in Hilmir's authoritative Windows evidence and
were consistent with independently inspected code.

## 13. Exploratory All-Research Failure Isolation

An exploratory all-`research\brainvision` run encountered independent-order
fixture sentinel failures.

Classification:

```text
EXPECTED_SENTINEL_REJECTION_UNRELATED_TO_BLOCKER_1
```

The failures:

```text
were outside the authorized nine-test surface
were outside the required Stage S3B v0.3 durable-evidence suite
were not modified by BLOCKER-1
did not import the changed BLOCKER-1 modules
used separate repository-local result-path sentinel rules
```

The BLOCKER-1 candidate created no forbidden result or manifest path.

These exploratory failures do not, by themselves, reopen or invalidate the
BLOCKER-1 implementation findings.

No attempt is made in this findings record to fix or modify those tests.

## 14. Remaining Limitations

Remaining limitations:

```text
support is bounded to the admitted Windows local-fixed-NTFS profile
only isolated pytest tmp_path positive-profile execution is established
no production filesystem deployment is established
no live publication or recovery test lane is open
no same-volume no-replace promotion is implemented
promotion ownership and final ownership remain BLOCKER-2 concerns
BLOCKER-4 remains open and separate
no volume-handle flush is implemented
no filesystem guarantee is claimed beyond the admitted profile
no live Brainvision, real-video, gameplay, production, service, kernel, memory, autonomy, cognition, or truth-selection integration is authorized
```

No live capture, real gameplay/video, real publication/recovery, production
adapter, general live-test, or production-kernel lane is open.

## 15. Findings Conclusion

The authorized implementation was committed.

The authorized implementation was independently accepted.

The isolated Windows directory-flush primitive was positively exercised.

The policy and evidence bindings are present.

No binding defect is presently identified.

Formal BLOCKER-1 closure remains pending.

The closure decision is deferred to a separate future assessment.

Expected next procedural step:

```text
independent review of this findings record
operator commit and push
separate BLOCKER-1 closure assessment
```

No closure label is enacted by this findings record.
