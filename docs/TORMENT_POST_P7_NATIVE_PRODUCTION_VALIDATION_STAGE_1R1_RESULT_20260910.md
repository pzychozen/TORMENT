# TORMENT Post-P7 Native Production Validation - Stage 1R1 Result

Date: 2026-09-10

## Verdict

```text
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R1 = HELD_FOR_HOST_PROOF_EVIDENCE
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
```

The exact seven-field host profile was recovered from the selected core's
immutable root admission record. Its digest matches the selected deployment,
core witness, and version-2 completion witness. The existing read-only resolver
returns `NATIVE_AGREEMENT` for that recovered profile.

An approved generated admission descriptor path could not be established from
current/frozen production evidence. The selected deployment is root-v2, whose
current recovery contract uses immutable evidence inside the selected core and
does not require a host descriptor file. The older descriptor-pair documentation
describes the v1 path; it does not establish a generated descriptor for this
selected root-v2 deployment.

Stage 1R1 section 4 explicitly requires both exact approved inputs and says to
stop when they cannot be established. Accordingly, no service launch was
attempted. A profile-only launch was not substituted for the requested contract.
This is a host-proof requirement reconciliation for review, not a new failed
qualified startup or a contradiction of durable native authority.

## Preflight and preserved attempt 1

```text
STARTING_HEAD = aef53264295a3ca262b90e3eff16dfcd342b1c68
ORIGIN_MAIN_AT_PREFLIGHT = aef53264295a3ca262b90e3eff16dfcd342b1c68
HEAD_EQUALS_ORIGIN_MAIN_AT_PREFLIGHT = YES
TRACKED_WORKTREE_AT_PREFLIGHT = CLEAN
VALIDATION_END_HEAD = aef53264295a3ca262b90e3eff16dfcd342b1c68
STAGE_1_ATTEMPT_1 = HELD_FOR_REVIEW
ATTEMPT_1_STARTUP_COMMAND = INCOMPLETE_FOR_QUALIFIED_NATIVE_HOST
BARE_STARTUP_WAS_NOT_THE_QUALIFIED_NATIVE_STARTUP_CONTRACT = YES
PREVIOUS_STAGE_1_RECORD_UNCHANGED = YES
```

Repository: `C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric`.
Preflight was captured at `2026-09-10T05:17:03.9799655Z`; no listener occupied
port 8787. The previous Stage-1 record was neither modified nor superseded.
Its working-file SHA-256 remained
`71750ddfd33c195a8b947036fd2bf758f4e8768ad1cb6b40040ac0fafc5438b2`.

## Recovered host proof and durable authority

The observation ran once through Windows CMD after activating `torment`:

```bat
call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment
python C:\TORMENT\TORMENT_administration\post-p7-stage-1r1-20260910\inspect_host_proof.py
```

The inspection script calls the existing read-only selector reader,
contained-core inspector, exact root-envelope reader, and deployment resolver.
It constructs no service/runtime owner and invokes no migration transition.
It returned exit code 0, with observation time
`2026-09-10T05:18:04.439521+00:00` and interpreter
`C:\Users\Notandi\miniconda3\envs\torment\python.exe`.

The authoritative profile source is
`RootAdmissionEnvelopeRecord.effective_profile_payload`, loaded from the core
selected by the current selector and its activation-completion witness. The
same recovery source is used by the frozen post-P7 verification and bounded
native smoke artifacts. No values were chosen to obtain a passing launch.

```text
HOST_PROFILE_FIELD_COUNT = 7
HOST_PROFILE_DIGEST = 35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a
ROOT_ADMISSION_ENVELOPE_DIGEST = e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb
SELECTOR_GENERATION = 8
SELECTOR_STATE = NATIVE_ACTIVE
SELECTED_CORE_ID = f21c730f-5222-4aa8-9a5f-1c1188456df3
CORE_ROLE = ACTIVE_CORE
CORE_DEPLOYMENT_STATE = NATIVE_ACTIVE
EVER_ACTIVE = TRUE
COMPLETION_CONTRACT = TORMENT_ROOT_ADMISSION_COMPLETION_WITNESS
COMPLETION_VERSION = 2
READ_ONLY_DEPLOYMENT_RESOLUTION = NATIVE_AGREEMENT
```

The profile has the existing seven field names: `compression_enabled`,
`deep_memory_enabled`, `representation_provider`, `representation_model`,
`representation_dimension`, `admitted_scope_plan_digest`, and
`external_owner_digest`. Its representation is `st` / `BAAI/bge-small-en-v1.5` /
384 dimensions, with compression and deep memory disabled. CPU and strict
embedder settings are specified by the work order but were not applied to any
service process because launch was not reached.

The typed profile digest was checked against the selector, core deployment
witness, completion witness, and stored envelope payload. The selected admission
identity is the root-envelope digest, not evidence of a descriptor filename.
Before/after SHA-256 fingerprints of the selected core and selector databases
and their WAL files matched. No root-wide migration census or P1-P7 proof
campaign was run.

## Descriptor evidence and contract difference

The following current sources distinguish the two recovery contracts:

- `docs/TORMENT_MEMORY_SUBSTRATE_POST_I4_ROOT_V2_PRODUCTION_RECOVERY_BRIDGE_QUALIFICATION_v0.1.md:49`
  states that root-v2 host configuration no longer requires a descriptor path.
- `torment_service/substrate/production_native_owner.py:219` selects root-v2
  recovery from the durable completion witness. The descriptor-file requirement
  occurs in the v1 branch at line 230.
- `torment_service/public_runtime.py:1097` documents the root-v2 startup branch
  as having no host descriptor dependency.
- The frozen `real-root-disposition-p7-20260910/run_post_p7_bounded_native_smoke.py`
  constructs its original and restarted native owners without a descriptor path
  (lines 253 and 340). This is prior owner-level evidence, not a full-service
  success established by this attempt.
- `docs/BLOCKER_5_A6_PRODUCTION_SHAPED_ADMINISTRATION_REHEARSAL.md:93` describes
  the older profile/descriptor pair. No current selected-deployment file path is
  supplied there.

Targeted searches of the real P2, corrected P3, P5, P6, and disposition/P7
administration directories found no non-fixture `*descriptor*.json` candidate.
The current P3/P6/P7 runner sources contain no `admission_descriptor_path` or
`TORMENT_ADMISSION_DESCRIPTOR_PATH` assignment. Test fixtures, snapshots, and
workspace content were excluded from the candidate search. These results mean
no approved matching path was established; they do not assert that no
descriptor-like file exists anywhere on disk.

No root admission record was exported as a substitute descriptor. No unrelated
JSON file or historical fixture was supplied to satisfy the environment parser.
No configuration, `.env`, application default, or startup code was changed.

## Result matrix

`NOT_RUN` marks all service-dependent checks because the host-proof recovery
gate stopped this attempt before launch. `SELECTOR_CORE_AGREEMENT = PASS` refers
only to the existing read-only durable resolver; it is not running-owner
recognition. Descriptor `NO` means the required approved path was not
established, rather than a recovered file being proven mismatched. Observation
fields marked `NO` do not claim coverage of unexecuted runtime behavior.

```text
POST_P7_STAGE_1R1_PREFLIGHT = PASS
HOST_PROFILE_FOUND = YES
ADMISSION_DESCRIPTOR_FOUND = NO
HOST_PROFILE_MATCHES_SELECTED_DEPLOYMENT = YES
ADMISSION_DESCRIPTOR_MATCHES_SELECTED_DEPLOYMENT = NO
QUALIFIED_HOST_PROOF_STARTUP = NOT_RUN
NORMAL_PRODUCTION_STARTUP = NOT_RUN
NATIVE_OWNER_RECOGNITION = NOT_RUN
SELECTOR_CORE_AGREEMENT = PASS
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
MAINTENANCE_ONLY_POSTURE = NOT_RUN
PRIVATE_NATIVE_QUERY = NOT_RUN
SHARED_NATIVE_QUERY = NOT_RUN
TEXT_SEARCH = NOT_RUN
VECTOR_SEARCH = NOT_RUN
PRIVATE_SHARED_SCOPE_ISOLATION = NOT_RUN
NATIVE_MEMORY_WRITE = NOT_RUN
WRITE_THEN_READ = NOT_RUN
NATIVE_REINFORCEMENT = NOT_RUN
CHARACTER_CONTINUITY_PRE_RESTART = NOT_RUN
NATIVE_TRAJECTORY_WRITE = NOT_RUN
NORMAL_SHUTDOWN = NOT_RUN
RESTART_STARTUP = NOT_RUN
MEMORY_PERSISTENCE_AFTER_RESTART = NOT_RUN
REINFORCEMENT_PERSISTENCE_AFTER_RESTART = NOT_RUN
CHARACTER_CONTINUITY_AFTER_RESTART = NOT_RUN
PRIVATE_QUERY_AFTER_RESTART = NOT_RUN
SHARED_QUERY_AFTER_RESTART = NOT_RUN
TRAJECTORY_AUTHORITY_RECONSTRUCTION = NOT_RUN
POST_RESTART_NATIVE_TRAJECTORY_WRITE = NOT_RUN
MODEL_D_PRESERVED = NOT_OBSERVED
CERTIFIED_REFUSAL_RUNTIME_LEAK_OBSERVED = NO
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R1 = HELD_FOR_HOST_PROOF_EVIDENCE
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R1_REVIEW
```

No production requests, memory mutations, reinforcement, Character changes,
trajectory writes, shutdown/restart, or unit/integration tests were executed.
No production code was changed. Pre-existing untracked files remain untouched.

## Evidence and publication

Local evidence directory:
`C:\TORMENT\TORMENT_administration\post-p7-stage-1r1-20260910`.

| Evidence | SHA-256 |
| --- | --- |
| `host_proof_observation.json` | `727be157548d7b80114436e807a099e55a0aac308f2f692e4ccec02c15e70feb` |
| `descriptor_recovery_evidence.json` | `0bfb6337e9efa19204e009cccddc328165f7349e0b19eaa1223ddd3615a01577` |
| `inspect_host_proof.py` | `fb52c4924106524467d1ec0bf2886e563612fee941a23f08527e05f4d1e6f02e` |
| `preflight.json` | `af7933b318b4ee3c4a0dcad4f415c5cf40afa1ca53f64ff3d30596d556f6a315` |

`evidence_manifest.json` records the same hashes and file sizes. The exact
profile was recovered in memory, not persisted as startup configuration.
Only necessary profile/authority observations were retained; no credentials,
idempotency keys, or memory payloads were collected.

The sole repository change is this new record. The previous Stage-1 record is
preserved. Publication follows the existing evidence-only policy, with
`git diff --check` and a staged whitespace check before committing and pushing.

`FINAL_HEAD` / `COMMIT` identifies the commit containing this record, resolvable
with `git log -1 --format=%H -- docs/TORMENT_POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R1_RESULT_20260910.md`.
Its own literal SHA cannot be embedded in its committed contents. Exact
`FINAL_HEAD`, `ORIGIN_MAIN`, remote main SHA, `HEAD_EQUALS_ORIGIN_MAIN`,
`TRACKED_WORKTREE`, and `COMMIT` are captured after publication in
`publication_verification.json` in the evidence directory and returned with
delivery.

Review must reconcile the requested descriptor-pair startup contract with the
selected root-v2 recovery contract before the bounded production retry resumes.
