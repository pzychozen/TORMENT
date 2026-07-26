# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Absolute-Path FileRenameInfo Isolating Control Assessment v0.1

## 1. Purpose

document_class = BLOCKER-2 absolute-path FileRenameInfo isolating control assessment

document_version = v0.1

assessment_scope =
docs-only assessment of the smallest justified diagnostic control after the
committed RootDirectory-relative FileRenameInfo validation implementation
returned ERROR_INVALID_PARAMETER / 87.

This document assesses whether the next bounded diagnostic control should
change only the destination-name resolution mechanism from:

```text
non-NULL destination-parent RootDirectory
+
simple relative final name
```

to:

```text
RootDirectory = NULL
+
full absolute same-volume destination path
```

This document does not implement, execute, authorize execution, create tests,
create retained evidence, stage, commit, push, or modify production or
publication surfaces.

## 2. Authority and Baseline

Baseline verified for this assessment:

```text
branch:
main

HEAD:
8af0ab86f3b23847ae9838bda84b8631f512f30f

origin/main:
8af0ab86f3b23847ae9838bda84b8631f512f30f

latest commit:
8af0ab8 docs(research): record blocker 2 promotion primitive findings

working tree before this assessment file:
clean

.git/index.lock:
absent
```

The reviewed committed BLOCKER-2 chain was:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SAME_VOLUME_NO_REPLACE_PROMOTION_AND_FINAL_OWNERSHIP_ASSESSMENT_v0.1.md

docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_WINDOWS_SAME_VOLUME_NO_REPLACE_DIRECTORY_PROMOTION_PRIMARY_SOURCE_PRIMITIVE_RESEARCH_v0.1.md

docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_BOUNDED_WINDOWS_SAME_VOLUME_NO_REPLACE_DIRECTORY_PROMOTION_PRIMITIVE_VALIDATION_AUTHORIZATION_v0.1.md

docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_BOUNDED_WINDOWS_PROMOTION_PRIMITIVE_VALIDATION_IMPLEMENTATION_FINDINGS_v0.1.md

research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py

research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py

research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
```

The inspected commit chain was:

```text
5593640 docs(research): research blocker 2 Windows promotion primitive
6c8b113 docs(research): authorize blocker 2 promotion primitive validation
89f41a5 research(brainvision): implement blocker 2 promotion primitive validation
8af0ab8 docs(research): record blocker 2 promotion primitive findings
```

Committed bytes are authoritative for repository evidence.

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

This assessment does not modify or integrate with:

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

This assessment opens no:

```text
live visual capture
real gameplay or video execution
production publication
production recovery
general live-test lanes
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

BLOCKER-1 and BLOCKER-3 are not reopened. BLOCKER-4 is not merged into
BLOCKER-2.

## 4. Current Committed Finding

The committed BLOCKER-2 implementation findings establish:

```text
The exact RootDirectory-relative FileRenameInfo contract was implemented
faithfully and returned ERROR_INVALID_PARAMETER / 87.

The committed classification is:
PRIMITIVE_VALIDATION_INDETERMINATE

The selected primitive is:
neither validated nor falsified

BLOCKER-2 remains:
OPEN
```

The independent static review found no known:

```text
ctypes ABI defect
structure-layout defect
variable-buffer construction defect
```

That review did not establish:

```text
all destination-parent access requirements
all native parameter requirements
RootDirectory-relative user-mode support
general FileRenameInfo directory support
rename atomicity
rename durability
```

No retained authoritative validation run was created or consumed.

## 5. Proposed Isolating Control

Proposed control:

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
FileName containing the full absolute same-volume destination path
+
the same source-directory handle contract
+
the same isolated local-fixed-NTFS fixture profile
```

The intended changed variable is:

```text
destination-name resolution mechanism
```

The control removes the load-bearing destination-parent handle from
`FILE_RENAME_INFO.RootDirectory` and gives the rename operation a full absolute
destination path in `FILE_RENAME_INFO.FileName`.

All other meaningful variables should remain fixed unless a later specification
records a precise, separately justified impossibility.

## 6. Primary-Source Windows Contract Review

Primary-source findings:

| Classification | Finding |
|---|---|
| documented | `SetFileInformationByHandle` accepts `FileRenameInfo` as a valid information class and uses a `FILE_RENAME_INFO` buffer for that class [MS-01] [MS-02]. |
| documented | `SetFileInformationByHandle` reports failure through a zero return and extended error information through `GetLastError` [MS-01]. |
| documented | `FILE_RENAME_INFO.ReplaceIfExists = FALSE` means the operation returns an error if the target exists [MS-03]. |
| documented | The Win32 `FILE_RENAME_INFO.RootDirectory` field is commonly NULL, and a non-NULL handle is tied to relative-name resolution [MS-03]. |
| documented | The Win32 `FILE_RENAME_INFO.FileName` value may be an absolute path containing drive, directory, and filename [MS-03]. |
| documented | The WDK `FILE_RENAME_INFORMATION` page says that when `RootDirectory` is NULL and the file is moved to a different directory, `FileName` specifies the full pathname [MS-04]. |
| documented | The WDK page separately lists a fully qualified file name with `RootDirectory` NULL as the form that changes both name and location [MS-04]. |
| documented | The WDK page lists the relative-name form as the one where `RootDirectory` contains the target-directory handle and the file name itself must be simple [MS-04]. |
| documented | A file or directory rename cannot move the object to another volume, and `ReplaceIfExists = FALSE` fails when the target exists [MS-04]. |
| documented | Renaming requires DELETE access to the source and appropriate access to create the new entry in the new parent directory [MS-04]. |
| documented | Opening a directory with `CreateFileW` requires `FILE_FLAG_BACKUP_SEMANTICS`; `FILE_FLAG_OPEN_REPARSE_POINT` opens the reparse point itself rather than normal reparse processing [MS-05]. |
| documented | Windows path documentation describes drive-qualified local paths and documents extended-length `\\?\` paths as a separate path-prefix convention [MS-06] [MS-07]. |
| documented | Volume serial number and file index can be compared to determine whether handles identify the same file on a single computer; NTFS keeps the same file ID until deletion [MS-08]. |
| empirically observed | The committed RootDirectory-relative implementation returned ERROR_INVALID_PARAMETER / 87 in the supplied focused evidence and was accepted as indeterminate. |
| inferred | The absolute-path form is a documented and relevant diagnostic control for separating RootDirectory-relative resolution from broader FileRenameInfo behavior. |
| proposed | The next control should use `RootDirectory = NULL` and a full absolute same-volume destination path while preserving the source handle and fixture profile. |
| unresolved | Microsoft documentation reviewed here does not guarantee rename atomicity, post-rename durability, exact error mapping for all BLOCKER-2 cases, or the exact cause of the observed 87. |

The primary-source contract is sufficient to assess the proposed control as a
valid next diagnostic subject. It is not sufficient to claim validation,
falsification, atomicity, durability, or BLOCKER-2 closure.

## 7. Absolute-Path Representation Analysis

The narrowest first absolute-path representation should be:

```text
canonical fully qualified Win32 DOS path
drive-qualified local path
example shape: C:\...\fixture\dest\final
```

Rationale:

1. The Win32 `FILE_RENAME_INFO` page explicitly admits an absolute path in
   drive, directory, and filename form [MS-03].
2. The WDK `FILE_RENAME_INFORMATION` page admits a fully qualified file name
   with `RootDirectory = NULL` for moving to a different directory [MS-04].
3. The bounded fixture path is expected to be short and ordinary, so the
   first control does not need the extended-length `\\?\` prefix.
4. The extended-length prefix is documented for Windows API path handling, but
   adding it would introduce a second namespace/path-normalization variable
   into the first isolating control [MS-07].

The assessment therefore does not select:

```text
NT native path
UNC path
device namespace path
relative current-directory path
volume GUID path
extended-length \\?\ path as the first control form
```

A later specification may record an explicit fallback or separate follow-up for
extended-length or native namespace forms only if the bounded Win32 DOS
absolute-path control leaves that question unresolved. This assessment does
not authorize that fallback.

## 8. Variable-Isolation Analysis

The proposed control is sufficiently isolating for a next diagnostic
specification because it changes the path-resolution mode directly implicated
by the committed indeterminate result.

Primary changed variable:

```text
RootDirectory-relative simple-name resolution
->
RootDirectory = NULL full-absolute-path resolution
```

Unavoidable secondary differences:

| Difference | Effect on isolation |
|---|---|
| buffer size | The `FILE_RENAME_INFO` buffer must hold the full destination path rather than a simple name. This is unavoidable and should be tested at the builder layer. |
| path encoding length | `FileNameLength` grows and remains byte length of UTF-16LE data without relying on a terminating NUL. This weakens isolation only if buffer construction changes beyond length/content. |
| path normalization | A canonical full path must be derived and verified before buffer construction. This adds containment risk that must be explicitly bounded. |
| separator handling | The absolute path necessarily contains backslash separators. This reverses the prior final-name rejection rule only for a validated full path, not for arbitrary names. |
| drive qualification | The destination path must carry a drive-qualified absolute form to satisfy the documented Win32 absolute-path shape. |
| destination-parent handle absence in native call | The parent is still opened for admission evidence, but it is no longer passed as `RootDirectory`. This is the intended isolating difference. |
| destination-parent access-right absence from native parameter | The future native call cannot test the same destination-parent handle access path, so a successful result would narrow suspicion to the old parent-handle path but would not prove which parent-handle property mattered. |

Conclusion:

```text
The control is clean enough to isolate RootDirectory-relative destination
resolution from full-absolute-path destination resolution. It cannot isolate
destination-parent handle presence separately from destination-parent
access-rights or relative-name resolution, because those variables are bound
together by the documented alternative form.
```

## 9. Source-Handle and Access-Right Analysis

The source handle should remain exactly:

```text
DELETE
FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE
OPEN_EXISTING
FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT
```

Reason:

The observed 87 was produced after static review found no known ABI or buffer
defect in the committed RootDirectory-relative implementation. Widening source
rights at the same time as changing destination-path form would add a second
major explanatory variable.

The reviewed Microsoft sources support DELETE as a rename requirement and
`FILE_FLAG_BACKUP_SEMANTICS` as required to obtain a directory handle [MS-04]
[MS-05]. They do not provide a new reason in this assessment to alter the
source access contract for the first diagnostic control.

The destination parent may still be opened for:

```text
containment admission
reparse rejection
same-volume identity
destination absence verification
post-operation identity analysis
```

but the opened destination-parent handle must not be passed as
`FILE_RENAME_INFO.RootDirectory` in this control.

## 10. Same-Volume and Fixture-Admission Analysis

The same intended fixture profile should be preserved:

```text
Windows 10/11 workstation
local fixed NTFS
absolute ordinary existing non-reparse fixture root
isolated pytest tmp_path
same-volume source and destination
```

Same-volume evidence should be established before the call by:

```text
opened source or source-parent identity
opened destination-parent identity
volume serial evidence
filesystem name evidence
drive type evidence
canonical fixture containment
```

Path-root string comparison is not sufficient as the only same-volume proof.
It may be retained as a diagnostic check, but the admission evidence should
prefer handle/object and volume information.

The final absolute destination path must be:

```text
inside the admitted fixture root
inside the admitted destination parent
absent before the positive control
on the same volume as the source
ordinary and non-reparse through all existing parent components
```

No network, removable, non-NTFS, UNC, repository, user document, production,
publication, service, kernel, memory, cognition, or live path is admitted.

## 11. Reparse and Containment Analysis

The control can preserve the current reparse and containment boundaries if a
future specification requires all of the following before native execution:

```text
canonical fixture root admission
source path inside fixture root
destination parent inside fixture root
final absolute path inside destination parent
final absolute path inside fixture root
source non-reparse
destination parent non-reparse
all existing destination ancestors non-reparse
destination absent for positive case
no .git path component
no repository-root path
no production path
no user-profile root path
no UNC path
no device namespace path
no traversal through . or ..
```

Absolute-path handling creates new containment and canonicalization risks
because the value placed in `FILE_RENAME_INFO.FileName` contains multiple path
components and a drive qualifier. Those risks are manageable only if the
future specification treats the absolute path as a derived, canonicalized,
fixture-bound value rather than user-supplied text.

## 12. Diagnostic Outcome Matrix

| Native observation | Assessment classification | What it would support | What it would not support |
|---|---|---|---|
| absolute-path control succeeds | diagnostic support | Narrows suspicion toward RootDirectory-relative usage, destination-parent handle setup, destination-parent access rights, or another relative-name-resolution requirement. | Primitive validation, BLOCKER-2 closure, production readiness, atomicity, durability, general Windows support. |
| absolute-path control also returns ERROR_INVALID_PARAMETER / 87 | indeterminate diagnostic support | Suggests a broader unresolved issue involving directory rename behavior, source-handle contract, access rights, path encoding, native parameter requirements, or another implementation-independent constraint. | FileRenameInfo falsification, RootDirectory-relative falsification, Microsoft documentation error, BLOCKER-2 closure. |
| ERROR_NOT_SUPPORTED / 50 | unsupported observation | Indicates the request was not supported in the observed profile or stack and should remain distinct from 87. | Cause of the prior 87, validation, closure. |
| ERROR_ACCESS_DENIED / 5 | access-related observation | Suggests an access-right or security context issue requiring separate assessment. | Primitive validation or falsification. |
| ERROR_NOT_SAME_DEVICE / 17 | fixture or same-volume failure unless intentionally cross-volume | Indicates same-volume admission failed or the path resolved across volumes. | No-replace behavior. |
| ERROR_FILE_EXISTS / 80 or ERROR_ALREADY_EXISTS / 183 | collision-related observation in collision cases | May characterize no-replace target-exists behavior only after fixture state is proven. | Positive promotion success. |
| ERROR_INVALID_NAME / 123 | path-syntax or representation observation | Suggests selected absolute path representation is unacceptable or malformed. | FileRenameInfo directory support in general. |
| sharing or lock errors | environmental or fixture-dependent observation | Indicates open-handle interference or fixture quiescence issue. | RootDirectory-relative cause by itself. |
| unknown native error | indeterminate fail-closed observation | Preserves numeric native evidence for later assessment. | Any positive claim. |

Distinct native errors must not be collapsed into one classification.

## 13. Alternatives Considered

| Alternative | Assessment |
|---|---|
| destination-parent access-right variants | Potentially useful only after the absolute-path control. They directly change access rights and keep the RootDirectory-relative path, so they are less clean as the first isolating control. |
| source access-right variants | Not preferred first because they change the source-handle contract and would obscure whether destination resolution was the cause of 87. |
| same-parent versus cross-parent variants | Not preferred first because they change fixture topology and leave the absolute versus relative question unresolved. |
| FileRenameInfoEx | Not preferred because it changes information class and imports flag semantics, version behavior, and POSIX/replacement risks. |
| MoveFileW | Not preferred because it changes API family and removes source-handle binding. |
| MoveFileExW with zero flags | Not preferred because it changes API family and brings a larger flag surface even when zero flags are used. |

The absolute-path `FileRenameInfo` control is the cleanest first isolating
experiment because it preserves the API, information class, replacement policy,
source-handle contract, and fixture profile while changing the documented
destination-name resolution form.

This assessment does not bundle any alternative into the next authorization.

## 14. Claims the Control Could Support

If separately specified, implemented, and executed under the bounded fixture
profile, the control could support:

```text
whether RootDirectory = NULL plus a full absolute same-volume destination path
executes differently from the committed RootDirectory-relative form

whether the previous ERROR_INVALID_PARAMETER / 87 narrows toward
RootDirectory-relative resolution or remains broader

whether no-replace collision cases under the absolute-path form reach native
collision behavior

whether source-to-final identity continuity becomes observable under the
absolute-path form

whether D1-D4 post-transition durability investigation becomes reachable after
a successful native transition
```

Any such support would remain bounded, synthetic, offline, Windows-only,
local-fixed-NTFS-profile-bound, and non-production.

## 15. Claims the Control Could Not Support

The control could not support:

```text
primitive validation by itself
primitive falsification by itself
BLOCKER-2 closure
production readiness
general Windows filesystem durability
documented rename atomicity
documented rename durability
general FileRenameInfo support or non-support
general RootDirectory-relative validity or invalidity
Microsoft documentation correctness or incorrectness
real-world Brainvision readiness
strong order sensitivity
publication completion
recovery or replay correctness
```

The control is diagnostic. It is not a production specification and not a
closure mechanism.

## 16. Relationship to Retained Authoritative Execution

The absolute-path control should first receive:

```text
ephemeral implementation tests only
```

before any separately authorized:

```text
authoritative retained one-run execution
```

Required procedural separation:

```text
this docs-only assessment
separate docs-only narrow control specification/implementation authorization
implementation and focused ephemeral tests only
independent implementation findings
separate one-run retained execution authorization, if still justified
authoritative retained execution, if explicitly authorized later
```

This assessment authorizes none of those later execution or implementation
steps.

## 17. Assessment Conclusion

Primary assessment outcome:

```text
A. PROCEED_TO_NARROW_ABSOLUTE_PATH_CONTROL_SPECIFICATION
```

Reason:

Microsoft primary documentation supports the central control contract:

```text
SetFileInformationByHandle
FileRenameInfo
FILE_RENAME_INFO
ReplaceIfExists = FALSE
RootDirectory = NULL
full absolute or fully qualified destination path
same-volume file-or-directory rename rule
```

The proposed control is sufficiently bounded and isolating to justify a
separate specification because it keeps the API, information class,
replacement policy, source handle, and fixture profile fixed while changing
the documented destination-resolution form.

Residual ambiguity remains around exact path representation details, error
mapping, directory behavior on the authorized profile, and durability. Those
ambiguities are precisely why the next step should be a narrow specification
and not execution or closure.

Rejected outcomes:

```text
B. REQUIRE_ADDITIONAL_PRIMARY_SOURCE_RESEARCH_BEFORE_SPECIFICATION
```

Rejected because the reviewed Microsoft sources are sufficient to establish
that `RootDirectory = NULL` with a full absolute or fully qualified destination
path is a documented rename-information form.

```text
C. REJECT_ABSOLUTE_PATH_CONTROL_AS_NON_ISOLATING_OR_INVALID
```

Rejected because the control is valid enough and isolates the smallest
meaningful variable available after the committed RootDirectory-relative 87.

## 18. Final Disposition

Final disposition:

```text
A. PROCEED_TO_NARROW_ABSOLUTE_PATH_CONTROL_SPECIFICATION
```

Exact next procedural step:

```text
Prepare a separate docs-only narrow absolute-path FileRenameInfo control
specification and implementation authorization.
```

That next document should not authorize execution, should not create retained
results, should not modify production/publication/recovery/replay surfaces,
and should not bundle destination-parent access variants, source-right
variants, same-parent/cross-parent variants, FileRenameInfoEx, MoveFileW, or
MoveFileExW controls.

## 19. Microsoft Source Register

MS-01

```text
document title:
SetFileInformationByHandle function (fileapi.h)
publisher:
Microsoft
retrieval date:
2026-07-26
URL:
https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfileinformationbyhandle
claims used:
FileRenameInfo is a valid information class for SetFileInformationByHandle;
the matching buffer type is FILE_RENAME_INFO; failures report extended error
information through GetLastError; appropriate file-handle access is required.
```

MS-02

```text
document title:
FILE_INFO_BY_HANDLE_CLASS enumeration (minwinbase.h)
publisher:
Microsoft
retrieval date:
2026-07-26
URL:
https://learn.microsoft.com/en-us/windows/win32/api/minwinbase/ne-minwinbase-file_info_by_handle_class
claims used:
FileRenameInfo changes the file name and is used only with
SetFileInformationByHandle.
```

MS-03

```text
document title:
FILE_RENAME_INFO structure (winbase.h)
publisher:
Microsoft
retrieval date:
2026-07-26
URL:
https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info
claims used:
ReplaceIfExists false returns an error if the target exists; RootDirectory is
NULL in the common case and may hold a directory handle for relative names;
FileNameLength is a byte length; FileName may contain an absolute path with
drive, directory, and filename.
```

MS-04

```text
document title:
FILE_RENAME_INFORMATION structure (ntifs.h)
publisher:
Microsoft
retrieval date:
2026-07-26
URL:
https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information
claims used:
With RootDirectory NULL and a move to a different directory, FileName supplies
the full pathname; a fully qualified file name with RootDirectory NULL changes
name and location; a relative file name uses RootDirectory and must be simple;
file or directory rename is within-volume only; ReplaceIfExists false fails if
the target exists; DELETE source access and appropriate new-parent access are
required.
```

MS-05

```text
document title:
CreateFileW function (fileapi.h)
publisher:
Microsoft
retrieval date:
2026-07-26
URL:
https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
claims used:
FILE_FLAG_BACKUP_SEMANTICS is required to open a directory handle;
FILE_FLAG_OPEN_REPARSE_POINT opens the reparse point itself rather than normal
reparse processing; OPEN_EXISTING is the directory-open mode for this use.
```

MS-06

```text
document title:
Naming Files, Paths, and Namespaces
publisher:
Microsoft
retrieval date:
2026-07-26
URL:
https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file
claims used:
Windows file and directory paths use backslash-separated components and may
include a volume designator; directory naming rules generally follow file
naming rules unless otherwise specified.
```

MS-07

```text
document title:
Maximum Path Length Limitation
publisher:
Microsoft
retrieval date:
2026-07-26
URL:
https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation
claims used:
Windows API path handling has ordinary drive-qualified local paths and a
separate extended-length `\\?\` prefix convention; the prefix requests minimal
path modification and changes separator/dot handling expectations.
```

MS-08

```text
document title:
BY_HANDLE_FILE_INFORMATION structure (fileapi.h)
publisher:
Microsoft
retrieval date:
2026-07-26
URL:
https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-by_handle_file_information
claims used:
Volume serial number plus file index can determine whether handles identify
the same file on one computer; NTFS keeps the same file ID until deletion.
```

MS-09

```text
document title:
System Error Codes (0-499)
publisher:
Microsoft
retrieval date:
2026-07-26
URL:
https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-
claims used:
numeric meanings for ERROR_ACCESS_DENIED / 5, ERROR_NOT_SAME_DEVICE / 17,
ERROR_NOT_SUPPORTED / 50, ERROR_FILE_EXISTS / 80, ERROR_INVALID_PARAMETER / 87,
ERROR_INVALID_NAME / 123, ERROR_DIR_NOT_EMPTY / 145, and related native
failure observations.
```
