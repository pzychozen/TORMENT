# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Narrow Absolute-Path FileRenameInfo Control Specification and Implementation Authorization v0.1

## 1. Purpose

document_class = BLOCKER-2 narrow absolute-path FileRenameInfo control specification and implementation authorization

document_version = v0.1

This document specifies and authorizes a future implementation of the bounded
absolute-path `FileRenameInfo` diagnostic control assessed in:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_ABSOLUTE_PATH_FILERENAMEINFO_ISOLATING_CONTROL_ASSESSMENT_v0.1.md
```

This is documentation only. It does not implement the control, does not modify
source or tests, does not run tests, does not execute a native rename, does not
authorize a retained execution, and does not stage, commit, or push.

## 2. Authority and Baseline

Verified baseline:

```text
branch:
main

HEAD:
9ab500fa7b16ae20c52d87debe6c173bc4ea8973

origin/main:
9ab500fa7b16ae20c52d87debe6c173bc4ea8973

latest commit:
9ab500f docs(research): assess blocker 2 absolute-path control

working tree before this file:
clean

.git/index.lock:
absent
```

The assessment commit is present and is the synchronized HEAD:

```text
9ab500fa7b16ae20c52d87debe6c173bc4ea8973
```

Authoritative committed chain reviewed:

```text
5593640 docs(research): research blocker 2 Windows promotion primitive
6c8b113 docs(research): authorize blocker 2 promotion primitive validation
89f41a5 research(brainvision): implement blocker 2 promotion primitive validation
8af0ab8 docs(research): record blocker 2 promotion primitive findings
9ab500f docs(research): assess blocker 2 absolute-path control
```

Committed bytes are authoritative.

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

Do not modify or integrate with:

```text
torment_service/kernel/
production TORMENT memory functionality
live service behavior
prompt surfaces
action surfaces
autonomy
identity
truth selection
memory cognition
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

This specification and authorization does not close BLOCKER-2, reopen
BLOCKER-1 or BLOCKER-3, merge BLOCKER-4 into BLOCKER-2, claim primitive
validation or falsification, claim general FileRenameInfo support or
non-support, claim rename atomicity or durability, or claim production
readiness.

## 4. Authoritative Prior Findings

The accepted committed evidence establishes:

```text
The RootDirectory-relative FileRenameInfo contract was implemented faithfully
and returned ERROR_INVALID_PARAMETER / 87.

The native cause remains indeterminate.

The primitive is neither validated nor falsified.

BLOCKER-2 remains OPEN.
```

Accepted classification:

```text
CORRECTLY_IMPLEMENTED_PRIMITIVE_WITH_CAUSE_INDETERMINATE_NATIVE_REJECTION
```

The implementation findings verdict was:

```text
A. ACCEPT_IMPLEMENTATION_FINDINGS_WITH_BLOCKER_2_REMAINING_OPEN
```

No retained authoritative validation run was created or consumed.

## 5. Assessment Disposition

The accepted absolute-path control assessment concluded:

```text
A. PROCEED_TO_NARROW_ABSOLUTE_PATH_CONTROL_SPECIFICATION
```

That assessment found the control sufficiently documented, bounded, and
isolating for a separate specification, while explicitly recording that it is
not perfectly single-variable because it necessarily also changes:

```text
destination-parent handle participation
destination-parent access-right participation
buffer length
FileNameLength
path canonicalization
drive qualification
separator-containing destination bytes
```

This document preserves that limitation. The control is diagnostic only.

## 6. Exact Control Contract

Authorized future control:

```text
SetFileInformationByHandle
+
FileRenameInfo
+
FILE_RENAME_INFO
+
ReplaceIfExists = FALSE
+
RootDirectory = NULL
+
FileName containing a canonical, fully qualified, drive-qualified Win32 DOS
absolute destination path
+
the same source-directory handle contract
+
the same isolated Windows local-fixed-NTFS fixture profile
```

The only intended experimental change is:

```text
FROM:
non-NULL destination-parent RootDirectory
simple relative final name

TO:
RootDirectory = NULL
canonical absolute destination path
```

No copy/delete fallback is permitted. No alternative primitive is permitted.
The control must not use `FileRenameInfoEx`, `MoveFileW`, `MoveFileExW`,
`Path.rename`, `os.rename`, `shutil.move`, or any production publication
adapter as the operation under validation.

## 7. Authorized Implementation Surface

Selected implementation-surface decision:

```text
B. extend the existing validation runner through a separately identified,
fail-closed control mode
```

Reason:

This is the smallest justified surface because the existing bounded validation
module already contains the fixture containment, identity, native ABI, native
error, and manifest utilities needed for the control. A separate runner would
duplicate the harness and raise review burden. The future implementation must
instead add a separately named absolute-path control mode with a distinct
policy identity, result vocabulary, and focused case matrix.

The only files authorized for future implementation are:

```text
research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
```

No fourth helper, schema, fixture, manifest, runner, retained-result file, or
new test file may be created.

The existing RootDirectory-relative policy declaration, result semantics, and
accepted findings must remain historically distinct. The future implementation
must not reuse, overwrite, or silently broaden the prior validation-policy
identity:

```text
df91a9bcc3c5b37e938a086801dd2bca42f0290533a6cf2682055df475f663f3
```

No production, publication, recovery, replay, kernel, service, memory,
cognition, autonomy, prompt, or action file may be touched.

## 8. Source-Handle Contract

The source directory handle must remain exactly:

```text
desired access:
DELETE

share mode:
FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE

creation disposition:
OPEN_EXISTING

flags:
FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT
```

The future implementation must not widen or change source rights. Any
source-right variant requires a later independent assessment and
authorization.

The source must remain an ordinary existing non-reparse directory admitted
inside the isolated fixture root.

## 9. Destination-Parent Evidence Role

For this control:

```text
FILE_RENAME_INFO.RootDirectory = NULL
```

must be enforced and independently testable.

The destination-parent handle must not be passed as:

```text
FILE_RENAME_INFO.RootDirectory
```

The future implementation may still open the destination parent as an
evidence/admission input for:

```text
canonical containment
reparse rejection
same-volume identity
destination-parent identity
destination absence
post-transition verification
directory-durability dependency
```

The future result schema and tests must distinguish:

```text
destination-parent handle used as evidence/admission input
```

from:

```text
destination-parent handle passed to the native rename structure
```

The latter must be NULL for every native absolute-path control call.

## 10. Absolute-Path Construction

The future implementation must derive the destination path from admitted
fixture objects. It must not accept arbitrary user-supplied absolute path text.

The derived path must be:

```text
fully qualified
drive-qualified
local Win32 DOS form
canonicalized
same-volume
inside the isolated fixture root
component-boundary checked
UTF-16LE encoded
```

The first control must not use:

```text
relative paths
current-directory-dependent paths
UNC paths
device paths
NT object-manager paths
volume-GUID paths
extended-length \\?\ paths
cross-volume destinations
```

Canonicalization requirements:

```text
1. Canonicalize the fixture root and destination parent using resolved
   filesystem paths before deriving the final path.
2. Derive the final path as destination_parent / final_component.
3. Validate the final component before derivation as a single ordinary name,
   rejecting empty names, ".", "..", separators, drive-qualified text, UNC
   text, device namespace text, alternate-stream syntax, wildcards, embedded
   NUL, and traversal.
4. Canonicalize the existing parent strictly.
5. Canonicalize the absent final path through its existing canonical parent.
6. Verify component-boundary containment using path-relative checks, not string
   prefix alone.
7. Verify the final derived path remains inside the fixture root and inside
   the destination parent.
8. Emit Win32 DOS drive-qualified text such as C:\...\dest\final, not an
   extended-length or NT path.
```

Native buffer requirements:

```text
FileName = exact UTF-16LE bytes of the canonical absolute destination path
FileNameLength = exact byte length of FileName
FileNameLength excludes any terminating NUL
no trailing NUL is required or counted
```

The future implementation may allocate a trailing NUL only as non-semantic
buffer padding if tests prove it is not counted in `FileNameLength`, but the
preferred first implementation is no trailing NUL.

## 11. Fixture Admission

Supported profile:

```text
Windows 10/11 workstation
local fixed drive
NTFS
absolute ordinary existing non-reparse fixture root
isolated pytest tmp_path
same-volume source and destination
```

Reject before native execution:

```text
UNC
network drives
removable drives
non-NTFS volumes
reparse points
symlinked fixture ancestors
junctioned fixture ancestors
repo root
.git
production directories
user-profile roots
cross-volume destinations
non-canonical escapes
"." or ".." traversal
```

Fixture-admission result vocabulary must distinguish at least:

```text
CONTROL_FIXTURE_INVALID
CONTROL_SAME_VOLUME_REJECTED
CONTROL_REPARSE_REJECTED
CONTROL_CONTAINMENT_REJECTED
CONTROL_SKIPPED_FIXTURE_UNAVAILABLE
```

Fixture invalidity is not native primitive evidence.

## 12. Same-Volume Verification

Same-volume admission must not rely only on drive-letter text.

Use opened-handle and volume evidence where available:

```text
volume serial number
filesystem name
drive type
source object identity
source-parent object identity
destination-parent object identity
canonical root identity
```

The control must reject a mismatch before the native rename call.

No cross-volume destination and no copy/delete fallback are permitted. A
cross-volume or uncertain-volume fixture is a fail-closed admission result, not
a native promotion result.

## 13. Reparse and Containment Safety

Preserve reparse rejection across:

```text
fixture root
source
source ancestors within the fixture
destination parent
destination-parent ancestors within the fixture
derived absolute destination path
```

The absolute destination path contains separators and a drive qualifier, so the
implementation must prevent escape even when:

```text
case differs
separator form differs
a prefix merely resembles the fixture root
a sibling path shares the same textual prefix
a component contains dots
a reparse point appears between checks
```

Where race-free proof is not available, the implementation must record
fail-closed pre/post evidence and bounded claims rather than claiming
impossible guarantees.

## 14. Native ABI and Buffer Contract

Construct `FILE_RENAME_INFO` exactly as:

```text
ReplaceIfExists = FALSE
RootDirectory = NULL
FileNameLength = exact UTF-16LE byte length of the canonical absolute path
FileName = variable-length UTF-16LE path bytes
```

Preserve:

```text
natural structure alignment
pointer-width-correct HANDLE field
DWORD-width FileNameLength
buffer lifetime through the native call
immediate GetLastError capture on failure
source-handle lifetime
destination-parent evidence-handle lifetime
```

Do not use:

```text
incorrect packing
absolute-path NUL included in FileNameLength
temporary pointer storage
RootDirectory sentinel values
non-zero RootDirectory
```

Unit tests must prove that the absolute-path buffer writes a NULL
`RootDirectory`, writes `ReplaceIfExists = FALSE`, stores the exact UTF-16LE
path bytes, and excludes any terminator from `FileNameLength`.

## 15. Control Cases

Minimal diagnostic control matrix:

| Case | Purpose |
|---|---|
| A1 | Positive absolute-path same-volume directory rename into an absent final name. |
| A2 | Existing destination directory with `ReplaceIfExists = FALSE`. |
| A3 | Existing destination file with `ReplaceIfExists = FALSE`. |
| A4 | Concurrent destination-creation race. |
| A5 | Source-to-final object identity continuity after successful transition. |
| A6 | Raw native error characterization for every failed native control call. |
| A7 | Invalid or escaping absolute destination rejected before native call. |
| A8 | Same-volume mismatch rejected before native call. |

Do not duplicate the full prior V1-V12/D1-D4 matrix unless a later docs-only
authorization justifies each added case.

Do not bundle:

```text
source-right variants
destination-parent-right variants
same-parent versus cross-parent variants
FileRenameInfoEx
MoveFileW
MoveFileExW
```

## 16. Result Taxonomy

The future implementation must define fail-closed control vocabulary that
keeps at least these outcomes distinct:

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

Required mappings:

```text
ERROR_INVALID_PARAMETER / 87
->
indeterminate

ERROR_NOT_SUPPORTED / 50
->
unsupported
```

Do not classify all failures as unsupported. Preserve raw numeric native error
codes and symbolic names where known.

## 17. Diagnostic Interpretation

If the absolute-path control succeeds:

```text
It supports that the broader source-handle and FileRenameInfo directory
operation can succeed under the admitted fixture using the absolute-path form.

It narrows suspicion toward one or more differences involving relative
destination resolution, destination-parent handle setup or rights, or another
difference between the forms.
```

It does not prove which individual difference caused the original `87`.

If the absolute-path control also returns `87`:

```text
The cause remains unresolved and may be broader than RootDirectory-relative
destination resolution.
```

It does not establish:

```text
FileRenameInfo unsupported
directory rename unsupported
primitive falsification
Microsoft documentation error
BLOCKER-2 closure
```

All other native errors remain distinct and fail closed until separately
interpreted.

## 18. Durability Boundary

The control's primary purpose is to diagnose the native rename form, not to
close durability.

If the native rename succeeds, the future implementation may define
post-transition calls using the already accepted BLOCKER-1 directory-durability
adapter. Any such calls must preserve the distinction between:

```text
native transition success
directory-entry durability evidence
scientific completion
```

Do not claim:

```text
power-loss persistence
documented rename durability
final-parent flush sufficiency
former-source-parent flush sufficiency
atomicity
BLOCKER-2 closure
```

D-class durability investigation remains gated behind successful transition
and must be separately interpreted.

## 19. Fault Injection

Bounded synthetic fault points must verify fail-closed behaviour at least:

```text
after fixture admission
after source handle open
after destination-parent evidence collection
after absolute-path derivation
after native buffer construction
immediately before native call
immediately after native success
before post-transition verification
```

Fault injection is harness evidence only. It must not be treated as native
platform evidence.

## 20. Test Authority

Future implementation may run only:

```text
focused ephemeral unit tests
focused ephemeral Windows integration tests
relevant BLOCKER-1 regressions where needed
```

Future implementation is not authorized to run:

```text
authoritative retained one-run execution
retained result artifacts
general validation matrix execution
production execution
publication execution
recovery execution
```

The exact authoritative retained run must remain separately gated after
implementation findings.

## 21. Policy Identity

The future implementation must define a new absolute-path control-policy
identity. It must bind at least:

```text
control version
implementation file identities
exact native contract
RootDirectory = NULL
absolute-path representation
fixture-admission rules
same-volume rules
containment rules
reparse policy
case matrix
result taxonomy
fault points
test authority
execution prohibition
```

Policy identity method:

```text
control_policy_sha256 =
SHA256(canonical_json_bytes(control_policy_declaration))
```

Canonical JSON must use deterministic key ordering, compact separators, UTF-8
encoding, and no NaN values.

Do not reuse or overwrite:

```text
df91a9bcc3c5b37e938a086801dd2bca42f0290533a6cf2682055df475f663f3
```

That identity belongs to the prior RootDirectory-relative validation policy.
The new control must have a distinct policy schema identity, distinct policy
SHA-256, distinct result vocabulary, and distinct case identifiers.

## 22. Explicitly Prohibited Actions

The future implementation authorization does not permit:

```text
authoritative retained execution
retained result artifacts
production publication
publication adapter modification
publication grammar modification
recovery modification
replay modification
service or kernel modification
production memory modification
source-right changes
destination-parent-right variants
same-parent/cross-parent variants
FileRenameInfoEx
MoveFileW
MoveFileExW
live visual capture
real gameplay or video execution
BLOCKER-2 closure claim
primitive validation claim beyond bounded ephemeral profile
primitive falsification claim
staging
committing
pushing
lock deletion
```

This present docs-only task also did not perform any of those actions.

## 23. Implementation Acceptance Criteria

The future implementation may be accepted only if:

```text
1. only the three authorized files are modified
2. no fourth helper, schema, runner, test file, or retained result is created
3. the original RootDirectory-relative logical policy remains distinct
4. the new absolute-path control policy identity is distinct
5. RootDirectory is NULL in the native buffer and unit-tested
6. ReplaceIfExists remains FALSE
7. source handle rights remain DELETE only
8. source share mode remains FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE
9. source open flags remain FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT
10. the destination path is derived from admitted fixture objects
11. arbitrary user-supplied absolute text is rejected
12. the absolute path is canonical, fully qualified, drive-qualified Win32 DOS form
13. UNC, device, NT, volume-GUID, and extended-length paths are rejected for this first control
14. containment is component-boundary checked, not string-prefix only
15. same-volume evidence uses handle/object and volume evidence where available
16. reparse points are rejected across the specified fixture surface
17. A1-A8 cases are implemented without bundling other controls
18. ERROR_INVALID_PARAMETER / 87 remains indeterminate
19. ERROR_NOT_SUPPORTED / 50 remains unsupported
20. focused tests cannot produce false positive retained or production claims
21. no native execution is represented as authoritative retained execution
22. no production, publication, recovery, replay, service, kernel, memory, cognition, autonomy, prompt, or action surface is changed
```

Any need to expand file surface, alter source rights, use an extended-length or
NT path in the first control, add a retained result, or test an alternative
primitive is a stop condition requiring renewed docs-only authorization.

## 24. Authorization Verdict

Authorization verdict:

```text
A. AUTHORIZE_NARROW_ABSOLUTE_PATH_CONTROL_IMPLEMENTATION
```

This verdict authorizes only future implementation of the narrowly specified
absolute-path control and focused ephemeral testing within the exact authorized
file surface.

This verdict does not authorize:

```text
authoritative retained one-run execution
retained result artifacts
production execution
publication execution
recovery execution
replay execution
BLOCKER-2 closure
primitive validation or falsification
source-right variants
destination-parent-right variants
alternative primitives
staging
committing
pushing
```
