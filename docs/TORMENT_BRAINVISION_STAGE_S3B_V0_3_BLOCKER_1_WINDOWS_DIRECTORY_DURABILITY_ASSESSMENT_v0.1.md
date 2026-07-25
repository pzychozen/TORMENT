# TORMENT Brainvision Stage S3B v0.3 BLOCKER-1 Windows Directory-Durability Assessment v0.1

## 1. DOCUMENT STATUS

```text
document_class                    = blocker assessment (docs-only)
selected_blocker                  = BLOCKER-1
authority_created                 = none
implementation_authorized         = false
execution_authorized              = false
live_test_authorized              = false
publication_authorized            = false
publication_recovery_authorized   = false
durability_reconfirmation_authorized = false
manifest_contact_authorized       = false
real_data_contact_authorized      = false
source_modified_by_this_document  = false
tests_modified_by_this_document   = false
git_mutations_by_this_document    = none
```

This assessment is read-only except for this documentation file. It does not
run live publication, live recovery, destructive crash testing, process
termination, power-loss simulation, real-data contact, or implementation work.

## 2. ASSESSMENT PURPOSE

Central question:

```text
What exact Windows directory-entry durability guarantee is required by
BLOCKER-1, what guarantee does the current Stage S3B v0.3 synthetic publication
and recovery machinery already provide, and what evidence or implementation
gap remains before BLOCKER-1 can be specified or closed?
```

Short answer:

```text
The current machinery provides canonical byte writing, exclusive creation,
file flush, file fsync, read-back verification, fail-closed directory-durability
adapter seams, fail-closed promotion seams, replay durability-evidence gating,
and synthetic tests around those seams.

It does not provide a validated Windows directory-entry durability primitive,
directory-handle flush implementation, support matrix, or exact unsupported /
unavailable / denied / indeterminate failure vocabulary sufficient to close
BLOCKER-1.
```

## 3. AUTHORITATIVE BASELINE

Repository baseline verified before creating this file:

```text
branch = main

HEAD =
4e8bc7c4ed9e0d808a010f5ec6749ebfc721129e

origin/main =
4e8bc7c4ed9e0d808a010f5ec6749ebfc721129e

latest subject =
docs(research): assess blocker 3 resource admissibility closure

working tree =
clean

index lock =
absent
```

## 4. GOVERNING SOURCES

Primary sources reviewed:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_PLATFORM_BLOCKER_DECOMPOSITION_AND_FIRST_BOUND_SELECTION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_ARCHITECTURE_REVIEW_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_ARCHITECTURE_DECISION_RECORD_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_IMPLEMENTATION_FINDINGS_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_IMPLEMENTATION_FINDINGS_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_3_RESOURCE_ADMISSIBILITY_CLOSURE_ASSESSMENT_v0.1.md
```

The exact committed document corresponding to:

```text
0d52dc0 docs(research): select resource bounds as first platform blocker
```

is:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_PLATFORM_BLOCKER_DECOMPOSITION_AND_FIRST_BOUND_SELECTION_v0.1.md
```

Committed implementation sources inspected read-only:

```text
research/brainvision/durable_evidence_windows_adapter_v0_3.py
research/brainvision/durable_evidence_primary_writer_v0_3.py
research/brainvision/durable_evidence_durability_v0_3.py
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
research/brainvision/durable_evidence_publication_replay_v0_3.py
research/brainvision/durable_evidence_publication_recovery_replay_v0_3.py
research/brainvision/durable_evidence_schema_v0_3.py
```

Relevant tests inspected read-only:

```text
research/brainvision/test_durable_evidence_core_v0_3.py
research/brainvision/test_durable_evidence_authority_v0_3.py
research/brainvision/test_durable_evidence_publication_v0_3.py
research/brainvision/test_durable_evidence_publication_resource_bounds_v0_3.py
research/brainvision/test_durable_evidence_publication_replay_v0_3.py
research/brainvision/test_durable_evidence_publication_boundary_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_resource_bounds_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_replay_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_boundary_v0_3.py
```

Evidence labels used below:

```text
explicit governing requirement = stated by governing docs
existing implementation evidence = committed code behavior
test evidence = committed pytest evidence
inference = bounded conclusion from source and docs
unresolved question = not decided by committed docs or code
```

## 5. BLOCKER-1 DEFINITION

Explicit governing requirement:

```text
BLOCKER-1 = Windows directory durability is not established.
```

The platform-blocker decomposition defines the required property as directory
state linking a validated object name to intended bytes, or a validated
directory name to an intended directory tree. It distinguishes file-data
durability and directory-entry durability. A byte-perfect read-back is not
evidence that the directory entry will survive interruption or crash.

The original durable-evidence architecture review states that records become
trusted only after canonical serialize, exclusive create, write, flush, file
fsync, read-back, byte compare, and a directory-durability step. It also states
that durable directory-entry synchronization on Windows requires
implementation-specific validation and may require a narrow Win32 adapter.

BLOCKER-1 is distinct from:

```text
file-content durability
file-handle flushing
rename durability
promotion no-replace semantics
promotion ownership attribution
real publication
real recovery
platform readiness
production readiness
scientific closure
```

Promotion involves directory state, but same-volume no-replace promotion,
replacement prevention, ownership attribution, and post-promotion ambiguity are
separately decomposed under BLOCKER-2.

## 6. EXISTING DURABILITY ARCHITECTURE

Relevant implementation archaeology:

| File | Symbol | Purpose | Platform scope | Mutates files/directories | File-content flush | Directory metadata flush | Guarantee status |
|---|---|---|---|---|---|---|---|
| `research/brainvision/durable_evidence_windows_adapter_v0_3.py` | `WindowsDurabilityAdapter.sync_directory_entry` | Abstract directory-entry durability seam | Windows-named abstraction, no concrete platform call | No | No | No | Explicit interface only |
| `research/brainvision/durable_evidence_windows_adapter_v0_3.py` | `FailClosedWindowsDurabilityAdapter.sync_directory_entry` | Default fail-closed directory durability result | Platform-neutral stub | No | No | No | Explicitly unconfirmed |
| `research/brainvision/durable_evidence_windows_adapter_v0_3.py` | `SameVolumeNoReplacePromotionAdapter.promote_verified_directory_no_replace` | Abstract promotion seam | Windows-named abstraction, no concrete platform call | Interface only | No | No | Explicit interface only |
| `research/brainvision/durable_evidence_windows_adapter_v0_3.py` | `FailClosedSameVolumeNoReplacePromotionAdapter.promote_verified_directory_no_replace` | Default fail-closed promotion result | Platform-neutral stub | No | No | No | Explicitly unconfirmed |
| `research/brainvision/durable_evidence_primary_writer_v0_3.py` | `_write_immutable_bytes` | Write stored record/bundle object | Cross-platform with Windows path normalization | Creates parent directory and file | `flush()` and `os.fsync()` | Calls adapter only | File bytes explicit; directory durability absent unless adapter confirms |
| `research/brainvision/durable_evidence_durability_v0_3.py` | `VerifiedDurabilityEvidence.from_immutable_write_results` | Admits only durable write evidence | Cross-platform evidence validator | No | Verifies bytes by read-back | Requires confirmed status but does not flush | Gating explicit |
| `research/brainvision/durable_evidence_publication_v0_3.py` | `project_publication` | J1 publication projection sequence | Synthetic/offline | Creates chain, staging, maybe final through adapter | Through primary writer and staging helper | Requires adapter confirmation for records and staging | Gated, not real Windows-proven |
| `research/brainvision/durable_evidence_publication_v0_3.py` | `_stage_publication_artifacts` | Create staging directory and artifacts | Synthetic/offline | Creates staging directory and files | `flush()` and `os.fsync()` per artifact | No direct directory flush | File bytes explicit; staging entry durability deferred to adapter |
| `research/brainvision/durable_evidence_publication_v0_3.py` | `_read_artifact_directory` | Verify visible artifact inventory/bytes | Synthetic/offline | No | No | No | Visibility and bytes, not crash durability |
| `research/brainvision/durable_evidence_publication_recovery_v0_3.py` | `verify_publication_recovery` | J2 evidence-only recovery verification | Synthetic/offline | Writes only recovery chain records | Through primary writer | Through adapter only for records | J2 evidence gated, final artifacts not mutated |
| `research/brainvision/durable_evidence_publication_recovery_v0_3.py` | `_read_final_artifact_directory` | Verify final artifact inventory and bounded bytes | Synthetic/offline | No | No | No | Recovery visibility and resource admission, not directory durability |
| `research/brainvision/durable_evidence_schema_v0_3.py` | `read_file_bytes_bounded` | Bounded file-type/read admission | Cross-platform | No | No | No | Type/read safety, not directory durability |
| `research/brainvision/durable_evidence_publication_replay_v0_3.py` | `replay_publication_chain` | Replay J1 chain with durability evidence | Cross-platform replay | No | No | No | Rejects unverified durability evidence |
| `research/brainvision/durable_evidence_publication_recovery_replay_v0_3.py` | `replay_publication_recovery_chain` | Replay J2 chain with durability evidence | Cross-platform replay | No | No | No | Rejects unverified durability evidence |

Existing implementation evidence:

```text
file-content write path =
exclusive create, write, flush, os.fsync, close, read-back byte compare, SHA-256 compare

directory-entry durability path =
adapter.sync_directory_entry(directory_path)

default adapter status =
DIRECTORY_DURABILITY_UNCONFIRMED

durable acceptance status =
DURABLE_ACCEPTED only when adapter returns DIRECTORY_DURABILITY_CONFIRMED
```

This is a fail-closed architecture seam, not a validated Windows primitive.

## 7. WINDOWS-SPECIFIC MECHANISMS

Investigation targets:

```text
CreateFileW on directories
FILE_FLAG_BACKUP_SEMANTICS
FILE_FLAG_WRITE_THROUGH
FlushFileBuffers
MoveFileExW
ReplaceFileW
MOVEFILE_WRITE_THROUGH
directory-handle flushing
parent-directory flushing
volume flushing
write-through rename or replacement
```

Existing implementation evidence from source search:

```text
CreateFileW usage                         = absent
FILE_FLAG_BACKUP_SEMANTICS usage          = absent
FILE_FLAG_WRITE_THROUGH usage             = absent
FlushFileBuffers usage                    = absent
MoveFileExW usage                         = absent
ReplaceFileW usage                        = absent
MOVEFILE_WRITE_THROUGH usage              = absent
ctypes or pywin32 Win32 bridge            = absent in durable-evidence modules
directory-handle flushing implementation  = absent
parent-directory flushing implementation  = absent
volume flushing implementation            = absent
```

The current Windows-specific mechanism is limited to path normalization via the
`\\?\` extended-length prefix in the primary writer, durability evidence, and
replay readers. Long-path support does not establish directory-entry
durability.

Test evidence:

```text
test_fail_closed_platform_stubs_do_not_claim_validation
```

confirms that fail-closed durability and promotion stubs return unconfirmed
statuses. Positive tests use pytest-local synthetic adapters, not real Win32
directory synchronization.

Unresolved question:

```text
Which exact Windows API sequence, supported filesystem set, error taxonomy,
and post-call verification criteria are sufficient for this project to classify
a directory entry as DIRECTORY_DURABILITY_CONFIRMED?
```

## 8. PUBLICATION SEQUENCING

Committed publication path:

```text
validate anchor
consume synthetic publication authority
create publication chain directory
write durable PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED record
write durable PUBLICATION_ATTEMPTED record
resource preflight
complete in-memory artifact generation
artifact-set validation
synthetic staging-capacity validation
create staging directory
write each artifact with flush, os.fsync, read-back verification
verify staging artifact inventory and hashes
call durability_adapter.sync_directory_entry(staging_directory)
fail closed if staging directory durability is unconfirmed
fail closed if final directory exists
call promotion_adapter.promote_verified_directory_no_replace(staging, final)
fail closed if promotion is unconfirmed
verify final artifact inventory and hashes
write durable PUBLICATION_COMPLETED record
return PUBLICATION_COMPLETED
```

Sequencing classifications:

| Question | Classification | Evidence |
|---|---|---|
| Artifact bytes durable before promotion | PARTIALLY_ESTABLISHED | `_stage_publication_artifacts` writes, flushes, `os.fsync`s, closes, and read-backs each file before promotion; directory-entry durability remains adapter-dependent. |
| Staging directory entries durable before promotion | PARTIALLY_ESTABLISHED | `project_publication` gates promotion on `sync_directory_entry(staging_directory) == DIRECTORY_DURABILITY_CONFIRMED`; the real Windows primitive is absent. |
| Promotion rename durable before final verification | NOT_ESTABLISHED | Default promotion adapter is fail closed; no concrete same-volume no-replace or write-through rename implementation exists. |
| Final directory entry durable before `PUBLICATION_COMPLETED` | NOT_ESTABLISHED | Final verification checks visible bytes and hashes; a concrete post-promotion parent-directory sync is not implemented. |
| Parent-directory metadata durable before `PUBLICATION_COMPLETED` | NOT_ESTABLISHED | No parent-directory handle flush or platform support matrix exists. |
| `PUBLICATION_COMPLETED` withheld on unconfirmed durability | ESTABLISHED | Primary writer, staging durability gate, promotion gate, and completed-record durability check all fail closed when adapters do not confirm. |

The current guarantee is therefore structural and fail-closed. It does not
establish real Windows directory-entry persistence.

## 9. RECOVERY AND EVIDENCE EFFECTS

Committed recovery path:

```text
validate recovery anchor
consume synthetic recovery authority
create recovery chain directory
write durable PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED record
write durable PUBLICATION_RECOVERY_ATTEMPTED record
validate recovery policy identity and resource boundary
replay original publication chain
verify final directory exists
read exact final artifact inventory through bounded file admission
validate canonical bytes, semantic content, regenerated bytes, and expected hashes
write durable PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED record
write durable PUBLICATION_RECOVERY_EVIDENCE_COMPLETED record
return PUBLICATION_RECOVERY_EVIDENCE_COMPLETED
```

Failure and evidence semantics:

| Condition | Existing classification or state | Assessment |
|---|---|---|
| Directory durability unsupported by default adapter | `DIRECTORY_DURABILITY_UNCONFIRMED`; primary writer returns `BYTE_VALID_DURABILITY_UNCONFIRMED` | Fails closed for durable acceptance. |
| Record write lacks confirmed durability | `PUBLICATION_CHAIN_GENESIS_WRITE_FAILED`, `PUBLICATION_ATTEMPTED_WRITE_FAILED`, `PUBLICATION_ARTIFACTS_VERIFIED_PUBLICATION_COMPLETED_RECORD_FAILED`, or `PUBLICATION_RECOVERY_EVIDENCE_WRITE_FAILED` depending on phase | Deterministic enough for current synthetic machinery, but not a detailed Windows error taxonomy. |
| Staging directory durability unconfirmed | `PUBLICATION_STAGING_DURABILITY_UNCONFIRMED` | Publication completion withheld. |
| Promotion unconfirmed | `PUBLICATION_PROMOTION_FAILED` or synthetic indeterminate classification when explicitly injected | Publication completion withheld; staging retained. |
| Final directory missing during recovery | `PUBLICATION_RECOVERY_FINAL_DIRECTORY_MISSING` | J2 completion withheld. |
| Final directory invalid or artifact mismatch | `PUBLICATION_RECOVERY_FINAL_DIRECTORY_INVALID` or `PUBLICATION_RECOVERY_ARTIFACT_HASH_MISMATCH` | J2 completion withheld. |
| Recovery artifact type/read/resource rejection | Resource failure or indeterminate J2 classifications | J2 verified/completed records withheld. |

The implementation preserves the original scientific result and does not
mutate final artifacts during recovery. Recovery may verify visible
already-existing final artifacts under separate J2 evidence, but recovery does
not prove the original J1 completion and does not reconstruct original J1
publication completion.

Gap:

```text
Unsupported, unavailable, denied, indeterminate, partial pre-promotion success,
partial post-promotion success, and filesystem-support mismatch are not yet
separated by a BLOCKER-1 Windows-specific failure vocabulary.
```

## 10. EXISTING TEST EVIDENCE

Relevant test evidence:

| Test file | Test names or categories | Platform | Synthetic/live | Proves | Does not prove |
|---|---|---|---|---|---|
| `research/brainvision/test_durable_evidence_core_v0_3.py` | `test_immutable_no_overwrite_and_byte_verification` | Cross-platform | Synthetic pytest-local | Exclusive create, byte read-back, synthetic confirmed durability acceptance | Real Windows directory durability |
| `research/brainvision/test_durable_evidence_core_v0_3.py` | `test_fail_closed_platform_stubs_do_not_claim_validation` | Cross-platform | Synthetic pytest-local | Default durability and promotion stubs return unconfirmed | Concrete Win32 primitive behavior |
| `research/brainvision/test_durable_evidence_authority_v0_3.py` | confirmed/unconfirmed durability evidence tests | Cross-platform | Synthetic pytest-local | Replay and authority recognition require verified durability evidence | Real directory flush correctness |
| `research/brainvision/test_durable_evidence_publication_v0_3.py` | `ConfirmedSyntheticAdapter`, `PositiveTmpPromotionAdapter`, successful projection tests | Cross-platform | Synthetic pytest-local | J1 can complete only under explicit synthetic positive adapters | Real same-volume no-replace promotion or directory sync |
| `research/brainvision/test_durable_evidence_publication_v0_3.py` | `test_default_promotion_adapter_fails_closed_and_retains_staging` | Cross-platform | Synthetic pytest-local | Default promotion failure withholds `PUBLICATION_COMPLETED` and retains staging | Real promotion failure modes |
| `research/brainvision/test_durable_evidence_publication_v0_3.py` | staging/final collision and final read-back mismatch tests | Cross-platform | Synthetic pytest-local | Collision and final verification failure paths fail closed | Crash/power-loss persistence |
| `research/brainvision/test_durable_evidence_publication_resource_bounds_v0_3.py` | `test_later_stage_classifications_are_preserved_after_positive_capacity` | Cross-platform | Synthetic pytest-local | Resource-capacity success does not hide later promotion failure | Real disk capacity or durability |
| `research/brainvision/test_durable_evidence_publication_replay_v0_3.py` | `test_publication_replay_requires_verified_durability` | Cross-platform | Synthetic pytest-local | Replay refuses an empty durability ledger | Real platform persistence |
| `research/brainvision/test_durable_evidence_publication_recovery_v0_3.py` | final missing/invalid/hash mismatch and no-artifact-mutation tests | Cross-platform | Synthetic pytest-local | J2 withholds completion and avoids artifact mutation | Real recovery from crash states |
| `research/brainvision/test_durable_evidence_publication_recovery_resource_bounds_v0_3.py` | non-mutation and resource rejection tests | Cross-platform; symlink case POSIX-executed, Windows skipped if unsupported | Synthetic pytest-local | J2 resource rejection preserves original J1 chain/final artifacts | Directory-entry durability |
| `research/brainvision/test_durable_evidence_publication_recovery_replay_v0_3.py` | `test_recovery_replay_requires_verified_durability` | Cross-platform | Synthetic pytest-local | J2 replay refuses unverified durability evidence | Real platform persistence |
| `research/brainvision/test_durable_evidence_publication_boundary_v0_3.py` | J1 import/path boundary tests | Cross-platform | Synthetic pytest-local/source inspection | No science/manifest/kernel surface and publication path ownership bounds | Windows directory durability |
| `research/brainvision/test_durable_evidence_publication_recovery_boundary_v0_3.py` | J2 import/mutation boundary tests | Cross-platform | Synthetic pytest-local/source inspection | J2 imports no projector/promotion/science and writes no final artifacts | Windows directory durability |

No destructive, live, privilege-sensitive, crash, or power-loss tests were run
for this assessment. Existing evidence was sufficient to identify the current
gap.

## 11. BLOCKER-1 OBLIGATION MATRIX

| Obligation | Classification | Repository evidence |
|---|---|---|
| B1.1 file-content durability before promotion | PARTIALLY_SATISFIED | Primary writer and staging artifact writer use exclusive create/write/flush/`os.fsync`/read-back. This is file-content evidence, not directory-entry durability. |
| B1.2 staging-directory entry durability | PARTIALLY_SATISFIED | `project_publication` gates promotion on `sync_directory_entry(staging_directory)`; no concrete Windows directory-sync primitive is implemented. |
| B1.3 promotion-operation durability | NOT_APPLICABLE | Same-volume no-replace promotion operation, ownership, replacement prevention, and post-promotion ambiguity are BLOCKER-2 obligations. |
| B1.4 final parent-directory durability | NOT_SATISFIED | No concrete parent-directory flush or post-promotion directory-entry durability primitive exists. Finalization context intersects BLOCKER-2. |
| B1.5 durable-completion gating | SATISFIED | `PUBLICATION_COMPLETED` and J2 completed records require durable write evidence; unconfirmed adapters withhold completion. |
| B1.6 Windows unsupported/indeterminate handling | PARTIALLY_SATISFIED | Default adapters fail closed as unconfirmed, but Windows-specific unsupported, unavailable, denied, indeterminate, partial-success, and filesystem-support cases are not separated. |
| B1.7 deterministic failure mapping | PARTIALLY_SATISFIED | Current synthetic mappings exist (`BYTE_VALID_DURABILITY_UNCONFIRMED`, write-failed classifications, `PUBLICATION_STAGING_DURABILITY_UNCONFIRMED`), but no BLOCKER-1-specific Windows taxonomy exists. |
| B1.8 non-mutation and evidence preservation | SATISFIED | Tests preserve original scientific result boundaries, J1/J2 chain separation, final artifacts, and recovery non-mutation. |
| B1.9 synthetic testability | SATISFIED | Existing adapter seams and pytest-local adapters are safely testable without real data. |
| B1.10 cross-platform separation | SATISFIED | Platform-dependent durability and promotion are isolated behind adapter interfaces; default behavior fails closed. |

Overall matrix result:

```text
BLOCKER-1 is not satisfied.
The architecture is ready for a separate BLOCKER-1 specification.
```

## 12. GAP CLASSIFICATION

| Topic | Classification | Assessment |
|---|---|---|
| File flush and read-back | NON_BINDING_FUTURE_HARDENING | Existing code performs file flush, `os.fsync`, close, read-back, and hash verification. Further handle-flag hardening may be considered later but is not the central BLOCKER-1 gap. |
| Directory flush primitive | BLOCKER_1_BINDING | No concrete Windows directory-entry sync implementation exists. |
| Parent directory persistence | BLOCKER_1_BINDING | No parent-directory handle/flush support matrix exists. |
| Filesystem support detection | BLOCKER_1_BINDING | The spec must decide supported filesystems and fail-closed unsupported cases. |
| Unsupported/unavailable/denied/indeterminate vocabulary | BLOCKER_1_BINDING | Current `UNCONFIRMED` collapse is safe but not precise enough for a closure proof. |
| Staging-directory entry durability | BLOCKER_1_BINDING | Gating exists, but real Windows primitive and tests are absent. |
| Rename persistence and no-replace promotion operation | BLOCKER_2 | Promotion semantics are explicitly decomposed separately. |
| Final directory ownership and attribution after promotion | BLOCKER_2 | Requires promotion-specific ownership and ambiguity handling beyond BLOCKER-1. |
| Network filesystems | BLOCKER_1_BINDING | A BLOCKER-1 spec must either exclude them or define fail-closed support detection. |
| Removable drives | BLOCKER_1_BINDING | A BLOCKER-1 spec must either exclude them or define fail-closed support detection. |
| FAT/exFAT/NTFS/ReFS differences | BLOCKER_1_BINDING | A BLOCKER-1 spec must define the supported Windows filesystem claim. |
| Concurrent mutation | NON_BINDING_FUTURE_HARDENING | Current immutable and no-replace seams reduce some risks; full concurrency is not assigned to BLOCKER-1 by governing docs. |
| TOCTOU races | NON_BINDING_FUTURE_HARDENING | Relevant to future hardening and BLOCKER-2; not sufficient to reopen BLOCKER-1 definition by itself. |
| Power-loss testing | NOT_AUTHORIZED | Governing docs do not authorize physical power-loss tests in this phase. |
| Crash consistency | OUT_OF_SCOPE | On-host evidence does not prove volume/host/power-loss survival; do not fold that into this assessment. |
| Real capacity | OUT_OF_SCOPE | Resource admissibility was BLOCKER-3; real free-space is not a BLOCKER-1 closure requirement here. |
| Real result trees | OUT_OF_SCOPE | Real data and result-tree contact are not authorized. |
| Production privilege handling | OUT_OF_SCOPE | Production readiness and privilege deployment are not part of this synthetic/offline assessment. |

## 13. LIVE-TEST ASSESSMENT

Live-test lane:

```text
NO_LIVE_TEST_LANE_OPEN
```

No governing document presently authorizes live durability probes, live
publication, live recovery, destructive crash testing, process termination,
power-loss simulation, real-data contact, or production-platform proof work.

Future validation lanes:

| Lane | Classification | Assessment |
|---|---|---|
| Pure unit tests | FUTURE_AFTER_SPECIFICATION | Appropriate first validation for adapter response validation and failure mapping after a spec exists. |
| Synthetic adapter tests | FUTURE_AFTER_SPECIFICATION | Appropriate for fail-closed unsupported/denied/indeterminate cases. |
| Isolated temporary-directory integration tests | FUTURE_AFTER_SPECIFICATION | May be specified for non-destructive directory sync behavior if bounded and authorized. |
| Windows-only non-destructive durability probes | FUTURE_AFTER_SPECIFICATION | May be considered only after the spec defines exact API, environment, and failure criteria. |
| Subprocess interruption tests | FUTURE_AFTER_IMPLEMENTATION | Useful later for failure windows, but not authorized now. |
| VM crash tests | NOT_AUTHORIZED | Too broad for this assessment and not required before specification. |
| Physical power-loss tests | OUT_OF_SCOPE | Not authorized and not required for the immediate BLOCKER-1 specification lane. |

## 14. REQUIRED NEXT DOCUMENT

Recommended state:

```text
State B =
BLOCKER_1_SPECIFICATION_REQUIRED
```

Reason:

```text
The governing obligation is clear enough to specify:
validated Windows directory-entry durability primitive/adapter,
fail-closed when unsupported or indeterminate,
and no claim from byte read-back alone.

A bounded implementation gap exists:
no concrete Windows directory-entry sync primitive, no support matrix,
no detailed Windows failure taxonomy, and no non-destructive validation plan.
```

Recommended next docs-only action:

```text
SEPARATE_DOCS_ONLY_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_SPECIFICATION
```

That specification should define at minimum:

```text
exact supported Windows filesystem/environment claim
exact directory-entry durability object being synchronized
required Win32 or Python API sequence, if any
support detection and fail-closed unsupported status
unavailable/denied/indeterminate/partial-success taxonomy
adapter result fields and validation
which parent directories must be synchronized for stored records, bundles,
publication chains, staging directories, and recovery chains
which promotion-related directory operations remain BLOCKER-2
non-destructive synthetic and Windows-only validation strategy
stop conditions for crash/power-loss, real data, production, and live publication
```

No implementation is authorized by this assessment.

## 15. FORMAL-HOLD AND MODE-0 BOUNDARIES

Preserve exactly:

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

Project blocker state:

```text
BLOCKER-3 =
CLOSED_WITHIN_AUTHORIZED_SYNTHETIC_OFFLINE_STAGE_S3B_V0_3_SCOPE

BLOCKER-1 = open
BLOCKER-2 = open
BLOCKER-4 = open
```

This assessment does not establish:

```text
platform readiness
production readiness
real publication
real recovery
scientific closure
live-test authorization
implementation authorization
kernel integration
memory-system integration
```

## 16. CONCLUSION

Current guarantee:

```text
The current Stage S3B v0.3 machinery has fail-closed durability adapter seams,
file-content flush/fsync/read-back evidence, replay gating on verified
durability evidence, publication completion gating, recovery evidence gating,
and synthetic pytest-local tests.
```

Exact remaining gap:

```text
BLOCKER-1 still lacks a specified and validated Windows directory-entry
durability primitive/adapter, including exact supported environment,
parent-directory synchronization target, error taxonomy, unsupported handling,
and non-destructive validation plan.
```

Implementation needed:

```text
yes, after a separate specification and authorization
```

Live tests justified now:

```text
NO_LIVE_TEST_LANE_OPEN
```

Recommended next docs-only action:

```text
SEPARATE_DOCS_ONLY_BLOCKER_1_WINDOWS_DIRECTORY_DURABILITY_SPECIFICATION
```

Primary verdict:

```text
B. BLOCKER_1_READY_FOR_SPECIFICATION
```
