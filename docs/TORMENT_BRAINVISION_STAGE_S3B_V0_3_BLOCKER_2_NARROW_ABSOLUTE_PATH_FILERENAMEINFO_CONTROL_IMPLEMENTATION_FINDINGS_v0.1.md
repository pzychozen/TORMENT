# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Narrow Absolute-Path FileRenameInfo Control Implementation Findings v0.1

## 1. Purpose

document_class = BLOCKER-2 narrow absolute-path FileRenameInfo control implementation findings

document_version = v0.1

findings_scope =
docs-only review of the committed implementation for the narrow absolute-path
`FileRenameInfo` diagnostic control.

implementation commit:

```text
03727e738bdb5dcd94ca63e958a9de39de25be43
```

implementation commit subject:

```text
research(brainvision): implement blocker 2 absolute-path control
```

This document records implementation findings only. It does not authorize
execution, does not create retained evidence, does not consume an authoritative
one-run gate, does not change a specification, does not integrate with
production, and does not close BLOCKER-2.

## 2. Authority and Baseline

Verified baseline for this findings document:

```text
branch:
main

HEAD:
03727e738bdb5dcd94ca63e958a9de39de25be43

origin/main:
03727e738bdb5dcd94ca63e958a9de39de25be43

latest commit:
03727e7 research(brainvision): implement blocker 2 absolute-path control

working tree before this findings file:
clean

.git/index.lock:
absent
```

Reviewed source material:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_BOUNDED_WINDOWS_PROMOTION_PRIMITIVE_VALIDATION_IMPLEMENTATION_FINDINGS_v0.1.md

docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_ABSOLUTE_PATH_FILERENAMEINFO_ISOLATING_CONTROL_ASSESSMENT_v0.1.md

docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_NARROW_ABSOLUTE_PATH_FILERENAMEINFO_CONTROL_SPECIFICATION_AND_IMPLEMENTATION_AUTHORIZATION_v0.1.md

research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py

research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py

research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
```

Inspected commits:

```text
89f41a5 research(brainvision): implement blocker 2 promotion primitive validation
8af0ab8 docs(research): record blocker 2 promotion primitive findings
9ab500f docs(research): assess blocker 2 absolute-path control
e34d3d4 docs(research): authorize blocker 2 absolute-path control
03727e7 research(brainvision): implement blocker 2 absolute-path control
```

Committed bytes are authoritative for these findings.

## 3. Permanent Boundaries

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

The implementation and these findings do not modify or integrate with:

```text
torment_service/kernel/
production TORMENT memory functionality
live service behavior
prompt or action surfaces
autonomy
identity
truth selection
memory cognition
publication
recovery
replay
```

Current blocker state remains:

```text
BLOCKER-1:
BLOCKER_1_CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_WINDOWS_LOCAL_FIXED_NTFS_TMP_PATH_SCOPE

BLOCKER-2:
OPEN

BLOCKER-3:
CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_STAGE_S3B_V0_3_SCOPE

BLOCKER-4:
OPEN AND SEPARATE
```

These findings do not close BLOCKER-2, reopen BLOCKER-1 or BLOCKER-3, merge
BLOCKER-4 into BLOCKER-2, claim general `FileRenameInfo` support, claim
RootDirectory-relative invalidity, claim rename atomicity, claim rename
durability, claim production readiness, or claim primitive validation beyond
the bounded ephemeral profile.

## 4. Implementation Surface

Implemented:

```text
B. extend the existing validation runner through a separately identified,
fail-closed control mode
```

The committed implementation modified exactly:

```text
research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py

research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py

research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
```

No fourth file was created by the implementation. No publication surface,
recovery surface, replay surface, service file, kernel file, or production
memory file changed. No retained result was created, and no authoritative
retained run was consumed.

The original RootDirectory-relative experiment remains present and distinct.
The prior mode was not overwritten and was not made non-default.

## 5. Mode Separation

The new absolute-path mode has:

```text
explicit mode selection
distinct A1-A8 case identifiers
distinct CONTROL_* vocabulary
distinct control-policy declaration
distinct policy identity
fail-closed mode gating
```

The implementation requires explicit selection of:

```text
ABSOLUTE_PATH_CONTROL
```

The prior RootDirectory-relative validation path remains separately identified.
The prior result vocabulary, policy declaration, and V1-V12/D1-D4 matrix remain
historically distinct.

## 6. Policy Identities

Prior RootDirectory-relative validation-policy identity:

```text
df91a9bcc3c5b37e938a086801dd2bca42f0290533a6cf2682055df475f663f3
```

Absolute-path control-policy identity:

```text
3d9b66a180fabf00c8bb6695c74fc9d69d21cd3ac9335cc5d2dc3a1169417531
```

Both identities independently recompute from their canonical declarations.

Identity method:

```text
SHA256(canonical_json_bytes(policy_declaration))
```

Canonical JSON method:

```text
sorted keys
compact separators
UTF-8
no NaN
stable primitive values
```

Findings:

```text
the prior identity remains unchanged
the new identity is distinct
the prior identity was not reused or overwritten
```

## 7. Native Absolute-Path Contract

The absolute-path control contract is:

```text
SetFileInformationByHandle
FileRenameInfo
FILE_RENAME_INFO
ReplaceIfExists = FALSE
RootDirectory = NULL
canonical fully qualified drive-qualified Win32 DOS absolute destination path
```

The unchanged source-handle contract is:

```text
DELETE

FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE

OPEN_EXISTING

FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT
```

The destination-parent handle remains available for bounded evidence and
admission, but it is not passed through `FILE_RENAME_INFO.RootDirectory`.

No alternate primitive and no copy/delete fallback is used.

## 8. ABI and Buffer Findings

Review and focused tests established:

```text
ReplaceIfExists = FALSE
RootDirectory = NULL
pointer-width-correct HANDLE field
DWORD-width FileNameLength
natural structure alignment
correct FileName offset
exact UTF-16LE absolute-path bytes
FileNameLength equals encoded path byte length
terminating NUL excluded from FileNameLength
buffer lifetime preserved through native call
immediate GetLastError capture
```

Trailing-NUL design:

```text
the absolute-path buffer allocates a trailing UTF-16 NUL
the trailing NUL is not included in FileNameLength
the prior relative-path builder does not allocate that trailing NUL by default
the authorization explicitly permitted this non-semantic padding when verified
```

This trailing-NUL difference is an ABI/buffer construction finding only. It is
not recorded here as a native causal finding.

## 9. Path Derivation and Containment

The absolute destination path is derived from admitted fixture objects rather
than arbitrary user text.

Rejected path or name forms include:

```text
relative paths
current-directory-dependent paths
UNC paths
device paths
NT object-manager paths
volume-GUID paths
extended-length \\?\ paths
cross-volume paths
empty final names
"." and ".."
separator-bearing final names
drive-bearing final names
streams
wildcards
embedded NUL
canonical escape
sibling-prefix confusion
```

Containment is component-aware and is not based only on textual prefix
comparison.

The destination must remain inside:

```text
the admitted fixture root
the admitted destination parent
```

## 10. Fixture and Same-Volume Admission

Bounded fixture profile:

```text
Windows 10/11 workstation
local fixed drive
NTFS
ordinary existing non-reparse fixture root
isolated pytest temporary path
same-volume source and destination
```

Same-volume admission uses handle and volume evidence, including where
available:

```text
volume serial number
filesystem name
drive type
source object identity
destination-parent object identity
canonical fixture-root identity
```

Textual drive-letter equality alone is insufficient.

Reparse points, unsafe roots, repository roots, `.git`, production directories,
profile roots, uncertain admission, and cross-volume destinations are rejected
or fail closed.

## 11. A1-A8 Matrix

Implemented control matrix:

```text
A1:
positive absolute-path same-volume directory rename into an absent final name

A2:
existing destination directory with ReplaceIfExists = FALSE

A3:
existing destination file with ReplaceIfExists = FALSE

A4:
concurrent destination-creation race

A5:
source-to-final object identity continuity after successful transition

A6:
raw native-error characterization against a collision fixture

A7:
invalid or escaping absolute destination rejected before native call

A8:
same-volume mismatch rejected before native call
```

The implementation did not duplicate the entire V1-V12/D1-D4 matrix. It did
not bundle alternate access-right variants, parent-layout variants, or
primitive variants.

## 12. Ephemeral Test Evidence

Exact supplied Windows evidence:

```text
python -m py_compile:
passed

unit suite:
47 passed in 0.36s

focused Windows integration selection:
3 passed in 0.42s
```

Test environment:

```text
conda environment:
torment

shell:
Windows Command Prompt wrapper
```

Temporary roots were of the form:

```text
C:\TORMENT\codex_pytest_tmp_abs_control_019f9c42_*
```

Those temporary roots were removed and rechecked absent.

Classification:

```text
focused ephemeral implementation-test evidence
not an authoritative retained execution
```

## 13. Native Observations

Exact reported ephemeral native observations:

```text
A1:
CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE

A5:
validated source-to-final identity continuity

A2:
ERROR_ALREADY_EXISTS / 183
CONTROL_COLLISION_OBSERVED

A3:
ERROR_ALREADY_EXISTS / 183
CONTROL_COLLISION_OBSERVED

A4:
ERROR_ALREADY_EXISTS / 183
CONTROL_COLLISION_OBSERVED

A6:
ERROR_ALREADY_EXISTS / 183
CONTROL_COLLISION_OBSERVED
raw native error retained

A7:
rejected locally before native invocation

A8:
CONTROL_SKIPPED_FIXTURE_UNAVAILABLE
SECOND_VOLUME_UNAVAILABLE
```

These observations are ephemeral. They were not retained as authoritative
repository evidence.

## 14. A5 Identity Continuity

A5 compares:

```text
source identity before native transition

retained source-handle identity after transition

reopened final-path identity after transition
```

Identity fields are equivalent to:

```text
volume serial number
file index high
file index low
```

Observed for the bounded ephemeral A5 case:

```text
source identity
==
retained-handle identity
==
final identity
```

Content-manifest continuity was also checked.

This identity-continuity observation is not upgraded into:

```text
rename atomicity
rename durability
power-loss persistence
```

## 15. A6 Raw-Error and Collision Interpretation

A6 intentionally used an existing-destination collision fixture.

A6 preserved:

```text
raw native error code:
183

raw symbolic error:
ERROR_ALREADY_EXISTS
```

The result was classified:

```text
CONTROL_COLLISION_OBSERVED
```

This is consistent because:

```text
the fixture intentionally presented an existing destination
ReplaceIfExists was FALSE
the destination was verified preserved
183 is in the defined collision-code set
```

A6 therefore provides both:

```text
raw-error characterization
bounded collision classification
```

A6 does not provide general native-error characterization across all possible
failure states.

## 16. Result Taxonomy

The implementation keeps distinct statuses equivalent to:

```text
CONTROL_VALIDATED_FOR_BOUNDED_EPHEMERAL_PROFILE
CONTROL_REJECTED_ERROR_INVALID_PARAMETER_INDETERMINATE
CONTROL_UNSUPPORTED_EXPLICIT_NATIVE_SIGNAL
CONTROL_ACCESS_REJECTED
CONTROL_COLLISION_OBSERVED
CONTROL_FIXTURE_INVALID
CONTROL_SAME_VOLUME_REJECTED
CONTROL_REPARSE_REJECTED
CONTROL_CONTAINMENT_REJECTED
CONTROL_SKIPPED_FIXTURE_UNAVAILABLE
CONTROL_NATIVE_ERROR_INDETERMINATE
CONTROL_FAULT_INJECTED
```

Exact mappings:

```text
ERROR_INVALID_PARAMETER / 87
->
indeterminate

ERROR_NOT_SUPPORTED / 50
->
unsupported

ERROR_ALREADY_EXISTS / 183
->
collision observed
```

Raw numeric and symbolic native errors are preserved.

## 17. Fault Injection

Bounded synthetic fault points exist across the control flow.

Injected outcomes:

```text
use CONTROL_FAULT_INJECTED
do not continue later steps
do not create retained artifacts
are synthetic harness evidence only
```

Fault-injected results are not native platform evidence.

## 18. Retained-Evidence Boundary

Retained-evidence findings:

```text
no retained validation record was written
no retained result artifact was created
no authoritative one-run was consumed
no publication result was created
no scientific completion was created
```

The in-memory control record contains:

```text
retained_execution = false
```

No silent persistence occurred.

## 19. Supported Claims

Supported:

```text
The implementation selected the authorized extension of the existing validation
runner through a separately identified fail-closed absolute-path control mode.
```

Supported:

```text
The broader source-handle and FileRenameInfo directory operation succeeded
under the admitted bounded Windows fixture using the absolute-path form.
```

Supported:

```text
The absolute-path form can reach no-replace collision behavior under bounded
ephemeral A2, A3, A4, and A6 fixtures, with ERROR_ALREADY_EXISTS / 183 retained
and classified as CONTROL_COLLISION_OBSERVED.
```

Supported:

```text
A5 observed source-to-final identity continuity and content-manifest continuity
within the bounded ephemeral fixture.
```

Supported:

```text
The implementation preserves a distinct policy identity, distinct result
vocabulary, explicit mode gate, and A1-A8 case matrix.
```

## 20. Unsupported Claims

The implementation evidence does not support:

```text
RootDirectory-relative form is invalid
Microsoft documentation is incorrect
general FileRenameInfo support
general FileRenameInfo directory support
rename atomicity
rename durability
power-loss persistence
final-parent flush sufficiency
former-source-parent flush sufficiency
primitive validation beyond the bounded ephemeral profile
primitive falsification
BLOCKER-2 closure
production readiness
real-world Brainvision readiness
```

## 21. Diagnostic Comparison With the Relative Form

Comparative observation:

```text
The prior RootDirectory-relative form returned ERROR_INVALID_PARAMETER / 87,
while the absolute-path form succeeded under the bounded ephemeral fixture.
```

This narrows suspicion toward one or more differences involving:

```text
relative destination resolution
destination-parent handle setup
destination-parent access rights
another parameter interaction distinguishing the two forms
```

It does not prove which difference caused the original `87`.

## 22. BLOCKER-2 Status

```text
BLOCKER-2 remains OPEN.
```

The absolute-path control implementation is a strong diagnostic narrowing
result, not closure.

## 23. Recommended Procedural Next Step

The next procedural step, after this findings document is independently
reviewed and committed, is a separate docs-only decision regarding an exact
authoritative retained single-run authorization.

This findings document does not authorize that run.

This findings document does not consume the one-run gate.

This findings document does not create retained evidence.

## 24. Final Findings Verdict

```text
A. ACCEPT_ABSOLUTE_PATH_CONTROL_IMPLEMENTATION_FINDINGS_WITH_BLOCKER_2_REMAINING_OPEN
```

This verdict does not authorize execution, retained evidence creation,
specification changes, production integration, or BLOCKER-2 closure.
