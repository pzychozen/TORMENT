# TORMENT Brainvision Stage S3B v0.3 BLOCKER-1 Windows Directory-Durability Closure Assessment v0.1

## 1. Assessment Identity and Status

document_class = BLOCKER-1 closure assessment

document_version = v0.1

assessment_scope = TORMENT Brainvision Stage S3B v0.3 synthetic-offline local-fixed-NTFS isolated-tmp-path Windows directory-entry durability

baseline_commit = 38cde9923919e4b70abf7e6100ae6dac34b47b63

baseline_branch = main

baseline_origin = origin/main

primary_outcome =
BLOCKER_1_CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_WINDOWS_LOCAL_FIXED_NTFS_TMP_PATH_SCOPE

This assessment is docs-only. It does not modify implementation code, tests,
fixtures, production code, kernel/service/memory/cognitive/autonomy surfaces, or
prior documents.

The closure assessed here is only the authorized BLOCKER-1 Windows directory
entry durability blocker. It is not a promotion decision, not a production
deployment decision, not arbitrary-filesystem durability, and not live
publication or recovery readiness.

FORMAL_HOLD remains active.

Mode_0 remains active.

The scientific state remains:
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY.

Brainvision remains offline, quarantined, synthetic-only, non-production,
non-service, non-kernel, non-memory-integrated, non-cognitive, and
non-autonomous.

## 2. Authoritative Baseline and Evidence Chain

The authoritative baseline for this closure assessment is:

38cde9923919e4b70abf7e6100ae6dac34b47b63

The baseline is on branch main and matches origin/main.

The latest authoritative commit is:

38cde99 docs(research): record blocker 1 directory durability findings

The committed evidence chain is:

1. 6897fc8 docs(research): assess blocker 1 Windows directory durability
2. 9ca92f9 docs(research): specify blocker 1 Windows directory durability
3. 6ed2613 docs(research): authorize blocker 1 Windows directory durability
4. 82b78fc research(brainvision): implement blocker 1 Windows directory durability
5. 38cde99 docs(research): record blocker 1 directory durability findings

The primary findings document is:

docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_IMPLEMENTATION_FINDINGS_v0.1.md

The findings document records the committed implementation evidence, the accepted
Windows execution evidence, the accepted independent-review evidence, and the
remaining scope boundaries for BLOCKER-1.

## 3. Exact Assessment Question

Assessment question:

Does the committed BLOCKER-1 implementation and its accepted findings close the
Windows directory-entry durability blocker within the exact authorised Stage S3B
v0.3 synthetic-offline local-fixed-NTFS isolated-tmp-path scope, without claiming
promotion, production deployment, arbitrary-filesystem durability, or live
publication/recovery readiness?

Answer:

Yes. The committed implementation and accepted findings close BLOCKER-1 within
the exact authorized synthetic-offline Windows local fixed NTFS isolated
pytest tmp_path scope. The closure does not claim promotion, production
deployment, arbitrary-filesystem durability, or live publication/recovery
readiness.

## 4. Closure Criteria Matrix

| # | Criterion | Classification | Evidence basis |
|---|---|---|---|
| 1 | Primitive implementation uses the authorized Win32 directory flush primitive and frozen handle contract. | SATISFIED | Commit 82b78fc modifies `durable_evidence_windows_adapter_v0_3.py` to use `CreateFileW`, `FlushFileBuffers`, `GetLastError`, `CloseHandle`, `GetFileAttributesW`, `GetDriveTypeW`, `GetVolumeInformationW`, and `GetFileInformationByHandle`; the handle contract uses `GENERIC_WRITE`, `FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE`, null security attributes, `OPEN_EXISTING`, `FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT`, and null template. |
| 2 | Positive support profile is limited to Windows 10/11 workstation, local fixed volume, NTFS, absolute path, ordinary existing directory, non-reparse target, and isolated pytest `tmp_path`; unsupported or uncertain cases fail closed. | SATISFIED | The findings record that only the admitted Windows local fixed NTFS profile can return positive confirmation; network, removable, non-NTFS, missing path, file path, non-absolute path, reparse target, and identity-uncertain cases are classified as non-confirmed. |
| 3 | Filesystem-object identity is checked before, during, and after flush by volume serial number and file index high/low; unavailable or changed identity prevents positive confirmation. | SATISFIED | The implementation records preflight handle identity, actual flush-handle identity, and reopened post-flush identity, and rejects identity-unavailable or identity-changed results rather than treating path-string equality as identity. |
| 4 | Reparse-point exclusion rejects directory symlinks, junctions, mount points, and unknown reparse tags. | SATISFIED | The findings document records explicit rejection of directory symlinks, junctions, mount points, and unknown reparse tags, with `FILE_FLAG_OPEN_REPARSE_POINT` used so the opened object is the reparse point rather than its target. |
| 5 | Policy identity is owned by the platform-neutral schema declaration, canonical, digest-bound into evidence and replay, and rejects missing, malformed, foreign, or mismatched identity. | SATISFIED | The schema-owned directory durability policy digest is `491ec6dc5704d26f97b58f155434e8f81fe424ee3f9bba997f6ed800298cbba4`; the findings record canonical computation, evidence binding, replay binding, and fail-closed handling for absent, malformed, foreign, or mismatched identity. |
| 6 | Durability sequencing records recovery-chain and receipt directory durability, staging parent creation, and complete staged artifact sets using `ARTIFACT_PARENT_DIRECTORY`, `STAGING_PARENT_DIRECTORY`, and one set-level `STAGING_DIRECTORY`, without per-artifact staging-directory sync. | SATISFIED | The findings record the authorized roles and sequence: artifact-parent durability for recovery and receipt records, staging-parent durability after staging parent creation, one set-level staging-directory durability for complete staged artifact sets, and no per-artifact staging-directory sync. |
| 7 | Evidence admission and completion require `DIRECTORY_DURABILITY_CONFIRMED` plus matching active policy; non-confirmed durability withholds `PUBLICATION_COMPLETED`, withholds J2 verified/completed, preserves original J1 evidence/final artifacts/authoritative scientific result, and emits deterministic failure evidence. | SATISFIED | Publication and recovery code paths bind directory durability status and policy identity into admission; non-confirmed durability is classified as unconfirmed rather than admitted, while original J1 evidence and final artifacts remain preserved. |
| 8 | Replay and recovery replay reject missing, malformed, foreign, or mismatched policy identity, and preserve J1/J2 separation. | SATISFIED | The findings and tests record publication replay and publication-recovery replay rejection for missing, malformed, foreign, and mismatched identity; J1 authoritative evidence remains distinct from J2 publication/recovery completion. |
| 9 | Authoritative Windows execution evidence covers focused, authorized-file, and complete required family suites, including a positive non-skipped Windows integration path. | SATISFIED | The accepted findings record focused pair results of `23 passed in 0.34s` and `23 passed in 0.33s`; nine authorized files results of `172 passed in 4.48s` and `172 passed in 5.15s`; complete required family results of `261 passed, 1 skipped in 6.75s` and `261 passed, 1 skipped in 8.13s`; the positive integration detected local fixed NTFS, opened the frozen `CreateFileW` handle, successfully ran `FlushFileBuffers`, retained stable identity, returned `DIRECTORY_DURABILITY_CONFIRMED`, and matched the active policy. |
| 10 | Independent review accepts the implementation candidate and findings candidate with no material unresolved BLOCKER-1 defect. | SATISFIED | The accepted findings record `A. ACCEPT_BLOCKER_1_IMPLEMENTATION_CANDIDATE` and `A. ACCEPT_BLOCKER_1_IMPLEMENTATION_FINDINGS_CANDIDATE`; no material unresolved BLOCKER-1 defect is recorded after those reviews. |
| 11 | Exploratory failure is isolated from BLOCKER-1 closure. | SATISFIED | The findings classify the exploratory failure as `EXPECTED_SENTINEL_REJECTION_UNRELATED_TO_BLOCKER_1`; it belongs to a separate independent-order synthetic-fixture lane outside the authorized nine-test surface and outside the required Stage S3B v0.3 durable-evidence suite. |
| 12 | Forbidden surfaces and forbidden primitives are absent. | SATISFIED | The findings record no pywin32 dependency, no new external dependency, no `MoveFileExW`, no `ReplaceFileW`, no `MOVEFILE_WRITE_THROUGH`, no volume-handle flushing, no `DeviceIoControl`, no `GetFinalPathNameByHandleW`, no production adapter, no live deployment, and no promotion implementation. |

## 5. Technical Findings

The committed implementation provides the authorized Windows directory-entry
durability primitive through `durable_evidence_windows_adapter_v0_3.py`.

The primitive is intentionally narrow. It opens existing directories with the
frozen `CreateFileW` contract, calls `FlushFileBuffers` on the opened directory
handle, records the relevant Win32 result, and closes the handle. A positive
result is available only when all support-profile and identity checks pass.

The implementation is fail-closed. Unsupported platforms, unsupported drive
types, unsupported filesystems, non-directory paths, absent paths, non-absolute
paths, reparse points, identity-unavailable cases, identity-changed cases, and
policy-identity mismatches do not produce positive directory-durability
confirmation.

The implementation does not infer object identity from normalized text paths.
It requires stable file identity across preflight, flush, and reopened
post-flush observations.

The active directory-durability policy is owned by the schema layer, not by a
hidden adapter-local policy identity. The policy digest is canonical and bound
into durability evidence and replay validation.

## 6. Evidence-Admission and Completion Findings

Publication completion is admitted only when directory durability is confirmed
and the observed policy identity matches the active schema-owned policy identity.

When directory durability is non-confirmed, publication and recovery do not
silently promote the result to completed. The evidence path withholds
`PUBLICATION_COMPLETED`, withholds J2 verified/completed status, and emits
deterministic unconfirmed durability evidence.

This behavior preserves the original J1 scientific evidence, final artifacts,
and authoritative scientific result. BLOCKER-1 does not mutate the original J1
scientific result and does not convert the publication chain into a new
scientific claim.

## 7. Windows Execution Evidence

The accepted Windows evidence recorded in the findings document is:

1. Focused pair:
   `23 passed in 0.34s`
2. Focused pair repeat:
   `23 passed in 0.33s`
3. Nine authorized files:
   `172 passed in 4.48s`
4. Nine authorized files repeat:
   `172 passed in 5.15s`
5. Complete required family:
   `261 passed, 1 skipped in 6.75s`
6. Complete required family repeat:
   `261 passed, 1 skipped in 8.13s`

The positive integration case executed on Windows and did not skip. It used
pytest `tmp_path`, detected a local fixed NTFS volume, opened the directory with
the frozen `CreateFileW` contract, successfully ran `FlushFileBuffers`, retained
stable object identity, returned `DIRECTORY_DURABILITY_CONFIRMED`, and matched
the active directory-durability policy identity.

This evidence is sufficient for the authorized local fixed NTFS isolated
tmp-path support profile. It is not evidence for arbitrary filesystems,
network/removable volumes, production publication, or live recovery.

## 8. Independent-Review Evidence

The accepted independent implementation-review verdict is:

A. ACCEPT_BLOCKER_1_IMPLEMENTATION_CANDIDATE

The accepted independent findings-review verdict is:

A. ACCEPT_BLOCKER_1_IMPLEMENTATION_FINDINGS_CANDIDATE

Those accepted reviews do not record a material unresolved BLOCKER-1 defect.
Their acceptance is evidence for closing the BLOCKER-1 platform-boundary
requirement within the authorized scope only.

## 9. Exploratory Failure Isolation

The exploratory failure recorded in the findings document is classified as:

EXPECTED_SENTINEL_REJECTION_UNRELATED_TO_BLOCKER_1

That failure belongs to the independent-order synthetic-fixture lane. It is
outside the authorized nine-test BLOCKER-1 surface and outside the required
Stage S3B v0.3 durable-evidence suite. It did not modify BLOCKER-1, did not
import the changed BLOCKER-1 modules, and concerns separate repo-local
result-path sentinel rules.

Therefore the exploratory failure does not materially prevent BLOCKER-1 closure
within the authorized Windows directory-entry durability scope.

## 10. Blocker Ownership Separation

BLOCKER-1 owns directory-entry durability within the authorized Windows support
profile: Windows workstation, local fixed NTFS volume, absolute ordinary
non-reparse directory, and isolated pytest `tmp_path`.

BLOCKER-2 owns same-volume no-replace promotion, promotion ownership, and final
ownership semantics. BLOCKER-1 closure does not close BLOCKER-2.

BLOCKER-3 is already closed within its separate authorized synthetic-offline
resource-admissibility scope.

BLOCKER-4 remains open and separate. BLOCKER-1 closure does not open, close, or
authorize BLOCKER-4 work.

No live-test lane, production lane, promotion implementation lane, or final
publication ownership lane is opened by this assessment.

## 11. Residual Limitations

The following limitations remain explicit and are not residual BLOCKER-1
requirements:

1. No production readiness is claimed.
2. No general Windows filesystem durability is claimed.
3. No arbitrary-volume, network-volume, removable-volume, or non-NTFS support is claimed.
4. No volume-handle durability is implemented or claimed.
5. No same-volume no-replace promotion closure is claimed.
6. No final publication ownership closure is claimed.
7. No live publication or live recovery readiness is claimed.
8. No real-world Brainvision readiness is claimed.
9. No temporal vision, strong order sensitivity, production cognition, kernel, memory, autonomy, or truth-selection capability is claimed.

These limitations remain outside BLOCKER-1 closure because they are either owned
by other blockers or outside Stage S3B v0.3's synthetic-offline scope.

## 12. Scientific and Production Boundaries

This assessment is a platform-boundary closure assessment, not a scientific
Brainvision result.

The durable evidence publication is a projection of the authoritative scientific
result. The authoritative durable result remains the verified
IMMUTABLE_SCIENTIFIC_BUNDLE linked to valid SCIENTIFIC_COMPLETION.

BLOCKER-1 closure does not change the scientific conclusion:

STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY

The closure does not establish true temporal vision, general visual cognition,
strong order sensitivity, production vision, real-world readiness, kernel
integration, service integration, memory integration, cognitive integration,
autonomy, or truth selection.

The system remains under FORMAL_HOLD and Mode_0.

## 13. Final Derived Outcome

Derived primary outcome:

A. BLOCKER_1_CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_WINDOWS_LOCAL_FIXED_NTFS_TMP_PATH_SCOPE

Exact outcome label:

BLOCKER_1_CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_WINDOWS_LOCAL_FIXED_NTFS_TMP_PATH_SCOPE

The committed BLOCKER-1 implementation and accepted findings close the Windows
directory-entry durability blocker within the exact authorized Stage S3B v0.3
synthetic-offline local-fixed-NTFS isolated-tmp-path scope.

This outcome is not a claim of promotion completion, production deployment,
arbitrary-filesystem durability, or live publication/recovery readiness.

## 14. Next Authorised Procedural Direction

The next authorized procedural direction is:

1. Independent review of this closure assessment.
2. Operator commit and push if the independent review accepts this assessment.
3. Prepare a separate BLOCKER-2 assessment.

This document does not prepare the BLOCKER-2 assessment, authorize BLOCKER-2
implementation, open BLOCKER-4, or open a live-test lane.
