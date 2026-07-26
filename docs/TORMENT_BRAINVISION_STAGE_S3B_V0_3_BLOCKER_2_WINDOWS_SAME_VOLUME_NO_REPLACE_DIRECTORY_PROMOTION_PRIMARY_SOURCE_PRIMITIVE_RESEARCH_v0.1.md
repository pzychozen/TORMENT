# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Windows Same-Volume No-Replace Directory Promotion Primary-Source Primitive Research v0.1

## 1. Research Identity and Scope

document_class = BLOCKER-2 primary-source primitive research

document_version = v0.1

research_scope =
same-volume no-replace promotion of a complete verified directory on the
authorised Windows 10/11 local-fixed-NTFS synthetic-offline profile.

baseline_commit = 031b06c570e6de88912da39e75b133bcd6faea71

baseline_branch = main

baseline_origin = origin/main

primary_research_result =
C. SETFILEINFORMATIONBYHANDLE_FILERENAMEINFO_RECOMMENDED_FOR_BLOCKER_2_SPECIFICATION

next_procedural_result =
REQUIRES_BOUNDED_WINDOWS_PRIMITIVE_VALIDATION_BEFORE_SPECIFICATION

This document is research only. It performs no implementation, creates no tests,
executes no promotion experiment, authorizes no future execution, and opens no
live or production publication lane.

Preserved project state:

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

No claim is made of validated promotion, atomic publication completion,
production readiness, general Windows filesystem durability, cross-volume
atomic promotion, true temporal vision, strong order sensitivity, real-world
Brainvision readiness, or BLOCKER-2 closure.

Classification vocabulary used below:

```text
DOCUMENTED
INFERRED
REQUIRES_EMPIRICAL_VALIDATION
UNRESOLVED
NOT_DOCUMENTED_IN_REVIEWED_PRIMARY_SOURCE
```

## 2. Authoritative Baseline and Blocker State

The required synchronized baseline for this research is:

```text
branch      = main
HEAD        = 031b06c570e6de88912da39e75b133bcd6faea71
origin/main = 031b06c570e6de88912da39e75b133bcd6faea71
latest      = 031b06c docs(research): assess blocker 2 promotion ownership
```

Current blocker state:

```text
BLOCKER-1:
BLOCKER_1_CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_WINDOWS_LOCAL_FIXED_NTFS_TMP_PATH_SCOPE

BLOCKER-2:
OPEN
BLOCKER_2_REQUIRES_PRE_SPECIFICATION_PRIMITIVE_RESEARCH

BLOCKER-3:
CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_STAGE_S3B_V0_3_SCOPE

BLOCKER-4:
OPEN
```

Boundary conclusion:

```text
BLOCKER-1 remains closed and is not reopened.
BLOCKER-2 remains open.
BLOCKER-3 remains closed within its authorised scope.
BLOCKER-4 remains open and separate.
No implementation has been performed.
No implementation or execution has been authorized.
No live or production publication lane has been opened.
```

The durable publication boundary remains:

```text
publication is a projection of the authoritative scientific result

authoritative durable result =
verified IMMUTABLE_SCIENTIFIC_BUNDLE
+
linked valid SCIENTIFIC_COMPLETION
```

Promotion evidence remains platform evidence linked to the authoritative pair
unless a later explicit architecture decision changes that rule.

## 3. Repository Architecture Summary

DOCUMENTED from committed repository documents and source:

The current publication object is the complete staging directory:

```text
paths.staging_directory -> paths.final_directory
```

The staged/final publication set is the exact three-file artifact directory:

```text
iososv_v0_3_result.json
iososv_v0_3_execution_envelope.json
iososv_v0_3_summary.txt
```

The repository already contains:

```text
abstract promotion seam
fail-closed production default
test-only positive fake
publication orchestration
```

The repository does not contain:

```text
real Windows operating-system promotion primitive
replay-verifiable promotion policy identity
source-to-final identity continuity evidence
post-promotion FINAL_PARENT_DIRECTORY durability gating
formal BLOCKER-2 specification
BLOCKER-2 implementation authorization
```

The relevant committed seams include:

```text
research/brainvision/durable_evidence_schema_v0_3.py
research/brainvision/durable_evidence_windows_adapter_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
research/brainvision/durable_evidence_publication_replay_v0_3.py
research/brainvision/durable_evidence_publication_recovery_replay_v0_3.py
```

Current source evidence:

```text
PROMOTION_CONFIRMED
PROMOTION_UNCONFIRMED
SameVolumeNoReplacePromotionAdapter
FailClosedSameVolumeNoReplacePromotionAdapter
PUBLICATION_PROMOTION_FAILED
PUBLICATION_PROMOTION_OUTCOME_INDETERMINATE
FINAL_PARENT_DIRECTORY
```

Current test-only evidence includes `PositiveTmpPromotionAdapter`, which uses
pytest-local behavior to exercise orchestration and must not be treated as a
Windows primitive.

## 4. Primary-Source Methodology

The reviewed external sources are Microsoft primary sources only:

```text
Microsoft Learn Win32 API documentation
Microsoft Windows protocol specifications
Microsoft Windows Driver Kit documentation
Microsoft system error-code documentation
```

No Stack Overflow, Reddit, blog, forum, AI-generated summary, unverified
example, third-party wrapper documentation, or source-code folklore is used as
evidence.

Citation rule:

Each external technical claim cites a source identifier such as `[MS-01]`.
Section 25 records for each identifier the document title, Microsoft source
family, publisher, retrieval date, URL, relevant section/member, and supported
claims.

Research posture:

```text
DOCUMENTED:
  explicitly stated by reviewed Microsoft source.

INFERRED:
  derived from documented statements but not itself stated as a guarantee.

REQUIRES_EMPIRICAL_VALIDATION:
  load-bearing for BLOCKER-2 and not settled by reviewed primary sources.

UNRESOLVED:
  no reviewed primary source settles the question and no safe inference is
  sufficient for the project claim.
```

## 5. Required BLOCKER-2 Primitive Contract

The primitive must support:

```text
complete verified staging directory as source
destination final directory name absent before promotion
same-volume directory promotion
no replacement
no merge
no copy/delete fallback
no delayed-reboot operation
race-safe source identity
race-resistant destination-parent identity
post-operation final identity verification
numeric native-error capture
post-promotion final-parent durability evidence
fail-closed recovery and replay semantics
```

DOCUMENTED source basis:

Windows exposes path-based file/directory move APIs, handle-based file
information APIs, file identity fields, volume identity fields, reparse-point
behavior, and directory handle opening through `CreateFileW` with
`FILE_FLAG_BACKUP_SEMANTICS` [MS-01] [MS-02] [MS-03] [MS-04] [MS-05] [MS-08]
[MS-10] [MS-11] [MS-12] [MS-13].

INFERRED project requirement:

Because the current repository requires verified staged artifacts before
promotion and durable `PUBLICATION_COMPLETED` only after evidence admission, the
promotion primitive must be evidence-bearing rather than a bare boolean status.

REQUIRES_EMPIRICAL_VALIDATION:

The selected primitive must later be validated on isolated pytest `tmp_path`
material for non-empty directory rename, destination collision, cross-volume
failure, source/final identity equality, reparse rejection, open-handle
behavior, native error capture, and parent flush behavior.

## 6. MoveFileW Findings

Candidate classification:

```text
MoveFileW = VIABLE_BUT_INFERIOR
```

DOCUMENTED:

`MoveFileW` moves an existing file or directory including children [MS-01].

DOCUMENTED:

For the new name, Microsoft states that the new name must not already exist and
that a new directory must be on the same drive [MS-01].

DOCUMENTED:

The remarks state that `MoveFile` moves or renames a file or directory,
including children, in the same directory or across directories, and fails on
directory moves when the destination is on a different volume [MS-01].

DOCUMENTED:

`MoveFileW` returns nonzero on success and zero on failure; callers use
`GetLastError` for extended error information [MS-01].

DOCUMENTED:

The minimum supported client listed for `MoveFileW` is Windows XP desktop apps,
so Windows 10/11 are not excluded by the published minimum-support table
[MS-01].

NOT_DOCUMENTED_IN_REVIEWED_PRIMARY_SOURCE:

The reviewed `MoveFileW` page does not explicitly use the word "atomic" for the
namespace transition, does not specify a final-parent durability operation, and
does not define a complete error taxonomy for destination exists, sharing
violation, access denied, cross-volume rejection, reparse involvement, or
unsupported filesystem states [MS-01].

INFERRED:

`MoveFileW` gives strong documented no-replace and same-drive directory
semantics, but it is path-based for both source and destination. Therefore it
has residual source-path and destination-parent substitution exposure unless
the project surrounds it with opened-handle preflight and post-operation
identity checks [MS-01] [MS-08] [MS-10] [MS-12] [MS-13].

REQUIRES_EMPIRICAL_VALIDATION:

Destination-collision native error, cross-volume native error, non-empty
directory behavior in the authorised profile, reparse behavior, and post-rename
source/final identity continuity require bounded Windows validation before this
candidate could be specified.

Assessment:

`MoveFileW` is documented enough to remain viable in the abstract. It is
inferior to `SetFileInformationByHandle(FileRenameInfo)` for BLOCKER-2 because
it does not provide a source handle or handle-relative destination-parent
contract.

## 7. MoveFileExW Findings

Candidate classification:

```text
MoveFileExW with dwFlags = 0 = REQUIRES_EMPIRICAL_VALIDATION
MoveFileExW with MOVEFILE_REPLACE_EXISTING = DISQUALIFIED
MoveFileExW with MOVEFILE_COPY_ALLOWED = DISQUALIFIED
MoveFileExW with MOVEFILE_DELAY_UNTIL_REBOOT = DISQUALIFIED
MoveFileExW with MOVEFILE_WRITE_THROUGH = DISQUALIFIED
MoveFileExW with MOVEFILE_CREATE_HARDLINK = DISQUALIFIED
MoveFileExW with MOVEFILE_FAIL_IF_NOT_TRACKABLE = VIABLE_BUT_INFERIOR
```

DOCUMENTED:

`MoveFileExW` moves an existing file or directory, including children, with
move options [MS-02].

DOCUMENTED:

For directory moves, the destination must be on the same drive [MS-02].

DOCUMENTED:

`MOVEFILE_COPY_ALLOWED` permits a cross-volume file move to be simulated by
copying and deleting; if copy succeeds and source delete fails, the function can
still succeed while leaving the source intact [MS-02].

BLOCKER-2 conclusion:

`MOVEFILE_COPY_ALLOWED` is disqualified because the contract forbids
cross-volume fallback, copy/delete substitution, and partial-copy success.

DOCUMENTED:

`MOVEFILE_REPLACE_EXISTING` gives replacement semantics for an existing file and
reports an error if the destination names an existing directory [MS-02].

BLOCKER-2 conclusion:

`MOVEFILE_REPLACE_EXISTING` is disqualified because BLOCKER-2 requires no
replacement.

DOCUMENTED:

`MOVEFILE_DELAY_UNTIL_REBOOT` delays the operation until restart, requires
administrative or LocalSystem context, and its return value can reflect registry
entry placement rather than the later file move/delete result [MS-02].

BLOCKER-2 conclusion:

`MOVEFILE_DELAY_UNTIL_REBOOT` is disqualified because BLOCKER-2 requires an
immediate evidence-bearing namespace operation.

DOCUMENTED:

`MOVEFILE_CREATE_HARDLINK` is reserved for future use [MS-02].

BLOCKER-2 conclusion:

`MOVEFILE_CREATE_HARDLINK` is disqualified because it is not a documented
directory promotion primitive.

DOCUMENTED:

`MOVEFILE_FAIL_IF_NOT_TRACKABLE` fails if the source file is a link source and
cannot be tracked after the move; Microsoft gives FAT as an example where this
can occur [MS-02].

BLOCKER-2 conclusion:

This flag is not a no-replace or identity-continuity primitive for the
publication directory. It is not selected.

DOCUMENTED:

`MOVEFILE_WRITE_THROUGH` guarantees flushing only for a move performed as a
copy/delete operation; the flush occurs at the end of the copy operation, and
the flag has no effect with delayed reboot [MS-02].

BLOCKER-2 conclusion:

`MOVEFILE_WRITE_THROUGH` must not be treated as final-parent directory-entry
durability for a same-volume directory rename. It is disqualified as a
durability substitute.

NOT_DOCUMENTED_IN_REVIEWED_PRIMARY_SOURCE:

The reviewed `MoveFileExW` page does not explicitly state that `dwFlags = 0`
has the same destination-must-not-exist guarantee stated on `MoveFileW`, does
not explicitly guarantee atomicity, and does not define parent-directory
durability [MS-02].

INFERRED:

`MoveFileExW` with `dwFlags = 0` likely follows the ordinary no-replace path,
but the reviewed primary source is less direct than `MoveFileW` and remains
path-based for source and destination [MS-02].

Assessment:

`MoveFileExW` is not recommended for BLOCKER-2. The zero-flag form remains a
possible fallback only after bounded validation and only if the recommended
handle-based primitive fails future validation.

## 8. SetFileInformationByHandle/FileRenameInfo Findings

Candidate classification:

```text
SetFileInformationByHandle + FileRenameInfo + FILE_RENAME_INFO = RECOMMENDED
```

DOCUMENTED:

`SetFileInformationByHandle` sets file information for a specified file handle
and accepts a `FILE_INFO_BY_HANDLE_CLASS` value and matching structure buffer
[MS-03].

DOCUMENTED:

`FileRenameInfo` is a valid information class for `SetFileInformationByHandle`
and maps to `FILE_RENAME_INFO` [MS-03] [MS-04].

DOCUMENTED:

`FILE_RENAME_INFO` contains the target name to which the source file should be
renamed and is used with `SetFileInformationByHandle` [MS-05].

DOCUMENTED:

When the information class is `FileRenameInfo`, `ReplaceIfExists = FALSE` means
that if the target exists, the operation returns an error; `TRUE` means a target
file can be replaced [MS-05].

BLOCKER-2 conclusion:

The proposed contract must set `ReplaceIfExists = FALSE`.

DOCUMENTED:

If `FILE_RENAME_INFO.FileName` specifies a relative name, `RootDirectory` can be
a handle to the directory relative to which the new name is resolved [MS-05].

DOCUMENTED:

The WDK rename structure says a relative name uses `RootDirectory` as a handle
to the target directory and the file name itself must be a simple file name
[MS-06].

BLOCKER-2 conclusion:

The destination should be bound to an opened destination-parent handle plus a
simple final directory name, avoiding a full destination path string as the
load-bearing namespace target.

DOCUMENTED:

The WDK rename rules state that a file or directory can only be renamed within
a volume, and that when `ReplaceIfExists` is false and the target exists, the
rename operation fails [MS-06].

BLOCKER-2 conclusion:

The handle-based `FileRenameInfo` contract gives the strongest reviewed primary
source basis for a same-volume no-replace directory promotion.

DOCUMENTED:

The WDK rename rules state that renaming requires `DELETE` access to the file
and appropriate access to create the new entry in the new parent directory
[MS-06]. `CreateFileW` documents `FILE_SHARE_DELETE` and states delete access
allows both delete and rename operations [MS-08].

INFERRED:

For the source staging directory, the future implementation should open the
source directory handle with `DELETE` and share modes that do not create
artificial conflicts, likely including `FILE_SHARE_READ | FILE_SHARE_WRITE |
FILE_SHARE_DELETE`, subject to formal specification and validation [MS-06]
[MS-08].

DOCUMENTED:

`CreateFileW` requires `FILE_FLAG_BACKUP_SEMANTICS` to obtain a directory
handle [MS-08].

INFERRED:

The source staging directory handle and destination-parent directory handle
should be opened with `FILE_FLAG_BACKUP_SEMANTICS`. When the project needs to
inspect or reject a reparse point itself, `FILE_FLAG_OPEN_REPARSE_POINT` is
relevant because Microsoft documents that `CreateFileW` opens the reparse point
rather than the target when that flag is used [MS-08] [MS-12].

DOCUMENTED:

`SetFileInformationByHandle` minimum supported client is Windows Vista desktop
apps/UWP apps, and `FILE_RENAME_INFO` minimum supported client is Windows Vista
desktop apps [MS-03] [MS-05].

INFERRED:

The minimum-support tables do not exclude Windows 10 or Windows 11. The exact
project support profile still requires bounded validation on the authorised
Windows 10/11 local-fixed-NTFS environment [MS-03] [MS-05].

NOT_DOCUMENTED_IN_REVIEWED_PRIMARY_SOURCE:

The reviewed Win32 pages do not explicitly state non-empty directory rename
success, do not state an atomic visibility guarantee, do not document final
parent directory durability after rename, and do not provide the complete
native error mapping for all BLOCKER-2 cases [MS-03] [MS-05].

REQUIRES_EMPIRICAL_VALIDATION:

The future validation must prove, inside isolated pytest `tmp_path`, that this
handle contract works for the complete non-empty staging directory and that
source/final `BY_HANDLE_FILE_INFORMATION` identity equality is observed on the
authorised NTFS profile [MS-10].

Assessment:

This is the recommended primitive for formal BLOCKER-2 specification drafting,
but it is not yet a specification, implementation, or closure result.

## 9. FileRenameInfoEx Findings

Candidate classification:

```text
SetFileInformationByHandle + FileRenameInfoEx = VIABLE_BUT_INFERIOR
```

DOCUMENTED:

`FILE_INFO_BY_HANDLE_CLASS` includes `FileRenameInfoEx` [MS-04].

DOCUMENTED:

`FILE_RENAME_INFO.Flags` is used when `SetFileInformationByHandle` uses
`FileRenameInfoEx` [MS-05].

DOCUMENTED:

The WDK rename structure describes `Flags` for `FileRenameInformationEx`, and
the Windows protocol specification defines `FileRenameInformationEx` with a
Flags field [MS-06] [MS-07].

DOCUMENTED:

The protocol specification states that if `FILE_RENAME_REPLACE_IF_EXISTS` is
not set, the rename operation must fail if the target name already exists
[MS-07].

DOCUMENTED:

`FILE_RENAME_POSIX_SEMANTICS` applies with replacement and permits POSIX-style
replacement behavior with existing handles continuing to refer to the replaced
file [MS-06] [MS-07].

BLOCKER-2 conclusion:

POSIX replacement behavior must be prohibited. The project must not import
POSIX replacement semantics into BLOCKER-2.

DOCUMENTED:

The extended flags include storage-reserve and read-only replacement modifiers,
some requiring manage-volume or write-attributes access [MS-06] [MS-07].

BLOCKER-2 conclusion:

Those extended flags are unnecessary and would broaden the project contract.
They should be prohibited by the future specification unless a renewed
architecture order authorizes them.

INFERRED:

`FileRenameInfoEx` with `Flags = 0` appears to preserve no-replace behavior, but
it adds no necessary benefit over `FileRenameInfo` for the current BLOCKER-2
contract and brings a larger flag surface [MS-05] [MS-06] [MS-07].

REQUIRES_EMPIRICAL_VALIDATION:

Public user-mode behavior and exact Windows 10/11 support for `FileRenameInfoEx`
should be validated if the project later considers it. It is not recommended
for v0.1 because the simpler `FileRenameInfo` contract is sufficient for the
recommended research result.

## 10. Candidate Comparison Matrix

Legend:

```text
DOC = documented in reviewed Microsoft primary source
INF = inference from documented source
VAL = requires bounded Windows validation
ND  = NOT_DOCUMENTED_IN_REVIEWED_PRIMARY_SOURCE
DQ  = disqualified for BLOCKER-2
```

| Property | MoveFileW | MoveFileExW dwFlags=0 | SetFileInformationByHandle/FileRenameInfo | SetFileInformationByHandle/FileRenameInfoEx |
|---|---|---|---|---|
| User-mode documented API status | DOC [MS-01] | DOC [MS-02] | DOC [MS-03] [MS-04] [MS-05] | DOC enum/structure exposure [MS-04] [MS-05] |
| Minimum supported Windows version | XP client [MS-01] | XP client [MS-02] | Vista client [MS-03] [MS-05] | enum appears in Vista-minimum page, details require validation [MS-04] [MS-06] |
| Windows 10 support | INF from minimum table [MS-01] | INF from minimum table [MS-02] | INF from minimum table [MS-03] [MS-05] | INF/VAL [MS-04] [MS-06] |
| Windows 11 support | INF from minimum table [MS-01] | INF from minimum table [MS-02] | INF from minimum table [MS-03] [MS-05] | INF/VAL [MS-04] [MS-06] |
| Directory support | DOC includes directory and children [MS-01] | DOC includes directory and children [MS-02] | DOC/INF from WDK "file or directory" rename rules [MS-06] | DOC/INF from WDK/protocol rename rules [MS-06] [MS-07] |
| Non-empty directory support | DOC "including children" [MS-01] | DOC "including children" [MS-02] | VAL for Win32 handle path; WDK mentions directory/open-handle rules [MS-06] | VAL |
| Same-directory rename | DOC [MS-01] | DOC/INF [MS-02] | DOC WDK simple-name rule [MS-06] | DOC WDK/protocol [MS-06] [MS-07] |
| Cross-directory same-volume | DOC same/cross directories and directory same volume [MS-01] | DOC destination same drive for directory [MS-02] | DOC within-volume only [MS-06] | DOC within-volume only [MS-06] |
| Cross-volume behavior | Directory fails across volume [MS-01] | Directory must stay same drive [MS-02] | Rename cannot cause file or directory to move to different volume [MS-06] | Same [MS-06] |
| Cross-volume copy fallback possible | ND for directory; not documented as copy fallback [MS-01] | DQ if COPY_ALLOWED; zero flags VAL [MS-02] | DOC no cross-volume rename rule, no copy fallback documented [MS-06] | Same |
| Destination-exists behavior | DOC new name must not already exist [MS-01] | ND for zero flags; replacement flag documented separately [MS-02] | DOC `ReplaceIfExists = FALSE` returns error [MS-05] [MS-06] | DOC replacement flag absence means fail if target exists [MS-07] |
| No-replace mode | DOC [MS-01] | VAL for zero flags [MS-02] | DOC [MS-05] [MS-06] | DOC with flags not setting replacement [MS-07] |
| Replace-existing mode | No replacement mode documented for MoveFileW [MS-01] | DOC `MOVEFILE_REPLACE_EXISTING`; DQ [MS-02] | DOC `ReplaceIfExists = TRUE`; prohibited [MS-05] | DOC replacement flags; prohibited [MS-06] [MS-07] |
| Namespace no-replace enforcement | DOC path new name must not exist [MS-01] | VAL | DOC target exists returns error [MS-05] [MS-06] | DOC target exists fails if replacement flag not set [MS-07] |
| Source binding | Path-based [MS-01] | Path-based [MS-02] | Handle-based source [MS-03] | Handle-based source [MS-03] |
| Destination binding | Path-based [MS-01] | Path-based [MS-02] | Handle-relative destination available [MS-05] [MS-06] | Handle-relative destination available [MS-05] [MS-07] |
| Required source access | ND exact for MoveFileW | DOC delete/delete-child note [MS-02] | DOC appropriate permission, WDK DELETE access [MS-03] [MS-06] | Same plus flag-specific access [MS-06] |
| Required share flags | ND | ND | INF from CreateFile share semantics; validate [MS-08] | Same |
| Reparse behavior | ND for move call; path functions need surrounding policy [MS-12] [MS-13] | ND for move call | Can open source/dest parents with reparse policy via CreateFileW [MS-08] [MS-12] | Same |
| Open-handle behavior | ND | ND | DOC WDK special open-handle rules [MS-06] | DOC WDK/protocol rules [MS-06] [MS-07] |
| Native error observability | GetLastError [MS-01] | GetLastError [MS-02] | GetLastError [MS-03] | GetLastError through SetFileInformationByHandle [MS-03] |
| Atomicity guarantee | ND | ND | ND | ND |
| Local fixed NTFS interaction | VAL; source supports NTFS identity via separate APIs [MS-10] | VAL | VAL; strongest identity support [MS-10] | VAL |
| Unsupported filesystem distinctions | ND beyond tables | DQ/VAL for flags | VAL | VAL |
| Documented durability semantics | ND | WRITE_THROUGH only copy/delete [MS-02] | ND | ND |
| Relation to FlushFileBuffers | ND | WRITE_THROUGH not final parent [MS-02] | final parent flush unresolved; FlushFileBuffers docs separate [MS-09] | same |
| Suitability | viable but inferior | not selected | recommended | viable but inferior |

Other reviewed user-mode primitives:

| Primitive | Classification | Reason |
|---|---|---|
| ReplaceFileW | DISQUALIFIED | It replaces one file with another and is not a no-replace directory promotion primitive [MS-15]. |
| MoveFileTransactedW / TxF | DISQUALIFIED | It is path-based, transaction-dependent, Microsoft recommends alternatives because TxF may not be available in future Windows versions, and the project has not authorized a transaction lane [MS-16] [MS-17]. |
| MoveFileWithProgress | NOT_SEPARATELY_SELECTED | Microsoft documents it as equivalent to MoveFileEx except for progress callback behavior [MS-02]. |

## 11. No-Replace and Destination-Collision Findings

Strongest documented no-replace basis:

```text
SetFileInformationByHandle
+ FileRenameInfo
+ FILE_RENAME_INFO.ReplaceIfExists = FALSE
+ destination RootDirectory handle
+ simple final directory name
```

DOCUMENTED:

`FILE_RENAME_INFO.ReplaceIfExists = FALSE` causes the operation to return an
error if the target exists [MS-05].

DOCUMENTED:

The WDK rename rule repeats that `ReplaceIfExists = FALSE` plus an existing
target causes failure [MS-06].

DOCUMENTED:

The protocol `FileRenameInformationEx` rule says not setting
`FILE_RENAME_REPLACE_IF_EXISTS` requires failure if the name exists [MS-07].

DOCUMENTED:

`MoveFileW` states the new name must not already exist [MS-01].

REQUIRES_EMPIRICAL_VALIDATION:

The numeric Win32 error for each destination-collision case is not frozen by
the reviewed candidate pages. Later validation must capture `GetLastError` for
destination file exists, destination directory exists, and collision with
reparse-point destination.

Relevant documented error names:

```text
ERROR_ALREADY_EXISTS = 183
ERROR_FILE_EXISTS = 80
ERROR_ACCESS_DENIED = 5
ERROR_NOT_SAME_DEVICE = 17
ERROR_SHARING_VIOLATION = 32
ERROR_INVALID_PARAMETER = 87
ERROR_NOT_SUPPORTED = 50
```

Those numeric meanings are documented in the Microsoft system error-code list,
but the candidate pages do not bind each one to every rename scenario [MS-14].

## 12. Same-Volume Findings

DOCUMENTED:

`MoveFileW` says a new directory must be on the same drive and that directory
moves fail when the destination is on a different volume [MS-01].

DOCUMENTED:

`MoveFileExW` says when moving a directory, the destination must be on the same
drive [MS-02].

DOCUMENTED:

The WDK rename rules state that a file or directory can only be renamed within
a volume [MS-06].

DOCUMENTED:

`BY_HANDLE_FILE_INFORMATION` contains `dwVolumeSerialNumber`,
`nFileIndexHigh`, and `nFileIndexLow`; Microsoft says the file identifier plus
volume serial number identify a file on a single computer for comparing
handles [MS-10].

DOCUMENTED:

`GetFileInformationByHandle` documentation says comparing `VolumeSerialNumber`
and `FileIndex` members can determine whether two paths map to the same target,
including whether two paths map to the same directory [MS-10].

DOCUMENTED:

`GetVolumeInformationW` can return volume serial number and filesystem name for
a volume root [MS-11].

INFERRED:

API failure alone is not sufficient for project classification. BLOCKER-2
should still preflight source parent and destination parent identity/volume and
postflight source/final identity to distinguish admission failure, native
cross-volume rejection, and identity-change failures [MS-06] [MS-10] [MS-11].

REQUIRES_EMPIRICAL_VALIDATION:

The exact native error emitted for cross-volume directory attempts under
`SetFileInformationByHandle(FileRenameInfo)` must be measured in a bounded
Windows tmp-path experiment or a controlled two-volume fixture if later
authorization provides one.

## 13. Handle, Identity, and Reparse Findings

DOCUMENTED:

`CreateFileW` opens files, directories, volumes, and other I/O objects. It
requires `FILE_FLAG_BACKUP_SEMANTICS` to obtain a directory handle [MS-08].

DOCUMENTED:

`CreateFileW` share mode includes `FILE_SHARE_DELETE`; if this flag is not
specified, delete-access opens can fail, and delete access allows delete and
rename operations [MS-08].

DOCUMENTED:

`CreateFileW` with `FILE_FLAG_OPEN_REPARSE_POINT` opens the reparse point rather
than its target when an existing file is a symbolic link; without the flag it
opens the target [MS-08] [MS-12].

DOCUMENTED:

`GetFileAttributesW` returns attributes for a symbolic link itself when the
path points to a symbolic link [MS-12] [MS-13].

DOCUMENTED:

`GetVolumeInformationW` returns volume information for the target when the path
points to a symbolic link [MS-11] [MS-12].

DOCUMENTED:

Reparse points can alter expected file-system behavior and are used for NTFS
file-system links and mounted folders [MS-13].

INFERRED:

For BLOCKER-2, path-root comparison is insufficient. The future primitive
contract should:

```text
open source staging directory handle
open source parent handle
open destination parent handle
reject source/destination-parent reparse points unless an explicit future
architecture decision admits them
compare source/destination volume identity before promotion
capture source object identity before promotion
call SetFileInformationByHandle on the source handle
reopen final path with reparse rejection
compare final object identity to source identity
```

REMAINING HAZARDS:

```text
source directory contents may be mutated unless source exclusivity/share policy
is specified and validated
destination simple name can be concurrently created and must be defeated by
the no-replace namespace operation itself
destination parent can change if the opened handle is not the RootDirectory
handle used for rename
reparse descendants inside the staged set are a content/inventory policy issue,
not fully solved by the top-level rename primitive
```

REQUIRES_EMPIRICAL_VALIDATION:

The final contract must validate the exact handle access rights, share modes,
and reparse rejection behavior under Windows 10/11 local fixed NTFS.

## 14. Atomicity Findings

Search target:

```text
atomic rename
atomic namespace transition
visibility of old versus new name
intermediate states
directory rename
```

Result:

```text
NO_EXPLICIT_MICROSOFT_ATOMICITY_GUARANTEE_FOUND
```

NOT_DOCUMENTED_IN_REVIEWED_PRIMARY_SOURCE:

The reviewed Microsoft sources document move/rename behavior, no-replace
failure rules, same-volume restrictions, and error reporting. They do not
explicitly guarantee atomic visibility or absence of intermediate states for
the BLOCKER-2 directory promotion [MS-01] [MS-02] [MS-03] [MS-05] [MS-06].

INFERRED:

BLOCKER-2 can draft a conservative specification that relies on documented
same-volume no-replace success/failure, source/final identity verification, and
fail-closed replay without claiming a stronger Microsoft atomicity guarantee.

REQUIRES_EMPIRICAL_VALIDATION:

If future reviewers require an atomicity claim rather than a fail-closed
namespace-transition claim, the project must stop for Hilmir architectural
decision or additional primary-source evidence. No experiment in this order
can prove general crash atomicity.

## 15. Durability and Parent-Directory Findings

DOCUMENTED:

`FlushFileBuffers` flushes buffers of a specified file and causes buffered data
to be written; the handle must have `GENERIC_WRITE`; failure is reported by
return value and `GetLastError` [MS-09].

DOCUMENTED:

`FlushFileBuffers` documentation discusses file handles and volume handles. It
states that flushing all open files on a volume requires a volume handle and
administrative privileges [MS-09].

DOCUMENTED:

`CreateFileW` documents `FILE_FLAG_WRITE_THROUGH` as causing write operations
to go directly to disk, and `FlushFileBuffers` documentation notes that
unbuffered I/O with `FILE_FLAG_NO_BUFFERING` and `FILE_FLAG_WRITE_THROUGH`
prevents file contents from being cached and flushes metadata with each write
[MS-08] [MS-09].

DOCUMENTED:

`MOVEFILE_WRITE_THROUGH` on `MoveFileExW` guarantees flush only for a move
performed as a copy/delete operation, with the flush at the end of the copy
operation [MS-02].

BLOCKER-2 conclusion:

`MOVEFILE_WRITE_THROUGH` does not document final-parent directory-entry
durability for a same-volume directory rename and must not be substituted for
BLOCKER-1 `FINAL_PARENT_DIRECTORY` durability evidence.

UNRESOLVED:

The reviewed primary sources do not explicitly state that
`FlushFileBuffers(final_parent_directory_handle)` after
`SetFileInformationByHandle(FileRenameInfo)` durably persists the new namespace
entry [MS-03] [MS-05] [MS-09].

UNRESOLVED:

The reviewed sources do not settle whether the former staging parent also must
be flushed after promotion to durably establish disappearance of the staging
name [MS-09].

INFERRED:

The minimum conservative future contract should require:

```text
post-promotion final path identity verification
post-promotion FINAL_PARENT_DIRECTORY sync using the closed BLOCKER-1 adapter
durability evidence linked to the promotion evidence
no PUBLICATION_COMPLETED before final-parent durability is confirmed
```

REQUIRES_EMPIRICAL_VALIDATION:

Later bounded validation should test that final-parent `FlushFileBuffers`
returns a positive `DIRECTORY_DURABILITY_CONFIRMED` result after the selected
rename under the authorised Windows profile. It should also test whether the
former staging parent can be opened/flushed after the source child entry is
removed, without claiming power-loss proof.

## 16. Native-Error Findings

DOCUMENTED:

`MoveFileW`, `MoveFileExW`, and `SetFileInformationByHandle` report failure via
zero return and extended error information through `GetLastError` [MS-01]
[MS-02] [MS-03].

DOCUMENTED:

Microsoft system error codes document the numeric meanings of relevant values,
including `ERROR_ACCESS_DENIED`, `ERROR_NOT_SAME_DEVICE`,
`ERROR_SHARING_VIOLATION`, `ERROR_NOT_SUPPORTED`, `ERROR_FILE_EXISTS`,
`ERROR_INVALID_PARAMETER`, `ERROR_DIR_NOT_EMPTY`, and others [MS-14].

NOT_DOCUMENTED_IN_REVIEWED_PRIMARY_SOURCE:

The reviewed candidate primitive pages do not provide a complete mapping from
each BLOCKER-2 failure class to specific numeric Win32 errors.

Required future evidence:

```text
destination exists file
destination exists directory
destination exists symlink/reparse point
source missing
source not directory
source top-level reparse point
destination parent missing
destination parent reparse point
source and destination parent different volume
source directory with open descendant handle
access denied
sharing violation
invalid FILE_RENAME_INFO buffer
unsupported filesystem/profile
```

Future taxonomy must preserve numeric native error code, symbolic name when
known, operation phase, source identity, destination-parent identity, and
fail-closed classification.

## 17. Crash and Recovery Implications

DOCUMENTED:

The reviewed Microsoft pages document API success/failure and error reporting;
they do not document the physical crash-state behavior for the project's
promotion sequence [MS-01] [MS-02] [MS-03] [MS-09].

INFERRED project behavior:

```text
failure before namespace transition:
  preserve authoritative scientific result; no PUBLICATION_COMPLETED.

native call returns failure:
  classify promotion failed/indeterminate using numeric native error; no
  PUBLICATION_COMPLETED.

native call returns success but final path cannot be identity-verified:
  classify post-verification failure; no PUBLICATION_COMPLETED.

success before final-parent durability confirmation:
  final path may be visible but durable final ownership is not admitted; no
  PUBLICATION_COMPLETED.

success and durability confirmation before evidence-record durability:
  namespace evidence may be observable, but replay cannot reconstruct original
  completion without a durable completed record.
```

UNRESOLVED:

The reviewed sources do not support a claim that any physical crash state is
resolved by the primitive alone. Recovery must remain fail-closed wherever
durable promotion/completion evidence is absent or contradictory.

## 18. Primary-Source Gaps

Gaps left after this review:

```text
1. explicit Microsoft atomicity guarantee for same-volume directory rename:
   NOT_DOCUMENTED_IN_REVIEWED_PRIMARY_SOURCE

2. exact SetFileInformationByHandle(FileRenameInfo) native errors for all
   BLOCKER-2 failure classes:
   REQUIRES_EMPIRICAL_VALIDATION

3. non-empty directory rename via the exact Win32 handle contract on Windows
   10/11 local fixed NTFS:
   REQUIRES_EMPIRICAL_VALIDATION

4. source-to-final file ID continuity for directory rename:
   REQUIRES_EMPIRICAL_VALIDATION, although NTFS file ID stability until delete
   is documented for files [MS-10]

5. final-parent FlushFileBuffers as a documented post-rename namespace
   durability guarantee:
   UNRESOLVED

6. former staging-parent FlushFileBuffers requirement:
   UNRESOLVED

7. exact FileRenameInfoEx user-mode support and version behavior:
   REQUIRES_EMPIRICAL_VALIDATION

8. hostile concurrent mutation exclusion:
   REQUIRES_EMPIRICAL_VALIDATION plus future specification policy
```

These gaps do not prevent selecting the recommended primitive for specification
research. They do prevent writing a formal BLOCKER-2 specification as the next
step without bounded Windows validation.

## 19. Required Bounded Empirical Validation

No experiment is executed by this research order. The later validation plan is:

| Question | Fixture | Operation | Expected fail-closed interpretation | Evidence to capture | Isolated tmp_path only |
|---|---|---|---|---|---|
| Non-empty directory promotion succeeds | staging dir with exact three artifacts | `SetFileInformationByHandle(FileRenameInfo)` with `ReplaceIfExists = FALSE` | failure keeps BLOCKER-2 open | return value, GetLastError, pre/post identities | yes |
| Destination absent success path | final name absent | handle-relative simple-name rename | no confirmed promotion without final identity | source identity, destination-parent identity, final identity | yes |
| Destination exists file | final path pre-created as file | same primitive | map to destination-exists/denied/indeterminate, no completion | native error, final object identity | yes |
| Destination exists directory | final dir pre-created | same primitive | destination-exists, no replacement/merge | native error, inventory | yes |
| Cross-volume rejection | two authorized isolated roots on different volumes if available | same primitive | cross-volume failure; no copy fallback | native error, source still present | yes, only if two-volume fixture authorized |
| Source/final identity continuity | source identity before and final path after | compare volume serial and file index | identity mismatch fails closed | `BY_HANDLE_FILE_INFORMATION` tuple | yes |
| Source-parent and destination-parent identity | opened parent handles | compare volume and object identity | unavailable/mismatched identity fails closed | parent identity tuples | yes |
| Reparse top-level source rejection | directory symlink/junction where host permits | open with reparse policy | fail closed before promotion | attributes, reparse classification | yes |
| Destination-parent reparse rejection | parent symlink/junction where host permits | parent preflight | fail closed before promotion | attributes and opened handle identity | yes |
| Concurrent destination creation | competing creation attempt around promotion | no-replace primitive | destination collision must not replace/merge | native result and final inventory | yes |
| Open-handle behavior | open descendant handle | rename attempt | classify native sharing/open-handle behavior | native error and source/final state | yes |
| Final-parent flush | final parent after successful promotion | BLOCKER-1 directory sync | no completion if unconfirmed | directory durability evidence | yes |
| Former staging-parent flush | staging parent after successful promotion | BLOCKER-1 directory sync | policy decision if unconfirmed | directory durability evidence | yes |
| Fault point after rename before final-parent durability | synthetic adapter interruption only, if later authorized | stop between phases | no reconstructed original completion | recovery/replay evidence | yes |

The validation must remain synthetic, offline, non-production, and confined to
pytest temporary paths. It must not probe real capacity, real publication
material, kernel/service/memory surfaces, live result trees, or production
paths.

## 20. Hilmir Decision Points

No genuine Hilmir architectural decision is presently required before bounded
Windows primitive validation.

Reason:

The reviewed primary-source evidence is sufficient to recommend a precise
candidate primitive for the next validation step. Remaining issues are
load-bearing technical validation questions and specification details, not yet
project-level architecture forks.

Conditional future decision 1:

```text
decision:
  whether lack of an explicit Microsoft atomicity guarantee is acceptable if
  the project relies on documented no-replace semantics, identity continuity,
  final-parent durability evidence, and fail-closed replay.

why primary evidence cannot settle it:
  no reviewed source provides an explicit atomic namespace-transition guarantee.

options:
  A. make no atomicity claim and rely on fail-closed evidence semantics.
  B. require additional primary-source authority before specification.
  C. require a stronger architecture or different platform primitive.

technical consequences:
  A allows specification without overclaiming; B delays specification; C may
  require re-architecture.

recommended default:
  A, provided validation confirms the selected no-replace/identity contract.
```

Conditional future decision 2:

```text
decision:
  whether both namespace parents must be durably synchronized after promotion.

why primary evidence cannot settle it:
  reviewed sources do not document final-parent or former-staging-parent
  post-rename durability semantics.

options:
  A. require final parent only before final ownership completion.
  B. require both final parent and former staging parent.
  C. require additional primary-source authority before deciding.

technical consequences:
  A is smaller but may leave source-retirement durability unresolved; B is more
  conservative but broadens implementation/test surface; C delays
  specification.

recommended default:
  A as the minimum completion gate, with B retained as a validation finding or
  future specification option if source-retirement evidence becomes
  load-bearing.
```

No decision in this section authorizes implementation.

## 21. Derived Research Result

Derived primary research result:

```text
C. SETFILEINFORMATIONBYHANDLE_FILERENAMEINFO_RECOMMENDED_FOR_BLOCKER_2_SPECIFICATION
```

Rationale:

```text
1. It is a documented user-mode Win32 API path through
   SetFileInformationByHandle and FileRenameInfo [MS-03] [MS-04] [MS-05].

2. It is handle-based for the source object [MS-03].

3. FILE_RENAME_INFO.ReplaceIfExists = FALSE gives documented no-replace
   behavior [MS-05].

4. RootDirectory can bind relative destination resolution to an opened
   destination-parent directory handle [MS-05] [MS-06].

5. WDK rename rules document within-volume-only rename for files and
   directories [MS-06].

6. It avoids MoveFileEx copy/delete fallback, delayed reboot, replacement, hard
   link, and write-through-as-durability-substitute traps [MS-02].

7. It minimizes path-race exposure compared with path-only MoveFileW and
   MoveFileExW.
```

Rejected primary outcomes:

```text
A. MOVEFILEW_RECOMMENDED_FOR_BLOCKER_2_SPECIFICATION
  rejected because path-only source/destination binding is inferior.

B. MOVEFILEEXW_ZERO_FLAGS_RECOMMENDED_FOR_BLOCKER_2_SPECIFICATION
  rejected because zero-flag no-replace behavior is less directly documented in
  the reviewed page and the API has a larger hazardous flag surface.

D. SETFILEINFORMATIONBYHANDLE_FILERENAMEINFOEX_RECOMMENDED_FOR_BLOCKER_2_SPECIFICATION
  rejected because FileRenameInfoEx adds unnecessary flags and version/support
  questions.

E. MULTIPLE_PRIMITIVES_REMAIN_VIABLE_PENDING_BOUNDED_WINDOWS_EXPERIMENT
  rejected because FileRenameInfo is sufficiently preferable to recommend for
  validation and specification drafting.

F. NO_REVIEWED_DOCUMENTED_PRIMITIVE_SATISFIES_BLOCKER_2
  rejected because FileRenameInfo provides documented no-replace,
  handle-source, handle-relative-destination, and within-volume evidence.

G. ARCHITECTURAL_DECISION_REQUIRED_BEFORE_PRIMITIVE_SELECTION
  rejected because no Hilmir-level decision blocks primitive selection.
```

## 22. Recommended Specification Contract

Label:

```text
RESEARCH_RECOMMENDATION_NOT_YET_SPECIFICATION
```

Proposed primitive contract:

```text
API:
  SetFileInformationByHandle

information class:
  FileRenameInfo

structure:
  FILE_RENAME_INFO

replacement policy:
  ReplaceIfExists = FALSE

flags:
  no FileRenameInfoEx flags
  no POSIX replacement semantics
  no storage-reserve flags
  no ignore-readonly replacement behavior

source-handle contract:
  open the complete verified staging directory as the source object
  request DELETE access
  use FILE_FLAG_BACKUP_SEMANTICS
  reject source reparse point by explicit preflight policy
  record source volume serial and file index before promotion

destination-parent contract:
  open the final publication parent directory
  use it as FILE_RENAME_INFO.RootDirectory
  pass a simple final directory name, not a full destination path string
  reject reparse destination parent by explicit preflight policy
  record destination-parent volume serial and file index

cross-volume policy:
  require source parent and destination parent to be on the same volume before
  promotion
  treat native cross-volume rejection as fail-closed evidence
  forbid copy/delete fallback

preflight identities:
  source object identity
  source parent identity
  destination parent identity
  volume identity
  immediate staged artifact inventory and hashes
  linked IMMUTABLE_SCIENTIFIC_BUNDLE identity
  linked SCIENTIFIC_COMPLETION identity

operation:
  call SetFileInformationByHandle on the opened source directory handle
  use FileRenameInfo
  use RootDirectory = opened destination-parent handle
  use FileName = simple final directory name

post-operation identities:
  reopen final path under reparse rejection policy
  compare final object identity to pre-promotion source identity
  verify final artifact inventory and hashes
  preserve numeric native result/error evidence

durability operations:
  require post-promotion FINAL_PARENT_DIRECTORY durability through the
  BLOCKER-1 directory-durability adapter before admitting final ownership
  record whether former staging-parent durability is performed or deliberately
  outside v0.1 completion scope

completion gate:
  no PUBLICATION_COMPLETED until promotion status, identity continuity,
  final artifact verification, promotion policy identity, directory durability
  policy identity, and final-parent durability are all admitted

required empirical validation:
  all validation cases listed in Section 19
```

This recommendation does not authorize code changes, tests, execution, live
publication, or specification drafting inside this document.

## 23. Remaining Limitations

Remaining limitations:

```text
BLOCKER-2 remains open.
The recommended primitive has not been validated in this order.
No formal BLOCKER-2 specification has been written.
No implementation authorization exists.
No tests were created or modified.
No Windows experiment was executed.
No atomicity guarantee was found in reviewed primary sources.
Final-parent durability after rename remains unresolved as a documented
Microsoft guarantee.
Former-staging-parent durability remains unresolved.
FileRenameInfoEx remains viable but inferior and unneeded for v0.1.
MoveFileW remains viable but inferior and path-based.
MoveFileExW zero flags remains unselected and validation-dependent.
No live or production publication lane is open.
```

The research does not alter:

```text
torment_service/kernel/
production TORMENT memory functionality
live service behavior
prompt or action surfaces
autonomy
identity
truth selection
memory cognition
```

## 24. Next Procedural Step

Selected next procedural result:

```text
REQUIRES_BOUNDED_WINDOWS_PRIMITIVE_VALIDATION_BEFORE_SPECIFICATION
```

Reason:

The primary-source review supports a recommended primitive, but load-bearing
properties remain unvalidated:

```text
non-empty directory handle rename on the authorised Windows profile
destination collision native behavior
cross-volume rejection native behavior
source-to-final identity continuity
reparse rejection behavior
open-handle behavior
final-parent directory durability result after rename
former-staging-parent durability result, if later required
numeric native error taxonomy
```

Next authorized work should be a separate docs/order phase authorizing bounded
Windows primitive validation. This document does not prepare that order, does
not prepare the formal specification, and does not authorize implementation.

## 25. Source Register

### Microsoft Sources

MS-01

```text
document title:
  MoveFileW function (winbase.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefilew
relevant sections/members:
  In this article; lpExistingFileName; lpNewFileName; Return value; Remarks;
  Requirements
claims supported:
  moves existing file or directory including children; new name must not
  already exist; new directory must be on same drive; directory move fails when
  destination is on different volume; GetLastError on failure; minimum
  supported client.
```

MS-02

```text
document title:
  MoveFileExW function (winbase.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw
relevant sections/members:
  In this article; lpNewFileName; dwFlags; MOVEFILE_COPY_ALLOWED;
  MOVEFILE_CREATE_HARDLINK; MOVEFILE_DELAY_UNTIL_REBOOT;
  MOVEFILE_FAIL_IF_NOT_TRACKABLE; MOVEFILE_REPLACE_EXISTING;
  MOVEFILE_WRITE_THROUGH; Return value; Remarks; Requirements
claims supported:
  directory moves require same drive; copy/delete fallback and partial source
  retention when copy allowed; replacement semantics; delayed reboot behavior;
  write-through limited to copy/delete flush; reserved hard-link flag; return
  and error behavior; MoveFileWithProgress equivalence.
```

MS-03

```text
document title:
  SetFileInformationByHandle function (fileapi.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfileinformationbyhandle
relevant sections/members:
  Syntax; hFile; FileInformationClass; lpFileInformation; Return value;
  Remarks table; Requirements
claims supported:
  handle-based information setting; FileRenameInfo as valid information class
  with FILE_RENAME_INFO; appropriate access requirements; GetLastError on
  failure; minimum supported client.
```

MS-04

```text
document title:
  FILE_INFO_BY_HANDLE_CLASS enumeration (minwinbase.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/api/minwinbase/ne-minwinbase-file_info_by_handle_class
relevant sections/members:
  FileRenameInfo; FileRenameInfoEx; Remarks; Requirements
claims supported:
  FileRenameInfo and FileRenameInfoEx enumeration exposure; valid use rules for
  get/set functions; minimum supported client for the enumeration page.
```

MS-05

```text
document title:
  FILE_RENAME_INFO structure (winbase.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info
relevant sections/members:
  In this article; DUMMYUNIONNAME.ReplaceIfExists; DUMMYUNIONNAME.Flags;
  RootDirectory; FileNameLength; FileName; Requirements
claims supported:
  target rename structure for SetFileInformationByHandle; ReplaceIfExists false
  returns error if target exists; Flags used for FileRenameInfoEx; RootDirectory
  handle-relative resolution; FileName length/name rules; minimum supported
  client.
```

MS-06

```text
document title:
  FILE_RENAME_INFORMATION structure (ntifs.h)
source family:
  Microsoft Windows Driver Kit documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information
relevant sections/members:
  ReplaceIfExists; Flags; RootDirectory; FileName; Remarks; general rules for
  rename operations; special rules for renaming open files
claims supported:
  rename structure and FileRenameInformationEx flags; target exists failure
  when ReplaceIfExists is false; RootDirectory target-directory handle;
  relative-name simple-file-name rule; DELETE access requirement; file or
  directory rename only within a volume; open-handle restrictions for
  directories.
```

MS-07

```text
document title:
  [MS-FSCC] 2.4.43 FileRenameInformationEx
source family:
  Microsoft Windows protocol specification
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/4217551b-d2c0-42cb-9dc1-69a716cf6d0c
relevant sections/members:
  Flags; FILE_RENAME_REPLACE_IF_EXISTS; FILE_RENAME_POSIX_SEMANTICS;
  RootDirectory; FileNameLength; FileName
claims supported:
  FileRenameInformationEx flag meanings; not setting replacement flag requires
  failure if the target exists; POSIX replacement behavior; RootDirectory and
  FileName field semantics in the protocol data element.
```

MS-08

```text
document title:
  CreateFileW function (fileapi.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew
relevant sections/members:
  dwDesiredAccess; dwShareMode; FILE_SHARE_DELETE; OPEN_EXISTING;
  FILE_FLAG_BACKUP_SEMANTICS; FILE_FLAG_OPEN_REPARSE_POINT;
  FILE_FLAG_WRITE_THROUGH; Return value
claims supported:
  directory handle opening requires FILE_FLAG_BACKUP_SEMANTICS; share-delete
  relation to delete/rename access; reparse point opening behavior; write
  through flag meaning; GetLastError on failure.
```

MS-09

```text
document title:
  FlushFileBuffers function (fileapi.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers
relevant sections/members:
  In this article; hFile; Return value; Remarks; Requirements
claims supported:
  flushes buffers for an open file handle; handle needs GENERIC_WRITE; returns
  GetLastError on failure; volume-handle flushing requires administrative
  privileges; unbuffered write-through metadata statement.
```

MS-10

```text
document title:
  GetFileInformationByHandle function (fileapi.h) and BY_HANDLE_FILE_INFORMATION structure (fileapi.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URLs:
  https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandle
  https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-by_handle_file_information
relevant sections/members:
  GetFileInformationByHandle Remarks; BY_HANDLE_FILE_INFORMATION
  dwVolumeSerialNumber; nFileIndexHigh; nFileIndexLow; Remarks
claims supported:
  retrieval of file information from a handle; comparing volume serial and file
  index to determine whether two handles/paths map to the same target; NTFS file
  ID stability until deletion; ReFS caveat for 64-bit identifier.
```

MS-11

```text
document title:
  GetVolumeInformationW function (fileapi.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumeinformationw
relevant sections/members:
  lpRootPathName; lpVolumeSerialNumber; lpFileSystemFlags;
  lpFileSystemNameBuffer; Symbolic link behavior; Requirements
claims supported:
  volume serial and filesystem-name retrieval; volume root path requirement;
  file-system flags including reparse-point and POSIX unlink/rename support;
  symbolic-link target behavior.
```

MS-12

```text
document title:
  Symbolic Link Effects on File Systems Functions
source family:
  Microsoft Learn Win32 file I/O documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/fileio/symbolic-link-effects-on-file-systems-functions
relevant sections/members:
  CreateFile and CreateFileTransacted; GetFileAttributes; GetVolumeInformation
claims supported:
  handle behavior differs with FILE_FLAG_OPEN_REPARSE_POINT; GetFileAttributes
  returns symbolic-link attributes; GetVolumeInformation follows symbolic-link
  target.
```

MS-13

```text
document title:
  Reparse points
source family:
  Microsoft Learn Win32 file I/O documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points
relevant sections/members:
  In this article; Reparse point restrictions
claims supported:
  definition of reparse points; examples including NTFS file-system links and
  mounted folders; restrictions and path behavior caution.
```

MS-14

```text
document title:
  System Error Codes (0-499) (WinError.h)
source family:
  Microsoft Learn Win32 debugging documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-
relevant sections/members:
  ERROR_ACCESS_DENIED; ERROR_NOT_SAME_DEVICE; ERROR_SHARING_VIOLATION;
  ERROR_NOT_SUPPORTED; ERROR_FILE_EXISTS; ERROR_INVALID_PARAMETER;
  ERROR_DIR_NOT_EMPTY; ERROR_ALREADY_EXISTS
claims supported:
  numeric meanings of relevant Win32 system error codes returned through
  GetLastError by many functions.
```

MS-15

```text
document title:
  ReplaceFileW function (winbase.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew
relevant sections/members:
  In this article; Parameters; Return value; Remarks; Requirements
claims supported:
  ReplaceFileW replaces one file with another; replacement flags and partial
  replacement error states; same-volume requirement for backup/replaced/
  replacement files; disqualification as no-replace directory promotion.
```

MS-16

```text
document title:
  MoveFileTransactedW function (winbase.h)
source family:
  Microsoft Learn Win32 API documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefiletransactedw
relevant sections/members:
  warning banner; lpNewFileName; dwFlags; hTransaction; Remarks; Requirements
claims supported:
  transacted directory move API exists; new directory same-drive rule;
  replacement and copy/delete flags; transaction handle requirement; delayed
  reboot/registry behavior; Microsoft warning to use alternatives.
```

MS-17

```text
document title:
  Alternatives to using Transactional NTFS
source family:
  Microsoft Learn Win32 file I/O documentation
publisher:
  Microsoft
retrieval date:
  2026-07-26
URL:
  https://learn.microsoft.com/en-us/windows/win32/fileio/deprecation-of-txf
relevant sections/members:
  Abstract; Introduction; Closing and Recommended Action
claims supported:
  Microsoft recommends alternatives rather than adopting TxF APIs that may not
  be available in future Windows versions; TxF complexity and limited
  developer interest.
```

### Repository Sources

Repository sources reviewed from baseline
`031b06c570e6de88912da39e75b133bcd6faea71`:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_SAME_VOLUME_NO_REPLACE_PROMOTION_AND_FINAL_OWNERSHIP_ASSESSMENT_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_CLOSURE_ASSESSMENT_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_IMPLEMENTATION_FINDINGS_v0.1.md
research/brainvision/durable_evidence_schema_v0_3.py
research/brainvision/durable_evidence_windows_adapter_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
research/brainvision/durable_evidence_publication_replay_v0_3.py
research/brainvision/durable_evidence_publication_recovery_replay_v0_3.py
research/brainvision/test_durable_evidence_publication_v0_3.py
research/brainvision/test_durable_evidence_publication_boundary_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_boundary_v0_3.py
research/brainvision/test_durable_evidence_publication_replay_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_v0_3.py
research/brainvision/test_durable_evidence_publication_resource_bounds_v0_3.py
research/brainvision/test_durable_evidence_windows_directory_durability_v0_3.py
```

These repository sources support the architecture summary only. They are not
external Windows primitive authority.
