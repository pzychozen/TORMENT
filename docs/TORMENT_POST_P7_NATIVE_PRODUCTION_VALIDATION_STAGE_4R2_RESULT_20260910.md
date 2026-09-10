# TORMENT — Stage 4R2 disposable failure / recovery administration

2026-09-10 UTC. **POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4R2 =
BLOCKED_TRAJECTORY_RECOVERY_REVIEW.** The aggregate Stage-4 verdict has the same
status; `SQLITE_MIGRATION_FULLY_VALIDATED = NO`.

All requested scenario-specific memory, receipt, lock, fencing, authority and
integrity checks passed on four fresh R1-qualified roots. Production remained
byte-identical. A and B nevertheless finish with invalid sealed trajectory
verification: each retains its original crash partial and reports
`MANIFEST_SEQUENCE_GAP` and `INCOMPLETE_FINAL_CHUNK`. Current source explicitly
preserves these remnants, and an existing test expects invalid verification
after this kind of restart. This is an unresolved acceptance question for
aggregate Stage 4, not evidence of SQLite corruption or a newly introduced
authority defect. R2 neither repairs the archives nor waives the finding.

## Execution and Git boundary

Starting HEAD = origin/main =
`9463def30db4031bb07ff2dbce8dd39bbc89f6ce`; branch `main`, tracked worktree clean.
P1–P7, Stages 1–3 and the R1 qualification remain closed. This result document is
the only repository change. External `publication.json` records the final
evidence-only commit, actual remote equality, clean tracked worktree, unchanged
untracked listing and evidence verification; the final return supplies that
commit without requiring a self-referential document hash.

All project Python used Windows CMD with `conda activate torment`:
`C:\Users\Notandi\miniconda3\envs\torment\python.exe`, SQLite 3.53.4.
Service embedding health identified local offline `BAAI/bge-small-en-v1.5`,
384 dimensions, without degraded mode. No conversational/generative model or
external AI API participated. No production application code, schema, indexes,
PRAGMAs, busy timeout, retry logic, BGE, motif or authority semantics changed.

The prior Stage-4 and R1 reports are frozen at these SHA-256 values respectively:

```text
e8c2ce64509171151288eceff0834919a8dc737201bce1e30c347b9fb074b91b
7dac894dfb0a899985e8aaf5d84d490fdc9aaebd5583926c6352249e98dad384
```

## Fresh roots and baseline qualification

External evidence directory, called `EVIDENCE` below:
`C:\TORMENT\TORMENT_administration\post-p7-stage-4r2-20260910`.
Every evidence filename below is relative to that directory. Each disposable
root is `EVIDENCE\<case>\root`, with core file
`substrate\cores\root-r1.db` under that root.

| Case | Fresh core UUID | Baseline valid | Native trajectory generation, baseline → final |
| --- | --- | --- | --- |
| A | `dbf1fdc8-c567-48bb-9d79-62760769dd2e` | YES | 4 → 5 |
| B | `bccbcb31-1395-4f39-bf70-4c84f3329e2b` | YES | 4 → 5 |
| C | `e8b1314c-945f-4ecb-8838-98881fe4248b` | YES | 4 → 4 |
| D | `8833463e-f961-4cbf-a822-8315fdc8d147` | YES | 4 → 5 → 6 → 7 |

All four roots used
`EXISTING_SYNTHETIC_ROOT_BUILDER_WITH_PRODUCTION_CUTOVER_AND_HANDOFF`.
The R1 constructor sequence and pre-admission Model-D request composition were
unchanged. Only the external builder's read-only production fingerprint guard
points to the common R2 preflight. `r1_reuse.json` binds the reused R1 evidence
manifest, SHA-256
`24bcf030346333a13fe23b4233fb2c6dd786e5ddd53c4a5b4d6f1472b5b80e6e`.
No active production core or authority database was copied or re-rooted.

The synthetic identity label `post-i4-r1:root` is shared by construction; each
deployment has its own core, scopes, profile/envelope digests and absolute
artifact paths. Each contains five admitted scopes: north/private/same-agent,
north/private/second-agent, north/shared/common-domain, south/private/same-agent
and south/shared/common-domain. Each selector is generation 2, NATIVE_ACTIVE,
with correct core agreement. Qualified handoff admitted native authority and
fenced legacy authority at generation 2 before ordinary startup.

Before any injection, each root passed 12 checks in `<case>/baseline_valid.json`:
fresh qualified authority, NATIVE health, ordinary shared-fixture read, ordinary
private ingest, exact read-after-write, four durable receipt stages, native
agreement, Model D, no orphan publication, SQLite integrity, valid live
trajectory and contained paths. The ordinary write created private EID 8 at
step 1000701, with READY/USABLE current representation, and one trajectory frame
containing two records. Its receipts were RESERVED, COGNITION_STARTED, PREPARED,
COMPLETE. Shared fixture EID 7 was read through the normal recall surface.

The R1 limitation remains: historical private fixture EID 7 lacks `user_id` and
is not searchable through the ordinary private filter. Its synthetic historical
vectors and Character inputs are not production-history validation. The shared
fixture read and new ordinary private write/read qualify the baseline without
altering that fixture. `NONEMPTY_SHARED_RANKING = NOT_YET_VALIDATED` remains frozen.

## A — committed memory survives abrupt process death

After baseline completion and read-back, Win32 `TerminateProcess` terminated
service PID 37864 with exit 73. The helper matched the conda executable, ordinary
`python -m torment_service` command, parent launcher, prelaunch root and listener
before acting. No normal application shutdown ran. `A/run1/abrupt_termination.json`
and the correctly ordered `A/after_actual_death.json` establish this boundary.

Ordinary restart `A/run3`, PID 64644, reconstructed NATIVE authority. The original
committed memory was returned by `A/survived_read.json`. Baseline, actual post-death
and post-restart snapshots have identical committed-memory inventories and exact
identity for the subject memory:

| Durable identity | Value |
| --- | --- |
| Object | `65e7d23f-ae16-46fd-90da-c2220007fade` |
| Current revision | `5ace9a36-fd3a-4872-bf4d-fe4d21ee91f8` |
| Revision ordinal / EID | 2 / 8 |
| Private semantic scope | `85c01230-1b62-4963-92c0-2082ce070b81` |
| Workspace / agent | north / same-agent |
| Summary SHA-256 | `6227e24ecc4af0ed07c7414541644601ed494fa6da616326531df95b337980f8` |
| Payload SHA-256 | `49707a58367eb8fc9520051a21bcd655557b4d849919b503288b0bee7850081f` |

Other-agent and other-workspace private queries did not return this memory.
Character hashes were unchanged across death and recovery. A further ordinary
write/read created EID 9, completed all four receipts, and exercised the recovered
native trajectory writer at generation 5. Final normal shutdown exited 0.

`A_UNCLEAN_RESTART`, committed-memory survival, lineage, scope isolation,
selector/core agreement and all SQLite/foreign-key checks are PASS;
`A_NATIVE_ACTIVE = YES`, `A_LEGACY_FALLBACK = NO`. Sealed trajectory verification
has the separate retained-crash finding below.

Administration errors are retained in `administration_notes.json`. The first
termination helper failed to import unavailable `psutil` before taking action.
A premature `A/run2` launch, PID 10656, occurred while run1 was still alive; it
refused occupied port 8787, served no request, shut down normally and exited 1.
`A/after_death.json` is therefore mislabeled: it was taken before actual death
and is excluded from the recovery proof. Its memories, operations,
representations, trajectory authority/intents/artifacts and Character hashes
equal the baseline. A port-absence guard was added to later external launchers.
There was one actual abrupt termination; run3 is the actual recovery restart.

## B — controlled PREPARED interruption and same-key recovery

`b_hook_service.py` ran the ordinary application with a thin administration-only
wrapper around `NativePublicIngestExecutor.execute`. After baseline qualification,
only the exact target key used the existing `_test_interrupt_after="PREPARED"`
hook. The wrapper checked disposable root/core and request scope, invoked the
existing implementation, caught `NativePublicIngestInterruption`, durably recorded
the boundary and executed `os._exit(74)` once. Application shutdown did not run.

`B/interruption_boundary.json` identifies PID 34940 and the exact key:
`stage4r2-B-target-0c788fbc-2171-4808-a73c-611357d3a019`.
RESERVED, COGNITION_STARTED and PREPARED were durable; storage had not been
entered and public COMPLETE was absent. The HTTP client recorded connection
reset, not successful completion. `B/after_interruption.json` contains the same
six memories as the baseline, no target representation and no orphan publication.

Normal restart `B/run2`, PID 32108, used unmodified `python -m torment_service`,
without the wrapper. Before replay, the target remained absent, committed
memories/representations were unchanged, and the three durable target stages
remained unambiguous. Character hashes matched the post-interruption snapshot.
One explicit ordinary replay used the same public key and identical request
body. `B/recovery_write.json` returned HTTP 200, stored=true, EID 9;
`B/recovery_read.json` returned that exact memory. Its identity is:

| Durable identity | Value |
| --- | --- |
| Object | `ec9ed53e-7526-42c7-9b9f-7ce8bb58d467` |
| Current revision | `8375a849-29b8-467f-b568-cba2aff3fdb6` |
| Revision ordinal / EID | 2 / 9 |
| Private semantic scope | `e4bbc551-e50f-4bc1-bcc3-40779138aca8` |
| Summary SHA-256 | `1cac132205e0c637de0cf0d4dee3eba4e0dcd74b2153833adafef8c58b1b5dc4` |

The original PREPARED intent hash was preserved, COMPLETE was added lawfully,
and the final current representation was READY/USABLE with matching integrity.
Baseline EID 8 survived; both scope controls passed. Normal shutdown exited 0.

`B_INTERRUPTION_BOUNDARY_ESTABLISHED = YES`,
`B_INTERRUPTED_WRITE_RECOVERY = PASS`,
`B_WRITE_FINAL_DISPOSITION = FULLY_COMMITTED`. This disposition includes the
explicit same-key recovery replay; startup alone did not publish the target.
Partial memory, orphan READY representation, orphan alias and ambiguous receipt
authority were absent before and after replay. Selector/core agreement passed
and there was no legacy fallback.

This is fresh direct administration of the controlled post-PREPARED,
pre-storage boundary. It does not establish arbitrary mid-SQLite-instruction
crash behavior. No old qualification was substituted for this run.

## C — bounded ordinary SQLite contention

After a qualified baseline, service PID 59012 remained live. `contend_c.py`
opened only C's contained core with ordinary SQLite `mode=rw` and held
`BEGIN IMMEDIATE` without changing rows. It submitted one ordinary native ingest,
observed its request intent and held the lock for a further 0.75 seconds before
releasing with ROLLBACK. Actual total hold was 0.766 seconds; the request was
still pending immediately before release. No application timeout, PRAGMA or
retry setting changed.

`C/contention.json` records HTTP 200 after 3.281 seconds and zero rows changed
by the lock holder. EID 9 was fully published and returned by ordinary read;
baseline EID 8 also remained readable. Health remained NATIVE, both scope
controls passed, and receipts and integrity were coherent. Normal shutdown
exited 0. Final sealed trajectory verification passed: one chunk, two steps,
five records.

`C_LOCK_CONTENTION_BEHAVIOR = CLEAN_WAIT`, with no database corruption, scope
leak or partial write; service recovered after release. The evidence establishes
bounded lock/request overlap and successful completion. It does not measure
SQLite's exact internal wait duration or qualify busy-timeout exhaustion,
refusal, saturation or performance.

## D — stale predecessor fencing and lawful current writer

Baseline service PID 34196 shut down normally, sealing valid chunk 1. The
external `stale_d.py` then used real spawned native trajectory runtimes:
predecessor PID 36448 held generation 5, and successor PID 30884 lawfully acquired
generation 6 with a distinct session. The predecessor attempted
`effect("trajectory_v2_step")` after replacement and received
`TrajectoryHandoffRefused` before entering the effect. The successor's legacy
writer request was also refused; native handoff authority remained intact.

The helper's supplemental current-frame input was incomplete: a
`DynamicRecordV2` lacked `vel0`. The existing writer emitted
`GENESIS_WRITE_FAILED` before publishing a frame. `D/stale_authority.json`
retains `pass=false` for that helper's full expectation, and the diagnostic is
preserved. This input error does not establish current authority refusal.

Current-writer acceptance was completed through ordinary service `D/run2`,
PID 55828. It acquired generation 7 and used the real entity carrier to perform
a normal EID-9 write/read and publish a trajectory frame. A separate bounded
probe reconstructed the exact saved generation-5 token actually issued to the
predecessor; `D/retained_stale_refusal.json` proves refusal against generation 7
before effect entry. No token field, authority identity or generation was forged
or manually edited. Both scope controls passed and the service closed normally,
exit 0.

Final sealed verification passed: two chunks, two steps, five records; contiguous
chunk sequences 1 and 2 in epochs 1 and 4. Empty helper epochs 2 and 3 retain
their lawful boundaries. Chunk 2's previous hash equals chunk 1's SHA-256:

```text
chunk 1: aacf151c885e5be14fdac19451740b1485d83cf53a37b7e5d01e40042b7382a6
chunk 2: 6c04c554546d9eddc4ef96948d0b6c2927eb6609981997fad17630551bbc89b8
```

Stale refusal, current native writer acceptance, monotone generations
4 → 5 → 6 → 7 and trajectory hash-chain validity are PASS.
`D_LEGACY_TRAJECTORY_AUTHORITY_RESTORED = NO`; legacy fence generation remains 2.

## E — recovery authority, scope, Character and integrity

A and B ordinary restarts reconstructed durable NATIVE_AGREEMENT, retained
NATIVE_ACTIVE selector generation 2 and selected their original correct cores.
Both accepted subsequent normal writes under newer lawful native trajectory
sessions. No hidden legacy fallback, automatic rollback authority or restoration
of legacy trajectory authority was observed. All admitted paths remained inside
their respective disposable root.

Every root finished with seven memories: five historical fixtures, the baseline
private EID 8 and one new private EID 9. Both new writes have complete public
receipt stages. EID 9's current representation is READY/USABLE, 384 dimensions,
1,536 payload bytes, with integrity result MATCH. Read-only checks found no
orphan aliases, orphan READY representations or unusable READY publication.

Final `PRAGMA integrity_check` returned `ok`, and `PRAGMA foreign_key_check`
returned no rows for each root's core, selector and trajectory-authority
database: twelve databases in total. No repair followed an integrity failure.
`SQLITE_INTEGRITY_ERROR = NO`, `FOREIGN_KEY_INTEGRITY_ERROR = NO`.

Other-agent and other-workspace private query controls passed in all four
cases. Model D remained unchanged: private `motif_domain_id=None`, with ordinary
operations using admitted `common-domain` and existing strict shared-domain
validation retained. `MODEL_D_PRESERVED = YES`.

Existing synthetic Character/seed/identity hashes matched across A's death and
recovery and B's interruption-to-restart interval before replay.
`CHARACTER_CONTINUITY_AFTER_FAILURE = PASS` is bounded to those existing
fixtures and intervals. No new Character fixture was fabricated. The roots do
not carry an appropriate certified-refusal corpus, so
`CERTIFIED_REFUSAL_RUNTIME_LEAK_OBSERVED = NOT_APPLICABLE`; P3 was not recertified.

## Retained A/B trajectory finding and aggregate decision

In both A and B, the pre-crash epoch-1/chunk-1 partial was valid as an active
live tail before death. Its bytes remain exactly preserved after restart.
The recovered ordinary writer produced and sealed epoch-2/chunk-2. Final
sealed verification returns `valid=false`, one checked chunk, one checked step,
three checked records, and these two issues in each root:

| Issue | Evidence |
| --- | --- |
| `MANIFEST_SEQUENCE_GAP` | Expected chunk sequence 1, actual 2. |
| `INCOMPLETE_FINAL_CHUNK` | Prior epoch's unclosed chunk 1 `.partial` remains. |

The original partial is under
`<case>/root/workspaces/north/agents/same-agent/private/trajectories/v2/chunks/epoch-00000001/chunk-00000000000000000001.partial`.
`assessment.json` compares its baseline/final hashes and retains both failed
verifier reports. No partial was deleted, sealed by administration, rewritten
or excluded to obtain a passing archive.

Narrow source review explains the mechanism. In
`torment_service/kernel/trajectory_v2.py`, `TrajectoryV2Writer` is best-effort;
`_discover_next_seq` considers physical partials, `_discover_next_epoch` advances
from persisted evidence, and `_report_prior_epoch_partials` preserves crash
remnants and emits `ORPHANED_CRASH_PARTIAL`. The native trajectory runtime keeps
writer failures from propagating into cognition. The existing
`tests/test_trajectory_v2.py::TestTrajectoryV2FrameIdentity::test_restart_marks_old_partial_as_orphan_crash_condition`
explicitly expects invalid live verification after restart with a retained
partial. This test was inspected, not rerun or counted as a fresh passing test.
`source_review.json` binds the reviewed source hashes.

The scenario assessment contains 65 passing checks (A 17, B 18, C 14, D 16),
in addition to four passing 12-check baseline qualifications. The A/B sealed
trajectory results are recorded separately and are **not PASS**. The aggregate
review hold is a conservative acceptance decision: the requested memory and
authority contracts pass, but a completely valid sealed trajectory archive
after abrupt death has not been established. Review must determine whether the
existing explicit crash-retention contract is sufficient for Stage-4 closure.
No new trajectory recovery policy or repair is authorized by this record.

## Real-root isolation and evidence retention

The real root was contacted only for read-only preflight and final verification:
`C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data`.
No production service was launched for these checks. All disposable services
stopped before the final production comparison at
`2026-09-10T16:49:19.240674+00:00`.

`real_before.json`, `real_after.json` and `real_postcheck.json` prove equality
of complete per-file hashes and authority observations, including SQLite
sidecars and policy/configuration files. Both inventories contain 2,093 files,
1,163,889,969 bytes, tree SHA-256:
`345d29441220273acc1371641be08e4e0dfd0fc381018b16a601b16dfb648776`.

Real core `f21c730f-5222-4aa8-9a5f-1c1188456df3`, selector generation 8,
NATIVE_ACTIVE/NATIVE_AGREEMENT, and lifecycle trajectory generation 10 with
legacy fence 2 remain unchanged. Thus real-root contact mode is READ_ONLY,
real-root unchanged is YES, selector/core agreement is PASS, native active is
YES, and trajectory authority unchanged is YES.

The external `evidence_manifest.json` binds 204 evidence/helper files. Its
SHA-256 is:
`eea9f3af0ce802b3c05d73629a363a0038b64f1274d21936f13c3ee55727a068`.
`root_inventories.json`, included in that manifest, binds all retained root
files: A 81, B 81, C 79, D 81. The manifest excludes its own hash,
`__pycache__`, and later `publication.json`; the result document binds the
manifest hash, and publication verification binds the result document.
Failed administration evidence and untouched crash artifacts remain available.
The report contains hashes/identities instead of unnecessary memory text;
external observations redact full memory summaries and PREPARED embedding bodies.

Validation for this evidence-only change consists of the administered scenarios,
integrity/authority observations, source review, evidence/hash reconciliation,
document review and Git diff checks. No full regression suite was rerun because
production code did not change. All disposable service processes are stopped.

```text
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4R2 = BLOCKED_TRAJECTORY_RECOVERY_REVIEW
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4 = BLOCKED_TRAJECTORY_RECOVERY_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NONEMPTY_SHARED_RANKING = NOT_YET_VALIDATED
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4R2_REVIEW
```

STOP at the R2 review boundary. No final migration YES or candidate promotion.
