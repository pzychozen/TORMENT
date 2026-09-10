# TORMENT post-P7 native production validation: Stage 1R4

## Result and authority

R4 reproduced the 240-second client timeout. The service continued CPU-active
and read-active afterward, while a single harmless health check returned HTTP
200 in about 15 ms. This establishes continued process activity and service
responsiveness after disconnect. It does not establish the query's eventual
internal result or identify a dominant execution stage.

The primary timeout classification is `UNRESOLVED`. The inspected repeated
whole-root validation path is a concrete candidate for later timing, but no
per-stage production measurement exists in the permitted observation surface.
Neither an SQLite timeout cause nor BGE latency is directly established.
R4 is held for review; no repair or further query campaign was performed.

R3 remains unchanged, including its formal `PRIVATE_NATIVE_QUERY = FAIL` and
unknown server-side query result. R4 uses the established R3 startup contract;
it does not revisit admission-contract qualification or repair Python CA trust.

```text
STARTING_HEAD = 1273e08f32eb5a7a299f230046965eee186e04be
ORIGIN_MAIN_AT_START = 1273e08f32eb5a7a299f230046965eee186e04be
HEAD_EQUALS_ORIGIN_MAIN_AT_START = YES
TRACKED_WORKTREE_AT_START = CLEAN
```

Preflight at `2026-09-10T06:20:36.5557331Z` found no listener on port 8787.
Pre-existing untracked artifacts were preserved. R3's result-record SHA-256 is
`46c99bb79674ae00dd813ac95e51f6d2078e34bb7139a091024025a74c830723`.
Its original query client, launcher, recovery helper, query observation, and
service log were verified against the frozen R3 manifest before reuse.

All project Python execution used Windows CMD and `conda activate torment`.
The service command remained `python -m torment_service`. Its process-local
environment retained the exact selected native deployment profile, strict ST
provider, and `HF_HUB_OFFLINE=1`; model/device/cache defaults were unchanged.
No package, certificate, timeout, query-mode, threading, logging, source-code,
SQLite-schema/index, or persistent configuration changes were made.

The selected authority remains generation 8, `NATIVE_ACTIVE`, core
`f21c730f-5222-4aa8-9a5f-1c1188456df3`, profile digest
`35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a`.
Before service execution, all 29 BGE cache/lock file fingerprints matched the
R3 baseline. The cache comparison did not load the model or construct a runtime.

## Exact R3 query recovered

`R3_QUERY_PATH_RECOVERED = YES`.

The R4 query client is a byte-for-byte copy of R3's external client. It sends
one JSON `POST http://127.0.0.1:8787/agent/query` with:

- Workspace `audit_smoke_v0_2`, private agent `smoke_runner`, admitted shared
  domain `personal`.
- `top_k=8`, `explain=true`, `continuity_debug=true`.
- No supplied vector or special search-mode flag. `peek_bridges` is omitted
  and defaults to false.
- The same 41-character, non-sensitive retained P7 smoke-memory phrase, SHA-256
  `87c006c9b6f3609934e2cb92228df31747d4b1539c200dc3507949005e11ae8c`.

The client uses `urllib.request.urlopen(request, timeout=240)` and reads the
response normally. It supplies no request/correlation identifier. The original
R3 observation started at `2026-09-10T05:59:09.911714+00:00` and recorded
`TimeoutError`, elapsed 240.0 seconds, no HTTP status, and no response bytes.
R3's log contains no query response or traceback; its clean shutdown does not
establish a successful query result.

Despite the private-query shorthand, this endpoint runs normal combined
private and shared retrieval. The `personal` argument routes the shared lane;
it does not fabricate a private motif-domain ID. Text is input to BGE/vector
search. `QueryReq` exposes neither a text-only search switch nor a separately
selectable vector-disabled mode. No synthetic substitute query was used.

## Ordered production path

This is the inspected control-flow map at the starting commit, not a claim
that existing telemetry timed every stage or proved every stage completed.

| Order | Code and operation |
| --- | --- |
| 1 | `__main__.py` starts Uvicorn. `app.py:168` checks auth/native route classification; `QueryReq` validates the body. `app.py:1259` is a synchronous FastAPI endpoint dispatched through the framework's thread pool. |
| 2 | Default thinking advisory calls the existing local `ThinkingController`. The native facade can refuse the optional geometric-context fallthrough; that inner exception is caught. The controller derives a memory plan through local rules, not LLM inference. |
| 3 | `public_runtime.py:709` checks supported query operation, prepares the existing native agent, and obtains a read-only workspace view. `_prepare_native_agent` and `_workspace_view` each call active-runtime recovery. Preparation loads existing identity and initializes process-local kernel state under an agent lock; that initialization can itself encode a seed string with BGE. |
| 4 | `production_native_owner.py:363` revalidates selector/profile authority and root-v2 runtime evidence. The whole-root profile, scope bindings, routing namespaces, membership closure, and disposition receipt are checked before the requested workspace is projected. Existing cached workspace views are consulted after fresh recovery, not before it. |
| 5 | `open_query_context` at owner line 290 performs another active-runtime recovery, then builds `NativeQualifiedQueryReadModel` and native motif geometry. No legacy memory graph is materialized. |
| 6 | `fabric.py:4734` uses the supplied native identity/read model. It encodes the query with ST/BGE, validates dimension 384, ranks admitted domains, and includes the explicit `personal` domain. |
| 7 | `_query_private_lane` and `_query_shared_lane` call native lane search. `query_read_model.py:419` delegates to `NativeMemoryVectorRuntime.search`; `native_memory_vector_runtime.py:281` independently encodes the text for each nonempty lane query. |
| 8 | Native readers open the qualified existing core, build source/vector snapshots from current native rows, validate witnesses, multiply the vector matrix, sort/filter candidates, and project current selected memory rows. This is the existing exact vector path, not a new SQL text-search substitute. |
| 9 | Fabric merges private/shared hits, reads motif geometry, applies ranking, continuity and governance filters, and optionally reads Character context. Native SRG query updates remain process-local overlays. Deep/collective retrieval is not enabled in this qualified profile. |
| 10 | Fabric returns a dictionary; the query context closes its readers; FastAPI serializes the result and Uvicorn sends the HTTP response. |

One concrete repeated-work candidate is visible in the source:
`root_membership_closure_digest` constructs `RootScopeMembershipRuntime`, asks
for `cache_keys`, and calls `resolve` for every key. Constructor recovery,
`cache_keys`, and each `resolve` recover membership state; recovery also verifies
the root profile. This traversal is reached by the ordinary native owner path.
It is a candidate for later stage timing, not a measured dominant-latency claim
or authorization to weaken any validation.

The configured path uses local ST encoding; no LLM or remote provider call was
found on it. Existing identity, workspace policy/metadata, bridges/conflicts,
and optional Character/affect reads use their retained external files. Native
memory, vectors, membership evidence, and compatibility projections come from
the selected core. Whole-root immutable admission/membership traversal is
present; no migration administration or legacy memory-directory census was
performed by R4.

## Existing observability and limits

`EXISTING_QUERY_STAGE_OBSERVABILITY = PARTIAL`.

| Observation | What it establishes |
| --- | --- |
| Uvicorn startup, response, error, shutdown log | Listening state, connected response status, uncaught exceptions, clean process shutdown. It has no query-stage timestamps. |
| `/health` | Existing harmless responsiveness check, public native mode, actual embedder identity and degradation status. |
| Health `locks` | Numbers of registered agent/workspace lock objects, not lock ownership, contention, or wait duration. |
| Health `embedder.cache_size` | Configured cache maximum, not the number of embeddings completed. It cannot timestamp or count query encoding. |
| Native vector runtime counters | Internal snapshot/rebuild properties exist, but this REST response and health surface do not expose them. No runtime inspection hook was added. |
| Windows process observations | CPU seconds, working/private memory, threads/handles, process read/write counters, and log progression. These counters do not identify individual Python stages, SQL statements, files, or physical disk traffic. |

There is no existing correlated query-start marker, encoding/read/search timer,
serialization timer, or durable response/completion record for this route.
`explain` and `continuity_debug` describe successful response contents; they do
not create a durable per-stage timing trace.

The installed Uvicorn H11 and httptools `send` implementations both return
immediately when the client has disconnected, before response access logging.
Consequently, absence of a post-timeout access line cannot distinguish a late
successful return from other unobserved internal outcomes. R4 did not change
logging levels, add instrumentation, attach a debugger, or install a profiler.

## Execution observations

R4 launched one service, PID 29348. Uvicorn reported completed startup and
listened at `127.0.0.1:8787`. At `2026-09-10T06:27:30.317445+00:00`, baseline
`GET /health` returned HTTP 200 in approximately 0.063 seconds, with `ok=true`,
`public_memory_mode=NATIVE`, ST/BGE/384, no degradation, and zero registered
agent/workspace locks.

The external host observer started before the one query. It samples only this
service PID and its existing log approximately every 15 seconds for a finite
window. The reproduction retains the 240-second client bound. The predeclared
post-timeout observation budget is at most 360 additional seconds, with one
harmless health check, no duplicate query, and no mutation request.

The primary request started at `2026-09-10T06:27:56.519245+00:00` and ended
client-side with `TimeoutError: timed out`, elapsed 240.016 seconds, no HTTP
status, and zero response bytes. The derived disconnect boundary is
`2026-09-10T06:31:56.535245+00:00`. No immediate shutdown or second query followed.

Host samples after that boundary continued to show increasing CPU and read
counters. At `2026-09-10T06:33:03.132621+00:00`, the one post-timeout health
request returned HTTP 200 in approximately 0.015 seconds, still NATIVE with
ST/BGE/384 and no degradation. Registered agent locks increased from zero to
one; workspace locks remained zero. This is consistent with native agent
preparation being reached, but does not prove lock release or embedding
completion. Health's cache field supplies no encoding counter.

The observer captured 44 samples, including final process absence. Within
the request/observation window:

| Sample interval (UTC) | Wall span | CPU increase | Process read-counter increase |
| --- | --- | --- | --- |
| 06:28:00.247 to 06:31:47.465, before client timeout | 227.218 s | 220.219 s, about 0.97 CPU core | 93,930,958,089 bytes; 22,943,845 read operations |
| 06:32:02.629 to 06:37:50.941, inside the planned post-timeout window | 348.312 s | 305.641 s, about 0.88 CPU core including the idle tail | 137,883,640,432 bytes; 33,679,899 read operations |

These are cumulative Windows process I/O counters, not measured physical-disk
throughput or attributed SQLite work. Working set across the query samples was
approximately 593-599 MB, without runaway growth. The raw observations retain
write counters as well; those are not evidence of semantic memory writes.

Between samples at `06:37:20.6635735Z` and `06:38:06.0396036Z`, the read counters
were identical and CPU increased only 0.015625 seconds. This supports a later
quiescent process state, after substantial post-disconnect activity. It does
not expose a response or distinguish successful completion from an unobserved
cancelled/otherwise handled outcome.

The planned 360-second post-timeout analysis window ended at
`2026-09-10T06:37:56.535245+00:00`. The transition-to-shutdown receipt was written
at `06:38:20.4731363Z`, about 24 seconds later, and immediately followed by one
Ctrl+C. No further request was issued during that interval. The finite host
observer also retained shutdown/exit samples outside the analysis window;
the interval statistics above use only samples inside the declared window.

Uvicorn logged normal shutdown, application shutdown completion, and finished
server PID 29348, with final log write time `06:38:20.8295415Z`. It did not log
a wait for background tasks. The service and command runner exited 0. As in R3,
CMD's subsequent batch prompt was answered N only to complete exit-code capture.
No force termination or second signal was used. The observer exited normally
after recording process absence; port 8787 had no listener.

There was still no query access line or traceback in the final service log.
Normal shutdown without a background wait narrows the final process state,
but cannot establish the query's return value, serialization success, or
semantic correctness.

Final read-only authority inspection at `06:39:25.949001+00:00` confirmed the
same generation-8 `NATIVE_ACTIVE` selection/core, active role, `ever_active`,
exact profile/envelope facts, and `NATIVE_AGREEMENT`, using SQLite 3.53.4.
All 29 BGE cache/lock file fingerprints remained unchanged after execution.

There was no observed busy/locked message, SQLite error, integrity error, or
exception tying the timeout to a native read. The Windows process I/O counters
do not attribute reads to SQLite, identify a query plan, or distinguish cached
reads from physical disk reads. `SQLITE_DIRECTLY_IMPLICATED_IN_TIMEOUT` remains
`UNESTABLISHED`, rather than a claim that SQLite has been exonerated.

The source path requires BGE encoding for the query if those stages are
reached, and may encode an agent seed during initial preparation. Neither
encoding start/completion nor duration is exposed by the collected telemetry.
Actual query-text encoding invocation and completion therefore remain
`UNESTABLISHED`. No synthetic embedding benchmark was run.

No control query was justified: a second combined query would not distinguish
root validation, encoding, or ranking costs, no text-only mode exists on this
surface, and the primary request's internal outcome was not established.
The prerequisite for additional Stage-1 read checks was not met. No shared-only,
text-only, vector-only, or scope-isolation follow-up was issued.

## Classification and behavioral matrix

The original R3 internal result remains `UNKNOWN`. R4's client result is a
separate reproduced timeout. `NOT_ESTABLISHED` below denotes unavailable
behavioral evidence from the combined request, not proof that a lane never
ran or that its search computation failed. No internal PASS is inferred from
process activity, absence of a traceback, or later clean shutdown.

```text
R3_QUERY_PATH_RECOVERED = YES
EXISTING_QUERY_STAGE_OBSERVABILITY = PARTIAL
R4_STARTUP = PASS
NATIVE_OWNER_RECOGNITION = PASS
SELECTOR_CORE_AGREEMENT = PASS
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
SERVICE_RESPONSIVE_BEFORE_QUERY = PASS
PRIVATE_QUERY_CLIENT_RESULT = TIMEOUT
CLIENT_RESULT = TIMEOUT
CLIENT_ELAPSED = 240.016 seconds
R3_PRIVATE_QUERY_INTERNAL_RESULT = UNKNOWN
R4_PRIVATE_QUERY_INTERNAL_RESULT = UNKNOWN
QUERY_RESULT_SEMANTICALLY_VALID = UNESTABLISHED
QUERY_STAGE_WITH_DOMINANT_LATENCY = UNESTABLISHED
SERVER_STATE_AFTER_CLIENT_TIMEOUT = CONTINUED_ACTIVITY_THEN_QUIESCENT; INTERNAL_RESULT_UNKNOWN
SERVICE_RESPONSIVE_AFTER_TIMEOUT = PASS
QUERY_PROCESS_STATE = CPU_ACTIVE
QUERY_PROCESS_SECONDARY_STATE = IO_ACTIVE (process read counters)
QUERY_EMBEDDING_INVOKED = UNESTABLISHED
QUERY_EMBEDDING_COMPLETED = UNESTABLISHED
SQLITE_DIRECTLY_IMPLICATED_IN_TIMEOUT = UNESTABLISHED
CONTROL_QUERY_RUN = NO
CONTROL_QUERY_RESULT = NOT_RUN
PRIVATE_QUERY_TIMEOUT_CLASS = UNRESOLVED
PRIVATE_NATIVE_QUERY = NOT_ESTABLISHED
SHARED_NATIVE_QUERY = NOT_ESTABLISHED
TEXT_SEARCH = NOT_ESTABLISHED
VECTOR_SEARCH = NOT_ESTABLISHED
PRIVATE_SHARED_SCOPE_ISOLATION = NOT_ESTABLISHED
NORMAL_SHUTDOWN = PASS
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R4 = HELD_FOR_REVIEW
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R4_REVIEW
```

## Evidence and publication

External evidence directory:
`C:\TORMENT\TORMENT_administration\post-p7-stage-1r4-20260910`.

`evidence_manifest.json` freezes the external clients/launcher, recovered-path
record, inspected-source hashes, preflight and authority checks, cache checks,
raw process samples, derived summary, HTTP observations, shutdown receipt,
and behavioral matrix. Manifest SHA-256:
`81dd0a4c76f73e7bebfeb115a411ccdec84f65c8cb4714ea186fcfdcc2f7e6d5`.

| Evidence | SHA-256 |
| --- | --- |
| `query_path_before_reproduction.json` | `bbcd33202fee7b7030659b354bad3f4055443f14f6e06c50e25a7e63d3183826` |
| `prelaunch_environment.json` | `44abcf692f66ac797c9912be3d39568ba72a489a2c8a9622dde327e4432ebac1` |
| `primary_query.json` | `fc9d0bbd37eb4c330a093463d1e56810e86bb9b651583f2a73ba68ecadfc5ed6` |
| `health_before.json` | `b703862fa26f4050169c943461acf7b51471058aee46902f6b58c36af53bcb16` |
| `health_after_timeout.json` | `8995adf18cc97d7830afbf08ac2d00643ac106e8a44e7896d2cf175f79730355` |
| `process_observations.jsonl` | `9e0deb427d3ba1071cbfdec2c76d298f1a62f24887f8d2ba343d87dc85413767` |
| `observation_summary.json` | `71847cd6797951178d2d71d3629afaf9c72d75b56611bc8911535de1e8f62104` |
| `startup.log` | `3f219542b3b6b9af1bc1b5791463209eb930fcede8dd2e441dcba2f161d4dd50` |
| `execution_receipt.json` | `8841905afdf2f435d287d26f5855734de163c516f27c248c618ffa7770ce4cd9` |
| `host_proof_observation.json` | `7b00acb37099c4bda4f93ac829b4630434941843eec4c112cad057b63cd229ff` |
| `cache_after_service.json` | `cf50065a93e3dfdf9b721a1e837114cfd573270d7e8d67cf94ab56bc097ed79f` |
| `behavioral_matrix.json` | `7d1f3bc6e6ab0ebc5a84ebd3948eeff97d206d1807774c0466a4ba57116eb1c3` |

This new result record is the only repository file to publish. No writes,
reinforcement, Character mutation, trajectory mutation, persistence/restart
testing, scale testing, or repair are authorized by R4. No unit suite or
synthetic embedding benchmark substitutes for the one real production query.

The remaining review need is correlated server completion and stage timing
for the same query, including repeated root recovery, agent initialization,
encoding, native snapshots, and ranking/serialization. R4 did not add that
instrumentation or change the client limit to conceal the anomaly.

Publication follows the existing evidence-only policy: whitespace validation,
one-file staging, commit, push, and verification of local/tracking/remote main.
`FINAL_HEAD` / `COMMIT` identifies the commit containing this record; embedding
its own literal commit SHA would be self-referential. Exact final Git values
and record SHA-256 are stored externally in `publication_verification.json`
after publication and returned with delivery.

The final stop boundary is
`POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R4_REVIEW`.
`POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW` and
`SQLITE_MIGRATION_FULLY_VALIDATED = NO`.
