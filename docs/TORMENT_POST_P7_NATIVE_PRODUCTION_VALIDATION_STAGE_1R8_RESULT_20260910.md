# TORMENT — Post-P7 Native Production Validation — Stage 1R8

Date: 2026-09-10 UTC.

**R8 stopped at the first ordinary memory write.** The public service returned
HTTP 409 because the selected existing audit domain enables an auto-merge
motif policy that the native public ingest path explicitly refuses before
cognition. No memory was created. No retry, policy change, repair, reinforcement,
trajectory write, or restart followed.

POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R8 = FAIL_STOPPED_NATIVE_WRITE_REFUSAL.
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW.
SQLITE_MIGRATION_FULLY_VALIDATED = NO.

## Authority, Git, and environment

The controlling R8 order is the attachment
65fd8f24-883e-42e8-9d63-b2213ac06248/pasted-text.txt. Its section 25 requires
an immediate stop for an unexpected normal native write refusal and prohibits
automatic repair. The original Stage-1 section 25 permits the bounded
evidence-only commit and push. This record is the sole repository change.

Starting HEAD and origin/main both:
**6d009b6d0bffa05406b8f98194d34514e34ba40b**.
The tracked worktree and index were clean. Existing unrelated untracked
artifacts were preserved; their listing fingerprint was unchanged after
shutdown. No reset, stash, clean, or broad staging occurred.

The service ran as **python -m torment_service**, in Windows CMD with
**conda activate torment**, using
C:\Users\Notandi\miniconda3\envs\torment\python.exe and SQLite **3.53.4**.
The exact seven-field qualified deployment profile was recovered from the
selected core's immutable root-v2 admission record. No external descriptor or
data-root override was supplied.

| Fact | Observed value before startup and after shutdown |
| --- | --- |
| Selector generation/state | 8 / NATIVE_ACTIVE |
| Active core | f21c730f-5222-4aa8-9a5f-1c1188456df3 |
| Core role / ever active | ACTIVE_CORE / true |
| Deployment agreement | NATIVE_AGREEMENT |
| Profile digest | 35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a |
| Root envelope digest | e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb |
| Completion witness | TORMENT_ROOT_ADMISSION_COMPLETION_WITNESS, version 2 |

The process-local environment retained HF_HUB_OFFLINE=1,
TORMENT_EMBED_PROVIDER=st, TORMENT_EMBED_STRICT=1, and the existing optional
TORMENT_DIAGNOSTIC_QUERY_TIMING=1. No configuration, timeout, index, SQLite
tuning, owner recovery, or performance instrumentation changed.

## Startup and safe scope

Uvicorn PID **56716** completed normal startup. GET /health returned HTTP 200
in **0.031 seconds**, with ok=true, public_memory_mode=NATIVE and
embedder_degraded=false. The root-v2 startup path constructs the native
production owner before the public native facade; the actual refusal stack
also reaches that facade. Native owner recognition and selector/core
agreement passed. No legacy public fallback or maintenance-only posture was
observed.

The intended write scope was the already admitted and previously designated
audit/smoke scope, with no existing Character state:

| Binding | Identifier |
| --- | --- |
| Workspace | audit_smoke_v0_2 |
| Agent / scope | smoke_runner / PRIVATE |
| Source namespace | bc5ba3ef-36f4-4aa0-9516-e46c1c0a6496 |
| Identity namespace | 9740307e-0393-4f64-9d15-f58ae3065afe |
| Semantic scope | 7fd00d8a-17b3-49e2-bab4-9b938f7f9a53 |
| Private motif domain | None |
| Operation's admitted shared domain | personal |
| Shared source namespace | c54e6edb-496c-4ae0-8b26-98bc32743eba |
| Shared semantic scope | bfba7bc1-71b7-4e55-9a72-d73f0cb692b9 |

No workspace or shared memory was created.

## Single write attempt and mandatory stop

At **2026-09-10T08:47:53.843705Z**, the client issued exactly one normal
POST /agent/ingest with private scope, domain personal, step 1000101, and
an Idempotency-Key. It supplied ordinary non-secret text; it supplied neither
an embedding nor a summary. The harmless note was intended to be safe to
retain and identifiable by this unique marker:

**R8-20260910-a0c569b6-ab8d-4c2a-bd58-50c6b223bf39**

Create key: R8-20260910-a0c569b6-ab8d-4c2a-bd58-50c6b223bf39:create.
Content SHA-256:
d65c6dfe663a27aa4829d4cc07f144df8e525b427f38c3e1b272d31d95d25982.
Request SHA-256:
380cbd6897c0919d8b0a00e548586451c202655f5af595f44f972c431a37b7a2.
The ordinary client timeout remained **240 seconds**.

The response arrived in **8.563 seconds**, HTTP **409**, with:

~~~text
NativePublicOperationRefused: native public ingest refuses an unqualified auto-merge motif policy before cognition
~~~

The existing file
data/workspaces/audit_smoke_v0_2/domain_policies.json contains
policies.personal.auto_merge_motifs=true. The corresponding guard in
torment_service/public_runtime.py:685-688 rejects this policy after private
and shared-domain admission checks, before constructing the executor request.
The stack shows Spine's ordinary fast ingest handler reaching this guard.
This is a production qualification blocker; successful memory persistence
must not be inferred from the fact that the refusal correctly fails closed.

The native public ingest executor, receipt reservation, source mutation, and
post-write tail were not reached. There is **no new EID, native object,
revision, mutation receipt, or trajectory write identifier**. Complete native
row-hash comparison independently confirms no new operation or memory.

The HTTP error receipt and server stack are frozen. No second ingest was
sent. No attempt was made with another domain, scope, policy, supplied vector,
alternate runtime adapter, or bypass.

## Unexercised lifecycle checks

The stop occurred before read-after-write. Consequently, write-then-read,
reinforcement, pre-restart reinforcement visibility, Character continuity,
native trajectory write, restart, memory persistence, reinforcement
persistence, post-restart Character continuity, trajectory authority
reconstruction, and the additional post-restart trajectory write are all
**NOT_RUN_STOP_CONDITION**.

The same applies to new-memory scope-isolation queries: there was no new
memory to validate. No production query was sent in R8. R6/R7 read and
isolation evidence remains retained, but does not qualify the missing R8
mutable lifecycle. Prepared external query and restart helpers were unused;
run2 has no startup log.

The planned ordinary Character observation was the existing query context
for the previously observed test-hive contrarian. It was not executed.
Unchanged Character files do not substitute for the required ordinary
pre/post-restart Character behavior observation.

## Trajectory authority and clean shutdown

The selected private artifact root's coordinator record remained:

| Fact | Before / after |
| --- | --- |
| Phase | HANDOFF_COMPLETE |
| Generation | 4 |
| Legacy fence generation | 2 |
| Native writer identity | NATIVE_TRAJECTORY_EVIDENCE |
| Native session | pid:27872:a8746b8c-be84-4cc7-bfa6-fd60edfd0de5 |
| Exclusivity key | 75645e5d7b5afb0e7143ed5651c4185509f2a075fc5b1a557d0b22656654d8b0 |

This is the unchanged pre-existing durable session record, **not** a claim
that PID 56716 acquired or reconstructed a trajectory session. No writer was
acquired and no new write intent appeared. No stale legacy writer was launched.

One Ctrl+C initiated ordinary Uvicorn shutdown after the refusal. The log
records application shutdown complete and finished server process 56716.
Answering N to CMD's terminate-batch prompt preserved launcher exit code
**0**. Both the process and the port-8787 listener were absent afterward.
This clean shutdown passed; no restart was attempted.

## Durable accounting, refusals, and models

| Durable artifact | Before bytes | After bytes | SHA-256 at both observations |
| --- | ---: | ---: | --- |
| Selected production core | 82,747,392 | 82,747,392 | eea6e07072e0cdad09ab2872203361c18adf19e044f452686249352aef84dc85 |
| Core WAL | 0 | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| Trajectory authority.sqlite | 819,200 | 819,200 | 7b754136a2449175dcb1d7cdc6dd6f8b528ae43c6629297a16d81e65e0c1593c |
| Trajectory WAL | 0 | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |

Every native-core and trajectory-authority table's row hashes matched.
All **105 fingerprinted files** across the selected audit workspace and the
planned Character-observation test hive matched, including domain policy,
Character, and trajectory files. Existing untracked artifacts matched.
The bounded post-run data-file timestamp inventory found only SQLite shared
memory coordination files and a still-empty core WAL. These coordination
file timestamp updates from normal database access are not durable semantic
mutations. No unexplained durable mutation was observed.

AUTHORIZED_DURABLE_MUTATION_ONLY = PASS for this stopped attempt: no durable
production mutation occurred. This does not establish successful mutable
lifecycle accounting or weaken the expected-write rule for a later slice.

The frozen **35 memory** and **23 motif** refusal identity sets were retained.
The byte-identical core and matching revision/representation rows exclude
successors or READY promotions during this run. No returned memory results
existed through which a refusal could have leaked. No new P3 semantic census
was performed.

Private motif_domain_id=None and operation domain personal were retained
through admission preflight. No successful motif consumer was exercised in
R8, so MODEL_D_PRESERVED is reported **NOT_OBSERVED** for this lifecycle.
R7's successful Model D observation and the unchanged strict shared validation
implementation remain retained.

Only local **BAAI/bge-small-en-v1.5** was loaded, with ST provider, CPU, and
384 dimensions. No conversational generative model or external AI provider
was configured or invoked. The request failed before ingest cognition.
All **29** previously frozen model-cache/lock fingerprints remained unchanged,
with no additions or removals. No inference count or benchmark is claimed.

## Evidence, validation, and required return

External evidence:
C:\TORMENT\TORMENT_administration\post-p7-stage-1r8-20260910.

Key artifacts are before.json, after_shutdown.json, create_intent.json,
create.json, run1/prelaunch_environment.json, run1/health.json,
run1/startup.log, run1/service_exit_code.txt, shutdown.json,
cache_before.json, cache_after.json, and stopped_evidence_verification.json.
They retain redacted native row fingerprints and identifiers, not historical
memory contents. The external plan contains only the deliberately harmless
proposed validation text.

Before service launch, the read-only snapshot helper's trajectory-intent
ORDER BY column was corrected to the existing prepared_at_ns name. Its first
attempt made no production operation or data mutation. No production code
was changed to obtain or alter this result.

stopped_evidence_verification.json passes all comparisons and stop/shutdown
checks. This verification PASS is evidence validation, not an R8 lifecycle
PASS. Since only this Markdown result record changes in the repository,
validation is git diff --check; no application test run or repair was made.

evidence_manifest.json binds the external observations/helpers and frozen
references. publication_verification.json records the final commit,
origin/main, tracked state, document digest, and manifest digest after the
bounded evidence-only publication. Literal final Git IDs are supplied there
and in the final response, avoiding a self-referential commit hash here.

~~~text
STARTING_HEAD = 6d009b6d0bffa05406b8f98194d34514e34ba40b
R8_STARTUP = PASS
NATIVE_OWNER_RECOGNITION = PASS
SELECTOR_CORE_AGREEMENT = PASS
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
NATIVE_MEMORY_WRITE = FAIL_HTTP_409_AUTO_MERGE_POLICY_REFUSED
WRITE_THEN_READ = NOT_RUN_STOP_CONDITION
NATIVE_REINFORCEMENT = NOT_RUN_STOP_CONDITION
REINFORCEMENT_VISIBLE_PRE_RESTART = NOT_RUN_STOP_CONDITION
CHARACTER_CONTINUITY_PRE_RESTART = NOT_RUN_STOP_CONDITION
NATIVE_TRAJECTORY_WRITE = NOT_RUN_STOP_CONDITION
NORMAL_SHUTDOWN = PASS
RESTART_STARTUP = NOT_RUN_STOP_CONDITION
MEMORY_PERSISTENCE_AFTER_RESTART = NOT_RUN_STOP_CONDITION
REINFORCEMENT_PERSISTENCE_AFTER_RESTART = NOT_RUN_STOP_CONDITION
CHARACTER_CONTINUITY_AFTER_RESTART = NOT_RUN_STOP_CONDITION
TRAJECTORY_AUTHORITY_RECONSTRUCTION = NOT_RUN_STOP_CONDITION
POST_RESTART_NATIVE_TRAJECTORY_WRITE = NOT_RUN_STOP_CONDITION
NEW_MEMORY_SCOPE_ISOLATION = NOT_RUN_STOP_CONDITION
AUTHORIZED_DURABLE_MUTATION_ONLY = PASS_NO_DURABLE_PRODUCTION_MUTATION
MODEL_D_PRESERVED = NOT_OBSERVED
CERTIFIED_REFUSAL_RUNTIME_LEAK_OBSERVED = NO
GENERATIVE_MODEL_INVOLVED = NO
GENERATIVE_MODEL_DETAILS = LOCAL_BGE_LOADED_ONLY; NO_GENERATIVE_PROVIDER
NONEMPTY_SHARED_RANKING = DEFERRED_EXISTING_CORPUS_EMPTY
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R8 = FAIL_STOPPED_NATIVE_WRITE_REFUSAL
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R8_REVIEW
~~~

The existing empty-shared ranking limit remains NOT_YET_VALIDATED and was
not the cause of this stop. R8 cannot close Stage 1 because the first ordinary
write did not succeed. Review the observed policy/qualification mismatch
before authorizing further mutable work. No repair or Stage 2 has begun.
