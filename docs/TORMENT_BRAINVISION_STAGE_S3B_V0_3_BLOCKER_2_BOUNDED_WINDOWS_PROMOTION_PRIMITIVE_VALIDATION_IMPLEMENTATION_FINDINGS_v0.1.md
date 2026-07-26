# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Bounded Windows Promotion Primitive Validation Implementation Findings v0.1

## 1. Purpose

document_class = BLOCKER-2 bounded Windows promotion primitive validation implementation findings

document_version = v0.1

findings_scope =
docs-only review of the committed research-only implementation for the
BLOCKER-2 bounded Windows same-volume no-replace directory promotion primitive
validation harness.

implementation commit:

```text
89f41a5a7d3fae9e19cb753cd30f7f0ce350d012
```

implementation commit subject:

```text
research(brainvision): implement blocker 2 promotion primitive validation
```

This document records implementation findings only. It creates no retained
authoritative validation result, consumes no separately gated authoritative
one-run validation authorization, authorizes no execution, authorizes no
specification, authorizes no integration, and does not close BLOCKER-2.

## 2. Authority and Baseline

The implementation baseline verified for these findings is:

```text
branch      = main
HEAD        = 89f41a5a7d3fae9e19cb753cd30f7f0ce350d012
origin/main = 89f41a5a7d3fae9e19cb753cd30f7f0ce350d012
latest      = 89f41a5 research(brainvision): implement blocker 2 promotion primitive validation
working tree before findings file = clean
.git/index.lock = absent
```

The implementation remained:

```text
synthetic
offline
Windows-only
local-fixed-NTFS-profile-bound
quarantined
non-production
non-publication-integrated
```

The reviewed committed source material was:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SAME_VOLUME_NO_REPLACE_PROMOTION_AND_FINAL_OWNERSHIP_ASSESSMENT_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_WINDOWS_SAME_VOLUME_NO_REPLACE_DIRECTORY_PROMOTION_PRIMARY_SOURCE_PRIMITIVE_RESEARCH_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_BOUNDED_WINDOWS_SAME_VOLUME_NO_REPLACE_DIRECTORY_PROMOTION_PRIMITIVE_VALIDATION_AUTHORIZATION_v0.1.md
research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
```

Commit inspection found that commit `89f41a5a7d3fae9e19cb753cd30f7f0ce350d012`
added exactly the three authorized implementation files and no publication or
production wiring.

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
prompt surfaces
action surfaces
autonomy
identity
truth selection
memory cognition
```

No live visual capture, real gameplay or video execution, production
publication, production recovery, or general live-test lane is opened.

Publication remains a projection of the authoritative scientific result.

The authoritative durable scientific result remains:

```text
verified IMMUTABLE_SCIENTIFIC_BUNDLE
+
linked valid SCIENTIFIC_COMPLETION
```

Promotion and durability evidence remain linked platform evidence, not
scientific completion evidence.

Current blocker state is preserved:

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

## 4. Reviewed Implementation Surface

The implementation commit created exactly:

```text
research/brainvision/validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_v0_1.py
research/brainvision/test_validate_windows_same_volume_no_replace_promotion_integration_v0_1.py
```

No existing file was modified by the implementation commit.

No fourth helper or schema module was created.

No publication adapter, publication grammar, recovery path, replay path,
service, kernel, or production surface was modified.

No retained authoritative result was created.

The separately gated authoritative one-run validation authorization was not
created or consumed.

## 5. Implemented Native Contract

The committed implementation targets this native contract:

```text
SetFileInformationByHandle
FileRenameInfo
FILE_RENAME_INFO
ReplaceIfExists = FALSE
non-NULL destination-parent RootDirectory handle
simple relative final directory name
source directory opened by handle
no copy/delete fallback
```

The committed source-handle configuration is:

```text
DELETE
FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE
OPEN_EXISTING
FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT
```

The destination parent is opened separately and passed through:

```text
FILE_RENAME_INFO.RootDirectory
```

The following are not used as the promotion operation:

```text
RootDirectory = NULL
absolute destination path
MoveFileW
MoveFileExW
FileRenameInfoEx
ReplaceFileW
Path.rename
os.rename
shutil.move
copy/delete fallback
```

Ordinary filesystem APIs appear only for isolated fixture construction,
inspection, or bounded test scaffolding. They are not the promotion primitive
under validation.

## 6. ABI and Static-Review Findings

The independent static review found no known ctypes ABI, structure-layout, or
variable-buffer construction defect in the committed implementation.

That review covered:

```text
FileRenameInfo enum value
SetFileInformationByHandle prototype
HANDLE width
BOOL handling
FILE_RENAME_INFO layout
natural alignment
RootDirectory offset and pointer width
FileNameLength offset and width
FileName offset
variable-length buffer allocation
UTF-16LE encoding
absence of a terminating-NUL requirement in FileNameLength
buffer lifetime
pointer lifetime
source-handle lifetime
destination-parent-handle lifetime
immediate GetLastError capture
simple relative final-name construction
```

This is a bounded static-review finding. It does not mathematically or
universally prove the ABI correct, and it does not establish every possible
destination-parent access or native parameter requirement.

## 7. Windows Focused-Test Evidence

The supplied implementation evidence records an initial fixture setup failure:

```text
WinError 5
C:\Users\Notandi\AppData\Local\Temp\pytest-of-Notandi
```

Classification:

```text
pytest temporary-directory environment failure
not promotion-primitive evidence
```

The supplied evidence records the corrected temporary-root configuration:

```text
TMP=C:\TORMENT\codex_pytest_tmp
TEMP=C:\TORMENT\codex_pytest_tmp
```

The supplied evidence records that the temporary scratch root was removed after
use.

Exact focused evidence supplied for this findings review:

```text
focused run 1:
30 passed in 0.48s

focused run 2:
30 passed in 0.53s

relevant BLOCKER-1 regression:
23 passed in 0.30s
```

This evidence is classified as:

```text
focused ephemeral implementation-test evidence
not an authoritative retained validation execution
```

No retained repository result artifact contains this as an authoritative
validation execution.

## 8. Native Validation Observations

The supplied focused evidence records that the exact authorized
RootDirectory-relative contract returned:

```text
ERROR_INVALID_PARAMETER
87
```

This occurred in native cases involving:

```text
V1 positive rename
V2 existing destination directory
V3 existing destination file
V4 concurrent destination race
V8 identity continuity
V12 native-error characterization
```

Because the native promotion did not succeed:

```text
collision semantics were not characterized
race ownership semantics were not characterized
source-to-final identity continuity was not characterized
D1-D4 post-transition durability investigation was not reached
```

This is a bounded negative native observation for the authorized
RootDirectory-relative contract. It is not a validation result, not a
falsification result, and not evidence about FileRenameInfo in general.

## 9. V1-V12 and D1-D4 Disposition

| Case | Disposition |
|---|---|
| V1 positive rename | Native call returned ERROR_INVALID_PARAMETER / 87; outcome is indeterminate. |
| V2 existing destination directory | Native call returned ERROR_INVALID_PARAMETER / 87 before collision semantics were characterized. |
| V3 existing destination file | Native call returned ERROR_INVALID_PARAMETER / 87 before file-collision semantics were characterized. |
| V4 concurrent destination race | Native call returned ERROR_INVALID_PARAMETER / 87 before race ownership semantics were characterized. |
| V5 source reparse rejection | SKIPPED_FIXTURE_UNAVAILABLE where the required symlink fixture was unavailable; committed test vocabulary permits SKIPPED with skip_reason SYMLINK_UNAVAILABLE. |
| V6 destination-parent reparse rejection | SKIPPED_FIXTURE_UNAVAILABLE where the required symlink fixture was unavailable; committed test vocabulary permits SKIPPED with skip_reason SYMLINK_UNAVAILABLE. |
| V7 mutation/content mismatch | Harness-level mutation detection only; not characterization of native rename mutation semantics. |
| V8 identity continuity | Native call returned ERROR_INVALID_PARAMETER / 87 before source-to-final identity continuity was characterized. |
| V9 invalid final names | Invalid names rejected before the native call. |
| V10 unsupported profile | Invalid or unsupported fixture rejected without upgrading to native evidence. |
| V11 cross-volume attempt | SKIPPED_SECOND_VOLUME_UNAVAILABLE. |
| V12 native-error characterization | Native error retention observed ERROR_INVALID_PARAMETER / 87; cause remains indeterminate. |
| D1 final-parent sync | Not reached because native promotion did not succeed. |
| D2 former source-parent sync | Not reached because native promotion did not succeed. |
| D3 both-parent ordering | Not reached because native promotion did not succeed. |
| D4 renamed-directory handle flush | Not reached because native promotion did not succeed. |

Skipped or harness-level outcomes are not upgraded into native promotion
evidence.

## 10. Classification Correction

The supplied implementation-review evidence records that the initial
implementation classification mapped:

```text
ERROR_INVALID_PARAMETER / 87
->
PRIMITIVE_VALIDATION_UNSUPPORTED
```

That was corrected before acceptance and commit to:

```text
ERROR_INVALID_PARAMETER / 87
->
PRIMITIVE_VALIDATION_INDETERMINATE
```

The committed implementation preserves the distinct mapping:

```text
ERROR_NOT_SUPPORTED / 50
->
PRIMITIVE_VALIDATION_UNSUPPORTED
```

Interpretation:

```text
The authorized RootDirectory-relative FileRenameInfo contract was rejected by
Windows with ERROR_INVALID_PARAMETER. The ABI and buffer construction passed
static review, but the native cause remains indeterminate. The primitive is
neither validated nor falsified. No workaround was attempted.
```

This does not state or imply that Windows rejected FileRenameInfo in general.
This does not state or imply that RootDirectory-relative usage is conclusively
invalid. This does not state or imply that Microsoft documentation is
incorrect.

## 11. Identity Bindings

Identity recomputation from the committed repository methods and committed
bytes matched the expected bindings:

| Binding | Result |
|---|---|
| validation-policy identity | `df91a9bcc3c5b37e938a086801dd2bca42f0290533a6cf2682055df475f663f3` |
| runner/source SHA-256 | `e19b6b1e4b7f7631acdd23f4a3f647c29d14233eac7ef3abf3a5a8405839cd03` |
| validation-schema source SHA-256 | `e19b6b1e4b7f7631acdd23f4a3f647c29d14233eac7ef3abf3a5a8405839cd03` |
| primitive-research document identity | `508324887bae882295cbe06d6c10b8729bf56fdc77c102fcf2c20f3758dc1916` |
| BLOCKER-2 assessment identity | `6f4e5091058dd0c17cb8483f6fe21e5c29a6e5e7fff098eb0546101a1da6b23e` |
| validation-authorization document identity | `370c1fd91c18e01ca05c0f3005a62b8829a7ec882b4b17ac755f139856dd3df7` |

Obsolete identity:

```text
7bfab963d8626c6c53ea4a10b0683dcf8cf4ac2b0bcf61fa806ea4e471eef930
```

Status:

```text
OBSOLETE
MUST NOT BE REUSED
```

No source was changed because of identity verification.

## 12. Claims Supported

| Classification | Claims |
|---|---|
| supported | The implementation commit is limited to the three authorized research/test files. |
| supported | The committed operation under validation is SetFileInformationByHandle + FileRenameInfo + FILE_RENAME_INFO with ReplaceIfExists = FALSE and a non-NULL RootDirectory destination-parent handle. |
| supported | The source directory is opened by handle with DELETE, FILE_SHARE_READ \| FILE_SHARE_WRITE \| FILE_SHARE_DELETE, OPEN_EXISTING, and FILE_FLAG_BACKUP_SEMANTICS \| FILE_FLAG_OPEN_REPARSE_POINT. |
| supported | The committed implementation does not modify publication, recovery, replay, service, kernel, memory, cognition, autonomy, prompt, action, or production surfaces. |
| supported | Static review found no known ctypes ABI, structure-layout, or variable-buffer construction defect. |
| supported | Focused implementation tests were reported as passing in supplied ephemeral evidence. |
| supported | The implementation is useful as a bounded negative native observation. |

## 13. Claims Not Supported

| Classification | Claims |
|---|---|
| not supported | production readiness |
| not supported | general Windows filesystem durability |
| not supported | documented rename atomicity |
| not supported | documented rename durability |
| not supported | BLOCKER-2 closure |
| not supported | primitive validation |
| not supported | primitive falsification |
| not supported | FileRenameInfo unsupported |
| not supported | RootDirectory-relative FileRenameInfo falsified |
| not supported | real-world Brainvision readiness |
| not supported | strong order sensitivity |
| not reached | collision semantics |
| not reached | race ownership semantics |
| not reached | source-to-final identity continuity |
| not reached | D1-D4 post-transition durability investigation |
| skipped | V5 and V6 reparse fixture cases where the required symlink fixture was unavailable |
| skipped | V11 cross-volume attempt because a second local fixed NTFS volume fixture was unavailable |
| indeterminate | native cause of ERROR_INVALID_PARAMETER / 87 for the authorized RootDirectory-relative contract |

## 14. BLOCKER-2 Status

BLOCKER-2 remains OPEN.

The selected primitive is neither validated nor falsified.

Allowed high-level classification:

```text
CORRECTLY_IMPLEMENTED_PRIMITIVE_WITH_CAUSE_INDETERMINATE_NATIVE_REJECTION
```

The implementation is useful as a bounded negative native observation, but it
does not support closure or a production specification.

## 15. Recommended Next Procedural Step

The next diagnostic question may be identified, but is not authorized here:

```text
Does FileRenameInfo succeed when RootDirectory = NULL and FileName contains the
full absolute same-volume destination path under the same isolated fixed-NTFS
fixture profile?
```

That control:

```text
was forbidden by the prior authorization
was not attempted
requires a new docs-only assessment and authorization
```

No additional controls are bundled into these findings.

## 16. Final Findings Verdict

```text
A. ACCEPT_IMPLEMENTATION_FINDINGS_WITH_BLOCKER_2_REMAINING_OPEN
```

This verdict does not authorize execution, implementation, specification,
closure, production use, publication wiring, recovery wiring, replay wiring, or
integration.
